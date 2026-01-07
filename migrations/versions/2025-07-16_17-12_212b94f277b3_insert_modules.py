"""insert modules

Revision ID: 212b94f277b3
Revises: 654e6510453c
Create Date: 2025-07-16 17:13:07.020379

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "212b94f277b3"
down_revision: Union[str, Sequence[str], None] = "654e6510453c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    sql = """
        INSERT INTO modules(code, title) VALUES 
        ('users', 'Пользователи'),
        ('roles', 'Роли'),
        ('organizations', 'Организации');
    """
    op.execute(sa.text(sql))


def downgrade() -> None:
    """Downgrade schema."""
    sql = """
        DELETE FROM modules;
        SELECT setval('modules_id_seq', 1, false)
    """
    op.execute(sa.text(sql))
