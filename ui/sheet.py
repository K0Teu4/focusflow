# ui/sheet.py
import asyncio
import flet as ft
from ui.theme import COLORS, SHADOWS, with_alpha


def sheet_action(icon, label, on_click, danger: bool = False,
                 icon_color: str = None, selected: bool = False):
    """Одна строка действия в bottom-sheet."""
    fg = COLORS["error"] if danger else COLORS["text"]
    ic = icon_color or (COLORS["error"] if danger else COLORS["text_secondary"])
    trailing = [ft.Icon(ft.Icons.CHECK, size=18, color=COLORS["primary"])] if selected else []
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=20, color=ic),
            ft.Text(label, size=15, color=fg,
                    weight=ft.FontWeight.W_600 if selected else ft.FontWeight.NORMAL, expand=True),
            *trailing,
        ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.Padding(14, 13, 14, 13),
        border_radius=12,
        bgcolor=with_alpha(COLORS["primary"], 0x22) if selected else COLORS["surface"],
        margin=ft.Margin(4, 2, 4, 2),
        on_click=on_click,
        ink=True,
    )


def show_sheet(page: ft.Page, title: str, build_items):
    """Bottom-sheet поверх контента с затемнением. build_items(close) -> list."""
    prev = getattr(page, "_ff_sheet", None)
    if prev:
        try:
            prev["close"]()
        except Exception:
            pass

    scrim = ft.Container(
        left=0, right=0, top=0, bottom=0,
        bgcolor=with_alpha("#000000", 0x80), opacity=0.0,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
    )
    sheet = ft.Container(
        left=0, right=0, bottom=0,
        bgcolor=COLORS["surface"],
        # В 0.85.3 BorderRadius требует все 4 угла явно.
        border_radius=ft.BorderRadius(top_left=22, top_right=22, bottom_left=0, bottom_right=0),
        shadow=SHADOWS["elevated"],
        padding=ft.padding.Padding(6, 4, 6, 6),
        offset=ft.Offset(0, 1), opacity=0.0,
        animate=ft.Animation(240, ft.AnimationCurve.EASE_OUT),
    )
    state = {"scrim": scrim, "sheet": sheet}

    def close(e=None):
        try:
            scrim.opacity = 0.0
            sheet.offset = ft.Offset(0, 1)
            sheet.opacity = 0.0
            page.update()
        except Exception:
            pass

        async def rm():
            await asyncio.sleep(0.24)
            for c in (sheet, scrim):
                try:
                    page.overlay.remove(c)
                except Exception:
                    pass
            try:
                page.update()
            except Exception:
                pass
            if getattr(page, "_ff_sheet", None) is state:
                page._ff_sheet = None

        asyncio.create_task(rm())

    state["close"] = close
    scrim.on_click = close

    body = build_items(close)
    # ВАЖНО: у Text в 0.85.3 нет padding — отступы задаём обёрткой-Container.
    sheet.content = ft.Column([
        ft.Container(
            content=ft.Row([ft.Container(width=40, height=4, border_radius=2,
                                         bgcolor=with_alpha(COLORS["text_secondary"], 0x66))],
                           alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.Padding(0, 10, 0, 6),
        ),
        ft.Container(
            content=ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
            padding=ft.padding.Padding(14, 2, 14, 8),
        ),
        *body,
        ft.Container(height=4),
        sheet_action(ft.Icons.CLOSE, "Отмена", close),
        ft.Container(height=10),
    ], spacing=0)

    page.overlay.append(scrim)
    page.overlay.append(sheet)
    page.update()
    scrim.opacity = 1.0
    sheet.offset = ft.Offset(0, 0)
    sheet.opacity = 1.0
    page.update()
    page._ff_sheet = state