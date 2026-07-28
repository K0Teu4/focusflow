# services/license_service.py
"""Лицензионные коды Premium (оффлайн, HMAC, без сервера).

Код самодостаточен: содержит payload (тип продукта + срок) и HMAC-подпись.
Проверка не требует сети. Секрет лежит в коде (компромисс MVP — см. план).

Формат кода: 4 группы по 4 base32-символа через дефис = XXXX-XXXX-XXXX-XXXX.
Внутри: 5 байт payload (1 байт продукт + 4 байта expiry_ts big-endian;
expiry_ts=0 означает «бессрочно») + 5 байт подписи = 16 base32-символов без паддинга.

CLI-генератор (для выдачи кодов покупателям):
    python -m services.license_service 30      # на 30 дней
    python -m services.license_service 365     # на год
    python -m services.license_service perm    # бессрочно
"""
import base64
import hashlib
import hmac
import struct
from datetime import datetime

# Секрет подписи. В проде можно вынести в env/сборку; для MVP — константа.
SECRET = "focusflow-2026-hmac-secret-change-me"

# Маппинг продукт <-> 1 байт (в payload).
_PRODUCT_TO_BYTE = {"focusflow_premium": 1}
_BYTE_TO_PRODUCT = {v: k for k, v in _PRODUCT_TO_BYTE.items()}

PRODUCT_PREMIUM = "focusflow_premium"

_PERM_TS = 0  # маркер бессрочного срока в payload


def _b32encode(b: bytes) -> str:
    return base64.b32encode(b).decode().rstrip("=")


def _b32decode(s: str) -> bytes:
    pad = "=" * ((8 - len(s) % 8) % 8)
    return base64.b32decode(s + pad)


def _sign(payload_raw: bytes) -> bytes:
    return hmac.new(SECRET.encode(), payload_raw, hashlib.sha256).digest()[:5]


def _format_code(raw16: str) -> str:
    return "-".join(raw16[i:i + 4] for i in range(0, 16, 4))


def generate_code(product_id: str = PRODUCT_PREMIUM, expires_at: datetime = None) -> str:
    """Сгенерировать лицензионный код. expires_at=None -> бессрочно."""
    if product_id not in _PRODUCT_TO_BYTE:
        raise ValueError(f"unknown product: {product_id}")
    product_byte = _PRODUCT_TO_BYTE[product_id]
    expiry_ts = _PERM_TS if expires_at is None else int(expires_at.timestamp())
    payload_raw = bytes([product_byte]) + struct.pack(">I", expiry_ts)  # 5 байт
    sig = _sign(payload_raw)                                            # 5 байт
    raw16 = _b32encode(payload_raw) + _b32encode(sig)                   # 8 + 8 = 16
    return _format_code(raw16)


class LicenseService:
    """Активация по коду. Без сети: парсинг + сверка HMAC + PremiumService.activate."""

    @staticmethod
    def activate_code(code: str) -> dict:
        """Проверить код и активировать Premium.

        Возвращает {"ok": bool, "error": str|None, "expires_at": datetime|None}.
        Истёкший код НЕ активирует (ok=False, error="expired").
        """
        # ленивый импорт, чтобы CLI-генерация работала без контекста пакета
        from services.premium_service import PremiumService

        clean = code.upper().replace("-", "").replace(" ", "").strip()
        if len(clean) != 16:
            return {"ok": False, "error": "invalid_format", "expires_at": None}
        try:
            payload_raw = _b32decode(clean[:8])   # 5 байт
            sig = _b32decode(clean[8:])           # 5 байт
        except Exception:
            return {"ok": False, "error": "invalid_format", "expires_at": None}

        if len(payload_raw) != 5 or len(sig) != 5:
            return {"ok": False, "error": "invalid_format", "expires_at": None}
        if not hmac.compare_digest(_sign(payload_raw), sig):
            return {"ok": False, "error": "bad_signature", "expires_at": None}

        product_byte = payload_raw[0]
        if product_byte not in _BYTE_TO_PRODUCT:
            return {"ok": False, "error": "unknown_product", "expires_at": None}

        expiry_ts = struct.unpack(">I", payload_raw[1:5])[0]
        if expiry_ts == _PERM_TS:
            expires_at = None
        else:
            expires_at = datetime.fromtimestamp(expiry_ts)
            if expires_at <= datetime.now():
                return {"ok": False, "error": "expired", "expires_at": expires_at}

        PremiumService.activate(expires_at=expires_at)
        return {"ok": True, "error": None, "expires_at": expires_at}


# --------------------------------------------------------------------------- #
# CLI-генератор кодов (оффлайн-утилита для выдачи покупателям)                #
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys
    from datetime import timedelta
    arg = sys.argv[1] if len(sys.argv) > 1 else "30"
    if arg in ("0", "perm", "permanent", "бессрочно"):
        exp = None
    else:
        exp = datetime.now() + timedelta(days=int(arg))
    code = generate_code(PRODUCT_PREMIUM, exp)
    label = "бессрочно" if exp is None else f"до {exp.strftime('%d.%m.%Y')}"
    print(f"Код ({label}): {code}")