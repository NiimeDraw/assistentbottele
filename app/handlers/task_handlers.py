"""Handler untuk fitur Tugas (Task): daftar, tambah, tandai selesai, hapus."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.states import TaskStates
from app.keyboards.main_menu import BTN_TUGAS, main_menu_keyboard
from app.keyboards.task_kb import confirm_delete_keyboard, task_detail_keyboard, task_list_keyboard
from app.models.user import User
from app.services.task_service import TaskService
from app.utils.exceptions import AppError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="task")


async def _render_task_list_text(tasks) -> str:
    if not tasks:
        return "📚 <b>Daftar Tugas</b>\n\nBelum ada tugas. Yuk tambahkan tugas pertamamu!"
    lines = ["📚 <b>Daftar Tugas</b>\n"]
    for t in tasks:
        status = "✅" if t.is_done else "⏳"
        lines.append(f"{status} {t.title} — {t.deadline.strftime('%d-%m-%Y %H:%M')}")
    return "\n".join(lines)


@router.message(F.text == BTN_TUGAS)
async def show_task_menu(message: Message, session: AsyncSession, db_user: User) -> None:
    service = TaskService(session)
    tasks = await service.list_tasks(db_user.id)
    await message.answer(await _render_task_list_text(tasks), reply_markup=task_list_keyboard(tasks))


@router.callback_query(F.data == "task_back")
async def task_back(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = TaskService(session)
    tasks = await service.list_tasks(db_user.id)
    await callback.message.edit_text(await _render_task_list_text(tasks), reply_markup=task_list_keyboard(tasks))
    await callback.answer()


@router.callback_query(F.data == "task_add")
async def task_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TaskStates.waiting_title)
    await callback.message.answer(
        "Masukkan <b>judul tugas</b> (ketik /cancel untuk membatalkan):"
    )
    await callback.answer()


@router.message(TaskStates.waiting_title)
async def task_add_title(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Judul tidak boleh kosong. Masukkan judul tugas:")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(TaskStates.waiting_deadline)
    await message.answer(
        "Masukkan <b>deadline</b> dengan format:\n<code>DD-MM-YYYY HH:MM</code>\nContoh: 25-12-2026 23:59"
    )


@router.message(TaskStates.waiting_deadline)
async def task_add_deadline(message: Message, state: FSMContext) -> None:
    await state.update_data(deadline_raw=message.text or "")
    await state.set_state(TaskStates.waiting_description)
    await message.answer("Masukkan <b>deskripsi</b> tugas (opsional, ketik - untuk lewati):")


@router.message(TaskStates.waiting_description)
async def task_add_description(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    description = None if (message.text or "").strip() == "-" else message.text

    service = TaskService(session)
    try:
        await service.create_task(
            user_id=db_user.id,
            title=data["title"],
            deadline_raw=data["deadline_raw"],
            description=description,
        )
    except AppError as exc:
        # Kembali ke tahap deadline agar user bisa memperbaiki input
        await state.set_state(TaskStates.waiting_deadline)
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang deadline:")
        return

    await state.clear()
    tasks = await service.list_tasks(db_user.id)
    await message.answer("✅ Tugas berhasil ditambahkan!", reply_markup=main_menu_keyboard())
    await message.answer(await _render_task_list_text(tasks), reply_markup=task_list_keyboard(tasks))


@router.callback_query(F.data.startswith("task_detail:"))
async def task_detail(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    task_id = int(callback.data.split(":")[1])
    service = TaskService(session)
    try:
        task = await service.get_task(task_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    status = "Selesai ✅" if task.is_done else "Belum selesai ⏳"
    text = (
        f"📌 <b>{task.title}</b>\n\n"
        f"Deadline: {task.deadline.strftime('%d-%m-%Y %H:%M')}\n"
        f"Status: {status}\n"
        f"Deskripsi: {task.description or '-'}"
    )
    await callback.message.edit_text(text, reply_markup=task_detail_keyboard(task.id, task.is_done))
    await callback.answer()


@router.callback_query(F.data.startswith("task_done:"))
async def task_mark_done(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    task_id = int(callback.data.split(":")[1])
    service = TaskService(session)
    try:
        await service.mark_done(task_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Tugas ditandai selesai ✅")
    await task_detail(callback, session, db_user)


@router.callback_query(F.data.startswith("task_delete:"))
async def task_delete_prompt(callback: CallbackQuery) -> None:
    task_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "Yakin ingin menghapus tugas ini?", reply_markup=confirm_delete_keyboard(task_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task_delete_confirm:"))
async def task_delete_confirm(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    task_id = int(callback.data.split(":")[1])
    service = TaskService(session)
    try:
        await service.delete_task(task_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Tugas dihapus 🗑️")
    tasks = await service.list_tasks(db_user.id)
    await callback.message.edit_text(await _render_task_list_text(tasks), reply_markup=task_list_keyboard(tasks))
