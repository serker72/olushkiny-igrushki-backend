"""create table product_properties

Revision ID: f58f62e653b1
Revises: 2c91b90f7e65
Create Date: 2026-06-06 12:43:09.124221

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f58f62e653b1"
down_revision: Union[str, Sequence[str], None] = "2c91b90f7e65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "product_properties",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="ID"),
        sa.Column("product_id", sa.Integer(), nullable=False, comment="ID товара"),
        sa.Column("property_id", sa.Integer(), nullable=False, comment="ID свойства"),
        sa.Column("quantity", sa.DECIMAL(16, 2), nullable=False, comment="Количество"),
        sa.Column("price", sa.DECIMAL(16, 2), nullable=False, comment="Цена"),
        sa.Column("cost", sa.DECIMAL(16, 2), nullable=False, comment="Стоимость"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_product_properties")),
        comment="Список значений свойств товаров",
    )

    op.create_foreign_key(
        op.f("fk_product_properties_product_id_products"),
        "product_properties",
        "products",
        ["product_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_product_properties_property_id_properties"),
        "product_properties",
        "properties",
        ["property_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_product_properties_created_by_users"),
        "product_properties",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_product_properties_updated_by_users"),
        "product_properties",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_product_properties_product_id_property_id"),
        "product_properties",
        ["product_id", "property_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("product_properties")
