"""Сравнивает количество записей во всех таблицах двух баз.  Запуск: python3 tools/compare_db.py shop.db restored.db"""
import sqlite3
import sys


def counts(path):
    conn = sqlite3.connect(path)
    names = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    result = {n: conn.execute("SELECT COUNT(*) FROM %s" % n).fetchone()[0] for n in names}
    conn.close()
    return result


def main():
    a_path, b_path = sys.argv[1], sys.argv[2]
    a, b = counts(a_path), counts(b_path)
    same = True
    print("%-15s %10s %10s" % ("таблица", a_path, b_path))
    for name in sorted(set(a) | set(b)):
        mark = "" if a.get(name) == b.get(name) else "   <- не совпало"
        same = same and not mark
        print("%-15s %10s %10s%s" % (name, a.get(name, "-"), b.get(name, "-"), mark))
    print("результат:", "количество записей совпадает" if same else "ЕСТЬ РАЗЛИЧИЯ")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
