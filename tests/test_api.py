"""Тесты API магазина (только unittest и стандартная библиотека).

Запуск из корня проекта:  python3 -m unittest discover -s tests -v
Тесты создают свою временную базу из xlsx-файлов, рабочий shop.db не трогают.
"""
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import create_db      # noqa: E402
import import_data    # noqa: E402
import server         # noqa: E402


class ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.tmp, "test.db")
        create_db.create_database(cls.db_path)
        import_data.DB_PATH = cls.db_path
        import_data.main()
        server.DB_PATH = cls.db_path
        os.environ["SHOP_TODAY"] = "2026-10-16"            # прошлый месяц = сентябрь 2026
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.ShopHandler)
        cls.base = "http://127.0.0.1:%d" % cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        os.environ.pop("SHOP_TODAY", None)

    def call(self, method, path, body=None, login=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if login:
            req.add_header("X-Login", login)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))

    def get(self, path, login=None):
        return self.call("GET", path, login=login)

    def post(self, path, body, login=None):
        return self.call("POST", path, body, login)


class LoginTests(ApiTestCase):
    def test_login_ok(self):
        status, data = self.get("/api/login?login=isivanov")
        self.assertEqual(status, 200)
        self.assertEqual(data["role"], "Клиент")

    def test_login_roles(self):
        roles = {login: self.get("/api/login?login=" + login)[1]["role"] for login in ("masokolova", "anpetrov", "dovolkov")}
        self.assertEqual(roles, {"masokolova": "Администратор", "anpetrov": "Менеджер", "dovolkov": "Клиент"})

    def test_login_not_found(self):
        self.assertEqual(self.get("/api/login?login=nobody")[0], 404)

    def test_login_empty(self):
        self.assertEqual(self.get("/api/login")[0], 400)


class CatalogTests(ApiTestCase):
    def test_all_products(self):
        status, items = self.get("/api/products")
        self.assertEqual((status, len(items)), (200, 33))

    def test_category_filter(self):
        _s, cats = self.get("/api/categories")
        women = [c["id"] for c in cats if c["name"] == "Женская обувь"][0]
        _s, items = self.get("/api/products?category=%d" % women)
        self.assertEqual(len(items), 10)
        self.assertTrue(all(i["category"] == "Женская обувь" for i in items))

    def test_search_is_case_insensitive_for_cyrillic(self):
        _s, items = self.get("/api/products?search=" + urllib.request.quote("ТУФЛИ"))
        names = [i["name"] for i in items]
        self.assertIn("Туфли Derby", names)
        self.assertTrue(all("туфли" in n.lower() for n in names))

    def test_sort_by_final_price(self):
        _s, asc = self.get("/api/products?sort=price_asc")
        prices = [i["price_final"] for i in asc]
        self.assertEqual(prices, sorted(prices))
        _s, desc = self.get("/api/products?sort=price_desc")
        self.assertEqual([i["price_final"] for i in desc], sorted(prices, reverse=True))

    def test_bad_sort(self):
        self.assertEqual(self.get("/api/products?sort=abc")[0], 400)

    def test_discount_rule(self):
        # в сентябре 2026 заказывали, например, «Ботинки Chelsea Man», а «Балетки Soft Flat» нет
        _s, items = self.get("/api/products")
        by_name = {i["name"]: i for i in items}
        flat = by_name["Балетки Soft Flat"]
        self.assertTrue(flat["discount"])
        self.assertEqual(flat["price_final"], round(flat["price"] * 0.75, 2))
        self.assertTrue(any(not i["discount"] for i in items), "должны быть и товары без скидки")

    def test_many_few_and_low_stock(self):
        _s, items = self.get("/api/products")
        for i in items:
            self.assertEqual(i["stock_label"], "много" if i["total_quantity"] > 5 else "мало")
            self.assertEqual(i["low_stock"], i["total_quantity"] <= 3)

    def test_product_card_sizes_sorted(self):
        status, p = self.get("/api/product?id=1")
        self.assertEqual(status, 200)
        sizes = [s["size"] for s in p["sizes"]]
        self.assertEqual(sizes, sorted(sizes))
        self.assertEqual(sum(s["quantity"] for s in p["sizes"]), p["total_quantity"])

    def test_product_errors(self):
        self.assertEqual(self.get("/api/product?id=9999")[0], 404)
        self.assertEqual(self.get("/api/product?id=abc")[0], 400)


class OrderTests(ApiTestCase):
    def first_size(self, product_id):
        return self.get("/api/product?id=%d" % product_id)[1]["sizes"][0]

    def test_client_cannot_see_orders(self):
        self.assertEqual(self.get("/api/orders")[0], 401)
        self.assertEqual(self.get("/api/orders", login="isivanov")[0], 403)

    def test_manager_sees_orders_with_totals(self):
        status, orders = self.get("/api/orders", login="anpetrov")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(orders), 10)
        status, order = self.get("/api/order?id=%d" % orders[0]["id"], login="anpetrov")
        self.assertEqual(round(sum(i["sum"] for i in order["items"]), 2), order["total"])

    def test_create_order_reduces_stock(self):
        size = self.first_size(2)
        before = size["quantity"]
        status, data = self.post("/api/order/create", {"items": [{"product_id": 2, "size_id": size["size_id"], "quantity": 1}]}, login="dovolkov")
        self.assertEqual(status, 200, data)
        after = self.first_size(2)["quantity"]
        self.assertEqual(after, before - 1)
        status, order = self.get("/api/order?id=%d" % data["order_id"], login="anpetrov")
        self.assertEqual(order["order_date"], "2026-10-16")
        self.assertEqual(order["client"], "Волков Дмитрий Олегович")

    def test_not_enough_stock(self):
        size = self.first_size(3)
        status, data = self.post("/api/order/create", {"items": [{"product_id": 3, "size_id": size["size_id"], "quantity": size["quantity"] + 1}]}, login="dovolkov")
        self.assertEqual(status, 409)
        self.assertEqual(self.first_size(3)["quantity"], size["quantity"])        # склад не изменился

    def test_validation(self):
        self.assertEqual(self.post("/api/order/create", {"items": []}, login="dovolkov")[0], 400)
        self.assertEqual(self.post("/api/order/create", {"items": [{"product_id": 1, "size_id": 1, "quantity": -2}]}, login="dovolkov")[0], 400)
        self.assertEqual(self.post("/api/order/create", {"items": [{"product_id": 1, "size_id": 1, "quantity": 1}]})[0], 401)

    def test_client_cannot_order_for_someone_else(self):
        size = self.first_size(4)
        status, _d = self.post("/api/order/create", {"client_id": 5, "items": [{"product_id": 4, "size_id": size["size_id"], "quantity": 1}]}, login="dovolkov")
        self.assertEqual(status, 403)

    def test_manager_creates_order_for_client(self):
        size = self.first_size(5)
        _s, users = self.get("/api/users", login="anpetrov")
        client = [u for u in users if u["login"] == "edsmirnova"][0]
        status, data = self.post("/api/order/create", {"client_id": client["id"], "items": [{"product_id": 5, "size_id": size["size_id"], "quantity": 1}]}, login="anpetrov")
        self.assertEqual(status, 200, data)
        _s, order = self.get("/api/order?id=%d" % data["order_id"], login="anpetrov")
        self.assertEqual(order["client"], client["full_name"])

    def test_admin_edit_returns_stock(self):
        size = self.first_size(6)
        _s, data = self.post("/api/order/create", {"items": [
            {"product_id": 6, "size_id": size["size_id"], "quantity": 2}, {"product_id": 7, "size_id": self.first_size(7)["size_id"], "quantity": 1}]}, login="dovolkov")
        quantity_after_order = self.first_size(6)["quantity"]
        _s, order = self.get("/api/order?id=%d" % data["order_id"], login="anpetrov")
        item_id = order["items"][0]["item_id"]
        # менеджер менять заказы не может
        self.assertEqual(self.post("/api/order/update", {"id": data["order_id"], "remove_item_ids": [item_id]}, login="anpetrov")[0], 403)
        status, result = self.post("/api/order/update", {"id": data["order_id"], "order_date": "2026-09-30", "remove_item_ids": [item_id]}, login="masokolova")
        self.assertEqual(status, 200, result)
        self.assertEqual(result["returned_to_stock"], 2)
        self.assertEqual(result["order"]["order_date"], "2026-09-30")
        self.assertEqual(len(result["order"]["items"]), 1)
        self.assertEqual(self.first_size(6)["quantity"], quantity_after_order + 2)

    def test_admin_update_bad_date(self):
        self.assertEqual(self.post("/api/order/update", {"id": 1, "order_date": "31.12.2026"}, login="masokolova")[0], 400)
        self.assertEqual(self.post("/api/order/update", {"id": 1, "order_date": "2026-02-31"}, login="masokolova")[0], 400)


class StaticTests(ApiTestCase):
    def test_traversal_blocked(self):
        try:
            urllib.request.urlopen(self.base + "/static/../server.py")
            self.fail("файл вне static не должен отдаваться")
        except urllib.error.HTTPError as err:
            self.assertEqual(err.code, 404)

    def test_head_request(self):
        req = urllib.request.Request(self.base + "/static/style.css", method="HEAD")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), b"")

    def test_bad_json(self):
        req = urllib.request.Request(self.base + "/api/order/create", data=b"{oops", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req)
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()
