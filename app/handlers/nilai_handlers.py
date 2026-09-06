"""Handler untuk fitur Nilai & IPK Calculator."""
# pyrefly: ignore [missing-import]
from aiogram import F, Router
# pyrefly: ignore [missing-import]
from aiogram.fsm.context import FSMContext
# pyrefly: ignore [missing-import]
from aiogram.types import CallbackQuery, Message
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession

# pyrefly: ignore [missing-import]
from app.handlers.states import NilaiStates
# pyrefly: ignore [missing-import]
from app.keyboards.main_menu import main_menu_keyboard
# pyrefly: ignore [missing-import]
from app.keyboards.nilai_kb import (
    back_to_nilai_keyboard,
    confirm_delete_nilai_keyboard,
    nilai_detail_keyboard,
    nilai_list_keyboard,
    nilai_menu_keyboard,
    semester_picker_keyboard,
)
# pyrefly: ignore [missing-import]
from app.models.user import User
# pyrefly: ignore [missing-import]
from app.services.nilai_service import NilaiService
# pyrefly: ignore [missing-import]
from app.utils.exceptions import AppError
# pyrefly: ignore [missing-import]
from app.utils.html import quote
# pyrefly: ignore [missing-import]
from app.utils.logger import get_logger
# pyrefly: ignore [missing-import]
from app.utils.telegram_helpers import safe_answer, safe_edit_or_send

logger = get_logger(__name__)
router = Router(name="nilai")


# ── Menu Utama ───────────────────────────────────────────

@router.callback_query(F.data == "dashboard:nilai")
async def nilai_menu_from_dashboard(
    callback: CallbackQuery,
) -> None:
    """Masuk ke menu nilai dari dashboard."""
    await safe_edit_or_send(
        callback,
        "<b>📈 IPK Calculator</b>\n\nPilih menu di bawah:",
        nilai_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "nilai_menu")
async def nilai_menu(callback: CallbackQuery) -> None:
    """Kembali ke menu utama nilai."""
    await safe_edit_or_send(
        callback,
        "<b>📈 IPK Calculator</b>\n\nPilih menu di bawah:",
        nilai_menu_keyboard(),
    )
    await callback.answer()


# ── Daftar Nilai ─────────────────────────────────────────

@router.callback_query(F.data == "nilai_list")
async def nilai_list(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Tampilkan daftar semua nilai."""
    service = NilaiService(session)
    try:
        nilai_data = await service.list_nilai(db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    if not nilai_data:
        await safe_edit_or_send(
            callback,
            "📋 <b>Daftar Nilai</b>\n\nBelum ada data nilai. Tambahkan nilai terlebih dahulu!",
            nilai_menu_keyboard(),
        )
        await callback.answer()
        return

    await safe_edit_or_send(
        callback,
        "📋 <b>Daftar Nilai</b>\n\nPilih mata kuliah untuk melihat detail:",
        nilai_list_keyboard(nilai_data),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("nilai_detail:"))
async def nilai_detail(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Tampilkan detail satu nilai."""
    if not callback.data:
        await callback.answer()
        return
    nilai_id = int(callback.data.split(":")[1])
    service = NilaiService(session)
    try:
        n = await service.get_nilai(db_user.id, nilai_id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    text = (
        f"📌 <b>{quote(n.mata_kuliah)}</b>\n\n"
        f"SKS: {n.sks}\n"
        f"Nilai: {n.nilai:.2f} ({n.nilai_huruf})\n"
        f"Semester: {n.semester}\n"
        f"Bobot: {n.bobot:.2f}"
    )
    await safe_edit_or_send(callback, text, nilai_detail_keyboard(n.id))
    await callback.answer()


# ── Tambah Nilai ─────────────────────────────────────────

@router.callback_query(F.data == "nilai_add")
async def nilai_add_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Mulai proses tambah nilai."""
    await state.set_state(NilaiStates.waiting_mata_kuliah)
    await safe_answer(
        callback,
        "Masukkan <b>nama mata kuliah</b> (ketik /cancel untuk membatalkan):",
    )
    await callback.answer()


@router.message(NilaiStates.waiting_mata_kuliah)
async def nilai_add_mk(message: Message, state: FSMContext) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Nama mata kuliah tidak boleh kosong. Masukkan ulang:")
        return
    await state.update_data(mata_kuliah=message.text.strip())
    await state.set_state(NilaiStates.waiting_sks)
    await message.answer("Masukkan <b>jumlah SKS</b> (contoh: 3):")


@router.message(NilaiStates.waiting_sks)
async def nilai_add_sks(message: Message, state: FSMContext) -> None:
    try:
        sks = int(message.text or "")
        if sks <= 0:
            raise ValueError
    except ValueError:
        await message.answer("SKS harus berupa angka positif. Masukkan ulang:")
        return
    await state.update_data(sks=sks)
    await state.set_state(NilaiStates.waiting_nilai)
    await message.answer(
        "Masukkan <b>nilai</b> (0.00 – 4.00):\n"
        "Contoh: 3.50 untuk A-"
    )


@router.message(NilaiStates.waiting_nilai)
async def nilai_add_nilai(message: Message, state: FSMContext) -> None:
    try:
        nilai = float(message.text or "")
        if nilai < 0 or nilai > 4.0:
            raise ValueError
    except ValueError:
        await message.answer(
            "Nilai harus berupa angka antara 0.00 – 4.00. Masukkan ulang:"
        )
        return
    await state.update_data(nilai=nilai)
    await state.set_state(NilaiStates.waiting_semester)
    await message.answer("Masukkan <b>semester</b> (contoh: 3):")


@router.message(NilaiStates.waiting_semester)
async def nilai_add_semester(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    try:
        semester = int(message.text or "")
        if semester <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Semester harus berupa angka positif. Masukkan ulang:")
        return

    data = await state.get_data()
    service = NilaiService(session)
    try:
        await service.add_nilai(
            user_id=db_user.id,
            mata_kuliah=data["mata_kuliah"],
            sks=data["sks"],
            nilai=data["nilai"],
            semester=semester,
        )
    except AppError as exc:
        await state.clear()
        await message.answer(f"⚠️ {exc.message}", reply_markup=main_menu_keyboard())
        return

    await state.clear()
    await message.answer(
        f"✅ Nilai <b>{quote(data['mata_kuliah'])}</b> berhasil ditambahkan!",
        reply_markup=main_menu_keyboard(),
    )

    # Tampilkan menu nilai
    nilai_data = await service.list_nilai(db_user.id)
    await message.answer(
        "📋 <b>Daftar Nilai</b>",
        reply_markup=nilai_list_keyboard(nilai_data),
    )


# ── Hapus Nilai ──────────────────────────────────────────

@router.callback_query(F.data.startswith("nilai_delete:"))
async def nilai_delete_prompt(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer()
        return
    nilai_id = int(callback.data.split(":")[1])
    await safe_edit_or_send(
        callback,
        "Yakin ingin menghapus data nilai ini?",
        confirm_delete_nilai_keyboard(nilai_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("nilai_delete_confirm:"))
async def nilai_delete_confirm(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not callback.data:
        await callback.answer()
        return
    nilai_id = int(callback.data.split(":")[1])
    service = NilaiService(session)
    try:
        await service.delete_nilai(db_user.id, nilai_id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    await callback.answer("Data nilai dihapus 🗑️")
    nilai_data = await service.list_nilai(db_user.id)
    if not nilai_data:
        await safe_edit_or_send(
            callback,
            "📋 <b>Daftar Nilai</b>\n\nBelum ada data nilai.",
            nilai_menu_keyboard(),
        )
    else:
        await safe_edit_or_send(
            callback,
            "📋 <b>Daftar Nilai</b>",
            nilai_list_keyboard(nilai_data),
        )


# ── IPS ──────────────────────────────────────────────────

@router.callback_query(F.data == "nilai_ips")
async def nilai_ips_pick_semester(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Tampilkan pilihan semester untuk menghitung IPS."""
    service = NilaiService(session)
    try:
        semesters = await service.get_semesters(db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    if not semesters:
        await callback.answer("Belum ada data nilai.", show_alert=True)
        return

    await safe_edit_or_send(
        callback,
        "📊 <b>Hitung IPS</b>\n\nPilih semester:",
        semester_picker_keyboard(semesters, "nilai_ips_sem"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("nilai_ips_sem:"))
async def nilai_ips_result(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    if not callback.data:
        await callback.answer()
        return
    semester = int(callback.data.split(":")[1])
    service = NilaiService(session)
    try:
        result = await service.hitung_ips(db_user.id, semester)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    text = (
        f"📊 <b>IPS Semester {result['semester']}</b>\n\n"
        f"IPS: <b>{result['ips']:.2f}</b>\n"
        f"Total SKS: {result['total_sks']}\n"
        f"Total Bobot: {result['total_bobot']}\n"
        f"Jumlah MK: {result['jumlah_mk']}"
    )
    await safe_edit_or_send(callback, text, back_to_nilai_keyboard())
    await callback.answer()


# ── IPK ──────────────────────────────────────────────────

@router.callback_query(F.data == "nilai_ipk")
async def nilai_ipk(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Hitung dan tampilkan IPK kumulatif."""
    service = NilaiService(session)
    try:
        result = await service.hitung_ipk(db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    lines = [
        f"🎯 <b>IPK Kumulatif</b>\n",
        f"IPK: <b>{result['ipk']:.2f}</b>",
        f"Total SKS: {result['total_sks']}",
        f"Jumlah Semester: {result['jumlah_semester']}",
        "",
        "<b>Rincian per Semester:</b>",
    ]
    for r in result["riwayat"]:
        lines.append(f"  Semester {r['semester']}: IPS {r['ips']:.2f} ({r['total_sks']} SKS)")

    await safe_edit_or_send(callback, "\n".join(lines), back_to_nilai_keyboard())
    await callback.answer()


# ── Target IPK ───────────────────────────────────────────

@router.callback_query(F.data == "nilai_target")
async def nilai_target_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Mulai input target IPK."""
    await state.set_state(NilaiStates.waiting_target_ipk)
    await safe_answer(
        callback,
        "Masukkan <b>target IPK</b> yang ingin dicapai (0.00 – 4.00):\nContoh: 3.50",
    )
    await callback.answer()


@router.message(NilaiStates.waiting_target_ipk)
async def nilai_target_ipk(message: Message, state: FSMContext) -> None:
    try:
        target = float(message.text or "")
        if target < 0 or target > 4.0:
            raise ValueError
    except ValueError:
        await message.answer(
            "Target IPK harus antara 0.00 – 4.00. Masukkan ulang:"
        )
        return
    await state.update_data(target_ipk=target)
    await state.set_state(NilaiStates.waiting_sisa_sks)
    await message.answer(
        "Masukkan <b>sisa SKS</b> yang akan diambil:\nContoh: 60"
    )


@router.message(NilaiStates.waiting_sisa_sks)
async def nilai_target_result(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    try:
        sisa_sks = int(message.text or "")
        if sisa_sks <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Sisa SKS harus berupa angka positif. Masukkan ulang:")
        return

    data = await state.get_data()
    await state.clear()

    service = NilaiService(session)
    try:
        result = await service.hitung_target_ipk(
            db_user.id, data["target_ipk"], sisa_sks
        )
    except AppError as exc:
        await message.answer(f"⚠️ {exc.message}", reply_markup=main_menu_keyboard())
        return

    text = (
        f"🏆 <b>Target IPK</b>\n\n"
        f"IPK Saat Ini: <b>{result['ipk_sekarang']:.2f}</b>\n"
        f"SKS Saat Ini: {result['sks_sekarang']}\n"
        f"Target IPK: <b>{result['target_ipk']:.2f}</b>\n"
        f"Sisa SKS: {result['sisa_sks']}\n"
        f"Total SKS Nanti: {result['total_sks_nanti']}\n\n"
        f"Rata-rata nilai yang dibutuhkan: <b>{result['required_avg']:.2f}</b> per SKS\n\n"
        f"{result['message']}"
    )
    await message.answer(text, reply_markup=main_menu_keyboard())


# ── Prediksi IPK ─────────────────────────────────────────

@router.callback_query(F.data == "nilai_prediksi")
async def nilai_prediksi_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Mulai input prediksi IPK."""
    await state.set_state(NilaiStates.waiting_prediksi_data)
    await safe_answer(
        callback,
        "Masukkan <b>rencana nilai</b> dalam format:\n\n"
        "<code>Mata Kuliah, SKS, Prediksi Nilai</code>\n"
        "Satu baris per mata kuliah.\n\n"
        "Contoh:\n"
        "<code>Algoritma, 3, 3.70\n"
        "Basis Data, 4, 3.50\n"
        "Statistika, 3, 4.00</code>\n\n"
        "Ketik /cancel untuk membatalkan.",
    )
    await callback.answer()


@router.message(NilaiStates.waiting_prediksi_data)
async def nilai_prediksi_result(
    message: Message, state: FSMContext, session: AsyncSession, db_user: User
) -> None:
    if not message.text or not message.text.strip():
        await message.answer("Data tidak boleh kosong. Masukkan ulang:")
        return

    rencana = []
    errors = []
    for i, line in enumerate(message.text.strip().split("\n"), 1):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 3:
            errors.append(f"Baris {i}: format salah (butuh 3 nilai dipisah koma)")
            continue
        try:
            mk = parts[0]
            sks = int(parts[1])
            pred_nilai = float(parts[2])
            if sks <= 0 or pred_nilai < 0 or pred_nilai > 4.0:
                raise ValueError
            rencana.append(
                {"mata_kuliah": mk, "sks": sks, "prediksi_nilai": pred_nilai}
            )
        except ValueError:
            errors.append(
                f"Baris {i}: SKS harus > 0, nilai harus 0.00–4.00"
            )

    if errors:
        await message.answer(
            "⚠️ Terdapat kesalahan:\n" + "\n".join(errors) + "\n\nMasukkan ulang:"
        )
        return

    await state.clear()
    service = NilaiService(session)
    result = await service.prediksi_ipk(db_user.id, rencana)

    lines = [
        "🔮 <b>Prediksi IPK</b>\n",
        f"IPK Saat Ini: <b>{result['ipk_sekarang']:.2f}</b>",
        f"SKS Saat Ini: {result['sks_sekarang']}",
        "",
        "<b>Rencana Nilai:</b>",
    ]
    for r in rencana:
        lines.append(
            f"  • {r['mata_kuliah']} ({r['sks']} SKS): {r['prediksi_nilai']:.2f}"
        )
    lines.append("")
    lines.append(f"Tambahan SKS: {result['tambahan_sks']}")
    lines.append(f"Tambahan Bobot: {result['tambahan_bobot']}")
    lines.append(f"Total SKS: {result['total_sks']}")
    lines.append(f"\n🎯 <b>Prediksi IPK: {result['prediksi_ipk']:.2f}</b>")

    await message.answer("\n".join(lines), reply_markup=main_menu_keyboard())


# ── Grafik Perkembangan ──────────────────────────────────

@router.callback_query(F.data == "nilai_grafik")
async def nilai_grafik(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Tampilkan grafik perkembangan IPS per semester."""
    service = NilaiService(session)
    try:
        grafik = await service.grafik_perkembangan(db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    await safe_edit_or_send(
        callback,
        f"<pre>{grafik}</pre>",
        back_to_nilai_keyboard(),
    )
    await callback.answer()


# ── Riwayat Semester ─────────────────────────────────────

@router.callback_query(F.data == "nilai_riwayat")
async def nilai_riwayat(
    callback: CallbackQuery, session: AsyncSession, db_user: User
) -> None:
    """Tampilkan riwayat lengkap per semester."""
    service = NilaiService(session)
    try:
        riwayat = await service.riwayat_semester(db_user.id)
    except AppError as exc:
        await callback.answer(exc.message, show_alert=True)
        return

    await safe_edit_or_send(callback, riwayat, back_to_nilai_keyboard())
    await callback.answer()
