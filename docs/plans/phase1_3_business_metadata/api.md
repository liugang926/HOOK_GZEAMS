# Phase 1.3: 核心业务单据元数据配置 - API接口定义

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
| GET | `/api/system/business-objects/` | 获取业务对象列表 |
| POST | `/api/system/business-objects/` | 创建业务对象 |
| GET | `/api/system/business-objects/{code}/` | 获取业务对象详情 |
| PUT | `/api/system/business-objects/{code}/` | 更新业务对象 |
| DELETE | `/api/system/business-objects/{code}/` | 删除业务对象 |
| GET | `/api/system/field-definitions/` | 获取字段定义列表 |
| POST | `/api/system/field-definitions/` | 创建字段定义 |
| GET | `/api/system/page-layouts/` | 获取页面布局列表 |
| POST | `/api/system/page-layouts/` | 创建页面布局 |
| GET | `/api/dynamic/{object_code}/` | 查询动态数据 |
| POST | `/api/dynamic/{object_code}/` | 创建动态数据 |
| GET | `/api/dynamic/{object_code}/{id}/` | 获取动态数据详情 |
| PUT | `/api/dynamic/{object_code}/{id}/` | 更新动态数据 |
| DELETE | `/api/dynamic/{object_code}/{id}/` | 删除动态数据 |

---

## 1. 获取业务对象列表

**请求**
```
GET /api/system/business-objects/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "code": "Asset",
        "name": "资产卡片",
        "name_en": "Asset",
        "description": "固定资产主数据",
        "enable_workflow": false,
        "enable_version": true,
        "table_name": "dynamic_data_asset",
        "field_count": 20,
        "layout_count": 2
      }
    ]
  }
}
```

---

## 2. 获取业务对象详情

**请求**
```
GET /api/system/business-objects/{code}/
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "code": "Asset",
    "name": "资产卡片",
    "name_en": "Asset",
    "description": "固定资产主数据",
    "enable_workflow": false,
    "enable_version": true,
    "table_name": "dynamic_data_asset",
    "default_form_layout": {
      "id": 1,
      "layout_code": "asset_form",
      "layout_name": "资产表单"
    },
    "default_list_layout": {
      "id": 2,
      "layout_code": "asset_list",
      "layout_name": "资产列表"
    },
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

## 3. 创建业务对象

**请求**
```
POST /api/system/business-objects/
Content-Type: application/json

{
  "code": "AssetPickup",
  "name": "资产领用单",
  "name_en": "Asset Pickup",
  "description": "员工领用资产的申请单据",
  "enable_workflow": true,
  "enable_version": true
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 2,
    "code": "AssetPickup",
    "name": "资产领用单",
    "name_en": "Asset Pickup",
    "description": "员工领用资产的申请单据",
    "enable_workflow": true,
    "enable_version": true
  }
}
```

---

## 4. 获取字段定义列表

**请求**
```
GET /api/system/field-definitions/?business_object=Asset
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| business_object | string | 业务对象编码 |
| field_type | string | 字段类型过滤 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 20,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "code": "asset_code",
        "name": "资产编码",
        "field_type": "text",
        "is_required": true,
        "is_unique": true,
        "is_readonly": true,
        "is_system": false,
        "is_searchable": true,
        "show_in_list": true,
        "show_in_detail": true,
        "show_in_filter": false,
        "sort_order": 1,
        "default_value": "",
        "options": [],
        "max_length": 50
      },
      {
        "id": 2,
        "code": "asset_status",
        "name": "资产状态",
        "field_type": "select",
        "is_required": true,
        "show_in_list": true,
        "sort_order": 20,
        "options": [
          {"value": "pending", "label": "待入库"},
          {"value": "in_use", "label": "在用"},
          {"value": "idle", "label": "闲置"},
          {"value": "maintenance", "label": "维修中"},
          {"value": "scrapped", "label": "已报废"}
        ],
        "default_value": "pending"
      }
    ]
  }
}
```

---

## 5. 创建字段定义

**请求**
```
POST /api/system/field-definitions/
Content-Type: application/json

{
  "business_object": "Asset",
  "code": "qr_code",
  "name": "二维码",
  "field_type": "qr_code",
  "is_readonly": true,
  "is_system": true,
  "sort_order": 30
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 21,
    "code": "qr_code",
    "name": "二维码",
    "field_type": "qr_code",
    "is_readonly": true,
    "is_system": true,
    "sort_order": 30
  }
}
```

---

## 6. 获取页面布局

**请求**
```
GET /api/system/page-layouts/?business_object=Asset&layout_code=asset_form
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| business_object | string | 业务对象编码 |
| layout_code | string | 布局编码 |
| layout_type | string | 布局类型: form/list/detail/search |

**响应**
```json
{
  "id": 1,
  "layout_code": "asset_form",
  "layout_name": "资产表单",
  "layout_type": "form",
  "layout_config": {
    "sections": [
      {
        "title": "基础信息",
        "columns": 2,
        "collapsible": false,
        "fields": ["asset_code", "asset_name", "category_id", "specification"]
      },
      {
        "title": "财务信息",
        "columns": 2,
        "collapsible": false,
        "fields": ["purchase_price", "current_value", "accumulated_depreciation", "purchase_date"]
      },
      {
        "title": "使用信息",
        "columns": 2,
        "collapsible": false,
        "fields": ["custodian_id", "department_id", "location_id", "asset_status"]
      }
    ]
  }
}
```

---

## 7. 创建页面布局

**请求**
```
POST /api/system/page-layouts/
Content-Type: application/json

{
  "business_object": "Asset",
  "layout_code": "asset_form",
  "layout_name": "资产表单",
  "layout_type": "form",
  "layout_config": {
    "sections": [
      {
        "title": "基础信息",
        "columns": 2,
        "fields": ["asset_code", "asset_name"]
      }
    ]
  },
  "is_default": true
}
```

---

## 8. 查询动态数据

**请求**
```
GET /api/dynamic/Asset/?search=电脑&page=1&page_size=20&sort=-created_at
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| search | string | 搜索关键词（搜索可搜索字段） |
| field_code | any | 字段过滤条件 |
| page | integer | 页码 |
| page_size | integer | 每页数量 |
| sort | string | 排序，-表示降序 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 156,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "data_no": "ASSET202401010001",
        "status": "in_use",
        "asset_code": "ASSET001",
        "asset_name": "MacBook Pro",
        "category_id": 1,
        "category_name": "计算机设备",
        "purchase_price": 12999.00,
        "custodian_id": 5,
        "custodian_name": "张三",
        "location_id": 10,
        "location_name": "总部-3楼-研发部",
        "asset_status": "in_use",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-15T14:30:00Z"
      }
    ]
  }
}
```

---

## 9. 创建动态数据

**请求**
```
POST /api/dynamic/Asset/
Content-Type: application/json

{
  "asset_code": "ASSET002",
  "asset_name": "Dell 显示器",
  "category_id": 1,
  "purchase_price": 1500.00,
  "custodian_id": 5,
  "location_id": 10,
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
    "data_no": "ASSET202406150001",
    "status": "draft",
    "created_at": "2024-06-15T10:30:00Z"
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
    "message": "必填字段不能为空",
    "details": {
      "asset_name": ["此字段为必填项"],
      "category_id": ["此字段为必填项"]
    }
  }
}
```

---

## 10. 获取动态数据详情

**请求**
```
GET /api/dynamic/Asset/{id}/
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "data_no": "ASSET202401010001",
    "status": "in_use",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z",
    "created_by": 1,
    "dynamic_fields": {
      "asset_code": "ASSET001",
      "asset_name": "MacBook Pro",
      "category_id": 1,
      "category": {
        "id": 1,
        "name": "计算机设备",
        "code": "2001"
      },
      "specification": "M2 Pro 16G 512G",
      "brand": "Apple",
      "model": "MacBook Pro",
      "purchase_price": 12999.00,
      "current_value": 11699.10,
      "accumulated_depreciation": 1299.90,
      "purchase_date": "2024-01-01",
      "custodian_id": 5,
      "custodian": {
        "id": 5,
        "name": "张三",
        "username": "zhangsan"
      },
      "department_id": 3,
      "location_id": 10,
      "asset_status": "in_use",
      "qr_code": "https://example.com/qrcode/ASSET001.png",
      "images": [
        "https://example.com/images/asset1_1.jpg"
      ],
      "attachments": []
    }
  }
}
```

---

## 11. 更新动态数据

**请求**
```
PUT /api/dynamic/Asset/{id}/
Content-Type: application/json

{
  "asset_name": "MacBook Pro (已更新)",
  "custodian_id": 6
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
    "data_no": "ASSET202401010001",
    "updated_at": "2024-06-15T11:00:00Z"
  }
}
```

---

## 12. 删除动态数据

**请求**
```
DELETE /api/dynamic/Asset/{id}/
```

**响应**
```json
{
  "success": true,
  "message": "删除成功"
}
```

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 业务对象/字段/数据不存在 |
| VALIDATION_ERROR | 400 | 编码已存在/字段类型无效/必填字段缺失/关联对象无效/公式计算错误 |
| CONFLICT | 409 | 编码已存在 |
| NOT_FOUND | 404 | 页面布局不存在 |
| NOT_FOUND | 404 | 数据记录不存在 |
| PERMISSION_DENIED | 403 | 权限不足 |

---

## 数据字典

### 字段类型 (field_type)

| 值 | 说明 | 配置属性 |
|----|------|----------|
| text | 单行文本 | max_length, regex_pattern |
| textarea | 多行文本 | max_length, rows |
| number | 数字 | decimal_places, min_value, max_value |
| currency | 金额 | decimal_places |
| date | 日期 | - |
| datetime | 日期时间 | - |
| select | 下拉选择 | options |
| multi_select | 多选下拉 | options |
| radio | 单选 | options |
| checkbox | 复选框 | options |
| boolean | 布尔值 | - |
| user | 用户选择 | - |
| department | 部门选择 | - |
| reference | 关联引用 | reference_object, reference_display_field |
| formula | 公式字段 | formula |
| sub_table | 子表 | sub_table_fields |
| file | 文件 | - |
| image | 图片 | - |
| rich_text | 富文本 | - |
| qr_code | 二维码(只读) | - |

### 页面布局类型 (layout_type)

| 值 | 说明 |
|----|------|
| form | 表单布局 |
| list | 列表布局 |
| detail | 详情布局 |
| search | 搜索布局 |

### 动态数据状态 (status)

| 值 | 说明 |
|----|------|
| draft | 草稿 |
| active | 激活 |
| archived | 归档 |
| deleted | 已删除 |

---

## 公式字段语法

公式字段支持简单的数学表达式和字段引用：

```
# 基本运算
{price} * {quantity}

# 复杂表达式
({price} * {quantity}) * (1 - {discount_rate})

# 条件表达式
{quantity} > 10 ? {price} * 0.9 : {price}
```

支持的运算符：`+`, `-`, `*`, `/`, `%`, `()`, `?:`
