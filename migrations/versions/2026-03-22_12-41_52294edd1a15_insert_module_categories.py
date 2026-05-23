"""insert module categories

Revision ID: 52294edd1a15
Revises: 42d8550a7dad
Create Date: 2026-03-22 12:41:02.835580

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from common.helpers.database import add_record_to_table, delete_record_from_table, get_op_connection, get_table_records

# revision identifiers, used by Alembic.
revision: str = "52294edd1a15"
down_revision: Union[str, Sequence[str], None] = "42d8550a7dad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_module_states() -> dict:
    return {
        "categories": [
            {
                "flag": 1,
                "code": "approved",
                "title": "Активна",
            },
            {
                "flag": 8192,
                "code": "blocked",
                "title": "Заблокирована",
            },
            {
                "flag": 16384,
                "code": "deleted",
                "title": "Удалена",
            },
        ],
    }


def upgrade() -> None:
    """Upgrade schema."""
    con = get_op_connection()

    sql = "INSERT INTO modules(code, title) VALUES ('categories', 'Категории')"
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

    sql = "DELETE FROM modules WHERE code = 'categories'"
    con.execute(sa.text(sql))
