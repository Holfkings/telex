"""
open_pr handler — bundles all verified patches for a repo+version into one PR.

Payload shape:
    { "repo_id": "<uuid>", "package_version_id": "<uuid>" }
    or: { "repo_id": "<uuid>", "code_usage_id": "<uuid>" }
"""
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


def format_verification_disclosure(vr) -> str:
    """Derive accurate human-readable verification disclosure from actual validation run gates."""
    if not vr:
        return "⚠️ No verification run recorded for this patch."

    mode_display = getattr(vr, "verification_mode", None) or "structural_only"
    tests_pass = getattr(vr, "tests_pass", None)
    typechecks = getattr(vr, "typechecks", None)

    if mode_display == "full":
        if tests_pass is True and typechecks is True:
            return "✅ Verified: repo's own test suite and type-checker both passed on this patch."
        elif tests_pass is True:
            return "✅ Verified: repo's own test suite passed on this patch (type-check not run / not configured)."
        else:
            return "✅ Verified: isolated sandbox verification passed on this patch."
    else:
        return "⚠️ No test suite detected in this repo — this patch was validated by parse and type-check only, not by running tests."


async def run(payload: dict) -> None:
    from db.session import AsyncSessionLocal
    from db.models import (
        Repo, PackageVersion, Package, DetectedChange,
        CodeUsage, Patch, PullRequest, Installation,
    )
    from services.github_service import open_patch_pr, get_installation_client, create_check_run
    from sqlalchemy import select

    repo_id = uuid.UUID(payload["repo_id"])
    pv_id_raw = payload.get("package_version_id")
    package_version_id = uuid.UUID(pv_id_raw) if pv_id_raw else None
    cu_id_raw = payload.get("code_usage_id")
    code_usage_id = uuid.UUID(cu_id_raw) if cu_id_raw else None

    if package_version_id is None and code_usage_id is None:
        logger.error("open_pr: both package_version_id and code_usage_id are missing")
        return

    async with AsyncSessionLocal() as session:
        repo = await session.get(Repo, repo_id)
        if repo is None:
            logger.error("open_pr: repo %s not found", repo_id)
            return

        # PackageVersion may be absent for Engine B escalations
        if package_version_id is not None:
            pv = await session.get(PackageVersion, package_version_id)
            if pv is None:
                logger.error("open_pr: version %s not found", package_version_id)
                return
            pkg = await session.get(Package, pv.package_id)
            pkg_name = pkg.name if pkg else "unknown"
            pv_version = pv.version
        else:
            pkg_name = "dependency"
            pv_version = "patch"

        installation = await session.get(Installation, repo.installation_id)
        if installation is None:
            logger.error("open_pr: installation missing for repo %s", repo_id)
            return

        # Read scalar values before session closes
        repo_full_name = repo.full_name
        repo_default_branch = repo.default_branch
        installation_github_id = installation.github_installation_id

        # Collect verified patches
        if package_version_id is not None:
            patches_result = await session.execute(
                select(Patch)
                .join(CodeUsage, Patch.code_usage_id == CodeUsage.id)
                .join(DetectedChange, CodeUsage.detected_change_id == DetectedChange.id)
                .where(
                    CodeUsage.repo_id == repo_id,
                    DetectedChange.package_version_id == package_version_id,
                    Patch.verified == True,
                )
            )
        else:
            patches_result = await session.execute(
                select(Patch)
                .join(CodeUsage, Patch.code_usage_id == CodeUsage.id)
                .where(
                    CodeUsage.repo_id == repo_id,
                    CodeUsage.id == code_usage_id,
                    Patch.verified == True,
                )
            )
        patches = list(patches_result.scalars())

        if not patches:
            logger.info("open_pr: no verified patches for repo %s (version=%s, usage=%s)", repo_id, package_version_id, code_usage_id)
            return

        # Pre-load CodeUsage and ValidationRun rows
        usage_map: dict = {}
        vr_map: dict = {}
        from db.models import ValidationRun
        for p in patches:
            cu = await session.get(CodeUsage, p.code_usage_id)
            if cu:
                usage_map[p.id] = cu
            vr_res = await session.execute(
                select(ValidationRun)
                .where(ValidationRun.patch_id == p.id)
                .order_by(ValidationRun.created_at.desc())
                .limit(1)
            )
            vr = vr_res.scalar_one_or_none()
            if vr:
                vr_map[p.id] = vr

    # ── PyGithub calls run in a thread — they are blocking I/O ───────────────
    gh = await asyncio.to_thread(get_installation_client, installation_github_id)
    gh_repo = await asyncio.to_thread(gh.get_repo, repo_full_name)

    from services.github_service import open_patch_pr, get_installation_client, apply_diff_to_content

    patch_dicts: list[dict] = []
    for p in patches:
        cu = usage_map.get(p.id)
        if not cu:
            continue
        try:
            content_file = await asyncio.to_thread(
                gh_repo.get_contents, cu.file_path, ref=repo_default_branch
            )
            original = content_file.decoded_content.decode("utf-8")  # type: ignore
        except Exception as exc:
            logger.warning("open_pr: could not fetch %s: %s", cu.file_path, exc)
            continue

        # Compute patched content by applying the validated diff
        apply_ok, new_content, apply_log = apply_diff_to_content(cu.file_path, original, p.diff)
        if not apply_ok:
            logger.warning("open_pr: could not apply diff to %s: %s", cu.file_path, apply_log)
            new_content = original

        patch_dicts.append(
            {
                "file_path": cu.file_path,
                "new_content": new_content,
                "package_name": pkg_name,
                "new_version": pv_version,
                "diff": p.diff,
                "validation": vr_map.get(p.id),
            }
        )

    # Guard: don't open a no-op PR with zero patches collected
    if not patch_dicts:
        logger.warning(
            "open_pr: no patch content collected for repo %s — skipping PR",
            repo_id,
        )
        return

    # Build PR body with explicit verification evidence
    body_lines = [
        f"## Telex Auto-Patch: `{pkg_name}` → `{pv_version}`\n",
        "Telex detected breaking API changes / runtime defects and generated the following patches.\n",
        "**Review each diff carefully before merging. Never auto-merge.**\n",
    ]
    for i, pd in enumerate(patch_dicts, 1):
        vr = pd.get("validation")
        vr_evidence = []
        if vr:
            mode_display = getattr(vr, "verification_mode", None) or "structural_only"
            disclosure_text = format_verification_disclosure(vr)
            vr_evidence.append(f"- **Verification Status**: {disclosure_text}")
            vr_evidence.append(f"- **Verification Mode**: `{mode_display}`")
            vr_evidence.append(f"- **Applied Cleanly**: {'✓ Passed' if vr.applies_cleanly else '✗ Failed'}")
            if vr.typechecks is not None:
                vr_evidence.append(f"- **Typecheck**: {'✓ Passed' if vr.typechecks else '✗ Failed'}")
            else:
                vr_evidence.append("- **Typecheck**: N/A (no config found)")
            if vr.tests_pass is not None:
                vr_evidence.append(f"- **Automated Tests**: {'✓ Passed' if vr.tests_pass else '✗ Failed'}")
            else:
                vr_evidence.append("- **Automated Tests**: N/A (no test suite found)")

        body_lines.append(f"\n### Patch {i}: `{pd['file_path']}`\n")
        if vr_evidence:
            body_lines.append("**Verification Gate Evidence:**\n" + "\n".join(vr_evidence) + "\n")
        body_lines.append(f"```diff\n{pd['diff']}\n```\n")

    summary = "\n".join(body_lines)

    # Include a short unique ID so concurrent defects don't collide on the same branch.
    unique_id_source = cu_id_raw or str(uuid.uuid4())
    short_id = unique_id_source.split("-")[0]  # e.g. "a3f2c1b8"
    branch_name = f"telex/{pkg_name}/{pv_version}/{short_id}"

    try:
        pr_url, pr_number = await open_patch_pr(
            repo_full_name=repo_full_name,
            installation_id=installation_github_id,
            branch_name=branch_name,
            patches=patch_dicts,
            summary=summary,
        )
    except Exception as exc:
        logger.error("open_pr: failed to open PR: %s", exc)
        return

    # ── Phase 8.4: create Telex Validation Check Run ──────────────────────────
    # Determine the head commit SHA from the PR branch so the check run appears
    # in the PR's "Checks" tab alongside the repo's own CI.
    try:
        import asyncio as _asyncio
        def _get_head_sha():
            gh = get_installation_client(installation_github_id)
            repo_obj = gh.get_repo(repo_full_name)
            branch_ref = repo_obj.get_branch(branch_name)
            return branch_ref.commit.sha
        head_sha = await _asyncio.to_thread(_get_head_sha)

        # Derive conclusion from the most recent validation run
        first_vr = next((vr_map.get(p.id) for p in patches if vr_map.get(p.id)), None)
        if first_vr:
            all_ok = (
                first_vr.applies_cleanly
                and first_vr.parses
                and first_vr.scope_ok
                and (first_vr.tests_pass is not False)
                and (first_vr.typechecks is not False)
            )
            check_conclusion = "success" if all_ok else "failure"
            check_title = (
                "Telex: patch verified (all gates passed)"
                if all_ok
                else "Telex: patch verification incomplete"
            )
            mode_label = getattr(first_vr, "verification_mode", None) or "structural_only"
            check_summary = (
                f"Verification mode: `{mode_label}` | "
                f"Applies cleanly: {'✓' if first_vr.applies_cleanly else '✗'} | "
                f"Tests: {'✓' if first_vr.tests_pass else ('N/A' if first_vr.tests_pass is None else '✗')} | "
                f"Typecheck: {'✓' if first_vr.typechecks else ('N/A' if first_vr.typechecks is None else '✗')}"
            )
        else:
            check_conclusion = "neutral"
            check_title = "Telex: no validation run recorded"
            check_summary = "No ValidationRun was found for this patch."

        await create_check_run(
            repo_full_name=repo_full_name,
            installation_id=installation_github_id,
            head_sha=head_sha,
            name="Telex Validation",
            conclusion=check_conclusion,
            title=check_title,
            summary=check_summary,
        )
    except Exception as check_exc:
        # Non-fatal — log and continue; the PR has already been opened
        logger.warning("open_pr: could not create Check Run for PR #%d: %s", pr_number, check_exc)

    # Record the PR in the database
    async with AsyncSessionLocal() as session:
        pr = PullRequest(
            repo_id=repo_id,
            package_version_id=package_version_id,
            github_pr_number=pr_number,
            github_pr_url=pr_url,
            patch_ids=[p.id for p in patches],
        )
        session.add(pr)
        await session.commit()

    logger.info("open_pr: opened PR #%d on %s (%s)", pr_number, repo_full_name, pr_url)


