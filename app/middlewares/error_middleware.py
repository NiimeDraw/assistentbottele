"""Middleware penanganan error global — jaring pengaman terluar.

Menangkap exception yang tidak ter-handle di handler manapun,
mengirim pesan ramah ke user, dan men-log stack trace lengkap.
Tanpa middleware ini, bot akan "diam" tanpa respon saat terjadi
error tak terduga.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from app.keyboards.main_menu import main_menu_keyboard
from app.utils.logger import get_logger

logger = get_logger(__name__)

_ERROR_TEXT = (
    "⚠️ Terjadi kesalahan. Silakan coba lagi atau ketik /start "
    "untuk kembali ke menu utama."
)


class ErrorHandlerMiddleware(BaseMiddleware):
    """Outer middleware yang membungkus seluruh pipeline handler.

    Ditempatkan di urutan pertama pada dp.update.outer_middleware()
    agar menjadi lapisan terluar yang menangkap semua exception,
    termasuk yang berasal dari middleware lain.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Unhandled error saat memproses update")
            await self._notify_user(event)
            # Tidak re-raise agar bot tetap berjalan dan menerima update berikutnya

    async def _notify_user(self, event: TelegramObject) -> None:
        """Berusaha mengirim pesan error ramah ke user jika memungkinkan."""
        try:
            # Jika event adalah Update, ambil message atau callback_query di dalamnya
            target = event
            if isinstance(event, Update):
                target = event.message or event.callback_query or event

            if isinstance(target, Message):
                await target.answer(_ERROR_TEXT, reply_markup=main_menu_keyboard())
            elif isinstance(target, CallbackQuery):
                await target.answer(_ERROR_TEXT, show_alert=True)
        except Exception:
            # Jika bahkan notifikasi gagal (mis. user blokir bot), hanya log
            logger.debug("Gagal mengirim notifikasi error ke user", exc_info=True)
