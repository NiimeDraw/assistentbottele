"""Inline Keyboard untuk fitur Kalender Akademik."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.academic_event import EVENT_TYPE_EMOJI, AcademicEvent, EventTypeEnum

BULAN_ID = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def event_type_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for event_type in EventTypeEnum:
        emoji = EVENT_TYPE_EMOJI.get(event_type, "")
        builder.button(
            text=f"{emoji} {event_type.value}".strip(),
            callback_data=f"akad_tipe:{event_type.value}",
        )
    builder.adjust(2)
    return builder.as_markup()


def academic_list_keyboard(
    events: list[AcademicEvent], year: int, month: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for e in events:
        emoji = EVENT_TYPE_EMOJI.get(e.event_type, "")
        label = f"{emoji} {e.start_date.strftime('%d/%m')} — {e.title}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"akad_detail:{e.id}"))

    # Navigasi bulan sebelumnya / berikutnya
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    builder.row(
        InlineKeyboardButton(text="◀️ Bulan Lalu", callback_data=f"akad_bulan:{prev_year}-{prev_month:02d}"),
        InlineKeyboardButton(text="Bulan Depan ▶️", callback_data=f"akad_bulan:{next_year}-{next_month:02d}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Cari Event", callback_data="akad_cari"),
        InlineKeyboardButton(text="➕ Tambah Event", callback_data="akad_add"),
    )
    return builder.as_markup()


def academic_detail_keyboard(event_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑️ Hapus", callback_data=f"akad_delete:{event_id}"),
        InlineKeyboardButton(text="⬅️ Kembali", callback_data="akad_back"),
    )
    return builder.as_markup()


def academic_search_result_keyboard(events: list[AcademicEvent]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for e in events:
        emoji = EVENT_TYPE_EMOJI.get(e.event_type, "")
        label = f"{emoji} {e.start_date.strftime('%d/%m/%Y')} — {e.title}"
        builder.row(InlineKeyboardButton(text=label, callback_data=f"akad_detail:{e.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ Kembali", callback_data="akad_back"))
    return builder.as_markup()