"""add PDF summary history

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pdf_summaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("short_summary", sa.Text(), nullable=False),
        sa.Column("detailed_summary", sa.Text(), nullable=False),
        sa.Column("key_points", sa.Text(), nullable=False),
        sa.Column("important_terms", sa.Text(), nullable=False),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("file_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pdf_summaries_user_id", "pdf_summaries", ["user_id"])
    op.create_index("ix_pdf_summaries_file_expires_at", "pdf_summaries", ["file_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_pdf_summaries_file_expires_at", table_name="pdf_summaries")
    op.drop_index("ix_pdf_summaries_user_id", table_name="pdf_summaries")
    op.drop_table("pdf_summaries")
