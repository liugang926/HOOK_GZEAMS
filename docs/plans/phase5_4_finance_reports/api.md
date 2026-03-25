# Phase 5.4: 财务报表生成 - API接口定义

## 公共模型引用

本模块所有后端组件均继承自公共基类，自动获得组织隔离、软删除、审计字段、批量操作等标准功能。

| 组件类型 | 基类 |
|---------|------|
| Model | BaseModel |
| Serializer | BaseModelSerializer |
| ViewSet | BaseModelViewSetWithBatch |
| Service | BaseCRUDService |
| Filter | BaseModelFilter |

---

## 1. 报表模板 API

### 1.1 模板列表

```
GET /api/reports/templates/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| report_type | string | 否 | 报表类型筛选 |
| status | string | 否 | 状态筛选 |
| keyword | string | 否 | 关键词搜索 |

**Response:**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "count": 10,
        "results": [
    {
      "id": 1,
      "template_code": "ASSET_DETAIL",
      "template_name": "固定资产明细表",
      "report_type": "asset_detail",
      "report_type_display": "资产明细表",
      "description": "包含资产基本信息、原值、折旧等完整数据",
      "status": "active",
      "is_system": true,
      "allow_export": true,
      "version": "1.0",
        "created_at": "2024-01-01T00:00:00Z"
        }
    ]
    }
}
```

### 1.2 模板详情

```
GET /api/reports/templates/{code}/
```

**Response:**
```json
{
  "id": 1,
  "template_code": "ASSET_DETAIL",
  "template_name": "固定资产明细表",
  "report_type": "asset_detail",
  "description": "包含资产基本信息、原值、折旧等完整数据",
  "status": "active",
  "template_config": {
    "layout": {
      "page_size": "A4",
      "orientation": "landscape"
    },
    "sections": [...]
  },
  "data_source": {
    "type": "model",
    "model": "assets.Asset",
    "fields": ["asset_no", "asset_name", ...]
  },
  "required_permission": "view_asset_detail",
  "allow_export": true,
  "is_system": true
}
```

---

## 2. 报表生成 API

### 2.1 生成报表

```
POST /api/reports/generate/
```

**Request:**
```json
{
  "template_code": "ASSET_DETAIL",
  "params": {
    "department_id": 1,
    "category_id": 2,
    "period_from": "2024-01-01",
    "period_to": "2024-01-31"
  },
  "output_format": "pdf"
}
```

**Response:** `201 Created`
```json
{
    "success": true,
    "message": "报表生成任务已创建",
    "data": {
        "id": 1,
        "generation_no": "RPT20240115123456789",
        "status": "pending",
        "template_code": "ASSET_DETAIL",
        "output_format": "pdf",
        "created_at": "2024-01-15T12:34:56Z"
    }
}
```

**Error Response:**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "报表参数验证失败",
        "details": {
            "template_code": ["报表模板不存在"]
        }
    }
}
```

### 2.2 获取报表预览

```
POST /api/reports/preview/
```

**Request:**
```json
{
  "template_code": "ASSET_DETAIL",
  "params": {
    "department_id": 1
  }
}
```

**Response:**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "template": {
    "code": "ASSET_DETAIL",
    "name": "固定资产明细表"
  },
  "data": {
    "data": [
      {
        "asset_no": "ZC2024010001",
        "asset_name": "笔记本电脑",
        "category_name": "电子设备",
        "original_value": 5000.00,
        "accumulated_depreciation": 500.00,
        "net_value": 4500.00
      }
    ],
    "summary": {
      "total_count": 100,
      "total_original": 500000.00,
        "total_net": 450000.00
        }
    }
    }
}
```

### 2.3 获取报表状态

```
GET /api/reports/generations/{id}/
```

**Response:**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": 1,
        "generation_no": "RPT20240115123456789",
  "status": "success",
  "status_display": "生成成功",
  "template": {
    "id": 1,
    "template_code": "ASSET_DETAIL",
    "template_name": "固定资产明细表"
  },
  "report_params": {
    "department_id": 1,
    "period_from": "2024-01-01"
  },
  "output_format": "pdf",
  "file_path": "/media/reports/202401/RPT20240115123456789.pdf",
  "file_url": "http://example.com/media/reports/202401/RPT20240115123456789.pdf",
  "file_size": 1024000,
  "generated_by": {
    "id": 1,
    "username": "admin"
  },
  "generated_at": "2024-01-15T12:35:00Z",
        "generation_duration": 4,
        "created_at": "2024-01-15T12:34:56Z"
    }
    }
}
```

**Error Response:**
```json
{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "报表生成记录不存在"
    }
}
```

### 2.4 下载报表文件

```
GET /api/reports/generations/{id}/download/
```

**Response:** PDF或Excel文件

### 2.5 生成记录列表

```
GET /api/reports/generations/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| template_code | string | 否 | 模板代码筛选 |
| status | string | 否 | 状态筛选 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**Response:**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "count": 50,
        "results": [
    {
      "id": 1,
      "generation_no": "RPT20240115123456789",
      "status": "success",
      "template_name": "固定资产明细表",
      "output_format": "pdf",
      "file_url": "/media/reports/...",
        "generated_at": "2024-01-15T12:35:00Z"
        }
    ]
    }
}
```

---

## 3. 报表调度 API

### 3.1 调度任务列表

```
GET /api/reports/schedules/
```

**Response:**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "count": 5,
        "results": [
    {
      "id": 1,
      "schedule_name": "月度资产明细表",
      "schedule_code": "MONTHLY_ASSET_DETAIL",
      "template": {
        "template_code": "ASSET_DETAIL",
        "template_name": "固定资产明细表"
      },
      "frequency": "monthly",
      "frequency_display": "每月",
      "cron_expression": "0 0 2 1 * *",
      "output_format": "pdf",
      "is_active": true,
      "last_run_at": "2024-01-01T02:00:00Z",
      "next_run_at": "2024-02-01T02:00:00Z",
        "subscriptions_count": 5
        }
    ]
    }
}
```

### 3.2 创建调度任务

```
POST /api/reports/schedules/
```

**Request:**
```json
{
  "schedule_name": "周度资产汇总",
  "schedule_code": "WEEKLY_ASSET_SUMMARY",
  "template_id": 1,
  "frequency": "weekly",
  "cron_expression": "0 0 8 * * 1",
  "default_params": {
    "period_type": "last_week"
  },
  "output_format": "pdf",
  "valid_from": "2024-01-01"
}
```

**Response:** `201 Created`

### 3.3 更新调度任务

```
PUT /api/reports/schedules/{id}/
PATCH /api/reports/schedules/{id}/
```

### 3.4 启用/停用调度

```
POST /api/reports/schedules/{id}/toggle/
```

**Response:**
```json
{
  "id": 1,
  "is_active": false,
  "message": "调度已停用"
}
```

---

## 4. 报表订阅 API

### 4.1 我的订阅列表

```
GET /api/reports/my-subscriptions/
```

**Response:**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "count": 3,
        "results": [
    {
      "id": 1,
      "schedule": {
        "id": 1,
        "schedule_name": "月度资产明细表",
        "template_name": "固定资产明细表"
      },
      "delivery_methods": ["email", "system"],
      "email": "user@example.com",
        "is_active": true
        }
    ]
    }
}
```

### 4.2 订阅报表

```
POST /api/reports/subscriptions/
```

**Request:**
```json
{
  "schedule_id": 1,
  "delivery_methods": ["email", "system"],
  "email": "user@example.com"
}
```

**Response:** `201 Created`

### 4.3 取消订阅

```
DELETE /api/reports/subscriptions/{id}/
```

**Response:** `204 No Content`

### 4.4 更新订阅

```
PUT /api/reports/subscriptions/{id}/
PATCH /api/reports/subscriptions/{id}/
```

---

## 5. 报表统计 API

### 5.1 报表生成统计

```
GET /api/reports/statistics/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date_from | date | 是 | 开始日期 |
| date_to | date | 是 | 结束日期 |
| group_by | string | 否 | 分组方式：template/user |

**Response:**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "summary": {
    "total_generations": 500,
    "success_count": 480,
    "failed_count": 15,
    "pending_count": 5,
    "success_rate": "96.0%",
    "avg_duration": 3.5
  },
  "by_template": [
    {
      "template_code": "ASSET_DETAIL",
      "template_name": "固定资产明细表",
      "count": 200,
      "success_count": 195
    }
  ],
  "by_user": [
    {
      "user_id": 1,
      "username": "admin",
      "count": 50
    }
  ],
  "trend": [
    {
      "date": "2024-01-01",
        "count": 50
        }
    ]
    }
}
```

---

## 6. WebSocket 事件

### 6.1 报表生成完成事件

```json
{
  "event": "report.generated",
  "data": {
    "generation_id": 1,
    "generation_no": "RPT20240115123456789",
    "status": "success",
    "file_url": "/media/reports/..."
  }
}
```

### 6.2 报表推送事件

```json
{
  "event": "report.delivered",
  "data": {
    "generation_no": "RPT20240115123456789",
    "template_name": "固定资产明细表",
    "delivery_method": "email",
    "delivered_at": "2024-01-15T12:40:00Z"
  }
}
```

---

## 7. 错误码定义

| 错误码 | 说明 |
|--------|------|
| 51001 | 报表模板不存在 |
| 51002 | 报表模板已停用 |
| 51003 | 无权限查看此报表 |
| 51004 | 报表参数无效 |
| 51005 | 报表生成失败 |
| 51006 | 报告文件不存在或已过期 |
| 51007 | 调度任务不存在 |
| 51008 | 调度任务冲突 |
| 51009 | Cron表达式无效 |
| 51010 | 订阅已存在 |
| 51011 | 导出格式不支持 |
| 51012 | 报表数据为空 |
