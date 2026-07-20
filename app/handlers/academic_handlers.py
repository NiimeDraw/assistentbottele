"""Handler untuk fitur Kalender Akademik: daftar, filter bulan, cari, tambah, hapus."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.states import AcademicStates
from app.keyboards.academic_kb import (
    BULAN_ID,
    academic_detail_keyboard,
    academic_list_keyboard,
    academic_search_result_keyboard,
    event_type_selection_keyboard,
)
from app.keyboards.main_menu import main_menu_keyboard
from app.models.academic_event import EVENT_TYPE_EMOJI
from app.models.user import User
from app.services.academic_event_service import AcademicEventService
from app.utils.exceptions import AppError
from app.utils.logger import get_logger
from app.utils.timezone_utils import now_local

logger = get_logger(__name__)
router = Router(name="academic")

BTN_AKADEMIK = "📚 Kalender Akademik"


def _render_month_header(year: int, month: int) -> str:
    return f"📅 <b>Kalender Akademik — {BULAN_ID[month]} {year}</b>\n"


def _render_event_list_text(events, year: int, month: int) -> str:
    header = _render_month_header(year, month)
    if not events:
        return header + "\nBelum ada event akademik di bulan ini."
    lines = [header]
    for e in events:
        emoji = EVENT_TYPE_EMOJI.get(e.event_type, "")
        tanggal = e.start_date.strftime("%d/%m")
        if e.end_date and e.end_date != e.start_date:
            tanggal += f" - {e.end_date.strftime('%d/%m')}"
        lines.append(f"{emoji} <b>{e.event_type.value}</b> — {e.title} ({tanggal})")
    return "\n".join(lines)


def _render_event_detail_text(e) -> str:
    emoji = EVENT_TYPE_EMOJI.get(e.event_type, "")
    tanggal = e.start_date.strftime("%d-%m-%Y")
    if e.end_date and e.end_date != e.start_date:
        tanggal += f" s.d. {e.end_date.strftime('%d-%m-%Y')}"
    reminder_text = (
        f"{e.reminder_days_before} hari sebelum acara" if e.reminder_days_before is not None else "-"
    )
    return (
        f"{emoji} <b>{e.title}</b>\n\n"
        f"Jenis: {e.event_type.value}\n"
        f"Tanggal: {tanggal}\n"
        f"Lokasi: {e.location or '-'}\n"
        f"Deskripsi: {e.description or '-'}\n"
        f"Pengingat: {reminder_text}"
    )


async def _safe_edit_or_send(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=reply_markup)
    elif callback.bot is not None:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=reply_markup)


async def _safe_answer(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    if isinstance(callback.message, Message):
        await callback.message.answer(text, reply_markup=reply_markup)
    elif callback.bot is not None:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=reply_markup)


async def _show_month(callback: CallbackQuery, session: AsyncSession, db_user: User, year: int, month: int) -> None:
    service = AcademicEventService(session)
    events = await service.list_events_by_month(db_user.id, year, month)
    await _safe_edit_or_send(
        callback, _render_event_list_text(events, year, month), academic_list_keyboard(events, year, month)
    )


@router.message(F.text == BTN_AKADEMIK)
async def show_academic_menu(message: Message, session: AsyncSession, db_user: User) -> None:
    today = now_local().date()
    service = AcademicEventService(session)
    events = await service.list_events_by_month(db_user.id, today.year, today.month)
    await message.answer(
        _render_event_list_text(events, today.year, today.month),
        reply_markup=academic_list_keyboard(events, today.year, today.month),
    )


@router.callback_query(F.data == "dashboard:akademik")
async def dashboard_open_academic(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    today = now_local().date()
    await _show_month(callback, session, db_user, today.year, today.month)
    await callback.answer()


@router.callback_query(F.data == "akad_back")
async def akad_back(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    today = now_local().date()
    await _show_month(callback, session, db_user, today.year, today.month)
    await callback.answer()


@router.callback_query(F.data.startswith("akad_bulan:"))
async def akad_bulan(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    if not callback.data:
        await callback.answer()
        return
    year_str, month_str = callback.data.split(":", 1)[1].split("-")
    await _show_month(callback, session, db_user, int(year_str), int(month_str))
    await callback.answer()


# ---------- Alur tambah event ----------

@router.callback_query(F.data == "akad_add")
async def akad_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AcademicStates.waiting_title)
    await _safe_answer(callback, "Masukkan <b>judul event</b> (ketik /cancel untuk membatalkan):")
    await callback.answer()


@router.message(AcademicStates.waiting_title)
async def akad_add_title(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Judul tidak boleh kosong. Coba lagi:")
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AcademicStates.waiting_type)
    await message.answer("Pilih <b>jenis event</b>:", reply_markup=event_type_selection_keyboard())


@router.callback_query(AcademicStates.waiting_type, F.data.startswith("akad_tipe:"))
async def akad_add_type(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    event_type = callback.data.split(":", 1)[1]
    await state.update_data(event_type=event_type)
    await state.set_state(AcademicStates.waiting_start_date)
    await _safe_answer(
        callback, "Masukkan <b>tanggal mulai</b> (format DD-MM-YYYY), contoh: 25-08-2026"
    )
    await callback.answer()


@router.message(AcademicStates.waiting_start_date)
async def akad_add_start_date(message: Message, state: FSMContext) -> None:
    await state.update_data(start_date=message.text or "")
    await state.set_state(AcademicStates.waiting_end_date)
    await message.answer(
        "Masukkan <b>tanggal selesai</b> (format DD-MM-YYYY), atau ketik - kalau cuma satu hari:"
    )


@router.message(AcademicStates.waiting_end_date)
async def akad_add_end_date(message: Message, state: FSMContext) -> None:
    await state.update_data(end_date=message.text or "")
    await state.set_state(AcademicStates.waiting_location)
    await message.answer("Masukkan <b>lokasi</b> (opsional, ketik - untuk lewati):")


@router.message(AcademicStates.waiting_location)
async def akad_add_location(message: Message, state: FSMContext) -> None:
    location = None if (message.text or "").strip() == "-" else (message.text or "").strip()
    await state.update_data(location=location)
    await state.set_state(AcademicStates.waiting_description)
    await message.answer("Masukkan <b>deskripsi</b> (opsional, ketik - untuk lewati):")


@router.message(AcademicStates.waiting_description)
async def akad_add_description(message: Message, state: FSMContext) -> None:
    description = None if (message.text or "").strip() == "-" else (message.text or "").strip()
    await state.update_data(description=description)
    await state.set_state(AcademicStates.waiting_reminder_days)
    await message.answer(
        "Ingatkan berapa <b>hari sebelum</b> acara? (masukkan angka, atau ketik - untuk tanpa pengingat):"
    )


@router.message(AcademicStates.waiting_reminder_days)
async def akad_add_reminder_days(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    service = AcademicEventService(session)
    try:
        await service.create_event(
            user_id=db_user.id,
            title=data["title"],
            event_type_raw=data["event_type"],
            start_date_raw=data["start_date"],
            end_date_raw=data.get("end_date"),
            location=data.get("location"),
            description=data.get("description"),
            reminder_days_before_raw=message.text or "-",
        )
    except AppError as exc:
        await state.set_state(AcademicStates.waiting_start_date)
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang tanggal mulai:")
        return

    await state.clear()
    today = now_local().date()
    events = await service.list_events_by_month(db_user.id, today.year, today.month)
    await message.answer("✅ Event berhasil ditambahkan!", reply_markup=main_menu_keyboard())
    await message.answer(
        _render_event_list_text(events, today.year, today.month),
        reply_markup=academic_list_keyboard(events, today.year, today.month),
    )


# ---------- Detail & hapus ----------

@router.callback_query(F.data.startswith("akad_detail:"))
async def akad_detail(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    if not callback.data:
        await callback.answer()
        return
    event_id = int(callback.data.split(":")[1])
    service = AcademicEventService(session)
    try:
        event = await service.get_event(event_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await _safe_edit_or_send(
        callback, _render_event_detail_text(event), academic_detail_keyboard(event.id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("akad_delete:"))
async def akad_delete(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    if not callback.data:
        await callback.answer()
        return
    event_id = int(callback.data.split(":")[1])
    service = AcademicEventService(session)
    try:
        await service.delete_event(event_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Event dihapus 🗑️")
    today = now_local().date()
    await _show_month(callback, session, db_user, today.year, today.month)


# ---------- Cari event ----------

@router.callback_query(F.data == "akad_cari")
async def akad_search_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AcademicStates.waiting_search_keyword)
    await _safe_answer(callback, "Ketik <b>kata kunci</b> judul event yang ingin dicari:")
    await callback.answer()


@router.message(AcademicStates.waiting_search_keyword)
async def akad_search_result(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    service = AcademicEventService(session)
    try:
        events = await service.search_events(db_user.id, message.text or "")
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}\n\nCoba masukkan kata kunci lain:")
        return

    await state.clear()
    if not events:
        await message.answer(
            "🔍 Tidak ada event yang cocok dengan kata kunci itu.", reply_markup=main_menu_keyboard()
        )
        return

    lines = [f"🔍 <b>Hasil pencarian:</b> \"{message.text}\"\n"]
    for e in events:
        emoji = EVENT_TYPE_EMOJI.get(e.event_type, "")
        lines.append(f"{emoji} {e.start_date.strftime('%d/%m/%Y')} — {e.title}")
    await message.answer("\n".join(lines), reply_markup=academic_search_result_keyboard(events))