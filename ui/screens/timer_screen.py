# ui/screens/timer_screen.py
import flet as ft
import asyncio
from services.timer_service import TimerService
from db.database import SessionLocal, get_tasks, get_today_stats, get_settings, get_task_by_id
from ui.theme import COLORS, GRADIENTS, SHADOWS
from ui.toast import show_toast


class TimerScreen(ft.Column):
    """Главный экран с таймером Pomodoro.

    Отвечает за отображение кругового прогресса, времени, типа сессии,
    управления (старт/пауза/пропуск/сброс), выбора задачи и автостарта.
    """

    def __init__(self, page: ft.Page):
        super().__init__(
            spacing=0,
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._page = page
        self.timer_service = TimerService()
        # Привязка звукового сервиса к page (на mobile — заглушка, на desktop — winsound)
        self.timer_service._sound_service.bind_page(page)
        self.selected_task_id = None
        self._auto_start_task = None  # handle задачи обратного отсчёта автостарта

        # === КРУГОВОЙ ПРОГРЕСС-БАР ===
        # Контейнер с градиентным фоном и тенью; внутри — ProgressRing.
        # scale + animation нужны для пульсации при старте/завершении сессии.
        self.timer_bg = ft.Container(
            width=240,
            height=240,
            border_radius=120,
            gradient=GRADIENTS["work"],
            alignment=ft.Alignment(0, 0),
            shadow=SHADOWS["elevated"],
            scale=1.0,
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
            content=ft.ProgressRing(
                value=0.0,
                width=210,
                height=210,
                stroke_width=10,
                color=COLORS["work"],
                bgcolor=COLORS["surface"],
            ),
            margin=ft.Margin(0, 20, 0, 16),
        )
        self.progress_ring = self.timer_bg.content

        # === ТЕКСТОВЫЕ ЭЛЕМЕНТЫ ===
        # Тип сессии: "Работа" / "Короткий перерыв" / "Длинный перерыв"
        self.session_type_text = ft.Text(
            self.timer_service.get_session_type_display(),
            size=22,
            weight=ft.FontWeight.BOLD,
            color=COLORS["text"],
        )

        # Счётчик сессий до длинного перерыва: "Сессия 0 из 4"
        self.progress_text = ft.Text(
            self._get_progress_display(),
            size=16,
            color=COLORS["text_secondary"],
            margin=ft.Margin(0, 0, 0, 8),
        )

        # Основное табло времени MM:SS
        self.time_display = ft.Text(
            self.timer_service.get_display_time(),
            size=56,
            weight=ft.FontWeight.BOLD,
            color=COLORS["work"],
            font_family="monospace",
            margin=ft.Margin(0, 0, 0, 8),
        )

        # Название текущей задачи или "Без задачи"
        self.current_task_text = ft.Text(
            "Без задачи",
            size=16,
            color=COLORS["text_secondary"],
            italic=True,
            margin=ft.Margin(0, 0, 0, 4),
        )

        # Кнопка вызова диалога выбора задачи
        self.select_task_button = ft.TextButton(
            "📋 Выбрать задачу",
            style=ft.ButtonStyle(color=COLORS["primary"]),
            on_click=self._show_task_picker_dialog,
            margin=ft.Margin(0, 0, 0, 20),
        )

        # === КНОПКИ УПРАВЛЕНИЯ ===
        self.start_button = ft.ElevatedButton(
            "Старт",
            bgcolor=COLORS["primary"],
            color=COLORS["bg"],
            on_click=self.on_start,
            width=140,
            height=48,
        )

        self.pause_button = ft.ElevatedButton(
            "Пауза",
            bgcolor=COLORS["pause_work"],
            color=COLORS["bg"],
            on_click=self.on_pause,
            width=140,
            height=48,
            visible=False,
        )

        # Пропуск виден во время любой запущенной сессии (работа и отдых)
        self.skip_button = ft.ElevatedButton(
            "Пропустить",
            bgcolor=COLORS["skip"],
            color=COLORS["bg"],
            on_click=self.on_skip,
            width=140,
            height=44,
            visible=False,
            margin=ft.Margin(0, 8, 0, 0),
        )

        self.reset_button = ft.OutlinedButton(
            "Сброс",
            style=ft.ButtonStyle(
                side=ft.BorderSide(1.5, COLORS["reset_border"]),
                color=COLORS["reset_border"],
            ),
            on_click=self.on_reset,
            width=110,
            height=38,
            margin=ft.Margin(0, 12, 0, 0),
        )

        # === АВТОСТАРТ СЛЕДУЮЩЕЙ СЕССИИ ===
        self.auto_start_bar = ft.ProgressBar(
            value=0.0,
            color=COLORS["primary"],
            bgcolor=COLORS["surface"],
            width=200,
            visible=False,
        )
        self.auto_start_text = ft.Text(
            "",
            size=16,
            color=COLORS["primary"],
            weight=ft.FontWeight.W_600,
            visible=False,
            margin=ft.Margin(0, 8, 0, 0),
        )
        self.cancel_auto_btn = ft.TextButton(
            "Отмена",
            style=ft.ButtonStyle(color=COLORS["text_secondary"]),
            on_click=self.on_cancel_auto_start,
            visible=False,
        )

        # Скрытый Dropdown — хранит id выбранной задачи, управляется программно
        self.task_dropdown = ft.Dropdown(
            label="Задача",
            hint_text="Выбрать задачу",
            width=280,
            border_color=COLORS["primary"],
            color=COLORS["text"],
            bgcolor=COLORS["surface"],
            visible=False,
        )
        self.task_dropdown.on_change = self.on_task_change

        # Статистика за сегодня внизу экрана
        self.stats_text = ft.Text(
            "",
            size=13,
            color=COLORS["text_secondary"],
            margin=ft.Margin(0, 16, 0, 20),
        )

        # === СБОРКА ЭКРАНА ===
        self.controls = [
            self.timer_bg,
            self.session_type_text,
            self.progress_text,
            self.time_display,
            self.current_task_text,
            self.select_task_button,
            self.task_dropdown,
            ft.Row(
                [self.start_button, self.pause_button],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            self.skip_button,
            self.auto_start_text,
            self.auto_start_bar,
            self.cancel_auto_btn,
            self.reset_button,
            self.stats_text,
        ]

        self.load_tasks()
        self.update_stats()

    # ------------------------------------------------------------------ #
    # ПУЛЬСАЦИЯ КРУГА                                                     #
    # ------------------------------------------------------------------ #
    def _pulse(self):
        """Короткая пульсация круга при старте и завершении сессии."""
        self.timer_bg.scale = 1.06
        self._page.update()

        async def back():
            await asyncio.sleep(0.18)
            self.timer_bg.scale = 1.0
            self._page.update()

        asyncio.create_task(back())

    # ------------------------------------------------------------------ #
    # ВСПОМОГАТЕЛЬНЫЕ ОТОБРАЖЕНИЯ                                         #
    # ------------------------------------------------------------------ #
    def _get_progress_display(self) -> str:
        """Возвращает строку счётчика вида 'Сессия 0 из 4'."""
        done = self.timer_service.completed_work_sessions
        total = self.timer_service.sessions_until_long_break
        return f"Сессия {done} из {total}"

    def _cancel_auto_start_countdown(self):
        """Останавливает обратный отсчёт автостарта и прячет его UI."""
        if self._auto_start_task and not self._auto_start_task.done():
            self._auto_start_task.cancel()
        self.auto_start_text.visible = False
        self.auto_start_bar.visible = False
        self.cancel_auto_btn.visible = False

    # ------------------------------------------------------------------ #
    # ОБНОВЛЕНИЕ ДАННЫХ                                                   #
    # ------------------------------------------------------------------ #
    def refresh_data(self):
        """Перечитывает настройки/задачи/статистику и перерисовывает экран."""
        self.timer_service.reload_settings()
        self.load_tasks()
        self.update_stats()
        self._apply_mode_colors()
        self._update_progress()
        self.time_display.value = self.timer_service.get_display_time()
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self.progress_text.value = self._get_progress_display()
        self._update_current_task_text()
        self._page.update()

    def load_tasks(self):
        """Загружает активные задачи в скрытый Dropdown."""
        with SessionLocal() as db:
            tasks = get_tasks(db)
            self.task_dropdown.options = [
                ft.dropdown.Option(key=str(t.id), text=t.title, data=t.category)
                for t in tasks
            ]
        self._page.update()

    def update_stats(self):
        """Обновляет строку статистики за сегодня."""
        with SessionLocal() as db:
            stats = get_today_stats(db)
            self.stats_text.value = (
                f"Сегодня: {stats['work_sessions']} 🍅 • {stats['total_work_minutes']} мин"
            )

    def _update_current_task_text(self):
        """Синхронизирует текст текущей задачи с выбранным значением Dropdown."""
        selected = self.task_dropdown.value
        if selected:
            for opt in self.task_dropdown.options:
                if opt.key == selected:
                    self.current_task_text.value = f"▶ {opt.text}"
                    self.current_task_text.color = COLORS["primary"]
                    self.current_task_text.italic = False
                    return
        self.current_task_text.value = "Без задачи"
        self.current_task_text.color = COLORS["text_secondary"]
        self.current_task_text.italic = True

    # ------------------------------------------------------------------ #
    # ДИАЛОГ ВЫБОРА ЗАДАЧИ                                                #
    # ------------------------------------------------------------------ #
    def _show_task_picker_dialog(self, e):
        """Показывает диалог со списком задач для привязки к таймеру."""
        with SessionLocal() as db:
            tasks = get_tasks(db)

        if not tasks:
            dialog = ft.AlertDialog(
                title=ft.Text("Нет задач"),
                content=ft.Text("Создайте задачу на вкладке 'Задачи'"),
                actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog(dialog))],
            )
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()
            return

        def make_task_button(task):
            cat_colors = {
                "work": COLORS["cat_work"],
                "rest": COLORS["cat_rest"],
                "hobby": COLORS["cat_hobby"],
                "study": COLORS["cat_study"],
            }
            cat_color = cat_colors.get(task.category, COLORS["cat_work"])

            def on_select(e):
                self.task_dropdown.value = str(task.id)
                self._update_session_label_from_dropdown()
                self._update_current_task_text()
                self._close_dialog(dialog)

            return ft.Container(
                content=ft.Row([
                    ft.Container(width=8, height=8, border_radius=4, bgcolor=cat_color),
                    ft.Text(task.title, size=16, color=COLORS["text"], expand=True),
                ], spacing=10),
                padding=14,
                bgcolor=COLORS["surface"],
                border_radius=10,
                margin=ft.Margin(0, 0, 0, 6),
                on_click=on_select,
                ink=True,
            )

        task_buttons = [make_task_button(t) for t in tasks]

        def on_clear(e):
            self.task_dropdown.value = None
            self._update_current_task_text()
            self.timer_service.set_session_mode(True)
            self.session_type_text.value = self.timer_service.get_session_type_display()
            self._apply_mode_colors()
            self._close_dialog(dialog)

        dialog = ft.AlertDialog(
            title=ft.Text("Выберите задачу"),
            content=ft.Column(
                task_buttons + [
                    ft.Container(height=8),
                    ft.TextButton(
                        "✕ Убрать задачу",
                        style=ft.ButtonStyle(color=COLORS["text_secondary"]),
                        on_click=on_clear,
                    ),
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
                height=min(len(tasks) * 60 + 60, 300),
            ),
            actions=[
                ft.TextButton("Закрыть", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()

    # ------------------------------------------------------------------ #
    # ЦВЕТА РЕЖИМА                                                        #
    # ------------------------------------------------------------------ #
    def _apply_mode_colors(self):
        """Обновляет цвета кольца, градиент фона и табло под текущий режим."""
        mode = self.timer_service.get_mode_key()

        if mode == "work":
            ring_color = COLORS["work"]
            gradient = GRADIENTS["work"]
            pause_color = COLORS["pause_work"]
        elif mode == "long_break":
            ring_color = COLORS["long_break"]
            gradient = GRADIENTS["long_break"]
            pause_color = COLORS["pause_rest"]
        else:
            ring_color = COLORS["rest"]
            gradient = GRADIENTS["rest"]
            pause_color = COLORS["pause_rest"]

        self.progress_ring.color = ring_color
        self.timer_bg.gradient = gradient
        self.time_display.color = ring_color
        self.pause_button.bgcolor = pause_color

        # Во время отдыха прячем выбор задачи и показываем следующую/отдых
        is_rest = not self.timer_service.is_work_session
        self.select_task_button.visible = not is_rest
        if is_rest:
            selected = self.task_dropdown.value
            if selected:
                for opt in self.task_dropdown.options:
                    if opt.key == selected:
                        self.current_task_text.value = f"Следующая: {opt.text}"
                        self.current_task_text.color = COLORS["text_secondary"]
                        self.current_task_text.italic = True
                        break
            else:
                self.current_task_text.value = "Отдых"
                self.current_task_text.color = COLORS["text_secondary"]
                self.current_task_text.italic = True
        else:
            self._update_current_task_text()

    # ------------------------------------------------------------------ #
    # ПРОГРЕСС И КНОПКИ                                                   #
    # ------------------------------------------------------------------ #
    def _update_progress(self):
        """Пересчитывает заполнение кольца по оставшемуся времени."""
        total = self.timer_service._get_current_target_sec()
        if total > 0:
            self.progress_ring.value = (total - self.timer_service.current_sec) / total
        else:
            self.progress_ring.value = 0.0

    def _update_buttons(self):
        """Пропуск виден, пока идёт любая сессия."""
        self.skip_button.visible = self.timer_service.is_running

    def _show_snackbar(self, message: str, color: str = COLORS["primary"]):
        """Показывает плавающий тост (единый виджет из ui.toast)."""
        if color == COLORS["success"]:
            icon = ft.Icons.CHECK_CIRCLE
        elif color == COLORS["skip"]:
            icon = ft.Icons.HOURGLASS_TOP
        else:
            icon = ft.Icons.INFO_OUTLINE
        show_toast(self._page, message, icon, color)

    # ------------------------------------------------------------------ #
    # ЦИКЛ ТАЙМЕРА                                                        #
    # ------------------------------------------------------------------ #
    def update_timer_display(self):
        """Колбэк таймера: вызывается каждую секунду и при смене сессии."""
        self.time_display.value = self.timer_service.get_display_time()
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self.progress_text.value = self._get_progress_display()
        self._apply_mode_colors()
        self._update_progress()
        self._update_buttons()

        with SessionLocal() as db:
            stats = get_today_stats(db)
            self.stats_text.value = (
                f"Сегодня: {stats['work_sessions']} 🍅 • {stats['total_work_minutes']} мин"
            )

        if self.timer_service.just_finished:
            self.timer_service.just_finished = False
            self._pulse()  # пульс при завершении сессии
            session_name = self.timer_service.get_session_type_display()
            self._show_snackbar(f"✅ {session_name} завершена!", COLORS["success"])
            self._check_auto_start()

        self._page.update()

    def _check_auto_start(self):
        """Если включён автостарт — запускает обратный отсчёт, иначе показывает Старт."""
        with SessionLocal() as db:
            settings = get_settings(db)
            if settings.get("auto_start", False):
                delay = int(settings.get("auto_start_delay", 3))
                self._start_countdown(delay)
            else:
                self.start_button.visible = True
                self.pause_button.visible = False

    def _start_countdown(self, delay: int):
        """Запускает визуальный обратный отсчёт перед автостартом."""
        self._cancel_auto_start_countdown()
        self.start_button.visible = False

        self.auto_start_text.value = f"Старт через {delay}..."
        self.auto_start_text.visible = True
        self.auto_start_bar.value = 0.0
        self.auto_start_bar.visible = True
        self.cancel_auto_btn.visible = True
        self._page.update()

        async def countdown():
            try:
                for i in range(delay, 0, -1):
                    self.auto_start_text.value = f"Старт через {i}..."
                    self.auto_start_bar.value = (delay - i) / delay
                    self._page.update()
                    await asyncio.sleep(1)

                self.auto_start_bar.value = 1.0
                self._page.update()
                await asyncio.sleep(0.3)

                self.auto_start_text.visible = False
                self.auto_start_bar.visible = False
                self.cancel_auto_btn.visible = False
                self._page.update()
                self.on_start(None)
            except asyncio.CancelledError:
                pass

        self._auto_start_task = asyncio.create_task(countdown())

    def on_cancel_auto_start(self, e):
        """Отмена обратного отсчёта автостарта пользователем."""
        self._cancel_auto_start_countdown()
        self.start_button.visible = True
        self.pause_button.visible = False
        self._page.update()

    # ------------------------------------------------------------------ #
    # ВЫБОР ЗАДАЧИ И РЕЖИМА                                               #
    # ------------------------------------------------------------------ #
    def on_task_change(self, e):
        """Реакция на смену задачи в Dropdown."""
        self._update_session_label_from_dropdown()
        self._update_current_task_text()
        self._page.update()

    def _update_session_label_from_dropdown(self):
        """Ставит режим работа/отдых по категории выбранной задачи."""
        selected_key = self.task_dropdown.value
        if selected_key:
            for opt in self.task_dropdown.options:
                if opt.key == selected_key:
                    category = opt.data or "work"
                    is_work = category in ["work", "study"]
                    self.timer_service.set_session_mode(is_work)
                    self.session_type_text.value = self.timer_service.get_session_type_display()
                    self._apply_mode_colors()
                    return
        self.timer_service.set_session_mode(True)
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self._apply_mode_colors()

    # ------------------------------------------------------------------ #
    # ФОКУС НА ЗАДАЧЕ ИЗ СПИСКА                                           #
    # ------------------------------------------------------------------ #
    def focus_on_task(self, task_id: int, category: str):
        """Запуск таймера по задаче из списка задач (с подтверждением, если идёт)."""
        if self.timer_service.is_running:
            def on_confirm(e):
                dialog.open = False
                self._page.update()
                asyncio.create_task(self.timer_service.pause())
                self._do_focus_on_task(task_id, category)

            def on_cancel(e):
                dialog.open = False
                self._page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("Таймер уже запущен"),
                content=ft.Text("Остановить и начать новую задачу?"),
                actions=[
                    ft.TextButton("Отмена", on_click=on_cancel),
                    ft.TextButton("Начать", on_click=on_confirm),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self._page.overlay.append(dialog)
            dialog.open = True
            self._page.update()
        else:
            self._do_focus_on_task(task_id, category)

    def _do_focus_on_task(self, task_id: int, category: str):
        """Фактическая привязка задачи и старт таймера."""
        self._cancel_auto_start_countdown()
        self.load_tasks()
        self.task_dropdown.value = str(task_id)
        is_work = category in ["work", "study"]
        self.timer_service.set_session_mode(is_work)
        self.session_type_text.value = self.timer_service.get_session_type_display()
        self._apply_mode_colors()
        self._update_current_task_text()
        self._update_progress()
        self.on_start(None)
        self._page.update()

    # ------------------------------------------------------------------ #
    # УПРАВЛЕНИЕ: СТАРТ / ПАУЗА / ПРОПУСК / СБРОС                         #
    # ------------------------------------------------------------------ #
    def on_start(self, e):
        """Запуск таймера с пульсацией круга."""
        self._cancel_auto_start_countdown()
        task_id = int(self.task_dropdown.value) if self.task_dropdown.value else None
        self.start_button.visible = False
        self.pause_button.visible = True
        self._apply_mode_colors()
        self._update_buttons()
        self._pulse()  # пульс при старте
        self._page.update()
        asyncio.create_task(
            self.timer_service.start(self.update_timer_display, task_id, sound_enabled=True)
        )

    def on_pause(self, e):
        """Пауза таймера."""
        self._cancel_auto_start_countdown()
        asyncio.create_task(self.timer_service.pause())
        self.start_button.visible = True
        self.pause_button.visible = False
        self.skip_button.visible = False
        self._page.update()

    def on_skip(self, e):
        """Пропуск сессии с сохранением частичного прогресса."""
        self._cancel_auto_start_countdown()

        async def do_skip():
            await self.timer_service.pause()
            elapsed = self.timer_service.skip_and_save()
            self.update_timer_display()
            self.start_button.visible = True
            self.pause_button.visible = False
            self.skip_button.visible = False

            if elapsed > 0:
                duration_str = TimerService.format_duration(elapsed)
                self._show_snackbar(f"✅ Сохранено: {duration_str}", COLORS["success"])
            else:
                self._show_snackbar("⏭ Сессия пропущена", COLORS["skip"])

            self._page.update()

        asyncio.create_task(do_skip())

    def on_reset(self, e):
        """Полный сброс таймера в начальное состояние."""
        self._cancel_auto_start_countdown()
        asyncio.create_task(self.timer_service.reset())
        self.start_button.visible = True
        self.pause_button.visible = False
        self.skip_button.visible = False
        self.progress_ring.value = 0.0
        self.update_timer_display()
        self.update_stats()

    # ------------------------------------------------------------------ #
    # УТИЛИТЫ                                                             #
    # ------------------------------------------------------------------ #
    def _close_dialog(self, dialog):
        """Закрывает переданный AlertDialog."""
        dialog.open = False
        self._page.update()