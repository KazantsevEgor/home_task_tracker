from datetime import date


def input_int(prompt: str) -> int:
    """Запросить у пользователя целое число."""
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Ошибка: введите целое число.")


def input_date(prompt: str) -> date:
    """Запросить у пользователя дату в формате ГГГГ-ММ-ДД."""
    while True:
        try:
            raw = input(prompt)
            return date.fromisoformat(raw)
        except ValueError:
            print("Ошибка: введите дату в формате ГГГГ-ММ-ДД.")
