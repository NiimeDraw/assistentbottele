"""Helper fungsi untuk interaksi Telegram yang aman.

Modul ini menyediakan fungsi utilitas terpusat untuk menangani
callback query secara aman, menghindari duplikasi di seluruh handler.
"""
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
        await callback.message.edit_text(text, reply_markup=reply_markup)
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
