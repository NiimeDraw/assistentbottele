"""
Modul timezone terpusat untuk seluruh aplikasi.

Seluruh input & tampilan waktu di bot ini SELALU dianggap sebagai
WIB (Asia/Jakarta), apapun timezone server tempat bot dijalankan.
Ini penting karena bot bisa saja dijalankan di server dengan timezone
berbeda (mis. VPS Singapore = UTC+8), sementara target pengguna
(mahasiswa Indonesia) berpatokan pada WIB (UTC+7).
"""
from datetime import datetime
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Asia/Jakarta")


def now_local() -> datetime:
    """Waktu saat ini, selalu dalam WIB (timezone-aware)."""
    return datetime.now(APP_TZ)


def attach_local_tz(naive_dt: datetime) -> datetime:
    """
    Menempelkan informasi timezone WIB ke datetime naive (tanpa tzinfo).
    Dipakai saat memparsing input pengguna, supaya tidak ambigu
    terlepas dari timezone server.
    """
    return naive_dt.replace(tzinfo=APP_TZ)


def to_local(dt: datetime) -> datetime:
    """
    Mengonversi datetime (timezone-aware, dari database) ke WIB untuk ditampilkan.
    Jika dt kebetulan naive (tidak seharusnya terjadi, tapi untuk jaga-jaga),
    anggap saja itu sudah WIB.
    """
    if dt.tzinfo is None:
        return attach_local_tz(dt)
    return dt.astimezone(APP_TZ)


def format_local(dt: datetime, fmt: str = "%d-%m-%Y %H:%M") -> str:
    """Shortcut: konversi ke WIB lalu format jadi string."""
    return to_local(dt).strftime(fmt)