"""insert properties for module products

Revision ID: 760c22cb6a82
Revises: 0c1f2ca49d1d
Create Date: 2026-06-06 13:44:06.193183

"""

from typing import Sequence, Union

from sqlalchemy import text

from common.helpers.database import add_record_to_table, delete_record_from_table, get_op_connection, get_table_records

# revision identifiers, used by Alembic.
revision: str = "760c22cb6a82"
down_revision: Union[str, Sequence[str], None] = "0c1f2ca49d1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def get_module_product_properties() -> dict:
    return {
        "products": [
            {
                "name": "Время",
                "is_required": True,
                "is_active": True,
            },
            {
                "name": "Оформление",
                "is_required": True,
                "is_active": True,
            },
            {
                "name": "Нитки",
                "is_required": True,
                "is_active": True,
            },
            {
                "name": "Наполнитель",
                "is_required": True,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 5",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 6",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 7",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 8",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 9",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 10",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 11",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза, диаметр 12",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 5",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 6",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 7",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 8",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 9",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 10",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 11",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Глаза п/б, диаметр 12",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Клей Момент",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Клей пистолет",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Бусины А 256",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Основа + колечко",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Волосы",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Нос 10х12",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Пластик",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Акрил",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Лак волосы",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Лак ногти",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Пуговица",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Пластырь",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Проволока",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Шерсть",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Фетр",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Кирка",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Фонарь",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Каска",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Табличка",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Спил",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Тонировка",
                "is_required": False,
                "is_active": True,
            },
            {
                "name": "Магнит 30х3",
                "is_required": False,
                "is_active": True,
            },
        ],
    }


def upgrade() -> None:
    """Upgrade schema."""
    con = get_op_connection()

    modules = get_table_records(con, "modules")
    for code, items in get_module_product_properties().items():
        module_id = modules.get(code)

        sql = "UPDATE modules SET is_used_entity_properties = true WHERE id = :module_id"
        con.execute(text(sql), {"module_id": module_id})

        for item in items:
            item["module_id"] = module_id
            add_record_to_table(con, "properties", item)


def downgrade() -> None:
    """Downgrade schema."""
    con = get_op_connection()

    modules = get_table_records(con, "modules")
    for code, items in get_module_product_properties().items():
        module_id = modules.get(code)

        sql = "UPDATE modules SET is_used_entity_properties = false WHERE id = :module_id"
        con.execute(text(sql), {"module_id": module_id})

        for item in items:
            item["module_id"] = module_id
            delete_record_from_table(con, "properties", ["module_id", "name"], item)
