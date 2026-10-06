from models import Task


def is_task_completed(tasks: list[Task], task_id: int) -> bool:
    for task in tasks:
        if task.id == task_id:
            return task.is_completed
    return False


def complete_task(tasks: list[Task], task_id: int) -> bool:
    for task in tasks:
        if task.id == task_id:
            if task.is_completed:
                return False
            task.mark_completed()
            return True
    return False


def cancel_completion(tasks: list[Task], task_id: int) -> bool:
    for task in tasks:
        if task.id == task_id:
            task.cancel_completion()
            return True
    return False
