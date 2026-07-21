# db/database.py
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
from db.models import Base, Task, Session as PomodoroSession, UserState
from pathlib import Path
from datetime import datetime, date

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
    """Считает количество завершённых work-сессий для задачи"""
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
    return user_state.settings or {
        "work_min": 25,
        "break_min": 5,
        "sound_enabled": True,
        "theme": "dark",
    }

def update_settings(db: Session, settings: dict):
    user_state = get_user_state(db)
    user_state.settings = settings
    db.commit()

init_db()