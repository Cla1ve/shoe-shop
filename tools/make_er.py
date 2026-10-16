"""Рисует ER-диаграмму из реальной схемы shop.db и сохраняет в ER_diagram.pdf и docs/ER_diagram.png.

Таблицы, столбцы, ключи и связи берутся из самой базы (PRAGMA table_info и foreign_key_list),
поэтому диаграмма всегда совпадает со schema.sql. Положение таблиц на листе задано вручную.
Запуск из корня проекта:  python tools/make_er.py   (нужен Pillow)
"""
import os
import sqlite3

from PIL import Image, ImageDraw, ImageFont

DB = "shop.db"
S = 2                                     # масштаб: рисуем в двойном размере
W, H = 1760, 1080
FONT = "C:/Windows/Fonts/arial.ttf"
FONT_B = "C:/Windows/Fonts/arialbd.ttf"
ROW = 28
BOX_W = 330

# левый верхний угол каждой таблицы на листе
POS = {
    "Categories": (40, 70), "Manufacturers": (40, 290), "Products": (470, 90),
    "Stock": (960, 70), "Sizes": (1380, 70), "OrderItems": (960, 410),
    "Orders": (960, 740), "Users": (470, 740), "Roles": (40, 740),
}


def load_schema(conn):
    tables = {}
    for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"):
        cols = conn.execute("PRAGMA table_info(%s)" % name).fetchall()
        fks = {r[3]: (r[2], r[4]) for r in conn.execute("PRAGMA foreign_key_list(%s)" % name)}
        uniques = set()
        for idx in conn.execute("PRAGMA index_list(%s)" % name):
            if idx[2]:
                for c in conn.execute("PRAGMA index_info(%s)" % idx[1]):
                    uniques.add(c[2])
        tables[name] = {"cols": cols, "fks": fks, "uniques": uniques}
    return tables


def box(d, name, info, x, y, f, fb):
    h = (len(info["cols"]) + 1) * ROW
    d.rectangle([x * S, y * S, (x + BOX_W) * S, (y + h) * S], fill=(255, 255, 255), outline=(27, 58, 92), width=2 * S)
    d.rectangle([x * S, y * S, (x + BOX_W) * S, (y + ROW) * S], fill=(27, 58, 92))
    d.text(((x + 12) * S, (y + 5) * S), name, font=fb, fill=(255, 255, 255))
    for i, (cid, cname, ctype, notnull, default, pk) in enumerate(info["cols"], 1):
        yy = y + i * ROW
        mark = "PK" if pk else ("FK" if cname in info["fks"] else "")
        if pk:
            d.rectangle([(x + 1) * S, (yy + 1) * S, (x + BOX_W - 1) * S, (yy + ROW) * S], fill=(255, 243, 214))
        d.text(((x + 10) * S, (yy + 5) * S), mark, font=fb, fill=(200, 80, 10))
        label = cname + ("  (U)" if cname in info["uniques"] and not pk else "")
        d.text(((x + 48) * S, (yy + 5) * S), label, font=f, fill=(30, 30, 30))
        d.text(((x + BOX_W - 100) * S, (yy + 5) * S), ctype or "", font=f, fill=(120, 120, 130))
        d.line([(x * S, (yy + ROW) * S), ((x + BOX_W) * S, (yy + ROW) * S)], fill=(225, 228, 235), width=S)
    return h


def anchor(name, tables, side, row_of=None):
    x, y = POS[name]
    h = (len(tables[name]["cols"]) + 1) * ROW
    yy = y + (row_of * ROW + ROW // 2 if row_of is not None else h // 2)
    return {"l": (x, yy), "r": (x + BOX_W, yy), "t": (x + BOX_W // 2, y), "b": (x + BOX_W // 2, y + h)}[side]


def main():
    conn = sqlite3.connect(DB)
    tables = load_schema(conn)
    img = Image.new("RGB", (W * S, H * S), (248, 249, 252))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, 15 * S)
    fb = ImageFont.truetype(FONT_B, 15 * S)
    ft = ImageFont.truetype(FONT_B, 26 * S)
    d.text((40 * S, 18 * S), "ER-диаграмма базы данных «Продажа обуви» (3НФ)", font=ft, fill=(27, 58, 92))

    # связи: (дочерняя таблица, столбец внешнего ключа) -> родитель; линия идёт ломаной
    def link(child, col, parent, child_side, parent_side, via=None):
        names = [c[1] for c in tables[child]["cols"]]
        a = anchor(child, tables, child_side, names.index(col) + 1)
        b = anchor(parent, tables, parent_side)
        pts = [a] + (via or []) + [b]
        d.line([(px * S, py * S) for px, py in pts], fill=(90, 100, 120), width=2 * S, joint="curve")
        # подписи: 1 у родителя, N у ребёнка
        def label(point, side, text, color):
            dx, dy = {"l": (-16, -22), "r": (6, -22), "t": (8, -24), "b": (8, 4)}[side]
            d.text(((point[0] + dx) * S, (point[1] + dy) * S), text, font=fb, fill=color)

        label(b, parent_side, "1", (200, 80, 10))
        label(a, child_side, "N", (27, 120, 60))

    link("Products", "category_id", "Categories", "l", "r")
    link("Products", "manufacturer_id", "Manufacturers", "l", "r", via=[(430, anchor("Products", tables, "l", 3)[1]), (430, anchor("Manufacturers", tables, "r")[1])])
    link("Stock", "product_id", "Products", "l", "r")
    link("Stock", "size_id", "Sizes", "r", "l")
    link("OrderItems", "product_id", "Products", "l", "b", via=[(700, anchor("OrderItems", tables, "l", 3)[1]), (700, anchor("Products", tables, "b")[1] + 30), (anchor("Products", tables, "b")[0], anchor("Products", tables, "b")[1] + 30)])
    link("OrderItems", "size_id", "Sizes", "r", "b", via=[(1480, anchor("OrderItems", tables, "r", 4)[1]), (1480 + 65, anchor("OrderItems", tables, "r", 4)[1]), (1480 + 65, anchor("Sizes", tables, "b")[1] + 30), (anchor("Sizes", tables, "b")[0], anchor("Sizes", tables, "b")[1] + 30)])
    link("OrderItems", "order_id", "Orders", "b", "t")
    link("Orders", "client_id", "Users", "l", "r")
    link("Users", "role_id", "Roles", "l", "r")

    for name, info in tables.items():
        box(d, name, info, *POS[name], f, fb)

    d.text((40 * S, (H - 60) * S), "PK ключ, FK внешний ключ, (U) уникальное значение. 1 это сторона «один», N сторона «много».", font=f, fill=(90, 100, 120))
    d.text((40 * S, (H - 34) * S), "Каждый факт хранится один раз: категории, производители, размеры и роли вынесены в справочники, цена заказа хранится в OrderItems.", font=f, fill=(90, 100, 120))
    img = img.resize((W, H), Image.LANCZOS)
    os.makedirs("docs", exist_ok=True)
    img.save(os.path.join("docs", "ER_diagram.png"))
    img.save("ER_diagram.pdf", "PDF", resolution=130.0)
    print("сохранено: ER_diagram.pdf, docs/ER_diagram.png")


if __name__ == "__main__":
    main()
