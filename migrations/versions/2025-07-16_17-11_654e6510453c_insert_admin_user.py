"""insert admin user

Revision ID: 654e6510453c
Revises: 0da975ad9668
Create Date: 2025-07-16 17:12:59.523416

"""

from typing import Sequence, Union

import sqlalchemy as sa

from common.helpers.database import get_op_connection

# revision identifiers, used by Alembic.
revision: str = "654e6510453c"
down_revision: Union[str, Sequence[str], None] = "0da975ad9668"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    con = get_op_connection()

    sql = """
        INSERT INTO users(state_id, surname, name, second_name, email)
        VALUES (:state_id, :surname, :name, :second_name, :email)
    """
    params = {
        "state_id": 1,
        "surname": "Керимов",
        "name": "Сергей",
        "second_name": "Константинович",
        "email": "admin@olushkiny-igrushki.ru",
    }
    con.execute(sa.text(sql), params)


def downgrade() -> None:
    """Downgrade schema."""
    sql = """
        DELETE FROM users WHERE email = :email;
        SELECT setval('users_id_seq', 1, false)
    """
    params = {"email": "admin@olushkiny-igrushki.ru"}
    con = get_op_connection()
    con.execute(sa.text(sql), params)
