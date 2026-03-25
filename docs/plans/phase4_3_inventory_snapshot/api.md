# Phase 4.3: 盘点快照和差异处理 - API接口定义

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
| POST | `/api/inventory/differences/detect/` | 检测差异 |
| GET | `/api/inventory/differences/by_task/` | 获取任务差异列表 |
| POST | `/api/inventory/differences/{id}/resolve/` | 处理差异 |
| POST | `/api/inventory/differences/{id}/ignore/` | 忽略差异 |
| POST | `/api/inventory/differences/batch_resolve/` | 批量处理差异 |
| GET | `/api/inventory/differences/report/{task_id}/` | 获取盘点报告 |

---

## 1. 差异检测

### 1.1 检测差异

**请求**
```
POST /api/inventory/differences/detect/
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_id": 1
}
```

**响应**
```json
{
  "success": true,
  "message": "差异检测成功",
  "data": {
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "task": 1,
        "task_code": "PD001",
        "asset": {
          "id": 123,
          "asset_code": "ZC001"
        },
        "asset_code": "ZC001",
        "asset_name": "MacBook Pro",
        "difference_type": "missing",
        "difference_type_display": "盘亏",
        "description": "资产 ZC001 未盘点到",
        "status": "pending",
        "status_display": "待处理"
      }
    ]
  }
}
```

---

## 2. 差异处理

### 2.1 处理单个差异

**请求**
```
POST /api/inventory/differences/1/resolve/
Authorization: Bearer <token>
Content-Type: application/json

{
  "resolution": "确认丢失，按资产丢失流程处理",
  "update_asset": true
}
```

**响应**
```json
{
  "success": true,
  "message": "差异处理完成",
  "data": {
    "id": 1,
    "status": "resolved",
    "resolution": "确认丢失，按资产丢失流程处理",
    "resolved_by": "张三",
    "resolved_at": "2024-01-21T10:00:00Z"
  }
}
```

### 2.2 批量处理

**请求**
```
POST /api/inventory/differences/batch_resolve/
Authorization: Bearer <token>
Content-Type: application/json

{
  "difference_ids": [1, 2, 3, 4, 5],
  "resolution": "批量确认处理"
}
```

**响应**
```json
{
  "success": true,
  "message": "批量处理完成",
  "data": {
    "summary": {
      "total": 5,
      "succeeded": 5,
      "failed": 0
    },
    "results": [
      {"id": 1, "success": true},
      {"id": 2, "success": true},
      {"id": 3, "success": true},
      {"id": 4, "success": true},
      {"id": 5, "success": true}
    ]
  }
}
```

---

## 3. 盘点报告

### 3.1 获取盘点报告

**请求**
```
GET /api/inventory/differences/report/1/?format=pdf
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| format | string | 报告格式：pdf/excel |

**响应（PDF）**
```
HTTP 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="inventory_report_PD001.pdf"

<pdf binary data>
```

---

## 差异类型

| 类型 | 说明 |
|-----|------|
| loss | 盘亏 |
| surplus | 盘盈 |
| damaged | 损坏 |
| location_mismatch | 位置不符 |
| custodian_mismatch | 保管人不符 |

---

## 后续任务

1. Phase 5.1: 实现万达宝M18采购对接
2. Phase 5.2: 实现万达宝M18财务对接
