"""Handler untuk fitur Tanya AI (integrasi OpenAI API)."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.handlers.states import AIStates
from app.keyboards.main_menu import (
    BTN_BANTUAN,
    BTN_CATATAN,
    BTN_JADWAL,
    BTN_TANYA_AI,
    BTN_TUGAS,
    main_menu_keyboard,
)
from app.services.ai_service import AIService
from app.utils.exceptions import AppError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="ai")

ai_service = AIService()

_MENU_BUTTONS = {BTN_TUGAS, BTN_JADWAL, BTN_CATATAN, BTN_TANYA_AI, BTN_BANTUAN}


@router.message(F.text == BTN_TANYA_AI)
async def ai_prompt(message: Message, state: FSMContext) -> None:
    await state.set_state(AIStates.waiting_question)
    await message.answer(
        "🤖 Silakan ketik pertanyaan akademikmu. Ketik /cancel untuk kembali ke menu."
    )


@router.message(AIStates.waiting_question, F.text.func(lambda t: t not in _MENU_BUTTONS))
async def ai_answer(message: Message, state: FSMContext) -> None:
    question = message.text or ""
    thinking_msg = await message.answer("🤖 Sedang berpikir...")
    try:
        answer = await ai_service.ask(question)
    except AppError as exc:
        await thinking_msg.edit_text(f"⚠️ {exc.message}")
        return

    await thinking_msg.edit_text(answer)
    await message.answer(
        "Ada pertanyaan lain? Ketik saja, atau pilih menu lain di bawah.",
        reply_markup=main_menu_keyboard(),
    )
    # Tetap di state waiting_question agar user bisa lanjut bertanya tanpa menekan tombol lagi
    await state.set_state(AIStates.waiting_question)
