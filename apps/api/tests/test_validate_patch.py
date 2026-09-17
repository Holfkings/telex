"""
Tests for Phase 4: Sandbox validation pipeline, validate_patch handler, and PR body verification disclosures.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from db.models import Patch, CodeUsage, Repo, Installation, ValidationRun
from jobs.handlers import validate_patch


@pytest.fixture
def base_patch_setup():
    patch_id = uuid.uuid4()
    cu_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    inst_id = uuid.uuid4()

    valid_diff = """--- a/src/index.ts
+++ b/src/index.ts
@@ -1,1 +1,1 @@
-const res = await openai.createCompletion({ model: 'text-davinci-003' });
+const res = await openai.chat.completions.create({ model: 'gpt-4' });"""

    code_snippet = "const res = await openai.createCompletion({ model: 'text-davinci-003' });"

    test_patch = Patch(
        id=patch_id,
        code_usage_id=cu_id,
        diff=valid_diff,
        llm_provider="gemini",
        llm_model="gemini-2.5-flash",
        prompt_version="v1",
        verified=False,
    )

    code_usage = CodeUsage(
        id=cu_id,
        repo_id=repo_id,
        file_path="src/index.ts",
        line_start=1,
        line_end=1,
        snippet=code_snippet,
        status="pending",
    )

    repo = Repo(
        id=repo_id,
        installation_id=inst_id,
        full_name="acme/service",
        default_branch="main",
        requires_tests=False,
        requires_typecheck=False,
    )

    installation = Installation(
        id=inst_id,
        github_installation_id=999888,
        account_login="acme",
        account_type="Organization",
    )

    return {
        "patch": test_patch,
        "code_usage": code_usage,
        "repo": repo,
        "installation": installation,
    }


def create_mock_session(entities):
    session = AsyncMock()
    added_items = []

    def fake_add(item):
        added_items.append(item)

    async def fake_get(model_cls, entity_id):
        for e in entities.values():
            if isinstance(e, model_cls) and getattr(e, "id", None) == entity_id:
                return e
        return None

    session.get = AsyncMock(side_effect=fake_get)
    session.add = MagicMock(side_effect=fake_add)
    session.commit = AsyncMock()
    session.added_items = added_items
    return session


@pytest.mark.asyncio
async def test_validate_patch_js_with_tests_produces_full_verification(
    base_patch_setup, monkeypatch
):
    """
    JS fixture with tests:
    - has_test=True, has_typecheck=True
    - produces ValidationRun with verification_mode='full'
    - PR body contains the full verification disclosure badge
    """
    import services.github_service as gh_svc

    entities = base_patch_setup
    mock_session = create_mock_session(entities)

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("db.session.AsyncSessionLocal", lambda: mock_session_ctx)
    monkeypatch.setattr(
        gh_svc, "fetch_file_content", lambda *args, **kwargs: entities["code_usage"].snippet
    )
    monkeypatch.setattr(
        gh_svc,
        "detect_repo_environment",
        lambda *args, **kwargs: {
            "ecosystem": "node",
            "package_manager": "npm",
            "install_cmd": "npm ci",
            "test_cmd": "npm test",
            "typecheck_cmd": "npx tsc --noEmit",
            "has_test": True,
            "has_typecheck": True,
        },
    )
    monkeypatch.setattr(gh_svc, "create_or_update_branch", lambda *args, **kwargs: "sha-base-123")
    monkeypatch.setattr(
        gh_svc, "commit_verification_bundle", lambda *args, **kwargs: "sha-commit-456"
    )
    monkeypatch.setattr(gh_svc, "delete_branch", lambda *args, **kwargs: True)

    async def mock_wait_ci(*args, **kwargs):
        return {
            "is_verified": True,
            "workflow_found": True,
            "completed": True,
            "conclusion": "success",
            "typechecks": True,
            "tests_pass": True,
            "log": "Verification Check [Telex Verification Gate]: passed",
            "check_runs": [
                {"name": "Telex Verification Gate", "status": "completed", "conclusion": "success"}
            ],
        }

    monkeypatch.setattr(gh_svc, "wait_for_telex_verification", mock_wait_ci)

    enqueued_jobs = []

    async def mock_enqueue(session, job_type, payload):
        enqueued_jobs.append({"job_type": job_type, "payload": payload})

    monkeypatch.setattr("jobs.queue.enqueue_job", mock_enqueue)

    await validate_patch.run({"patch_id": str(entities["patch"].id)})

    # Confirm ValidationRun
    validation_runs = [item for item in mock_session.added_items if isinstance(item, ValidationRun)]
    assert len(validation_runs) == 1
    vr = validation_runs[0]
    assert vr.verification_mode == "full"
    assert vr.tests_pass is True
    assert vr.typechecks is True
    assert vr.applies_cleanly is True
    assert entities["patch"].verified is True
    assert entities["code_usage"].status == "patched"

    # Confirm open_pr was enqueued
    assert len(enqueued_jobs) == 1
    assert enqueued_jobs[0]["job_type"] == "open_pr"

    # Verify PR body disclosure format via production helper
    from jobs.handlers.open_pr import format_verification_disclosure

    disclosure = format_verification_disclosure(vr)
    assert (
        "✅ Verified: repo's own test suite and type-checker both passed on this patch."
        in disclosure
    )


@pytest.mark.asyncio
async def test_validate_patch_js_without_tests_produces_structural_only(
    base_patch_setup, monkeypatch
):
    """
    JS fixture without tests:
    - has_test=False, has_typecheck=True
    - produces ValidationRun with verification_mode='structural_only'
    - PR body contains the warning disclosure badge
    """
    import services.github_service as gh_svc

    entities = base_patch_setup
    mock_session = create_mock_session(entities)

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("db.session.AsyncSessionLocal", lambda: mock_session_ctx)
    monkeypatch.setattr(
        gh_svc, "fetch_file_content", lambda *args, **kwargs: entities["code_usage"].snippet
    )
    monkeypatch.setattr(
        gh_svc,
        "detect_repo_environment",
        lambda *args, **kwargs: {
            "ecosystem": "node",
            "package_manager": "npm",
            "install_cmd": "npm ci",
            "test_cmd": "",
            "typecheck_cmd": "npx tsc --noEmit",
            "has_test": False,
            "has_typecheck": True,
        },
    )
    monkeypatch.setattr(gh_svc, "create_or_update_branch", lambda *args, **kwargs: "sha-base-123")
    monkeypatch.setattr(
        gh_svc, "commit_verification_bundle", lambda *args, **kwargs: "sha-commit-456"
    )
    monkeypatch.setattr(gh_svc, "delete_branch", lambda *args, **kwargs: True)

    async def mock_wait_ci(*args, **kwargs):
        return {
            "is_verified": True,
            "workflow_found": True,
            "completed": True,
            "conclusion": "success",
            "typechecks": True,
            "tests_pass": None,
            "log": "Verification Check: typecheck passed",
            "check_runs": [
                {"name": "Telex Verification Gate", "status": "completed", "conclusion": "success"}
            ],
        }

    monkeypatch.setattr(gh_svc, "wait_for_telex_verification", mock_wait_ci)

    enqueued_jobs = []

    async def mock_enqueue(session, job_type, payload):
        enqueued_jobs.append({"job_type": job_type, "payload": payload})

    monkeypatch.setattr("jobs.queue.enqueue_job", mock_enqueue)

    await validate_patch.run({"patch_id": str(entities["patch"].id)})

    validation_runs = [item for item in mock_session.added_items if isinstance(item, ValidationRun)]
    assert len(validation_runs) == 1
    vr = validation_runs[0]
    assert vr.verification_mode == "structural_only"
    assert vr.tests_pass is None
    assert vr.typechecks is True
    assert entities["patch"].verified is True

    # Verify PR disclosure formatting via production helper
    from jobs.handlers.open_pr import format_verification_disclosure

    disclosure = format_verification_disclosure(vr)
    assert "⚠️ No test suite detected in this repo" in disclosure


@pytest.mark.asyncio
async def test_validate_patch_python_with_tests_produces_full_verification(
    base_patch_setup, monkeypatch
):
    """
    Python fixture with tests:
    - has_test=True
    - produces ValidationRun with verification_mode='full'
    """
    import services.github_service as gh_svc

    entities = base_patch_setup
    entities["code_usage"].file_path = "services/service.py"
    entities["code_usage"].snippet = "client.create_completion(model='gpt-4')"
    entities["patch"].diff = """--- a/services/service.py
+++ b/services/service.py
@@ -1,1 +1,1 @@
-client.create_completion(model='gpt-4')
+client.chat.completions.create(model='gpt-4')"""

    mock_session = create_mock_session(entities)
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("db.session.AsyncSessionLocal", lambda: mock_session_ctx)
    monkeypatch.setattr(
        gh_svc, "fetch_file_content", lambda *args, **kwargs: entities["code_usage"].snippet
    )
    monkeypatch.setattr(
        gh_svc,
        "detect_repo_environment",
        lambda *args, **kwargs: {
            "ecosystem": "python",
            "package_manager": "pip",
            "install_cmd": "pip install -r requirements.txt",
            "test_cmd": "pytest",
            "typecheck_cmd": "",
            "has_test": True,
            "has_typecheck": False,
        },
    )
    monkeypatch.setattr(gh_svc, "create_or_update_branch", lambda *args, **kwargs: "sha-base-123")
    monkeypatch.setattr(
        gh_svc, "commit_verification_bundle", lambda *args, **kwargs: "sha-commit-456"
    )
    monkeypatch.setattr(gh_svc, "delete_branch", lambda *args, **kwargs: True)

    async def mock_wait_ci(*args, **kwargs):
        return {
            "is_verified": True,
            "workflow_found": True,
            "completed": True,
            "conclusion": "success",
            "typechecks": None,
            "tests_pass": True,
            "log": "Verification Check: pytest passed",
            "check_runs": [
                {"name": "Telex Verification Gate", "status": "completed", "conclusion": "success"}
            ],
        }

    monkeypatch.setattr(gh_svc, "wait_for_telex_verification", mock_wait_ci)

    enqueued_jobs = []

    async def mock_enqueue(session, job_type, payload):
        enqueued_jobs.append({"job_type": job_type, "payload": payload})

    monkeypatch.setattr("jobs.queue.enqueue_job", mock_enqueue)

    await validate_patch.run({"patch_id": str(entities["patch"].id)})

    validation_runs = [item for item in mock_session.added_items if isinstance(item, ValidationRun)]
    assert len(validation_runs) == 1
    vr = validation_runs[0]
    assert vr.verification_mode == "full"
    assert vr.tests_pass is True
    assert entities["patch"].verified is True
    assert len(enqueued_jobs) == 1


@pytest.mark.asyncio
async def test_validate_patch_gating_requires_tests_fails_when_untested(
    base_patch_setup, monkeypatch
):
    """
    Repo policy requires_tests=True:
    If tests do not pass or are missing, patch must NOT be verified and open_pr must NOT be enqueued.
    """
    import services.github_service as gh_svc

    entities = base_patch_setup
    entities["repo"].requires_tests = True

    mock_session = create_mock_session(entities)
    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=None)

    monkeypatch.setattr("db.session.AsyncSessionLocal", lambda: mock_session_ctx)
    monkeypatch.setattr(
        gh_svc, "fetch_file_content", lambda *args, **kwargs: entities["code_usage"].snippet
    )
    monkeypatch.setattr(
        gh_svc,
        "detect_repo_environment",
        lambda *args, **kwargs: {
            "ecosystem": "node",
            "package_manager": "npm",
            "install_cmd": "npm ci",
            "test_cmd": "",
            "typecheck_cmd": "npx tsc --noEmit",
            "has_test": False,
            "has_typecheck": True,
        },
    )
    monkeypatch.setattr(gh_svc, "create_or_update_branch", lambda *args, **kwargs: "sha-base-123")
    monkeypatch.setattr(
        gh_svc, "commit_verification_bundle", lambda *args, **kwargs: "sha-commit-456"
    )
    monkeypatch.setattr(gh_svc, "delete_branch", lambda *args, **kwargs: True)

    async def mock_wait_ci(*args, **kwargs):
        return {
            "is_verified": True,
            "workflow_found": True,
            "completed": True,
            "conclusion": "success",
            "typechecks": True,
            "tests_pass": None,
            "log": "Typecheck only",
            "check_runs": [],
        }

    monkeypatch.setattr(gh_svc, "wait_for_telex_verification", mock_wait_ci)

    enqueued_jobs = []

    async def mock_enqueue(session, job_type, payload):
        enqueued_jobs.append({"job_type": job_type, "payload": payload})

    monkeypatch.setattr("jobs.queue.enqueue_job", mock_enqueue)

    await validate_patch.run({"patch_id": str(entities["patch"].id)})

    assert entities["patch"].verified is False
    assert entities["code_usage"].status == "failed"
    assert len(enqueued_jobs) == 0


@pytest.mark.asyncio
async def test_validate_patch_incomplete_workflow_fails_even_without_requirements(
    base_patch_setup, monkeypatch
):
    """
    Regression test:
    When wait_for_telex_verification returns completed=False and conclusion=None,
    the patch must be rejected as failed even when the repository does NOT require
    tests or typechecks (repo.requires_tests=False, repo.requires_typecheck=False).
    """
    import services.github_service as gh_svc

    entities = base_patch_setup
    entities["repo"].requires_tests = False
    entities["repo"].requires_typecheck = False
    mock_session = create_mock_session(entities)

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__.return_value = mock_session
    mock_session_ctx.__aexit__.return_value = None
    monkeypatch.setattr("db.session.AsyncSessionLocal", lambda: mock_session_ctx)

    monkeypatch.setattr(
        gh_svc,
        "detect_repo_environment",
        lambda *args, **kwargs: {
            "ecosystem": "node",
            "package_manager": "npm",
            "install_cmd": "npm ci",
            "test_cmd": "npm test",
            "typecheck_cmd": "npx tsc --noEmit",
            "has_test": True,
            "has_typecheck": True,
        },
    )
    monkeypatch.setattr(gh_svc, "create_or_update_branch", lambda *args, **kwargs: "sha-base-123")
    monkeypatch.setattr(
        gh_svc, "commit_verification_bundle", lambda *args, **kwargs: "sha-commit-456"
    )
    monkeypatch.setattr(gh_svc, "delete_branch", lambda *args, **kwargs: True)

    async def mock_wait_ci_incomplete(*args, **kwargs):
        return {
            "is_verified": False,
            "workflow_found": True,
            "completed": False,
            "conclusion": None,
            "typechecks": None,
            "tests_pass": None,
            "log": "Workflow timed out or cancelled",
            "check_runs": [],
        }

    monkeypatch.setattr(gh_svc, "wait_for_telex_verification", mock_wait_ci_incomplete)

    enqueued_jobs = []

    async def mock_enqueue(session, job_type, payload):
        enqueued_jobs.append({"job_type": job_type, "payload": payload})

    monkeypatch.setattr("jobs.queue.enqueue_job", mock_enqueue)

    await validate_patch.run({"patch_id": str(entities["patch"].id)})

    assert entities["patch"].verified is False
    assert entities["code_usage"].status == "failed"
    assert len(enqueued_jobs) == 0
