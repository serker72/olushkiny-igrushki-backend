"""insert module_states

Revision ID: 45934804764a
Revises: 212b94f277b3
Create Date: 2025-07-16 17:13:31.433537

"""

from typing import Sequence, Union

import sqlalchemy as sa

from common.helpers.database import add_record_to_table, delete_record_from_table, get_op_connection, get_table_records

# revision identifiers, used by Alembic.
revision: str = "45934804764a"
down_revision: Union[str, Sequence[str], None] = "212b94f277b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_module_states() -> dict:
    return {
        "users": [
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
        "roles": [
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
        "organizations": [
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

    con.execute(sa.text("SELECT setval('module_states_id_seq', 1, false)"))
