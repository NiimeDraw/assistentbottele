"""Reply Keyboard untuk menu utama bot."""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_TUGAS = "📚 Tugas"
BTN_JADWAL = "🗓️ Jadwal Kuliah"
BTN_AKADEMIK = "📅 Kalender Akademik"
BTN_CATATAN = "📝 Catatan"
BTN_NILAI = "📈 IPK Calculator"
BTN_TANYA_AI = "🤖 Tanya AI"
BTN_PROFIL = "👤 Profil"
BTN_BANTUAN = "❓ Bantuan"

ALL_MENU_BUTTONS = {
    BTN_TUGAS,
    BTN_JADWAL,
    BTN_AKADEMIK,
    BTN_CATATAN,
    BTN_NILAI,
    BTN_TANYA_AI,
    BTN_PROFIL,
    BTN_BANTUAN,
    "/start",
    "/help",
    "/cancel",
    "/menu",
    "/back",
}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TUGAS), KeyboardButton(text=BTN_JADWAL)],
            [KeyboardButton(text=BTN_AKADEMIK), KeyboardButton(text=BTN_CATATAN)],
            [KeyboardButton(text=BTN_NILAI)],
            [KeyboardButton(text=BTN_TANYA_AI), KeyboardButton(text=BTN_PROFIL)],
            [KeyboardButton(text=BTN_BANTUAN)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Pilih menu di bawah...",
    )
