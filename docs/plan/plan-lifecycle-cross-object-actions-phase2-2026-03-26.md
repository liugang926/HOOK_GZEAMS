# 生命周期跨对象动作 Phase 2 实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `lifecycle_cross_object_actions_phase2`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `在现有动作协议基础上扩下游联动，优先补维修、处置、财务与项目回收链路`

## 2. 现状判断

当前生命周期跨对象动作已经形成第一版统一协议，但覆盖范围仍偏窄。

现状依据:

1. 已有统一动作协议:
   - `purchase.create_receipt`
   - `receipt.generate_assets`
   - `asset.create_maintenance`
   - `asset.create_disposal`
   - 代码位于 `backend/apps/lifecycle/services/lifecycle_action_service.py`
2. 已有生命周期时间线聚合:
   - `backend/apps/lifecycle/services/closed_loop_service.py`
3. 当前主链路已能覆盖采购、验收、资产、维保、处置的部分关系。
4. 缺少的主要是下游联动广度，而不是动作框架本身。

结论:

1. Phase 2 不需要重写动作协议。
2. 重点应从“能发起下游对象”升级为“下游完成后能真正驱动资产与相关域收口”。

## 3. 实施原则

1. 所有跨对象动作继续由后端统一编排，前端只消费动作列表与执行结果。
2. 生命周期动作不能只负责创建下游草稿，还要负责终态联动。
3. 资产状态、财务状态、项目占用、保险保障、租赁占用等联动要优先通过统一编排服务收口。
4. 动作结果必须写入时间线与历史流，避免出现“做了动作但详情页看不见结果”。
5. 新动作先做高价值闭环链路，不追求一次性铺满所有对象。

## 4. 分阶段执行

## Phase 0: 动作目录冻结

### 目标

明确 Phase 2 要补的动作目录和链路边界。

### 任务

1. 冻结新增动作目录:
   - `maintenance.complete`
   - `maintenance.accept`
   - `disposal.execute`
   - `disposal.generate_finance_voucher`
   - `disposal.close_source_asset`
   - `asset.recover_to_available`
   - `asset.return_to_project_pool`
2. 冻结下游联动对象:
   - `Asset`
   - `Maintenance`
   - `DisposalRequest`
   - `FinanceVoucher`
   - `AssetProject` 或项目分配对象
3. 冻结动作结果返回结构:
   - `target_object_code`
   - `target_id`
   - `target_url`
   - `refresh_current`
   - `summary`
   - `timeline_event`

### 验收

1. Phase 2 动作目录和联动边界明确。
2. 不再边做边加动作名和结果字段。

建议工期: `1 人天`

---

## Phase 1: 维修链路收口

### 目标

把维修从“发起了维修单”升级为“维修完成后资产状态恢复并可继续流转”。

### 任务

1. 扩展维修动作:
   - 完工
   - 验收通过
   - 验收不通过
2. 统一资产状态回写:
   - 维修中
   - 待验收
   - 恢复可用
3. 对接时间线:
   - 发起维修
   - 维修执行
   - 维修验收
4. 如果维修失败或不可修复，支持推荐转入处置候选动作。

### 涉及模块

1. `backend/apps/lifecycle/services/maintenance_service.py`
2. `backend/apps/lifecycle/services/lifecycle_action_service.py`
3. `backend/apps/lifecycle/services/closed_loop_service.py`
4. `backend/apps/assets/`

### 验收

1. 维修完成能够驱动资产状态恢复或进入下一个推荐动作。
2. 维修全过程能在详情页时间线中查看。

建议工期: `3-4 人天`

---

## Phase 2: 处置链路收口

### 目标

把处置从“创建申请”升级为“处置执行后资产、财务、项目状态同步收口”。

### 任务

1. 扩展处置动作:
   - 审批通过后执行处置
   - 生成财务凭证
   - 标记资产报废完成
2. 对接财务:
   - 处置生成凭证入口已存在于财务 viewset，需纳入统一动作编排
3. 对接资产:
   - 资产状态改为 `scrapped`
   - 写入状态历史
4. 对接项目:
   - 若资产仍被项目占用，要求先回收或同步更新占用状态
5. 对接时间线和关系图:
   - 展示“处置 -> 财务凭证 -> 终态”链路

### 涉及模块

1. `backend/apps/lifecycle/services/disposal_service.py`
2. `backend/apps/lifecycle/services/lifecycle_action_service.py`
3. `backend/apps/finance/viewsets/__init__.py`
4. `backend/apps/projects/services.py`
5. `backend/apps/assets/`

### 验收

1. 处置执行后资产终态、财务记录、项目占用状态保持一致。
2. 处置链路能看到明确的下游财务结果。

建议工期: `4-5 人天`

---

## Phase 3: 推荐动作与跨域回收

### 目标

让对象详情页不仅展示“已有结果”，还展示“下一步推荐动作”。

### 任务

1. 为 `PurchaseRequest`、`AssetReceipt`、`Asset`、`Maintenance`、`DisposalRequest` 输出推荐动作。
2. 对于已处置、已维修、已退回项目的资产，输出下一阶段建议。
3. 在闭环摘要中增加:
   - 当前阶段
   - 阻塞原因
   - 推荐动作
4. 对接对象工作台公共协议。

### 交付物

1. 生命周期推荐动作 payload
2. 生命周期闭环摘要

### 验收

1. 生命周期关键对象详情页能直接看到下一步。
2. 页面层不再手工推导动作优先级。

建议工期: `2-3 人天`

---

## Phase 4: 自动化测试与回归守护

### 目标

用自动化测试守住 Phase 1 和 Phase 2 的跨域链路。

### 任务

1. 后端集成测试:
   - 维修完成后的资产回写
   - 处置执行后的资产和财务联动
   - 时间线聚合
2. 前端测试:
   - 生命周期动作栏
   - 推荐动作
   - 时间线渲染
3. 如有需要补 E2E:
   - 资产 -> 维修 -> 恢复
   - 资产 -> 处置 -> 财务凭证

### 验收

1. 主链路自动化测试稳定通过。
2. 新增动作不会破坏既有生命周期入口。

建议工期: `2-3 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/lifecycle/services/lifecycle_action_service.py`
2. `backend/apps/lifecycle/services/closed_loop_service.py`
3. `backend/apps/lifecycle/services/maintenance_service.py`
4. `backend/apps/lifecycle/services/disposal_service.py`
5. `backend/apps/assets/`
6. `backend/apps/finance/viewsets/__init__.py`
7. `backend/apps/projects/services.py`

### 前端

1. `frontend/src/views/dynamic/DynamicDetailPage.vue`
2. 生命周期对象详情相关组件
3. 工作台推荐动作和闭环面板接入

## 6. 测试计划

### 6.1 后端

1. 维修动作和资产状态回写
2. 处置动作和财务联动
3. 推荐动作可用性判断
4. 时间线聚合正确性

### 6.2 前端

1. 生命周期动作栏显示
2. 推荐动作渲染
3. 详情页闭环摘要更新

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 动作越来越多但缺少统一目录 | 容易再次散乱 | Phase 0 先冻结动作目录 |
| 只创建下游对象不回写终态 | 仍然不是闭环 | 每个动作必须定义上游回写规则 |
| 跨域联动把边界做乱 | 生命周期直接侵入其它域 | 用 orchestrator 调用，不把业务规则散在页面里 |
| 时间线无法解释复杂链路 | 用户看不懂结果 | 所有动作必须带 timeline_event 和 target summary |

## 8. 完成标准

1. 生命周期动作不再只负责“创建下游单据”，还能驱动资产和相关域终态收口。
2. 维修和处置链路能形成真正可追踪的闭环。
3. 详情页能明确给出当前阶段和下一步推荐动作。
