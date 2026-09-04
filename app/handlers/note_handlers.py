"""Handler untuk fitur Catatan (Note): daftar, tambah, lihat, hapus."""
# pyrefly: ignore [missing-import]
from aiogram import F, Router
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext
# pyrefly: ignore [missing-import]
from aiogram.html import quote
# pyrefly: ignore [missing-import]
from aiogram.types import CallbackQuery, Message
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

# pyrefly: ignore [missing-import]
from app.handlers.states import NoteStates
# pyrefly: ignore [missing-import]
from app.keyboards.main_menu import BTN_CATATAN, main_menu_keyboard
# pyrefly: ignore [missing-import]
from app.keyboards.note_kb import note_detail_keyboard, note_list_keyboard
# pyrefly: ignore [missing-import]
from app.models.user import User
# pyrefly: ignore [missing-import]
from app.services.note_service import NoteService
# pyrefly: ignore [missing-import]
from app.utils.exceptions import AppError
# pyrefly: ignore [missing-import]
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="note")


def _render_note_list_text(notes) -> str:
    if not notes:
        return "📝 <b>Catatan</b>\n\nBelum ada catatan. Tambahkan catatan pertamamu!"
    return "📝 <b>Catatan</b>\n\nPilih catatan di bawah untuk melihat isinya."


async def _safe_edit_or_send(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    """Edit pesan callback jika memungkinkan, kalau tidak fallback kirim pesan baru.

    Menggunakan isinstance check (bukan cuma truthy check) karena
    callback.message bertipe Message | InaccessibleMessage | None di aiogram 3.x.
    """
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=reply_markup)
    elif callback.bot is not None:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=reply_markup)


async def _safe_answer(callback: CallbackQuery, text: str) -> None:
    """Kirim pesan baru (bukan edit) dengan aman terlepas dari tipe callback.message."""
    if isinstance(callback.message, Message):
        await callback.message.answer(text)
    elif callback.bot is not None:
        await callback.bot.send_message(callback.from_user.id, text)


@router.message(F.text == BTN_CATATAN)
async def show_note_menu(message: Message, session: AsyncSession, db_user: User) -> None:
    service = NoteService(session)
    notes = await service.list_notes(db_user.id)
    await message.answer(_render_note_list_text(notes), reply_markup=note_list_keyboard(notes))


@router.callback_query(F.data == "note_back")
async def note_back(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = NoteService(session)
    notes = await service.list_notes(db_user.id)
    await _safe_edit_or_send(callback, _render_note_list_text(notes), note_list_keyboard(notes))
    await callback.answer()


@router.callback_query(F.data == "note_add")
async def note_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(NoteStates.waiting_title)
    await _safe_answer(callback, "Masukkan <b>judul catatan</b> (ketik /cancel untuk membatalkan):")
    await callback.answer()


@router.message(NoteStates.waiting_title)
async def note_add_title(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Judul tidak boleh kosong. Coba lagi:")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(NoteStates.waiting_content)
    await message.answer("Masukkan <b>isi catatan</b>:")


@router.message(NoteStates.waiting_content)
async def note_add_content(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    service = NoteService(session)
    try:
        await service.create_note(user_id=db_user.id, title=data["title"], content=message.text or "")
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang isi catatan:")
        return

    await state.clear()
    notes = await service.list_notes(db_user.id)
    await message.answer("✅ Catatan berhasil disimpan!", reply_markup=main_menu_keyboard())
    await message.answer(_render_note_list_text(notes), reply_markup=note_list_keyboard(notes))


@router.callback_query(F.data.startswith("note_detail:"))
async def note_detail(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    if not callback.data:
        await callback.answer("Error: invalid data", show_alert=True)
        return
    note_id = int(callback.data.split(":")[1])
    service = NoteService(session)
    try:
        note = await service.get_note(note_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    text = f"📄 <b>{quote(note.title)}</b>\n\n{quote(note.content)}"
    await _safe_edit_or_send(callback, text, note_detail_keyboard(note.id))
    await callback.answer()


@router.callback_query(F.data.startswith("note_delete:"))
async def note_delete(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    if not callback.data:
        await callback.answer("Error: invalid data", show_alert=True)
        return
    note_id = int(callback.data.split(":")[1])
    service = NoteService(session)
    try:
        await service.delete_note(note_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Catatan dihapus 🗑️")
    notes = await service.list_notes(db_user.id)
    await _safe_edit_or_send(callback, _render_note_list_text(notes), note_list_keyboard(notes))