"""create table modules

Revision ID: 188d1620f5cf
Revises: 85e15ad2f2c0
Create Date: 2025-07-15 17:57:23.793525

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "188d1620f5cf"
down_revision: Union[str, Sequence[str], None] = "85e15ad2f2c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), nullable=False, comment="ID"),
        sa.Column("code", sa.String(), nullable=False, comment="Код"),
        sa.Column("title", sa.String(), nullable=False, comment="Наименование"),
        # ----- Audit fields -----
        sa.Column("created_by", sa.BigInteger(), server_default=sa.text("1"), nullable=False, comment="ID создателя"),
        sa.Column(
            "created_on",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Время создания",
        ),
        sa.Column("updated_by", sa.BigInteger(), server_default=sa.text("1"), nullable=False, comment="ID редактора"),
        sa.Column(
            "updated_on",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Время изменения",
        ),
        # ----- Audit fields - End -----
        sa.PrimaryKeyConstraint("id", name=op.f("pk_modules")),
        comment="Список модулей",
    )

    op.create_foreign_key(
        op.f("fk_modules_created_by_users"),
        "modules",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_modules_updated_by_users"),
        "modules",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_modules_code"),
        "modules",
        ["code"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("modules")
