"""add_merged_and_merged_at_to_pull_requests

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-15 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add merged and merged_at columns to pull_requests."""
    op.add_column("pull_requests", sa.Column("merged", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("pull_requests", sa.Column("merged_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove merged and merged_at columns from pull_requests."""
    op.drop_column("pull_requests", "merged_at")
    op.drop_column("pull_requests", "merged")
