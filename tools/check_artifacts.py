"""Проверка комплекта для сдачи (ПР 4.5): на месте ли все файлы из списка.

Запуск из корня проекта:  python3 tools/check_artifacts.py
"""
import glob
import os
import sys

CHECKS = [
    ("schema.sql: скрипт базы данных", "schema.sql"),
    ("shop.db или dump.sql: база с данными", ["shop.db", "dump.sql"]),
    ("create_db.py: создание базы", "create_db.py"),
    ("read_excel.py: чтение xlsx", "read_excel.py"),
    ("import_data.py: импорт данных", "import_data.py"),
    ("queries.sql: восемь запросов", "queries.sql"),
    ("server.py: сервер и API", "server.py"),
    ("static/index.html, app.js, style.css", ["static/index.html", "static/app.js", "static/style.css"]),
    ("static/uploads: картинки и заглушка", ["static/uploads/picture.png", "static/uploads/IMG_001.png"]),
    ("ER_diagram.pdf", "ER_diagram.pdf"),
    ("пять файлов импорта .xlsx", ["Products_import.xlsx", "Stock_Items_import.xlsx", "Sizes_import.xlsx", "Orders_import.xlsx", "Users_import.xlsx"]),
    ("errors_analysis.md", "errors_analysis.md"),
    ("README.md", "README.md"),
    (".gitignore", ".gitignore"),
]


def main():
    bad = 0
    for title, files in CHECKS:
        files = [files] if isinstance(files, str) else files
        # для пары shop.db / dump.sql достаточно любого из двух
        found = [f for f in files if os.path.exists(f)]
        ok = bool(found) if "или" in title else len(found) == len(files)
        print("[%s] %s" % ("ok" if ok else "НЕТ", title))
        bad += 0 if ok else 1
    print("картинок товаров в static/uploads:", len(glob.glob("static/uploads/IMG_*.png")))
    print("итог:", "все файлы на месте" if not bad else "не хватает файлов: %d" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
