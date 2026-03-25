# Phase7.2.4 Asset Project Return Closure Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M4 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `ReturnItem` 新增 `project_allocation` 显式关联，确保从项目工作区发起的资产回收可以把 `AssetReturn` 与 `ProjectAsset` 绑定到同一条业务链路。
- 在 `AssetReturnService` 中补齐项目分配解析逻辑：创建 / 更新归还单时优先读取 `project_allocation_id`，没有显式上下文时则自动匹配唯一在用的项目分配。
- 在归还确认阶段，联动调用 `ProjectAssetService.mark_returned()`，同步回写 `ProjectAsset.return_status=returned`、`actual_return_date` 和操作备注，并触发项目汇总指标刷新。
- 前端项目工作区回收入口追加 `project_allocation_id` 预填充，使 `/objects/AssetReturn/create` 不再只是“跳过去”，而是能回写到正确的项目资产分配记录。
- 补充项目分配回写的后端服务 / API 测试和前端 helper 单测，并更新报告索引。

- 本阶段定向覆盖文件：11 个
- 本阶段新增文件：2 个
- 定向文件总行数：6606 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 项目工作区发起资产回收需带上项目分配上下文 | ✅ 已完成 | `frontend/src/components/projects/assetProjectAssetActions.ts`、`frontend/src/components/projects/__tests__/assetProjectAssetActions.spec.ts` |
| `AssetReturn` 与 `ProjectAsset.return_status` 建立真实业务联动 | ✅ 已完成 | `backend/apps/assets/services/operation_service.py`、`backend/apps/projects/services.py` |
| 归还确认后同步更新项目资产状态与项目汇总 | ✅ 已完成 | `backend/apps/assets/services/operation_service.py`、`backend/apps/projects/services.py`、`backend/apps/projects/models.py` |
| 归还明细保留项目分配审计关联 | ✅ 已完成 | `backend/apps/assets/models.py`、`backend/apps/assets/migrations/0011_returnitem_project_allocation.py`、`backend/apps/assets/serializers/operation.py` |
| 回收闭环专项测试 | ✅ 已完成 | `backend/apps/assets/tests/test_operation_models.py`、`backend/apps/assets/tests/test_api.py`、`backend/apps/projects/tests/test_services.py` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 继续复用 `/objects/AssetReturn` 与 `/objects/AssetProject`，没有新增独立业务路由。 |
| 公共基类继承 | ✅ | 本阶段未引入新的脱离基类的模型 / 服务 / ViewSet。 |
| 业务联动收敛到服务层 | ✅ | 项目分配回写逻辑下沉到 `AssetReturnService` + `ProjectAssetService`，没有把状态同步散落到前端。 |
| 审计可追溯性 | ✅ | `ReturnItem.project_allocation` 为归还单与项目分配建立显式关联。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均使用英文。 |
| 后端语法校验 | ✅ | 目标 Python 文件 `py_compile` 通过。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端定向单测 | ✅ | `vitest` 定向 3 个文件、11 个用例通过。 |
| 前端定向 lint | ✅ | 目标 helper / spec 文件 `eslint` 通过。 |
| Django 运行态测试 | ⚠️ | 本轮未执行，新增测试已落库。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/assets/models.py \
  backend/apps/assets/serializers/operation.py \
  backend/apps/assets/services/operation_service.py \
  backend/apps/assets/tests/test_operation_models.py \
  backend/apps/assets/tests/test_api.py \
  backend/apps/assets/migrations/0011_returnitem_project_allocation.py \
  backend/apps/projects/services.py \
  backend/apps/projects/tests/test_services.py

cd frontend && npm run typecheck:app

cd frontend && npm exec vitest -- run \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicFormPage.spec.ts

cd frontend && npm exec eslint \
  src/components/projects/assetProjectAssetActions.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/assets/migrations/0011_returnitem_project_allocation.py` | New | 为归还明细补齐 `project_allocation` 关联字段 |
| `docs/reports/implementation/PHASE7_2_4_ASSET_PROJECT_RETURN_CLOSURE_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步建议把 `AssetReturn` 的确认动作也挂进统一工作区 action bar，让项目工作区可以直接查看并推进待确认归还单。
- 如果后续支持“共享资产一键多项目归还”，需要在当前 `ReturnItem.project_allocation` 单条关联之上设计批量拆分或多对多映射，而不是复用模糊自动匹配。
- 当前回收联动已经闭环，但 Django 运行态测试还没有在本机执行；具备后端测试环境后，优先补跑 `assets` 和 `projects` 的定向测试。
