# GZEAMS 业务闭环优化路线图 PRD

## 文档信息
| 字段 | 说明 |
|------|------|
| 功能名称 | 业务闭环优化路线图 |
| 功能代码 | `business_closed_loop_optimization_roadmap` |
| 文档版本 | 1.0.0 |
| 创建日期 | 2026-03-26 |
| 维护人 | Codex |
| 审核状态 | 草稿 |

## 1. 功能概述与业务场景

### 1.1 业务背景

GZEAMS 当前已经具备较成熟的平台底座，包括统一动态对象路由、元数据驱动页面、生命周期时间线、工作流 SLA、财务异步集成、盘点快照与差异识别等能力。当前主要问题不再是单点功能缺失，而是多个业务域尚未形成一致的闭环经营能力。

从当前代码状态看：

| 业务域 | 当前成熟能力 | 主要缺口 |
|------|------|------|
| `AssetProject` | 已具备工作台、统计汇总、关闭约束、专项菜单配置 | 可作为其他域的产品模板 |
| 生命周期 | 已具备时间线聚合、部分跨对象动作 | 下游联动覆盖仍不够完整 |
| 盘点 | 已具备任务、快照、差异生成 | 差异认责、审批、结案链条偏薄 |
| 财务 | 已具备凭证生命周期、ERP 异步推送与日志 | 缺少源单到结算到核销的统一闭环视图 |
| 保险 | 已具备保单、理赔、赔付、续保服务 | 更偏对象管理与统计，缺少异常处理工作台 |
| 租赁 | 已具备合同、支付、归还、延期服务 | 缺少逾期催收、结清归档、现场收口工作台 |
| 工作流 | 已具备 SLA、超时、升级、瓶颈统计 | 仍偏审批中心，未充分嵌入业务对象运营界面 |

### 1.2 现状依据

以下代码可作为本 PRD 的现状依据：

1. `AssetProject` 已形成工作台模板：
   - `backend/apps/projects/services.py`
   - `backend/apps/system/menu_config.py`
   - `frontend/src/views/dynamic/workspace/useDynamicDetailWorkspace.ts`
   - `frontend/src/views/dynamic/workspace/dynamicListWorkspaceModel.ts`
2. 生命周期已形成时间线与部分闭环动作：
   - `backend/apps/lifecycle/services/closed_loop_service.py`
   - `backend/apps/lifecycle/services/lifecycle_action_service.py`
3. 盘点已形成任务与差异识别，但差异闭环偏薄：
   - `backend/apps/inventory/services/inventory_service.py`
   - `backend/apps/inventory/services/difference_service.py`
4. 财务、保险、租赁已具备服务层，但前端仍偏 dashboard 或对象页：
   - `backend/apps/finance/services.py`
   - `backend/apps/finance/tasks.py`
   - `backend/apps/insurance/services.py`
   - `backend/apps/leasing/services.py`
   - `frontend/src/views/insurance/InsuranceDashboard.vue`
   - `frontend/src/views/leasing/LeasingDashboard.vue`
5. 工作流 SLA 已具备技术能力，但业务嵌入不够：
   - `backend/apps/workflows/services/sla_service.py`
   - `frontend/src/views/workflow/MyApprovals.vue`

### 1.3 目标

本路线图目标不是新增更多业务对象，而是把现有对象组装成真正可经营、可例外处理、可结案追踪的业务闭环系统。

本次路线图聚焦以下目标：

1. 将长链路业务对象从“通用列表/详情”升级为“工作台 + 队列 + 动作 + 结案”。
2. 将差异、逾期、失败、超时等例外统一纳入可追踪、可处理、可升级的闭环机制。
3. 将跨对象动作从少量节点扩展到完整资产全生命周期。
4. 将工作流 SLA 从审批中心能力升级为业务对象原生能力。
5. 建立统一的闭环指标体系，支持经营视角的持续优化。

### 1.4 本次实现范围

#### 1.4.1 路线图范围内

1. 工作台化产品方向定义。
2. 子 PRD 目录与优先级拆分。
3. 公共框架层改造范围定义。
4. 分阶段实施路线图与出口标准。

#### 1.4.2 不在本期范围内

1. 本文不直接落具体代码实现。
2. 本文不替代各子 PRD 的详细接口与字段级设计。
3. 本文不重新设计基础元数据引擎、组织隔离或基础工作流引擎。

## 2. 用户角色与权限

| 用户角色 | 使用场景 | 核心需求 |
|---------|---------|----------|
| 系统管理员 | 维护对象工作台、菜单、布局、动作配置 | 能配置工作台入口、面板、动作与指标 |
| 业务运营负责人 | 追踪待处理队列、超时、异常、闭环效率 | 能按域查看工作台和闭环经营指标 |
| 审批人/主管 | 审批差异、理赔、结算、归还、处置等事项 | 能在对象上下文中直接处理待办 |
| 执行人 | 盘点、维修、催收、理赔处理、归还验收 | 能快速看到自己待处理事项和下一步动作 |
| 财务人员 | 处理凭证、核销、过账、ERP 异常 | 能追踪源单与财务终态的一致性 |
| 资产管理员 | 处理资产状态、盘点差异、处置、维保 | 能基于异常和 SLA 管理资产全生命周期 |

### 2.1 权限矩阵

| 功能 | 系统管理员 | 业务运营负责人 | 审批人/主管 | 执行人 | 财务人员 | 资产管理员 |
|------|------------|----------------|-------------|--------|----------|------------|
| 查看工作台统计 | ✅ | ✅ | ✅ | 视授权 | ✅ | ✅ |
| 查看例外队列 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 执行对象动作 | ✅ | 视授权 | ✅ | ✅ | ✅ | ✅ |
| 查看 SLA/超时信息 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 配置工作台布局/动作 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 查看跨域经营指标 | ✅ | ✅ | 视授权 | ❌ | ✅ | ✅ |

## 3. 公共模型引用声明

### 3.1 公共模型引用

| 组件类型 | 基类/能力 | 引用路径 | 自动获得功能 |
|---------|-----------|---------|-------------|
| Model | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| Metadata Model | `GlobalMetadataManager` | `apps.common.managers.GlobalMetadataManager` | 元数据全局共享、仅过滤软删除 |
| Serializer | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields 序列化 |
| ViewSet | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤、删除状态过滤 |
| Service | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |
| Dynamic Object Router | `ObjectRouterViewSet` 扩展 | `apps.system.viewsets.object_router.ObjectRouterViewSet` | 统一对象入口、runtime、actions、history、related |

### 3.2 本路线图适用说明

1. 优先扩展现有对象和元数据，不轻易新增顶层对象。
2. 优先通过工作台 runtime、详情扩展面板、对象动作、统计面板实现业务闭环。
3. 只有在多个业务域存在共性时，才新增框架级通用模型或通用面板协议。

## 4. 数据模型设计

### 4.1 总体设计原则

1. 业务闭环优先通过现有对象编排完成，不为“展示工作台”单独复制业务表。
2. 各域工作台统一由元数据和 runtime 共同描述，避免前端重复硬编码。
3. 例外处理优先基于现有对象状态、动作、关联关系与历史信息实现。
4. 通用能力优先抽为平台层配置，域差异保留在各自 service 中。

### 4.2 闭环能力分层

| 能力层 | 说明 | 首批适用对象 |
|------|------|-------------|
| `workbench` | 业务工作台摘要、动作、面板、队列 | `AssetProject`、`InventoryTask`、`InsurancePolicy`、`ClaimRecord`、`LeasingContract`、`FinanceVoucher` |
| `exception_queue` | 差异、逾期、失败、超时、待结案队列 | `InventoryDifference`、`RentPayment`、`ClaimRecord`、`FinanceVoucher` |
| `closure` | 当前阶段、责任人、下一动作、结案条件 | 全部长链路对象 |
| `sla` | 时限、超时、升级、瓶颈、催办 | 工作流挂接对象 |
| `metrics` | 闭环时长、超时率、异常结案率、自动闭环率 | 各业务域工作台和管理报表 |

### 4.3 元数据扩展约定

建议在 `BusinessObject` runtime 组装层增加以下语义：

| 配置项 | 类型 | 说明 |
|------|------|------|
| `workspace_mode` | string | `standard` / `extended` |
| `workbench.summary_cards` | array | 工作台摘要卡定义 |
| `workbench.queue_panels` | array | 待处理队列定义 |
| `workbench.exception_panels` | array | 例外队列定义 |
| `workbench.closure_panel` | object | 结案条件与当前阶段定义 |
| `workbench.sla_indicators` | array | SLA 指标与状态徽标定义 |
| `workbench.recommended_actions` | array | 基于当前状态推荐的对象动作 |

### 4.4 各域子 PRD 的数据策略

| 子域 | 数据策略 |
|------|---------|
| 盘点差异闭环 | 复用 `InventoryTask` / `InventoryDifference`，扩展处置状态与责任链 |
| 生命周期动作扩展 | 复用 `PurchaseRequest` / `AssetReceipt` / `Asset` / `MaintenanceRecord` / `DisposalRequest` |
| 财务闭环 | 复用 `FinanceVoucher` 及源单对象，补统一闭环视图与动作协议 |
| 保险闭环 | 复用 `InsurancePolicy` / `ClaimRecord`，强化续保、赔付、结案 |
| 租赁闭环 | 复用 `LeasingContract` / `RentPayment` / `LeaseReturn`，强化催收、归还、结清 |
| SLA 嵌入 | 复用工作流实例、任务、SLA 服务，不新增业务对象 |

## 5. API 接口设计

### 5.1 统一原则

1. 所有业务对象主入口保持在 `/api/system/objects/{code}/`。
2. 工作台、队列、闭环摘要等能力优先通过对象 runtime 与详情扩展接口提供。
3. 对象动作继续走统一动作协议，避免散落专用页面接口。

### 5.2 建议新增的工作台接口族

#### 5.2.1 获取对象工作台运行时配置

```http
GET /api/system/objects/{code}/runtime/?mode=workbench
```

返回重点：

1. `workbench.summary_cards`
2. `workbench.queue_panels`
3. `workbench.exception_panels`
4. `workbench.closure_panel`
5. `workbench.sla_indicators`
6. `workbench.recommended_actions`

#### 5.2.2 获取工作台摘要

```http
GET /api/system/objects/{code}/workbench/summary/
```

用途：

1. 返回当前对象域的核心经营指标。
2. 用于工作台头部摘要卡和运营看板。

#### 5.2.3 获取工作台队列

```http
GET /api/system/objects/{code}/workbench/queues/{queue_code}/
```

用途：

1. 返回待处理、待审核、待结案、即将超时、已超时等对象列表。
2. 支持组织、责任人、时间范围筛选。

#### 5.2.4 获取对象闭环摘要

```http
GET /api/system/objects/{code}/{id}/closure/
```

返回重点：

1. 当前阶段
2. 阻塞原因
3. 当前责任人
4. 下一动作建议
5. 结案条件完成度

#### 5.2.5 获取对象 SLA 摘要

```http
GET /api/system/objects/{code}/{id}/sla/
```

返回重点：

1. 当前 SLA 状态
2. 剩余时限
3. 是否已升级
4. 催办建议

#### 5.2.6 执行例外处理动作

```http
POST /api/system/objects/{code}/{id}/actions/{action_code}/execute/
```

首批建议统一纳入的动作：

1. 差异认责
2. 提交复核
3. 发起调账/维修/报废/归还
4. 重试推送 ERP
5. 催办/升级
6. 标记结案

### 5.3 错误码

沿用平台统一错误码，并新增以下业务语义映射要求：

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 结案前置条件不满足 |
| `PERMISSION_DENIED` | 403 | 无权执行例外处理动作 |
| `NOT_FOUND` | 404 | 对象或队列不存在 |
| `CONFLICT` | 409 | 当前对象状态不允许执行该动作 |
| `SERVER_ERROR` | 500 | 工作台聚合或外部依赖执行失败 |

## 6. 前端组件设计

### 6.1 设计原则

1. 优先基于 `DynamicListPage`、`DynamicDetailPage` 和动态工作区能力扩展。
2. 尽量避免为每个业务域再新增一套完全独立页面。
3. 共性能力抽为公共组件，域差异通过 runtime 配置和 panel adapter 承载。

### 6.2 建议新增/强化的公共组件

| 组件 | 作用 | 复用范围 |
|------|------|---------|
| `WorkbenchSummaryCards` | 头部经营指标卡 | 全域工作台 |
| `WorkbenchQueuePanel` | 待处理与异常队列面板 | 盘点、保险、租赁、财务 |
| `ClosureStatusPanel` | 当前阶段、责任人、阻塞与结案条件 | 长链路详情页 |
| `SlaIndicatorBar` | 超时、升级、剩余 SLA 展示 | 工作流挂接对象 |
| `RecommendedActionPanel` | 推荐动作与下一步引导 | 各业务详情页 |
| `ExceptionResolutionDrawer` | 例外处理表单与记录 | 差异、理赔、逾期、失败推送 |

### 6.3 首批改造入口

1. `InventoryTask` 工作台
2. `InsurancePolicy` / `ClaimRecord` 工作台
3. `LeasingContract` / `RentPayment` 工作台
4. `FinanceVoucher` 工作台
5. `PurchaseRequest` / `AssetReceipt` / `Asset` 详情页推荐动作与闭环面板

## 7. 测试用例

### 7.1 后端测试

| 测试类型 | 重点 |
|---------|------|
| Service 测试 | 工作台摘要、队列聚合、闭环条件判断、例外动作执行 |
| API 测试 | `/runtime/?mode=workbench`、`/workbench/summary/`、`/closure/`、`/sla/` |
| Workflow 集成测试 | SLA 变化、升级、催办、对象动作联动 |
| 跨对象闭环测试 | 生命周期动作触发下游对象与状态回写 |

### 7.2 前端测试

| 测试类型 | 重点 |
|---------|------|
| 组件测试 | SummaryCards、QueuePanel、ClosureStatusPanel、SlaIndicatorBar |
| 视图测试 | 关键对象工作台渲染、推荐动作、异常处理交互 |
| 合同测试 | runtime 配置变化时的前端适配稳定性 |
| E2E 场景 | 盘点差异结案、理赔结案、租赁逾期处理、财务异常重推 |

## 8. 子 PRD 目录拆分

### 8.1 母 PRD 下的子 PRD 清单

| 优先级 | 子 PRD 名称 | 功能代码 | 建议文档名 | 目标 |
|--------|-------------|----------|-----------|------|
| P0 | 统一业务工作台运行时增强 | `business_workbench_runtime_phase2` | `docs/prd/prd-business-workbench-runtime-phase2-2026-03-26.md` | 为各业务域提供统一工作台摘要、队列、SLA、推荐动作协议 |
| P0 | 盘点差异闭环优化 | `inventory_difference_closure` | `docs/prd/prd-inventory-difference-closure-2026-03-26.md` | 将盘点从任务完成推进到差异认责、审批、结案 |
| P0 | 工作流 SLA 业务嵌入 | `workflow_sla_business_embedding` | `docs/prd/prd-workflow-sla-business-embedding-2026-03-26.md` | 将超时、升级、催办嵌入对象工作台与详情页 |
| P1 | 生命周期跨对象动作扩展 Phase 2 | `lifecycle_cross_object_actions_phase2` | `docs/prd/prd-lifecycle-cross-object-actions-phase2-2026-03-26.md` | 补齐维修、处置、调账、项目回收等下游联动 |
| P1 | 财务源单到核销闭环 | `finance_source_to_settlement_closure` | `docs/prd/prd-finance-source-to-settlement-closure-2026-03-26.md` | 从源单、凭证、过账、核销、ERP 异常形成统一闭环 |
| P1 | 保险续保与理赔闭环 | `insurance_renewal_claim_closure` | `docs/prd/prd-insurance-renewal-claim-closure-2026-03-26.md` | 强化临期续保、理赔处理、赔付、结案工作台 |
| P1 | 租赁逾期与归还结清闭环 | `leasing_payment_return_closure` | `docs/prd/prd-leasing-payment-return-closure-2026-03-26.md` | 强化逾期催收、归还验收、结清归档 |
| P2 | 闭环经营指标与管理驾驶舱 | `closed_loop_operational_metrics` | `docs/prd/prd-closed-loop-operational-metrics-2026-03-26.md` | 面向组织和管理层输出闭环效率、异常治理和瓶颈指标 |

### 8.2 子 PRD 依赖关系

1. `business_workbench_runtime_phase2` 是其余子 PRD 的公共前置。
2. `workflow_sla_business_embedding` 需与工作台运行时并行设计。
3. `inventory_difference_closure` 可最先落地，用于验证例外处理闭环范式。
4. `finance_source_to_settlement_closure`、`insurance_renewal_claim_closure`、`leasing_payment_return_closure` 共享工作台与 SLA 基础设施。
5. `closed_loop_operational_metrics` 依赖前面各域积累的标准化状态与动作埋点。

## 9. 分阶段实施路线图

### 9.1 Phase 0: 公共基础能力收敛

建议周期：1.5 至 2 周

目标：

1. 完成工作台 runtime 协议扩展。
2. 完成 SummaryCards、QueuePanel、ClosurePanel、SlaIndicator 公共组件。
3. 明确对象级闭环摘要与 SLA 接口协议。

交付：

1. `business_workbench_runtime_phase2`
2. `workflow_sla_business_embedding`
3. 一套公共前后端测试基座

出口标准：

1. `AssetProject` 之外至少再有 1 个对象跑通工作台协议。
2. 动态详情页可展示闭环摘要、推荐动作、SLA 状态。
3. 统一队列面板能承载待处理和异常队列。

### 9.2 Phase 1: 盘点与生命周期闭环

建议周期：2 至 3 周

目标：

1. 把盘点从“差异识别”升级到“差异结案”。
2. 扩展生命周期跨对象动作，打通维修、处置、调账等下游动作。

交付：

1. `inventory_difference_closure`
2. `lifecycle_cross_object_actions_phase2`

出口标准：

1. `InventoryDifference` 可完成认责、复核、审批、处置、结案。
2. 生命周期关键对象可在详情页看到下一步动作建议。
3. 至少 3 条跨对象动作链支持自动或半自动收口。

### 9.3 Phase 2: 财务、保险、租赁闭环

建议周期：3 至 4 周

目标：

1. 让财务、保险、租赁从统计页升级为经营工作台。
2. 形成源单到终态的一致性追踪。

交付：

1. `finance_source_to_settlement_closure`
2. `insurance_renewal_claim_closure`
3. `leasing_payment_return_closure`

出口标准：

1. 财务可查看源单、凭证、推送、异常、核销的统一状态。
2. 保险可查看临期续保、理赔处理、赔付、结案队列。
3. 租赁可查看待收租、逾期、待归还、待结清队列。

### 9.4 Phase 3: 经营指标与管理驾驶舱

建议周期：1.5 至 2 周

目标：

1. 形成可用于组织运营复盘的统一闭环指标体系。
2. 支持部门、组织、业务域维度的瓶颈分析。

交付：

1. `closed_loop_operational_metrics`

出口标准：

1. 至少提供闭环时长、超时率、异常结案率、自动闭环率 4 类核心指标。
2. 可按对象、组织、责任人查看异常堆积与闭环效率。
3. 管理端可识别高风险队列和重复瓶颈节点。

## 10. 实施优先级建议

### 10.1 必须先做

1. 统一工作台运行时协议
2. SLA 业务嵌入
3. 盘点差异闭环

原因：

1. 这三项是后续所有业务域复制的公共基础。
2. 盘点差异最能验证“例外处理闭环”是否真正成立。

### 10.2 第二批推进

1. 财务闭环
2. 保险闭环
3. 租赁闭环
4. 生命周期跨对象动作扩展

原因：

1. 这些模块已有服务层和基础对象，适合在统一工作台框架上快速收敛。
2. 这些业务都天然需要“待处理队列 + 异常处理 + 终态结案”。

### 10.3 最后统一经营指标

原因：

1. 若提前做管理指标，容易因前面各域状态定义不一致而失真。
2. 指标应建立在统一工作台和统一闭环语义之上。

## 11. 风险与约束

| 风险 | 说明 | 应对建议 |
|------|------|---------|
| 工作台再次散落为专页 | 各域可能各自新增页面 | 强制通过 runtime 和公共组件承载共性能力 |
| 动作协议不统一 | 各域自定义动作名称和响应结构 | 统一动作命名规范和响应结构 |
| 状态语义不一致 | 不同域的“完成”“结案”“核销”含义不同 | 在子 PRD 中强制定义终态语义与出口条件 |
| 指标无法横向比较 | 不同域缺少统一埋点和时间节点 | 提前定义闭环开始、阻塞、结案等标准事件 |

## 12. 成功标准

本路线图完成后，应满足以下业务结果：

1. 至少 4 个长链路业务域具备工作台化入口，而不只是列表/详情页。
2. 差异、逾期、失败、超时都能在统一队列中被追踪和处理。
3. 对象详情页能直接回答“卡在哪、谁负责、下一步做什么、何时算结案”。
4. 经营层能按对象、组织、责任人查看闭环效率和异常堆积。
5. 新业务域接入时，优先复用工作台与闭环协议，而不是再开发独立专页。
