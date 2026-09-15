"""drop_engine_b_payment_recovery_tables

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop Engine B payment recovery tables and trim the job_type constraint."""

    # 1. Drop recovery_events first (FK depends on payment_attempts)
    op.drop_index("idx_recovery_events_payment_attempt_id", "recovery_events")
    op.drop_table("recovery_events")

    # 2. Drop payment_attempts
    op.drop_index("idx_payment_attempts_batch_request_id", "payment_attempts")
    op.drop_index("idx_payment_attempts_razorpay_order_id", "payment_attempts")
    op.drop_table("payment_attempts")

    # 3. Remove Engine B job types from the check constraint.
    #    First clean up any existing rows with obsolete Engine B job types
    #    so Postgres constraint validation passes cleanly.
    op.execute(
        "DELETE FROM jobs WHERE job_type IN ("
        "'detect_payment_failure','diagnose_runtime_failure','recover_runtime'"
        ")"
    )
    op.drop_constraint("ck_jobs_type", "jobs", type_="check")
    op.create_check_constraint(
        "ck_jobs_type",
        "jobs",
        "job_type IN ('poll_registry','extract_changes','scan_repo','generate_patch','open_pr')",
    )


def downgrade() -> None:
    """Restore Engine B tables and original job_type constraint."""

    # 1. Restore the original constraint (includes Engine B job types)
    op.drop_constraint("ck_jobs_type", "jobs", type_="check")
    op.create_check_constraint(
        "ck_jobs_type",
        "jobs",
        (
            "job_type IN ("
            "'poll_registry','extract_changes','scan_repo','generate_patch','open_pr',"
            "'detect_payment_failure','diagnose_runtime_failure','recover_runtime'"
            ")"
        ),
    )

    # 2. Recreate payment_attempts (source of truth: original PaymentAttempt model
    #    as it existed before Phase 1 deletion, including razorpay_event_id from
    #    migration c3d4e5f6a7b8 and retry_count from b2c3d4e5f6a7)
    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("razorpay_order_id", sa.Text(), nullable=False),
        sa.Column("razorpay_payment_id", sa.Text(), nullable=True),
        sa.Column("razorpay_event_id", sa.Text(), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="created"),
        sa.Column("injected_failure", sa.Text(), nullable=True),
        sa.Column("batch_request_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('created','success','failed')", name="ck_payment_attempts_status"),
        sa.UniqueConstraint("razorpay_event_id", name="uq_payment_attempts_razorpay_event_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_payment_attempts_razorpay_order_id", "payment_attempts", ["razorpay_order_id"])
    op.create_index("idx_payment_attempts_batch_request_id", "payment_attempts", ["batch_request_id"])

    # 3. Recreate recovery_events (source of truth: original RecoveryEvent model
    #    as it existed before Phase 1 deletion, including retry_count from b2c3d4e5f6a7)
    op.create_table(
        "recovery_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("payment_attempt_id", sa.UUID(), nullable=False),
        sa.Column("failure_type", sa.Text(), nullable=False),
        sa.Column("classification", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("action_taken", sa.Text(), nullable=False, server_default=""),
        sa.Column("llm_provider", sa.Text(), nullable=False, server_default="none"),
        sa.Column("llm_model", sa.Text(), nullable=False, server_default="none"),
        sa.Column("outcome", sa.Text(), nullable=False, server_default="unresolved"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pull_request_id", sa.UUID(), nullable=True),
        sa.Column("detected_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "classification IN ('transient','code_defect','unknown')",
            name="ck_recovery_events_classification",
        ),
        sa.CheckConstraint(
            "outcome IN ('recovered','escalated','unresolved')",
            name="ck_recovery_events_outcome",
        ),
        sa.ForeignKeyConstraint(["payment_attempt_id"], ["payment_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_recovery_events_payment_attempt_id", "recovery_events", ["payment_attempt_id"])
