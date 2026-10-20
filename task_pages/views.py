from django.shortcuts import render

from storage import load_tasks
from tasks import find_task_by_id

TASKS_FILE = "data/tasks.json"


def tasks(request):
    tasks_list = load_tasks(TASKS_FILE)

    context = {
        "tasks": tasks_list,
    }

    return render(
        request,
        "task_pages/task_list.html",
        context,
    )


def task_detail(request, task_id):
    tasks_list = load_tasks(TASKS_FILE)
    task = find_task_by_id(tasks_list, task_id)

    context = {
        "task": task,
    }

    return render(
        request,
        "task_pages/task_detail.html",
        context,
        status=404 if task is None else 200,
    )
