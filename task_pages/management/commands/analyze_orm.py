"""Воспроизводимое сравнение запросов без изменения пользовательских данных."""
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext

from task_pages.models import Task


class Command(BaseCommand):
    help = "Сравнить число SQL-запросов с select_related и без него"

    def handle(self, *args, **options):
        with CaptureQueriesContext(connection) as plain:
            names = [task.category.name for task in Task.objects.all()[:20]]
        with CaptureQueriesContext(connection) as optimized:
            optimized_names = [task.category.name for task in
                               Task.objects.with_category()[:20]]
        assert names == optimized_names
        self.stdout.write(f"Объектов: {len(names)}")
        self.stdout.write(f"Без select_related: {len(plain)} запросов")
        self.stdout.write(f"С select_related: {len(optimized)} запросов")
        self.stdout.write("SQL оптимизированной выборки:")
        self.stdout.write(optimized.captured_queries[0]["sql"])
        self.stdout.write("План выполнения:")
        self.stdout.write(Task.objects.with_category().explain())
