"""
Handler untuk Dashboard utama (tombol inline yang muncul setelah /start).
Menangkap seluruh callback berpola "dashboard:<nama_fitur>" dan meneruskan
ke fitur terkait, atau menampilkan placeholder untuk fitur yang belum dibuat.
"""
from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.states import AIStates
from app.keyboards.schedule_kb import schedule_list_keyboard
from app.keyboards.task_kb import task_list_keyboard
from app.models.user import User
from app.services.schedule_service import ScheduleService
from app.services.task_service import TaskService
from app.utils.logger import get_logger
from aiogram.fsm.context import FSMContext

# Import fungsi render teks yang sudah ada di masing-masing handler,
# supaya format tampilannya konsisten dan tidak duplikasi kode.
from app.handlers.task_handlers import _render_task_list_text
from app.handlers.schedule_handlers import _render_schedule_list_text

logger = get_logger(__name__)
router = Router(name="dashboard")

# Fitur yang belum diimplementasikan — tampilkan placeholder yang ramah,
# bukan diam saja (silent) seperti sebelumnya.
_PLACEHOLDER_FEATURES = {
    "nilai": "📈 Nilai",
    "keuangan": "💰 Keuangan",
    "dokumen": "📂 Dokumen",
    "pengaturan": "⚙️ Pengaturan",
}


@router.callback_query(F.data == "dashboard:tugas")
async def dashboard_tugas(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = TaskService(session)
    tasks = await service.list_tasks(db_user.id)
    if callback.message:
        await callback.message.answer(
            await _render_task_list_text(tasks), reply_markup=task_list_keyboard(tasks)
        )
    await callback.answer()


@router.callback_query(F.data == "dashboard:jadwal")
async def dashboard_jadwal(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = ScheduleService(session)
    schedules = await service.list_schedules(db_user.id)
    if callback.message:
        await callback.message.answer(
            _render_schedule_list_text(schedules), reply_markup=schedule_list_keyboard(schedules)
        )
    await callback.answer()


@router.callback_query(F.data == "dashboard:ai")
async def dashboard_ai(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AIStates.waiting_question)
    if callback.message:
        await callback.message.answer(
            "🤖 Silakan ketik pertanyaan akademikmu. Ketik /cancel untuk kembali ke menu."
        )
    await callback.answer()


@router.callback_query(F.data.in_({f"dashboard:{key}" for key in _PLACEHOLDER_FEATURES}))
async def dashboard_placeholder(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer()
        return
    key = callback.data.split(":", 1)[1]
    label = _PLACEHOLDER_FEATURES.get(key, key.capitalize())
    await callback.answer(f"Fitur {label} belum tersedia. Segera hadir! 🚧", show_alert=True)