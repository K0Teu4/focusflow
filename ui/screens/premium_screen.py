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

        # Заголовок
        self.title_text = ft.Text(
            "FocusFlow Premium",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=COLORS["primary"],
            margin=ft.Margin(0, 30, 0, 10),
        )

        self.subtitle_text = ft.Text(
            "Разблокируйте все возможности",
            size=18,
            color=COLORS["text_secondary"],
            margin=ft.Margin(0, 0, 0, 30),
        )

        # Список преимуществ
        self.features = [
            ("📊", "История и графики", "Статистика за всё время с графиками"),
            ("📤", "Экспорт данных", "Сохранение сессий в CSV и PDF"),
            ("🎵", "Расширенные звуки", "3+ звука на выбор"),
            ("🎨", "Кастомные темы", "Персонализация интерфейса"),
            ("☁️", "Облако", "Синхронизация между устройствами"),
            ("🤖", "Telegram-бот", "Дайджест продуктивности в Telegram"),
        ]

        self.features_list = ft.Column(
            spacing=12,
            margin=ft.Margin(20, 0, 20, 30),
        )

        for icon, title, desc in self.features:
            self.features_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(icon, size=28),
                        ft.Column([
                            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                            ft.Text(desc, size=13, color=COLORS["text_secondary"]),
                        ], spacing=2, expand=True),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.START),
                    padding=16,
                    bgcolor=COLORS["surface"],
                    border_radius=12,
                    margin=ft.Margin(0, 0, 0, 8),
                )
            )

        # Цены (ИСПРАВЛЕНО: ft.border.all -> ft.BorderSide)
        self.price_monthly = ft.Container(
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

        self.price_yearly = ft.Container(
            content=ft.Column([
                ft.Text("1 год", size=14, color=COLORS["text_secondary"]),
                ft.Text("990 ₽", size=28, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ft.Text("Экономия 45%", size=12, color=COLORS["success"], weight=ft.FontWeight.BOLD),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=20,
            border=ft.BorderSide(2, COLORS["primary"]),
            border_radius=12,
            width=140,
            on_click=lambda e: self._show_purchase_dialog("yearly"),
            ink=True,
        )

        self.pricing_row = ft.Row(
            [self.price_monthly, self.price_yearly],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            margin=ft.Margin(0, 0, 0, 30),
        )

        # Кнопка восстановления
        self.restore_button = ft.TextButton(
            "Восстановить покупку",
            style=ft.ButtonStyle(color=COLORS["text_secondary"]),
            on_click=self._on_restore,
            margin=ft.Margin(0, 0, 0, 20),
        )

        # Статус Premium
        with SessionLocal() as db:
            user_state = get_user_state(db)
            self.is_premium = user_state.is_premium
            self.premium_expires = user_state.premium_expires_at

        if self.is_premium:
            self.status_container = ft.Container(
                content=ft.Column([
                    ft.Text("✓ Premium активен", size=18, weight=ft.FontWeight.BOLD, color=COLORS["success"]),
                    ft.Text(
                        f"Действует до: {self.premium_expires.strftime('%d.%m.%Y')}" if self.premium_expires else "Бессрочно",
                        size=14,
                        color=COLORS["text_secondary"],
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                padding=20,
                bgcolor=COLORS["surface"],
                border_radius=12,
                margin=ft.Margin(20, 0, 20, 30),
            )
        else:
            self.status_container = ft.Container(height=0)

        self.controls = [
            self.title_text,
            self.subtitle_text,
            self.status_container,
            self.features_list,
            self.pricing_row,
            self.restore_button,
            ft.Container(height=30),
        ]

    def _show_purchase_dialog(self, plan: str):
        """Показывает диалог покупки (заглушка для RuStore Billing)"""
        plan_name = "1 месяц" if plan == "monthly" else "1 год"
        price = "149 ₽" if plan == "monthly" else "990 ₽"

        def on_confirm(e):
            # Заглушка: активируем Premium на 30 дней (monthly) или 365 дней (yearly)
            days = 30 if plan == "monthly" else 365
            expires_at = datetime.utcnow() + timedelta(days=days)

            with SessionLocal() as db:
                update_premium_status(db, True, expires_at)

            dialog.open = False
            self._page.update()

            # Уведомляем об изменении
            if self.on_premium_changed:
                self.on_premium_changed(True)

            # Показываем успех
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
                ft.Container(height=10),
                ft.Text("В реальной версии здесь будет интеграция с RuStore Billing", 
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
        """Восстановление покупки (заглушка)"""
        dialog = ft.AlertDialog(
            title=ft.Text("Восстановление покупки"),
            content=ft.Text("В реальной версии здесь будет проверка покупок через RuStore Billing API"),
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