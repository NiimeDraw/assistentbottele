"""Inline Keyboard untuk fitur Tugas."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.task import Task


def task_list_keyboard(tasks: list[Task]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        status = "✅" if task.is_done else "⏳"
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {task.title}",
                callback_data=f"task_detail:{task.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Tambah Tugas", callback_data="task_add"))
    return builder.as_markup()


def task_detail_keyboard(task_id: int, is_done: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if not is_done:
        builder.row(
            InlineKeyboardButton(text="✅ Tandai Selesai", callback_data=f"task_done:{task_id}")
        )
    builder.row(
        InlineKeyboardButton(text="🗑️ Hapus", callback_data=f"task_delete:{task_id}"),
        InlineKeyboardButton(text="⬅️ Kembali", callback_data="task_back"),
    )
    return builder.as_markup()


def confirm_delete_keyboard(task_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Ya, hapus", callback_data=f"task_delete_confirm:{task_id}"),
        InlineKeyboardButton(text="❌ Batal", callback_data=f"task_detail:{task_id}"),
    )
    return builder.as_markup()
