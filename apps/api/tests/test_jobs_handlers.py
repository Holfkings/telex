"""
Unit tests for jobs/handlers/ — testing poll_registry, extract_changes, and scan_repo.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from jobs.handlers.poll_registry import run as poll_registry_run
from jobs.handlers.extract_changes import run as extract_changes_run
from jobs.handlers.scan_repo import run as scan_repo_run


@pytest.mark.asyncio
async def test_poll_registry_no_version_found():
    with patch("services.registry_watcher.fetch_latest_version", AsyncMock(return_value=None)):
        # Should cleanly return without errors
        await poll_registry_run({"package_id": str(uuid.uuid4()), "package_name": "unknown"})


@pytest.mark.asyncio
async def test_poll_registry_already_known_version():
    latest_meta = {"version": "1.0.0", "published_at": None}
    with patch(
        "services.registry_watcher.fetch_latest_version", AsyncMock(return_value=latest_meta)
    ):
        with patch("db.session.AsyncSessionLocal") as mock_ctx:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session.execute = AsyncMock(
                return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=MagicMock()))
            )
            mock_ctx.return_value = mock_session

            await poll_registry_run({"package_id": str(uuid.uuid4()), "package_name": "known-pkg"})
            mock_session.add.assert_not_called()


@pytest.mark.asyncio
async def test_extract_changes_missing_package_version():
    with patch("db.session.AsyncSessionLocal") as mock_ctx:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get = AsyncMock(return_value=None)
        mock_ctx.return_value = mock_session

        # Should cleanly log and return
        await extract_changes_run(
            {
                "package_version_id": str(uuid.uuid4()),
                "package_name": "pkg",
            }
        )


@pytest.mark.asyncio
async def test_extract_changes_empty_changes():
    mock_pv = MagicMock()
    mock_pv.version = "2.0.0"
    mock_pv.changelog_raw = "None"
    with patch("db.session.AsyncSessionLocal") as mock_ctx:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get = AsyncMock(return_value=mock_pv)
        mock_session.commit = AsyncMock()
        mock_ctx.return_value = mock_session

        with patch(
            "services.change_extractor.extract_breaking_changes", AsyncMock(return_value=[])
        ):
            await extract_changes_run(
                {
                    "package_version_id": str(uuid.uuid4()),
                    "package_name": "pkg",
                }
            )
            mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_scan_repo_missing_repo():
    with patch("db.session.AsyncSessionLocal") as mock_ctx:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get = AsyncMock(return_value=None)
        mock_ctx.return_value = mock_session

        await scan_repo_run(
            {
                "repo_id": str(uuid.uuid4()),
                "package_version_id": str(uuid.uuid4()),
            }
        )


@pytest.mark.asyncio
async def test_extract_changes_with_detected_changes(monkeypatch):
    from db.models import PackageVersion, RepoPackage

    pv_id = uuid.uuid4()
    pkg_id = uuid.uuid4()
    repo_id = uuid.uuid4()

    mock_pv = PackageVersion(
        id=pv_id,
        package_id=pkg_id,
        version="2.0.0",
        changelog_raw="Breaking: renamed oldMethod to newMethod",
    )
    mock_rp = RepoPackage(repo_id=repo_id, package_id=pkg_id)

    mock_changes = [
        {
            "change_type": "renamed_symbol",
            "symbol_old": "oldMethod",
            "symbol_new": "newMethod",
            "description": "renamed function",
            "confidence": 0.95,
        }
    ]

    with patch("db.session.AsyncSessionLocal") as mock_ctx:
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session.get = AsyncMock(return_value=mock_pv)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=[mock_rp]))
        )
        mock_ctx.return_value = mock_session

        enqueued = []

        async def fake_enqueue(session, job_type, payload):
            enqueued.append((job_type, payload))

        monkeypatch.setattr("jobs.queue.enqueue_job", fake_enqueue)

        with patch(
            "services.change_extractor.extract_breaking_changes",
            AsyncMock(return_value=mock_changes),
        ):
            await extract_changes_run(
                {
                    "package_version_id": str(pv_id),
                    "package_name": "pkg-a",
                    "old_version": "1.0.0",
                    "changelog": "some changelog",
                }
            )
            assert mock_session.add.called
            assert mock_session.commit.called
            assert len(enqueued) == 1
            assert enqueued[0][0] == "scan_repo"
            assert enqueued[0][1]["repo_id"] == str(repo_id)
