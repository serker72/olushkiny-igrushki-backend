"""create table module_states

Revision ID: 0da975ad9668
Revises: 188d1620f5cf
Create Date: 2025-07-15 17:57:29.238862

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import LtreeType

# revision identifiers, used by Alembic.
revision: str = "0da975ad9668"
down_revision: Union[str, Sequence[str], None] = "188d1620f5cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS ltree"))

    op.create_table(
        "module_states",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="ID"),
        sa.Column("module_id", sa.Integer(), nullable=False, comment="ID модуля"),
        sa.Column("flag", sa.Integer(), nullable=False, comment="Флаг"),
        sa.Column("code", sa.String(), nullable=False, comment="Код"),
        sa.Column("title", sa.String(), nullable=False, comment="Наименование"),
        sa.Column("hierarchy", LtreeType(), nullable=True, comment="Иерархия"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_module_states")),
        comment="Список статусов объектов модулей",
    )

    op.create_foreign_key(
        op.f("fk_module_states_module_id_modules"),
        "module_states",
        "modules",
        ["module_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_module_states_created_by_users"),
        "module_states",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_module_states_updated_by_users"),
        "module_states",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_module_states_module_id_flag"),
        "module_states",
        ["module_id", "flag"],
        unique=True,
    )

    op.create_index(
        op.f("uq_module_states_module_id_code"),
        "module_states",
        ["module_id", "code"],
        unique=True,
    )

    op.create_index(
        op.f("ix_module_states_hierarchy"),
        "module_states",
        ["hierarchy"],
        postgresql_using="gist",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("module_states")
    op.execute(sa.text("DROP EXTENSION IF EXISTS ltree CASCADE"))
