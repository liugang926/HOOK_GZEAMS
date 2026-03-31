# PHASE7_2_33_ASSET_FINANCE_TRACE_AND_PROJECT_CLOSURE_IMPLEMENTATION_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.33 |
| 作者/Agent | Codex |

## 一、实施概述

- 本阶段围绕“用户能否在一个上下文中完成闭环”补齐两段关键链路：
  - `Asset -> FinanceVoucher` 源单追溯与财务终态回写视图。
  - `AssetProject` 结项前的资产占用与待确认归还单约束。
- 财务侧将生成型凭证的来源对象、来源单号、关联资产索引写入 `FinanceVoucher.custom_fields`，并在序列化层、过滤层和工作台摘要中统一暴露。
- 资产侧 closure summary 已纳入财务联动指标，用户在资产详情页可直接看到关联凭证总数、未完成凭证数、最近凭证状态及来源验收/请购信息。
- 项目侧关闭规则新增“待处理归还单”拦截，避免出现“项目已关闭，但仍有待确认归还单悬空”的业务断点。
- 统一 closure summary 已同步补强 `AssetProject` 的“Pending asset returns”阶段语义，与工作台 closure panel 展示保持一致。

### 涉及文件

- 后端
  - `backend/apps/finance/viewsets/__init__.py`
  - `backend/apps/finance/serializers/__init__.py`
  - `backend/apps/finance/filters/__init__.py`
  - `backend/apps/projects/services.py`
  - `backend/apps/system/services/object_closure_binding_service.py`
  - `backend/apps/system/menu_config.py`
- 测试
  - `backend/apps/finance/tests/test_api_compat.py`
  - `backend/apps/projects/tests/test_api.py`
  - `backend/apps/projects/tests/test_services.py`
  - `backend/apps/system/tests/test_menu_config_sync.py`
  - `backend/apps/system/tests/test_object_closure_binding_service.py`
- 前端
  - `frontend/src/locales/en-US/finance.json`
  - `frontend/src/locales/zh-CN/finance.json`
  - `frontend/src/types/finance.ts`

### 代码行数统计

- 触达文件数：14
- 触达源码体量：8075 行
- 已跟踪文件增量：1268 行新增，27 行删除
- 新增文件：2 个
  - `backend/apps/system/services/object_closure_binding_service.py`
  - `backend/apps/system/tests/test_object_closure_binding_service.py`

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| `PurchaseRequest / AssetReceipt / Asset <-> FinanceVoucher` 需可追溯源单，源单可见财务终态 | 已实现（当前先完成 `Asset -> FinanceVoucher` 主链路） | `backend/apps/finance/viewsets/__init__.py` / `backend/apps/finance/serializers/__init__.py` / `backend/apps/finance/filters/__init__.py` / `backend/apps/system/services/object_closure_binding_service.py` |
| `FinanceVoucher` 升级为源单到结算闭环对象，工作台展示来源单据 | 已实现 | `backend/apps/system/menu_config.py` / `frontend/src/types/finance.ts` / `frontend/src/locales/en-US/finance.json` / `frontend/src/locales/zh-CN/finance.json` |
| `Asset` 详情页可直接看财务终态，不必进入日志页 | 已实现（通过 closure summary + Asset workbench summary/queue） | `backend/apps/system/services/object_closure_binding_service.py` / `backend/apps/system/menu_config.py` |
| `AssetProject -> ProjectAsset -> return/transfer -> project close`，项目关闭前必须校验资产占用是否收回 | 已实现，并增加待确认归还单拦截 | `backend/apps/projects/services.py` / `backend/apps/projects/tests/test_services.py` / `backend/apps/projects/tests/test_api.py` |
| closure summary 与工作台 closure panel 语义保持一致 | 已实现 | `backend/apps/system/services/object_closure_binding_service.py` / `backend/apps/system/tests/test_object_closure_binding_service.py` / `backend/apps/system/tests/test_menu_config_sync.py` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象路由优先 | 通过 | 财务、项目关闭与工作台仍使用 `/api/system/objects/{code}/...` 统一入口 |
| 统一 API 响应格式 | 通过 | 项目关闭失败继续走 `BaseResponse.validation_error` 标准结构 |
| 服务层复用公共基类 | 通过 | `AssetProjectService` 继续继承 `BaseCRUDService`，未引入旁路逻辑 |
| English comments only | 通过 | 本阶段新增代码未引入中文注释 |
| i18n 一致性 | 通过 | `npm run i18n:parity --changed` 结果为 0 issue |
| Python 语法校验 | 通过 | `python3 -m py_compile` 覆盖本阶段后端改动文件 |
| 后端自动化测试 | 部分通过 | 已补充测试用例，但当前环境缺少 `django/pytest`，未能执行 Django `pytest` |

## 四、创建文件清单

- `backend/apps/system/services/object_closure_binding_service.py`
- `backend/apps/system/tests/test_object_closure_binding_service.py`
- `docs/reports/implementation/PHASE7_2_33_ASSET_FINANCE_TRACE_AND_PROJECT_CLOSURE_IMPLEMENTATION_REPORT.md`

## 五、后续建议

- 将 `PurchaseRequest` 与 `AssetReceipt` 也纳入 closure summary，补齐“源单视角直接看到财务是否落账”的上游闭环。
- 将 `AssetProject` 工作台的关闭动作可见性从“仅按状态”升级为“按 closure metrics + blocker”动态控制，减少无效点击。
- 在当前开发环境补齐 `django/pytest` 依赖，尽快把项目关闭和财务追溯用例纳入可执行回归。
