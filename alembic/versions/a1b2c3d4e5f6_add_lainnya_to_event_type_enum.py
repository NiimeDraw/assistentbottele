"""add lainnya to event type enum

Revision ID: a1b2c3d4e5f6
Revises: 82fec0ca69ed
Create Date: 2026-07-21 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "82fec0ca69ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE tidak bisa dijalankan di dalam blok transaksi
    # biasa di PostgreSQL, jadi harus pakai autocommit_block().
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE eventtypeenum ADD VALUE IF NOT EXISTS 'Lainnya'")


def downgrade() -> None:
    # PostgreSQL tidak mendukung menghapus satu value dari enum secara langsung
    # (perlu bikin ulang tipe enum dari nol). Karena ini cuma penambahan opsi
    # yang aman & non-destruktif, downgrade sengaja dibiarkan no-op.
    pass