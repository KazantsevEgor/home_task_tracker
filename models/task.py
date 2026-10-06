from datetime import date


class Task:
    """Домашняя задача."""

    def __init__(
        self,
        task_id: int,
        name: str,
        category: str,
        deadline: str,
        is_completed: bool = False,
    ) -> None:
        self.id = task_id
        self.name = name
        self.category = category
        self.deadline = deadline
        self.is_completed = is_completed

    def mark_completed(self) -> None:
        self.is_completed = True

    def cancel_completion(self) -> None:
        self.is_completed = False

    def get_status(self) -> str:
        if self.is_completed:
            return "Задача выполнена"
        elif date.today() > date.fromisoformat(self.deadline):
            return "Задача просрочена"
        else:
            return "Задача в процессе"

    def days_until_deadline(self) -> int:
        return (date.fromisoformat(self.deadline) - date.today()).days

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "deadline": self.deadline,
            "is_completed": self.is_completed,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            task_id=data["id"],
            name=data["name"],
            category=data["category"],
            deadline=data["deadline"],
            is_completed=data.get("is_completed", False),
        )

    def __str__(self) -> str:
        status = self.get_status()
        return (
            f"[{self.id}] {self.name} ({self.category})"
            f" — до {self.deadline} — {status}"
        )
