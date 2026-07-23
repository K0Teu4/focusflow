# ui/theme.py
import flet as ft

# === ТЁМНАЯ ТЕМА (по умолчанию) ===
DARK_COLORS = {
    "bg": "#08033D",
    "surface": "#1A1A4D",
    "primary": "#FECCE7",
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

# === СВЕТЛАЯ ТЕМА (cyan вместо розового) ===
LIGHT_COLORS = {
    "bg": "#F0F0F8",
    "surface": "#FFFFFF",
    "primary": "#00AEEF",
    "text": "#1A1A2E",
    "text_secondary": "#6B6B8D",
    "pause_work": "#FF9A5C",
    "pause_rest": "#4A8FC4",
    "reset": "#D4A0A0",
    "reset_border": "#B07070",
    "skip": "#5A9FE6",
    "work": "#00AEEF",
    "work_bg": "#E0F7FF",
    "rest": "#5A9FE6",
    "rest_bg": "#E8F0FD",
    "long_break": "#8B6FE8",
    "long_break_bg": "#F0E8FD",
    "success": "#4CAF50",
    "error": "#F44336",
    "cat_work": "#00AEEF",
    "cat_rest": "#5A9FE6",
    "cat_hobby": "#7BC45A",
    "cat_study": "#E6A83C",
}

# === ГРАДИЕНТЫ ===
DARK_GRADIENTS = {
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

LIGHT_GRADIENTS = {
    "work": ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=["#E0F7FF", "#F0F0F8"],
    ),
    "rest": ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=["#E8F0FD", "#F0F0F8"],
    ),
    "long_break": ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=["#F0E8FD", "#F0F0F8"],
    ),
}

# === ТЕНИ ===
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

# === ТЕКУЩАЯ ТЕМА ===
COLORS = DARK_COLORS.copy()
GRADIENTS = DARK_GRADIENTS.copy()


def set_theme(theme_name: str):
    source_colors = DARK_COLORS if theme_name == "dark" else LIGHT_COLORS
    COLORS.clear()
    COLORS.update(source_colors)

    source_gradients = DARK_GRADIENTS if theme_name == "dark" else LIGHT_GRADIENTS
    GRADIENTS.clear()
    GRADIENTS.update(source_gradients)


def get_flet_theme_mode(theme_name: str):
    return ft.ThemeMode.DARK if theme_name == "dark" else ft.ThemeMode.LIGHT


def get_theme():
    return ft.Theme(
        color_scheme_seed=COLORS["primary"],
    )