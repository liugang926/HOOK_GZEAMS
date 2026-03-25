# Phase7.2.8 Asset Project Return History Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M8 |
| 作者/Agent | Codex |

## 一、实施概述

- 在 `AssetProject` 工作区新增“项目回收历史” panel，与既有“待确认归还单” panel 分工明确，分别承载处理队列与历史追踪。
- `AssetReturn` 列表序列化补充 `reject_reason`，使项目级历史面板可以直接展示驳回原因，而无需为每条归还单额外发起详情请求。
- 历史 panel 通过项目维度过滤复用既有 `AssetReturn?project=` 能力，汇总 `pending / completed / rejected` 数量，并展示最近已处理归还单。
- 更新 workbench 菜单配置、迁移补丁、runtime 导航断言和前端单测，确保历史 panel 在新老环境下都能稳定挂载。

- 本阶段定向覆盖文件：12 个
- 本阶段新增文件：4 个
- 定向文件总行数：5098 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 项目工作区需要区分“待处理归还队列”和“已处理归还历史” | ✅ 已完成 | `backend/apps/system/menu_config.py`、`backend/apps/system/migrations/0049_asset_project_workbench_return_history_panel.py`、`frontend/src/components/projects/AssetProjectReturnHistoryPanel.vue` |
| 项目回收历史需展示驳回原因与处理状态，形成可审阅轨迹 | ✅ 已完成 | `backend/apps/assets/serializers/operation.py`、`frontend/src/components/projects/AssetProjectReturnHistoryPanel.vue` |
| 历史 panel 需支持从项目工作区跳转到归还单列表 / 详情 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectReturnHistoryPanel.vue` |
| workbench 扩展需具备配置同步与回归验证 | ✅ 已完成 | `backend/apps/system/tests/test_asset_project_catalog.py`、`backend/apps/system/tests/test_menu_config_sync.py`、`frontend/src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts` |
| 新增接口契约需有测试支撑 | ✅ 已完成 | `backend/apps/assets/tests/test_api.py`、`frontend/src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 历史视图继续基于 `/objects/AssetProject` 与 `/objects/AssetReturn`，没有新增独立业务路由。 |
| 工作区收敛 | ✅ | 归还历史继续挂在统一 detail workbench 中，没有回退到专页分叉实现。 |
| i18n 模块化 | ✅ | 新增文案均落在 `frontend/src/locales/*/projects.json`。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均为英文。 |
| 后端语法校验 | ✅ | 目标 Python 文件 `py_compile` 通过。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端单元测试 | ✅ | `vitest` 定向 6 个文件、22 个用例通过。 |
| 前端定向 lint | ⚠️ | 目标文件无 error；测试桩文件和导航 spec 仍有既有 `vue/one-component-per-file` / `vue/require-prop-types` warnings。 |
| Django 运行态测试 | ⚠️ | 本地环境未执行 Django 运行态测试，新增后端用例已落库。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/system/menu_config.py \
  backend/apps/system/migrations/0049_asset_project_workbench_return_history_panel.py \
  backend/apps/system/tests/test_asset_project_catalog.py \
  backend/apps/system/tests/test_menu_config_sync.py \
  backend/apps/assets/serializers/operation.py \
  backend/apps/assets/tests/test_api.py

cd frontend && npm run typecheck:app

cd frontend && npm exec vitest -- run \
  src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts

cd frontend && npm exec eslint \
  src/components/projects/AssetProjectReturnHistoryPanel.vue \
  src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts \
  src/components/common/ObjectWorkbenchPanelHost.vue \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/system/migrations/0049_asset_project_workbench_return_history_panel.py` | New | 为存量 `AssetProject` workbench 回填历史 panel |
| `frontend/src/components/projects/AssetProjectReturnHistoryPanel.vue` | New | 项目回收历史 panel |
| `frontend/src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts` | New | 历史 panel 单测 |
| `docs/reports/implementation/PHASE7_2_8_ASSET_PROJECT_RETURN_HISTORY_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步建议把当前历史 panel 再向前推进成“项目回收仪表板”，补充时间范围筛选和已处理趋势，而不仅是最近记录。
- 如果后续项目结项要依赖回收状态，建议把当前 `pending / completed / rejected` 计数下沉为后端聚合接口，减少前端多次列表请求。
- 当前后端新增 API 断言已落库，但未做 Django 运行态执行；具备环境后建议优先补跑 `AssetReturn` 项目过滤和 reject list payload 用例。
