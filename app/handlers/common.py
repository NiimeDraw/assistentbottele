"""Handler umum: /start, /help, dan tombol Bantuan."""
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.keyboards.main_menu import BTN_BANTUAN, main_menu_keyboard
from app.keyboards.dashboard_kb import build_dashboard_kb
from app.models.user import User

router = Router(name="common")

HELP_TEXT = (
    "🎓 <b>Campus Assistant</b>\n\n"
    "Bot ini membantu aktivitas akademik dan produktivitas harianmu.\n\n"
    "<b>Menu yang tersedia:</b>\n"
    "📚 <b>Tugas</b> — catat & pantau deadline tugas kuliah\n"
    "🗓️ <b>Jadwal Kuliah</b> — simpan jadwal kuliah mingguan\n"
    "📝 <b>Catatan</b> — simpan catatan pribadi\n"
    "🤖 <b>Tanya AI</b> — tanya apa saja seputar akademik ke AI\n\n"
    "Gunakan tombol menu di bawah untuk memulai. Ketik /cancel kapan saja "
    "untuk membatalkan proses yang sedang berjalan."
)


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User) -> None:
    # Dashboard utama saat /start — menggunakan InlineKeyboard, modular per menu
    kb = build_dashboard_kb()
    first_name = (db_user.full_name.split()[0] if db_user and db_user.full_name else "User")
    text = (
        f"Halo {first_name} 👋\n\n"
        "Selamat datang di Campus Assistant.\n\n"
        "Menu:\n\n"
        "📚 Akademik\n\n"
        "📝 Tugas\n\n"
        "📅 Jadwal\n\n"
        "📈 Nilai\n\n"
        "💰 Keuangan\n\n"
        "🤖 AI Assistant\n\n"
        "📂 Dokumen\n\n"
        "⚙ Pengaturan\n\n"
        "Pilih menu di bawah untuk melanjutkan."
    )
    await message.answer(text, reply_markup=kb)


@router.message(Command("help"))
@router.message(F.text == BTN_BANTUAN)
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Tidak ada proses yang sedang berjalan.", reply_markup=main_menu_keyboard())
        return
    await state.clear()
    await message.answer("Proses dibatalkan.", reply_markup=main_menu_keyboard())
