"""
Unit tests for services/registry_watcher.py — npm registry polling.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.registry_watcher import fetch_latest_version, fetch_package_versions


@pytest.mark.asyncio
async def test_fetch_latest_version_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "dist-tags": {"latest": "2.0.0"},
        "time": {"2.0.0": "2026-09-01T12:00:00.000Z"},
        "versions": {
            "2.0.0": {
                "homepage": "https://axios-http.com",
            }
        },
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp)):
        result = await fetch_latest_version("axios")
        assert result is not None
        assert result["version"] == "2.0.0"
        assert result["changelog_url"] == "https://axios-http.com"


@pytest.mark.asyncio
async def test_fetch_latest_version_error_returns_none():
    with patch("httpx.AsyncClient.get", AsyncMock(side_effect=Exception("HTTP 500"))):
        result = await fetch_latest_version("broken-pkg")
        assert result is None


@pytest.mark.asyncio
async def test_fetch_package_versions_success():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "versions": {
            "1.0.0": {},
            "1.1.0": {},
            "2.0.0": {},
        }
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", AsyncMock(return_value=mock_resp)):
        versions = await fetch_package_versions("my-lib")
        assert versions == ["2.0.0", "1.1.0", "1.0.0"]


@pytest.mark.asyncio
async def test_fetch_package_versions_error_returns_empty():
    with patch("httpx.AsyncClient.get", AsyncMock(side_effect=Exception("Network error"))):
        versions = await fetch_package_versions("unknown")
        assert versions == []
