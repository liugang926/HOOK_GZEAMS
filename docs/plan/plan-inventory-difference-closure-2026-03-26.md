# 盘点差异闭环优化实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `inventory_difference_closure`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `先补差异状态机与处置动作，再补任务工作台和结案出口`

## 2. 现状判断

当前盘点已经完成了“任务、快照、扫描、差异生成”的前半程，但差异治理仍然偏轻。

现状依据:

1. 盘点任务完成时已自动生成差异:
   - `backend/apps/inventory/services/inventory_service.py`
   - `backend/apps/inventory/services/difference_service.py`
2. `InventoryDifference` 模型已有 `pending / confirmed / resolved / ignored` 状态，但服务层当前仅使用 `resolved / ignored`:
   - `backend/apps/inventory/models.py`
   - `backend/apps/inventory/services/difference_service.py`
3. 当前 API 主要支持:
   - `resolve`
   - `batch-resolve`
   - `pending`
   - `summary`
   - `sync-asset`
   - 入口在 `backend/apps/inventory/viewsets/difference_viewsets.py`
4. 前端目前缺少差异专门的工作台或闭环页，更多还是任务级页面:
   - `frontend/src/views/inventory/TaskList.vue`

结论:

1. 差异识别能力已成熟，差异处置闭环尚未真正产品化。
2. 当前“resolved/ignored”更像技术状态，不足以支撑认责、复核、审批、结案。

## 3. 实施原则

1. 差异闭环优先基于现有 `InventoryTask` 与 `InventoryDifference` 对象扩展，不新增平行业务对象。
2. 差异必须从“识别结果”升级为“待处理事项”。
3. 差异闭环要覆盖:
   - 认责
   - 复核
   - 审批
   - 处置
   - 资产回写
   - 结案
4. 盘点任务是否完成，不再等同于业务已经闭环。
5. 所有差异操作优先走统一对象动作协议和工作台队列。

## 4. 分阶段执行

## Phase 0: 差异生命周期冻结

### 目标

明确盘点差异从发现到结案的标准状态机。

### 任务

1. 冻结差异主状态:
   - `pending`
   - `confirmed`
   - `in_review`
   - `approved`
   - `executing`
   - `resolved`
   - `ignored`
   - `closed`
2. 冻结处置类型:
   - 位置纠正
   - 保管人纠正
   - 维修
   - 报废
   - 补录建卡
   - 调账
   - 无效差异
3. 冻结角色语义:
   - 发现人
   - 责任人
   - 复核人
   - 审批人
   - 结案人
4. 冻结结案条件:
   - 已有处置结论
   - 必要审批已完成
   - 资产回写或豁免已明确
   - 证据材料齐全

### 验收

1. 差异状态机与处置类型冻结。
2. 模型、动作、工作台队列使用统一语义。

建议工期: `1-2 人天`

---

## Phase 1: 后端模型与服务增强

### 目标

把差异从简单结果记录升级为可运营的处置对象。

### 任务

1. 扩展 `InventoryDifference` 字段:
   - `owner`
   - `reviewed_by`
   - `reviewed_at`
   - `approved_by`
   - `approved_at`
   - `closure_type`
   - `closure_notes`
   - `closure_completed_at`
   - `evidence_refs` 或附件引用字段
   - `linked_action_code`
2. 扩展 `DifferenceService`:
   - 确认差异
   - 指派责任人
   - 提交复核
   - 审批通过/驳回
   - 执行处置
   - 标记结案
3. 把现有 `resolve_difference()` 调整为新状态机的一部分，而不是最终总入口。
4. 把 `_sync_asset_from_difference()` 升级为可控的处置回写步骤。

### 涉及模块

1. `backend/apps/inventory/models.py`
2. `backend/apps/inventory/services/difference_service.py`
3. `backend/apps/inventory/serializers/difference_serializers.py`
4. `backend/apps/inventory/filters/difference_filters.py`
5. `backend/apps/inventory/migrations/`

### 交付物

1. 差异状态机迁移
2. 差异处置服务
3. 差异字段扩展

### 验收

1. 差异可经历确认、复核、审批、处置、结案流程。
2. 旧接口仍能兼容基础读取，写操作走新状态机。

建议工期: `4-5 人天`

---

## Phase 2: API 与对象动作收口

### 目标

让差异闭环通过统一 API 和动作协议对外暴露。

### 任务

1. 保留并增强现有差异 API:
   - `resolve`
   - `batch-resolve`
   - `pending`
   - `summary`
   - `sync-asset`
2. 新增动作接口或统一收口到对象动作:
   - `confirm`
   - `assign_owner`
   - `submit_review`
   - `approve_resolution`
   - `reject_resolution`
   - `execute_resolution`
   - `close_difference`
3. 新增任务级工作台摘要接口:
   - 差异总数
   - 待确认
   - 待复核
   - 待审批
   - 待回写
   - 待结案
4. 为 `InventoryTask` 提供差异闭环面板数据接口。

### 涉及模块

1. `backend/apps/inventory/viewsets/difference_viewsets.py`
2. `backend/apps/inventory/viewsets/task_viewsets.py`
3. `backend/apps/system/viewsets/object_router.py`
   - 如采用统一对象动作接入

### 交付物

1. 差异闭环动作协议
2. 任务级差异摘要与队列接口
3. 兼容现有 inventory REST 入口

### 验收

1. 差异所有关键处理动作都可通过 API 调用。
2. 盘点任务能直接展示差异闭环状态，而不只是差异数量。

建议工期: `3-4 人天`

---

## Phase 3: 前端工作台与详情闭环

### 目标

把盘点差异真正做成“待处理业务队列”。

### 任务

1. 为 `InventoryTask` 接入工作台增强:
   - 差异摘要卡
   - 待处理队列
   - 结案条件面板
   - 推荐动作
2. 为 `InventoryDifference` 增加:
   - 闭环状态展示
   - 责任人/审批信息展示
   - 处置表单入口
   - 证据与历史记录展示
3. 优先复用公共工作台组件:
   - `WorkbenchSummaryCards`
   - `WorkbenchQueuePanel`
   - `ClosureStatusPanel`
4. 如果保留 inventory 专页，则专页与动态对象页必须语义一致。

### 涉及模块

1. `frontend/src/views/inventory/TaskList.vue`
2. `frontend/src/views/dynamic/DynamicDetailPage.vue`
3. `frontend/src/components/common/`
   - 复用工作台公共组件
4. `frontend/src/api/`
   - 补差异闭环动作 API

### 交付物

1. `InventoryTask` 差异工作台
2. `InventoryDifference` 闭环详情增强
3. 差异处置交互入口

### 验收

1. 用户能直接从任务详情进入待处理差异队列。
2. 用户能看到差异卡在哪、谁负责、下一步做什么、何时算结案。

建议工期: `4-5 人天`

---

## Phase 4: 资产回写与后置联动

### 目标

让盘点差异处理结果真正影响资产终态，而不是停留在差异记录里。

### 任务

1. 位置差异:
   - 回写资产位置
2. 保管人差异:
   - 回写保管人
3. 损坏差异:
   - 更新资产状态
   - 必要时发起维修候选动作
4. 盘亏差异:
   - 发起报废、调账或继续追查
5. 盘盈差异:
   - 发起补录建卡或待认领动作
6. 所有回写动作写入历史与审计流。

### 交付物

1. 差异到资产的回写策略
2. 差异到下游动作的联动策略

### 验收

1. 差异处置后资产主数据与状态可一致回写。
2. 高风险差异可进入后续维修、报废或建卡链路。

建议工期: `3-4 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/inventory/models.py`
2. `backend/apps/inventory/services/difference_service.py`
3. `backend/apps/inventory/viewsets/difference_viewsets.py`
4. `backend/apps/inventory/viewsets/task_viewsets.py`
5. `backend/apps/inventory/serializers/difference_serializers.py`
6. `backend/apps/inventory/filters/difference_filters.py`
7. `backend/apps/inventory/tests/`
8. `backend/apps/system/viewsets/object_router.py`
   - 如接入统一对象动作

### 前端

1. `frontend/src/views/inventory/TaskList.vue`
2. `frontend/src/views/dynamic/DynamicDetailPage.vue`
3. `frontend/src/api/`
   - 差异闭环动作客户端
4. `frontend/src/components/common/`
   - 复用工作台组件
   - 如需新增差异处置抽屉或状态卡

## 6. 测试计划

### 6.1 后端

1. 差异状态流转测试
2. 差异指派、复核、审批、结案测试
3. 差异摘要统计测试
4. 资产回写测试
5. 旧 `resolve` 接口兼容测试

### 6.2 前端

1. 任务工作台差异摘要渲染
2. 差异闭环状态展示
3. 差异处置动作交互
4. 任务详情与差异详情联动跳转

### 6.3 E2E

1. 完成盘点任务
2. 生成差异
3. 指派责任人
4. 提交复核
5. 审批通过
6. 回写资产
7. 标记结案

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 状态机过度复杂 | 盘点差异处理链路变得太重 | 保留最小闭环链条，按高风险差异优先加强 |
| 与现有 resolve 接口冲突 | 老接口语义过于简单 | 保留兼容层，内部映射到新状态机 |
| 资产回写过早执行 | 可能导致错误主数据 | 把回写动作放到审批/执行后置步骤 |
| 前端仍停留在任务统计页 | 用户无法真正处理差异 | 必须提供队列和差异详情入口 |

## 8. 完成标准

1. 盘点任务完成后，差异会进入可运营的待处理队列。
2. 差异不再只有 `resolved/ignored` 两种粗粒度结果。
3. 差异能完成认责、复核、审批、回写、结案闭环。
4. 盘点模块从“任务结束”升级为“业务真正结案”。
