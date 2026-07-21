# ui/screens/settings_screen.py
import flet as ft
from db.database import SessionLocal, get_settings, update_settings, get_user_state, update_premium_status
from ui.theme import COLORS
from datetime import datetime

class SettingsScreen(ft.Column):
    def __init__(self, page: ft.Page, on_settings_changed=None, on_open_premium=None):
        super().__init__(
            spacing=15,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
        self._page = page
        self.on_settings_changed = on_settings_changed
        self.on_open_premium = on_open_premium

        # Загружаем текущие значения
        with SessionLocal() as db:
            settings = get_settings(db)
            user_state = get_user_state(db)
            self.is_premium = user_state.is_premium
            self.premium_expires = user_state.premium_expires_at

        # Автосохранение
        def auto_save(e=None):
            self._save_current_values()

        # === ПОЛЯ ДЛИТЕЛЬНОСТИ ===
        self.work_min_field = ft.TextField(
            label="Работа (минуты)",
            value=str(settings.get("work_min", 25)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            width=200,
            on_change=auto_save,
        )

        self.break_min_field = ft.TextField(
            label="Короткий отдых (минуты)",
            value=str(settings.get("break_min", 5)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            width=200,
            on_change=auto_save,
        )

        self.long_break_min_field = ft.TextField(
            label="Длинный перерыв (минуты)",
            value=str(settings.get("long_break_min", 15)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            width=200,
            on_change=auto_save,
        )

        self.sessions_until_long_break_field = ft.TextField(
            label="Сессий до длинного перерыва",
            value=str(settings.get("sessions_until_long_break", 4)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            width=200,
            on_change=auto_save,
        )

        # === ПОВЕДЕНИЕ ===
        self.sound_checkbox = ft.Checkbox(
            label="Звук при завершении",
            value=settings.get("sound_enabled", True),
            check_color=COLORS["primary"],
            on_change=auto_save,
        )

        self.auto_start_checkbox = ft.Checkbox(
            label="Автостарт следующей сессии",
            value=settings.get("auto_start", False),
            check_color=COLORS["primary"],
            on_change=auto_save,
        )

        self.auto_start_delay_field = ft.TextField(
            label="Задержка автостарта (сек)",
            value=str(settings.get("auto_start_delay", 3)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            width=200,
            on_change=auto_save,
        )

        # === СТАТУС ===
        self.status_message = ft.Text(
            "✓ Автосохранение включено",
            size=14,
            color=COLORS["success"],
        )

        # === PREMIUM СТАТУС ===
        # ИСПРАВЛЕНО: используем просто BorderSide для uniforme border
        primary_border = ft.BorderSide(1.5, COLORS["primary"])
        
        if self.is_premium:
            expires_text = f"до {self.premium_expires.strftime('%d.%m.%Y')}" if self.premium_expires else "бессрочно"
            self.premium_status = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.VERIFIED, size=24, color=COLORS["success"]),
                    ft.Column([
                        ft.Text("Premium активен", size=16, weight=ft.FontWeight.BOLD, color=COLORS["success"]),
                        ft.Text(f"Действует {expires_text}", size=12, color=COLORS["text_secondary"]),
                    ], spacing=0),
                ], spacing=12),
                padding=16,
                bgcolor=COLORS["surface"],
                border_radius=12,
                margin=ft.Margin(20, 0, 20, 0),
            )
        else:
            self.premium_status = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.STAR, size=24, color=COLORS["primary"]),
                        ft.Text("FocusFlow Premium", size=16, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                    ], spacing=8),
                    ft.Container(height=8),
                    ft.Text(
                        "Разблокируйте графики, экспорт, темы и многое другое",
                        size=13,
                        color=COLORS["text_secondary"],
                    ),
                    ft.Container(height=12),
                    ft.ElevatedButton(
                        "Открыть Premium",
                        bgcolor=COLORS["primary"],
                        color=COLORS["bg"],
                        on_click=self._navigate_to_premium,
                        width=200,
                        height=44,
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=12,
                border=primary_border,  # ИСПРАВЛЕНО: просто передаем BorderSide
                margin=ft.Margin(20, 0, 20, 0),
            )

        # Сборка UI
        self.controls = [
            ft.Container(
                content=ft.Text("Настройки", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                padding=ft.padding.Padding(20, 20, 20, 0),
                alignment=ft.Alignment(0, 0),
            ),
            # Premium статус
            self.premium_status,
            # Длительность
            ft.Container(
                content=ft.Column([
                    ft.Text("Длительность", size=18, color=COLORS["text"]),
                    ft.Container(height=8),
                    self.work_min_field,
                    self.break_min_field,
                    self.long_break_min_field,
                    self.sessions_until_long_break_field,
                ], spacing=8),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(20, 0, 20, 0),
            ),
            # Поведение
            ft.Container(
                content=ft.Column([
                    ft.Text("Поведение", size=18, color=COLORS["text"]),
                    ft.Container(height=8),
                    self.sound_checkbox,
                    self.auto_start_checkbox,
                    self.auto_start_delay_field,
                ], spacing=8),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(20, 0, 20, 0),
            ),
            # Premium функции (заглушка)
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Premium функции", size=18, color=COLORS["text"]),
                        self._create_pro_badge(),
                    ], spacing=8),
                    ft.Container(height=8),
                    self._create_locked_feature(ft.Icons.MUSIC_NOTE, "Выбор звука (3+ варианта)"),
                    self._create_locked_feature(ft.Icons.PALETTE, "Кастомные темы"),
                    self._create_locked_feature(ft.Icons.BAR_CHART, "Расширенная статистика"),
                    self._create_locked_feature(ft.Icons.FILE_DOWNLOAD, "Экспорт в CSV/PDF"),
                ], spacing=8),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(20, 0, 20, 0),
            ),
            # Статус
            ft.Container(
                content=self.status_message,
                padding=20,
                alignment=ft.Alignment(0, 0),
            ),
            ft.Container(height=40),
        ]

    def _create_pro_badge(self):
        """Бейдж PRO"""
        return ft.Container(
            content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color=COLORS["bg"]),
            bgcolor=COLORS["primary"],
            border_radius=4,
            padding=ft.padding.Padding(6, 2, 6, 2),
        )

    def _create_locked_feature(self, icon, title):
        """Заблокированная Premium-функция"""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=20, color=COLORS["text_secondary"]),
                ft.Text(title, size=14, color=COLORS["text_secondary"], expand=True),
                ft.Icon(ft.Icons.LOCK, size=16, color=COLORS["text_secondary"]),
            ], spacing=10),
            padding=12,
            bgcolor=COLORS["bg"],
            border_radius=8,
            opacity=0.7,
            on_click=lambda e: self._navigate_to_premium(e),
            ink=True,
        )

    def _navigate_to_premium(self, e=None):
        """Переход на вкладку Premium"""
        if self.on_open_premium:
            self.on_open_premium()

    def _save_current_values(self):
        """Автосохранение всех настроек"""
        try:
            work_min = int(self.work_min_field.value or 0)
            break_min = int(self.break_min_field.value or 0)
            long_break_min = int(self.long_break_min_field.value or 0)
            sessions = int(self.sessions_until_long_break_field.value or 0)
            delay = int(self.auto_start_delay_field.value or 0)

            # Валидация
            if work_min <= 0 or break_min <= 0 or long_break_min <= 0 or sessions <= 0 or delay < 1:
                self.status_message.value = "⚠ Введите корректные значения"
                self.status_message.color = COLORS["error"]
                self._page.update()
                return

            settings = {
                "work_min": work_min,
                "break_min": break_min,
                "long_break_min": long_break_min,
                "sessions_until_long_break": sessions,
                "sound_enabled": self.sound_checkbox.value,
                "auto_start": self.auto_start_checkbox.value,
                "auto_start_delay": delay,
                "sound_type": "bell",
                "theme": "dark",
            }

            with SessionLocal() as db:
                update_settings(db, settings)

            self.status_message.value = "✓ Сохранено"
            self.status_message.color = COLORS["success"]
            self._page.update()

            if self.on_settings_changed:
                self.on_settings_changed(settings)

        except ValueError:
            self.status_message.value = "⚠ Некорректные числа"
            self.status_message.color = COLORS["error"]
            self._page.update()