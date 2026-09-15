# Telex API — Backend Service & Autonomous Worker

> **FastAPI REST API, PostgreSQL Job Queue, and Autonomous Code Repair Substrate**

---

## Overview

The `apps/api` service powers Telex's dependency change detection, multi-language Tree-Sitter AST repository scanning, sandboxed patch verification, and self-healing GitHub Pull Request delivery.

It runs as an asynchronous FastAPI application paired with a PostgreSQL row-level locked job queue (`SELECT ... FOR UPDATE SKIP LOCKED`), ensuring robust, duplicate-free task processing.

---

## Key Modules & Responsibilities

| Path | Responsibility |
|---|---|
| `routers/auth.py` | GitHub OAuth callback, signed session token generation, and `/api/auth/me` cross-domain authentication. |
| `routers/repos.py` | Connected repository listing, sync, and verification policy management (`requires_tests`, `requires_typecheck`). |
| `routers/packages.py` | Package tracking, version history, and detected breaking changes catalog. |
| `routers/webhooks.py` | Cryptographic HMAC-SHA256 validation for GitHub events (`X-Hub-Signature-256`). |
| `routers/stats.py` | Aggregated dashboard telemetry (repositories, packages, patches, open PRs). |
| `services/code_scanner.py` | Tree-Sitter AST parser supporting TypeScript, TSX, JavaScript, and Python (`LANGUAGE_CONFIG`). |
| `services/github_service.py` | GitHub App authentication, atomic Git tree commits, ephemeral CI workflow synthesis, and PR creation. |
| `services/patch_providers/` | Gemini and Claude unified diff synthesis providers. |
| `jobs/handlers/` | Asynchronous worker tasks: `poll_registry`, `extract_changes`, `scan_repo`, `generate_patch`, `open_pr`. |

---

## Endpoint Catalog

### Authentication (`/api/auth`)
- `GET /api/auth/github`: Initiates GitHub OAuth authorization flow.
- `GET /api/auth/callback`: Handles GitHub OAuth code exchange and issues session cookies.
- `GET /api/auth/me`: Returns the currently authenticated user based on signed session cookie.
- `GET /api/auth/logout`: Clears session cookies and redirects to home.

### Repositories (`/api/repos`)
- `GET /api/repos`: Lists connected repositories for the authenticated user.
- `GET /api/repos/{id}`: Detailed view of a repository with its detected changes and patches.

### Packages (`/api/packages`)
- `GET /api/packages`: Monitored package listing across npm and PyPI.
- `GET /api/packages/{id}`: Package details with detected breaking changes.

### System Health (`/health`)
- `GET /health`: Returns JSON status `{"status": "ok", "provider": "gemini"}`.

---

## Local Setup & Development

### 1. Virtual Environment & Dependencies
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Database Migrations
```bash
alembic upgrade head
```

### 3. Start the API & Embedded Worker
```bash
uvicorn main:app --reload --port 8000
```

---

## Automated Test Suite (18/18 Passing)

Run the full test suite with verbose output:
```bash
pytest -v
```

Expected result:
```text
======================= 18 passed, 8 warnings in 3.50s =======================
```

To run individual suites:
- **Tree-Sitter AST Scanner**: `pytest tests/test_code_scanner.py -v`
- **Patch Generation & CI Gate**: `pytest tests/test_patch_generation.py -v`
