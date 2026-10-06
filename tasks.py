from datetime import date
from typing import Optional

from models import Task


def add_task(
    tasks: list[Task],
    name: str,
    category: str,
    deadline: date,
) -> None:
    task_id = max((t.id for t in tasks), default=0) + 1
    tasks.append(Task(task_id, name, category, str(deadline)))


def find_task(tasks: list[Task], query: str) -> list[Task]:
    return [t for t in tasks if query.lower() in t.name.lower()]


def filter_tasks_by_category(tasks: list[Task], category: str):
    for task in tasks:
        if task.category.lower() == category.lower():
            yield task


def sort_tasks(tasks: list[Task]) -> list[Task]:
    return sorted(tasks, key=lambda t: t.deadline)


def check_task_deadline(
    tasks: list[Task],
    task_id: int,
    days_left: int,
) -> bool:
    for task in tasks:
        if task.id == task_id:
            return task.days_until_deadline() >= days_left
    return False


def find_task_by_id(
    tasks: list[Task],
    task_id: int,
) -> Optional[Task]:
    for task in tasks:
        if task.id == task_id:
            return task
    return None
