"""Custom exceptions untuk validasi & error handling yang rapi di seluruh layer service."""


class AppError(Exception):
    """Base exception untuk error aplikasi yang bersifat 'ramah pengguna'."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationError(AppError):
    """Dilempar saat input pengguna tidak valid."""
    pass


class NotFoundError(AppError):
    """Dilempar saat data yang diminta tidak ditemukan / bukan milik pengguna."""
    pass
