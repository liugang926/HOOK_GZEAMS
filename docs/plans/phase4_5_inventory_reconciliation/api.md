# Phase 4.5: 盘点业务链条 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 1. 盘点差异 API

### 1.1 差异列表

```
GET /api/inventory/differences/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| task_id | int | 否 | 盘点任务筛选 |
| difference_type | string | 否 | 差异类型筛选 |
| status | string | 否 | 状态筛选 |
| responsible_user_id | int | 否 | 责任人筛选 |
| keyword | string | 否 | 关键词搜索（资产名称、编号） |

**Response:**
```json
{
  "success": true,
  "message": "获取差异列表成功",
  "data": {
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "task": {
          "id": 1,
          "task_no": "PD2024010001",
          "task_name": "2024年1月全公司盘点"
        },
        "difference_type": "loss",
        "difference_type_display": "盘亏",
        "status": "pending",
        "status_display": "待认定",
        "asset": {
          "id": 1,
          "asset_no": "ZC2024010001",
          "asset_name": "笔记本电脑"
        },
        "account_location": {
          "id": 1,
          "name": "A栋301"
        },
        "account_status": "in_use",
        "account_value": "5000.00",
        "actual_location": null,
        "actual_status": null,
        "description": "资产未在盘点中扫描到",
        "confirmed_by": null,
        "confirmed_at": null,
        "responsible_user": null,
        "responsible_department": null,
        "created_at": "2024-01-20T10:00:00Z"
      }
    ]
  }
}
```

### 1.2 差异详情

```
GET /api/inventory/differences/{id}/
```

**Response:**
```json
{
  "success": true,
  "message": "获取差异详情成功",
  "data": {
    "id": 1,
    "task": {
      "id": 1,
      "task_no": "PD2024010001",
      "task_name": "2024年1月全公司盘点"
    },
    "snapshot_item": {
      "id": 1,
      "asset_no": "ZC2024010001",
      "location": "A栋301"
    },
    "difference_type": "loss",
    "difference_type_display": "盘亏",
    "status": "confirmed",
    "status_display": "已认定",
    "asset": {
      "id": 1,
      "asset_no": "ZC2024010001",
      "asset_name": "笔记本电脑",
      "category": "电子设备",
      "original_value": "5000.00",
      "net_value": "2500.00"
    },
    "account_location": {
      "id": 1,
      "name": "A栋301",
      "full_path": "总部/A栋/301"
    },
    "account_status": "in_use",
    "account_status_display": "在用",
    "account_value": "5000.00",
    "actual_location": null,
    "actual_status": null,
    "actual_value": null,
    "description": "资产未在盘点中扫描到",
    "confirmed_by": {
      "id": 3,
      "username": "admin",
      "full_name": "管理员"
    },
    "confirmed_at": "2024-01-21T10:00:00Z",
    "confirmation_note": "确认盘亏，需进一步调查原因",
    "responsible_user": {
      "id": 5,
      "username": "zhangsan",
      "full_name": "张三"
    },
    "responsible_department": {
      "id": 2,
      "name": "研发部"
    },
    "resolution": null,
    "adjustment": null,
    "scan_history": [
      {
        "scan_time": "2024-01-15T10:30:00Z",
        "location": "A栋301",
        "scanner": "李四"
      }
    ],
    "created_at": "2024-01-20T10:00:00Z",
    "updated_at": "2024-01-21T10:00:00Z"
  }
}
```

### 1.3 认定差异

```
POST /api/inventory/differences/{id}/confirm/
```

**Request:**
```json
{
  "confirmation_note": "确认盘亏，资产可能已丢失",
  "responsible_user_id": 5,
  "responsible_department_id": 2
}
```

**Response:**
```json
{
  "success": true,
  "message": "差异认定成功",
  "data": {
    "id": 1,
    "status": "confirmed"
  }
}
```

### 1.4 批量认定差异

```
POST /api/inventory/differences/batch-confirm/
```

**Request:**
```json
{
  "difference_ids": [1, 2, 3],
  "confirmation_note": "批量认定",
  "responsible_user_id": 5,
  "responsible_department_id": 2
}
```

**Response:**
```json
{
  "success": true,
  "message": "批量认定完成",
  "data": {
    "summary": {
      "total": 3,
      "succeeded": 3,
      "failed": 0
    },
    "results": [
      {"id": 1, "success": true},
      {"id": 2, "success": true},
      {"id": 3, "success": true}
    ]
  }
}
```

### 1.5 重新分析差异

```
POST /api/inventory/differences/analyze/
```

**Request:**
```json
{
  "task_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "差异分析完成",
  "data": {
    "task_id": 1,
    "new_differences": 5,
    "total_differences": 50
  }
}
```

---

## 2. 差异处理 API

### 2.1 处理单列表

```
GET /api/inventory/resolutions/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| task_id | int | 否 | 盘点任务筛选 |
| status | string | 否 | 状态筛选 |
| action | string | 否 | 处理方式筛选 |
| applicant_id | int | 否 | 申请人筛选 |

**Response:**
```json
{
  "success": true,
  "message": "获取处理单列表成功",
  "data": {
    "count": 20,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "resolution_no": "RS2024010001",
        "status": "approved",
        "status_display": "已批准",
        "task": {
          "id": 1,
          "task_no": "PD2024010001"
        },
        "action": "adjust_account",
        "action_display": "调整账面",
        "description": "批量调整位置不符的资产",
        "applicant": {
          "id": 3,
          "username": "admin",
          "full_name": "管理员"
        },
        "application_date": "2024-01-21",
        "differences_count": 10,
        "approved_by": {
          "id": 2,
          "username": "manager",
          "full_name": "经理"
        },
        "approved_at": "2024-01-22T10:00:00Z",
        "created_at": "2024-01-21T14:00:00Z"
      }
    ]
  }
}
```

### 2.2 处理单详情

```
GET /api/inventory/resolutions/{id}/
```

**Response:**
```json
{
  "success": true,
  "message": "获取处理单详情成功",
  "data": {
    "id": 1,
    "resolution_no": "RS2024010001",
    "status": "approved",
    "status_display": "已批准",
    "task": {
      "id": 1,
      "task_no": "PD2024010001",
      "task_name": "2024年1月全公司盘点"
    },
    "action": "adjust_account",
    "action_display": "调整账面",
    "description": "批量调整位置不符的资产",
    "applicant": {
      "id": 3,
      "username": "admin",
      "full_name": "管理员",
      "department": "资产管理部"
    },
    "application_date": "2024-01-21",
    "current_approver": null,
    "approved_by": {
      "id": 2,
      "username": "manager",
      "full_name": "经理"
    },
    "approved_at": "2024-01-22T10:00:00Z",
    "approval_note": "同意处理方案",
    "executor": {
      "id": 2,
      "username": "manager",
      "full_name": "经理"
    },
    "executed_at": "2024-01-22T10:05:00Z",
    "execution_note": "已完成调账",
    "differences": [
      {
        "id": 1,
        "difference_type": "location_mismatch",
        "asset": {
          "asset_no": "ZC2024010001",
          "asset_name": "笔记本电脑"
        },
        "account_location": "A栋301",
        "actual_location": "A栋302",
        "status": "resolved"
      }
    ],
    "approval_history": [
      {
        "level": 1,
        "approver": "经理",
        "action": "approved",
        "opinion": "同意",
        "approved_at": "2024-01-22T10:00:00Z"
      }
    ],
    "created_at": "2024-01-21T14:00:00Z"
  }
}
```

### 2.3 创建差异处理

```
POST /api/inventory/resolutions/
```

**Request:**
```json
{
  "task_id": 1,
  "action": "adjust_account",
  "description": "批量调整位置不符的资产",
  "difference_ids": [1, 2, 3, 4, 5]
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "差异处理单创建成功",
  "data": {
    "id": 1,
    "resolution_no": "RS2024010001",
    "status": "draft"
  }
}
```

### 2.4 提交处理审批

```
POST /api/inventory/resolutions/{id}/submit/
```

**Response:**
```json
{
  "success": true,
  "message": "已提交审批",
  "data": {
    "id": 1,
    "status": "submitted",
    "current_approver": {
      "id": 2,
      "username": "manager",
      "full_name": "经理"
    }
  }
}
```

### 2.5 审批处理

```
POST /api/inventory/resolutions/{id}/approve/
```

**Request:**
```json
{
  "approved": true,
  "note": "同意处理方案"
}
```

**Response:**
```json
{
  "success": true,
  "message": "审批通过，已自动执行处理",
  "data": {
    "id": 1,
    "status": "approved"
  }
}
```

---

## 3. 资产调账 API

### 3.1 调账记录列表

```
GET /api/inventory/adjustments/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| asset_id | int | 否 | 资产筛选 |
| adjustment_type | string | 否 | 调账类型 |
| status | string | 否 | 状态筛选 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "count": 100,
  "results": [
    {
      "id": 1,
      "adjustment_no": "ADJ2024010001",
      "status": "completed",
      "status_display": "已完成",
      "adjustment_type": "location",
      "adjustment_type_display": "位置调整",
      "asset": {
        "id": 1,
        "asset_no": "ZC2024010001",
        "asset_name": "笔记本电脑"
      },
      "before_value": {
        "location_id": 1,
        "location_name": "A栋301"
      },
      "after_value": {
        "location_id": 2,
        "location_name": "A栋302"
      },
      "change_description": "盘点差异调整：位置不符",
      "executed_by": {
        "id": 2,
        "username": "manager",
        "full_name": "经理"
      },
      "executed_at": "2024-01-22T10:05:00Z",
      "created_at": "2024-01-22T10:00:00Z"
    }
  ]
}
```

### 3.2 调账详情

```
GET /api/inventory/adjustments/{id}/
```

**Response:**
```json
{
  "id": 1,
  "adjustment_no": "ADJ2024010001",
  "status": "completed",
  "status_display": "已完成",
  "adjustment_type": "location",
  "adjustment_type_display": "位置调整",
  "resolution": {
    "id": 1,
    "resolution_no": "RS2024010001"
  },
  "asset": {
    "id": 1,
    "asset_no": "ZC2024010001",
    "asset_name": "笔记本电脑",
    "category": "电子设备",
    "department": "研发部"
  },
  "before_value": {
    "location_id": 1,
    "location_name": "A栋301",
    "full_path": "总部/A栋/301"
  },
  "after_value": {
    "location_id": 2,
    "location_name": "A栋302",
    "full_path": "总部/A栋/302"
  },
  "change_description": "盘点差异调整：位置不符，账面A栋301，实际A栋302",
  "executed_by": {
    "id": 2,
    "username": "manager",
    "full_name": "经理"
  },
  "executed_at": "2024-01-22T10:05:00Z",
  "rolled_back": false,
  "created_at": "2024-01-22T10:00:00Z"
}
```

### 3.3 回滚调账

```
POST /api/inventory/adjustments/{id}/rollback/
```

**Request:**
```json
{
  "reason": "处理方案有误，需要回滚"
}
```

**Response:**
```json
{
  "success": true,
  "message": "调账已回滚",
  "data": {
    "id": 1,
    "status": "rolled_back"
  }
}
```

---

## 4. 盘点报告 API

### 4.1 报告列表

```
GET /api/inventory/reports/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| task_id | int | 否 | 盘点任务筛选 |
| status | string | 否 | 状态筛选 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "report_no": "RPT2024010001",
      "status": "approved",
      "status_display": "已批准",
      "task": {
        "id": 1,
        "task_no": "PD2024010001",
        "task_name": "2024年1月全公司盘点",
        "start_date": "2024-01-01",
        "end_date": "2024-01-15"
      },
      "summary": {
        "total_assets": 1000,
        "scanned_assets": 950,
        "difference_count": 50,
        "difference_rate": "5.0%"
      },
      "generated_by": {
        "id": 3,
        "username": "admin",
        "full_name": "管理员"
      },
      "generated_at": "2024-01-20T16:00:00Z",
      "current_approver": null,
      "created_at": "2024-01-20T15:00:00Z"
    }
  ]
}
```

### 4.2 报告详情

```
GET /api/inventory/reports/{id}/
```

**Response:**
```json
{
  "id": 1,
  "report_no": "RPT2024010001",
  "status": "approved",
  "status_display": "已批准",
  "task": {
    "id": 1,
    "task_no": "PD2024010001",
    "task_name": "2024年1月全公司盘点",
    "start_date": "2024-01-01",
    "end_date": "2024-01-15",
    "departments": ["研发部", "市场部", "行政部"]
  },
  "template": {
    "id": 1,
    "template_name": "标准盘点报告",
    "template_code": "STD"
  },
  "report_data": {
    "summary": {
      "task_no": "PD2024010001",
      "task_name": "2024年1月全公司盘点",
      "period_start": "2024-01-01",
      "period_end": "2024-01-15",
      "total_assets": 1000,
      "scanned_assets": 950,
      "unscanned_assets": 50,
      "scan_rate": "95.00%",
      "difference_count": 50,
      "difference_rate": "5.0%"
    },
    "differences_by_type": {
      "盘亏": 15,
      "盘盈": 3,
      "位置不符": 25,
      "状态不符": 7
    },
    "differences_by_department": [
      {
        "department": "研发部",
        "total": 500,
        "scanned": 480,
        "differences": 20
      },
      {
        "department": "市场部",
        "total": 300,
        "scanned": 285,
        "differences": 15
      }
    ],
    "differences_detail": [
      {
        "type": "盘亏",
        "asset": "笔记本电脑",
        "asset_no": "ZC2024010001",
        "value": "5000.00",
        "description": "资产未扫描到",
        "status": "已处理"
      }
    ],
    "recommendations": [
      "加强资产日常管理",
      "完善资产转移登记流程",
      "定期进行资产抽查"
    ]
  },
  "generated_by": {
    "id": 3,
    "username": "admin",
    "full_name": "管理员"
  },
  "generated_at": "2024-01-20T16:00:00Z",
  "current_approver": null,
  "approvals": [
    {
      "level": 1,
      "approver": "资产管理员",
      "action": "approved",
      "opinion": "盘点结果确认无误",
      "approved_at": "2024-01-21T10:00:00Z"
    },
    {
      "level": 2,
      "approver": "财务经理",
      "action": "approved",
      "opinion": "财务数据核对无误",
      "approved_at": "2024-01-21T15:00:00Z"
    },
    {
      "level": 3,
      "approver": "总经理",
      "action": "approved",
      "opinion": "同意",
      "approved_at": "2024-01-22T09:00:00Z"
    }
  ],
  "created_at": "2024-01-20T15:00:00Z"
}
```

### 4.3 生成报告

```
POST /api/inventory/reports/generate/
```

**Request:**
```json
{
  "task_id": 1,
  "template_id": 1
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "message": "报告生成成功",
  "data": {
    "id": 1,
    "report_no": "RPT2024010001",
    "status": "draft"
  }
}
```

### 4.4 提交报告审批

```
POST /api/inventory/reports/{id}/submit/
```

**Response:**
```json
{
  "success": true,
  "message": "已提交审批",
  "data": {
    "id": 1,
    "status": "pending_approval",
    "current_approver": {
      "id": 2,
      "username": "manager",
      "full_name": "资产管理员"
    }
  }
}
```

### 4.5 审批报告

```
POST /api/inventory/reports/{id}/approve/
```

**Request:**
```json
{
  "action": "approved",
  "opinion": "盘点结果确认无误"
}
```

**Response:**
```json
{
  "success": true,
  "message": "审批成功",
  "data": {
    "id": 1,
    "status": "pending_approval",
    "approval_level": 1
  }
}
```

### 4.6 导出报告

```
GET /api/inventory/reports/{id}/export/?format=pdf
GET /api/inventory/reports/{id}/export/?format=excel
```

**Response:** PDF或Excel文件

---

## 5. 报告模板 API

### 5.1 模板列表

```
GET /api/inventory/report-templates/
```

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": 1,
      "template_name": "标准盘点报告",
      "template_code": "STD",
      "description": "适用于常规盘点任务的标准报告模板",
      "is_default": true,
      "sections_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "template_name": "简式盘点报告",
      "template_code": "SIMPLE",
      "description": "简化版报告，适用于小型盘点",
      "is_default": false,
      "sections_count": 3,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 5.2 模板详情

```
GET /api/inventory/report-templates/{id}/
```

**Response:**
```json
{
  "id": 1,
  "template_name": "标准盘点报告",
  "template_code": "STD",
  "description": "适用于常规盘点任务的标准报告模板",
  "is_default": true,
  "template_config": {
    "sections": [
      {
        "title": "盘点概况",
        "type": "summary",
        "fields": ["task_name", "period", "total_assets", "scan_rate"]
      },
      {
        "title": "差异明细",
        "type": "table",
        "data_source": "differences",
        "columns": ["asset_no", "asset_name", "type", "description"]
      },
      {
        "title": "部门统计",
        "type": "chart",
        "chart_type": "bar",
        "data_source": "by_department"
      }
    ],
    "styles": {
      "primary_color": "#409EFF",
      "font_size": 14
    }
  },
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 5.3 创建模板

```
POST /api/inventory/report-templates/
```

**Request:**
```json
{
  "template_name": "自定义报告模板",
  "template_code": "CUSTOM",
  "description": "自定义报告模板",
  "template_config": {
    "sections": [...]
  }
}
```

### 5.4 更新模板

```
PUT /api/inventory/report-templates/{id}/
PATCH /api/inventory/report-templates/{id}/
```

### 5.5 删除模板

```
DELETE /api/inventory/report-templates/{id}/
```

### 5.6 设置默认模板

```
POST /api/inventory/report-templates/{id}/set-default/
```

---

## 6. 统计分析 API

### 6.1 差异统计

```
GET /api/inventory/statistics/differences/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | int | 否 | 盘点任务 |
| date_from | date | 是 | 开始日期 |
| date_to | date | 是 | 结束日期 |
| group_by | string | 否 | 分组方式：type/department/responsible_user |

**Response:**
```json
{
  "summary": {
    "total_differences": 50,
    "pending_differences": 10,
    "confirmed_differences": 15,
    "resolved_differences": 20,
    "closed_differences": 5
  },
  "by_type": [
    {
      "type": "loss",
      "type_display": "盘亏",
      "count": 15,
      "total_value": "75000.00"
    },
    {
      "type": "surplus",
      "type_display": "盘盈",
      "count": 3,
      "total_value": "0.00"
    },
    {
      "type": "location_mismatch",
      "type_display": "位置不符",
      "count": 25,
      "total_value": "0.00"
    }
  ],
  "by_department": [
    {
      "department": "研发部",
      "total": 20,
      "pending": 5,
      "resolved": 15
    }
  ],
  "trend": [
    {
      "month": "2024-01",
      "total": 50,
      "resolved": 20
    }
  ]
}
```

### 6.2 处理效率统计

```
GET /api/inventory/statistics/resolution-efficiency/
```

**Response:**
```json
{
  "summary": {
    "total_resolutions": 30,
    "avg_resolution_days": 3.5,
    "pending_resolutions": 5,
    "overdue_resolutions": 2
  },
  "by_action": [
    {
      "action": "adjust_account",
      "action_display": "调整账面",
      "count": 20,
      "avg_days": 2.5
    },
    {
      "action": "write_off",
      "action_display": "资产报损",
      "count": 5,
      "avg_days": 7.0
    }
  ]
}
```

---

## 7. WebSocket 事件

### 7.1 差异生成事件

```json
{
  "event": "difference.generated",
  "data": {
    "task_id": 1,
    "task_no": "PD2024010001",
    "new_differences_count": 10,
    "total_differences": 50
  }
}
```

### 7.2 差异认定事件

```json
{
  "event": "difference.confirmed",
  "data": {
    "difference_id": 1,
    "difference_type": "loss",
    "responsible_user_id": 5
  }
}
```

### 7.3 处理审批事件

```json
{
  "event": "resolution.approved",
  "data": {
    "resolution_id": 1,
    "resolution_no": "RS2024010001",
    "status": "approved",
    "approved_by": "经理"
  }
}
```

### 7.4 报告审批事件

```json
{
  "event": "report.approved",
  "data": {
    "report_id": 1,
    "report_no": "RPT2024010001",
    "status": "approved",
    "approval_level": 3
  }
}
```

---

## 8. 错误码定义

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 差异记录不存在 |
| VALIDATION_ERROR | 400 | 差异状态不允许此操作 |
| VALIDATION_ERROR | 400 | 差异已认定，不能重复认定 |
| NOT_FOUND | 404 | 处理单不存在 |
| VALIDATION_ERROR | 400 | 处理单状态不允许此操作 |
| PERMISSION_DENIED | 403 | 不是当前审批人 |
| NOT_FOUND | 404 | 调账记录不存在 |
| VALIDATION_ERROR | 400 | 调账已执行，不能回滚 |
| NOT_FOUND | 404 | 报告不存在 |
| VALIDATION_ERROR | 400 | 报告状态不允许此操作 |
| NOT_FOUND | 404 | 报告模板不存在 |
| VALIDATION_ERROR | 400 | 默认模板不能删除 |
| SERVER_ERROR | 500 | 差异处理执行失败 |
| SERVER_ERROR | 500 | 资产调账失败 |
