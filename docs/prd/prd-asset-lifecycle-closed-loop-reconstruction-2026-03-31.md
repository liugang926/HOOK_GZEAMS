# 资产生命周期闭环重构 PRD

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 阶段 | Phase 7.2.35 |
| 作者/Agent | Codex |
| 目标范围 | Asset 与领用/调拨/归还/借用/维修/处置/折旧/财务闭环重构 |

## 一、功能概述与业务场景

当前系统已具备资产对象、生命周期单据对象、动态对象路由、闭环摘要和业务工作台能力，但核心资产对象尚未成为统一的生命周期聚合根。各类业务单据仍在各自服务中直接改写资产状态、责任人、位置和组织归属，导致以下问题：

- 资产状态更新口径不统一，状态日志与业务单据语义存在偏差。
- 资产详情页的闭环摘要未完整覆盖领用、调拨、归还、借用、保修、折旧等关键链路。
- 采购到资产、资产到维修/处置、资产到财务之间存在“可关联但不可编排”的断点。
- 工作台和统一动作协议仅覆盖部分对象，无法形成以资产为中心的业务闭环。

本 PRD 的目标是将 `Asset` 重构为生命周期聚合根，通过统一协调服务、统一闭环摘要、统一动作协议和统一工作台配置，使资产对象与生命周期单据对象形成可追踪、可阻塞、可推进、可核销的业务闭环。

核心业务场景：

1. 采购申请 -> 验收 -> 资产卡生成 -> 折旧/财务入账。
2. 资产领用 -> 借用/调拨/归还 -> 当前占用态与责任人同步。
3. 资产维修 -> 处置 -> 财务凭证 -> 生命周期完成。
4. 资产项目占用、盘点异常、保修、保险、租赁等下游事项统一回流到资产闭环状态。

## 二、用户角色与权限

| 角色 | 权限范围 | 关键动作 |
|------|---------|---------|
| 资产管理员 | 管理资产主数据、操作单据、闭环核对 | 生成资产卡、确认归还、完成调拨、发起处置 |
| 部门申请人/借用人 | 发起领用、借用、归还申请 | 创建单据、查看本人资产流转状态 |
| 生命周期处理人 | 维修、处置、折旧、财务处理 | 完成维修、执行处置、生成财务凭证 |
| 项目经理 | 项目资产占用和回收管理 | 资产分配、回收、项目结项 |
| 财务人员 | 资产采购、折旧、处置凭证处理 | 生成、审批、过账财务凭证 |

权限控制要求：

- 所有对象继续遵循组织隔离。
- 所有动作继续通过对象级权限和工作流节点权限控制。
- 资产生命周期协调服务不得绕过现有对象可见性和组织边界。

## 三、公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields 序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一 CRUD 方法 |

新增服务约束：

| 组件类型 | 基类/模式 | 引用路径 | 说明 |
|---------|----------|---------|------|
| Lifecycle Coordinator | Service Object | apps.assets.services.lifecycle_coordinator.AssetLifecycleCoordinatorService | 统一资产状态、责任人、位置、组织上下文协调更新 |
| Closure Binding | Existing Service | apps.system.services.object_closure_binding_service.ObjectClosureBindingService | 统一资产主闭环摘要聚合 |
| Timeline Aggregator | Existing Service | apps.lifecycle.services.closed_loop_service.LifecycleClosedLoopService | 统一资产主时间线聚合 |

## 四、数据模型设计

### 4.1 现有核心对象

| 对象 | 当前状态 | 闭环角色 |
|------|---------|---------|
| Asset | 已存在 | 生命周期聚合根 |
| PurchaseRequest | 已存在 | 上游采购需求单 |
| AssetReceipt | 已存在 | 收货与验收单 |
| AssetPickup | 已存在 | 领用单 |
| AssetTransfer | 已存在 | 调拨单 |
| AssetReturn | 已存在 | 归还单 |
| AssetLoan | 已存在 | 借用单 |
| Maintenance | 已存在 | 维修单 |
| DisposalRequest | 已存在 | 处置单 |
| DepreciationRecord | 已存在 | 折旧记录 |
| FinanceVoucher | 已存在 | 财务闭环对象 |
| AssetWarranty | 已存在 | 保修闭环对象 |

### 4.2 本次重构的数据职责

| 字段/概念 | 所属对象 | 设计要求 |
|----------|---------|---------|
| asset_status | Asset | 只作为资产主状态，不允许在多个业务服务内无序直接写入 |
| custodian/user/department/location | Asset | 必须通过统一协调服务修改 |
| source_purchase_request/source_receipt/source_receipt_item | Asset | 继续保留，用于上游追溯 |
| project_allocations/pickup_items/transfer_items/return_items/loan_items | Asset 反向关系 | 用于聚合闭环摘要、时间线和推荐动作 |
| depreciation_records/warranties | Asset 反向关系 | 纳入闭环判定与财务闭环 |

### 4.3 后续扩展预留

本 PRD 预留以下增强项：

- `Asset.current_context_code/current_context_id`：标识当前业务上下文。
- `Asset.lifecycle_stage`：标识资产主闭环阶段。
- `AssetLifecycleEvent`：统一业务事件流表，用于时间线、报表和审计收敛。

## 五、API 接口设计

### 5.1 动态对象路由约束

本功能禁止新增独立 URL 配置，所有对象继续通过统一入口访问：

- `GET /api/objects/Asset/`
- `GET /api/objects/Asset/{id}/`
- `GET /api/system/objects/Asset/{id}/closure/`
- `GET /api/system/objects/Asset/{id}/actions/`
- `POST /api/system/objects/Asset/{id}/actions/{action_code}/execute/`

### 5.2 闭环接口增强

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/objects/Asset/{id}/closure/` | 返回资产聚合闭环摘要，覆盖领用/调拨/归还/借用/维修/处置/盘点/折旧/财务/保修 |
| GET | `/api/system/objects/PurchaseRequest/{id}/closure/` | 返回采购到资产生成到财务的闭环摘要 |
| GET | `/api/system/objects/AssetReceipt/{id}/closure/` | 返回验收到资产生成到财务的闭环摘要 |

### 5.3 动作协议增强

| 对象 | 动作编码 | 说明 |
|------|---------|------|
| PurchaseRequest | `purchase.create_receipt` | 由采购申请生成收货单 |
| AssetReceipt | `receipt.generate_assets` | 由验收单生成资产卡 |
| Asset | `asset.create_maintenance` | 由资产生成维修单 |
| Asset | `asset.create_disposal` | 由资产生成处置单 |
| Asset | `asset.create_pickup` | 后续阶段新增 |
| Asset | `asset.create_transfer` | 后续阶段新增 |
| Asset | `asset.create_loan` | 后续阶段新增 |
| Asset | `asset.create_return` | 后续阶段新增 |
| DisposalRequest | `disposal.generate_voucher` | 后续阶段新增 |
| AssetReceipt | `receipt.generate_voucher` | 后续阶段新增 |
| PurchaseRequest | `purchase.generate_voucher` | 后续阶段新增 |

### 5.4 错误码

沿用平台统一错误码：

- `VALIDATION_ERROR`
- `ORGANIZATION_MISMATCH`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `CONFLICT`
- `SERVER_ERROR`

## 六、前端组件设计

### 6.1 公共组件引用

| 组件类型 | 使用组件 | 引用路径 | 说明 |
|---------|---------|---------|------|
| 详情页 | BaseDetailPage | `@/components/common/BaseDetailPage.vue` | 资产和单据详情承载容器 |
| 工作台动作条 | ObjectActionBar | `@/components/common/ObjectActionBar.vue` | 统一动作展示 |
| 工作台面板宿主 | ObjectWorkbenchPanelHost | `@/components/common/ObjectWorkbenchPanelHost.vue` | 统一闭环/队列/panel 容器 |
| 闭环面板 | ClosureStatusPanel | `@/components/common/ClosureStatusPanel.vue` | 展示主闭环阶段、阻塞项、责任人 |
| 推荐动作 | RecommendedActionPanel | `@/components/common/RecommendedActionPanel.vue` | 展示下一步动作 |
| 动态详情控制器 | useDynamicDetailController | `@/views/dynamic/workspace/useDynamicDetailController.ts` | 聚合 closure/actions/workbench 数据 |

### 6.2 页面设计要求

- `Asset` 工作台必须逐步纳入领用、调拨、归还、借用、维修、处置、盘点、折旧、财务队列。
- `Maintenance`、`DisposalRequest`、`AssetTransfer`、`AssetReturn`、`AssetLoan` 后续需要补齐对象 workbench。
- 前端禁止直接根据资产状态硬编码闭环逻辑，必须消费后端 closure summary。

## 七、实施分期

### Phase 1：资产状态协调收口

- 新增 `AssetLifecycleCoordinatorService`。
- 领用/调拨/归还/借用的资产主状态、责任人、位置更新统一收口。
- 借用确认后资产主状态使用 `lent`，不再与普通在用混用。

### Phase 2：资产主闭环摘要与时间线补齐

- `Asset` 的 closure summary 纳入领用/调拨/归还/借用/保修/折旧。
- `Asset` 时间线纳入操作单据、财务、项目分配、保修、折旧事件。

### Phase 3：统一动作协议扩展

- 补齐资产到操作单据的创建动作。
- 将采购/验收/处置到财务凭证的生成动作接入统一动作协议。

### Phase 4：工作台与端到端测试

- 为核心生命周期单据配置工作台。
- 建立真实业务链路测试：采购申请 -> 验收 -> 资产卡 -> 借用/归还 -> 维修/处置 -> 财务闭环。

## 八、测试用例

| 测试层级 | 核心用例 |
|---------|---------|
| Service | 资产协调服务统一更新状态和责任人，并写入状态日志 |
| Service | 领用/调拨/归还/借用服务不再直接分散改写资产主状态 |
| Closure API | 资产主闭环摘要正确暴露 openPickup/openTransfer/openReturn/openLoan/pendingDepreciation 等指标 |
| Integration | 采购申请 -> 验收 -> 资产卡 -> 财务凭证闭环 |
| Integration | 资产借用 -> 归还 -> 维修/处置 -> 财务闭环 |

## 九、验收标准

1. 资产主状态、责任人、位置的业务更新全部通过统一协调服务执行。
2. `Asset` 闭环摘要必须覆盖操作单据、维修、处置、盘点、折旧、财务、保修。
3. 借用资产在主状态上必须与普通在用资产区分。
4. 不新增静态业务路由，继续使用动态对象路由体系。
5. 端到端测试能够证明资产对象与生命周期单据形成业务闭环。
