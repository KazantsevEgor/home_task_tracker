from datetime import date


def input_int(numb: str) -> int:
    """Запросить у пользователя целое число."""
    while True:
        try:
            return int(input(numb))
        except ValueError:
            print("Ошибка: введите целое число.")


def input_date(user_date: str) -> date:
    """Запросить у пользователя дату в формате ГГГГ-ММ-ДД."""
    while True:
        try:
            raw = input(user_date)
            return date.fromisoformat(raw)
        except ValueError:
            print("Ошибка: введите дату в формате ГГГГ-ММ-ДД.")
