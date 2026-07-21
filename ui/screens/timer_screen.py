# ui/screens/timer_screen.py
import flet as ft
import asyncio
from services.timer_service import TimerService
from db.database import SessionLocal, get_tasks, get_today_stats, get_settings
from ui.theme import COLORS

class TimerScreen(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._page = page
        self.timer_service = TimerService()
        self.selected_task_id = None
        self._auto_start_task = None

        # Фон таймера
        self.timer_bg = ft.Container(
            width=220,
            height=220,
            border_radius=110,
            bgcolor=COLORS["work_bg"],
            alignment=ft.Alignment(0, 0),
            content=ft.ProgressRing(
                value=0.0,
                width=200,
                height=200,
                stroke_width=8,
                color=COLORS["work"],
                bgcolor=COLORS["surface"],
            ),
            margin=ft.Margin(0, 20, 0, 12),  # left, top, right, bottom
        )
        self.progress_ring = self.timer_bg.content

        self.session_type_text = ft.Text(
            self.timer_service.get_session_type_display(),
            size=22,
            weight=ft.FontWeight.BOLD,
            color=COLORS["text"],
        )

        self.progress_text = ft.Text(
            self.timer_service.get_session_progress(),
            size=20,
            weight=ft.FontWeight.BOLD,
            color=COLORS["primary"],
            margin=ft.Margin(0, 0, 0, 8),
        )

        self.time_display = ft.Text(
            self.timer_service.get_display_time(),
            size=56,
            weight=ft.FontWeight.BOLD,
            color=COLORS["work"],
            font_family="monospace",
            margin=ft.Margin(0, 0, 0, 16),
        )

        self.start_button = ft.ElevatedButton(
            "Старт",
            bgcolor=COLORS["primary"],
            color=COLORS["bg"],
            on_click=self.on_start,
            width=140,
            height=48,
        )

        self.pause_button = ft.ElevatedButton(
            "Пауза",
            bgcolor=COLORS["pause_work"],
            color=COLORS["bg"],
            on_click=self.on_pause,
            width=140,
            height=48,
            visible=False,
        )

        self.skip_button = ft.ElevatedButton(
            "Пропустить",
            bgcolor=COLORS["skip"],
            color=COLORS["bg"],
            on_click=self.on_skip,
            width=140,
            height=44,
            visible=False,
            margin=ft.Margin(0, 8, 0, 0),
        )

        self.reset_button = ft.OutlinedButton(
            "Сброс",
            style=ft.ButtonStyle(
                side=ft.BorderSide(1.5, COLORS["reset_border"]),
                color=COLORS["reset_border"],
            ),
            on_click=self.on_reset,
            width=110,
            height=38,
            margin=ft.Margin(0, 12, 0, 0),
        )

        # Автостарт
        self.auto_start_bar = ft.ProgressBar(
            value=0.0,
            color=COLORS["primary"],
            bgcolor=COLORS["surface"],
            width=200,
            visible=False,
        )
        self.auto_start_text = ft.Text(
            "",
            size=16,
            color=COLORS["primary"],
            weight=ft.FontWeight.W_600,
            visible=False,
            margin=ft.Margin(0, 8, 0, 0),
        )
        self.cancel_auto_btn = ft.TextButton(
            "Отмена",
            style=ft.ButtonStyle(color=COLORS["text_secondary"]),
            on_click=self.on_cancel_auto_start,
            visible=False,
        )

        # Dropdown
        self.task_dropdown = ft.Dropdown(
            label="Задача",
            hint_text="Выбрать задачу",
            width=280,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            margin=ft.Margin(0, 0, 0, 12),
        )
        self.task_dropdown.on_change = self.on_task_change

        self.next_task_text = ft.Text(
            "",
            size=14,
            color=COLORS["text_secondary"],
            italic=True,
            visible=False,
            margin=ft.Margin(0, 0, 0, 12),
        )

        self.stats_text = ft.Text(
            "",
            size=13,
            color=COLORS["text_secondary"],
            margin=ft.Margin(0, 16, 0, 20),
        )

        self.controls = [
            self.timer_bg,
            self.session_type_text,
            self.progress_text,
            self.time_display,
            self.task_dropdown,
            self.next_task_text,
            ft.Row([self.start_button, self.pause_button], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
            self.skip_button,
            self.auto_start_text,
            self.auto_start_bar,
            self.cancel_auto_btn,
            self.reset_button,
            self.stats_text,
        ]

        self.load_tasks()
        self.update_stats()

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
        self.progress_ring.value = 0.0
        self.time_display.value = self.timer_service.get_display_time()
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self.progress_text.value = self.timer_service.get_session_progress()
        self._page.update()

    def load_tasks(self):
        with SessionLocal() as db:
            tasks = get_tasks(db)
            self.task_dropdown.options = [
                ft.dropdown.Option(key=str(t.id), text=t.title, data=t.category)
                for t in tasks
            ]
        self._page.update()

    def update_stats(self):
        with SessionLocal() as db:
            stats = get_today_stats(db)
            self.stats_text.value = f"Сегодня: {stats['work_sessions']} 🍅 • {stats['total_work_minutes']} мин"

    def _apply_mode_colors(self):
        mode = self.timer_service.get_mode_key()
        if mode == "work":
            ring_color = COLORS["work"]
            bg_color = COLORS["work_bg"]
            pause_color = COLORS["pause_work"]
        elif mode == "long_break":
            ring_color = COLORS["long_break"]
            bg_color = COLORS["long_break_bg"]
            pause_color = COLORS["pause_rest"]
        else:
            ring_color = COLORS["rest"]
            bg_color = COLORS["rest_bg"]
            pause_color = COLORS["pause_rest"]

        self.progress_ring.color = ring_color
        self.timer_bg.bgcolor = bg_color
        self.time_display.color = ring_color
        self.pause_button.bgcolor = pause_color

        is_rest = not self.timer_service.is_work_session
        self.task_dropdown.visible = not is_rest
        if is_rest:
            selected = self.task_dropdown.value
            if selected:
                for opt in self.task_dropdown.options:
                    if opt.key == selected:
                        self.next_task_text.value = f"Следующая: {opt.text}"
                        self.next_task_text.visible = True
                        break
                else:
                    self.next_task_text.visible = False
            else:
                self.next_task_text.visible = False
        else:
            self.next_task_text.visible = False

    def _update_progress(self):
        total = self.timer_service._get_current_target_sec()
        if total > 0:
            self.progress_ring.value = (total - self.timer_service.current_sec) / total
        else:
            self.progress_ring.value = 0.0

    def _update_buttons(self):
        is_rest = not self.timer_service.is_work_session
        is_running = self.timer_service.is_running
        self.skip_button.visible = is_rest and is_running

    def update_timer_display(self):
        self.time_display.value = self.timer_service.get_display_time()
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self.progress_text.value = self.timer_service.get_session_progress()
        self._apply_mode_colors()
        self._update_progress()
        self._update_buttons()

        with SessionLocal() as db:
            stats = get_today_stats(db)
            self.stats_text.value = f"Сегодня: {stats['work_sessions']} 🍅 • {stats['total_work_minutes']} мин"

        if self.timer_service.just_finished:
            self.timer_service.just_finished = False
            self._check_auto_start()

        self._page.update()

    def _check_auto_start(self):
        with SessionLocal() as db:
            settings = get_settings(db)
            if settings.get("auto_start", False):
                delay = int(settings.get("auto_start_delay", 3))
                self._start_countdown(delay)
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
        self._page.update()

    def _update_session_label_from_dropdown(self):
        selected_key = self.task_dropdown.value
        if selected_key:
            for opt in self.task_dropdown.options:
                if opt.key == selected_key:
                    category = opt.data or "work"
                    is_work = category in ["work", "study"]
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
                actions=[
                    ft.TextButton("Отмена", on_click=on_cancel),
                    ft.TextButton("Начать", on_click=on_confirm),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()
        else:
            self._do_focus_on_task(task_id, category)

    def _do_focus_on_task(self, task_id: int, category: str):
        self._cancel_auto_start_countdown()
        self.load_tasks()
        self.task_dropdown.value = str(task_id)
        is_work = category in ["work", "study"]
        self.timer_service.set_session_mode(is_work)
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self._apply_mode_colors()
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
        self._page.update()
        asyncio.create_task(self.timer_service.start(
            self.update_timer_display, task_id, sound_enabled=True,
        ))

    def on_pause(self, e):
        self._cancel_auto_start_countdown()
        asyncio.create_task(self.timer_service.pause())
        self.start_button.visible = True
        self.pause_button.visible = False
        self.skip_button.visible = False
        self._page.update()

    def on_skip(self, e):
        self._cancel_auto_start_countdown()
        async def do_skip():
            await self.timer_service.pause()
            self.timer_service.toggle_session_type()
            self.timer_service.current_sec = self.timer_service._get_current_target_sec()
            self.update_timer_display()
            self.start_button.visible = True
            self.pause_button.visible = False
            self.skip_button.visible = False
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