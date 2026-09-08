"""Fungsi validasi input pengguna, dipakai di layer service sebelum data disimpan."""
from datetime import time
import math

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


SIMPLE_DATE_FORMAT = "%d-%m-%Y"


def validate_date(raw: str, field_name: str = "Tanggal"):
    """Parsing tanggal (tanpa jam) dengan format DD-MM-YYYY, mengembalikan objek date."""
    from datetime import datetime

    raw = (raw or "").strip()
    try:
        return datetime.strptime(raw, SIMPLE_DATE_FORMAT).date()
    except ValueError:
        raise ValidationError(
            f"{field_name} formatnya salah. Gunakan format DD-MM-YYYY, contoh: 25-12-2026"
        )


def validate_optional_int(raw: str, field_name: str, min_value: int = 0) -> int | None:
    """
    Parsing angka opsional. Ketik '-' untuk melewati (hasil None).
    Dipakai misalnya untuk input 'reminder berapa hari sebelum acara'.
    """
    raw = (raw or "").strip()
    if raw == "-":
        return None
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(f"{field_name} harus berupa angka, atau ketik - untuk melewati.")
    if value < min_value:
        raise ValidationError(f"{field_name} tidak boleh kurang dari {min_value}.")
    return value


def validate_reminder_minutes(value: int | None) -> int | None:
    """Validasi jeda pengingat jadwal dalam menit; None berarti tanpa pengingat."""
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError("Pengingat harus berupa bilangan bulat dalam menit.")
    if value < 0:
        raise ValidationError("Pengingat tidak boleh bernilai negatif.")
    return value or None


def validate_positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field_name} harus berupa bilangan bulat positif.")
    return value


def validate_grade(value: float, field_name: str = "Nilai") -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} harus berupa angka antara 0.00 dan 4.00.")
    value = float(value)
    if not math.isfinite(value) or not 0 <= value <= 4.0:
        raise ValidationError(f"{field_name} harus antara 0.00 dan 4.00.")
    return value