"""
Middleware yang memastikan pengguna Telegram terdaftar di database (get_or_create)
dan menyisipkan objek User (internal, bukan telegram user) ke context handler.
Ini menjamin isolasi data: setiap handler bekerja dengan user_id internal, bukan telegram_id.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from app.services.user_service import UserService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        session = data.get("session")
        tg_user = data.get("event_from_user")

        if session is not None and tg_user is not None:
            user_service = UserService(session)
            full_name = tg_user.full_name or tg_user.username or f"user_{tg_user.id}"
            db_user = await user_service.get_or_create_user(
                telegram_id=tg_user.id,
                full_name=full_name,
                username=tg_user.username,
            )
            data["db_user"] = db_user

        return await handler(event, data)
