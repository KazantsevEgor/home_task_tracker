import os
import sys

from datetime import date  # noqa: F401

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Task  # noqa: E402
from completions import (  # noqa: E402
    cancel_completion,
    complete_task,
    is_task_completed,
)
from tasks import add_task  # noqa: E402


def test_complete_task():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    result = complete_task(tasks, 1)
    assert result is True
    assert tasks[0].is_completed is True


def test_complete_task_already_done():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    complete_task(tasks, 1)
    result = complete_task(tasks, 1)
    assert result is False


def test_cancel_completion():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    complete_task(tasks, 1)
    cancel_completion(tasks, 1)
    assert tasks[0].is_completed is False


def test_is_task_completed_false():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    assert is_task_completed(tasks, 1) is False


def test_is_task_completed_true():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    complete_task(tasks, 1)
    assert is_task_completed(tasks, 1) is True


def test_task_get_status_completed():
    task = Task(1, "Убрать кухню", "Уборка", "2026-09-17", is_completed=True)
    assert task.get_status() == "Задача выполнена"


def test_task_get_status_overdue():
    task = Task(1, "Убрать кухню", "Уборка", "2020-01-01")
    assert task.get_status() == "Задача просрочена"


def test_task_get_status_in_progress():
    task = Task(1, "Убрать кухню", "Уборка", "2030-01-01")
    assert task.get_status() == "Задача в процессе"
