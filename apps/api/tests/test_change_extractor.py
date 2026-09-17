"""
Unit tests for services/change_extractor.py — parsing changelogs into structured breaking changes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.change_extractor import classify_risk, extract_breaking_changes, EXTRACT_PROMPT


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


# ── classify_risk tests ───────────────────────────────────────────────────────


def test_classify_risk_behavior_change_is_always_true():
    """behavior_change is always a semantic risk regardless of confidence."""
    assert classify_risk("behavior_change", 0.99) is True
    assert classify_risk("behavior_change", 0.50) is True
    assert classify_risk("behavior_change", 0.0) is True


def test_classify_risk_signature_change_low_confidence_is_true():
    """signature_change with confidence < 0.75 is risky (model is uncertain)."""
    assert classify_risk("signature_change", 0.74) is True
    assert classify_risk("signature_change", 0.0) is True


def test_classify_risk_deprecated_low_confidence_is_true():
    """deprecated with confidence < 0.75 is risky."""
    assert classify_risk("deprecated", 0.60) is True


def test_classify_risk_signature_change_high_confidence_is_false():
    """signature_change with confidence >= 0.75 is mechanical — not risky."""
    assert classify_risk("signature_change", 0.75) is False
    assert classify_risk("signature_change", 0.90) is False
    assert classify_risk("signature_change", 1.0) is False


def test_classify_risk_deprecated_high_confidence_is_false():
    """deprecated with confidence >= 0.75 is mechanical — not risky."""
    assert classify_risk("deprecated", 0.80) is False


def test_classify_risk_removed_is_always_false():
    """removed changes are mechanical regardless of confidence."""
    assert classify_risk("removed", 0.99) is False
    assert classify_risk("removed", 0.0) is False


def test_classify_risk_renamed_is_always_false():
    """renamed changes are mechanical regardless of confidence."""
    assert classify_risk("renamed", 0.99) is False
    assert classify_risk("renamed", 0.0) is False


def test_classify_risk_unknown_type_is_false():
    """Unrecognised types default to False (safe default)."""
    assert classify_risk("unknown", 0.5) is False


# ── PR body / title prefix tests ──────────────────────────────────────────────


from jobs.handlers.open_pr import build_pr_metadata


def _build_pr_body(change_type: str, confidence: float) -> tuple[str, str]:
    """Call production PR metadata formatting helper to verify title and classification table."""
    return build_pr_metadata(
        change_type=change_type,
        confidence=confidence,
        base_title="chore(deps): auto-patch for my-lib@2.0",
    )


def test_pr_body_semantic_risk_contains_warning_and_prefix():
    """For a behavior_change, PR title gets [semantic-risk] and body has warning row."""
    title, table = _build_pr_body("behavior_change", 0.85)
    assert title.startswith("[semantic-risk]")
    assert "## Change classification" in table
    assert "[Warning] Possible semantic/behavior change" in table
    assert "behavior_change" in table


def test_pr_body_mechanical_change_no_prefix():
    """For a high-confidence removed change, title has no prefix and body has safe row."""
    title, table = _build_pr_body("removed", 0.95)
    assert not title.startswith("[semantic-risk]")
    assert "[Safe] Mechanical change" in table
    assert "removed" in table


def test_pr_body_low_confidence_signature_change_is_semantic():
    """Low-confidence signature_change triggers [semantic-risk] prefix."""
    title, table = _build_pr_body("signature_change", 0.60)
    assert title.startswith("[semantic-risk]")
    assert "[Warning] Possible semantic/behavior change" in table


def test_pr_body_high_confidence_signature_change_is_mechanical():
    """High-confidence signature_change stays mechanical — no prefix."""
    title, table = _build_pr_body("signature_change", 0.90)
    assert not title.startswith("[semantic-risk]")
    assert "[Safe] Mechanical change" in table
