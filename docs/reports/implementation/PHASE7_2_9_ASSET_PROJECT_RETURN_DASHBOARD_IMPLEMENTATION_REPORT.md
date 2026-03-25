# Phase7.2.9 Asset Project Return Dashboard Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M9 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `AssetProject` 新增 detail custom action `return_dashboard`，把项目回收历史 panel 从多次 `AssetReturn` 列表请求下沉为一次聚合请求。
- 聚合接口统一返回 `summary / history / trend / window` 四段数据，覆盖待确认数量、已处理数量、最近处理记录和时间窗口内趋势统计。
- `AssetProjectReturnHistoryPanel` 现在基于单请求载荷渲染，并新增 `7/30/90` 天时间范围切换与轻量趋势视图，不再依赖前端自行拼装多个列表结果。
- 补充后端 service/API 回归测试和前端单测，确保聚合契约、range 切换和工作区导航都可回归验证。

- 本阶段定向覆盖文件：11 个
- 本阶段新增文件：2 个
- 定向文件总行数：4925 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 项目回收历史需要统一聚合接口，避免前端多请求拼装 | ✅ 已完成 | `backend/apps/projects/services.py`、`backend/apps/projects/viewsets.py` |
| 历史 panel 需支持时间范围切换和趋势展示 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectReturnHistoryPanel.vue`、`frontend/src/locales/en-US/projects.json`、`frontend/src/locales/zh-CN/projects.json` |
| 项目统一对象入口需直接暴露回收仪表板数据 | ✅ 已完成 | `backend/apps/projects/tests/test_api.py` |
| 聚合契约需要前后端回归覆盖 | ✅ 已完成 | `backend/apps/projects/tests/test_services.py`、`backend/apps/assets/tests/test_api.py`、`frontend/src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts` |
| 阶段结果需归档并更新报告索引 | ✅ 已完成 | `docs/reports/implementation/PHASE7_2_9_ASSET_PROJECT_RETURN_DASHBOARD_IMPLEMENTATION_REPORT.md`、`docs/reports/README.md` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 仪表板通过 `/api/system/objects/AssetProject/{id}/return_dashboard/` 暴露，没有新增独立路由。 |
| 工作区收敛 | ✅ | 历史 panel 继续挂在 `AssetProject` detail workbench 中，没有拆出单独 dashboard 页面。 |
| i18n 模块化 | ✅ | 新增 range / trend 文案继续落在 `frontend/src/locales/*/projects.json`。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均为英文。 |
| 后端语法校验 | ✅ | 目标 Python 文件 `py_compile` 通过。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端单元测试 | ✅ | `vitest` 定向 6 个文件、22 个用例通过。 |
| 前端定向 lint | ⚠️ | 目标文件无 error；测试桩文件仍有 `vue/one-component-per-file` warnings。 |
| Django 运行态测试 | ⚠️ | 本地环境未执行 Django 运行态测试，新增 API 用例已落库。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/projects/services.py \
  backend/apps/projects/viewsets.py \
  backend/apps/projects/tests/test_services.py \
  backend/apps/projects/tests/test_api.py \
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
  src/components/projects/__tests__/AssetProjectReturnHistoryPanel.spec.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/projects/tests/test_api.py` | New | `AssetProject.return_dashboard` 对象接口回归测试 |
| `docs/reports/implementation/PHASE7_2_9_ASSET_PROJECT_RETURN_DASHBOARD_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步建议把当前 `return_dashboard` 继续扩成可复用的项目工作区聚合协议，把资产、成员、回收三类统计统一收口，减少 workbench 面板各自独立请求。
- 如果后续要上正式图表，可直接复用当前 `trend.points` 契约，不需要重做后端数据层。
- 当前范围以快速范围切换为主，后续可以再补自定义日期区间和按状态筛选。
