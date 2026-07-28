# ui/theme.py
import flet as ft

# =========================================================================== #
# УТИЛИТЫ ЦВЕТОВ (определены первыми — используются в SHADOWS)                #
# =========================================================================== #
def with_alpha(hex_color, alpha):
    """hex '#RRGGBB' + alpha (int 0..255 или float 0..1) -> '#AARRGGBB'."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    a = alpha if isinstance(alpha, int) else int(round(alpha * 255))
    a = max(0, min(255, a))
    return f"#{a:02X}{h.upper()}"


def _channel(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def contrast_on(hex_color: str) -> str:
    """Белый или тёмный текст для читаемости на заданном цвете фона."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return "#FFFFFF"
    lum = 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)
    return "#10131C" if lum > 0.5 else "#FFFFFF"


# =========================================================================== #
# РЕЕСТР ТЕМ                                                                  #
# Free: dark, light. Premium: ocean, sunset, forest, mono.                    #
# Палитры: Tokyo Night, тёплая «бумага», Oceanic teal, Rosé Pine, Everforest, #
# Mono. Светлая намеренно без #FFFFFF — чтобы не выжигала глаза.              #
# =========================================================================== #

THEME_DISPLAY = {
    "dark":   "Тёмная",
    "light":  "Светлая",
    "ocean":  "Океан",
    "sunset": "Закат",
    "forest": "Лес",
    "mono":   "Монохром",
}

PREMIUM_THEMES = {"ocean", "sunset", "forest", "mono"}

THEMES = {
    # ------------------------------------------------------------------ #
    # ТЁМНАЯ — Tokyo Night                                                #
    # ------------------------------------------------------------------ #
    "dark": {
        "colors": {
            "bg": "#1A1B26", "surface": "#24283B", "surface_2": "#2F3349",
            "primary": "#7AA2F7", "text": "#C0CAF5", "text_secondary": "#565F89",
            "pause_work": "#FF9E64", "pause_rest": "#7DCFFF", "reset_border": "#3B4261",
            "skip": "#565F89",
            "work": "#F7768E", "rest": "#7DCFFF", "long_break": "#BB9AF7",
            "success": "#9ECE6A", "error": "#F7768E",
            "cat_work": "#F7768E", "cat_rest": "#7DCFFF",
            "cat_hobby": "#9ECE6A", "cat_study": "#E0AF68",
        },
        "gradients": {
            "work":       ["#2E1A24", "#1A1B26"],
            "rest":       ["#1A2833", "#1A1B26"],
            "long_break": ["#241A33", "#1A1B26"],
        },
        "mode": "dark",
    },
    # ------------------------------------------------------------------ #
    # СВЕТЛАЯ — тёплая «бумага» (без белого, приглушённые акценты)        #
    # ------------------------------------------------------------------ #
    "light": {
        "colors": {
            "bg": "#E8E4DC", "surface": "#F2EFE8", "surface_2": "#DDD8CE",
            "primary": "#5B8DEF", "text": "#4A463E", "text_secondary": "#8A8478",
            "pause_work": "#E08A4C", "pause_rest": "#3FA796", "reset_border": "#C7C1B5",
            "skip": "#8A8478",
            "work": "#E0556B", "rest": "#3FA796", "long_break": "#9B7EDE",
            "success": "#5BA85B", "error": "#E0556B",
            "cat_work": "#E0556B", "cat_rest": "#3FA796",
            "cat_hobby": "#5BA85B", "cat_study": "#D99A3C",
        },
        "gradients": {
            "work":       ["#F0DDE0", "#E8E4DC"],
            "rest":       ["#DCEAE6", "#E8E4DC"],
            "long_break": ["#E6DDF0", "#E8E4DC"],
        },
        "mode": "light",
    },
    # ------------------------------------------------------------------ #
    # ОКЕАН — Oceanic teal (глубокая вода + бирюзовый свет + коралл)      #
    # ------------------------------------------------------------------ #
    "ocean": {
        "colors": {
            "bg": "#081820", "surface": "#0E2733", "surface_2": "#143443",
            "primary": "#2DD4BF", "text": "#D6F5F0", "text_secondary": "#5E8A8F",
            "pause_work": "#FB923C", "pause_rest": "#38BDF8", "reset_border": "#1E4452",
            "skip": "#5E8A8F",
            "work": "#FB7185", "rest": "#38BDF8", "long_break": "#818CF8",
            "success": "#34D399", "error": "#FB7185",
            "cat_work": "#FB7185", "cat_rest": "#38BDF8",
            "cat_hobby": "#34D399", "cat_study": "#FCD34D",
        },
        "gradients": {
            "work":       ["#2A1320", "#081820"],
            "rest":       ["#0C2430", "#081820"],
            "long_break": ["#141830", "#081820"],
        },
        "mode": "dark",
    },
    # ------------------------------------------------------------------ #
    # ЗАКАТ — Rosé Pine (тёплый, сбалансированный)                        #
    # ------------------------------------------------------------------ #
    "sunset": {
        "colors": {
            "bg": "#191724", "surface": "#1F1D2E", "surface_2": "#26233A",
            "primary": "#F6C177", "text": "#E0DEF4", "text_secondary": "#908CAA",
            "pause_work": "#F6C177", "pause_rest": "#9CCFD8", "reset_border": "#403D52",
            "skip": "#908CAA",
            "work": "#EB6F92", "rest": "#9CCFD8", "long_break": "#C4A7E7",
            "success": "#31748F", "error": "#EB6F92",
            "cat_work": "#EB6F92", "cat_rest": "#9CCFD8",
            "cat_hobby": "#31748F", "cat_study": "#F6C177",
        },
        "gradients": {
            "work":       ["#2E1A24", "#191724"],
            "rest":       ["#1A2428", "#191724"],
            "long_break": ["#241A2E", "#191724"],
        },
        "mode": "dark",
    },
    # ------------------------------------------------------------------ #
    # ЛЕС — Everforest Dark (мягкий зелёный)                              #
    # ------------------------------------------------------------------ #
    "forest": {
        "colors": {
            "bg": "#2D353B", "surface": "#343F44", "surface_2": "#3D484D",
            "primary": "#A7C080", "text": "#D3C6AA", "text_secondary": "#859289",
            "pause_work": "#E69875", "pause_rest": "#83C092", "reset_border": "#4F585E",
            "skip": "#859289",
            "work": "#E67E80", "rest": "#83C092", "long_break": "#7FBBB3",
            "success": "#A7C080", "error": "#E67E80",
            "cat_work": "#E67E80", "cat_rest": "#83C092",
            "cat_hobby": "#A7C080", "cat_study": "#DBBC7F",
        },
        "gradients": {
            "work":       ["#3B2E30", "#2D353B"],
            "rest":       ["#2E3B33", "#2D353B"],
            "long_break": ["#2E383B", "#2D353B"],
        },
        "mode": "dark",
    },
    # ------------------------------------------------------------------ #
    # МОНОХРОМ — смягчённый ч/б                                           #
    # ------------------------------------------------------------------ #
    "mono": {
        "colors": {
            "bg": "#161616", "surface": "#222222", "surface_2": "#2C2C2C",
            "primary": "#D4D4D4", "text": "#F0F0F0", "text_secondary": "#808080",
            "pause_work": "#B0B0B0", "pause_rest": "#808080", "reset_border": "#404040",
            "skip": "#606060",
            "work": "#FFFFFF", "rest": "#A0A0A0", "long_break": "#707070",
            "success": "#4CAF50", "error": "#F44336",
            "cat_work": "#FFFFFF", "cat_rest": "#A0A0A0",
            "cat_hobby": "#707070", "cat_study": "#D0D0D0",
        },
        "gradients": {
            "work":       ["#2A2A2A", "#161616"],
            "rest":       ["#222222", "#161616"],
            "long_break": ["#1E1E1E", "#161616"],
        },
        "mode": "dark",
    },
}

# =========================================================================== #
# МУТИРУЕМЫЕ СЛОВАРИ ТЕКУЩЕЙ ТЕМЫ (все импорты COLORS/GRADIENTS смотрят сюда) #
# =========================================================================== #
# Алиасы для обратной совместимости (тесты)
DARK_COLORS = THEMES["dark"]["colors"]
LIGHT_COLORS = THEMES["light"]["colors"]
COLORS = THEMES["dark"]["colors"].copy()
GRADIENTS = {
    k: ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=v)
    for k, v in THEMES["dark"]["gradients"].items()
}

SHADOWS = {
    "card": ft.BoxShadow(spread_radius=0, blur_radius=8,
                         color=with_alpha("#000000", 0x40), offset=ft.Offset(0, 2)),
    "elevated": ft.BoxShadow(spread_radius=0, blur_radius=14,
                             color=with_alpha("#000000", 0x60), offset=ft.Offset(0, 5)),
}


# =========================================================================== #
# API ТЕМ                                                                      #
# =========================================================================== #
def set_theme(name: str):
    """Применить тему по имени. Мутирует глобальные COLORS/GRADIENTS/SHADOWS."""
    if name not in THEMES:
        name = "dark"
    src = THEMES[name]
    COLORS.clear()
    COLORS.update(src["colors"])
    GRADIENTS.clear()
    for k, v in src["gradients"].items():
        GRADIENTS[k] = ft.LinearGradient(
            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=v)
    # Тени: тёмные темы — чёрная тень, светлая — серая
    shadow_color = with_alpha("#000000", 0x40) if src["mode"] == "dark" else with_alpha("#000000", 0x18)
    shadow_color_elev = with_alpha("#000000", 0x60) if src["mode"] == "dark" else with_alpha("#000000", 0x28)
    SHADOWS["card"] = ft.BoxShadow(spread_radius=0, blur_radius=8,
                                   color=shadow_color, offset=ft.Offset(0, 2))
    SHADOWS["elevated"] = ft.BoxShadow(spread_radius=0, blur_radius=14,
                                       color=shadow_color_elev, offset=ft.Offset(0, 5))


def get_theme_names() -> list:
    """Все имена тем в порядке отображения."""
    return list(THEME_DISPLAY.keys())


def get_theme_display_name(name: str) -> str:
    return THEME_DISPLAY.get(name, name)


def is_premium_theme(name: str) -> bool:
    return name in PREMIUM_THEMES


def get_flet_theme_mode(name: str):
    """ThemeMode для Flet (dark/light) по имени темы."""
    mode = THEMES.get(name, THEMES["dark"]).get("mode", "dark")
    return ft.ThemeMode.DARK if mode == "dark" else ft.ThemeMode.LIGHT


def get_theme():
    return ft.Theme(color_scheme_seed=COLORS["primary"])