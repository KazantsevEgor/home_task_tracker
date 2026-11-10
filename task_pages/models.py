from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField("Название", max_length=200, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Task(models.Model):
    name = models.CharField("Название", max_length=200)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="tasks",
        verbose_name="Категория",
    )
    deadline = models.DateField("Срок выполнения")
    is_completed = models.BooleanField("Выполнена", default=False)

    class Meta:
        ordering = ["deadline", "id"]
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

    @property
    def is_overdue(self):
        return not self.is_completed and self.deadline < timezone.localdate()

    def __str__(self):
        return self.name
