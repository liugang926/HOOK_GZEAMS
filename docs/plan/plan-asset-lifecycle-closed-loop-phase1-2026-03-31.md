# 资产生命周期闭环重构开发计划

## 文档信息
| 项目 | 说明 |
|------|------|
| 版本 | v1.0 |
| 日期 | 2026-03-31 |
| 对应 PRD | `docs/prd/prd-asset-lifecycle-closed-loop-reconstruction-2026-03-31.md` |
| 作者/Agent | Codex |

## 一、目标

本计划用于分阶段落地“资产作为生命周期聚合根”的闭环重构，目标是在不破坏现有动态对象路由和基础 CRUD 能力的前提下，逐步实现：

- 资产主状态更新统一协调。
- 资产闭环摘要覆盖核心单据链路。
- 统一动作协议覆盖资产生命周期推进动作。
- 业务工作台围绕资产主闭环收敛。

## 二、现状问题

| 问题 | 当前表现 | 影响 |
|------|---------|------|
| 状态写入口分散 | 领用/调拨/归还/借用服务分别直接写资产字段 | 状态日志、时间线、工作台摘要不一致 |
| 借用语义混淆 | 借出资产写成 `in_use` | 无法区分普通在用和借出 |
| 闭环摘要不完整 | 资产摘要未纳入操作单据、保修、折旧 | 资产主闭环不可信 |
| 动作协议覆盖不足 | 统一动作仅覆盖采购/验收/维修/处置局部动作 | 无法形成“看见阻塞并立即推进”的工作流 |
| 工作台成熟度不均 | 仅部分对象具备 workbench | 用户侧无法感知真正闭环 |

## 三、里程碑计划

### M1：状态协调层收口

目标：

- 新增 `AssetLifecycleCoordinatorService`。
- 统一收口 `AssetPickupService`、`AssetTransferService`、`AssetReturnService`、`AssetLoanService` 的资产主状态更新。
- 对 `AssetPickup` 工作流通过模型 hook 更新资产状态的场景做一致性收口。

交付物：

- 统一协调服务
- 现有服务改造
- 基础测试补充

验收标准：

- 相关服务不再直接分散调用 `asset.save()` 更新主状态。
- 状态变更自动写入 `AssetStatusLog`。
- 借出资产状态为 `lent`。

### M2：资产主闭环摘要增强

目标：

- 扩展 `ObjectClosureBindingService._build_asset_summary()`。
- 纳入领用/调拨/归还/借用/保修/折旧指标。

交付物：

- 新指标：`openPickupCount`、`openTransferCount`、`openReturnCount`、`openLoanCount`、`activeWarrantyCount`、`pendingDepreciationCount`
- 新阶段判定：`Transfer in progress`、`Return in progress`、`Loan in progress`、`Pickup in progress`、`Depreciation posting pending`

验收标准：

- 资产闭环摘要能正确识别核心操作单据阻塞项。

### M3：资产主时间线和动作协议扩展

目标：

- 补齐资产主时间线。
- 将财务凭证生成动作接入统一动作协议。
- 补齐资产到领用/调拨/归还/借用的动作入口。

交付物：

- 扩展 `LifecycleClosedLoopService`
- 扩展 `LifecycleActionService`

### M4：工作台收敛与端到端测试

目标：

- 资产工作台展示核心单据队列。
- 核心生命周期单据对象接入统一工作台。
- 增加端到端闭环测试。

交付物：

- workbench config
- 前端面板补齐
- 集成测试与回归测试

## 四、本轮执行范围

本轮直接执行 M1 + M2 的最小可落地范围：

1. 新增 `AssetLifecycleCoordinatorService`。
2. 改造领用/调拨/归还/借用服务，统一调用协调服务。
3. 改造 `AssetPickup` 工作流审批 hook，避免旁路更新。
4. 扩展资产闭环摘要，纳入领用/调拨/归还/借用/保修/折旧指标。
5. 增补服务测试和闭环摘要测试。

## 五、任务拆分

| 编号 | 任务 | 模块 | 状态 |
|------|------|------|------|
| T1 | 新增资产生命周期协调服务 | `backend/apps/assets/services/` | 本轮执行 |
| T2 | 改造操作单据服务状态更新 | `backend/apps/assets/services/operation_service.py` | 本轮执行 |
| T3 | 改造模型 hook 状态更新 | `backend/apps/assets/models.py` | 本轮执行 |
| T4 | 扩展资产闭环摘要 | `backend/apps/system/services/object_closure_binding_service.py` | 本轮执行 |
| T5 | 增补服务与闭环测试 | `backend/apps/assets/tests/`、`backend/apps/system/tests/` | 本轮执行 |
| T6 | 扩展时间线聚合 | `backend/apps/lifecycle/services/closed_loop_service.py` | 下一轮 |
| T7 | 扩展统一动作协议 | `backend/apps/lifecycle/services/lifecycle_action_service.py` | 下一轮 |
| T8 | 扩展工作台 | `backend/apps/system/menu_config.py`、前端 workspace | 下一轮 |

## 六、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 现有测试库状态不稳定 | pytest 结果可能受测试库残留影响 | 优先做语法检查和定向测试，必要时清理测试库 |
| 借用状态收敛到 `lent` 可能影响旧断言 | 旧测试和旧筛选逻辑可能失败 | 先补服务测试，再逐步修复旧假设 |
| 工作区存在大量脏改动 | 易覆盖用户未提交内容 | 保持最小写入面，避免修改无关文件 |

## 七、下一步建议

1. 下一轮优先扩展资产主时间线，把操作单据和折旧/保修事件并入主链路。
2. 紧接着扩展统一动作协议，把采购/验收/处置到财务的推进动作并入对象路由。
3. 最后再做工作台前端收敛，避免前后端契约来回调整。
