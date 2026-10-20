from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.tasks, name='list'),
    path('<int:task_id>/', views.task_detail, name='detail'),
]
