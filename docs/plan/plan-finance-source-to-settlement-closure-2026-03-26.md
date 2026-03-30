# 财务源单到核销闭环实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `finance_source_to_settlement_closure`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `先统一源单追溯与闭环语义，再扩工作台和异常队列，最后收口核销与归档`

## 2. 现状判断

当前财务域已经具备凭证生命周期和 ERP 异步推送能力，但整体仍偏“凭证对象管理”，距离“源单到终态结算”的经营闭环还有明显缺口。

现状依据:

1. 凭证生命周期服务已具备:
   - `submit`
   - `approve`
   - `reject`
   - `post_voucher`
   - `reverse_voucher`
   - 代码位于 `backend/apps/finance/services.py`
2. ERP 推送已具备异步任务、重试、集成日志和失败提醒:
   - `backend/apps/finance/tasks.py`
   - `backend/apps/finance/viewsets/__init__.py`
3. 财务凭证已具备第一版 workbench 配置:
   - `backend/apps/system/migrations/0045_finance_voucher_workbench_menu_config.py`
4. 对象路由已兼容 `/finance/vouchers` -> `/objects/FinanceVoucher`:
   - `frontend/src/router/index.ts`
5. 当前已具备财务 summary，但仍以凭证统计为主:
   - `backend/apps/finance/viewsets/__init__.py`

结论:

1. 现有财务域的“技术闭环”已经初步存在。
2. 真正缺的是“源单 -> 凭证 -> 过账 -> 推送 -> 异常 -> 核销 -> 归档”的统一视图和统一队列。

## 3. 实施原则

1. 不再把财务闭环理解为“凭证 posted 就结束”。
2. 财务对象必须能追溯上游来源单据和下游 ERP/核销终态。
3. 推送失败、重试、未核销、已冲销等都属于可运营例外，而不是日志细节。
4. 财务工作台优先建立在现有 `FinanceVoucher` workbench 基础上，不再新建专属页面体系。
5. 所有队列和闭环状态优先通过统一对象路由和工作台协议输出。

## 4. 分阶段执行

## Phase 0: 闭环语义与状态冻结

### 目标

冻结财务闭环在业务视角下的标准阶段，避免“posted 是否等于完成”继续混乱。

### 任务

1. 冻结财务主阶段:
   - `draft`
   - `submitted`
   - `approved`
   - `posted`
   - `push_pending`
   - `push_failed`
   - `synced`
   - `reconciled`
   - `reversed`
   - `archived`
2. 冻结源单追溯语义:
   - `source_object_code`
   - `source_record_id`
   - `source_business_type`
   - `source_record_no`
3. 冻结异常队列语义:
   - 待审核
   - 待过账
   - 待推送
   - 推送失败
   - 已推送未核销
   - 已冲销待归档
4. 冻结结案条件:
   - 上游来源明确
   - 凭证状态终态明确
   - ERP 同步结果明确
   - 核销或豁免结论明确

### 验收

1. 财务闭环状态语义冻结。
2. 工作台和对象动作使用统一状态字典。

建议工期: `1-2 人天`

---

## Phase 1: 源单追溯与闭环聚合

### 目标

让 `FinanceVoucher` 不再是孤立对象，而是能显示来源、同步状态和当前闭环位置。

### 任务

1. 扩展凭证与来源追溯协议:
   - 为凭证补齐统一来源字段或统一 source payload 组装
2. 整理现有生成入口:
   - 资产采购生成凭证
   - 折旧生成凭证
   - 处置生成凭证
   - 现有入口在 `backend/apps/finance/viewsets/__init__.py`
3. 新增财务闭环聚合服务:
   - `backend/apps/finance/services/finance_closure_service.py`
4. 新增对象级闭环摘要接口:
   - `GET /api/system/objects/FinanceVoucher/{id}/closure/`
5. 新增工作台摘要与异常队列接口:
   - 已有 workbench 基础上继续扩展

### 交付物

1. 源单追溯字段或统一追溯 payload
2. 财务闭环聚合服务
3. 凭证闭环摘要接口
4. 财务异常队列接口

### 验收

1. 任一凭证都能看到来源对象和当前闭环阶段。
2. 生成类凭证能追溯到上游业务记录。
3. 推送状态不再只存在于 integration log 中。

建议工期: `3-4 人天`

---

## Phase 2: ERP 异常处理与核销收口

### 目标

把 ERP 推送失败和未核销状态从“日志问题”升级为“经营待办”。

### 任务

1. 补充财务异常动作:
   - `push`
   - `retry_push`
   - `mark_reconciled`
   - `mark_writeoff_exempt`
   - `archive_closure`
2. 对接现有异步任务:
   - `backend/apps/finance/tasks.py`
3. 对接现有集成日志和同步任务:
   - IntegrationLog
   - IntegrationSyncTask
4. 明确失败重试和成功回写后的状态流转。
5. 为失败提醒建立工作台入口，而不只停留在通知中心。

### 交付物

1. 财务异常动作协议
2. 推送失败与未核销队列
3. 核销/豁免/归档动作

### 验收

1. 财务人员能直接在工作台处理失败重试和核销。
2. 推送失败凭证可以从“失败”推进到“已同步/已豁免/已归档”。

建议工期: `3-4 人天`

---

## Phase 3: 财务工作台与来源单据联动

### 目标

把当前 `FinanceVoucher` 的专项 workbench 扩成完整财务闭环工作台。

### 任务

1. 扩展现有财务 workbench:
   - 摘要卡
   - 推送状态面板
   - 集成日志面板
   - 核销状态面板
   - 推荐动作
2. 在来源单据详情页显示:
   - 已生成凭证状态
   - 财务终态
   - 跳转到凭证
3. 接入动态详情页公共工作台协议。
4. 统一 `/finance/vouchers` 和 `/objects/FinanceVoucher` 的体验语义。

### 交付物

1. 增强版 `FinanceVoucher` 工作台
2. 来源单据的财务闭环摘要
3. 工作台推荐动作和风险队列

### 验收

1. 财务对象详情页能直接回答“源自哪里、推送状态如何、是否已核销、下一步做什么”。
2. 上游单据可看到对应财务终态，而不是只看到是否生成凭证。

建议工期: `4-5 人天`

---

## Phase 4: 冲销与归档终态

### 目标

把财务终态补完整，不让流程停在“已过账/已推送”。

### 任务

1. 把 `reverse_voucher()` 也纳入闭环工作台。
2. 定义冲销后的归档规则:
   - 原凭证
   - 冲销凭证
   - 来源单据状态
3. 明确归档条件与只读策略。
4. 对管理统计输出:
   - 已同步未核销
   - 已冲销
   - 已归档

### 交付物

1. 财务终态规则
2. 冲销与归档策略

### 验收

1. 财务闭环可走到“核销/豁免/冲销/归档”终态。
2. 不再存在“业务上已结束但系统仍停在 posted”的灰色状态。

建议工期: `2-3 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/finance/services.py`
2. `backend/apps/finance/tasks.py`
3. `backend/apps/finance/viewsets/__init__.py`
4. `backend/apps/system/viewsets/object_router.py`
5. `backend/apps/system/migrations/0045_finance_voucher_workbench_menu_config.py`
6. `backend/apps/finance/services/`
   - 新增财务闭环聚合服务

### 前端

1. `frontend/src/views/dynamic/DynamicDetailPage.vue`
2. `frontend/src/api/dynamic.ts`
3. `frontend/src/components/common/`
   - 复用工作台摘要、队列、闭环面板
4. 与财务工作台面板相关组件

## 6. 测试计划

### 6.1 后端

1. 源单到凭证追溯测试
2. 推送失败与重试测试
3. 核销与豁免状态测试
4. 冲销与归档测试
5. 工作台摘要与异常队列测试

### 6.2 前端

1. 财务工作台摘要渲染
2. 推送状态面板
3. 集成日志面板
4. 推荐动作与异常队列交互

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 仍停留在凭证对象视角 | 看不到上游来源和下游终态 | 强制建立 source/closure 统一摘要 |
| ERP 失败仍只在日志里 | 业务用户无法追踪 | 失败队列进入工作台摘要和推荐动作 |
| 核销定义不清 | 各业务域自行理解终态 | Phase 0 冻结财务终态语义 |
| workbench 继续对象专属硬编码 | 难以扩到其他闭环对象 | 统一复用工作台运行时协议 |

## 8. 完成标准

1. `FinanceVoucher` 能完整展示来源、推送、核销、冲销、归档状态。
2. 财务异常从日志问题升级为可运营的工作台待办。
3. 上游来源单据可以感知财务终态，而不是只知道是否生成了凭证。
