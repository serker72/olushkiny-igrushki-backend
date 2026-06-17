"""create table properties

Revision ID: 2c91b90f7e65
Revises: a4b68c74dd25
Create Date: 2026-06-06 12:42:53.946036

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2c91b90f7e65"
down_revision: Union[str, Sequence[str], None] = "a4b68c74dd25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "properties",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="ID"),
        sa.Column("module_id", sa.Integer(), nullable=False, comment="ID модуля"),
        sa.Column("name", sa.String(), nullable=False, comment="Наименование"),
        sa.Column(
            "is_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Флаг обязательности",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Флаг активности",
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_properties")),
        comment="Список свойств объектов модулей",
    )

    op.create_foreign_key(
        op.f("fk_properties_module_id_modules"),
        "properties",
        "modules",
        ["module_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_properties_created_by_users"),
        "properties",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_properties_updated_by_users"),
        "properties",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_properties_module_id_name"),
        "properties",
        ["module_id", sa.text("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("properties")
