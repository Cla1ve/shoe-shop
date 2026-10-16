"""Импорт данных из пяти файлов xlsx в shop.db одной транзакцией.

Порядок важен: сначала справочники (размеры, роли, пользователи), потом товары, потом остатки, потом заказы.
Запуск:  python3 import_data.py       (базу создаёт create_db.py)
Если что-то упало, ничего не сохраняется (rollback). Повторный запуск дублей не создаёт.
"""
import logging
import os
import sqlite3
import sys

from read_excel import read_xlsx, excel_date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shop.db")
LOG_PATH = os.path.join(BASE_DIR, "import.log")

# таблицы, в которых есть только id и name; get_or_create принимает имя таблицы только из этого списка
NAME_TABLES = ("Categories", "Manufacturers", "Roles")

log = logging.getLogger("import")


def data_rows(filename):
    """Читает файл и отбрасывает первую строку (заголовки) и полностью пустые строки."""
    rows = read_xlsx(os.path.join(BASE_DIR, filename))
    return [r for r in rows[1:] if any(cell not in (None, "") for cell in r)]


def clean(value):
    """Пустую ячейку превращаем в None, строки обрезаем по краям."""
    if isinstance(value, str):
        value = value.strip()
    return value if value != "" else None


def get_or_create(cur, table, name):
    """Возвращает id записи с таким названием, при необходимости создаёт её."""
    if table not in NAME_TABLES:
        raise ValueError("неизвестная таблица справочника: %s" % table)
    cur.execute("INSERT OR IGNORE INTO %s (name) VALUES (?)" % table, (name,))
    return cur.execute("SELECT id FROM %s WHERE name = ?" % table, (name,)).fetchone()[0]


def import_sizes(cur):
    added = 0
    for (value, *_rest) in data_rows("Sizes_import.xlsx"):
        cur.execute("INSERT OR IGNORE INTO Sizes (value) VALUES (?)", (int(value),))
        added += cur.rowcount
    log.info("Sizes: добавлено %d", added)


def import_users(cur):
    added = 0
    for full_name, login, role in data_rows("Users_import.xlsx"):
        role_id = get_or_create(cur, "Roles", clean(role))
        cur.execute("INSERT OR IGNORE INTO Users (login, full_name, role_id) VALUES (?, ?, ?)",
                    (clean(login), clean(full_name), role_id))
        added += cur.rowcount
    log.info("Users: добавлено %d, ролей в справочнике %d", added, cur.execute("SELECT COUNT(*) FROM Roles").fetchone()[0])


def import_products(cur):
    """Товары вместе со справочниками категорий и производителей.
    Если такая модель того же производителя уже есть, обновляем цену, описание и картинку."""
    count = 0
    for name, category, manufacturer, description, composition, price, image in data_rows("Products_import.xlsx"):
        category_id = get_or_create(cur, "Categories", clean(category))
        manufacturer_id = get_or_create(cur, "Manufacturers", clean(manufacturer))
        cur.execute(
            """INSERT INTO Products (name, category_id, manufacturer_id, description, composition, price, image)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(name, manufacturer_id) DO UPDATE SET
                   category_id = excluded.category_id,
                   description = excluded.description,
                   composition = excluded.composition,
                   price       = excluded.price,
                   image       = excluded.image""",
            (clean(name), category_id, manufacturer_id, clean(description), clean(composition), float(price), clean(image)))
        count += 1
    log.info("Products: обработано %d (в таблице теперь %d)", count, cur.execute("SELECT COUNT(*) FROM Products").fetchone()[0])
    log.info("Categories: %d, Manufacturers: %d",
             cur.execute("SELECT COUNT(*) FROM Categories").fetchone()[0],
             cur.execute("SELECT COUNT(*) FROM Manufacturers").fetchone()[0])


def find_product(cur, name, manufacturer):
    row = cur.execute(
        """SELECT p.id FROM Products p JOIN Manufacturers m ON m.id = p.manufacturer_id
           WHERE p.name = ? AND m.name = ?""", (name, manufacturer)).fetchone()
    return row[0] if row else None


def find_size(cur, value):
    row = cur.execute("SELECT id FROM Sizes WHERE value = ?", (int(value),)).fetchone()
    return row[0] if row else None


def import_stock(cur):
    loaded = skipped = 0
    for name, manufacturer, size, quantity in data_rows("Stock_Items_import.xlsx"):
        product_id = find_product(cur, clean(name), clean(manufacturer))
        size_id = find_size(cur, size)
        if product_id is None or size_id is None:
            # такой модели или размера нет в справочниках: строку пропускаем и пишем об этом
            log.warning("Stock: пропущена строка (%s, %s, размер %s): нет такого товара или размера", name, manufacturer, size)
            skipped += 1
            continue
        cur.execute(
            """INSERT INTO Stock (product_id, size_id, quantity) VALUES (?, ?, ?)
               ON CONFLICT(product_id, size_id) DO UPDATE SET quantity = excluded.quantity""",
            (product_id, size_id, int(quantity)))
        loaded += 1
    total = cur.execute("SELECT SUM(quantity) FROM Stock").fetchone()[0]
    log.info("Stock: загружено %d, пропущено %d, всего пар на складе %s", loaded, skipped, total)


def get_client(cur, full_name, guests):
    """Клиент заказа по ФИО. Если такого нет в Users, создаём гостя с ролью Клиент."""
    row = cur.execute("SELECT id FROM Users WHERE full_name = ?", (full_name,)).fetchone()
    if row:
        return row[0]
    role_id = get_or_create(cur, "Roles", "Клиент")
    login = "guest%d" % (cur.execute("SELECT COUNT(*) FROM Users WHERE login LIKE 'guest%'").fetchone()[0] + 1)
    cur.execute("INSERT INTO Users (login, full_name, role_id) VALUES (?, ?, ?)", (login, full_name, role_id))
    guests.append(full_name)
    return cur.lastrowid


def import_orders(cur):
    """Несколько строк файла с одним номером заказа попадают в один Orders.id (для этого кэш order_ids)."""
    order_ids = {}          # номер заказа из файла -> Orders.id
    guests = []
    items = 0
    for number, order_date, client, name, manufacturer, size, quantity, price in data_rows("Orders_import.xlsx"):
        number = int(number)
        if number not in order_ids:
            existing = cur.execute("SELECT id FROM Orders WHERE external_number = ?", (number,)).fetchone()
            if existing:
                order_ids[number] = None          # заказ уже загружен раньше, его позиции пропускаем
            else:
                client_id = get_client(cur, clean(client), guests)
                cur.execute("INSERT INTO Orders (external_number, order_date, client_id) VALUES (?, ?, ?)",
                            (number, excel_date(order_date), client_id))
                order_ids[number] = cur.lastrowid
        order_id = order_ids[number]
        if order_id is None:
            continue
        product_id = find_product(cur, clean(name), clean(manufacturer))
        size_id = find_size(cur, size)
        if product_id is None or size_id is None:
            log.warning("Orders: заказ %s, не найден товар %s (%s) размер %s", number, name, manufacturer, size)
            continue
        cur.execute("INSERT INTO OrderItems (order_id, product_id, size_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
                    (order_id, product_id, size_id, int(quantity), float(price)))
        items += 1
    new_orders = len([v for v in order_ids.values() if v is not None])
    log.info("Orders: новых заказов %d, позиций %d, создано гостей %d", new_orders, items, len(guests))
    for g in guests:
        log.info("   гость: %s", g)


def report(cur):
    """Итоговые количества и проверочный JOIN: заказ -> позиции -> товары."""
    log.info("--- итог по таблицам ---")
    for table in ("Roles", "Users", "Categories", "Manufacturers", "Sizes", "Products", "Stock", "Orders", "OrderItems"):
        log.info("%-14s %d", table, cur.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0])
    row = cur.execute(
        """SELECT o.external_number, u.full_name, COUNT(oi.id), SUM(oi.quantity * oi.unit_price)
           FROM Orders o JOIN Users u ON u.id = o.client_id JOIN OrderItems oi ON oi.order_id = o.id
           GROUP BY o.id ORDER BY o.id LIMIT 1""").fetchone()
    log.info("проверка JOIN: заказ %s, клиент %s, позиций %s, сумма %s", *row)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S",
                        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_PATH, encoding="utf-8")])
    if not os.path.exists(DB_PATH):
        log.error("нет файла shop.db, сначала запустите python3 create_db.py")
        return 1
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    try:
        log.info("начинаю импорт")
        import_sizes(cur)
        import_users(cur)
        import_products(cur)
        import_stock(cur)
        import_orders(cur)
        conn.commit()                     # один commit в самом конце
        log.info("импорт завершён, изменения сохранены")
        report(cur)
    except Exception:
        conn.rollback()                   # при любой ошибке база остаётся как была
        log.exception("импорт не удался, изменения отменены")
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
