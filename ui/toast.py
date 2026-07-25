# ui/toast.py
import asyncio
import flet as ft
from ui.theme import SHADOWS

# Текст/иконки тоста всегда белые — фон цветной в любой теме
WHITE = "#FFFFFF"


def show_toast(page: ft.Page, message: str, icon, color: str,
               action_label: str = None, on_action=None, duration: int = 4000):
    """Плавающее уведомление: прижато к низу контентной области (над панелью вкладок)."""
    # --- закрываем предыдущий тост, чтобы не копились и не накладывались ---
    prev = getattr(page, "_ff_toast", None)
    if prev:
        task = prev.get("task")
        if task and not task.done():
            task.cancel()
        try:
            page.overlay.remove(prev["toast"])
        except Exception:
            pass
        try:
            page.update()
        except Exception:
            pass

    # --- карточка тоста (animate для fade + scale) ---
    # overlay в Flet покрывает только контентную область (между AppBar и
    # NavigationBar), поэтому bottom отсчитывается от её низа — берём маленький
    # отступ, чтобы тост сел вплотную над панелью вкладок.
    toast = ft.Container(
        border_radius=14,
        bgcolor=color,
        shadow=SHADOWS["elevated"],
        padding=ft.padding.Padding(14, 12, 8, 12),
        opacity=0.0,
        scale=0.92,
        animate=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
        left=16,
        right=16,
        bottom=12,
    )

    def hide_now(e=None):
        """Немедленное скрытие по крестику или после undo."""
        cur = getattr(page, "_ff_toast", None)
        if cur and cur.get("task") and not cur["task"].done():
            cur["task"].cancel()
        asyncio.create_task(_hide())

    # --- содержимое: иконка + текст + (Отменить) + крестик ---
    row_controls = [
        ft.Icon(icon, color=WHITE, size=20),
        ft.Text(message, color=WHITE, size=14, expand=True),
    ]

    if action_label:
        def _on_action(ev):
            if on_action:
                on_action(ev)
            hide_now(ev)
        row_controls.append(
            ft.TextButton(
                action_label,
                style=ft.ButtonStyle(
                    color=WHITE,
                    padding=ft.padding.Padding(8, 4, 8, 4),
                ),
                on_click=_on_action,
            )
        )

    row_controls.append(
        ft.IconButton(
            icon=ft.Icons.CLOSE,
            icon_color=WHITE,
            icon_size=18,
            tooltip="Закрыть",
            on_click=hide_now,
            style=ft.ButtonStyle(padding=ft.padding.Padding(6, 4, 6, 4)),
        )
    )

    toast.content = ft.Row(
        row_controls,
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    page.overlay.append(toast)
    page.update()

    # --- появление ---
    toast.opacity = 1.0
    toast.scale = 1.0
    page.update()

    # --- уход ---
    async def _hide():
        try:
            toast.opacity = 0.0
            toast.scale = 0.92
            page.update()
            await asyncio.sleep(0.22)
        except Exception:
            pass
        try:
            page.overlay.remove(toast)
            page.update()
        except Exception:
            pass

    async def auto_hide():
        try:
            await asyncio.sleep(duration / 1000)
        except asyncio.CancelledError:
            return
        await _hide()

    task = asyncio.create_task(auto_hide())
    page._ff_toast = {"toast": toast, "task": task, "hide": hide_now}