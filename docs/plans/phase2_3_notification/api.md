# Phase 2.3: 通知中心模块 - API接口定义

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
| GET | `/api/notifications/channels/` | 获取通知渠道配置 |
| PATCH | `/api/notifications/channels/{id}/` | 更新渠道配置 |
| GET | `/api/notifications/templates/` | 获取消息模板列表 |
| GET | `/api/notifications/templates/{id}/` | 获取模板详情 |
| POST | `/api/notifications/send/` | 发送通知 |
| GET | `/api/notifications/my-messages/` | 获取我的站内信 |
| GET | `/api/notifications/my-messages/unread-count/` | 获取未读数量 |
| POST | `/api/notifications/my-messages/{id}/mark-read/` | 标记为已读 |
| POST | `/api/notifications/my-messages/mark-all-read/` | 全部标记为已读 |
| GET | `/api/notifications/messages/` | 获取通知发送记录 |
| GET | `/api/notifications/statistics/` | 获取通知统计 |

---

## 1. 通知渠道配置

### 1.1 获取渠道配置

**请求**
```
GET /api/notifications/channels/
Authorization: Bearer <token>
```

**响应**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "channel_type": "wework",
      "channel_type_display": "企业微信",
      "config": {
        "corp_id": "ww123456",
        "agent_id": 1000001,
        "agent_secret": "***"
      },
      "priority": 1,
      "is_enabled": true,
      "description": "企业工作通知"
    },
    {
      "id": 2,
      "channel_type": "email",
      "channel_type_display": "邮件",
      "config": {
        "from_email": "noreply@example.com",
        "email_host": "smtp.example.com"
      },
      "priority": 2,
      "is_enabled": true,
      "description": "邮件通知"
    },
    {
      "id": 3,
      "channel_type": "inapp",
      "channel_type_display": "站内信",
      "config": {},
      "priority": 0,
      "is_enabled": true,
      "description": "系统内消息"
    }
  ]
}
```

### 1.2 更新渠道配置

**请求**
```
PATCH /api/notifications/channels/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_enabled": true,
  "priority": 1,
  "config": {
    "corp_id": "ww123456",
    "agent_id": 1000001,
    "agent_secret": "new_secret"
  }
}
```

**响应**
```json
{
  "id": 1,
  "channel_type": "wework",
  "is_enabled": true,
  "priority": 1,
  "config": {
    "corp_id": "ww123456",
    "agent_id": 1000001,
    "agent_secret": "***"
  }
}
```

---

## 2. 消息模板

### 2.1 获取模板列表

**请求**
```
GET /api/notifications/templates/?category=approval
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| category | string | 业务分类筛选 |
| search | string | 搜索关键词 |

**响应**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "code": "asset_pickup_created",
      "name": "资产领用待审批",
      "template_type": "textcard",
      "template_type_display": "文本卡片",
      "title": "待审批: 资产领用",
      "content": "申请人: {{applicant}}\n领用部门: {{department}}\n领用原因: {{pickup_reason}}",
      "url_template": "",
      "button_text": "立即处理",
      "button_url_template": "",
      "business_category": "approval",
      "business_category_display": "审批通知"
    }
  ]
}
```

### 2.2 获取模板详情

**请求**
```
GET /api/notifications/templates/{id}/
Authorization: Bearer <token>
```

**响应**
```json
{
  "id": 1,
  "code": "asset_pickup_created",
  "name": "资产领用待审批",
  "template_type": "textcard",
  "title": "待审批: 资产领用",
  "content": "申请人: {{applicant}}\n领用部门: {{department}}\n领用原因: {{pickup_reason}}",
  "url_template": "",
  "button_text": "立即处理",
  "button_url_template": "",
  "business_category": "approval",
  "remark": ""
}
```

---

## 3. 发送通知

### 3.1 直接发送通知

**请求**
```
POST /api/notifications/send/
Authorization: Bearer <token>
Content-Type: application/json

{
  "business_type": "manual",
  "business_id": "",
  "title": "系统通知",
  "content": "这是一条测试通知",
  "recipients": [
    {"user_id": "1"},
    {"user_id": "2"}
  ],
  "channels": ["wework", "inapp"],
  "url": "https://example.com/detail",
  "button_text": "查看详情"
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| business_type | string | 是 | 业务类型 |
| business_id | string | 否 | 业务ID |
| title | string | 是 | 消息标题 |
| content | string | 是 | 消息内容 |
| recipients | array | 是 | 接收人列表 |
| channels | array | 否 | 指定渠道（默认使用配置的渠道） |
| url | string | 否 | 跳转链接 |
| button_text | string | 否 | 按钮文字 |
| button_url | string | 否 | 按钮链接 |

**响应**
```json
{
  "id": 123,
  "business_type": "manual",
  "title": "系统通知",
  "content": "这是一条测试通知",
  "status": "success",
  "status_display": "成功",
  "sent_count": 4,
  "failed_count": 0,
  "sent_at": "2024-01-15T10:30:00Z",
  "logs": [
    {
      "recipient_id": "1",
      "channel": "wework",
      "channel_display": "企业微信",
      "status": "sent",
      "status_display": "已发送"
    },
    {
      "recipient_id": "1",
      "channel": "inapp",
      "channel_display": "站内信",
      "status": "sent",
      "status_display": "已发送"
    }
  ]
}
```

### 3.2 发送模板消息

**请求**
```
POST /api/notifications/send/
Authorization: Bearer <token>
Content-Type: application/json

{
  "template_code": "asset_pickup_created",
  "params": {
    "applicant": "张三",
    "department": "技术部",
    "pickup_reason": "项目开发需要"
  },
  "recipients": [
    {"user_id": "3"}
  ],
  "channels": ["wework"]
}
```

**响应**
```json
{
  "id": 124,
  "business_type": "approval",
  "title": "待审批: 资产领用",
  "content": "申请人: 张三\n领用部门: 技术部\n领用原因: 项目开发需要",
  "status": "success",
  "sent_count": 1,
  "failed_count": 0
}
```

---

## 4. 站内信

### 4.1 获取我的站内信

**请求**
```
GET /api/notifications/my-messages/?unread_only=true
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| unread_only | boolean | 是否只获取未读消息 |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

**响应**
```json
{
  "count": 25,
  "next": "/api/notifications/my-messages/?page=2",
  "previous": null,
  "results": [
    {
      "id": 456,
      "message_type": "approval",
      "message_type_display": "审批通知",
      "title": "待审批: 资产领用申请",
      "content": "张三提交了资产领用申请，请及时审批",
      "url": "/assets/pickups/123/approve",
      "button_text": "立即处理",
      "button_url": "/assets/pickups/123/approve",
      "business_type": "asset_pickup",
      "business_id": "123",
      "is_read": false,
      "read_at": null,
      "created_at": "2024-01-15T10:25:00Z"
    },
    {
      "id": 455,
      "message_type": "system",
      "message_type_display": "系统通知",
      "title": "系统维护通知",
      "content": "系统将于今晚22:00进行维护，请提前保存工作",
      "url": "",
      "button_text": "",
      "button_url": "",
      "business_type": "system",
      "business_id": "",
      "is_read": true,
      "read_at": "2024-01-14T08:30:00Z",
      "created_at": "2024-01-14T08:00:00Z"
    }
  ]
}
```

### 4.2 获取未读数量

**请求**
```
GET /api/notifications/my-messages/unread-count/
Authorization: Bearer <token>
```

**响应**
```json
{
  "count": 5
}
```

### 4.3 标记为已读

**请求**
```
POST /api/notifications/my-messages/{id}/mark-read/
Authorization: Bearer <token>
```

**响应**
```json
{
  "status": "success",
  "message": "已标记为已读"
}
```

### 4.4 全部标记为已读

**请求**
```
POST /api/notifications/my-messages/mark-all-read/
Authorization: Bearer <token>
```

**响应**
```json
{
  "status": "success",
  "count": 5
}
```

---

## 5. 通知记录

### 5.1 获取发送记录

**请求**
```
GET /api/notifications/messages/?status=success
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| business_type | string | 业务类型筛选 |
| status | string | 状态筛选 |
| start_date | string | 开始日期 |
| end_date | string | 结束日期 |

**响应**
```json
{
  "count": 100,
  "results": [
    {
      "id": 123,
      "business_type": "asset_pickup",
      "business_id": "456",
      "title": "待审批: 资产领用",
      "content": "申请人: 张三...",
      "status": "success",
      "status_display": "成功",
      "recipients": [{"user_id": "1", "channel": "wework"}],
      "sent_count": 3,
      "failed_count": 0,
      "sent_at": "2024-01-15T10:30:00Z",
      "logs": [...]
    }
  ]
}
```

---

## 6. 通知统计

### 6.1 获取统计数据

**请求**
```
GET /api/notifications/statistics/
Authorization: Bearer <token>
```

**响应**
```json
{
  "total_sent": 1250,
  "by_channel": [
    {"channel": "wework", "count": 500},
    {"channel": "email", "count": 300},
    {"channel": "inapp", "count": 450}
  ],
  "by_status": [
    {"status": "success", "count": 1100},
    {"status": "partial_success", "count": 100},
    {"status": "failed", "count": 50}
  ],
  "by_type": [
    {"business_type": "approval", "count": 600},
    {"business_type": "asset", "count": 300},
    {"business_type": "inventory", "count": 200},
    {"business_type": "system", "count": 150}
  ],
  "trend": [
    {"date": "2024-01-08", "count": 150},
    {"date": "2024-01-09", "count": 180},
    {"date": "2024-01-10", "count": 200},
    {"date": "2024-01-11", "count": 175},
    {"date": "2024-01-12", "count": 190},
    {"date": "2024-01-13", "count": 160},
    {"date": "2024-01-14", "count": 195}
  ]
}
```

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| channel_not_enabled | 400 | 渠道未启用 |
| invalid_recipients | 400 | 无效的接收人 |
| template_not_found | 404 | 模板不存在 |
| send_failed | 500 | 发送失败 |
| rate_limit_exceeded | 429 | 超出频率限制 |

---

## WebSocket 通知（可选）

### 连接

```
wss://api.example.com/ws/notifications/?token=<jwt_token>
```

### 消息格式

```json
{
  "type": "new_notification",
  "message": {
    "id": 457,
    "message_type": "approval",
    "title": "待审批: 资产领用",
    "content": "...",
    "is_read": false,
    "created_at": "2024-01-15T10:35:00Z"
  }
}
```

---

## 后续任务

1. Phase 3.1: 集成LogicFlow流程设计器
2. Phase 3.2: 实现工作流执行引擎
