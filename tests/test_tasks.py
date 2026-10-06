import os
import sys

from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Task  # noqa: E402
from tasks import (  # noqa: E402
    add_task,
    check_task_deadline,
    filter_tasks_by_category,
    find_task,
    sort_tasks,
)


def test_add_task():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    assert len(tasks) == 1
    assert isinstance(tasks[0], Task)


def test_add_task_id_increment():
    tasks = []
    add_task(tasks, "Задача 1", "Уборка", date(2026, 9, 17))
    add_task(tasks, "Задача 2", "Покупки", date(2026, 9, 18))
    assert tasks[1].id == 2


def test_find_task():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    result = find_task(tasks, "кухню")
    assert len(result) == 1


def test_find_task_not_found():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    result = find_task(tasks, "балкон")
    assert result == []


def test_filter_tasks_by_category():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    add_task(tasks, "Купить молоко", "Покупки", date(2026, 9, 18))
    result = list(filter_tasks_by_category(tasks, "Уборка"))
    assert len(result) == 1
    assert result[0].name == "Убрать кухню"


def test_sort_tasks():
    tasks = []
    add_task(tasks, "Задача B", "Уборка", date(2026, 9, 20))
    add_task(tasks, "Задача A", "Покупки", date(2026, 9, 16))
    sorted_list = sort_tasks(tasks)
    assert sorted_list[0].name == "Задача A"


def test_check_task_deadline_sufficient():
    tasks = []
    add_task(tasks, "Задача", "Уборка", date(2030, 1, 1))
    assert check_task_deadline(tasks, 1, 10) is True


def test_check_task_deadline_not_found():
    tasks = []
    assert check_task_deadline(tasks, 99, 1) is False
