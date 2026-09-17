"""
Unit tests for db/session.py and config.py — database session lifecycle and environment validation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from config import get_settings, Settings
from db.session import get_session


def test_get_settings_returns_instance():
    s = get_settings()
    assert isinstance(s, Settings)
    assert s.demo_key == "telex_demo_secret_2026"


@pytest.mark.asyncio
async def test_get_session_lifecycle_normal():
    mock_session = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    mock_maker = MagicMock()
    mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("db.session.AsyncSessionLocal", mock_maker):
        session_gen = get_session()
        session = await session_gen.__anext__()
        assert session is mock_session
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
        mock_session.rollback.assert_not_called()
        mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_lifecycle_exception():
    mock_session = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()

    mock_maker = MagicMock()
    mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)

    with patch("db.session.AsyncSessionLocal", mock_maker):
        session_gen = get_session()
        session = await session_gen.__anext__()
        assert session is mock_session
        with pytest.raises(RuntimeError):
            await session_gen.athrow(RuntimeError("DB query failed"))
        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()
