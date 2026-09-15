# Security Policy

## Supported Versions

We actively maintain and provide security updates for the following versions of Telex:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## Reporting a Vulnerability

We take the security of Telex, our users' source code, and connected repository credentials with the highest level of priority.

If you believe you have discovered a security vulnerability in Telex, **please do not open a public GitHub issue or discussion.**

Instead, please submit your report privately using GitHub's **Private Vulnerability Reporting**:

1. Navigate to the [Telex Security Advisories](https://github.com/Kesavaraja67/telex/security/advisories) tab.
2. Click **"Report a vulnerability"**.
3. Provide a detailed summary, including:
   - Type of vulnerability (e.g. authentication bypass, secret exposure, injection, privilege escalation).
   - Step-by-step reproduction steps or a minimal proof of concept (PoC).
   - Potential impact and affected components (`apps/api`, `apps/web`, or CI/CD pipelines).

Alternatively, you may contact the maintainers directly via email at:  
**krkesavaraja67@gmail.com**

---

## What to Expect

- **Acknowledgement**: We will acknowledge receipt of your vulnerability report within **24 hours**.
- **Assessment**: We will confirm the vulnerability and provide an estimated timeline for remediation within **72 hours**.
- **Coordination**: We will coordinate with you to test and verify the fix prior to public disclosure.
- **Credit**: We will credit your discovery in our Security Advisories release notes (unless you prefer to remain anonymous).

---

## Security Best Practices for Self-Hosting

1. **Production Secrets**: Never commit real private keys (`GITHUB_APP_PRIVATE_KEY`), webhook secrets, or session keys to git. Always use environment variables or a dedicated KMS / Secrets Manager.
2. **Database Permissions**: Ensure the production PostgreSQL database user has minimal necessary table permissions and cannot drop schema tables.
3. **CORS Configuration**: Restrict `CORS_ORIGINS` to explicit, trusted domains. Never use wildcards (`*`) when `allow_credentials=True`.
