"""create table user_devices

Revision ID: bfba643b570e
Revises: 15c1e3e4af65
Create Date: 2025-11-22 14:57:15.178065

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bfba643b570e"
down_revision: Union[str, Sequence[str], None] = "15c1e3e4af65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_devices",
        sa.Column(
            "id",
            postgresql.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="ID",
        ),
        sa.Column("device_id", postgresql.UUID(), nullable=False, comment="ID устройства"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="ID пользователя"),
        sa.Column("last_logged_on", sa.DateTime(timezone=True), nullable=True, comment="Время последней авторизации"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_devices")),
        comment="Список устройств пользователей",
    )

    op.create_foreign_key(
        op.f("fk_user_devices_device_id_devices"),
        "user_devices",
        "devices",
        ["device_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_user_devices_user_id_users"),
        "user_devices",
        "users",
        ["user_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_user_devices_created_by_users"),
        "user_devices",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_user_devices_updated_by_users"),
        "user_devices",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_user_devices_device_id_user_id"),
        "user_devices",
        ["device_id", "user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_devices")
