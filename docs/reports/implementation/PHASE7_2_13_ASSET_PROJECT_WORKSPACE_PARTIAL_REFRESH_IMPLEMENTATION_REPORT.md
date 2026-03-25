# Phase7.2.13 Asset Project Workspace Partial Refresh Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M13 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `AssetProject` 工作区建立局部刷新协议，把原来统一的 `refresh-requested` 拆分成三类能力：共享摘要刷新、指定 panel 刷新、整页 detail 刷新兜底。
- `ObjectWorkbenchPanelHost` 现在支持处理 `workbench-refresh-requested` 载荷，并对 `workspace_dashboard`、目标 panel 刷新版本以及 detail 兜底刷新做分层控制。
- `DynamicDetailPage` 新增 `record-patch` 合并链路，让共享摘要刷新后可以直接回写 `activeAssets / memberCount / assetCost` 等工作区统计字段，避免 hero 区域继续依赖整页刷新。
- `AssetProjectOverviewPanel`、`AssetProjectAssetsPanel`、`AssetProjectReturnsPanel` 已切到新的局部刷新事件；其中归还确认/驳回动作现在只刷新共享摘要和命中的 `project_assets / project_return_history`，不再默认拉整页 detail。
- 补充宿主局部刷新回归测试，并同步更新 overview / returns panel 的事件断言。

- 本阶段定向覆盖文件：11 个
- 本阶段新增文件：1 个
- 定向文件总行数：4043 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 工作区刷新链路需要支持共享摘要与 panel 列表分层刷新 | ✅ 已完成 | `frontend/src/components/common/ObjectWorkbenchPanelHost.vue` |
| 工作区摘要刷新后需同步到 detail hero / 统计区域 | ✅ 已完成 | `frontend/src/views/dynamic/DynamicDetailPage.vue` |
| overview / returns / assets 等面板需接入新的局部刷新协议 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectOverviewPanel.vue`、`frontend/src/components/projects/AssetProjectAssetsPanel.vue`、`frontend/src/components/projects/AssetProjectReturnsPanel.vue` |
| 宿主层需要回归验证目标 panel 刷新和整页刷新隔离 | ✅ 已完成 | `frontend/src/components/common/__tests__/ObjectWorkbenchPanelHost.spec.ts` |
| 阶段结果需归档并更新索引 | ✅ 已完成 | `docs/reports/implementation/PHASE7_2_13_ASSET_PROJECT_WORKSPACE_PARTIAL_REFRESH_IMPLEMENTATION_REPORT.md`、`docs/reports/README.md` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 工作区收敛 | ✅ | 刷新协议继续收敛在统一 `workbench` 宿主内，没有拆分新的状态管理入口。 |
| 动态对象统一入口 | ✅ | 本阶段无新增接口，继续复用既有 `workspace_dashboard`。 |
| i18n 模块化 | ✅ | 本阶段未新增额外模块文案。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均为英文。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端单元测试 | ✅ | `vitest` 定向 8 个文件、30 个用例通过。 |
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
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts \
  src/views/dynamic/DynamicDetailPage.vue
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `docs/reports/implementation/PHASE7_2_13_ASSET_PROJECT_WORKSPACE_PARTIAL_REFRESH_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步可以把 `ObjectWorkbenchActionBar` 也接入同一套局部刷新协议，让 `refresh_rollups` 这类动作优先刷新摘要和 patch，而不是默认整页 reload。
- 当前 `record-patch` 只覆盖工作区关键统计字段，后续可以扩展成通用 workbench record overlay，减少更多 detail shell 对原始 detail 请求的依赖。
- 如果后续推广到其他对象，建议把 `workbench-refresh-requested` 协议沉淀到 runtime workbench 文档里，形成统一契约。
