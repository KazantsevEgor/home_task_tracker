import json

from models import Task


def load_tasks(filename: str) -> list[Task]:
    try:
        with open(filename, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []
    return [Task.from_dict(item) for item in data]


def save_tasks(filename: str, tasks: list[Task]) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            [t.to_dict() for t in tasks], f, ensure_ascii=False, indent=2
        )
