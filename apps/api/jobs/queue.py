"""
Job queue engine — Section 7.3.
SELECT … FOR UPDATE SKIP LOCKED pattern (OpusQueue).

Phase 8 additions:
- dequeue_job now enforces a per-installation concurrent-job cap (option a
  from the spec: simple max-N running cap, not a full fair-share scheduler).
  The cap prevents one high-volume installation from starving all others.
"""
import logging
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import Job

logger = logging.getLogger(__name__)

# ── Phase 8.1: per-installation cap ─────────────────────────────────────────
# Maximum number of jobs in "running" state per installation_id.
# Default: 3. Override with env var TELEX_MAX_JOBS_PER_INSTALLATION.
import os as _os
_MAX_RUNNING_PER_INSTALLATION: int = int(_os.getenv("TELEX_MAX_JOBS_PER_INSTALLATION", "3"))


async def _count_running_for_installation(session: AsyncSession, installation_id: str) -> int:
    """Count how many jobs are currently running for a given installation_id."""
    # installation_id is stored as a JSON key inside the JSONB payload column.
    result = await session.execute(
        text(
            "SELECT COUNT(*) FROM jobs "
            "WHERE status = 'running' "
            "AND payload->>'installation_id' = :iid"
        ),
        {"iid": installation_id},
    )
    row = result.one_or_none()
    return int(row[0]) if row else 0


async def dequeue_job(session: AsyncSession, worker_id: str) -> Job | None:
    """
    Atomically claim the oldest queued job whose run_after is in the past,
    subject to the per-installation concurrent-job cap (Phase 8.1).

    Algorithm:
      1. Select the N oldest eligible queued jobs.
      2. For each candidate (oldest first), check whether its installation is
         already at the cap. If so, skip it and try the next.
      3. Claim the first uncapped job.

    Uses SKIP LOCKED so concurrent workers never block each other.
    Returns None if there are no jobs ready to run.
    """
    # Fetch up to 20 candidates at once to avoid per-row round-trips
    stmt = (
        select(Job)
        .where(Job.status == "queued", Job.run_after <= func.now())
        .order_by(Job.created_at)
        .limit(20)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    candidates = list(result.scalars())

    if not candidates:
        return None

    # Try to claim the first candidate whose installation isn't at the cap
    claimed_job: Job | None = None
    for job in candidates:
        iid = str(job.payload.get("installation_id", "")) if isinstance(job.payload, dict) else ""
        if iid:
            running = await _count_running_for_installation(session, iid)
            if running >= _MAX_RUNNING_PER_INSTALLATION:
                logger.debug(
                    "dequeue_job: installation %s is at cap (%d running) — skipping job %s",
                    iid, running, job.id,
                )
                continue
        # This job's installation is not at the cap (or has no installation_id)
        claimed_job = job
        break

    if claimed_job is None:
        return None

    claimed_job.status = "running"
    claimed_job.locked_by = worker_id
    claimed_job.locked_at = func.now()
    claimed_job.attempts += 1
    await session.commit()
    return claimed_job


async def enqueue_job(
    session: AsyncSession,
    job_type: str,
    payload: dict,
    run_after_seconds: int = 0,
) -> Job:
    """
    Insert a new job into the queue.

    Args:
        job_type: one of the values in the jobs.job_type CHECK constraint.
        payload: arbitrary dict passed to the handler.
        run_after_seconds: delay before the job becomes eligible to run.
    """
    from datetime import datetime, timedelta, timezone

    if run_after_seconds:
        run_after_expr = datetime.now(timezone.utc) + timedelta(seconds=run_after_seconds)
    else:
        run_after_expr = func.now()

    job = Job(
        job_type=job_type,
        payload=payload,
        status="queued",
        run_after=run_after_expr,  # type: ignore[arg-type]
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    logger.info("Enqueued job %s (type=%s)", job.id, job_type)
    return job
