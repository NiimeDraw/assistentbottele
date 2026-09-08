"""Handler upload PDF dan histori ringkasannya."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.states import DocumentStates
from app.keyboards.pdf_summary_kb import pdf_summary_list_keyboard
from app.models.user import User
from app.services.pdf_summary_service import PdfSummaryService
from app.utils.exceptions import AppError
from app.utils.html import quote
from app.utils.telegram_helpers import safe_answer, safe_edit_or_send

router = Router(name="pdf_summary")


async def _show_history(target: Message | CallbackQuery, session: AsyncSession, user: User) -> None:
    history = await PdfSummaryService(session).list_history(user.id)
    text = "🧾 <b>Histori Ringkasan PDF</b>\n\n"
    text += "Belum ada ringkasan." if not history else "Pilih ringkasan untuk melihat hasilnya."
    if isinstance(target, CallbackQuery):
        await safe_edit_or_send(target, text, pdf_summary_list_keyboard(history))
    else:
        await target.answer(text, reply_markup=pdf_summary_list_keyboard(history))


@router.callback_query(F.data == "pdf_summary_add")
async def pdf_summary_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DocumentStates.waiting_pdf_summary)
    await safe_answer(callback, "Kirim file PDF yang ingin diringkas. File sementara akan dihapus setelah proses.")
    await callback.answer()


@router.message(DocumentStates.waiting_pdf_summary)
async def pdf_summary_receive(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User, bot: Bot
) -> None:
    if not message.document or not message.document.file_name:
        await message.answer("Silakan kirim file PDF sebagai dokumen.")
        return
    thinking = await message.answer("⏳ PDF sedang diunduh, dibaca, dan diringkas...")
    try:
        summary = await PdfSummaryService(session).summarize_upload(
            bot, db_user.id, message.document.file_id,
            message.document.file_name, message.document.file_size,
        )
    except AppError as exc:
        await thinking.edit_text(f"⚠️ {exc.message}")
        return
    await state.clear()
    await thinking.edit_text(
        f"✅ Ringkasan <b>{quote(summary.file_name)}</b> selesai "
        f"({summary.page_count} halaman).\n\n"
        "Gunakan menu Histori Ringkasan untuk membukanya."
    )
    await _show_history(message, session, db_user)


@router.callback_query(F.data == "pdf_summary_history")
async def pdf_summary_history(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await _show_history(callback, session, db_user)
    await callback.answer()


@router.callback_query(F.data.startswith("pdf_summary_detail:"))
async def pdf_summary_detail(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    summary_id = int(callback.data.split(":")[1])
    history = await PdfSummaryService(session).list_history(db_user.id)
    summary = next((item for item in history if item.id == summary_id), None)
    if not summary:
        await callback.answer("Ringkasan tidak ditemukan.", show_alert=True)
        return
    await safe_edit_or_send(callback, PdfSummaryService.format_history(summary), pdf_summary_list_keyboard(history))
    await callback.answer()
