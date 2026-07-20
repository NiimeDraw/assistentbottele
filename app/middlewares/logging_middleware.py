"""Middleware untuk mencatat setiap update yang masuk ke bot (audit/debug)."""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        user_info = f"user_id={tg_user.id}" if tg_user else "unknown_user"
        logger.info("Update masuk | %s | type=%s", user_info, type(event).__name__)
        try:
            return await handler(event, data)
        except Exception:
            logger.exception("Terjadi error saat memproses update dari %s", user_info)
            raise
