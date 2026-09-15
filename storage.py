import json


def load_tasks(filename: str) -> list[dict]:
    """Загрузить задачи из JSON-файла."""
    try:
        with open(filename, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def save_tasks(filename: str, tasks: list[dict]) -> None:
    """Сохранить задачи в JSON-файл."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
