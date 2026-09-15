<p align="center">
  <img src="apps/web/public/logo.svg" width="96" height="96" alt="Telex Logo" />
</p>

<h1 align="center">Telex</h1>

<p align="center">
  <strong>Autonomous Self-Healing Agent for Codebase Dependencies.</strong><br>
  <em>Detect breaking dependency releases → AST-scan target repos (TS, JS, Python) → Synthesize minimal unified diffs via LLMs → Verify in native CI sandboxes → Open human-reviewed GitHub PRs.</em>
</p>

<p align="center">
  <a href="ARCHITECTURE.md"><img src="https://img.shields.io/badge/Architecture-ARCHITECTURE.md-purple?style=flat-square" alt="Architecture" /></a>
  <a href="DEMO.md"><img src="https://img.shields.io/badge/Reproduction_Guide-DEMO.md-blue?style=flat-square" alt="Demo Guide" /></a>
  <img src="https://img.shields.io/badge/Tests-26%2F26_Passing-brightgreen?style=flat-square" alt="Tests 26 Passing" />
  <img src="https://img.shields.io/badge/Phases-0--9_Complete-white?style=flat-square" alt="Phases 0-9 Complete" />
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
           (Best-of-N LLM: Gemini / Claude / OpenAI / …)
                             │
                     validate_patch
                 (Native CI Verification Gate)
                 (Typecheck & Test Suite Gates)
                             │
                          open_pr
                (Human-Reviewed GitHub PR)
                (+ Telex Validation Check Run)
```

---

## Key Engineering Innovations

### 1. Multi-Language Tree-Sitter AST Scanning
Telex avoids naive grep or regex searches that produce false positives. It uses native **Tree-Sitter AST queries** across **TypeScript**, **TSX**, **JavaScript**, and **Python** to pinpoint exact call sites:
- Plain function calls: `create_completion(...)`
- Object method & attribute calls: `client.create_completion(...)`
- Zero regex guessing: 100% AST-level syntax precision with line and byte offsets.

### 2. Best-of-N Patch Synthesis + Ephemeral Verification Gates
Telex never assumes an LLM-generated patch is correct:
- **Best-of-N Generation**: Requests 3 candidate diffs, filters by structural validity and real `git apply` success, selects the smallest passing candidate.
- **Sandbox Validation**: Every patch is verified in an isolated GitHub Actions sandbox using the repository's own test suite.
- **Repository Verification Policies**: Enforces repository-configured typecheck (`npx tsc`, `mypy`) and test execution (`pytest`, `npm test`) gates.
- **Honest Disclosure**: PR body explicitly states the verification mode (`full` / `structural_only`) — never hides the absence of a test suite.

### 3. Absolute Safety: Never Auto-Merge
- **Strict Human Review**: Telex opens pull requests with comprehensive verification receipts and exact diff disclosures. A human engineer always reviews and merges.
- **Cryptographic Webhook Verification**: Inbound GitHub events are validated with HMAC-SHA256 (`X-Hub-Signature-256`).
- **GitHub Check Runs**: A "Telex Validation" check run appears alongside the repo's own CI checks in every PR — clearly labeled, not replacing existing checks.

### 4. BYOK API Keys & Security
- **Bring Your Own Key**: Users can supply API keys for any of 10 supported providers (Gemini, OpenAI, Claude, Mistral, Groq, Cohere, xAI, DeepSeek, Together AI, Nemotron). Keys are encrypted at rest with Fernet symmetric encryption.
- **Key Redaction**: A global log filter strips API key patterns from all log output before emission.
- **Platform Fallback**: Users without a BYOK key automatically use the platform's hosted Gemini key — zero configuration required.

### 5. Fair Multi-Tenant Scheduling
- **Per-Installation Cap**: A simple concurrent-job cap (default 3) prevents any single high-volume installation from starving others.
- **GitHub Rate-Limit Awareness**: The worker checks remaining API quota before heavy GitHub operations and sleeps until reset rather than hard-failing.

---

## Feature Matrix

| Component | Feature | Implementation Details |
|---|---|---|
| **AST Scanner** | Multi-Language AST Parsing | Tree-sitter queries: TypeScript, TSX, JavaScript, Python |
| **Patch Engine** | Best-of-N LLM Synthesis | Gemini, Claude, OpenAI, Mistral, Groq, Cohere, xAI, DeepSeek, Together, Nemotron |
| **BYOK** | Per-User API Key Management | Fernet encryption at rest · `POST/GET/DELETE /api/settings/api-keys` |
| **Verification Gate** | Sandboxed Verification | GitHub Actions ephemeral sandbox · typecheck + test suite gates |
| **Check Runs** | GitHub Checks API | "Telex Validation" check run on every PR alongside native CI |
| **GitHub App** | Autonomous PR Delivery | Atomic branch creation, patch commits, human-reviewed PRs |
| **Job Queue** | Async PostgreSQL Worker | `SELECT … FOR UPDATE SKIP LOCKED` + per-installation cap |
| **Auth & Session** | Secure GitHub OAuth | Cross-origin `/api/auth/me` with HMAC webhook validation |
| **Dashboard** | Next.js Web App | Repo management, BYOK settings, telemetry, activity feed |
| **CI & Testing** | Pytest + pip-audit + npm audit | 26/26 unit & integration tests · dependency scanning in CI |

---

## Quick Start & Local Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- A GitHub App (see [ARCHITECTURE.md](ARCHITECTURE.md) for setup)

### 1. Clone & Configure Environment
```bash
git clone https://github.com/Kesavaraja67/telex.git
cd telex
cp .env.example apps/api/.env
# Edit apps/api/.env with your actual values (see .env.example for all fields)
```

### 2. Generate Encryption Key (required for BYOK)
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add the output as TELEX_ENCRYPTION_KEY= in apps/api/.env
```

### 3. Backend (FastAPI + Async Worker)
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

### 4. Frontend (Next.js Dashboard)
```bash
cd apps/web
npm install
npm run dev
```
Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard).

---

## Automated Test Suite (26 Tests)

```bash
cd apps/api
pytest -v
```

**26/26 Passing** across:
- `test_code_scanner.py` — 7 AST scanner tests (TS, TSX, JS, Python)
- `test_patch_generation.py` — 11 patch synthesis and verification tests
- `test_validate_patch.py` — 5 sandbox validation and disclosure tests
- `test_webhooks.py` — 3 PR lifecycle webhook tests

---

## Security Posture

| Control | Status |
|---|---|
| Secret scanning (Gitleaks in CI) | ✅ Active |
| Dependency scanning (`pip-audit` + `npm audit` in CI) | ✅ Active |
| BYOK keys encrypted at rest (Fernet) | ✅ Active |
| API key patterns redacted from all logs | ✅ Active |
| HMAC-SHA256 webhook signature verification | ✅ Active |
| Explicit CORS allowlist (no wildcard) | ✅ Active |
| GitHub Actions workflow permissions: `contents: read` | ✅ Active |
| No automerge, at any confidence level | ✅ By design |

> **Note**: A formal third-party penetration test should be completed before describing this system as production-grade to external parties.

For step-by-step evaluator instructions, see [DEMO.md](DEMO.md).
For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).
