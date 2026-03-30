# Inventory Frontend Contract Remediation Completion Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v2.2 |
| 创建日期 | 2026-03-30 |
| 涉及阶段 | Phase 4 Inventory Stabilization |
| 作者/Agent | Codex |

## 一、实施概述
- 本次整改分两阶段完成。第一阶段先消除 assignment 404 与进度接口契约错误；第二阶段补齐 `InventoryReconciliation` 与 `InventoryReport` 两个真实动态对象，恢复原有页面能力。
- 已完成的核心动作包括：assignment API 改为复用既有 `executors` 能力、为库存任务补充 executor 列表与进度接口、为 reconciliation/report 新增后端模型/迁移/对象注册/ViewSet 动作，并将前端重新接回 `/api/system/objects/{code}/` 动态对象路由。
- 已将 inventory reconciliation/report 的前后端契约回归命令接入 `.github/workflows/ci.yml`，作为 full pytest / full vitest 之前的 fail-fast gate。
- 由于当前工作区存在大量其他未提交修改，本报告继续以“整改范围与验证结果”为主，不对总代码增删行做强归因统计。

## 二、与 PRD / 缺陷对应关系
| PRD 要求 / 缺陷项 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 盘点任务分配页面不得调用不存在的 `/inventory/tasks/{id}/assignments/` 资源 | 已修复 | `frontend/src/api/inventory.ts` / `backend/apps/inventory/viewsets/task_viewsets.py` |
| 分配进度不得复用任务级 `/progress/` 汇总对象 | 已修复 | `backend/apps/inventory/services/inventory_service.py` / `backend/apps/inventory/viewsets/task_viewsets.py` |
| reconciliation 页面不得暴露到不存在的 `/inventory/reconciliations/` 资源 | 已修复（真实动态对象落地） | `backend/apps/inventory/models.py` / `backend/apps/inventory/viewsets/reconciliation_viewsets.py` / `frontend/src/api/inventory.ts` |
| report 页面不得暴露到不存在的 `/inventory/reports/` 资源 | 已修复（真实动态对象落地） | `backend/apps/inventory/models.py` / `backend/apps/inventory/viewsets/reconciliation_viewsets.py` / `frontend/src/api/inventory.ts` |
| reconciliation/report 页面入口恢复后不得再跳转到 `InventoryTask` 列表 | 已修复 | `frontend/src/router/index.ts` / `frontend/src/router/index.spec.ts` |
| 分配面板不得继续暗示区域/位置范围已落地 | 已修复 | `frontend/src/views/inventory/AssignmentPanel.vue` / `frontend/src/locales/*/inventory.json` |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|--------|------|------|
| 仅使用已实现后端资源 | 通过 | assignment 改走 `executors`；reconciliation/report 现已绑定真实动态对象资源 |
| English comments only | 通过 | 本次新增代码注释与 docstring 均为英文 |
| 报告存放目录规范 | 通过 | 本报告位于 `docs/reports/compliance/` |
| 路由可用性回归保护 | 通过 | 前端路由单测已从临时重定向断言更新为真实页面路由断言 |
| 后端接口回归保护 | 通过 | 已在 Docker backend 容器内执行 reconciliation/report 对象路由测试与对象路由 smoke 测试 |
| CI fail-fast 契约保护 | 通过 | 已在 `.github/workflows/ci.yml` 中新增 inventory contract regression gate |

## 四、创建 / 修改文件清单
- `backend/apps/inventory/serializers/task_serializers.py`
- `backend/apps/inventory/serializers/reconciliation_serializers.py`
- `backend/apps/inventory/services/inventory_service.py`
- `backend/apps/inventory/services/reconciliation_service.py`
- `backend/apps/inventory/services/scan_service.py`
- `backend/apps/inventory/viewsets/task_viewsets.py`
- `backend/apps/inventory/viewsets/reconciliation_viewsets.py`
- `backend/apps/inventory/migrations/0008_inventoryreconciliation_inventoryreport.py`
- `backend/apps/inventory/tests/test_api.py`
- `backend/apps/system/object_catalog.py`
- `backend/apps/system/menu_config.py`
- `backend/apps/system/management/commands/init_all_translations.py`
- `backend/apps/system/tests/test_object_router_legacy_module_smoke.py`
- `.github/workflows/ci.yml`
- `frontend/src/api/inventory.ts`
- `frontend/src/api/dynamic.ts`
- `frontend/src/views/inventory/AssignmentPanel.vue`
- `frontend/src/__tests__/unit/api/inventory-contract-adapters.spec.ts`
- `frontend/src/router/index.ts`
- `frontend/src/router/index.spec.ts`
- `frontend/src/locales/en-US/inventory.json`
- `frontend/src/locales/zh-CN/inventory.json`

## 五、验证记录
- `npm test -- --run src/router/index.spec.ts`
  结果：通过
- `npm test -- --run src/__tests__/unit/api/inventory-contract-adapters.spec.ts`
  结果：通过
- `npx eslint src/api/inventory.ts src/api/dynamic.ts src/router/index.ts src/router/index.spec.ts src/views/inventory/reconciliation/ReconciliationList.vue src/views/inventory/reconciliation/ReportList.vue src/__tests__/unit/api/inventory-contract-adapters.spec.ts --ext .ts,.vue --ignore-path .gitignore`
  结果：通过；存在 `frontend/src/api/dynamic.ts` 与 `frontend/src/api/inventory.ts` 的既有 `any` 警告，但无新增错误
- `python3 -m compileall backend/apps/inventory/services/reconciliation_service.py backend/apps/inventory/serializers/reconciliation_serializers.py backend/apps/inventory/viewsets/reconciliation_viewsets.py backend/apps/inventory/models.py`
  结果：通过
- `docker compose exec backend python manage.py test apps.inventory.tests.test_api.InventoryReconciliationReportObjectRouteTests --settings=config.settings.test`
  结果：通过
- `docker compose exec backend pytest apps/system/tests/test_object_router_legacy_module_smoke.py -q`
  结果：通过
- `npm test -- --run src/router/index.spec.ts src/__tests__/unit/api/inventory-contract-adapters.spec.ts`
  结果：通过

## 六、后续建议
- 若要真正恢复“区域 / 位置范围分配”，应新增独立 assignment 资源，而不是继续在 `executors` 上叠加范围语义。
- reconciliation/report 当前已具备最小可用闭环，但审批链、模板中心和报表内容格式仍是轻量实现，后续应按正式业务 PRD 继续细化。
- 已为 `frontend/src/api/inventory.ts` 新增 reconciliation/report 契约级单测，并已将前后端 inventory contract 回归命令接入 CI；后续可再为这些 gate 单独生成 JUnit 工件，进一步提升失败定位速度。
