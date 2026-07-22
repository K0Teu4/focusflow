# ui/screens/stats_screen.py
import flet as ft
from pathlib import Path
from ui.theme import COLORS
from db.database import (
    SessionLocal, get_user_state, get_total_stats,
    get_daily_activity, get_current_streak, get_recent_sessions,
    get_all_sessions_for_export,
)
from services.export_service import ExportService


class StatsScreen(ft.Column):
    def __init__(self, page: ft.Page, on_open_premium=None):
        super().__init__(
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._page = page
        self.on_open_premium = on_open_premium

        with SessionLocal() as db:
            user_state = get_user_state(db)
            self.is_premium = user_state.is_premium

        if not self.is_premium:
            self.controls = self._build_paywall()
        else:
            self.controls = self._build_premium_content()

    def _build_paywall(self):
        return [
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
                "Графики продуктивности, история сессий,\nсерия дней и экспорт данных",
                size=16,
                color=COLORS["text_secondary"],
                text_align=ft.TextAlign.CENTER,
                margin=ft.Margin(20, 0, 20, 30),
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

    def _build_premium_content(self):
        with SessionLocal() as db:
            total = get_total_stats(db)
            activity = get_daily_activity(db, days=7)
            streak = get_current_streak(db)
            recent = get_recent_sessions(db, limit=15)

        controls = []

        controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(
                        "📊 Статистика",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=COLORS["text"],
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.padding.Padding(20, 20, 20, 10),
            )
        )

        controls.append(self._build_summary_cards(total, streak))
        controls.append(self._build_activity_chart(activity))
        controls.append(self._build_export_button())
        controls.append(self._build_recent_sessions(recent))
        controls.append(ft.Container(height=40))
        return controls

    def _build_summary_cards(self, total: dict, streak: int):
        cards_data = [
            ("🍅", str(total['work_sessions']), "Сессий"),
            ("⏱", str(total['total_work_hours']), "Часов"),
            ("🔥", str(streak), "Дней"),
        ]
        cards = []
        for icon, value, label in cards_data:
            cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(icon, size=24),
                        ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                        ft.Text(label, size=12, color=COLORS["text_secondary"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                    padding=12,
                    bgcolor=COLORS["surface"],
                    border_radius=12,
                    expand=True,
                )
            )
        return ft.Container(
            content=ft.Row(cards, spacing=10),
            padding=ft.padding.Padding(15, 0, 15, 0),
        )

    def _build_activity_chart(self, activity: list):
        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        max_minutes = max([d['work_minutes'] for d in activity] + [1])
        bar_max_height = 120

        bars = []
        for d in activity:
            day_idx = d['date'].weekday()
            day_name = day_names[day_idx]
            minutes = d['work_minutes']
            bar_height = int((minutes / max_minutes) * bar_max_height) if max_minutes > 0 else 0
            bar_height = max(bar_height, 4)
            is_today = d == activity[-1]
            bar_color = COLORS["primary"] if minutes > 0 else COLORS["surface"]

            bar_column = ft.Column([
                ft.Text(str(minutes) if minutes > 0 else "", size=10, color=COLORS["text_secondary"]),
                ft.Container(width=22, height=bar_height, bgcolor=bar_color, border_radius=4),
                ft.Text(
                    day_name,
                    size=11,
                    color=COLORS["text"] if is_today else COLORS["text_secondary"],
                    weight=ft.FontWeight.BOLD if is_today else ft.FontWeight.NORMAL,
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)

            bars.append(
                ft.Container(
                    content=bar_column,
                    expand=True,
                    alignment=ft.Alignment(0, 1),
                )
            )

        week_start = activity[0]['date'].strftime('%d.%m') if activity else ''
        week_end = activity[-1]['date'].strftime('%d.%m') if activity else ''

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Активность за 7 дней", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ft.Text(f"{week_start}–{week_end}", size=12, color=COLORS["text_secondary"]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Row(
                        bars, spacing=6, vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    height=bar_max_height + 50,
                ),
                ft.Container(height=6),
                ft.Text(f"Пик: {max_minutes} мин", size=12, color=COLORS["text_secondary"]),
            ], spacing=0),
            padding=16,
            bgcolor=COLORS["surface"],
            border_radius=12,
            margin=ft.Margin(15, 10, 15, 0),
        )

    def _build_export_button(self):
        """Кнопка экспорта CSV — сохраняет в стандартную папку без диалога."""
        self.export_status = ft.Text(
            "",
            size=12,
            color=COLORS["text_secondary"],
            margin=ft.Margin(0, 6, 0, 0),
            text_align=ft.TextAlign.CENTER,
        )

        return ft.Container(
            content=ft.Column([
                ft.ElevatedButton(
                    "📤 Экспорт в CSV",
                    bgcolor=COLORS["primary"],
                    color=COLORS["bg"],
                    icon=ft.Icons.FILE_DOWNLOAD,
                    on_click=self._on_export_click,
                    width=250,
                    height=48,
                ),
                self.export_status,
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            padding=12,
            margin=ft.Margin(15, 10, 15, 0),
            alignment=ft.Alignment(0, 0),
        )

    def _on_export_click(self, e):
        """Сохраняет CSV в стандартную папку (Downloads/Documents)."""
        try:
            # Генерируем путь
            file_path = ExportService.generate_full_path()
            
            # Получаем данные из БД
            with SessionLocal() as db:
                sessions = get_all_sessions_for_export(db)
            
            if not sessions:
                self.export_status.value = "⚠ Нет сессий для экспорта"
                self.export_status.color = COLORS["error"]
                self._page.update()
                return
            
            # Выполняем экспорт
            success = ExportService.export_sessions_to_csv(sessions, file_path)
            
            if success:
                self.export_status.value = f"✓ Сохранено: {file_path.name}\n📁 {file_path.parent}"
                self.export_status.color = COLORS["success"]
            else:
                self.export_status.value = "✗ Ошибка при сохранении"
                self.export_status.color = COLORS["error"]
            
        except Exception as ex:
            self.export_status.value = f"⚠ Ошибка: {ex}"
            self.export_status.color = COLORS["error"]
        
        self._page.update()

    def _build_recent_sessions(self, recent: list):
        type_icons = {
            'work': ("🍅", COLORS["work"]),
            'short_break': ("☕", COLORS["rest"]),
            'long_break': ("🌙", COLORS["long_break"]),
        }
        type_names = {
            'work': "Работа",
            'short_break': "Короткий перерыв",
            'long_break': "Длинный перерыв",
        }

        items = []
        for s in recent:
            icon, color = type_icons.get(s['type'], ("•", COLORS["text"]))
            name = type_names.get(s['type'], s['type'])
            task = s['task_title'] or "Без задачи"
            time_str = s['started_at'].strftime('%d.%m %H:%M') if s['started_at'] else ''

            items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(icon, size=20),
                        ft.Column([
                            ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                            ft.Text(task, size=12, color=COLORS["text_secondary"]),
                        ], spacing=2, expand=True),
                        ft.Column([
                            ft.Text(f"{s['duration_min']} мин", size=14, color=color, weight=ft.FontWeight.BOLD),
                            ft.Text(time_str, size=11, color=COLORS["text_secondary"]),
                        ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=12,
                    bgcolor=COLORS["surface"],
                    border_radius=10,
                    margin=ft.Margin(0, 0, 0, 6),
                )
            )

        if not items:
            items.append(
                ft.Container(
                    content=ft.Text(
                        "Пока нет завершённых сессий",
                        size=14,
                        color=COLORS["text_secondary"],
                        italic=True,
                    ),
                    padding=20,
                    alignment=ft.Alignment(0, 0),
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "Последние сессии",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=COLORS["text"],
                    margin=ft.Margin(0, 0, 0, 10),
                ),
                *items,
            ]),
            padding=16,
            margin=ft.Margin(15, 10, 15, 0),
        )

    def _navigate_to_premium(self):
        if self.on_open_premium:
            self.on_open_premium()