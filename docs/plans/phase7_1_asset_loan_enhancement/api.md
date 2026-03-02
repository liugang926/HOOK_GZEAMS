# Phase 7.1: 资产借用/外借增强 - API接口设计

## 1. API概述

### 1.1 接口规范

所有API遵循GZEAMS统一接口规范：

| 规范项 | 说明 |
|--------|------|
| 基础URL | `/api/loans/` |
| 认证方式 | JWT Token (Header: Authorization: Bearer {token}) |
| 响应格式 | JSON |
| 编码 | UTF-8 |

### 1.2 统一响应格式

**成功响应**：
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

**列表响应（分页）**：
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/loans/?page=2",
        "previous": null,
        "results": [...]
    }
}
```

**错误响应**：
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "deposit_amount": ["押金金额必须大于0"]
        }
    }
}
```

---

## 2. 资产借用接口（扩展）

### 2.1 借用单列表

**请求**：
```http
GET /api/loans/asset-loans/
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| borrower_type | string | 否 | 筛选借用类型: internal/external |
| status | string | 否 | 状态筛选 |
| is_overdue | boolean | 否 | 是否超期: true/false |
| borrower | uuid | 否 | 借用人ID（内部） |
| borrow_date_from | date | 否 | 借用日期起 |
| borrow_date_to | date | 否 | 借用日期止 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**响应示例**：
```json
{
    "success": true,
    "data": {
        "count": 45,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": "uuid-1",
                "loan_no": "LN2025010001",
                "borrower_type": "external",
                "borrower": null,
                "borrower_external_id": "EXT202501001",
                "borrower_name": "张三",
                "borrower_phone": "13800138000",
                "borrower_company": null,
                "borrow_date": "2025-01-01",
                "expected_return_date": "2025-01-15",
                "actual_return_date": null,
                "status": "borrowed",
                "enable_deposit": true,
                "enable_overdue_fee": true,
                "deposit_status": {
                    "amount": "5000.00",
                    "date": "2025-01-01",
                    "status": "collected"
                },
                "overdue_fee_total": "250.00",
                "is_overdue": true,
                "overdue_days": 5,
                "items": [
                    {
                        "id": "uuid-item-1",
                        "asset": {
                            "id": "asset-uuid",
                            "asset_code": "ZC001",
                            "asset_name": "MacBook Pro",
                            "category_name": "电子设备"
                        },
                        "quantity": 1,
                        "remark": ""
                    }
                ],
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z",
                "created_by": "user-uuid"
            }
        ]
    }
}
```

### 2.2 创建内部借用

**请求**：
```http
POST /api/loans/asset-loans/
Content-Type: application/json
```

**请求体**：
```json
{
    "borrower_type": "internal",
    "borrower": "user-uuid",
    "borrow_date": "2025-01-01",
    "expected_return_date": "2025-01-15",
    "loan_reason": "项目需要临时使用",
    "items": [
        {
            "asset": "asset-uuid-1",
            "quantity": 1,
            "remark": ""
        }
    ],
    "enable_deposit": false,
    "enable_overdue_fee": false
}
```

**响应**：
```json
{
    "success": true,
    "message": "借用单创建成功",
    "data": {
        "id": "new-uuid",
        "loan_no": "LN2025010002",
        "status": "pending",
        ...
    }
}
```

### 2.3 创建对外借用

**请求**：
```http
POST /api/loans/asset-loans/external/
Content-Type: application/json
```

**请求体**：
```json
{
    "borrower_external_id": "EXT202501001",
    "borrow_date": "2025-01-01",
    "expected_return_date": "2025-01-15",
    "loan_reason": "合作单位展示使用",
    "items": [
        {
            "asset": "asset-uuid-1",
            "quantity": 1,
            "remark": ""
        }
    ],
    "enable_deposit": true,
    "enable_overdue_fee": true,
    "deposit_amount": "5000.00"
}
```

**响应**：
```json
{
    "success": true,
    "message": "对外借用单创建成功",
    "data": {
        "id": "new-uuid",
        "loan_no": "LN2025010003",
        "borrower_type": "external",
        "borrower_name": "张三",
        "borrower_phone": "13800138000",
        "borrower_company": "某某科技有限公司",
        "status": "pending",
        ...
    }
}
```

### 2.4 获取借用单详情

**请求**：
```http
GET /api/loans/asset-loans/{id}/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "uuid-1",
        "loan_no": "LN2025010001",
        "borrower_type": "external",
        "borrower_name": "张三",
        "borrower_external_detail": {
            "id": "EXT202501001",
            "name": "张三",
            "type": "个人",
            "phone": "13800138000",
            "company": null,
            "id_card": "110***********1234"
        },
        "borrow_date": "2025-01-01",
        "expected_return_date": "2025-01-15",
        "actual_return_date": null,
        "loan_reason": "合作单位展示使用",
        "status": "borrowed",
        "approved_by": null,
        "approved_at": null,
        "lent_by": {
            "id": "admin-uuid",
            "username": "admin",
            "full_name": "管理员"
        },
        "lent_at": "2025-01-01T14:30:00Z",
        "returned_by": null,
        "returned_at": null,
        "asset_condition": null,
        "enable_deposit": true,
        "enable_overdue_fee": true,
        "deposit_status": {
            "amount": "5000.00",
            "date": "2025-01-01",
            "status": "collected",
            "payment_method": "transfer"
        },
        "overdue_fee_total": "250.00",
        "is_overdue": true,
        "overdue_days": 5,
        "items": [...],
        "organization": "org-uuid",
        "created_at": "2025-01-01T10:00:00Z",
        "updated_at": "2025-01-06T09:00:00Z",
        "created_by": "user-uuid"
    }
}
```

### 2.5 确认借出

**请求**：
```http
POST /api/loans/asset-loans/{id}/lend/
Content-Type: application/json
```

**请求体**：
```json
{
    "confirm": true
}
```

**响应**：
```json
{
    "success": true,
    "message": "资产已借出",
    "data": {
        "id": "uuid-1",
        "status": "borrowed",
        "lent_by": "admin-uuid",
        "lent_at": "2025-01-01T14:30:00Z"
    }
}
```

### 2.6 确认归还

**请求**：
```http
POST /api/loans/asset-loans/{id}/return/
Content-Type: application/json
```

**请求体**：
```json
{
    "asset_condition": "good",
    "return_remark": "资产完好，正常归还"
}
```

**资产状况选项**：

| 值 | 说明 |
|----|------|
| good | 完好 |
| minor_damage | 轻微损坏 |
| major_damage | 严重损坏 |
| lost | 遗失 |

**响应**：
```json
{
    "success": true,
    "message": "资产归还确认成功",
    "data": {
        "id": "uuid-1",
        "status": "returned",
        "actual_return_date": "2025-01-16",
        "returned_by": "admin-uuid",
        "returned_at": "2025-01-16T10:00:00Z",
        "asset_condition": "good",
        "credit_updated": true,
        "credit_score_change": 2
    }
}
```

### 2.7 收取押金

**请求**：
```http
POST /api/loans/asset-loans/{id}/collect-deposit/
Content-Type: application/json
```

**请求体**：
```json
{
    "deposit_amount": "5000.00",
    "payment_method": "transfer",
    "payment_account": "6222 0000 0000 0000",
    "deposit_date": "2025-01-01",
    "voucher": "(file)"
}
```

**支付方式选项**：

| 值 | 说明 |
|----|------|
| cash | 现金 |
| transfer | 转账 |
| check | 支票 |
| other | 其他 |

**响应**：
```json
{
    "success": true,
    "message": "押金收取成功",
    "data": {
        "id": "deposit-uuid",
        "deposit_no": "YJ2025010001",
        "deposit_amount": "5000.00",
        "deposit_date": "2025-01-01",
        "payment_method": "transfer",
        "payment_account": "6222 0000 0000 0000",
        "deposit_status": "collected"
    }
}
```

### 2.8 退还押金

**请求**：
```http
POST /api/loans/asset-loans/{id}/refund-deposit/
Content-Type: application/json
```

**请求体**：
```json
{
    "amount": "4750.00",
    "reason": "正常归还，扣除超期费用250元",
    "voucher": "(file)"
}
```

**响应**：
```json
{
    "success": true,
    "message": "押金退还成功",
    "data": {
        "id": "deposit-uuid",
        "deposit_status": "refunded",
        "refunded_amount": "4750.00",
        "refunded_date": "2025-01-16",
        "refund_reason": "正常归还，扣除超期费用250元",
        "refunded_voucher": "/media/deposit_vouchers/xxx.pdf",
        "refunded_by": {
            "id": "admin-uuid",
            "username": "admin",
            "full_name": "管理员"
        }
    }
}
```

### 2.9 计算超期费用

**请求**：
```http
POST /api/loans/asset-loans/{id}/calculate-overdue-fee/
```

**响应**：
```json
{
    "success": true,
    "message": "费用计算完成",
    "data": {
        "overdue_days": 5,
        "total_fee": "250.00",
        "fee_details": [
            {
                "id": "fee-uuid",
                "calculation_date": "2025-01-16",
                "overdue_days": 5,
                "unit_price": "50.0000",
                "calculated_fee": "250.00",
                "waived_fee": "0.00",
                "actual_fee": "250.00",
                "fee_status": "pending"
            }
        ]
    }
}
```

### 2.10 获取借用人信用

**请求**：
```http
GET /api/loans/asset-loans/{id}/borrower-credit/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "credit-uuid",
        "borrower_type": "external",
        "borrower_external_id": "EXT202501001",
        "borrower_name": "张三",
        "borrower_info": {
            "type": "external",
            "external_id": "EXT202501001",
            "name": "张三",
            "person_type": "个人",
            "phone": "138***8000",
            "company": null
        },
        "credit_score": 95,
        "credit_level": "excellent",
        "credit_level_display": "优秀",
        "total_loan_count": 5,
        "normal_return_count": 4,
        "overdue_count": 1,
        "damage_count": 0,
        "lost_count": 0,
        "last_overdue_days": 3,
        "total_overdue_days": 3,
        "last_updated_at": "2025-01-16T10:00:00Z"
    }
}
```

### 2.11 手动更新信用分

**请求**：
```http
POST /api/loans/asset-loans/{id}/update-credit/
Content-Type: application/json
```

**请求体**：
```json
{
    "score_change": -5,
    "reason": "归还时发现轻微划痕"
}
```

**响应**：
```json
{
    "success": true,
    "message": "信用分更新成功",
    "data": {
        "id": "credit-uuid",
        "credit_score": 90,
        "credit_level": "good",
        "score_change": -5
    }
}
```

---

## 3. 押金管理接口

### 3.1 押金记录列表

**请求**：
```http
GET /api/loans/deposits/
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| loan | uuid | 否 | 借用单ID |
| deposit_status | string | 否 | 状态: collected/refunded/cancelled |
| deposit_date_from | date | 否 | 收取日期起 |
| deposit_date_to | date | 否 | 收取日期止 |

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 30,
        "results": [
            {
                "id": "deposit-uuid",
                "loan": "loan-uuid",
                "loan_no": "LN2025010001",
                "borrower_name": "张三",
                "deposit_no": "YJ2025010001",
                "deposit_amount": "5000.00",
                "deposit_date": "2025-01-01",
                "payment_method": "transfer",
                "payment_account": "6222 0000 0000 0000",
                "deposit_status": "collected",
                "refunded_date": null,
                "refunded_amount": null,
                "refund_reason": null,
                "refund_voucher": null,
                "refunded_by": null,
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z"
            }
        ]
    }
}
```

### 3.2 押金汇总

**请求**：
```http
GET /api/loans/deposits/summary/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "collected": {
            "total": "150000.00",
            "count": 30
        },
        "refunded": {
            "total": "120000.00",
            "count": 25
        },
        "pending_refund": {
            "total": "5000.00",
            "count": 2
        }
    }
}
```

### 3.3 押金详情

**请求**：
```http
GET /api/loans/deposits/{id}/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "deposit-uuid",
        "loan": {
            "id": "loan-uuid",
            "loan_no": "LN2025010001"
        },
        "borrower_name": "张三",
        "deposit_no": "YJ2025010001",
        "deposit_amount": "5000.00",
        "deposit_date": "2025-01-01",
        "payment_method": "transfer",
        "payment_account": "6222 0000 0000 0000",
        "deposit_status": "refunded",
        "refunded_date": "2025-01-16",
        "refunded_amount": "4750.00",
        "refund_reason": "正常归还，扣除超期费用250元",
        "refund_voucher": "/media/deposit_vouchers/xxx.pdf",
        "refunded_by": {
            "id": "admin-uuid",
            "username": "admin",
            "full_name": "管理员"
        },
        "organization": "org-uuid",
        "created_at": "2025-01-01T10:00:00Z"
    }
}
```

---

## 4. 计费规则接口

### 4.1 计费规则列表

**请求**：
```http
GET /api/loans/fee-rules/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 3,
        "results": [
            {
                "id": "rule-uuid",
                "name": "内部借用免费",
                "code": "INTERNAL_FREE",
                "rule_type": "daily",
                "is_active": true,
                "daily_rate": "0.0000",
                "apply_to_internal": true,
                "apply_to_external": false,
                "min_overdue_days": 1,
                "max_fee": null,
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z"
            },
            {
                "id": "rule-uuid-2",
                "name": "对外借用每日50元",
                "code": "EXTERNAL_DAILY_50",
                "rule_type": "daily",
                "is_active": true,
                "daily_rate": "50.0000",
                "apply_to_internal": false,
                "apply_to_external": true,
                "min_overdue_days": 1,
                "max_fee": null,
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z"
            },
            {
                "id": "rule-uuid-3",
                "name": "阶梯计费",
                "code": "TIERED_FEE",
                "rule_type": "tiered",
                "is_active": true,
                "daily_rate": null,
                "tier_config": {
                    "tiers": [
                        {"days_start": 1, "days_end": 7, "daily_rate": "10.00"},
                        {"days_start": 8, "days_end": 30, "daily_rate": "20.00"},
                        {"days_start": 31, "days_end": null, "daily_rate": "50.00"}
                    ]
                },
                "apply_to_internal": false,
                "apply_to_external": true,
                "min_overdue_days": 1,
                "max_fee": "5000.00",
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z"
            }
        ]
    }
}
```

### 4.2 创建计费规则

**请求**：
```http
POST /api/loans/fee-rules/
Content-Type: application/json
```

**请求体（按日计费）**：
```json
{
    "name": "每日50元",
    "code": "DAILY_50",
    "rule_type": "daily",
    "daily_rate": "50.00",
    "apply_to_external": true,
    "apply_to_internal": false,
    "min_overdue_days": 1
}
```

**请求体（阶梯计费）**：
```json
{
    "name": "阶梯计费",
    "code": "TIERED",
    "rule_type": "tiered",
    "tier_config": {
        "tiers": [
            {"days_start": 1, "days_end": 7, "daily_rate": "10.00"},
            {"days_start": 8, "days_end": 30, "daily_rate": "20.00"},
            {"days_start": 31, "days_end": null, "daily_rate": "50.00"}
        ]
    },
    "apply_to_external": true,
    "apply_to_internal": false,
    "max_fee": "5000.00"
}
```

**响应**：
```json
{
    "success": true,
    "message": "计费规则创建成功",
    "data": {
        "id": "new-rule-uuid",
        "name": "每日50元",
        "code": "DAILY_50",
        "rule_type": "daily",
        ...
    }
}
```

---

## 5. 信用管理接口

### 5.1 信用记录列表

**请求**：
```http
GET /api/loans/credits/
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| borrower_type | string | 否 | 筛选类型: internal/external |
| credit_level | string | 否 | 筛选等级: excellent/good/normal/poor/blacklisted |
| min_credit_score | int | 否 | 最低分数 |
| search | string | 否 | 搜索借用人姓名 |

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 50,
        "results": [
            {
                "id": "credit-uuid",
                "borrower_type": "external",
                "borrower_user": null,
                "borrower_external_id": "EXT202501001",
                "borrower_name": "张三",
                "borrower_info": {
                    "type": "external",
                    "external_id": "EXT202501001",
                    "name": "张三",
                    "person_type": "个人",
                    "phone": "138***8000",
                    "company": null
                },
                "credit_score": 95,
                "credit_level": "excellent",
                "credit_level_display": "优秀",
                "total_loan_count": 5,
                "normal_return_count": 4,
                "overdue_count": 1,
                "damage_count": 0,
                "lost_count": 0,
                "last_overdue_days": 3,
                "total_overdue_days": 3,
                "last_updated_at": "2025-01-16T10:00:00Z",
                "organization": "org-uuid",
                "created_at": "2024-01-01T10:00:00Z"
            }
        ]
    }
}
```

### 5.2 获取我的信用

**请求**：
```http
GET /api/loans/credits/my-credit/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "credit-uuid",
        "borrower_type": "internal",
        "borrower_user": "my-user-uuid",
        "borrower_name": "李四",
        "borrower_info": {
            "type": "internal",
            "user_id": "my-user-uuid",
            "username": "lisi",
            "full_name": "李四",
            "email": "lisi@example.com",
            "department": "技术部"
        },
        "credit_score": 85,
        "credit_level": "good",
        "credit_level_display": "良好",
        "total_loan_count": 10,
        "normal_return_count": 9,
        "overdue_count": 1,
        "damage_count": 0,
        "lost_count": 0,
        "last_overdue_days": 2,
        "total_overdue_days": 2,
        "last_updated_at": "2025-01-16T10:00:00Z"
    }
}
```

### 5.3 信用记录详情

**请求**：
```http
GET /api/loans/credits/{id}/
```

**响应**：
```json
{
    "success": true,
    "data": {
        "id": "credit-uuid",
        "borrower_type": "external",
        "borrower_external_id": "EXT202501001",
        "borrower_name": "张三",
        "borrower_info": {...},
        "credit_score": 95,
        "credit_level": "excellent",
        "credit_level_display": "优秀",
        "total_loan_count": 5,
        "normal_return_count": 4,
        "overdue_count": 1,
        "damage_count": 0,
        "lost_count": 0,
        "last_overdue_days": 3,
        "total_overdue_days": 3,
        "last_updated_at": "2025-01-16T10:00:00Z",
        "organization": "org-uuid",
        "created_at": "2024-01-01T10:00:00Z"
    }
}
```

### 5.4 信用历史记录

**请求**：
```http
GET /api/loans/credits/{id}/history/
```

**查询参数**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| event_type | string | 否 | 事件类型筛选 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 10,
        "results": [
            {
                "id": "history-uuid",
                "credit": "credit-uuid",
                "loan": "loan-uuid",
                "loan_no": "LN2025010001",
                "related_asset": "asset-uuid",
                "asset_name": "MacBook Pro",
                "event_type": "returned_normal",
                "event_type_display": "正常归还",
                "event_date": "2025-01-16",
                "score_change": 2,
                "score_after": 95,
                "event_description": "分数从 93 变更为 95",
                "organization": "org-uuid",
                "created_at": "2025-01-16T10:00:00Z"
            },
            {
                "id": "history-uuid-2",
                "credit": "credit-uuid",
                "loan": "loan-uuid-2",
                "loan_no": "LN2024050001",
                "related_asset": "asset-uuid-2",
                "asset_name": "iPad Pro",
                "event_type": "returned_overdue_short",
                "event_type_display": "超期短期归还",
                "event_date": "2024-05-20",
                "score_change": 0,
                "score_after": 93,
                "event_description": "超期3天归还",
                "organization": "org-uuid",
                "created_at": "2024-05-20T10:00:00Z"
            }
        ]
    }
}
```

### 5.5 检查借用资格

**请求**：
```http
POST /api/loans/credits/check-eligibility/
Content-Type: application/json
```

**请求体**：
```json
{
    "borrower_type": "external",
    "borrower_external_id": "EXT202501001"
}
```

**或内部用户**：
```json
{
    "borrower_type": "internal",
    "borrower_user_id": "user-uuid"
}
```

**响应**：
```json
{
    "success": true,
    "data": {
        "eligible": true,
        "credit_score": 95,
        "credit_level": "excellent"
    }
}
```

**不符合资格响应**：
```json
{
    "success": true,
    "data": {
        "eligible": false,
        "reason": "信用等级过低（黑名单）",
        "credit_score": 20
    }
}
```

---

## 6. 外部人员接口（通过低代码引擎）

### 6.1 外部人员列表

**请求**：
```http
GET /api/system/dynamic-data/?business_object=ExternalPerson
```

**响应**：
```json
{
    "success": true,
    "data": {
        "count": 20,
        "results": [
            {
                "id": "dynamic-uuid",
                "data_no": "EXT202501001",
                "status": "active",
                "dynamic_fields": {
                    "person_name": "张三",
                    "person_type": "个人",
                    "phone": "13800138000",
                    "id_card": "110101199001011234",
                    "company_name": null,
                    "bank_account": "6222 0000 0000 0000",
                    "bank_name": "工商银行",
                    "address": "北京市朝阳区xxx",
                    "notes": ""
                },
                "organization": "org-uuid",
                "created_at": "2025-01-01T10:00:00Z",
                "created_by": "user-uuid"
            }
        ]
    }
}
```

### 6.2 创建外部人员

**请求**：
```http
POST /api/system/dynamic-data/
Content-Type: application/json
```

**请求体**：
```json
{
    "business_object_code": "ExternalPerson",
    "data_no": "EXT202501002",
    "dynamic_fields": {
        "person_name": "李四",
        "person_type": "单位",
        "phone": "13900139000",
        "id_card": "91110000123456789X",
        "company_name": "某某科技有限公司",
        "credit_code": "91110000123456789X",
        "bank_account": "6222 0000 0000 0001",
        "bank_name": "建设银行",
        "contact_person": "王五",
        "contact_phone": "13700137000",
        "notes": "合作单位"
    }
}
```

**响应**：
```json
{
    "success": true,
    "message": "外部人员创建成功",
    "data": {
        "id": "new-dynamic-uuid",
        "data_no": "EXT202501002",
        "dynamic_fields": {...}
    }
}
```

---

## 7. 批量操作接口

### 7.1 批量退还押金

**请求**：
```http
POST /api/loans/deposits/batch-refund/
Content-Type: application/json
```

**请求体**：
```json
{
    "ids": ["deposit-uuid-1", "deposit-uuid-2", "deposit-uuid-3"],
    "refund_reason": "批量退还",
    "operator_note": ""
}
```

**响应**：
```json
{
    "success": true,
    "message": "批量退还完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "deposit-uuid-1", "success": true},
        {"id": "deposit-uuid-2", "success": true},
        {"id": "deposit-uuid-3", "success": true}
    ]
}
```

### 7.2 批量计算超期费用

**请求**：
```http
POST /api/loans/asset-loans/batch-calculate-fee/
Content-Type: application/json
```

**请求体**：
```json
{
    "ids": ["loan-uuid-1", "loan-uuid-2"],
    "calculation_date": "2025-01-16"
}
```

**响应**：
```json
{
    "success": true,
    "message": "批量计算完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0,
        "total_fee": "500.00"
    },
    "results": [
        {
            "id": "loan-uuid-1",
            "success": true,
            "overdue_days": 5,
            "calculated_fee": "250.00"
        },
        {
            "id": "loan-uuid-2",
            "success": true,
            "overdue_days": 3,
            "calculated_fee": "150.00"
        }
    ]
}
```

---

## 8. 错误码

### 8.1 业务错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| `DEPOSIT_ALREADY_COLLECTED` | 400 | 该借用单已收取押金 |
| `DEPOSIT_NOT_FOUND` | 404 | 未找到有效的押金记录 |
| `DEPOSIT_ALREADY_REFUNDED` | 400 | 该押金已退还 |
| `REFUND_AMOUNT_EXCEEDS` | 400 | 退款金额超过可退金额 |
| `CREDIT_BLACKLISTED` | 403 | 借用人信用等级过低（黑名单） |
| `CREDIT_ASSET_LOST` | 403 | 存在资产遗失记录 |
| `CREDIT_OVERDUE_EXCESS` | 403 | 超期次数过多 |
| `OVERDUE_FEE_NOT_ENABLED` | 400 | 该借用单未启用超期计费 |
| `EXTERNAL_PERSON_NOT_FOUND` | 404 | 外部人员不存在 |
| `LOAN_NOT_APPROVED` | 400 | 借用单未批准，无法操作 |
| `LOAN_ALREADY_RETURNED` | 400 | 借用单已归还 |
| `ASSET_CONDITION_REQUIRED` | 400 | 归还时必须填写资产状况 |

### 8.2 错误响应示例

```json
{
    "success": false,
    "error": {
        "code": "CREDIT_BLACKLISTED",
        "message": "该借用人信用等级过低，无法创建借用单",
        "details": {
            "credit_score": 20,
            "credit_level": "blacklisted",
            "reason": "存在资产遗失记录"
        }
    }
}
```
