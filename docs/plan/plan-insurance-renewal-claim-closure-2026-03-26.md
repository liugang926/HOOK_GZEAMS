# 保险续保与理赔闭环实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `insurance_renewal_claim_closure`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `先补续保链和理赔链的闭环状态，再把 dashboard 收口为工作台`

## 2. 现状判断

当前保险域已经具备保单、保费、理赔的基础服务，但还缺完整的续保和结案工作台。

现状依据:

1. 保单服务已具备:
   - 激活
   - 取消
   - 临期查询
   - dashboard stats
   - 代码位于 `backend/apps/insurance/services.py`
2. 理赔服务已具备:
   - 审批
   - 驳回
   - 记录赔付
   - 关闭
3. `PolicyRenewalService` 当前仅有空壳:
   - `backend/apps/insurance/services.py`
4. 前端仍保留专门 dashboard 和 claims 页面:
   - `frontend/src/views/insurance/InsuranceDashboard.vue`
   - `frontend/src/router/index.ts`
5. Policy summary 和 dashboard stats 已有局部统计能力:
   - `backend/apps/insurance/viewsets.py`

结论:

1. 保险域的问题不是没有对象，而是续保和理赔链条没有被产品化为闭环运营面板。
2. 当前 dashboard 更像统计页，还不是“待办/异常/结案”工作台。

## 3. 实施原则

1. 保单闭环要覆盖承保、生效、保费、临期、续保、终止。
2. 理赔闭环要覆盖报案、调查、审批、赔付、结案。
3. 临期、未缴保费、待赔付、待结案都必须进入工作台队列。
4. 续保不应只是新建一张保单，要能追溯旧保单与续保批次。
5. 保险对象优先纳入统一工作台协议，而不是继续扩专属 dashboard。

## 4. 分阶段执行

## Phase 0: 续保与理赔语义冻结

### 目标

冻结保险闭环的标准阶段和队列分类。

### 任务

1. 冻结保单主阶段:
   - `draft`
   - `active`
   - `expiring_soon`
   - `renewal_pending`
   - `renewed`
   - `expired`
   - `cancelled`
   - `closed`
2. 冻结理赔主阶段:
   - `reported`
   - `investigating`
   - `approved`
   - `rejected`
   - `paid`
   - `closed`
3. 冻结工作台队列:
   - 临期续保
   - 待缴保费
   - 报案待处理
   - 待审批
   - 待赔付
   - 待结案
4. 冻结保单终态与资产保障状态关系。

### 验收

1. 保单和理赔的闭环状态语义冻结。
2. 工作台队列与对象动作使用统一命名。

建议工期: `1-2 人天`

---

## Phase 1: 续保链补齐

### 目标

把当前空壳 `PolicyRenewalService` 补成可运营的续保流程。

### 任务

1. 实现 `PolicyRenewalService`:
   - 生成续保候选
   - 生成续保记录
   - 审批续保
   - 续保成功后关联新旧保单
2. 为临期保单建立推荐动作:
   - 发起续保
   - 标记不续保
   - 重新报价
3. 为 `InsurancePolicy` 提供闭环摘要:
   - 是否临期
   - 是否存在续保草稿
   - 续保批次信息
4. 明确保单续保后旧保单终态。

### 涉及模块

1. `backend/apps/insurance/services.py`
2. `backend/apps/insurance/models.py`
3. `backend/apps/insurance/viewsets.py`

### 验收

1. 临期保单可生成续保候选和续保记录。
2. 新旧保单之间能追溯续保关系。

建议工期: `3-4 人天`

---

## Phase 2: 理赔链收口

### 目标

把理赔从对象状态流转升级为可运营的赔付与结案闭环。

### 任务

1. 细化理赔处置动作:
   - 受理
   - 调查
   - 审批通过
   - 审批驳回
   - 记录赔付
   - 结案
2. 为 `ClaimRecord` 补闭环摘要:
   - 当前阶段
   - 批准金额
   - 已赔付金额
   - 待结案条件
3. 如理赔与资产维修/损失相关，支持推荐下游动作:
   - 发起维修
   - 发起报废
   - 标记资产补偿
4. 理赔成功或拒赔后的通知与时间线写入。

### 验收

1. 理赔对象详情页能直接回答“卡在哪、是否赔付、何时结案”。
2. 理赔结果能驱动后续处置建议。

建议工期: `3-4 人天`

---

## Phase 3: 保险工作台收口

### 目标

将现有 `InsuranceDashboard` 从统计页升级为工作台范式，并逐步收敛到动态对象入口。

### 任务

1. 为 `InsurancePolicy` 工作台提供:
   - 摘要卡
   - 临期续保队列
   - 未缴保费队列
   - 推荐动作
2. 为 `ClaimRecord` 工作台提供:
   - 报案待处理
   - 待审批
   - 待赔付
   - 待结案
3. 将现有专页的统计卡和列表能力映射到统一工作台协议。
4. 逐步弱化 `/insurance/dashboard` 的独立角色。

### 涉及模块

1. `frontend/src/views/insurance/InsuranceDashboard.vue`
2. `frontend/src/views/dynamic/DynamicDetailPage.vue`
3. `frontend/src/router/index.ts`
4. `backend/apps/system/menu_config.py`

### 验收

1. 保单和理赔都能通过统一工作台显示待处理与异常队列。
2. 保险专页不再承载独占的核心业务能力。

建议工期: `4-5 人天`

---

## Phase 4: 资产保障状态联动

### 目标

让保险闭环影响到资产主数据语义，而不只停留在保险对象内部。

### 任务

1. 保单激活/到期/取消时回写资产保障状态摘要。
2. 理赔赔付完成后记录资产补偿或损失结果。
3. 在资产详情页展示保险保障与理赔摘要。
4. 将关键保险事件写入统一历史或时间线。

### 验收

1. 资产对象能感知当前保障状态。
2. 理赔结果能在资产侧被追踪。

建议工期: `2-3 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/insurance/services.py`
2. `backend/apps/insurance/viewsets.py`
3. `backend/apps/insurance/models.py`
4. `backend/apps/system/viewsets/object_router.py`
5. `backend/apps/system/menu_config.py`

### 前端

1. `frontend/src/views/insurance/InsuranceDashboard.vue`
2. `frontend/src/views/dynamic/DynamicDetailPage.vue`
3. 工作台公共组件接入
4. 保险对象相关 API 封装

## 6. 测试计划

### 6.1 后端

1. 续保候选与续保记录生成
2. 理赔审批与赔付
3. 工作台摘要与队列
4. 资产保障状态联动

### 6.2 前端

1. 保单工作台摘要渲染
2. 理赔队列和详情展示
3. 专页到工作台的兼容跳转

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 续保链一直是空壳 | 保单只能到期，不能运营续保 | Phase 1 优先实现续保服务 |
| dashboard 与工作台长期双轨 | 继续形成双入口分叉 | 专页能力逐步映射到工作台并收敛 |
| 理赔只停留在状态变更 | 用户看不到结案条件 | 必须提供闭环摘要与推荐动作 |
| 资产侧感知不到保险状态 | 业务闭环断裂 | Phase 4 明确保单和理赔回写 |

## 8. 完成标准

1. 保险域具备临期续保、理赔待办、赔付、结案的统一工作台。
2. `PolicyRenewalService` 从空壳升级为真实闭环服务。
3. 资产对象可以感知保险保障和理赔结果。
