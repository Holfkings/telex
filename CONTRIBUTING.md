# Contributing to Telex

Thank you for your interest in contributing to **Telex**! Telex is an open-source autonomous dependency self-healing system designed for production codebases.

We welcome contributions of all kinds: bug fixes, new features, documentation enhancements, performance optimizations, and architectural improvements.

---

## Code of Conduct

All contributors and maintainers are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md) to ensure an inclusive, welcoming, and harassment-free community.

---

## Issue Assignment & Contribution Policies

To ensure fair collaboration, prevent duplicate efforts, and maintain an orderly workflow, all contributors must follow these rules:

### 1. Request Assignment Before Starting Work
- **Do not start work or submit a pull request without being officially assigned first.**
- If you want to work on an open issue, leave a professional comment on the issue asking a maintainer to assign it to you:
  > *"Hi maintainers! I would like to work on this issue. Could you please assign it to me?"*
- Wait until a maintainer formally assigns the issue to you on GitHub before starting implementation.

### 2. One Contributor per Issue
- **Each issue is assigned to exactly one (1) contributor at a time.**
- Two people cannot work on the same issue at the same time. This avoids wasted effort and conflicting solutions.
- If an assigned contributor is inactive for more than 7 consecutive days without posting a status update, maintainers reserve the right to reassign the issue to another contributor.

### 3. Maximum 2 Active Issues per Contributor
- A contributor can be assigned to **at most two (2) active issues at the same time**.
- Once you complete and merge your open pull requests, you may request assignment on new issues.

### 4. Professional Communication
- All communications across issues, pull requests, and discussions must be **polite, courteous, constructive, and professional**.
- Explain technical decisions clearly, ask questions constructively, and respect the time of fellow contributors and maintainers.

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

### 2. 80% Test Coverage Requirement
- All backend code changes must include unit tests.
- Our CI pipeline enforces a minimum of **80% test coverage** using `pytest-cov`.
- Test your coverage locally before opening a PR:
  ```bash
  cd apps/api
  pytest --cov=. --cov-report=term-missing --cov-fail-under=80
  ```

### 3. Conventional Commit Messages
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `style:` Changes that do not affect the meaning of the code (white-space, formatting)
- `refactor:` A code change that neither fixes a bug nor adds a feature
- `test:` Adding missing tests or correcting existing tests
- `chore:` Changes to the build process or auxiliary tools

*Example*: `feat(scanner): add tree-sitter support for python decorator calls`

### 4. Branch Naming
- Features: `feat/short-description`
- Bug fixes: `fix/short-description`
- Documentation: `docs/short-description`

---

## Pull Request Checklist

Before submitting your PR, make sure you can check off all items:

- [ ] My code adheres to the project's formatting (`black`) and linting (`ruff`) standards.
- [ ] All comments and documentation are written in **simple, clear English**.
- [ ] Backend test suite passes and maintains at least **80% test coverage**.
- [ ] Frontend type check (`npx tsc --noEmit`) and lint (`npm run lint`) pass with zero errors.
- [ ] For any UI/visual changes: **Screenshots or screen-recorded video (GIF/MP4) are attached** to the PR description.
- [ ] Commit history is clean and follows Conventional Commits.

---

## Getting Help

Have questions or need assistance?
- Open an issue using our [Issue Templates](.github/ISSUE_TEMPLATE/).
- Discuss architectural ideas in GitHub Discussions or reach out to maintainers.

Thank you for helping make Telex the best autonomous dependency self-healing platform!
