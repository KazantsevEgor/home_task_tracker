import os
import re
import sys

import django
from django.test import Client
from django.test.utils import setup_test_environment

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracker.settings")
django.setup()
setup_test_environment()

client = Client()


def get_html(url):
    return client.get(url).content.decode()


def test_index_uses_base_template():
    response = client.get("/")
    html = response.content.decode()
    assert response.status_code == 200
    assert re.search(
        r"<title>\s*Главная - Трекер домашних задач\s*</title>", html
    )
    assert "homepage/css/style.css" in html
    assert "homepage/js/main.js" in html
    assert "homepage/img/logo.png" in html


def test_navigation_links_are_built_by_url_tag():
    html = get_html("/")
    for url in ("/", "/tasks/", "/tasks/active/", "/tasks/statistics/"):
        assert f'href="{url}"' in html
    assert "{%" not in html


def test_task_list_shows_data_from_sqlite():
    response = client.get("/tasks/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Всего задач: 6" in html
    assert html.count("task-card") == 6
    assert 'href="/tasks/1/"' in html
    assert "Убрать кухню" in html


def test_task_list_filter_by_category():
    html = get_html("/tasks/?category=Уборка")
    assert "Всего задач: 3" in html
    assert "Убрать кухню" in html
    assert "Купить продукты" not in html


def test_task_list_unknown_category_is_empty():
    html = get_html("/tasks/?category=Несуществующая")
    assert "Задачи не найдены." in html


def test_category_parameter_is_not_inserted_into_sql():
    html = get_html("/tasks/?category=' OR '1'='1")
    assert "Задачи не найдены." in html


def test_status_badges_come_from_sql_columns():
    assert "task-status-overdue" in get_html("/tasks/1/")
    assert "task-status-completed" in get_html("/tasks/2/")
    assert "task-status-active" in get_html("/tasks/5/")


def test_task_detail_found():
    response = client.get("/tasks/1/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Убрать кухню" in html
    assert "Уборка" in html
    assert "к списку задач" in html


def test_task_detail_not_found_returns_404():
    response = client.get("/tasks/9999/")
    assert response.status_code == 404
    assert "Задача не найдена" in response.content.decode()


def test_non_numeric_task_id_returns_404():
    assert client.get("/tasks/abc/").status_code == 404


def test_active_tasks_exclude_completed():
    html = get_html("/tasks/active/")
    assert "Невыполненных задач: 5" in html
    assert "Убрать кухню" in html
    assert "Купить продукты" not in html


def test_tasks_due_without_date_shows_only_form():
    html = get_html("/tasks/due/")
    assert '<input' in html
    assert "Срок не позже" not in html


def test_tasks_due_filters_by_date():
    html = get_html("/tasks/due/?date=2026-10-31")
    assert "Срок не позже 2026-10-31" in html
    assert "Купить лампочки" in html
    assert "Помыть окна" not in html
    assert "Купить продукты" not in html


def test_tasks_due_empty_result():
    html = get_html("/tasks/due/?date=2000-01-01")
    assert "подходящих задач нет" in html


def test_tasks_due_invalid_date():
    html = get_html("/tasks/due/?date=abc")
    assert "Некорректная дата" in html
    html = get_html("/tasks/due/?date=2026-01-01'; DROP TABLE tasks;--")
    assert "Некорректная дата" in html
    assert "Всего задач: 6" in get_html("/tasks/")


def test_statistics_page():
    response = client.get("/tasks/statistics/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Всего задач: 6" in html
    assert "Выполнено: 1" in html
    assert "Уборка: 3" in html
    assert "Покупки: 2" in html
    assert "Ремонт: 1" not in html
