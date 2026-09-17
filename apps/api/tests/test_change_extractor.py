"""
Unit tests for services/change_extractor.py — parsing changelogs into structured breaking changes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.change_extractor import extract_breaking_changes, EXTRACT_PROMPT


def test_extract_prompt_format():
    prompt = EXTRACT_PROMPT.format(
        package_name="test-pkg",
        old_version="1.0.0",
        new_version="2.0.0",
        changelog="Removed foo()",
    )
    assert "PACKAGE: test-pkg" in prompt
    assert "OLD VERSION: 1.0.0" in prompt
    assert "NEW VERSION: 2.0.0" in prompt
    assert "Removed foo()" in prompt


@pytest.mark.asyncio
async def test_extract_breaking_changes_json_array():
    mock_resp = MagicMock()
    mock_resp.text = """
    [
        {
            "change_type": "removed",
            "symbol_old": "oldMethod",
            "symbol_new": null,
            "description": "oldMethod has been removed.",
            "confidence": 0.95
        }
    ]
    """
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    with patch("google.genai.Client", return_value=mock_client):
        changes = await extract_breaking_changes(
            package_name="my-lib",
            old_version="1.0",
            new_version="2.0",
            changelog="Deprecations and removals: oldMethod is gone.",
        )
        assert len(changes) == 1
        assert changes[0]["change_type"] == "removed"
        assert changes[0]["symbol_old"] == "oldMethod"


@pytest.mark.asyncio
async def test_extract_breaking_changes_markdown_fenced():
    mock_resp = MagicMock()
    mock_resp.text = """```json
    [
        {
            "change_type": "renamed",
            "symbol_old": "foo",
            "symbol_new": "bar",
            "description": "foo renamed to bar",
            "confidence": 0.9
        }
    ]
    ```"""
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    with patch("google.genai.Client", return_value=mock_client):
        changes = await extract_breaking_changes("lib", "1.0", "2.0", "diff")
        assert len(changes) == 1
        assert changes[0]["symbol_new"] == "bar"


@pytest.mark.asyncio
async def test_extract_breaking_changes_empty_returns_value_error():
    mock_resp = MagicMock()
    mock_resp.text = None
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_resp)

    with patch("google.genai.Client", return_value=mock_client):
        with pytest.raises(ValueError, match="model returned no text"):
            await extract_breaking_changes("lib", "1.0", "2.0", "empty")
