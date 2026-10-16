"""Чтение файлов .xlsx без сторонних библиотек: xlsx это zip-архив с xml-файлами.

Что внутри архива, что нам нужно:
  xl/sharedStrings.xml       общий список всех строк (в ячейках лежат только номера строк из него)
  xl/worksheets/sheet1.xml   данные первого листа

Запуск:  python3 read_excel.py   (покажет первые 3 строки каждого из пяти файлов)
"""
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, timedelta

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILES = ["Products_import.xlsx", "Stock_Items_import.xlsx", "Sizes_import.xlsx", "Orders_import.xlsx", "Users_import.xlsx"]


def column_index(address):
    """Адрес ячейки в номер столбца с нуля: A1 -> 0, B7 -> 1, AA3 -> 26."""
    letters = re.match(r"[A-Z]+", address).group(0)
    number = 0
    for ch in letters:
        number = number * 26 + (ord(ch) - ord("A") + 1)
    return number - 1


def read_shared_strings(archive):
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    strings = []
    for si in root.findall(NS + "si"):
        # у обычной строки один тег <t>, у строки с разным форматированием несколько <r><t>, склеиваем всё
        strings.append("".join(t.text or "" for t in si.iter(NS + "t")))
    return strings


def convert_number(text):
    value = float(text)
    return int(value) if value.is_integer() else value


def read_xlsx(path):
    """Возвращает список строк листа, каждая строка это список значений (пустая ячейка = None)."""
    with zipfile.ZipFile(path) as archive:
        strings = read_shared_strings(archive)
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    rows = []
    for row in sheet.iter(NS + "row"):
        values = {}
        for cell in row.findall(NS + "c"):
            kind = cell.get("t")
            v = cell.find(NS + "v")
            if kind == "s" and v is not None:                  # строка из sharedStrings
                value = strings[int(v.text)]
            elif kind == "inlineStr":                          # строка прямо в ячейке
                value = "".join(t.text or "" for t in cell.iter(NS + "t"))
            elif kind in ("str", "e") and v is not None:
                value = v.text
            elif kind == "b" and v is not None:
                value = v.text == "1"
            elif v is not None and v.text not in (None, ""):
                value = convert_number(v.text)
            else:
                value = None
            values[column_index(cell.get("r"))] = value
        if not values:
            continue
        width = max(values) + 1
        rows.append([values.get(i) for i in range(width)])
    return rows


def excel_date(serial):
    """Дата в Excel хранится числом дней с 30.12.1899. Возвращает строку ГГГГ-ММ-ДД."""
    return (date(1899, 12, 30) + timedelta(days=int(serial))).isoformat()


def main():
    for name in FILES:
        path = os.path.join(BASE_DIR, name)
        try:
            rows = read_xlsx(path)
        except (OSError, KeyError, zipfile.BadZipFile) as err:
            print("%s: не удалось прочитать (%s)" % (name, err))
            continue
        print("=== %s: строк %d, столбцов %d" % (name, len(rows), len(rows[0]) if rows else 0))
        for row in rows[:3]:
            print("   ", row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
