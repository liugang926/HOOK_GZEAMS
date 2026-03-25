## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

# Phase 1.7: 资产生命周期管理 - API接口定义

## 1. 采购申请 API

### 1.1 采购申请列表

```
GET /api/lifecycle/purchase-requests/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |
| status | string | 否 | 状态筛选 |
| department_id | int | 否 | 部门筛选 |
| applicant_id | int | 否 | 申请人筛选 |
| request_no | string | 否 | 申请单号模糊搜索 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "count": 100,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "request_no": "PR2024010001",
      "status": "approved",
      "status_display": "已审批",
      "applicant": {
        "id": 1,
        "username": "zhangsan",
        "full_name": "张三"
      },
      "department": {
        "id": 1,
        "name": "研发部"
      },
      "request_date": "2024-01-15",
      "expected_date": "2024-02-15",
      "reason": "新增开发人员需要配置电脑",
      "budget_amount": "50000.00",
      "cost_center": {
        "id": 1,
        "name": "研发成本中心"
      },
      "current_approver": null,
      "approved_at": "2024-01-16T10:30:00Z",
      "approved_by": {
        "id": 2,
        "username": "lisi",
        "full_name": "李四"
      },
      "m18_purchase_order_no": "PO2024010001",
      "m18_sync_status": "completed",
      "items_count": 5,
      "items_total_amount": "45000.00",
      "created_at": "2024-01-15T09:00:00Z",
      "updated_at": "2024-01-16T10:30:00Z"
    }
  ]
}
```

### 1.2 采购申请详情

```
GET /api/lifecycle/purchase-requests/{id}/
```

**Response:**
```json
{
  "id": 1,
  "request_no": "PR2024010001",
  "status": "approved",
  "status_display": "已审批",
  "applicant": {
    "id": 1,
    "username": "zhangsan",
    "full_name": "张三",
    "email": "zhangsan@example.com"
  },
  "department": {
    "id": 1,
    "name": "研发部",
    "code": "RD"
  },
  "request_date": "2024-01-15",
  "expected_date": "2024-02-15",
  "reason": "新增开发人员需要配置电脑",
  "budget_amount": "50000.00",
  "cost_center": {
    "id": 1,
    "name": "研发成本中心",
    "code": "CC001"
  },
  "current_approver": null,
  "approved_at": "2024-01-16T10:30:00Z",
  "approved_by": {
    "id": 2,
    "username": "lisi",
    "full_name": "李四"
  },
  "m18_purchase_order_no": "PO2024010001",
  "pushed_to_m18_at": "2024-01-16T11:00:00Z",
  "m18_sync_status": "completed",
  "custom_fields": {},
  "items": [
    {
      "id": 1,
      "sequence": 1,
      "asset_category": {
        "id": 1,
        "name": "电子设备",
        "code": "IT"
      },
      "item_name": "笔记本电脑",
      "specification": "ThinkPad X1 Carbon, i7/16G/512G",
      "brand": "Lenovo",
      "quantity": 10,
      "unit": "台",
      "unit_price": "4500.00",
      "total_amount": "45000.00",
      "suggested_supplier": "联想代理商",
      "remark": ""
    }
  ],
  "attachments": [],
  "approval_history": [
    {
      "step": "部门主管审批",
      "approver": "李四",
      "action": "approved",
      "comment": "同意",
      "approved_at": "2024-01-16T10:30:00Z"
    }
  ],
  "created_at": "2024-01-15T09:00:00Z",
  "updated_at": "2024-01-16T10:30:00Z",
  "created_by": {
    "id": 1,
    "username": "zhangsan"
  }
}
```

### 1.3 创建采购申请

```
POST /api/lifecycle/purchase-requests/
```

**Request:**
```json
{
  "department_id": 1,
  "request_date": "2024-01-15",
  "expected_date": "2024-02-15",
  "reason": "新增开发人员需要配置电脑",
  "budget_amount": "50000.00",
  "cost_center_id": 1,
  "custom_fields": {},
  "items": [
    {
      "asset_category_id": 1,
      "item_name": "笔记本电脑",
      "specification": "ThinkPad X1 Carbon, i7/16G/512G",
      "brand": "Lenovo",
      "quantity": 10,
      "unit": "台",
      "unit_price": "4500.00",
      "suggested_supplier": "联想代理商",
      "remark": ""
    }
  ]
}
```

**响应**
```json
{
  "success": true,
  "message": "采购申请创建成功",
  "data": {
    "id": 1,
    "request_no": "PR2024010001",
    "status": "draft"
  }
}
```

### 1.4 更新采购申请

```
PUT /api/lifecycle/purchase-requests/{id}/
PATCH /api/lifecycle/purchase-requests/{id}/
```

**Request:** 同创建

### 1.5 删除采购申请

```
DELETE /api/lifecycle/purchase-requests/{id}/
```

**响应**
```json
{
  "success": true,
  "message": "采购申请删除成功"
}
```

### 1.6 提交审批

```
POST /api/lifecycle/purchase-requests/{id}/submit/
```

**响应**
```json
{
  "success": true,
  "message": "已提交审批",
  "data": {
    "id": 1,
    "status": "submitted"
  }
}
```

### 1.7 审批采购申请

```
POST /api/lifecycle/purchase-requests/{id}/approve/
```

**Request:**
```json
{
  "approved": true,
  "comment": "同意采购"
}
```

**响应**
```json
{
  "success": true,
  "message": "审批通过",
  "data": {
    "id": 1,
    "status": "approved"
  }
}
```

### 1.8 取消采购申请

```
POST /api/lifecycle/purchase-requests/{id}/cancel/
```

**Request:**
```json
{
  "reason": "需求变更"
}
```

---

## 2. 资产入库 API

### 2.1 验收单列表

```
GET /api/lifecycle/asset-receipts/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| status | string | 否 | 状态筛选 |
| receipt_type | string | 否 | 入库类型 |
| receipt_no | string | 否 | 验收单号搜索 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "receipt_no": "RC2024010001",
      "status": "passed",
      "status_display": "验收通过",
      "receipt_date": "2024-01-20",
      "receipt_type": "purchase",
      "receipt_type_display": "采购入库",
      "purchase_request": {
        "id": 1,
        "request_no": "PR2024010001"
      },
      "m18_purchase_order_no": "PO2024010001",
      "supplier": "联想代理商",
      "delivery_no": "DN20240115001",
      "receiver": {
        "id": 3,
        "username": "wangwu",
        "full_name": "王五"
      },
      "inspector": {
        "id": 3,
        "username": "wangwu",
        "full_name": "王五"
      },
      "items_count": 1,
      "passed_at": "2024-01-20T15:30:00Z",
      "created_at": "2024-01-20T10:00:00Z"
    }
  ]
}
```

### 2.2 验收单详情

```
GET /api/lifecycle/asset-receipts/{id}/
```

**Response:**
```json
{
  "id": 1,
  "receipt_no": "RC2024010001",
  "status": "passed",
  "status_display": "验收通过",
  "receipt_date": "2024-01-20",
  "receipt_type": "purchase",
  "receipt_type_display": "采购入库",
  "purchase_request": {
    "id": 1,
    "request_no": "PR2024010001"
  },
  "m18_purchase_order_no": "PO2024010001",
  "supplier": "联想代理商",
  "delivery_no": "DN20240115001",
  "receiver": {
    "id": 3,
    "username": "wangwu",
    "full_name": "王五"
  },
  "inspector": {
    "id": 3,
    "username": "wangwu",
    "full_name": "王五"
  },
  "inspection_result": "货物完好，数量一致",
  "passed_at": "2024-01-20T15:30:00Z",
  "custom_fields": {},
  "items": [
    {
      "id": 1,
      "sequence": 1,
      "asset_category": {
        "id": 1,
        "name": "电子设备"
      },
      "item_name": "笔记本电脑",
      "specification": "ThinkPad X1 Carbon, i7/16G/512G",
      "brand": "Lenovo",
      "ordered_quantity": 10,
      "received_quantity": 10,
      "qualified_quantity": 10,
      "defective_quantity": 0,
      "unit_price": "4500.00",
      "total_amount": "45000.00",
      "asset_generated": true,
      "generated_assets": [
        {
          "id": 1,
          "asset_no": "ZC2024010001",
          "asset_name": "笔记本电脑"
        }
      ],
      "remark": ""
    }
  ],
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T15:30:00Z"
}
```

### 2.3 创建验收单

```
POST /api/lifecycle/asset-receipts/
```

**Request:**
```json
{
  "receipt_date": "2024-01-20",
  "receipt_type": "purchase",
  "purchase_request_id": 1,
  "m18_purchase_order_no": "PO2024010001",
  "supplier": "联想代理商",
  "delivery_no": "DN20240115001",
  "custom_fields": {},
  "items": [
    {
      "asset_category_id": 1,
      "item_name": "笔记本电脑",
      "specification": "ThinkPad X1 Carbon, i7/16G/512G",
      "brand": "Lenovo",
      "ordered_quantity": 10,
      "received_quantity": 10,
      "defective_quantity": 0,
      "unit_price": "4500.00",
      "remark": ""
    }
  ]
}
```

**响应**
```json
{
  "success": true,
  "message": "验收单创建成功",
  "data": {
    "id": 1,
    "receipt_no": "RC2024010001",
    "status": "draft"
  }
}
```

### 2.4 验收通过

```
POST /api/lifecycle/asset-receipts/{id}/pass-inspection/
```

**Request:**
```json
{
  "inspection_result": "货物完好，数量一致，质量合格"
}
```

**Response:**
```json
{
  "id": 1,
  "status": "passed",
  "message": "验收通过，已生成资产卡片",
  "generated_assets_count": 10
}
```

### 2.5 验收不通过

```
POST /api/lifecycle/asset-receipts/{id}/reject-inspection/
```

**Request:**
```json
{
  "reason": "货物外包装破损，需重新发货"
}
```

---

## 3. 维护保养 API

### 3.1 维修单列表

```
GET /api/lifecycle/maintenance/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| status | string | 否 | 状态筛选 |
| priority | string | 否 | 优先级筛选 |
| asset_id | int | 否 | 资产筛选 |
| reporter_id | int | 否 | 报修人筛选 |
| technician_id | int | 否 | 维修人员筛选 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "count": 30,
  "results": [
    {
      "id": 1,
      "maintenance_no": "MT2024010001",
      "status": "completed",
      "status_display": "已完成",
      "priority": "normal",
      "priority_display": "普通",
      "asset": {
        "id": 1,
        "asset_no": "ZC2024010001",
        "asset_name": "笔记本电脑"
      },
      "reporter": {
        "id": 1,
        "username": "zhangsan",
        "full_name": "张三"
      },
      "report_time": "2024-01-25T09:00:00Z",
      "fault_description": "无法开机，电源指示灯不亮",
      "technician": {
        "id": 5,
        "username": "fixer",
        "full_name": "维修员"
      },
      "start_time": "2024-01-25T10:00:00Z",
      "end_time": "2024-01-25T11:30:00Z",
      "work_hours": 1.5,
      "total_cost": "150.00",
      "created_at": "2024-01-25T09:00:00Z"
    }
  ]
}
```

### 3.2 维修单详情

```
GET /api/lifecycle/maintenance/{id}/
```

**Response:**
```json
{
  "id": 1,
  "maintenance_no": "MT2024010001",
  "status": "completed",
  "status_display": "已完成",
  "priority": "normal",
  "priority_display": "普通",
  "asset": {
    "id": 1,
    "asset_no": "ZC2024010001",
    "asset_name": "笔记本电脑",
    "category": "电子设备",
    "location": "A栋301"
  },
  "reporter": {
    "id": 1,
    "username": "zhangsan",
    "full_name": "张三",
    "phone": "13800138000"
  },
  "report_time": "2024-01-25T09:00:00Z",
  "fault_description": "无法开机，电源指示灯不亮",
  "fault_photo_urls": ["https://example.com/photos/1.jpg"],
  "technician": {
    "id": 5,
    "username": "fixer",
    "full_name": "维修员",
    "phone": "13900139000"
  },
  "assigned_at": "2024-01-25T09:30:00Z",
  "start_time": "2024-01-25T10:00:00Z",
  "end_time": "2024-01-25T11:30:00Z",
  "work_hours": 1.5,
  "fault_cause": "电源适配器损坏",
  "repair_method": "更换电源适配器",
  "replaced_parts": "65W电源适配器 x1",
  "repair_result": "修复完成，正常使用",
  "labor_cost": "100.00",
  "material_cost": "50.00",
  "other_cost": "0.00",
  "total_cost": "150.00",
  "verified_by": {
    "id": 1,
    "username": "zhangsan",
    "full_name": "张三"
  },
  "verified_at": "2024-01-25T12:00:00Z",
  "verification_result": "确认修复",
  "custom_fields": {},
  "created_at": "2024-01-25T09:00:00Z",
  "updated_at": "2024-01-25T12:00:00Z"
}
```

### 3.3 创建维修申请

```
POST /api/lifecycle/maintenance/
```

**Request:**
```json
{
  "asset_id": 1,
  "fault_description": "无法开机，电源指示灯不亮",
  "fault_photo_urls": ["https://example.com/photos/1.jpg"],
  "priority": "normal"
}
```

**响应**
```json
{
  "success": true,
  "message": "维修申请创建成功",
  "data": {
    "id": 1,
    "maintenance_no": "MT2024010001",
    "status": "pending"
  }
}
```

### 3.4 派单

```
POST /api/lifecycle/maintenance/{id}/assign/
```

**Request:**
```json
{
  "technician_id": 5
}
```

### 3.5 完成维修

```
POST /api/lifecycle/maintenance/{id}/complete/
```

**Request:**
```json
{
  "start_time": "2024-01-25T10:00:00Z",
  "work_hours": 1.5,
  "fault_cause": "电源适配器损坏",
  "repair_method": "更换电源适配器",
  "replaced_parts": "65W电源适配器 x1",
  "repair_result": "修复完成，正常使用",
  "labor_cost": "100.00",
  "material_cost": "50.00",
  "other_cost": "0.00"
}
```

### 3.6 验收维修

```
POST /api/lifecycle/maintenance/{id}/verify/
```

**Request:**
```json
{
  "verification_result": "确认修复，可以正常使用"
}
```

### 3.7 保养计划列表

```
GET /api/lifecycle/maintenance-plans/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| status | string | 否 | 状态筛选 |
| cycle_type | string | 否 | 周期类型 |

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "plan_name": "空调季度保养",
      "plan_code": "MP001",
      "status": "active",
      "status_display": "启用",
      "target_type": "category",
      "target_type_display": "按类别",
      "cycle_type": "quarterly",
      "cycle_type_display": "每季度",
      "cycle_value": 1,
      "start_date": "2024-01-01",
      "end_date": null,
      "remind_days_before": 3,
      "maintenance_content": "清洗滤网、检查制冷剂、检查电路",
      "estimated_hours": 2.0,
      "asset_categories_count": 1,
      "assets_count": 20,
      "tasks_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 3.8 创建保养计划

```
POST /api/lifecycle/maintenance-plans/
```

**Request:**
```json
{
  "plan_name": "空调季度保养",
  "plan_code": "MP001",
  "target_type": "category",
  "cycle_type": "quarterly",
  "cycle_value": 1,
  "start_date": "2024-01-01",
  "remind_days_before": 3,
  "maintenance_content": "清洗滤网、检查制冷剂、检查电路",
  "estimated_hours": 2.0,
  "asset_category_ids": [5],
  "remind_user_ids": [3, 4]
}
```

### 3.9 保养任务列表

```
GET /api/lifecycle/maintenance-tasks/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| status | string | 否 | 状态筛选 |
| plan_id | int | 否 | 计划筛选 |
| executor_id | int | 否 | 执行人筛选 |
| scheduled_date_from | date | 否 | 计划日期起 |
| scheduled_date_to | date | 否 | 计划日期止 |

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "task_no": "TSK20240125001",
      "status": "pending",
      "status_display": "待执行",
      "plan": {
        "id": 1,
        "plan_name": "空调季度保养",
        "plan_code": "MP001"
      },
      "asset": {
        "id": 15,
        "asset_no": "ZC2023010015",
        "asset_name": "空调",
        "location": "A栋301"
      },
      "scheduled_date": "2024-01-28",
      "deadline_date": "2024-02-04",
      "executor": null,
      "start_time": null,
      "end_time": null,
      "created_at": "2024-01-25T00:00:00Z"
    }
  ]
}
```

### 3.10 执行保养任务

```
POST /api/lifecycle/maintenance-tasks/{id}/execute/
```

**Request:**
```json
{
  "executor_id": 6,
  "start_time": "2024-01-28T09:00:00Z",
  "end_time": "2024-01-28T11:00:00Z",
  "execution_content": "已完成清洗滤网、检查制冷剂、检查电路",
  "execution_photo_urls": ["https://example.com/photos/1.jpg"],
  "finding": "制冷剂充足，无需补充",
  "next_maintenance_suggestion": "3个月后继续常规保养"
}
```

---

## 4. 报废处置 API

### 4.1 报废申请列表

```
GET /api/lifecycle/disposal-requests/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| status | string | 否 | 状态筛选 |
| disposal_type | string | 否 | 处置方式 |
| applicant_id | int | 否 | 申请人筛选 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "request_no": "DS2024010001",
      "status": "completed",
      "status_display": "已完成",
      "disposal_type": "scrap",
      "disposal_type_display": "报废",
      "applicant": {
        "id": 2,
        "username": "lisi",
        "full_name": "李四"
      },
      "department": {
        "id": 2,
        "name": "行政部"
      },
      "request_date": "2024-01-10",
      "disposal_reason": "使用年限已到，设备老化",
      "reason_type": "expired",
      "reason_type_display": "使用年限到期",
      "items_count": 3,
      "total_original_value": "15000.00",
      "total_net_value": "500.00",
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

### 4.2 报废申请详情

```
GET /api/lifecycle/disposal-requests/{id}/
```

**Response:**
```json
{
  "id": 1,
  "request_no": "DS2024010001",
  "status": "completed",
  "status_display": "已完成",
  "disposal_type": "scrap",
  "disposal_type_display": "报废",
  "applicant": {
    "id": 2,
    "username": "lisi",
    "full_name": "李四"
  },
  "department": {
    "id": 2,
    "name": "行政部"
  },
  "request_date": "2024-01-10",
  "disposal_reason": "使用年限已到，设备老化",
  "reason_type": "expired",
  "reason_type_display": "使用年限到期",
  "custom_fields": {},
  "items": [
    {
      "id": 1,
      "sequence": 1,
      "asset": {
        "id": 100,
        "asset_no": "ZC2020010001",
        "asset_name": "台式电脑",
        "category": "电子设备",
        "specification": "联想启天 M415",
        "original_value": "5000.00",
        "accumulated_depreciation": "4833.33",
        "net_value": "166.67"
      },
      "original_value": "5000.00",
      "accumulated_depreciation": "4833.33",
      "net_value": "166.67",
      "appraisal_result": "设备老化严重，无法修复，建议报废",
      "residual_value": "0.00",
      "appraised_by": {
        "id": 7,
        "username": "appraiser",
        "full_name": "鉴定员"
      },
      "appraised_at": "2024-01-12T10:00:00Z",
      "disposal_executed": true,
      "executed_at": "2024-01-15T14:00:00Z",
      "actual_residual_value": "0.00",
      "buyer_info": null,
      "remark": ""
    }
  ],
  "approval_history": [
    {
      "step": "资产管理审批",
      "approver": "资产管理员",
      "action": "approved",
      "comment": "同意",
      "approved_at": "2024-01-11T10:00:00Z"
    },
    {
      "step": "财务审批",
      "approver": "财务经理",
      "action": "approved",
      "comment": "符合报废条件，同意",
      "approved_at": "2024-01-11T15:00:00Z"
    }
  ],
  "created_at": "2024-01-10T09:00:00Z",
  "updated_at": "2024-01-15T14:00:00Z"
}
```

### 4.3 创建报废申请

```
POST /api/lifecycle/disposal-requests/
```

**Request:**
```json
{
  "department_id": 2,
  "disposal_type": "scrap",
  "disposal_reason": "使用年限已到，设备老化",
  "reason_type": "expired",
  "asset_ids": [100, 101, 102],
  "custom_fields": {}
}
```

**响应**
```json
{
  "success": true,
  "message": "报废申请创建成功",
  "data": {
    "id": 1,
    "request_no": "DS2024010001",
    "status": "draft"
  }
}
```

### 4.4 提交鉴定

```
POST /api/lifecycle/disposal-requests/{id}/submit-appraisal/
```

### 4.5 完成鉴定

```
POST /api/lifecycle/disposal-requests/items/{item_id}/complete-appraisal/
```

**Request:**
```json
{
  "appraisal_result": "设备老化严重，无法修复，建议报废",
  "residual_value": "0.00"
}
```

### 4.6 执行处置

```
POST /api/lifecycle/disposal-requests/{id}/execute/
```

**Request:**
```json
{
  "items": [
    {
      "item_id": 1,
      "actual_residual_value": "0.00",
      "buyer_info": null
    }
  ]
}
```

---

## 5. 统计报表 API

### 5.1 采购统计

```
GET /api/lifecycle/statistics/purchase/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date_from | date | 是 | 开始日期 |
| date_to | date | 是 | 结束日期 |
| department_id | int | 否 | 部门筛选 |
| group_by | string | 否 | 分组方式：department/category |

**Response:**
```json
{
  "summary": {
    "total_requests": 50,
    "pending_requests": 5,
    "approved_requests": 40,
    "rejected_requests": 5,
    "total_amount": "500000.00",
    "completed_amount": "450000.00"
  },
  "by_department": [
    {
      "department_id": 1,
      "department_name": "研发部",
      "request_count": 20,
      "total_amount": "200000.00"
    }
  ],
  "by_category": [
    {
      "category_id": 1,
      "category_name": "电子设备",
      "request_count": 30,
      "total_amount": "300000.00"
    }
  ],
  "trend": [
    {
      "month": "2024-01",
      "count": 10,
      "amount": "100000.00"
    }
  ]
}
```

### 5.2 维修统计

```
GET /api/lifecycle/statistics/maintenance/
```

**Query Parameters:** 同采购统计

**Response:**
```json
{
  "summary": {
    "total_maintenance": 100,
    "pending_maintenance": 10,
    "in_progress_maintenance": 5,
    "completed_maintenance": 85,
    "total_cost": "15000.00",
    "avg_work_hours": 2.5
  },
  "by_asset": [
    {
      "asset_id": 1,
      "asset_name": "笔记本电脑",
      "maintenance_count": 5,
      "total_cost": "500.00"
    }
  ],
  "by_technician": [
    {
      "technician_id": 5,
      "technician_name": "维修员",
      "completed_count": 30,
      "total_cost": "3000.00"
    }
  ]
}
```

### 5.3 处置统计

```
GET /api/lifecycle/statistics/disposal/
```

**Response:**
```json
{
  "summary": {
    "total_requests": 20,
    "pending_requests": 2,
    "completed_requests": 18,
    "total_original_value": "100000.00",
    "total_net_value": "5000.00",
    "total_residual_value": "2000.00"
  },
  "by_reason_type": [
    {
      "reason_type": "expired",
      "reason_type_display": "使用年限到期",
      "count": 15,
      "original_value": "75000.00"
    }
  ],
  "by_disposal_type": [
    {
      "disposal_type": "scrap",
      "disposal_type_display": "报废",
      "count": 15,
      "residual_value": "500.00"
    }
  ]
}
```

---

## 6. WebSocket 事件

### 6.1 采购审批事件

```json
{
  "event": "purchase.request.approved",
  "data": {
    "request_id": 1,
    "request_no": "PR2024010001",
    "status": "approved",
    "approved_by": "李四",
    "approved_at": "2024-01-16T10:30:00Z"
  }
}
```

### 6.2 维修派单事件

```json
{
  "event": "maintenance.assigned",
  "data": {
    "maintenance_id": 1,
    "maintenance_no": "MT2024010001",
    "asset_name": "笔记本电脑",
    "technician_id": 5,
    "fault_description": "无法开机"
  }
}
```

### 6.3 保养提醒事件

```json
{
  "event": "maintenance.task.reminder",
  "data": {
    "task_id": 1,
    "task_no": "TSK20240125001",
    "asset_name": "空调",
    "scheduled_date": "2024-01-28",
    "days_remaining": 3
  }
}
```

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 采购申请不存在 |
| CONFLICT | 409 | 采购申请状态不允许此操作 |
| NOT_FOUND | 404 | 验收单不存在 |
| CONFLICT | 409 | 验收单已验收通过 |
| NOT_FOUND | 404 | 维修单不存在 |
| CONFLICT | 409 | 资产正在维修中 |
| NOT_FOUND | 404 | 保养计划不存在 |
| NOT_FOUND | 404 | 报废申请不存在 |
| CONFLICT | 409 | 资产已报废 |
| VALIDATION_ERROR | 400 | 资产不在申请部门 |
| CONFLICT | 409 | 鉴定未完成，无法执行处置 |
| SERVER_ERROR | 500 | M18同步失败 |
