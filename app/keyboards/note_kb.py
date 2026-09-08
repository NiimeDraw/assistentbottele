"""Inline Keyboard untuk fitur Catatan."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.note import Note
from app.keyboards.dashboard_kb import dashboard_button


def note_list_keyboard(notes: list[Note]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for note in notes:
        builder.row(
            InlineKeyboardButton(text=f"📄 {note.title}", callback_data=f"note_detail:{note.id}")
        )
    builder.row(InlineKeyboardButton(text="➕ Tambah Catatan", callback_data="note_add"))
    builder.row(dashboard_button())
    return builder.as_markup()


def note_detail_keyboard(note_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑️ Hapus", callback_data=f"note_delete:{note_id}"),
        InlineKeyboardButton(text="⬅️ Kembali", callback_data="note_back"),
    )
    return builder.as_markup()
