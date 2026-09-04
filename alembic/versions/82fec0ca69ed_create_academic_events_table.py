"""create academic_events table

Revision ID: 82fec0ca69ed
Revises: 792ad672245b
Create Date: 2026-07-21 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
# pyrefly: ignore [missing-import]
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "82fec0ca69ed"
down_revision: Union[str, None] = "792ad672245b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "academic_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "UTS", "UAS", "KRS", "KHS", "LIBUR", "WISUDA", "SEMINAR",
                name="eventtypeenum",
            ),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reminder_days_before", sa.Integer(), nullable=True),
        sa.Column("reminder_sent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_academic_events_user_id"), "academic_events", ["user_id"], unique=False)
    op.create_index(op.f("ix_academic_events_event_type"), "academic_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_academic_events_start_date"), "academic_events", ["start_date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_academic_events_start_date"), table_name="academic_events")
    op.drop_index(op.f("ix_academic_events_event_type"), table_name="academic_events")
    op.drop_index(op.f("ix_academic_events_user_id"), table_name="academic_events")
    op.drop_table("academic_events")
    sa.Enum(name="eventtypeenum").drop(op.get_bind(), checkfirst=True)
