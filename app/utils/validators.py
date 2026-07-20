"""Fungsi validasi input pengguna, dipakai di layer service sebelum data disimpan."""
from datetime import datetime, time

from app.utils.exceptions import ValidationError

DATE_FORMAT = "%d-%m-%Y %H:%M"
TIME_FORMAT = "%H:%M"


def validate_non_empty(value: str, field_name: str, max_length: int = 255) -> str:
    value = (value or "").strip()
    if not value:
        raise ValidationError(f"{field_name} tidak boleh kosong.")
    if len(value) > max_length:
        raise ValidationError(f"{field_name} maksimal {max_length} karakter.")
    return value


def validate_deadline(raw: str) -> datetime:
    raw = (raw or "").strip()
    try:
        dt = datetime.strptime(raw, DATE_FORMAT)
    except ValueError:
        raise ValidationError(
            "Format tanggal salah. Gunakan format: DD-MM-YYYY HH:MM\nContoh: 25-12-2026 23:59"
        )
    if dt < datetime.now():
        raise ValidationError("Deadline tidak boleh di waktu lampau.")
    return dt


def validate_time(raw: str, field_name: str = "Jam") -> time:
    raw = (raw or "").strip()
    try:
        return datetime.strptime(raw, TIME_FORMAT).time()
    except ValueError:
        raise ValidationError(f"{field_name} formatnya salah. Gunakan format HH:MM, contoh: 08:00")
