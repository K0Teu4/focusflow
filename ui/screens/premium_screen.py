# ui/screens/premium_screen.py
import flet as ft
from ui.theme import COLORS
from db.database import SessionLocal, get_user_state, update_premium_status
from datetime import datetime, timedelta


class PremiumScreen(ft.Column):
    def __init__(self, page: ft.Page, on_premium_changed=None):
        super().__init__(
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._page = page
        self.on_premium_changed = on_premium_changed

        with SessionLocal() as db:
            user_state = get_user_state(db)
            self.is_premium = user_state.is_premium
            self.premium_expires = user_state.premium_expires_at

        self.controls = self._build_content()

    def _build_content(self):
        controls = []

        # НОВОЕ: Карточка статуса Premium
        if self.is_premium:
            expires_text = (
                f"до {self.premium_expires.strftime('%d.%m.%Y')}"
                if self.premium_expires else "бессрочно"
            )
            controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("⭐", size=40),
                        ft.Text("Premium активен", size=22, weight=ft.FontWeight.BOLD, color=COLORS["success"]),
                        ft.Text(f"Действует {expires_text}", size=14, color=COLORS["text_secondary"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=24,
                    bgcolor=COLORS["surface"],
                    border_radius=16,
                    border=ft.BorderSide(2, COLORS["success"]),
                    margin=ft.Margin(20, 20, 20, 20),
                )
            )
        else:
            controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("FocusFlow Premium", size=32, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                        ft.Text("Разблокируйте все возможности", size=18, color=COLORS["text_secondary"]),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=ft.padding.Padding(20, 30, 20, 20),
                )
            )

        # Список преимуществ
        features = [
            ("📊", "История и графики", "Статистика за всё время"),
            ("📤", "Экспорт данных", "Сохранение в CSV"),
            ("🎵", "Расширенные звуки", "3+ звука на выбор"),
            ("🎨", "Кастомные темы", "Персонализация интерфейса"),
            ("☁️", "Облако", "Синхронизация между устройствами"),
            ("🤖", "Telegram-бот", "Дайджест в Telegram"),
        ]

        features_list = ft.Column(spacing=8, margin=ft.Margin(20, 0, 20, 20))
        for icon, title, desc in features:
            features_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(icon, size=24),
                        ft.Column([
                            ft.Text(title, size=15, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                            ft.Text(desc, size=12, color=COLORS["text_secondary"]),
                        ], spacing=2, expand=True),
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=20, color=COLORS["success"]),
                    ], spacing=12),
                    padding=14,
                    bgcolor=COLORS["surface"],
                    border_radius=12,
                )
            )
        controls.append(features_list)

        # Тарифы
        if not self.is_premium:
            # НОВОЕ: бейдж "Выгодно!"
            monthly = ft.Container(
                content=ft.Column([
                    ft.Text("1 месяц", size=14, color=COLORS["text_secondary"]),
                    ft.Text("149 ₽", size=28, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                padding=20,
                border=ft.BorderSide(2, COLORS["surface"]),
                border_radius=12,
                width=140,
                on_click=lambda e: self._show_purchase_dialog("monthly"),
                ink=True,
            )

            yearly = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("1 год", size=14, color=COLORS["text_secondary"]),
                        ft.Container(
                            content=ft.Text("🔥 Выгодно!", size=10, weight=ft.FontWeight.BOLD, color=COLORS["bg"]),
                            bgcolor=COLORS["success"],
                            border_radius=4,
                            padding=ft.padding.Padding(4, 2, 4, 2),
                        ),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                    ft.Text("990 ₽", size=28, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                    ft.Text("−45%", size=13, color=COLORS["success"], weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                padding=20,
                border=ft.BorderSide(2, COLORS["primary"]),
                border_radius=12,
                width=140,
                on_click=lambda e: self._show_purchase_dialog("yearly"),
                ink=True,
            )

            controls.append(
                ft.Row([monthly, yearly], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
            )

            # НОВОЕ: кнопка Купить на всю ширину
            controls.append(
                ft.Container(
                    content=ft.ElevatedButton(
                        "Купить Premium",
                        bgcolor=COLORS["success"],
                        color=COLORS["bg"],
                        on_click=lambda e: self._show_purchase_dialog("yearly"),
                        width=300,
                        height=52,
                    ),
                    padding=ft.padding.Padding(20, 20, 20, 0),
                    alignment=ft.Alignment(0, 0),
                )
            )

            # НОВОЕ: Восстановить — текстовая ссылка
            controls.append(
                ft.TextButton(
                    "Восстановить покупку",
                    style=ft.ButtonStyle(color=COLORS["text_secondary"]),
                    on_click=self._on_restore,
                    margin=ft.Margin(0, 10, 0, 20),
                )
            )

        controls.append(ft.Container(height=30))
        return controls

    def _show_purchase_dialog(self, plan: str):
        plan_name = "1 месяц" if plan == "monthly" else "1 год"
        price = "149 ₽" if plan == "monthly" else "990 ₽"

        def on_confirm(e):
            days = 30 if plan == "monthly" else 365
            expires_at = datetime.utcnow() + timedelta(days=days)

            with SessionLocal() as db:
                update_premium_status(db, True, expires_at)

            dialog.open = False
            self._page.update()

            if self.on_premium_changed:
                self.on_premium_changed(True)

            success_dialog = ft.AlertDialog(
                title=ft.Text("🎉 Premium активирован!"),
                content=ft.Text(f"Подписка '{plan_name}' активна до {expires_at.strftime('%d.%m.%Y')}"),
                actions=[
                    ft.TextButton("Отлично", on_click=lambda e: self._close_dialog(success_dialog)),
                ],
            )
            self._page.overlay.append(success_dialog)
            success_dialog.open = True
            self._page.update()

        def on_cancel(e):
            dialog.open = False
            self._page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Купить Premium ({plan_name})"),
            content=ft.Column([
                ft.Text(f"Стоимость: {price}", size=16),
                ft.Text("Подписка активируется автоматически", size=14, color=COLORS["text_secondary"]),
                ft.Container(height=8),
                ft.Text("В реальной версии — интеграция с RuStore Billing",
                       size=12, color=COLORS["text_secondary"], italic=True),
            ], spacing=8),
            actions=[
                ft.TextButton("Отмена", on_click=on_cancel),
                ft.TextButton("Купить", on_click=on_confirm),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _on_restore(self, e):
        dialog = ft.AlertDialog(
            title=ft.Text("Восстановление покупки"),
            content=ft.Text("В реальной версии — проверка через RuStore Billing API"),
            actions=[
                ft.TextButton("Понятно", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    def _close_dialog(self, dialog):
        dialog.open = False
        self._page.update()