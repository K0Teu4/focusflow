# ui/theme.py
import flet as ft

PINK = "#FECCE7"
DARK_BLUE = "#08033D"

COLORS = {
    "bg": DARK_BLUE,
    "surface": "#1A1A4D",
    "primary": PINK,
    "text": "#FFFFFF",
    "text_secondary": "#A0A0C0",
    "pause_work": "#FFB88C",
    "pause_rest": "#5A9FD4",
    "reset": "#6B3A3A",
    "reset_border": "#8B5555",
    "skip": "#7EB6FF",
    "work": "#FECCE7",
    "work_bg": "#2A1535",
    "rest": "#7EB6FF",
    "rest_bg": "#0F1F3D",
    "long_break": "#A78BFA",
    "long_break_bg": "#1A1540",
    "success": "#4CAF50",
    "error": "#F44336",
    "cat_work": "#FECCE7",
    "cat_rest": "#7EB6FF",
    "cat_hobby": "#B8E6A0",
    "cat_study": "#FFD88C",
}

# НОВОЕ: тени для карточек
SHADOWS = {
    "card": ft.BoxShadow(
        spread_radius=0,
        blur_radius=8,
        color="#00000040",
        offset=ft.Offset(0, 2),
    ),
    "elevated": ft.BoxShadow(
        spread_radius=0,
        blur_radius=12,
        color="#00000060",
        offset=ft.Offset(0, 4),
    ),
}

# НОВОЕ: градиенты
GRADIENTS = {
    "work": ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=["#2A1535", "#1A1A4D"],
    ),
    "rest": ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=["#0F1F3D", "#1A1A4D"],
    ),
    "long_break": ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=["#1A1540", "#1A1A4D"],
    ),
}

def get_theme():
    return ft.Theme(
        color_scheme_seed=PINK,
    )