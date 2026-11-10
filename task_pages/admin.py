from django.contrib import admin

from .models import Category, Task


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "deadline", "is_completed")
    list_filter = ("category", "is_completed")
    search_fields = ("name", "category__name")
    list_select_related = ("category",)
