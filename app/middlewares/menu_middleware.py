"""Middleware untuk navigasi menu: membatalkan FSM State saat tombol menu ditekan."""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

from app.keyboards.main_menu import ALL_MENU_BUTTONS

# Tombol dan perintah yang langsung memicu pembatalan state saat ditekan
# (kecualikan /cancel karena sudah memiliki handler sendiri untuk menampilkan pesan pembatalan)
NAVIGATION_TRIGGERS = ALL_MENU_BUTTONS - {"/cancel"}


class MenuNavigationMiddleware(BaseMiddleware):
    """
    Middleware yang mendeteksi jika pengguna menekan tombol menu utama atau perintah navigasi
    saat masih berada di tengah-tengah alur FSM State (mis. input judul tugas atau tanggal).

    Jika terdeteksi, state akan dibersihkan terlebih dahulu sehingga handler menu terkait
    dapat menangani pesan tersebut tanpa salah menyimpan teks tombol sebagai input form.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text:
            text = event.text.strip()
            if text in NAVIGATION_TRIGGERS:
                state: FSMContext | None = data.get("state")
                if state is not None:
                    current_state = await state.get_state()
                    if current_state is not None:
                        await state.clear()

        return await handler(event, data)
