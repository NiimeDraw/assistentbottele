"""Handler untuk fitur Jadwal Kuliah: daftar, tambah, edit, hapus."""
from datetime import datetime

# pyrefly: ignore [missing-import]
from aiogram import F, Router
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext
# pyrefly: ignore [missing-import]
from app.utils.html import quote
# pyrefly: ignore [missing-import]
from aiogram.types import CallbackQuery, Message
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

# pyrefly: ignore [missing-import]
from app.handlers.states import ScheduleEditStates, ScheduleStates
# pyrefly: ignore [missing-import]
from app.keyboards.main_menu import BTN_JADWAL, main_menu_keyboard
# pyrefly: ignore [missing-import]
from app.keyboards.schedule_kb import (
    edit_hari_selection_keyboard,
    edit_reminder_selection_keyboard,
    hari_selection_keyboard,
    reminder_selection_keyboard,
    schedule_detail_keyboard,
    schedule_edit_menu_keyboard,
    schedule_list_keyboard,
)
# pyrefly: ignore [missing-import]
from app.models.schedule import HariEnum, hari_from_date
# pyrefly: ignore [missing-import]
from app.models.user import User
# pyrefly: ignore [missing-import]
from app.services.schedule_service import ScheduleService
# pyrefly: ignore [missing-import]
from app.utils.exceptions import AppError
# pyrefly: ignore [missing-import]
from app.utils.logger import get_logger
# pyrefly: ignore [missing-import]
from app.utils.telegram_helpers import safe_edit_or_send
# pyrefly: ignore [missing-import]
from app.utils.timezone_utils import now_local

logger = get_logger(__name__)
router = Router(name="schedule")


def _render_schedule_list_text(schedules) -> str:
    if not schedules:
        return "🗓️ <b>Jadwal Kuliah</b>\n\nBelum ada jadwal. Tambahkan jadwal kuliahmu!"
    lines = ["🗓️ <b>Jadwal Kuliah</b>\n"]
    for s in schedules:
        jam = f"{s.jam_mulai.strftime('%H:%M')}-{s.jam_selesai.strftime('%H:%M')}"
        ruangan = f" ({quote(s.ruangan)})" if s.ruangan else ""
        lines.append(f"• {s.hari.value} {jam} — {quote(s.mata_kuliah)}{ruangan}")
    return "\n".join(lines)


def _render_schedule_edit_text(s) -> str:
    ruangan_str = quote(s.ruangan) if s.ruangan else "-"
    dosen_str = quote(s.dosen) if s.dosen else "-"
    return (
        f"✏️ <b>Edit Jadwal: {quote(s.mata_kuliah)}</b>\n\n"
        f"Hari: {s.hari.value}\n"
        f"Jam: {s.jam_mulai.strftime('%H:%M')} - {s.jam_selesai.strftime('%H:%M')}\n"
        f"Ruangan: {ruangan_str}\n"
        f"Dosen: {dosen_str}\n"
        f"Pengingat: {str(s.reminder_minutes) + ' menit sebelum' if s.reminder_minutes else '-'}\n\n"
        "Pilih bagian yang ingin diubah:"
    )


@router.message(F.text == BTN_JADWAL)
async def show_schedule_menu(message: Message, session: AsyncSession, db_user: User) -> None:
    service = ScheduleService(session)
    schedules = await service.list_schedules(db_user.id)
    await message.answer(_render_schedule_list_text(schedules), reply_markup=schedule_list_keyboard(schedules))


@router.callback_query(F.data == "schedule_back")
async def schedule_back(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = ScheduleService(session)
    schedules = await service.list_schedules(db_user.id)
    await safe_edit_or_send(
        callback, _render_schedule_list_text(schedules), schedule_list_keyboard(schedules)
    )
    await callback.answer()


@router.callback_query(F.data == "schedule_add")
async def schedule_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()  # pastikan tidak membawa sisa data "editing_id" dari alur edit sebelumnya
    await state.set_state(ScheduleStates.waiting_mata_kuliah)
    if callback.message:
        await callback.message.answer("Masukkan <b>nama mata kuliah</b> (ketik /cancel untuk membatalkan):")
    await callback.answer()


@router.message(ScheduleStates.waiting_mata_kuliah)
async def schedule_add_mata_kuliah(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Nama mata kuliah tidak boleh kosong. Coba lagi:")
        return
    await state.update_data(mata_kuliah=message.text.strip())
    await state.set_state(ScheduleStates.waiting_hari)
    await message.answer("Pilih <b>hari</b>:", reply_markup=hari_selection_keyboard())


@router.callback_query(ScheduleStates.waiting_hari, F.data.startswith("schedule_hari:"))
async def schedule_add_hari(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer()
        return
    hari = callback.data.split(":", 1)[1]
    await state.update_data(hari=hari)
    await state.set_state(ScheduleStates.waiting_jam_mulai)
    if callback.message:
        await callback.message.answer("Masukkan <b>jam mulai</b> (format HH:MM), contoh: 08:00")
    await callback.answer()


@router.message(ScheduleStates.waiting_jam_mulai)
async def schedule_add_jam_mulai(message: Message, state: FSMContext) -> None:
    await state.update_data(jam_mulai=message.text or "")
    await state.set_state(ScheduleStates.waiting_jam_selesai)
    await message.answer("Masukkan <b>jam selesai</b> (format HH:MM), contoh: 10:00")


@router.message(ScheduleStates.waiting_jam_selesai)
async def schedule_add_jam_selesai(message: Message, state: FSMContext) -> None:
    await state.update_data(jam_selesai=message.text or "")
    await state.set_state(ScheduleStates.waiting_ruangan)
    await message.answer("Masukkan <b>ruangan</b> (opsional, ketik - untuk lewati):")


@router.message(ScheduleStates.waiting_ruangan)
async def schedule_add_ruangan(message: Message, state: FSMContext) -> None:
    """Menyimpan ruangan, lalu lanjut menanyakan dosen."""
    await state.update_data(ruangan=(message.text or "").strip())
    await state.set_state(ScheduleStates.waiting_dosen)
    await message.answer("Masukkan <b>dosen</b> (opsional, ketik - untuk lewati):")


@router.message(ScheduleStates.waiting_dosen)
async def schedule_add_dosen(message: Message, state: FSMContext) -> None:
    await state.update_data(dosen=(message.text or "").strip())
    await state.set_state(ScheduleStates.waiting_reminder)
    await message.answer("Pilih pengingat sebelum kuliah:", reply_markup=reminder_selection_keyboard())


@router.callback_query(ScheduleStates.waiting_reminder, F.data.startswith("reminder:"))
async def schedule_add_reminder(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    if not callback.data:
        await callback.answer()
        return
    reminder_raw = int(callback.data.split(":", 1)[1])
    data = await state.get_data()
    ruangan = None if (data.get("ruangan") or "-") == "-" else data.get("ruangan")
    dosen = None if (data.get("dosen") or "-") == "-" else data.get("dosen")
    reminder_minutes = reminder_raw if reminder_raw > 0 else None

    service = ScheduleService(session)

    try:
        await service.create_schedule(
            user_id=db_user.id,
            mata_kuliah=data["mata_kuliah"],
            hari=data["hari"],
            jam_mulai_raw=data["jam_mulai"],
            jam_selesai_raw=data["jam_selesai"],
            ruangan=ruangan,
            dosen=dosen,
            reminder_minutes=reminder_minutes,
        )
        msg = "✅ Jadwal berhasil ditambahkan!"
    except AppError as exc:
        await state.set_state(ScheduleStates.waiting_jam_mulai)
        if callback.message:
            await callback.message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang jam mulai:")
        await callback.answer()
        return

    await state.clear()
    schedules = await service.list_schedules(db_user.id)
    if callback.message:
        await callback.message.answer(msg, reply_markup=main_menu_keyboard())
        await callback.message.answer(
            _render_schedule_list_text(schedules), reply_markup=schedule_list_keyboard(schedules)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("schedule_detail:"))
async def schedule_detail(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    if not callback.data:
        await callback.answer()
        return
    schedule_id = int(callback.data.split(":")[1])
    service = ScheduleService(session)
    try:
        s = await service.get_schedule(schedule_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    ruangan_str = quote(s.ruangan) if s.ruangan else "-"
    dosen_str = quote(s.dosen) if s.dosen else "-"
    text = (
        f"🗓️ <b>{quote(s.mata_kuliah)}</b>\n\n"
        f"Hari: {s.hari.value}\n"
        f"Jam: {s.jam_mulai.strftime('%H:%M')} - {s.jam_selesai.strftime('%H:%M')}\n"
        f"Ruangan: {ruangan_str}\n"
        f"Dosen: {dosen_str}\n"
        f"Pengingat: {str(s.reminder_minutes) + ' menit sebelum' if s.reminder_minutes else '-'}"
    )
    await safe_edit_or_send(callback, text, schedule_detail_keyboard(s.id))
    await callback.answer()


@router.callback_query(F.data.startswith("schedule_delete:"))
async def schedule_delete(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    if not callback.data:
        await callback.answer()
        return
    schedule_id = int(callback.data.split(":")[1])
    service = ScheduleService(session)
    try:
        await service.delete_schedule(schedule_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Jadwal dihapus 🗑️")
    schedules = await service.list_schedules(db_user.id)
    await safe_edit_or_send(
        callback, _render_schedule_list_text(schedules), schedule_list_keyboard(schedules)
    )


@router.callback_query(F.data == "schedule_today")
async def schedule_today(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    hari_hari_ini = hari_from_date(now_local().date())

    service = ScheduleService(session)
    all_schedules = await service.list_schedules(db_user.id)
    schedules_today = [s for s in all_schedules if s.hari == hari_hari_ini]

    if not schedules_today:
        await safe_edit_or_send(
            callback, "Tidak ada jadwal untuk hari ini.", schedule_list_keyboard(all_schedules)
        )
        await callback.answer()
        return

    lines = ["🗓️ <b>Jadwal Hari Ini</b>\n"]
    for s in schedules_today:
        jam = f"{s.jam_mulai.strftime('%H:%M')}-{s.jam_selesai.strftime('%H:%M')}"
        ruangan = f" ({quote(s.ruangan)})" if s.ruangan else ""
        lines.append(f"• {jam} — {quote(s.mata_kuliah)}{ruangan}")

    await safe_edit_or_send(callback, "\n".join(lines), schedule_list_keyboard(all_schedules))
    await callback.answer()


@router.callback_query(F.data == "schedule_week")
async def schedule_week(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = ScheduleService(session)
    all_schedules = await service.list_schedules(db_user.id)

    if not all_schedules:
        await safe_edit_or_send(
            callback, "Belum ada jadwal untuk minggu ini.", schedule_list_keyboard(all_schedules)
        )
        await callback.answer()
        return

    grouped: dict[str, list] = {}
    for s in all_schedules:
        grouped.setdefault(s.hari.value, []).append(s)

    lines = ["🗓️ <b>Jadwal Minggu Ini</b>\n"]
    for hari in [h.value for h in HariEnum]:
        items = grouped.get(hari, [])
        if not items:
            continue
        lines.append(f"\n<b>{hari}</b>")
        for s in items:
            jam = f"{s.jam_mulai.strftime('%H:%M')}-{s.jam_selesai.strftime('%H:%M')}"
            ruangan = f" ({quote(s.ruangan)})" if s.ruangan else ""
            lines.append(f"• {jam} — {quote(s.mata_kuliah)}{ruangan}")

    await safe_edit_or_send(callback, "\n".join(lines), schedule_list_keyboard(all_schedules))
    await callback.answer()


@router.callback_query(F.data.startswith("schedule_edit:"))
async def schedule_edit(
    callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext
) -> None:
    if not callback.data:
        await callback.answer()
        return
    await state.clear()
    schedule_id = int(callback.data.split(":")[1])
    service = ScheduleService(session)
    try:
        s = await service.get_schedule(schedule_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    await safe_edit_or_send(callback, _render_schedule_edit_text(s), schedule_edit_menu_keyboard(s.id))
    await callback.answer()


@router.callback_query(F.data.startswith("sched_edit_field:"))
async def schedule_edit_field_pick(
    callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext
) -> None:
    if not callback.data:
        await callback.answer()
        return
    _, schedule_id_str, field = callback.data.split(":", 2)
    schedule_id = int(schedule_id_str)
    service = ScheduleService(session)
    try:
        s = await service.get_schedule(schedule_id, db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    if field == "matkul":
        await state.set_state(ScheduleEditStates.waiting_mata_kuliah)
        await state.update_data(schedule_id=schedule_id)
        await safe_edit_or_send(
            callback,
            f"Mata kuliah saat ini: <b>{quote(s.mata_kuliah)}</b>\n\nMasukkan <b>nama mata kuliah baru</b> (ketik /cancel untuk batal):"
        )
    elif field == "hari":
        await safe_edit_or_send(callback, "Pilih <b>hari baru</b>:", edit_hari_selection_keyboard(schedule_id))
    elif field == "jam":
        await state.set_state(ScheduleEditStates.waiting_jam_mulai)
        await state.update_data(schedule_id=schedule_id)
        current_jam = f"{s.jam_mulai.strftime('%H:%M')} - {s.jam_selesai.strftime('%H:%M')}"
        await safe_edit_or_send(
            callback,
            f"Jam kuliah saat ini: <b>{current_jam}</b>\n\nMasukkan <b>jam mulai baru</b> (format HH:MM, contoh: 08:00):"
        )
    elif field == "ruangan":
        await state.set_state(ScheduleEditStates.waiting_ruangan)
        await state.update_data(schedule_id=schedule_id)
        curr_ruang = quote(s.ruangan) if s.ruangan else "-"
        await safe_edit_or_send(
            callback,
            f"Ruangan saat ini: <b>{curr_ruang}</b>\n\nMasukkan <b>ruangan baru</b> (ketik - jika ingin dikosongkan):"
        )
    elif field == "dosen":
        await state.set_state(ScheduleEditStates.waiting_dosen)
        await state.update_data(schedule_id=schedule_id)
        curr_dosen = quote(s.dosen) if s.dosen else "-"
        await safe_edit_or_send(
            callback,
            f"Dosen saat ini: <b>{curr_dosen}</b>\n\nMasukkan <b>nama dosen baru</b> (ketik - jika ingin dikosongkan):"
        )
    elif field == "reminder":
        await safe_edit_or_send(callback, "Pilih <b>pengingat baru</b>:", edit_reminder_selection_keyboard(schedule_id))

    await callback.answer()


@router.callback_query(F.data.startswith("sched_set_hari:"))
async def schedule_edit_set_hari(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not callback.data:
        await callback.answer()
        return
    _, schedule_id_str, hari = callback.data.split(":", 2)
    schedule_id = int(schedule_id_str)
    service = ScheduleService(session)
    try:
        s = await service.update_schedule(schedule_id, db_user.id, hari=hari)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Hari berhasil diubah! ✅")
    await safe_edit_or_send(callback, _render_schedule_edit_text(s), schedule_edit_menu_keyboard(s.id))


@router.callback_query(F.data.startswith("sched_set_rem:"))
async def schedule_edit_set_reminder(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not callback.data:
        await callback.answer()
        return
    _, schedule_id_str, rem_str = callback.data.split(":", 2)
    schedule_id = int(schedule_id_str)
    rem_min = int(rem_str) if int(rem_str) > 0 else None
    service = ScheduleService(session)
    try:
        s = await service.update_schedule(schedule_id, db_user.id, reminder_minutes=rem_min)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return
    await callback.answer("Pengingat berhasil diubah! ✅")
    await safe_edit_or_send(callback, _render_schedule_edit_text(s), schedule_edit_menu_keyboard(s.id))


@router.message(ScheduleEditStates.waiting_mata_kuliah)
async def schedule_edit_save_matkul(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    if not schedule_id:
        await state.clear()
        return
    service = ScheduleService(session)
    try:
        s = await service.update_schedule(schedule_id, db_user.id, mata_kuliah=message.text or "")
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang nama mata kuliah:")
        return

    await state.clear()
    await message.answer("✅ Nama mata kuliah berhasil diperbarui!", reply_markup=main_menu_keyboard())
    await message.answer(_render_schedule_edit_text(s), reply_markup=schedule_edit_menu_keyboard(s.id))


@router.message(ScheduleEditStates.waiting_jam_mulai)
async def schedule_edit_save_jam_mulai(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        from app.utils.validators import validate_time
        validate_time(text, "Jam mulai")
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang jam mulai (format HH:MM):")
        return

    await state.update_data(jam_mulai=text)
    await state.set_state(ScheduleEditStates.waiting_jam_selesai)
    await message.answer("Masukkan <b>jam selesai baru</b> (format HH:MM, contoh: 10:00):")


@router.message(ScheduleEditStates.waiting_jam_selesai)
async def schedule_edit_save_jam_selesai(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    if not schedule_id:
        await state.clear()
        return
    jam_mulai = data.get("jam_mulai")
    jam_selesai = (message.text or "").strip()

    service = ScheduleService(session)
    try:
        s = await service.update_schedule(
            schedule_id, db_user.id, jam_mulai=jam_mulai, jam_selesai=jam_selesai
        )
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang jam selesai (format HH:MM):")
        return

    await state.clear()
    await message.answer("✅ Jam kuliah berhasil diperbarui!", reply_markup=main_menu_keyboard())
    await message.answer(_render_schedule_edit_text(s), reply_markup=schedule_edit_menu_keyboard(s.id))


@router.message(ScheduleEditStates.waiting_ruangan)
async def schedule_edit_save_ruangan(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    if not schedule_id:
        await state.clear()
        return
    ruangan = (message.text or "").strip()
    ruangan_val = None if ruangan == "-" else ruangan

    service = ScheduleService(session)
    try:
        s = await service.update_schedule(schedule_id, db_user.id, ruangan=ruangan_val)
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang ruangan:")
        return

    await state.clear()
    await message.answer("✅ Ruangan berhasil diperbarui!", reply_markup=main_menu_keyboard())
    await message.answer(_render_schedule_edit_text(s), reply_markup=schedule_edit_menu_keyboard(s.id))


@router.message(ScheduleEditStates.waiting_dosen)
async def schedule_edit_save_dosen(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    data = await state.get_data()
    schedule_id = data.get("schedule_id")
    if not schedule_id:
        await state.clear()
        return
    dosen = (message.text or "").strip()
    dosen_val = None if dosen == "-" else dosen

    service = ScheduleService(session)
    try:
        s = await service.update_schedule(schedule_id, db_user.id, dosen=dosen_val)
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}\n\nMasukkan ulang dosen:")
        return

    await state.clear()
    await message.answer("✅ Dosen berhasil diperbarui!", reply_markup=main_menu_keyboard())
    await message.answer(_render_schedule_edit_text(s), reply_markup=schedule_edit_menu_keyboard(s.id))