from uuid import uuid4

from django.db import models
from django.db.models.functions import ExtractYear
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField("Название", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class TaskQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status=Task.Status.ACTIVE)

    def completed(self):
        return self.filter(status=Task.Status.COMPLETED)

    def cancelled(self):
        return self.filter(status=Task.Status.CANCELLED)

    def overdue(self):
        return self.active().filter(deadline__lt=timezone.localdate())

    def due_by(self, day):
        return self.active().filter(deadline__lte=day)

    def with_category(self):
        return self.select_related("category")


class Task(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активна"
        COMPLETED = "completed", "Выполнена"
        CANCELLED = "cancelled", "Отменена"

    name = models.CharField("Название", max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="tasks",
        verbose_name="Категория",
    )
    deadline = models.DateField("Срок выполнения")
    status = models.CharField(
        "Статус", max_length=10, choices=Status.choices, default=Status.ACTIVE,
    )
    slug = models.SlugField("Адрес", max_length=240, unique=True, blank=True)
    deadline_year = models.GeneratedField(
        expression=ExtractYear("deadline"), output_field=models.IntegerField(),
        db_persist=True, verbose_name="Год срока",
    )
    objects = TaskQuerySet.as_manager()

    class Meta:
        ordering = ["deadline", "id"]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        constraints = [models.CheckConstraint(
            condition=models.Q(
                status__in=["active", "completed", "cancelled"],
            ),
            name="task_valid_status",
        )]

    @property
    def is_completed(self):
        """Совместимость чтения статуса со старыми шаблонами ПР9."""
        return self.status == self.Status.COMPLETED

    @property
    def is_overdue(self):
        return (self.status == self.Status.ACTIVE
                and self.deadline < timezone.localdate())

    def save(self, *args, **kwargs):
        if not self.slug:
            prefix = slugify(self.name) or "task"
            self.slug = f"{prefix}-{uuid4().hex}"
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = (
                    set(kwargs["update_fields"]) | {"slug"}
                )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("tasks:detail_slug", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name
