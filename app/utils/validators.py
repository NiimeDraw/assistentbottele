"""Fungsi validasi input pengguna, dipakai di layer service sebelum data disimpan."""
from datetime import time

from app.utils.exceptions import ValidationError
from app.utils.timezone_utils import attach_local_tz, now_local

DATE_FORMAT = "%d-%m-%Y %H:%M"
TIME_FORMAT = "%H:%M"


def validate_non_empty(value: str, field_name: str, max_length: int = 255) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field_name} tidak boleh kosong.")
    if len(value) > max_length:
        raise ValidationError(f"{field_name} maksimal {max_length} karakter.")
    return value


def validate_deadline(raw: str):
    """
    Parsing input deadline sebagai waktu WIB (Asia/Jakarta), terlepas dari
    timezone server tempat bot dijalankan. Ini penting karena bot bisa
    saja dijalankan di server dengan timezone berbeda (mis. VPS luar negeri),
    sementara target pengguna berpatokan pada WIB.
    """
    raw = (raw or "").strip()
    try:
        from datetime import datetime

        naive_dt = datetime.strptime(raw, DATE_FORMAT)
    except ValueError:
        raise ValidationError(
            "Format tanggal salah. Gunakan format: DD-MM-YYYY HH:MM\nContoh: 25-12-2026 23:59"
        )

    dt = attach_local_tz(naive_dt)

    if dt < now_local():
        raise ValidationError("Deadline tidak boleh di waktu lampau.")
    return dt


def validate_time(raw: str, field_name: str = "Jam") -> time:
    from datetime import datetime

    raw = (raw or "").strip()
    try:
        return datetime.strptime(raw, TIME_FORMAT).time()
    except ValueError:
        raise ValidationError(f"{field_name} formatnya salah. Gunakan format HH:MM, contoh: 08:00")