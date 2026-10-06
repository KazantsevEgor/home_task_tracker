from django.http import HttpResponse

from homepage.views import page
from storage import load_tasks
from tasks import find_task_by_id

TASKS_FILE = "data/tasks.json"


def tasks(request):
    tasks_list = load_tasks(TASKS_FILE)
    items = ""
    for task in tasks_list:
        status = task.get_status()
        if task.is_completed:
            badge = "bg-success"
        elif "просрочена" in status:
            badge = "bg-danger"
        else:
            badge = "bg-warning text-dark"
        items += f"""
<li class="list-group-item d-flex justify-content-between align-items-center">
    <a href="/tasks/{task.id}/">
        {task.name} ({task.category}) &mdash; до {task.deadline}
    </a>
    <span class="badge {badge}">{status}</span>
</li>
"""
    content = f"""
<h1>Задачи</h1>
<ul class="list-group">
{items}
</ul>
"""
    return HttpResponse(page("Трекер — задачи", content))


def task_detail(request, task_id):
    tasks_list = load_tasks(TASKS_FILE)
    task = find_task_by_id(tasks_list, task_id)

    if task is None:
        content = """
<h1 class="text-danger">Задача не найдена</h1>
<a href="/tasks/" class="btn btn-outline-secondary">&larr; к списку задач</a>
"""
        return HttpResponse(
            page("Задача не найдена", content),
            status=404,
        )

    status = task.get_status()
    if task.is_completed:
        badge = "bg-success"
    elif "просрочена" in status:
        badge = "bg-danger"
    else:
        badge = "bg-warning text-dark"

    content = f"""
<div class="card">
    <div class="card-body">
        <h5 class="card-title">{task.name}</h5>
        <p class="card-text"><strong>ID:</strong> {task.id}</p>
        <p class="card-text"><strong>Категория:</strong> {task.category}</p>
        <p class="card-text"><strong>Дедлайн:</strong> {task.deadline}</p>
        <p class="card-text">
            Статус: <span class="badge {badge}">{status}</span>
        </p>
        <a href="/tasks/" class="btn btn-outline-secondary">
            &larr; к списку задач
        </a>
    </div>
</div>
"""
    return HttpResponse(page(task.name, content))
