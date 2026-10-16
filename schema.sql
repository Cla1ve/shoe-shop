-- Схема базы данных «Продажа обуви» (SQLite). Третья нормальная форма.
-- Проверка:  sqlite3 shop.db < schema.sql   и потом  .tables

PRAGMA foreign_keys = ON;

-- роли пользователей вынесены в отдельную таблицу, чтобы название роли не повторялось в каждой строке пользователя
CREATE TABLE IF NOT EXISTS Roles (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Users (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    login     TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role_id   INTEGER NOT NULL
              REFERENCES Roles(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS Categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Manufacturers (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS Sizes (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    value INTEGER NOT NULL UNIQUE CHECK (value BETWEEN 15 AND 60)
);

-- модель обуви; размеры и остатки лежат отдельно в Stock
CREATE TABLE IF NOT EXISTS Products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category_id     INTEGER NOT NULL
                    REFERENCES Categories(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    manufacturer_id INTEGER NOT NULL
                    REFERENCES Manufacturers(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    description     TEXT,
    composition     TEXT,
    price           REAL NOT NULL CHECK (price >= 0),
    image           TEXT,
    UNIQUE (name, manufacturer_id)
);

-- остатки: сколько пар модели есть в каждом размере
CREATE TABLE IF NOT EXISTS Stock (
    product_id INTEGER NOT NULL
               REFERENCES Products(id) ON UPDATE CASCADE ON DELETE CASCADE,
    size_id    INTEGER NOT NULL
               REFERENCES Sizes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity   INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    PRIMARY KEY (product_id, size_id)
);

-- external_number это номер заказа из файла Orders_import.xlsx, по нему повторный импорт не создаёт дубли
CREATE TABLE IF NOT EXISTS Orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    external_number INTEGER UNIQUE,
    order_date      TEXT NOT NULL,                       -- дата в виде ГГГГ-ММ-ДД
    client_id       INTEGER NOT NULL
                    REFERENCES Users(id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- цена записывается на момент заказа (unit_price), потому что цена товара потом может поменяться
CREATE TABLE IF NOT EXISTS OrderItems (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL
               REFERENCES Orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    product_id INTEGER NOT NULL
               REFERENCES Products(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    size_id    INTEGER NOT NULL
               REFERENCES Sizes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0)
);

-- индексы под частые запросы: фильтр каталога, список заказов, состав заказа, скидка по заказам за месяц
CREATE INDEX IF NOT EXISTS idx_users_role          ON Users(role_id);
CREATE INDEX IF NOT EXISTS idx_products_category   ON Products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_manuf      ON Products(manufacturer_id);
CREATE INDEX IF NOT EXISTS idx_products_name       ON Products(name);
CREATE INDEX IF NOT EXISTS idx_stock_size          ON Stock(size_id);
CREATE INDEX IF NOT EXISTS idx_orders_date         ON Orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_client       ON Orders(client_id);
CREATE INDEX IF NOT EXISTS idx_orderitems_order    ON OrderItems(order_id);
CREATE INDEX IF NOT EXISTS idx_orderitems_product  ON OrderItems(product_id);
