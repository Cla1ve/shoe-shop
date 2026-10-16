-- Восемь запросов к базе «Продажа обуви» (ПР 1.10).
-- Запуск с красивым выводом:  sqlite3 -header -column shop.db ".read queries.sql"

.print '--- 1. Товары дороже 10 000 руб. ---'
SELECT p.name AS "Модель", m.name AS "Производитель", p.price AS "Цена"
FROM Products p
JOIN Manufacturers m ON m.id = p.manufacturer_id
WHERE p.price > 10000
ORDER BY p.price DESC;

.print ''
.print '--- 2. Товары категории «Женская обувь» ---'
SELECT p.name AS "Модель", m.name AS "Производитель", p.price AS "Цена"
FROM Products p
JOIN Categories c    ON c.id = p.category_id
JOIN Manufacturers m ON m.id = p.manufacturer_id
WHERE c.name = 'Женская обувь'
ORDER BY p.name;

.print ''
.print '--- 3. Количество моделей у каждого производителя ---'
SELECT m.name AS "Производитель", COUNT(p.id) AS "Моделей"
FROM Manufacturers m
LEFT JOIN Products p ON p.manufacturer_id = m.id
GROUP BY m.id
ORDER BY "Моделей" DESC, m.name;

.print ''
.print '--- 4. Средняя цена по категориям ---'
SELECT c.name AS "Категория", COUNT(p.id) AS "Моделей", ROUND(AVG(p.price), 2) AS "Средняя цена"
FROM Categories c
JOIN Products p ON p.category_id = c.id
GROUP BY c.id
ORDER BY "Средняя цена" DESC;

.print ''
.print '--- 5. Товары, которых на складе меньше 3 пар (суммарно по всем размерам) ---'
SELECT p.name AS "Модель", m.name AS "Производитель", COALESCE(SUM(s.quantity), 0) AS "Всего пар"
FROM Products p
JOIN Manufacturers m ON m.id = p.manufacturer_id
LEFT JOIN Stock s    ON s.product_id = p.id
GROUP BY p.id
HAVING COALESCE(SUM(s.quantity), 0) < 3
ORDER BY "Всего пар", p.name;

.print ''
.print '--- 6. Товары без заказов в прошлом календарном месяце (скидка 25%) ---'
SELECT p.name AS "Модель", p.price AS "Цена", ROUND(p.price * 0.75, 2) AS "Цена со скидкой"
FROM Products p
WHERE p.id NOT IN (
    SELECT oi.product_id
    FROM OrderItems oi
    JOIN Orders o ON o.id = oi.order_id
    WHERE o.order_date >= date('now', 'start of month', '-1 month')
      AND o.order_date <  date('now', 'start of month')
)
ORDER BY p.name;

.print ''
.print '--- 7. Пять самых дорогих заказов с ФИО клиента ---'
SELECT o.external_number AS "Заказ", o.order_date AS "Дата", u.full_name AS "Клиент",
       SUM(oi.quantity * oi.unit_price) AS "Сумма"
FROM Orders o
JOIN Users u        ON u.id = o.client_id
JOIN OrderItems oi  ON oi.order_id = o.id
GROUP BY o.id
ORDER BY "Сумма" DESC
LIMIT 5;

.print ''
.print '--- 8. Размеры, которые есть на складе, но ни разу не заказывались ---'
SELECT sz.value AS "Размер", SUM(st.quantity) AS "На складе, пар"
FROM Sizes sz
JOIN Stock st ON st.size_id = sz.id AND st.quantity > 0
WHERE sz.id NOT IN (SELECT size_id FROM OrderItems)
GROUP BY sz.id
ORDER BY sz.value;
