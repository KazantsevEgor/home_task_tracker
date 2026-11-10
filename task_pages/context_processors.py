from django.utils.functional import SimpleLazyObject

from .models import Task


def tracker_context(request):
    return {
        "tracker_name": "Трекер домашних задач",
        "tracker_active_count": SimpleLazyObject(
            lambda: Task.objects.active().count(),
        ),
    }
