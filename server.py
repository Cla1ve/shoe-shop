"""Сервер магазина обуви: отдаёт страницы из static/ и работает как JSON API.
Использует только встроенные модули Python 3.8 (http.server, sqlite3, json, mimetypes).

Запуск:  python3 server.py        (адрес http://localhost:8000, порт можно сменить: PORT=8080 python3 server.py)

Как работает вход: по заданию пароля нет, пользователь вводит логин из списка. Браузер запоминает логин
и отправляет его в заголовке X-Login. По этому логину сервер сам находит роль в базе и решает,
что можно (менеджеру и администратору можно смотреть заказы, только администратору можно их менять).
"""
import json
import logging
import mimetypes
import os
import re
import sqlite3
import sys
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shop.db")
STATIC_DIR = os.path.join(BASE_DIR, "static")
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))

DISCOUNT = 0.25            # скидка, если в прошлом месяце не было заказов на модель
MANY_FROM = 6              # на складе больше 5 пар -> «много», иначе «мало»
LOW_STOCK = 3              # остаток 3 пары и меньше подсвечиваем в каталоге
ROLE_CLIENT, ROLE_MANAGER, ROLE_ADMIN = "Клиент", "Менеджер", "Администратор"

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")
log = logging.getLogger("server")


class ApiError(Exception):
    """Ошибка, которую нужно показать пользователю: код ответа и понятный текст."""

    def __init__(self, status, message):
        Exception.__init__(self, message)
        self.status = status
        self.message = message


# ---------- работа с базой ----------

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def today():
    """Сегодняшняя дата. Переменная SHOP_TODAY=ГГГГ-ММ-ДД нужна, чтобы проверять скидку на любую дату."""
    fixed = os.environ.get("SHOP_TODAY")
    return datetime.strptime(fixed, "%Y-%m-%d").date() if fixed else date.today()


def previous_month_range(day):
    """Границы прошлого календарного месяца: [первый день прошлого месяца, первый день этого)."""
    first_this = day.replace(day=1)
    if first_this.month == 1:
        first_prev = first_this.replace(year=first_this.year - 1, month=12)
    else:
        first_prev = first_this.replace(month=first_this.month - 1)
    return first_prev.isoformat(), first_this.isoformat()


def products_ordered_last_month(conn):
    """Множество id моделей, на которые были заказы в прошлом месяце."""
    start, end = previous_month_range(today())
    rows = conn.execute(
        """SELECT DISTINCT oi.product_id FROM OrderItems oi JOIN Orders o ON o.id = oi.order_id
           WHERE o.order_date >= ? AND o.order_date < ?""", (start, end)).fetchall()
    return {r["product_id"] for r in rows}


def final_price(price, ordered_last_month):
    """Цена со скидкой 25%, если заказов в прошлом месяце не было. Округляем до копеек."""
    if ordered_last_month:
        return round(price, 2), False
    return round(price * (1 - DISCOUNT), 2), True


def stock_label(total):
    return "много" if total >= MANY_FROM else "мало"


def product_dict(row, ordered):
    price_final, has_discount = final_price(row["price"], row["id"] in ordered)
    total = row["total_quantity"] or 0
    return {
        "id": row["id"], "name": row["name"], "category": row["category"], "manufacturer": row["manufacturer"],
        "description": row["description"] or "", "composition": row["composition"] or "",
        "price": row["price"], "price_final": price_final, "discount": has_discount,
        "image": row["image"] or "", "total_quantity": total, "stock_label": stock_label(total),
        "low_stock": total <= LOW_STOCK,
    }


PRODUCT_SELECT = """
    SELECT p.id, p.name, c.name AS category, m.name AS manufacturer, p.description, p.composition, p.price, p.image,
           COALESCE((SELECT SUM(s.quantity) FROM Stock s WHERE s.product_id = p.id), 0) AS total_quantity
    FROM Products p
    JOIN Categories c    ON c.id = p.category_id
    JOIN Manufacturers m ON m.id = p.manufacturer_id
"""


# ---------- обработчики API ----------

def api_login(conn, user, query, body):
    login = (query.get("login", [""])[0]).strip()
    if not login:
        raise ApiError(400, "Введите логин")
    row = conn.execute(
        "SELECT u.id, u.login, u.full_name, r.name AS role FROM Users u JOIN Roles r ON r.id = u.role_id WHERE u.login = ?",
        (login,)).fetchone()
    if row is None:
        raise ApiError(404, "Пользователь с таким логином не найден")
    return dict(row)


def api_categories(conn, user, query, body):
    return [dict(r) for r in conn.execute("SELECT id, name FROM Categories ORDER BY name")]


def api_products(conn, user, query, body):
    category = query.get("category", [""])[0].strip()
    search = query.get("search", [""])[0].strip().lower()
    sort = query.get("sort", [""])[0].strip()
    if sort not in ("", "price_asc", "price_desc"):
        raise ApiError(400, "Неизвестный вариант сортировки")

    sql, params = PRODUCT_SELECT, []
    if category:
        if category.isdigit():
            sql += " WHERE p.category_id = ?"
        else:
            sql += " WHERE c.name = ?"
        params.append(int(category) if category.isdigit() else category)
    sql += " ORDER BY p.name"
    ordered = products_ordered_last_month(conn)
    items = [product_dict(r, ordered) for r in conn.execute(sql, params)]

    if search:
        # поиск без учёта регистра делаем в Python: в SQLite LIKE не понимает заглавные кириллические буквы
        items = [i for i in items if search in (i["name"] + " " + i["manufacturer"] + " " + i["category"] + " " + i["description"]).lower()]
    if sort:
        items.sort(key=lambda i: i["price_final"], reverse=(sort == "price_desc"))
    return items


def api_product(conn, user, query, body):
    raw = query.get("id", [""])[0]
    if not raw.isdigit():
        raise ApiError(400, "Нужен числовой параметр id")
    row = conn.execute(PRODUCT_SELECT + " WHERE p.id = ?", (int(raw),)).fetchone()
    if row is None:
        raise ApiError(404, "Товар не найден")
    result = product_dict(row, products_ordered_last_month(conn))
    sizes = conn.execute(
        """SELECT sz.id AS size_id, sz.value AS size, s.quantity FROM Stock s JOIN Sizes sz ON sz.id = s.size_id
           WHERE s.product_id = ? ORDER BY sz.value""", (row["id"],)).fetchall()
    result["sizes"] = [dict(s) for s in sizes]
    return result


def require_role(user, *roles):
    if user is None:
        raise ApiError(401, "Сначала войдите в систему")
    if user["role"] not in roles:
        raise ApiError(403, "Недостаточно прав для этого действия")


def parse_positive_int(value, what):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ApiError(400, "%s: нужно целое число" % what)
    if number <= 0:
        raise ApiError(400, "%s: число должно быть больше нуля" % what)
    return number


def api_order_create(conn, user, query, body):
    """Создаёт заказ и списывает товар со склада одной транзакцией.
    Клиент оформляет заказ для себя, менеджер и администратор могут указать client_id (ручной заказ)."""
    require_role(user, ROLE_CLIENT, ROLE_MANAGER, ROLE_ADMIN)
    items = body.get("items")
    if not isinstance(items, list) or not items:
        raise ApiError(400, "В заказе нет товаров")

    client_id = user["id"]
    if body.get("client_id") is not None:
        if user["role"] == ROLE_CLIENT:
            raise ApiError(403, "Клиент может оформить заказ только для себя")
        client_id = parse_positive_int(body["client_id"], "Клиент")
        if conn.execute("SELECT 1 FROM Users WHERE id = ?", (client_id,)).fetchone() is None:
            raise ApiError(404, "Клиент не найден")

    ordered = products_ordered_last_month(conn)
    conn.execute("BEGIN IMMEDIATE")           # блокируем базу, чтобы два заказа не продали одну и ту же пару
    try:
        cur = conn.execute("INSERT INTO Orders (order_date, client_id) VALUES (?, ?)", (today().isoformat(), client_id))
        order_id = cur.lastrowid
        total = 0.0
        for item in items:
            product_id = parse_positive_int(item.get("product_id"), "Товар")
            size_id = parse_positive_int(item.get("size_id"), "Размер")
            quantity = parse_positive_int(item.get("quantity"), "Количество")
            product = conn.execute("SELECT id, name, price FROM Products WHERE id = ?", (product_id,)).fetchone()
            if product is None:
                raise ApiError(404, "Товар с номером %d не найден" % product_id)
            stock = conn.execute("SELECT quantity FROM Stock WHERE product_id = ? AND size_id = ?", (product_id, size_id)).fetchone()
            if stock is None or stock["quantity"] < quantity:
                available = stock["quantity"] if stock else 0
                raise ApiError(409, "Не хватает товара «%s»: на складе %d, нужно %d" % (product["name"], available, quantity))
            price, _discount = final_price(product["price"], product_id in ordered)
            conn.execute("UPDATE Stock SET quantity = quantity - ? WHERE product_id = ? AND size_id = ?", (quantity, product_id, size_id))
            conn.execute("INSERT INTO OrderItems (order_id, product_id, size_id, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
                         (order_id, product_id, size_id, quantity, price))
            total += price * quantity
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {"order_id": order_id, "total": round(total, 2)}


def api_orders(conn, user, query, body):
    require_role(user, ROLE_MANAGER, ROLE_ADMIN)
    rows = conn.execute(
        """SELECT o.id, o.order_date, u.full_name AS client, COUNT(oi.id) AS items_count,
                  COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total
           FROM Orders o JOIN Users u ON u.id = o.client_id LEFT JOIN OrderItems oi ON oi.order_id = o.id
           GROUP BY o.id ORDER BY o.order_date DESC, o.id DESC""").fetchall()
    return [dict(r) for r in rows]


def load_order(conn, order_id):
    order = conn.execute(
        "SELECT o.id, o.order_date, o.client_id, u.full_name AS client FROM Orders o JOIN Users u ON u.id = o.client_id WHERE o.id = ?",
        (order_id,)).fetchone()
    if order is None:
        raise ApiError(404, "Заказ не найден")
    items = conn.execute(
        """SELECT oi.id AS item_id, p.name, m.name AS manufacturer, sz.value AS size, oi.quantity, oi.unit_price,
                  oi.quantity * oi.unit_price AS sum
           FROM OrderItems oi JOIN Products p ON p.id = oi.product_id JOIN Manufacturers m ON m.id = p.manufacturer_id
           JOIN Sizes sz ON sz.id = oi.size_id WHERE oi.order_id = ? ORDER BY oi.id""", (order_id,)).fetchall()
    result = dict(order)
    result["items"] = [dict(i) for i in items]
    result["total"] = round(sum(i["sum"] for i in result["items"]), 2)
    return result


def api_order(conn, user, query, body):
    require_role(user, ROLE_MANAGER, ROLE_ADMIN)
    raw = query.get("id", [""])[0]
    if not raw.isdigit():
        raise ApiError(400, "Нужен числовой параметр id")
    return load_order(conn, int(raw))


def api_order_update(conn, user, query, body):
    """Изменение заказа администратором: новая дата и удаление позиций. Удалённый товар возвращается на склад."""
    require_role(user, ROLE_ADMIN)
    order_id = parse_positive_int(body.get("id"), "Номер заказа")
    new_date = body.get("order_date")
    remove_ids = body.get("remove_item_ids") or []
    if not isinstance(remove_ids, list):
        raise ApiError(400, "remove_item_ids должен быть списком")
    if new_date is not None:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(new_date)):
            raise ApiError(400, "Дата должна быть в формате ГГГГ-ММ-ДД")
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            raise ApiError(400, "Такой даты не существует")

    conn.execute("BEGIN IMMEDIATE")
    try:
        if conn.execute("SELECT 1 FROM Orders WHERE id = ?", (order_id,)).fetchone() is None:
            raise ApiError(404, "Заказ не найден")
        if new_date is not None:
            conn.execute("UPDATE Orders SET order_date = ? WHERE id = ?", (new_date, order_id))
        returned = 0
        for item_id in remove_ids:
            item = conn.execute("SELECT product_id, size_id, quantity FROM OrderItems WHERE id = ? AND order_id = ?",
                                (parse_positive_int(item_id, "Позиция"), order_id)).fetchone()
            if item is None:
                raise ApiError(404, "Позиция %s не найдена в этом заказе" % item_id)
            # возврат на склад: если строки остатка для размера уже нет, создаём её
            conn.execute(
                """INSERT INTO Stock (product_id, size_id, quantity) VALUES (?, ?, ?)
                   ON CONFLICT(product_id, size_id) DO UPDATE SET quantity = quantity + excluded.quantity""",
                (item["product_id"], item["size_id"], item["quantity"]))
            conn.execute("DELETE FROM OrderItems WHERE id = ?", (item_id,))
            returned += item["quantity"]
        deleted = False
        if conn.execute("SELECT COUNT(*) FROM OrderItems WHERE order_id = ?", (order_id,)).fetchone()[0] == 0:
            conn.execute("DELETE FROM Orders WHERE id = ?", (order_id,))      # заказ без позиций не нужен
            deleted = True
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    result = {"deleted": deleted, "returned_to_stock": returned}
    if not deleted:
        result["order"] = load_order(conn, order_id)
    return result


def api_users(conn, user, query, body):
    require_role(user, ROLE_MANAGER, ROLE_ADMIN)
    rows = conn.execute(
        "SELECT u.id, u.login, u.full_name, r.name AS role FROM Users u JOIN Roles r ON r.id = u.role_id ORDER BY u.full_name")
    return [dict(r) for r in rows]


GET_ROUTES = {
    "/api/login": api_login, "/api/categories": api_categories, "/api/products": api_products,
    "/api/product": api_product, "/api/orders": api_orders, "/api/order": api_order, "/api/users": api_users,
}
POST_ROUTES = {"/api/order/create": api_order_create, "/api/order/update": api_order_update}


# ---------- http-сервер ----------

class ShopHandler(BaseHTTPRequestHandler):
    server_version = "ShopServer/1.0"

    def log_message(self, fmt, *args):
        log.info("%s %s", self.address_string(), fmt % args)

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def current_user(self, conn):
        login = self.headers.get("X-Login")
        if not login:
            return None
        row = conn.execute(
            "SELECT u.id, u.login, u.full_name, r.name AS role FROM Users u JOIN Roles r ON r.id = u.role_id WHERE u.login = ?",
            (login,)).fetchone()
        return dict(row) if row else None

    def handle_api(self, routes, body):
        parsed = urlparse(self.path)
        handler = routes.get(parsed.path)
        if handler is None:
            self.send_json(404, {"error": "Такого адреса нет: " + parsed.path})
            return
        conn = connect()
        try:
            result = handler(conn, self.current_user(conn), parse_qs(parsed.query), body)
            self.send_json(200, result)
        except ApiError as err:
            self.send_json(err.status, {"error": err.message})
        except sqlite3.Error:
            log.exception("ошибка базы данных")
            self.send_json(500, {"error": "Ошибка базы данных, попробуйте позже"})
        except Exception:
            log.exception("необработанная ошибка")
            self.send_json(500, {"error": "Внутренняя ошибка сервера"})
        finally:
            conn.close()

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/api/"):
            self.handle_api(GET_ROUTES, {})
        else:
            self.send_static(path)

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in POST_ROUTES:
            self.send_json(404, {"error": "Такого адреса нет: " + path})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            body = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(body, dict):
                raise ValueError("ожидался JSON-объект")
        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {"error": "Тело запроса должно быть корректным JSON"})
            return
        self.handle_api(POST_ROUTES, body)

    def send_static(self, url_path):
        """Отдаёт файл из папки static. Адрес / открывает index.html."""
        if url_path in ("", "/"):
            url_path = "/index.html"
        if url_path.startswith("/static/"):
            url_path = url_path[len("/static"):]
        full = os.path.realpath(os.path.join(STATIC_DIR, url_path.lstrip("/")))
        # защита от адресов вида /../server.py: файл должен лежать внутри static
        if not full.startswith(os.path.realpath(STATIC_DIR) + os.sep) or not os.path.isfile(full):
            self.send_json(404, {"error": "Файл не найден"})
            return
        mime, _enc = mimetypes.guess_type(full)
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", (mime or "application/octet-stream") + ("; charset=utf-8" if (mime or "").startswith("text/") or mime == "application/javascript" else ""))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    if not os.path.exists(DB_PATH):
        log.error("нет файла shop.db. Сначала: python3 create_db.py и python3 import_data.py")
        return 1
    server = ThreadingHTTPServer((HOST, PORT), ShopHandler)
    log.info("сервер запущен: http://localhost:%d (остановить: Ctrl+C)", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("останавливаю сервер")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
