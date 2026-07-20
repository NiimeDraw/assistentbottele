"""Reply Keyboard untuk menu utama bot."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_TUGAS = "📚 Tugas"
BTN_JADWAL = "🗓️ Jadwal Kuliah"
BTN_CATATAN = "📝 Catatan"
BTN_TANYA_AI = "🤖 Tanya AI"
BTN_BANTUAN = "❓ Bantuan"
BTN_PROFIL = "👤 Profil"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TUGAS), KeyboardButton(text=BTN_JADWAL)],
            [KeyboardButton(text=BTN_CATATAN), KeyboardButton(text=BTN_TANYA_AI)],
            [KeyboardButton(text=BTN_PROFIL), KeyboardButton(text=BTN_BANTUAN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Pilih menu di bawah...",
    )
