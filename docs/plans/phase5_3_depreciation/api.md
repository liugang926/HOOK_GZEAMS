# Phase 5.3: 折旧自动计算 - API接口定义

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
| GET | `/api/assets/depreciation/` | 获取折旧记录列表 |
| GET | `/api/assets/depreciation/{id}/` | 获取折旧记录详情 |
| GET | `/api/assets/depreciation/by-asset/{asset_id}/` | 获取资产折旧明细 |
| POST | `/api/assets/depreciation/calculate/` | 触发折旧计算 |
| POST | `/api/assets/depreciation/{id}/post/` | 折旧记录过账 |
| POST | `/api/assets/depreciation/{id}/approve/` | 审核折旧记录 |
| GET | `/api/assets/depreciation/report/` | 获取折旧报表 |
| GET | `/api/assets/depreciation/export/` | 导出折旧记录 |
| GET | `/api/assets/{id}/depreciation-summary/` | 获取资产折旧汇总 |

---

## 1. 折旧记录列表

### GET /api/assets/depreciation/

**请求参数：**

```json
{
  "asset_code": "ZC001",           // 资产编码（可选）
  "period": "2024-01",             // 折旧期间（可选）
  "status": "approved",            // 状态（可选）
  "depreciation_method": "straight_line",  // 折旧方法（可选）
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
        "count": 150,
        "next": null,
        "previous": null,
        "results": [
    {
      "id": "uuid",
      "asset": {
        "id": "uuid",
        "asset_code": "ZC001",
        "asset_name": "笔记本电脑",
        "category_name": "电子设备"
      },
      "period": "2024-01",
      "depreciation_method": "straight_line",
      "purchase_price": "8000.00",
      "residual_value": "400.00",
      "useful_life": 48,
      "used_months": 12,
      "depreciation_amount": "158.33",
      "accumulated_depreciation": "1900.00",
      "net_value": "6100.00",
      "status": "approved",
      "voucher_no": "PZ202401001",
        "created_at": "2024-01-31T10:00:00Z"
        }
    ]
    }
}
```

---

## 2. 资产折旧明细

### GET /api/assets/depreciation/by-asset/{asset_id}/

**响应数据：**

```json
{
  "asset_info": {
    "id": "uuid",
    "asset_code": "ZC001",
    "asset_name": "笔记本电脑",
    "category_name": "电子设备",
    "purchase_price": "8000.00",
    "residual_rate": 5.0,
    "residual_value": "400.00",
    "useful_life": 48,
    "depreciation_method": "straight_line",
    "purchase_date": "2023-01-15"
  },
  "stat": {
    "used_months": 12,
    "accumulated": "1900.00",
    "net_value": "6100.00",
    "progress": 23.75
  },
  "records": [
    {
      "id": "uuid",
      "period": "2023-02",
      "used_months": 1,
      "depreciation_amount": "158.33",
      "accumulated_depreciation": "158.33",
      "net_value": "7841.67",
      "status": "posted",
      "voucher_no": "PZ202302001"
    }
  ]
}
```

---

## 3. 触发折旧计算

### POST /api/assets/depreciation/calculate/

**请求参数：**

```json
{
  "period": "2024-01",           // 计算期间（可选，默认当前月）
  "asset_ids": [],               // 指定资产ID列表（可选，为空则计算全部）
  "async": true                  // 是否异步执行（默认true）
}
```

**响应数据（异步）：**

```json
{
    "success": true,
    "message": "折旧计算任务已提交",
    "data": {
        "task_id": "celery-task-id",
        "estimated_seconds": 30
    }
}
```

**响应数据（同步）：**

```json
{
    "success": true,
    "message": "折旧计算完成",
    "data": {
        "processed": 150,
        "succeeded": 148,
        "failed": 2,
        "errors": [
            {
                "asset_id": "uuid",
                "asset_code": "ZC999",
                "error": "使用年限不能为0"
            }
        ]
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "折旧计算参数验证失败",
        "details": {
            "period": ["期间格式错误"]
        }
    }
}
```

---

## 4. 折旧记录过账

### POST /api/assets/depreciation/{id}/post/

**请求参数：**

```json
{
  "voucher_no": "PZ202401001"    // 凭证号（可选，自动生成）
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "折旧记录过账成功",
    "data": {
        "id": "uuid",
        "status": "posted",
        "voucher_no": "PZ202401001",
        "posted_at": "2024-01-31T15:30:00Z",
        "posted_by": {
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
        "code": "PERMISSION_DENIED",
        "message": "无权限过账此折旧记录"
    }
}
```

---

## 5. 审核折旧记录

### POST /api/assets/depreciation/{id}/approve/

**请求参数：**

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
    "message": "折旧记录审核成功",
    "data": {
        "id": "uuid",
        "status": "approved",
        "approved_at": "2024-01-31T14:00:00Z",
        "approved_by": {
            "id": "uuid",
            "username": "admin",
            "full_name": "管理员"
        },
        "approve_comment": "审核通过"
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "折旧记录状态不允许审核"
    }
}
```

---

## 6. 折旧报表

### GET /api/assets/depreciation/report/

**请求参数：**

```json
{
  "period": "2024-01",
  "category_id": "uuid"
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "summary": {
    "asset_count": 150,
    "current_amount": "23750.00",
    "accumulated_amount": "285000.00",
    "net_value": "1215000.00"
  },
  "by_category": [
    {
      "category_id": "uuid",
      "category_name": "电子设备",
      "asset_count": 80,
      "original_value": "640000.00",
      "current_depreciation": "12666.67",
      "accumulated_depreciation": "152000.00",
      "net_value": "488000.00",
      "depreciation_rate": 23.75
    },
    {
      "category_id": "uuid",
      "category_name": "办公家具",
      "asset_count": 70,
      "original_value": "860000.00",
      "current_depreciation": "11083.33",
      "accumulated_depreciation": "133000.00",
      "net_value": "727000.00",
      "depreciation_rate": 15.47
    }
  ],
  "by_method": [
    {
      "method": "straight_line",
      "method_name": "直线法",
      "asset_count": 120,
      "current_amount": "19000.00"
    },
    {
      "method": "double_declining",
      "method_name": "双倍余额递减法",
      "asset_count": 30,
        "current_amount": "4750.00"
        }
    ]
    }
}
```

---

## 7. 导出折旧记录

### GET /api/assets/depreciation/export/

**请求参数：** 同列表接口

**响应：** Excel文件（application/vnd.openxmlformats-officedocument.spreadsheetml.sheet）

---

## 8. 资产折旧汇总

### GET /api/assets/{id}/depreciation-summary/

**响应数据：**

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "asset_id": "uuid",
  "asset_code": "ZC001",
  "asset_name": "笔记本电脑",
  "purchase_price": "8000.00",
  "residual_value": "400.00",
  "useful_life": 48,
  "depreciation_method": "straight_line",
  "start_date": "2023-01-15",
  "end_date": "2027-01-15",
  "current_status": {
    "used_months": 12,
    "remaining_months": 36,
    "monthly_depreciation": "158.33",
    "accumulated_depreciation": "1900.00",
    "net_value": "6100.00",
    "depreciation_rate": 23.75
  },
  "projection": [
    {
      "period": "2024-02",
      "depreciation_amount": "158.33",
      "accumulated": "2058.33",
        "net_value": "5941.67"
        }
    ]
    }
}
```

---

## Serializers

```python
# apps/assets/serializers/depreciation_serializers.py

from rest_framework import serializers
from apps.assets.models import AssetDepreciation, Asset


class AssetDepreciationListSerializer(serializers.ModelSerializer):
    """折旧记录列表序列化器"""

    asset = serializers.SerializerMethodField()

    class Meta:
        model = AssetDepreciation
        fields = [
            'id', 'asset', 'period', 'depreciation_method',
            'purchase_price', 'depreciation_amount', 'accumulated_depreciation',
            'net_value', 'status', 'voucher_no', 'created_at'
        ]

    def get_asset(self, obj):
        return {
            'id': str(obj.asset.id),
            'asset_code': obj.asset.asset_code,
            'asset_name': obj.asset.asset_name,
            'category_name': obj.asset.asset_category.name
        }


class AssetDepreciationDetailSerializer(serializers.ModelSerializer):
    """折旧记录详情序列化器"""

    asset = AssetSerializer(read_only=True)

    class Meta:
        model = AssetDepreciation
        fields = '__all__'


class AssetDepreciationSummarySerializer(serializers.Serializer):
    """资产折旧汇总序列化器"""

    asset_info = serializers.DictField()
    stat = serializers.DictField()
    records = AssetDepreciationListSerializer(many=True)


class DepreciationReportSerializer(serializers.Serializer):
    """折旧报表序列化器"""

    summary = serializers.DictField()
    by_category = serializers.ListField()
    by_method = serializers.ListField()
```

---

## 后续任务

所有Phase已完成！
