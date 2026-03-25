# Phase7.2.7 Asset Project Return Tracking Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M7 |
| 作者/Agent | Codex |

## 一、实施概述

- 为 `ProjectAsset` 增加“最近归还单摘要”派生字段，把项目资产与最近一次 `AssetReturn` 的单号、状态、处理时间、归还原因 / 驳回原因重新联通。
- 在 `AssetReturn.reject` 链路中同步回写项目资产 notes，保留“驳回但仍在用”的审计轨迹，避免项目侧只能看到 `in_use` 而丢失归还处理上下文。
- `AssetProjectAssetsPanel` 新增“最近归还记录”列，支持在项目工作区直接查看回收状态摘要，并从摘要入口跳转到对应 `AssetReturn` 详情。
- 补齐后端服务/API 回归与前端 panel 单测，确保“驳回原因 + 最近处理记录”能稳定回到项目资产视图。

- 本阶段定向覆盖文件：10 个
- 本阶段新增文件：2 个
- 定向文件总行数：5186 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 项目资产视图需感知最近一次归还处理状态，而不是只显示静态分配状态 | ✅ 已完成 | `backend/apps/projects/serializers.py`、`backend/apps/projects/viewsets.py`、`frontend/src/components/projects/AssetProjectAssetsPanel.vue` |
| 归还驳回原因应回到项目上下文，形成资产侧可见的追踪信息 | ✅ 已完成 | `backend/apps/assets/services/operation_service.py`、`backend/apps/projects/services.py` |
| 项目工作区需可从资产行直接追到对应归还单 | ✅ 已完成 | `frontend/src/components/projects/AssetProjectAssetsPanel.vue` |
| 新增联动需具备前后端回归验证 | ✅ 已完成 | `backend/apps/projects/tests/test_services.py`、`backend/apps/assets/tests/test_api.py`、`frontend/src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts` |
| 阶段结果归档并更新报告索引 | ✅ 已完成 | `docs/reports/implementation/PHASE7_2_7_ASSET_PROJECT_RETURN_TRACKING_IMPLEMENTATION_REPORT.md`、`docs/reports/README.md` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| 动态对象统一入口 | ✅ | 继续通过 `ProjectAsset` / `AssetReturn` 统一对象入口工作，没有新增独立业务路由。 |
| 项目工作区收敛 | ✅ | 回收追踪继续挂在 `AssetProject` detail panel 内，而不是拆出新的资产回收专页。 |
| 后端基类继承规范 | ✅ | 本阶段未引入新的 Model/ViewSet/Service 类型，沿用既有 `BaseCRUDService` 与统一对象 ViewSet。 |
| i18n 模块化 | ✅ | 新增文案继续落在 `frontend/src/locales/*/projects.json`。 |
| 代码注释语言约束 | ✅ | 本阶段新增注释均为英文。 |
| 后端语法校验 | ✅ | 目标 Python 文件 `py_compile` 通过。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 通过。 |
| 前端单元测试 | ✅ | `vitest` 定向 5 个文件、20 个用例通过。 |
| 前端定向 lint | ⚠️ | 目标文件无 error；测试桩文件仍有 `vue/one-component-per-file` warnings。 |
| Django 运行态测试 | ⚠️ | 本地环境未执行 Django 运行态测试，新增用例已落库。 |

### 本阶段验证命令

```bash
PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile \
  backend/apps/projects/services.py \
  backend/apps/assets/services/operation_service.py \
  backend/apps/projects/serializers.py \
  backend/apps/projects/viewsets.py \
  backend/apps/projects/tests/test_services.py \
  backend/apps/assets/tests/test_api.py

cd frontend && npm run typecheck:app

cd frontend && npm exec vitest -- run \
  src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts \
  src/components/projects/__tests__/assetProjectAssetActions.spec.ts \
  src/components/common/__tests__/ObjectWorkbenchActionBar.spec.ts \
  src/__tests__/unit/views/dynamic/DynamicDetailPage.navigation.spec.ts

cd frontend && npm exec eslint \
  src/components/projects/AssetProjectAssetsPanel.vue \
  src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts \
  src/components/projects/AssetProjectReturnsPanel.vue \
  src/components/projects/__tests__/AssetProjectReturnsPanel.spec.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `frontend/src/components/projects/__tests__/AssetProjectAssetsPanel.spec.ts` | New | 项目资产 panel 最近归还摘要展示与跳转单测 |
| `docs/reports/implementation/PHASE7_2_7_ASSET_PROJECT_RETURN_TRACKING_IMPLEMENTATION_REPORT.md` | New | 本阶段实施报告 |

## 五、后续建议

- 下一步建议补一个“项目回收历史” panel 或状态卡，把已确认 / 已驳回 / 待确认三类归还单做聚合视图，而不是只显示每条资产的最近一次记录。
- 如果后续要做项目结项审计，建议基于当前 `latest_return_summary + notes` 再沉淀成显式统计字段，减少结项时的派生查询成本。
- 当前后端回归只做了语法和落库测试，具备 Django 运行环境后，建议优先补跑 `AssetReturn.reject` 与 `ProjectAsset` 动态对象列表的真实接口用例。
