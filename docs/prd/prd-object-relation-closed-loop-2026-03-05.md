# 对象关联闭环重构 PRD（资产域 + IT资产域）

## 1. 文档信息
- 文档版本: `v1.1`
- 日期: `2026-03-05`
- 作者角色: `系统高级架构 / 高级前端工程`
- 目标系统: `GZEAMS (Django + Vue3 元数据引擎)`
- 适用范围: `对象关系建模、对象详情关联展示、单据与资产/IT资产闭环`

## 2. 背景与问题
当前系统已具备大量资产业务对象、IT资产对象与操作单据，但在“对象关系可见性”和“跨对象追溯链路”上没有形成统一闭环。典型现象：
1. 资产详情页看不到领用/调拨/借用/归还等单据，或展示不稳定。
2. IT 资产详情页难以一站式查看维护记录、配置变更、许可证分配等关联对象。
3. 布局设计器中的关联配置无法稳定映射到运行时页面。
4. 部分生命周期业务状态变化后，没有同步反映在资产/IT资产主档或可追溯链路中。

## 3. 现状全面分析（代码级）

### 3.1 数据模型关系现状
资产相关关系存在三种模式：
1. 直接关系（可直接闭环）
   - `Maintenance.asset -> Asset`
   - `MaintenanceTask.asset -> Asset`
   - `InventorySnapshot/InventoryScan/InventoryDifference.asset -> Asset`
   - `DepreciationRecord.asset -> Asset`
   - `InsuredAsset.asset -> Asset`
   - `ClaimRecord.asset -> Asset`
   - `LeaseItem.asset`, `LeaseReturn.asset`
   - `ITMaintenanceRecord.asset`, `ConfigurationChange.asset`, `LicenseAllocation.asset`
2. 间接关系（单据头通过明细关联资产）
   - `AssetPickup <- PickupItem.asset`
   - `AssetTransfer <- TransferItem.asset`
   - `AssetReturn <- ReturnItem.asset`
   - `AssetLoan <- LoanItem.asset`
   - `DisposalRequest <- DisposalItem.asset`
3. 关系缺失或弱追溯
   - `AssetReceipt` 与 `Asset` 缺少稳定可追溯链路（`generate_asset_cards` 仍为 stub，仅标记 `asset_generated=true`）。

### 3.2 元数据/路由层现状
1. `ObjectRouterViewSet.fields/runtime` 对硬编码对象读取 `ModelFieldDefinition`。
2. `_format_model_field` 对 reverse relation 输出固定空值：
   - `reverse_relation_model=''`
   - `reverse_relation_field=''`
3. `ModelFieldDefinition` 映射不包含 `ManyToOneRel` 等 reverse relation 类型，导致硬编码模型反向关系元数据不足。
4. 对象注册以“单据头对象”为主，`PickupItem/TransferItem/ReturnItem/LoanItem/DisposalItem` 等明细对象未统一纳入对象引擎可消费关系层。

### 3.3 前端展示层现状
1. `RelatedObjectTable` 以“直接外键过滤”作为核心假设：
   - 请求 `GET /system/objects/{relatedObjectCode}/?{reverseRelationField}={parentId}`
2. 该假设不支持“通过明细表关联”的单据头关系，导致资产关联单据缺失。
3. 对于 IT 资产对象，仍缺少统一的“经 Asset 反查”关系协议。
4. `AssetDetail.vue` 存在硬编码关联配置（例如 `AssetPickup + reverseRelationField=asset`），与真实模型不一致。
5. 设计器与运行时虽然已有 `canvas placement` 能力，但关联数据来源仍未统一抽象。

### 3.4 业务闭环现状
1. 资产操作服务（领用/调拨/归还/借用）已更新资产状态与保管信息，具备部分业务闭环。
2. 生命周期服务存在闭环缺口：
   - `AssetReceipt.generate_asset_cards` 未真正生成资产与来源绑定。
   - `DisposalRequestService` 执行报废后未同步资产报废状态。
3. IT 资产域存在关系展示闭环缺口：
   - `ITAsset(ITAssetInfo)` 与 `ITMaintenanceRecord/ConfigurationChange/ITLicenseAllocation` 关系未在统一关系协议下稳定展示。

## 4. 根因总结
1. 平台缺少“统一关系定义层”，前端只能猜测关系字段。
2. 关系查询能力绑定在列表过滤，不支持 through relation（父单据 <- 明细 -> 资产）与 derived relation（父对象经桥接键反查）。
3. 资产与 IT 资产生命周期状态机分散在不同服务，未抽象为统一事件/规则。
4. 关系展示与布局引擎未共享同一关系契约。

## 5. 产品目标

### 5.1 目标
1. 资产对象详情可稳定展示全量关联业务单据（直接 + 间接）。
2. IT 资产对象详情可稳定展示全量关联业务对象（维护、配置变更、许可证分配、基础资产卡）。
3. 布局设计器、详情页、编辑页使用同一关系契约与渲染协议。
4. 形成资产全生命周期可追溯链路（创建来源、操作轨迹、状态变化）。
5. 将关系展示从“对象硬编码”升级为“元数据驱动”。

### 5.2 非目标
1. 不处理历史兼容包袱（按项目当前约束可做结构性重构）。
2. 不在本期处理 BI 报表体系。

## 6. 方案设计（目标架构）

### 6.1 新增统一关系定义层（Object Relation Graph）
新增关系元数据模型（建议 `ObjectRelationDefinition`），核心字段：
- `relation_code`
- `parent_object_code`
- `target_object_code`
- `relation_kind`: `direct_fk | through_line_item | derived_query`
- `target_fk_field`（direct 场景）
- `through_object_code`（through 场景）
- `through_parent_fk_field`
- `through_target_fk_field`
- `derived_parent_key_field`
- `derived_target_key_field`
- `display_mode`（inline/tab/readonly）
- `layout_binding`（关系卡片默认位置与顺序）

### 6.2 统一关系查询 API
新增标准端点（替代前端拼 filter）：
1. `GET /api/system/objects/{code}/relations/`
   - 返回该对象可展示关系定义（含显示策略）。
2. `GET /api/system/objects/{code}/{id}/related/{relation_code}/`
   - 后端根据关系定义执行 direct/through/derived 查询并返回分页结果。

说明：前端不再关心 `reverseRelationField` 是否真实存在，避免模型实现细节泄露到 UI。

### 6.3 对象路由层改造
1. `ObjectRouterViewSet.fields/runtime` 输出统一 `relations` 契约。
2. 硬编码对象 reverse relation 不再依赖 `ModelFieldDefinition.field_type='sub_table'` 猜测。
3. 关系契约优先于旧 reverse relation 字段，逐步收敛旧字段。

### 6.4 资产与 IT 资产生命周期闭环补齐
1. `AssetReceipt.generate_asset_cards` 实现真实建卡，补充资产来源追溯字段：
   - `source_object_code`
   - `source_record_id`
   - `source_line_id`
2. `DisposalRequestService.execute_disposal/complete_request` 同步资产状态为 `scrapped`，并记录状态日志。
3. 引入统一资产状态变更入口（AssetLifecycleService），避免各服务重复散落修改。
4. IT 资产关系闭环接入（关系层面）：
   - `ITAsset -> Asset`（direct）
   - `ITAsset -> ITMaintenanceRecord`（derived_query，按 `asset_id`）
   - `ITAsset -> ConfigurationChange`（derived_query，按 `asset_id`）
   - `ITAsset -> ITLicenseAllocation`（derived_query，按 `asset_id`）

### 6.5 前端关系组件升级
1. `RelatedObjectTable` 改为调用 `/{parent}/{id}/related/{relation_code}`。
2. `BaseDetailPage` / `DynamicDetailPage` 直接消费 `relations` 元数据。
3. 布局设计器关系卡片使用统一 schema（支持画布比例 + 栅格映射）。
4. 关系卡片支持：计数、快速跳转、创建入口、筛选与排序。

## 7. 关键业务关系闭环矩阵
| 关系 | 当前状态 | 问题 | 目标状态 |
|---|---|---|---|
| 资产-领用单 | 间接（PickupItem） | 详情页无法稳定展示 | 通过关系引擎稳定展示单据头 |
| 资产-调拨单 | 间接（TransferItem） | 同上 | 同上 |
| 资产-归还单 | 间接（ReturnItem） | 同上 | 同上 |
| 资产-借用单 | 间接（LoanItem） | 同上 | 同上 |
| 资产-报废单 | 间接（DisposalItem） | 缺展示 + 缺状态闭环 | 展示 + 状态联动 |
| 资产-入库单 | 弱关联 | 建卡链路不完整 | 建卡时强绑定来源 |
| 资产-维修/盘点/折旧/保险等 | 多数可关联 | 展示协议不统一 | 全部通过统一关系协议输出 |
| IT资产-基础资产卡 | 直接（OneToOne） | 详情未统一联动展示 | 双向可跳转、统一关系卡 |
| IT资产-维护记录 | 间接（经 Asset） | 缺统一关系定义 | 通过 derived_query 稳定展示 |
| IT资产-配置变更 | 间接（经 Asset） | 缺统一关系定义 | 通过 derived_query 稳定展示 |
| IT资产-许可证分配 | 间接（经 Asset） | 缺统一关系定义 | 通过 derived_query 稳定展示 |

## 8. 验收标准（DoD）
1. 在资产详情页可查看领用/调拨/归还/借用/报废等单据头，数据准确率 100%。
2. 在 IT 资产详情页可查看维护记录/配置变更/许可证分配，数据准确率 100%。
3. 关系展示不依赖对象硬编码字段名（移除 `reverseRelationField` 猜测路径）。
4. 资产入库建卡后可从资产追溯到来源单据与明细。
5. 报废完成后资产状态与状态日志正确更新。
6. 设计器配置的关系卡片在运行时位置、顺序、大小一致。
7. 新增后端与前端自动化测试覆盖 direct + through + derived_query 三类关系。

## 9. 风险与应对
1. 风险：关系定义配置错误导致查询异常。
   - 应对：关系定义保存时做模型字段校验与启动期健康检查。
2. 风险：through/derived 查询性能下降。
   - 应对：为 through 表增加复合索引；关系 API 默认分页 + 必选排序；derived 查询限制白名单字段。
3. 风险：旧页面仍有硬编码关系渲染。
   - 应对：关系 API 上线后按对象清单逐步替换并加 lint 规则禁用旧方式。

## 10. 里程碑建议
- `M1 (1周)`: 关系定义模型 + 关系查询 API 最小可用。
- `M2 (1周)`: 资产域 + IT资产域关系接入（through/derived）+ 详情页升级。
- `M3 (1周)`: 入库建卡与报废状态闭环 + 统一状态服务。
- `M4 (1周)`: 设计器关系卡片对齐 + 全量测试与回归。
