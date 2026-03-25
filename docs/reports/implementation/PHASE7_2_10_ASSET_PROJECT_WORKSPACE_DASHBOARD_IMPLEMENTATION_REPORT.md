# Phase7.2.10 Asset Project Workspace Dashboard Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M10 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `AssetProject` 新增统一聚合接口 `workspace_dashboard`，把项目基础信息、资产统计、成员统计和归还统计收口成一个工作区总览协议。
- `AssetProject` workbench 新增 overview panel，并通过菜单配置和 migration 将该面板插入详情页首位，作为项目详情的默认总览入口。
- 前端新增 `AssetProjectOverviewPanel`，基于单次请求渲染项目状态、时间线、预算快照，以及资产 / 成员 / 回收三类摘要卡片。
- 保持现有资产、成员、待确认归还、回收历史 panel 的取数逻辑不变，先完成“总览协议”接入，再为下一阶段的逐步收敛保留兼容空间。
- 同步补齐后端 service/API 回归、菜单配置回归、前端单测和导航断言，并更新中英文文案与报告索引。

- 本阶段定向覆盖文件：16 个
- 本阶段新增文件：4 个
- 定向文件总行数：3922 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 项目工作区需要统一总览协议，聚合项目 / 资产 / 成员 / 回收摘要 | ✅ 已完成 | `backend/apps/projects/services.py`、`backend/apps/projects/viewsets.py` |
| `AssetProject` 详情工作区需要新增 overview panel 作为首屏摘要入口 | ✅ 已完成 | `backend/apps/system/menu_config.py`、`backend/apps/system/migrations/0050_asset_project_workbench_overview_panel.py`、`frontend/src/components/projects/AssetProjectOverviewPanel.vue` |
| workbench 组件宿主需识别新的项目总览 panel | ✅ 已完成 | `frontend/src/components/common/ObjectWorkbenchPanelHost.vue` |
| 统一对象详情导航和菜单配置回归需要覆盖新的 panel 顺序 | ✅ 已完成 | `backend/apps/system/tests/test_asset_project_catalog.py`、`backend/apps/system/tests/test_menu_config_sync.py`、`frontend/src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts` |
| 项目总览文案与阶段报告需要完成归档 | ✅ 已完成 | `frontend/src/locales/en-US/projects.json`、`frontend/src/locales/zh-CN/projects.json`、`docs/reports/implementation/PHASE7_2_10_ASSET_PROJECT_WORKSPACE_DASHBOARD_IMPLEMENTATION_REPORT.md`、`docs/reports/README.md` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 总览接口通过 `/api/system/objects/AssetProject/{id}/workspace_dashboard/` 暴露，没有新增独立业务路由。 |
| 工作区收敛 | ✅ | overview 以 detail panel 形式挂入 `AssetProject` 统一工作区，没有新增分叉页面。 |
| 菜单 / workbench 配置一致性 | ✅ | 默认配置和迁移数据都已插入 `project_overview`，并放在 detail panels 首位。 |
| i18n 模块化 | ✅ | 新增文案继续落在 `frontend/src/locales/*/projects.json`。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均为英文。 |
| 后端语法校验 | ✅ | 目标 Python 文件 `py_compile` 通过。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端单元测试 | ✅ | `vitest` 定向 7 个文件、24 个用例通过。 |
| 前端定向 lint | ⚠️ | 目标文件无 error；测试桩文件仍有既有 `vue/one-component-per-file` warnings。 |
| Locale JSON 校验 | ✅ | 中英文 `projects.json` 解析通过。 |
| Django 运行态测试 | ⚠️ | 本地环境未执行 Django 运行态测试，新增 API 用例已落库。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/projects/services.py \
  backend/apps/projects/viewsets.py \
  backend/apps/projects/tests/test_services.py \
  backend/apps/projects/tests/test_api.py \
  backend/apps/system/menu_config.py \
  backend/apps/system/tests/test_asset_project_catalog.py \
  backend/apps/system/tests/test_menu_config_sync.py \
  backend/apps/system/migrations/0050_asset_project_workbench_overview_panel.py

cd frontend && npm run typecheck:app

cd frontend && npm exec vitest -- run \
  src/components/projects/__tests__/AssetProjectOverviewPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts

cd frontend && npm exec eslint \
  src/components/projects/AssetProjectOverviewPanel.vue \
  src/components/projects/__tests__/AssetProjectOverviewPanel.spec.ts \
  src/components/common/ObjectWorkbenchPanelHost.vue \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts

python3 - <<'PY'
import json
for path in [
  'frontend/src/locales/en-US/projects.json',
  'frontend/src/locales/zh-CN/projects.json',
]:
    with open(path, 'r', encoding='utf-8') as f:
        json.load(f)
PY
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/system/migrations/0050_asset_project_workbench_overview_panel.py` | New | 为已存在的 `AssetProject` workbench 数据插入 overview panel |
| `frontend/src/components/projects/AssetProjectOverviewPanel.vue` | New | 项目工作区总览 panel |
| `frontend/src/components/projects/__tests__/AssetProjectOverviewPanel.spec.ts` | New | 项目总览 panel 单测 |
| `docs/reports/implementation/PHASE7_2_10_ASSET_PROJECT_WORKSPACE_DASHBOARD_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步可以把 overview payload 继续扩成“项目工作区共享协议”，把资产 / 成员 / 回收列表面板的头部统计也逐步改为复用这一接口，减少重复请求。
- 当前总览先聚焦摘要展示，后续可补项目级 SLA、预算偏差和成员权限热区等更强的管理指标。
- 如果后续继续推进 `AssetProject` 深化，优先建议把 `workspace_dashboard` 再向异步任务、关闭前校验和项目生命周期事件流扩展。
