# ui/screens/stats_screen.py
import json
from datetime import datetime, timedelta

import flet as ft
from db.database import (
    SessionLocal, get_total_stats, get_daily_activity,
    get_current_streak, get_recent_sessions,
    get_all_sessions_for_export,
)
from services.premium_service import PremiumService
from ui.theme import COLORS, SHADOWS, with_alpha
from ui.toast import show_toast
from ui.sheet import show_sheet, sheet_action

DAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

SESSION_META = {
    "work":        ("🍅", "Работа",           COLORS["work"]),
    "short_break": ("☕", "Короткий перерыв", COLORS["rest"]),
    "long_break":  ("🌙", "Длинный перерыв",  COLORS["long_break"]),
}


class StatsScreen(ft.Column):
    """Статистика: серия, метрики, график 7д, premium-аналитика (heatmap/сравнение/
    30-90д), последние сессии, бесплатный экспорт (буфер/диалог), premium-тизер."""

    def __init__(self, page: ft.Page, on_open_premium=None):
        super().__init__(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
        self._page = page
        self.on_open_premium = on_open_premium
        self.recent_filter = "all"

        with SessionLocal() as db:
            total = get_total_stats(db)
            activity = get_daily_activity(db, 90)   # один запрос на всю аналитику
            streak = get_current_streak(db)
            recent = get_recent_sessions(db, 50)

        self.is_premium = PremiumService.is_premium()

        self._total = total
        self._activity = activity
        self._recent = recent

        self.recent_list = ft.Column(spacing=6)
        self._fill_recent()
        self._assemble()

    # ------------------------------------------------------------------ #
    def _assemble(self):
        c = [
            ft.Container(
                content=ft.Text("Статистика", size=28, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                padding=ft.padding.Padding(20, 20, 20, 12)),
            self._streak_card(),
            self._metrics_row(),
            self._chart_card(),
        ]
        if self.is_premium:
            c += [self._comparison_card(), self._heatmap_card(),
                  self._extended_card(), self._recent_card(), self._data_card()]
        else:
            c += [self._recent_card(), self._data_card(), self._premium_teaser()]
        c.append(ft.Container(height=30))
        self.controls = c

    def refresh_data(self):
        self.__init__(self._page, self.on_open_premium)

    # ------------------------------------------------------------------ #
    def _slice(self, n):
        return self._activity[-n:] if len(self._activity) >= n else self._activity

    @staticmethod
    def _sum_min(s):
        return sum(d["work_minutes"] for d in s)

    @staticmethod
    def _sum_sess(s):
        return sum(d["work_sessions"] for d in s)

    @staticmethod
    def _best(s):
        return max((d["work_minutes"] for d in s), default=0)

    @staticmethod
    def _avg(s):
        return round(sum(d["work_minutes"] for d in s) / len(s)) if s else 0

    @staticmethod
    def _delta_pct(cur, prev):
        if prev > 0:
            return round((cur - prev) / prev * 100)
        return 100 if cur > 0 else 0

    # ------------------------------------------------------------------ #
    def _streak_card(self):
        streak = get_current_streak(SessionLocal())
        return ft.Container(
            content=ft.Row([
                ft.Text("🔥", size=34),
                ft.Column([
                    ft.Text(f"{streak}", size=30, weight=ft.FontWeight.BOLD, color=COLORS["work"]),
                    ft.Text("дней подряд", size=13, color=COLORS["text_secondary"]),
                ], spacing=0),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 12))

    def _metric(self, value, label, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(str(value), size=24, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=11, color=COLORS["text_secondary"], text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
            padding=ft.padding.Padding(8, 14, 8, 14),
            bgcolor=COLORS["surface"], border_radius=14, shadow=SHADOWS["card"], expand=True)

    def _metrics_row(self):
        last7 = self._slice(7)
        return ft.Container(
            content=ft.Row([
                self._metric(f"{self._best(last7)} м", "Лучший день", COLORS["work"]),
                self._metric(f"{self._avg(last7)} м", "Среднее / день", COLORS["primary"]),
                self._metric(self._total["total_work_hours"], "Всего часов", COLORS["long_break"]),
            ], spacing=10),
            margin=ft.Margin(20, 0, 20, 12))

    # ------------------------------------------------------------------ #
    def _chart_card(self):
        week = self._slice(7)
        seconds = [d.get("work_seconds", d["work_minutes"] * 60) for d in week]
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
                height=150, alignment=ft.Alignment(0, 0))
        else:
            maxv = max(seconds) or 1
            bars = []
            for d in week:
                sec = d.get("work_seconds", d["work_minutes"] * 60)
                mins = d["work_minutes"]
                if sec > 0:
                    h = max(14, int(78 * sec / maxv))
                    label = str(mins) if mins > 0 else "<1 м."
                    bar_color, label_color = COLORS["work"], COLORS["work"]
                    label_weight, bar_shadow = ft.FontWeight.BOLD, SHADOWS["card"]
                else:
                    h, label = 4, ""
                    bar_color = with_alpha(COLORS["text_secondary"], 0x30)
                    label_color = COLORS["text_secondary"]
                    label_weight, bar_shadow = ft.FontWeight.NORMAL, None
                bars.append(ft.Container(
                    height=130, expand=True,
                    content=ft.Column([
                        ft.Container(expand=True),
                        ft.Container(alignment=ft.Alignment(0, 0),
                                     content=ft.Text(label, size=10, color=label_color, weight=label_weight)),
                        ft.Container(width=24, height=h, border_radius=7, bgcolor=bar_color, shadow=bar_shadow),
                        ft.Text(DAY_LABELS[d["date"].weekday()], size=11, color=COLORS["text_secondary"]),
                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True)))
            body = ft.Row(bars, spacing=4)

        return ft.Container(
            content=ft.Column([
                ft.Text("Активность за 7 дней", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=16), body], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 12))

    # ------------------------------------------------------------------ #
    def _delta_chip(self, pct):
        if pct > 0:
            icon, color = ft.Icons.ARROW_UPWARD, COLORS["success"]
        elif pct < 0:
            icon, color = ft.Icons.ARROW_DOWNWARD, COLORS["error"]
        else:
            icon, color = ft.Icons.REMOVE, COLORS["text_secondary"]
        return ft.Row([ft.Icon(icon, size=16, color=color),
                       ft.Text(f"{abs(pct)}%", size=13, weight=ft.FontWeight.BOLD, color=color)],
                      spacing=2)

    def _compare_row(self, label, cur, prev, unit="м"):
        pct = self._delta_pct(cur, prev)
        return ft.Row([
            ft.Text(label, size=14, color=COLORS["text"], expand=True),
            ft.Text(f"{cur} {unit}", size=14, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
            ft.Container(width=8),
            self._delta_chip(pct),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _comparison_card(self):
        cur_w, prev_w = self._sum_min(self._slice(7)), self._sum_min(self._activity[-14:-7])
        cur_m, prev_m = self._sum_min(self._slice(30)), self._sum_min(self._activity[-60:-30])
        cur_ws, prev_ws = self._sum_sess(self._slice(7)), self._sum_sess(self._activity[-14:-7])
        return ft.Container(
            content=ft.Column([
                ft.Text("Сравнение периодов", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=14),
                self._compare_row("Эта неделя / прошлая", cur_w, prev_w),
                ft.Container(height=10),
                self._compare_row("Сессий за неделю", cur_ws, prev_ws, unit=""),
                ft.Container(height=10),
                self._compare_row("Этот месяц / прошлый", cur_m, prev_m),
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 12))

    # ------------------------------------------------------------------ #
    def _heat_color(self, mins):
        if mins <= 0:
            return with_alpha(COLORS["text_secondary"], 0x18)
        if mins <= 30:
            return with_alpha(COLORS["work"], 0x40)
        if mins <= 60:
            return with_alpha(COLORS["work"], 0x70)
        if mins <= 120:
            return with_alpha(COLORS["work"], 0xA0)
        return COLORS["work"]

    def _heatmap_card(self):
        date_map = {d["date"]: d["work_minutes"] for d in self._activity}
        end = self._activity[-1]["date"]
        begin = self._activity[0]["date"]
        start_mon = begin - timedelta(days=begin.weekday())

        weeks = []
        cur = start_mon
        while cur <= end:
            week = [date_map.get(cur + timedelta(days=wd), 0) for wd in range(7)]
            weeks.append(week)
            cur += timedelta(days=7)
        weeks = weeks[-13:]

        week_cols = []
        for week in weeks:
            week_cols.append(ft.Column(
                [ft.Container(width=14, height=14, border_radius=3, bgcolor=self._heat_color(m))
                 for m in week],
                spacing=3))

        legend = ft.Row([
            ft.Text("Меньше", size=11, color=COLORS["text_secondary"]),
            ft.Container(width=12, height=12, border_radius=3, bgcolor=self._heat_color(0)),
            ft.Container(width=12, height=12, border_radius=3, bgcolor=self._heat_color(20)),
            ft.Container(width=12, height=12, border_radius=3, bgcolor=self._heat_color(50)),
            ft.Container(width=12, height=12, border_radius=3, bgcolor=self._heat_color(100)),
            ft.Container(width=12, height=12, border_radius=3, bgcolor=self._heat_color(200)),
            ft.Text("Больше", size=11, color=COLORS["text_secondary"]),
        ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER)

        return ft.Container(
            content=ft.Column([
                ft.Text("Heatmap активности", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=14),
                ft.Row(week_cols, spacing=3, scroll=ft.ScrollMode.AUTO),
                ft.Container(height=12),
                legend,
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 12))

    # ------------------------------------------------------------------ #
    def _ext_block(self, title, s):
        hours = round(self._sum_min(s) / 60, 1)
        return ft.Container(
            content=ft.Column([
                ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=COLORS["primary"]),
                ft.Container(height=8),
                ft.Row([
                    ft.Column([ft.Text(str(self._sum_sess(s)), size=20, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                               ft.Text("сессий", size=11, color=COLORS["text_secondary"])], spacing=2),
                    ft.Column([ft.Text(f"{hours}", size=20, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                               ft.Text("часов", size=11, color=COLORS["text_secondary"])], spacing=2),
                    ft.Column([ft.Text(f"{self._avg(s)} м", size=20, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                               ft.Text("сред / день", size=11, color=COLORS["text_secondary"])], spacing=2),
                    ft.Column([ft.Text(f"{self._best(s)} м", size=20, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                               ft.Text("лучший", size=11, color=COLORS["text_secondary"])], spacing=2),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=0),
            padding=14, bgcolor=COLORS["bg"], border_radius=12, margin=ft.Margin(0, 0, 0, 10))

    def _extended_card(self):
        return ft.Container(
            content=ft.Column([
                ft.Text("Статистика за 30 и 90 дней", size=16, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                ft.Container(height=14),
                self._ext_block("Последние 30 дней", self._slice(30)),
                self._ext_block("Последние 90 дней", self._slice(90)),
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 12))

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
            shadow=SHADOWS["card"], margin=ft.Margin(20, 0, 20, 0))

    def _build_filter_chips(self):
        chips = []
        for key, label in [("all", "Все"), ("work", "Работа"), ("break", "Перерыв")]:
            sel = key == self.recent_filter
            def make(k):
                return lambda e: self._set_filter(k)
            chips.append(ft.Container(
                content=ft.Text(label, size=12,
                                weight=ft.FontWeight.BOLD if sel else ft.FontWeight.NORMAL,
                                color=COLORS["bg"] if sel else COLORS["text_secondary"]),
                bgcolor=COLORS["primary"] if sel else COLORS["surface_2"],
                border_radius=14, padding=ft.padding.Padding(12, 6, 12, 6),
                on_click=make(key), ink=True))
        return ft.Row(chips, spacing=8)

    def _set_filter(self, key):
        self.recent_filter = key
        self._fill_recent()
        self._assemble()
        self._page.update()

    def _fill_recent(self):
        rows = self._recent
        if self.recent_filter == "work":
            rows = [r for r in rows if r["type"] == "work"]
        elif self.recent_filter == "break":
            rows = [r for r in rows if r["type"] != "work"]
        self.recent_list.controls.clear()
        if not rows:
            self.recent_list.controls.append(ft.Container(
                content=ft.Text("Нет сессий в этом фильтре", size=13,
                                color=COLORS["text_secondary"], italic=True),
                padding=ft.padding.Padding(0, 16, 0, 8), alignment=ft.Alignment(0, 0)))
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
                ft.Container(content=ft.Text(icon, size=18), width=38, height=38, border_radius=12,
                             bgcolor=with_alpha(color, 0x26), alignment=ft.Alignment(0, 0)),
                ft.Column([ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                           ft.Text(task, size=12, color=COLORS["text_secondary"])], spacing=2, expand=True),
                ft.Column([ft.Text(dur, size=14, weight=ft.FontWeight.BOLD, color=color),
                           ft.Text(when, size=11, color=COLORS["text_secondary"])],
                          horizontal_alignment=ft.CrossAxisAlignment.END, spacing=2),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
            padding=12, bgcolor=with_alpha(color, 0x14), border_radius=14,
            margin=ft.Margin(0, 0, 0, 6))

    # ------------------------------------------------------------------ #
    def _data_card(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.CLOUD_DOWNLOAD_OUTLINED, size=20, color=COLORS["primary"]),
                        ft.Text("Данные и резервная копия", size=16, weight=ft.FontWeight.BOLD,
                                color=COLORS["text"], expand=True)], spacing=8),
                ft.Container(height=6),
                ft.Text("Экспортируйте все сессии или сохраните копию —\nданные всегда останутся вашими.",
                        size=12, color=COLORS["text_secondary"]),
                ft.Container(height=12),
                ft.Row([
                    self._export_button("CSV", ft.Icons.TABLE_VIEW, "csv"),
                    self._export_button("JSON", ft.Icons.DATA_OBJECT, "json"),
                ], spacing=10),
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            shadow=SHADOWS["card"], margin=ft.Margin(20, 12, 20, 0))

    def _export_button(self, label, icon, fmt):
        return ft.Container(
            content=ft.Row([ft.Icon(icon, size=18, color=COLORS["primary"]),
                            ft.Text(label, size=14, weight=ft.FontWeight.W_600, color=COLORS["text"])],
                           spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.Padding(14, 12, 14, 12), expand=True,
            bgcolor=COLORS["surface_2"], border_radius=12,
            border=ft.BorderSide(1, with_alpha(COLORS["primary"], 0x55)),
            on_click=lambda e, f=fmt: self._do_export(f), ink=True)

    def _build_export_text(self, fmt):
        with SessionLocal() as db:
            rows = get_all_sessions_for_export(db)
        if not rows:
            return None, 0
        if fmt == "json":
            text = json.dumps(rows, ensure_ascii=False, indent=2, default=str)
        else:
            lines = ["started_at,type,duration_sec,task,is_completed"]
            for r in rows:
                when = r["started_at"].strftime("%Y-%m-%d %H:%M:%S") if r["started_at"] else ""
                task = (r["task_title"] or "").replace('"', '""')
                lines.append(f'{when},{r["type"]},{r["duration_sec"]},"{task}",{r["is_completed"]}')
            text = "\n".join(lines)
        return text, len(rows)

    def _do_export(self, fmt):
        text, n = self._build_export_text(fmt)
        if text is None:
            show_toast(self._page, "Нет данных для экспорта", ft.Icons.INFO_OUTLINE,
                       COLORS["text_secondary"], duration=2500)
            return
        self._copy_or_show(text, fmt, n)

    def _copy_or_show(self, text, fmt, n):
        cb = getattr(self._page, "set_clipboard", None)
        copied = False
        if cb:
            try:
                cb(text)
                copied = True
            except Exception as ex:
                print(f"⚠ clipboard error: {ex}")
        if copied:
            show_toast(self._page, f"Скопировано в буфер: {n} сессий ({fmt.upper()})",
                       ft.Icons.CONTENT_COPY, COLORS["success"], duration=3500)
        else:
            field = ft.TextField(value=text, read_only=True, multiline=True, max_lines=8,
                                 border_color=COLORS["primary"], color=COLORS["text"],
                                 bgcolor=COLORS["surface"], width=320)
            def copy_now(ev):
                c2 = getattr(self._page, "set_clipboard", None)
                if c2:
                    try:
                        c2(text)
                        show_toast(self._page, "Скопировано", ft.Icons.CHECK_CIRCLE,
                                   COLORS["success"], duration=2500)
                    except Exception:
                        pass
                dialog.open = False
                self._page.update()
            dialog = ft.AlertDialog(
                title=ft.Text(f"Экспорт {fmt.upper()}"),
                content=field,
                actions=[ft.TextButton("Закрыть", on_click=lambda ev: self._close_dialog(dialog)),
                         ft.TextButton("Скопировать", on_click=copy_now)],
                actions_alignment=ft.MainAxisAlignment.END)
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()

    # ------------------------------------------------------------------ #
    def _premium_teaser(self):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.INSIGHTS, size=20, color=COLORS["primary"]),
                    ft.Text("Расширенная аналитика", size=16, weight=ft.FontWeight.BOLD,
                            color=COLORS["text"], expand=True),
                    ft.Container(content=ft.Text("PRO", size=10, weight=ft.FontWeight.BOLD, color=COLORS["bg"]),
                                 bgcolor=COLORS["primary"], border_radius=4,
                                 padding=ft.padding.Padding(6, 2, 6, 2)),
                ], spacing=8),
                ft.Container(height=12),
                self._locked_row(ft.Icons.GRID_ON, "Heatmap активности", "Календарь продуктивности по месяцам"),
                self._locked_row(ft.Icons.COMPARE_ARROWS, "Сравнение периодов", "Неделя к неделе, месяц к месяцу"),
                self._locked_row(ft.Icons.SHOW_CHART, "Статистика за 30 и 90 дней", "Тренды и детальные цифры"),
                ft.Container(height=14),
                ft.ElevatedButton("Открыть Premium", bgcolor=COLORS["primary"], color=COLORS["bg"],
                                  on_click=lambda e: self._go_premium(), width=220, height=44),
            ], spacing=0),
            padding=20, bgcolor=COLORS["surface"], border_radius=16,
            border=ft.BorderSide(1.5, with_alpha(COLORS["primary"], 0x66)),
            shadow=SHADOWS["card"], margin=ft.Margin(20, 12, 20, 0))

    def _locked_row(self, icon, title, subtitle):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=20, color=COLORS["text_secondary"]),
                ft.Column([ft.Text(title, size=14, color=COLORS["text"], weight=ft.FontWeight.W_500),
                           ft.Text(subtitle, size=11, color=COLORS["text_secondary"])], spacing=1, expand=True),
                ft.Icon(ft.Icons.LOCK, size=16, color=COLORS["text_secondary"]),
            ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.Padding(4, 8, 4, 8),
            on_click=lambda e: self._go_premium(), ink=True)

    def _go_premium(self):
        if self.on_open_premium:
            self.on_open_premium()

    def _close_dialog(self, dialog):
        dialog.open = False
        self._page.update()