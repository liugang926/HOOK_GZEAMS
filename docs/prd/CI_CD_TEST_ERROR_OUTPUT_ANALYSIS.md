# CI/CD 自动化测试错误输出分析 PRD

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-05 |
| 分析范围 | GitHub Actions CI 工作流 |
| 状态 | 待修复 |

---

## 一、CI/CD 工作流概述

### 1.1 工作流配置文件
- **位置**: `.github/workflows/ci.yml`
- **触发条件**: Push 到任意分支，PR 到 master/main

### 1.2 CI 任务矩阵

| 任务名称 | 类型 | 状态 | 说明 |
|---------|------|------|------|
| detect-changes | 检测变更 | - | 路径过滤器，跳过不必要的任务 |
| backend-lint | 后端代码检查 | ❌ 需验证 | Black, isort, flake8, mypy |
| backend-test | 后端单元测试 | ❌ 需验证 | pytest with coverage |
| frontend-lint | 前端代码检查 | ❌ 失败 | ESLint, i18n 检查, Prettier |
| frontend-unit | 前端单元测试 | ✅ 通过 | Vitest with coverage |
| frontend-e2e | 前端 E2E 测试 | ❓ 需验证 | Playwright 测试套件 |
| frontend-e2e-backend-search | 后端搜索 E2E | ❓ 需验证 | 非阻塞测试 |
| security-scan | 安全扫描 | ✅ 非阻塞 | npm audit, safety check |
| status-check | 状态检查 | - | 汇总所有任务状态 |

---

## 二、前端 Lint 错误详情

### 2.1 错误统计
- **总问题数**: 2425 个
- **错误数**: 56 个
- **警告数**: 2369 个

### 2.2 错误分类

| 错误类型 | 数量 | 严重程度 | 说明 |
|---------|------|----------|------|
| no-useless-escape | 47 | 高 | 不必要的转义字符 |
| vue/no-dupe-keys | 2 | 高 | Vue 组件重复键 |
| typescript-eslint/no-empty-object-type | 5 | 中 | 空对象类型 `{}` |
| Parsing error | 1 | 严重 | 语法解析错误 |
| no-useless-catch | 1 | 中 | 不必要的 try/catch 包装 |

### 2.3 严重错误详情

#### 2.3.1 解析错误 (Parsing Error)
```
文件: src/views/dynamic/DynamicListPage.vue
位置: 272:37
错误: Parsing error: ',' expected
```

#### 2.3.2 Vue 组件重复键 (Duplicate Keys)
```
文件: src/components/designer/WysiwygLayoutDesigner.vue

错误 1:
位置: 820:7
错误: Duplicate key 'translationMode'. May cause name collision in script or template tag

错误 2:
位置: 876:7
错误: Duplicate key 'isDefault'. May cause name collision in script or template tag
```

#### 2.3.3 空对象类型 (Empty Object Type)
```
文件: src/types/integration.ts
错误: Don't use `{}` as a type. `{}` actually means "any non-nullish value".

受影响行:
- 第 2 行第 76 列
- 第 5 行第 80 列
- 第 14 行第 76 列
- 第 17 行第 76 列
- 第 19 行第 64 列
```

#### 2.3.4 不必要的转义字符 (Useless Escapes)
```
主要受影响文件:
- fix_garbled_2.cjs (大量转义字符错误)
```

#### 2.3.5 不必要的 Try/Catch (Useless Catch)
```
文件: src/views/finance/DepreciationList.vue
位置: 109:5
错误: Unnecessary try/catch wrapper
```

---

## 三、i18n 检查错误详情

### 3.1 硬编码文本违规 (Hardcode Violations)

| 文件 | 行号 | 类型 | 内容 |
|------|------|------|------|
| ExportButton.vue | 14 | cjk-literal | filename="资产列表" |
| ImportButton.vue | 15 | cjk-literal | filename="资产" |
| ImportButton.vue | 23 | cjk-literal | await myApi.create(row) 注释 |
| MainLayout.vue | 15 | template-text-literal | <span class="logo-icon">G</span> |
| MainLayout.vue | 20 | template-text-literal | >GZEAMS</span> |
| exportService.ts | 59 | cjk-literal | return value ? '是' : '否' |
| UserPortal.vue | 4 | cjk-literal | 三个 Tab，面向普通员工的"我的"入口： |
| SSOConfigPage.vue | 227 | cjk-literal | label="企业微信" |
| SSOConfigPage.vue | 231 | cjk-literal | label="钉钉" |
| SSOConfigPage.vue | 235 | cjk-literal | label="飞书" |
| SSOConfigPage.vue | 345 | cjk-literal | label="企业微信 (WeWork)" |
| SSOConfigPage.vue | 349 | cjk-literal | label="钉钉 (DingTalk)" |
| SSOConfigPage.vue | 353 | cjk-literal | label="飞书 (Feishu)" |

### 3.2 i18n 语言环境对等检查 (Locale Parity Check)

| 模块 | 基础条目 | 目标条目 | 状态 | 问题 |
|------|---------|---------|------|------|
| integration.json | 106 | 106 | ⚠️ 警告 | 96 个可疑值 (suspiciousValues) |
| 其他模块 | - | - | ✅ 通过 | 无问题 |

### 3.3 i18n 动态覆盖检查
- **状态**: ✅ 通过
- **覆盖率**: 100%
- **阈值**: 95%

### 3.4 i18n P1 缺陷门禁
- **状态**: ✅ 通过
- **活跃缺陷数**: 0

---

## 四、后端检查状态

### 4.1 依赖安装问题
```
错误: ImportError: cannot import name 'main' from 'pip._internal.cli.main'
错误: ImportError: cannot import name 'sync_to_async' from 'asgiref.sync'
```

### 4.2 Django 检查失败
```
错误: Couldn't import Django. Are you sure it's installed?
原因: asgiref 版本不兼容或依赖损坏
```

---

## 五、其他检查结果

### 5.1 布局顺序一致性
- **状态**: ✅ 通过
- **一致性**: 100%
- **阈值**: 100%

### 5.2 关联表元数据审计
- **状态**: ✅ 通过
- **问题数**: 0

### 5.3 TypeScript 类型检查
- **状态**: ✅ 通过
- **命令**: `npm run typecheck:app`

---

## 六、修复优先级

### P0 - 阻塞 CI 的问题 (必须立即修复)

1. **前端 Lint 错误 (56 个)**
   - [ ] 修复 `DynamicListPage.vue` 解析错误
   - [ ] 修复 `WysiwygLayoutDesigner.vue` 重复键
   - [ ] 修复 `integration.ts` 空对象类型
   - [ ] 清理 `fix_garbled_2.cjs` 或移除无用转义字符

2. **后端依赖问题**
   - [ ] 修复 asgiref 导入问题
   - [ ] 确保所有依赖正确安装

### P1 - 高优先级问题

1. **i18n 硬编码文本 (13 处)**
   - [ ] 替换所有 CJK 字面量为 i18n 键
   - [ ] 或添加 `// i18n-hardcode-ignore` 注释

2. **i18n 可疑值 (96 个)**
   - [ ] 检查 `integration.json` 中的可疑值

### P2 - 中优先级问题

1. **ESLint 警告 (2369 个)**
   - [ ] 减少 `any` 类型使用
   - [ ] 移除 console 语句
   - [ ] 清理未使用的变量

---

## 七、CI 失败根因分析

### 7.1 直接原因
1. **frontend-lint 任务失败**: ESLint 报告 56 个错误，超过 `--max-warnings 0` 限制
2. **i18n:check 失败**: 发现 13 处硬编码文本违规

### 7.2 根本原因
1. **代码规范未严格执行**: 开发过程中未及时修复 lint 错误
2. **i18n 标准未完全落地**: 新增组件未遵循国际化标准
3. **依赖管理问题**: 后端环境依赖版本冲突

---

## 八、建议修复步骤

### 阶段一：恢复 CI 通过 (P0)
1. 修复 56 个 ESLint 错误
2. 解决后端依赖问题
3. 确保 CI 工作流全部任务通过

### 阶段二：提升代码质量 (P1)
1. 修复 i18n 硬编码问题
2. 检查并修复可疑值
3. 减少 lint 警告数量

### 阶段三：持续改进 (P2)
1. 配置本地 pre-commit hook
2. 定期执行 CI 检查
3. 建立代码审查规范

---

## 九、附录

### 9.1 CI 工作流文件
- 位置: `.github/workflows/ci.yml`

### 9.2 相关脚本
- `frontend/scripts/i18n-hardcode-check.mjs`
- `frontend/scripts/i18n-locale-parity-check.mjs`
- `frontend/scripts/i18n-coverage-metrics.mjs`

### 9.3 检查命令
```bash
# 前端 lint
cd frontend && npm run lint

# i18n 检查
cd frontend && npm run i18n:check
cd frontend && npm run i18n:parity:all:strict
cd frontend && npm run i18n:coverage:all:strict

# 类型检查
cd frontend && npm run typecheck:app
```
