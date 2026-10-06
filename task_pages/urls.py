from django.urls import path

from . import views

urlpatterns = [
    path('', views.tasks, name='tasks'),
    path('<int:task_id>/', views.task_detail, name='task_detail'),
]
