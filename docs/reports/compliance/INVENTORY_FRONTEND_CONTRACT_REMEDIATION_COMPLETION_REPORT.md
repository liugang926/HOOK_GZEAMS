# Inventory Frontend Contract Remediation Completion Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v2.12 |
| 创建日期 | 2026-03-30 |
| 涉及阶段 | Phase 4 Inventory Stabilization |
| 作者/Agent | Codex |

## 一、实施概述
- 本次整改分两阶段完成。第一阶段先消除 assignment 404 与进度接口契约错误；第二阶段补齐 `InventoryReconciliation` 与 `InventoryReport` 两个真实动态对象，恢复原有页面能力。
- 已完成的核心动作包括：assignment API 改为复用既有 `executors` 能力、为库存任务补充 executor 列表与进度接口、为 reconciliation/report 新增后端模型/迁移/对象注册/ViewSet 动作，并将前端重新接回 `/api/system/objects/{code}/` 动态对象路由。
- 已将 inventory reconciliation/report 的前后端契约回归命令接入 `.github/workflows/ci.yml`，作为 full pytest / full vitest 之前的 fail-fast gate。
- 在接入 pytest 型 CI gate 的过程中，修复了 reconciliation/report create serializer 在类定义期绑定 tenant-aware queryset 的问题，避免多组织上下文被首次导入时错误缓存。
- 已为 inventory contract gate 增加独立 JUnit、独立 artifact 和独立 GitHub step summary，并修复 `render_junit_summary.py` 对多 `testsuite` JUnit 的统计偏差。
- backend inventory gate 已进一步收窄到专用 smoke 节点 `test_inventory_contract_list_endpoints`，避免为库存契约回归额外执行整组 legacy module list smoke。
- inventory contract gate 已进一步提升为独立 CI job：PR checks 中会直接显示 `Backend - Inventory Contract Gate` 与 `Frontend - Inventory Contract Gate`。
- `CI Status Check` 现已显式汇总 backend/frontend inventory contract gate，分支保护最终汇总不再只显示大套件结果。
- `render_gate_summary.py` 已支持按 section 分组展示 gate；`CI Status Check` 现按 backend contract / frontend contract / full suites and quality gates 分层输出。
- `backend-demo-data` 已从 contract gate 分组中拆出，`CI Status Check` 现单独显示 `Bootstrap Gates`，避免环境引导校验与对象契约回归混淆。
- `security-scan` 已从功能回归套件分组中拆出，`CI Status Check` 现单独显示 `Security Advisory Gates`，避免安全扫描与功能测试混排。
- `render_gate_summary.py` 已增加 `Blocking Scope` 列，`required / advisory / report-only` 语义现直接以可读标签展示，不再要求 reviewer 记忆 mode 约定。
- `render_gate_summary.py` 已增加可选 `Job Policy` 字段，`CI Status Check` 现显式展示 job 级策略；`security-scan` 会显示为“Required job (advisory findings inside)”。
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
| CI summary / artifact 可观测性 | 通过 | inventory contract gate 现已产出独立 JUnit、artifact 和正确聚合的 step summary |
| CI fail-fast 执行范围收敛 | 通过 | backend inventory gate 现仅执行库存对象主用例与定向 smoke 节点 |
| CI 检查项可辨识性 | 通过 | inventory contract gate 已拆分为独立 workflow job，PR 页面可直接识别 |
| CI 最终汇总可追踪性 | 通过 | `CI Status Check` 已显式列出 backend/frontend inventory contract gate 结果 |
| CI 最终汇总分层可读性 | 通过 | `CI Status Check` 已按 contract gates 与 full suites 分组展示 |
| CI bootstrap 语义清晰度 | 通过 | `backend-demo-data` 已单列为 `Bootstrap Gates`，不再与 contract gate 混用 |
| CI 安全扫描语义清晰度 | 通过 | `security-scan` 已单列为 `Security Advisory Gates`，不再与功能回归套件混排 |
| CI blocking 语义显式化 | 通过 | summary 表格已新增 `Blocking Scope` 列，`required / advisory / report-only` 可直接读懂 |
| CI job 策略可见性 | 通过 | summary 表格已新增 `Job Policy` 列，job 级 required / advisory 语义可直接识别 |

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
- `.github/scripts/render_junit_summary.py`
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
- `docker compose exec backend sh -lc 'cd /app && pytest apps/inventory/tests/test_api.py::InventoryReconciliationReportObjectRouteTests apps/system/tests/test_object_router_legacy_module_smoke.py::test_inventory_contract_list_endpoints -q --junitxml=inventory-contract-gate-junit.xml'`
  结果：通过；共 3 条定向后端 gate 用例
- `npm test -- --run src/router/index.spec.ts src/__tests__/unit/api/inventory-contract-adapters.spec.ts`
  结果：通过
- `python3 .github/scripts/render_junit_summary.py --summary-path /tmp/frontend_inventory_gate_summary.md --title "Frontend Inventory Contract Gate" --command-label "Gate command" --command "npm test -- --run src/router/index.spec.ts src/__tests__/unit/api/inventory-contract-adapters.spec.ts --reporter=default --reporter=junit --outputFile.junit=coverage/inventory-contract-vitest-junit.xml" --artifact "frontend-inventory-contract-results" --junit-path frontend/coverage/inventory-contract-vitest-junit.xml --include-classname`
  结果：通过；已确认多 `testsuite` JUnit 聚合结果为 11 条用例
- `python3 .github/scripts/render_gate_summary.py --summary-path /tmp/ci_status_grouped_summary.md --title "CI Status Check" --group-label "Gate group" --group "required branch protection checks" --check "backend-demo-data|success|required|Demo data smoke gate and artifact bundle|Backend Contract Gates" --check "backend-inventory-contract|success|required|Focused object contract gate for InventoryReconciliation and InventoryReport|Backend Contract Gates" --check "frontend-inventory-contract|success|required|Focused route and adapter contract gate for inventory reconciliation and report flows|Frontend Contract Gates" --check "backend-lint|success|required|Python linting and Django system checks|Full Suites and Quality Gates"`
- `python3 .github/scripts/render_gate_summary.py --summary-path /tmp/ci_status_grouped_summary.md --title "CI Status Check" --group-label "Gate group" --group "required branch protection checks" --check "backend-demo-data|success|required|Demo data smoke gate and artifact bundle|Bootstrap Gates" --check "backend-inventory-contract|success|required|Focused object contract gate for InventoryReconciliation and InventoryReport|Backend Contract Gates" --check "frontend-inventory-contract|success|required|Focused route and adapter contract gate for inventory reconciliation and report flows|Frontend Contract Gates" --check "backend-lint|success|required|Python linting and Django system checks|Full Suites and Quality Gates" --check "security-scan|success|required|Job completion gate; dependency findings remain advisory inside the job|Security Advisory Gates"`
  结果：通过；已确认 summary 分组标题和表格结构正确输出
- `python3 .github/scripts/render_gate_summary.py --summary-path /tmp/gate_summary_scope_matrix.md --title "Scope Matrix" --group-label "Gate group" --group "mode semantics" --check "required-check|success|required|blocking gate" --check "advisory-check|success|advisory|non-blocking advisory" --check "report-only-check|success|report-only|telemetry baseline"`
  结果：通过；已确认 `Blocking Scope` 列分别显示 `Blocking`、`Advisory only`、`Report only`
- `python3 .github/scripts/render_gate_summary.py --summary-path /tmp/gate_summary_legacy.md --title "Legacy Summary" --group-label "Gate group" --group "legacy compatibility" --check "eslint|success|required|eslint --max-warnings 0"`
  结果：通过；已确认旧 4 段 `--check` 输入仍兼容
- `python3 .github/scripts/render_gate_summary.py --summary-path /tmp/gate_summary_policy_matrix.md --title "Policy Matrix" --group-label "Gate group" --group "job policy semantics" --check "required-job|success|required|blocking gate|Core Gates|Required job" --check "security-job|success|required|advisory findings stay inside the job|Security Advisory Gates|Required job (advisory findings inside)"`
  结果：通过；已确认 `Job Policy` 列显示显式策略文本

## 六、后续建议
- 若要真正恢复“区域 / 位置范围分配”，应新增独立 assignment 资源，而不是继续在 `executors` 上叠加范围语义。
- reconciliation/report 当前已具备最小可用闭环，但审批链、模板中心和报表内容格式仍是轻量实现，后续应按正式业务 PRD 继续细化。
- 已为 `frontend/src/api/inventory.ts` 新增 reconciliation/report 契约级单测，并已将前后端 inventory contract 回归命令接入独立 CI job，且补齐独立 JUnit / artifact / summary；backend gate 现已收敛到库存专用 smoke 节点，后续可继续考虑把 object export 等重路径拆成更轻量的纯 contract 检查。
- inventory contract gate 现已进入最终 `CI Status Check` 汇总；后续若继续增强，可考虑把更多对象级 contract gate 复用同一汇总模式，而不是继续堆叠单独的 branch protection 总检查项。
- `render_gate_summary.py` 的 section 分组能力现已可复用；后续若新增对象级 contract gate，优先沿用同一 summary 模式，不再为可读性单独扩写 shell 模板。
- `Bootstrap Gates` / `Contract Gates` / `Full Suites` 的语义边界已初步明确；后续若继续扩展，可将 `security-scan` 进一步独立成 `Security Advisory Gates`，避免与功能回归套件混排。
- `Job Policy` 已落地；后续若继续扩展，可考虑把 step 级 `continue-on-error` 或 artifact 可用性也映射进 summary，但应优先复用现有列而不是继续横向扩表。
