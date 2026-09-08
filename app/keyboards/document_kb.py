"""Inline keyboard fitur Dokumen."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.keyboards.dashboard_kb import dashboard_button
from app.models.document import Document


def document_list_keyboard(documents: list[Document]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for document in documents:
        builder.row(
            InlineKeyboardButton(
                text=f"📄 {document.original_name[:45]}",
                callback_data=f"document_detail:{document.id}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="➕ Upload", callback_data="document_add"),
        InlineKeyboardButton(text="🔎 Search", callback_data="document_search"),
    )
    builder.row(InlineKeyboardButton(text="🧾 Ringkas PDF", callback_data="pdf_summary_history"))
    builder.row(dashboard_button())
    return builder.as_markup()


def document_detail_keyboard(document_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬇️ Download", callback_data=f"document_download:{document_id}"))
    builder.row(
        InlineKeyboardButton(text="✏️ Rename", callback_data=f"document_rename:{document_id}"),
        InlineKeyboardButton(text="🗑️ Delete", callback_data=f"document_delete:{document_id}"),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Kembali", callback_data="document_back"))
    return builder.as_markup()
