"""add_validate_patch_to_ck_jobs_type

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-15 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add validate_patch to ck_jobs_type check constraint."""
    op.drop_constraint("ck_jobs_type", "jobs", type_="check")
    op.create_check_constraint(
        "ck_jobs_type",
        "jobs",
        "job_type IN ('poll_registry','extract_changes','scan_repo','generate_patch','validate_patch','open_pr')",
    )


def downgrade() -> None:
    """Remove validate_patch from ck_jobs_type check constraint."""
    op.drop_constraint("ck_jobs_type", "jobs", type_="check")
    op.create_check_constraint(
        "ck_jobs_type",
        "jobs",
        "job_type IN ('poll_registry','extract_changes','scan_repo','generate_patch','open_pr')",
    )
