"""Inline Keyboard untuk fitur Nilai & IPK Calculator."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models.nilai import Nilai
from app.keyboards.dashboard_kb import dashboard_button


def nilai_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu utama IPK Calculator."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Daftar Nilai", callback_data="nilai_list"),
        InlineKeyboardButton(text="➕ Tambah Nilai", callback_data="nilai_add"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 IPS", callback_data="nilai_ips"),
        InlineKeyboardButton(text="🎯 IPK", callback_data="nilai_ipk"),
    )
    builder.row(
        InlineKeyboardButton(text="🏆 Target IPK", callback_data="nilai_target"),
        InlineKeyboardButton(text="🔮 Prediksi IPK", callback_data="nilai_prediksi"),
    )
    builder.row(
        InlineKeyboardButton(text="📈 Grafik", callback_data="nilai_grafik"),
        InlineKeyboardButton(text="📚 Riwayat", callback_data="nilai_riwayat"),
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Kembali", callback_data="nilai_menu"),
    )
    builder.row(dashboard_button())
    return builder.as_markup()


def nilai_list_keyboard(
    nilai_list: list[Nilai], semester: int | None = None
) -> InlineKeyboardMarkup:
    """Daftar nilai dengan filter semester."""
    builder = InlineKeyboardBuilder()
    for n in nilai_list:
        builder.row(
            InlineKeyboardButton(
                text=f"{n.nilai_huruf} {n.mata_kuliah} ({n.sks} SKS) — Sem {n.semester}",
                callback_data=f"nilai_detail:{n.id}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="➕ Tambah", callback_data="nilai_add"),
        InlineKeyboardButton(text="⬅️ Kembali", callback_data="nilai_menu"),
    )
    return builder.as_markup()


def nilai_detail_keyboard(nilai_id: int) -> InlineKeyboardMarkup:
    """Keyboard detail satu nilai."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Hapus", callback_data=f"nilai_delete:{nilai_id}"
        ),
        InlineKeyboardButton(text="⬅️ Kembali", callback_data="nilai_list"),
    )
    return builder.as_markup()


def confirm_delete_nilai_keyboard(nilai_id: int) -> InlineKeyboardMarkup:
    """Konfirmasi hapus nilai."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Ya, hapus", callback_data=f"nilai_delete_confirm:{nilai_id}"
        ),
        InlineKeyboardButton(
            text="❌ Batal", callback_data=f"nilai_detail:{nilai_id}"
        ),
    )
    return builder.as_markup()


def semester_picker_keyboard(
    semesters: list[int], action: str
) -> InlineKeyboardMarkup:
    """Pilih semester untuk aksi tertentu (IPS, daftar, dll)."""
    builder = InlineKeyboardBuilder()
    for sem in semesters:
        builder.row(
            InlineKeyboardButton(
                text=f"Semester {sem}",
                callback_data=f"{action}:{sem}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="⬅️ Kembali", callback_data="nilai_menu"),
    )
    return builder.as_markup()


def back_to_nilai_keyboard() -> InlineKeyboardMarkup:
    """Tombol kembali ke menu nilai."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⬅️ Kembali ke Menu Nilai", callback_data="nilai_menu"),
    )
    return builder.as_markup()
