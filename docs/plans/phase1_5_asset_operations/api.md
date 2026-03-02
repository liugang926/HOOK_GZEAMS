# Phase 1.5: 资产领用/调拨/退库业务 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 接口概览

### 领用单接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/assets/pickups/` | 获取领用单列表 |
| POST | `/api/assets/pickups/` | 创建领用单 |
| GET | `/api/assets/pickups/{id}/` | 获取领用单详情 |
| PUT | `/api/assets/pickups/{id}/` | 更新领用单 |
| DELETE | `/api/assets/pickups/{id}/` | 删除领用单 |
| POST | `/api/assets/pickups/{id}/submit/` | 提交审批 |
| POST | `/api/assets/pickups/{id}/approve/` | 审批领用单 |
| POST | `/api/assets/pickups/{id}/complete/` | 完成领用 |
| POST | `/api/assets/pickups/{id}/cancel/` | 取消领用单 |

### 调拨单接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/assets/transfers/` | 获取调拨单列表 |
| POST | `/api/assets/transfers/` | 创建调拨单 |
| GET | `/api/assets/transfers/{id}/` | 获取调拨单详情 |
| POST | `/api/assets/transfers/{id}/submit/` | 提交审批 |
| POST | `/api/assets/transfers/{id}/approve_from/` | 调出方审批 |
| POST | `/api/assets/transfers/{id}/approve_to/` | 调入方审批 |
| POST | `/api/assets/transfers/{id}/complete/` | 完成调拨 |

### 退库单接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/assets/returns/` | 获取退库单列表 |
| POST | `/api/assets/returns/` | 创建退库单 |
| GET | `/api/assets/returns/{id}/` | 获取退库单详情 |
| POST | `/api/assets/returns/{id}/confirm/` | 确认退库 |
| POST | `/api/assets/returns/{id}/reject/` | 拒绝退库 |

### 借用单接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/assets/loans/` | 获取借用单列表 |
| POST | `/api/assets/loans/` | 创建借用单 |
| GET | `/api/assets/loans/{id}/` | 获取借用单详情 |
| POST | `/api/assets/loans/{id}/approve/` | 审批借用单 |
| POST | `/api/assets/loans/{id}/confirm_borrow/` | 确认借出 |
| POST | `/api/assets/loans/{id}/confirm_return/` | 确认归还 |
| POST | `/api/assets/loans/check_overdue/` | 检查逾期借用 |

---

## 1. 领用单接口

### 1.1 获取领用单列表

**请求**
```
GET /api/assets/pickups/?status=pending&page=1&page_size=20
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态过滤 (draft/pending/approved/rejected/completed/cancelled) |
| search | string | 搜索关键词（领用单号/申请人） |
| applicant | integer | 申请人ID |
| department | integer | 部门ID |
| start_date | string | 开始日期 (YYYY-MM-DD) |
| end_date | string | 结束日期 (YYYY-MM-DD) |
| order_by | string | 排序字段 |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

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
        "id": 1,
        "pickup_no": "LY20240601001",
        "applicant": {
          "id": 5,
          "username": "zhangsan",
          "real_name": "张三"
        },
        "department": {
          "id": 3,
          "name": "研发部"
        },
        "pickup_date": "2024-06-01",
        "pickup_reason": "新员工入职设备配备",
        "status": "pending",
        "status_label": "待审批",
        "items_count": 3,
        "created_at": "2024-06-01T09:00:00Z",
        "approved_at": null,
        "approved_by": null
      }
    ]
  }
}
```

### 1.2 创建领用单

**请求**
```
POST /api/assets/pickups/
Content-Type: application/json

{
  "department": 3,
  "pickup_date": "2024-06-15",
  "pickup_reason": "项目需要领用笔记本电脑",
  "items": [
    {
      "asset_id": 15,
      "quantity": 1,
      "remark": "开发人员使用"
    },
    {
      "asset_id": 22,
      "quantity": 1,
      "remark": ""
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
    "id": 46,
    "pickup_no": "LY20240615001",
    "applicant": {
      "id": 5,
      "real_name": "张三"
    },
    "department": {
      "id": 3,
      "name": "研发部"
    },
    "status": "draft",
    "status_label": "草稿",
    "created_at": "2024-06-15T10:00:00Z"
  }
}
```

**错误响应**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "验证失败",
    "details": {
      "department": ["请选择领用部门"],
      "items": ["请至少添加一项资产"],
      "__all__": ["资产 MacBook Pro 已被使用，不能领用"]
    }
  }
}
```

### 1.3 获取领用单详情

**请求**
```
GET /api/assets/pickups/46/
```

**响应**
```json
{
  "id": 46,
  "pickup_no": "LY20240615001",
  "applicant": {
    "id": 5,
    "username": "zhangsan",
    "real_name": "张三",
    "department": {
      "id": 3,
      "name": "研发部"
    }
  },
  "department": {
    "id": 3,
    "name": "研发部"
  },
  "pickup_date": "2024-06-15",
  "pickup_reason": "项目需要领用笔记本电脑",
  "status": "approved",
  "status_label": "已批准",
  "approved_by": {
    "id": 2,
    "real_name": "李经理"
  },
  "approved_at": "2024-06-15T14:30:00Z",
  "approval_comment": "同意领用",
  "completed_at": null,
  "created_at": "2024-06-15T10:00:00Z",
  "items": [
    {
      "id": 101,
      "asset": {
        "id": 15,
        "asset_code": "ZC20240501005",
        "asset_name": "MacBook Pro",
        "specification": "M2 Pro 16G 512G",
        "asset_status": "in_use"
      },
      "quantity": 1,
      "remark": "开发人员使用",
      "snapshot_original_location": {
        "id": 10,
        "name": "3楼A区"
      },
      "snapshot_original_custodian": null
    }
  ],
  "approvals": [
    {
      "id": 201,
      "approver": {
        "id": 2,
        "real_name": "李经理"
      },
      "approval": "approved",
      "approval_label": "同意",
      "comment": "同意领用",
      "approved_at": "2024-06-15T14:30:00Z"
    }
  ]
}
```

### 1.4 提交审批

**请求**
```
POST /api/assets/pickups/46/submit/
```

**响应**
```json
{
  "id": 46,
  "pickup_no": "LY20240615001",
  "status": "pending",
  "status_label": "待审批"
}
```

### 1.5 审批领用单

**请求**
```
POST /api/assets/pickups/46/approve/
Content-Type: application/json

{
  "approval": "approved",
  "comment": "同意领用，请资产管理员发放"
}
```

**请求参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| approval | string | 是 | 审批结果 (approved/rejected) |
| comment | string | 否 | 审批意见 |

**响应（批准）**
```json
{
  "id": 46,
  "pickup_no": "LY20240615001",
  "status": "approved",
  "status_label": "已批准",
  "approved_by": {
    "id": 2,
    "real_name": "李经理"
  },
  "approved_at": "2024-06-15T14:30:00Z",
  "affected_assets": [
    {
      "id": 15,
      "asset_code": "ZC20240501005",
      "asset_name": "MacBook Pro",
      "custodian": {
        "id": 5,
        "real_name": "张三"
      },
      "asset_status": "in_use"
    }
  ]
}
```

**响应（拒绝）**
```json
{
  "id": 46,
  "pickup_no": "LY20240615001",
  "status": "rejected",
  "status_label": "已拒绝"
}
```

### 1.6 完成领用

**请求**
```
POST /api/assets/pickups/46/complete/
```

**响应**
```json
{
  "id": 46,
  "pickup_no": "LY20240615001",
  "status": "completed",
  "status_label": "已完成",
  "completed_at": "2024-06-15T16:00:00Z"
}
```

### 1.7 取消领用单

**请求**
```
POST /api/assets/pickups/46/cancel/
```

**响应**
```json
{
  "id": 46,
  "pickup_no": "LY20240615001",
  "status": "cancelled",
  "status_label": "已取消"
}
```

---

## 2. 调拨单接口

### 2.1 获取调拨单列表

**请求**
```
GET /api/assets/transfers/?status=pending&page=1
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态过滤 |
| from_department | integer | 调出部门ID |
| to_department | integer | 调入部门ID |
| search | string | 搜索关键词 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 12,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 8,
        "transfer_no": "DB20240610001",
        "from_department": {
          "id": 3,
          "name": "研发部"
        },
        "to_department": {
          "id": 5,
          "name": "市场部"
        },
        "transfer_date": "2024-06-10",
        "transfer_reason": "项目调整，设备转移",
        "status": "out_approved",
        "status_label": "调出方已批准",
        "items_count": 2,
        "created_at": "2024-06-10T09:00:00Z"
      }
    ]
  }
}
```

### 2.2 创建调拨单

**请求**
```
POST /api/assets/transfers/
Content-Type: application/json

{
  "from_department": 3,
  "to_department": 5,
  "transfer_date": "2024-06-15",
  "transfer_reason": "部门间设备调配",
  "items": [
    {
      "asset_id": 25,
      "to_location": 15,
      "remark": "调往市场部使用"
    },
    {
      "asset_id": 28,
      "to_location": 15,
      "remark": ""
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
    "id": 13,
    "transfer_no": "DB20240615001",
    "status": "draft"
  }
}
```

### 2.3 获取调拨单详情

**请求**
```
GET /api/assets/transfers/13/
```

**响应**
```json
{
  "id": 13,
  "transfer_no": "DB20240615001",
  "from_department": {
    "id": 3,
    "name": "研发部",
    "manager": {
      "id": 10,
      "real_name": "王经理"
    }
  },
  "to_department": {
    "id": 5,
    "name": "市场部",
    "manager": {
      "id": 12,
      "real_name": "赵经理"
    }
  },
  "transfer_date": "2024-06-15",
  "transfer_reason": "部门间设备调配",
  "status": "approved",
  "status_label": "双方已批准",
  "from_approved_by": {
    "id": 10,
    "real_name": "王经理"
  },
  "from_approved_at": "2024-06-15T10:00:00Z",
  "from_approve_comment": "同意调出",
  "to_approved_by": {
    "id": 12,
    "real_name": "赵经理"
  },
  "to_approved_at": "2024-06-15T14:00:00Z",
  "to_approve_comment": "同意接收",
  "completed_at": null,
  "items": [
    {
      "id": 301,
      "asset": {
        "id": 25,
        "asset_code": "ZC20240301010",
        "asset_name": "Dell 显示器 27寸"
      },
      "from_location": {
        "id": 10,
        "name": "3楼A区"
      },
      "from_custodian": {
        "id": 20,
        "real_name": "张三"
      },
      "to_location": {
        "id": 15,
        "name": "5楼B区"
      },
      "to_location_name": "5楼B区",
      "remark": ""
    }
  ]
}
```

### 2.4 调出方审批

**请求**
```
POST /api/assets/transfers/13/approve_from/
Content-Type: application/json

{
  "comment": "同意调出，设备状态良好"
}
```

**响应**
```json
{
  "id": 13,
  "transfer_no": "DB20240615001",
  "status": "out_approved",
  "status_label": "调出方已批准",
  "from_approved_by": {
    "id": 10,
    "real_name": "王经理"
  },
  "from_approved_at": "2024-06-15T10:00:00Z"
}
```

**错误响应**
```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "只有调出部门负责人可以审批"
  }
}
```

### 2.5 调入方审批

**请求**
```
POST /api/assets/transfers/13/approve_to/
Content-Type: application/json

{
  "comment": "同意接收"
}
```

**响应**
```json
{
  "id": 13,
  "transfer_no": "DB20240615001",
  "status": "approved",
  "status_label": "双方已批准",
  "to_approved_by": {
    "id": 12,
    "real_name": "赵经理"
  },
  "to_approved_at": "2024-06-15T14:00:00Z"
}
```

**错误响应**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请先完成调出方审批"
  }
}
```

### 2.6 完成调拨

**请求**
```
POST /api/assets/transfers/13/complete/
```

**响应**
```json
{
  "id": 13,
  "transfer_no": "DB20240615001",
  "status": "completed",
  "status_label": "已完成",
  "completed_at": "2024-06-15T16:00:00Z",
  "transferred_assets": [
    {
      "id": 25,
      "asset_code": "ZC20240301010",
      "department": {
        "id": 5,
        "name": "市场部"
      },
      "location": {
        "id": 15,
        "name": "5楼B区"
      }
    }
  ]
}
```

---

## 3. 退库单接口

### 3.1 获取退库单列表

**请求**
```
GET /api/assets/returns/?status=pending
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 8,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 5,
        "return_no": "TK20240612001",
        "returner": {
          "id": 8,
          "real_name": "李四"
        },
        "return_date": "2024-06-12",
        "return_reason": "项目结束，设备归还",
        "status": "pending",
        "status_label": "待确认",
        "items_count": 2,
        "return_location": {
          "id": 20,
          "name": "仓库A区"
        }
      }
    ]
  }
}
```

### 3.2 创建退库单

**请求**
```
POST /api/assets/returns/
Content-Type: application/json

{
  "return_date": "2024-06-15",
  "return_reason": "工作调动，归还设备",
  "return_location": 20,
  "items": [
    {
      "asset_id": 35,
      "asset_status": "idle",
      "condition_description": "设备完好，无损坏"
    },
    {
      "asset_id": 38,
      "asset_status": "maintenance",
      "condition_description": "屏幕有轻微划痕"
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
    "id": 9,
    "return_no": "TK20240615001",
    "status": "pending"
  }
}
```

### 3.3 获取退库单详情

**请求**
```
GET /api/assets/returns/9/
```

**响应**
```json
{
  "id": 9,
  "return_no": "TK20240615001",
  "returner": {
    "id": 8,
    "real_name": "李四"
  },
  "return_date": "2024-06-15",
  "return_reason": "工作调动，归还设备",
  "return_location": {
    "id": 20,
    "name": "仓库A区"
  },
  "status": "pending",
  "status_label": "待确认",
  "confirmed_by": null,
  "confirmed_at": null,
  "items": [
    {
      "id": 401,
      "asset": {
        "id": 35,
        "asset_code": "ZC20240201005",
        "asset_name": "ThinkPad X1"
      },
      "asset_status": "idle",
      "asset_status_label": "闲置",
      "condition_description": "设备完好，无损坏"
    }
  ]
}
```

### 3.4 确认退库

**请求**
```
POST /api/assets/returns/9/confirm/
```

**响应**
```json
{
  "id": 9,
  "return_no": "TK20240615001",
  "status": "completed",
  "status_label": "已完成",
  "confirmed_by": {
    "id": 2,
    "real_name": "资产管理员"
  },
  "confirmed_at": "2024-06-15T15:00:00Z",
  "updated_assets": [
    {
      "id": 35,
      "asset_code": "ZC20240201005",
      "asset_status": "idle",
      "custodian": null,
      "location": {
        "id": 20,
        "name": "仓库A区"
      }
    }
  ]
}
```

### 3.5 拒绝退库

**请求**
```
POST /api/assets/returns/9/reject/
Content-Type: application/json

{
  "reason": "设备有损坏，请先维修后再退库"
}
```

**响应**
```json
{
  "id": 9,
  "return_no": "TK20240615001",
  "status": "rejected",
  "status_label": "已拒绝"
}
```

---

## 4. 借用单接口

### 4.1 获取借用单列表

**请求**
```
GET /api/assets/loans/?status=borrowed
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
        "id": 12,
        "loan_no": "JY20240605001",
        "borrower": {
          "id": 15,
          "real_name": "王五"
        },
        "borrow_date": "2024-06-05",
        "expected_return_date": "2024-06-20",
        "status": "borrowed",
        "status_label": "借出中",
        "items_count": 1,
        "is_overdue": false
      }
    ]
  }
}
```

### 4.2 创建借用单

**请求**
```
POST /api/assets/loans/
Content-Type: application/json

{
  "borrow_date": "2024-06-15",
  "expected_return_date": "2024-06-30",
  "loan_reason": "临时出差使用",
  "items": [
    {
      "asset_id": 50,
      "remark": ""
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
    "id": 18,
    "loan_no": "JY20240615001",
    "status": "pending"
  }
}
```

### 4.3 获取借用单详情

**请求**
```
GET /api/assets/loans/18/
```

**响应**
```json
{
  "id": 18,
  "loan_no": "JY20240615001",
  "borrower": {
    "id": 15,
    "real_name": "王五"
  },
  "borrow_date": "2024-06-15",
  "expected_return_date": "2024-06-30",
  "actual_return_date": null,
  "loan_reason": "临时出差使用",
  "status": "borrowed",
  "status_label": "借出中",
  "is_overdue": false,
  "approved_by": {
    "id": 10,
    "real_name": "李经理"
  },
  "approved_at": "2024-06-15T10:00:00Z",
  "lent_by": {
    "id": 5,
    "real_name": "资产管理员"
  },
  "lent_at": "2024-06-15T11:00:00Z",
  "items": [
    {
      "id": 501,
      "asset": {
        "id": 50,
        "asset_code": "ZC20240101020",
        "asset_name": "iPad Pro 12.9寸"
      }
    }
  ]
}
```

### 4.4 审批借用单

**请求**
```
POST /api/assets/loans/18/approve/
Content-Type: application/json

{
  "approval": "approved",
  "comment": "同意借用，请按时归还"
}
```

**响应**
```json
{
  "id": 18,
  "loan_no": "JY20240615001",
  "status": "approved",
  "status_label": "已批准",
  "approved_by": {
    "id": 10,
    "real_name": "李经理"
  },
  "approved_at": "2024-06-15T10:00:00Z"
}
```

### 4.5 确认借出

**请求**
```
POST /api/assets/loans/18/confirm_borrow/
```

**响应**
```json
{
  "id": 18,
  "loan_no": "JY20240615001",
  "status": "borrowed",
  "status_label": "借出中",
  "lent_by": {
    "id": 5,
    "real_name": "资产管理员"
  },
  "lent_at": "2024-06-15T11:00:00Z",
  "updated_assets": [
    {
      "id": 50,
      "asset_status": "in_use",
      "user": {
        "id": 15,
        "real_name": "王五"
      }
    }
  ]
}
```

### 4.6 确认归还

**请求**
```
POST /api/assets/loans/18/confirm_return/
Content-Type: application/json

{
  "condition": "good",
  "comment": "设备完好"
}
```

**请求参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| condition | string | 资产状况 (good/minor_damage/major_damage/lost) |
| comment | string | 备注 |

**响应**
```json
{
  "id": 18,
  "loan_no": "JY20240615001",
  "status": "returned",
  "status_label": "已归还",
  "actual_return_date": "2024-06-28",
  "returned_at": "2024-06-28T14:00:00Z",
  "return_confirmed_by": {
    "id": 5,
    "real_name": "资产管理员"
  },
  "asset_condition": "good",
  "asset_condition_label": "完好",
  "updated_assets": [
    {
      "id": 50,
      "asset_status": "idle",
      "user": null
    }
  ]
}
```

### 4.7 检查逾期借用

**请求**
```
POST /api/assets/loans/check_overdue/
```

**响应**
```json
{
  "updated_count": 5,
  "overdue_loans": [
    {
      "id": 10,
      "loan_no": "JY20240501001",
      "borrower": "张三",
      "expected_return_date": "2024-05-15",
      "overdue_days": 3
    }
  ]
}
```

---

## 数据字典

### 领用单状态 (pickup_status)

| 值 | 说明 | 允许操作 |
|----|------|----------|
| draft | 草稿 | 编辑、提交、取消 |
| pending | 待审批 | 审批、取消 |
| approved | 已批准 | 完成 |
| rejected | 已拒绝 | - |
| completed | 已完成 | - |
| cancelled | 已取消 | - |

### 调拨单状态 (transfer_status)

| 值 | 说明 | 允许操作 |
|----|------|----------|
| draft | 草稿 | 编辑、提交 |
| pending | 待审批 | 调出方审批 |
| out_approved | 调出方已批准 | 调入方审批 |
| approved | 双方已批准 | 完成 |
| rejected | 已拒绝 | - |
| completed | 已完成 | - |
| cancelled | 已取消 | - |

### 退库单状态 (return_status)

| 值 | 说明 |
|----|------|
| pending | 待确认 |
| approved | 已确认 |
| rejected | 已拒绝 |
| completed | 已完成 |

### 借用单状态 (loan_status)

| 值 | 说明 |
|----|------|
| pending | 待审批 |
| approved | 已批准 |
| borrowed | 借出中 |
| returned | 已归还 |
| overdue | 已逾期 |
| rejected | 已拒绝 |
| cancelled | 已取消 |

### 资产归还状况 (asset_condition)

| 值 | 说明 |
|----|------|
| good | 完好 |
| minor_damage | 轻微损坏 |
| major_damage | 严重损坏 |
| lost | 丢失 |

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 领用单/调拨单/借用单不存在 |
| VALIDATION_ERROR | 400 | 领用单当前状态不允许编辑/资产不可用/状态转换不允许/调拨单未完成审批/借用已逾期/借用期限超过限制/退库资产与保管人不匹配 |
| PERMISSION_DENIED | 403 | 无权限操作 |
