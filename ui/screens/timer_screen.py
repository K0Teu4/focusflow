# ui/screens/timer_screen.py
import flet as ft
import asyncio
from services.timer_service import TimerService
from db.database import (
    SessionLocal, get_tasks, get_today_stats, get_settings,
    get_task_by_id, create_task,
)
from services.premium_service import PremiumService
from db.models import CATEGORIES
from ui.theme import COLORS, GRADIENTS, SHADOWS, with_alpha
from ui.toast import show_toast
from ui.sheet import show_sheet, sheet_action


class TimerScreen(ft.Stack):
    """Таймер Pomodoro. Stack = скроллируемый контент + угловая кнопка Фокуса поверх."""

    def __init__(self, page: ft.Page, on_focus_task=None, on_enter_focus=None, on_open_premium=None):
        super().__init__(expand=True)
        self._page = page
        self.timer_service = TimerService()
        self.timer_service._sound_service.bind_page(page)
        self.selected_task_id = None
        self._auto_start_task = None
        self.on_focus_task = on_focus_task
        self.on_enter_focus = on_enter_focus
        self.on_open_premium = on_open_premium

        with SessionLocal() as db:
            self.is_premium = PremiumService.is_premium()

        # === КОЛЬЦО ===
        self.timer_bg = ft.Container(
            width=240, height=240, border_radius=120,
            gradient=GRADIENTS["work"],
            border=ft.BorderSide(2, with_alpha(COLORS["work"], 0x55)),
            alignment=ft.Alignment(0, 0), shadow=SHADOWS["elevated"],
            scale=1.0, animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            content=ft.ProgressRing(
                value=0.0, width=210, height=210, stroke_width=12,
                color=COLORS["work"], bgcolor=COLORS["surface_2"],
            ),
            margin=ft.Margin(0, 16, 0, 14),
        )
        self.progress_ring = self.timer_bg.content

        self.session_type_text = ft.Text(
            self.timer_service.get_session_type_display(),
            size=22, weight=ft.FontWeight.BOLD, color=COLORS["text"])
        self.progress_text = ft.Text(
            self._get_progress_display(), size=16,
            color=COLORS["text_secondary"], margin=ft.Margin(0, 0, 0, 8))
        self.time_display = ft.Text(
            self.timer_service.get_display_time(), size=58,
            weight=ft.FontWeight.BOLD, color=COLORS["work"],
            font_family="monospace", margin=ft.Margin(0, 0, 0, 8))
        self.current_task_text = ft.Text(
            "Без задачи", size=16, color=COLORS["text_secondary"],
            italic=True, margin=ft.Margin(0, 0, 0, 4))

        # === СЕЛЕКТОР ЗАДАЧИ ===
        self.select_task_button = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.PLAYLIST_ADD_CHECK, size=18, color=COLORS["primary"]),
                ft.Text("Выбрать задачу", size=14, color=COLORS["text"],
                        weight=ft.FontWeight.W_600, expand=True),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=22, color=COLORS["text_secondary"]),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(14, 12, 10, 12),
            bgcolor=COLORS["surface_2"], border_radius=12,
            border=ft.BorderSide(1, with_alpha(COLORS["primary"], 0x66)),
            on_click=self._show_task_picker_dialog, ink=True,
            width=260, margin=ft.Margin(0, 0, 0, 6))

        self.create_task_button = ft.TextButton(
            "+ Новая задача", style=ft.ButtonStyle(color=COLORS["primary"]),
            on_click=self._show_create_task_dialog, margin=ft.Margin(0, 0, 0, 18))

        # === УПРАВЛЕНИЕ ===
        self.start_button = ft.ElevatedButton(
            "Старт", bgcolor=COLORS["primary"], color=COLORS["bg"],
            on_click=self.on_start, width=140, height=48)
        self.pause_button = ft.ElevatedButton(
            "Пауза", bgcolor=COLORS["pause_work"], color=COLORS["bg"],
            on_click=self.on_pause, width=140, height=48, visible=False)
        self.skip_button = ft.ElevatedButton(
            "Пропустить", bgcolor=COLORS["skip"], color=COLORS["bg"],
            on_click=self.on_skip, width=140, height=44,
            visible=False, margin=ft.Margin(0, 8, 0, 0))
        self.reset_button = ft.OutlinedButton(
            "Сброс",
            style=ft.ButtonStyle(side=ft.BorderSide(1.5, COLORS["reset_border"]),
                                 color=COLORS["text_secondary"]),
            on_click=self.on_reset, width=110, height=38, margin=ft.Margin(0, 12, 0, 0))

        # === АВТОСТАРТ ===
        self.auto_start_bar = ft.ProgressBar(
            value=0.0, color=COLORS["primary"], bgcolor=COLORS["surface_2"],
            width=200, visible=False)
        self.auto_start_text = ft.Text(
            "", size=16, color=COLORS["primary"], weight=ft.FontWeight.W_600,
            visible=False, margin=ft.Margin(0, 8, 0, 0))
        self.cancel_auto_btn = ft.TextButton(
            "Отмена", style=ft.ButtonStyle(color=COLORS["text_secondary"]),
            on_click=self.on_cancel_auto_start, visible=False)

        self.task_dropdown = ft.Dropdown(
            label="Задача", hint_text="Выбрать задачу", width=280,
            border_color=COLORS["primary"], color=COLORS["text"],
            bgcolor=COLORS["surface"], visible=False)
        self.task_dropdown.on_change = self.on_task_change

        # === СТАТИСТИКА-КАРТОЧКА ===
        self.stat_sessions_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=COLORS["work"])
        self.stat_minutes_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=COLORS["primary"])
        self.stats_card = ft.Container(
            content=ft.Row([
                ft.Column([self.stat_sessions_text,
                           ft.Text("🍅 сессий", size=12, color=COLORS["text_secondary"])],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                ft.Container(width=1, height=34, bgcolor=with_alpha(COLORS["text_secondary"], 0x40)),
                ft.Column([self.stat_minutes_text,
                           ft.Text("минут", size=12, color=COLORS["text_secondary"])],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(20, 14, 20, 14),
            bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], width=260, margin=ft.Margin(0, 16, 0, 24))

        # === СКРОЛЛИРУЕМЫЙ КОНТЕНТ (без кнопки Фокуса в потоке) ===
        self.content_column = ft.Column(
            spacing=0, expand=True, scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(height=8),  # отступ под угловую кнопку
                self.timer_bg, self.session_type_text, self.progress_text, self.time_display,
                self.current_task_text, self.select_task_button, self.create_task_button,
                self.task_dropdown,
                ft.Row([self.start_button, self.pause_button],
                       alignment=ft.MainAxisAlignment.CENTER, spacing=12),
                self.skip_button, self.auto_start_text, self.auto_start_bar, self.cancel_auto_btn,
                self.reset_button, self.stats_card,
            ])

        # === УГЛОВАЯ КНОПКА ФОКУСА (поверх, не сдвигает круг) ===
        self.focus_icon = ft.Container(
            top=12, right=12, width=44, height=44, border_radius=22,
            bgcolor=with_alpha(COLORS["surface"], 0xCC),
            alignment=ft.Alignment(0, 0),
            content=ft.Icon(
                ft.Icons.FULLSCREEN if self.is_premium else ft.Icons.LOCK_OUTLINE,
                color=COLORS["primary"] if self.is_premium else COLORS["text_secondary"],
                size=22),
            on_click=self._on_focus_click, ink=True,
            tooltip="Режим Фокус" if self.is_premium else "Режим Фокус (Premium)",
            opacity=1.0 if self.is_premium else 0.55,
        )

        self.controls = [self.content_column, self.focus_icon]
        self.load_tasks()
        self.update_stats()

    # ------------------------------------------------------------------ #
    def _on_focus_click(self, e):
        if not self.is_premium:
            if self.on_open_premium:
                self.on_open_premium()
            return
        if self.on_enter_focus:
            self.on_enter_focus()

    def _pulse(self):
        self.timer_bg.scale = 1.06
        self._page.update()
        async def back():
            await asyncio.sleep(0.18)
            self.timer_bg.scale = 1.0
            self._page.update()
        asyncio.create_task(back())

    def _get_progress_display(self) -> str:
        return f"Сессия {self.timer_service.completed_work_sessions} из {self.timer_service.sessions_until_long_break}"

    def _cancel_auto_start_countdown(self):
        if self._auto_start_task and not self._auto_start_task.done():
            self._auto_start_task.cancel()
        self.auto_start_text.visible = False
        self.auto_start_bar.visible = False
        self.cancel_auto_btn.visible = False

    def refresh_data(self):
        self.timer_service.reload_settings()
        self.load_tasks()
        self.update_stats()
        self._apply_mode_colors()
        self._update_progress()
        self.time_display.value = self.timer_service.get_display_time()
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self.progress_text.value = self._get_progress_display()
        self._update_current_task_text()
        self._page.update()

    def load_tasks(self):
        with SessionLocal() as db:
            tasks = get_tasks(db)
            self.task_dropdown.options = [
                ft.dropdown.Option(key=str(t.id), text=t.title, data=t.category) for t in tasks]
        self._page.update()

    def update_stats(self):
        with SessionLocal() as db:
            stats = get_today_stats(db)
        self.stat_sessions_text.value = str(stats['work_sessions'])
        self.stat_minutes_text.value = str(stats['total_work_minutes'])

    def _update_current_task_text(self):
        selected = self.task_dropdown.value
        if selected:
            for opt in self.task_dropdown.options:
                if opt.key == selected:
                    self.current_task_text.value = f"▶ {opt.text}"
                    self.current_task_text.color = COLORS["primary"]
                    self.current_task_text.italic = False
                    return
        self.current_task_text.value = "Без задачи"
        self.current_task_text.color = COLORS["text_secondary"]
        self.current_task_text.italic = True

    def _show_task_picker_dialog(self, e):
        with SessionLocal() as db:
            tasks = get_tasks(db)
        def build(close):
            rows = []
            if not tasks:
                rows.append(sheet_action(
                    ft.Icons.ADD_CIRCLE, "Создать задачу",
                    lambda ev: (close(), self._show_create_task_dialog(ev))))
                return rows
            for task in tasks:
                cat_color = {"work": COLORS["cat_work"], "rest": COLORS["cat_rest"],
                             "hobby": COLORS["cat_hobby"], "study": COLORS["cat_study"]}.get(
                    task.category, COLORS["cat_work"])
                def pick(tid):
                    def handler(ev):
                        self.task_dropdown.value = str(tid)
                        self._update_session_label_from_dropdown()
                        self._update_current_task_text()
                        close()
                    return handler
                rows.append(sheet_action(ft.Icons.CIRCLE, task.title, pick(task.id), icon_color=cat_color))
            rows.append(sheet_action(ft.Icons.CLEAR_ALL, "Убрать задачу",
                                     lambda ev: (self._clear_task(), close())))
            return rows
        show_sheet(self._page, "Задача для фокуса", build)

    def _clear_task(self):
        self.task_dropdown.value = None
        self._update_current_task_text()
        self.timer_service.set_session_mode(True)
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self._apply_mode_colors()

    def _show_create_task_dialog(self, e):
        chosen = {"cat": "work"}
        title_field = ft.TextField(
            label="Название задачи", autofocus=True,
            border_color=COLORS["primary"], color=COLORS["text"], bgcolor=COLORS["surface"])
        def chip(key, label):
            color = {"work": COLORS["cat_work"], "rest": COLORS["cat_rest"],
                     "hobby": COLORS["cat_hobby"], "study": COLORS["cat_study"]}[key]
            sel = chosen["cat"] == key
            c = ft.Container(
                content=ft.Text(label, size=12, weight=ft.FontWeight.BOLD,
                                color=COLORS["bg"] if sel else color),
                bgcolor=color if sel else COLORS["surface"],
                border_radius=14, padding=ft.padding.Padding(10, 6, 10, 6), ink=True,
                border=ft.BorderSide(1.5, color) if not sel else None)
            def set_cat(ev):
                chosen["cat"] = key
                cat_row.controls = [chip(k, l) for k, l in CATEGORIES.items()]
                dialog.update()
            c.on_click = set_cat
            return c
        cat_row = ft.Row([chip(k, l) for k, l in CATEGORIES.items()], spacing=8, scroll=ft.ScrollMode.AUTO)
        def save(ev):
            t = (title_field.value or "").strip()
            if not t:
                return
            with SessionLocal() as db:
                new = create_task(db, t, chosen["cat"])
            dialog.open = False
            self._page.update()
            self.load_tasks()
            self.task_dropdown.value = str(new.id)
            self._update_session_label_from_dropdown()
            self._update_current_task_text()
            show_toast(self._page, f"Создано: {t}", ft.Icons.ADD_TASK, COLORS["success"], duration=2500)
        title_field.on_submit = save
        dialog = ft.AlertDialog(
            title=ft.Text("Новая задача"),
            content=ft.Column([title_field, ft.Container(height=6),
                               ft.Text("Категория", size=13, color=COLORS["text_secondary"]), cat_row],
                              spacing=6, tight=True),
            actions=[ft.TextButton("Отмена", on_click=lambda ev: self._close_dialog(dialog)),
                     ft.TextButton("Создать", on_click=save)],
            actions_alignment=ft.MainAxisAlignment.END)
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _apply_mode_colors(self):
        mode = self.timer_service.get_mode_key()
        if mode == "work":
            ring_color, gradient, pause_color = COLORS["work"], GRADIENTS["work"], COLORS["pause_work"]
        elif mode == "long_break":
            ring_color, gradient, pause_color = COLORS["long_break"], GRADIENTS["long_break"], COLORS["pause_rest"]
        else:
            ring_color, gradient, pause_color = COLORS["rest"], GRADIENTS["rest"], COLORS["pause_rest"]
        self.progress_ring.color = ring_color
        self.timer_bg.gradient = gradient
        self.timer_bg.border = ft.BorderSide(2, with_alpha(ring_color, 0x55))
        self.time_display.color = ring_color
        self.pause_button.bgcolor = pause_color
        self._apply_reset_style()
        is_rest = not self.timer_service.is_work_session
        self.select_task_button.visible = not is_rest
        self.create_task_button.visible = not is_rest
        if is_rest:
            selected = self.task_dropdown.value
            if selected:
                for opt in self.task_dropdown.options:
                    if opt.key == selected:
                        self.current_task_text.value = f"Следующая: {opt.text}"
                        self.current_task_text.color = COLORS["text_secondary"]
                        self.current_task_text.italic = True
                        break
            else:
                self.current_task_text.value = "Отдых"
                self.current_task_text.color = COLORS["text_secondary"]
                self.current_task_text.italic = True
        else:
            self._update_current_task_text()

    def _apply_reset_style(self):
        if self.timer_service.is_running:
            self.reset_button.style = ft.ButtonStyle(
                side=ft.BorderSide(1.5, COLORS["error"]), color=COLORS["error"])
        else:
            self.reset_button.style = ft.ButtonStyle(
                side=ft.BorderSide(1.5, COLORS["reset_border"]), color=COLORS["text_secondary"])

    def _update_progress(self):
        total = self.timer_service._get_current_target_sec()
        self.progress_ring.value = (total - self.timer_service.current_sec) / total if total > 0 else 0.0

    def _update_buttons(self):
        self.skip_button.visible = self.timer_service.is_running
        self._apply_reset_style()

    def _show_snackbar(self, message: str, color: str = COLORS["primary"]):
        if color == COLORS["success"]:
            icon = ft.Icons.CHECK_CIRCLE
        elif color == COLORS["skip"]:
            icon = ft.Icons.HOURGLASS_TOP
        else:
            icon = ft.Icons.INFO_OUTLINE
        show_toast(self._page, message, icon, color)

    def update_timer_display(self):
        self.time_display.value = self.timer_service.get_display_time()
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self.progress_text.value = self._get_progress_display()
        self._apply_mode_colors()
        self._update_progress()
        self._update_buttons()
        self.update_stats()
        if self.timer_service.just_finished:
            self.timer_service.just_finished = False
            self._pulse()
            self._show_snackbar(f"✅ {self.timer_service.last_finished_text}", COLORS["success"])
            self._check_auto_start()
        self._page.update()

    def _check_auto_start(self):
        with SessionLocal() as db:
            settings = get_settings(db)
            if settings.get("auto_start", False):
                self._start_countdown(int(settings.get("auto_start_delay", 3)))
            else:
                self.start_button.visible = True
                self.pause_button.visible = False

    def _start_countdown(self, delay: int):
        self._cancel_auto_start_countdown()
        self.start_button.visible = False
        self.auto_start_text.value = f"Старт через {delay}..."
        self.auto_start_text.visible = True
        self.auto_start_bar.value = 0.0
        self.auto_start_bar.visible = True
        self.cancel_auto_btn.visible = True
        self._page.update()
        async def countdown():
            try:
                for i in range(delay, 0, -1):
                    self.auto_start_text.value = f"Старт через {i}..."
                    self.auto_start_bar.value = (delay - i) / delay
                    self._page.update()
                    await asyncio.sleep(1)
                self.auto_start_bar.value = 1.0
                self._page.update()
                await asyncio.sleep(0.3)
                self.auto_start_text.visible = False
                self.auto_start_bar.visible = False
                self.cancel_auto_btn.visible = False
                self._page.update()
                self.on_start(None)
            except asyncio.CancelledError:
                pass
        self._auto_start_task = asyncio.create_task(countdown())

    def on_cancel_auto_start(self, e):
        self._cancel_auto_start_countdown()
        self.start_button.visible = True
        self.pause_button.visible = False
        self._page.update()

    def on_task_change(self, e):
        self._update_session_label_from_dropdown()
        self._update_current_task_text()
        self._page.update()

    def _update_session_label_from_dropdown(self):
        selected_key = self.task_dropdown.value
        if selected_key:
            for opt in self.task_dropdown.options:
                if opt.key == selected_key:
                    is_work = (opt.data or "work") in ["work", "study"]
                    self.timer_service.set_session_mode(is_work)
                    self.session_type_text.value = self.timer_service.get_session_type_display()
                    self._apply_mode_colors()
                    return
        self.timer_service.set_session_mode(True)
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self._apply_mode_colors()

    def focus_on_task(self, task_id: int, category: str):
        if self.timer_service.is_running:
            def on_confirm(e):
                dialog.open = False
                self._page.update()
                asyncio.create_task(self.timer_service.pause())
                self._do_focus_on_task(task_id, category)
            def on_cancel(e):
                dialog.open = False
                self._page.update()
            dialog = ft.AlertDialog(
                title=ft.Text("Таймер уже запущен"),
                content=ft.Text("Остановить и начать новую задачу?"),
                actions=[ft.TextButton("Отмена", on_click=on_cancel),
                         ft.TextButton("Начать", on_click=on_confirm)],
                actions_alignment=ft.MainAxisAlignment.END)
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()
        else:
            self._do_focus_on_task(task_id, category)

    def _do_focus_on_task(self, task_id: int, category: str):
        self._cancel_auto_start_countdown()
        self.load_tasks()
        self.task_dropdown.value = str(task_id)
        self.timer_service.set_session_mode(category in ["work", "study"])
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self._apply_mode_colors()
        self._update_current_task_text()
        self._update_progress()
        self.on_start(None)
        self._page.update()

    def on_start(self, e):
        self._cancel_auto_start_countdown()
        task_id = int(self.task_dropdown.value) if self.task_dropdown.value else None
        self.start_button.visible = False
        self.pause_button.visible = True
        self._apply_mode_colors()
        self._update_buttons()
        self._pulse()
        self._page.update()
        asyncio.create_task(
            self.timer_service.start(self.update_timer_display, task_id, sound_enabled=True))

    def on_pause(self, e):
        self._cancel_auto_start_countdown()
        asyncio.create_task(self.timer_service.pause())
        self.start_button.visible = True
        self.pause_button.visible = False
        self.skip_button.visible = False
        self._apply_reset_style()
        self._page.update()

    def on_skip(self, e):
        self._cancel_auto_start_countdown()
        async def do_skip():
            await self.timer_service.pause()
            elapsed = self.timer_service.skip_and_save()
            self.update_timer_display()
            self.start_button.visible = True
            self.pause_button.visible = False
            self.skip_button.visible = False
            if elapsed > 0:
                self._show_snackbar(f"✅ Сохранено: {TimerService.format_duration(elapsed)}", COLORS["success"])
            else:
                self._show_snackbar("⏭ Сессия пропущена", COLORS["skip"])
            self._page.update()
        asyncio.create_task(do_skip())

    def on_reset(self, e):
        self._cancel_auto_start_countdown()
        asyncio.create_task(self.timer_service.reset())
        self.start_button.visible = True
        self.pause_button.visible = False
        self.skip_button.visible = False
        self.progress_ring.value = 0.0
        self.update_timer_display()
        self.update_stats()

    def _close_dialog(self, dialog):
        dialog.open = False
        self._page.update()