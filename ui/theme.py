# ui/theme.py
import flet as ft

# --------------------------------------------------------------------------- #
# ПАЛИТРА                                                                     #
# Акцент интерфейса (primary) = cyan в ОБЕИХ темах — тёмная является именно   #
# тёмной версией светлой, а не отдельной «розовой» темой.                     #
# Magenta/розовый = бренд-цвет ФОКУСА (кольцо работы, категория «Работа»).    #
# --------------------------------------------------------------------------- #

_PRIMARY = "#00AEEF"
_WORK    = "#FF5C8A"
_REST    = "#5A9FE6"
_LONG    = "#A78BFA"
_HOBBY   = "#34C77B"
_STUDY   = "#E6962E"
_SUCCESS = "#34C759"
_ERROR   = "#FF453A"

DARK_COLORS = {
    "bg": "#141A2E", "surface": "#1E2640", "surface_2": "#262F4D",
    "primary": _PRIMARY, "text": "#F2F4F8", "text_secondary": "#8B94A8",
    "pause_work": "#FF8A5C", "pause_rest": _REST, "reset_border": "#5A6478",
    "skip": "#7C8CFF", "work": _WORK, "rest": _REST, "long_break": _LONG,
    "success": _SUCCESS, "error": _ERROR,
    "cat_work": _WORK, "cat_rest": _REST, "cat_hobby": _HOBBY, "cat_study": _STUDY,
}

LIGHT_COLORS = {
    "bg": "#F2F4F8", "surface": "#FFFFFF", "surface_2": "#E9ECF3",
    "primary": _PRIMARY, "text": "#141A2E", "text_secondary": "#6B7385",
    "pause_work": "#FF7A45", "pause_rest": _REST, "reset_border": "#C2C8D4",
    "skip": _REST, "work": _WORK, "rest": _REST, "long_break": _LONG,
    "success": _SUCCESS, "error": _ERROR,
    "cat_work": _WORK, "cat_rest": _REST, "cat_hobby": _HOBBY, "cat_study": _STUDY,
}

DARK_GRADIENTS = {
    "work": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#33142A", "#141A2E"]),
    "rest": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#15243F", "#141A2E"]),
    "long_break": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#221A44", "#141A2E"]),
}
LIGHT_GRADIENTS = {
    "work": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#FFE3EC", "#F2F4F8"]),
    "rest": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#E1ECFB", "#F2F4F8"]),
    "long_break": ft.LinearGradient(begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1), colors=["#ECE6FB", "#F2F4F8"]),
}


# --------------------------------------------------------------------------- #
# ПРОЗРАЧНОСТЬ — ЕДИНСТВЕННО ВЕРНЫЙ СПОСОБ В FLET                             #
# Flet читает 8-hex как #AARRGGBB (Android), поэтому байт alpha ставим ВПЕРЁД.#
# Конкатенация color + "14" НЕРАБОТАЕТ (даёт левые цвета).                    #
# --------------------------------------------------------------------------- #
def with_alpha(hex_color, alpha):
    """hex_color '#RRGGBB' + alpha (int 0..255 или float 0..1) -> '#AARRGGBB'."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    a = alpha if isinstance(alpha, int) else int(round(alpha * 255))
    a = max(0, min(255, a))
    return f"#{a:02X}{h.upper()}"


SHADOWS = {
    "card": ft.BoxShadow(spread_radius=0, blur_radius=8,
                         color=with_alpha("#000000", 0x40), offset=ft.Offset(0, 2)),
    "elevated": ft.BoxShadow(spread_radius=0, blur_radius=14,
                             color=with_alpha("#000000", 0x60), offset=ft.Offset(0, 5)),
}

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