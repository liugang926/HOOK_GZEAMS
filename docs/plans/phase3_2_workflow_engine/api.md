# Phase 3.2: 工作流执行引擎 - API接口定义

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
| POST | `/api/workflows/execution/start/` | 启动工作流 |
| GET | `/api/workflows/execution/my_tasks/` | 获取我的待办任务 |
| GET | `/api/workflows/execution/my_instances/` | 获取我发起的流程 |
| POST | `/api/workflows/execution/{id}/approve/` | 同意任务 |
| POST | `/api/workflows/execution/{id}/reject/` | 拒绝任务 |
| POST | `/api/workflows/execution/{id}/transfer/` | 转交任务 |
| POST | `/api/workflows/execution/{id}/withdraw/` | 撤回流程 |
| GET | `/api/workflows/execution/{id}/detail/` | 获取流程详情 |
| GET | `/api/workflows/execution/{id}/logs/` | 获取操作日志 |
| GET | `/api/workflows/execution/{id}/chain/` | 获取审批链 |
| GET | `/api/workflows/execution/statistics/` | 获取统计数据 |

---

## 1. 启动工作流

### 1.1 启动流程

**请求**
```
POST /api/workflows/execution/start/
Authorization: Bearer <token>
Content-Type: application/json

{
  "definition_id": 1,
  "business_id": "123",
  "business_no": "LY20240115001",
  "variables": {
    "amount": 50000,
    "department_id": 5
  }
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| definition_id | integer | 是 | 流程定义ID |
| business_id | string | 是 | 业务数据ID |
| business_no | string | 否 | 业务单号（用于显示） |
| variables | object | 否 | 流程变量 |

**响应（成功）**
```json
{
  "success": true,
  "message": "工作流启动成功",
  "data": {
    "id": 456,
    "definition": {
      "id": 1,
      "name": "资产领用审批",
      "code": "asset_pickup_approval"
    },
    "definition_name": "资产领用审批",
    "business_object": "asset_pickup",
    "business_id": "123",
    "business_no": "LY20240115001",
    "status": "running",
    "status_display": "运行中",
    "current_node_id": "node_2",
    "current_node_name": "部门审批",
    "initiator": {
      "id": 10,
      "name": "张三"
    },
    "initiator_name": "张三",
    "started_at": "2024-01-15T10:00:00Z",
    "completed_at": null,
    "progress": 25,
    "current_task_count": 2,
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

**响应（错误）**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "流程定义不存在"
  }
}
```

---

## 2. 待办任务

### 2.1 获取我的待办

**请求**
```
GET /api/workflows/execution/my_tasks/?status=pending&page=1&page_size=20
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 任务状态：pending/approved/rejected |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**响应**
```json
{
  "success": true,
  "data": {
    "count": 15,
    "next": "/api/workflows/execution/my_tasks/?page=2",
    "previous": null,
    "results": [
      {
        "id": 789,
        "instance": 456,
        "instance_no": "LY20240115001",
        "node_id": "node_2",
        "node_name": "部门审批",
        "node_type": "approval",
        "status": "pending",
        "status_display": "待处理",
        "assignee": {
          "id": 5,
          "name": "李经理"
        },
        "assignee_name": "李经理",
        "assignee_avatar": "https://example.com/avatar/5.jpg",
        "approve_type": "or",
        "action": "",
        "comment": "",
        "assigned_at": "2024-01-15T10:00:00Z",
        "completed_at": null,
        "is_overdue": false,
        "remaining_hours": 48,
        "initiator_name": "张三",
        "initiator_avatar": "https://example.com/avatar/10.jpg",
        "created_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 2.2 获取任务详情

**请求**
```
GET /api/workflows/execution/tasks/789/detail/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "data": {
    "task": {
      "id": 789,
      "node_name": "部门审批",
      "status": "pending",
      "assignee": {
        "id": 5,
        "name": "李经理",
        "avatar": "https://example.com/avatar/5.jpg"
      },
      "approve_type": "or",
      "assigned_at": "2024-01-15T10:00:00Z",
      "timeout_hours": 72,
      "timeout_at": "2024-01-18T10:00:00Z",
      "field_permissions": {
        "amount": "read_only",
        "pickup_reason": "editable",
        "department": "hidden"
      }
    },
    "instance": {
      "id": 456,
      "business_no": "LY20240115001",
      "status": "pending_approval",
      "definition_name": "资产领用审批",
      "initiator": {
        "id": 10,
        "name": "张三",
        "avatar": "https://example.com/avatar/10.jpg"
      },
      "started_at": "2024-01-15T10:00:00Z"
    },
    "business_data": {
      "applicant": {
        "id": 10,
        "name": "张三",
        "department": "技术部"
      },
      "department": {
        "id": 5,
        "name": "技术部"
      },
      "pickup_date": "2024-01-20",
      "pickup_reason": "项目开发需要",
      "amount": 50000,
      "items": [
        {
          "asset_id": 101,
          "asset_code": "ZC001",
          "asset_name": "MacBook Pro",
          "quantity": 2,
          "amount": 35000
        }
      ]
    },
    "logs": [
      {
        "id": 1001,
        "action": "submit",
        "action_display": "提交",
        "actor": {
          "id": 10,
          "name": "张三",
          "avatar": "https://example.com/avatar/10.jpg"
        },
        "actor_name": "张三",
        "actor_avatar": "https://example.com/avatar/10.jpg",
        "comment": "",
        "node_name": "",
        "old_status": "",
        "new_status": "running",
        "created_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

---

## 3. 审批操作

### 3.1 同意

**请求**
```
POST /api/workflows/execution/789/approve/
Authorization: Bearer <token>
Content-Type: application/json

{
  "comment": "同意，理由充分",
  "attachments": [201, 202]
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| comment | string | 是 | 审批意见 |
| attachments | array | 否 | 附件ID列表 |

**响应**
```json
{
  "success": true,
  "message": "审批操作成功",
  "data": {
    "id": 456,
    "status": "approved",
    "status_display": "已通过",
    "progress": 100,
    "completed_at": "2024-01-15T14:30:00Z",
    "current_node_id": "",
    "current_node_name": "",
    "current_task_count": 0
  }
}
```

### 3.2 拒绝

**请求**
```
POST /api/workflows/execution/789/reject/
Authorization: Bearer <token>
Content-Type: application/json

{
  "comment": "金额超出预算，请重新申请"
}
```

**响应**
```json
{
  "success": true,
  "message": "拒绝操作成功",
  "data": {
    "id": 456,
    "status": "rejected",
    "status_display": "已拒绝",
    "progress": 50,
    "completed_at": "2024-01-15T14:30:00Z"
  }
}
```

### 3.3 转交

**请求**
```
POST /api/workflows/execution/789/transfer/
Authorization: Bearer <token>
Content-Type: application/json

{
  "target_user_id": 8,
  "comment": "转交给王总监处理"
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target_user_id | integer | 是 | 转交目标用户ID |
| comment | string | 否 | 转交说明 |

**响应**
```json
{
  "success": true,
  "message": "任务转交成功",
  "data": {
    "id": 789,
    "assignee": {
      "id": 8,
      "name": "王总监"
    },
    "transferred_from": {
      "id": 5,
      "name": "李经理"
    },
    "status": "pending"
  }
}
```

---

## 4. 流程实例

### 4.1 获取我发起的流程

**请求**
```
GET /api/workflows/execution/my_instances/?status=running
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 流程状态筛选 |

**响应**
```json
{
  "success": true,
  "data": {
    "count": 8,
    "results": [
      {
        "id": 456,
        "definition_name": "资产领用审批",
        "business_no": "LY20240115001",
        "status": "running",
        "status_display": "运行中",
        "current_node_name": "部门审批",
        "started_at": "2024-01-15T10:00:00Z",
        "progress": 25,
        "current_tasks": [
          {
            "id": 789,
            "assignee_name": "李经理",
            "assignee_avatar": "https://example.com/avatar/5.jpg"
          }
        ]
      }
    ]
  }
}
```

### 4.2 获取流程详情

**请求**
```
GET /api/workflows/execution/456/detail/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": 456,
    "definition": {
      "id": 1,
      "name": "资产领用审批",
      "code": "asset_pickup_approval"
    },
    "definition_name": "资产领用审批",
    "business_object": "asset_pickup",
    "business_id": "123",
    "business_no": "LY20240115001",
    "status": "pending_approval",
    "status_display": "待审批",
    "current_node_id": "node_2",
    "current_node_name": "部门审批",
    "initiator": {
      "id": 10,
      "name": "张三"
    },
    "initiator_name": "张三",
    "started_at": "2024-01-15T10:00:00Z",
    "completed_at": null,
    "progress": 25,
    "total_tasks": 4,
    "completed_tasks": 1,
    "current_task_count": 2,
    "current_tasks": [
      {
        "id": 789,
        "node_name": "部门审批",
        "assignee_name": "李经理",
        "assignee_avatar": "https://example.com/avatar/5.jpg",
        "status": "pending",
        "approve_type": "or"
      },
      {
        "id": 790,
        "node_name": "部门审批",
        "assignee_name": "王副理",
        "assignee_avatar": "https://example.com/avatar/6.jpg",
        "status": "pending",
        "approve_type": "or"
      }
    ],
    "graph_data": {
      "nodes": [...],
      "edges": [...]
    },
    "approval_chain": [
      {
        "id": 788,
        "node_name": "开始",
        "node_type": "start",
        "status": "approved",
        "assignee_name": "",
        "comment": "",
        "completed_at": "2024-01-15T10:00:00Z"
      },
      {
        "id": 789,
        "node_name": "部门审批",
        "node_type": "approval",
        "status": "pending",
        "assignee_name": "李经理",
        "comment": "",
        "assigned_at": "2024-01-15T10:00:05Z"
      }
    ],
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

### 4.3 撤回流程

**请求**
```
POST /api/workflows/execution/456/withdraw/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "流程撤回成功",
  "data": {
    "id": 456,
    "status": "cancelled",
    "status_display": "已撤回",
    "completed_at": "2024-01-15T11:00:00Z"
  }
}
```

---

## 5. 操作日志

### 5.1 获取操作日志

**请求**
```
GET /api/workflows/execution/456/logs/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "data": {
    "count": 3,
    "results": [
      {
        "id": 1001,
        "action": "submit",
        "action_display": "提交",
        "actor": {
          "id": 10,
          "name": "张三"
        },
        "actor_name": "张三",
        "actor_avatar": "https://example.com/avatar/10.jpg",
        "comment": "",
        "node_name": "",
        "old_status": "",
        "new_status": "running",
        "created_at": "2024-01-15T10:00:00Z"
      },
      {
        "id": 1002,
        "action": "approve",
        "action_display": "同意",
        "actor": {
          "id": 5,
          "name": "李经理"
        },
        "actor_name": "李经理",
        "actor_avatar": "https://example.com/avatar/5.jpg",
        "comment": "同意，理由充分",
        "node_name": "部门审批",
        "old_status": "pending",
        "new_status": "approved",
        "created_at": "2024-01-15T14:30:00Z"
      }
    ]
  }
}
```

---

## 6. 审批链

### 6.1 获取审批链

**请求**
```
GET /api/workflows/execution/456/chain/
Authorization: Bearer <token>
```

**响应**
```json
{
  "chain": [
    {
      "id": 788,
      "node_id": "node_1",
      "node_name": "开始",
      "node_type": "start",
      "status": "approved",
      "status_display": "已通过",
      "assignee": null,
      "assignee_name": "",
      "assignee_avatar": "",
      "action": "submit",
      "comment": "",
      "assigned_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": 789,
      "node_id": "node_2",
      "node_name": "部门审批",
      "node_type": "approval",
      "status": "approved",
      "status_display": "已通过",
      "assignee": 5,
      "assignee_name": "李经理",
      "assignee_avatar": "https://example.com/avatar/5.jpg",
      "action": "approved",
      "comment": "同意，理由充分",
      "assigned_at": "2024-01-15T10:00:05Z",
      "completed_at": "2024-01-15T14:30:00Z"
    },
    {
      "id": 791,
      "node_id": "node_3",
      "node_name": "条件判断",
      "node_type": "condition",
      "status": "skipped",
      "status_display": "已跳过",
      "assignee": null,
      "assignee_name": "",
      "action": "",
      "comment": "",
      "assigned_at": "2024-01-15T14:30:05Z",
      "completed_at": "2024-01-15T14:30:05Z"
    },
    {
      "id": 792,
      "node_id": "node_4",
      "node_name": "财务审批",
      "node_type": "approval",
      "status": "pending",
      "status_display": "待处理",
      "assignee": 8,
      "assignee_name": "王总监",
      "assignee_avatar": "https://example.com/avatar/8.jpg",
      "action": "",
      "comment": "",
      "assigned_at": "2024-01-15T14:30:10Z",
      "completed_at": null
    }
  ]
}
```

---

## 7. 统计数据

### 7.1 获取统计

**请求**
```
GET /api/workflows/execution/statistics/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "data": {
    "pending_count": 15,
    "completed_today": 8,
    "initiated_count": 42,
    "overdue_count": 2,
    "cc_unread_count": 5
  }
}
```

---

## 8. 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 流程定义不存在 |
| NOT_FOUND | 404 | 流程实例不存在 |
| NOT_FOUND | 404 | 任务不存在 |
| VALIDATION_ERROR | 400 | 任务已完成 |
| PERMISSION_DENIED | 403 | 无权限操作 |
| VALIDATION_ERROR | 400 | 无效的审批人 |
| VALIDATION_ERROR | 400 | 流程已终止 |
| VALIDATION_ERROR | 400 | 当前状态不允许撤回 |
| VALIDATION_ERROR | 400 | 任务已超时 |

---

## 9. WebSocket 通知（可选）

### 连接

```
wss://api.example.com/ws/workflows/?token=<jwt_token>
```

### 消息格式

#### 新任务通知

```json
{
  "type": "new_task",
  "data": {
    "id": 789,
    "node_name": "部门审批",
    "instance_no": "LY20240115001",
    "initiator_name": "张三",
    "assigned_at": "2024-01-15T10:00:00Z"
  }
}
```

#### 任务完成通知

```json
{
  "type": "task_completed",
  "data": {
    "task_id": 789,
    "action": "approved",
    "actor_name": "李经理"
  }
}
```

#### 流程完成通知

```json
{
  "type": "workflow_completed",
  "data": {
    "instance_id": 456,
    "instance_no": "LY20240115001",
    "status": "approved",
    "definition_name": "资产领用审批"
  }
}
```

---

## 10. 任务状态图

```
                    ┌─────────────────────────────────────┐
                    │           WorkflowInstance           │
                    └─────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
    │   draft     │            │   running   │            │   pending   │
    │   (草稿)    │────────────▶│   (运行中)  │────────────▶│ _approval  │
    └─────────────┘            └─────────────┘            │  (待审批)   │
                                                          └─────────────┘
                                                                   │
                          ┌────────────────────────────────────────┤
                          │                                        │
                          ▼                                        ▼
                   ┌─────────────┐                          ┌─────────────┐
                   │  approved   │                          │  rejected   │
                   │   (已通过)  │                          │   (已拒绝)  │
                   └─────────────┘                          └─────────────┘


                    ┌─────────────────────────────────────┐
                    │           WorkflowTask               │
                    └─────────────────────────────────────┘
                                       │
           ┌───────────────────────────┼───────────────────────────┐
           │                           │                           │
           ▼                           ▼                           ▼
    ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
    │   pending   │────────────▶│  approved   │            │  rejected   │
    │  (待处理)   │            │   (已通过)  │            │   (已拒绝)  │
    └─────────────┘            └─────────────┘            └─────────────┘
           │
           ▼
    ┌─────────────┐            ┌─────────────┐
    │ transferred │            │   timeout   │
    │  (已转交)   │            │   (已超时)  │
    └─────────────┘            └─────────────┘
```

---

## 后续任务

1. Phase 4.1: 实现QR码扫描盘点
2. Phase 4.2: 实现RFID批量盘点
3. Phase 4.3: 实现盘点快照和差异处理
