# Конспект: поиск информации в документации (ПР 3.4)

Искал в официальной документации Python 3.8 (docs.python.org/3.8) и на MDN Web Docs. Читал разделы про то, что нужно для проекта, и выписывал главное. Скриншоты страниц лежат в `docs/screenshots` (файлы `3.4_...`).

## Python 3.8

### http.server (docs.python.org/3.8/library/http.server.html)

- Сервер создаётся так: `httpd = HTTPServer(адрес, КлассОбработчик)`, потом `httpd.serve_forever()`.
- `ThreadingHTTPServer` появился в Python 3.7. Он такой же, как `HTTPServer`, но каждый запрос обрабатывает в отдельном потоке. В документации сказано, что это полезно, потому что браузеры заранее открывают соединения, и обычный `HTTPServer` на них может зависнуть.
- Обработчик наследуется от `BaseHTTPRequestHandler`. Для метода GET пишется `do_GET`, для POST `do_POST`, для HEAD `do_HEAD`. Если метода нет, сервер отвечает 501.
- Ответ собирается так: `send_response(код)`, потом `send_header(имя, значение)`, потом обязательно `end_headers()` (с версии 3.3 заголовки копятся в буфере и сами не отправляются). Тело пишется в `self.wfile`.
- Тело запроса читается из `self.rfile`, длина берётся из заголовка `Content-Length`.

**Где применил:** `server.py`, класс `ShopHandler`, методы `do_GET`, `do_POST`, `do_HEAD`, `send_json`, `send_static`. Нашёл и исправил ошибку: без `do_HEAD` сервер отвечал 501 (ПР 2.11).

### sqlite3 (docs.python.org/3.8/library/sqlite3.html)

- `sqlite3.connect('файл.db')` возвращает соединение. Есть имя `:memory:` для базы в памяти.
- `cursor.execute(sql, параметры)`: значения надо подставлять через `?`, а не собирать строку через `%` или `+`. В документации прямо написано, что сборка запроса из строк небезопасна (SQL-инъекции).
- `executescript(скрипт)` выполняет сразу много команд. Использую в `create_db.py` для `schema.sql`.
- `commit()` сохраняет изменения, без него они пропадут, `rollback()` отменяет.
- `row_factory = sqlite3.Row` позволяет обращаться к столбцам по имени (`row["price"]`).
- `sqlite3.IntegrityError` возникает при нарушении ограничений (UNIQUE, внешний ключ), это подкласс `DatabaseError`.

**Где применил:** `create_db.py` (`executescript`), `import_data.py` (commit в конце и rollback при ошибке), `server.py` (`row_factory`, запросы с `?`, перехват `sqlite3.Error`).

### zipfile (docs.python.org/3.8/library/zipfile.html)

- `ZipFile(путь)` открывает архив, удобно через `with`.
- `namelist()` возвращает список имён файлов внутри архива.
- `read(имя)` возвращает содержимое файла как `bytes`.
- Файл `.xlsx` это обычный zip, внутри лежат xml-файлы.

**Где применил:** `read_excel.py`: читаю `xl/sharedStrings.xml` и `xl/worksheets/sheet1.xml`, разбираю их через `xml.etree.ElementTree`.

## MDN Web Docs (developer.mozilla.org)

### fetch()

- `fetch(url, опции)` возвращает `Promise<Response>`. В опциях можно задать `method`, `headers`, `body`.
- Главное, что я оттуда вынес: промис **не отклоняется при HTTP-ошибках**. Ответ 404 или 500 это не сетевая ошибка, промис выполняется нормально, а свойство `response.ok` будет `false`. Отклоняется он только при настоящем сбое сети.

**Где применил:** функция `api()` в `app.js`. Сбой сети ловлю в `try/catch` и показываю «Нет связи с сервером», а для кодов 4xx и 5xx проверяю `response.ok` и показываю текст ошибки из ответа сервера.

### addEventListener()

- `элемент.addEventListener(тип, обработчик, опции)` вешает обработчик на событие. Можно повесить несколько обработчиков на одно событие, это его плюс перед `onclick`.
- Цели: элементы, `document`, `window`.

**Где применил:** фильтры каталога (`change`, `input`), закрытие окон (`mousedown`, `keydown` для Escape), отправка формы входа (`submit`), кнопки в таблицах заказов.

### JSON.stringify()

- Превращает значение JavaScript в строку JSON. Второй параметр `replacer` позволяет отфильтровать поля, третий задаёт отступы.

**Где применил:** тело POST-запросов (`/api/order/create`, `/api/order/update`) и запоминание корзины и пользователя в `localStorage`.
