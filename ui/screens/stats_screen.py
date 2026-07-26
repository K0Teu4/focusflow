# ui/screens/stats_screen.py
import flet as ft
from db.database import (
    SessionLocal, get_total_stats, get_daily_activity,
    get_current_streak, get_recent_sessions, get_user_state,
)
from ui.theme import COLORS, SHADOWS, with_alpha

DAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

SESSION_META = {
    "work":        ("🍅", "Работа",           COLORS["work"]),
    "short_break": ("☕", "Короткий перерыв", COLORS["rest"]),
    "long_break":  ("🌙", "Длинный перерыв",  COLORS["long_break"]),
}


class StatsScreen(ft.Column):
    """Статистика: серия, метрики, гистограмма с осью, фильтр сессий, premium-тизер."""

    def __init__(self, page: ft.Page, on_open_premium=None):
        super().__init__(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
        self._page = page
        self.on_open_premium = on_open_premium
        self.recent_filter = "all"

        with SessionLocal() as db:
            total = get_total_stats(db)
            activity = get_daily_activity(db, 7)
            streak = get_current_streak(db)
            recent = get_recent_sessions(db, 50)
            user = get_user_state(db)
            self.is_premium = user.is_premium

        self._total = total
        self._activity = activity
        self._recent = recent

        self.recent_list = ft.Column(spacing=6)
        self._fill_recent()

        self.controls = [
            ft.Container(
                content=ft.Text("Статистика", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                padding=ft.padding.Padding(20, 20, 20, 12),
            ),
            self._streak_card(streak),
            self._metrics_row(activity, total),
            self._chart_card(activity),
            self._recent_card(),
            self._premium_teaser(),
            ft.Container(height=30),
        ]

    def refresh_data(self):
        self.__init__(self._page, self.on_open_premium)

    # ------------------------------------------------------------------ #
    def _streak_card(self, streak):
        return ft.Container(
            content=ft.Row([
                ft.Text("🔥", size=34),
                ft.Column([
                    ft.Text(f"{streak}", size=30, weight=ft.FontWeight.BOLD, color=COLORS["work"]),
                    ft.Text("дней подряд", size=13, color=COLORS["text_secondary"]),
                ], spacing=0),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 12),
        )

    def _metric(self, value, label, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=11, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=ft.padding.Padding(8, 14, 8, 14),
            bgcolor=COLORS["surface"], border_radius=14, shadow=SHADOWS["card"], expand=True,
        )

    def _metrics_row(self, activity, total):
        minutes = [d["work_minutes"] for d in activity]
        best = max(minutes) if minutes else 0
        avg = round(sum(minutes) / 7) if minutes else 0
        return ft.Container(
            content=ft.Row([
                self._metric(f"{best} м", "Лучший день", COLORS["work"]),
                self._metric(f"{avg} м", "Среднее / день", COLORS["primary"]),
                self._metric(total["total_work_hours"], "Всего часов", COLORS["long_break"]),
            ], spacing=10),
            margin=ft.Margin(20, 0, 20, 12),
        )

    # ------------------------------------------------------------------ #
    def _chart_card(self, activity):
        # Масштаб по секундам: короткие сессии тоже дают пропорциональный столбик.
        seconds = [d.get("work_seconds", d["work_minutes"] * 60) for d in activity]
        has_data = any(s > 0 for s in seconds)

        if not has_data:
            body = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BAR_CHART, size=56, color=with_alpha(COLORS["text_secondary"], 0x55)),
                    ft.Container(height=10),
                    ft.Text("Пока нет данных", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ft.Container(height=4),
                    ft.Text("Запустите первую сессию —\nздесь появится ваша активность.",
                            size=13, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                height=150, alignment=ft.Alignment(0, 0),
            )
        else:
            maxv = max(seconds) or 1
            bars = []
            for d in activity:
                sec = d.get("work_seconds", d["work_minutes"] * 60)
                mins = d["work_minutes"]
                if sec > 0:
                    h = max(14, int(70 * sec / maxv))
                    label = str(mins) if mins > 0 else "<1 м."
                    bar_color = COLORS["work"]
                    label_color = COLORS["work"]
                    label_weight = ft.FontWeight.BOLD
                    bar_shadow = SHADOWS["card"]
                else:
                    h = 4
                    label = ""
                    bar_color = with_alpha(COLORS["text_secondary"], 0x30)
                    label_color = COLORS["text_secondary"]
                    label_weight = ft.FontWeight.NORMAL
                    bar_shadow = None
                # Контейнер фиксированной высоты с прижатием к низу через конструктор
                # Alignment (в 0.85.3 ft.alignment.* констант нет): дни на общей линии,
                # столбики растут вверх.
                bars.append(
                    ft.Container(
                        height=110, expand=True,
                        alignment=ft.Alignment(0, 1),
                        content=ft.Column([
                            ft.Text(label, size=10, color=label_color, weight=label_weight),
                            ft.Container(width=24, height=h, border_radius=7,
                                         bgcolor=bar_color, shadow=bar_shadow),
                            ft.Text(DAY_LABELS[d["date"].weekday()], size=11,
                                    color=COLORS["text_secondary"]),
                        ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    )
                )
            body = ft.Column([
                ft.Row(bars, spacing=4),
                ft.Container(height=2, border_radius=1,
                             bgcolor=with_alpha(COLORS["text_secondary"], 0x30)),
            ], spacing=6)

        return ft.Container(
            content=ft.Column([
                ft.Text("Активность за 7 дней", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=16),
                body,
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 12),
        )

    # ------------------------------------------------------------------ #
    def _recent_card(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("Последние сессии", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"])]),
                ft.Container(height=10),
                self._build_filter_chips(),
                ft.Container(height=12),
                self.recent_list,
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 0),
        )

    def _build_filter_chips(self):
        opts = [("all", "Все"), ("work", "Работа"), ("break", "Перерыв")]
        chips = []
        for key, label in opts:
            sel = key == self.recent_filter

            def make(k):
                return lambda e: self._set_filter(k)

            chips.append(
                ft.Container(
                    content=ft.Text(label, size=12,
                                    weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL,
                                    color=COLORS["bg"] if sel else COLORS["text_secondary"]),
                    bgcolor=COLORS["primary"] if sel else COLORS["surface_2"],
                    border_radius=14, padding=ft.padding.Padding(12, 6, 12, 6),
                    on_click=make(key), ink=True,
                )
            )
        return ft.Row(chips, spacing=8)

    def _set_filter(self, key):
        self.recent_filter = key
        self._fill_recent()
        self.controls[4] = self._recent_card()
        self._page.update()

    def _fill_recent(self):
        rows = self._recent
        if self.recent_filter == "work":
            rows = [r for r in rows if r["type"] == "work"]
        elif self.recent_filter == "break":
            rows = [r for r in rows if r["type"] != "work"]

        self.recent_list.controls.clear()
        if not rows:
            self.recent_list.controls.append(
                ft.Container(
                    content=ft.Text("Нет сессий в этом фильтре", size=13,
                                    color=COLORS["text_secondary"], italic=True),
                    padding=ft.padding.Padding(0, 16, 0, 8), alignment=ft.Alignment(0, 0),
                )
            )
            return

        for s in rows[:20]:
            self.recent_list.controls.append(self._session_row(s))

    def _session_row(self, s):
        icon, name, color = SESSION_META.get(s["type"], ("•", s["type"], COLORS["text"]))
        m = s.get("duration_min", 0)
        sec = s.get("duration_sec", 0)
        rem = sec % 60 if sec else 0
        dur = f"{m} мин {rem} сек" if rem else f"{m} мин"
        when = s["started_at"].strftime("%d.%m %H:%M") if s["started_at"] else ""
        task = s["task_title"] or "Без задачи"
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(icon, size=18), width=38, height=38, border_radius=12,
                    bgcolor=with_alpha(color, 0x26), alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                    ft.Text(task, size=12, color=COLORS["text_secondary"]),
                ], spacing=2, expand=True),
                ft.Column([
                    ft.Text(dur, size=14, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(when, size=11, color=COLORS["text_secondary"]),
                ], horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            padding=12, bgcolor=with_alpha(color, 0x14), border_radius=14,
            margin=ft.Margin(0, 0, 0, 6),
        )

    # ------------------------------------------------------------------ #
    # PREMIUM-ТИЗЕР: базовая статистика бесплатна, расширенная — за замком #
    # ------------------------------------------------------------------ #
    def _premium_teaser(self):
        if self.is_premium:
            return ft.Container(height=0)  # премиум-пользователю тизер не показываем
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INSIGHTS, size=20, color=COLORS["primary"]),
                    ft.Text("Расширенная аналитика", size=16, weight=ft.FontWeight.BOLD,
                            color=COLORS["text"], expand=True),
                    ft.Container(
                        content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color=COLORS["bg"]),
                        bgcolor=COLORS["primary"], border_radius=4,
                        padding=ft.padding.Padding(6, 2, 6, 2),
                    ),
                ], spacing=8),
                ft.Container(height=12),
                self._locked_row(ft.Icons.GRID_ON, "Heatmap активности", "Календарь продуктивности как на GitHub"),
                self._locked_row(ft.Icons.COMPARE_ARROWS, "Сравнение периодов", "Неделя к неделе, месяц к месяцу"),
                self._locked_row(ft.Icons.FILE_DOWNLOAD, "Полный экспорт", "Все сессии в CSV и JSON"),
                ft.Container(height=14),
                ft.ElevatedButton(
                    "Открыть Premium", bgcolor=COLORS["primary"], color=COLORS["bg"],
                    on_click=lambda e: self._go_premium(), width=220, height=44,
                ),
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            border=ft.BorderSide(1.5, with_alpha(COLORS["primary"], 0x66)),
            shadow=SHADOWS["card"], margin=ft.Margin(20, 12, 20, 0),
        )

    def _locked_row(self, icon, title, subtitle):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=20, color=COLORS["text_secondary"]),
                ft.Column([
                    ft.Text(title, size=14, color=COLORS["text"], weight=ft.FontWeight.W_500),
                    ft.Text(subtitle, size=11, color=COLORS["text_secondary"]),
                ], spacing=1, expand=True),
                ft.Icon(ft.Icons.LOCK, size=16, color=COLORS["text_secondary"]),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(4, 8, 4, 8),
            on_click=lambda e: self._go_premium(), ink=True,
        )

    def _go_premium(self):
        if self.on_open_premium:
            self.on_open_premium()