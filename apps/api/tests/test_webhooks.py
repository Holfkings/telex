"""
Tests for webhook handlers — Section 5.3 acceptance rate tracking.
"""
import uuid
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from db.models import Repo, PullRequest
from routers.webhooks import _handle_pull_request


@pytest.mark.asyncio
async def test_handle_pull_request_merged(monkeypatch):
    repo_id = uuid.uuid4()
    pr_id = uuid.uuid4()

    mock_repo = Repo(
        id=repo_id,
        github_repo_id=12345,
        full_name="org/repo",
    )

    mock_pr = PullRequest(
        id=pr_id,
        repo_id=repo_id,
        github_pr_number=42,
        github_pr_url="https://github.com/org/repo/pull/42",
        status="open",
        merged=False,
    )

    session = AsyncMock()

    async def fake_execute(stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt)
        if "repos" in stmt_str:
            mock_result.scalar_one_or_none.return_value = mock_repo
        elif "pull_requests" in stmt_str:
            mock_result.scalar_one_or_none.return_value = mock_pr
        else:
            mock_result.scalar_one_or_none.return_value = None
        return mock_result

    session.execute = AsyncMock(side_effect=fake_execute)
    session.commit = AsyncMock()

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=session)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("routers.webhooks.AsyncSessionLocal", lambda: mock_ctx)

    payload = {
        "action": "closed",
        "pull_request": {
            "number": 42,
            "merged": True,
            "merged_at": "2026-09-15T12:00:00Z",
            "closed_at": "2026-09-15T12:00:00Z",
        },
        "repository": {
            "id": 12345,
        },
    }

    await _handle_pull_request(payload)

    assert mock_pr.status == "merged"
    assert mock_pr.merged is True
    assert mock_pr.merged_at is not None
    assert mock_pr.closed_at is not None
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_pull_request_closed_unmerged(monkeypatch):
    repo_id = uuid.uuid4()
    pr_id = uuid.uuid4()

    mock_repo = Repo(
        id=repo_id,
        github_repo_id=12345,
        full_name="org/repo",
    )

    mock_pr = PullRequest(
        id=pr_id,
        repo_id=repo_id,
        github_pr_number=43,
        github_pr_url="https://github.com/org/repo/pull/43",
        status="open",
        merged=False,
    )

    session = AsyncMock()

    async def fake_execute(stmt):
        mock_result = MagicMock()
        stmt_str = str(stmt)
        if "repos" in stmt_str:
            mock_result.scalar_one_or_none.return_value = mock_repo
        elif "pull_requests" in stmt_str:
            mock_result.scalar_one_or_none.return_value = mock_pr
        else:
            mock_result.scalar_one_or_none.return_value = None
        return mock_result

    session.execute = AsyncMock(side_effect=fake_execute)
    session.commit = AsyncMock()

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=session)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("routers.webhooks.AsyncSessionLocal", lambda: mock_ctx)

    payload = {
        "action": "closed",
        "pull_request": {
            "number": 43,
            "merged": False,
            "merged_at": None,
            "closed_at": "2026-09-15T12:05:00Z",
        },
        "repository": {
            "id": 12345,
        },
    }

    await _handle_pull_request(payload)

    assert mock_pr.status == "closed"
    assert mock_pr.merged is False
    assert mock_pr.merged_at is None
    assert mock_pr.closed_at is not None
    session.commit.assert_awaited_once()
