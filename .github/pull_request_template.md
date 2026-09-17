## Description
<!-- Provide a brief description of the changes introduced by this pull request. -->

## Related Issue
<!-- Link the issue this PR resolves, e.g. Fixes #123 or Closes #456 -->
Fixes #

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Code style / formatting / refactor (no logic change)
- [ ] 🧪 Tests (adding or updating test cases)

---

## 📸 Visual Evidence (Mandatory for UI / UX / Dashboard Changes)
<!--
IMPORTANT: If your pull request introduces, updates, or fixes any user interface, visual layout,
dashboard component, styling, or frontend workflow, you MUST attach visual evidence below.
Accepted formats:
- Screenshots (PNG/JPG) showing Before and After states.
- Screen recording (GIF/MP4/WebM) demonstrating the interaction flow.
-->

### Before
<!-- Insert screenshot or recording of the previous state, or N/A -->

### After
<!-- Insert screenshot or recording of the new state -->

---

## 🧪 Test Coverage
<!-- Confirm that backend test coverage meets or exceeds the 80% threshold -->
- [ ] Added / updated automated tests covering the changes.
- [ ] Test coverage meets or exceeds **80%** (`pytest --cov=. --cov-fail-under=80`).

---

## 📋 Quality & Contribution Checklist
- [ ] **Issue Assignment**: I asked to be assigned and was officially assigned to the related issue before opening this PR.
- [ ] **Simple English Comments**: All code comments and docstrings are written in simple, clear, and direct English.
- [ ] **Professional Communication**: PR description and any discussion adhere to professional, respectful standards.
- [ ] **Python Formatting & Linting**: Ran `ruff check --fix .` and `black .` in `apps/api` with zero violations.
- [ ] **Frontend Validation**: Ran `npx tsc --noEmit` and `npm run lint` in `apps/web` with zero errors.
- [ ] **No Secrets Committed**: Checked that no API keys, private tokens, or credentials are leaked in the diff.
- [ ] **Clean Git History**: Commits follow Conventional Commits standard (`feat:`, `fix:`, `docs:`).
