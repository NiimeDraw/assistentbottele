"""Handler untuk fitur Jadwal Kuliah: daftar, tambah, edit, hapus."""
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.handlers.states import ScheduleStates
from app.keyboards.main_menu import BTN_JADWAL, main_menu_keyboard
from app.keyboards.schedule_kb import (
    hari_selection_keyboard,
    reminder_selection_keyboard,
    schedule_detail_keyboard,
    schedule_list_keyboard,
)
from app.models.schedule import HariEnum
from app.models.user import User
from app.services.schedule_service import ScheduleService
from app.utils.exceptions import AppError
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="schedule")

_HARI_MAPPING_EN_TO_ID = {
    "Monday": HariEnum.SENIN.value,
    "Tuesday": HariEnum.SELASA.value,
    "Wednesday": HariEnum.RABU.value,
    "Thursday": HariEnum.KAMIS.value,
    "Friday": HariEnum.JUMAT.value,
    "Saturday": HariEnum.SABTU.value,
    "Sunday": HariEnum.MINGGU.value,
}


def _render_schedule_list_text(schedules) -> str:
    if not schedules:
        return "🗓️ <b>Jadwal Kuliah</b>\n\nBelum ada jadwal. Tambahkan jadwal kuliahmu!"
    lines = ["🗓️ <b>Jadwal Kuliah</b>\n"]
    for s in schedules:
        jam = f"{s.jam_mulai.strftime('%H:%M')}-{s.jam_selesai.strftime('%H:%M')}"
        lines.append(f"• {s.hari.value} {jam} — {s.mata_kuliah} ({s.ruangan or '-'})")
    return "\n".join(lines)


async def _safe_edit_or_send(callback: CallbackQuery, text: str, reply_markup=None) -> None:
    """Edit pesan callback jika memungkinkan, kalau tidak fallback kirim pesan baru.

    Menggunakan isinstance check (bukan cuma truthy check) karena
    callback.message bertipe Message | InaccessibleMessage | None di aiogram 3.x.
    InaccessibleMessage tidak punya method edit_text/answer, jadi harus
    dibedakan secara eksplisit agar aman dari AttributeError sekaligus
    lolos pengecekan tipe statis (Pylance).
    """
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=reply_markup)
    elif callback.bot is not None:
        await callback.bot.send_message(callback.from_user.id, text, reply_markup=reply_markup)


@router.message(F.text == BTN_JADWAL)
async def show_schedule_menu(message: Message, session: AsyncSession, db_user: User) -> None:
    service = ScheduleService(session)
    schedules = await service.list_schedules(db_user.id)
    await message.answer(_render_schedule_list_text(schedules), reply_markup=schedule_list_keyboard(schedules))


@router.callback_query(F.data == "schedule_back")
async def schedule_back(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = ScheduleService(session)
    schedules = await service.list_schedules(db_user.id)
    await _safe_edit_or_send(
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
    editing_id = data.get("editing_id")

    try:
        if editing_id:
            await service.update_schedule(
                editing_id,
                db_user.id,
                mata_kuliah=data["mata_kuliah"],
                hari=data["hari"],
                jam_mulai=data["jam_mulai"],
                jam_selesai=data["jam_selesai"],
                ruangan=ruangan,
                dosen=dosen,
                reminder_minutes=reminder_minutes,
            )
            msg = "✅ Jadwal berhasil diperbarui!"
        else:
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

    text = (
        f"🗓️ <b>{s.mata_kuliah}</b>\n\n"
        f"Hari: {s.hari.value}\n"
        f"Jam: {s.jam_mulai.strftime('%H:%M')} - {s.jam_selesai.strftime('%H:%M')}\n"
        f"Ruangan: {s.ruangan or '-'}\n"
        f"Dosen: {s.dosen or '-'}\n"
        f"Pengingat: {str(s.reminder_minutes) + ' menit sebelum' if s.reminder_minutes else '-'}"
    )
    await _safe_edit_or_send(callback, text, schedule_detail_keyboard(s.id))
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
    await _safe_edit_or_send(
        callback, _render_schedule_list_text(schedules), schedule_list_keyboard(schedules)
    )


@router.callback_query(F.data == "schedule_today")
async def schedule_today(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    today_name = datetime.now().strftime("%A")
    hari_value = _HARI_MAPPING_EN_TO_ID.get(today_name)

    service = ScheduleService(session)
    all_schedules = await service.list_schedules(db_user.id)
    schedules_today = [s for s in all_schedules if s.hari.value == hari_value]

    if not schedules_today:
        await _safe_edit_or_send(
            callback, "Tidak ada jadwal untuk hari ini.", schedule_list_keyboard(all_schedules)
        )
        await callback.answer()
        return

    lines = ["🗓️ <b>Jadwal Hari Ini</b>\n"]
    for s in schedules_today:
        jam = f"{s.jam_mulai.strftime('%H:%M')}-{s.jam_selesai.strftime('%H:%M')}"
        lines.append(f"• {jam} — {s.mata_kuliah} ({s.ruangan or '-'})")

    await _safe_edit_or_send(callback, "\n".join(lines), schedule_list_keyboard(all_schedules))
    await callback.answer()


@router.callback_query(F.data == "schedule_week")
async def schedule_week(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    service = ScheduleService(session)
    all_schedules = await service.list_schedules(db_user.id)

    if not all_schedules:
        await _safe_edit_or_send(
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
            lines.append(f"• {jam} — {s.mata_kuliah} ({s.ruangan or '-'})")

    await _safe_edit_or_send(callback, "\n".join(lines), schedule_list_keyboard(all_schedules))
    await callback.answer()


@router.callback_query(F.data.startswith("schedule_edit:"))
async def schedule_edit(
    callback: CallbackQuery, session: AsyncSession, db_user: User, state: FSMContext
) -> None:
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

    # Mulai alur edit: simpan id dan nilai saat ini di state
    await state.update_data(
        editing_id=s.id,
        mata_kuliah=s.mata_kuliah,
        hari=s.hari.value,
        jam_mulai=s.jam_mulai.strftime("%H:%M"),
        jam_selesai=s.jam_selesai.strftime("%H:%M"),
        ruangan=s.ruangan or "-",
        dosen=s.dosen or "-",
    )
    await state.set_state(ScheduleStates.waiting_mata_kuliah)
    if callback.message:
        await callback.message.answer("(Edit) Masukkan <b>nama mata kuliah</b> (ketik /cancel untuk membatalkan):")
    await callback.answer()