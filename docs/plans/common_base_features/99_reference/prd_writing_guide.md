# PRD 编写指南 - 公共模型引用规范

## 目录
1. [指南概述](#1-指南概述)
2. [PRD 编写流程](#2-prd-编写流程)
3. [后端公共模型引用](#3-后端公共模型引用)
4. [前端公共模型引用](#4-前端公共模型引用)
5. [API 规范引用](#5-api-规范引用)
6. [元数据驱动引用](#6-元数据驱动引用)
7. [PRD 模板](#7-prd-模板)
8. [常见场景示例](#8-常见场景示例)
9. [检查清单](#9-检查清单)

---

## 1. 指南概述

### 1.1 目的

本文档为 GZEAMS 平台开发新功能或新对象时提供 **PRD（产品需求文档）编写指南**，明确：

- 如何正确引用 `common_base_features` 中的公共模型
- 后端必须继承的基类和必须使用的服务
- 前端必须使用的公共组件和 Hooks
- API 必须遵循的响应格式和错误处理规范
- 元数据驱动模式的引用规则

### 1.2 适用范围

- ✅ **新增业务对象**（如：Asset、ProcurementRequest）
- ✅ **新增业务模块**（如：采购管理、库存管理）
- ✅ **扩展现有功能**（如：添加新的字段类型、新的操作）
- ✅ **新建报表功能**
- ✅ **新建工作流功能**

### 1.3 不适用场景

- ❌ 修改 `common_base_features` 本身（需要修改核心规范文档）
- ❌ 第三方集成（参考 `EXECUTION_PLAN.md` 中的集成规范）

---

## 2. PRD 编写流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        新功能 PRD 编写流程                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ 1. 需求分析  │───>│ 2. 架构设计  │───>│ 3. PRD 编写  │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                  │                  │                         │
│         ▼                  ▼                  ▼                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ • 业务场景   │    │ • 数据模型   │    │ • 引用公共   │              │
│  │ • 用户角色   │    │ • 接口设计   │    │   模型声明   │              │
│  │ • 功能范围   │    │ • 前端组件   │    │ • 后端实现   │              │
│  └──────────────┘    └──────────────┘    │ • 前端实现   │              │
│                                         │ • API 规范   │              │
│                                         └──────────────┘              │
│                                                   │                     │
│                                                   ▼                     │
│                                         ┌──────────────┐              │
│                                         │ 4. 评审验收  │              │
│                                         └──────────────┘              │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.1 PRD 编写前检查

在开始编写 PRD 之前，请确认：

| 检查项 | 说明 | 引用文档 |
|--------|------|---------|
| 功能类型判断 | 传统模式 vs 元数据驱动模式 | `overview.md` 第 8.2 节 |
| 数据模型需求 | 需要哪些字段、主从关系 | `backend.md` |
| 页面布局需求 | 列表/表单/详情页面布局 | `page_layout_config.md` |
| 权限控制需求 | 基于角色的权限控制 | `permission_models.md` |
| 工作流需求 | 审批流程 | `workflow_integration.md` |

---

## 3. 后端公共模型引用

### 3.1 后端基类声明规范

在 PRD 中，使用以下**表格声明式**描述后端组件的继承关系（**不要写完整代码示例**）：

```markdown
## 后端实现

### 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields 序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一 CRUD 方法 |

### 业务字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| asset_code | string | unique, max_length=50 | 资产编码 |
| asset_name | string | max_length=200 | 资产名称 |
| ... | ... | ... | ... |
```

### 3.2 各基类功能说明

#### 3.2.1 Model（必选）

| 项目 | 说明 |
|------|------|
| **基类** | `apps.common.models.BaseModel` |
| **自动字段** | organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields |
| **自动功能** | 组织隔离、软删除、完整审计日志、动态字段扩展 |

#### 3.2.2 Serializer（必选）

| 项目 | 说明 |
|------|------|
| **基类** | `apps.common.serializers.base.BaseModelSerializer` |
| **自动序列化** | id, organization, created_at, updated_at, created_by, custom_fields |
| **特殊功能** | created_by 用户信息嵌套序列化、custom_fields JSONB 序列化 |

#### 3.2.3 ViewSet（必选）

| 项目 | 说明 |
|------|------|
| **基类** | `apps.common.viewsets.base.BaseModelViewSetWithBatch` |
| **标准端点** | GET/POST/PUT/PATCH/DELETE CRUD + /deleted/ + /{id}/restore/ |
| **批量端点** | /batch-delete/, /batch-restore/, /batch-update/ |
| **自动功能** | 组织过滤、软删除过滤、审计字段自动设置 |

#### 3.2.4 Filter（必选）

| 项目 | 说明 |
|------|------|
| **基类** | `apps.common.filters.base.BaseModelFilter` |
| **自动过滤** | created_at_from/to, updated_at_from/to, created_by, is_deleted |

#### 3.2.5 Service（推荐）

| 项目 | 说明 |
|------|------|
| **基类** | `apps.common.services.base_crud.BaseCRUDService` |
| **自动方法** | create(), update(), delete(软), restore(), get(), query(), paginate() |

### 3.3 代码结构

```
apps/new_module/
├── __init__.py
├── models.py          # 继承 BaseModel
├── serializers.py     # 继承 BaseModelSerializer
├── viewsets.py        # 继承 BaseModelViewSetWithBatch
├── filters.py         # 继承 BaseModelFilter
├── services.py        # 继承 BaseCRUDService（推荐）
└── urls.py            # 路由配置
```

---

## 4. 前端公共模型引用

### 4.1 前端组件声明规范

在 PRD 中，使用以下**表格声明式**描述前端组件的使用（**不要写完整代码示例**）：

```markdown
## 前端实现

### 公共组件引用

| 组件类型 | 使用组件 | 引用路径 | 说明 |
|---------|---------|---------|------|
| 列表页 | BaseListPage | @/components/common/BaseListPage.vue | 配合 useListPage Hook |
| 表单页 | BaseFormPage | @/components/common/BaseFormPage.vue | 配合 useFormPage Hook |
| 详情页 | BaseDetailPage | @/components/common/BaseDetailPage.vue | 详情展示页面 |
| 标签页 | DynamicTabs | @/components/engine/DynamicTabs.vue | 参考 tab_configuration.md |
| 区块 | SectionBlock | @/components/engine/SectionBlock.vue | 参考 section_block_layout.md |
| 字段渲染 | FieldRenderer | @/components/engine/FieldRenderer.vue | 参考 field_configuration_layout.md |
| 列配置 | ColumnManager | @/components/common/ColumnManager.vue | 参考 list_column_configuration.md |

### 必用 Hooks

| Hook | 引用路径 | 用途 |
|------|---------|------|
| useListPage | @/composables/useListPage.js | 列表页逻辑 |
| useFormPage | @/composables/useFormPage.js | 表单页逻辑 |
| useValidation | @/composables/useValidation.js | 表单验证 |
| usePermission | @/composables/usePermission.js | 权限检查 |
```

### 4.2 组件功能索引

#### 4.2.1 页面级组件

| 组件 | 功能 | 自动获得 |
|------|------|---------|
| BaseListPage | 列表页框架 | 搜索、分页、批量操作、列配置 |
| BaseFormPage | 表单页框架 | 表单验证、提交处理、错误提示 |
| BaseDetailPage | 详情页框架 | 审计信息展示、操作历史 |

#### 4.2.2 基础组件

| 组件 | 功能 |
|------|------|
| BaseTable | 统一表格（支持列配置、排序） |
| BaseSearchBar | 搜索栏 |
| BasePagination | 分页器 |
| BaseAuditInfo | 审计信息展示 |
| BaseFileUpload | 文件上传 |

#### 4.2.3 列配置功能（ColumnManager）

| 功能 | 说明 |
|------|------|
| 列显示/隐藏 | 用户自定义显示列 |
| 列拖拽排序 | 拖拽调整列顺序 |
| 列宽调整 | 拖拽调整列宽 |
| 列固定 | 左右固定列 |
| 配置保存 | 用户个性化配置持久化 |

#### 4.2.4 元数据驱动组件（可选）

| 组件 | 引用文档 |
|------|---------|
| MetadataDrivenForm | metadata_frontend.md |
| MetadataDrivenList | metadata_frontend.md |
| FieldRenderer | field_configuration_layout.md |

### 4.3 代码结构

```
frontend/src/views/new_module/
├── NewObjectList.vue       # 列表页（使用 BaseListPage）
├── NewObjectForm.vue       # 表单页（使用 BaseFormPage）
└── NewObjectDetail.vue     # 详情页（使用 BaseDetailPage）

frontend/src/api/
└── new_module.js           # API 调用封装
```

---

## 5. API 规范引用

### 5.1 必须遵循的响应格式

#### 5.1.1 成功响应

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        ...
    }
}
```

#### 5.1.2 列表响应

```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 5.1.3 错误响应

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {...}
    }
}
```

### 5.2 必须提供的 API 端点

继承 `BaseModelViewSet` 后，自动提供以下端点：

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/new-objects/` | 列表查询（分页、过滤、搜索） |
| GET | `/api/new-objects/{id}/` | 获取单条记录 |
| POST | `/api/new-objects/` | 创建新记录 |
| PUT | `/api/new-objects/{id}/` | 完整更新 |
| PATCH | `/api/new-objects/{id}/` | 部分更新 |
| DELETE | `/api/new-objects/{id}/` | 软删除 |
| GET | `/api/new-objects/deleted/` | 查看已删除记录 |
| POST | `/api/new-objects/{id}/restore/` | 恢复已删除记录 |
| POST | `/api/new-objects/batch-delete/` | 批量软删除 |
| POST | `/api/new-objects/batch-restore/` | 批量恢复 |
| POST | `/api/new-objects/batch-update/` | 批量更新 |

### 5.3 动态对象路由（新增）

**禁止为新增业务对象创建独立的URL配置**

所有业务对象必须通过统一动态路由访问：

```python
# ❌ 禁止：在 urls.py 中注册独立路由
router.register(r'my-object', MyObjectViewSet, basename='my-object')

# ✅ 正确：对象自动注册到 /api/objects/{code}/
# 只需确保 BusinessObject 存在即可
```

**API端点规范**：

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/objects/{object_code}/` | 列表查询 |
| POST | `/api/objects/{object_code}/` | 创建记录 |
| GET | `/api/objects/{object_code}/{id}/` | 获取详情 |
| PUT | `/api/objects/{object_code}/{id}/` | 更新记录 |
| DELETE | `/api/objects/{object_code}/{id}/` | 删除记录 |
| GET | `/api/objects/{object_code}/metadata/` | 获取元数据 |

**前端调用规范**：

```javascript
// ✅ 使用统一动态 API
import { createObjectClient } from '@/api/dynamic'

const api = createObjectClient('MyObject')
await api.list({ page: 1 })
await api.create(data)
```

**PRD中需声明的对象配置**：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| object_code | 对象代码（唯一） | "AssetPickup" |
| name | 对象名称 | "资产领用单" |
| is_hardcoded | 是否硬编码对象 | true/false |
| django_model_path | Django模型路径 | "apps.assets.models.AssetPickup" |

### 5.4 API 规范声明模板

```markdown
## API 接口

### 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

详见 `api.md` 中的标准 API 规范。

### 自定义端点（如有）

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/new-objects/{id}/approve/` | 审批 | new_object.approve |
| POST | `/api/new-objects/{id}/reject/` | 驳回 | new_object.reject |

### 响应格式

遵循 `api.md` 中定义的统一响应格式。

### 错误码

使用 `api.md` 中定义的标准错误码：
- `VALIDATION_ERROR` (400)
- `UNAUTHORIZED` (401)
- `PERMISSION_DENIED` (403)
- `NOT_FOUND` (404)
- `ORGANIZATION_MISMATCH` (403)
- `SOFT_DELETED` (410)
```

---

## 6. 元数据驱动引用

### 6.1 何时使用元数据驱动模式

参考 `overview.md` 第 8.3 节：

**适合元数据驱动的场景：**
- ✅ 动态表单需求
- ✅ 多租户定制需求
- ✅ 快速原型开发
- ✅ 频繁变更的字段定义

**不适合元数据驱动的场景：**
- ❌ 核心业务实体（使用传统模式）
- ❌ 复杂业务逻辑
- ❌ 高性能要求场景

### 6.2 元数据驱动引用模板

```markdown
## 元数据驱动配置（可选）

如采用元数据驱动模式，参考以下文档：

| 文档 | 说明 |
|------|------|
| metadata_driven.md | 元数据驱动核心架构 |
| dynamic_data_service.md | 动态数据 CRUD 服务 |
| metadata_validators.md | 动态字段验证 |
| metadata_frontend.md | 元数据前端组件 |
| page_layout_config.md | 页面布局配置 |
| field_cascade.md | 字段级联配置 |
```

---

## 7. PRD 模板

### 7.1 完整 PRD 模板

```markdown
# [功能名称] PRD

## 1. 需求概述

### 1.1 业务背景
描述业务场景和需求来源

### 1.2 目标用户
描述目标用户角色

### 1.3 功能范围
描述本次实现的功能范围

## 2. 后端设计

### 2.1 数据模型

#### 2.1.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields 序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一 CRUD 方法 |

#### 2.1.2 业务字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| name | string | max_length=200 | 名称 |
| code | string | unique, max_length=50 | 编码 |
| ... | ... | ... | ... |

### 2.2 API 接口

#### 2.2.1 动态对象路由（强制使用）

**禁止创建独立URL路由，必须使用统一动态路由**

| 配置项 | 值 | 说明 |
|--------|---|------|
| 路由方式 | 统一动态路由 | `/api/objects/{object_code}/` |
| object_code | [对象代码] | 必须唯一，如 "AssetPickup" |
| is_hardcoded | true/false | 是否为硬编码对象 |
| django_model_path | [模型路径] | 如 "apps.assets.models.AssetPickup" |

**自动获得的API端点**：
- GET/POST `/api/objects/{object_code}/` - 列表/创建
- GET/PUT/PATCH/DELETE `/api/objects/{object_code}/{id}/` - 详情/更新/删除
- GET `/api/objects/{object_code}/metadata/` - 元数据
- POST `/api/objects/{object_code}/batch-delete/` - 批量删除
- POST `/api/objects/{object_code}/batch-restore/` - 批量恢复

#### 2.2.2 自定义端点（如有）
| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | /api/new-objects/{id}/action/ | 操作说明 | new_object.action |

## 3. 前端设计

### 3.1 公共组件引用

| 组件类型 | 使用组件 | 引用路径 |
|---------|---------|---------|
| 列表页 | BaseListPage | @/components/common/BaseListPage.vue |
| 表单页 | BaseFormPage | @/components/common/BaseFormPage.vue |
| 详情页 | BaseDetailPage | @/components/common/BaseDetailPage.vue |

### 3.2 布局配置

| 配置项 | 参考文档 |
|--------|---------|
| 标签页配置 | tab_configuration.md |
| 区块布局 | section_block_layout.md |
| 字段配置 | field_configuration_layout.md |
| 列表列配置 | list_column_configuration.md |

## 4. 权限设计

### 4.1 权限定义

| 权限代码 | 说明 | 默认角色 |
|---------|------|---------|
| new_object.view | 查看权限 | 所有用户 |
| new_object.add | 创建权限 | 管理员 |
| new_object.change | 编辑权限 | 管理员 |
| new_object.delete | 删除权限 | 管理员 |

## 5. 实施计划

| 阶段 | 任务 | 说明 |
|------|------|------|
| 1 | 后端模型开发 | 继承 BaseModel 定义业务字段 |
| 2 | 后端 API 开发 | 继承 BaseModelViewSet 实现接口 |
| 3 | 前端页面开发 | 使用公共组件开发页面 |
| 4 | 联调测试 | 接口联调和功能测试 |
| 5 | 上线部署 | 部署到生产环境 |
```

---

## 8. 常见场景示例

### 8.1 场景一：简单 CRUD 对象

**场景**：新增一个简单的业务对象，只需基本的 CRUD 功能

**引用清单**：

```markdown
## 后端引用

- Model: 继承 `BaseModel`
- Serializer: 继承 `BaseModelSerializer`
- ViewSet: 继承 `BaseModelViewSet`（无需批量操作可用 `BaseModelViewSet`）
- Filter: 继承 `BaseModelFilter`

## 前端引用

- 列表页: `BaseListPage` + `useListPage`
- 表单页: `BaseFormPage` + `useFormPage`
- 详情页: `BaseDetailPage`

## 布局引用

- 参考默认布局：`default_page_layouts.md`
- 字段配置：`field_configuration_layout.md`
```

### 8.2 场景二：主从关系对象

**场景**：新增一个带明细行的业务对象（如采购单+采购明细）

**引用清单**：

```markdown
## 后端引用

- 主对象 Model: 继承 `BaseModel`
- 从对象 Model: 继承 `BaseModel`（带外键关联）
- 主对象 Serializer: 继承 `BaseModelSerializer`，嵌套从对象 Serializer
- 从对象 Serializer: 继承 `BaseModelSerializer`
- ViewSet: 继承 `BaseModelViewSetWithBatch`

## 前端引用

- 主表单页: `BaseFormPage` + `SubTableField` 组件
- 参考：`sub_object_layout.md`

## 布局引用

- 主从表布局配置：`sub_object_layout.md`
- 子表组件：`SubTableField.vue`
```

### 8.3 场景三：元数据驱动对象

**场景**：新增一个需要动态配置字段的对象

**引用清单**：

```markdown
## 元数据驱动引用

- 后端服务：`MetadataDrivenService`（参考 `dynamic_data_service.md`）
- 前端表单：`MetadataDrivenForm`（参考 `metadata_frontend.md`）
- 前端列表：`MetadataDrivenList`
- 动态验证：`DynamicFieldValidator`（参考 `metadata_validators.md`）

## 配置文档

- BusinessObject 配置：`metadata_driven.md`
- PageLayout 配置：`page_layout_config.md`
- FieldDefinition 配置：`metadata_driven.md`
```

### 8.4 场景四：工作流对象

**场景**：新增一个需要审批流程的对象

**引用清单**：

```markdown
## 工作流引用

- 工作流集成：`workflow_integration.md`
- 字段级权限：配置工作流节点的字段读写权限
- 状态驱动：通过 WorkflowDefinition 定义状态流转

## 变更审批

- 数据变更审批：`data_change_approval.md`
```

---

## 9. 检查清单

### 9.1 后端检查清单

开发完成后，确认以下项目：

- [ ] Model 继承 `BaseModel`
- [ ] Serializer 继承 `BaseModelSerializer`
- [ ] ViewSet 继承 `BaseModelViewSet` 或 `BaseModelViewSetWithBatch`
- [ ] Filter 继承 `BaseModelFilter`
- [ ] Service（如使用）继承 `BaseCRUDService`
- [ ] API 响应格式符合 `api.md` 规范
- [ ] 错误码使用标准定义
- [ ] 组织隔离正常工作
- [ ] 软删除正常工作
- [ ] 审计字段正常设置

### 9.2 前端检查清单

开发完成后，确认以下项目：

- [ ] 使用公共页面组件（BaseListPage/BaseFormPage/BaseDetailPage）
- [ ] 使用公共基础组件（BaseTable/BaseSearchBar 等）
- [ ] API 调用封装在 `@/api/` 目录下
- [ ] 使用全局错误处理
- [ ] 布局配置符合 `page_layout_config.md` 规范
- [ ] 字段配置符合 `field_configuration_layout.md` 规范
- [ ] 权限控制正确实现

### 9.3 PRD 文档检查清单

PRD 编写完成后，确认以下项目：

- [ ] 包含后端公共模型引用声明
- [ ] 包含前端公共组件引用声明
- [ ] 包含 API 规范引用声明
- [ ] 明确数据模型继承关系
- [ ] 明确权限定义
- [ ] 包含页面布局配置
- [ ] 如有主从关系，引用 `sub_object_layout.md`
- [ ] 如需工作流，引用 `workflow_integration.md`

---

## 附录

### A. 快速参考卡片

```
┌─────────────────────────────────────────────────────────────┐
│                    GZEAMS 公共模型快速参考                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  后端基类引用路径：                                          │
│  ├── BaseModel          → apps.common.models                │
│  ├── BaseModelSerializer → apps.common.serializers.base     │
│  ├── BaseModelViewSet   → apps.common.viewsets.base        │
│  ├── BaseModelFilter     → apps.common.filters.base         │
│  └── BaseCRUDService     → apps.common.services.base_crud   │
│                                                             │
│  前端公共组件引用路径：                                      │
│  ├── BaseListPage       → @/components/common/BaseListPage  │
│  ├── BaseFormPage       → @/components/common/BaseFormPage  │
│  ├── BaseDetailPage     → @/components/common/BaseDetailPage│
│  ├── DynamicTabs        → @/components/engine/DynamicTabs   │
│  ├── SectionBlock       → @/components/engine/SectionBlock  │
│  └── FieldRenderer      → @/components/engine/FieldRenderer │
│                                                             │
│  核心文档：                                                 │
│  ├── overview.md              → 总览                        │
│  ├── backend.md               → 后端基类                    │
│  ├── frontend.md              → 前端组件                    │
│  ├── api.md                   → API 规范                    │
│  ├── page_layout_config.md    → 页面布局                    │
│  ├── sub_object_layout.md     → 主从布局                    │
│  └── workflow_integration.md  → 工作流                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### B. 相关文档索引

| 文档 | 说明 |
|------|------|
| `overview.md` | 公共功能总览，包含传统模式与元数据驱动模式的选择指南 |
| `backend.md` | 后端基类详细实现 |
| `frontend.md` | 前端公共组件详细实现 |
| `api.md` | API 响应格式和批量操作规范 |
| `permission_models.md` | 权限模型设计 |
| `workflow_integration.md` | 工作流集成 |
| `page_layout_config.md` | 页面布局配置 |
| `default_page_layouts.md` | 默认布局示例 |
| `list_column_configuration.md` | **列表字段显示管理（列配置）** |
| `sub_object_layout.md` | 主从关系布局 |
| `tab_configuration.md` | 标签页配置 |
| `section_block_layout.md` | 区块布局 |
| `field_configuration_layout.md` | 字段配置 |
| `layout_customization_workflow.md` | 布局自定义流程 |
| `metadata_driven.md` | 元数据驱动架构 |
| `metadata_frontend.md` | 元数据前端组件 |

---

**版本**: 2.1.0
**更新日期**: 2026-01-27
**维护人**: GZEAMS 开发团队

## 版本变更记录

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| 2.1.0 | 2026-01-27 | 添加动态对象路由规范；禁止创建独立URL路由；统一使用/api/objects/{code}/端点 |
| 2.0.0 | 2025-01-16 | 移除代码示例，改为表格声明式描述；精简 PRD 模板 |
| 1.1.0 | 2025-01-15 | 添加列表字段显示管理功能 |
| 1.0.0 | 2024-12-01 | 初始版本 |
