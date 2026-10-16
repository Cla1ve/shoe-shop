# Магазин обуви

Учебный проект по МДК 04.01: база данных, сервер и веб-приложение для компании по продаже обуви.

## Запуск

```
python3 create_db.py
python3 import_data.py
python3 server.py
```

Сервер запускается на http://localhost:8000.

## API

| Метод | Адрес | Что делает |
|---|---|---|
| GET | `/api/login?login=...` | вход по логину, возвращает id, ФИО и роль |
| GET | `/api/categories` | список категорий |
| GET | `/api/products?category=&search=&sort=` | каталог с ценой со скидкой и остатками |
| GET | `/api/product?id=N` | карточка товара с размерами |
| POST | `/api/order/create` | оформление заказа, списание со склада |
| GET | `/api/orders` | список заказов (менеджер, администратор) |

Сервер написан на встроенных модулях Python (`http.server`, `sqlite3`).
