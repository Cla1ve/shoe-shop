"""Короткая проверка API на работающем сервере (ПР 2.2, 2.3, 2.4). Только стандартная библиотека.

Запуск (сервер должен быть запущен):  python3 tools/api_demo.py
"""
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"


def get(path):
    try:
        with urllib.request.urlopen(BASE + path) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def show_login():
    print("== /api/login, пять пользователей и один неверный логин")
    for login in ("isivanov", "edsmirnova", "anpetrov", "masokolova", "dovolkov", "nouser"):
        status, data = get("/api/login?login=" + login)
        text = "%s, %s" % (data["full_name"], data["role"]) if status == 200 else data["error"]
        print("  %-11s -> %d  %s" % (login, status, text))


def show_products():
    print("== /api/products")
    status, items = get("/api/products")
    print("  без параметров: %d, моделей %d, со скидкой %d, подсвечено (остаток <= 3) %d"
          % (status, len(items), sum(1 for i in items if i["discount"]), sum(1 for i in items if i["low_stock"])))
    status, items = get("/api/products?category=1")
    print("  category=1 (%s): %d моделей" % (items[0]["category"], len(items)))
    status, items = get("/api/products?search=" + urllib.parse.quote("кеды"))
    print("  search=кеды: " + ", ".join(i["name"] for i in items))
    status, items = get("/api/products?category=4&sort=price_asc")
    print("  category=4&sort=price_asc, первые три:")
    for i in items[:3]:
        print("    %-28s %9.2f руб.  (было %.0f, скидка: %s, на складе: %s)" % (i["name"], i["price_final"], i["price"], "да" if i["discount"] else "нет", i["stock_label"]))


def show_product():
    print("== /api/product, три товара")
    for pid in (1, 11, 29, 9999):
        status, data = get("/api/product?id=%d" % pid)
        if status != 200:
            print("  id=%d -> %d  %s" % (pid, status, data["error"]))
            continue
        sizes = ", ".join("%d(%d)" % (s["size"], s["quantity"]) for s in data["sizes"])
        print("  id=%d -> %d  %s, %s, цена %.2f, размеры: %s" % (pid, status, data["name"], data["manufacturer"], data["price_final"], sizes))


if __name__ == "__main__":
    try:
        show_login()
        show_products()
        show_product()
    except urllib.error.URLError as err:
        print("сервер не отвечает:", err.reason)
        sys.exit(1)
