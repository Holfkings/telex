# Contributing to Telex

Thank you for your interest in contributing to **Telex**! Telex is an open-source autonomous dependency self-healing system designed for production codebases.

We welcome contributions of all kinds: bug fixes, new features, documentation enhancements, performance optimizations, and architectural improvements.

---

## Code of Conduct

All contributors and maintainers are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure an inclusive, welcoming, and harassment-free community.

---

## Contribution Workflow & Policies

We welcome community contributions. To keep collaboration effective and maintain high code quality, please keep the following guidelines in mind:

### 1. Large Features vs. Small Fixes
- **Large Features & Architecture Changes**: For substantial new features, schema updates, or architectural changes, please open an issue (or comment on an existing one) to discuss your proposal before starting. This ensures alignment with the project roadmap and prevents duplicate effort.
- **Small Fixes, Bug Fixes & Documentation**: Bug fixes, typo corrections, documentation improvements, and test coverage additions do not require prior assignment — feel free to open a pull request directly!

### 2. Respectful & Professional Communication
- All communications across issues, pull requests, code reviews, and discussions must strictly remain **polite, courteous, constructive, and professional**.
- Always explain technical decisions clearly, ask questions respectfully, and treat maintainers and fellow contributors with dignity.
- Unprofessional language, personal attacks, sarcasm, or dismissive attitudes will not be tolerated and will result in warnings or restrictions under our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Quick Start & Local Setup

### Prerequisites
- **Python**: 3.11 or later
- **Node.js**: 20.x or later (`npm` 10+)
- **PostgreSQL**: 15+ (or run via Docker or cloud provider like Neon)
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/Kesavaraja67/telex.git
cd telex
```

### 2. Backend Setup (`apps/api`)
```bash
cd apps/api

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies including development tooling
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your local database URL and test settings

# Run migrations
alembic upgrade head

# Start development server with auto-reload
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup (`apps/web`)
```bash
cd apps/web

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env.local

# Run Next.js dev server
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Coding Standards

### 1. Python Code (Backend)
- **Formatting**: We use [Black](https://github.com/psf/black) with a line length of 100 characters.
- **Linting & Import Sorting**: We use [Ruff](https://github.com/astral-sh/ruff) for lightning-fast linting, bug detection, and import sorting.
- **Type Hints**: Type annotations are required on all public functions, schemas, and service methods.

#### Running Formatters & Linters Locally
```bash
cd apps/api

# Auto-format and sort imports
ruff check --fix .
black .

# Check formatting and linting without making changes
ruff check .
black --check .
```

### 2. Code Comments Rule: Simple English Only
To ensure our codebase is accessible, clear, and easy to maintain for contributors around the world:
- **All code comments and docstrings must be written in simple, plain English.**
- Keep sentences short, concise, and direct.
- Explain *why* code does something non-obvious rather than restating what the code already clearly shows.
- Avoid obscure slang, informal idioms, or overly complex academic vocabulary.

**Good Example:**
```python
# Check if the repository is already active in the database.
# If it exists, update its branch name; otherwise, insert a new record.
```

**Bad Example:**
```python
# Here we elucidate the pre-existence of the target codebase artifact
# within our relational datastore prior to conditional transmutation...
```

### 3. Frontend Code (`apps/web`)
- Built with **Next.js (App Router)** and **React 19**.
- Use **TypeScript** strictly. Avoid `any` where possible.
- Run type checks and linter before submitting:
  ```bash
  cd apps/web
  npx tsc --noEmit
  npm run lint
  ```

---

## Pull Request Guidelines

To maintain code quality, reliability, and visual excellence, every pull request must meet the following criteria:

### 1. Mandatory Visual Evidence (Screenshots or Video)
- **If your PR modifies the UI, styling, dashboard, landing page, or user workflows, you MUST include visual proof in your PR description.**
- Acceptable formats:
  - **Screenshots** (PNG, JPG) showing Before and After states.
  - **Screen Recordings** (GIF, MP4, WebM) demonstrating the interaction flow.
- PRs modifying visual components without screenshots or video recordings will be paused until provided.

### 2. Appropriate Tests & Above 80% Test Coverage
- **Appropriate automated tests are required for all changes.** Every bug fix, new feature, and logic adjustment must include comprehensive unit/integration tests.
- Backend tests are written with `pytest` in `apps/api/tests/`.
- The CI test suite strictly enforces a minimum of **80% test coverage** using `pytest-cov` (`--cov-fail-under=80`). PRs failing this gate cannot be merged.
- Always run the test suite and verify test coverage locally before submitting:
  ```bash
  cd apps/api
  pytest --cov=. --cov-report=term-missing --cov-fail-under=80
  ```

### 3. Strict Git Policy: No Rebasing & No Force Pushing
To maintain a safe, traceable, and conflict-free collaboration environment:
- **No Force Pushing (`git push --force` or `--force-with-lease`)**: Never force push to branches that have open pull requests. Force pushing rewrites commit history, breaks reviewers' comment threads, and deletes previous review states.
- **No Rebasing PR Branches**: Do not rebase branches after opening a pull request. If you need to sync your branch with `main`, merge `main` into your branch (`git merge origin/main`) or let maintainers handle branch updates.
- **Squash and Merge Only**: Maintainers merge all approved pull requests using GitHub's **Squash and Merge**. This guarantees a clean, linear, and atomic commit history on `main` without requiring contributors to rebase manually.

### 4. Conventional Commit Messages
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `style:` Changes that do not affect the meaning of the code (white-space, formatting)
- `refactor:` A code change that neither fixes a bug nor adds a feature
- `test:` Adding missing tests or correcting existing tests
- `chore:` Changes to the build process or auxiliary tools

*Example*: `feat(scanner): add tree-sitter support for python decorator calls`

### 5. Branch Naming
- Features: `feat/short-description`
- Bug fixes: `fix/short-description`
- Documentation: `docs/short-description`

---

## Pull Request Checklist

Before submitting your PR, make sure you can check off all items:

- [ ] **Professional Conversation**: All communication in the issue, PR description, and reviews is polite, respectful, and professional.
- [ ] **Simple English Comments**: All code comments and docstrings are written strictly in simple, clear, and direct English.
- [ ] **Appropriate Tests Included**: Comprehensive tests have been added or updated for all modified logic.
- [ ] **Test Coverage Above 80%**: Backend test suite passes locally and maintains **above 80% test coverage** (`--cov-fail-under=80`).
- [ ] **No Force Pushes or Rebasing**: Commit history has not been rewritten or force pushed (`--force`).
- [ ] **Formatting & Linting**: Code passes `black .` formatting and `ruff check .` linting in `apps/api`.
- [ ] **Frontend Validation**: Frontend passes type checking (`npx tsc --noEmit`) and linting (`npm run lint`) with zero errors.
- [ ] **Visual Evidence Attached**: For any UI, styling, or dashboard changes, screenshots or screen recordings (GIF/MP4) are attached.
- [ ] **Clean Commits**: Commit messages follow Conventional Commits standard (`feat:`, `fix:`, `docs:`).

---

## Getting Help

Have questions or need assistance?
- Open an issue using our [Issue Templates](.github/ISSUE_TEMPLATE/).
- Discuss architectural ideas in GitHub Discussions or reach out to maintainers.

Thank you for helping make Telex the best autonomous dependency self-healing platform!
