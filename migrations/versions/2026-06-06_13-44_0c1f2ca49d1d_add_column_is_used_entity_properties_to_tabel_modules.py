"""add column is_used_entity_properties to tabel modules

Revision ID: 0c1f2ca49d1d
Revises: f58f62e653b1
Create Date: 2026-06-07 14:12:37.194693

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0c1f2ca49d1d"
down_revision: Union[str, Sequence[str], None] = "f58f62e653b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "modules",
        sa.Column(
            "is_used_entity_properties",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Флаг использования свойств объекта",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("modules", "is_used_entity_properties")
