# main.py
import flet as ft
from ui.theme import get_theme, COLORS
from ui.screens.timer_screen import TimerScreen
from ui.screens.tasks_screen import TasksScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.premium_screen import PremiumScreen
from ui.screens.stats_screen import StatsScreen


def main(page: ft.Page):
    page.title = "FocusFlow"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = get_theme()
    page.bgcolor = COLORS["bg"]
    page.window.width = 400
    page.window.height = 700
    page.window.resizable = False

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
        premium_screen.refresh_data()  # НОВОЕ: обновляем перед показом
        screen_container.controls.append(premium_screen)
        page.update()

    def on_premium_changed(is_premium: bool):
        # НОВОЕ: обновляем оба экрана после покупки
        stats_screen.refresh_data()
        premium_screen.refresh_data()
        settings_screen.refresh_data()
        page.update()

    settings_screen = SettingsScreen(
        page,
        on_settings_changed=on_settings_changed,
        on_open_premium=on_open_premium,
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
            stats_screen.refresh_data()  # НОВОЕ: обновляем статистику
            screen_container.controls.append(stats_screen)
        elif index == 3:
            settings_screen.refresh_data()  # НОВОЕ
            screen_container.controls.append(settings_screen)
        elif index == 4:
            premium_screen.refresh_data()  # НОВОЕ
            screen_container.controls.append(premium_screen)
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        bgcolor=COLORS["surface"],
        indicator_color=COLORS["primary"],
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.TIMER, label="Таймер"),
            ft.NavigationBarDestination(icon=ft.Icons.CHECKLIST, label="Задачи"),
            ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART, label="Статистика"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Настройки"),
            ft.NavigationBarDestination(icon=ft.Icons.STAR, label="Premium"),
        ],
    )

    page.add(screen_container)


if __name__ == "__main__":
    ft.run(main)