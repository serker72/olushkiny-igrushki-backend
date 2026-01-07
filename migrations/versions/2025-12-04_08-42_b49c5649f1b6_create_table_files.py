"""create table files

Revision ID: b49c5649f1b6
Revises: 23e647aed9f7
Create Date: 2025-12-04 08:42:49.016124

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b49c5649f1b6"
down_revision: Union[str, Sequence[str], None] = "23e647aed9f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, comment="ID"),
        sa.Column("module_id", sa.Integer(), nullable=False, comment="ID модуля"),
        sa.Column("entity_id", sa.BigInteger(), nullable=True, comment="ID объекта"),
        sa.Column("entity_uuid", postgresql.UUID(as_uuid=True), nullable=True, comment="UUID объекта"),
        sa.Column("tmp_entity_uuid", postgresql.UUID(as_uuid=True), nullable=True, comment="Временный UUID объекта"),
        sa.Column("entity_field", sa.String(), nullable=False, comment="Поле объекта"),
        sa.Column("entity_field_index", sa.SmallInteger(), nullable=True, comment="Индекс поля объекта"),
        sa.Column("name", sa.String(), nullable=False, comment="Имя файла"),
        sa.Column("size", sa.BigInteger(), nullable=False, comment="Размер файла"),
        sa.Column("mime_type", sa.String(), nullable=False, comment="MIME-тип файла"),
        sa.Column("url", sa.String(), nullable=False, comment="Ссылка для получения файла"),
        sa.Column("image_width", sa.SmallInteger(), nullable=True, comment="Ширина изображения"),
        sa.Column("image_height", sa.SmallInteger(), nullable=True, comment="Высота изображения"),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_files")),
        comment="Список файлов",
    )

    op.create_foreign_key(
        op.f("fk_files_module_id_modules"),
        "files",
        "modules",
        ["module_id"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_files_created_by_users"),
        "files",
        "users",
        ["created_by"],
        ["id"],
    )

    op.create_foreign_key(
        op.f("fk_files_updated_by_users"),
        "files",
        "users",
        ["updated_by"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("files")
