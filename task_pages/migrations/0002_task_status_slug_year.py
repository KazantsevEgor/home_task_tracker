from django.db import migrations, models
from django.db.models.functions import ExtractYear


def transfer_data(apps, schema_editor):
    Task = apps.get_model("task_pages", "Task")
    tasks = Task.objects.using(schema_editor.connection.alias)
    for task in tasks.all().iterator():
        tasks.filter(pk=task.pk).update(
            status="completed" if task.is_completed else "active",
            slug=f"task-{task.pk}",
        )


def restore_boolean(apps, schema_editor):
    Task = apps.get_model("task_pages", "Task")
    tasks = Task.objects.using(schema_editor.connection.alias)
    tasks.update(is_completed=False)
    tasks.filter(status="completed").update(is_completed=True)


class Migration(migrations.Migration):
    dependencies = [("task_pages", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="task", name="status",
            field=models.CharField(
                "Статус", max_length=10, default="active",
                choices=[("active", "Активна"), ("completed", "Выполнена"),
                         ("cancelled", "Отменена")],
            ),
        ),
        migrations.AddField(
            model_name="task", name="slug",
            field=models.SlugField("Адрес", max_length=240, blank=True),
        ),
        migrations.RunPython(transfer_data, restore_boolean),
        migrations.AlterField(
            model_name="task", name="slug",
            field=models.SlugField(
                "Адрес", max_length=240, blank=True, unique=True,
            ),
        ),
        migrations.RemoveField(model_name="task", name="is_completed"),
        migrations.AddField(
            model_name="task", name="deadline_year",
            field=models.GeneratedField(
                expression=ExtractYear("deadline"),
                output_field=models.IntegerField(), db_persist=True,
                verbose_name="Год срока",
            ),
        ),
        migrations.AddConstraint(
            model_name="task",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    status__in=["active", "completed", "cancelled"],
                ), name="task_valid_status",
            ),
        ),
    ]
