from datetime import date

from django.core.paginator import Paginator
from django.db.models import Count, F, Min, Q
from django.shortcuts import render
from django.utils import timezone

from .models import Category, Task


SORTS = {
    "deadline": ("deadline", "id"),
    "-deadline": ("-deadline", "id"),
    "name": ("name", "id"),
    "category": ("category__name", "deadline", "id"),
}
SORT_LABELS = {
    "deadline": "Сначала ближайшие сроки",
    "-deadline": "Сначала дальние сроки",
    "name": "По названию",
    "category": "По категории",
}


def tasks(request):
    category = request.GET.get("category", "")
    status = request.GET.get("status", "")
    query = request.GET.get("q", "").strip()
    search_in = request.GET.get("search_in", "all")
    due_date = request.GET.get("date", "")
    sort = request.GET.get("sort", "deadline")
    if sort not in SORTS:
        sort = "deadline"
    if status not in ("active", "completed", "overdue"):
        status = ""
    if search_in not in ("all", "name"):
        search_in = "all"
    tasks_list = Task.objects.select_related("category")
    if category:
        tasks_list = tasks_list.filter(category__name=category)
    if status == "active":
        tasks_list = tasks_list.exclude(is_completed=True)
    elif status == "completed":
        tasks_list = tasks_list.filter(is_completed=True)
    elif status == "overdue":
        tasks_list = tasks_list.filter(
            is_completed=False, deadline__lt=timezone.localdate(),
        )
    if query:
        if search_in == "name":
            tasks_list = tasks_list.filter(name__icontains=query)
        else:
            tasks_list = tasks_list.filter(
                Q(name__icontains=query) | Q(category__name__icontains=query)
            )
    invalid_date = False
    if due_date:
        try:
            parsed_date = date.fromisoformat(due_date)
        except ValueError:
            invalid_date = True
            tasks_list = tasks_list.none()
        else:
            tasks_list = tasks_list.filter(deadline__lte=parsed_date)
    page = Paginator(tasks_list.order_by(*SORTS[sort]), 10).get_page(
        request.GET.get("page")
    )
    params = request.GET.copy()
    params.pop("page", None)
    return render(request, "task_pages/task_list.html", {
        "tasks": page.object_list,
        "page_obj": page,
        "query_params": params.urlencode(),
        "categories": Category.objects.order_by("name"),
        "selected_category": category,
        "selected_status": status,
        "q": query,
        "search_in": search_in,
        "due_date": due_date,
        "invalid_date": invalid_date,
        "sort": sort,
        "sort_options": SORT_LABELS.items(),
    })


def task_detail(request, task_id):
    try:
        task = Task.objects.select_related("category").get(pk=task_id)
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
    tasks_list = Task.objects.select_related("category").exclude(
        is_completed=True,
    ).order_by("deadline", "id")
    return render(
        request, "task_pages/active_tasks.html", {"tasks": tasks_list},
    )


def tasks_due(request):
    due_date = request.GET.get("date")
    tasks_list = Task.objects.none()
    invalid_date = False
    if due_date:
        try:
            parsed_date = date.fromisoformat(due_date)
        except ValueError:
            invalid_date = True
        else:
            tasks_list = Task.objects.select_related("category").filter(
                is_completed=False, deadline__lte=parsed_date,
            ).order_by("deadline", "id")
    return render(request, "task_pages/tasks_due.html", {
        "tasks": tasks_list, "due_date": due_date,
        "invalid_date": invalid_date,
    })


def statistics(request):
    summary = Task.objects.aggregate(
        total_count=Count("id"),
        completed_count=Count("id", filter=Q(is_completed=True)),
        overdue_count=Count("id", filter=Q(
            is_completed=False, deadline__lt=timezone.localdate(),
        )),
    )
    nearest = Task.objects.filter(is_completed=False).aggregate(
        nearest_deadline=Min("deadline"),
    )
    by_category = Category.objects.annotate(
        category_name=F("name"),
        tasks_count=Count("tasks"),
        completed_count=Count("tasks", filter=Q(tasks__is_completed=True)),
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
