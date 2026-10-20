import json

from db.database import BASE_DIR, DB_PATH, get_connection, init_db

TASKS_FILE = BASE_DIR / "data" / "tasks.json"


def load_json(filename):
    with open(filename, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn):
    """Очищает таблицы: задачи удаляются раньше категорий (внешний ключ)."""
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM categories")


def import_categories(conn, tasks):
    names = sorted({task["category"] for task in tasks})
    conn.executemany(
        "INSERT INTO categories (name) VALUES (?)",
        [(name,) for name in names],
    )


def import_tasks(conn, tasks):
    category_ids = {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM categories")
    }
    conn.executemany(
        """
        INSERT INTO tasks (
            id,
            name,
            category_id,
            deadline,
            is_completed
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                task["id"],
                task["name"],
                category_ids[task["category"]],
                task["deadline"],
                int(task.get("is_completed", False)),
            )
            for task in tasks
        ],
    )


def main(db_path=DB_PATH, tasks_file=TASKS_FILE):
    tasks = load_json(tasks_file)
    conn = get_connection(db_path)
    try:
        init_db(conn)
        clear_tables(conn)
        import_categories(conn, tasks)
        import_tasks(conn, tasks)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
