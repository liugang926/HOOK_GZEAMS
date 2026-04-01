# PHASE7_2_36_LIFECYCLE_FINANCE_ACTIONS_IMPLEMENTATION_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.36 |
| 作者/Agent | Codex |

## 一、实施概述

- 本阶段将 `PurchaseRequest` 和 `AssetReceipt` 的“财务 blocker”升级为可执行动作，用户现在可以直接在对象详情页通过统一动作协议创建采购凭证。
- 新增 `FinanceVoucherService.generate_purchase_voucher_for_assets()`，统一处理采购凭证号生成、默认分录、source trace 归档和同源凭证去重，避免 finance endpoint 与 lifecycle action 出现规则漂移。
- `LifecycleActionService` 补齐两个新动作：`purchase.generate_finance_voucher` 与 `receipt.generate_finance_voucher`，并根据对象状态、已生成资产、待建卡数量、同源已存在凭证做启用/禁用判定。
- `FinanceVoucher` 生成接口改为复用 service，并修复 `FinanceVoucherDetailSerializer` 的继承关系，确保 source trace 字段能稳定返回给动态对象路由。
- 补充对象动作回归测试与财务兼容性测试，覆盖新动作执行、重复生成保护和 source filter 行为。

### 涉及文件

- 后端
  - `backend/apps/finance/serializers/__init__.py`
  - `backend/apps/finance/services.py`
  - `backend/apps/finance/viewsets/__init__.py`
  - `backend/apps/lifecycle/services/lifecycle_action_service.py`
- 测试
  - `backend/apps/system/tests/test_object_router_cross_object_actions.py`
  - `backend/apps/finance/tests/test_api_compat.py`

### 代码行数统计

- 触达文件数：6
- 触达源码体量：3723 行
- 已跟踪文件增量：676 行新增，19 行删除
- 新增文件：1 个
  - `docs/reports/implementation/PHASE7_2_36_LIFECYCLE_FINANCE_ACTIONS_IMPLEMENTATION_REPORT.md`

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| `PurchaseRequest / AssetReceipt` 应能在当前对象内直接推进财务闭环 | 已完成，通过统一对象动作创建凭证 | `backend/apps/lifecycle/services/lifecycle_action_service.py` |
| 采购凭证生成规则需要统一，避免多入口行为漂移 | 已完成，收敛到 `FinanceVoucherService` | `backend/apps/finance/services.py` |
| 所有生成型财务单必须可追溯源单且防止重复生成 | 已完成，落库 source trace 并增加 source-scope 去重 | `backend/apps/finance/services.py` |
| 上游对象生成凭证后应能直达目标对象 | 已完成，动作返回 `target_object_code / target_id / target_url` | `backend/apps/lifecycle/services/lifecycle_action_service.py` |
| 财务兼容层需维持现有对象路由和过滤能力 | 已完成，`generate/asset-purchase` 继续可用，source filter 测试通过 | `backend/apps/finance/viewsets/__init__.py` / `backend/apps/finance/tests/test_api_compat.py` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象路由优先 | 通过 | 新动作继续走 `/api/system/objects/{code}/{id}/actions/{action_code}/execute/` |
| 公共服务层收敛 | 通过 | 采购凭证生成逻辑迁入 `FinanceVoucherService`，未新增旁路入口 |
| 统一 API 响应格式 | 通过 | 动作执行与财务生成接口均返回标准 success/error 结构 |
| English comments only | 通过 | 本阶段新增注释和 docstring 使用英文 |
| Python 语法校验 | 通过 | `python3 -m py_compile` 覆盖本阶段改动文件 |
| Django 定向回归 | 通过 | Docker 容器内对象动作与 finance compat 用例均通过 |

## 四、创建文件清单

- `docs/reports/implementation/PHASE7_2_36_LIFECYCLE_FINANCE_ACTIONS_IMPLEMENTATION_REPORT.md`

## 五、验证记录

- `python3 -m py_compile backend/apps/finance/serializers/__init__.py backend/apps/finance/services.py backend/apps/lifecycle/services/lifecycle_action_service.py backend/apps/finance/viewsets/__init__.py backend/apps/system/tests/test_object_router_cross_object_actions.py backend/apps/finance/tests/test_api_compat.py`
  - 结果：通过
- `docker compose exec -T backend sh -lc 'cd /app && pytest apps/system/tests/test_object_router_cross_object_actions.py -q --create-db'`
  - 结果：`5 passed`
- `docker compose exec -T backend sh -lc 'cd /app && pytest apps/finance/tests/test_api_compat.py -q --reuse-db'`
  - 结果：`17 passed`

## 六、后续建议

1. 将 `PurchaseRequest / AssetReceipt` 的 workbench `recommended_actions` 与新动作编码对齐，让 blocker 卡片可直接触发动作而不只显示建议。
2. 继续把同类财务推进动作扩展到 `DisposalRequest`、`ClaimRecord`、`LeasingContract`，统一复用当前 source trace 与去重协议。
3. 在 `FinanceVoucher` workbench 中直接反向展示“由哪个对象动作生成”，把源单、凭证、ERP 过账三段闭环进一步收口。
