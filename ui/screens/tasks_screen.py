# ui/screens/tasks_screen.py
import flet as ft
from db.database import SessionLocal, get_tasks, create_task, complete_task, delete_task, get_task_session_count
from db.models import CATEGORIES
from ui.theme import COLORS

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
        self.selected_category = "work"

        self.task_input = ft.TextField(
            hint_text="Новая задача...",
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            expand=True,
            on_submit=self.on_add_task,
        )

        self.add_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE,
            icon_color=COLORS["primary"],
            icon_size=32,
            on_click=self.on_add_task,
        )

        # НОВОЕ: категории как цветные чипы
        self.category_chips = ft.Row(
            spacing=8,
            controls=self._build_category_chips(),
        )

        # НОВОЕ: Toggle вместо checkbox (ИСПРАВЛЕНО: label_text_style)
        self.show_done_toggle = ft.Switch(
            label="Выполненные",
            value=False,
            active_color=COLORS["primary"],
            inactive_thumb_color=COLORS["text_secondary"],
            on_change=self.on_filter_change,
            label_text_style=ft.TextStyle(size=13, color=COLORS["text_secondary"]),
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
                    self.add_button,
                ], tight=True),
                padding=ft.padding.Padding(20, 15, 20, 10),
                bgcolor=COLORS["bg"],
            ),
            ft.Container(
                content=self.category_chips,
                padding=ft.padding.Padding(20, 0, 20, 10),
                bgcolor=COLORS["bg"],
            ),
            ft.Container(
                content=self.show_done_toggle,
                padding=ft.padding.Padding(20, 0, 20, 10),
                bgcolor=COLORS["bg"],
            ),
            self.tasks_list,
        ]

        self.load_tasks()

    def _build_category_chips(self):
        """Создаёт цветные чипы категорий"""
        chips = []
        for key, label in CATEGORIES.items():
            color = CATEGORY_COLORS.get(key, COLORS["primary"])
            is_selected = key == self.selected_category

            def make_on_click(cat_key):
                def handler(e):
                    self.selected_category = cat_key
                    self._update_chips()
                return handler

            chips.append(
                ft.Container(
                    content=ft.Text(
                        label,
                        size=13,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                        color=COLORS["bg"] if is_selected else color,
                    ),
                    bgcolor=color if is_selected else COLORS["surface"],
                    border_radius=16,
                    padding=ft.padding.Padding(12, 6, 12, 6),
                    on_click=make_on_click(key),
                    ink=True,
                    border=ft.BorderSide(1.5, color) if not is_selected else None,
                )
            )
        return chips

    def _update_chips(self):
        """Обновляет визуальное состояние чипов"""
        self.category_chips.controls = self._build_category_chips()
        self._page.update()

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
            margin=ft.Margin(0, 0, 0, 5),
        )

    def on_add_task(self, e):
        title = self.task_input.value.strip()
        if not title:
            return
        with SessionLocal() as db:
            create_task(db, title, self.selected_category)
        self.task_input.value = ""
        self._page.update()
        self.load_tasks()

    def on_filter_change(self, e):
        self.show_done = self.show_done_toggle.value
        self.load_tasks()