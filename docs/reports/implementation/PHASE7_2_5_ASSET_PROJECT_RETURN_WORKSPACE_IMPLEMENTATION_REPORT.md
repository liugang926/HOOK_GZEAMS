# Phase7.2.5 Asset Project Return Workspace Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M5 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `AssetProject` 工作区新增“待确认归还单” panel，将项目回收后的 `AssetReturn` 队列直接挂到统一 detail workbench 中。
- 为 `AssetReturn` 后端过滤能力补齐 `project` 参数，支持通过 `items.project_allocation.project` 反查当前项目下的归还单。
- 在项目工作区内支持直接确认归还单，无需再切回资产操作模块列表手动检索待确认单据。
- 为存量 `AssetProject.menu_config.workbench` 增加补丁迁移，确保历史环境同步出现新的 returns panel。
- 补充前端 panel 单测、动态详情导航断言、以及后端项目过滤 API 回归测试，并更新报告索引。

- 本阶段定向覆盖文件：13 个
- 本阶段新增文件：3 个
- 定向文件总行数：4370 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 项目工作区聚合项目回收后的待确认归还单 | ✅ 已完成 | `backend/apps/system/menu_config.py`、`backend/apps/system/migrations/0048_asset_project_workbench_returns_panel.py`、`frontend/src/components/projects/AssetProjectReturnsPanel.vue` |
| 归还单支持按项目上下文过滤 | ✅ 已完成 | `backend/apps/assets/filters/operation.py`、`backend/apps/assets/tests/test_api.py` |
| 项目工作区内直接推进归还确认 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectReturnsPanel.vue` |
| workbench 注册与 runtime 导航断言更新 | ✅ 已完成 | `frontend/src/components/common/ObjectWorkbenchPanelHost.vue`、`frontend/src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts` |
| 项目工作区 returns panel 文案与回归测试 | ✅ 已完成 | `frontend/src/locales/en-US/projects.json`、`frontend/src/locales/zh-CN/projects.json`、`frontend/src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 继续通过 `/objects/AssetProject` 与 `/objects/AssetReturn` 收敛，没有新增独立业务路由。 |
| 工作区能力继续收敛 | ✅ | 待确认归还单通过 `detail_panels` 注入到统一 workbench，没有扩散新的专页壳。 |
| 后端过滤逻辑复用既有 ViewSet/Filter | ✅ | 只在 `AssetReturnFilter` 扩展 `project` 过滤，没有破坏统一 CRUD 入口。 |
| i18n 模块化 | ✅ | 新增文案仍落在 `frontend/src/locales/*/projects.json`。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均使用英文。 |
| 后端语法校验 | ✅ | 目标 Python 文件 `py_compile` 通过。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端单元测试 | ✅ | `vitest` 定向 4 个文件、17 个用例通过。 |
| 前端定向 lint | ⚠️ | 目标文件无 error；测试桩文件存在 `vue/one-component-per-file` warnings。 |
| Django 运行态测试 | ⚠️ | 本轮未执行，新增测试已落库。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/assets/filters/operation.py \
  backend/apps/assets/tests/test_api.py \
  backend/apps/system/menu_config.py \
  backend/apps/system/tests/test_asset_project_catalog.py \
  backend/apps/system/tests/test_menu_config_sync.py \
  backend/apps/system/migrations/0048_asset_project_workbench_returns_panel.py

cd frontend && npm run typecheck:app

cd frontend && npm exec vitest -- run \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts

cd frontend && npm exec eslint \
  src/components/projects/AssetProjectReturnsPanel.vue \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts \
  src/components/common/ObjectWorkbenchPanelHost.vue \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/system/migrations/0048_asset_project_workbench_returns_panel.py` | New | 为存量 `AssetProject` workbench 回填 returns panel |
| `frontend/src/components/projects/AssetProjectReturnsPanel.vue` | New | 项目工作区待确认归还单 panel |
| `frontend/src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts` | New | returns panel 单测 |
| `docs/reports/implementation/PHASE7_2_5_ASSET_PROJECT_RETURN_WORKSPACE_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步建议把 `AssetReturn` 的 reject / 补充原因也做成 panel 内动作，彻底闭环“查看、确认、驳回”三类项目归还处理。
- 如果后续项目规模较大，建议再补一个 `AssetReturn` 的已确认历史 panel 或统计卡，避免当前只有待确认队列、缺少项目回收历史视角。
- 后端过滤与前端 panel 已完成静态和单测验证，待具备 Django 测试环境后，优先补跑 `assets/tests/test_api.py` 中的项目过滤与确认联动用例。
