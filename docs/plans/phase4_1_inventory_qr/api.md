# Phase 4.1: QR码扫描盘点 - API接口定义

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
| GET | `/api/inventory/tasks/` | 获取盘点任务列表 |
| POST | `/api/inventory/tasks/` | 创建盘点任务 |
| GET | `/api/inventory/tasks/{id}/` | 获取任务详情 |
| PUT/PATCH | `/api/inventory/tasks/{id}/` | 更新任务 |
| DELETE | `/api/inventory/tasks/{id}/` | 删除任务 |
| POST | `/api/inventory/tasks/{id}/start/` | 开始盘点 |
| POST | `/api/inventory/tasks/{id}/complete/` | 完成盘点 |
| GET | `/api/inventory/tasks/{id}/statistics/` | 获取统计 |
| GET | `/api/inventory/tasks/{id}/scanned_assets/` | 获取已盘资产 |
| GET | `/api/inventory/tasks/{id}/unscanned_assets/` | 获取未盘资产 |
| POST | `/api/inventory/tasks/{id}/record_scan/` | 记录扫描 |
| GET | `/api/assets/qr/generate/` | 生成二维码 |
| GET | `/api/assets/{id}/qr/image/` | 获取二维码图片 |
| POST | `/api/assets/qr/print_labels/` | 生成打印标签PDF |

---

## 1. 盘点任务管理

### 1.1 获取任务列表

**请求**
```
GET /api/inventory/tasks/?status=pending
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选：draft/pending/in_progress/completed |
| inventory_type | string | 否 | 盘点类型：full/partial/department/category |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**响应**
```json
{
  "success": true,
  "message": "获取任务列表成功",
  "data": {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "task_code": "PD20240115001",
        "task_name": "2024年1月全盘",
        "inventory_type": "full",
        "inventory_type_display": "全盘",
        "planned_date": "2024-01-20",
        "status": "pending",
        "status_display": "待执行",
        "total_count": 500,
        "scanned_count": 0,
        "normal_count": 0,
        "surplus_count": 0,
        "missing_count": 0,
        "damaged_count": 0,
        "progress": 0,
        "planned_by": {
          "id": 1,
          "real_name": "管理员"
        },
        "created_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 1.2 创建任务

**请求**
```
POST /api/inventory/tasks/
Authorization: Bearer <token>
Content-Type: application/json

{
  "task_name": "技术部资产盘点",
  "inventory_type": "department",
  "department_id": 5,
  "planned_date": "2024-01-20",
  "executor_ids": [2, 3],
  "primary_executor_id": 2,
  "description": "技术部季度盘点"
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_name | string | 是 | 任务名称 |
| inventory_type | string | 否 | 盘点类型，默认full |
| department_id | integer | 否 | 部门ID（department类型时必填） |
| asset_category_id | integer | 否 | 分类ID（category类型时必填） |
| location_id | integer | 否 | 地点ID |
| planned_date | string | 是 | 计划日期（YYYY-MM-DD） |
| executor_ids | array | 是 | 执行人ID列表 |
| primary_executor_id | integer | 否 | 主执行人ID |
| description | string | 否 | 盘点说明 |

**响应**
```json
{
  "success": true,
  "message": "任务创建成功",
  "data": {
    "id": 2,
    "task_code": "PD20240115002",
    "task_name": "技术部资产盘点",
    "inventory_type": "department",
    "status": "pending",
    "total_count": 120,
    "progress": 0,
    "created_at": "2024-01-15T11:00:00Z"
  }
}
```

### 1.3 开始盘点

**请求**
```
POST /api/inventory/tasks/{id}/start/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "盘点已开始",
  "data": {
    "started_at": "2024-01-20T09:00:00Z"
  }
}
```

### 1.4 完成盘点

**请求**
```
POST /api/inventory/tasks/{id}/complete/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "盘点已完成",
  "data": {
    "id": 1,
    "task_code": "PD20240115001",
    "status": "completed",
    "status_display": "已完成",
    "completed_at": "2024-01-20T17:30:00Z",
    "total_count": 500,
    "scanned_count": 498,
    "normal_count": 490,
    "surplus_count": 2,
    "missing_count": 8,
    "damaged_count": 0,
    "progress": 100
  }
}
```

---

## 2. 盘点统计

### 2.1 获取统计

**请求**
```
GET /api/inventory/tasks/{id}/statistics/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "获取统计成功",
  "data": {
    "total": 500,
    "scanned": 350,
    "normal": 340,
    "surplus": 3,
    "missing": 7,
    "damaged": 0,
    "progress": 70,
    "remaining": 150
  }
}
```

### 2.2 获取已盘资产

**请求**
```
GET /api/inventory/tasks/{id}/scanned_assets/?page=1
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "获取已盘资产成功",
  "data": {
    "count": 350,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1001,
        "asset_id": 123,
        "asset_code": "ZC001",
        "asset_name": "MacBook Pro",
        "scan_time": "2024-01-20T10:15:30Z",
        "scan_status": "normal",
        "scan_status_display": "正常",
        "scan_method": "qr",
        "scanned_by": "张三",
        "remark": ""
      },
      {
        "id": 1002,
        "asset_id": 124,
        "asset_code": "ZC002",
        "asset_name": "显示器",
        "scan_time": "2024-01-20T10:16:45Z",
        "scan_status": "location_changed",
        "scan_status_display": "位置变更",
        "scan_method": "qr",
        "scanned_by": "张三",
        "remark": "从301室搬到303室"
      }
    ]
  }
}
```

### 2.3 获取未盘资产

**请求**
```
GET /api/inventory/tasks/{id}/unscanned_assets/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "获取未盘资产成功",
  "data": {
    "count": 150,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 125,
        "asset_code": "ZC005",
        "asset_name": "打印机",
        "custodian": "李四",
        "location": "302室"
      }
    ]
  }
}
```

---

## 3. 扫描记录

### 3.1 记录扫描

**请求**
```
POST /api/inventory/tasks/{id}/record_scan/
Authorization: Bearer <token>
Content-Type: application/json

{
  "asset_id": 123,
  "scan_method": "qr",
  "status": "normal",
  "actual_location": "",
  "photos": [],
  "remark": "",
  "latitude": 39.9042,
  "longitude": 116.4074
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| asset_id | integer | 否 | 资产ID（与asset_code二选一） |
| asset_code | string | 否 | 资产编码（与asset_id二选一） |
| scan_method | string | 是 | 扫描方式：qr/rfid/manual |
| status | string | 是 | 盘点状态：normal/location_changed/damaged/missing |
| actual_location | string | 否 | 实际位置（status=location_changed时） |
| actual_custodian | string | 否 | 实际保管人 |
| photos | array | 否 | 照片URL列表 |
| remark | string | 否 | 备注 |
| latitude | float | 否 | GPS纬度 |
| longitude | float | 否 | GPS经度 |

**响应**
```json
{
  "success": true,
  "message": "扫描记录成功",
  "data": {
    "id": 1001,
    "task": 1,
    "asset": {
      "id": 123,
      "asset_code": "ZC001",
      "asset_name": "MacBook Pro"
    },
    "scanned_by": "张三",
    "scanned_at": "2024-01-20T10:15:30Z",
    "scan_method": "qr",
    "scan_status": "normal"
  }
}
```

### 3.2 盘盈记录

**请求**
```
POST /api/inventory/tasks/{id}/record_scan/
Authorization: Bearer <token>
Content-Type: application/json

{
  "asset_code": "ZC999",
  "scan_method": "qr",
  "status": "surplus",
  "remark": "不在任务中的资产"
}
```

**响应**
```json
{
  "success": true,
  "message": "盘盈记录成功",
  "data": {
    "id": 1003,
    "scan_status": "surplus",
    "remark": "资产编码: ZC999"
  }
}
```

---

## 4. 二维码

### 4.1 生成二维码

**请求**
```
POST /api/assets/qr/generate/
Authorization: Bearer <token>
Content-Type: application/json

{
  "asset_ids": [1, 2, 3]
}
```

**响应**
```json
{
  "success": true,
  "message": "二维码生成成功",
  "data": {
    "total": 3,
    "success": [
      {
        "asset_id": 1,
        "asset_code": "ZC001",
        "qr_url": "/media/qr_codes/1/asset_qr_ZC001.png"
      },
      {
        "asset_id": 2,
        "asset_code": "ZC002",
        "qr_url": "/media/qr_codes/1/asset_qr_ZC002.png"
      },
      {
        "asset_id": 3,
        "asset_code": "ZC003",
        "qr_url": "/media/qr_codes/1/asset_qr_ZC003.png"
      }
    ],
    "failed": []
  }
}
```

### 4.2 获取二维码图片

**请求**
```
GET /api/assets/{id}/qr/image/
Authorization: Bearer <token>
```

**响应**
```
HTTP 200 OK
Content-Type: image/png

<binary image data>
```

### 4.3 生成打印标签

**请求**
```
POST /api/assets/qr/print_labels/
Authorization: Bearer <token>
Content-Type: application/json

{
  "asset_ids": [1, 2, 3, 4, 5, 6, 7, 8]
}
```

**响应**
```
HTTP 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="asset_labels.pdf"

<pdf binary data>
```

---

## 5. 二维码数据格式

### 5.1 二维码内容结构

```json
{
  "type": "asset",
  "version": "1.0",
  "asset_id": "123",
  "asset_code": "ZC001",
  "org_id": "1",
  "checksum": "a1b2c3d4"
}
```

**字段说明**

| 字段 | 说明 |
|------|------|
| type | 类型，固定为"asset" |
| version | 版本号 |
| asset_id | 资产ID（字符串） |
| asset_code | 资产编码 |
| org_id | 组织ID |
| checksum | 校验和（MD5前8位） |

### 5.2 校验和计算

```
checksum = MD5(asset_id:asset_code:org_id)[:8]
```

示例：
```
输入: "123:ZC001:1"
MD5: a1b2c3d4e5f6g7h8
checksum: a1b2c3d4
```

---

## 6. 盘点状态枚举

| 值 | 显示 | 颜色 |
|----|------|------|
| normal | 正常 | success |
| location_changed | 位置变更 | warning |
| damaged | 损坏 | danger |
| missing | 丢失 | info |
| surplus | 盘盈 | primary |

---

## 7. 任务状态流转

```
draft(草稿)
    ↓
pending(待执行)
    ↓
in_progress(进行中)
    ↓
completed(已完成)

任何状态 → cancelled(已取消)
```

---

## 8. 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 任务不存在 |
| VALIDATION_ERROR | 400 | 任务已开始，无法修改 |
| VALIDATION_ERROR | 400 | 任务已完成，无法操作 |
| VALIDATION_ERROR | 400 | 任务未开始，无法记录扫描 |
| NOT_FOUND | 404 | 资产不存在 |
| VALIDATION_ERROR | 400 | 无效的二维码 |
| VALIDATION_ERROR | 400 | 校验和不匹配 |
| VALIDATION_ERROR | 400 | 资产不在盘点范围内 |

---

## 后续任务

1. Phase 4.2: 实现RFID批量盘点
2. Phase 4.3: 实现盘点快照和差异处理
