"""create table users

Revision ID: 85e15ad2f2c0
Revises:
Create Date: 2025-07-11 16:33:30.783880

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "85e15ad2f2c0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="ID"),
        sa.Column("state_id", sa.BigInteger(), nullable=False, comment="ID статуса"),
        sa.Column("email", sa.String(), nullable=False, comment="Адрес e-mail"),
        sa.Column("surname", sa.String(), nullable=False, comment="Фамилия"),
        sa.Column("name", sa.String(), nullable=False, comment="Имя"),
        sa.Column("second_name", sa.String(), nullable=True, comment="Отчество"),
        # sa.Column("password", sa.String(), nullable=False, comment="Пароль"),
        sa.Column("phone", sa.String(), nullable=True, comment="Номер телефона"),
        sa.Column("birthday", sa.Date(), nullable=True, comment="Дата рождения"),
        sa.Column(
            "time_zone", sa.String(), nullable=False, server_default=sa.text("'Europe/Moscow'"), comment="Часовой пояс"
        ),
        sa.Column("last_logged_on", sa.DateTime(timezone=True), nullable=True, comment="Время последней авторизации"),
        # sa.Column(
        #     "incorrect_password_attempts",
        #     sa.SmallInteger(),
        #     server_default=sa.text("0"),
        #     comment="Количество попыток ввода неверного пароля",
        # ),
        # sa.Column(
        #     "incorrect_password_lockout_on",
        #     sa.DateTime(timezone=True),
        #     nullable=True,
        #     comment="Время окончания блокировки ввода пароля",
        # ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        comment="Список пользователей",
    )

    op.create_foreign_key(
        op.f("fk_users_created_by_users"),
        "users",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_users_updated_by_users"),
        "users",
        "users",
        ["updated_by"],
        ["id"],
    )

    op.create_index(
        op.f("uq_users_email"),
        "users",
        ["email"],
        unique=True,
    )

    op.create_index(
        op.f("uq_users_phone"),
        "users",
        ["phone"],
        unique=True,
        postgresql_where=sa.text("phone IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("users")
