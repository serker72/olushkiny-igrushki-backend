"""create table user_authorization_codes

Revision ID: 656a73efafec
Revises: bfba643b570e
Create Date: 2025-11-22 15:45:52.348496

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from common.enums import UserAuthorizationCodeStatuses

# revision identifiers, used by Alembic.
revision: str = "656a73efafec"
down_revision: Union[str, Sequence[str], None] = "bfba643b570e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_authorization_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, comment="ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="ID пользователя"),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False, comment="Идентификатор устройства"),
        sa.Column("email", sa.String(), nullable=True, comment="Адрес EMail"),
        sa.Column("phone", sa.String(), nullable=True, comment="Номер телефона"),
        sa.Column("code", sa.String(), nullable=False, comment="Код подтверждения"),
        sa.Column(
            "status",
            sa.Enum(
                *[item.name for item in iter(UserAuthorizationCodeStatuses)], name="user_authorization_codes_status"
            ),
            nullable=False,
            server_default=sa.text(f"'{UserAuthorizationCodeStatuses.created.name}'"),
            comment="Статус",
        ),
        sa.Column("group_number", sa.SmallInteger(), nullable=True, comment="Номер группы сгенерированных кодов"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_authorization_codes")),
        sa.CheckConstraint("email IS NOT NULL OR phone IS NOT NULL", name="ch_user_authorization_codes_email_phone"),
        sa.CheckConstraint("group_number > 0", name="ch_user_authorization_codes_group_number"),
        comment="Список кодов подтверждения авторизации пользователей",
    )

    op.create_foreign_key(
        op.f("fk_user_authorization_codes_user_id_users"),
        "user_authorization_codes",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        op.f("fk_user_authorization_codes_device_id_devices"),
        "user_authorization_codes",
        "devices",
        ["device_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        op.f("fk_user_authorization_codes_created_by_users"),
        "user_authorization_codes",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_user_authorization_codes_updated_by_users"),
        "user_authorization_codes",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("ix_user_authorization_codes_device_id_email_created_on"),
        "user_authorization_codes",
        ["device_id", "email", sa.text("created_on DESC")],
        postgresql_where=sa.text("phone IS NULL"),
    )
    op.create_index(
        op.f("ix_user_authorization_codes_device_id_email_group_number"),
        "user_authorization_codes",
        ["device_id", "email", sa.text("group_number DESC")],
        postgresql_where=sa.text("phone IS NULL"),
    )

    op.create_index(
        op.f("ix_user_authorization_codes_device_id_phone_created_on"),
        "user_authorization_codes",
        ["device_id", "phone", sa.text("created_on DESC")],
        postgresql_where=sa.text("email IS NULL"),
    )
    op.create_index(
        op.f("ix_user_authorization_codes_device_id_phone_group_number"),
        "user_authorization_codes",
        ["device_id", "phone", sa.text("group_number DESC")],
        postgresql_where=sa.text("email IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_authorization_codes")
    op.execute("DROP TYPE IF EXISTS user_authorization_codes_status")
