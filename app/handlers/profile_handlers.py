"""Handler untuk manajemen profil pengguna: lihat, edit, hapus akun."""
# pyrefly: ignore [missing-import]
from aiogram import F, Router
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext
# pyrefly: ignore [missing-import]
from aiogram.html import quote
# pyrefly: ignore [missing-import]
from aiogram.types import Message
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

# pyrefly: ignore [missing-import]
from app.handlers.states import UserStates
# pyrefly: ignore [missing-import]
from app.keyboards.main_menu import main_menu_keyboard, BTN_PROFIL
# pyrefly: ignore [missing-import]
from app.keyboards.profile_kb import profile_keyboard, BTN_EDIT_PROFILE, BTN_DELETE_ACCOUNT, BTN_BACK
# pyrefly: ignore [missing-import]
from app.models.user import User
# pyrefly: ignore [missing-import]
from app.services.user_service import UserService
# pyrefly: ignore [missing-import]
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = Router(name="profile")


def _render_profile_text(user: User) -> str:
    username_line = f"Username: <b>@{quote(user.username)}</b>\n" if user.username else "Username: -\n"
    fakultas_str = quote(user.fakultas) if user.fakultas else "-"
    jurusan_str = quote(user.jurusan) if user.jurusan else "-"
    angkatan_str = str(user.angkatan) if user.angkatan else "-"
    semester_str = str(user.semester) if user.semester else "-"
    terdaftar_str = user.created_at.strftime("%d-%m-%Y") if hasattr(user.created_at, "strftime") else str(user.created_at)

    return (
        "👤 <b>Profil</b>\n\n"
        f"Nama: <b>{quote(user.full_name)}</b>\n"
        f"{username_line}"
        f"Fakultas: <b>{fakultas_str}</b>\n"
        f"Jurusan: <b>{jurusan_str}</b>\n"
        f"Angkatan: <b>{angkatan_str}</b>\n"
        f"Semester: <b>{semester_str}</b>\n"
        f"Terdaftar: <b>{terdaftar_str}</b>"
    )


@router.message(F.text == BTN_PROFIL)
async def show_profile(message: Message, db_user: User) -> None:
    await message.answer(_render_profile_text(db_user), reply_markup=profile_keyboard())


@router.message(F.text == BTN_BACK)
async def profile_back(message: Message) -> None:
    await message.answer("Kembali ke menu utama.", reply_markup=main_menu_keyboard())


@router.message(F.text == BTN_EDIT_PROFILE)
async def edit_profile_start(message: Message, state: FSMContext) -> None:
    await state.set_state(UserStates.waiting_fakultas)
    await message.answer("Masukkan <b>fakultas</b> (ketik - jika ingin kosong):")


@router.message(UserStates.waiting_fakultas)
async def edit_fakultas(message: Message, state: FSMContext) -> None:
    await state.update_data(fakultas=message.text.strip() if message.text.strip() != "-" else None)
    await state.set_state(UserStates.waiting_jurusan)
    await message.answer("Masukkan <b>jurusan</b> (ketik - jika ingin kosong):")


@router.message(UserStates.waiting_jurusan)
async def edit_jurusan(message: Message, state: FSMContext) -> None:
    await state.update_data(jurusan=message.text.strip() if message.text.strip() != "-" else None)
    await state.set_state(UserStates.waiting_angkatan)
    await message.answer("Masukkan <b>angkatan</b> (tahun, contoh: 2022). Ketik - jika ingin kosong:")


@router.message(UserStates.waiting_angkatan)
async def edit_angkatan(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    angkatan = None
    if text != "-":
        try:
            angkatan = int(text)
        except ValueError:
            await message.answer("Angkatan harus berupa angka (tahun). Coba lagi:")
            return
    await state.update_data(angkatan=angkatan)
    await state.set_state(UserStates.waiting_semester)
    await message.answer("Masukkan <b>semester</b> (angka). Ketik - jika ingin kosong:")


@router.message(UserStates.waiting_semester)
async def edit_semester(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    text = message.text.strip()
    semester = None
    if text != "-":
        try:
            semester = int(text)
        except ValueError:
            await message.answer("Semester harus berupa angka. Coba lagi:")
            return

    data = await state.get_data()
    data["semester"] = semester

    # Terapkan perubahan
    service = UserService(session)
    await service.update_profile(
        db_user.id,
        fakultas=data.get("fakultas"),
        jurusan=data.get("jurusan"),
        angkatan=data.get("angkatan"),
        semester=data.get("semester"),
    )

    await state.clear()
    await message.answer("✅ Profil berhasil diperbarui.", reply_markup=main_menu_keyboard())


@router.message(F.text == BTN_DELETE_ACCOUNT)
async def delete_account_start(message: Message, state: FSMContext) -> None:
    await state.set_state(UserStates.confirm_delete)
    await message.answer(
        "Konfirmasi penghapusan akun: ketik <b>YA</b> untuk menghapus akunmu secara permanen, atau ketik /cancel untuk membatalkan."
    )


@router.message(UserStates.confirm_delete)
async def confirm_delete(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    if message.text and message.text.strip().lower() == "ya":
        service = UserService(session)
        await service.delete_user_by_telegram_id(db_user.telegram_id)
        await state.clear()
        await message.answer("✅ Akun Anda telah dihapus. Untuk mulai ulang, kirim /start.", reply_markup=main_menu_keyboard())
        return

    await state.clear()
    await message.answer("Penghapusan akun dibatalkan.", reply_markup=main_menu_keyboard())