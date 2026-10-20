-- ==========================================
-- Трекер домашних задач: структура базы данных
-- ==========================================

-- Категории задач (Уборка, Покупки, Ремонт, ...)
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Задачи; каждая задача относится к одной категории
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    deadline TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0
        CHECK (is_completed IN (0, 1)),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
