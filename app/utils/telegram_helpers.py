"""Helper fungsi untuk interaksi Telegram yang aman.

Modul ini menyediakan fungsi utilitas terpusat untuk menangani
callback query secara aman, menghindari duplikasi di seluruh handler.
"""
import asyncio
from collections.abc import Awaitable, Callable

from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError, TelegramRetryAfter
from aiogram.types import CallbackQuery, Message


async def safe_edit_or_send(
    callback: CallbackQuery, text: str, reply_markup=None
) -> None:
    """Edit pesan callback jika memungkinkan, kalau tidak fallback kirim pesan baru.

    Menggunakan isinstance check (bukan cuma truthy check) karena
    callback.message bertipe Message | InaccessibleMessage | None di aiogram 3.x.
    InaccessibleMessage tidak punya method edit_text/answer, jadi harus
    dibedakan secara eksplisit agar aman dari AttributeError sekaligus
    lolos pengecekan tipe statis (Pylance).
    """
    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(text, reply_markup=reply_markup)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                return  # Tidak ada perubahan, abaikan saja
            raise
    elif callback.bot is not None:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=reply_markup
        )


async def safe_answer(
    callback: CallbackQuery, text: str, reply_markup=None
) -> None:
    """Kirim pesan baru (bukan edit) dengan aman terlepas dari tipe callback.message."""
    if isinstance(callback.message, Message):
        await callback.message.answer(text, reply_markup=reply_markup)
    elif callback.bot is not None:
        await callback.bot.send_message(
            callback.from_user.id, text, reply_markup=reply_markup
        )


async def send_with_retry(
    operation: Callable[[], Awaitable[object]],
    retries: int,
    delay_seconds: float,
) -> object:
    """Jalankan pengiriman Telegram ulang hanya untuk error yang transient."""
    attempts = max(1, retries + 1)
    for attempt in range(attempts):
        try:
            return await operation()
        except TelegramRetryAfter as exc:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(max(delay_seconds, float(exc.retry_after)))
        except TelegramNetworkError:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(delay_seconds)
