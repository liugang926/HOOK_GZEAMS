# 租赁逾期与归还结清闭环实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `leasing_payment_return_closure`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `先统一合同、收款、归还、结清的终态语义，再把 dashboard 和 payments 页收敛为工作台`

## 2. 现状判断

当前租赁域已经有合同、付款、归还、延期能力，但还缺少“逾期催收 + 归还验收 + 费用结清 + 归档”的完整收口。

现状依据:

1. 合同服务已具备:
   - activate
   - suspend
   - terminate
   - complete
   - `backend/apps/leasing/services.py`
2. 租金支付服务已具备:
   - record_payment
   - get_overdue_payments
3. 归还与延期服务已具备:
   - `LeaseReturnService.calculate_charges`
   - `LeaseExtensionService.approve_extension`
4. ViewSet 已具备逾期合同和付款逾期入口:
   - `backend/apps/leasing/viewsets.py`
5. 前端仍保留专门 dashboard 与 payment list:
   - `frontend/src/views/leasing/LeasingDashboard.vue`
   - `frontend/src/router/index.ts`

结论:

1. 租赁域的基础对象和基础动作已经有了。
2. 缺的不是 CRUD，而是“从收租到归还到结清”的工作台与终态约束。

## 3. 实施原则

1. 合同是否完成，不能只看合同状态，要同时看归还、费用和结清状态。
2. 逾期收款必须进入工作台待处理队列，而不只是过滤条件。
3. 归还验收、押金扣减、退款、结清必须纳入同一闭环摘要。
4. 租赁闭环优先纳入统一对象工作台协议，不继续扩独立专页。
5. 合同结束后要能同步资产可用状态或归还结果。

## 4. 分阶段执行

## Phase 0: 租赁终态语义冻结

### 目标

冻结租赁域从合同开始到结清归档的标准阶段。

### 任务

1. 冻结合同主阶段:
   - `draft`
   - `active`
   - `suspended`
   - `expiring_soon`
   - `return_pending`
   - `settlement_pending`
   - `completed`
   - `terminated`
   - `archived`
2. 冻结付款主阶段:
   - `pending`
   - `partial`
   - `paid`
   - `overdue`
   - `waived`
3. 冻结归还主阶段:
   - `scheduled`
   - `inspecting`
   - `charges_calculated`
   - `refund_pending`
   - `closed`
4. 冻结工作台队列:
   - 待收款
   - 已逾期
   - 即将到期
   - 待归还验收
   - 待结清

### 验收

1. 合同、付款、归还闭环状态语义冻结。
2. 完成和结清不再混为一谈。

建议工期: `1-2 人天`

---

## Phase 1: 收租与逾期治理

### 目标

把租金支付从记录动作升级为待处理和催收闭环。

### 任务

1. 在现有 `RentPayment` 基础上补充:
   - 催收动作
   - 催收次数/最后催收时间
   - 逾期原因备注
2. 明确逾期支付流程:
   - 标记逾期
   - 催收
   - 部分支付
   - 豁免
   - 结清
3. 新增工作台队列:
   - 待收款
   - 已逾期
   - 催收中
4. 为 `LeasingContract` 补充收款摘要:
   - 应收
   - 已收
   - 未收
   - 逾期数

### 涉及模块

1. `backend/apps/leasing/services.py`
2. `backend/apps/leasing/viewsets.py`
3. `backend/apps/leasing/models.py`

### 验收

1. 租金逾期可以作为独立待处理事项运营。
2. 合同详情能看到收款进度和逾期风险。

建议工期: `3-4 人天`

---

## Phase 2: 归还验收与费用结算

### 目标

把租赁归还从“计算费用”升级为“验收、扣费、退款、结清”链路。

### 任务

1. 扩展 `LeaseReturn` 闭环动作:
   - 发起验收
   - 记录损坏
   - 计算费用
   - 确认扣款
   - 确认退款
   - 关闭归还单
2. 将现有 `calculate_charges()` 纳入统一闭环状态机。
3. 为合同补充结清前置条件:
   - 资产已归还
   - 归还验收完成
   - 损坏费用确认
   - 押金退款或扣减完成
4. 如有延期申请，结束后自动回到合同闭环路径。

### 验收

1. 归还对象详情页可直接回答“验收是否完成、费用是否结清、是否已退款”。
2. 合同不能在存在未结清归还事项时直接完成。

建议工期: `4-5 人天`

---

## Phase 3: 合同工作台收口

### 目标

将现有 `LeasingDashboard` 和 `RentPaymentList` 的核心能力收敛到统一工作台。

### 任务

1. 为 `LeasingContract` 工作台提供:
   - 摘要卡
   - 即将到期队列
   - 逾期收款队列
   - 待归还验收队列
   - 待结清队列
2. 为 `RentPayment` 工作台提供:
   - 待收款
   - 已逾期
   - 部分支付
   - 豁免待确认
3. 将专页已有统计和列表映射到统一对象工作台协议。
4. 逐步弱化 `/leasing/dashboard` 与 `/leasing/payments` 的独立角色。

### 涉及模块

1. `frontend/src/views/leasing/LeasingDashboard.vue`
2. `frontend/src/views/leasing/RentPaymentList.vue`
3. `frontend/src/router/index.ts`
4. `frontend/src/views/dynamic/DynamicDetailPage.vue`

### 验收

1. 合同和付款对象都能通过统一工作台查看待处理事项。
2. 专页不再承载独占的核心闭环逻辑。

建议工期: `4-5 人天`

---

## Phase 4: 资产回收与归档

### 目标

让租赁闭环影响资产终态，并形成最终归档。

### 任务

1. 合同完成或终止后同步资产可用状态。
2. 归还完成后写入资产历史与可用性摘要。
3. 合同进入 `archived` 前校验:
   - 收款无挂账
   - 归还无未结项
   - 押金结算完成
4. 归档后详情页默认只读。

### 验收

1. 租赁合同关闭后，资产状态与合同终态一致。
2. 系统存在明确的结清与归档出口。

建议工期: `2-3 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/leasing/services.py`
2. `backend/apps/leasing/viewsets.py`
3. `backend/apps/leasing/models.py`
4. `backend/apps/system/viewsets/object_router.py`
5. `backend/apps/system/menu_config.py`

### 前端

1. `frontend/src/views/leasing/LeasingDashboard.vue`
2. `frontend/src/views/leasing/RentPaymentList.vue`
3. `frontend/src/views/dynamic/DynamicDetailPage.vue`
4. 工作台公共组件和 API 客户端接入

## 6. 测试计划

### 6.1 后端

1. 逾期标记与催收动作
2. 部分支付与结清
3. 归还费用计算与关闭
4. 合同结清前置条件校验
5. 资产回收回写

### 6.2 前端

1. 合同工作台摘要和队列
2. 付款逾期状态显示
3. 归还结算面板
4. 专页与工作台跳转兼容

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 合同状态过早完成 | 实际仍有未收款或未退款 | 将“completed”与“settlement_pending”分开 |
| 收款和归还两条线继续分裂 | 用户需要在多个页面来回找信息 | 强制在合同工作台汇总收款与归还摘要 |
| 专页继续增长 | 动态对象页无法接管 | 专页能力逐步映射到统一工作台协议 |
| 资产回收不同步 | 合同结束但资产仍不可用 | Phase 4 明确资产可用性回写规则 |

## 8. 完成标准

1. 租赁域能完整覆盖逾期收款、归还验收、费用结清、归档。
2. `LeasingContract` 和 `RentPayment` 成为可运营的工作台对象。
3. 合同关闭后资产状态和租赁终态一致。
