## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

# Phase 1.9: 统一通知机制 - API接口定义

## 1. 通知模板 API

### 1.1 模板列表

```
GET /api/notifications/templates/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| template_type | string | 否 | 通知类型筛选 |
| channel | string | 否 | 渠道筛选 |
| language | string | 否 | 语言筛选 |
| is_active | bool | 否 | 是否启用 |

**Response:**
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
        "template_code": "WORKFLOW_APPROVAL",
        "template_name": "审批通知",
        "template_type": "workflow_approval",
        "channel": "inbox",
        "subject_template": "待处理审批: {{ task_title }}",
        "content_template": "您有 {{ count }} 条待处理的审批任务...",
        "variables": {
          "task_title": {"type": "string", "description": "任务标题"},
          "count": {"type": "int", "description": "任务数量"}
        },
        "language": "zh-CN",
        "is_active": true,
        "version": 1,
        "created_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 1.2 创建模板

```
POST /api/notifications/templates/
```

**Request:**
```json
{
  "template_code": "CUSTOM_NOTIFICATION",
  "template_name": "自定义通知",
  "template_type": "custom",
  "channel": "email",
  "subject_template": "系统通知: {{ title }}",
  "content_template": "<p>尊敬的 {{ recipient_name }}：</p><p>{{ content }}</p>",
  "variables": {
    "title": {"type": "string", "required": true},
    "content": {"type": "string", "required": true}
  },
  "language": "zh-CN",
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 1,
    "template_code": "CUSTOM_NOTIFICATION",
    "template_name": "自定义通知",
    "template_type": "custom",
    "channel": "email",
    "subject_template": "系统通知: {{ title }}",
    "content_template": "<p>尊敬的 {{ recipient_name }}：</p><p>{{ content }}</p>",
    "variables": {
      "title": {"type": "string", "required": true},
      "content": {"type": "string", "required": true}
    },
    "language": "zh-CN",
    "is_active": true
  }
}
```

### 1.3 更新模板

```
PUT /api/notifications/templates/{id}/
PATCH /api/notifications/templates/{id}/
```

### 1.4 预览模板

```
POST /api/notifications/templates/{id}/preview/
```

**Request:**
```json
{
  "example_data": {
    "task_title": "资产采购申请",
    "count": 3,
    "workflow_name": "采购流程"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "预览成功",
  "data": {
    "subject": "待处理审批: 资产采购申请",
    "content": "您有 3 条待处理的审批任务..."
  }
}
```

### 1.5 创建新版本

```
POST /api/notifications/templates/{id}/new-version/
```

**Response:**
```json
{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 2,
    "template_code": "WORKFLOW_APPROVAL",
    "version": 2,
    "previous_version": 1
  }
}
```

---

## 2. 通知发送 API

### 2.1 发送通知

```
POST /api/notifications/send/
```

**Request:**
```json
{
  "recipient_id": 5,
  "notification_type": "workflow_approval",
  "variables": {
    "task_title": "资产采购申请",
    "workflow_name": "采购流程",
    "link": "https://example.com/approval/123"
  },
  "channels": ["inbox", "email"],
  "priority": "high",
  "scheduled_at": "2024-01-15T14:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "通知已发送",
  "data": {
    "notification_id": 100,
    "status": "pending",
    "channels": ["inbox", "email"],
    "scheduled_at": "2024-01-15T14:00:00Z"
  }
}
```

### 2.2 批量发送通知

```
POST /api/notifications/send/batch/
```

**Request:**
```json
{
  "recipient_ids": [5, 6, 7],
  "notification_type": "system_announcement",
  "variables": {
    "title": "系统维护通知",
    "content": "系统将于今晚进行维护..."
  },
  "priority": "high"
}
```

**Response:**
```json
{
  "success": true,
  "message": "批量发送完成",
  "data": {
    "created": 3,
    "notification_ids": [100, 101, 102]
  }
}
```

### 2.3 广播通知（发送给所有用户）

```
POST /api/notifications/send/broadcast/
```

**Request:**
```json
{
  "notification_type": "system_announcement",
  "variables": {
    "title": "重要通知",
    "content": "..."
  },
  "filter": {
    "org_id": 1,
    "role_code": "asset_user"
  }
}
```

---

## 3. 通知查询 API

### 3.1 我的通知列表

```
GET /api/notifications/my/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_read | bool | 否 | 是否已读 |
| type | string | 否 | 通知类型筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 50,
    "unread_count": 15,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 100,
        "type": "workflow_approval",
        "type_display": "审批通知",
        "title": "待处理审批: 资产采购申请",
        "content": "您有 1 条待处理的审批任务",
        "priority": "high",
        "priority_display": "重要",
        "data": {
          "link": "/approval/123"
        },
        "is_read": false,
        "created_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 3.2 通知详情

```
GET /api/notifications/my/{id}/
```

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "id": 100,
    "type": "workflow_approval",
    "title": "待处理审批: 资产采购申请",
    "content": "完整内容...",
    "data": {
      "task_id": 123,
      "link": "/approval/123"
    },
    "is_read": false,
    "created_at": "2024-01-15T10:00:00Z",
    "sender": {
      "id": 3,
      "username": "system",
      "full_name": "系统"
    }
  }
}
```

### 3.3 标记已读

```
POST /api/notifications/my/{id}/read/
```

**Response:**
```json
{
  "success": true,
  "message": "标记已读成功",
  "data": {
    "id": 100,
    "is_read": true,
    "read_at": "2024-01-15T10:30:00Z"
  }
}
```

### 3.4 批量标记已读

```
POST /api/notifications/my/read-batch/
```

**Request:**
```json
{
  "notification_ids": [100, 101, 102]
}
```

或标记全部已读：
```json
{
  "all": true
}
```

### 3.5 删除通知

```
DELETE /api/notifications/my/{id}/
```

**Response:**
```json
{
  "success": true,
  "message": "删除成功"
}
```

### 3.6 获取未读数量

```
GET /api/notifications/my/unread-count/
```

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "unread_count": 15,
    "by_type": {
      "workflow_approval": 5,
      "inventory_assigned": 3,
      "system_announcement": 7
    }
  }
}
```

---

## 4. 通知配置 API

### 4.1 获取我的配置

```
GET /api/notifications/config/
```

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "id": 1,
    "enable_inbox": true,
    "enable_email": true,
    "enable_sms": false,
    "enable_wework": true,
    "enable_dingtalk": false,
    "channel_settings": {
      "workflow_approval": {
        "inbox": true,
        "email": false,
        "sms": false,
        "wework": true
      },
      "inventory_assigned": {
        "inbox": true,
        "sms": true,
        "email": false
      }
    },
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00:00",
    "quiet_hours_end": "08:00:00",
    "email_address": "user@example.com",
    "phone_number": "13800138000"
  }
}
```

### 4.2 更新配置

```
PUT /api/notifications/config/
PATCH /api/notifications/config/
```

**Request:**
```json
{
  "enable_email": false,
  "enable_sms": true,
  "quiet_hours_enabled": true,
  "quiet_hours_start": "23:00:00",
  "quiet_hours_end": "07:00:00",
  "channel_settings": {
    "workflow_approval": {
      "email": true,
      "sms": false
    }
  }
}
```

---

## 5. 通知管理 API (管理员)

### 5.1 通知列表

```
GET /api/notifications/admin/notifications/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| recipient_id | int | 否 | 接收人筛选 |
| type | string | 否 | 类型筛选 |
| status | string | 否 | 状态筛选 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 100,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 100,
        "recipient": {
          "id": 5,
          "username": "user001"
        },
        "type": "workflow_approval",
        "channel": "email",
        "status": "success",
        "title": "待处理审批",
        "retry_count": 0,
        "sent_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 5.2 重试失败通知

```
POST /api/notifications/admin/notifications/{id}/retry/
```

**Response:**
```json
{
  "success": true,
  "message": "已加入重试队列"
}
```

### 5.3 通知日志

```
GET /api/notifications/admin/logs/
```

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 200,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 500,
        "notification_id": 100,
        "channel": "email",
        "status": "success",
        "error_code": null,
        "error_message": null,
        "duration": 1250,
        "created_at": "2024-01-15T10:00:01Z"
      }
    ]
  }
}
```

### 5.4 通知统计

```
GET /api/notifications/admin/statistics/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date_from | date | 是 | 开始日期 |
| date_to | date | 是 | 结束日期 |
| group_by | string | 否 | 分组方式 (type/channel/date) |

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "summary": {
      "total_sent": 5000,
      "total_success": 4850,
      "total_failed": 150,
      "success_rate": "97%"
    },
    "by_type": [
      {
        "type": "workflow_approval",
        "count": 2000,
        "success": 1950,
        "failed": 50
      }
    ],
    "by_channel": [
      {
        "channel": "inbox",
        "count": 3000,
        "success": 2980,
        "failed": 20
      },
      {
        "channel": "email",
        "count": 1500,
        "success": 1450,
        "failed": 50
      }
    ],
    "trend": [
      {
        "date": "2024-01-15",
        "count": 500
      }
    ]
  }
}
```

---

## 6. WebSocket 事件

### 6.1 新通知推送

```json
{
  "event": "notification.created",
  "data": {
    "id": 100,
    "type": "workflow_approval",
    "title": "待处理审批: 资产采购申请",
    "content": "您有 1 条待处理的审批任务",
    "priority": "high",
    "link": "/approval/123"
  }
}
```

### 6.2 通知已读同步

```json
{
  "event": "notification.read",
  "data": {
    "notification_id": 100,
    "unread_count": 14
  }
}
```

---

## 7. 错误码定义

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 模板不存在 |
| VALIDATION_ERROR | 400 | 模板变量校验失败 |
| VALIDATION_ERROR | 400 | 渠道不支持 |
| VALIDATION_ERROR | 400 | 接收人无效 |
| VALIDATION_ERROR | 400 | 无可用渠道 |
| NOT_FOUND | 404 | 通知类型未定义 |
| VALIDATION_ERROR | 400 | 发送频率超限 |
| VALIDATION_ERROR | 400 | 邮箱格式错误 |
| VALIDATION_ERROR | 400 | 手机号格式错误 |
| VALIDATION_ERROR | 400 | 短信余额不足 |
| VALIDATION_ERROR | 400 | 企业微信配置错误 |
| VALIDATION_ERROR | 400 | 免打扰时段 |

---

## 8. 通知类型常量

| 类型代码 | 名称 | 默认渠道 | 说明 |
|----------|------|----------|------|
| workflow_approval | 审批通知 | inbox,wework | 待审批任务 |
| workflow_approved | 审批通过 | inbox,email | 审批完成通知 |
| workflow_rejected | 审批拒绝 | inbox,email | 审批拒绝通知 |
| workflow_returned | 审批驳回 | inbox | 被驳回通知 |
| inventory_assigned | 盘点任务分配 | inbox,sms | 盘点任务通知 |
| inventory_reminder | 盘点提醒 | inbox,wework | 盘点截止提醒 |
| inventory_completed | 盘点完成 | inbox,email | 盘点完成通知 |
| asset_warning | 资产预警 | inbox,email | 资产异常预警 |
| asset_expired | 资产到期 | inbox,sms | 资产到期提醒 |
| report_generated | 报表生成完成 | inbox,email | 报表生成通知 |
| report_failed | 报表生成失败 | inbox | 报表失败通知 |
| system_announcement | 系统公告 | inbox | 系统公告 |
| system_maintenance | 系统维护 | inbox | 维护通知 |
| user_login | 用户登录 | inbox | 异地登录提醒 |
| password_changed | 密码修改 | inbox,email | 密码修改通知 |
