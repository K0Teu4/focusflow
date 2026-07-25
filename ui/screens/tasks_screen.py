# ui/screens/tasks_screen.py
import asyncio
import flet as ft
from db.database import (
    SessionLocal, get_tasks, create_task, complete_task,
    delete_task, get_task_session_count, update_task,
)
from db.models import CATEGORIES
from ui.theme import COLORS, SHADOWS
from ui.toast import show_toast

CATEGORY_COLORS = {
    "work": COLORS["cat_work"],
    "rest": COLORS["cat_rest"],
    "hobby": COLORS["cat_hobby"],
    "study": COLORS["cat_study"],
}


class TasksScreen(ft.Column):
    """Экран списка задач: категории, редактирование, счётчик, undo-тосты."""

    def __init__(self, page: ft.Page, on_focus_task=None):
        super().__init__(spacing=0, expand=True)
        self._page = page
        self.on_focus_task = on_focus_task
        self.show_done = False
        self.selected_category = "work"
        self._cards = []
        self._reveal_task = None

        # === ВВОД НОВОЙ ЗАДАЧИ ===
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

        # === ФИЛЬТР ПО КАТЕГОРИЯМ (цветные чипы) ===
        self.category_chips = ft.Row(spacing=8, controls=self._build_category_chips())

        # === ПЕРЕКЛЮЧАТЕЛЬ ВЫПОЛНЕННЫХ ===
        self.show_done_toggle = ft.Switch(
            label="Выполненные",
            value=False,
            active_color=COLORS["primary"],
            inactive_thumb_color=COLORS["text_secondary"],
            on_change=self.on_filter_change,
            label_text_style=ft.TextStyle(size=13, color=COLORS["text_secondary"]),
        )

        # === СЧЁТЧИК ЗАДАЧ ===
        self.counter_text = ft.Text("", size=13, color=COLORS["text_secondary"])

        # === СПИСОК ===
        self.tasks_list = ft.ListView(expand=True, spacing=10, padding=20)

        self.controls = [
            ft.Container(
                content=ft.Row([self.task_input, self.add_button], tight=True),
                padding=ft.padding.Padding(20, 15, 20, 10),
                bgcolor=COLORS["bg"],
            ),
            ft.Container(
                content=self.category_chips,
                padding=ft.padding.Padding(20, 0, 20, 10),
                bgcolor=COLORS["bg"],
            ),
            ft.Container(
                content=ft.Row([
                    self.show_done_toggle,
                    self.counter_text,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.Padding(20, 0, 20, 10),
                bgcolor=COLORS["bg"],
            ),
            self.tasks_list,
        ]
        self.load_tasks()

    # ------------------------------------------------------------------ #
    # ЧИПЫ КАТЕГОРИЙ                                                      #
    # ------------------------------------------------------------------ #
    def _build_category_chips(self):
        """Строит ряд цветных чипов-фильтров категорий."""
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
        """Перерисовывает чипы после смены выбранной категории."""
        self.category_chips.controls = self._build_category_chips()
        self._page.update()

    # ------------------------------------------------------------------ #
    # ЗАГРУЗКА И СЧЁТЧИК                                                  #
    # ------------------------------------------------------------------ #
    def refresh_data(self):
        """Обновление при переходе на вкладку — с каскадной анимацией."""
        self.load_tasks(animate=True)

    def load_tasks(self, animate=False):
        """Пересобирает список задач и (опционально) запускает каскад появления."""
        if self._reveal_task and not self._reveal_task.done():
            self._reveal_task.cancel()

        self.tasks_list.controls.clear()
        self._cards = []
        with SessionLocal() as db:
            all_tasks = get_tasks(db, include_done=True)
            tasks = all_tasks if self.show_done else [t for t in all_tasks if not t.is_done]
            done_count = sum(1 for t in all_tasks if t.is_done)
            active_count = len(all_tasks) - done_count
            for task in tasks:
                count = get_task_session_count(db, task.id)
                card = self._create_task_card(task, count, start_hidden=animate)
                self._cards.append(card)
                self.tasks_list.controls.append(card)

        if self.show_done:
            self.counter_text.value = f"Всего {len(all_tasks)} • выполнено {done_count}"
        else:
            self.counter_text.value = f"Активных {active_count}"

        self._page.update()

        if animate:
            try:
                asyncio.get_running_loop()
                self._reveal_task = asyncio.create_task(self._reveal_cards())
            except RuntimeError:
                for c in self._cards:
                    c.opacity = 1.0
                self._page.update()

    async def _reveal_cards(self):
        """Каскадное появление карточек (по одной с задержкой)."""
        try:
            for c in self._cards:
                await asyncio.sleep(0.045)
                c.opacity = 1.0
                self._page.update()
        except asyncio.CancelledError:
            pass

    # ------------------------------------------------------------------ #
    # КАРТОЧКА ЗАДАЧИ                                                     #
    # ------------------------------------------------------------------ #
    def _create_task_card(self, task, pomodoro_count, start_hidden=False):
        """Карточка задачи с hover-эффектом и анимацией появления."""
        def on_check(e):
            new_val = e.control.value
            with SessionLocal() as db:
                if new_val:
                    complete_task(db, task.id)
                else:
                    update_task(db, task.id, is_done=False)
            self.load_tasks()
            if new_val:
                show_toast(
                    self._page,
                    f"Выполнено: {task.title}",
                    ft.Icons.CHECK_CIRCLE, COLORS["success"],
                    action_label="Отменить",
                    on_action=lambda ev: self._uncomplete(task.id),
                )

        def on_delete(e):
            title, cat, done = task.title, task.category, task.is_done
            with SessionLocal() as db:
                delete_task(db, task.id)
            self.load_tasks()
            show_toast(
                self._page,
                f"Удалено: {title}",
                ft.Icons.DELETE_OUTLINE, COLORS["error"],
                action_label="Отменить",
                on_action=lambda ev: self._restore_task(title, cat, done),
            )

        def on_focus(e):
            if self.on_focus_task:
                self.on_focus_task(task.id, task.category)

        def on_edit_title(e):
            self._show_edit_dialog(task)

        def on_edit_category(e):
            self._show_category_dialog(task)

        category_label = CATEGORIES.get(task.category, "Работа")
        cat_color = CATEGORY_COLORS.get(task.category, COLORS["cat_work"])

        category_badge = ft.Container(
            content=ft.Row([
                ft.Text(category_label, size=11, color=COLORS["bg"], weight=ft.FontWeight.BOLD),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=14, color=COLORS["bg"]),
            ], spacing=0),
            bgcolor=cat_color,
            border_radius=6,
            padding=ft.padding.Padding(6, 2, 4, 2),
            on_click=on_edit_category,
            ink=True,
            tooltip="Изменить категорию",
        )
        tomato_text = ft.Text(f"🍅 {pomodoro_count}", size=13, color=COLORS["text_secondary"])

        title_row = ft.Row([
            ft.Text(
                task.title, size=16,
                color=COLORS["text_secondary"] if task.is_done else COLORS["text"],
                italic=task.is_done, expand=True,
            ),
            ft.Icon(ft.Icons.EDIT_OUTLINED, size=16, color=COLORS["text_secondary"]),
        ], spacing=6)
        title_container = ft.Container(
            content=title_row, on_click=on_edit_title, ink=True, tooltip="Редактировать название",
        )

        card = ft.Container(
            content=ft.Row([
                ft.Checkbox(value=task.is_done, on_change=on_check, check_color=COLORS["primary"]),
                ft.Column([
                    title_container,
                    ft.Row([category_badge, tomato_text], spacing=8),
                ], expand=True, spacing=4),
                ft.IconButton(icon=ft.Icons.PLAY_CIRCLE_FILLED, icon_color=COLORS["primary"],
                              on_click=on_focus, tooltip="Начать фокус"),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLORS["error"], on_click=on_delete),
            ]),
            padding=14,
            border_radius=16,
            bgcolor=COLORS["surface"],
            shadow=SHADOWS["card"],
            margin=ft.Margin(0, 0, 0, 8),
            opacity=0.0 if start_hidden else 1.0,
            animate=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
        )
        card.on_hover = self._make_hover(card)
        return card

    def _make_hover(self, card):
        """Hover: розовая рамка + усиленная тень при наведении."""
        def h(e):
            hovered = str(getattr(e, "data", "")).lower() == "true"
            if hovered:
                card.border = ft.BorderSide(1, COLORS["primary"])
                card.shadow = SHADOWS["elevated"]
            else:
                card.border = None
                card.shadow = SHADOWS["card"]
            self._page.update()
        return h

    # ------------------------------------------------------------------ #
    # UNDO-ДЕЙСТВИЯ                                                       #
    # ------------------------------------------------------------------ #
    def _restore_task(self, title, category, was_done):
        """Восстанавливает удалённую задачу."""
        with SessionLocal() as db:
            t = create_task(db, title, category)
            if was_done:
                complete_task(db, t.id)
        self.load_tasks()
        show_toast(self._page, "Задача восстановлена", ft.Icons.UNDO,
                   COLORS["success"], duration=2500)

    def _uncomplete(self, task_id):
        """Снимает отметку выполнения."""
        with SessionLocal() as db:
            update_task(db, task_id, is_done=False)
        self.load_tasks()
        show_toast(self._page, "Возвращено в активные", ft.Icons.UNDO,
                   COLORS["success"], duration=2500)

    # ------------------------------------------------------------------ #
    # РЕДАКТИРОВАНИЕ НАЗВАНИЯ                                             #
    # ------------------------------------------------------------------ #
    def _show_edit_dialog(self, task):
        """Диалог редактирования названия задачи."""
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

        def on_cancel(e):
            dialog.open = False
            self._page.update()

        edit_field.on_submit = on_save
        dialog = ft.AlertDialog(
            title=ft.Text("Редактировать задачу"),
            content=edit_field,
            actions=[
                ft.TextButton("Отмена", on_click=on_cancel),
                ft.TextButton("Сохранить", on_click=on_save),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    # ------------------------------------------------------------------ #
    # СМЕНА КАТЕГОРИИ                                                     #
    # ------------------------------------------------------------------ #
    def _show_category_dialog(self, task):
        """Диалог выбора категории задачи."""
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
                    ft.Text(cat_label, size=15, color=COLORS["text"],
                            weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL, expand=True),
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE if is_current else ft.Icons.CIRCLE_OUTLINED,
                        size=20, color=COLORS["primary"] if is_current else COLORS["text_secondary"],
                    ),
                ], spacing=10),
                padding=14,
                bgcolor=COLORS["primary"] + "30" if is_current else COLORS["surface"],
                border_radius=10, margin=ft.Margin(0, 0, 0, 6),
                on_click=on_select, ink=True,
                border=ft.BorderSide(1.5, COLORS["primary"]) if is_current else None,
            )

        dialog = ft.AlertDialog(
            title=ft.Text("Выберите категорию"),
            content=ft.Column([make_category_button(k, l) for k, l in CATEGORIES.items()],
                              spacing=0, height=250),
            actions=[ft.TextButton("Закрыть", on_click=lambda e: self._close_dialog(dialog))],
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self, dialog):
        """Закрывает переданный AlertDialog."""
        dialog.open = False
        self._page.update()

    # ------------------------------------------------------------------ #
    # ДОБАВЛЕНИЕ / ФИЛЬТР                                                 #
    # ------------------------------------------------------------------ #
    def on_add_task(self, e):
        """Создаёт задачу из поля ввода в выбранной категории."""
        title = self.task_input.value.strip()
        if not title:
            return
        with SessionLocal() as db:
            create_task(db, title, self.selected_category)
        self.task_input.value = ""
        self._page.update()
        self.load_tasks()

    def on_filter_change(self, e):
        """Переключает показ выполненных задач."""
        self.show_done = self.show_done_toggle.value
        self.load_tasks()