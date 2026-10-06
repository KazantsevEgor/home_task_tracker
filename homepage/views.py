from django.http import HttpResponse


def page(title, content):
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{bootstrap}">
</head>
<body>
    <nav class="nav">
        <a class="nav-link" href="/">Главная</a>
        <a class="nav-link" href="/tasks/">Задачи</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


def index(request):
    content = """
<h1 class="display-4">Трекер домашних задач</h1>
<p class="lead">Планирование и контроль выполнения домашних дел.</p>
<p>Основные разделы:</p>
<a href="/tasks/" class="btn btn-primary">Задачи</a>
"""
    return HttpResponse(page("Трекер домашних задач", content))
