import json
import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import BASE_DIR, DB_PATH, get_connection  # noqa: E402
from db.import_json import TASKS_FILE, main  # noqa: E402

QUERIES_FILE = BASE_DIR / "sql" / "queries.sql"


def load_tasks_json():
    with open(TASKS_FILE, encoding="utf-8") as file:
        return json.load(file)


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.sqlite"
    main(db_path=db_path)
    connection = get_connection(db_path)
    yield connection
    connection.close()


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_schema_creates_tables(conn):
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"categories", "tasks"} <= tables


def test_import_transfers_all_tasks(conn):
    tasks = load_tasks_json()
    categories = {task["category"] for task in tasks}
    assert count(conn, "tasks") == len(tasks)
    assert count(conn, "categories") == len(categories)


def test_import_can_be_repeated(tmp_path):
    db_path = tmp_path / "again.sqlite"
    main(db_path=db_path)
    main(db_path=db_path)
    connection = get_connection(db_path)
    assert count(connection, "tasks") == len(load_tasks_json())
    connection.close()


def test_foreign_key_is_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO tasks (name, category_id, deadline) "
            "VALUES (?, ?, ?)",
            ["Задача", 999, "2026-12-01"],
        )


def test_is_completed_check_constraint(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO tasks (name, category_id, deadline, is_completed) "
            "VALUES (?, ?, ?, ?)",
            ["Задача", 1, "2026-12-01", 5],
        )


def test_rows_are_accessible_by_name(conn):
    row = conn.execute(
        "SELECT tasks.name, categories.name AS category "
        "FROM tasks JOIN categories ON tasks.category_id = categories.id "
        "WHERE tasks.id = ?",
        [1],
    ).fetchone()
    assert row["name"] == "Убрать кухню"
    assert row["category"] == "Уборка"


def test_parameterized_query_ignores_injection(conn):
    rows = conn.execute(
        "SELECT * FROM tasks WHERE name = ?",
        ["x' OR '1'='1"],
    ).fetchall()
    assert rows == []
    assert count(conn, "tasks") == len(load_tasks_json())


def test_group_by_and_having(conn):
    rows = conn.execute("""
        SELECT categories.name AS category_name, COUNT(tasks.id) AS n
        FROM categories
        JOIN tasks ON categories.id = tasks.category_id
        GROUP BY categories.id, categories.name
        HAVING COUNT(tasks.id) > 1
        ORDER BY n DESC
    """).fetchall()
    assert [row["category_name"] for row in rows] == ["Уборка", "Покупки"]


def test_queries_file_is_valid_sql(conn):
    conn.executescript(QUERIES_FILE.read_text(encoding="utf-8"))


def test_committed_database_matches_json():
    connection = get_connection(DB_PATH)
    rows = connection.execute(
        "SELECT tasks.id, tasks.name, categories.name AS category, "
        "tasks.deadline, tasks.is_completed "
        "FROM tasks JOIN categories ON tasks.category_id = categories.id "
        "ORDER BY tasks.id"
    ).fetchall()
    connection.close()
    expected = [
        (
            task["id"],
            task["name"],
            task["category"],
            task["deadline"],
            int(task["is_completed"]),
        )
        for task in load_tasks_json()
    ]
    assert [tuple(row) for row in rows] == expected
