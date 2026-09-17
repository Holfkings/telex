"""
Unit tests for routers/stats.py — dashboard summary and activity feed endpoints.
"""

import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from main import app
from db.session import get_session
from db.models import Repo, PullRequest, Patch, DetectedChange


@pytest.mark.asyncio
async def test_get_stats_empty():
    mock_session = AsyncMock()
    # Scalar returns for counts
    mock_session.execute = AsyncMock()
    mock_session.execute.side_effect = [
        MagicMock(scalar_one=MagicMock(return_value=2)),  # repos_count
        MagicMock(scalar_one=MagicMock(return_value=5)),  # prs_total
        MagicMock(scalar_one=MagicMock(return_value=4)),  # prs_merged
        MagicMock(scalar_one=MagicMock(return_value=3)),  # patches_count
        MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ),  # dc_res
    ]

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/stats")
            assert resp.status_code == 200
            data = resp.json()
            assert data["repos_watched"] == 2
            assert data["prs_opened"] == 5
            assert data["patches_generated"] == 3
            assert data["merge_rate"] == 0.8
            assert data["recent_changes"] == []
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_get_activity_empty():
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=[])),  # pr_res
        MagicMock(all=MagicMock(return_value=[])),  # patch_res
        MagicMock(all=MagicMock(return_value=[])),  # dc_res
    ]

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/activity")
            assert resp.status_code == 200
            data = resp.json()
            assert "activities" in data
            assert data["activities"] == []
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_get_stats_zero_prs():
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.execute.side_effect = [
        MagicMock(scalar_one=MagicMock(return_value=0)),  # repos_count
        MagicMock(scalar_one=MagicMock(return_value=0)),  # prs_total
        MagicMock(scalar_one=MagicMock(return_value=0)),  # prs_merged
        MagicMock(scalar_one=MagicMock(return_value=0)),  # patches_count
        MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ),  # dc_res
    ]

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/stats")
            assert resp.status_code == 200
            assert resp.json()["merge_rate"] == 0.0
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_get_activity_populated():
    mock_session = AsyncMock()
    now = datetime.now(timezone.utc)
    pr = MagicMock(
        id=uuid.uuid4(),
        status="merged",
        github_pr_number=101,
        github_pr_url="https://github.com/org/repo/pull/1",
        created_at=now,
        opened_at=now,
    )
    repo = MagicMock(full_name="org/repo")

    patch_obj = MagicMock(
        id=uuid.uuid4(),
        llm_provider="openai",
        verified=True,
        created_at=now,
    )
    cu = MagicMock(file_path="src/index.ts", status="patched")

    dc = MagicMock(
        id=uuid.uuid4(),
        symbol_old="legacyFunc",
        change_type="removed",
        description="Removed legacy function",
        created_at=now,
    )

    mock_session.execute = AsyncMock()
    mock_session.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=[(pr, repo)])),  # pr_res
        MagicMock(all=MagicMock(return_value=[(patch_obj, cu, repo)])),  # patch_res
        MagicMock(
            scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        ),  # vr_res
        MagicMock(all=MagicMock(return_value=[(dc, cu, repo)])),  # dc_res
    ]

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/activity")
            assert resp.status_code == 200
            activities = resp.json()["activities"]
            assert len(activities) == 3
            types = [a["type"] for a in activities]
            assert "pull_request" in types
            assert "patch" in types
            assert "detected_change" in types
    finally:
        app.dependency_overrides.pop(get_session, None)
