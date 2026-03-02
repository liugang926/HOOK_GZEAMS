# Phase 7.3: 资产标签系统 - API接口设计

## 1. API概述

### 1.1 接口规范

所有API遵循GZEAMS统一接口规范：

| 规范项 | 说明 |
|--------|------|
| 基础URL | `/api/tags/` |
| 认证方式 | JWT Token (Header: Authorization: Bearer {token}) |
| 响应格式 | JSON |
| 编码 | UTF-8 |

### 1.2 统一响应格式

**成功响应**：
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

**列表响应（分页）**：
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/tags/?page=2",
        "previous": null,
        "results": [...]
    }
}
```

**错误响应**：
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "name": ["标签名称不能为空"]
        }
    }
}
```

---

## 2. 标签组接口

### 2.1 标签组列表

**请求**：
```http
GET /api/tags/groups/
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 否 | 是否只显示启用的标签组 |
| is_system | boolean | 否 | 是否只显示系统标签组 |
| search | string | 否 | 搜索标签组名称 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**响应示例**：
```json
{
    "success": true,
    "data": {
        "count": 5,
        "results": [
            {
                "id": "tag-group-uuid-1",
                "name": "使用状态",
                "code": "usage_status",
                "description": "资产当前使用状态",
                "color": "#409eff",
                "icon": "status",
                "sort_order": 1,
                "is_system": true,
                "is_active": true,
                "tags_count": 4,
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z"
            },
            {
                "id": "tag-group-uuid-2",
                "name": "资产来源",
                "code": "asset_source",
                "description": "资产来源方式",
                "color": "#67c23a",
                "icon": "source",
                "sort_order": 2,
                "is_system": true,
                "is_active": true,
                "tags_count": 4,
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z",
                "updated_at": "2025-01-01T10:00:00Z"
            }
        ]
    }
}
```

### 2.2 创建标签组

**请求**：
```http
POST /api/tags/groups/
Content-Type: application/json
```

**请求体**：
```json
{
    "name": "特殊管理",
    "code": "special_management",
    "description": "需要特殊管理的资产",
    "color": "#f56c6c",
    "icon": "warning",
    "sort_order": 10,
    "is_active": true
}
```

**响应**：
```json
{
    "success": true,
    "message": "标签组创建成功",
    "data": {
        "id": "new-tag-group-uuid",
        "name": "特殊管理",
        "code": "special_management",
        "description": "需要特殊管理的资产",
        "color": "#f56c6c",
        "icon": "warning",
        "sort_order": 10,
        "is_system": false,
        "is_active": true,
        "tags_count": 0
    }
}
```

### 2.3 获取标签组详情

**请求**：
```http
GET /api/tags/groups/{id}/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "tag-group-uuid-1",
        "name": "使用状态",
        "code": "usage_status",
        "description": "资产当前使用状态",
        "color": "#409eff",
        "icon": "status",
        "sort_order": 1,
        "is_system": true,
        "is_active": true,
        "tags_count": 4,
        "tags": [
            {
                "id": "tag-uuid-1",
                "name": "在用",
                "code": "in_use",
                "color": "#409eff",
                "sort_order": 1,
                "is_active": true,
                "asset_count": 150
            },
            {
                "id": "tag-uuid-2",
                "name": "闲置",
                "code": "idle",
                "color": "#909399",
                "sort_order": 2,
                "is_active": true,
                "asset_count": 45
            }
        ],
        "organization": "org-uuid",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-01T10:00:00Z"
    }
}
```

### 2.4 更新标签组

**请求**：
```http
PUT /api/tags/groups/{id}/
Content-Type: application/json
```

**请求体**：
```json
{
    "name": "使用状态（更新）",
    "description": "资产当前使用状态描述",
    "color": "#409eff",
    "sort_order": 1
}
```

**响应**：同创建响应

### 2.5 删除标签组

**请求**：
```http
DELETE /api/tags/groups/{id}/
```

**响应**：
```json
{
    "success": true,
    "message": "标签组删除成功"
}
```

**错误响应（系统标签组）**：
```json
{
    "success": false,
    "error": {
        "code": "SYSTEM_TAG_GROUP_CANNOT_DELETE",
        "message": "系统标签组不能删除"
    }
}
```

---

## 3. 标签接口

### 3.1 标签列表

**请求**：
```http
GET /api/tags/
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tag_group | uuid | 否 | 筛选标签组ID |
| is_active | boolean | 否 | 是否只显示启用的标签 |
| search | string | 否 | 搜索标签名称 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应示例**：
```json
{
    "success": true,
    "data": {
        "count": 15,
        "results": [
            {
                "id": "tag-uuid-1",
                "tag_group": "tag-group-uuid-1",
                "group_name": "使用状态",
                "group_color": "#409eff",
                "name": "在用",
                "code": "in_use",
                "color": "#409eff",
                "icon": "",
                "description": "资产正在使用中",
                "sort_order": 1,
                "is_active": true,
                "asset_count": 150,
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z"
            },
            {
                "id": "tag-uuid-2",
                "tag_group": "tag-group-uuid-1",
                "group_name": "使用状态",
                "group_color": "#409eff",
                "name": "闲置",
                "code": "idle",
                "color": "#909399",
                "icon": "",
                "description": "资产闲置中",
                "sort_order": 2,
                "is_active": true,
                "asset_count": 45,
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z"
            }
        ]
    }
}
```

### 3.2 创建标签

**请求**：
```http
POST /api/tags/
Content-Type: application/json
```

**请求体**：
```json
{
    "tag_group": "tag-group-uuid-1",
    "name": "待维修",
    "code": "pending_repair",
    "color": "#e6a23c",
    "icon": "tool",
    "description": "资产需要维修",
    "sort_order": 5
}
```

**响应**：
```json
{
    "success": true,
    "message": "标签创建成功",
    "data": {
        "id": "new-tag-uuid",
        "tag_group": "tag-group-uuid-1",
        "group_name": "使用状态",
        "name": "待维修",
        "code": "pending_repair",
        "color": "#e6a23c",
        "icon": "tool",
        "description": "资产需要维修",
        "sort_order": 5,
        "is_active": true,
        "asset_count": 0
    }
}
```

### 3.3 获取标签详情

**请求**：
```http
GET /api/tags/{id}/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "tag-uuid-1",
        "tag_group": "tag-group-uuid-1",
        "group_name": "使用状态",
        "group_color": "#409eff",
        "name": "在用",
        "code": "in_use",
        "color": "#409eff",
        "icon": "",
        "description": "资产正在使用中",
        "sort_order": 1,
        "is_active": true,
        "asset_count": 150,
        "tagged_assets": [
            {
                "asset_id": "asset-uuid-1",
                "asset_code": "ZC001",
                "asset_name": "MacBook Pro",
                "tagged_at": "2025-01-10T10:00:00Z",
                "tagged_by": {
                    "id": "user-uuid",
                    "username": "admin",
                    "full_name": "管理员"
                },
                "notes": ""
            }
        ],
        "organization": "org-uuid",
        "created_at": "2025-01-01T10:00:00Z"
    }
}
```

### 3.4 更新标签

**请求**：
```http
PUT /api/tags/{id}/
Content-Type: application/json
```

**请求体**：
```json
{
    "name": "在用（更新）",
    "description": "资产正在使用中",
    "color": "#409eff"
}
```

**响应**：同创建响应

### 3.5 删除标签

**请求**：
```http
DELETE /api/tags/{id}/
```

**响应**：
```json
{
    "success": true,
    "message": "标签删除成功"
}
```

### 3.6 获取标签统计

**请求**：
```http
GET /api/tags/statistics/
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| tag_group | uuid | 否 | 筛选标签组 |

**响应**：
```json
{
    "success": true,
    "data": {
        "total_tags": 15,
        "total_tagged_assets": 250,
        "tag_statistics": [
            {
                "id": "tag-uuid-1",
                "tag_group": "tag-group-uuid-1",
                "group_name": "使用状态",
                "name": "在用",
                "code": "in_use",
                "color": "#409eff",
                "asset_count": 150,
                "percentage": 60
            },
            {
                "id": "tag-uuid-2",
                "tag_group": "tag-group-uuid-1",
                "group_name": "使用状态",
                "name": "闲置",
                "code": "idle",
                "color": "#909399",
                "asset_count": 45,
                "percentage": 18
            },
            {
                "id": "tag-uuid-3",
                "tag_group": "tag-group-uuid-1",
                "group_name": "使用状态",
                "name": "待维修",
                "code": "pending_repair",
                "color": "#e6a23c",
                "asset_count": 30,
                "percentage": 12
            },
            {
                "id": "tag-uuid-4",
                "tag_group": "tag-group-uuid-2",
                "group_name": "资产来源",
                "name": "采购",
                "code": "purchased",
                "color": "#67c23a",
                "asset_count": 200,
                "percentage": 80
            }
        ]
    }
}
```

---

## 4. 资产标签关联接口

### 4.1 获取资产标签

**请求**：
```http
GET /api/assets/{asset_id}/tags/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "asset_id": "asset-uuid-1",
        "asset_code": "ZC001",
        "asset_name": "MacBook Pro",
        "tags": [
            {
                "id": "relation-uuid-1",
                "tag": {
                    "id": "tag-uuid-1",
                    "name": "在用",
                    "code": "in_use",
                    "color": "#409eff",
                    "group_name": "使用状态"
                },
                "tagged_by": {
                    "id": "user-uuid",
                    "username": "admin",
                    "full_name": "管理员"
                },
                "tagged_at": "2025-01-10T10:00:00Z",
                "notes": "日常使用"
            },
            {
                "id": "relation-uuid-2",
                "tag": {
                    "id": "tag-uuid-5",
                    "name": "关键",
                    "code": "critical",
                    "color": "#f56c6c",
                    "group_name": "重要性"
                },
                "tagged_by": {
                    "id": "user-uuid",
                    "username": "admin",
                    "full_name": "管理员"
                },
                "tagged_at": "2025-01-10T10:00:00Z",
                "notes": "核心设备"
            }
        ]
    }
}
```

### 4.2 为资产添加标签

**请求**：
```http
POST /api/assets/{asset_id}/tags/
Content-Type: application/json
```

**请求体（单个标签）**：
```json
{
    "tag_id": "tag-uuid-1",
    "notes": "日常使用"
}
```

**请求体（多个标签）**：
```json
{
    "tag_ids": ["tag-uuid-1", "tag-uuid-5"],
    "notes": "批量打标签"
}
```

**响应**：
```json
{
    "success": true,
    "message": "标签添加成功",
    "data": {
        "added_count": 2,
        "relations": [
            {
                "id": "relation-uuid-1",
                "tag_id": "tag-uuid-1",
                "tag_name": "在用",
                "tagged_at": "2025-01-20T10:00:00Z"
            },
            {
                "id": "relation-uuid-2",
                "tag_id": "tag-uuid-5",
                "tag_name": "关键",
                "tagged_at": "2025-01-20T10:00:00Z"
            }
        ]
    }
}
```

### 4.3 移除资产标签

**请求**：
```http
DELETE /api/assets/{asset_id}/tags/{tag_id}/
```

**响应**：
```json
{
    "success": true,
    "message": "标签移除成功"
}
```

### 4.4 批量添加标签

**请求**：
```http
POST /api/tags/batch-add/
Content-Type: application/json
```

**请求体**：
```json
{
    "asset_ids": ["asset-uuid-1", "asset-uuid-2", "asset-uuid-3"],
    "tag_ids": ["tag-uuid-1", "tag-uuid-5"],
    "notes": "批量标记为在用+关键"
}
```

**响应**：
```json
{
    "success": true,
    "message": "批量打标签完成",
    "summary": {
        "total_assets": 3,
        "total_tags": 2,
        "relations_created": 6,
        "skipped": 0
    },
    "data": [
        {
            "asset_id": "asset-uuid-1",
            "asset_code": "ZC001",
            "tags_added": 2
        },
        {
            "asset_id": "asset-uuid-2",
            "asset_code": "ZC002",
            "tags_added": 2
        },
        {
            "asset_id": "asset-uuid-3",
            "asset_code": "ZC003",
            "tags_added": 2
        }
    ]
}
```

### 4.5 批量移除标签

**请求**：
```http
POST /api/tags/batch-remove/
Content-Type: application/json
```

**请求体**：
```json
{
    "asset_ids": ["asset-uuid-1", "asset-uuid-2"],
    "tag_ids": ["tag-uuid-1"]
}
```

**响应**：
```json
{
    "success": true,
    "message": "批量移除标签完成",
    "summary": {
        "total_assets": 2,
        "relations_removed": 2
    }
}
```

### 4.6 按标签查询资产

**请求**：
```http
POST /api/assets/by-tags/
Content-Type: application/json
```

**请求体（AND关系 - 资产必须包含所有指定标签）**：
```json
{
    "tag_ids": ["tag-uuid-1", "tag-uuid-5"],
    "match_type": "and",
    "page": 1,
    "page_size": 20
}
```

**请求体（OR关系 - 资产包含任一标签即可）**：
```json
{
    "tag_ids": ["tag-uuid-1", "tag-uuid-2"],
    "match_type": "or",
    "page": 1,
    "page_size": 20
}
```

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 50,
        "match_type": "and",
        "tags": [
            {"id": "tag-uuid-1", "name": "在用", "color": "#409eff"},
            {"id": "tag-uuid-5", "name": "关键", "color": "#f56c6c"}
        ],
        "results": [
            {
                "id": "asset-uuid-1",
                "asset_code": "ZC001",
                "asset_name": "MacBook Pro",
                "category_name": "电子设备",
                "matching_tags": [
                    {"id": "tag-uuid-1", "name": "在用", "color": "#409eff"},
                    {"id": "tag-uuid-5", "name": "关键", "color": "#f56c6c"}
                ]
            }
        ]
    }
}
```

---

## 5. 自动化规则接口

### 5.1 自动化规则列表

**请求**：
```http
GET /api/tags/auto-rules/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 3,
        "results": [
            {
                "id": "rule-uuid-1",
                "name": "高值设备自动打标",
                "rule_type": "condition",
                "tag": {
                    "id": "tag-uuid-5",
                    "name": "关键",
                    "color": "#f56c6c"
                },
                "condition": {
                    "field": "purchase_price",
                    "operator": "gt",
                    "value": 10000
                },
                "is_active": true,
                "last_executed_at": "2025-01-20T01:00:00Z",
                "created_at": "2025-01-01T10:00:00Z"
            }
        ]
    }
}
```

### 5.2 创建自动化规则

**请求**：
```http
POST /api/tags/auto-rules/
Content-Type: application/json
```

**请求体（条件规则）**：
```json
{
    "name": "高值设备自动打标",
    "rule_type": "condition",
    "tag_id": "tag-uuid-5",
    "condition": {
        "field": "purchase_price",
        "operator": "gt",
        "value": 10000
    },
    "is_active": true
}
```

**请求体（定时规则）**：
```json
{
    "name": "每月折旧完毕标记",
    "rule_type": "schedule",
    "tag_id": "tag-uuid-10",
    "schedule": "0 0 1 * *",
    "is_active": true
}
```

**响应**：
```json
{
    "success": true,
    "message": "自动化规则创建成功",
    "data": {
        "id": "new-rule-uuid",
        "name": "高值设备自动打标",
        "rule_type": "condition",
        "tag": {...},
        "is_active": true
    }
}
```

### 5.3 手动执行自动化规则

**请求**：
```http
POST /api/tags/auto-rules/{id}/execute/
```

**响应**：
```json
{
    "success": true,
    "message": "规则执行完成",
    "data": {
        "rule_id": "rule-uuid-1",
        "executed_at": "2025-01-20T10:30:00Z",
        "tags_added": 15,
        "assets_processed": 100,
        "details": [
            {
                "asset_id": "asset-uuid-1",
                "asset_code": "ZC001",
                "tag_added": "关键"
            }
        ]
    }
}
```

---

## 6. 错误码

### 6.1 业务错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `TAG_GROUP_NOT_FOUND` | 404 | 标签组不存在 |
| `TAG_GROUP_CODE_EXISTS` | 400 | 标签组编码已存在 |
| `SYSTEM_TAG_GROUP_CANNOT_DELETE` | 403 | 系统标签组不能删除 |
| `SYSTEM_TAG_CANNOT_DELETE` | 403 | 系统标签不能删除 |
| `TAG_NOT_FOUND` | 404 | 标签不存在 |
| `TAG_ALREADY_EXISTS` | 400 | 标签已存在（同一标签组下编码重复） |
| `TAG_ALREADY_ON_ASSET` | 400 | 资产已有该标签 |
| `TAG_NOT_ON_ASSET` | 404 | 资产没有该标签 |
| `ASSET_TAG_LIMIT_EXCEEDED` | 400 | 资产标签数量超过限制（默认20个） |
| `INVALID_CONDITION_EXPRESSION` | 400 | 条件表达式无效 |
| `TAG_GROUP_HAS_TAGS` | 400 | 标签组下还有标签，无法删除 |

### 6.2 错误响应示例

```json
{
    "success": false,
    "error": {
        "code": "ASSET_TAG_LIMIT_EXCEEDED",
        "message": "资产标签数量超过限制",
        "details": {
            "limit": 20,
            "current": 20
        }
    }
}
```

```json
{
    "success": false,
    "error": {
        "code": "SYSTEM_TAG_GROUP_CANNOT_DELETE",
        "message": "系统标签组不能删除",
        "details": {
            "tag_group_name": "使用状态",
            "reason": "系统预设标签组，用于系统功能"
        }
    }
}
```

---

## 7. 初始化数据

### 7.1 预设标签组初始化

**请求**：
```http
POST /api/tags/initialize/
```

**响应**：
```json
{
    "success": true,
    "message": "预设标签组初始化完成",
    "data": {
        "tag_groups_created": 5,
        "tags_created": 17,
        "details": [
            {
                "group_name": "使用状态",
                "group_code": "usage_status",
                "tags_created": 4
            },
            {
                "group_name": "资产来源",
                "group_code": "asset_source",
                "tags_created": 4
            },
            {
                "group_name": "重要性",
                "group_code": "importance",
                "tags_created": 3
            },
            {
                "group_name": "盘点状态",
                "group_code": "inventory",
                "tags_created": 3
            },
            {
                "group_name": "特殊管理",
                "group_code": "special",
                "tags_created": 3
            }
        ]
    }
}
```

---

## 8. Webhook事件

### 8.1 标签添加事件

```json
{
    "event": "tag.added",
    "timestamp": "2025-01-20T10:00:00Z",
    "data": {
        "asset_id": "asset-uuid-1",
        "asset_code": "ZC001",
        "tag": {
            "id": "tag-uuid-1",
            "name": "在用",
            "code": "in_use"
        },
        "tagged_by": {
            "id": "user-uuid",
            "username": "admin"
        }
    }
}
```

### 8.2 标签移除事件

```json
{
    "event": "tag.removed",
    "timestamp": "2025-01-20T10:00:00Z",
    "data": {
        "asset_id": "asset-uuid-1",
        "asset_code": "ZC001",
        "tag": {
            "id": "tag-uuid-1",
            "name": "在用",
            "code": "in_use"
        },
        "removed_by": {
            "id": "user-uuid",
            "username": "admin"
        }
    }
}
```
