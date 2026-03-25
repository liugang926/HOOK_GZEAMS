# Phase 6: User Portal (用户门户) - API接口定义

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

## 接口概览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 门户首页 | GET | `/api/portal/overview/` | 获取门户首页概览 |
| 我的资产 | GET | `/api/portal/my-assets/` | 获取我的资产列表 |
| 我的资产 | GET | `/api/portal/my-assets/{id}/` | 获取资产详情 |
| 我的资产 | GET | `/api/portal/my-assets/summary/` | 获取资产汇总统计 |
| 我的申请 | GET | `/api/portal/my-requests/` | 获取我的申请列表 |
| 我的申请 | GET | `/api/portal/my-requests/{type}/{id}/` | 获取申请详情 |
| 我的申请 | POST | `/api/portal/my-requests/{type}/{id}/cancel/` | 取消申请 |
| 我的待办 | GET | `/api/portal/my-tasks/` | 获取我的待办列表 |
| 我的待办 | GET | `/api/portal/my-tasks/summary/` | 获取待办汇总 |
| 我的待办 | POST | `/api/portal/my-tasks/{id}/complete/` | 完成待办 |
| 个人信息 | GET | `/api/portal/profile/` | 获取个人信息 |
| 个人信息 | PUT | `/api/portal/profile/` | 更新个人信息 |
| 快捷操作 | POST | `/api/portal/quick-actions/` | 执行快捷操作 |

---

## 1. 门户首页

### 1.1 获取门户概览

**请求**
```
GET /api/portal/overview/
```

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "user": {
        "id": 5,
        "username": "zhangsan",
        "real_name": "张三",
        "avatar": "https://example.com/avatar/user5.jpg",
        "primary_department": {
      "id": 3,
        "name": "研发部"
        }
    }
    }
    }
}
```

---

## 2. 我的资产

### 2.1 获取我的资产列表

**请求**
```
GET /api/portal/my-assets/?status=in_use&page=1&page_size=20
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| relation | string | 关系类型 (custodian/borrowed/pickup) |
| status | string | 资产状态 |
| category | integer | 分类ID |
| keyword | string | 搜索关键词（编码/名称/序列号） |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "total": 5,
        "page": 1,
        "page_size": 20,
        "items": [
    {
      "id": 101,
      "asset_code": "ZC20240101005",
      "asset_name": "MacBook Pro 16寸",
      "category": {
        "id": 10,
        "name": "计算机设备"
      },
      "specification": "M2 Pro 16G 512G",
      "serial_number": "C02XXXXXXXX",
      "asset_status": "in_use",
      "asset_status_label": "在用",
      "relation": "custodian",
      "relation_label": "保管中",
      "department": {
        "id": 3,
        "name": "研发部"
      },
      "location": {
        "id": 15,
        "name": "3楼A区"
      },
      "purchase_price": 18999.00,
      "purchase_date": "2024-01-15",
      "qr_code": "https://example.com/qr/ZC20240101005.png",
      "image": "https://example.com/assets/macbook.jpg",
      "recent_operations": [
        {
          "action": "pickup",
          "action_label": "领用",
          "operator": "张三",
          "created_at": "2024-01-15T10:00:00Z"
        }
      ],
      "can_return": false,
      "can_transfer": true
    }
  ],
  "summary": {
    "total_count": 5,
    "custodian_count": 3,
    "borrowed_count": 1,
    "pickup_count": 1,
    "by_status": {
      "in_use": 4,
        "idle": 1
        }
    }
    }
}
```

### 2.2 获取资产详情

**请求**
```
GET /api/portal/my-assets/101/
```

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "asset": {
    "id": 101,
    "asset_code": "ZC20240101005",
    "asset_name": "MacBook Pro 16寸",
    "category": {
      "id": 10,
      "name": "计算机设备",
      "code": "2001"
    },
    "specification": "M2 Pro 16G 512G",
    "serial_number": "C02XXXXXXXX",
    "asset_status": "in_use",
    "asset_status_label": "在用",
    "department": {
      "id": 3,
      "name": "研发部",
      "full_path": "总部/研发部"
    },
    "location": {
      "id": 15,
      "name": "3楼A区",
      "path": "总部大楼/3楼/A区"
    },
    "custodian": {
      "id": 5,
      "name": "张三",
      "avatar": "https://example.com/avatar/user5.jpg",
      "department": "研发部"
    },
    "purchase_price": 18999.00,
    "purchase_date": "2024-01-15",
    "supplier": {
      "id": 5,
      "name": "苹果授权经销商"
    },
    "qr_code": "https://example.com/qr/ZC20240101005.png",
    "image": "https://example.com/assets/macbook.jpg",
    "warranty_expire_date": "2025-01-15",
    "depreciation_method": "straight_line",
    "useful_life": 60,
    "net_value": 15199.20,
    "custom_fields": {
      "cpu": "M2 Pro",
      "ram": "16GB",
        "disk": "512GB SSD"
        }
    }
    },
    "relation": "custodian",
  "relation_label": "保管中",
  "history": [
    {
      "id": 1001,
      "action": "pickup",
      "action_label": "领用",
      "from_status": "idle",
      "to_status": "in_use",
      "operator": "张三",
      "reason": "新员工入职配备",
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": 888,
      "action": "purchase",
      "action_label": "采购入库",
      "from_status": null,
      "to_status": "idle",
      "operator": "系统",
      "reason": "采购入库",
      "created_at": "2024-01-10T14:00:00Z"
    }
  ],
  "related_documents": [
    {
      "type": "pickup",
      "type_label": "领用单",
      "id": 46,
        "no": "LY20240115001",
        "status": "completed",
      "status_label": "已完成",
        "created_at": "2024-01-15T10:00:00Z"
        }
    ]
    }
    }
}
```

### 2.3 获取资产汇总

**请求**
```
GET /api/portal/my-assets/summary/
```

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "by_relation": {
    "custodian": {
      "count": 3,
      "total_value": 45000.00
    },
    "borrowed": {
      "count": 1,
      "total_value": 5000.00
    },
    "pickup": {
      "count": 1,
      "total_value": 2000.00
    }
  },
  "by_category": [
    {
      "category_id": 10,
      "category_name": "计算机设备",
      "count": 4,
      "total_value": 47000.00
    },
    {
      "category_id": 15,
      "category_name": "办公家具",
      "count": 1,
      "total_value": 5000.00
    }
  ],
  "by_status": {
        "in_use": 4,
        "idle": 1
        }
    }
    }
}
```

---

## 3. 我的申请

### 3.1 获取我的申请列表

**请求**
```
GET /api/portal/my-requests/?status=pending&type=pickup&page=1
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态过滤 (draft/pending/approved/rejected/completed/cancelled) |
| type | string | 申请类型 (pickup/transfer/return/loan/consumable_issue/consumable_purchase) |
| keyword | string | 搜索关键词（单号） |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "total": 12,
        "page": 1,
        "page_size": 20,
        "items": [
    {
      "id": "pickup_46",
      "request_type": "pickup",
      "request_type_label": "资产领用",
      "no": "LY20240615001",
      "status": "pending",
      "status_label": "待审批",
      "created_at": "2024-06-15T10:00:00Z",
      "updated_at": "2024-06-15T10:00:00Z",
      "summary": "3 项资产 - 新员工入职配备",
      "can_cancel": true,
      "can_edit": false,
      "can_withdraw": true
    },
    {
      "id": "loan_18",
      "request_type": "loan",
      "request_type_label": "资产借用",
      "no": "JY20240610001",
      "status": "borrowed",
      "status_label": "借出中",
      "created_at": "2024-06-10T14:00:00Z",
      "updated_at": "2024-06-10T15:00:00Z",
      "summary": "1 项资产 - 临时出差使用",
      "can_cancel": false,
      "can_edit": false,
      "can_withdraw": false
    },
    {
      "id": "consumable_issue_25",
      "request_type": "consumable_issue",
      "request_type_label": "易耗品领用",
      "no": "HCL20240612001",
      "status": "approved",
      "status_label": "已审批",
      "created_at": "2024-06-12T09:00:00Z",
      "updated_at": "2024-06-12T14:30:00Z",
      "summary": "5 种耗材 - 部门日常使用",
      "can_cancel": false,
      "can_edit": false,
      "can_withdraw": false
    }
  ],
  "summary": {
    "total": 12,
    "by_status": {
      "draft": 1,
      "pending": 2,
      "approved": 3,
      "borrowed": 1,
      "completed": 4,
      "rejected": 1
    },
    "by_type": {
      "pickup": 5,
      "loan": 2,
      "transfer": 1,
      "consumable_issue": 3,
        "consumable_purchase": 1
        }
    }
    }
}
```

### 3.2 获取申请详情

**请求**
```
GET /api/portal/my-requests/pickup/46/
```

**URL参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| type | string | 申请类型 (pickup/transfer/return/loan/consumable_issue/consumable_purchase) |
| id | integer | 申请ID |

**响应（领用单详情）**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "request_type": "pickup",
  "request_type_label": "资产领用",
  "id": 46,
  "no": "LY20240615001",
  "status": "pending",
  "status_label": "待审批",
  "created_at": "2024-06-15T10:00:00Z",
  "updated_at": "2024-06-15T10:00:00Z",
  "applicant": {
    "id": 5,
    "name": "张三",
    "department": "研发部"
  },
  "department": {
    "id": 3,
    "name": "研发部"
  },
  "pickup_date": "2024-06-15",
  "pickup_reason": "新员工入职设备配备",
  "items": [
    {
      "id": 101,
      "asset": {
        "id": 15,
        "asset_code": "ZC20240501005",
        "asset_name": "MacBook Pro",
        "specification": "M2 Pro 16G 512G",
        "image": "https://example.com/assets/macbook.jpg"
      },
      "quantity": 1,
      "remark": "开发人员使用"
    },
    {
      "id": 102,
      "asset": {
        "id": 22,
        "asset_code": "ZC20240501010",
        "asset_name": "Dell 27寸显示器",
        "specification": "U2723QE",
        "image": "https://example.com/assets/dell.jpg"
      },
      "quantity": 1,
      "remark": ""
    }
  ],
  "approvals": [
    {
      "id": 201,
      "approver": {
        "id": 2,
        "name": "李经理"
      },
      "approval": "pending",
      "approval_label": "待审批",
      "comment": null,
      "approved_at": null
    }
  ],
        "can_cancel": true,
        "can_withdraw": true
    }
    }
}
```

**响应（借用单详情）**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "request_type": "loan",
  "request_type_label": "资产借用",
  "id": 18,
  "no": "JY20240605001",
  "status": "borrowed",
  "status_label": "借出中",
  "created_at": "2024-06-05T10:00:00Z",
  "updated_at": "2024-06-05T11:00:00Z",
  "borrower": {
    "id": 15,
    "name": "王五"
  },
  "borrow_date": "2024-06-05",
  "expected_return_date": "2024-06-20",
  "actual_return_date": null,
  "loan_reason": "临时出差使用",
  "is_overdue": false,
  "days_left": 5,
  "items": [
    {
      "id": 501,
      "asset": {
        "id": 50,
        "asset_code": "ZC20240101020",
        "asset_name": "iPad Pro 12.9寸",
        "specification": "WiFi 256G",
        "image": "https://example.com/assets/ipad.jpg"
      },
      "quantity": 1,
      "condition": "good",
      "condition_label": "完好"
    }
  ],
        "can_return": true,
        "can_extend": true
    }
    }
}
```

### 3.3 取消申请

**请求**
```
POST /api/portal/my-requests/pickup/46/cancel/
```

**响应**
```json
{
    "success": true,
    "message": "申请已取消",
    "data": {
        "status": "cancelled",
        "status_label": "已取消"
    }
}
```

**错误响应**
```json
{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "当前状态不允许取消",
        "details": {
            "current_status": "approved"
        }
    }
}
```

---

## 4. 我的待办

### 4.1 获取我的待办列表

**请求**
```
GET /api/portal/my-tasks/?task_type=workflow_approval&page=1
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| task_type | string | 任务类型 (workflow_approval/inventory/return_confirm/loan_return/pickup) |
| priority | string | 优先级 (urgent/high/normal) |
| status | string | 状态 (pending/in_progress/completed) |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "total": 8,
        "page": 1,
        "page_size": 20,
        "items": [
    {
      "id": "workflow_123",
      "task_type": "workflow_approval",
      "task_type_label": "流程审批",
      "title": "资产调拨审批",
      "description": "调拨: 研发部 → 市场部",
      "priority": "high",
      "priority_label": "高",
      "status": "pending",
      "status_label": "待处理",
      "due_date": "2024-06-16T18:00:00Z",
      "created_at": "2024-06-15T09:00:00Z",
      "action_url": "/workflows/tasks/123",
      "action_type": "approve",
      "instance": {
        "id": 56,
        "no": "WF20240615001",
        "definition": "资产调拨流程"
      },
      "applicant": {
        "id": 5,
        "name": "张三"
      }
    },
    {
      "id": "inventory_45",
      "task_type": "inventory",
      "task_type_label": "资产盘点",
      "title": "2024年6月资产盘点",
      "description": "待盘点 150 项资产",
      "priority": "urgent",
      "priority_label": "紧急",
      "status": "in_progress",
      "status_label": "进行中",
      "due_date": "2024-06-20T18:00:00Z",
      "progress": {
        "total": 150,
        "completed": 80,
        "pending": 70,
        "percent": 53
      },
      "action_url": "/inventory/my/45",
      "action_type": "continue",
      "is_overdue": false
    },
    {
      "id": "loan_due_18",
      "task_type": "loan_return",
      "task_type_label": "借用归还",
      "title": "借用资产归还提醒",
      "description": "1 项资产将在3天后到期",
      "priority": "high",
      "priority_label": "高",
      "status": "pending",
      "status_label": "待归还",
      "due_date": "2024-06-18T18:00:00Z",
      "days_left": 3,
      "is_overdue": false,
      "action_url": "/assets/loans/18",
      "action_type": "return"
    },
    {
      "id": "return_confirm_9",
      "task_type": "return_confirm",
      "task_type_label": "退库确认",
      "title": "李四的退库申请",
      "description": "2 项资产待确认",
      "priority": "normal",
      "priority_label": "普通",
      "status": "pending",
      "status_label": "待确认",
      "action_url": "/assets/returns/9",
      "action_type": "confirm"
    },
    {
      "id": "pickup_47",
      "task_type": "pickup",
      "task_type_label": "资产领取",
      "title": "待领取资产",
      "description": "2 项资产已审批通过，请及时领取",
      "priority": "high",
      "priority_label": "高",
      "status": "approved",
      "status_label": "待领取",
      "approved_at": "2024-06-14T10:00:00Z",
      "days_passed": 1,
      "action_url": "/assets/pickups/47",
      "action_type": "receive"
    }
  ],
  "summary": {
    "total": 8,
    "urgent": 1,
    "high": 3,
    "normal": 4,
    "by_type": {
      "workflow_approval": 2,
      "inventory": 1,
      "loan_return": 2,
      "return_confirm": 2,
        "pickup": 1
        }
    }
    }
}
```

### 4.2 获取待办汇总

**请求**
```
GET /api/portal/my-tasks/summary/
```

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "total": 8,
        "pending": 5,
  "in_progress": 1,
  "completed_today": 2,
  "overdue": 0,
  "urgent": 1,
  "high": 3,
  "normal": 4,
  "by_type": {
    "workflow_approval": {
      "count": 2,
      "label": "流程审批"
    },
    "inventory": {
      "count": 1,
      "label": "资产盘点"
    },
    "loan_return": {
      "count": 2,
      "label": "借用归还"
    },
    "return_confirm": {
      "count": 2,
      "label": "退库确认"
    },
    "pickup": {
      "count": 1,
      "label": "资产领取"
    }
  },
  "upcoming_deadlines": [
    {
      "task_id": "workflow_123",
      "title": "资产调拨审批",
      "due_date": "2024-06-16T18:00:00Z",
      "hours_left": 24
    },
    {
      "task_id": "loan_due_18",
      "title": "借用资产归还",
      "due_date": "2024-06-18T18:00:00Z",
        "hours_left": 72
        }
    ]
    }
}
```

### 4.3 快速处理待办

**请求**
```
POST /api/portal/my-tasks/{id}/quick-action/
Content-Type: application/json

{
  "action": "approve",
  "comment": "同意调拨"
}
```

**请求参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| action | string | 操作类型 (approve/reject/confirm/return) |
| comment | string | 备注/意见 |

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "task": {
            "id": "workflow_123",
            "status": "completed",
            "status_label": "已处理"
        }
    }
}
```

**错误响应**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "无效的操作类型",
        "details": {
            "action": ["操作类型必须是 approve, reject, confirm 或 return 之一"]
        }
    }
}
```

---

## 5. 个人信息

### 5.1 获取个人信息

**请求**
```
GET /api/portal/profile/
```

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": 5,
        "username": "zhangsan",
  "real_name": "张三",
  "email": "zhangsan@example.com",
  "mobile": "13800138000",
  "avatar": "https://example.com/avatar/user5.jpg",
  "employee_no": "EMP001",
  "position": "高级工程师",
  "organization": {
    "id": 1,
    "name": "总部",
    "code": "HQ"
  },
  "primary_department": {
    "id": 3,
    "name": "研发部",
    "full_path": "总部/研发部"
  },
  "departments": [
    {
      "id": 3,
      "name": "研发部",
      "full_path": "总部/研发部",
      "is_primary": true,
      "is_leader": false,
      "position": "高级工程师"
    },
    {
      "id": 8,
      "name": "项目管理办公室",
      "full_path": "总部/项目管理办公室",
      "is_primary": false,
      "is_leader": false,
      "position": "项目经理"
    }
  ],
  "roles": ["member"],
  "permissions": [
    "assets.view",
    "assets.create_request",
    "inventory.scan"
  ],
  "preferences": {
    "language": "zh-CN",
    "timezone": "Asia/Shanghai",
    "notification_enabled": true,
    "notification_types": ["email", "wework"]
  },
  "statistics": {
    "assets_custodian": 3,
    "assets_borrowed": 1,
    "requests_this_month": 5,
    "pending_requests": 2
  },
  "joined_at": "2023-01-15T10:00:00Z",
        "last_login": "2024-06-15T09:30:00Z"
    }
    }
}
```

### 5.2 更新个人信息

**请求**
```
PUT /api/portal/profile/
Content-Type: application/json

{
  "real_name": "张三丰",
  "email": "zhangsanfeng@example.com",
  "mobile": "13900139000",
  "avatar": "base64_image_data...",
  "position": "技术专家",
  "preferences": {
    "language": "zh-CN",
    "timezone": "Asia/Shanghai",
    "notification_enabled": true
  }
}
```

**响应**
```json
{
    "success": true,
    "message": "个人信息已更新",
    "data": {
        "user": {
    "id": 5,
    "real_name": "张三丰",
    "email": "zhangsanfeng@example.com",
    "mobile": "13900139000",
    "avatar": "https://example.com/avatar/user5_new.jpg",
        "position": "技术专家"
        }
    }
}
```

**错误响应**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "个人信息验证失败",
        "details": {
            "email": ["邮箱格式不正确"]
        }
    }
}
```

### 5.3 切换主部门

**请求**
```
POST /api/portal/profile/switch-department/
Content-Type: application/json

{
  "department_id": 8
}
```

**响应**
```json
{
    "success": true,
    "message": "已切换主部门",
    "data": {
        "primary_department": {
    "id": 8,
    "name": "项目管理办公室",
        "full_path": "总部/项目管理办公室"
        }
    }
}
```

**错误响应**
```json
{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "部门不存在",
        "details": {
            "department_id": 8
        }
    }
}
```

---

## 6. 快捷操作

### 6.1 执行快捷操作

**请求**
```
POST /api/portal/quick-actions/
Content-Type: application/json

{
  "action": "scan_qr",
  "params": {
    "qr_data": "ASSET:ZC20240101005"
  }
}
```

**可用操作**
| 操作 | 说明 | 参数 |
|------|------|------|
| scan_qr | 扫码查看资产 | qr_data: 二维码数据 |
| create_pickup | 创建领用申请 | - |
| create_loan | 创建借用申请 | - |
| my_assets | 跳转我的资产 | - |
| my_tasks | 跳转我的待办 | - |

**响应（扫码查看资产）**
```json
{
    "success": true,
    "message": "扫码成功",
    "data": {
        "action": "scan_qr",
        "result": {
    "type": "asset",
    "data": {
      "id": 101,
      "asset_code": "ZC20240101005",
      "asset_name": "MacBook Pro 16寸",
      "asset_status": "in_use",
      "custodian": {
        "name": "张三"
            }
        }
    }
    }
}
```

**错误响应**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "无法识别的二维码",
        "details": {
            "qr_data": ["二维码格式错误或资产不存在"]
        }
    }
}
```

---

## 7. 移动端专用接口

### 7.1 移动端首页

**请求**
```
GET /api/portal/mobile/home/
```

**响应**
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "user": {
        "id": 5,
        "real_name": "张三",
        "avatar": "https://example.com/avatar/user5.jpg"
        },
        "summary": {
            "assets_count": 5,
            "tasks_count": 3,
            "notifications_count": 2
        },
        "quick_actions": [
            {
                "id": "scan",
                "name": "扫码",
                "icon": "qr-scan",
                "color": "#409EFF"
            },
            {
                "id": "my_assets",
                "name": "我的资产",
                "icon": "box",
                "color": "#67C23A"
            },
            {
                "id": "my_tasks",
                "name": "待办",
                "icon": "bell",
                "color": "#E6A23C",
                "badge": 3
            },
            {
                "id": "more",
                "name": "更多",
                "icon": "more",
                "color": "#909399"
            }
        ],
        "pending_tasks": [
            {
                "id": "workflow_123",
                "title": "资产调拨审批",
                "priority": "high"
            },
            {
                "id": "loan_due_18",
                "title": "借用即将到期",
                "priority": "high"
            }
        ],
        "recent_assets": [
            {
                "id": 101,
                "asset_name": "MacBook Pro",
                "relation_label": "保管中"
            }
        ]
    }
}
```

### 7.2 扫码解析

**请求**
```
POST /api/portal/mobile/scan/
Content-Type: application/json

{
  "qr_data": "https://example.com/qr/ASSET:ZC20240101005"
}
```

**响应**
```json
{
    "success": true,
    "message": "扫码解析成功",
    "data": {
        "type": "asset",
        "id": "101",
        "asset_code": "ZC20240101005",
        "asset_name": "MacBook Pro 16寸",
        "redirect_url": "/portal/mobile/assets/101"
    }
}
```

**错误响应**
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "无效的二维码数据"
    }
}
```

---

## 8. 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| VALIDATION_ERROR | 400 | 请求数据验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| PERMISSION_DENIED | 403 | 无权限访问 |
| NOT_FOUND | 404 | 资源不存在（资产/申请/部门等） |
| METHOD_NOT_ALLOWED | 405 | 请求方法不允许 |
| CONFLICT | 409 | 资源冲突 |

---

## 9. WebSocket 实时通知

### 9.1 连接

```
ws://example.com/ws/portal/notifications/
```

**连接参数**
| 参数 | 说明 |
|------|------|
| token | JWT Token |
| organization_id | 组织ID |

### 9.2 消息格式

**服务端推送**
```json
{
  "type": "new_task",
  "data": {
    "task_id": "workflow_123",
    "task_type": "workflow_approval",
    "title": "资产调拨审批",
    "priority": "high",
    "created_at": "2024-06-15T10:00:00Z"
  }
}
```

**消息类型**
| 类型 | 说明 |
|------|------|
| new_task | 新待办任务 |
| task_updated | 任务状态更新 |
| request_approved | 申请已批准 |
| request_rejected | 申请已拒绝 |
| asset_reminder | 资产相关提醒 |
| system_notification | 系统通知 |

### 9.3 心跳保活

```json
{
  "type": "ping"
}
```

```json
{
  "type": "pong",
  "timestamp": 1718432000
}
```
