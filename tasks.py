from datetime import date


def add_task(
    tasks: list[dict],
    name: str,
    category: str,
    deadline: date,
) -> None:
    """Добавить задачу в список tasks."""
    task_id = max((t["id"] for t in tasks), default=0) + 1
    tasks.append({
        "id": task_id,
        "name": name,
        "category": category,
        "deadline": str(deadline),
        "is_completed": False,
    })


def find_task(tasks: list[dict], query: str) -> list[dict]:
    """Найти задачи по подстроке названия."""
    return [t for t in tasks if query.lower() in t["name"].lower()]


def filter_tasks_by_category(tasks: list[dict], category: str):
    """Отобрать задачи по категории (генератор)."""
    for task in tasks:
        if task["category"].lower() == category.lower():
            yield task


def sort_tasks(tasks: list[dict]) -> list[dict]:
    """Отсортировать задачи по дедлайну."""
    return sorted(tasks, key=lambda t: t["deadline"])


def check_task_deadline(
    tasks: list[dict],
    task_id: int,
    days_left: int,
) -> bool:
    """Проверить, осталось ли у задачи не менее days_left дней до дедлайна."""
    for task in tasks:
        if task["id"] == task_id:
            deadline = date.fromisoformat(task["deadline"])
            return (deadline - date.today()).days >= days_left
    return False
