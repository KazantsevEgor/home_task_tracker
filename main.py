from datetime import date, timedelta

task_name = "Убрать кухню"
category = "Уборка"
deadline_days = 2
is_completed = False

today = date.today()
deadline = today + timedelta(days=deadline_days)

def check_status(is_completed, deadline):
    if is_completed:
        return "Задача выполнена"
    elif not is_completed and date.today() > deadline:
        return "Задача просрочена" 
    else:
        return "Задача в процессе"
        
task_status = check_status(is_completed, deadline) 

print(f"Задача: {task_name}")
print(f"Категория: {category}")
print(f"Срок выполнения: {deadline}")
print(f"Статус: {task_status}")
