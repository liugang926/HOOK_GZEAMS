# Common Base Features: API 接口规范

## 任务概述

定义统一的 API 响应格式、错误处理规范和批量操作接口标准。

---

## API 响应模型定义

### 成功响应模型

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| success | boolean | 是 | 操作是否成功 |
| message | string | 否 | 成功消息 |
| data | object/array | 否 | 响应数据 |

### 错误响应模型

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| success | boolean | 是 | 固定为false |
| error.code | string | 是 | 错误码 (VALIDATION_ERROR, NOT_FOUND, etc.) |
| error.message | string | 是 | 错误描述 |
| error.details | object | 否 | 详细错误信息 |

### 批量操作响应模型

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| success | boolean | 是 | 整体是否成功 |
| message | string | 是 | 操作消息 |
| summary.total | integer | 是 | 总数 |
| summary.succeeded | integer | 是 | 成功数 |
| summary.failed | integer | 是 | 失败数 |
| results | array | 是 | 每条记录的执行结果 |
| results[].id | string | 是 | 记录ID |
| results[].success | boolean | 是 | 该条是否成功 |
| results[].error | string | 否 | 失败原因 |

---

## 1. 统一响应格式

### 1.1 成功响应格式

#### 单条记录响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "ASSET001",
        "name": "办公电脑",
        "organization": {...},
        "created_at": "2026-01-14T10:30:00Z",
        "created_by": {...}
    }
}
```

#### 列表响应（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/assets/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "ASSET001",
                ...
            }
        ]
    }
}
```

#### 创建/更新响应

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "ASSET001",
        ...
    }
}
```

#### 删除响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "删除成功"
}
```

### 1.2 错误响应格式

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "code": ["该字段不能为空"],
            "category": ["分类不存在"]
        }
    }
}
```

---

## 2. 统一错误码定义

### 2.1 错误码列表

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 2.2 BaseResponse 响应类

| 方法 | 说明 | HTTP状态码 |
|------|------|-----------|
| `success(data, message)` | 成功响应 | 200 |
| `created(data, message)` | 创建成功 | 201 |
| `no_content(message)` | 无内容 | 204 |
| `error(code, message, details)` | 错误响应 | 400/自定义 |
| `validation_error(details)` | 验证错误 | 400 |
| `unauthorized(message)` | 未授权 | 401 |
| `permission_denied(message)` | 权限不足 | 403 |
| `not_found(resource)` | 资源不存在 | 404 |
| `organization_mismatch(message)` | 组织不匹配 | 403 |
| `soft_deleted(message)` | 资源已删除 | 410 |
| `server_error(message)` | 服务器错误 | 500 |
| `paginated(count, next, previous, results)` | 分页响应 | 200 |

---

## 3. 统一异常处理

### 3.1 异常处理器

| 异常类型 | 映射错误码 | HTTP状态码 | 说明 |
|---------|-----------|-----------|------|
| `ValidationError` | `VALIDATION_ERROR` | 400 | DRF验证错误 |
| `AuthenticationFailed` | `UNAUTHORIZED` | 401 | 认证失败 |
| `PermissionDenied` | `PERMISSION_DENIED` | 403 | 权限不足 |
| `NotFound` | `NOT_FOUND` | 404 | 资源不存在 |
| `MethodNotAllowed` | `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `Throttled` | `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `Http404` | `NOT_FOUND` | 404 | HTTP 404 |
| `APIException` | `default_code` | 自定义 | 其他API异常 |
| 未知异常 | `SERVER_ERROR` | 500 | 服务器错误 |

### 3.2 业务逻辑异常类

| 异常类 | 状态码 | 错误码 | 说明 |
|--------|--------|--------|------|
| `BusinessLogicError` | 400 | `BUSINESS_LOGIC_ERROR` | 业务逻辑异常基类 |
| `OrganizationMismatchError` | 403 | `ORGANIZATION_MISMATCH` | 组织不匹配 |
| `ResourceDeletedError` | 410 | `SOFT_DELETED` | 资源已删除 |
| `ResourceConflictError` | 409 | `CONFLICT` | 资源冲突 |

### 3.3 配置更新

```python
# backend/config/settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.common.handlers.exceptions.custom_exception_handler',
}
```

---

## 4. 批量操作 API 规范

### 4.1 批量删除

```http
POST /api/assets/batch-delete/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001",
        "550e8400-e29b-41d4-a716-446655440002"
    ]
}
```

**响应 (全部成功)**

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "success": true
        }
    ]
}
```

**响应 (部分失败)**

```http
HTTP/1.1 207 Multi-Status

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "记录不存在"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "success": true
        }
    ]
}
```

### 4.2 批量恢复

```http
POST /api/assets/batch-restore/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应格式与批量删除相同**

### 4.3 批量更新

```http
POST /api/assets/batch-update/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "data": {
        "status": "idle",
        "location_id": "550e8400-e29b-41d4-a716-446655440100"
    }
}
```

**响应格式与批量删除相同**

---

## 5. 标准 CRUD API

### 5.1 列表查询

```http
GET /api/assets/?page=1&page_size=20&status=idle&search=电脑

# 支持的查询参数：
# - page: 页码
# - page_size: 每页数量
# - ordering: 排序字段 (如：-created_at)
# - search: 搜索关键词
# - created_at_from: 创建时间起始
# - created_at_to: 创建时间结束
# - created_by: 创建人ID
# - 以及各模块自定义的过滤字段
```

### 5.2 获取详情

```http
GET /api/assets/{id}/
```

### 5.3 创建

```http
POST /api/assets/
Content-Type: application/json

{
    "code": "ASSET001",
    "name": "办公电脑",
    "category_id": "...",
    "status": "idle"
}
```

### 5.4 更新

```http
PUT /api/assets/{id}/
Content-Type: application/json

{
    "code": "ASSET001",
    "name": "办公电脑（更新）",
    "status": "in_use"
}
```

### 5.5 部分更新

```http
PATCH /api/assets/{id}/
Content-Type: application/json

{
    "status": "in_use"
}
```

### 5.6 删除（软删除）

```http
DELETE /api/assets/{id}/
```

---

## 6. 扩展操作 API

### 6.1 查询已删除记录

```http
GET /api/assets/deleted/
```

### 6.2 恢复单条记录

```http
POST /api/assets/{id}/restore/
```

### 6.3 获取变更历史

```http
GET /api/assets/{id}/history/
```

---

## 7. 动态对象路由 API（强制规范）

### 7.1 核心原则

**禁止为新增业务对象创建独立的URL配置**

所有业务对象必须通过统一动态路由访问：

```python
# ❌ 禁止：在 urls.py 中注册独立路由
router.register(r'my-object', MyObjectViewSet, basename='my-object')

# ✅ 正确：对象自动注册到 /api/objects/{code}/
# 只需确保 BusinessObject 存在即可
```

### 7.2 对象配置要求

在创建新业务对象时，必须在系统中配置以下信息：

| 配置项 | 说明 | 示例 | 约束 |
|--------|------|------|------|
| object_code | 对象代码（唯一） | "AssetPickup" | 必填，大驼峰命名 |
| name | 对象名称 | "资产领用单" | 必填 |
| is_hardcoded | 是否硬编码对象 | true | 必填 |
| django_model_path | Django模型路径 | "apps.assets.models.AssetPickup" | 硬编码对象必填 |

### 7.3 标准 CRUD 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/objects/{object_code}/` | 列表查询（分页、过滤、搜索） |
| POST | `/api/objects/{object_code}/` | 创建记录 |
| GET | `/api/objects/{object_code}/{id}/` | 获取详情 |
| PUT | `/api/objects/{object_code}/{id}/` | 完整更新 |
| PATCH | `/api/objects/{object_code}/{id}/` | 部分更新 |
| DELETE | `/api/objects/{object_code}/{id}/` | 删除记录（软删除） |

### 7.4 批量操作端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/objects/{object_code}/batch-delete/` | 批量软删除 |
| POST | `/api/objects/{object_code}/batch-restore/` | 批量恢复 |
| POST | `/api/objects/{object_code}/batch-update/` | 批量更新 |

### 7.5 元数据端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/objects/{object_code}/metadata/` | 获取对象元数据 |
| GET | `/api/objects/{object_code}/schema/` | 获取数据验证Schema |

### 7.6 扩展操作端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/objects/{object_code}/deleted/` | 查询已删除记录 |
| POST | `/api/objects/{object_code}/{id}/restore/` | 恢复单条记录 |

### 7.7 请求/响应示例

#### 列表查询

```http
GET /api/objects/AssetPickup/?page=1&page_size=20&status=pending
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "pickup_code": "PICKUP001",
                "asset_name": "办公电脑",
                "status": "pending",
                "created_at": "2026-01-15T10:30:00Z"
            }
        ],
        "layout_meta": {
            "columns": [...],
            "page_size": 20
        }
    }
}
```

#### 创建记录

```http
POST /api/objects/AssetPickup/
Content-Type: application/json

{
    "pickup_code": "PICKUP001",
    "asset_id": "550e8400-e29b-41d4-a716-446655440000",
    "pickup_date": "2026-01-15",
    "pickup_user_id": "550e8400-e29b-41d4-a716-446655440001",
    "reason": "部门领用"
}
```

**响应**：

```http
HTTP/1.1 201 Created

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "pickup_code": "PICKUP001",
        "status": "pending",
        "created_at": "2026-01-15T10:30:00Z"
    }
}
```

#### 获取元数据

```http
GET /api/objects/AssetPickup/metadata/
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "business_object": {
            "code": "AssetPickup",
            "name": "资产领用单",
            "description": "资产领用申请单据",
            "is_hardcoded": true,
            "enable_workflow": true,
            "django_model_path": "apps.assets.models.AssetPickup"
        },
        "field_definitions": [
            {
                "code": "pickup_code",
                "name": "领用单号",
                "field_type": "text",
                "is_required": true,
                "is_unique": true
            },
            {
                "code": "asset",
                "name": "领用资产",
                "field_type": "reference",
                "is_required": true,
                "reference_object": "Asset"
            }
        ],
        "list_layout": {...},
        "form_layout": {...}
    }
}
```

### 7.8 前端调用规范

**使用统一动态 API 客户端**：

```javascript
// frontend/src/api/dynamic.js
import { createObjectClient } from '@/api/dynamic'

// 创建对象客户端
const api = createObjectClient('AssetPickup')

// 列表查询
const { data } = await api.list({
  page: 1,
  page_size: 20,
  status: 'pending'
})

// 创建记录
const { data } = await api.create({
  pickup_code: 'PICKUP001',
  asset_id: '...',
  pickup_date: '2026-01-15'
})

// 更新记录
const { data } = await api.update(id, {
  status: 'approved'
})

// 删除记录
await api.delete(id)

// 批量删除
const { data } = await api.batchDelete([id1, id2, id3])
```

### 7.9 动态字段过滤

支持基于`FieldDefinition`的动态字段过滤：

```http
GET /api/objects/AssetPickup/?pickup_code__icontains=PICKUP&pickup_date__gte=2026-01-01
```

过滤规则：

| 字段类型 | 支持的过滤 | 示例 |
|---------|-----------|------|
| text/textarea | `__icontains`, `__exact` | `?name__icontains=电脑` |
| number/integer/float | `__gte`, `__lte`, 精确匹配 | `?price__gte=1000` |
| date/datetime | `__gte`, `__lte`, 精确匹配 | `?date__gte=2026-01-01` |
| choice/multi_choice | 精确匹配, 多选 | `?status=pending` |
| reference/user/department | UUID匹配 | `?user_id=xxx` |

---

## 8. 动态数据 API（已弃用 - 请使用第7节动态对象路由）

> **注意**: 本节描述的传统动态数据API已被第7节的动态对象路由API取代。
> 新开发功能请直接使用 `/api/objects/{object_code}/` 端点。

元数据驱动的动态数据API，支持基于BusinessObject的零代码CRUD操作。

### 8.1 获取元数据

```http
GET /api/dynamic/{object_code}/metadata/
```

**响应**

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "business_object": {
            "code": "Asset",
            "name": "资产卡片",
            "description": "固定资产卡片信息",
            "enable_workflow": true,
            "enable_version": false
        },
        "field_definitions": [
            {
                "code": "asset_code",
                "name": "资产编码",
                "field_type": "text",
                "is_required": true,
                "is_readonly": false,
                "is_searchable": true,
                "sortable": true,
                "show_in_filter": true,
                "is_unique": true,
                "max_length": 50,
                "placeholder": "请输入资产编码",
                "description": "资产唯一编码"
            }
        ],
        "list_layout": {
            "code": "asset_list",
            "name": "资产列表",
            "layout_type": "list",
            "layout_config": {
                "columns": [
                    {"field": "asset_code", "label": "资产编码", "width": 150},
                    {"field": "asset_name", "label": "资产名称", "width": 200}
                ],
                "page_size": 20
            }
        },
        "form_layout": {
            "code": "asset_form",
            "name": "资产表单",
            "layout_type": "form",
            "layout_config": {
                "sections": [
                    {
                        "title": "基本信息",
                        "fields": ["asset_code", "asset_name", "category"]
                    }
                ]
            }
        }
    }
}
```

### 8.2 获取数据模式（Schema）

```http
GET /api/dynamic/{object_code}/schema/
```

**响应**（用于前端表单验证）

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "type": "object",
        "properties": {
            "asset_code": {
                "type": "string",
                "title": "资产编码",
                "maxLength": 50
            },
            "purchase_price": {
                "type": "number",
                "title": "采购价格",
                "minimum": 0,
                "maximum": 1000000
            },
            "category": {
                "type": "string",
                "title": "资产分类",
                "enum": ["electronics", "furniture", "vehicle"]
            }
        },
        "required": ["asset_code", "asset_name"]
    }
}
```

### 8.3 动态数据 CRUD

#### 列表查询

```http
GET /api/dynamic/{object_code}/?page=1&page_size=20&search=电脑
```

**响应**

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "business_object": "Asset",
                "asset_code": "ASSET001",
                "asset_name": "办公电脑",
                "category": "electronics",
                "created_at": "2026-01-14T10:30:00Z"
            }
        ],
        "layout_meta": {
            "columns": [...],
            "page_size": 20
        }
    }
}
```

#### 创建数据

```http
POST /api/dynamic/{object_code}/
Content-Type: application/json

{
    "asset_code": "ASSET001",
    "asset_name": "办公电脑",
    "category": "electronics",
    "purchase_price": 5000.00
}
```

#### 更新数据

```http
PUT /api/dynamic/{object_code}/{id}/
Content-Type: application/json

{
    "asset_name": "办公电脑（更新）",
    "status": "in_use"
}
```

#### 删除数据

```http
DELETE /api/dynamic/{object_code}/{id}/
```

#### 批量删除

```http
POST /api/dynamic/{object_code}/batch-delete/
Content-Type: application/json

{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 8.4 动态字段过滤

支持基于`FieldDefinition`的动态字段过滤：

```http
GET /api/dynamic/Asset/?asset_code__icontains=ASSET&purchase_price__gte=1000
```

过滤规则：

| 字段类型 | 支持的过滤 | 示例 |
|---------|-----------|------|
| text/textarea | `__icontains`, `__exact` | `?name__icontains=电脑` |
| number/integer/float | `__gte`, `__lte`, 精确匹配 | `?price__gte=1000` |
| date/datetime | `__gte`, `__lte`, 精确匹配 | `?date__from=2026-01-01` |
| choice/multi_choice | 精确匹配, 多选 | `?status=in_use` |
| reference/user/department | UUID匹配 | `?user_id=xxx` |

---

## 9. API 版本控制

### 9.1 版本化策略

采用 URL 路径版本控制方式：

```
/api/v1/          # 当前稳定版本
/api/v2/          # 未来版本
/api/             # 最新版本的别名
```

### 9.2 版本路由配置

| 路由 | 说明 |
|------|------|
| `/api/version/` | API版本信息端点 |
| `/api/v1/` | v1版本路由 |
| `/api/` | 最新版本别名 |

**版本信息响应**:
```json
{
    "success": true,
    "data": {
        "version": "1.0.0",
        "name": "GZEAMS API",
        "description": "Hook Fixed Assets Management API",
        "documentation": "/api/docs/",
        "versions": [
            {"version": "v1", "status": "current", "deprecated": false}
        ]
    }
}
```

### 9.3 版本中间件

| 功能 | 说明 |
|------|------|
| 版本响应头 | 自动添加 `API-Version: 1.0.0` |
| 废弃版本检测 | 自动添加 `Deprecation` 和 `Sunset` 响应头 |
| 速率限制头 | 添加 `X-RateLimit-Limit/Remaining/Reset` |
| 迁移指南 | 废弃版本包含迁移指南链接 |

### 9.4 版本兼容性

| 版本 | 状态 | 发布日期 | 废弃日期 | 支持截止 |
|------|------|----------|----------|----------|
| v1 | Current | 2026-01-15 | - | - |

---

## 10. 数据导入导出 API

### 10.1 数据导出

#### 导出列表数据

```http
POST /api/v1/assets/export/
Content-Type: application/json

{
    "format": "xlsx",           // xlsx, csv, pdf
    "columns": [                // 指定导出列
        "code", "name", "category", "status", "purchase_price"
    ],
    "filters": {                // 导出过滤条件
        "status": "idle",
        "created_at_from": "2026-01-01"
    },
    "options": {
        "sheet_name": "资产列表",
        "include_header": true
    }
}
```

**响应**：

```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="assets_export_20260115.xlsx"

[文件内容]
```

#### 导出模板

```http
GET /api/v1/assets/export-template/
```

**响应**：

```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

[包含表头的模板文件]
```

### 10.2 数据导入

#### 上传导入文件

```http
POST /api/v1/assets/import/
Content-Type: multipart/form-data

file: [Excel文件]
options: {
    "skip_errors": true,      // 跳过错误行继续导入
    "update_existing": false,  // 更新已存在的记录
    "create_missing": true     # 创建缺失的关联数据
}
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "导入任务已创建",
    "data": {
        "task_id": "import-task-uuid-xxx",
        "status": "processing",
        "estimated_time": 30
    }
}
```

#### 查询导入状态

```http
GET /api/v1/assets/import/{task_id}/status/
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "task_id": "import-task-uuid-xxx",
        "status": "completed",      // processing, completed, failed
        "progress": 100,
        "summary": {
            "total": 1000,
            "succeeded": 980,
            "failed": 15,
            "skipped": 5
        },
        "errors": [
            {
                "row": 15,
                "field": "code",
                "message": "资产编码已存在",
                "value": "ASSET001"
            }
        ]
    }
}
```

### 10.3 导入导出 Mixin

| 方法 | 端点 | 说明 |
|------|------|------|
| `export()` | `POST /{resource}/export/` | 导出数据（xlsx/csv/pdf） |
| `import_data()` | `POST /{resource}/import/` | 导入数据（异步） |
| `import_status()` | `GET /{resource}/import/{task_id}/status/` | 查询导入状态 |

**支持格式**:
- 导出: `xlsx`, `csv`, `pdf`
- 导入: `xlsx`, `csv`

**导入任务状态**:
| 状态 | 说明 |
|------|------|
| `processing` | 处理中 |
| `completed` | 已完成 |
| `failed` | 失败 |

---

## 11. 输出产物

| 文件 | 说明 |
|------|------|
| `apps/common/responses/base.py` | BaseResponse 响应类 |
| `apps/common/handlers/exceptions.py` | 统一异常处理器 |
| `apps/common/viewsets/metadata_driven.py` | MetadataDrivenViewSet |
| `apps/common/serializers/metadata_driven.py` | MetadataDrivenSerializer |
| `backend/config/settings.py` | DRF 配置更新 |
