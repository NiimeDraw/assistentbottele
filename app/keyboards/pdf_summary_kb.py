"""Keyboard fitur ringkasan PDF."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.dashboard_kb import dashboard_button
from app.models.pdf_summary import PdfSummary


def pdf_summary_list_keyboard(history: list[PdfSummary]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in history:
        builder.row(
            InlineKeyboardButton(
                text=f"📄 {item.file_name[:45]}",
                callback_data=f"pdf_summary_detail:{item.id}",
            )
        )
    builder.row(InlineKeyboardButton(text="➕ Ringkas PDF", callback_data="pdf_summary_add"))
    builder.row(dashboard_button())
    return builder.as_markup()
