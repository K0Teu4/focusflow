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
    # Кнопки
    "pause_work": "#FFB88C",
    "pause_rest": "#5A9FD4",
    "reset": "#6B3A3A",
    "reset_border": "#8B5555",
    "skip": "#7EB6FF",
    # Режимы
    "work": "#FECCE7",
    "work_bg": "#2A1535",
    "rest": "#7EB6FF",
    "rest_bg": "#0F1F3D",
    "long_break": "#A78BFA",
    "long_break_bg": "#1A1540",
    # Статусы
    "success": "#4CAF50",
    "error": "#F44336",
    # Категории
    "cat_work": "#FECCE7",
    "cat_rest": "#7EB6FF",
    "cat_hobby": "#B8E6A0",
    "cat_study": "#FFD88C",
}

def get_theme():
    return ft.Theme(
        color_scheme_seed=PINK,
    )