# ui/screens/tasks_screen.py
import flet as ft
from db.database import SessionLocal, get_tasks, create_task, complete_task, delete_task, get_task_session_count
from db.models import CATEGORIES
from ui.theme import COLORS

# Цвета для категорий
CATEGORY_COLORS = {
    "work": COLORS["cat_work"],
    "rest": COLORS["cat_rest"],
    "hobby": COLORS["cat_hobby"],
    "study": COLORS["cat_study"],
}

class TasksScreen(ft.Column):
    def __init__(self, page: ft.Page, on_focus_task=None):
        super().__init__(
            spacing=0,
            expand=True,
        )
        self._page = page
        self.on_focus_task = on_focus_task
        self.show_done = False

        self.task_input = ft.TextField(
            hint_text="Новая задача...",
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            expand=True,
            on_submit=self.on_add_task,
        )

        self.category_dropdown = ft.Dropdown(
            width=120,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            value="work",
            options=[
                ft.dropdown.Option(key=k, text=v) for k, v in CATEGORIES.items()
            ],
        )

        self.add_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE,
            icon_color=COLORS["primary"],
            icon_size=32,
            on_click=self.on_add_task,
        )

        self.filter_checkbox = ft.Checkbox(
            label="Показать выполненные",
            value=self.show_done,
            on_change=self.on_filter_change,
            check_color=COLORS["primary"],
        )

        self.tasks_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
        )

        self.controls = [
            ft.Container(
                content=ft.Row([
                    self.task_input,
                    self.category_dropdown,
                    self.add_button,
                ], tight=True),
                padding=20,
                bgcolor=COLORS["bg"],
            ),
            ft.Container(
                content=self.filter_checkbox,
                padding=ft.padding.Padding(20, 0, 0, 10),
                bgcolor=COLORS["bg"],
            ),
            self.tasks_list,
        ]

        self.load_tasks()

    def refresh_data(self):
        self.load_tasks()

    def load_tasks(self):
        self.tasks_list.controls.clear()
        with SessionLocal() as db:
            tasks = get_tasks(db, include_done=self.show_done)
            for task in tasks:
                count = get_task_session_count(db, task.id)
                self.tasks_list.controls.append(self._create_task_card(task, count))
        self._page.update()

    def _create_task_card(self, task, pomodoro_count):
        def on_check(e):
            with SessionLocal() as db:
                complete_task(db, task.id)
            self.load_tasks()

        def on_delete(e):
            with SessionLocal() as db:
                delete_task(db, task.id)
            self.load_tasks()

        def on_focus(e):
            if self.on_focus_task:
                self.on_focus_task(task.id, task.category)

        category_label = CATEGORIES.get(task.category, "Работа")
        cat_color = CATEGORY_COLORS.get(task.category, COLORS["cat_work"])

        # Цветовой тег категории
        category_badge = ft.Container(
            content=ft.Text(
                category_label,
                size=11,
                color=COLORS["bg"],
                weight=ft.FontWeight.BOLD,
            ),
            bgcolor=cat_color,
            border_radius=6,
            padding=ft.padding.Padding(6, 2, 6, 2),
        )

        # Счётчик помидоров
        tomato_text = ft.Text(
            f"🍅 {pomodoro_count}",
            size=13,
            color=COLORS["text_secondary"],
        )

        return ft.Container(
            content=ft.Row([
                ft.Checkbox(
                    value=task.is_done,
                    on_change=on_check,
                    check_color=COLORS["primary"],
                ),
                ft.Column([
                    ft.Text(
                        task.title,
                        size=16,
                        color=COLORS["text_secondary"] if task.is_done else COLORS["text"],
                        italic=task.is_done,
                    ),
                    ft.Row([
                        category_badge,
                        tomato_text,
                    ], spacing=8),
                ], expand=True, spacing=4),
                ft.IconButton(
                    icon=ft.Icons.PLAY_CIRCLE_FILLED,
                    icon_color=COLORS["primary"],
                    on_click=on_focus,
                    tooltip="Начать фокус",
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=COLORS["error"],
                    on_click=on_delete,
                ),
            ]),
            padding=10,
            border_radius=10,
            bgcolor=COLORS["surface"],
            margin=ft.margin.Margin(0, 0, 0, 5),
        )

    def on_add_task(self, e):
        title = self.task_input.value.strip()
        if not title:
            return
        category = self.category_dropdown.value or "work"
        with SessionLocal() as db:
            create_task(db, title, category)
        self.task_input.value = ""
        self._page.update()
        self.load_tasks()

    def on_filter_change(self, e):
        self.show_done = self.filter_checkbox.value
        self.load_tasks()