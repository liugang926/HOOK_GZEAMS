# Phase 1.4: 资产卡片CRUD - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/assets/assets/` | 获取资产列表 |
| POST | `/api/assets/assets/` | 创建资产 |
| GET | `/api/assets/assets/{id}/` | 获取资产详情 |
| PUT | `/api/assets/assets/{id}/` | 更新资产 |
| DELETE | `/api/assets/assets/{id}/` | 删除资产 |
| GET | `/api/assets/assets/statistics/` | 获取资产统计 |
| GET | `/api/assets/assets/{id}/qr_code/` | 获取资产二维码图片 |
| POST | `/api/assets/assets/{id}/change_status/` | 变更资产状态 |
| POST | `/api/assets/assets/batch_change_status/` | 批量变更状态 |

---

## 1. 获取资产列表

**请求**
```
GET /api/assets/assets/?search=MacBook&category=1&status=in_use&page=1&page_size=20
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| search | string | 搜索关键词（编码/名称/序列号） |
| category | integer | 资产分类ID |
| status | string | 资产状态 |
| department | integer | 使用部门ID |
| custodian | integer | 保管人ID |
| location | integer | 存放地点ID |
| order_by | string | 排序字段 |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 156,
    "next": "https://api.example.com/api/assets/assets/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "asset_code": "ZC20240601001",
        "asset_name": "MacBook Pro",
        "asset_category": {
          "id": 1,
          "code": "200101",
          "name": "台式机"
        },
        "specification": "M2 Pro 16G 512G",
        "brand": "Apple",
        "model": "MacBook Pro",
        "serial_number": "C02XXXXXXXX",
        "unit": "台",
        "purchase_price": 12999.00,
        "current_value": 11699.10,
        "accumulated_depreciation": 1299.90,
        "net_value": 11699.10,
        "purchase_date": "2024-01-01",
        "useful_life": 60,
        "residual_rate": 5.00,
        "department": {
          "id": 3,
          "name": "研发部"
        },
        "location": {
          "id": 10,
          "name": "3楼A区",
          "path": "总部/3楼/A区"
        },
        "custodian": {
          "id": 5,
          "username": "zhangsan",
          "real_name": "张三"
        },
        "user": {
          "id": 5,
          "username": "zhangsan"
        },
        "asset_status": "in_use",
        "asset_status_label": "在用",
        "qr_code": "uuid-string",
        "images": ["https://example.com/image1.jpg"],
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-06-15T14:30:00Z"
      }
    ]
  }
}
```

---

## 2. 创建资产

**请求**
```
POST /api/assets/assets/
Content-Type: application/json

{
  "asset_name": "Dell 显示器",
  "asset_category": 2,
  "specification": "27英寸 4K",
  "brand": "Dell",
  "unit": "台",
  "purchase_price": 3500.00,
  "purchase_date": "2024-06-15",
  "useful_life": 60,
  "residual_rate": 5,
  "department": 3,
  "location": 10,
  "custodian": 5,
  "asset_status": "in_use"
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 157,
    "asset_code": "ZC20240615001",
    "asset_name": "Dell 显示器",
    "qr_code": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**错误响应**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "验证失败",
    "details": {
      "asset_name": ["此字段为必填项"],
      "asset_category": ["此字段为必填项"]
    }
  }
}
```

---

## 3. 获取资产详情

**请求**
```
GET /api/assets/assets/{id}/
```

**响应**
```json
{
  "success": true,
  "data": {
    "asset": {
      "id": 1,
      "asset_code": "ZC20240601001",
      "asset_name": "MacBook Pro"
    },
    "history": [
      {
        "type": "status_change",
        "date": "2024-06-15T10:00:00Z",
        "description": "状态变更: 待入库 → 在用",
        "operator": "admin",
        "reason": "新资产入库"
      },
      {
        "type": "pickup",
        "date": "2024-06-16T14:30:00Z",
        "description": "领用: LY20240616001",
        "operator": "zhangsan"
      }
    ]
  }
}
```

---

## 4. 更新资产

**请求**
```
PUT /api/assets/assets/{id}/
Content-Type: application/json

{
  "asset_name": "MacBook Pro (已升级)",
  "custodian": 6
}
```

**响应**
```
HTTP 200 OK

{
  "success": true,
  "message": "更新成功",
  "data": {
    "id": 1,
    "asset_name": "MacBook Pro (已升级)",
    "custodian": {
      "id": 6,
      "username": "lisi",
      "real_name": "李四"
    }
  }
}
```

---

## 5. 删除资产

**请求**
```
DELETE /api/assets/assets/{id}/
```

**响应**
```
HTTP 200 OK

{
  "success": true,
  "message": "删除成功"
}
```

**错误响应 - 资产不存在**
```
HTTP 404 Not Found

{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "资产不存在"
  }
}
```

**错误响应 - 有未完成的业务单据**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "该资产存在未完成的业务单据，无法删除"
  }
}
```

---

## 6. 获取资产统计

**请求**
```
GET /api/assets/assets/statistics/
```

**响应**
```json
{
  "success": true,
  "data": {
    "total": 156,
    "by_status": [
      {"asset_status": "in_use", "count": 120},
      {"asset_status": "idle", "count": 25},
      {"asset_status": "maintenance", "count": 8},
      {"asset_status": "pending", "count": 3}
    ],
    "by_category": [
      {"asset_category__name": "计算机设备", "count": 80},
      {"asset_category__name": "办公设备", "count": 45},
      {"asset_category__name": "车辆", "count": 31}
    ],
    "total_value": 2450000.00,
    "total_depreciation": 245000.00
  }
}
```

---

## 7. 获取资产二维码图片

**请求**
```
GET /api/assets/assets/{id}/qr_code/
Accept: image/png
```

**响应**
```
HTTP 200 OK
Content-Type: image/png

(二进制图片数据)
```

---

## 8. 变更资产状态

**请求**
```
POST /api/assets/assets/{id}/change_status/
Content-Type: application/json

{
  "status": "maintenance",
  "reason": "屏幕故障，送修中"
}
```

**响应**
```json
{
  "success": true,
  "message": "状态变更成功",
  "data": {
    "status": "maintenance",
    "status_label": "维修中"
  }
}
```

---

## 9. 批量变更状态

**请求**
```
POST /api/assets/assets/batch_change_status/
Content-Type: application/json

{
  "asset_ids": [1, 2, 3, 5, 8],
  "status": "idle",
  "reason": "批量回收"
}
```

**响应**
```json
{
  "success": true,
  "message": "批量操作完成",
  "summary": {
    "total": 5,
    "succeeded": 4,
    "failed": 1
  },
  "results": [
    {"id": 1, "success": true},
    {"id": 2, "success": true},
    {"id": 3, "success": true},
    {"id": 5, "success": false, "error": "资产状态不允许变更"},
    {"id": 8, "success": true}
  ]
}
```

---

## 错误码

本模块使用GZEAMS标准错误码，自定义错误情况通过 `details` 字段说明。

| 标准错误码 | HTTP状态 | 说明 | 使用场景 |
|-----------|----------|------|----------|
| VALIDATION_ERROR | 400 | 请求数据验证失败 | 字段验证失败、分类无效、状态无效、状态转换不允许 |
| UNAUTHORIZED | 401 | 未授权访问 | 未登录、token无效 |
| PERMISSION_DENIED | 403 | 权限不足 | 无权限操作资产 |
| NOT_FOUND | 404 | 资源不存在 | 资产不存在 |
| CONFLICT | 409 | 资源冲突 | 编码重复、二维码重复 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 | 跨组织访问 |
| SOFT_DELETED | 410 | 资源已删除 | 访问已删除的资产 |

**自定义业务场景通过details说明**：
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求数据验证失败",
    "details": {
      "field": "asset_category",
      "reason": "invalid_category",
      "message": "资产分类无效"
    }
  }
}
```

---

## 数据字典

### 资产状态 (asset_status)

| 值 | 说明 |
|----|------|
| pending | 待入库 |
| in_use | 在用 |
| idle | 闲置 |
| maintenance | 维修中 |
| lost | 已丢失 |
| scrapped | 已报废 |

### 计量单位 (unit)

| 值 | 说明 |
|----|------|
| 台 | 计算机等设备 |
| 套 | 套装设备 |
| 辆 | 车辆 |
| 张 | 家具 |
| 台 | 通用单位 |
| 个 | 通用单位 |
| 件 | 通用单位 |
