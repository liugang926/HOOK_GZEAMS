# Phase 5.2: 财务凭证集成 - API接口定义

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

| 方法 | 路径 | 说明 |
|------|------|------|
| 凭证模板 | | |
| GET | `/api/finance/voucher-templates/` | 获取凭证模板列表 |
| POST | `/api/finance/voucher-templates/` | 创建凭证模板 |
| GET | `/api/finance/voucher-templates/{id}/` | 获取模板详情 |
| PUT | `/api/finance/voucher-templates/{id}/` | 更新凭证模板 |
| DELETE | `/api/finance/voucher-templates/{id}/` | 删除凭证模板 |
| 财务凭证 | | |
| GET | `/api/finance/vouchers/` | 获取财务凭证列表 |
| POST | `/api/finance/vouchers/` | 创建财务凭证 |
| GET | `/api/finance/vouchers/{id}/` | 获取凭证详情 |
| PUT | `/api/finance/vouchers/{id}/` | 更新财务凭证 |
| DELETE | `/api/finance/vouchers/{id}/` | 删除财务凭证 |
| POST | `/api/finance/vouchers/{id}/submit/` | 提交凭证 |
| POST | `/api/finance/vouchers/{id}/approve/` | 审核凭证 |
| POST | `/api/finance/vouchers/{id}/reject/` | 驳回凭证 |
| POST | `/api/finance/vouchers/{id}/push/` | 推送凭证到ERP |
| 业务凭证 | | |
| POST | `/api/finance/vouchers/generate/asset-purchase/` | 生成资产购入凭证 |
| POST | `/api/finance/vouchers/generate/depreciation/` | 生成折旧凭证 |
| POST | `/api/finance/vouchers/generate/disposal/` | 生成处置凭证 |

---

## 1. 凭证模板

### GET /api/finance/voucher-templates/

获取凭证模板列表

**请求参数：**

```json
{
  "business_type": "asset_purchase",  // 业务类型（可选）
  "is_active": true,                   // 是否启用（可选）
  "page": 1,
  "size": 20
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "count": 5,
        "results": [
    {
      "id": "uuid",
      "business_type": "asset_purchase",
      "business_type_display": "资产购入",
      "template_name": "资产购入默认模板",
      "voucher_type": "记",
      "default_description": "购入固定资产",
      "entries_config": [
        {
          "line_no": 1,
          "account_code": "1601",
          "account_name": "固定资产",
          "direction": "debit",
          "amount": "${asset.purchase_price}"
        },
        {
          "line_no": 2,
          "account_code": "1002",
          "account_name": "银行存款",
          "direction": "credit",
          "amount": "${asset.purchase_price}"
        }
      ],
      "is_active": true,
        "created_at": "2024-01-01T00:00:00Z"
        }
    ]
    }
}
```

### POST /api/finance/voucher-templates/

创建凭证模板

**请求体：**

```json
{
  "business_type": "asset_purchase",
  "template_name": "自定义资产购入模板",
  "voucher_type": "记",
  "default_description": "购入固定资产",
  "entries_config": [
    {
      "line_no": 1,
      "account_code": "1601",
      "account_name": "固定资产",
      "direction": "debit",
      "amount": "${asset.purchase_price}"
    }
  ],
  "is_active": true
}
```

---

## 2. 财务凭证

### GET /api/finance/vouchers/

获取财务凭证列表

**请求参数：**

```json
{
  "business_type": "asset_depreciation",  // 业务类型（可选）
  "status": "draft",                      // 状态（可选）
  "voucher_date_from": "2024-01-01",      // 起始日期（可选）
  "voucher_date_to": "2024-01-31",        // 结束日期（可选）
  "page": 1,
  "size": 20
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "count": 50,
        "results": [
    {
      "id": "uuid",
      "business_type": "asset_depreciation",
      "business_type_display": "资产折旧",
      "business_id": "depreciation-id",
      "voucher_no": "PZ2024010001",
      "voucher_date": "2024-01-31",
      "voucher_type": "记",
      "description": "2024-01 折旧: 笔记本电脑",
      "entries": [
        {
          "line_no": 1,
          "account_code": "6602",
          "account_name": "管理费用-折旧费",
          "debit": "158.33",
          "credit": "0.00",
          "description": ""
        },
        {
          "line_no": 2,
          "account_code": "1602",
          "account_name": "累计折旧",
          "debit": "0.00",
          "credit": "158.33",
          "description": ""
        }
      ],
      "total_debit": "158.33",
      "total_credit": "158.33",
      "status": "draft",
      "status_display": "草稿",
      "integration_system": "m18",
      "external_voucher_no": "",
      "pushed_at": null,
        "created_at": "2024-01-15T10:00:00Z"
        }
    ]
    }
}
```

### POST /api/finance/vouchers/

手动创建财务凭证

**请求体：**

```json
{
  "business_type": "asset_purchase",
  "business_id": "asset-123",
  "voucher_date": "2024-01-15",
  "voucher_type": "记",
  "description": "购入固定资产",
  "entries": [
    {
      "line_no": 1,
      "account_code": "1601",
      "account_name": "固定资产",
      "debit": 8000,
      "credit": 0
    },
    {
      "line_no": 2,
      "account_code": "1002",
      "account_name": "银行存款",
      "debit": 0,
      "credit": 8000
    }
  ]
}
```

### POST /api/finance/vouchers/{id}/submit/

提交凭证

**请求体：** 无

**响应数据：**

```json
{
    "success": true,
    "message": "凭证提交成功",
    "data": {
        "id": "uuid",
        "status": "submitted",
        "status_display": "已提交"
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "无权限提交此凭证"
    }
}
```

### POST /api/finance/vouchers/{id}/approve/

审核凭证

**请求体：**

```json
{
  "approved": true,
  "comment": "审核通过"
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "凭证审核成功",
    "data": {
        "id": "uuid",
        "status": "approved",
        "approved_at": "2024-01-15T14:00:00Z",
        "approved_by": {
            "id": "uuid",
            "username": "admin",
            "full_name": "管理员"
        }
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "凭证状态不允许审核"
    }
}
```

### POST /api/finance/vouchers/{id}/reject/

驳回凭证

**请求体：**

```json
{
  "comment": "科目选择有误，请修改"
}
```

### POST /api/finance/vouchers/{id}/push/

推送凭证到ERP

**请求体：**

```json
{
  "system_type": "m18"  // 目标系统（可选，默认使用配置的系统）
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "凭证推送成功",
    "data": {
        "voucher_no": "PZ2024010001",
        "external_voucher_no": "M18-PZ-2024010001",
        "pushed_at": "2024-01-15T15:00:00Z"
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "CONFLICT",
        "message": "凭证推送失败",
        "details": {
            "error": "ERP系统连接失败"
        }
    }
}
```

---

## 3. 业务凭证生成

### POST /api/finance/vouchers/generate/asset-purchase/

生成资产购入凭证

**请求体：**

```json
{
  "asset_id": "asset-uuid",
  "voucher_date": "2024-01-15",
  "template_id": "template-uuid"  // 可选，指定模板
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "凭证生成成功",
    "data": {
        "id": "voucher-uuid",
        "voucher_no": "PZ2024010001",
        "business_type": "asset_purchase",
        "entries": [...],
        "total_debit": "8000.00",
        "total_credit": "8000.00",
        "status": "draft"
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "资产不存在",
        "details": {
            "asset_id": "asset-uuid"
        }
    }
}
```

### POST /api/finance/vouchers/generate/depreciation/

生成折旧凭证

**请求体：**

```json
{
  "depreciation_id": "depreciation-uuid",
  "template_id": "template-uuid"  // 可选
}
```

**响应数据：** 同上

### POST /api/finance/vouchers/generate/disposal/

生成处置凭证

**请求体：**

```json
{
  "operation_id": "operation-uuid",
  "voucher_date": "2024-01-15",
  "template_id": "template-uuid"  // 可选
}
```

---

## Serializers

```python
# apps/assets/serializers/finance_serializers.py

from rest_framework import serializers
from apps.assets.models.finance import VoucherTemplate, FinanceVoucher


class VoucherEntrySerializer(serializers.Serializer):
    """凭证分录序列化器"""
    line_no = serializers.IntegerField()
    account_code = serializers.CharField(max_length=20)
    account_name = serializers.CharField(max_length=100)
    debit = serializers.DecimalField(max_digits=14, decimal_places=2)
    credit = serializers.DecimalField(max_digits=14, decimal_places=2)
    description = serializers.CharField(required=False, allow_blank=True)


class VoucherTemplateSerializer(serializers.ModelSerializer):
    """凭证模板序列化器"""
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)

    class Meta:
        model = VoucherTemplate
        fields = '__all__'


class FinanceVoucherSerializer(serializers.ModelSerializer):
    """财务凭证序列化器"""
    business_type_display = serializers.CharField(source='get_business_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    entries = VoucherEntrySerializer(many=True)

    class Meta:
        model = FinanceVoucher
        fields = '__all__'


class FinanceVoucherCreateSerializer(serializers.ModelSerializer):
    """财务凭证创建序列化器"""
    entries = VoucherEntrySerializer(many=True)

    class Meta:
        model = FinanceVoucher
        fields = [
            'business_type', 'business_id', 'voucher_date',
            'voucher_type', 'description', 'entries'
        ]

    def validate(self, data):
        entries = data.get('entries', [])
        total_debit = sum(e.get('debit', 0) for e in entries)
        total_credit = sum(e.get('credit', 0) for e in entries)

        if total_debit != total_credit:
            raise serializers.ValidationError(
                f"借贷不平衡: 借方={total_debit}, 贷方={total_credit}"
            )

        return data


class VoucherApproveSerializer(serializers.Serializer):
    """凭证审核序列化器"""
    approved = serializers.BooleanField()
    comment = serializers.CharField(required=False, allow_blank=True)
```

---

## 后续任务

1. 实现其他ERP系统的财务适配器
2. 扩展更多业务类型的凭证模板
