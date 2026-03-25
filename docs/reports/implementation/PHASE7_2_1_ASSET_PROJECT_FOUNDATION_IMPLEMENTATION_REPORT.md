# Phase7.2.1 Asset Project Foundation Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 涉及阶段 | Phase 7.2-M1 |
| 作者/Agent | Codex |

## 一、实施概述

- 新增 `apps.projects` 模块，落地 `AssetProject`、`ProjectAsset`、`ProjectMember` 三个核心模型及初始迁移。
- 完成项目模块的 `Serializer`、`Filter`、`Service`、`ViewSet` 基础层，全部遵循 `BaseModel` / `BaseModelSerializer` / `BaseModelViewSetWithBatch` / `BaseCRUDService` / `BaseModelFilter` 继承规范。
- 将资产项目对象接入 hardcoded object catalog、统一对象路由菜单规则和前端对象名称映射，正式支持 `/objects/AssetProject`、`/objects/ProjectAsset`、`/objects/ProjectMember`。
- 为 `AssetProject` 增加项目编码生成与分配汇总刷新能力，为 `ProjectAsset` 增加分配单号生成、资产快照与项目汇总刷新。
- 补充 `AssetProject` catalog/menu 侧回归测试骨架，供后续 Django 运行环境可用时直接执行。

- 本阶段涉及文件：13 个
- 本阶段新增文件：9 个
- 定向统计代码行数：1541 行

## 二、与 PRD 对应关系

| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 新增 `AssetProject`、`ProjectAsset`、`ProjectMember` 数据模型 | ✅ 已完成 | `backend/apps/projects/models.py`、`backend/apps/projects/migrations/0001_initial.py` |
| 所有后端组件继承公共基类体系 | ✅ 已完成 | `backend/apps/projects/serializers.py`、`backend/apps/projects/filters.py`、`backend/apps/projects/services.py`、`backend/apps/projects/viewsets.py` |
| 将项目对象纳入统一对象路由体系 | ✅ 已完成 | `backend/apps/system/object_catalog.py`、`backend/config/settings/base.py` |
| 为项目对象补齐默认菜单规则与入口 | ✅ 已完成 | `backend/apps/system/menu_config.py` |
| 前端对象名称与菜单文案可识别新对象 | ✅ 已完成 | `frontend/src/utils/objectDisplay.ts`、`frontend/src/locales/en-US/menu.json`、`frontend/src/locales/zh-CN/menu.json` |
| 补充对象目录 / 菜单同步回归测试 | ✅ 已完成 | `backend/apps/system/tests/test_asset_project_catalog.py` |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|--------|------|------|
| Model 继承 `BaseModel` | ✅ | 三个核心模型均复用组织隔离、软删除、审计字段与 `custom_fields`。 |
| Serializer 继承 `BaseModelSerializer` | ✅ | 项目、分配、成员序列化均基于统一公共序列化器。 |
| ViewSet 继承 `BaseModelViewSetWithBatch` | ✅ | 三个对象均支持标准 CRUD 与批量能力。 |
| Filter 继承 `BaseModelFilter` | ✅ | 提供状态、时间、关联对象与 `search` 筛选能力。 |
| Service 继承 `BaseCRUDService` | ✅ | 新增三个服务类，其中 `AssetProjectService` 补充汇总刷新方法。 |
| 动态对象统一入口 | ✅ | 新对象通过 hardcoded object catalog 接入 `/api/system/objects/{code}/`，未新增独立业务 URL。 |
| 菜单与 i18n 映射 | ✅ | 已补 `menu.routes.assetProject/projectAsset/projectMember` 中英文文案与 route key 映射。 |
| 代码注释语言约束 | ✅ | 本阶段新增代码注释均为英文。 |
| 后端语法校验 | ✅ | `python3 -m py_compile` 已通过。 |
| 前端 typecheck | ✅ | `npm run typecheck:app` 已通过。 |
| 前端 lint | ✅ | 目标文件 `eslint` 已通过。 |
| Django 运行态测试 | ⚠️ 环境限制 | 已新增 `pytest` 测试文件，但当前工作区缺少 Django 运行环境，尚未执行。 |

### 本阶段验证命令

```bash
python3 -m py_compile \
  backend/apps/projects/models.py \
  backend/apps/projects/serializers.py \
  backend/apps/projects/filters.py \
  backend/apps/projects/services.py \
  backend/apps/projects/viewsets.py \
  backend/apps/projects/migrations/0001_initial.py \
  backend/apps/system/tests/test_asset_project_catalog.py \
  backend/apps/system/object_catalog.py \
  backend/apps/system/menu_config.py \
  backend/config/settings/base.py

cd frontend && npm run typecheck:app

cd frontend && npm exec eslint src/utils/objectDisplay.ts
```

## 四、创建文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/apps/projects/__init__.py` | New | 项目模块包入口 |
| `backend/apps/projects/models.py` | New | `AssetProject` / `ProjectAsset` / `ProjectMember` 模型定义 |
| `backend/apps/projects/serializers.py` | New | 项目模块统一序列化器 |
| `backend/apps/projects/filters.py` | New | 项目模块统一筛选器 |
| `backend/apps/projects/services.py` | New | 项目模块服务层 |
| `backend/apps/projects/viewsets.py` | New | 项目模块 ViewSet |
| `backend/apps/projects/migrations/0001_initial.py` | New | 项目模块初始迁移 |
| `backend/apps/projects/migrations/__init__.py` | New | 迁移包入口 |
| `backend/apps/system/tests/test_asset_project_catalog.py` | New | 项目对象 catalog / menu 同步测试 |

## 五、后续建议

- 下一步进入 Phase 7.2-M2，优先补齐 `AssetProject` 的统一工作区页面、项目资产明细与成员明细的 detail/list 呈现。
- 在 Django 运行环境可用后，优先执行项目模块迁移与 `pytest`，确认对象注册、菜单同步和 CRUD 运行态行为。
- 项目结项、跨项目转移、成本汇总等业务动作建议放到 Phase 7.2-M3，再结合工作流和财务能力追加。
