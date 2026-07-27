# main.py
import flet as ft
from ui.theme import get_theme, set_theme, get_flet_theme_mode, COLORS
from ui.screens.timer_screen import TimerScreen
from ui.screens.tasks_screen import TasksScreen
from ui.screens.settings_screen import SettingsScreen
from ui.screens.premium_screen import PremiumScreen
from ui.screens.stats_screen import StatsScreen
from ui.screens.onboarding_screen import OnboardingScreen
from ui.screens.focus_screen import FocusScreen
from db.database import SessionLocal, get_settings, update_settings


def main(page: ft.Page):
    page.title = "FocusFlow"
    page.window.width = 440
    page.window.height = 820
    page.window.min_width = 380
    page.window.max_width = 520
    page.window.min_height = 640
    page.window.max_height = 940
    page.window.resizable = True

    with SessionLocal() as db:
        settings = get_settings(db)
        initial_theme = settings.get("theme", "dark")
        first_launch = not settings.get("onboarding_completed", False)

    set_theme(initial_theme)
    page.theme_mode = get_flet_theme_mode(initial_theme)
    page.theme = get_theme()
    page.bgcolor = COLORS["bg"]

    # === ТАЙМЕР (создаётся первым — нужен timer_service для focus_screen) ===
    timer_screen = TimerScreen(page)

    # === CALLBACK'И (определяются до создания экранов, которые их используют) ===
    def on_focus_task(task_id: int, category: str):
        page.navigation_bar.selected_index = 0
        screen_container.controls.clear()
        screen_container.controls.append(timer_screen)
        timer_screen.focus_on_task(task_id, category)
        page.update()

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
        nonlocal timer_screen, tasks_screen, settings_screen, premium_screen, stats_screen, focus_screen
        set_theme(theme_name)
        page.theme_mode = get_flet_theme_mode(theme_name)
        page.theme = get_theme()
        page.bgcolor = COLORS["bg"]
        page.navigation_bar.bgcolor = COLORS["surface"]
        page.navigation_bar.indicator_color = COLORS["primary"]
        for dest in page.navigation_bar.destinations:
            if hasattr(dest, 'icon') and isinstance(dest.icon, ft.Icon):
                dest.icon.color = COLORS["text_secondary"]
            if hasattr(dest, 'selected_icon') and isinstance(dest.selected_icon, ft.Icon):
                dest.selected_icon.color = COLORS["bg"]
        page.update()

        timer_screen = TimerScreen(page, on_enter_focus=on_enter_focus, on_open_premium=on_open_premium)
        tasks_screen = TasksScreen(page, on_focus_task=on_focus_task)
        settings_screen = SettingsScreen(page, on_settings_changed=on_settings_changed,
                                         on_open_premium=on_open_premium, on_theme_changed=on_theme_changed)
        premium_screen = PremiumScreen(page, on_premium_changed=on_premium_changed)
        stats_screen = StatsScreen(page, on_open_premium=on_open_premium)
        focus_screen = FocusScreen(page, timer_screen.timer_service, on_exit_focus, timer_screen)

        screen_container.controls.clear()
        index = page.navigation_bar.selected_index
        screens = [timer_screen, tasks_screen, stats_screen, settings_screen, premium_screen]
        screen_container.controls.append(screens[index])
        page.update()

    # === ЭКРАНЫ (создаются после определения callback'ов) ===
    tasks_screen = TasksScreen(page, on_focus_task=on_focus_task)
    settings_screen = SettingsScreen(page, on_settings_changed=on_settings_changed,
                                     on_open_premium=on_open_premium, on_theme_changed=on_theme_changed)
    premium_screen = PremiumScreen(page, on_premium_changed=on_premium_changed)
    stats_screen = StatsScreen(page, on_open_premium=on_open_premium)

    # === РЕЖИМ ФОКУС (callback'и используют focus_screen через late binding) ===
    def on_enter_focus():
        task_title = None
        if timer_screen.task_dropdown.value:
            for opt in timer_screen.task_dropdown.options:
                if opt.key == timer_screen.task_dropdown.value:
                    task_title = opt.text
                    break
        focus_screen.set_task(task_title)
        page.navigation_bar.visible = False
        screen_container.controls.clear()
        focus_screen.start_ticking()
        screen_container.controls.append(focus_screen)
        page.update()

    def on_exit_focus():
        focus_screen.stop_ticking()
        page.navigation_bar.visible = True
        screen_container.controls.clear()
        timer_screen.refresh_data()
        screen_container.controls.append(timer_screen)
        page.update()

    focus_screen = FocusScreen(page, timer_screen.timer_service, on_exit_focus, timer_screen)

    # Привязать callback'и к timer_screen
    timer_screen.on_enter_focus = on_enter_focus
    timer_screen.on_open_premium = on_open_premium

    # === НАВИГАЦИЯ ===
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

    page.navigation_bar = ft.NavigationBar(
        selected_index=0, on_change=on_nav_change,
        bgcolor=COLORS["surface"], indicator_color=COLORS["primary"],
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.TIMER, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.TIMER, color=COLORS["bg"]), label="Таймер"),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.CHECKLIST, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.CHECKLIST, color=COLORS["bg"]), label="Задачи"),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.BAR_CHART, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.BAR_CHART, color=COLORS["bg"]), label="Статистика"),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.SETTINGS, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.SETTINGS, color=COLORS["bg"]), label="Настройки"),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.STAR, color=COLORS["text_secondary"]),
                selected_icon=ft.Icon(ft.Icons.STAR, color=COLORS["bg"]), label="Premium"),
        ])

    # === ОНБОРДИНГ / СТАРТ ===
    def on_onboarding_complete():
        with SessionLocal() as db:
            s = get_settings(db)
            s["onboarding_completed"] = True
            update_settings(db, s)
        page.navigation_bar.visible = True
        screen_container.controls.clear()
        screen_container.controls.append(timer_screen)
        page.update()

    if first_launch:
        onboarding_screen = OnboardingScreen(page, on_onboarding_complete)
        screen_container = ft.Column([onboarding_screen], expand=True)
        page.navigation_bar.visible = False
    else:
        screen_container = ft.Column([timer_screen], expand=True)

    page.add(screen_container)


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")