from datetime import date

from completions import cancel_completion, check_status, complete_task
from storage import load_tasks, save_tasks
from tasks import add_task, filter_tasks_by_category, find_task, sort_tasks
from utils import input_date, input_int

TASKS_FILE = "data/tasks.json"


def show_tasks(tasks: list[dict]) -> None:
    """Вывести список задач в виде таблицы."""
    if not tasks:
        print("Задач нет.")
        return
    cols = f"{'ID':<5} {'Название':<25} {'Категория':<15} {'Дедлайн':<12}"
    print(f"\n{cols} Статус")
    print("-" * 72)
    for task in tasks:
        deadline = date.fromisoformat(task["deadline"])
        status = check_status(task["is_completed"], deadline)
        print(
            f"{task['id']:<5} {task['name']:<25} "
            f"{task['category']:<15} {task['deadline']:<12} {status}"
        )


def main() -> None:
    """Точка запуска приложения."""
    tasks = load_tasks(TASKS_FILE)

    while True:
        print("\n=== Трекер домашних задач ===")
        print("1. Показать все задачи")
        print("2. Найти задачу по названию")
        print("3. Фильтр по категории")
        print("4. Показать задачи по дедлайну")
        print("5. Добавить задачу")
        print("6. Отметить задачу выполненной")
        print("7. Снять отметку выполнения")
        print("0. Выход")

        choice = input_int("\nВыберите действие: ")

        if choice == 1:
            show_tasks(tasks)
        elif choice == 2:
            query = input("Подстрока названия: ")
            results = find_task(tasks, query)
            show_tasks(results)
        elif choice == 3:
            category = input("Категория: ")
            results = list(filter_tasks_by_category(tasks, category))
            show_tasks(results)
        elif choice == 4:
            show_tasks(sort_tasks(tasks))
        elif choice == 5:
            name = input("Название задачи: ")
            category = input("Категория: ")
            deadline = input_date("Дедлайн (ГГГГ-ММ-ДД): ")
            add_task(tasks, name, category, deadline)
            save_tasks(TASKS_FILE, tasks)
            print("Задача добавлена.")
        elif choice == 6:
            task_id = input_int("ID задачи: ")
            if complete_task(tasks, task_id):
                save_tasks(TASKS_FILE, tasks)
                print("Задача отмечена выполненной.")
            else:
                print("Задача не найдена или уже выполнена.")
        elif choice == 7:
            task_id = input_int("ID задачи: ")
            if cancel_completion(tasks, task_id):
                save_tasks(TASKS_FILE, tasks)
                print("Отметка выполнения снята.")
            else:
                print("Задача не найдена.")
        elif choice == 0:
            print("Выход.")
            break
        else:
            print("Неверный выбор, попробуйте снова.")


if __name__ == "__main__":
    main()
