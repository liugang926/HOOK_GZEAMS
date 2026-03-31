# Sprint 5 实施计划 — InventoryTask 闭环工作台试点

> **Version**: v2.0  
> **Date**: 2026-03-31  
> **PRD**: `docs/prd/prd-sprint5-first-closed-loop-and-production-readiness-2026-03-30.md`  
> **Primary Goal**: 在统一动态详情页上，为 `InventoryTask` 补齐首批真正可运营的 workbench / closure / SLA 能力

---

## 1. 本期范围重定义

### 1.1 已完成基线，不再重复立项

| 项 | 当前状态 |
|----|---------|
| `AssetPickup` + `WorkflowStatusMixin` | 已完成 |
| 开发 Docker Gunicorn | 已完成 |
| DRF throttle | 已完成 |
| Dashboard summary API | 已完成 |
| Dashboard 增强页面 | 已完成 |

### 1.2 本期真正要做的事

| # | 任务 | 优先级 | 目标 |
|---|------|:------:|------|
| 1 | 修订 Sprint 5 文档基线 | P0 | 让计划与当前仓库真实状态一致 |
| 2 | 为 `InventoryTask` workbench 增加 detail panel 配置 | P0 | 让详情页有执行层面板入口 |
| 3 | 为 `InventoryTask` workbench 增加 SLA indicator 配置 | P0 | 把对象级 workflow SLA 直接暴露到详情页 |
| 4 | 新增执行人进度 workbench 面板组件 | P0 | 展示执行人负载和盘点进度 |
| 5 | 补前后端测试 | P0 | 锁住 runtime 配置和前端渲染行为 |

---

## 2. 设计约束

1. 不新增 `InventoryTask` 独立静态详情页。
2. 不新增散落的后端顶层 URL。
3. 优先复用现有接口与 runtime workbench 机制。
4. 不把 TypeScript 全量清零作为本期 gate。

---

## 3. 任务拆解

## 3.1 任务一：修订 Sprint 5 文档基线

**目标**  
将 Sprint 5 文档从“重复规划已完成项”改为“InventoryTask workbench 试点”。

**涉及文件**

| 文件 | 操作 |
|------|------|
| `docs/prd/prd-sprint5-first-closed-loop-and-production-readiness-2026-03-30.md` | 重写 |
| `docs/plans/sprint-5-implementation-plan.md` | 重写 |

**完成标准**

1. 文档不再把 Gunicorn、Dashboard、Throttle、`AssetPickup` workflow 集成列为待实施项。
2. 文档主目标与 roadmap 的 `workbench / closure / SLA` 方向一致。

---

## 3.2 任务二：补齐 `InventoryTask` workbench runtime 配置

**目标**  
为 `InventoryTask` 的 runtime workbench 增加：

| 配置项 | 说明 |
|------|------|
| `detail_panels` | 新增执行人进度面板定义 |
| `sla_indicators` | 新增 workflow SLA 指示器定义 |

**涉及文件**

| 文件 | 操作 |
|------|------|
| `backend/apps/system/menu_config.py` | 修改 `INVENTORY_TASK_WORKBENCH` |
| `backend/apps/system/tests/test_menu_config_sync.py` | 增加断言 |

**完成标准**

1. `InventoryTask` menu config 含 `inventory-task-executor-progress` 面板组件。
2. `InventoryTask` menu config 含至少一个 SLA indicator。

---

## 3.3 任务三：新增执行人进度面板组件

**目标**  
在统一详情页的 workbench panel 区域内展示执行人进度，不跳出当前详情页。

**组件职责**

| 能力 | 说明 |
|------|------|
| 数据加载 | 并行读取 executors 和 executor progress |
| 汇总指标 | 展示执行人数、分配资产数、累计扫描数、累计异常数 |
| 卡片列表 | 每位执行人显示 progress card |
| 刷新 | 支持局部刷新 |
| 空态/错误态 | 显示内联空态或告警，不触发全局弹窗 |

**涉及文件**

| 文件 | 操作 |
|------|------|
| `frontend/src/components/inventory/InventoryTaskExecutorProgressPanel.vue` | 新增 |
| `frontend/src/components/common/ObjectWorkbenchPanelHost.vue` | 注册面板组件 |
| `frontend/src/locales/en-US/inventory.json` | 新增面板文案 |
| `frontend/src/locales/zh-CN/inventory.json` | 新增面板文案 |

---

## 3.4 任务四：补前端测试

**目标**  
锁定面板渲染和刷新行为。

**涉及文件**

| 文件 | 操作 |
|------|------|
| `frontend/src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts` | 增加 InventoryTask 面板挂载断言 |
| `frontend/src/components/inventory/__tests__/InventoryTaskExecutorProgressPanel.spec.ts` | 新增组件测试 |

**测试点**

1. 面板首次挂载时加载数据。
2. 面板能合并 assignment 与 progress 数据。
3. `panelRefreshVersion` 变化后会重新加载。
4. 空数据时显示空态。

---

## 4. 实施顺序

| 顺序 | 动作 | 依赖 |
|------|------|------|
| 1 | 修文档 | 无 |
| 2 | 改 `menu_config` 和后端断言 | 1 |
| 3 | 新增前端面板并接入 panel host | 2 |
| 4 | 补前端测试 | 3 |
| 5 | 运行验证 | 4 |

---

## 5. 目标变更清单

### 5.1 后端

| 文件 | 变更 |
|------|------|
| `backend/apps/system/menu_config.py` | `InventoryTask` workbench 加 detail panel 和 SLA indicator |
| `backend/apps/system/tests/test_menu_config_sync.py` | 新增 InventoryTask workbench 断言 |

### 5.2 前端

| 文件 | 变更 |
|------|------|
| `frontend/src/components/inventory/InventoryTaskExecutorProgressPanel.vue` | 新增组件 |
| `frontend/src/components/common/ObjectWorkbenchPanelHost.vue` | 注册新组件 |
| `frontend/src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts` | 更新测试 |
| `frontend/src/components/inventory/__tests__/InventoryTaskExecutorProgressPanel.spec.ts` | 新增测试 |
| `frontend/src/locales/en-US/inventory.json` | 新增面板文案 |
| `frontend/src/locales/zh-CN/inventory.json` | 新增面板文案 |

### 5.3 文档

| 文件 | 变更 |
|------|------|
| `docs/prd/prd-sprint5-first-closed-loop-and-production-readiness-2026-03-30.md` | 重写 |
| `docs/plans/sprint-5-implementation-plan.md` | 重写 |

---

## 6. 验证计划

### 6.1 后端

```bash
docker compose exec backend pytest apps/system/tests/test_menu_config_sync.py -q
```

### 6.2 前端

```bash
npm test -- --run \
  src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts \
  src/components/inventory/__tests__/InventoryTaskExecutorProgressPanel.spec.ts
```

### 6.3 补充检查

```bash
npx eslint \
  src/components/inventory/InventoryTaskExecutorProgressPanel.vue \
  src/components/common/ObjectWorkbenchPanelHost.vue \
  src/components/inventory/__tests__/InventoryTaskExecutorProgressPanel.spec.ts \
  src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts \
  --ext .ts,.vue --ignore-path .gitignore
```

---

## 7. 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| `InventoryTask` 当前并非所有场景都绑定 workflow | SLA 面板可能为空 | 用可选显示策略处理，无实例时不报错 |
| executors 与 progress 数据口径存在差异 | 面板数据可能不完整 | 前端统一 merge，并以前端 progress 数据优先 |
| 新增面板导致详情页信息过多 | 影响阅读密度 | 保持为独立 panel，延续现有懒加载机制 |

---

## 8. 本期完成定义

1. Sprint 5 文档已与真实仓库状态对齐。
2. `InventoryTask` 详情页 workbench 出现执行人进度面板。
3. `InventoryTask` 详情页在存在流程实例时可显示 SLA。
4. 目标测试集通过。
