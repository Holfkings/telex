"""
Pydantic request/response schemas — Section 9 API contract.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: uuid.UUID
    github_login: str
    email: Optional[str]
    avatar_url: Optional[str]

    model_config = {"from_attributes": True}


# ── Repos ─────────────────────────────────────────────────────────────────────

class CommitInfo(BaseModel):
    hash: str
    short_hash: str
    message: str
    author: str
    email: Optional[str] = None
    date: str
    relative_time: str


class RepoOut(BaseModel):
    id: str
    full_name: str
    name: Optional[str] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    default_branch: str = "main"
    is_active: bool = True
    requires_tests: bool = False
    requires_typecheck: bool = False
    created_at: datetime
    github_url: str
    languages: list[str] = []
    patch_count: int = 0
    status: str = "healthy"
    last_commit: Optional[CommitInfo] = None
    dependencies: list[str] = []

    model_config = {"from_attributes": True}


class RepoUpdateIn(BaseModel):
    requires_tests: Optional[bool] = None
    requires_typecheck: Optional[bool] = None
    is_active: Optional[bool] = None


class RepoDetailOut(RepoOut):
    commits: list[CommitInfo] = []


class CommitInsight(BaseModel):
    hash: str
    impact: str
    risk_level: str


class AIExplainOut(BaseModel):
    summary: str
    commit_insights: list[CommitInsight] = []
    architecture_verdict: str
    risk_score: int
    recommended_actions: list[str] = []


class RepoToggleIn(BaseModel):
    is_active: bool


# ── Patches ───────────────────────────────────────────────────────────────────

class PatchOut(BaseModel):
    id: str
    package: str
    old_version: str
    new_version: str
    status: str
    pr_url: Optional[str] = None
    usages_patched: int = 1
    opened_at: datetime
    diff: Optional[str] = None
    verification_mode: Optional[str] = None
    tests_passed: Optional[bool] = None
    typecheck_passed: Optional[bool] = None
    change_type: Optional[str] = None
    change_description: Optional[str] = None


class RepoPatchesOut(BaseModel):
    repo: str
    patches: list[PatchOut]


# ── Stats ─────────────────────────────────────────────────────────────────────

class DetectedChangeSummary(BaseModel):
    id: str
    symbol_old: str
    symbol_new: Optional[str] = None
    change_type: str
    description: str
    created_at: datetime


class StatsOut(BaseModel):
    repos_watched: int
    prs_opened: int
    patches_generated: int
    merge_rate: float  # fraction 0.0–1.0
    recent_changes: list[DetectedChangeSummary] = []


# ── Webhooks ──────────────────────────────────────────────────────────────────

class GitHubInstallationEvent(BaseModel):
    action: str
    installation: dict
    repositories: Optional[list[dict]] = None


# ── Rescan ────────────────────────────────────────────────────────────────────

class RescanIn(BaseModel):
    package_name: str
    old_version: str
    new_version: str
    changelog: Optional[str] = None


