<p align="center">
  <img src="apps/web/public/logo.svg" width="96" height="96" alt="Telex Logo" />
</p>

<h1 align="center">Telex</h1>

<p align="center">
  <strong>Autonomous Self-Healing Agent for Codebase Dependencies.</strong><br>
  <em>Detect breaking dependency releases → AST-scan target repos (TS, JS, Python) → Synthesize minimal unified diffs via LLMs → Verify in native CI sandboxes → Open human-reviewed GitHub PRs.</em>
</p>

<p align="center">
  <a href="https://telex-pi.vercel.app"><img src="https://img.shields.io/badge/Live_Dashboard-telex--pi.vercel.app-white?style=flat-square&logo=vercel" alt="Live Dashboard" /></a>
  <a href="https://telex-api.onrender.com/health"><img src="https://img.shields.io/badge/API_Status-Live_200_OK-green?style=flat-square" alt="API Status" /></a>
  <a href="ARCHITECTURE.md"><img src="https://img.shields.io/badge/Architecture-ARCHITECTURE.md-purple?style=flat-square" alt="Architecture" /></a>
  <a href="DEMO.md"><img src="https://img.shields.io/badge/Reproduction_Guide-DEMO.md-blue?style=flat-square" alt="Demo Guide" /></a>
  <img src="https://img.shields.io/badge/Tests-18%2F18_Passing-brightgreen?style=flat-square" alt="Tests 18 Passing" />
</p>

---

## Overview

Telex is an autonomous software healing daemon designed to protect production codebases from breaking upstream dependency updates. When an open-source package publishes a breaking version, Telex identifies affected call sites across your repositories, generates verified repair patches, and opens a ready-to-merge Pull Request before broken builds ever reach your users.

```text
 ┌────────────────────────────────────────────────────────┐
 │                      TELEX ENGINE                      │
 └────────────────────────────────────────────────────────┘
                             │
            [ Trigger: Upstream Registry Release ]
                    (npm, PyPI monitoring)
                             │
                      extract_changes
            (Parse changelog & breaking symbols)
                             │
                        scan_repo
             (Tree-Sitter AST Code Scanner)
             (TypeScript, TSX, JS, Python)
                             │
                      generate_patch
                  (LLM: Gemini / Claude)
                             │
                      verify_in_clone
                 (Native CI Verification Gate)
                 (Typecheck & Test Suite Gates)
                             │
                          open_pr
                (Human-Reviewed GitHub PR)
```

---

## Key Engineering Innovations

### 1. Multi-Language Tree-Sitter AST Scanning
Telex avoids naive grep or regex searches that produce false positives. It uses native **Tree-Sitter AST queries** across **TypeScript**, **TSX**, **JavaScript**, and **Python** to pinpoint exact call sites:
- Plain function calls: `create_completion(...)`
- Object method & attribute calls: `client.create_completion(...)`
- Zero regex guessing: 100% AST-level syntax precision with line and byte offsets.

### 2. Ephemeral Native Verification Gates
Telex never assumes an LLM-generated patch is correct:
- **Sandbox Validation**: Every patch is applied in an isolated clone environment.
- **Repository Verification Policies**: Enforces repository-configured typecheck (`npx tsc`, `mypy`) and test execution (`pytest`, `npm test`) gates.
- **Compiler Feedback Retries**: If verification fails, the compiler error log is fed back into the LLM for a single bounded self-correction attempt.

### 3. Absolute Safety: Never Auto-Merge
- **Strict Human Review**: Telex opens pull requests with comprehensive verification receipts and exact diff disclosures. A human engineer always reviews and merges the PR.
- **Cryptographic Webhook Verification**: Inbound GitHub events are validated with HMAC-SHA256 (`X-Hub-Signature-256`).
- **Cross-Origin Authenticated Sessions**: Robust `/api/auth/me` cross-domain credential verification between Vercel and Render hosts.

---

## Feature Matrix

| Component | Feature | Implementation Details | Status |
|---|---|---|---|
| **AST Scanner** | Multi-Language AST Parsing | Tree-sitter queries for TypeScript, TSX, JavaScript, and Python | Live |
| **Patch Engine** | LLM Patch Synthesis | Gemini & Claude providers with unified diff extraction & bounds checking | Live |
| **Verification Gate** | Sandboxed Verification | Native clone execution with typecheck & automated test gates | Live |
| **GitHub App** | Autonomous PR Delivery | Atomic branch creation, patch commits, and human-reviewed PR opening | Live |
| **Job Queue** | Async PostgreSQL Worker | Row-level locking (`SELECT ... FOR UPDATE SKIP LOCKED`) + heartbeat watchdog | Live |
| **Auth & Session** | Secure GitHub OAuth | Cross-origin `/api/auth/me` session validation with HttpOnly tokens | Live |
| **Dashboard** | Next.js 16 Web App | High-contrast monochrome UI, repo management, and telemetry | Live |
| **CI & Testing** | Pytest Test Suite | 18 passing unit and integration tests with zero regressions | Live |

---

## Quick Start & Local Setup

### 1. Clone & Configure Environment
```bash
git clone https://github.com/Kesavaraja67/telex.git
cd telex
cp .env.example apps/api/.env
cp .env.example apps/web/.env.local
```

### 2. Backend (FastAPI + Async Worker)
```bash
cd apps/api
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head

# Run API Server
uvicorn main:app --reload --port 8000
```

### 3. Frontend (Next.js Dashboard)
```bash
cd apps/web
npm install
npm run dev
# If Turbopack native binary is blocked on Windows:
# npm run dev -- --webpack
```
Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard) to view the connected repositories and patch status.

---

## Automated Test Suite (18 Tests)

The backend test suite validates AST scanning across all supported languages, patch formatting, unified diff parsing, and verification gates:

```bash
cd apps/api
pytest -v
```

### Test Coverage Breakdown (18/18 Passing):
- **`test_code_scanner.py` (7 Tests)**:
  - `test_find_usages_plain_identifier`: Direct function calls in TypeScript.
  - `test_find_usages_member_expression`: Method calls on objects in TypeScript/JavaScript.
  - `test_find_usages_multiple_call_sites`: Discovers all occurrences across multiple lines.
  - `test_find_usages_no_match`: Clean empty list when target symbol is absent.
  - `test_find_usages_tsx_syntax`: React JSX/TSX syntax parsing without syntax errors.
  - `test_find_usages_python_syntax`: Plain and attribute method calls in Python code.
  - `test_find_usages_python_fixture`: End-to-end AST scan of real Python service fixture.
- **`test_patch_generation.py` (11 Tests)**:
  - `test_validate_patch_valid_diff`: Valid unified diff validation.
  - `test_validate_patch_out_of_scope`: Rejection of out-of-scope diff modifications.
  - `test_validate_patch_unable_to_patch_sentinel`: Safe handling of `UNABLE_TO_PATCH` sentinels.
  - `test_validate_patch_invalid_format`: Syntax rejection on malformed diffs.
  - `test_extract_diff_markdown_fences`: Diff extraction from markdown-fenced LLM responses.
  - `test_extract_diff_unable_to_patch_handling`: Refusal extraction handling.
  - `test_verify_patch_in_clone_no_installation_is_structural_only`: Structural validation fallback.
  - `test_verify_patch_in_clone_broken_patch_rejected`: Rejection of patches that fail to apply cleanly.
  - `test_verify_patch_in_clone_exception_fails_verification`: Graceful failure handling on unexpected errors.
  - `test_verify_patch_in_clone_requires_tests_policy`: Enforces repository `requires_tests` configuration.
  - `test_verify_patch_via_github_actions_success`: Ephemeral verification workflow generation.

For step-by-step evaluator instructions, see [DEMO.md](DEMO.md).
