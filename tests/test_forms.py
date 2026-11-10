from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.utils import timezone
from PIL import Image

from task_pages.forms import TaskFilterForm, TaskForm
from task_pages.models import Category, Task


def upload_image(fmt="PNG", extra=b""):
    stream = BytesIO()
    Image.new("RGB", (8, 8), "blue").save(stream, fmt)
    return SimpleUploadedFile(
        f"sample.{fmt.lower()}", stream.getvalue() + extra,
        content_type=f"image/{fmt.lower()}",
    )


class FormTests(TestCase):
    def setUp(self):
        self.category = Category.objects.first()
        self.future = timezone.localdate() + timedelta(days=30)
        self.payload = {
            "name": "Новая задача", "category": self.category.pk,
            "deadline": self.future.isoformat(), "status": "active",
            "description": "Подробности задачи",
        }
        self.temp_media = TemporaryDirectory()
        self.addCleanup(self.temp_media.cleanup)
        override = self.settings(MEDIA_ROOT=self.temp_media.name)
        override.enable()
        self.addCleanup(override.disable)

    def create_task(self, **changes):
        data = {**self.payload, **changes}
        data["category_id"] = data.pop("category")
        return Task.objects.create(**data)

    def test_get_form_does_not_create_record(self):
        count = Task.objects.count()
        response = self.client.get("/tasks/create/")
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertEqual(Task.objects.count(), count)

    def test_create_redirect_and_refresh_no_duplicate(self):
        response = self.client.post("/tasks/create/", self.payload)
        task = Task.objects.get(name=self.payload["name"])
        self.assertRedirects(response, task.get_absolute_url())
        self.client.get(response.url)
        self.assertEqual(Task.objects.filter(name=task.name).count(), 1)
        self.assertEqual(task.description, "Подробности задачи")

    def test_empty_post_is_bound_with_errors(self):
        response = self.client.post("/tasks/create/", {})
        self.assertTrue(response.context["form"].is_bound)
        self.assertIn("name", response.context["form"].errors)
        self.assertEqual(Task.objects.count(), 6)

    def test_invalid_input_preserves_values_without_saving(self):
        for changes, field in [
            ({"name": "  "}, "name"),
            ({"name": "ab"}, "name"),
            ({"category": "99999"}, "category"),
            ({"status": "invalid"}, "status"),
            ({"deadline": "bad"}, "deadline"),
            ({"description": "x" * 2001}, "description"),
        ]:
            with self.subTest(field=field):
                response = self.client.post(
                    "/tasks/create/", {**self.payload, **changes},
                )
                self.assertIn(field, response.context["form"].errors)
                self.assertEqual(Task.objects.count(), 6)
                self.assertEqual(
                    response.context["form"].data["description"],
                    changes.get("description", "Подробности задачи"),
                )

    def test_past_date_and_today_boundary(self):
        past = timezone.localdate() - timedelta(days=1)
        form = TaskForm({**self.payload, "deadline": past.isoformat()})
        self.assertFalse(form.is_valid())
        self.assertIn("deadline", form.errors)
        form = TaskForm({**self.payload, "deadline": timezone.localdate()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_duplicate_and_self_exclusion(self):
        task = self.create_task()
        form = TaskForm(self.payload)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        form = TaskForm(self.payload, instance=task)
        self.assertTrue(form.is_valid(), form.errors)

    def test_cancelled_duplicate_does_not_block_new_task(self):
        self.create_task(status=Task.Status.CANCELLED)
        form = TaskForm(self.payload)
        self.assertTrue(form.is_valid(), form.errors)

    def test_edit_existing_task_preserves_id_slug_and_count(self):
        task = self.create_task()
        old_slug = task.slug
        response = self.client.get(f"/tasks/{task.pk}/edit/")
        self.assertEqual(response.context["form"].instance.pk, task.pk)
        response = self.client.post(f"/tasks/{task.pk}/edit/", {
            **self.payload, "name": "Изменённая задача",
        })
        self.assertEqual(response.status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.name, "Изменённая задача")
        self.assertEqual(task.slug, old_slug)
        self.assertEqual(Task.objects.count(), 7)

    def test_edit_old_overdue_task_can_keep_deadline(self):
        task = self.create_task(
            deadline=timezone.localdate() - timedelta(days=2),
        )
        form = TaskForm({**self.payload, "deadline": task.deadline,
                         "status": "completed"}, instance=task)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        task.refresh_from_db()
        self.assertTrue(task.is_completed)

    def test_cancel_post_only_and_does_not_cancel_completed(self):
        task = self.create_task()
        url = f"/tasks/{task.pk}/cancel/"
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.CANCELLED)
        self.assertNotIn(task, Task.objects.due_by(self.future))
        task.status = Task.Status.COMPLETED
        task.save()
        self.client.post(url)
        task.refresh_from_db()
        self.assertEqual(task.status, Task.Status.COMPLETED)

    def test_delete_confirmation_then_post(self):
        task = self.create_task()
        url = f"/tasks/{task.pk}/delete/"
        self.assertContains(self.client.get(url), "Подтвердить удаление")
        self.assertTrue(Task.objects.filter(pk=task.pk).exists())
        self.assertRedirects(self.client.post(url), "/tasks/")
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_missing_task_returns_404(self):
        for operation in ("edit", "delete", "cancel"):
            self.assertEqual(self.client.post(
                f"/tasks/99999/{operation}/", self.payload,
            ).status_code, 404)

    def test_csrf_required_for_all_mutations(self):
        task = self.create_task()
        client = Client(enforce_csrf_checks=True)
        for url in ("/tasks/create/", f"/tasks/{task.pk}/edit/",
                    f"/tasks/{task.pk}/cancel/", f"/tasks/{task.pk}/delete/"):
            self.assertEqual(client.post(url, self.payload).status_code, 403)
        client.get("/tasks/create/")
        token = client.cookies["csrftoken"].value
        response = client.post("/tasks/create/", {
            **self.payload, "name": "CSRF accepted",
            "csrfmiddlewaretoken": token,
        })
        self.assertEqual(response.status_code, 302)

    def test_image_upload_preserve_clear_and_display(self):
        response = self.client.post("/tasks/create/", {
            **self.payload, "image": upload_image(),
        })
        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(name=self.payload["name"])
        original = task.image.name
        self.assertTrue(Path(task.image.path).is_file())
        self.assertContains(
            self.client.get(task.get_absolute_url()), task.image.url,
        )
        self.client.post(f"/tasks/{task.pk}/edit/", self.payload)
        task.refresh_from_db()
        self.assertEqual(task.image.name, original)
        self.client.post(f"/tasks/{task.pk}/edit/", {
            **self.payload, "image-clear": "on",
        })
        task.refresh_from_db()
        self.assertFalse(task.image)
        self.assertContains(self.client.get(task.get_absolute_url()),
                            "Изображение не загружено")

    def test_invalid_image_and_oversized_image_rejected(self):
        for image in (
            SimpleUploadedFile("fake.png", b"not an image"),
            upload_image("GIF"), upload_image(extra=b"x" * (5 * 1024 * 1024)),
        ):
            form = TaskForm(self.payload, {"image": image})
            self.assertFalse(form.is_valid())
            self.assertIn("image", form.errors)
        self.assertEqual(Task.objects.count(), 6)
        self.assertFalse(list(Path(self.temp_media.name).rglob("*")))

    def test_description_is_escaped(self):
        self.client.post("/tasks/create/", {
            **self.payload, "description": "<script>alert(1)</script>",
        })
        task = Task.objects.get(name=self.payload["name"])
        response = self.client.get(task.get_absolute_url())
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_filter_dates_and_invalid_choice(self):
        form = TaskFilterForm({
            "from_date": "2030-01-02", "date": "2030-01-01",
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        form = TaskFilterForm({"date": "2000-01-01"})
        self.assertTrue(form.is_valid(), form.errors)
        for data in ({"category": "Missing"}, {"status": "bad"},
                     {"sort": "unknown"}, {"date": "bad"}):
            response = self.client.get("/tasks/", data)
            self.assertTrue(response.context["form"].errors)
            self.assertEqual(response.context["page_obj"].paginator.count, 0)
