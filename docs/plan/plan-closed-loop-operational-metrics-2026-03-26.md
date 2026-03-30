# 闭环经营指标与管理驾驶舱实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `closed_loop_operational_metrics`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `先统一指标口径和事件语义，再做适配层聚合，最后输出驾驶舱和治理报表`

## 2. 现状判断

当前项目已经在多个业务域各自实现了 summary/dashboard，但这些能力是分散的，尚未形成统一的经营指标体系。

现状依据:

1. 项目域已有成熟 workspace dashboard:
   - `backend/apps/projects/services.py`
   - `backend/apps/projects/viewsets.py`
2. 财务已有 summary:
   - `backend/apps/finance/viewsets/__init__.py`
3. 保险已有 dashboard stats 与 policy summary:
   - `backend/apps/insurance/viewsets.py`
4. 盘点已有 snapshot/scan/difference summary:
   - `backend/apps/inventory/viewsets/task_viewsets.py`
   - `backend/apps/inventory/viewsets/difference_viewsets.py`
5. 租赁已有逾期和到期查询能力:
   - `backend/apps/leasing/viewsets.py`
6. 工作流已有 SLA 与瓶颈分析:
   - `backend/apps/workflows/services/sla_service.py`
7. 前端已有报表中心入口:
   - `frontend/src/router/index.ts`

结论:

1. 当前不是没有统计，而是统计入口、口径、时间窗口和业务语义都不统一。
2. 真正的驾驶舱建设前提，是把“开单、阻塞、超时、结案”事件先标准化。

## 3. 实施原则

1. 指标优先建立在标准化业务事件和闭环阶段之上，而不是直接拼各域计数字段。
2. 第一阶段不做重数据平台，优先做服务层适配与聚合。
3. 指标必须支持对象、组织、责任人、时间窗口 4 个基础维度。
4. 指标不仅用于展示，还要能反向驱动例外队列和瓶颈治理。
5. 驾驶舱与工作台的职责要分开:
   - 工作台负责处理
   - 驾驶舱负责监控与分析

## 4. 分阶段执行

## Phase 0: 指标口径冻结

### 目标

统一闭环经营指标的基础事件、时间点和维度。

### 任务

1. 冻结标准业务事件:
   - `opened`
   - `assigned`
   - `entered_review`
   - `approved`
   - `overdue`
   - `escalated`
   - `resolved`
   - `closed`
   - `archived`
2. 冻结核心指标:
   - 闭环时长
   - 超时率
   - 异常结案率
   - 自动闭环率
   - 待处理积压量
   - 瓶颈节点排行
3. 冻结分析维度:
   - 业务对象
   - 组织
   - 责任人
   - 时间窗口
4. 冻结管理报表时间窗口:
   - `7d`
   - `30d`
   - `90d`

### 验收

1. 各业务域使用统一的指标名和时间定义。
2. 驾驶舱不会因为域差异导致口径失真。

建议工期: `1-2 人天`

---

## Phase 1: 指标适配层建设

### 目标

把现有各域 summary/dashboard 通过适配层统一输出。

### 任务

1. 新增指标适配服务:
   - `backend/apps/system/services/closed_loop_metrics_service.py`
   - `backend/apps/system/services/metrics_adapters/`
2. 首批适配对象:
   - `AssetProject`
   - `InventoryTask`
   - `FinanceVoucher`
   - `InsurancePolicy`
   - `ClaimRecord`
   - `LeasingContract`
3. 复用现有域能力:
   - 项目 workspace dashboard
   - 盘点 summary
   - 财务 summary
   - 保险 dashboard stats
   - SLA bottleneck report
4. 将分散统计转换为统一结构:
   - `summary`
   - `queues`
   - `trend`
   - `bottlenecks`

### 验收

1. 至少 4 个业务域可以通过统一指标服务输出 summary。
2. 指标适配不要求业务域立即重写原统计接口。

建议工期: `3-4 人天`

---

## Phase 2: 管理驾驶舱接口与视图模型

### 目标

输出真正可用于管理层查看的闭环驾驶舱数据结构。

### 任务

1. 新增驾驶舱接口:
   - `GET /api/system/metrics/closed-loop/overview/`
   - `GET /api/system/metrics/closed-loop/by-object/`
   - `GET /api/system/metrics/closed-loop/bottlenecks/`
   - `GET /api/system/metrics/closed-loop/queues/`
2. 输出视图模型:
   - 汇总卡
   - 趋势图
   - 异常堆积排行
   - 责任人排行
   - 节点瓶颈排行
3. 接入工作流 SLA 数据和对象闭环数据。
4. 支持按组织和窗口切换。

### 验收

1. 驾驶舱接口可以独立为前端提供完整视图模型。
2. 队列、趋势和瓶颈不再需要前端多接口拼装。

建议工期: `3-4 人天`

---

## Phase 3: 前端驾驶舱与报表中心接入

### 目标

在现有报表中心或管理页中提供统一的闭环经营驾驶舱。

### 任务

1. 新增管理驾驶舱页面或模块:
   - 可接入 `reports/center`
2. 统一组件:
   - 摘要卡
   - 趋势图
   - 队列排行
   - 瓶颈排行
3. 支持 drill-down:
   - 从指标卡进入对象工作台队列
4. 保证中英文文案齐全。

### 涉及模块

1. `frontend/src/views/reports/ReportCenter.vue`
2. 新增闭环经营驾驶舱视图
3. 相关图表与表格组件

### 验收

1. 管理层可查看统一闭环指标，而不是分别打开财务、保险、盘点等 dashboard。
2. 指标可以直接跳转到待处理对象队列。

建议工期: `4-5 人天`

---

## Phase 4: 指标治理与数据质量守护

### 目标

保证指标长期可靠，不因业务域扩展而漂移。

### 任务

1. 为关键指标建立 contract tests。
2. 为各域适配器建立口径校验测试。
3. 建立指标变更说明与 PRD 对应关系。
4. 为新增业务域定义接入模板:
   - 标准事件
   - 标准 summary
   - 标准 queue

### 验收

1. 新业务域接入驾驶舱时有统一模板。
2. 指标改动能通过测试发现回归。

建议工期: `2-3 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/system/services/`
   - 新增 `closed_loop_metrics_service.py`
   - 新增 `metrics_adapters/`
2. `backend/apps/projects/services.py`
3. `backend/apps/finance/viewsets/__init__.py`
4. `backend/apps/insurance/viewsets.py`
5. `backend/apps/inventory/viewsets/task_viewsets.py`
6. `backend/apps/leasing/viewsets.py`
7. `backend/apps/workflows/services/sla_service.py`

### 前端

1. `frontend/src/views/reports/ReportCenter.vue`
2. 新增闭环经营驾驶舱页
3. 驾驶舱图表与队列组件
4. 与对象工作台队列的跳转联动

## 6. 测试计划

### 6.1 后端

1. 指标聚合 contract tests
2. 各域适配器口径测试
3. SLA 与闭环指标融合测试

### 6.2 前端

1. 汇总卡和趋势图渲染
2. 组织和时间窗口切换
3. drill-down 到对象队列的交互

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 过早做大而全驾驶舱 | 口径不稳，指标失真 | 先做指标口径冻结和适配层 |
| 继续拼接旧 dashboard | 前端逻辑越来越重 | 驾驶舱接口直接输出视图模型 |
| 各域状态不统一 | 统计不可横向比较 | 依赖前序闭环计划统一阶段语义 |
| 指标只能看不能处理 | 缺少业务价值 | 所有关键指标支持 drill-down 到队列 |

## 8. 完成标准

1. 项目形成统一的闭环经营指标体系，而不是多个域各自统计。
2. 管理驾驶舱能查看闭环时长、超时率、异常结案率和瓶颈排行。
3. 指标可以直接联动到具体对象队列，支撑治理动作。
