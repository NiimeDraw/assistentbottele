"""Handler upload, pencarian, rename, download, dan hapus dokumen."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.states import DocumentStates
from app.keyboards.dashboard_kb import BTN_DOKUMEN
from app.keyboards.document_kb import document_detail_keyboard, document_list_keyboard
from app.models.document import Document
from app.models.user import User
from app.services.document_service import DocumentService
from app.utils.exceptions import AppError
from app.utils.html import quote
from app.utils.telegram_helpers import safe_answer, safe_edit_or_send

router = Router(name="document")


def _render_document_list(documents: list[Document], query: str | None = None) -> str:
    if not documents:
        suffix = f' untuk pencarian "{quote(query)}"' if query else ""
        return f"📂 <b>Dokumen</b>\n\nBelum ada dokumen{suffix}."
    groups: dict[str, dict[str, dict[str, list[Document]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for document in documents:
        groups[document.semester][document.mata_kuliah][document.category].append(document)
    lines = ["📂 <b>Dokumen</b>"]
    for semester, courses in groups.items():
        lines.append(f"\n🎓 <b>Semester: {quote(semester)}</b>")
        for course, categories in courses.items():
            lines.append(f"  📚 <b>{quote(course)}</b>")
            for category, items in categories.items():
                lines.append(f"    🗂️ {quote(category)} ({len(items)})")
    lines.append("\nPilih dokumen di bawah untuk mengelola file.")
    return "\n".join(lines)


def _file_info(message: Message) -> tuple[str, str, int | None, str | None] | None:
    if message.document:
        return (
            message.document.file_id,
            message.document.file_name or "dokumen",
            message.document.file_size,
            message.document.mime_type,
        )
    if message.photo:
        photo = message.photo[-1]
        return photo.file_id, "gambar.jpg", photo.file_size, "image/jpeg"
    return None


async def _show_documents(
    target: Message | CallbackQuery,
    session: AsyncSession,
    user: User,
    query: str | None = None,
) -> None:
    documents = await DocumentService(session).list_documents(user.id, query)
    text = _render_document_list(documents, query)
    if isinstance(target, CallbackQuery):
        await safe_edit_or_send(target, text, document_list_keyboard(documents))
    else:
        await target.answer(text, reply_markup=document_list_keyboard(documents))


@router.message(F.text == BTN_DOKUMEN)
async def document_menu(message: Message, session: AsyncSession, db_user: User) -> None:
    await _show_documents(message, session, db_user)


@router.callback_query(F.data == "dashboard:dokumen")
async def dashboard_documents(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await _show_documents(callback, session, db_user)
    await callback.answer()


@router.callback_query(F.data == "document_back")
async def document_back(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    await _show_documents(callback, session, db_user)
    await callback.answer()


@router.callback_query(F.data == "document_add")
async def document_add(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DocumentStates.waiting_file)
    await safe_answer(
        callback,
        "📤 Kirim PDF, DOCX, PPT/PPTX, ZIP, atau gambar.\n"
        "Maksimal 20 MB. Ketik /cancel untuk membatalkan.",
    )
    await callback.answer()


@router.message(DocumentStates.waiting_file)
async def document_receive_file(message: Message, state: FSMContext) -> None:
    info = _file_info(message)
    if not info:
        await message.answer("Kirim file atau gambar yang didukung.")
        return
    file_id, name, file_size, mime_type = info
    try:
        DocumentService.validate_upload(name, file_size)
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}")
        return
    await state.update_data(
        file_id=file_id, original_name=name, file_size=file_size, mime_type=mime_type
    )
    await state.set_state(DocumentStates.waiting_semester)
    await message.answer("Masukkan semester, misalnya <b>Semester 3</b>:")


@router.message(DocumentStates.waiting_semester)
async def document_receive_semester(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Semester tidak boleh kosong. Coba lagi:")
        return
    await state.update_data(semester=message.text.strip())
    await state.set_state(DocumentStates.waiting_course)
    await message.answer("Masukkan nama mata kuliah:")


@router.message(DocumentStates.waiting_course)
async def document_receive_course(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Mata kuliah tidak boleh kosong. Coba lagi:")
        return
    await state.update_data(mata_kuliah=message.text.strip())
    await state.set_state(DocumentStates.waiting_category)
    await message.answer("Masukkan kategori, misalnya <b>Materi</b>, <b>Tugas</b>, atau <b>Ujian</b>:")


@router.message(DocumentStates.waiting_category)
async def document_receive_category(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User, bot: Bot
) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Kategori tidak boleh kosong. Coba lagi:")
        return
    data = await state.get_data()
    try:
        await DocumentService(session).save_upload(
            bot=bot, user_id=db_user.id, file_id=data["file_id"],
            original_name=data["original_name"], file_size=data["file_size"],
            mime_type=data["mime_type"], semester=data["semester"],
            mata_kuliah=data["mata_kuliah"], category=message.text.strip(),
        )
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}")
        return
    await state.clear()
    await message.answer("✅ Dokumen berhasil disimpan.")
    await _show_documents(message, session, db_user)


@router.callback_query(F.data == "document_search")
async def document_search(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DocumentStates.waiting_search)
    await safe_answer(callback, "Ketik kata kunci nama file, semester, mata kuliah, atau kategori:")
    await callback.answer()


@router.message(DocumentStates.waiting_search)
async def document_search_query(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    query = (message.text or "").strip()
    if not query:
        await message.answer("Kata kunci tidak boleh kosong.")
        return
    await state.clear()
    await _show_documents(message, session, db_user, query)


@router.callback_query(F.data.startswith("document_detail:"))
async def document_detail(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    document_id = int(callback.data.split(":")[1])
    try:
        document = await DocumentService(session).get_document(document_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    text = (
        f"📄 <b>{quote(document.original_name)}</b>\n"
        f"🎓 Semester: {quote(document.semester)}\n"
        f"📚 Mata kuliah: {quote(document.mata_kuliah)}\n"
        f"🗂️ Kategori: {quote(document.category)}\n"
        f"💾 Ukuran: {document.file_size / (1024 * 1024):.2f} MB"
    )
    await safe_edit_or_send(callback, text, document_detail_keyboard(document.id))
    await callback.answer()


@router.callback_query(F.data.startswith("document_download:"))
async def document_download(callback: CallbackQuery, session: AsyncSession, db_user: User, bot: Bot) -> None:
    document_id = int(callback.data.split(":")[1])
    try:
        document = await DocumentService(session).get_document(document_id, db_user.id)
        path = Path(document.storage_path)
        if not path.is_file():
            await callback.answer("File tidak ditemukan di penyimpanan.", show_alert=True)
            return
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=FSInputFile(path, filename=document.original_name),
        )
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("File dikirim.")


@router.callback_query(F.data.startswith("document_rename:"))
async def document_rename_start(callback: CallbackQuery, state: FSMContext) -> None:
    document_id = int(callback.data.split(":")[1])
    await state.update_data(rename_document_id=document_id)
    await state.set_state(DocumentStates.waiting_rename)
    await safe_answer(callback, "Ketik nama baru beserta ekstensi file (contoh: pertemuan-1.pdf):")
    await callback.answer()


@router.message(DocumentStates.waiting_rename)
async def document_rename_finish(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    data = await state.get_data()
    try:
        document = await DocumentService(session).rename_document(
            data["rename_document_id"], db_user.id, message.text or ""
        )
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}")
        return
    await state.clear()
    await message.answer(f"✅ Dokumen diubah menjadi <b>{quote(document.original_name)}</b>.")
    await _show_documents(message, session, db_user)


@router.callback_query(F.data.startswith("document_delete:"))
async def document_delete(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    document_id = int(callback.data.split(":")[1])
    try:
        await DocumentService(session).delete_document(document_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Dokumen dihapus 🗑️")
    await _show_documents(callback, session, db_user)
