# Phase 7.4: 智能搜索增强 - API接口设计

## 1. API概述

### 1.1 接口规范

所有API遵循GZEAMS统一接口规范：

| 规范项 | 说明 |
|--------|------|
| 基础URL | `/api/search/` |
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
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5,
        "results": [...],
        "aggregations": {...}
    }
}
```

**错误响应**：
```json
{
    "success": false,
    "error": {
        "code": "SEARCH_INDEX_UNAVAILABLE",
        "message": "搜索服务不可用",
        "details": {}
    }
}
```

---

## 2. 搜索接口

### 2.1 全文搜索资产

**请求**：
```http
POST /api/search/assets/
Content-Type: application/json
```

**请求体**：
```json
{
    "keyword": "笔记本",
    "filters": {
        "category": "电子设备",
        "status": "in_use",
        "purchase_price_min": 1000,
        "purchase_price_max": 50000
    },
    "sort_by": "relevance",
    "sort_order": "desc",
    "page": 1,
    "page_size": 20
}
```

**排序选项**：

| 值 | 说明 |
|----|------|
| relevance | 相关性（默认，有关键词时） |
| date | 购置日期 |
| price | 价格 |
| code | 资产编号 |

**筛选字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| category | string | 分类ID |
| status | string | 状态 |
| location | string | 存放位置ID |
| manufacturer | string | 厂商 |
| tags | array | 标签ID数组 |
| purchase_price_min | decimal | 最低价格 |
| purchase_price_max | decimal | 最高价格 |
| purchase_date_from | date | 购买日期起 |
| purchase_date_to | date | 购买日期止 |

**响应示例**：
```json
{
    "success": true,
    "data": {
        "total": 15,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
        "results": [
            {
                "id": "asset-uuid-1",
                "asset_code": "ZC001",
                "asset_name": "<em>笔记本</em>电脑",
                "highlight": {
                    "asset_name": ["<em>笔记本</em>电脑"]
                },
                "score": 2.5,
                "category": "category-uuid",
                "category_name": "电子设备",
                "status": "in_use",
                "status_display": "在用",
                "purchase_price": 5000.00,
                "location": "location-uuid",
                "location_name": "A区仓库",
                "custodian": "user-uuid",
                "custodian_name": "张三",
                "tags": ["tag-uuid-1", "tag-uuid-2"]
            },
            {
                "id": "asset-uuid-2",
                "asset_code": "ZC002",
                "asset_name": "联想<em>笔记本</em>",
                "highlight": {
                    "asset_name": ["联想<em>笔记本</em>"]
                },
                "score": 2.0,
                "category": "category-uuid",
                "category_name": "电子设备",
                "status": "in_use",
                "status_display": "在用",
                "purchase_price": 4500.00,
                "location": "location-uuid",
                "location_name": "A区仓库",
                "custodian": "user-uuid-2",
                "custodian_name": "李四",
                "tags": ["tag-uuid-1"]
            }
        ],
        "aggregations": {
            "category": {
                "category-uuid-1": 12,
                "category-uuid-2": 3
            },
            "status": {
                "in_use": 10,
                "idle": 5
            },
            "location": {
                "location-uuid-1": 8,
                "location-uuid-2": 7
            },
            "manufacturer": {
                "联想": 5,
                "戴尔": 4,
                "惠普": 3,
                "苹果": 3
            },
            "price_ranges": {
                "under_1k": 0,
                "1k_to_5k": 8,
                "5k_to_10k": 5,
                "10k_to_50k": 2,
                "over_50k": 0
            }
        }
    }
}
```

### 2.2 搜索项目

**请求**：
```http
POST /api/search/projects/
Content-Type: application/json
```

**请求体**：
```json
{
    "keyword": "AI平台",
    "filters": {
        "status": "active",
        "project_type": "development"
    },
    "sort_by": "relevance",
    "page": 1,
    "page_size": 20
}
```

**响应**：与资产搜索类似结构

### 2.3 搜索借用单

**请求**：
```http
POST /api/search/loans/
Content-Type: application/json
```

**响应**：与资产搜索类似结构

---

## 3. 搜索建议接口

### 3.1 获取搜索建议

**请求**：
```http
GET /api/search/suggestions/?keyword=笔&type=asset
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| type | string | 否 | 类型: asset/project/loan (默认asset) |

**响应示例**：
```json
{
    "success": true,
    "data": [
        {
            "suggestion": "笔记本",
            "count": 45
        },
        {
            "suggestion": "笔记本电脑",
            "count": 30
        },
        {
            "suggestion": "笔记本支架",
            "count": 5
        }
    ]
}
```

---

## 4. 搜索历史接口

### 4.1 获取搜索历史

**请求**：
```http
GET /api/search/history/?type=asset&limit=10
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | 类型筛选 |
| limit | int | 否 | 返回数量，默认10 |

**响应示例**：
```json
{
    "success": true,
    "data": [
        {
            "id": "history-uuid-1",
            "search_type": "asset",
            "keyword": "笔记本",
            "filters": {
                "category": "电子设备"
            },
            "result_count": 15,
            "search_count": 3,
            "last_searched_at": "2025-01-20T10:30:00Z"
        },
        {
            "id": "history-uuid-2",
            "search_type": "asset",
            "keyword": "服务器",
            "filters": {},
            "result_count": 25,
            "search_count": 1,
            "last_searched_at": "2025-01-19T15:20:00Z"
        }
    ]
}
```

### 4.2 清空搜索历史

**请求**：
```http
DELETE /api/search/history/?type=asset
```

**响应**：
```json
{
    "success": true,
    "message": "已删除15条历史记录"
}
```

---

## 5. 保存的搜索接口

### 5.1 保存搜索

**请求**：
```http
POST /api/search/save/
Content-Type: application/json
```

**请求体**：
```json
{
    "name": "高价值电子设备",
    "search_type": "asset",
    "keyword": "",
    "filters": {
        "category": "电子设备",
        "purchase_price_min": 10000
    },
    "is_public": false
}
```

**响应**：
```json
{
    "success": true,
    "message": "搜索保存成功",
    "data": {
        "id": "saved-uuid-1",
        "name": "高价值电子设备",
        "search_type": "asset",
        "keyword": "",
        "filters": {
            "category": "电子设备",
            "purchase_price_min": 10000
        },
        "is_public": false,
        "use_count": 0
    }
}
```

### 5.2 获取保存的搜索

**请求**：
```http
GET /api/search/saved/?type=asset
```

**响应示例**：
```json
{
    "success": true,
    "data": [
        {
            "id": "saved-uuid-1",
            "name": "高价值电子设备",
            "search_type": "asset",
            "keyword": "",
            "filters": {
                "category": "电子设备",
                "purchase_price_min": 10000
            },
            "is_public": false,
            "use_count": 5,
            "created_at": "2025-01-10T10:00:00Z"
        },
        {
            "id": "saved-uuid-2",
            "name": "闲置资产",
            "search_type": "asset",
            "keyword": "",
            "filters": {
                "status": "idle"
            },
            "is_public": true,
            "use_count": 12,
            "created_at": "2025-01-05T10:00:00Z"
        }
    ]
}
```

### 5.3 使用保存的搜索

**请求**：
```http
POST /api/search/saved/{id}/use/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "saved-uuid-1",
        "name": "高价值电子设备",
        "keyword": "",
        "filters": {
            "category": "电子设备",
            "purchase_price_min": 10000
        }
    }
}
```

### 5.4 更新保存的搜索

**请求**：
```http
PUT /api/search/saved/{id}/
Content-Type: application/json
```

**请求体**：
```json
{
    "name": "高价值电子设备（更新）",
    "filters": {
        "category": "电子设备",
        "purchase_price_min": 15000
    }
}
```

**响应**：同保存搜索

### 5.5 删除保存的搜索

**请求**：
```http
DELETE /api/search/saved/{id}/
```

**响应**：
```json
{
    "success": true,
    "message": "搜索删除成功"
}
```

---

## 6. 热门搜索接口

### 6.1 获取热门搜索

**请求**：
```http
GET /api/search/trending/?type=asset&limit=10
```

**响应示例**：
```json
{
    "success": true,
    "data": [
        {
            "keyword": "笔记本",
            "search_count": 156,
            "result_count_avg": 25
        },
        {
            "keyword": "服务器",
            "search_count": 98,
            "result_count_avg": 12
        },
        {
            "keyword": "打印机",
            "search_count": 67,
            "result_count_avg": 8
        }
    ]
}
```

---

## 7. 错误码

### 7.1 业务错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `SEARCH_INDEX_UNAVAILABLE` | 503 | 搜索服务不可用 |
| `INVALID_SEARCH_QUERY` | 400 | 搜索查询无效 |
| `SEARCH_TIMEOUT` | 504 | 搜索超时 |
| `SEARCH_KEYWORD_TOO_SHORT` | 400 | 搜索关键词过短（小于1个字符） |
| `SAVED_SEARCH_NOT_FOUND` | 404 | 保存的搜索不存在 |
| `SAVED_SEARCH_NAME_EXISTS` | 400 | 搜索名称已存在 |
| `INVALID_SORT_FIELD` | 400 | 无效的排序字段 |
| `INVALID_SORT_ORDER` | 400 | 无效的排序方向 |

### 7.2 错误响应示例

```json
{
    "success": false,
    "error": {
        "code": "SEARCH_INDEX_UNAVAILABLE",
        "message": "搜索服务暂时不可用，请稍后重试",
        "details": {
            "reason": "Connection timeout",
            "retry_after": 60
        }
    }
}
```

```json
{
    "success": false,
    "error": {
        "code": "SEARCH_KEYWORD_TOO_SHORT",
        "message": "搜索关键词至少需要1个字符",
        "details": {
            "min_length": 1,
            "provided_length": 0
        }
    }
}
```

---

## 8. 高级搜索功能

### 8.1 拼音搜索

支持拼音首字母和全拼搜索：

| 输入 | 匹配示例 |
|------|---------|
| `bj` | 笔记本、笔记本支架 |
| `notebook` | 笔记本电脑 |
| `zq` | 服务器、质检 |

### 8.2 模糊匹配

支持拼写错误和模糊匹配：

| 输入 | 匹配示例 |
|------|---------|
| `bijiben` | 笔记本 |
| `lenovo` | 联想 |

### 8.3 通配符搜索

支持通配符：

| 通配符 | 说明 | 示例 |
|--------|------|------|
| `?` | 匹配单个字符 | `笔记本?` 匹配 "笔记本电脑" |
| `*` | 匹配零个或多个字符 | `笔记本*` 匹配 "笔记本电脑" 和 "笔记本支架" |

### 8.4 短语搜索

支持引号包裹的短语精确搜索：

| 输入 | 说明 |
|------|------|
| `"MacBook Pro"` | 精确匹配 "MacBook Pro" |
| `MacBook Pro` | 分别匹配 "MacBook" 和 "Pro" |

---

## 9. 搜索配置接口

### 9.1 获取搜索配置

**请求**：
```http
GET /api/search/config/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "enabled_features": {
            "fulltext_search": true,
            "pinyin_search": true,
            "fuzzy_search": true,
            "wildcard_search": true,
            "phrase_search": true,
            "suggestions": true,
            "search_history": true,
            "saved_searches": true
        },
        "limits": {
            "max_results": 10000,
            "max_page_size": 100,
            "max_history_per_user": 100,
            "max_saved_searches_per_user": 50
        },
        "search_fields": {
            "asset": {
                "name": {
                    "boost": 3.0,
                    "analyzer": "ik_max_word"
                },
                "code": {
                    "boost": 2.0,
                    "analyzer": "ik_max_word"
                },
                "specification": {
                    "boost": 1.5,
                    "analyzer": "ik_max_word"
                }
            }
        }
    }
}
```

---

## 10. 管理接口

### 10.1 重建索引

**请求**：
```http
POST /api/search/admin/reindex/
Content-Type: application/json
```

**请求体**：
```json
{
    "index_type": "asset"
}
```

**响应**：
```json
{
    "success": true,
    "message": "索引重建任务已提交",
    "data": {
        "task_id": "task-uuid-1",
        "status": "pending",
        "estimated_records": 1500
    }
}
```

### 10.2 获取索引状态

**请求**：
```http
GET /api/search/admin/index-status/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "asset_index": {
            "docs": 1523,
            "size": "2.5MB",
            "status": "green",
            "last_updated": "2025-01-20T10:00:00Z"
        },
        "project_index": {
            "docs": 45,
            "size": "50KB",
            "status": "green",
            "last_updated": "2025-01-20T10:00:00Z"
        }
    }
}
```

### 10.3 搜索统计

**请求**：
```http
GET /api/search/admin/statistics/?from=2025-01-01&to=2025-01-20
```

**响应**：
```json
{
    "success": true,
    "data": {
        "total_searches": 1523,
        "unique_users": 45,
        "avg_results": 12.5,
        "top_keywords": [
            {"keyword": "笔记本", "count": 156},
            {"keyword": "服务器", "count": 98},
            {"keyword": "打印机", "count": 67}
        ],
        "zero_result_rate": 0.05,
        "avg_response_time_ms": 45
    }
}
```
