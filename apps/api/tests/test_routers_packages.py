"""
Unit tests for routers/packages.py — package rescan endpoint.
"""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from main import app
from db.session import get_session
from db.models import Package


@pytest.mark.asyncio
async def test_rescan_package_not_found():
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=None)

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            pkg_id = str(uuid.uuid4())
            body = {
                "package_name": "unknown-pkg",
                "old_version": "1.0",
                "new_version": "2.0",
            }
            resp = await client.post(f"/api/packages/{pkg_id}/rescan", json=body)
            assert resp.status_code == 404
            assert resp.json()["detail"] == "Package not found"
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_rescan_package_success(monkeypatch):
    from db.models import PackageVersion

    pkg_id = uuid.uuid4()
    mock_pkg = Package(id=pkg_id, name="express", ecosystem="npm")

    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_pkg)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_res)

    enqueued_jobs = []

    async def fake_enqueue(session, job_type, payload):
        enqueued_jobs.append((job_type, payload))

    monkeypatch.setattr("routers.packages.enqueue_job", fake_enqueue)

    async def override_get_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            body = {
                "package_name": "express",
                "old_version": "4.17.0",
                "new_version": "4.18.0",
                "changelog": "Bugfixes and performance improvements",
            }
            resp = await client.post(f"/api/packages/{pkg_id}/rescan", json=body)
            assert resp.status_code == 202
            data = resp.json()
            assert data["status"] == "queued"
            assert len(enqueued_jobs) == 1
            assert enqueued_jobs[0][0] == "extract_changes"
    finally:
        app.dependency_overrides.pop(get_session, None)
