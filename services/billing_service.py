# services/billing_service.py
import flet as ft
from services.premium_service import PremiumService
from ui.theme import COLORS
from ui.toast import show_toast

PRODUCT_PREMIUM = "focusflow_premium"


class BillingService:
    """Абстракция над покупкой/восстановлением.

    Сейчас нативный канал (RuStore Pay SDK через Flet-extension) не подключён:
    _native_available = False, методы работают в mock-режиме (честный тост).
    Когда extension заработает, флаг станет True, и purchase/restore пойдут через
    MethodChannel в Kotlin; успех -> PremiumService.activate(expires_at=...).
    Экраны про MethodChannel не знают — они дёргают только этот сервис.
    """

    _native_available = False  # переключится в True, когда Flet-extension подключён

    @classmethod
    def is_available(cls) -> bool:
        return cls._native_available

    @classmethod
    def purchase(cls, page, product_id=PRODUCT_PREMIUM, on_success=None, on_error=None):
        if not cls._native_available:
            show_toast(page, "Покупка появится в следующем обновлении",
                       ft.Icons.INFO_OUTLINE, COLORS["primary"], duration=3000)
            if on_error:
                on_error("native_channel_not_connected")
            return
        # TODO(натив): MethodChannel -> Kotlin RuStorePayClient.purchase(...)
        #   успех -> PremiumService.activate(expires_at=...) -> on_success()

    @classmethod
    def restore(cls, page, on_success=None, on_error=None):
        if not cls._native_available:
            show_toast(page, "Восстановление покупок появится вместе с оплатой",
                       ft.Icons.INFO_OUTLINE, COLORS["text_secondary"], duration=3000)
            if on_error:
                on_error("native_channel_not_connected")
            return
        # TODO(натив): MethodChannel -> Kotlin getPurchases()
        #   есть активная покупка -> PremiumService.activate(expires_at=...) -> on_success()