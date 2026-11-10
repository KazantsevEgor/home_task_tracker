from datetime import date

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from task_pages.models import Category, Task


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = get_user_model().objects.create_superuser(
            username="test_admin", password="test-only-password",
        )

    def setUp(self):
        self.client.force_login(self.admin)

    def test_localization_and_lists(self):
        response = self.client.get("/admin/")
        self.assertContains(response, "Домашние задачи")
        self.assertContains(response, "Трекер домашних задач")
        response = self.client.get("/admin/task_pages/task/")
        self.assertContains(response, "Убрать кухню")
        self.assertContains(response, "Год срока")

    def test_search_and_status_filter(self):
        response = self.client.get("/admin/task_pages/task/", {
            "q": "Уборка", "status__exact": "active",
        })
        self.assertEqual(response.context["cl"].result_count, 3)
        self.assertNotContains(response, "Купить продукты")

    def test_category_inline(self):
        category = Category.objects.get(name="Уборка")
        response = self.client.get(reverse(
            "admin:task_pages_category_change", args=[category.pk],
        ))
        self.assertContains(response, 'name="tasks-TOTAL_FORMS"')
        self.assertContains(response, "Убрать кухню")

    def test_admin_create_edit_delete_task(self):
        category = Category.objects.first()
        data = {
            "name": "Admin CRUD", "category": category.pk,
            "deadline": "2030-01-02", "status": "active", "_save": "1",
        }
        response = self.client.post("/admin/task_pages/task/add/", data)
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(name="Admin CRUD")
        data["status"] = "cancelled"
        response = self.client.post(reverse(
            "admin:task_pages_task_change", args=[task.pk],
        ), data)
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.CANCELLED)
        self.assertNotIn(
            task, self.client.get("/tasks/active/").context["tasks"],
        )
        self.assertContains(self.client.get(task.get_absolute_url()),
                            "Задача отменена")
        response = self.client.post(reverse(
            "admin:task_pages_task_delete", args=[task.pk],
        ), {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_non_staff_cannot_access_admin(self):
        user = get_user_model().objects.create_user(username="ordinary")
        self.client.force_login(user)
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_inline_edit_changes_public_status(self):
        category = Category.objects.create(name="Inline test")
        task = Task.objects.create(
            name="Inline task", category=category, deadline=date(2020, 1, 1),
        )
        response = self.client.post(reverse(
            "admin:task_pages_category_change", args=[category.pk],
        ), {
            "name": category.name, "_save": "1",
            "tasks-TOTAL_FORMS": "1", "tasks-INITIAL_FORMS": "1",
            "tasks-MIN_NUM_FORMS": "0", "tasks-MAX_NUM_FORMS": "1000",
            "tasks-0-id": task.pk, "tasks-0-category": category.pk,
            "tasks-0-name": task.name, "tasks-0-deadline": "2020-01-01",
            "tasks-0-status": "completed",
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertTrue(task.is_completed)
        self.assertFalse(task.is_overdue)


class PR10Tests(TestCase):
    def test_cancelled_excluded_from_due_and_statistics(self):
        task = Task.objects.create(
            name="Cancelled test", category=Category.objects.first(),
            deadline=date(2000, 1, 1), status=Task.Status.CANCELLED,
        )
        self.assertFalse(task.is_overdue)
        self.assertNotIn(task, Task.objects.due_by(date(2100, 1, 1)))
        self.assertIn(task, Task.objects.cancelled())
        response = self.client.get("/tasks/statistics/")
        self.assertEqual(response.context["summary"]["cancelled_count"], 1)
        self.assertEqual(response.context["summary"]["active_count"], 5)
        response = self.client.get("/tasks/", {"status": "cancelled"})
        self.assertEqual(list(response.context["tasks"]), [task])

    def test_slug_unique_stable_and_generated_year(self):
        kwargs = {"name": "Проверка", "category": Category.objects.first(),
                  "deadline": date(2030, 1, 1)}
        first = Task.objects.create(**kwargs)
        second = Task.objects.create(**kwargs)
        self.assertNotEqual(first.slug, second.slug)
        self.assertTrue(first.slug.isascii())
        original_slug = first.slug
        first.name = "Новое название"
        first.deadline = date(2032, 1, 1)
        first.save()
        first.refresh_from_db()
        self.assertEqual(first.slug, original_slug)
        self.assertEqual(first.deadline_year, 2032)
        for url in (first.get_absolute_url(), f"/tasks/{first.pk}/"):
            self.assertContains(self.client.get(url), "Новое название")
        self.assertEqual(self.client.get(
            "/tasks/by-slug/unknown/",
        ).status_code, 404)

    def test_n_plus_one_measurement(self):
        with CaptureQueriesContext(connection) as plain:
            names = [t.category.name for t in Task.objects.all()]
        with CaptureQueriesContext(connection) as optimized:
            optimized_names = [t.category.name
                               for t in Task.objects.with_category()]
        self.assertEqual(names, optimized_names)
        self.assertEqual(len(plain), len(names) + 1)
        self.assertEqual(len(optimized), 1)

    def test_context_counter_updates(self):
        response = self.client.get("/")
        self.assertContains(response, "Активных задач: 5")
        Task.objects.active().first().delete()
        self.assertContains(self.client.get("/"), "Активных задач: 4")
