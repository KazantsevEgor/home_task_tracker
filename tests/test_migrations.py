"""Переход ПР9 → ПР10 проверяется в отдельном процессе и временной БД."""
import os
import subprocess
import sys


def test_pr9_data_migration(tmp_path):
    script = '''
import django
from django.conf import settings
db_path = __import__("os").environ["MIGRATION_DB"]
settings.DATABASES["default"]["NAME"] = db_path
django.setup()
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
old = [("task_pages", "0001_initial")]
new = [("task_pages", "0002_task_status_slug_year")]
executor = MigrationExecutor(connection)
executor.migrate(old)
apps = executor.loader.project_state(old).apps
Category = apps.get_model("task_pages", "Category")
Task = apps.get_model("task_pages", "Task")
c = Category.objects.create(name="Migration")
for pk, completed in [(41, False), (42, True)]:
    Task.objects.create(id=pk, name="Same", category=c,
                        deadline="2030-02-01", is_completed=completed)
executor = MigrationExecutor(connection)
executor.migrate(new)
apps = executor.loader.project_state(new).apps
Task = apps.get_model("task_pages", "Task")
a, b = list(Task.objects.order_by("id"))
assert (a.status, b.status) == ("active", "completed")
assert (a.slug, b.slug) == ("task-41", "task-42")
assert a.category_id == c.pk and b.category_id == c.pk
assert a.deadline_year == 2030
executor = MigrationExecutor(connection)
executor.migrate(old)
apps = executor.loader.project_state(old).apps
Task = apps.get_model("task_pages", "Task")
assert list(Task.objects.order_by("id").values_list(
    "is_completed", flat=True)) == [False, True]
connection.close()
'''
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True,
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "tracker.settings",
             "DJANGO_DEBUG_TOOLBAR": "0",
             "MIGRATION_DB": str(tmp_path / "migration.sqlite")},
    )
    assert result.returncode == 0, result.stdout + result.stderr
