# ui/theme.py
import flet as ft

# --------------------------------------------------------------------------- #
# ПАЛИТРА                                                                     #
# Акцент интерфейса (primary) = cyan в ОБЕИХ темах — тёмная является именно   #
# тёмной версией светлой, а не отдельной «розовой» темой.                     #
# Magenta/розовый = бренд-цвет ФОКУСА (кольцо работы, категория «Работа»).    #
# Между темами отличаются только фон/поверхность/текст и градиенты.           #
# --------------------------------------------------------------------------- #

# Общие «смысловые» цвета (одинаковы в обеих темах)
_PRIMARY   = "#00AEEF"   # акцент интерфейса (cyan)
_WORK      = "#FF5C8A"   # фокус / работа (magenta, бренд)
_REST      = "#5A9FE6"   # короткий перерыв
_LONG      = "#A78BFA"   # длинный перерыв
_HOBBY     = "#34C77B"   # хобби (насыщенный изумруд)
_STUDY     = "#E6962E"   # учёба (насыщенный янтарь)
_SUCCESS   = "#34C759"
_ERROR     = "#FF453A"

DARK_COLORS = {
    "bg": "#141A2E",
    "surface": "#1E2640",
    "surface_2": "#262F4D",
    "primary": _PRIMARY,
    "text": "#F2F4F8",
    "text_secondary": "#8B94A8",
    "pause_work": "#FF8A5C",
    "pause_rest": _REST,
    "reset_border": "#5A6478",   # нейтральный сброс в покое
    "skip": "#7C8CFF",
    "work": _WORK,
    "rest": _REST,
    "long_break": _LONG,
    "success": _SUCCESS,
    "error": _ERROR,
    "cat_work": _WORK,
    "cat_rest": _REST,
    "cat_hobby": _HOBBY,
    "cat_study": _STUDY,
}

LIGHT_COLORS = {
    "bg": "#F2F4F8",
    "surface": "#FFFFFF",
    "surface_2": "#E9ECF3",
    "primary": _PRIMARY,
    "text": "#141A2E",
    "text_secondary": "#6B7385",
    "pause_work": "#FF7A45",
    "pause_rest": _REST,
    "reset_border": "#C2C8D4",   # нейтральный сброс в покое
    "skip": _REST,
    "work": _WORK,
    "rest": _REST,
    "long_break": _LONG,
    "success": _SUCCESS,
    "error": _ERROR,
    "cat_work": _WORK,
    "cat_rest": _REST,
    "cat_hobby": _HOBBY,
    "cat_study": _STUDY,
}

DARK_GRADIENTS = {
    "work": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                              colors=["#33142A", "#141A2E"]),
    "rest": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                              colors=["#15243F", "#141A2E"]),
    "long_break": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                                    colors=["#221A44", "#141A2E"]),
}

LIGHT_GRADIENTS = {
    "work": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                              colors=["#FFE3EC", "#F2F4F8"]),
    "rest": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                              colors=["#E1ECFB", "#F2F4F8"]),
    "long_break": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                                    colors=["#ECE6FB", "#F2F4F8"]),
}

SHADOWS = {
    "card": ft.BoxShadow(spread_radius=0, blur_radius=8,
                         color="#00000040", offset=ft.Offset(0, 2)),
    "elevated": ft.BoxShadow(spread_radius=0, blur_radius=14,
                             color="#00000060", offset=ft.Offset(0, 5)),
}

# Мутируемые словари «текущей темы» (все импорты COLORS/GRADIENTS смотрят сюда)
COLORS = DARK_COLORS.copy()
GRADIENTS = DARK_GRADIENTS.copy()


def set_theme(theme_name: str):
    src_c = DARK_COLORS if theme_name == "dark" else LIGHT_COLORS
    COLORS.clear(); COLORS.update(src_c)
    src_g = DARK_GRADIENTS if theme_name == "dark" else LIGHT_GRADIENTS
    GRADIENTS.clear(); GRADIENTS.update(src_g)


def get_flet_theme_mode(theme_name: str):
    return ft.ThemeMode.DARK if theme_name == "dark" else ft.ThemeMode.LIGHT


def get_theme():
    return ft.Theme(color_scheme_seed=COLORS["primary"])


# --------------------------------------------------------------------------- #
# КОНТРАСТ ТЕКСТА НА ЦВЕТНОМ ФОНЕ                                             #
# Для насыщенных фонов (выбранная пилюля, бейдж категории) возвращает белый    #
# или тёмный текст по относительной яркости — чтобы «Учёба»/«Хобби» читались.  #
# --------------------------------------------------------------------------- #
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