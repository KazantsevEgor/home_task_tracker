from django.contrib import admin
from django.db.models import Count

from .models import Category, Task

admin.site.site_header = "Трекер домашних задач — управление"
admin.site.site_title = "Трекер задач"
admin.site.index_title = "Администрирование"


class TaskInline(admin.TabularInline):
    model = Task
    fields = ("name", "deadline", "status")
    extra = 0
    show_change_link = True
    ordering = ("deadline", "id")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "task_count")
    search_fields = ("name",)
    ordering = ("name", "id")
    list_per_page = 20
    inlines = (TaskInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            task_total=Count("tasks"),
        )

    @admin.display(description="Количество задач", ordering="task_total")
    def task_count(self, obj):
        return obj.task_total


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "deadline", "status", "overdue")
    list_display_links = ("id", "name")
    list_filter = ("category", "status", "deadline", "deadline_year")
    search_fields = ("name", "category__name")
    list_select_related = ("category",)
    ordering = ("deadline", "id")
    list_per_page = 20
    date_hierarchy = "deadline"
    readonly_fields = ("slug", "deadline_year")
    autocomplete_fields = ("category",)
    fieldsets = (
        (None, {"fields": ("name", "category", "description", "image")}),
        ("Выполнение", {"fields": ("deadline", "status")}),
        ("Вычисляемые значения", {"fields": ("slug", "deadline_year")}),
    )

    @admin.display(boolean=True, description="Просрочена")
    def overdue(self, obj):
        return obj.is_overdue
