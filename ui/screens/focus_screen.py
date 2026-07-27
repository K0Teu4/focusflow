# ui/screens/focus_screen.py
import asyncio
import flet as ft
from ui.theme import COLORS, GRADIENTS, SHADOWS


class FocusScreen(ft.Column):
    """Полноэкранный таймер без навбара. Read-only дисплей TimerService."""

    def __init__(self, page: ft.Page, timer_service, on_exit):
        super().__init__(expand=True, spacing=0)
        self._page = page
        self._ts = timer_service
        self._on_exit = on_exit
        self._ticking = False
        self._tick_task = None
        self._task_title = None  # устанавливается при входе

        # === КНОПКА ВЫХОДА ===
        self.back_button = ft.IconButton(
            icon=ft.Icons.ARROW_BACK, icon_color=COLORS["text_secondary"],
            icon_size=28, tooltip="Выйти из режима Фокус",
            on_click=lambda e: self._on_exit(),
        )

        # === КОЛЬЦО ПРОГРЕССА (большое, по центру) ===
        self.ring = ft.Container(
            width=300, height=300, border_radius=150,
            gradient=GRADIENTS["work"],
            alignment=ft.Alignment(0, 0),
            shadow=SHADOWS["elevated"],
            content=ft.ProgressRing(
                value=0.0, width=270, height=270, stroke_width=14,
                color=COLORS["work"], bgcolor=COLORS["surface_2"],
            ),
        )
        self.progress_ring = self.ring.content

        # === ТЕКСТЫ ===
        self.time_text = ft.Text(
            "25:00", size=72, weight=ft.FontWeight.BOLD,
            color=COLORS["work"], font_family="monospace",
        )
        self.session_text = ft.Text(
            "Работа", size=24, weight=ft.FontWeight.W_600, color=COLORS["text"],
        )
        self.task_text = ft.Text(
            "Без задачи", size=18, color=COLORS["text_secondary"], italic=True,
        )
        self.progress_text = ft.Text(
            "Сессия 0 из 4", size=16, color=COLORS["text_secondary"],
        )

        # === LAYOUT ===
        self.controls = [
            ft.Container(
                content=self.back_button,
                padding=ft.padding.Padding(16, 16, 0, 0),
            ),
            ft.Container(
                expand=True,
                alignment=ft.Alignment(0, -0.15),
                content=ft.Column([
                    self.ring,
                    ft.Container(height=28),
                    self.time_text,
                    ft.Container(height=10),
                    self.session_text,
                    ft.Container(height=6),
                    self.task_text,
                    ft.Container(height=20),
                    self.progress_text,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            ),
        ]

    # ------------------------------------------------------------------ #
    # API: запуск/остановка тикера                                        #
    # ------------------------------------------------------------------ #
    def set_task(self, title: str):
        """Установить название текущей задачи (вызывается при входе)."""
        self._task_title = title

    def start_ticking(self):
        """Запустить async-цикл обновления UI каждую секунду."""
        self._ticking = True
        self._refresh()  # мгновенное обновление при входе
        self._tick_task = asyncio.create_task(self._tick())

    def stop_ticking(self):
        """Остановить тикер."""
        self._ticking = False
        if self._tick_task and not self._tick_task.done():
            self._tick_task.cancel()

    # ------------------------------------------------------------------ #
    # ВНУТРЕННЕЕ                                                          #
    # ------------------------------------------------------------------ #
    async def _tick(self):
        """Async-цикл: обновляет UI каждую секунду из TimerService."""
        while self._ticking:
            await asyncio.sleep(1)
            if not self._ticking:
                break
            self._refresh()

    def _refresh(self):
        """Читает состояние TimerService и обновляет UI."""
        # Время и тип сессии
        self.time_text.value = self._ts.get_display_time()
        self.session_text.value = self._ts.get_session_type_display()
        self.progress_text.value = (
            f"Сессия {self._ts.completed_work_sessions} из {self._ts.sessions_until_long_break}"
        )

        # Задача или «Отдых»
        if not self._ts.is_work_session:
            self.task_text.value = "Отдых"
            self.task_text.italic = True
            self.task_text.color = COLORS["text_secondary"]
        else:
            self.task_text.value = self._task_title or "Без задачи"
            self.task_text.italic = (self._task_title is None)
            self.task_text.color = COLORS["text"] if self._task_title else COLORS["text_secondary"]

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

        # Прогресс кольца
        total = self._ts._get_current_target_sec()
        self.progress_ring.value = (total - self._ts.current_sec) / total if total > 0 else 0.0

        self._page.update()