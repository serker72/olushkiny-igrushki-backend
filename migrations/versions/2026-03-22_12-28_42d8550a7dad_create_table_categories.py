"""create table categories

Revision ID: 42d8550a7dad
Revises: b49c5649f1b6
Create Date: 2026-03-22 12:28:19.317432

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "42d8550a7dad"
down_revision: Union[str, Sequence[str], None] = "b49c5649f1b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="ID"),
        sa.Column("state_id", sa.BigInteger(), nullable=False, comment="ID статуса"),
        sa.Column("name", sa.String(), nullable=False, comment="Наименование"),
        sa.Column("sku_prefix", sa.String(), nullable=False, comment="Префикс артикула"),
        sa.Column(
            "toy_max_index",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="Максимальный индекс игрушки",
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        comment="Список категорий",
    )

    op.create_foreign_key(
        op.f("fk_categories_created_by_users"),
        "categories",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_categories_updated_by_users"),
        "categories",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_categories_name"),
        "categories",
        [sa.text("lower(name)")],
        unique=True,
    )

    op.create_index(
        op.f("uq_categories_sku_prefix"),
        "categories",
        ["sku_prefix"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("categories")
