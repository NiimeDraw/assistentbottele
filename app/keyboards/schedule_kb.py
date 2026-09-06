"""Inline Keyboard untuk fitur Jadwal Kuliah."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.schedule import HariEnum, Schedule


def hari_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for hari in HariEnum:
        builder.button(text=hari.value, callback_data=f"schedule_hari:{hari.value}")
    builder.adjust(3)
    return builder.as_markup()


def schedule_list_keyboard(schedules: list[Schedule]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in schedules:
        label = f"{s.hari.value} {s.jam_mulai.strftime('%H:%M')} - {s.mata_kuliah}"
        builder.row(
            InlineKeyboardButton(text=label, callback_data=f"schedule_detail:{s.id}")
        )
    builder.row(
        InlineKeyboardButton(text="📅 Lihat Hari Ini", callback_data="schedule_today"),
        InlineKeyboardButton(text="📆 Lihat Minggu Ini", callback_data="schedule_week"),
    )
    builder.row(InlineKeyboardButton(text="➕ Tambah Jadwal", callback_data="schedule_add"))
    return builder.as_markup()


def reminder_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="30 menit sebelum", callback_data="reminder:30"),
        InlineKeyboardButton(text="15 menit sebelum", callback_data="reminder:15"),
        InlineKeyboardButton(text="5 menit sebelum", callback_data="reminder:5"),
    )
    builder.row(InlineKeyboardButton(text="Tidak ada", callback_data="reminder:0"))
    return builder.as_markup()


def schedule_detail_keyboard(schedule_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Edit", callback_data=f"schedule_edit:{schedule_id}"),
        InlineKeyboardButton(text="🗑️ Hapus", callback_data=f"schedule_delete:{schedule_id}"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Kembali", callback_data="schedule_back"))
    return builder.as_markup()


def schedule_edit_menu_keyboard(schedule_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Mata Kuliah", callback_data=f"sched_edit_field:{schedule_id}:matkul"),
    )
    builder.row(
        InlineKeyboardButton(text="🗓️ Hari", callback_data=f"sched_edit_field:{schedule_id}:hari"),
        InlineKeyboardButton(text="⏰ Jam Kuliah", callback_data=f"sched_edit_field:{schedule_id}:jam"),
    )
    builder.row(
        InlineKeyboardButton(text="🚪 Ruangan", callback_data=f"sched_edit_field:{schedule_id}:ruangan"),
        InlineKeyboardButton(text="👨‍🏫 Dosen", callback_data=f"sched_edit_field:{schedule_id}:dosen"),
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Pengingat", callback_data=f"sched_edit_field:{schedule_id}:reminder"),
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Selesai / Kembali", callback_data=f"schedule_detail:{schedule_id}")
    )
    return builder.as_markup()


def edit_hari_selection_keyboard(schedule_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for hari in HariEnum:
        builder.button(text=hari.value, callback_data=f"sched_set_hari:{schedule_id}:{hari.value}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="⬅️ Batal", callback_data=f"schedule_edit:{schedule_id}"))
    return builder.as_markup()


def edit_reminder_selection_keyboard(schedule_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="30 menit sebelum", callback_data=f"sched_set_rem:{schedule_id}:30"),
        InlineKeyboardButton(text="15 menit sebelum", callback_data=f"sched_set_rem:{schedule_id}:15"),
        InlineKeyboardButton(text="5 menit sebelum", callback_data=f"sched_set_rem:{schedule_id}:5"),
    )
    builder.row(InlineKeyboardButton(text="Tidak ada", callback_data=f"sched_set_rem:{schedule_id}:0"))
    builder.row(InlineKeyboardButton(text="⬅️ Batal", callback_data=f"schedule_edit:{schedule_id}"))
    return builder.as_markup()

