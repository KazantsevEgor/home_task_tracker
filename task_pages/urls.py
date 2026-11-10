from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.tasks, name='list'),
    path('create/', views.task_create, name='create'),
    path('<int:task_id>/edit/', views.task_edit, name='edit'),
    path('<int:task_id>/cancel/', views.task_cancel, name='cancel'),
    path('<int:task_id>/delete/', views.task_delete, name='delete'),
    path('<int:task_id>/', views.task_detail, name='detail'),
    path('by-slug/<slug:slug>/', views.task_detail, name='detail_slug'),
    path('active/', views.active_tasks, name='active'),
    path('due/', views.tasks_due, name='due'),
    path('statistics/', views.statistics, name='statistics'),
]
