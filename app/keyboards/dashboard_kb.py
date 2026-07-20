from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BTN_AKADEMIK = "📚 Akademik"
BTN_TUGAS = "📝 Tugas"
BTN_JADWAL = "📅 Jadwal"
BTN_NILAI = "📈 Nilai"
BTN_KEUANGAN = "💰 Keuangan"
BTN_AI = "🤖 AI Assistant"
BTN_DOKUMEN = "📂 Dokumen"
BTN_PENGATURAN = "⚙ Pengaturan"


def build_dashboard_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=BTN_AKADEMIK, callback_data="dashboard:akademik"),
            InlineKeyboardButton(text=BTN_TUGAS, callback_data="dashboard:tugas"),
        ],
        [
            InlineKeyboardButton(text=BTN_JADWAL, callback_data="dashboard:jadwal"),
            InlineKeyboardButton(text=BTN_NILAI, callback_data="dashboard:nilai"),
        ],
        [
            InlineKeyboardButton(text=BTN_KEUANGAN, callback_data="dashboard:keuangan"),
            InlineKeyboardButton(text=BTN_AI, callback_data="dashboard:ai"),
        ],
        [
            InlineKeyboardButton(text=BTN_DOKUMEN, callback_data="dashboard:dokumen"),
            InlineKeyboardButton(text=BTN_PENGATURAN, callback_data="dashboard:pengaturan"),
        ],
    ])

    return kb
