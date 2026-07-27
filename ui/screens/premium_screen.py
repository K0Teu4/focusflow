# ui/screens/premium_screen.py
import flet as ft
from db.database import SessionLocal, get_user_state, update_premium_status
from ui.theme import COLORS, SHADOWS, with_alpha
from ui.toast import show_toast
from ui.sheet import show_sheet, sheet_action

# --------------------------------------------------------------------------- #
# РЕЕСТР ФИЧ                                                                  #
# PREMIUM_FEATURES — за замком для Free (gated=True).                         #
# FREE_FEATURES    — всегда доступны (галочка у всех).                        #
# COMING_FEATURES  — в разработке («скоро»).                                  #
# Цвет в кортеже — для живой разноцветной сетки иконок.                       #
# --------------------------------------------------------------------------- #
PREMIUM_FEATURES = [
    (ft.Icons.FULLSCREEN, "Режим «Фокус»",
     "Полноэкранный таймер без отвлекающих факторов", "#7AA2F7"),
    (ft.Icons.PALETTE, "Кастомные темы",
     "6 уникальных оформлений интерфейса", "#BB9AF7"),
    (ft.Icons.GRID_ON, "Heatmap активности",
     "Календарь продуктивности по месяцам", "#F7768E"),
    (ft.Icons.SHOW_CHART, "Расширенная статистика",
     "Сравнение периодов и тренды за 30 и 90 дней", "#7DCFFF"),
    (ft.Icons.MUSIC_NOTE, "Расширенные звуки",
     "3+ звука уведомления на выбор", "#9ECE6A"),
]

FREE_FEATURES = [
    (ft.Icons.CLOUD_DOWNLOAD_OUTLINED, "Экспорт и резервная копия",
     "Сохранение всех сессий в CSV и JSON", "#7DCFFF"),
    (ft.Icons.BAR_CHART, "Базовая статистика",
     "Графики, серия дней и последние сессии", "#9ECE6A"),
]

COMING_FEATURES = [
    (ft.Icons.CLOUD_OUTLINED, "Облачная синхронизация",
     "Одни данные на всех ваших устройствах", "#8B94A8"),
]


class PremiumScreen(ft.Column):
    """Экран Premium: статус/оффер + актуальный список фич с гейтингом."""

    def __init__(self, page: ft.Page, on_premium_changed=None):
        super().__init__(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
        self._page = page
        self.on_premium_changed = on_premium_changed

        with SessionLocal() as db:
            user = get_user_state(db)
            self.is_premium = user.is_premium
            self.premium_expires = user.premium_expires_at

        self.controls = [
            ft.Container(
                content=ft.Text("Premium", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                padding=ft.padding.Padding(20, 20, 20, 12)),
            self._status_card(),
            self._section_title("Входит в Premium", COLORS["primary"]),
            self._features_block(PREMIUM_FEATURES, gated=True),
            self._section_title("Во всех тарифах", COLORS["success"]),
            self._features_block(FREE_FEATURES, gated=False, coming=False),
            self._section_title("Скоро", COLORS["text_secondary"]),
            self._features_block(COMING_FEATURES, gated=False, coming=True),
            ft.Container(height=12),
            self._action_area(),
            ft.Container(height=40),
        ]

    def refresh_data(self):
        self.__init__(self._page, self.on_premium_changed)

    # ------------------------------------------------------------------ #
    # СТАТУС-КАРТОЧКА: двухслойный ореол у звезды для глубины             #
    # ------------------------------------------------------------------ #
    def _star_halo(self, color):
        """Звезда в двухслойном светящемся ореоле (внешнее свечение + подложка)."""
        return ft.Container(
            width=92, height=92, border_radius=46,
            bgcolor=with_alpha(color, 0x10),  # внешнее мягкое свечение
            alignment=ft.Alignment(0, 0),
            content=ft.Container(
                width=70, height=70, border_radius=35,
                bgcolor=with_alpha(color, 0x22),  # внутренняя подложка
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.STAR_ROUNDED, size=40, color=color),
            ),
        )

    def _status_card(self):
        if self.is_premium:
            expires_text = (f"Действует до {self.premium_expires.strftime('%d.%m.%Y')}"
                            if self.premium_expires else "Действует бессрочно")
            accent = COLORS["success"]
            body = ft.Column([
                self._star_halo("#FFD54F"),
                ft.Container(height=14),
                ft.Text("Premium активен", size=24, weight=ft.FontWeight.BOLD, color=accent),
                ft.Container(height=4),
                ft.Text(expires_text, size=14, color=COLORS["text_secondary"]),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            border_color = with_alpha(accent, 0x55)
        else:
            accent = COLORS["primary"]
            body = ft.Column([
                self._star_halo(accent),
                ft.Container(height=14),
                ft.Text("FocusFlow Premium", size=24, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=6),
                ft.Text("Раскройте весь потенциал фокуса:\nбольше тем, глубокая аналитика\nи режим без отвлекающих факторов.",
                        size=14, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
            border_color = with_alpha(accent, 0x55)

        return ft.Container(
            content=body,
            padding=ft.padding.Padding(20, 26, 20, 26),
            bgcolor=COLORS["surface"], border_radius=20,
            border=ft.BorderSide(1.5, border_color),
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 16))

    # ------------------------------------------------------------------ #
    # ЗАГОЛОВОК СЕКЦИИ: акцентная полоска слева (не hairline на всю ширину)#
    # ------------------------------------------------------------------ #
    def _section_title(self, text, accent):
        return ft.Container(
            content=ft.Row([
                ft.Container(width=3, height=14, border_radius=2, bgcolor=accent),
                ft.Text(text.upper(), size=12, weight=ft.FontWeight.BOLD,
                        color=COLORS["text_secondary"]),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(24, 10, 24, 8))

    # ------------------------------------------------------------------ #
    def _features_block(self, features, gated=False, coming=False):
        return ft.Container(
            content=ft.Column([self._feature_row(*f, gated=gated, coming=coming) for f in features], spacing=8),
            margin=ft.Margin(20, 0, 20, 8))

    def _feature_row(self, icon, title, subtitle, color, gated=False, coming=False):
        # Статус справа: «скоро» / замок / галочка
        if coming:
            status = ft.Icon(ft.Icons.ACCESS_TIME, size=20, color=COLORS["text_secondary"])
        elif gated and not self.is_premium:
            status = ft.Icon(ft.Icons.LOCK_OUTLINE, size=18, color=COLORS["text_secondary"])
        else:
            status = ft.Container(
                content=ft.Icon(ft.Icons.CHECK, size=14, color=COLORS["bg"]),
                width=22, height=22, border_radius=11,
                bgcolor=COLORS["success"], alignment=ft.Alignment(0, 0))

        locked = gated and not self.is_premium

        row = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=22, color=color),
                    width=44, height=44, border_radius=12,
                    bgcolor=with_alpha(color, 0x1A), alignment=ft.Alignment(0, 0)),
                ft.Column([
                    ft.Text(title, size=15, weight=ft.FontWeight.BOLD,
                            color=COLORS["text"] if not locked else COLORS["text_secondary"]),
                    ft.Text(subtitle, size=12, color=COLORS["text_secondary"]),
                ], spacing=2, expand=True),
                status,
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"],
            opacity=0.7 if (locked or coming) else 1.0,
        )
        # Hover-подсветка (отклик на десктопе; на мобилке безвредно не срабатывает)
        row.on_hover = self._make_row_hover(row, color, locked or coming)
        return row

    def _make_row_hover(self, row, color, dim):
        def h(e):
            hovered = str(getattr(e, "data", "")).lower() == "true"
            if dim:
                row.border = None
                row.shadow = SHADOWS["card"]
            elif hovered:
                row.border = ft.BorderSide(1, with_alpha(color, 0x70))
                row.shadow = SHADOWS["elevated"]
            else:
                row.border = None
                row.shadow = SHADOWS["card"]
            self._page.update()
        return h

    # ------------------------------------------------------------------ #
    # ДЕЙСТВИЕ: покупка (Free) / отмена (Premium)                         #
    # ------------------------------------------------------------------ #
    def _action_area(self):
        if self.is_premium:
            return ft.Container(
                content=ft.Column([
                    ft.Text("Спасибо, что вы с нами 💜", size=15,
                            color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
                    ft.Container(height=12),
                    ft.OutlinedButton(
                        "Отменить подписку",
                        style=ft.ButtonStyle(side=ft.BorderSide(1.5, with_alpha(COLORS["error"], 0x66)),
                                             color=COLORS["error"]),
                        on_click=self._on_cancel, width=240, height=44),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                margin=ft.Margin(20, 8, 20, 0))

        return ft.Container(
            content=ft.Column([
                ft.ElevatedButton(
                    "Оформить Premium",
                    bgcolor=COLORS["primary"], color=COLORS["bg"],
                    on_click=self._on_buy, width=260, height=52,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16))),
                ft.Container(height=8),
                ft.Text("Покупка появится в ближайшем обновлении",
                        size=12, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
            margin=ft.Margin(20, 8, 20, 0))

    # ------------------------------------------------------------------ #
    def _on_buy(self, e):
        # Заглушка до интеграции RuStore Pay SDK / веб-покупки.
        show_toast(self._page, "Покупка появится в следующем обновлении",
                   ft.Icons.INFO_OUTLINE, COLORS["primary"], duration=3000)

    def _on_cancel(self, e):
        def build(close):
            return [sheet_action(
                ft.Icons.CHECK, "Да, отменить Premium",
                lambda ev: (close(), self._do_cancel()))]
        show_sheet(self._page, "Отменить Premium?", build)

    def _do_cancel(self):
        with SessionLocal() as db:
            update_premium_status(db, False)
        if self.on_premium_changed:
            self.on_premium_changed(False)
        self.refresh_data()
        show_toast(self._page, "Premium отключён", ft.Icons.INFO_OUTLINE,
                   COLORS["text_secondary"], duration=2500)