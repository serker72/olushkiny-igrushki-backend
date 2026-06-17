"""create table products

Revision ID: a4b68c74dd25
Revises: 5dbe44049a3d
Create Date: 2026-06-06 12:38:09.928618

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a4b68c74dd25"
down_revision: Union[str, Sequence[str], None] = "5dbe44049a3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "products",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="ID"),
        sa.Column("state_id", sa.BigInteger(), nullable=False, comment="ID статуса"),
        sa.Column("category_id", sa.BigInteger(), nullable=False, comment="ID категории"),
        sa.Column("sku", sa.String(), nullable=False, comment="Артикул"),
        sa.Column("name", sa.String(), nullable=False, comment="Наименование"),
        sa.Column(
            "is_permanent_toys",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="Флаг постоянной игрушки",
        ),
        sa.Column("creation_date", sa.Date(), nullable=False, comment="Дата создания"),
        sa.Column("author", sa.String(), nullable=True, comment="Автор"),
        sa.Column("size", sa.DECIMAL(16, 2), nullable=False, comment="Размер в сантиметрах"),
        sa.Column("cost_of_work", sa.DECIMAL(16, 2), nullable=False, comment="Стоимость работы"),
        sa.Column("cost_of_materials", sa.DECIMAL(16, 2), nullable=False, comment="Стоимость материалов"),
        sa.Column("price", sa.DECIMAL(16, 2), nullable=False, comment="Цена"),
        sa.Column("price_for_sale", sa.DECIMAL(16, 2), nullable=False, comment="Цена для продажи"),
        sa.Column("profit", sa.DECIMAL(16, 2), nullable=False, comment="Прибыль"),
        sa.Column("hook_number", sa.Integer(), nullable=True, comment="Номер крючка"),
        sa.Column("spoke_number", sa.Integer(), nullable=True, comment="Номер спицы"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_products")),
        comment="Список товаров",
    )

    op.create_foreign_key(
        op.f("fk_products_state_id_module_states"),
        "products",
        "module_states",
        ["state_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_products_category_id_categories"),
        "products",
        "categories",
        ["category_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_products_created_by_users"),
        "products",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_products_updated_by_users"),
        "products",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_products_name"),
        "products",
        [sa.text("lower(name)")],
        unique=True,
    )

    op.create_index(
        op.f("uq_products_sku"),
        "products",
        ["sku"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("products")
