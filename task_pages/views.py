from datetime import date

from django.shortcuts import render

from db.database import get_connection

# Общая часть запросов: задача + название её категории (JOIN).
# Признак просрочки is_overdue вычисляется в самом запросе.
TASK_SELECT = """
    SELECT
        tasks.id,
        tasks.name,
        categories.name AS category,
        tasks.deadline,
        tasks.is_completed,
        CASE
            WHEN tasks.is_completed = 0
             AND tasks.deadline < date('now', 'localtime') THEN 1
            ELSE 0
        END AS is_overdue
    FROM tasks
    JOIN categories ON tasks.category_id = categories.id
"""


def fetch_all(query, params=()):
    conn = get_connection()
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def fetch_one(query, params=()):
    conn = get_connection()
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()


def tasks(request):
    category = request.GET.get("category")
    categories = fetch_all("SELECT id, name FROM categories ORDER BY name")

    if category:
        tasks_list = fetch_all(
            TASK_SELECT
            + " WHERE categories.name = ?"
            + " ORDER BY tasks.deadline, tasks.id",
            [category],
        )
    else:
        tasks_list = fetch_all(
            TASK_SELECT + " ORDER BY tasks.deadline, tasks.id"
        )

    context = {
        "tasks": tasks_list,
        "categories": categories,
        "selected_category": category,
    }

    return render(
        request,
        "task_pages/task_list.html",
        context,
    )


def task_detail(request, task_id):
    task = fetch_one(TASK_SELECT + " WHERE tasks.id = ?", [task_id])

    context = {
        "task": task,
    }

    return render(
        request,
        "task_pages/task_detail.html",
        context,
        status=404 if task is None else 200,
    )


def active_tasks(request):
    tasks_list = fetch_all(
        TASK_SELECT
        + " WHERE tasks.is_completed = 0"
        + " ORDER BY tasks.deadline, tasks.id"
    )

    return render(
        request,
        "task_pages/active_tasks.html",
        {"tasks": tasks_list},
    )


def tasks_due(request):
    due_date = request.GET.get("date")
    tasks_list = []
    invalid_date = False

    if due_date:
        try:
            date.fromisoformat(due_date)
        except ValueError:
            invalid_date = True
        else:
            tasks_list = fetch_all(
                TASK_SELECT
                + " WHERE tasks.is_completed = 0 AND tasks.deadline <= ?"
                + " ORDER BY tasks.deadline, tasks.id",
                [due_date],
            )

    context = {
        "tasks": tasks_list,
        "due_date": due_date,
        "invalid_date": invalid_date,
    }

    return render(
        request,
        "task_pages/tasks_due.html",
        context,
    )


def statistics(request):
    summary = fetch_one("""
        SELECT
            COUNT(*) AS total_count,
            COALESCE(SUM(is_completed), 0) AS completed_count,
            COALESCE(SUM(
                CASE
                    WHEN is_completed = 0
                     AND deadline < date('now', 'localtime') THEN 1
                    ELSE 0
                END
            ), 0) AS overdue_count
        FROM tasks
    """)
    nearest = fetch_one("""
        SELECT MIN(deadline) AS nearest_deadline
        FROM tasks
        WHERE is_completed = 0
    """)
    by_category = fetch_all("""
        SELECT
            categories.name AS category_name,
            COUNT(tasks.id) AS tasks_count,
            COALESCE(SUM(tasks.is_completed), 0) AS completed_count
        FROM categories
        LEFT JOIN tasks ON categories.id = tasks.category_id
        GROUP BY categories.id, categories.name
        ORDER BY tasks_count DESC, categories.name
    """)
    busy_categories = fetch_all("""
        SELECT
            categories.name AS category_name,
            COUNT(tasks.id) AS tasks_count
        FROM categories
        JOIN tasks ON categories.id = tasks.category_id
        GROUP BY categories.id, categories.name
        HAVING COUNT(tasks.id) > 1
        ORDER BY tasks_count DESC
    """)

    context = {
        "summary": summary,
        "nearest_deadline": nearest["nearest_deadline"],
        "by_category": by_category,
        "busy_categories": busy_categories,
    }

    return render(
        request,
        "task_pages/statistics.html",
        context,
    )
