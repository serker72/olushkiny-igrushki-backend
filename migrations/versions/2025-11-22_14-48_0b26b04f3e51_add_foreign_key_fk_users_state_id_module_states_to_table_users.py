"""add foreign_key fk_users_state_id_module_states to table users

Revision ID: 0b26b04f3e51
Revises: 45934804764a
Create Date: 2025-11-22 14:48:31.102039

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0b26b04f3e51"
down_revision: Union[str, Sequence[str], None] = "45934804764a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_foreign_key(
        op.f("fk_users_state_id_module_states"),
        "users",
        "module_states",
        ["state_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("fk_users_state_id_module_states"),
        "users",
        type_="foreignkey",
    )
