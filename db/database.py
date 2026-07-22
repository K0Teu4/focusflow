# db/database.py
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from db.models import Base, Task, Session as PomodoroSession, UserState
from pathlib import Path
from datetime import datetime, date, timedelta

DB_PATH = Path(__file__).parent / "focusflow.db"

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        if not session.query(UserState).first():
            session.add(UserState(id=1))
            session.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_task(db: Session, title: str, category: str = "work") -> Task:
    task = Task(title=title, category=category)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_tasks(db: Session, include_done: bool = False):
    query = db.query(Task)
    if not include_done:
        query = query.filter(Task.is_done == False)
    return query.order_by(Task.created_at.desc()).all()


def complete_task(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.is_done = True
        db.commit()


def delete_task(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()


def get_task_by_id(db: Session, task_id: int) -> Task:
    return db.query(Task).filter(Task.id == task_id).first()


def get_task_session_count(db: Session, task_id: int) -> int:
    """Считает количество завершённых work-сессий для задачи."""
    count = db.query(func.count(PomodoroSession.id)).filter(
        PomodoroSession.task_id == task_id,
        PomodoroSession.type == 'work',
        PomodoroSession.is_completed == True,
    ).scalar()
    return count or 0


def create_session(db: Session, task_id: int, session_type: str, duration_sec: int, is_completed: bool = False) -> PomodoroSession:
    session = PomodoroSession(
        task_id=task_id,
        type=session_type,
        duration_sec=duration_sec,
        is_completed=is_completed,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_user_state(db: Session) -> UserState:
    return db.query(UserState).first()


def update_premium_status(db: Session, is_premium: bool, expires_at: datetime = None):
    user_state = get_user_state(db)
    user_state.is_premium = is_premium
    user_state.premium_expires_at = expires_at
    db.commit()


def get_today_stats(db: Session):
    today = datetime.utcnow().date()
    sessions = db.query(PomodoroSession).filter(
        PomodoroSession.started_at >= today,
        PomodoroSession.is_completed == True,
    ).all()
    work_sessions = [s for s in sessions if s.type == 'work']
    return {
        'total_sessions': len(sessions),
        'work_sessions': len(work_sessions),
        'total_work_minutes': sum(s.duration_sec for s in work_sessions) // 60,
    }


def get_settings(db: Session) -> dict:
    user_state = get_user_state(db)
    settings = user_state.settings or {}
    # Дефолты с поддержкой минут+секунд
    defaults = {
        "work_min": 25,
        "work_sec": 0,
        "break_min": 5,
        "break_sec": 0,
        "long_break_min": 15,
        "long_break_sec": 0,
        "sessions_until_long_break": 4,
        "sound_enabled": True,
        "auto_start": False,
        "auto_start_delay": 3,
        "sound_type": "bell",
        "theme": "dark",
    }
    # Миграция: если в старых настройках нет work_sec, но есть work_min — ок, _calc_seconds разберётся
    merged = {**defaults, **settings}
    return merged


def update_settings(db: Session, settings: dict):
    user_state = get_user_state(db)
    user_state.settings = settings
    db.commit()


# === СТАТИСТИКА ДЛЯ PREMIUM ===

def get_total_stats(db: Session) -> dict:
    """Общая статистика за всё время."""
    sessions = db.query(PomodoroSession).filter(
        PomodoroSession.is_completed == True
    ).all()
    work_sessions = [s for s in sessions if s.type == 'work']
    total_work_sec = sum(s.duration_sec for s in work_sessions)
    return {
        'total_sessions': len(sessions),
        'work_sessions': len(work_sessions),
        'total_work_minutes': total_work_sec // 60,
        'total_work_hours': round(total_work_sec / 3600, 1),
    }


def get_daily_activity(db: Session, days: int = 7) -> list:
    """Активность за последние N дней."""
    today = datetime.utcnow().date()
    result = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        sessions = db.query(PomodoroSession).filter(
            PomodoroSession.started_at >= datetime.combine(day, datetime.min.time()),
            PomodoroSession.started_at < datetime.combine(next_day, datetime.min.time()),
            PomodoroSession.type == 'work',
            PomodoroSession.is_completed == True,
        ).all()
        work_minutes = sum(s.duration_sec for s in sessions) // 60
        result.append({
            'date': day,
            'work_sessions': len(sessions),
            'work_minutes': work_minutes,
        })
    return result


def get_current_streak(db: Session) -> int:
    """Серия дней подряд с хотя бы одной work-сессией."""
    today = datetime.utcnow().date()
    streak = 0
    for i in range(365):
        day = today - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count = db.query(func.count(PomodoroSession.id)).filter(
            PomodoroSession.started_at >= datetime.combine(day, datetime.min.time()),
            PomodoroSession.started_at < datetime.combine(next_day, datetime.min.time()),
            PomodoroSession.type == 'work',
            PomodoroSession.is_completed == True,
        ).scalar() or 0
        if count > 0:
            streak += 1
        else:
            if i > 0:
                break
            continue
    return streak


def get_recent_sessions(db: Session, limit: int = 20) -> list:
    """Последние N завершённых сессий."""
    sessions = db.query(PomodoroSession).filter(
        PomodoroSession.is_completed == True
    ).order_by(PomodoroSession.started_at.desc()).limit(limit).all()
    
    result = []
    for s in sessions:
        task_title = None
        if s.task_id:
            task = db.query(Task).filter(Task.id == s.task_id).first()
            task_title = task.title if task else None
        result.append({
            'type': s.type,
            'duration_min': s.duration_sec // 60,
            'started_at': s.started_at,
            'task_title': task_title,
            'duration_sec': s.duration_sec,
            'is_completed': s.is_completed,
        })
    return result


def get_all_sessions_for_export(db: Session) -> list:
    """
    Все сессии для экспорта в CSV.
    Возвращает список словарей с полными данными, включая названия задач.
    """
    sessions = db.query(PomodoroSession).order_by(
        PomodoroSession.started_at.desc()
    ).all()
    
    result = []
    # Кэшируем задачи, чтобы не делать N+1 запросов
    tasks_cache = {}
    for s in sessions:
        if s.task_id and s.task_id not in tasks_cache:
            task = db.query(Task).filter(Task.id == s.task_id).first()
            tasks_cache[s.task_id] = task.title if task else None
        
        result.append({
            'started_at': s.started_at,
            'type': s.type,
            'duration_sec': s.duration_sec,
            'task_title': tasks_cache.get(s.task_id),
            'is_completed': s.is_completed,
        })
    
    return result


init_db()