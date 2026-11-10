"""Однократный перенос ПР7; повторный запуск проверяет совпадение данных."""
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from task_pages.models import Category, Task


class Command(BaseCommand):
    help = "Перенести категории и задачи из SQLite ПР7 с сохранением ID"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source", type=Path,
            default=settings.BASE_DIR / "data" / "tracker.sqlite",
        )

    def handle(self, *args, **options):
        source = options["source"].resolve()
        target = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if not source.is_file() or source == target:
            raise CommandError("Нужен отдельный существующий файл базы ПР7.")
        try:
            with closing(sqlite3.connect(
                source.as_uri() + "?mode=ro", uri=True,
            )) as connection:
                categories = connection.execute(
                    "SELECT id, name FROM categories ORDER BY id"
                ).fetchall()
                tasks = connection.execute(
                    "SELECT id, name, category_id, deadline, is_completed "
                    "FROM tasks ORDER BY id"
                ).fetchall()
            with transaction.atomic():
                for pk, name in categories:
                    self.copy_object(Category, pk, {"name": name})
                category_ids = {row[0] for row in categories}
                for pk, name, category_id, deadline, completed in tasks:
                    if (category_id not in category_ids
                            or completed not in (0, 1)):
                        raise CommandError(f"Некорректная задача ID={pk}.")
                    self.copy_object(Task, pk, {
                        "name": name, "category_id": category_id,
                        "deadline": date.fromisoformat(deadline),
                        "is_completed": bool(completed),
                    })
        except (sqlite3.Error, ValueError, TypeError,
                ValidationError, IntegrityError) as error:
            raise CommandError(f"Перенос отменён: {error}") from error
        self.stdout.write(self.style.SUCCESS(
            f"Проверено/перенесено: категорий {len(categories)}, "
            f"задач {len(tasks)}."
        ))

    def copy_object(self, model, pk, fields):
        existing = model.objects.filter(pk=pk).first()
        if existing:
            if any(getattr(existing, key) != value
                   for key, value in fields.items()):
                raise CommandError(
                    f"Конфликт {model.__name__} ID={pk}; перенос отменён."
                )
            return
        obj = model(pk=pk, **fields)
        obj.full_clean()
        obj.save(force_insert=True)
