"""fix lainnya enum label to match sqlalchemy name convention

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-07-21 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migrasi sebelumnya (a1b2c3d4e5f6) salah menambahkan label 'Lainnya'.
    # SQLAlchemy secara default menyimpan enum Python berdasarkan .name
    # (huruf besar semua, mis. LIBUR bukan Libur), jadi label yang benar
    # untuk EventTypeEnum.LAINNYA adalah 'LAINNYA', bukan 'Lainnya'.
    # Label lama 'Lainnya' dibiarkan saja (tidak dipakai, tidak mengganggu).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE eventtypeenum ADD VALUE IF NOT EXISTS 'LAINNYA'")


def downgrade() -> None:
    pass