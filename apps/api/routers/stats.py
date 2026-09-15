"""
Stats API — dashboard summary counts.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from db.models import Repo, PullRequest, Patch, DetectedChange
from schemas import StatsOut, DetectedChangeSummary
from routers.auth import require_auth

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsOut)
async def get_stats(session: AsyncSession = Depends(get_session)):
    """Return aggregate counts and recent detected changes for the dashboard overview."""

    repos_count = (
        await session.execute(select(func.count(Repo.id)).where(Repo.is_active == True))
    ).scalar_one()

    prs_total = (
        await session.execute(select(func.count(PullRequest.id)))
    ).scalar_one()

    prs_merged = (
        await session.execute(
            select(func.count(PullRequest.id)).where(PullRequest.status == "merged")
        )
    ).scalar_one()

    patches_count = (
        await session.execute(select(func.count(Patch.id)).where(Patch.verified == True))
    ).scalar_one()

    merge_rate = (prs_merged / prs_total) if prs_total > 0 else 0.0

    dc_stmt = select(DetectedChange).order_by(DetectedChange.created_at.desc()).limit(5)
    dc_res = await session.execute(dc_stmt)
    recent_changes = [
        DetectedChangeSummary(
            id=str(dc.id),
            symbol_old=dc.symbol_old,
            symbol_new=dc.symbol_new,
            change_type=dc.change_type,
            description=dc.description,
            created_at=dc.created_at,
        )
        for dc in dc_res.scalars().all()
    ]

    return StatsOut(
        repos_watched=repos_count,
        prs_opened=prs_total,
        patches_generated=patches_count,
        merge_rate=round(merge_rate, 3),
        recent_changes=recent_changes,
    )


@router.get("/activity")
async def get_activity(session: AsyncSession = Depends(get_session)):
    """Return flat reverse-chronological activity across all repos (PRs, patches, detected changes)."""
    from db.models import CodeUsage, DetectedChange, PackageVersion, Package, ValidationRun
    from sqlalchemy.orm import selectinload

    activities: list[dict] = []

    # 1. Pull Requests
    pr_stmt = (
        select(PullRequest, Repo)
        .join(Repo, PullRequest.repo_id == Repo.id)
        .order_by(PullRequest.opened_at.desc())
        .limit(20)
    )
    pr_res = await session.execute(pr_stmt)
    for pr, repo in pr_res.all():
        activities.append({
            "id": f"pr-{pr.id}",
            "type": "pull_request",
            "repo_name": repo.full_name,
            "title": f"PR #{pr.github_pr_number} ({pr.status})",
            "description": f"Auto-patch delivery on {repo.full_name}",
            "status": pr.status,
            "url": pr.github_pr_url,
            "timestamp": pr.opened_at.isoformat() if pr.opened_at else None,
            "merged": getattr(pr, "merged", False),
        })

    # 2. Patches & Validation Runs
    patch_stmt = (
        select(Patch, CodeUsage, Repo)
        .join(CodeUsage, Patch.code_usage_id == CodeUsage.id)
        .join(Repo, CodeUsage.repo_id == Repo.id)
        .order_by(Patch.created_at.desc())
        .limit(20)
    )
    patch_res = await session.execute(patch_stmt)
    patch_rows = patch_res.all()

    vr_map = {}
    if patch_rows:
        patch_ids = [p.id for p, _, _ in patch_rows]
        vr_stmt = (
            select(ValidationRun)
            .where(ValidationRun.patch_id.in_(patch_ids))
            .order_by(ValidationRun.created_at.desc())
        )
        vr_res = await session.execute(vr_stmt)
        for vr in vr_res.scalars().all():
            if vr.patch_id not in vr_map:
                vr_map[vr.patch_id] = vr

    for patch_row, cu_row, repo_row in patch_rows:
        vr = vr_map.get(patch_row.id)
        activities.append({
            "id": f"patch-{patch_row.id}",
            "type": "patch",
            "repo_name": repo_row.full_name,
            "title": f"Patch for {cu_row.file_path}",
            "description": f"Candidate diff generated via {patch_row.llm_provider}",
            "status": "verified" if patch_row.verified else "unverified",
            "verification_mode": vr.verification_mode if vr else "structural_only",
            "timestamp": patch_row.created_at.isoformat() if patch_row.created_at else None,
            "url": None,
        })

    # 3. Detected Changes
    dc_stmt = (
        select(DetectedChange, CodeUsage, Repo)
        .join(CodeUsage, CodeUsage.detected_change_id == DetectedChange.id)
        .join(Repo, CodeUsage.repo_id == Repo.id)
        .order_by(DetectedChange.created_at.desc())
        .limit(20)
    )
    dc_res = await session.execute(dc_stmt)
    for dc_row, cu_row, repo_row in dc_res.all():
        activities.append({
            "id": f"change-{dc_row.id}",
            "type": "detected_change",
            "repo_name": repo_row.full_name,
            "title": f"{dc_row.symbol_old} ({dc_row.change_type})",
            "description": dc_row.description,
            "status": cu_row.status,
            "url": None,
            "timestamp": dc_row.created_at.isoformat() if dc_row.created_at else None,
        })

    # Sort all activities by timestamp descending
    activities.sort(
        key=lambda x: x.get("timestamp") or "",
        reverse=True,
    )
    return {"activities": activities[:50]}
