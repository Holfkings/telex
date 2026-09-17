"""
Unit tests for schemas.py — Pydantic models serialization and validation.
"""

import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from schemas import (
    UserOut,
    CommitInfo,
    RepoOut,
    RepoDetailOut,
    RepoUpdateIn,
    RepoToggleIn,
    AIExplainOut,
    CommitInsight,
    PatchOut,
    RepoPatchesOut,
    DetectedChangeSummary,
    StatsOut,
    GitHubInstallationEvent,
    RescanIn,
)


def test_user_out_schema():
    uid = uuid.uuid4()
    data = {
        "id": uid,
        "github_login": "testuser",
        "email": "test@example.com",
        "avatar_url": "https://avatars.example.com/u/1",
    }
    user = UserOut(**data)
    assert user.github_login == "testuser"
    assert user.id == uid


def test_repo_out_defaults():
    now = datetime.now(timezone.utc)
    repo = RepoOut(
        id="repo-1",
        full_name="owner/repo",
        created_at=now,
        github_url="https://github.com/owner/repo",
    )
    assert repo.default_branch == "main"
    assert repo.is_active is True
    assert repo.patch_count == 0
    assert repo.status == "healthy"
    assert repo.allow_install_scripts is False


def test_repo_detail_out_with_commits():
    now = datetime.now(timezone.utc)
    commit = CommitInfo(
        hash="abc1234567890",
        short_hash="abc1234",
        message="feat: init",
        author="Dev",
        email="dev@example.com",
        date="2026-09-17",
        relative_time="1 hour ago",
    )
    detail = RepoDetailOut(
        id="repo-1",
        full_name="owner/repo",
        created_at=now,
        github_url="https://github.com/owner/repo",
        commits=[commit],
    )
    assert len(detail.commits) == 1
    assert detail.commits[0].short_hash == "abc1234"
    assert detail.allow_install_scripts is False


def test_repo_update_in():
    up = RepoUpdateIn(requires_tests=True, requires_typecheck=False, allow_install_scripts=True)
    assert up.requires_tests is True
    assert up.requires_typecheck is False
    assert up.allow_install_scripts is True
    assert up.is_active is None


def test_repo_toggle_in():
    toggle = RepoToggleIn(is_active=False)
    assert toggle.is_active is False


def test_ai_explain_out():
    insight = CommitInsight(hash="123", impact="High", risk_level="low")
    explanation = AIExplainOut(
        summary="Architecture summary",
        commit_insights=[insight],
        architecture_verdict="healthy",
        risk_score=15,
        recommended_actions=["update dependencies"],
    )
    assert explanation.risk_score == 15
    assert len(explanation.commit_insights) == 1


def test_patch_out():
    now = datetime.now(timezone.utc)
    patch = PatchOut(
        id="patch-1",
        package="axios",
        old_version="1.0.0",
        new_version="2.0.0",
        status="verified",
        opened_at=now,
    )
    assert patch.usages_patched == 1
    assert patch.status == "verified"
    assert patch.confidence is None
    assert patch.is_semantic_risk is None

    patch_risky = PatchOut(
        id="patch-2",
        package="axios",
        old_version="1.0.0",
        new_version="2.0.0",
        status="verified",
        opened_at=now,
        confidence=0.85,
        is_semantic_risk=True,
    )
    assert patch_risky.confidence == 0.85
    assert patch_risky.is_semantic_risk is True


def test_stats_out():
    now = datetime.now(timezone.utc)
    dc = DetectedChangeSummary(
        id="dc-1",
        symbol_old="oldFunc",
        change_type="removed",
        description="Removed oldFunc",
        created_at=now,
        confidence=0.9,
        is_semantic_risk=False,
    )
    stats = StatsOut(
        repos_watched=5,
        prs_opened=10,
        patches_generated=8,
        merge_rate=0.8,
        recent_changes=[dc],
    )
    assert stats.repos_watched == 5
    assert stats.merge_rate == 0.8
    assert len(stats.recent_changes) == 1
    assert stats.recent_changes[0].confidence == 0.9
    assert stats.recent_changes[0].is_semantic_risk is False


def test_rescan_in():
    rescan = RescanIn(package_name="lodash", old_version="4.0", new_version="5.0")
    assert rescan.package_name == "lodash"
    assert rescan.changelog is None
