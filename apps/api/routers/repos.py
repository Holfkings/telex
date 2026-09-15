"""
Repos API — list live repositories, commit history, and Gemini 2.5 Flash architecture insights.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, or_, cast, Text
from datetime import datetime, timezone
import uuid

from db.session import AsyncSessionLocal
from db.models import Repo, Patch, CodeUsage, PullRequest, ValidationRun, DetectedChange
from services.repo_service import get_core_repositories_async, explain_repo_with_gemini
from schemas import RepoOut, RepoDetailOut, AIExplainOut, RepoToggleIn, RepoUpdateIn, RepoPatchesOut, PatchOut
from routers.auth import require_auth

router = APIRouter(prefix="/api/repos", tags=["repos"])


@router.get("", response_model=list[RepoOut])
async def list_repos():
    """Return all active monitored repositories with live git commit metadata."""
    repos = await get_core_repositories_async()
    return repos


@router.get("/{repo_id}", response_model=RepoDetailOut)
async def get_repo_details(repo_id: str):
    """Return full repository detail with full recent commit history."""
    repos = await get_core_repositories_async()
    repo = next((r for r in repos if r["id"] == repo_id or r["full_name"] == repo_id or r["name"] == repo_id), None)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")
    return repo


@router.post("/{repo_id}/ai-explain", response_model=AIExplainOut)
async def ai_explain_repo(repo_id: str):
    """Invoke Gemini 2.5 Flash to generate live architectural and commit analysis."""
    try:
        explanation = await explain_repo_with_gemini(repo_id)
        return explanation
    except KeyError:
        raise HTTPException(status_code=404, detail="Repo not found")


@router.post("/{repo_id}/toggle", response_model=dict, dependencies=[Depends(require_auth)])
async def toggle_repo(repo_id: str, body: RepoToggleIn):
    """Toggle monitoring state for a repository."""
    repos = await get_core_repositories_async()
    repo = next((r for r in repos if r["id"] == repo_id or r["full_name"] == repo_id or r["name"] == repo_id), None)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")
    repo["is_active"] = body.is_active

    # Persist in DB if repository record exists
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Repo).where(Repo.full_name == repo["full_name"]).limit(1)
        )
        db_repo = result.scalar_one_or_none()
        if db_repo:
            db_repo.is_active = body.is_active
            await session.commit()

    return {"id": repo_id, "is_active": body.is_active}


@router.patch("/{repo_id}", response_model=dict)
async def update_repo_settings(repo_id: str, body: RepoUpdateIn):
    """Update repo verification policy (requires_tests, requires_typecheck) or monitoring status."""
    async with AsyncSessionLocal() as session:
        stmt = select(Repo).where(
            or_(
                cast(Repo.id, Text) == repo_id,
                Repo.full_name == repo_id,
            )
        ).limit(1)
        result = await session.execute(stmt)
        repo = result.scalar_one_or_none()
        if not repo:
            raise HTTPException(status_code=404, detail="Repo not found")

        if body.requires_tests is not None:
            repo.requires_tests = body.requires_tests
        if body.requires_typecheck is not None:
            repo.requires_typecheck = body.requires_typecheck
        if body.is_active is not None:
            repo.is_active = body.is_active

        await session.commit()
        return {
            "id": str(repo.id),
            "full_name": repo.full_name,
            "requires_tests": repo.requires_tests,
            "requires_typecheck": repo.requires_typecheck,
            "is_active": repo.is_active,
        }


@router.get("/{repo_id}/patches", response_model=RepoPatchesOut)
async def list_patches(repo_id: str):
    """Return recent patches for repository from real DB records (P1-8)."""
    repos = await get_core_repositories_async()
    repo = next((r for r in repos if r["id"] == repo_id or r["full_name"] == repo_id or r["name"] == repo_id), None)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")
    repo_name = repo["full_name"]

    patches_out: list[PatchOut] = []
    async with AsyncSessionLocal() as session:
        # Find DB repo row by full_name or id
        repo_res = await session.execute(
            select(Repo).where(
                or_(
                    Repo.full_name == repo_name,
                    cast(Repo.id, Text) == repo_id,
                )
            ).limit(1)
        )
        db_repo = repo_res.scalar_one_or_none()

        if db_repo:
            stmt = (
                select(Patch, CodeUsage)
                .join(CodeUsage, Patch.code_usage_id == CodeUsage.id)
                .where(CodeUsage.repo_id == db_repo.id)
                .order_by(Patch.created_at.desc())
                .limit(20)
            )
            res = await session.execute(stmt)
            for patch_row, cu_row in res.all():
                # Query associated pull request if opened
                pr_res = await session.execute(
                    select(PullRequest)
                    .where(
                        PullRequest.repo_id == db_repo.id,
                        PullRequest.patch_ids.contains([patch_row.id]),
                    )
                    .limit(1)
                )
                pr_row = pr_res.scalar_one_or_none()

                # Query latest validation run
                vr_res = await session.execute(
                    select(ValidationRun)
                    .where(ValidationRun.patch_id == patch_row.id)
                    .order_by(ValidationRun.created_at.desc())
                    .limit(1)
                )
                vr_row = vr_res.scalar_one_or_none()

                # Query detected change
                dc_res = await session.execute(
                    select(DetectedChange)
                    .where(DetectedChange.id == cu_row.detected_change_id)
                    .limit(1)
                )
                dc_row = dc_res.scalar_one_or_none()

                patches_out.append(
                    PatchOut(
                        id=str(patch_row.id),
                        package=cu_row.file_path,
                        old_version="current",
                        new_version="patched",
                        status="verified" if patch_row.verified else "generated",
                        pr_url=pr_row.github_pr_url if pr_row else f"https://github.com/{repo_name}",
                        usages_patched=1,
                        opened_at=patch_row.created_at if patch_row.created_at else datetime.now(timezone.utc),
                        diff=patch_row.diff,
                        verification_mode=vr_row.verification_mode if vr_row else "structural_only",
                        tests_passed=vr_row.tests_pass if vr_row else None,
                        typecheck_passed=vr_row.typechecks if vr_row else None,
                        change_type=dc_row.change_type if dc_row else None,
                        change_description=dc_row.description if dc_row else None,
                    )
                )

    return RepoPatchesOut(
        repo=repo_name,
        patches=patches_out,
    )
