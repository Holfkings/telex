# Telex — Demo & Reproduction Guide (15-Minute Evaluator Walkthrough)

This guide walks through evaluating Telex end-to-end:
1. **Scenario 1: Upstream Breaking Change Detection & Tree-Sitter AST Scanning (TypeScript & Python)**
2. **Scenario 2: Autonomous Patch Synthesis, Native CI Verification & Human-Reviewed GitHub PR Delivery**

---

## Live Demo URLs
- **Telex Dashboard**: [https://telex-pi.vercel.app](https://telex-pi.vercel.app)
- **Backend API**: [https://telex-api.onrender.com](https://telex-api.onrender.com)
- **API Health**: [https://telex-api.onrender.com/health](https://telex-api.onrender.com/health)

---

## Scenario 1: Upstream Breaking Change Detection & AST Scanning

### Step 1: Upstream Registry Ingestion
When an upstream package (such as `openai` or `stripe`) publishes a breaking release on `npm` or `pypi`:
1. `poll_registry` discovers the new version and extracts changelog diffs.
2. `extract_changes` creates `DetectedChange` rows recording obsolete symbols, replacement APIs, and defect descriptions.

### Step 2: Multi-Language AST Repository Scanning
1. `scan_repo` inspects connected repositories for matching source files (`.ts`, `.tsx`, `.js`, `.py`).
2. Tree-Sitter queries execute natively against the AST:
   - TypeScript/JS: call expressions and member expressions.
   - Python: direct identifier calls and attribute method calls.
3. Every call site is isolated as a `CodeUsage` record with exact line and byte positions.

---

## Scenario 2: Autonomous Patch Synthesis & Verified GitHub PR

### Step 1: LLM Unified Diff Generation
1. `generate_patch` retrieves the target code snippet and context.
2. The active LLM provider (Gemini / Claude) synthesizes a minimal unified diff.
3. The diff is validated for format, bounds, and syntax correctness.

### Step 2: Native Sandbox Verification Gate
1. The patch is applied in an isolated clone sandbox.
2. The repository's configured gates (`requires_typecheck`, `requires_tests`) are enforced:
   - Typechecks (`tsc`, `mypy`) must pass cleanly.
   - Test suites (`pytest`, `npm test`) must exit with code 0.
3. If verification fails, a single bounded self-correction retry with compiler diagnostics is attempted.

### Step 3: Human-Reviewed Pull Request
1. Telex opens a pull request via the GitHub App with full disclosure of the verification mode (`full` or `structural_only`).
2. A human engineer reviews the pull request and merges it. **Telex never auto-merges.**

---

## Running Local Verification Tests

Telex includes 18 automated unit and integration tests across AST scanning and patch validation:

```bash
cd apps/api
pytest -v
```

Expected output:
```text
======================= 18 passed, 8 warnings in 3.50s =======================
```

To run the AST scanner suite specifically:
```bash
pytest tests/test_code_scanner.py -v
```

To run the patch generation & verification gate suite:
```bash
pytest tests/test_patch_generation.py -v
```
