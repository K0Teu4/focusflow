# services/premium_service.py
from datetime import datetime
from db.database import SessionLocal, get_user_state, update_premium_status


class PremiumService:
    """Единая точка чтения/записи Premium-статуса.

    Учитывает срок действия: если premium_expires_at в прошлом — effective
    статус False, даже если флаг в БД ещё True. Это гарантирует, что все
    экраны и будущая нативная покупка (Pay SDK) видят одно и то же значение.
    """

    @staticmethod
    def get_status(db=None) -> dict:
        """{is_premium (effective), expires_at, raw_is_premium}."""
        own = db is None
        if own:
            db = SessionLocal()
        try:
            user = get_user_state(db)
            raw = bool(user.is_premium)
            expires_at = user.premium_expires_at
            effective = raw and (expires_at is None or expires_at > datetime.utcnow())
            return {"is_premium": effective, "expires_at": expires_at, "raw_is_premium": raw}
        finally:
            if own:
                db.close()

    @staticmethod
    def is_premium(db=None) -> bool:
        return PremiumService.get_status(db)["is_premium"]

    @staticmethod
    def activate(expires_at: datetime = None, db=None):
        """Активировать Premium. expires_at=None — бессрочно. Сюда придёт Pay SDK."""
        own = db is None
        if own:
            db = SessionLocal()
        try:
            update_premium_status(db, True, expires_at)
        finally:
            if own:
                db.close()

    @staticmethod
    def deactivate(db=None):
        own = db is None
        if own:
            db = SessionLocal()
        try:
            update_premium_status(db, False)
        finally:
            if own:
                db.close()