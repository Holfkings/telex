"""
Unit tests for jobs/queue.py — job payload installation resolution and queue helpers.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from jobs.queue import (
    _resolve_payload_installation_id,
    _resolve_job_installation_id,
    enqueue_job,
)
from db.models import Job


@pytest.mark.asyncio
async def test_resolve_payload_direct_installation_id():
    session = AsyncMock()
    payload = {"installation_id": "inst-123", "data": "value"}
    iid = await _resolve_payload_installation_id(session, payload)
    assert iid == "inst-123"


@pytest.mark.asyncio
async def test_resolve_payload_non_dict():
    session = AsyncMock()
    assert await _resolve_payload_installation_id(session, None) is None
    assert await _resolve_payload_installation_id(session, "string") is None


@pytest.mark.asyncio
async def test_resolve_job_installation_id():
    session = AsyncMock()
    job = Job(payload={"installation_id": "inst-999"})
    iid = await _resolve_job_installation_id(session, job)
    assert iid == "inst-999"


@pytest.mark.asyncio
async def test_enqueue_job():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    payload = {"installation_id": "inst-abc", "file": "index.ts"}
    job = await enqueue_job(session, "scan_repo", payload, run_after_seconds=10)
    assert job.job_type == "scan_repo"
    assert job.status == "queued"
    assert job.payload["installation_id"] == "inst-abc"
    session.add.assert_called_once()
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_resolve_payload_from_repo_id():
    session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = "inst-resolved-repo"
    session.execute = AsyncMock(return_value=mock_res)

    iid = await _resolve_payload_installation_id(session, {"repo_id": str(uuid.uuid4())})
    assert iid == "inst-resolved-repo"


@pytest.mark.asyncio
async def test_dequeue_job_empty_queue():
    from jobs.queue import dequeue_job

    session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value = []
    session.execute = AsyncMock(return_value=mock_res)
    session.rollback = AsyncMock()

    job = await dequeue_job(session, "worker-1")
    assert job is None
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_dequeue_job_claims_successfully(monkeypatch):
    from jobs.queue import dequeue_job

    session = AsyncMock()
    candidate_job = Job(
        id=uuid.uuid4(),
        status="queued",
        payload={"installation_id": "inst-1"},
        attempts=0,
    )
    mock_res = MagicMock()
    mock_res.scalars.return_value = [candidate_job]
    session.execute = AsyncMock(return_value=mock_res)
    session.commit = AsyncMock()
    session.get_bind = MagicMock(return_value=MagicMock(dialect=MagicMock(name="sqlite")))

    monkeypatch.setattr("jobs.queue._count_running_for_installation", AsyncMock(return_value=0))
    claimed = await dequeue_job(session, "worker-1")
    assert claimed is candidate_job
    assert claimed.status == "running"
    assert claimed.locked_by == "worker-1"
    assert claimed.attempts == 1
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_payload_from_code_usage_and_patch():
    from jobs.queue import _resolve_payload_installation_id, _count_running_for_installation

    session = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = "inst-from-chain"
    session.execute = AsyncMock(return_value=mock_res)

    # 1. code_usage_id
    iid1 = await _resolve_payload_installation_id(session, {"code_usage_id": str(uuid.uuid4())})
    assert iid1 == "inst-from-chain"

    # 2. patch_id
    iid2 = await _resolve_payload_installation_id(session, {"patch_id": str(uuid.uuid4())})
    assert iid2 == "inst-from-chain"

    # 3. count running
    mock_count_res = MagicMock()
    mock_count_res.one_or_none.return_value = (3,)
    session.execute = AsyncMock(return_value=mock_count_res)
    cnt = await _count_running_for_installation(session, "inst-from-chain")
    assert cnt == 3
