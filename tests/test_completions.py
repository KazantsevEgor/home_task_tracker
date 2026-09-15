from datetime import date

from completions import (
    cancel_completion,
    check_status,
    complete_task,
    is_task_completed,
)
from tasks import add_task


def test_complete_task():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    result = complete_task(tasks, 1)
    assert result is True
    assert tasks[0]["is_completed"] is True


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
    assert tasks[0]["is_completed"] is False


def test_is_task_completed_false():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    assert is_task_completed(tasks, 1) is False


def test_is_task_completed_true():
    tasks = []
    add_task(tasks, "Убрать кухню", "Уборка", date(2026, 9, 17))
    complete_task(tasks, 1)
    assert is_task_completed(tasks, 1) is True


def test_check_status_completed():
    status = check_status(True, date(2026, 9, 17))
    assert status == "Задача выполнена"


def test_check_status_overdue():
    status = check_status(False, date(2020, 1, 1))
    assert status == "Задача просрочена"


def test_check_status_in_progress():
    status = check_status(False, date(2030, 1, 1))
    assert status == "Задача в процессе"
