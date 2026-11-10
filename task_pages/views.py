from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Min, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from .forms import DueDateForm, SORTS, TaskFilterForm, TaskForm
from .models import Category, Task


@require_http_methods(["GET"])
def tasks(request):
    form = TaskFilterForm(request.GET or None)
    data = {}
    tasks_list = Task.objects.with_category()
    if form.is_bound:
        if form.is_valid():
            data = form.cleaned_data
        else:
            tasks_list = tasks_list.none()
    category = data.get("category")
    if category:
        tasks_list = tasks_list.filter(category=category)
    status = data.get("status")
    if status == "active":
        tasks_list = tasks_list.active()
    elif status == "completed":
        tasks_list = tasks_list.completed()
    elif status == "cancelled":
        tasks_list = tasks_list.cancelled()
    elif status == "overdue":
        tasks_list = tasks_list.overdue()
    if data.get("q"):
        if data.get("search_in") == "name":
            tasks_list = tasks_list.filter(name__icontains=data["q"])
        else:
            tasks_list = tasks_list.filter(
                Q(name__icontains=data["q"])
                | Q(category__name__icontains=data["q"])
            )
    if data.get("date"):
        tasks_list = tasks_list.filter(deadline__lte=data["date"])
    if data.get("from_date"):
        tasks_list = tasks_list.filter(deadline__gte=data["from_date"])
    sort = data.get("sort") or "deadline"
    page = Paginator(tasks_list.order_by(*SORTS[sort]), 10).get_page(
        request.GET.get("page")
    )
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "task_pages/task_list.html", {
        "form": form, "tasks": page.object_list, "page_obj": page,
        "query_params": params.urlencode(), "selected_category": category,
        "sort": sort, "invalid_date": bool(form.errors.get("date")),
    })


def task_detail(request, task_id=None, slug=None):
    try:
        task = Task.objects.with_category().get(
            **({"slug": slug} if slug is not None else {"pk": task_id})
        )
    except Task.DoesNotExist:
        task = None
    related_tasks = (
        task.category.tasks.exclude(pk=task.pk).select_related("category")[:3]
        if task else []
    )
    return render(request, "task_pages/task_detail.html", {
        "task": task, "related_tasks": related_tasks,
    }, status=200 if task else 404)


def active_tasks(request):
    tasks_list = Task.objects.with_category().active().order_by(
        "deadline", "id",
    )
    return render(
        request, "task_pages/active_tasks.html", {"tasks": tasks_list},
    )


def tasks_due(request):
    form = DueDateForm(request.GET or None)
    tasks_list = Task.objects.none()
    if form.is_bound and form.is_valid():
        tasks_list = Task.objects.with_category().due_by(
            form.cleaned_data["date"],
        ).order_by("deadline", "id")
    return render(request, "task_pages/tasks_due.html", {
        "form": form, "tasks": tasks_list,
        "due_date": request.GET.get("date"),
        "invalid_date": bool(form.errors),
    })


def statistics(request):
    summary = Task.objects.aggregate(
        total_count=Count("id"),
        active_count=Count("id", filter=Q(status=Task.Status.ACTIVE)),
        cancelled_count=Count("id", filter=Q(status=Task.Status.CANCELLED)),
        completed_count=Count("id", filter=Q(status=Task.Status.COMPLETED)),
        overdue_count=Count("id", filter=Q(
            status=Task.Status.ACTIVE, deadline__lt=timezone.localdate(),
        )),
    )
    nearest = Task.objects.active().aggregate(
        nearest_deadline=Min("deadline"),
    )
    by_category = Category.objects.annotate(
        category_name=F("name"),
        tasks_count=Count("tasks"),
        completed_count=Count(
            "tasks", filter=Q(tasks__status=Task.Status.COMPLETED),
        ),
    ).order_by("-tasks_count", "name")
    busy_categories = by_category.filter(tasks_count__gt=1)
    empty_categories = Category.objects.filter(tasks__isnull=True).values_list(
        "name", flat=True,
    )
    return render(request, "task_pages/statistics.html", {
        "summary": summary,
        "nearest_deadline": nearest["nearest_deadline"],
        "by_category": by_category,
        "busy_categories": busy_categories,
        "empty_categories": empty_categories,
    })


@require_http_methods(["GET", "POST"])
def task_create(request):
    form = TaskForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
    )
    if request.method == "POST" and form.is_valid():
        task = form.save()
        messages.success(request, "Задача создана.")
        return redirect(task)
    return render(request, "task_pages/task_form.html", {"form": form})


@require_http_methods(["GET", "POST"])
def task_edit(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    form = TaskForm(
        request.POST if request.method == "POST" else None,
        request.FILES if request.method == "POST" else None,
        instance=task,
    )
    if request.method == "POST" and form.is_valid():
        task = form.save()
        messages.success(request, "Изменения сохранены.")
        return redirect(task)
    return render(request, "task_pages/task_form.html", {
        "form": form, "task": task,
    })


@require_POST
def task_cancel(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    changed = Task.objects.active().filter(pk=task.pk).update(
        status=Task.Status.CANCELLED,
    )
    if changed:
        messages.success(request, "Задача отменена.")
    else:
        messages.info(request, "Отменить можно только активную задачу.")
    return redirect(task)


@require_http_methods(["GET", "POST"])
def task_delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Задача удалена.")
        return redirect("tasks:list")
    return render(
        request, "task_pages/task_confirm_delete.html", {"task": task},
    )
