# ui/screens/tasks_screen.py
import asyncio
import flet as ft
from db.database import (
    SessionLocal, get_tasks, create_task, complete_task,
    delete_task, get_task_session_count, update_task,
)
from db.models import CATEGORIES
from ui.theme import COLORS, SHADOWS, contrast_on, with_alpha
from ui.toast import show_toast
from ui.sheet import show_sheet, sheet_action

CATEGORY_COLORS = {
    "work": COLORS["cat_work"],
    "rest": COLORS["cat_rest"],
    "hobby": COLORS["cat_hobby"],
    "study": COLORS["cat_study"],
}


class TasksScreen(ft.Column):
    """Список задач: поиск, группировка по категориям, more-меню, empty states."""

    def __init__(self, page: ft.Page, on_focus_task=None):
        super().__init__(spacing=0, expand=True)
        self._page = page
        self.on_focus_task = on_focus_task
        self.show_done = False
        self.selected_category = "work"
        self.search_query = ""
        self._cards = []
        self._reveal_task = None

        self.task_input = ft.TextField(
            hint_text="Новая задача...",
            border_color=COLORS["primary"], color=COLORS["text"], bgcolor=COLORS["surface"],
            expand=True, on_submit=self.on_add_task,
        )
        self.add_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE, icon_color=COLORS["primary"], icon_size=32,
            on_click=self.on_add_task,
        )

        # Поиск: иконка-лупа через prefix_icon (без эмодзи в hint, чтобы не двоилось), на всю ширину.
        self.search_field = ft.TextField(
            hint_text="Поиск задач", expand=True,
            border_color=with_alpha(COLORS["text_secondary"], 0x55), color=COLORS["text"],
            bgcolor=COLORS["surface"], prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search,
        )

        self.category_chips = ft.Row(spacing=8, controls=self._build_category_chips(), scroll=ft.ScrollMode.AUTO)

        self.show_done_toggle = ft.Switch(
            label="Выполненные", value=False,
            active_color=COLORS["primary"], inactive_thumb_color=COLORS["text_secondary"],
            on_change=self.on_filter_change,
            label_text_style=ft.TextStyle(size=13, color=COLORS["text_secondary"]),
        )
        self.counter_text = ft.Text("", size=13, color=COLORS["text_secondary"])

        self.tasks_list = ft.ListView(expand=True, spacing=6, padding=20)

        self.controls = [
            ft.Container(
                content=ft.Row([self.task_input, self.add_button], tight=True),
                padding=ft.padding.Padding(20, 16, 20, 10), bgcolor=COLORS["bg"],
            ),
            ft.Container(content=self.search_field,
                         padding=ft.padding.Padding(20, 0, 20, 10), bgcolor=COLORS["bg"]),
            ft.Container(content=self.category_chips,
                         padding=ft.padding.Padding(20, 0, 20, 10), bgcolor=COLORS["bg"]),
            ft.Container(
                content=ft.Row([self.show_done_toggle, self.counter_text],
                               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.Padding(20, 0, 20, 10), bgcolor=COLORS["bg"],
            ),
            self.tasks_list,
        ]
        self.load_tasks()

    # ------------------------------------------------------------------ #
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
                        label, size=13,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                        color=contrast_on(color) if is_selected else color,
                    ),
                    bgcolor=color if is_selected else COLORS["surface"],
                    border_radius=16, padding=ft.padding.Padding(12, 6, 12, 6),
                    on_click=make_on_click(key), ink=True,
                    border=ft.BorderSide(1.5, color) if not is_selected else None,
                )
            )
        return chips

    def _update_chips(self):
        self.category_chips.controls = self._build_category_chips()
        self._page.update()

    def _on_search(self, e):
        self.search_query = (self.search_field.value or "").strip().lower()
        self.load_tasks()

    # ------------------------------------------------------------------ #
    def refresh_data(self):
        self.load_tasks(animate=True)

    def load_tasks(self, animate=False):
        if self._reveal_task and not self._reveal_task.done():
            self._reveal_task.cancel()

        self.tasks_list.controls.clear()
        self._cards = []

        with SessionLocal() as db:
            all_tasks = get_tasks(db, include_done=True)
            for t in all_tasks:
                t._count = get_task_session_count(db, t.id)

        active = [t for t in all_tasks if not t.is_done]
        done_count = len(all_tasks) - len(active)
        pool = all_tasks if self.show_done else active
        if self.search_query:
            pool = [t for t in pool if self.search_query in t.title.lower()]

        self.counter_text.value = (f"Всего {len(all_tasks)} • выполнено {done_count}"
                                   if self.show_done else f"Активных {len(active)}")

        if not pool:
            self.tasks_list.controls.append(self._empty_state(len(all_tasks) == 0))
            self._page.update()
            return

        for key, label in CATEGORIES.items():
            group = [t for t in pool if t.category == key]
            if not group:
                continue
            color = CATEGORY_COLORS.get(key, COLORS["primary"])
            self.tasks_list.controls.append(self._group_header(label, len(group), color))
            for task in group:
                card = self._create_task_card(task, task._count, start_hidden=animate)
                self._cards.append(card)
                self.tasks_list.controls.append(card)

        self._page.update()
        if animate:
            try:
                asyncio.get_running_loop()
                self._reveal_task = asyncio.create_task(self._reveal_cards())
            except RuntimeError:
                for c in self._cards:
                    c.opacity = 1.0
                self._page.update()

    def _group_header(self, label, count, color):
        return ft.Container(
            content=ft.Row([
                ft.Container(width=10, height=10, border_radius=5, bgcolor=color),
                ft.Text(label, size=13, weight=ft.FontWeight.BOLD,
                        color=COLORS["text_secondary"], expand=True),
                ft.Text(str(count), size=12, color=COLORS["text_secondary"]),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(4, 14, 4, 6),
        )

    def _empty_state(self, no_tasks_at_all):
        icon = ft.Icons.INBOX_OUTLINED if no_tasks_at_all else ft.Icons.SEARCH_OFF
        title = "Пока нет задач" if no_tasks_at_all else "Ничего не найдено"
        hint = ("Создайте первую задачу сверху —\nи запустите фокус в один тап."
                if no_tasks_at_all else "Попробуйте другой запрос\nили сбросьте фильтр.")
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=64, color=with_alpha(COLORS["text_secondary"], 0x80)),
                ft.Container(height=12),
                ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=6),
                ft.Text(hint, size=14, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=ft.padding.Padding(20, 60, 20, 40), alignment=ft.Alignment(0, 0),
        )

    async def _reveal_cards(self):
        try:
            for c in self._cards:
                await asyncio.sleep(0.04)
                c.opacity = 1.0
                self._page.update()
        except asyncio.CancelledError:
            pass

    # ------------------------------------------------------------------ #
    def _create_task_card(self, task, pomodoro_count, start_hidden=False):
        def toggle_done():
            new_val = not task.is_done
            with SessionLocal() as db:
                if new_val:
                    complete_task(db, task.id)
                else:
                    update_task(db, task.id, is_done=False)
            self.load_tasks()
            if new_val:
                show_toast(self._page, f"Выполнено: {task.title}",
                           ft.Icons.CHECK_CIRCLE, COLORS["success"],
                           action_label="Отменить", on_action=lambda ev: self._uncomplete(task.id))

        cat_color = CATEGORY_COLORS.get(task.category, COLORS["cat_work"])

        checkbox = ft.Checkbox(value=task.is_done, check_color=COLORS["primary"])
        check_zone = ft.Container(
            content=checkbox, width=48, height=48,
            alignment=ft.Alignment(0, 0), on_click=lambda e: toggle_done(), ink=True,
        )

        title_container = ft.Container(
            content=ft.Text(
                task.title, size=16,
                color=COLORS["text_secondary"] if task.is_done else COLORS["text"],
                italic=task.is_done, weight=ft.FontWeight.W_500,
            ),
            on_click=lambda e: self._show_edit_dialog(task), ink=True, expand=True,
        )

        badge = ft.Container(
            content=ft.Text(CATEGORIES.get(task.category, "Работа"), size=11,
                            weight=ft.FontWeight.BOLD, color=contrast_on(cat_color)),
            bgcolor=cat_color, border_radius=6, padding=ft.padding.Padding(7, 3, 7, 3),
        )
        tomato = ft.Text(f"🍅 {pomodoro_count}", size=13, color=COLORS["text_secondary"])

        more = ft.IconButton(
            icon=ft.Icons.MORE_VERT, icon_color=COLORS["text_secondary"],
            icon_size=22, tooltip="Ещё", on_click=lambda e: self._open_task_menu(task),
        )

        card = ft.Container(
            content=ft.Row([
                check_zone,
                ft.Column([title_container, ft.Row([badge, tomato], spacing=8)],
                          expand=True, spacing=5),
                more,
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(8, 12, 4, 12),
            border_radius=16, bgcolor=COLORS["surface"], shadow=SHADOWS["card"],
            margin=ft.Margin(0, 0, 0, 8),
            opacity=0.0 if start_hidden else 1.0,
            animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
        )
        card.on_hover = self._make_hover(card)
        if hasattr(card, "on_long_press"):
            card.on_long_press = lambda e: self._open_task_menu(task)
        return card

    def _make_hover(self, card):
        def h(e):
            hovered = str(getattr(e, "data", "")).lower() == "true"
            card.border = ft.BorderSide(1, COLORS["primary"]) if hovered else None
            card.shadow = SHADOWS["elevated"] if hovered else SHADOWS["card"]
            self._page.update()
        return h

    # ------------------------------------------------------------------ #
    def _open_task_menu(self, task):
        def build(close):
            is_done = task.is_done
            return [
                sheet_action(ft.Icons.PLAY_CIRCLE_FILLED, "Начать фокус",
                             lambda e: (close(), self._focus(task))),
                sheet_action(ft.Icons.EDIT_OUTLINED, "Редактировать название",
                             lambda e: (close(), self._show_edit_dialog(task))),
                sheet_action(ft.Icons.LABEL_OUTLINED, "Категория",
                             lambda e: self._open_category_sheet(task)),
                sheet_action(
                    ft.Icons.UNDO if is_done else ft.Icons.CHECK_CIRCLE_OUTLINE,
                    "Вернуть в активные" if is_done else "Отметить выполненной",
                    lambda e: (close(), self._toggle_from_menu(task)),
                ),
                sheet_action(ft.Icons.DELETE_OUTLINE, "Удалить",
                             lambda e: (close(), self._delete(task)), danger=True),
            ]

        show_sheet(self._page, task.title, build)

    def _open_category_sheet(self, task):
        def build(close):
            rows = []
            for key, label in CATEGORIES.items():
                color = CATEGORY_COLORS.get(key, COLORS["primary"])

                def pick(k):
                    def handler(e):
                        if k != task.category:
                            with SessionLocal() as db:
                                update_task(db, task.id, category=k)
                            self.load_tasks()
                        close()
                    return handler

                rows.append(sheet_action(ft.Icons.CIRCLE, label, pick(key),
                                         icon_color=color, selected=(key == task.category)))
            return rows

        show_sheet(self._page, "Категория", build)

    def _focus(self, task):
        if self.on_focus_task:
            self.on_focus_task(task.id, task.category)

    def _toggle_from_menu(self, task):
        new_val = not task.is_done
        with SessionLocal() as db:
            if new_val:
                complete_task(db, task.id)
            else:
                update_task(db, task.id, is_done=False)
        self.load_tasks()
        if new_val:
            show_toast(self._page, f"Выполнено: {task.title}",
                       ft.Icons.CHECK_CIRCLE, COLORS["success"],
                       action_label="Отменить", on_action=lambda ev: self._uncomplete(task.id))

    def _delete(self, task):
        title, cat, done = task.title, task.category, task.is_done
        with SessionLocal() as db:
            delete_task(db, task.id)
        self.load_tasks()
        show_toast(self._page, f"Удалено: {title}", ft.Icons.DELETE_OUTLINE, COLORS["error"],
                   action_label="Отменить", on_action=lambda ev: self._restore_task(title, cat, done))

    def _restore_task(self, title, category, was_done):
        with SessionLocal() as db:
            t = create_task(db, title, category)
            if was_done:
                complete_task(db, t.id)
        self.load_tasks()
        show_toast(self._page, "Задача восстановлена", ft.Icons.UNDO, COLORS["success"], duration=2500)

    def _uncomplete(self, task_id):
        with SessionLocal() as db:
            update_task(db, task_id, is_done=False)
        self.load_tasks()
        show_toast(self._page, "Возвращено в активные", ft.Icons.UNDO, COLORS["success"], duration=2500)

    # ------------------------------------------------------------------ #
    def _show_edit_dialog(self, task):
        edit_field = ft.TextField(
            value=task.title, label="Название задачи",
            border_color=COLORS["primary"], color=COLORS["text"],
            bgcolor=COLORS["surface"], width=300, autofocus=True,
        )

        def on_save(e):
            new_title = edit_field.value.strip()
            if new_title and new_title != task.title:
                with SessionLocal() as db:
                    update_task(db, task.id, title=new_title)
                self.load_tasks()
            dialog.open = False
            self._page.update()

        edit_field.on_submit = on_save
        dialog = ft.AlertDialog(
            title=ft.Text("Редактировать задачу"), content=edit_field,
            actions=[ft.TextButton("Отмена", on_click=lambda e: self._close_dialog(dialog)),
                     ft.TextButton("Сохранить", on_click=on_save)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self._page.update()

    # ------------------------------------------------------------------ #
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