"""create table email_messages

Revision ID: 9b137c281d18
Revises: 656a73efafec
Create Date: 2025-11-23 15:24:16.271818

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "9b137c281d18"
down_revision: Union[str, Sequence[str], None] = "656a73efafec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "email_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, comment="ID"),
        sa.Column("user_id", sa.BigInteger(), nullable=True, comment="ID пользователя"),
        sa.Column("user_email", sa.String(), nullable=True, comment="Адрес EMail"),
        sa.Column("event_code", sa.String(), nullable=False, comment="Код события"),
        sa.Column("subject", sa.String(), nullable=False, comment="Тема"),
        sa.Column("body", sa.String(), nullable=False, comment="Тело"),
        sa.Column(
            "is_sent",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="Флаг отправки",
        ),
        sa.Column("is_error", sa.Boolean(), nullable=True, comment="Флаг ошибки"),
        sa.Column("sending_errors", postgresql.JSONB(), nullable=True, comment="Сообщения об ошибках"),
        sa.Column(
            "repeated_attempts",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Количество повторных попыток отправки",
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_messages")),
        comment="Список email сообщений",
    )

    op.create_foreign_key(
        op.f("fk_email_messages_user_id_users"),
        "email_messages",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_foreign_key(
        op.f("fk_email_messages_created_by_users"),
        "email_messages",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_email_messages_updated_by_users"),
        "email_messages",
        "users",
        ["updated_by"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("email_messages")
