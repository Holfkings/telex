# Telex System Architecture & Technical Specification

> **Autonomous AI Self-Healing Patch Agent for Codebase Dependencies**

---

## 1. Executive System Topology

Telex operates as an asynchronous, event-driven daemon that continuously tracks upstream library releases, detects breaking symbol changes, scans connected customer repositories, synthesizes unified diffs using LLMs, and verifies every patch inside a native CI sandbox before opening a human-reviewed Pull Request.

```text
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   INGESTION LAYER                                      │
 └────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                          [ Upstream Registry Notifications ]
                            - npm & PyPI registry polling
                            - Package version updates & changelog discovery
                            - Breaking interface diffs
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                               AST CODE SCANNER LAYER                                   │
 │       (Tree-Sitter Multi-Language Scanner: TypeScript, TSX, JavaScript, Python)         │
 └────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                       [ Pinpoint Exact Usages & Byte Offsets ]
                        - Function calls: create_completion(...)
                        - Attribute calls: client.create_completion(...)
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                              LLM REPAIR SYNTHESIS LAYER                                │
 │                         (Gemini 2.5 Flash / Claude Providers)                          │
 └────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                             [ Unified Patch Diff Synthesis ]
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                           EPHEMERAL VERIFICATION GATE                                  │
 │                     (Isolated Clone Sandbox & Native CI Runs)                          │
 │                      Typechecks (tsc / mypy) + Test Suites                             │
 └────────────────────────────────────────────────────────────────────────────────────────┘
                                             │
                                     [ 100% Verified ]
                                             │
                                             ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                             PULL REQUEST DELIVERY LAYER                                │
 │                              (Human-Reviewed GitHub PR)                                │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Language AST Code Scanner Architecture

A critical engineering advantage of Telex is that it avoids regex or textual search when detecting breaking change impacts. Regex searches produce false positives on comments, strings, and unrelated identifiers.

Telex uses **Tree-Sitter AST queries** configured through a unified `LANGUAGE_CONFIG` architecture:

```python
LANGUAGE_CONFIG = {
    "typescript": {
        "parser_name": "typescript",
        "extensions": {".ts", ".mts", ".cts"},
        "call_node_type": "call_expression",
        "queries": [
            ("(call_expression function: (identifier) @fn)", "fn"),
            ("(call_expression function: (member_expression property: (property_identifier) @prop))", "prop"),
        ],
    },
    "tsx": {
        "parser_name": "tsx",
        "extensions": {".tsx"},
        "call_node_type": "call_expression",
        "queries": [
            ("(call_expression function: (identifier) @fn)", "fn"),
            ("(call_expression function: (member_expression property: (property_identifier) @prop))", "prop"),
        ],
    },
    "javascript": {
        "parser_name": "javascript",
        "extensions": {".js", ".jsx", ".mjs", ".cjs"},
        "call_node_type": "call_expression",
        "queries": [
            ("(call_expression function: (identifier) @fn)", "fn"),
            ("(call_expression function: (member_expression property: (property_identifier) @prop))", "prop"),
        ],
    },
    "python": {
        "parser_name": "python",
        "extensions": {".py"},
        "call_node_type": "call",
        "queries": [
            ("(call function: (identifier) @fn)", "fn"),
            ("(call function: (attribute attribute: (identifier) @prop))", "prop"),
        ],
    },
}
```

Every discovered usage returns exact character and byte offsets, line numbers, and the isolated syntax node snippet for minimal LLM context windows.

---

## 3. Ephemeral GitHub Actions Verification Gate

Telex never assumes that an LLM-generated patch is bug-free. Instead of relying on simulated diff parsers or local system clones that diverge from the target repository, Telex uses a **native verification gate**:

1. **Candidate Branch Creation**: Telex creates a dedicated verification branch:  
   `telex/validate-<patch-id>`
2. **Atomic Verification Bundle**: Using PyGithub's Git Data API, Telex commits:
   - The candidate unified patch applied to the target code.
   - An auto-generated verification workflow: `.github/workflows/telex-verify.yml`.
3. **Native Runner Execution**: The environment executes the target repository's **real package dependencies, typecheckers, and test runner** on clean runners.
4. **Autonomous Status Polling**: Telex monitors the check runs via the GitHub API with bounded exponential backoff.
5. **Gating Rule**:
   - **PASS (100% Green)** → Clean pull request opened with detailed verification receipts.
   - **FAIL** → Bounded retry with compiler feedback, or immediate rejection. **Zero hallucinated code ever reaches a production pull request.**

---

## 4. Security Model & Deliberate Stop Safety Guardrails

- **Cryptographic Webhook Validation**: All inbound GitHub webhooks are cryptographically authenticated via HMAC-SHA256 (`X-Hub-Signature-256`) against `GITHUB_WEBHOOK_SECRET`.
- **Absolute Non-Negotiable: Never Auto-Merge**: Telex opens pull requests. A human engineer merges them. Under no condition, at any confidence threshold, does Telex merge code automatically.
- **Cross-Origin Authenticated Sessions**: Authentication between the Next.js frontend (Vercel) and FastAPI backend (Render) uses HttpOnly session tokens with `/api/auth/me` verification and strict origin whitelisting.
- **Production Secret Guard**: In `ENVIRONMENT=production`, the API process fails loudly at boot if required credentials (`GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`, `NEXTAUTH_SECRET`) are missing or using development defaults.
