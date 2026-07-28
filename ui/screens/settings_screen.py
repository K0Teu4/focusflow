# ui/screens/settings_screen.py
import asyncio
import flet as ft
from db.database import SessionLocal, get_settings, update_settings
from services.premium_service import PremiumService
from services.sound_service import SoundService, SOUNDS
from ui.theme import (
    COLORS, with_alpha, get_theme_names, get_theme_display_name,
    is_premium_theme, THEMES,
)
from ui.sheet import show_sheet, sheet_action

_F_W = 56
_U_W = 26
_SP = 6
_PAD = ft.padding.Padding(10, 12, 10, 12)


class SettingsScreen(ft.Column):
    """Настройки: длительность, поведение, темы (Free 2 / Premium 6), premium-статус.
    Позиция скролла сохраняется между сменами темы и переходами на вкладку."""

    def __init__(self, page: ft.Page, on_settings_changed=None, on_open_premium=None, on_theme_changed=None):
        super().__init__(spacing=15, expand=True, scroll=ft.ScrollMode.AUTO)
        self._page = page
        self.on_settings_changed = on_settings_changed
        self.on_open_premium = on_open_premium
        self.on_theme_changed = on_theme_changed
        self.sound_service = SoundService()
        self.sound_service.bind_page(page)

        try:
            self.on_scroll = self._on_scroll
        except Exception:
            pass

        with SessionLocal() as db:
            settings = get_settings(db)
            self._current_theme = settings.get("theme", "dark")

        _pst = PremiumService.get_status()
        self.is_premium = _pst["is_premium"]
        self.premium_expires = _pst["expires_at"]

        def auto_save(e=None):
            self._save_current_values()

        def num_field(value):
            return ft.TextField(
                value=str(value), hint_text="00",
                keyboard_type=ft.KeyboardType.NUMBER,
                border_color=COLORS["primary"], color=COLORS["text"], bgcolor=COLORS["surface"],
                text_align=ft.TextAlign.CENTER, width=_F_W, content_padding=_PAD,
                on_change=auto_save,
            )

        def unit(text):
            return ft.Container(
                width=_U_W, alignment=ft.Alignment(0, 0),
                content=ft.Text(text, size=12, color=COLORS["text_secondary"]),
            )

        def make_time_row(label: str, min_val: int, sec_val: int):
            min_field = num_field(min_val)
            sec_field = num_field(sec_val)
            row = ft.Row([
                ft.Text(label, size=13, color=COLORS["text"],
                        weight=ft.FontWeight.W_500, expand=True),
                min_field, unit("мин"), sec_field, unit("сек"),
            ], spacing=_SP, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            return min_field, sec_field, row

        # === ДЛИТЕЛЬНОСТЬ ===
        self.work_min_field, self.work_sec_field, work_row = make_time_row(
            "Работа", int(settings.get("work_min", 25)), int(settings.get("work_sec", 0)))
        self.break_min_field, self.break_sec_field, break_row = make_time_row(
            "Короткий отдых", int(settings.get("break_min", 5)), int(settings.get("break_sec", 0)))
        self.long_break_min_field, self.long_break_sec_field, long_break_row = make_time_row(
            "Длинный перерыв", int(settings.get("long_break_min", 15)), int(settings.get("long_break_sec", 0)))

        self.sessions_until_long_break_field = ft.TextField(
            value=str(settings.get("sessions_until_long_break", 4)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"], color=COLORS["text"], bgcolor=COLORS["surface"],
            text_align=ft.TextAlign.CENTER, width=_F_W, content_padding=_PAD,
            on_change=auto_save,
        )
        sessions_row = ft.Row([
            ft.Text("Сессий до длинного перерыва", size=13, color=COLORS["text"],
                    weight=ft.FontWeight.W_500, expand=True),
            ft.Container(width=_F_W), unit(""),
            self.sessions_until_long_break_field, unit(""),
        ], spacing=_SP, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # === ПОВЕДЕНИЕ ===
        self.sound_checkbox = ft.Switch(
            label="Звук при завершении", value=settings.get("sound_enabled", True),
            active_color=COLORS["primary"], inactive_thumb_color=COLORS["text_secondary"],
            on_change=auto_save, label_text_style=ft.TextStyle(size=14, color=COLORS["text"]),
        )

        self.sound_row = ft.Column([
            ft.Text("Звук уведомления", size=14, color=COLORS["text"], weight=ft.FontWeight.W_500),
            self._build_sound_button(),
        ], spacing=6)

        self.auto_start_checkbox = ft.Switch(
            label="Автостарт следующей сессии", value=settings.get("auto_start", False),
            active_color=COLORS["primary"], inactive_thumb_color=COLORS["text_secondary"],
            on_change=auto_save, label_text_style=ft.TextStyle(size=14, color=COLORS["text"]),
        )
        self.auto_start_delay_field = ft.TextField(
            value=str(settings.get("auto_start_delay", 3)),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=COLORS["primary"], color=COLORS["text"], bgcolor=COLORS["surface"],
            text_align=ft.TextAlign.CENTER, width=_F_W, content_padding=_PAD,
            on_change=auto_save,
        )
        delay_row = ft.Row([
            ft.Text("Задержка автостарта", size=14, color=COLORS["text"], weight=ft.FontWeight.W_500, expand=True),
            self.auto_start_delay_field, unit("сек"),
        ], spacing=_SP, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        # === PREMIUM-СТАТУС ===
        if self.is_premium:
            expires_text = (f"до {self.premium_expires.strftime('%d.%m.%Y')}"
                            if self.premium_expires else "бессрочно")
            self.premium_status = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.VERIFIED, size=24, color=COLORS["success"]),
                    ft.Column([
                        ft.Text("Premium активен", size=16, weight=ft.FontWeight.BOLD, color=COLORS["success"]),
                        ft.Text(f"Действует {expires_text}", size=12, color=COLORS["text_secondary"]),
                    ], spacing=0),
                ], spacing=12),
                padding=16, bgcolor=COLORS["surface"], border_radius=16,
                margin=ft.Margin(20, 0, 20, 0),
            )
        else:
            self.premium_status = ft.Container(
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.STAR, size=24, color=COLORS["primary"]),
                            ft.Text("FocusFlow Premium", size=16, weight=ft.FontWeight.BOLD, color=COLORS["primary"])],
                           spacing=8),
                    ft.Container(height=8),
                    ft.Text("Режим Фокус, 6 тем, heatmap и 3+ звука", size=13, color=COLORS["text_secondary"]),
                    ft.Container(height=12),
                    ft.ElevatedButton("Открыть Premium", bgcolor=COLORS["primary"], color=COLORS["bg"],
                                      on_click=self._navigate_to_premium, width=200, height=44),
                ], horizontal_alignment=ft.CrossAxisAlignment.START),
                padding=20, bgcolor=COLORS["surface"], border_radius=16,
                border=ft.BorderSide(1.5, COLORS["primary"]), margin=ft.Margin(20, 0, 20, 0),
            )

        # === СБОРКА ===
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Настройки", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ft.Container(height=6),
                    ft.Row([ft.Icon(ft.Icons.SAVE_OUTLINED, size=16, color=COLORS["text_secondary"]),
                            ft.Text("Все изменения сохраняются автоматически", size=13, color=COLORS["text_secondary"])],
                           spacing=6),
                ], spacing=0),
                padding=ft.padding.Padding(20, 20, 20, 10),
            ),
            self.premium_status,
            ft.Container(
                content=ft.Column([
                    ft.Text("Длительность", size=18, color=COLORS["text"]),
                    ft.Container(height=10), work_row, ft.Container(height=8),
                    break_row, ft.Container(height=8), long_break_row,
                    ft.Container(height=12), sessions_row,
                ], spacing=8),
                padding=20, bgcolor=COLORS["surface"], border_radius=16, margin=ft.Margin(20, 0, 20, 0),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Поведение", size=18, color=COLORS["text"]),
                    ft.Container(height=8), self.sound_checkbox, ft.Container(height=8), self.sound_row,
                    ft.Container(height=12), self.auto_start_checkbox, ft.Container(height=8), delay_row,
                ], spacing=8),
                padding=20, bgcolor=COLORS["surface"], border_radius=16, margin=ft.Margin(20, 0, 20, 0),
            ),
            self._build_theme_section(),
            ft.Container(height=40),
        ]

        pos = getattr(page, "_ff_settings_scroll", 0.0)
        if pos and pos > 0:
            try:
                asyncio.create_task(self._restore_scroll(pos))
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    def _on_scroll(self, e):
        try:
            self._page._ff_settings_scroll = float(getattr(e, "pixels", 0) or 0)
        except Exception:
            pass

    async def _restore_scroll(self, pos):
        try:
            await asyncio.sleep(0.06)
            await self.scroll_to(offset=pos, duration=0)
        except Exception:
            pass

    def refresh_data(self):
        self.__init__(self._page, self.on_settings_changed, self.on_open_premium, self.on_theme_changed)

    # ------------------------------------------------------------------ #
    def _build_sound_button(self):
        with SessionLocal() as db:
            cur = get_settings(db).get("sound_type", "bell")
        name = SOUNDS.get(cur, SOUNDS["bell"])["name"]
        return ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.MUSIC_NOTE, size=18, color=COLORS["primary"]),
                ft.Text(name, size=14, color=COLORS["text"], expand=True),
                ft.Icon(ft.Icons.ARROW_DROP_DOWN, size=22, color=COLORS["text_secondary"]),
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(14, 12, 10, 12),
            bgcolor=COLORS["surface_2"], border_radius=12,
            border=ft.BorderSide(1, with_alpha(COLORS["text_secondary"], 0x55)),
            on_click=self._open_sound_dialog, ink=True,
        )

    def _refresh_sound_button(self):
        self.sound_row.controls[1] = self._build_sound_button()

    # ------------------------------------------------------------------ #
    def _build_theme_section(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Оформление", size=18, color=COLORS["text"]),
                    ft.Container(
                        content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color=COLORS["bg"]),
                        bgcolor=COLORS["primary"], border_radius=4,
                        padding=ft.padding.Padding(6, 2, 6, 2),
                    ),
                ], spacing=8),
                ft.Container(height=12),
                self._build_theme_grid(),
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16, margin=ft.Margin(20, 0, 20, 0),
        )

    def _build_theme_grid(self):
        names = get_theme_names()
        rows = []
        for i in range(0, len(names), 2):
            pair = names[i:i + 2]
            rows.append(ft.Row([self._theme_card(n) for n in pair], spacing=10))
        return ft.Column(rows, spacing=10)

    def _theme_card(self, name):
        theme = THEMES[name]
        c = theme["colors"]
        is_selected = name == self._current_theme
        locked = is_premium_theme(name) and not self.is_premium

        preview = ft.Row([
            ft.Container(width=18, height=18, border_radius=9, bgcolor=c["bg"],
                         border=ft.BorderSide(1, with_alpha(COLORS["text_secondary"], 0x55))),
            ft.Container(width=18, height=18, border_radius=9, bgcolor=c["primary"]),
            ft.Container(width=18, height=18, border_radius=9, bgcolor=c["work"]),
        ], spacing=6)

        label_row = ft.Row([
            ft.Text(get_theme_display_name(name), size=13,
                    weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.NORMAL,
                    color=COLORS["text"], expand=True),
            ft.Icon(ft.Icons.CHECK_CIRCLE if is_selected else
                    (ft.Icons.LOCK if locked else ft.Icons.CIRCLE_OUTLINED),
                    size=18,
                    color=COLORS["primary"] if is_selected else COLORS["text_secondary"]),
        ], spacing=6)

        def on_click(e):
            if locked:
                self._navigate_to_premium()
                return
            self._current_theme = name
            with SessionLocal() as db:
                s = get_settings(db)
                s["theme"] = name
                update_settings(db, s)
            if self.on_theme_changed:
                self.on_theme_changed(name)
            self.refresh_data()

        return ft.Container(
            content=ft.Column([preview, ft.Container(height=8), label_row], spacing=0),
            padding=14, expand=True,
            bgcolor=COLORS["surface_2"] if is_selected else COLORS["bg"],
            border_radius=14,
            border=ft.BorderSide(2, COLORS["primary"]) if is_selected else
                  ft.BorderSide(1, with_alpha(COLORS["text_secondary"], 0x30)),
            on_click=on_click, ink=True,
            opacity=0.6 if locked else 1.0,
        )

    # ------------------------------------------------------------------ #
    def _create_pro_badge(self):
        return ft.Container(
            content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color=COLORS["bg"]),
            bgcolor=COLORS["primary"], border_radius=4, padding=ft.padding.Padding(6, 2, 6, 2),
        )

    def _open_sound_dialog(self, e):
        current = self._get_current_sound_type()

        def build(close):
            rows = []
            for sid, info in SOUNDS.items():
                is_locked = info["premium"] and not self.is_premium
                label = f"🔒 {info['name']}" if is_locked else info["name"]

                def pick(sound_id, locked):
                    def handler(ev):
                        if locked:
                            close()
                            self._show_premium_for_sound_dialog()
                            return
                        self._set_current_sound(sound_id)
                        self.sound_service.play(sound_id)
                        close()
                    return handler

                rows.append(sheet_action(
                    ft.Icons.LOCK if is_locked else ft.Icons.MUSIC_NOTE, label,
                    pick(sid, is_locked), selected=(sid == current),
                    icon_color=COLORS["text_secondary"] if is_locked else COLORS["primary"],
                ))
            return rows

        show_sheet(self._page, "Звук уведомления", build)

    def _get_current_sound_type(self) -> str:
        with SessionLocal() as db:
            return get_settings(db).get("sound_type", "bell")

    def _set_current_sound(self, sound_id: str):
        with SessionLocal() as db:
            settings = get_settings(db)
            settings["sound_type"] = sound_id
            update_settings(db, settings)
        self._refresh_sound_button()
        self._page.update()
        if self.on_settings_changed:
            self.on_settings_changed(settings)

    def _show_premium_for_sound_dialog(self):
        dialog = ft.AlertDialog(
            title=ft.Text("🔒 Premium звук"),
            content=ft.Text("Этот звук доступен только в Premium версии."),
            actions=[ft.TextButton("Остаться на Free", on_click=lambda e: self._close_dialog(dialog)),
                     ft.TextButton("Открыть Premium", on_click=lambda e: self._go_to_premium(dialog))],
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
                "work_min": work_min, "work_sec": work_sec,
                "break_min": break_min, "break_sec": break_sec,
                "long_break_min": long_break_min, "long_break_sec": long_break_sec,
                "sessions_until_long_break": sessions,
                "sound_enabled": self.sound_checkbox.value,
                "auto_start": self.auto_start_checkbox.value,
                "auto_start_delay": delay,
                "sound_type": self._get_current_sound_type(),
                "theme": self._current_theme,
            }
            with SessionLocal() as db:
                update_settings(db, settings)
            if self.on_settings_changed:
                self.on_settings_changed(settings)
        except ValueError:
            pass