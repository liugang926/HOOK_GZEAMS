## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

# Phase 1.6: 低值易耗品/办公用品管理 - API接口定义

## 接口概览

### 耗材档案接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/consumables/consumables/` | 获取耗材列表 |
| POST | `/api/consumables/consumables/` | 创建耗材 |
| GET | `/api/consumables/consumables/{id}/` | 获取耗材详情 |
| PUT | `/api/consumables/consumables/{id}/` | 更新耗材 |
| DELETE | `/api/consumables/consumables/{id}/` | 删除耗材 |
| GET | `/api/consumables/consumables/stock_summary/` | 获取库存汇总 |
| GET | `/api/consumables/consumables/{id}/stock_movements/` | 获取库存流水 |

### 采购单接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/consumables/purchases/` | 获取采购单列表 |
| POST | `/api/consumables/purchases/` | 创建采购单 |
| GET | `/api/consumables/purchases/{id}/` | 获取采购单详情 |
| PUT | `/api/consumables/purchases/{id}/` | 更新采购单 |
| POST | `/api/consumables/purchases/{id}/submit/` | 提交审批 |
| POST | `/api/consumables/purchases/{id}/approve/` | 审批采购单 |
| POST | `/api/consumables/purchases/{id}/confirm_receipt/` | 确认入库 |

### 领用单接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/consumables/issues/` | 获取领用单列表 |
| POST | `/api/consumables/issues/` | 创建领用单 |
| GET | `/api/consumables/issues/{id}/` | 获取领用单详情 |
| POST | `/api/consumables/issues/{id}/submit/` | 提交审批 |
| POST | `/api/consumables/issues/{id}/approve/` | 审批领用单 |
| POST | `/api/consumables/issues/{id}/confirm_issue/` | 确认发放 |

### 库存预警接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/consumables/alerts/low_stock/` | 获取低库存列表 |
| GET | `/api/consumables/alerts/summary/` | 获取预警汇总 |
| POST | `/api/consumables/alerts/check_all/` | 检查并发送预警 |

---

## 1. 耗材档案接口

### 1.1 获取耗材列表

**请求**
```
GET /api/consumables/consumables/?category=1&status=low_stock&page=1&page_size=20
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| search | string | 搜索关键词（编码/名称/品牌/规格） |
| category | integer | 分类ID |
| status | string | 状态过滤 (normal/low_stock/out_of_stock/discontinued) |
| warehouse | integer | 仓库ID |
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
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "code": "HC001",
        "name": "A4打印纸",
        "category": {
          "id": 5,
          "name": "纸张类",
          "full_name": "办公用品 > 纸张类"
        },
        "specification": "70g 500张/包",
        "brand": "得力",
        "unit": "包",
        "current_stock": 45,
        "available_stock": 45,
        "locked_stock": 0,
        "purchase_price": 25.00,
        "average_price": 24.50,
        "min_stock": 20,
        "max_stock": 100,
        "reorder_point": 30,
        "status": "normal",
        "status_label": "正常",
        "warehouse": {
          "id": 10,
          "name": "办公用品仓"
        },
        "created_at": "2024-01-01T10:00:00Z"
      }
    ]
  }
}
```

### 1.2 创建耗材

**请求**
```
POST /api/consumables/consumables/
Content-Type: application/json

{
  "code": "HC002",
  "name": "签字笔",
  "category": 3,
  "specification": "0.5mm 黑色",
  "brand": "晨光",
  "unit": "支",
  "min_stock": 50,
  "max_stock": 200,
  "reorder_point": 80,
  "purchase_price": 1.50,
  "warehouse": 10
}
```

**响应**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 2,
    "code": "HC002",
    "name": "签字笔",
    "status": "normal"
  }
}
```

### 1.3 获取库存汇总

**请求**
```
GET /api/consumables/consumables/stock_summary/?category_id=5
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "by_category": [
      {
        "category_id": 5,
        "category_name": "纸张类",
        "total_items": 8,
        "total_stock": 350,
        "total_value": 8750.00,
        "low_stock_count": 2,
        "out_of_stock_count": 0
      }
    ],
    "total_categories": 4,
    "total_low_stock": 5,
    "total_out_of_stock": 1
  }
}
```

### 1.4 获取库存流水

**请求**
```
GET /api/consumables/consumables/1/stock_movements/?start_date=2024-06-01&end_date=2024-06-30
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 101,
        "transaction_type": "purchase",
        "transaction_type_label": "采购入库",
        "quantity": 50,
        "before_stock": 20,
        "after_stock": 70,
        "source_type": "ConsumablePurchase",
        "source_no": "HC20240601001",
        "handler": {
          "id": 5,
          "real_name": "张三"
        },
        "remark": "采购入库",
        "created_at": "2024-06-01T10:00:00Z"
      },
      {
        "id": 102,
        "transaction_type": "issue",
        "transaction_type_label": "领用出库",
        "quantity": -25,
        "before_stock": 70,
        "after_stock": 45,
        "source_type": "ConsumableIssue",
        "source_no": "HCL20240615001",
        "handler": {
          "id": 8,
          "real_name": "李四"
        },
        "remark": "部门领用",
        "created_at": "2024-06-15T14:00:00Z"
      }
    ]
  }
}
```

---

## 2. 采购单接口

### 2.1 获取采购单列表

**请求**
```
GET /api/consumables/purchases/?status=approved&page=1
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态过滤 |
| supplier | integer | 供应商ID |
| purchase_type | string | 采购类型 |
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |
| search | string | 搜索关键词 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 28,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 5,
        "purchase_no": "HC20240601001",
        "purchase_date": "2024-06-01",
        "supplier": {
          "id": 3,
          "name": "晨光文具"
        },
        "purchase_type": "regular",
        "purchase_type_label": "常规采购",
        "total_amount": 1250.00,
        "status": "approved",
        "status_label": "已审批",
        "applicant": {
          "id": 5,
          "real_name": "张三"
        },
        "approved_by": {
          "id": 2,
          "real_name": "采购经理"
        },
        "approved_at": "2024-06-01T15:00:00Z",
        "items_count": 5
      }
    ]
  }
}
```

### 2.2 创建采购单

**请求**
```
POST /api/consumables/purchases/
Content-Type: application/json

{
  "supplier": 3,
  "purchase_date": "2024-06-15",
  "purchase_type": "regular",
  "remark": "月度采购",
  "items": [
    {
      "consumable_id": 1,
      "order_quantity": 50,
      "received_quantity": 50,
      "unit_price": 25.00
    },
    {
      "consumable_id": 2,
      "order_quantity": 100,
      "received_quantity": 100,
      "unit_price": 1.50
    }
  ]
}
```

**响应**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 10,
    "purchase_no": "HC20240615001",
    "status": "draft",
    "total_amount": 1400.00
  }
}
```

### 2.3 提交审批

**请求**
```
POST /api/consumables/purchases/10/submit/
```

**响应**
```json
{
  "id": 10,
  "purchase_no": "HC20240615001",
  "status": "submitted"
}
```

### 2.4 审批采购单

**请求**
```
POST /api/consumables/purchases/10/approve/
Content-Type: application/json

{
  "approval": "approved",
  "comment": "同意采购，质量可靠"
}
```

**响应**
```json
{
  "id": 10,
  "purchase_no": "HC20240615001",
  "status": "approved",
  "approved_by": {
    "id": 2,
    "real_name": "采购经理"
  },
  "approved_at": "2024-06-15T16:00:00Z"
}
```

### 2.5 确认入库

**请求**
```
POST /api/consumables/purchases/10/confirm_receipt/
```

**响应**
```json
{
  "status": "received",
  "message": "入库成功",
  "updated_consumables": [
    {
      "id": 1,
      "code": "HC001",
      "name": "A4打印纸",
      "current_stock": 95,
      "available_stock": 95
    }
  ]
}
```

---

## 3. 领用单接口

### 3.1 获取领用单列表

**请求**
```
GET /api/consumables/issues/?status=approved&page=1
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 45,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 12,
        "issue_no": "HCL20240615001",
        "issue_date": "2024-06-15",
        "issue_type": "department",
        "issue_type_label": "部门领用",
        "department": {
          "id": 3,
          "name": "研发部"
        },
        "applicant": {
          "id": 8,
          "real_name": "李四"
        },
        "purpose": "项目使用",
        "status": "approved",
        "status_label": "已审批",
        "items_count": 3,
        "created_at": "2024-06-15T09:00:00Z"
      }
    ]
  }
}
```

### 3.2 创建领用单

**请求**
```
POST /api/consumables/issues/
Content-Type: application/json

{
  "issue_date": "2024-06-15",
  "issue_type": "department",
  "department": 3,
  "purpose": "项目使用",
  "items": [
    {
      "consumable_id": 1,
      "quantity": 5
    },
    {
      "consumable_id": 2,
      "quantity": 20
    }
  ]
}
```

**响应**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 15,
    "issue_no": "HCL20240615002",
    "status": "draft"
  }
}
```

### 3.3 提交审批

**请求**
```
POST /api/consumables/issues/15/submit/
```

**响应**
```json
{
  "id": 15,
  "issue_no": "HCL20240615002",
  "status": "submitted"
}
```

### 3.4 审批领用单

**请求**
```
POST /api/consumables/issues/15/approve/
Content-Type: application/json

{
  "approval": "approved"
}
```

**响应**
```json
{
  "id": 15,
  "issue_no": "HCL20240615002",
  "status": "approved"
}
```

### 3.5 确认发放

**请求**
```
POST /api/consumables/issues/15/confirm_issue/
```

**响应**
```json
{
  "status": "issued",
  "message": "发放成功",
  "updated_consumables": [
    {
      "id": 1,
      "name": "A4打印纸",
      "available_stock": 90
    }
  ]
}
```

**错误响应**（库存不足）
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_STOCK",
    "message": "A4打印纸 库存不足，当前库存: 3"
  }
}
```

---

## 4. 库存预警接口

### 4.1 获取低库存列表

**请求**
```
GET /api/consumables/alerts/low_stock/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 8,
        "code": "HC008",
        "name": "文件夹A4",
        "category": {
          "name": "文件管理"
        },
        "available_stock": 5,
        "min_stock": 20,
        "status": "low_stock",
        "status_label": "库存不足"
      }
    ]
  }
}
```

### 4.2 获取预警汇总

**请求**
```
GET /api/consumables/alerts/summary/
```

**响应**
```json
{
  "has_alert": true,
  "total_categories": 2,
  "alerts": [
    {
      "category": "文件管理",
      "items": [
        {
          "id": 8,
          "code": "HC008",
          "name": "文件夹A4",
          "current_stock": 5,
          "min_stock": 20,
          "status": "库存不足"
        }
      ]
    },
    {
      "category": "书写工具",
      "items": [
        {
          "id": 3,
          "code": "HC003",
          "name": "签字笔",
          "current_stock": 0,
          "min_stock": 50,
          "status": "缺货"
        }
      ]
    }
  ]
}
```

### 4.3 检查并发送预警

**请求**
```
POST /api/consumables/alerts/check_all/
```

**响应**
```json
{
  "status": "checked",
  "sent_count": 3,
  "message": "已发送预警通知给采购人员"
}
```

---

## 5. 退库单接口

### 5.1 创建退库单

**请求**
```
POST /api/consumables/returns/
Content-Type: application/json

{
  "return_date": "2024-06-20",
  "original_issue": 15,
  "reason": "项目结束，剩余耗材退回",
  "items": [
    {
      "consumable_id": 1,
      "quantity": 2,
      "condition": "good"
    }
  ]
}
```

**响应**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 5,
    "return_no": "HCT20240620001",
    "status": "draft"
  }
}
```

### 5.2 确认收货

**请求**
```
POST /api/consumables/returns/5/confirm_receipt/
```

**响应**
```json
{
  "status": "received",
  "message": "退库已确认，库存已更新"
}
```

---

## 6. 盘点单接口

### 6.1 创建盘点单

**请求**
```
POST /api/consumables/inventories/
Content-Type: application/json

{
  "inventory_date": "2024-06-30",
  "inventory_range": "category",
  "category_id": 5,
  "responsible": 8
}
```

**响应**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 3,
    "inventory_no": "HCIN20240630001",
    "status": "draft"
  }
}
```

### 6.2 添加盘点明细

**请求**
```
POST /api/consumables/inventories/3/items/
Content-Type: application/json

{
  "items": [
    {
      "consumable_id": 1,
      "book_quantity": 45,
      "actual_quantity": 43
    }
  ]
}
```

**响应**
```json
{
  "success_count": 1,
  "items": [
    {
      "id": 25,
      "consumable": {
        "name": "A4打印纸"
      },
      "book_quantity": 45,
      "actual_quantity": 43,
      "difference": -2,
      "difference_amount": -49.00
    }
  ]
}
```

---

## 数据字典

### 耗材状态 (status)

| 值 | 说明 |
|----|------|
| normal | 正常 |
| low_stock | 库存不足 |
| out_of_stock | 缺货 |
| discontinued | 停用 |

### 采购单状态 (purchase_status)

| 值 | 说明 |
|----|------|
| draft | 草稿 |
| submitted | 已提交 |
| approved | 已审批 |
| received | 已入库 |
| cancelled | 已取消 |

### 领用单状态 (issue_status)

| 值 | 说明 |
|----|------|
| draft | 草稿 |
| submitted | 已提交 |
| approved | 已审批 |
| issued | 已发放 |
| cancelled | 已取消 |

### 采购类型 (purchase_type)

| 值 | 说明 |
|----|------|
| regular | 常规采购 |
| urgent | 紧急采购 |
| replenish | 补货采购 |

### 领用类型 (issue_type)

| 值 | 说明 |
|----|------|
| department | 部门领用 |
| personal | 个人领用 |
| project | 项目领用 |

### 库存变动类型 (transaction_type)

| 值 | 说明 |
|----|------|
| purchase | 采购入库 |
| issue | 领用出库 |
| return | 退库入库 |
| transfer_in | 调入入库 |
| transfer_out | 调拨出库 |
| inventory_add | 盘点增加 |
| inventory_reduce | 盘亏减少 |
| adjustment | 调整 |

### 退库物品状态 (condition)

| 值 | 说明 |
|----|------|
| new | 全新 |
| good | 完好 |
| damaged | 损坏 |

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 耗材不存在 |
| VALIDATION_ERROR | 400 | 分类无效 |
| INSUFFICIENT_STOCK | 400 | 库存不足 |
| CONFLICT | 400 | 采购单未审批 |
| CONFLICT | 400 | 领用单未审批 |
| VALIDATION_ERROR | 400 | 数量无效 |
| CONFLICT | 409 | 耗材编码已存在 |
