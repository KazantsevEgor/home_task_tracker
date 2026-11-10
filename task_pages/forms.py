from django import forms
from django.utils import timezone

from .models import Category, Task


SORTS = {
    "deadline": ("deadline", "id"),
    "-deadline": ("-deadline", "id"),
    "name": ("name", "id"),
    "category": ("category__name", "deadline", "id"),
}
SORT_LABELS = {
    "deadline": "Сначала ближайшие сроки",
    "-deadline": "Сначала дальние сроки",
    "name": "По названию",
    "category": "По категории",
}


def date_widget():
    return forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(
                field.widget, forms.Select,
            ) else "form-control"
            field.widget.attrs["class"] = css


class TaskFilterForm(StyledFormMixin, forms.Form):
    category = forms.ModelChoiceField(
        Category.objects.order_by("name"), to_field_name="name",
        label="Категория", required=False, empty_label="Все категории",
    )
    status = forms.ChoiceField(
        label="Статус", required=False,
        choices=[("", "Все статусы"), *Task.Status.choices,
                 ("overdue", "Просроченные")],
    )
    q = forms.CharField(label="Поиск", required=False, max_length=200)
    search_in = forms.ChoiceField(
        label="Искать в", required=False, initial="all",
        choices=[("all", "Названии и категории"), ("name", "Названии")],
    )
    from_date = forms.DateField(
        label="Срок не раньше", required=False, widget=date_widget(),
    )
    date = forms.DateField(
        label="Срок не позже", required=False, widget=date_widget(),
        error_messages={"invalid": "Некорректная дата. Введите ГГГГ-ММ-ДД."},
    )
    sort = forms.ChoiceField(
        label="Сортировка", required=False, choices=list(SORT_LABELS.items()),
        initial="deadline",
    )

    def clean(self):
        data = super().clean()
        start, end = data.get("from_date"), data.get("date")
        if start and end and start > end:
            raise forms.ValidationError(
                "Начало периода не может быть позже его окончания."
            )
        return data


class DueDateForm(StyledFormMixin, forms.Form):
    date = forms.DateField(
        label="Дата", widget=date_widget(),
        error_messages={"invalid": "Некорректная дата. Введите ГГГГ-ММ-ДД."},
    )


def validate_image_size(image):
    if image.size > 5 * 1024 * 1024:
        raise forms.ValidationError(
            "Размер изображения не должен превышать 5 МБ."
        )


class TaskForm(StyledFormMixin, forms.ModelForm):
    description = forms.CharField(
        label="Описание", required=False, max_length=2000,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Подробности задачи, до 2000 символов.",
    )
    image = forms.ImageField(
        label="Изображение", required=False, validators=[validate_image_size],
        help_text="PNG, JPEG или WebP, не более 5 МБ.",
    )

    class Meta:
        model = Task
        fields = ("name", "category", "deadline", "status",
                  "description", "image")
        widgets = {"deadline": date_widget()}
        help_texts = {"name": "Не менее 3 символов."}

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if len(name) < 3:
            raise forms.ValidationError(
                "Название должно содержать от 3 символов."
            )
        return name

    def clean_deadline(self):
        deadline = self.cleaned_data["deadline"]
        unchanged = self.instance.pk and deadline == self.instance.deadline
        if deadline < timezone.localdate() and not unchanged:
            raise forms.ValidationError(
                "Нельзя назначить новый срок в прошлом."
            )
        return deadline

    def clean_image(self):
        image = self.cleaned_data.get("image")
        # Существующее изображение и отметка удаления не являются загрузками.
        if image and hasattr(image, "image"):
            if image.image.format not in {"PNG", "JPEG", "WEBP"}:
                raise forms.ValidationError(
                    "Допустимы только PNG, JPEG и WebP."
                )
        return image

    def clean(self):
        data = super().clean()
        name, category, deadline = (
            data.get("name"), data.get("category"), data.get("deadline")
        )
        if (name and category and deadline
                and data.get("status") == Task.Status.ACTIVE):
            duplicates = Task.objects.active().filter(
                name=name, category=category, deadline=deadline,
            ).exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise forms.ValidationError(
                    "Активная задача с таким названием, категорией "
                    "и сроком уже существует."
                )
        return data
