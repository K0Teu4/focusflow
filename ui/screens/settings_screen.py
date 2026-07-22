# ui/screens/settings_screen.py
import flet as ft
from db.database import SessionLocal, get_settings, update_settings, get_user_state
from services.sound_service import SoundService, SOUNDS
from ui.theme import COLORS


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
        self.sound_service = SoundService()

        with SessionLocal() as db:
            settings = get_settings(db)
            user_state = get_user_state(db)
            self.is_premium = user_state.is_premium
            self.premium_expires = user_state.premium_expires_at

        def auto_save(e=None):
            self._save_current_values()

        # === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===
        def make_time_row(label: str, min_val: int, sec_val: int):
            min_field = ft.TextField(
                label="мин",
                value=str(min_val),
                keyboard_type=ft.KeyboardType.NUMBER,
                border_color=COLORS["primary"],
                color=COLORS["text"],
                bgcolor=COLORS["surface"],
                expand=True,
                text_align=ft.TextAlign.CENTER,
                on_change=auto_save,
            )
            sec_field = ft.TextField(
                label="сек",
                value=str(sec_val),
                keyboard_type=ft.KeyboardType.NUMBER,
                border_color=COLORS["primary"],
                color=COLORS["text"],
                bgcolor=COLORS["surface"],
                expand=True,
                text_align=ft.TextAlign.CENTER,
                on_change=auto_save,
            )
            return (
                min_field, sec_field,
                ft.Column([
                    ft.Text(label, size=14, color=COLORS["text"], weight=ft.FontWeight.W_500),
                    ft.Row([min_field, sec_field], spacing=10),
                ], spacing=6),
            )

        def make_labeled_field(label: str, field_widget):
            return ft.Column([
                ft.Text(label, size=14, color=COLORS["text"], weight=ft.FontWeight.W_500),
                field_widget,
            ], spacing=6)

        # === ДЛИТЕЛЬНОСТЬ ===
        self.work_min_field, self.work_sec_field, work_row = make_time_row(
            "Работа",
            int(settings.get("work_min", 25)),
            int(settings.get("work_sec", 0)),
        )
        self.break_min_field, self.break_sec_field, break_row = make_time_row(
            "Короткий отдых",
            int(settings.get("break_min", 5)),
            int(settings.get("break_sec", 0)),
        )
        self.long_break_min_field, self.long_break_sec_field, long_break_row = make_time_row(
            "Длинный перерыв",
            int(settings.get("long_break_min", 15)),
            int(settings.get("long_break_sec", 0)),
        )

        self.sessions_until_long_break_field = ft.TextField(
            value=str(settings.get("sessions_until_long_break", 4)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            text_align=ft.TextAlign.CENTER,
            on_change=auto_save,
        )
        sessions_row = make_labeled_field("Сессий до длинного перерыва", self.sessions_until_long_break_field)

        # === ПОВЕДЕНИЕ ===
        self.sound_checkbox = ft.Switch(
            label="Звук при завершении",
            value=settings.get("sound_enabled", True),
            active_color=COLORS["primary"],
            inactive_thumb_color=COLORS["text_secondary"],
            on_change=auto_save,
            label_text_style=ft.TextStyle(size=14, color=COLORS["text"]),
        )

        current_sound = settings.get("sound_type", "bell")
        current_sound_name = SOUNDS.get(current_sound, SOUNDS["bell"])["name"]
        self.sound_button = ft.ElevatedButton(
            f"🎵 {current_sound_name}",
            bgcolor=COLORS["surface"],
            color=COLORS["text"],
            icon=ft.Icons.ARROW_DROP_DOWN,
            on_click=self._open_sound_dialog,
            width=280,
            height=48,
        )
        sound_row = make_labeled_field("Звук уведомления", self.sound_button)

        self.auto_start_checkbox = ft.Switch(
            label="Автостарт следующей сессии",
            value=settings.get("auto_start", False),
            active_color=COLORS["primary"],
            inactive_thumb_color=COLORS["text_secondary"],
            on_change=auto_save,
            label_text_style=ft.TextStyle(size=14, color=COLORS["text"]),
        )

        self.auto_start_delay_field = ft.TextField(
            value=str(settings.get("auto_start_delay", 3)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            text_align=ft.TextAlign.CENTER,
            on_change=auto_save,
        )
        delay_row = make_labeled_field("Задержка автостарта (сек)", self.auto_start_delay_field)

        # === PREMIUM СТАТУС ===
        primary_border = ft.BorderSide(1.5, COLORS["primary"])

        if self.is_premium:
            expires_text = (
                f"до {self.premium_expires.strftime('%d.%m.%Y')}"
                if self.premium_expires else "бессрочно"
            )
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
                        "Графики, экспорт, 3+ звука и темы",
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
                border=primary_border,
                margin=ft.Margin(20, 0, 20, 0),
            )

        # === СБОРКА UI ===
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Настройки", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ft.Container(height=6),
                    ft.Row([
                        ft.Icon(ft.Icons.SAVE_OUTLINED, size=16, color=COLORS["text_secondary"]),
                        ft.Text("Все изменения сохраняются автоматически", size=13, color=COLORS["text_secondary"]),
                    ], spacing=6),
                ], spacing=0),
                padding=ft.padding.Padding(20, 20, 20, 10),
            ),
            self.premium_status,
            ft.Container(
                content=ft.Column([
                    ft.Text("Длительность", size=18, color=COLORS["text"]),
                    ft.Container(height=8),
                    work_row,
                    ft.Container(height=4),
                    break_row,
                    ft.Container(height=4),
                    long_break_row,
                    ft.Container(height=12),
                    sessions_row,
                ], spacing=8),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(20, 0, 20, 0),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Поведение", size=18, color=COLORS["text"]),
                    ft.Container(height=8),
                    self.sound_checkbox,
                    ft.Container(height=8),
                    sound_row,
                    ft.Container(height=12),
                    self.auto_start_checkbox,
                    ft.Container(height=8),
                    delay_row,
                ], spacing=8),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(20, 0, 20, 0),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Premium функции", size=18, color=COLORS["text"]),
                        self._create_pro_badge(),
                    ], spacing=8),
                    ft.Container(height=8),
                    self._create_locked_feature(ft.Icons.PALETTE, "Кастомные темы"),
                ], spacing=8),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(20, 0, 20, 0),
            ),
            ft.Container(height=40),
        ]

    def refresh_data(self):
        """Перечитывает Premium статус и настройки из БД, пересоздаёт UI"""
        # Сохраняем ссылки на callbacks
        page = self._page
        on_settings_changed = self.on_settings_changed
        on_open_premium = self.on_open_premium
        # Переинициализируем с актуальными данными
        self.__init__(page, on_settings_changed, on_open_premium)

    def _create_pro_badge(self):
        return ft.Container(
            content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color=COLORS["bg"]),
            bgcolor=COLORS["primary"],
            border_radius=4,
            padding=ft.padding.Padding(6, 2, 6, 2),
        )

    def _create_locked_feature(self, icon, title):
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

    def _open_sound_dialog(self, e):
        current = self._get_current_sound_type()

        def make_sound_row(sound_id, info):
            name = info["name"]
            is_premium_sound = info["premium"]
            is_locked = is_premium_sound and not self.is_premium
            is_selected = sound_id == current

            display_name = f"🔒 {name}" if is_locked else name

            def on_select(ev):
                if is_locked:
                    self._show_premium_for_sound_dialog()
                    return
                self._set_current_sound(sound_id)
                sound_dialog.open = False
                self._page.update()

            def on_test(ev):
                if is_locked:
                    self._show_premium_for_sound_dialog()
                    return
                self.sound_service.play(sound_id)

            return ft.Container(
                content=ft.Row([
                    ft.Text(
                        display_name,
                        size=15,
                        color=COLORS["text"] if not is_locked else COLORS["text_secondary"],
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PLAY_CIRCLE,
                        icon_color=COLORS["primary"] if not is_locked else COLORS["text_secondary"],
                        on_click=on_test,
                        tooltip="Тест",
                    ),
                ]),
                padding=12,
                bgcolor=COLORS["primary"] + "30" if is_selected else COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(0, 0, 0, 6),
                on_click=on_select,
                ink=True,
                border=ft.BorderSide(1.5, COLORS["primary"]) if is_selected else None,
            )

        sound_rows = []
        for sound_id, info in SOUNDS.items():
            sound_rows.append(make_sound_row(sound_id, info))

        sound_dialog = ft.AlertDialog(
            title=ft.Text("Выберите звук"),
            content=ft.Column(
                sound_rows,
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                height=300,
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: self._close_dialog(sound_dialog)),
            ],
        )
        self._page.overlay.append(sound_dialog)
        sound_dialog.open = True
        self._page.update()

    def _get_current_sound_type(self) -> str:
        with SessionLocal() as db:
            settings = get_settings(db)
            return settings.get("sound_type", "bell")

    def _set_current_sound(self, sound_id: str):
        with SessionLocal() as db:
            settings = get_settings(db)
            settings["sound_type"] = sound_id
            update_settings(db, settings)
        name = SOUNDS.get(sound_id, SOUNDS["bell"])["name"]
        self.sound_button.text = f"🎵 {name}"
        self._page.update()
        if self.on_settings_changed:
            self.on_settings_changed(settings)

    def _show_premium_for_sound_dialog(self):
        dialog = ft.AlertDialog(
            title=ft.Text("🔒 Premium звук"),
            content=ft.Text("Этот звук доступен только в Premium версии."),
            actions=[
                ft.TextButton("Остаться на Free", on_click=lambda e: self._close_dialog(dialog)),
                ft.TextButton("Открыть Premium", on_click=lambda e: self._go_to_premium(dialog)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _go_to_premium(self, dialog):
        dialog.open = False
        self._page.update()
        self._navigate_to_premium()

    def _navigate_to_premium(self, e=None):
        if self.on_open_premium:
            self.on_open_premium()

    def _close_dialog(self, dialog):
        dialog.open = False
        self._page.update()

    def _save_current_values(self):
        try:
            work_min = int(self.work_min_field.value or 0)
            work_sec = int(self.work_sec_field.value or 0)
            break_min = int(self.break_min_field.value or 0)
            break_sec = int(self.break_sec_field.value or 0)
            long_break_min = int(self.long_break_min_field.value or 0)
            long_break_sec = int(self.long_break_sec_field.value or 0)
            sessions = int(self.sessions_until_long_break_field.value or 0)
            delay = int(self.auto_start_delay_field.value or 0)

            if work_min * 60 + work_sec <= 0:
                return
            if break_min * 60 + break_sec <= 0:
                return
            if long_break_min * 60 + long_break_sec <= 0:
                return
            if sessions <= 0 or delay < 1:
                return
            if work_sec >= 60 or break_sec >= 60 or long_break_sec >= 60:
                return

            settings = {
                "work_min": work_min,
                "work_sec": work_sec,
                "break_min": break_min,
                "break_sec": break_sec,
                "long_break_min": long_break_min,
                "long_break_sec": long_break_sec,
                "sessions_until_long_break": sessions,
                "sound_enabled": self.sound_checkbox.value,
                "auto_start": self.auto_start_checkbox.value,
                "auto_start_delay": delay,
                "sound_type": self._get_current_sound_type(),
                "theme": "dark",
            }

            with SessionLocal() as db:
                update_settings(db, settings)

            if self.on_settings_changed:
                self.on_settings_changed(settings)

        except ValueError:
            pass