from datetime import date


def is_task_completed(tasks: list[dict], task_id: int) -> bool:
    """Проверить, выполнена ли задача."""
    for task in tasks:
        if task["id"] == task_id:
            return task["is_completed"]
    return False


def complete_task(tasks: list[dict], task_id: int) -> bool:
    """Отметить задачу как выполненную.

    Возвращает False, если задача уже выполнена.
    """
    for task in tasks:
        if task["id"] == task_id:
            if task["is_completed"]:
                return False
            task["is_completed"] = True
            return True
    return False


def cancel_completion(tasks: list[dict], task_id: int) -> bool:
    """Снять отметку выполнения с задачи."""
    for task in tasks:
        if task["id"] == task_id:
            task["is_completed"] = False
            return True
    return False


def check_status(is_completed: bool, deadline: date) -> str:
    """Вернуть текстовый статус задачи."""
    if is_completed:
        return "Задача выполнена"
    elif date.today() > deadline:
        return "Задача просрочена"
    else:
        return "Задача в процессе"
