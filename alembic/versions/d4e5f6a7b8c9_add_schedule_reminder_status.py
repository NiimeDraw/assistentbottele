"""add persistent schedule reminder status

Revision ID: d4e5f6a7b8c9
Revises: 3c0b4653399f
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "3c0b4653399f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "schedules",
        sa.Column("last_reminder_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("schedules", "last_reminder_date")
