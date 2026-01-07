"""create table devices

Revision ID: 15c1e3e4af65
Revises: 0b26b04f3e51
Create Date: 2025-11-22 14:56:46.860094

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "15c1e3e4af65"
down_revision: Union[str, Sequence[str], None] = "0b26b04f3e51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "devices",
        sa.Column(
            "id",
            postgresql.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="ID",
        ),
        sa.Column("device_id", sa.String(), nullable=False, comment="ID устройства"),
        sa.Column("user_agent", sa.String(), nullable=False, comment="User Agent"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_devices")),
        comment="Список устройств",
    )

    op.create_foreign_key(
        op.f("fk_devices_created_by_users"),
        "devices",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_devices_updated_by_users"),
        "devices",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_devices_device_id_user_agent"),
        "devices",
        ["device_id", "user_agent"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("devices")
