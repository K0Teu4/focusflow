# ui/screens/stats_screen.py
import flet as ft
from ui.theme import COLORS
from db.database import SessionLocal, get_user_state
from datetime import datetime, timedelta

class StatsScreen(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__(
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self._page = page

        # Проверяем Premium статус
        with SessionLocal() as db:
            user_state = get_user_state(db)
            self.is_premium = user_state.is_premium

        if not self.is_premium:
            # Показываем Paywall
            self.controls = [
                ft.Container(height=40),
                ft.Text("🔒", size=64, margin=ft.Margin(0, 0, 0, 20)),
                ft.Text(
                    "Статистика доступна в Premium",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["text"],
                    margin=ft.Margin(0, 0, 0, 10),
                ),
                ft.Text(
                    "Получите доступ к графикам продуктивности,\nистории за всё время и экспорту данных",
                    size=16,
                    color=COLORS["text_secondary"],
                    margin=ft.Margin(0, 0, 0, 30),
                ),
                ft.ElevatedButton(
                    "Открыть Premium",
                    bgcolor=COLORS["primary"],
                    color=COLORS["bg"],
                    on_click=lambda e: self._navigate_to_premium(),
                    width=200,
                    height=50,
                ),
            ]
        else:
            # Premium контент (заглушка)
            self.controls = [
                ft.Container(height=30),
                ft.Text(
                    "📊 Статистика",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["text"],
                    margin=ft.Margin(0, 0, 0, 30),
                ),
                ft.Container(
                    content=ft.Text(
                        "Здесь будут графики продуктивности,\nфильтры по периодам и экспорт данных",
                        size=16,
                        color=COLORS["text_secondary"],
                    ),
                    padding=30,
                    bgcolor=COLORS["surface"],
                    border_radius=12,
                    margin=ft.Margin(20, 0, 20, 0),
                ),
            ]

    def _navigate_to_premium(self):
        """Переключает на вкладку Premium"""
        self._page.navigation_bar.selected_index = 3  # Индекс вкладки Premium
        self._page.update()