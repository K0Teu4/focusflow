# ui/screens/focus_screen.py
import asyncio
import flet as ft
from ui.theme import COLORS, GRADIENTS, SHADOWS, with_alpha


class FocusScreen(ft.Column):
    """Полноэкранный таймер без навбара + минимальное управление."""

    def __init__(self, page: ft.Page, timer_service, on_exit, controller):
        super().__init__(expand=True, spacing=0)
        self._page = page
        self._ts = timer_service
        self._on_exit = on_exit
        self._ctrl = controller          # TimerScreen: on_start/on_pause/on_skip/on_reset
        self._ticking = False
        self._tick_task = None
        self._task_title = None

        # === ВЫХОД ===
        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK, icon_color=COLORS["text_secondary"],
            icon_size=28, tooltip="Выйти из режима Фокус",
            on_click=lambda e: self._on_exit(),
        )

        # === КОЛЬЦО ===
        self.ring = ft.Container(
            width=280, height=280, border_radius=140,
            gradient=GRADIENTS["work"], alignment=ft.Alignment(0, 0),
            shadow=SHADOWS["elevated"],
            content=ft.ProgressRing(
                value=0.0, width=252, height=252, stroke_width=14,
                color=COLORS["work"], bgcolor=COLORS["surface_2"],
            ),
        )
        self.progress_ring = self.ring.content

        # === ТЕКСТЫ ===
        self.time_text = ft.Text("25:00", size=68, weight=ft.FontWeight.BOLD,
                                 color=COLORS["work"], font_family="monospace")
        self.session_text = ft.Text("Работа", size=22, weight=ft.FontWeight.W_600, color=COLORS["text"])
        self.task_text = ft.Text("Без задачи", size=17, color=COLORS["text_secondary"], italic=True)
        self.progress_text = ft.Text("Сессия 0 из 4", size=15, color=COLORS["text_secondary"])

        # === УПРАВЛЕНИЕ (минимализм) ===
        self.play_pause_btn = ft.Container(
            width=64, height=64, border_radius=32,
            bgcolor=COLORS["primary"], alignment=ft.Alignment(0, 0),
            content=ft.Icon(ft.Icons.PLAY_ARROW, color=COLORS["bg"], size=34),
            on_click=lambda e: self._on_play_pause(), ink=True,
        )
        self.skip_btn = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT, icon_color=COLORS["text_secondary"],
            icon_size=26, tooltip="Пропустить", on_click=lambda e: self._ctrl.on_skip(None),
        )
        self.reset_btn = ft.IconButton(
            icon=ft.Icons.REPLAY, icon_color=COLORS["text_secondary"],
            icon_size=24, tooltip="Сброс", on_click=lambda e: self._ctrl.on_reset(None),
        )
        self.controls_row = ft.Row(
            [self.reset_btn, self.play_pause_btn, self.skip_btn],
            alignment=ft.MainAxisAlignment.CENTER, spacing=28,
        )

        # === LAYOUT ===
        self.controls = [
            ft.Container(content=self.back_button, padding=ft.padding.Padding(16, 16, 0, 0)),
            ft.Container(
                expand=True, alignment=ft.Alignment(0, -0.1),
                content=ft.Column([
                    self.ring, ft.Container(height=24), self.time_text,
                    ft.Container(height=8), self.session_text, ft.Container(height=4),
                    self.task_text, ft.Container(height=16), self.progress_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            ),
            ft.Container(content=self.controls_row, padding=ft.padding.Padding(0, 0, 0, 44)),
        ]

    # ------------------------------------------------------------------ #
    def set_task(self, title: str):
        self._task_title = title

    def start_ticking(self):
        self._ticking = True
        self._refresh()
        self._tick_task = asyncio.create_task(self._tick())

    def stop_ticking(self):
        self._ticking = False
        if self._tick_task and not self._tick_task.done():
            self._tick_task.cancel()

    def _on_play_pause(self):
        if self._ts.is_running:
            self._ctrl.on_pause(None)
        else:
            self._ctrl.on_start(None)

    # ------------------------------------------------------------------ #
    async def _tick(self):
        while self._ticking:
            await asyncio.sleep(1)
            if not self._ticking:
                break
            self._refresh()

    def _refresh(self):
        self.time_text.value = self._ts.get_display_time()
        self.session_text.value = self._ts.get_session_type_display()
        self.progress_text.value = (
            f"Сессия {self._ts.completed_work_sessions} из {self._ts.sessions_until_long_break}")

        if not self._ts.is_work_session:
            self.task_text.value = "Отдых"
            self.task_text.italic = True
            self.task_text.color = COLORS["text_secondary"]
        else:
            self.task_text.value = self._task_title or "Без задачи"
            self.task_text.italic = (self._task_title is None)
            self.task_text.color = COLORS["text"] if self._task_title else COLORS["text_secondary"]

        # Иконка play/pause
        if self._ts.is_running:
            self.play_pause_btn.content = ft.Icon(ft.Icons.PAUSE, color=COLORS["bg"], size=32)
            self.play_pause_btn.bgcolor = COLORS["pause_work"]
        else:
            self.play_pause_btn.content = ft.Icon(ft.Icons.PLAY_ARROW, color=COLORS["bg"], size=34)
            self.play_pause_btn.bgcolor = COLORS["primary"]

        # Цвета кольца под режим
        mode = self._ts.get_mode_key()
        if mode == "work":
            ring_color, gradient = COLORS["work"], GRADIENTS["work"]
        elif mode == "long_break":
            ring_color, gradient = COLORS["long_break"], GRADIENTS["long_break"]
        else:
            ring_color, gradient = COLORS["rest"], GRADIENTS["rest"]
        self.progress_ring.color = ring_color
        self.ring.gradient = gradient
        self.time_text.color = ring_color

        total = self._ts._get_current_target_sec()
        self.progress_ring.value = (total - self._ts.current_sec) / total if total > 0 else 0.0

        self._page.update()