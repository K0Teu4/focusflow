# db/models.py (полная актуальная версия)
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

CATEGORIES = {
    "work": "Работа",
    "rest": "Отдых",
    "hobby": "Хобби",
    "study": "Учеба"
}

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(20), default="work")  # ВАЖНО
    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sessions = relationship("Session", back_populates="task")

class Session(Base):
    __tablename__ = 'sessions'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True)
    type = Column(String(15))
    duration_sec = Column(Integer)
    started_at = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    task = relationship("Task", back_populates="sessions")

class UserState(Base):
    __tablename__ = 'user_state'
    id = Column(Integer, primary_key=True)
    __table_args__ = (CheckConstraint('id=1'),)
    is_premium = Column(Boolean, default=False)
    premium_expires_at = Column(DateTime, nullable=True)
    settings = Column(JSON, default={
        "work_min": 25,
        "break_min": 5,
        "long_break_min": 15,
        "sessions_until_long_break": 4,
        "sound_enabled": True,
        "auto_start": False,
        "auto_start_delay": 3,
        "sound_type": "bell",
        "theme": "dark"
    })