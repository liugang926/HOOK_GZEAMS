# REGRESSION_OUTPUT_GOVERNANCE_COMPLETION_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-26 |
| 涉及阶段 | Post-PRD Stabilization / Regression Closure |
| 作者/Agent | Codex (GPT-5) |
| 对应 PRD | `docs/prd/prd-object-layering-history-convergence-2026-03-25.md` |
| 对应实施报告 | `docs/reports/summaries/GZEAMS_OBJECT_HISTORY_CONVERGENCE_REPORT.md` |

## 一、实施概述

本轮工作目标不是新增业务能力，而是完成对象分层与历史语义收敛之后的全量回归闭环，并把前端测试输出中的非阻塞噪音压缩到可接受范围，保证后续迭代在“全量可跑、结果可读、异常可定位”的基线上继续推进。

### 1. 完成内容摘要

- 完成后端全量回归修复与清库重建验证，收口历史实例兼容、工作流聚合、品牌配置请求归一化、通知测试夹具、分页排序、时区与测试基座等问题。
- 完成前端全量回归修复，收口 `Element Plus` 测试 stub、i18n 缺失键、`ColumnManager`/`SectionBlock` 错误文案命名空间、`ActivityTimeline` 文案缺口与测试环境日志噪音。
- 保持对象历史收敛主线不回退，继续沿用统一历史入口、详情页历史聚合、菜单 fallback 审计对象隐藏等既有方案。

### 2. 验证结果

```bash
# Backend clean-db full regression
docker compose exec -T db psql -U postgres -d postgres -c "DROP DATABASE IF EXISTS test_gzeams_test WITH (FORCE);"
docker compose exec -T backend pytest apps/ -q --create-db
# Result: 1336 passed, 2 skipped

# Frontend full unit regression
cd frontend && npm test -- --run
# Result: 184 passed (184 files), 1005 passed (1005 tests)

# Frontend production build
cd frontend && npm run build
# Result: success
```

### 3. 文件清单与代码行数统计

| 范围 | 文件数 | 行数 |
|------|--------|------|
| Backend source + tests | 38 | 19031 |
| Frontend source + tests | 11 | 4269 |
| 合计纳入统计范围 | 49 | 23300 |

### 4. 关键修复分组

| 分组 | 说明 | 代表代码位置 |
|------|------|-------------|
| Backend compatibility hardening | 修复历史实例兼容、品牌 payload 归一化、统一分页排序、测试环境配置与时区告警 | `backend/apps/workflows/services/workflow_engine.py`, `backend/apps/system/viewsets/branding.py`, `backend/apps/common/pagination.py`, `backend/config/settings/test.py` |
| Backend regression test closure | 补齐通知、工作流、管理器与模型测试基座，消除全量回归阻塞项 | `backend/apps/notifications/tests/test_api.py`, `backend/apps/workflows/tests/test_api.py`, `backend/apps/common/tests/test_models.py` |
| Frontend output governance | 修复测试 stub 破坏真实渲染契约的问题，回收 i18n 缺口与测试环境冗余告警 | `frontend/src/__tests__/setup.ts`, `frontend/src/components/common/ColumnManager.vue`, `frontend/src/locales/zh-CN/common.json` |
| Frontend expected-error test silence | 对故意触发异常分支的测试显式接管 `console.warn/error`，保留断言、压缩噪音 | `frontend/src/__tests__/unit/composables/useCrud.spec.ts`, `frontend/src/__tests__/unit/composables/useColumnConfig.spec.ts`, `frontend/src/components/common/__tests__/ErrorBoundary.spec.ts` |

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 审计对象收敛后补齐回归验证，避免历史语义改造引入系统级回归 | 已完成 | `backend/apps/system/viewsets/object_router_relation_actions.py`, `frontend/src/composables/useActivityTimeline.ts` |
| `ChangeHistory` 统一走聚合历史入口，详情页关联区过滤 `log/history` 语义对象 | 已完成并保持稳定 | `frontend/src/components/common/useBaseDetailPageRelations.ts`, `frontend/src/components/common/BaseDetailPage.relationGroups.spec.ts` |
| 菜单 fallback 不重新暴露审计对象 | 已完成并纳入回归覆盖 | `frontend/src/router/menuRegistry.ts`, `backend/apps/system/menu_config.py` |
| 审计语义收敛后需要补定向测试并扩展到全量验证 | 已完成并扩展为 full regression + build gate | `backend/apps/workflows/tests/test_integration_scenarios.py`, `frontend/src/router/menuRegistry.test.ts` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 报告存放于 `docs/reports/` 规范目录 | 符合 | 本报告位于 `docs/reports/compliance/` |
| 报告命名符合 fix/completion 约定 | 符合 | 使用 `REGRESSION_OUTPUT_GOVERNANCE_COMPLETION_REPORT.md` |
| 报告索引同步更新 | 符合 | 已更新 `docs/reports/README.md` |
| 代码注释使用英文 | 符合 | 本轮未新增中文代码注释 |
| 后端动态对象统一路由不回退为独立 URL | 符合 | 所有修复均在现有统一入口与兼容层内完成 |
| 前端测试治理不侵入业务语义 | 符合 | 主要调整测试 stub、测试断言与 locale 文案，不改变业务行为 |
| 全量验证结果可复现 | 符合 | 已记录完整命令、环境和结果摘要 |

## 四、创建文件清单

| 类型 | 路径 | 说明 |
|------|------|------|
| 新增 | `docs/reports/compliance/REGRESSION_OUTPUT_GOVERNANCE_COMPLETION_REPORT.md` | 本次全量回归闭环与输出治理报告 |
| 更新 | `docs/reports/README.md` | 补充报告索引与最近更新记录 |

## 五、后续建议

1. 将前端“预期失败路径”的日志接管模式沉淀为测试约定，避免后续新增用例再次污染全量输出。
2. 为对象历史收敛补一条 Playwright smoke，用于覆盖“详情页历史聚合 + 审计对象菜单隐藏”这一用户可见主路径。
3. 将后端 clean-db 全量回归命令沉淀到 CI 或开发手册，避免并发本地 `pytest` 造成测试库竞争。
4. 若后续继续扩展 `ActivityTimeline`，优先保持 `common.*` 命名空间一致，避免再次出现跨模块 i18n key 漂移。
