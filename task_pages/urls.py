from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.tasks, name='list'),
    path('<int:task_id>/', views.task_detail, name='detail'),
    path('active/', views.active_tasks, name='active'),
    path('due/', views.tasks_due, name='due'),
    path('statistics/', views.statistics, name='statistics'),
]
