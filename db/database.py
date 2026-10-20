import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "tracker.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(db_path=DB_PATH):
    """Подключение к SQLite: строки доступны по именам столбцов."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn):
    """Создаёт таблицы из sql/schema.sql (если их ещё нет)."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
