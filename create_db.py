"""Создаёт базу данных shop.db из schema.sql (только встроенные модули Python).

Запуск:  python3 create_db.py            создать базу (если файл уже есть, остановиться)
         python3 create_db.py --force    пересоздать базу с нуля
"""
import argparse
import logging
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "shop.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
EXPECTED_TABLES = ["Categories", "Manufacturers", "OrderItems", "Orders", "Products", "Roles", "Sizes", "Stock", "Users"]

log = logging.getLogger("create_db")


def create_database(db_path=DB_PATH, schema_path=SCHEMA_PATH, force=False):
    """Создаёт файл базы и таблицы. Возвращает список созданных таблиц."""
    if os.path.exists(db_path):
        if not force:
            raise FileExistsError("файл %s уже есть, запустите с --force, чтобы пересоздать" % db_path)
        os.remove(db_path)
        log.info("старая база удалена")

    with open(schema_path, encoding="utf-8") as f:
        script = f.read()

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(script)
        conn.commit()
        log.info("схема применена из %s", os.path.basename(schema_path))
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]
    except sqlite3.Error:
        conn.rollback()
        log.exception("ошибка при создании базы")
        raise
    finally:
        conn.close()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    parser = argparse.ArgumentParser(description="Создание базы данных «Продажа обуви»")
    parser.add_argument("--force", action="store_true", help="пересоздать базу, если она уже есть")
    args = parser.parse_args()

    try:
        tables = create_database(force=args.force)
    except (OSError, sqlite3.Error) as err:
        log.error("не получилось: %s", err)
        return 1

    # проверяем результат: все ли нужные таблицы появились
    missing = [t for t in EXPECTED_TABLES if t not in tables]
    log.info("созданы таблицы (%d): %s", len(tables), ", ".join(tables))
    if missing:
        log.error("не хватает таблиц: %s", ", ".join(missing))
        return 1
    log.info("готово, база: %s", DB_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
