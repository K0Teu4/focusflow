# main.py
import flet as ft
from ui.theme import get_theme, set_theme, get_flet_theme_mode, COLORS
from ui.screens.timer_screen import TimerScreen
from ui.screens.tasks_screen import TasksScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.premium_screen import PremiumScreen
from ui.screens.stats_screen import StatsScreen
from db.database import SessionLocal, get_settings


def main(page: ft.Page):
    page.title = "FocusFlow"
    page.window.width = 400
    page.window.height = 700
    page.window.resizable = False

    # Применяем тему из настроек при запуске
    with SessionLocal() as db:
        settings = get_settings(db)
        initial_theme = settings.get("theme", "dark")

    set_theme(initial_theme)
    page.theme_mode = get_flet_theme_mode(initial_theme)
    page.theme = get_theme()
    page.bgcolor = COLORS["bg"]

    page.appbar = ft.AppBar(
        title=ft.Text("FocusFlow", color=COLORS["primary"]),
        bgcolor=COLORS["surface"],
        center_title=True,
    )

    timer_screen = TimerScreen(page)

    def on_focus_task(task_id: int, category: str):
        page.navigation_bar.selected_index = 0
        screen_container.controls.clear()
        screen_container.controls.append(timer_screen)
        timer_screen.focus_on_task(task_id, category)
        page.update()

    tasks_screen = TasksScreen(page, on_focus_task=on_focus_task)

    def on_settings_changed(settings: dict):
        timer_screen.timer_service.reload_settings()
        timer_screen.refresh_data()

    def on_open_premium():
        page.navigation_bar.selected_index = 4
        screen_container.controls.clear()
        premium_screen.refresh_data()
        screen_container.controls.append(premium_screen)
        page.update()

    def on_premium_changed(is_premium: bool):
        stats_screen.refresh_data()
        premium_screen.refresh_data()
        settings_screen.refresh_data()
        page.update()

    def on_theme_changed(theme_name: str):
        nonlocal timer_screen, tasks_screen, settings_screen, premium_screen, stats_screen

        set_theme(theme_name)
        page.theme_mode = get_flet_theme_mode(theme_name)
        page.theme = get_theme()
        page.bgcolor = COLORS["bg"]
        page.appbar.bgcolor = COLORS["surface"]
        page.appbar.title.color = COLORS["primary"]

        # Обновляем цвета NavigationBar
        page.navigation_bar.bgcolor = COLORS["surface"]
        page.navigation_bar.indicator_color = COLORS["primary"]
        for dest in page.navigation_bar.destinations:
            if hasattr(dest, 'icon') and isinstance(dest.icon, ft.Icon):
                dest.icon.color = COLORS["text_secondary"]
            if hasattr(dest, 'selected_icon') and isinstance(dest.selected_icon, ft.Icon):
                dest.selected_icon.color = COLORS["bg"]
        page.update()

        # Пересоздаём все экраны
        timer_screen = TimerScreen(page)
        tasks_screen = TasksScreen(page, on_focus_task=on_focus_task)
        settings_screen = SettingsScreen(
            page,
            on_settings_changed=on_settings_changed,
            on_open_premium=on_open_premium,
            on_theme_changed=on_theme_changed,
        )
        premium_screen = PremiumScreen(page, on_premium_changed=on_premium_changed)
        stats_screen = StatsScreen(page, on_open_premium=on_open_premium)

        screen_container.controls.clear()
        index = page.navigation_bar.selected_index
        screens = [timer_screen, tasks_screen, stats_screen, settings_screen, premium_screen]
        screen_container.controls.append(screens[index])
        page.update()

    settings_screen = SettingsScreen(
        page,
        on_settings_changed=on_settings_changed,
        on_open_premium=on_open_premium,
        on_theme_changed=on_theme_changed,
    )
    premium_screen = PremiumScreen(page, on_premium_changed=on_premium_changed)
    stats_screen = StatsScreen(page, on_open_premium=on_open_premium)

    screen_container = ft.Column([timer_screen], expand=True)

    def on_nav_change(e):
        screen_container.controls.clear()
        index = page.navigation_bar.selected_index
        if index == 0:
            timer_screen.refresh_data()
            screen_container.controls.append(timer_screen)
        elif index == 1:
            tasks_screen.refresh_data()
            screen_container.controls.append(tasks_screen)
        elif index == 2:
            stats_screen.refresh_data()
            screen_container.controls.append(stats_screen)
        elif index == 3:
            settings_screen.refresh_data()
            screen_container.controls.append(settings_screen)
        elif index == 4:
            premium_screen.refresh_data()
            screen_container.controls.append(premium_screen)
        page.update()

    # NavigationBar с явными цветами иконок
    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        bgcolor=COLORS["surface"],
        indicator_color=COLORS["primary"],
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.TIMER, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.TIMER, color=COLORS["bg"]),
                label="Таймер",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.CHECKLIST, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.CHECKLIST, color=COLORS["bg"]),
                label="Задачи",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.BAR_CHART, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.BAR_CHART, color=COLORS["bg"]),
                label="Статистика",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.SETTINGS, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.SETTINGS, color=COLORS["bg"]),
                label="Настройки",
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.STAR, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.STAR, color=COLORS["bg"]),
                label="Premium",
            ),
        ],
    )

    page.add(screen_container)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")