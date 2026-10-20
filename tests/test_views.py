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
    html = client.get("/").content.decode()
    assert 'href="/"' in html
    assert 'href="/tasks/"' in html
    assert "{%" not in html


def test_task_list_shows_count_and_cards():
    response = client.get("/tasks/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Всего задач: 3" in html
    assert html.count("task-card") == 3
    assert 'href="/tasks/1/"' in html


def test_task_list_status_badges():
    html = client.get("/tasks/").content.decode()
    assert "task-status-completed" in html
    assert "task-status-overdue" in html


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
