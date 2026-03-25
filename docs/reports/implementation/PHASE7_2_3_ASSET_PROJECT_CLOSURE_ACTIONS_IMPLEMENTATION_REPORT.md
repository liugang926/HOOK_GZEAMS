# Phase7.2.3 Asset Project Closure Actions Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M3 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `AssetProject` workbench 补齐“结项”动作，后端新增 `close` custom action，并在项目仍有在用资产时阻止结项。
- 为 `ProjectAsset` 增加跨项目转移后端能力，支持从当前分配记录创建目标项目的新分配，同时将源分配回写为 `transferred`。
- 在 `AssetProject` 资产 panel 上追加“资产回收 / 跨项目转移”行级动作：
  - “资产回收”跳转到 `AssetReturn/create`，通过 `prefill` + `returnTo` 复用 M2 的创建闭环，把用户保存后带回项目工作区。
  - “跨项目转移”在 panel 内弹出目标项目选择框，直接调用 `ProjectAsset.transfer` custom action。
- 为已有 `BusinessObject.menu_config` 增加补丁迁移，确保存量 `AssetProject` workbench 也能显示“结项”动作。
- 补充后端服务测试、workbench action bar 单测和项目资产动作构造单测，并更新报告索引。

- 本阶段定向覆盖文件：14 个
- 本阶段新增文件：6 个
- 定向文件总行数：2817 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| `AssetProject` 工作区追加“结项”动作 | ✅ 已完成 | `backend/apps/system/menu_config.py`、`backend/apps/system/migrations/0047_asset_project_workbench_close_action.py`、`backend/apps/projects/viewsets.py` |
| 项目结项需校验项目资产已处理完毕 | ✅ 已完成 | `backend/apps/projects/services.py`、`backend/apps/projects/tests/test_services.py` |
| 工作区发起资产回收时复用 `returnTo` 创建闭环 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectAssetsPanel.vue`、`frontend/src/components/projects/assetProjectAssetActions.ts` |
| 工作区支持跨项目转移当前项目资产 | ✅ 已完成 | `backend/apps/projects/services.py`、`backend/apps/projects/viewsets.py`、`frontend/src/components/projects/AssetProjectAssetsPanel.vue` |
| 工作区动作回归测试 | ✅ 已完成 | `frontend/src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts`、`frontend/src/components/projects/__tests__/assetProjectAssetActions.spec.ts`、`backend/apps/system/tests/test_asset_project_catalog.py` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 仍通过 `/api/system/objects/{code}/` 和 `/objects/{code}` 工作，没有新增独立业务路由。 |
| 后端复用统一 ViewSet / Service | ✅ | `AssetProjectViewSet`、`ProjectAssetViewSet` 继续继承 `BaseModelViewSetWithBatch`，服务层继续基于 `BaseCRUDService` 扩展。 |
| 工作区能力收敛 | ✅ | “结项”走 runtime workbench toolbar，“资产回收 / 跨项目转移”收敛到 `AssetProjectAssetsPanel`，未新增独立壳页面。 |
| i18n 模块化 | ✅ | 新增动作、对话框和提示文案全部落在 `frontend/src/locales/*/projects.json`。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均使用英文。 |
| 后端语法校验 | ✅ | 通过 `python3 -m py_compile` 定向校验。 |
| 后端 pytest | ⚠️ | 当前环境缺少 `pytest` 模块，无法执行新增 Django 测试。 |
| 前端单元测试 | ✅ | `vitest` 定向 4 个文件、19 个用例全部通过。 |
| 前端定向 lint | ✅ | 新增 panel / helper / 测试文件 `eslint` 通过。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/projects/services.py \
  backend/apps/projects/viewsets.py \
  backend/apps/system/menu_config.py \
  backend/apps/system/migrations/0047_asset_project_workbench_close_action.py \
  backend/apps/projects/tests/test_services.py \
  backend/apps/system/tests/test_asset_project_catalog.py

cd backend && python3 -m pytest \
  apps/projects/tests/test_services.py \
  apps/system/tests/test_asset_project_catalog.py \
  apps/system/tests/test_menu_config_sync.py
# Result: failed in current environment because pytest is not installed.

cd frontend && npm exec vitest -- run \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicFormPage.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts

cd frontend && npm exec eslint \
  src/components/projects/AssetProjectAssetsPanel.vue \
  src/components/projects/assetProjectAssetActions.ts \
  src/components/common/ObjectWorkbenchPanelHost.vue \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/system/migrations/0047_asset_project_workbench_close_action.py` | New | 为存量 `AssetProject` workbench 回填“结项”动作 |
| `backend/apps/projects/tests/test_services.py` | New | 项目结项与跨项目转移服务测试 |
| `frontend/src/components/projects/assetProjectAssetActions.ts` | New | 项目资产回收跳转与目标项目标签 helper |
| `frontend/src/components/projects/__tests__/assetProjectAssetActions.spec.ts` | New | 项目资产动作 helper 单测 |
| `frontend/src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts` | New | workbench action bar 状态门控与 close action 单测 |
| `docs/reports/implementation/PHASE7_2_3_ASSET_PROJECT_CLOSURE_ACTIONS_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 当前“资产回收”动作已经完成 `returnTo` 导航闭环，但 `AssetReturn` 与 `ProjectAsset.return_status` 的业务联动仍可在后续阶段继续收口为真正的项目资产回收闭环。
- 如果后续还要追加“批量资产回收 / 批量跨项目转移”，建议直接在 `AssetProjectAssetsPanel` 上补多选和批量 action，而不是再拆新页面。
- 后端测试文件已补齐，待开发环境安装 `pytest` 后建议第一时间补跑 Django 定向测试，确认对象路由与多组织上下文没有环境差异。
