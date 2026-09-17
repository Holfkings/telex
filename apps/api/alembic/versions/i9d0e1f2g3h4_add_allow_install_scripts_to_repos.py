"""add_allow_install_scripts_to_repos

Revision ID: i9d0e1f2g3h4
Revises: h8c9d0e1f2g3
Create Date: 2026-09-17 22:50:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i9d0e1f2g3h4"
down_revision: Union[str, Sequence[str], None] = "h8c9d0e1f2g3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "repos",
        sa.Column(
            "allow_install_scripts",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("repos", "allow_install_scripts")
