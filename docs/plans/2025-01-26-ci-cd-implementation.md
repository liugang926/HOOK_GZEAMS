# CI/CD 自动化测试流水线实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use @superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 GZEAMS 项目构建完整的 GitHub Actions CI/CD 自动化测试流水线，包含代码质量检查、单元测试、E2E 测试和安全扫描。

**Architecture:** 使用 GitHub Actions 平台，通过路径过滤实现智能触发（backend/frontend 变更独立运行），采用并行任务策略加速执行，配置依赖缓存优化构建时间。

**Tech Stack:** GitHub Actions, pytest, Vitest, Playwright, black, flake8, isort, mypy, ESLint, Prettier, safety, npm audit

---

## 文件清单

### 需要创建的文件

| 文件 | 用途 |
|------|------|
| `.github/workflows/ci.yml` | 主 CI 流水线配置 |
| `backend/pyproject.toml` | Python 代码质量工具统一配置 |
| `backend/.coveragerc` | pytest 覆盖率配置 |
| `backend/.flake8` | flake8 代码规范配置 |

### 需要修改的文件

| 文件 | 修改内容 |
|------|----------|
| `backend/pytest.ini` | 添加覆盖率参数 |
| `frontend/playwright.config.ts` | 优化 CI 环境配置 |

---

## Task 1: 创建 Backend 代码质量配置文件

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.flake8`
- Create: `backend/.coveragerc`

### Step 1: Create pyproject.toml

This file unifies configuration for black, flake8, isort, and mypy.

```toml
# backend/pyproject.toml

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
    | migrations
)/
'''

[tool.isort]
profile = 'black'
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
skip_gitignore = true
skip_glob = ['*/migrations/*']

[tool.mypy]
python_version = '3.11'
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true
exclude = [
    'migrations/',
    'venv/',
    'build/',
    'dist/',
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = 'config.settings.test'
python_files = ['test_*.py']
python_classes = ['Test*']
python_functions = ['test_*']
addopts = [
    '--tb=short',
    '--strict-markers',
    '--cov=apps',
    '--cov-report=xml',
    '--cov-report=html',
    '--cov-report=term-missing:skip-covered',
    '--cov-fail-under=80',
]
markers = [
    'slow: marks tests as slow (deselect with "-m \"not slow\"")',
    'integration: marks tests as integration tests',
]
```

### Step 2: Create .flake8 configuration

```ini
# backend/.flake8

[flake8]
max-line-length = 100
exclude =
    .git,
    __pycache__,
    migrations,
    venv,
    build,
    dist,
    .tox,
    *.egg-info
ignore =
    # E203: whitespace before ':' (conflicts with black)
    E203,
    # W503: line break before binary operator (conflicts with black)
    W503,
    # C901: too complex (handle with cognitive complexity later)
    C901,
max-complexity = 10
per-file-ignores =
    __init__.py:F401
```

### Step 3: Create .coveragerc configuration

```ini
# backend/.coveragerc

[run]
source = apps
omit =
    */migrations/*
    */tests/*
    */conftest.py
    */venv/*
    */__pycache__/*
branch = true

[report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__..:
    if TYPE_CHECKING:
    @abstractmethod

[html]
directory = htmlcov
```

### Step 4: Verify configurations exist

Run: `ls -la backend/ | grep -E "(pyproject|flake8|coveragerc)"`

Expected output:
```
pyproject.toml
.flake8
.coveragerc
```

### Step 5: Commit

```bash
git add backend/pyproject.toml backend/.flake8 backend/.coveragerc
git commit -m "chore: add Python code quality configuration files"
```

---

## Task 2: 更新 pytest.ini 配置

**Files:**
- Modify: `backend/pytest.ini`

### Step 1: Read current pytest.ini

Current content (from exploration):
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --tb=short
    --strict-markers
```

### Step 2: Update pytest.ini with coverage options

Replace `backend/pytest.ini` content with:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --tb=short
    --strict-markers
    --cov=apps
    --cov-report=xml
    --cov-report=html
    --cov-report=term-missing:skip-covered
    --cov-fail-under=80
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
```

### Step 3: Verify pytest configuration

Run: `cd backend && python -m pytest --help | grep -A 5 "cov options"`

Expected: Output should include coverage options (requires pytest-cov installed)

### Step 4: Commit

```bash
git add backend/pytest.ini
git commit -m "chore: update pytest.ini with coverage configuration"
```

---

## Task 3: 优化 Playwright CI 配置

**Files:**
- Modify: `frontend/playwright.config.ts`

### Step 1: Update playwright.config.ts for CI

Update the `projects` section in `frontend/playwright.config.ts` to add a CI-only project:

```typescript
// Replace the projects array with:
projects: [
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'] },
  },

  // CI-only project - runs only chromium on GitHub Actions
  {
    name: 'ci-chromium',
    use: { ...devices['Desktop Chrome'] },
    // Only run this project on CI
    only: process.env.CI === 'true' ? true : undefined,
  },

  // The following projects are disabled on CI for speed
  ...(process.env.CI !== 'true' ? [
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ] : []),
],
```

### Step 2: Verify Playwright config syntax

Run: `cd frontend && npx playwright test --list` (requires playwright installed)

Expected: List of test files, or "no tests found" if directory is empty

### Step 3: Commit

```bash
git add frontend/playwright.config.ts
git commit -m "chore: optimize Playwright config for CI environment"
```

---

## Task 4: 创建主 CI 工作流文件

**Files:**
- Create: `.github/workflows/ci.yml`

### Step 1: Create .github/workflows directory

Run: `mkdir -p .github/workflows`

### Step 2: Create the main CI workflow file

Create `.github/workflows/ci.yml` with:

```yaml
name: CI

on:
  push:
    branches: ['**']
  pull_request:
    branches: [master, main]

jobs:
  # ============================================================================
  # Job 1: Detect path changes to skip unnecessary jobs
  # ============================================================================
  detect-changes:
    name: Detect Changes
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.changes.outputs.backend }}
      frontend: ${{ steps.changes.outputs.frontend }}
      workflow: ${{ steps.changes.outputs.workflow }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Detect changes
        uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            backend:
              - 'backend/**'
              - '.github/workflows/**'
            frontend:
              - 'frontend/**'
              - '.github/workflows/**'
            workflow:
              - '.github/workflows/ci.yml'

  # ============================================================================
  # Job 2: Backend - Code Quality Check
  # ============================================================================
  backend-lint:
    name: Backend - Lint
    runs-on: ubuntu-latest
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements/**/*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements/development.txt

      - name: Run black check
        run: |
          cd backend
          black --check .

      - name: Run isort check
        run: |
          cd backend
          isort --check-only .

      - name: Run flake8
        run: |
          cd backend
          flake8 .

      - name: Run mypy (non-blocking)
        run: |
          cd backend
          mypy . || true

  # ============================================================================
  # Job 3: Backend - Unit Tests
  # ============================================================================
  backend-test:
    name: Backend - Tests
    runs-on: ubuntu-latest
    needs: detect-changes
    if: needs.detect-changes.outputs.backend == 'true'

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: gzeams_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DJANGO_SETTINGS_MODULE: config.settings.test
      DATABASE_URL: postgres://postgres:postgres@localhost:5432/gzeams_test
      REDIS_URL: redis://localhost:6379/0

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Cache pip packages
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('backend/requirements/**/*.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements/development.txt

      - name: Run migrations
        run: |
          cd backend
          python manage.py migrate
          python manage.py sync_schemas

      - name: Run tests with coverage
        run: |
          cd backend
          pytest --cov=apps --cov-report=xml --cov-report=html --cov-report=term-missing:skip-covered

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend
          name: backend-coverage

      - name: Archive coverage reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: backend-coverage-report
          path: backend/htmlcov/
          retention-days: 7

      - name: Archive test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: backend-test-results
          path: backend/.pytest_cache/
          retention-days: 7

  # ============================================================================
  # Job 4: Frontend - Code Quality Check
  # ============================================================================
  frontend-lint:
    name: Frontend - Lint
    runs-on: ubuntu-latest
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v3
        with:
          path: frontend/node_modules
          key: ${{ runner.os }}-node-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run ESLint
        run: |
          cd frontend
          npm run lint -- --max-warnings 0

      - name: Run Prettier check
        run: |
          cd frontend
          npx prettier --check "src/**/*.{vue,ts,js,tsx,jsx}"

  # ============================================================================
  # Job 5: Frontend - Unit Tests
  # ============================================================================
  frontend-unit:
    name: Frontend - Unit Tests
    runs-on: ubuntu-latest
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v3
        with:
          path: frontend/node_modules
          key: ${{ runner.os }}-node-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run unit tests with coverage
        run: |
          cd frontend
          npm run test:coverage -- --run

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./frontend/coverage/coverage-final.json
          flags: frontend
          name: frontend-coverage

      - name: Archive coverage reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: frontend-coverage-report
          path: frontend/coverage/
          retention-days: 7

  # ============================================================================
  # Job 6: Frontend - E2E Tests
  # ============================================================================
  frontend-e2e:
    name: Frontend - E2E Tests
    runs-on: ubuntu-latest
    needs: detect-changes
    if: needs.detect-changes.outputs.frontend == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Cache node modules
        uses: actions/cache@v3
        with:
          path: frontend/node_modules
          key: ${{ runner.os }}-node-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-node-

      - name: Cache Playwright browsers
        uses: actions/cache@v3
        with:
          path: frontend/node_modules/.cache/ms-playwright
          key: ${{ runner.os }}-playwright-${{ hashFiles('frontend/package-lock.json') }}
          restore-keys: |
            ${{ runner.os }}-playwright-

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Playwright browsers
        run: |
          cd frontend
          npx playwright install --with-deps chromium

      - name: Build frontend
        run: |
          cd frontend
          npm run build

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test --project=chromium
        env:
          CI: true

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: frontend/playwright-report/
          retention-days: 7

      - name: Upload test artifacts
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-test-results
          path: |
            frontend/test-results/
            frontend/playwright-report/
          retention-days: 7

  # ============================================================================
  # Job 7: Security Scanning
  # ============================================================================
  security-scan:
    name: Security - Dependency Scan
    runs-on: ubuntu-latest
    needs: detect-changes
    if: |
      needs.detect-changes.outputs.backend == 'true' ||
      needs.detect-changes.outputs.frontend == 'true'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install safety for Python dependency scanning
        run: pip install safety

      - name: Run Python dependency security check
        run: |
          cd backend
          safety check --json || true
        continue-on-error: true

      - name: Run npm audit
        run: |
          cd frontend
          npm audit --audit-level=moderate || true
        continue-on-error: true

      - name: Run npm audit (production only)
        run: |
          cd frontend
          npm audit --audit-level=high --production || true
        continue-on-error: true

  # ============================================================================
  # Job 8: Status Check (Optional - for GitHub branch protection)
  # ============================================================================
  status-check:
    name: CI Status Check
    runs-on: ubuntu-latest
    needs:
      - backend-lint
      - backend-test
      - frontend-lint
      - frontend-unit
      - frontend-e2e
      - security-scan
    if: always()

    steps:
      - name: Check all jobs status
        run: |
          if [[ "${{ needs.backend-lint.result }}" != "success" ]] ||
             [[ "${{ needs.backend-test.result }}" != "success" ]] ||
             [[ "${{ needs.frontend-lint.result }}" != "success" ]] ||
             [[ "${{ needs.frontend-unit.result }}" != "success" ]] ||
             [[ "${{ needs.frontend-e2e.result }}" != "success" ]]; then
            echo "::error::One or more jobs failed"
            exit 1
          fi
          echo "All jobs passed successfully!"
```

### Step 3: Verify YAML syntax

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`

Expected: No errors (requires PyYAML installed, or use online YAML validator)

### Step 4: Commit

```bash
git add .github/workflows/ci.yml
git commit -m "feat: add GitHub Actions CI workflow"
```

---

## Task 5: 更新 README.md 添加 CI Badge

**Files:**
- Modify: `README.md` (if exists, otherwise create)

### Step 1: Check if README exists

Run: `ls -la README.md 2>/dev/null || echo "README.md not found"`

### Step 2: Add CI badges to README

If `README.md` exists, add at the top of the file:

```markdown
[![CI](https://github.com/liugang926/HOOK_GZEAMS/workflows/CI/badge.svg)](https://github.com/liugang926/HOOK_GZEAMS/actions)
[![codecov](https://codecov.io/gh/liugang926/HOOK_GZEAMS/branch/master/graph/badge.svg)](https://codecov.io/gh/liugang926/HOOK_GZEAMS)

# GZEAMS - Hook Fixed Assets Management System
...
```

If `README.md` doesn't exist, create it with:

```markdown
# GZEAMS - Hook Fixed Assets Management System

[![CI](https://github.com/liugang926/HOOK_GZEAMS/workflows/CI/badge.svg)](https://github.com/liugang926/HOOK_GZEAMS/actions)
[![codecov](https://codecov.io/gh/liugang926/HOOK_GZEAMS/branch/master/graph/badge.svg)](https://codecov.io/gh/liugang926/HOOK_GZEAMS)

## Overview

GZEAMS is a metadata-driven low-code platform for enterprise fixed asset management.

## Quick Start

See [docs/](./docs) for detailed documentation.
```

### Step 3: Verify README content

Run: `head -20 README.md`

Expected: Badges and project title visible

### Step 4: Commit

```bash
git add README.md
git commit -m "docs: add CI badge to README"
```

---

## Task 6: 可选 - 配置 Codecov

**Files:**
- Create: `codecov.yml` (optional)
- Modify: GitHub repository settings (manual step)

### Step 1: Create codecov.yml (optional)

Create `codecov.yml` at project root:

```yaml
# Codecov configuration
coverage:
  status:
    project:
      default:
        target: 80%
        threshold: 1%
        base: auto
    patch:
      default:
        target: 75%

comment:
  layout: "reach,diff,flags,files,footer"
  behavior: default
  require_changes: false

ignore:
  - "**/migrations/**"
  - "**/tests/**"
  - "**/test_*.py"
```

### Step 2: Commit

```bash
git add codecov.yml
git commit -m "chore: add codecov configuration"
```

### Step 3: Enable Codecov on GitHub (Manual)

1. Visit https://codecov.io
2. Sign up with GitHub account
3. Add repository `liugang926/HOOK_GZEAMS`
4. Copy the upload token (if needed for private repo)

---

## Task 7: 本地验证配置

**Files:**
- No file changes - validation only

### Step 1: Test backend linting locally

Run: `cd backend && black --check .`

Expected: No output if files are properly formatted, or list of files to reformat

### Step 2: Test backend isort locally

Run: `cd backend && isort --check-only .`

Expected: No output if imports are properly sorted

### Step 3: Test backend flake8 locally

Run: `cd backend && flake8 .`

Expected: No output if code follows style guide

### Step 4: Test backend pytest with coverage

Run: `cd backend && pytest --cov=apps --cov-report=term-missing:skip-covered`

Expected: Tests run with coverage summary

### Step 5: Test frontend lint locally

Run: `cd frontend && npm run lint`

Expected: ESLint passes with no errors

### Step 6: Test frontend unit tests

Run: `cd frontend && npm run test:coverage`

Expected: Tests run with coverage report

### Step 7: No commit needed for this task

This is validation only - no code changes

---

## Task 8: 推送并触发 CI

**Files:**
- None - git operations only

### Step 1: Push all commits to remote

Run: `git push origin HEAD`

Expected: Commits pushed successfully

### Step 2: Verify CI workflow starts

1. Visit: https://github.com/liugang926/HOOK_GZEAMS/actions
2. Check that the "CI" workflow is running

Expected: CI workflow triggered automatically

### Step 3: Monitor workflow execution

Watch the workflow run through all jobs:
1. detect-changes
2. backend-lint
3. backend-test
4. frontend-lint
5. frontend-unit
6. frontend-e2e
7. security-scan
8. status-check

Expected: All jobs pass (may take 5-10 minutes on first run)

### Step 4: Download and review artifacts (optional)

1. Go to the workflow run page
2. Scroll to "Artifacts" section
3. Download coverage reports for review

### Step 5: No commit needed

This task is about triggering and monitoring CI

---

## Task 9: 配置 GitHub Branch Protection (可选)

**Files:**
- None - GitHub UI configuration

### Step 1: Go to repository settings

1. Visit: https://github.com/liugang926/HOOK_GZEAMS/settings
2. Click "Branches" in left sidebar

### Step 2: Add branch protection rule for master/main

1. Click "Add branch protection rule"
2. Branch name pattern: `master` or `main`
3. Enable:
   - [x] Require status checks to pass before merging
   - [x] Require branches to be up to date before merging
4. Select required status checks:
   - [x] CI Status Check
5. Save changes

### Step 6: No commit needed

This is GitHub UI configuration only

---

## 验证清单

在完成所有任务后，验证以下内容：

### Backend 验证

- [ ] `black --check .` passes
- [ ] `isort --check-only .` passes
- [ ] `flake8 .` passes
- [ ] `pytest --cov=apps` runs with coverage
- [ ] Coverage report is generated (htmlcov/)

### Frontend 验证

- [ ] `npm run lint` passes
- [ ] `npm run test:coverage` runs
- [ ] `npm run test:e2e` runs with chromium only

### CI 验证

- [ ] CI workflow triggers on push
- [ ] All jobs complete successfully
- [ ] Coverage reports are uploaded
- [ ] Artifacts are available for download

### 配置文件验证

- [ ] `.github/workflows/ci.yml` exists and valid
- [ ] `backend/pyproject.toml` exists
- [ ] `backend/.flake8` exists
- [ ] `backend/.coveragerc` exists
- [ ] `backend/pytest.ini` updated with coverage options
- [ ] `frontend/playwright.config.ts` optimized for CI

---

## 故障排查

### 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| Backend tests fail to connect to DB | PostgreSQL service not ready | Add health check wait time |
| Frontend build fails | Node version mismatch | Ensure Node 18 is used |
| E2E tests timeout | Playwright browsers not installed | Run `npx playwright install` |
| Coverage below threshold | New code without tests | Add tests or adjust threshold |
| Path filter not working | dorny/paths-filter version | Check v2 is being used |

### 调试命令

```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"

# Test backend locally with Docker
docker-compose up -d postgres redis
cd backend && pytest

# Test frontend locally
cd frontend && npm run build && npm run test:e2e
```

---

## 参考资料

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Codecov Documentation](https://codecov.io/)
