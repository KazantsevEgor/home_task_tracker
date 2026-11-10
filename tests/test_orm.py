import sqlite3
from datetime import date, timedelta
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from task_pages.models import Category, Task


class ORMTests(TestCase):
    def test_crud_and_relations(self):
        category = Category.objects.create(name="Тестовая")
        task = Task.objects.create(
            name="Проверить", category=category, deadline=date(2030, 1, 1),
        )
        self.assertEqual(category.tasks.get(pk=task.pk), task)
        self.assertFalse(task.is_completed)
        task.is_completed = True
        task.save(update_fields=["is_completed"])
        task.refresh_from_db()
        self.assertTrue(task.is_completed)
        with self.assertRaises(ProtectedError):
            category.delete()
        task_id = task.pk
        task.delete()
        self.assertFalse(Task.objects.filter(pk=task_id).exists())
        category.delete()

    def test_overdue_boundary(self):
        today = timezone.localdate()
        task = Task(deadline=today, is_completed=False)
        self.assertFalse(task.is_overdue)
        task.deadline = today - timedelta(days=1)
        self.assertTrue(task.is_overdue)
        task.is_completed = True
        self.assertFalse(task.is_overdue)

    def test_pagination_filter_search_sort(self):
        category = Category.objects.create(name="Pagination")
        for i in range(23):
            Task.objects.create(
                name=f"Search {i:02}", category=category,
                deadline=date(2030, 1, 1),
            )
        params = {
            "category": "Pagination", "q": "Search", "status": "active",
            "sort": "name", "date": "2030-01-01", "page": "2",
        }
        response = self.client.get("/tasks/", params)
        page = response.context["page_obj"]
        self.assertEqual(page.paginator.count, 23)
        self.assertEqual([t.name for t in page], [
            f"Search {i:02}" for i in range(10, 20)
        ])
        self.assertContains(response, "category=Pagination")
        self.assertContains(response, "sort=name")
        self.assertContains(response, "q=Search")
        self.assertContains(response, "page=3")
        for value, expected in [("abc", 1), ("999", 3), ("-1", 3)]:
            params["page"] = value
            self.assertEqual(self.client.get(
                "/tasks/", params,
            ).context["page_obj"].number, expected)

    def test_search_by_related_field_and_name(self):
        response = self.client.get("/tasks/", {"q": "Уборка"})
        self.assertEqual(response.context["page_obj"].paginator.count, 3)
        response = self.client.get("/tasks/", {
            "q": "Уборка", "search_in": "name",
        })
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_invalid_params_and_date(self):
        response = self.client.get("/tasks/", {
            "sort": "bad", "status": "bad", "date": "bad",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["invalid_date"])
        self.assertEqual(response.context["sort"], "deadline")
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

    def test_empty_category_statistics(self):
        Category.objects.create(name="Пустая")
        response = self.client.get("/tasks/statistics/")
        row = next(x for x in response.context["by_category"]
                   if x.name == "Пустая")
        self.assertEqual(row.tasks_count, 0)
        self.assertEqual(row.completed_count, 0)
        self.assertIn("Пустая", response.context["empty_categories"])

    def test_list_queries_do_not_grow_per_task(self):
        with self.assertNumQueries(3):
            self.client.get("/tasks/")

    def test_import_is_repeatable(self):
        before = list(Task.objects.values())
        call_command("import_legacy", stdout=StringIO())
        self.assertEqual(list(Task.objects.values()), before)

    def test_import_conflict_rolls_back(self):
        Task.objects.filter(pk=1).update(name="Изменено пользователем")
        with self.assertRaises(CommandError):
            call_command("import_legacy", stdout=StringIO())
        self.assertEqual(Task.objects.get(pk=1).name, "Изменено пользователем")

    def test_invalid_source_rolls_back_categories(self):
        with TemporaryDirectory() as folder:
            source = Path(folder) / "source.sqlite"
            with sqlite3.connect(source) as conn:
                conn.executescript(
                    "CREATE TABLE categories (id INTEGER, name TEXT);"
                    "CREATE TABLE tasks (id INTEGER, name TEXT, "
                    "category_id INTEGER, deadline TEXT, "
                    "is_completed INTEGER);"
                    "INSERT INTO categories VALUES (999, 'Rollback');"
                    "INSERT INTO tasks VALUES (999, 'Bad', 999, 'bad', 0);"
                )
            with self.assertRaises(CommandError):
                call_command(
                    "import_legacy", source=source, stdout=StringIO(),
                )
            self.assertFalse(Category.objects.filter(pk=999).exists())

    def test_completed_and_overdue_filters(self):
        with patch("task_pages.views.timezone.localdate",
                   return_value=date(2026, 10, 20)):
            response = self.client.get("/tasks/", {"status": "overdue"})
        self.assertTrue(all(
            not task.is_completed and task.deadline < date(2026, 10, 20)
            for task in response.context["tasks"]
        ))
        response = self.client.get("/tasks/", {"status": "completed"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
