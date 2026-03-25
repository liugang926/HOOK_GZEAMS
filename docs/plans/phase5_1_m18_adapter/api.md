# Phase 5.1: 万达宝M18适配器 - API接口定义

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

M18适配器复用通用集成框架的API接口。以下是M18特有的接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| M18特定 | | |
| GET | `/api/integration/m18/purchase-orders/` | 获取同步的采购订单 |
| GET | `/api/integration/m18/purchase-orders/{id}/` | 获取采购订单详情 |
| POST | `/api/integration/m18/sync/purchase-orders/` | 触发采购订单同步 |
| GET | `/api/integration/m18/suppliers/` | 获取同步的供应商 |
| POST | `/api/integration/m18/sync/suppliers/` | 触发供应商同步 |
| GET | `/api/integration/m18/goods-receipts/` | 获取收货单 |
| POST | `/api/integration/m18/goods-receipts/` | 创建收货单 |

---

## 1. 采购订单同步

### POST /api/integration/m18/sync/purchase-orders/

触发M18采购订单同步

**请求体：**

```json
{
  "start_date": "2024-01-01",    // 开始日期（可选）
  "end_date": "2024-01-31",      // 结束日期（可选）
  "async": true                  // 是否异步执行
}
```

**响应数据（异步）：**

```json
{
    "success": true,
    "message": "采购订单同步任务已创建",
    "data": {
        "task_id": "sync_task_123456",
        "celery_task_id": "xxx-xxx-xxx",
        "status": "pending"
    }
}
```

**响应数据（同步）：**

```json
{
    "success": true,
    "message": "同步完成",
    "data": {
        "task_id": "sync_task_123456",
        "status": "success",
        "total": 50,
        "succeeded": 48,
        "failed": 2,
        "errors": [
            {
                "po_id": "123",
                "po_no": "PO202401001",
                "error": "供应商不存在"
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
        "code": "PERMISSION_DENIED",
        "message": "未找到启用的M18配置或无权限访问"
    }
}
```

---

## 2. 供应商同步

### POST /api/integration/m18/sync/suppliers/

触发M18供应商同步

**请求体：**

```json
{
  "updated_since": "2024-01-01T00:00:00Z",  // 更新时间（可选）
  "async": true
}
```

**响应数据：**

```json
{
  "task_id": "sync_task_123457",
  "message": "供应商同步任务已创建",
  "status": "pending"
}
```

---

## 3. 创建收货单

### POST /api/integration/m18/goods-receipts/

推送收货单到M18

**请求体：**

```json
{
  "po_id": "PO_M18_123",
  "receipt_date": "2024-01-15",
  "warehouse_code": "WH01",
  "line_items": [
    {
      "line_id": "1",
      "material_code": "M001",
      "quantity": 100,
      "uom": "PCS",
      "location": "A01-01-01"
    }
  ]
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "收货单创建成功",
    "data": {
        "gr_no": "GR2024010001",
        "gr_id": "123456",
        "external_id": "123456"
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "收货单数据验证失败",
        "details": {
            "po_id": ["采购订单不存在"]
        }
    }
}
```

---

## Serializers

```python
# apps/integration/serializers/m18_serializers.py

from rest_framework import serializers


class M18SyncRequestSerializer(serializers.Serializer):
    """M18同步请求序列化器"""
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    updated_since = serializers.DateTimeField(required=False)
    async = serializers.BooleanField(default=True)


class M18GoodsReceiptSerializer(serializers.Serializer):
    """M18收货单序列化器"""
    po_id = serializers.CharField(max_length=50)
    receipt_date = serializers.DateField()
    warehouse_code = serializers.CharField(max_length=20)
    line_items = serializers.ListField(
        child=serializers.DictField()
    )


class M18LineItemSerializer(serializers.Serializer):
    """M18明细行序列化器"""
    line_id = serializers.CharField(max_length=20, required=False)
    material_code = serializers.CharField(max_length=50)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    uom = serializers.CharField(max_length=10)
    location = serializers.CharField(max_length=50, required=False)
```

---

## ViewSets

```python
# apps/integration/views/m18_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.integration.adapters.m18_adapter import M18Adapter
from apps.integration.factory import AdapterFactory


class M18PurchaseOrderViewSet(viewsets.ViewSet):
    """M18采购订单视图集"""

    def list(self, request):
        """获取同步的采购订单列表"""
        from apps.procurement.models import PurchaseOrder

        queryset = PurchaseOrder.objects.filter(
            organization=request.user.organization,
            integration_source='m18'
        )

        # 筛选
        po_code = request.query_params.get('po_code')
        if po_code:
            queryset = queryset.filter(po_code__icontains=po_code)

        # 分页
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)

        serializer = PurchaseOrderSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def retrieve(self, request, pk=None):
        """获取采购订单详情"""
        from apps.procurement.models import PurchaseOrder

        try:
            order = PurchaseOrder.objects.get(
                id=pk,
                organization=request.user.organization
            )
            return Response(PurchaseOrderSerializer(order).data)
        except PurchaseOrder.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """触发采购订单同步"""
        from apps.integration.models import IntegrationConfig
        from apps.integration.tasks.m18_tasks import sync_m18_purchase_orders

        # 获取M18配置
        config = IntegrationConfig.objects.filter(
            organization=request.user.organization,
            system_type='m18',
            is_enabled=True
        ).first()

        if not config:
            return Response(
                {'error': '未找到启用的M18配置'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = M18SyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        async_exec = data.get('async', True)

        if async_exec:
            # 异步执行
            task = sync_m18_purchase_orders.delay(
                str(config.id),
                data.get('start_date'),
                data.get('end_date')
            )
            return Response({
                'task_id': task.id,
                'message': '采购订单同步任务已创建',
                'status': 'pending'
            })
        else:
            # 同步执行
            adapter = AdapterFactory.create(config)
            result = adapter.sync_purchase_orders_batch(
                data.get('start_date'),
                data.get('end_date')
            )
            return Response(result)


class M18GoodsReceiptViewSet(viewsets.ViewSet):
    """M18收货单视图集"""

    def create(self, request):
        """创建收货单"""
        from apps.integration.models import IntegrationConfig

        config = IntegrationConfig.objects.filter(
            organization=request.user.organization,
            system_type='m18',
            is_enabled=True
        ).first()

        if not config:
            return Response(
                {'error': '未找到启用的M18配置'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = M18GoodsReceiptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        adapter = AdapterFactory.create(config)
        result = adapter.create_goods_receipt(
            po_id=serializer.validated_data['po_id'],
            items=serializer.validated_data['line_items'],
            receipt_date=serializer.validated_data['receipt_date']
        )

        return Response(result)
```

---

## URL配置

```python
# apps/integration/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.integration.views.m18_views import M18PurchaseOrderViewSet, M18GoodsReceiptViewSet

router = DefaultRouter()
router.register(r'purchase-orders', M18PurchaseOrderViewSet, basename='m18-purchase-order')
router.register(r'goods-receipts', M18GoodsReceiptViewSet, basename='m18-goods-receipt')

urlpatterns = [
    path('m18/', include(router.urls)),
]
```

---

## 后续任务

1. Phase 5.2: 实现财务凭证集成（基于通用框架）
2. 扩展其他ERP适配器
