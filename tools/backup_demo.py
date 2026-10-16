"""Резервное копирование и восстановление базы (ПР 1.11): все четыре действия подряд, с проверкой.

Запуск из корня проекта:  python3 tools/backup_demo.py
Нужен клиент sqlite3 (на ROSA Linux ставится пакетом sqlite). Файл shop.db не меняется.

Что делает:
  1. резервная копия:   sqlite3 shop.db ".backup shop_backup.db"
  2. восстановление:    sqlite3 restored_from_backup.db ".restore shop_backup.db"
  3. дамп в SQL:        sqlite3 shop.db ".dump" > dump_check.sql
  4. разворачивание:    sqlite3 restored_from_dump.db < dump_check.sql
  и после каждого восстановления сравнивает количество записей с исходной базой.
"""
import os
import subprocess
import sys

SQLITE = "sqlite3"


def run(args, stdin_file=None, stdout_file=None):
    shown = SQLITE + " " + " ".join('"%s"' % a if " " in a or a.startswith(".") else a for a in args)
    if stdin_file:
        shown += " < " + stdin_file
    if stdout_file:
        shown += " > " + stdout_file
    print("$", shown)
    stdin = open(stdin_file, "rb") if stdin_file else None
    stdout = open(stdout_file, "wb") if stdout_file else None
    try:
        result = subprocess.run([SQLITE] + args, stdin=stdin, stdout=stdout)
    finally:
        for f in (stdin, stdout):
            if f:
                f.close()
    if result.returncode != 0:
        print("команда завершилась с ошибкой", result.returncode)
        sys.exit(1)


def compare(a, b):
    result = subprocess.run([sys.executable, os.path.join("tools", "compare_db.py"), a, b])
    return result.returncode == 0


def main():
    if not os.path.exists("shop.db"):
        print("нет shop.db, запустите из корня проекта после import_data.py")
        return 1
    for name in ("shop_backup.db", "restored_from_backup.db", "restored_from_dump.db", "dump_check.sql"):
        if os.path.exists(name):
            os.remove(name)

    print("--- 1. резервная копия")
    run(["shop.db", ".backup shop_backup.db"])
    print("   создан shop_backup.db, %d байт" % os.path.getsize("shop_backup.db"))

    print("\n--- 2. восстановление из копии")
    run(["restored_from_backup.db", ".restore shop_backup.db"])
    ok1 = compare("shop.db", "restored_from_backup.db")

    print("\n--- 3. дамп в SQL")
    run(["shop.db", ".dump"], stdout_file="dump_check.sql")
    print("   создан dump_check.sql, %d байт" % os.path.getsize("dump_check.sql"))

    print("\n--- 4. разворачивание дампа в чистую базу")
    run(["restored_from_dump.db"], stdin_file="dump_check.sql")
    ok2 = compare("shop.db", "restored_from_dump.db")

    for name in ("restored_from_backup.db", "restored_from_dump.db", "dump_check.sql"):
        os.remove(name)
    print("\nитог:", "обе проверки пройдены" if ok1 and ok2 else "ЕСТЬ ОШИБКИ")
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
