# ui/screens/onboarding_screen.py
import flet as ft
from ui.theme import COLORS


class OnboardingScreen(ft.Column):
    def __init__(self, page: ft.Page, on_complete):
        super().__init__(
            expand=True,
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._page = page
        self.on_complete = on_complete
        self.current = 0

        self.slides = [
            {
                "icon": ft.Icons.TIMER,
                "color": COLORS["work"],
                "title": "Фокус по Pomodoro",
                "text": "Работай интервалами по 25 минут\nс короткими перерывами.\nТак проще удерживать концентрацию.",
            },
            {
                "icon": ft.Icons.CHECKLIST,
                "color": COLORS["rest"],
                "title": "Задачи и категории",
                "text": "Создавай задачи, распределяй их\nпо категориям и запускай таймер\nпрямо из списка одним касанием.",
            },
            {
                "icon": ft.Icons.BAR_CHART,
                "color": COLORS["long_break"],
                "title": "Статистика прогресса",
                "text": "Следи за активностью и сериями дней,\nэкспортируй данные в CSV.\nPremium откроет ещё больше возможностей.",
            },
        ]

        # AnimatedSwitcher без transition = fade по умолчанию (надёжно в 0.85.3)
        self.slide_switcher = ft.AnimatedSwitcher(
            content=self._build_slide(0),
            duration=300,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
            switch_out_curve=ft.AnimationCurve.EASE_IN,
        )

        self.dots_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=self._build_dots(),
        )

        self.next_button = ft.ElevatedButton(
            "Далее",
            bgcolor=COLORS["primary"],
            color=COLORS["bg"],
            on_click=self._on_next,
            width=160,
            height=50,
        )

        self.skip_button = ft.TextButton(
            "Пропустить",
            style=ft.ButtonStyle(color=COLORS["text_secondary"]),
            on_click=self._on_skip,
        )

        self.controls = [
            ft.Container(height=50),
            ft.Container(
                content=self.slide_switcher,
                expand=True,
                alignment=ft.Alignment(0, 0),
            ),
            self.dots_row,
            ft.Container(height=30),
            self.next_button,
            self.skip_button,
            ft.Container(height=30),
        ]

    def _build_slide(self, index: int):
        s = self.slides[index]
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(s["icon"], size=90, color=s["color"]),
                    width=160,
                    height=160,
                    border_radius=80,
                    bgcolor=COLORS["surface"],
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(height=40),
                ft.Text(
                    s["title"],
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["text"],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=16),
                ft.Text(
                    s["text"],
                    size=16,
                    color=COLORS["text_secondary"],
                    text_align=ft.TextAlign.CENTER,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=30,
            alignment=ft.Alignment(0, 0),
        )

    def _build_dots(self):
        dots = []
        for i in range(len(self.slides)):
            active = i == self.current
            dots.append(
                ft.Container(
                    width=10 if active else 8,
                    height=10 if active else 8,
                    border_radius=5,
                    bgcolor=COLORS["primary"] if active else COLORS["text_secondary"],
                    opacity=1.0 if active else 0.4,
                )
            )
        return dots

    def _update_dots(self):
        self.dots_row.controls = self._build_dots()

    def _on_next(self, e):
        if self.current < len(self.slides) - 1:
            self.current += 1
            self.slide_switcher.content = self._build_slide(self.current)
            self._update_dots()
            if self.current == len(self.slides) - 1:
                self.next_button.text = "Начать"
            self._page.update()
        else:
            self.on_complete()

    def _on_skip(self, e):
        self.on_complete()