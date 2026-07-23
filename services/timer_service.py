# services/timer_service.py
import asyncio
from typing import Callable, Optional
from datetime import datetime
from db.database import SessionLocal, create_session, get_settings
from services.sound_service import SoundService


class TimerService:
    def __init__(self, work_min=25, break_min=5):
        try:
            with SessionLocal() as db:
                settings = get_settings(db)
                self.work_sec = self._calc_seconds(settings, "work", work_min)
                self.break_sec = self._calc_seconds(settings, "break", break_min)
                self.long_break_sec = self._calc_seconds(settings, "long_break", 15)
                self.sessions_until_long_break = int(settings.get("sessions_until_long_break", 4))
                self.auto_start_delay = int(settings.get("auto_start_delay", 3))
        except:
            self.work_sec = int(work_min * 60)
            self.break_sec = int(break_min * 60)
            self.long_break_sec = 15 * 60
            self.sessions_until_long_break = 4
            self.auto_start_delay = 3

        self.current_sec = self.work_sec
        self.is_running = False
        self.is_work_session = True
        self.is_long_break = False
        self.completed_work_sessions = 0
        self.task_id: Optional[int] = None
        self.session_started_at: Optional[datetime] = None
        self._callback: Optional[Callable] = None
        self._sound_enabled = True
        self._sound_type = "bell"
        self._sound_service = SoundService()
        self._task: Optional[asyncio.Task] = None
        self.just_finished = False

    @staticmethod
    def _calc_seconds(settings: dict, key: str, default_min: int) -> int:
        if f"{key}_min" in settings or f"{key}_sec" in settings:
            mins = int(settings.get(f"{key}_min", 0) or 0)
            secs = int(settings.get(f"{key}_sec", 0) or 0)
            total = mins * 60 + secs
            if total > 0:
                return total
        legacy_min = settings.get(f"{key}_min")
        if legacy_min is not None:
            return int(legacy_min) * 60
        return int(default_min * 60)

    def reload_settings(self):
        try:
            with SessionLocal() as db:
                settings = get_settings(db)
                self.work_sec = self._calc_seconds(settings, "work", 25)
                self.break_sec = self._calc_seconds(settings, "break", 5)
                self.long_break_sec = self._calc_seconds(settings, "long_break", 15)
                self.sessions_until_long_break = int(settings.get("sessions_until_long_break", 4))
                self.auto_start_delay = int(settings.get("auto_start_delay", 3))
                if not self.is_running:
                    self.current_sec = self._get_current_target_sec()
        except:
            pass

    def _get_current_target_sec(self):
        if self.is_work_session:
            return self.work_sec
        elif self.is_long_break:
            return self.long_break_sec
        else:
            return self.break_sec

    def get_elapsed_sec(self) -> int:
        """НОВОЕ: сколько секунд прошло с начала текущей сессии"""
        return max(0, self._get_current_target_sec() - self.current_sec)

    async def start(self, callback: Callable, task_id: Optional[int] = None, sound_enabled: bool = True):
        try:
            with SessionLocal() as db:
                settings = get_settings(db)
                self._sound_enabled = settings.get("sound_enabled", sound_enabled)
                self._sound_type = settings.get("sound_type", "bell")
        except:
            self._sound_enabled = sound_enabled
            self._sound_type = "bell"

        self.is_running = True
        self.just_finished = False
        self.session_started_at = datetime.utcnow()
        self.task_id = task_id
        self._callback = callback
        self._task = asyncio.create_task(self._run())

    async def pause(self):
        self.is_running = False
        if self._task:
            self._task.cancel()

    async def reset(self):
        await self.pause()
        self.current_sec = self.work_sec
        self.is_work_session = True
        self.is_long_break = False
        self.completed_work_sessions = 0
        self.just_finished = False
        if self._callback:
            self._callback()

    def toggle_session_type(self):
        if self.is_work_session:
            self.completed_work_sessions += 1
            self.is_work_session = False
            if self.completed_work_sessions >= self.sessions_until_long_break:
                self.is_long_break = True
            else:
                self.is_long_break = False
        else:
            if self.is_long_break:
                self.completed_work_sessions = 0
            self.is_work_session = True
            self.is_long_break = False
        self.current_sec = self._get_current_target_sec()

    def skip_and_save(self) -> int:
        """
        НОВОЕ: Пропускает сессию, сохраняя частичный прогресс.
        Возвращает количество сохранённых секунд.
        """
        elapsed = self.get_elapsed_sec()

        # Сохраняем только если прошло хотя бы 1 секунда
        if elapsed > 0:
            self._save_session_with_duration(elapsed)

        # Переключаем тип (счётчик увеличивается для работы)
        self.toggle_session_type()
        return elapsed

    def _save_session_with_duration(self, duration: int):
        """Сохраняет сессию с указанной длительностью"""
        if self.is_work_session:
            session_type = 'work'
        elif self.is_long_break:
            session_type = 'long_break'
        else:
            session_type = 'short_break'
        with SessionLocal() as db:
            create_session(db, self.task_id, session_type, duration, True)

    def set_session_mode(self, is_work: bool):
        if not self.is_running:
            self.is_work_session = is_work
            self.is_long_break = False
            self.current_sec = self._get_current_target_sec()

    def get_session_progress(self) -> str:
        return f"{self.completed_work_sessions}/{self.sessions_until_long_break}"

    def get_session_type_display(self) -> str:
        if self.is_work_session:
            return "Работа"
        elif self.is_long_break:
            return "Длинный перерыв"
        else:
            return "Короткий перерыв"

    def get_mode_key(self) -> str:
        if self.is_work_session:
            return "work"
        elif self.is_long_break:
            return "long_break"
        else:
            return "rest"

    async def _run(self):
        try:
            while self.is_running and self.current_sec > 0:
                await asyncio.sleep(1)
                self.current_sec -= 1
                if self._callback:
                    self._callback()

            if self.current_sec <= 0 and self.is_running:
                self.is_running = False
                self.just_finished = True
                self._save_session()
                if self._sound_enabled:
                    self._sound_service.play(self._sound_type)
                self.toggle_session_type()
                if self._callback:
                    self._callback()
        except asyncio.CancelledError:
            pass

    def _save_session(self):
        duration = self._get_current_target_sec()
        if self.is_work_session:
            session_type = 'work'
        elif self.is_long_break:
            session_type = 'long_break'
        else:
            session_type = 'short_break'
        with SessionLocal() as db:
            create_session(db, self.task_id, session_type, duration, True)

    def get_display_time(self) -> str:
        total_sec = max(0, self.current_sec)
        minutes = total_sec // 60
        seconds = total_sec % 60
        return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def format_duration(total_sec: int) -> str:
        """НОВОЕ: форматирует длительность с секундами"""
        minutes = total_sec // 60
        seconds = total_sec % 60
        if seconds > 0:
            return f"{minutes} мин {seconds} сек"
        return f"{minutes} мин"