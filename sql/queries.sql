-- ==========================================
-- Трекер домашних задач: проверенные SQL-запросы
-- Запуск: sqlite3 data/tracker.sqlite < sql/queries.sql
-- В веб-приложении значения-примеры (категория, даты, id)
-- передаются параметрами "?".
-- ==========================================

-- ------------------------------------------
-- Выборка списков (SELECT)
-- ------------------------------------------

-- 1. Список всех категорий (страница «Задачи»: фильтр по категории)
SELECT
    id,
    name
FROM categories
ORDER BY name;

-- 2. Список всех задач по возрастанию дедлайна с постраничным
--    ограничением: первые 5 задач (LIMIT / OFFSET)
SELECT
    id,
    name,
    deadline,
    is_completed
FROM tasks
ORDER BY deadline, id
LIMIT 5 OFFSET 0;

-- ------------------------------------------
-- Фильтрация (WHERE)
-- ------------------------------------------

-- 3. Активные (невыполненные) задачи (страница «Активные задачи»)
SELECT
    id,
    name,
    deadline
FROM tasks
WHERE is_completed = 0
ORDER BY deadline;

-- 4. Невыполненные задачи со сроком не позже выбранной даты
--    (страница «Задачи по сроку»; дата передаётся параметром)
SELECT
    id,
    name,
    deadline
FROM tasks
WHERE is_completed = 0
  AND deadline <= '2026-11-01'
ORDER BY deadline;

-- 5. Просроченные задачи: не выполнены, дедлайн раньше сегодняшней даты
SELECT
    id,
    name,
    deadline
FROM tasks
WHERE is_completed = 0
  AND deadline < date('now', 'localtime')
ORDER BY deadline;

-- ------------------------------------------
-- Соединение таблиц (JOIN)
-- ------------------------------------------

-- 6. Полная информация о задачах: название категории вместо category_id
--    (страница «Задачи»; признак просрочки вычисляется в запросе)
SELECT
    tasks.id,
    tasks.name,
    categories.name AS category,
    tasks.deadline,
    tasks.is_completed,
    CASE
        WHEN tasks.is_completed = 0
         AND tasks.deadline < date('now', 'localtime') THEN 1
        ELSE 0
    END AS is_overdue
FROM tasks
JOIN categories ON tasks.category_id = categories.id
ORDER BY tasks.deadline, tasks.id;

-- 7. Одна задача по идентификатору (страница отдельной задачи)
SELECT
    tasks.id,
    tasks.name,
    categories.name AS category,
    tasks.deadline,
    tasks.is_completed
FROM tasks
JOIN categories ON tasks.category_id = categories.id
WHERE tasks.id = 1;

-- 8. Задачи выбранной категории (страница «Задачи»: фильтр по категории)
SELECT
    tasks.id,
    tasks.name,
    tasks.deadline
FROM tasks
JOIN categories ON tasks.category_id = categories.id
WHERE categories.name = 'Уборка'
ORDER BY tasks.deadline;

-- ------------------------------------------
-- Агрегатные функции
-- ------------------------------------------

-- 9. Количество активных задач
SELECT COUNT(*) AS active_count
FROM tasks
WHERE is_completed = 0;

-- 10. Общая сводка: всего, выполнено, просрочено
SELECT
    COUNT(*) AS total_count,
    COALESCE(SUM(is_completed), 0) AS completed_count,
    COALESCE(SUM(
        CASE
            WHEN is_completed = 0
             AND deadline < date('now', 'localtime') THEN 1
            ELSE 0
        END
    ), 0) AS overdue_count
FROM tasks;

-- 11. Ближайший и самый поздний дедлайн среди активных задач
SELECT
    MIN(deadline) AS nearest_deadline,
    MAX(deadline) AS latest_deadline
FROM tasks
WHERE is_completed = 0;

-- ------------------------------------------
-- Группировка (GROUP BY, HAVING)
-- ------------------------------------------

-- 12. Количество задач и выполненных задач по категориям
--     (LEFT JOIN: категории без задач не пропадают из результата)
SELECT
    categories.name AS category_name,
    COUNT(tasks.id) AS tasks_count,
    COALESCE(SUM(tasks.is_completed), 0) AS completed_count
FROM categories
LEFT JOIN tasks ON categories.id = tasks.category_id
GROUP BY categories.id, categories.name
ORDER BY tasks_count DESC, categories.name;

-- 13. Категории, в которых больше одной задачи (фильтрация групп: HAVING)
SELECT
    categories.name AS category_name,
    COUNT(tasks.id) AS tasks_count
FROM categories
JOIN tasks ON categories.id = tasks.category_id
GROUP BY categories.id, categories.name
HAVING COUNT(tasks.id) > 1
ORDER BY tasks_count DESC;

-- 14. Количество активных задач по категориям
SELECT
    categories.name AS category_name,
    COUNT(tasks.id) AS active_count
FROM tasks
JOIN categories ON tasks.category_id = categories.id
WHERE tasks.is_completed = 0
GROUP BY categories.id, categories.name
ORDER BY active_count DESC, categories.name;

-- 15. Ближайший дедлайн активных задач в каждой категории
SELECT
    categories.name AS category_name,
    MIN(tasks.deadline) AS nearest_deadline
FROM tasks
JOIN categories ON tasks.category_id = categories.id
WHERE tasks.is_completed = 0
GROUP BY categories.id, categories.name
ORDER BY nearest_deadline;

-- ------------------------------------------
-- Подзапрос
-- ------------------------------------------

-- 16. Категории, в которых нет невыполненных задач
SELECT
    id,
    name
FROM categories
WHERE id NOT IN (
    SELECT category_id
    FROM tasks
    WHERE is_completed = 0
)
ORDER BY name;
