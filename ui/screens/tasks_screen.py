# ui/screens/tasks_screen.py
import flet as ft
from db.database import SessionLocal, get_tasks, create_task, complete_task, delete_task, get_task_session_count, update_task
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

        self.category_chips = ft.Row(
            spacing=8,
            controls=self._build_category_chips(),
        )

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

        def on_edit_title(e):
            self._show_edit_dialog(task)

        def on_edit_category(e):
            self._show_category_dialog(task)

        category_label = CATEGORIES.get(task.category, "Работа")
        cat_color = CATEGORY_COLORS.get(task.category, COLORS["cat_work"])

        # НОВОЕ: категория с иконкой ▾
        category_badge = ft.Container(
            content=ft.Row([
                ft.Text(
                    category_label,
                    size=11,
                    color=COLORS["bg"],
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Icon(
                    ft.Icons.ARROW_DROP_DOWN,
                    size=14,
                    color=COLORS["bg"],
                ),
            ], spacing=0),
            bgcolor=cat_color,
            border_radius=6,
            padding=ft.padding.Padding(6, 2, 4, 2),
            on_click=on_edit_category,
            ink=True,
            tooltip="Изменить категорию",
        )

        tomato_text = ft.Text(
            f"🍅 {pomodoro_count}",
            size=13,
            color=COLORS["text_secondary"],
        )

        # НОВОЕ: название с иконкой ✏️
        title_row = ft.Row([
            ft.Text(
                task.title,
                size=16,
                color=COLORS["text_secondary"] if task.is_done else COLORS["text"],
                italic=task.is_done,
                expand=True,
            ),
            ft.Icon(
                ft.Icons.EDIT_OUTLINED,
                size=16,
                color=COLORS["text_secondary"],
            ),
        ], spacing=6)

        title_container = ft.Container(
            content=title_row,
            on_click=on_edit_title,
            ink=True,
            tooltip="Редактировать название",
        )

        return ft.Container(
            content=ft.Row([
                ft.Checkbox(
                    value=task.is_done,
                    on_change=on_check,
                    check_color=COLORS["primary"],
                ),
                ft.Column([
                    title_container,
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

    def _show_edit_dialog(self, task):
        edit_field = ft.TextField(
            value=task.title,
            label="Название задачи",
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            width=300,
            autofocus=True,
        )

        def on_save(e):
            new_title = edit_field.value.strip()
            if new_title and new_title != task.title:
                with SessionLocal() as db:
                    update_task(db, task.id, title=new_title)
                self.load_tasks()
            dialog.open = False
            self._page.update()

        def on_cancel(e):
            dialog.open = False
            self._page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Редактировать задачу"),
            content=edit_field,
            actions=[
                ft.TextButton("Отмена", on_click=on_cancel),
                ft.TextButton("Сохранить", on_click=on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def on_submit(e):
            on_save(e)
        edit_field.on_submit = on_submit

        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _show_category_dialog(self, task):
        def make_category_button(cat_key, cat_label):
            color = CATEGORY_COLORS.get(cat_key, COLORS["primary"])
            is_current = task.category == cat_key

            def on_select(e):
                if cat_key != task.category:
                    with SessionLocal() as db:
                        update_task(db, task.id, category=cat_key)
                    self.load_tasks()
                dialog.open = False
                self._page.update()

            return ft.Container(
                content=ft.Row([
                    ft.Container(width=12, height=12, border_radius=6, bgcolor=color),
                    ft.Text(
                        cat_label,
                        size=15,
                        color=COLORS["text"],
                        weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                        expand=True,
                    ),
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if is_current else ft.Icons.CIRCLE_OUTLINED,
                        size=20,
                        color=COLORS["primary"] if is_current else COLORS["text_secondary"],
                    ),
                ], spacing=10),
                padding=14,
                bgcolor=COLORS["primary"] + "30" if is_current else COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(0, 0, 0, 6),
                on_click=on_select,
                ink=True,
                border=ft.BorderSide(1.5, COLORS["primary"]) if is_current else None,
            )

        category_buttons = [
            make_category_button(key, label)
            for key, label in CATEGORIES.items()
        ]

        dialog = ft.AlertDialog(
            title=ft.Text("Выберите категорию"),
            content=ft.Column(
                category_buttons,
                spacing=0,
                height=250,
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self._page.update()

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