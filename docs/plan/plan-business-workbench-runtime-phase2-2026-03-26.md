# 统一业务工作台运行时增强实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `business_workbench_runtime_phase2`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `先冻结 runtime 协议，再抽公共组件，最后扩到业务样板对象`

## 2. 现状判断

当前代码已经具备工作台基础，但仍停留在“单对象专项增强”阶段，还没有升级为跨业务域可复制的通用闭环能力。

现状依据:

1. 后端 runtime 已能输出 `workspace_mode`、`toolbar`、`detail_panels`、`async_indicators`:
   - `backend/apps/system/viewsets/object_router_runtime_actions.py`
2. 前端动态详情页已经具备工作台动作栏和面板宿主:
   - `frontend/src/views/dynamic/DynamicDetailPage.vue`
   - `frontend/src/components/common/ObjectWorkbenchActionBar.vue`
   - `frontend/src/components/common/ObjectWorkbenchPanelHost.vue`
   - `frontend/src/composables/useObjectWorkbench.ts`
3. 当前真正成熟的工作台样板主要是 `AssetProject`，其它对象尚未形成通用协议复用:
   - `backend/apps/system/menu_config.py`
   - `backend/apps/system/tests/test_asset_project_catalog.py`

结论:

1. 现有能力足以作为 Phase 2 起点。
2. 关键缺口不是“有没有 workbench”，而是缺少统一的摘要卡、队列、闭环、SLA、推荐动作协议。

## 3. 实施原则

1. 继续坚持 `/api/system/objects/{code}/` 统一对象入口，不新增新一套业务专页 API 体系。
2. 先抽象工作台通用协议，再扩具体业务对象，避免重复做对象专属壳。
3. 动作、队列、闭环、SLA 必须由后端提供结构化 payload，前端不自行推导业务含义。
4. `AssetProject` 作为回归样板，`FinanceVoucher` 与 `InventoryTask` 作为首批复制对象。
5. 所有新增用户文案从一开始支持 `zh-CN` 与 `en-US`。

## 4. 分阶段执行

## Phase 0: 协议冻结

### 目标

把“工作台到底包含哪些通用能力”一次冻结，避免后续每个业务域自行加字段。

### 任务

1. 冻结 `RuntimeWorkbench` 协议:
   - `workspaceMode`
   - `primaryEntryRoute`
   - `legacyAliases`
   - `toolbar.primaryActions`
   - `toolbar.secondaryActions`
   - `detailPanels`
   - `asyncIndicators`
   - `summaryCards`
   - `queuePanels`
   - `exceptionPanels`
   - `closurePanel`
   - `slaIndicators`
   - `recommendedActions`
2. 冻结队列语义:
   - `pending`
   - `review`
   - `exception`
   - `approaching_sla`
   - `overdue`
   - `awaiting_closure`
3. 冻结对象闭环摘要语义:
   - 当前阶段
   - 阻塞原因
   - 当前责任人
   - 下一步推荐动作
   - 结案条件完成度
4. 冻结 camelCase 与 snake_case 映射规则，避免再次出现前后端命名双轨。

### 交付物

1. runtime 协议冻结清单
2. 队列与闭环字段定义
3. 首批样板对象映射清单

### 验收

1. 工作台通用字段集合冻结，后续对象不再新增私有 payload 主字段。
2. 前后端 types 与接口字段命名保持一致。

建议工期: `1-2 人天`

---

## Phase 1: 后端运行时与查询接口增强

### 目标

把“摘要卡、队列、闭环、SLA、推荐动作”正式纳入对象 runtime 和对象扩展接口。

### 任务

1. 扩展 runtime 组装:
   - `backend/apps/system/viewsets/object_router_runtime_actions.py`
   - `backend/apps/system/services/layout_runtime_normalizer.py`
2. 新增工作台聚合服务:
   - `backend/apps/system/services/object_workbench_runtime_service.py`
   - `backend/apps/system/services/object_workbench_queue_service.py`
   - `backend/apps/system/services/object_closure_summary_service.py`
3. 在对象路由扩展接口:
   - `GET /api/system/objects/{code}/workbench/summary/`
   - `GET /api/system/objects/{code}/workbench/queues/{queue_code}/`
   - `GET /api/system/objects/{code}/{id}/closure/`
4. 保持对象动作仍通过:
   - `GET /api/system/objects/{code}/{id}/actions/`
   - `POST /api/system/objects/{code}/{id}/actions/{action_code}/execute/`
5. 抽离工作台 payload builder，避免继续在 `menu_config` 或页面里堆对象专属判断。

### 涉及模块

1. `backend/apps/system/viewsets/object_router.py`
2. `backend/apps/system/viewsets/object_router_runtime_actions.py`
3. `backend/apps/system/services/`
4. `backend/apps/system/menu_config.py`

### 交付物

1. 统一工作台聚合服务
2. 对象工作台摘要与队列接口
3. 对象闭环摘要接口
4. Runtime payload 扩展

### 验收

1. 任意支持工作台的对象都能通过统一 runtime 获得完整工作台协议。
2. 队列和摘要不依赖前端硬编码拼装。
3. 现有 `AssetProject` workbench 行为回归通过。

建议工期: `3-4 人天`

---

## Phase 2: 前端公共组件与动态详情页接入

### 目标

把工作台通用能力收口到公共组件层，而不是继续扩散在对象详情页里。

### 任务

1. 扩展前端 runtime 类型:
   - `frontend/src/api/dynamic.ts`
   - `frontend/src/types/` 如需拆分独立类型
2. 新增公共组件:
   - `frontend/src/components/common/WorkbenchSummaryCards.vue`
   - `frontend/src/components/common/WorkbenchQueuePanel.vue`
   - `frontend/src/components/common/ClosureStatusPanel.vue`
   - `frontend/src/components/common/RecommendedActionPanel.vue`
3. 扩展现有组件:
   - `frontend/src/components/common/ObjectWorkbenchPanelHost.vue`
   - `frontend/src/components/common/ObjectWorkbenchActionBar.vue`
   - `frontend/src/composables/useObjectWorkbench.ts`
4. 在动态详情页接入:
   - `frontend/src/views/dynamic/DynamicDetailPage.vue`
5. 在动态工作区模型层接入摘要和空态文案:
   - `frontend/src/views/dynamic/workspace/`

### 交付物

1. 通用工作台摘要组件
2. 通用队列面板组件
3. 通用闭环摘要组件
4. 推荐动作面板
5. 动态详情页统一接入

### 验收

1. 对象详情页能统一展示摘要卡、闭环状态和推荐动作。
2. 面板渲染基于 runtime 配置，不新增对象专属 shell。
3. 对象工作台新增字段不会要求页面重写结构。

建议工期: `4-5 人天`

---

## Phase 3: 样板对象落地

### 目标

用 2 个非 `AssetProject` 对象证明该协议可复制。

### 首批对象

1. `FinanceVoucher`
2. `InventoryTask`

### 任务

1. 为 `FinanceVoucher` 增加:
   - 摘要卡
   - 异常推送队列
   - 闭环状态面板
   - 推荐动作
2. 为 `InventoryTask` 增加:
   - 任务进度摘要
   - 差异待处理队列
   - 结案前置条件
   - 推荐动作
3. 将现有 `AssetProject` 作为回归样板，验证兼容性。

### 交付物

1. `FinanceVoucher` 工作台增强
2. `InventoryTask` 工作台增强
3. `AssetProject` 回归修正

### 验收

1. 至少 3 个对象共享同一套工作台通用协议。
2. 新对象接入时只需要配置 runtime 和服务，不需要复制页面壳。

建议工期: `3-4 人天`

---

## Phase 4: 自动化测试与迁移收口

### 目标

用测试和迁移把协议真正固定下来。

### 任务

1. 后端测试:
   - runtime payload 测试
   - 队列接口测试
   - 闭环摘要接口测试
2. 前端测试:
   - `ObjectWorkbenchPanelHost`
   - `ObjectWorkbenchActionBar`
   - 新增工作台公共组件
   - `DynamicDetailPage` workbench 渲染
3. 迁移与种子:
   - 首批对象 `menu_config.workbench` 配置补齐

### 验收

1. runtime 协议测试覆盖主要字段。
2. 首批样板对象工作台渲染稳定通过。
3. 迁移后环境可重复构建工作台配置。

建议工期: `2-3 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/system/viewsets/object_router_runtime_actions.py`
2. `backend/apps/system/viewsets/object_router.py`
3. `backend/apps/system/services/layout_runtime_normalizer.py`
4. `backend/apps/system/services/`
   - 新增工作台 runtime/queue/closure 聚合服务
5. `backend/apps/system/menu_config.py`
6. `backend/apps/system/migrations/`
   - 新增首批对象 workbench 配置迁移

### 前端

1. `frontend/src/api/dynamic.ts`
2. `frontend/src/views/dynamic/DynamicDetailPage.vue`
3. `frontend/src/components/common/ObjectWorkbenchPanelHost.vue`
4. `frontend/src/components/common/ObjectWorkbenchActionBar.vue`
5. `frontend/src/composables/useObjectWorkbench.ts`
6. `frontend/src/components/common/`
   - 新增 `WorkbenchSummaryCards.vue`
   - 新增 `WorkbenchQueuePanel.vue`
   - 新增 `ClosureStatusPanel.vue`
   - 新增 `RecommendedActionPanel.vue`

## 6. 测试计划

### 6.1 后端

1. `runtime` 返回新增工作台字段
2. `workbench/summary` 接口正常返回摘要
3. `workbench/queues/{queue_code}` 支持筛选
4. `closure` 接口返回完整闭环摘要

### 6.2 前端

1. 摘要卡渲染
2. 队列面板加载与空态
3. 闭环状态面板渲染
4. 推荐动作面板与动作栏协同
5. 动态详情页在有无 workbench 配置下的兼容行为

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 继续堆对象专属 workbench 分支 | 各业务域可能各自补逻辑 | 强制通过 runtime builder 和公共组件承载共性 |
| 协议字段膨胀 | 新对象继续自行加字段 | Phase 0 冻结字段并建立测试 |
| 页面仍自行推导业务状态 | 前端写死业务语义 | 后端统一输出闭环与队列 payload |
| i18n 漏补 | 新组件直接写死文案 | 所有新组件首批同步 `zh-CN/en-US` |

## 8. 完成标准

1. 平台存在统一的工作台 runtime 协议，而不是只有 `AssetProject` 特例。
2. `FinanceVoucher` 与 `InventoryTask` 接入统一工作台，不再依赖专属页面壳。
3. 摘要、队列、闭环、推荐动作都能通过统一对象入口获得。
