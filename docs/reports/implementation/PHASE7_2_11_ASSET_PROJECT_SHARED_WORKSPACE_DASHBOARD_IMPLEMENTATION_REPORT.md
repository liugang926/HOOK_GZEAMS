# Phase7.2.11 Asset Project Shared Workspace Dashboard Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M11 |
| 作者/Agent | Codex |

## 一、实施概述

- 将 `AssetProject workspace_dashboard` 从 overview panel 的单点依赖，升级为 `ObjectWorkbenchPanelHost` 统一拉取并分发的共享摘要协议。
- `AssetProjectOverviewPanel` 不再在工作区内单独请求 `workspace_dashboard`；当宿主提供共享摘要时，panel 直接消费共享数据并通过 `refresh-requested` 触发统一刷新。
- `AssetProjectAssetsPanel`、`AssetProjectMembersPanel`、`AssetProjectReturnsPanel`、`AssetProjectReturnHistoryPanel` 的头部统计与摘要卡片已切到共享 `workspace_dashboard`，不再各自维护独立总数口径。
- 补充 workbench 宿主单测，以及 overview / assets / returns panel 的共享摘要回归验证，确保工作区内只保留一条总览摘要数据源。

- 本阶段定向覆盖文件：11 个
- 本阶段新增文件：2 个
- 定向文件总行数：3568 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 项目工作区摘要协议需要从单 panel 扩展为工作区共享协议 | ✅ 已完成 | `frontend/src/components/common/ObjectWorkbenchPanelHost.vue` |
| overview panel 需复用宿主共享摘要，避免重复请求 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectOverviewPanel.vue` |
| 资产 / 成员 / 回收 panel 头部统计需复用统一工作区摘要 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectAssetsPanel.vue`、`frontend/src/components/projects/AssetProjectMembersPanel.vue`、`frontend/src/components/projects/AssetProjectReturnsPanel.vue`、`frontend/src/components/projects/AssetProjectReturnHistoryPanel.vue` |
| 共享摘要分发与前端交互需要回归覆盖 | ✅ 已完成 | `frontend/src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts`、`frontend/src/components/projects/__tests__/AssetProjectOverviewPanel.spec.ts`、`frontend/src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts`、`frontend/src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts` |
| 阶段结果需归档并更新索引 | ✅ 已完成 | `docs/reports/implementation/PHASE7_2_11_ASSET_PROJECT_SHARED_WORKSPACE_DASHBOARD_IMPLEMENTATION_REPORT.md`、`docs/reports/README.md` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 工作区收敛 | ✅ | `workspace_dashboard` 已由宿主统一请求并分发，没有新增分叉页面或临时接口。 |
| 动态对象统一入口 | ✅ | 共享摘要继续使用既有 `/api/system/objects/AssetProject/{id}/workspace_dashboard/`。 |
| i18n 模块化 | ✅ | 本阶段未新增额外文案，继续复用既有 `projects.json`。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均为英文。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端单元测试 | ✅ | `vitest` 定向 8 个文件、29 个用例通过。 |
| 前端定向 lint | ⚠️ | 目标文件无 error；测试桩文件仍有既有 `vue/one-component-per-file` warnings。 |
| 后端运行态测试 | ⚠️ | 本阶段无后端代码变更，未执行 Django 运行态测试。 |

### 本阶段验证命令

```bash
cd frontend && npm run typecheck:app

cd frontend && npm exec vitest -- run \
  src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts \
  src/components/projects/__tests__/AssetProjectOverviewPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts

cd frontend && npm exec eslint \
  src/components/common/ObjectWorkbenchPanelHost.vue \
  src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts \
  src/components/projects/AssetProjectOverviewPanel.vue \
  src/components/projects/AssetProjectAssetsPanel.vue \
  src/components/projects/AssetProjectMembersPanel.vue \
  src/components/projects/AssetProjectReturnsPanel.vue \
  src/components/projects/AssetProjectReturnHistoryPanel.vue \
  src/components/projects/__tests__/AssetProjectOverviewPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `frontend/src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts` | New | workbench 宿主共享摘要分发回归测试 |
| `docs/reports/implementation/PHASE7_2_11_ASSET_PROJECT_SHARED_WORKSPACE_DASHBOARD_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步可以继续把 `workspace_dashboard` 扩成工作区共享头部缓存，让详情页 action bar、hero stats 和 panel header 全部复用一份状态。
- 当前 assets / members / returns 仍需要各自加载列表数据，后续可考虑引入可见区懒加载，进一步压缩详情页首屏请求数量。
- 如果继续深化 `AssetProject`，建议下一阶段开始梳理“共享摘要刷新策略”，把动作成功后的局部刷新从全页 refresh 缩成面板级增量刷新。
