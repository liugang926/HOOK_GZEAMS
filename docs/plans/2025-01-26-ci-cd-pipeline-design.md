# CI/CD 自动化测试流水线设计文档

## 文档信息

| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2025-01-26 |
| 作者 | Claude (Brainstorming Mode) |
| 状态 | 设计已完成，待实施 |

---

## 一、需求概述

### 1.1 项目背景

GZEAMS (Hook Fixed Assets) 是一个基于 Django 5.0 + Vue3 的企业级固定资产低代码平台。项目已有完整的测试框架，但尚未配置 CI/CD 自动化流水线。

### 1.2 现有测试基础设施

| 类别 | 框架/工具 | 状态 |
|------|----------|------|
| Backend 单元测试 | pytest + pytest-django | ✅ 已配置，42 个测试文件 |
| Frontend 单元测试 | Vitest | ✅ 已配置 |
| E2E 测试 | Playwright | ✅ 已配置，42 个测试场景 |
| 代码覆盖率 | pytest-cov, @vitest/coverage-v8 | ✅ 已配置 |
| CI/CD 平台 | - | ❌ 未配置 |

### 1.3 CI/CD 需求确认

| 需求项 | 选择 |
|--------|------|
| 平台 | GitHub Actions |
| 触发条件 | 所有分支 push 都触发 |
| 部署 | 第一阶段仅测试，暂不部署 |
| 检查内容 | 代码质量 + 测试覆盖率 + E2E + 安全扫描 |
| E2E 浏览器 | 仅 Chromium |

---

## 二、整体架构设计

### 2.1 流水线架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Workflow                      │
│                        (所有分支 push 触发)                      │
└────────────────────────────────────┬────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│  Backend Jobs   │         │  Frontend Jobs  │         │   Security Job  │
│   (并行执行)     │         │   (并行执行)     │         │   (独立执行)     │
└────────┬────────┘         └────────┬────────┘         └────────┬────────┘
         │                           │                           │
         ▼                           ▼                           │
┌─────────────────┐         ┌─────────────────┐                   │
│  1. Lint Check  │         │  1. Lint Check  │                   │
│  2. Type Check  │         │  2. Unit Tests  │                   │
│  3. Unit Tests  │         │  3. E2E Tests   │                   │
│  4. Coverage    │         │  4. Coverage    │                   │
└────────┬────────┘         └────────┬────────┘                   │
         │                           │                           │
         └───────────────┬───────────┴───────────────────────────┘
                         │
                         ▼
                 ┌─────────────────┐
                 │   Final Status  │
                 │ (所有任务都成功) │
                 └─────────────────┘
```

### 2.2 工作流文件结构

```
.github/
└── workflows/
    ├── ci.yml              # 主 CI 流水线
    └── codeql.yml          # CodeQL 安全扫描（可选，GitHub 自动生成）
```

---

## 三、Backend 工作流设计

### 3.1 任务序列

```yaml
backend:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:16
      env: { POSTGRES_PASSWORD: postgres }
    redis:
      image: redis:7-alpine

  steps:
    1. Checkout 代码
    2. 缓存 pip dependencies (pip cache)
    3. 安装 Python 依赖
    4. 代码质量检查:
       - black --check (代码格式)
       - flake8 (代码规范)
       - isort --check-only (导入排序)
       - mypy (类型检查，可选)
    5. 运行测试:
       - pytest --cov=apps --cov-report=xml --cov-report=html
       - 覆盖率阈值: 80%
    6. 上传覆盖率报告到 Codecov
    7. 上传测试结果作为 artifact
```

### 3.2 质量检查标准

| 检查项 | 工具 | 命令 | 失败处理 |
|--------|------|------|----------|
| 代码格式 | black | `black --check .` | CI 失败 |
| 代码规范 | flake8 | `flake8 .` | CI 失败 |
| 导入排序 | isort | `isort --check-only .` | CI 失败 |
| 类型检查 | mypy | `mypy .` | 警告但不失败 |
| 单元测试 | pytest | `pytest -v` | CI 失败 |
| 覆盖率 | pytest-cov | `pytest --cov=apps` | <80% 失败 |

### 3.3 数据库处理

- 使用 GitHub Actions `services` 内置 PostgreSQL
- 每次测试前自动运行 `migrate` + `sync_schemas`
- 测试完成后自动清理

---

## 四、Frontend 工作流设计

### 4.1 任务序列

```yaml
frontend:
  runs-on: ubuntu-latest

  steps:
    1. Checkout 代码
    2. 缓存 node_modules (npm cache)
    3. 安装 Node.js 依赖
    4. 代码质量检查:
       - eslint . --ext .vue,.ts,.js (ESLint 检查)
       - prettier --check "src/**/*.{vue,ts,js}" (格式检查)
    5. 单元测试:
       - vitest run --coverage (Vitest 单元测试)
       - 覆盖率阈值: 80%
    6. E2E 测试:
       - npm run build (构建生产版本)
       - 启动开发服务器后台运行
       - playwright test --project=chromium (仅 Chromium)
       - 失败时上传截图和视频
    7. 上传覆盖率报告
```

### 4.2 E2E 测试特殊处理

| 场景 | 处理方式 |
|------|----------|
| 需要后端 API | 使用 MSW (Mock Service Worker) 拦截请求 |
| 需要登录 | 使用 test/fixtures 中的认证 fixture |
| 测试失败 | 自动截图 + 录屏，上传为 artifact |
| 重试机制 | playwright.config.ts 已配置 `retries: 2` |

### 4.3 缓存策略

- `node_modules` 完整缓存
- Playwright 浏览器二进制缓存 (`playwright --force-browsers-cache-path`)

---

## 五、安全扫描设计

### 5.1 扫描任务

```yaml
security:
  runs-on: ubuntu-latest
  permissions:
    contents: read
    security-events: write

  steps:
    1. Checkout 代码

    2. Python 依赖扫描:
       - pip install safety
       - safety check --json > safety-report.json

    3. Node.js 依赖扫描:
       - npm audit --audit-level=moderate --json
       - 或使用 Snyk (需配置 token)

    4. 代码安全扫描:
       - 使用 CodeQL 分析 (GitHub 内置)
       - 或使用 bandit (Python) + npm audit (JS)

    5. Secrets 扫描:
       - trufflehog (可选，检测硬编码密钥)

    6. 上传 SARIF 报告到 GitHub Security
```

### 5.2 扫描级别设置

| 扫描类型 | 工具 | 失败阈值 |
|----------|------|----------|
| Python 漏洞 | safety | 高危/中危 = 失败 |
| JS 漏洞 | npm audit | 高危 = 失败，中危 = 警告 |
| 代码漏洞 | CodeQL | 高危 = 失败 |
| 密钥泄露 | trufflehog | 发现 = 失败 |

---

## 六、路径过滤与优化

### 6.1 智能路径过滤

```yaml
detect-changes:
  outputs:
    backend: ${{ steps.changes.outputs.backend }}
    frontend: ${{ steps.changes.outputs.frontend }}
  steps:
    - uses: dorny/paths-filter@v2
      id: changes
      with:
        filters: |
          backend:
            - 'backend/**'
            - '.github/workflows/**'
          frontend:
            - 'frontend/**'
            - '.github/workflows/**'

backend:
  needs: detect-changes
  if: needs.detect-changes.outputs.backend == 'true'

frontend:
  needs: detect-changes
  if: needs.detect-changes.outputs.frontend == 'true'
```

### 6.2 缓存策略优化

| 缓存内容 | Key 策略 | 预估节省时间 |
|----------|----------|-------------|
| pip packages | `pip-${{ hashFiles('backend/requirements/*.txt') }}` | ~30s |
| node_modules | `node-${{ hashFiles('frontend/package-lock.json') }}` | ~20s |
| Playwright browsers | `playwright-${{ hashFiles('frontend/package-lock.json') }}` | ~40s |
| pytest cache | `pytest-${{ github.sha }}` | ~10s |

### 6.3 运行时间估算

| 场景 | 并行任务 | 耗时 |
|------|----------|------|
| 仅 backend 变更 | backend + security | ~3-4 分钟 |
| 仅 frontend 变更 | frontend + security | ~4-5 分钟 |
| 全部变更 | backend + frontend + security | ~5-6 分钟 |

---

## 七、完整工作流文件预览

### 7.1 ci.yml 结构

```yaml
name: CI

on:
  push:
    branches: ['**']
  pull_request:
    branches: [master, main]

jobs:
  # 1. 变更检测
  detect-changes:
    # 路径过滤逻辑

  # 2. Backend 测试
  backend-lint:      # 代码质量
  backend-test:      # 单元测试 + 覆盖率

  # 3. Frontend 测试
  frontend-lint:     # 代码质量
  frontend-unit:     # 单元测试 + 覆盖率
  frontend-e2e:      # E2E 测试

  # 4. 安全扫描
  security-scan:     # 依赖漏洞扫描

  # 5. 状态汇总（可选）
  status-check:      # 汇总所有任务结果
```

### 7.2 需要补充的配置文件

| 文件 | 用途 | 状态 |
|------|------|------|
| `backend/pyproject.toml` | 统一配置 black/flake8/isort/mypy | 需创建 |
| `backend/.coveragerc` | pytest 覆盖率配置 | 需创建 |
| `frontend/.eslintrc.cjs` | ESLint 规则 | 已存在 |
| `frontend/vitest.config.ts` | Vitest 覆盖率配置 | 已存在 |

### 7.3 Badge 状态展示

```markdown
[![CI](https://github.com/liugang926/HOOK_GZEAMS/workflows/CI/badge.svg)]
[![Coverage](https://codecov.io/gh/liugang926/HOOK_GZEAMS/branch/master/graph/badge.svg)]
```

---

## 八、实施检查清单

### 8.1 配置文件创建

- [ ] 创建 `.github/workflows/ci.yml`
- [ ] 创建 `backend/pyproject.toml` (代码质量工具配置)
- [ ] 创建 `backend/.coveragerc` (覆盖率配置)

### 8.2 GitHub 配置

- [ ] 在 GitHub Repository Settings 中启用:
  - [ ] Actions (默认已启用)
  - [ ] Code scanning (CodeQL)
  - [ ] Dependabot alerts (依赖安全警报)

### 8.3 第三方服务（可选）

- [ ] Codecov 账号注册 + token 配置
- [ ] Snyk 账号注册 + token 配置（可选，替代 npm audit）

---

## 九、后续扩展方向

### 9.1 部署阶段（Phase 2）

当自动化测试稳定后，可考虑添加：

1. **Docker 镜像构建** - 自动构建并推送到容器镜像服务
2. **自动部署** - SSH 到服务器执行部署脚本
3. **多环境部署** - dev/staging/production 环境分离

### 9.2 通知集成

- [ ] Slack/企业微信/钉钉通知
- [ ] 失败时 @ 相关开发者

---

## 十、参考资源

- [GitHub Actions 官方文档](https://docs.github.com/en/actions)
- [pytest 文档](https://docs.pytest.org/)
- [Vitest 文档](https://vitest.dev/)
- [Playwright 文档](https://playwright.dev/)
- [Codecov 文档](https://codecov.io/)
