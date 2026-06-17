"""insert module products

Revision ID: 5dbe44049a3d
Revises: 42d8550a7dad
Create Date: 2026-06-06 12:42:04.301080

"""

from typing import Sequence, Union

import sqlalchemy as sa

from common.helpers.database import add_record_to_table, delete_record_from_table, get_op_connection, get_table_records

# revision identifiers, used by Alembic.
revision: str = "5dbe44049a3d"
down_revision: Union[str, Sequence[str], None] = "42d8550a7dad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_module_states() -> dict:
    return {
        "products": [
            {
                "flag": 1,
                "code": "approved",
                "title": "Активен",
            },
            {
                "flag": 8192,
                "code": "blocked",
                "title": "Заблокирован",
            },
            {
                "flag": 16384,
                "code": "deleted",
                "title": "Удален",
            },
        ],
    }


def upgrade() -> None:
    """Upgrade schema."""
    con = get_op_connection()

    sql = "INSERT INTO modules(code, title) VALUES ('products', 'Товары')"
    con.execute(sa.text(sql))

    modules = get_table_records(con, "modules")
    for code, items in get_module_states().items():
        module_id = modules.get(code)
        for item in items:
            item["module_id"] = module_id
            item["hierarchy"] = f"{code}.{item['code']}"
            add_record_to_table(con, "module_states", item)


def downgrade() -> None:
    """Downgrade schema."""
    con = get_op_connection()

    modules = get_table_records(con, "modules")
    for code, items in get_module_states().items():
        module_id = modules.get(code)
        for item in items:
            item["module_id"] = module_id
            delete_record_from_table(con, "module_states", ["module_id", "code"], item)

    sql = "DELETE FROM modules WHERE code = 'products'"
    con.execute(sa.text(sql))
