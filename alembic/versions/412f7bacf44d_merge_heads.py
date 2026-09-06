"""merge heads

Revision ID: 412f7bacf44d
Revises: 2df4197b01a8, b7c8d9e0f1a2
Create Date: 2026-09-06 08:49:21.318545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '412f7bacf44d'
down_revision: Union[str, None] = ('2df4197b01a8', 'b7c8d9e0f1a2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
