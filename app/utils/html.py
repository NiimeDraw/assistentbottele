"""Helper HTML escape terpusat untuk seluruh aplikasi.

aiogram menghapus modul `aiogram.html` pada versi baru (>= 3.23), sehingga
`from aiogram.html import quote` tidak lagi valid. Shim ini memakai
`aiogram.utils.text_decorations` yang tersedia di semua versi 3.x,
sehingga kode tetap jalan baik dengan aiogram lama maupun baru.
"""
from aiogram.utils.text_decorations import html_decoration

quote = html_decoration.quote
