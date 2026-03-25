# Phase7.2.2 Asset Project Workspace Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M2 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `AssetProject` 补齐 runtime `workbench` 默认配置，统一将 `/objects/AssetProject` 作为项目工作区正式入口，并通过迁移回填已存在 `BusinessObject.menu_config`。
- 在统一动态详情页中新增“项目资产”“项目成员”两个 detail panel，直接复用通用 `ObjectWorkbenchPanelHost` 承载项目相关数据与跳转动作。
- 打通 `/objects/AssetProject` 前端闭环：列表行级动作可跳转到按项目过滤的 `ProjectAsset` / `ProjectMember` 列表，detail panel 内可继续进入列表、详情或发起带 `project` 预填充的创建流程。
- 为动态表单新增 `prefill_*` / `returnTo` 查询参数支持，保证从项目工作区发起的新增流程能够自动带入项目上下文并在保存后返回项目详情页。
- 补充 AssetProject 专项中英文字典、动态页面工作区文案与定向单元测试，覆盖详情 workbench、列表行级动作和创建页预填充。

- 本阶段定向覆盖文件：22 个
- 本阶段新增文件：7 个
- 定向文件总行数：4337 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| `AssetProject` 统一工作区页面收敛到 `/objects/AssetProject` | ✅ 已完成 | `backend/apps/system/menu_config.py`、`backend/apps/system/migrations/0046_asset_project_workbench_menu_config.py`、`frontend/src/views/dynamic/workspace/dynamicListWorkspaceModel.ts`、`frontend/src/views/dynamic/workspace/useDynamicDetailWorkspace.ts` |
| 项目资产 / 成员 detail panel | ✅ 已完成 | `frontend/src/components/projects/AssetProjectAssetsPanel.vue`、`frontend/src/components/projects/AssetProjectMembersPanel.vue`、`frontend/src/components/common/ObjectWorkbenchPanelHost.vue` |
| `/objects/AssetProject` 前端交互闭环 | ✅ 已完成 | `frontend/src/views/dynamic/workspace/useDynamicListInteractions.ts`、`frontend/src/views/dynamic/workspace/useDynamicFormController.ts`、`frontend/src/views/dynamic/workspace/dynamicFormPrefill.ts` |
| 项目工作区 i18n 与菜单/runtime 契约补齐 | ✅ 已完成 | `frontend/src/locales/en-US/projects.json`、`frontend/src/locales/zh-CN/projects.json`、`frontend/src/locales/en-US/index.ts`、`frontend/src/locales/zh-CN/index.ts` |
| 回归测试覆盖工作区动作、detail panel 与创建预填充 | ✅ 已完成 | `backend/apps/system/tests/test_asset_project_catalog.py`、`backend/apps/system/tests/test_menu_config_sync.py`、`frontend/src/__tests__/unit/views/dynamic/DynamicFormPage.spec.ts`、`frontend/src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts`、`frontend/src/__tests__/unit/views/dynamic/DynamicListPage.search.spec.ts` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 未新增独立项目前端/后端业务路由，继续通过 `/api/system/objects/{code}/` 与 `/objects/{code}` 收敛。 |
| 通用工作区基座复用 | ✅ | 资产/成员面板通过通用 `workbench` 配置和 `ObjectWorkbenchPanelHost` 注入，没有扩散新的专页壳子。 |
| 查询参数预填充能力 | ✅ | 新增通用 `prefill_*` / `returnTo` 机制，可复用于后续对象工作区创建闭环。 |
| i18n 模块化 | ✅ | 新增 `projects.json` 中英文资源，并接入 locale index。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均为英文。 |
| 后端语法校验 | ✅ | 通过 `PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile ...` 校验。 |
| 前端定向单元测试 | ✅ | 4 个 `vitest` 文件共 22 个用例通过。 |
| 前端定向 lint | ✅ | 项目新增 panel / 预填充 / 详情工作区关键文件 `eslint` 通过，无 error。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/system/menu_config.py \
  backend/apps/system/migrations/0046_asset_project_workbench_menu_config.py \
  backend/apps/system/tests/test_asset_project_catalog.py \
  backend/apps/system/tests/test_menu_config_sync.py

cd frontend && npm exec vitest -- run \
  src/__tests__/unit/views/dynamic/DynamicFormPage.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicListPage.search.spec.ts \
  src/views/dynamic/workspace/dynamicListWorkspaceModel.test.ts

cd frontend && npm exec eslint \
  src/views/dynamic/DynamicFormPage.vue \
  src/components/projects/AssetProjectAssetsPanel.vue \
  src/components/projects/AssetProjectMembersPanel.vue \
  src/__tests__/unit/views/dynamic/DynamicFormPage.spec.ts \
  src/views/dynamic/workspace/useDynamicDetailWorkspace.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/system/migrations/0046_asset_project_workbench_menu_config.py` | New | 回填 `AssetProject` workbench 与正式入口 |
| `frontend/src/views/dynamic/workspace/dynamicFormPrefill.ts` | New | 动态表单通用预填充 / 返回路径解析 |
| `frontend/src/components/projects/AssetProjectAssetsPanel.vue` | New | 项目资产 detail panel |
| `frontend/src/components/projects/AssetProjectMembersPanel.vue` | New | 项目成员 detail panel |
| `frontend/src/locales/en-US/projects.json` | New | 项目工作区英文文案 |
| `frontend/src/locales/zh-CN/projects.json` | New | 项目工作区中文文案 |
| `docs/reports/implementation/PHASE7_2_2_ASSET_PROJECT_WORKSPACE_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- Phase 7.2-M3 可继续在 `AssetProject` workbench 上追加“结项 / 资产回收 / 跨项目转移”动作，并复用本阶段的 `returnTo` 创建闭环。
- 若后续要保留历史 `/projects` 菜单或书签，可在 router alias 层补一层 legacy redirect，与当前 `workbench.legacy_aliases` 保持一致。
- 当前只做了定向 lint；若要恢复全量 `eslint` / `typecheck:app` 绿灯，仍需继续清理动态工作区相关存量 `no-explicit-any` 和测试桩 warning。
