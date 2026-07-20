from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_EDIT_PROFILE = "✏️ Edit Profil"
BTN_DELETE_ACCOUNT = "🗑️ Hapus Akun"
BTN_BACK = "🔙 Kembali"


def profile_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_EDIT_PROFILE), KeyboardButton(text=BTN_DELETE_ACCOUNT)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Kelola profil Anda",
    )
