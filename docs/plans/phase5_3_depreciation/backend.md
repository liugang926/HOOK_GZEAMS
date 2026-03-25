# Phase 5.3: 折旧自动计算 - 后端实现

## 概述

实现固定资产折旧自动计算功能，支持多种折旧方法。本模块使用公共基类架构，确保代码的一致性和可维护性。

---

## 3. 公共模型引用

### 3.1 后端基类引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields 序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织隔离、软删除、批量操作、审计字段 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤、时间范围过滤 |

### 3.2 基类功能详解

#### BaseModel 自动功能
- **组织隔离**: 自动通过 `org` 字段过滤数据，支持多租户
- **软删除**: `is_deleted` 和 `deleted_at` 字段，避免物理删除
- **审计字段**: `created_at`, `updated_at`, `created_by` 自动管理
- **动态扩展**: `custom_fields` (JSONB) 支持低代码动态字段

#### BaseModelSerializer 自动功能
- **公共字段**: 自动序列化 `id`, `organization`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`, `created_by`
- **用户信息**: `created_by` 字段自动嵌套 UserSerializer
- **动态字段**: 支持自定义字段的 JSONB 序列化
- **扁平化选项**: 支持 `flatten_custom_fields` 参数展开动态字段

#### BaseModelViewSetWithBatch 自动功能
- **组织过滤**: `get_queryset()` 自动应用组织过滤
- **软删除**: 只显示未删除记录，提供 `/deleted/` 和 `/restore/` 接口
- **批量操作**: 支持批量删除、批量恢复、批量更新
- **审计字段**: `created_by` 和 `organization_id` 自动设置

#### BaseCRUDService 自动功能
- **统一CRUD**: 提供标准的 `create()`, `update()`, `delete()`, `get()`, `query()`, `paginate()` 方法
- **组织隔离**: 所有操作自动应用组织隔离
- **批量支持**: `batch_delete()` 等批量操作方法
- **分页支持**: 标准化的分页查询和响应格式

#### BaseModelFilter 自动功能
- **时间范围**: `created_at`, `updated_at` 范围过滤
- **用户过滤**: `created_by` 用户过滤
- **组织过滤**: 自动继承 TenantManager 的组织过滤
- **扩展过滤**: 支持业务字段的复杂过滤条件

---

## 折旧方法

| 方法 | 代码 | 公式 |
|------|------|------|
| 直线法 | straight_line | 月折旧额 = (原值 - 残值) / 使用月数 |
| 双倍余额递减法 | double_declining | 月折旧额 = 账面净值 × 2 / 使用年限 / 12 |
| 年数总和法 | sum_of_years | 月折旧额 = (原值 - 残值) × 剩余月数 / 总月数 |

---

## 折旧方法

| 方法 | 代码 | 公式 |
|------|------|------|
| 直线法 | straight_line | 月折旧额 = (原值 - 残值) / 使用月数 |
| 双倍余额递减法 | double_declining | 月折旧额 = 账面净值 × 2 / 使用年限 / 12 |
| 年数总和法 | sum_of_years | 月折旧额 = (原值 - 残值) × 剩余月数 / 总月数 |

---

## 折旧模型

```python
# apps/assets/models.py

from apps.common.models import BaseModel

class AssetDepreciation(BaseModel):
    """资产折旧记录"""

    class Meta:
        db_table = 'asset_depreciation'
        verbose_name = '资产折旧记录'
        ordering = ['-period']
        unique_together = [['asset', 'period']]

    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='depreciations')

    # 折旧期间
    period = models.CharField(max_length=7)  # YYYY-MM

    # 折旧信息
    depreciation_method = models.CharField(max_length=20)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2)  # 原值
    residual_value = models.DecimalField(max_digits=12, decimal_places=2)  # 残值
    useful_life = models.IntegerField()  # 使用月数
    used_months = models.IntegerField()  # 已使用月数

    # 折旧金额
    depreciation_amount = models.DecimalField(max_digits=12, decimal_places=2)
    accumulated_depreciation = models.DecimalField(max_digits=12, decimal_places=2)
    net_value = models.DecimalField(max_digits=12, decimal_places=2)

    # 状态
    status = models.CharField(
        max_length=20,
        choices=[('draft', '草稿'), ('submitted', '已提交'), ('approved', '已审核'), ('posted', '已过账')],
        default='draft'
    )
    voucher_no = models.CharField(max_length=50, blank=True)  # 凭证号

    def __str__(self):
        return f"{self.asset.code} - {self.period}"
```

---

## 折旧序列化器

```python
# apps/assets/serializers/depreciation.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.assets.models import AssetDepreciation
from apps.assets.serializers import AssetSimpleSerializer

class AssetDepreciationSerializer(BaseModelSerializer):
    """资产折旧序列化器 - 继承公共基类"""

    # 自动继承 BaseModelSerializer 的所有公共字段：
    # - id, organization, is_deleted, deleted_at
    # - created_at, updated_at, created_by
    # - custom_fields

    # 扩展业务字段
    asset = AssetSimpleSerializer(read_only=True)
    asset_id = serializers.UUIDField(write_only=True)

    depreciation_method_display = serializers.CharField(
        source='get_depreciation_method_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = AssetDepreciation
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'asset_id', 'period',
            'depreciation_method', 'depreciation_method_display',
            'purchase_price', 'residual_value',
            'useful_life', 'used_months',
            'depreciation_amount', 'accumulated_depreciation', 'net_value',
            'status', 'status_display', 'voucher_no'
        ]


class AssetDepreciationListSerializer(BaseModelSerializer):
    """折旧列表序列化器 - 简化版"""

    asset_code = serializers.CharField(source='asset.code', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = AssetDepreciation
        fields = BaseModelSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'period',
            'depreciation_amount', 'accumulated_depreciation',
            'net_value', 'status', 'status_display'
        ]
```

---

## 折旧过滤器

```python
# apps/assets/filters/depreciation.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.assets.models import AssetDepreciation

class AssetDepreciationFilter(BaseModelFilter):
    """资产折旧过滤器 - 继承公共基类"""

    # 自动继承 BaseModelFilter 的所有公共字段：
    # - created_at, created_at_from, created_at_to
    # - updated_at_from, updated_at_to
    # - created_by, is_deleted

    # 扩展业务字段过滤
    period = filters.CharFilter(label='折旧期间')
    period_gte = filters.CharFilter(
        field_name='period',
        lookup_expr='gte',
        label='期间起始'
    )
    period_lte = filters.CharFilter(
        field_name='period',
        lookup_expr='lte',
        label='期间结束'
    )

    status = filters.ChoiceFilter(
        choices=AssetDepreciation.Status.choices,
        label='状态'
    )

    asset = filters.UUIDFilter(field_name='asset_id', label='资产')
    depreciation_method = filters.CharFilter(label='折旧方法')

    # 金额范围过滤
    depreciation_amount_gte = filters.NumberFilter(
        field_name='depreciation_amount',
        lookup_expr='gte',
        label='折旧额（起始）'
    )
    depreciation_amount_lte = filters.NumberFilter(
        field_name='depreciation_amount',
        lookup_expr='lte',
        label='折旧额（结束）'
    )

    class Meta(BaseModelFilter.Meta):
        model = AssetDepreciation
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'period', 'period_gte', 'period_lte',
            'status', 'asset', 'depreciation_method',
            'depreciation_amount_gte', 'depreciation_amount_lte'
        ]
```

---

## 折旧计算引擎

```python
# apps/assets/services/depreciation_engine.py

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict
from apps.assets.models import Asset

class DepreciationEngine:
    """折旧计算引擎"""

    @staticmethod
    def calculate(asset: Asset, period: str) -> Dict:
        """
        计算资产折旧

        Args:
            asset: 资产实例
            period: 折旧期间 (YYYY-MM)

        Returns:
            折旧计算结果字典
        """
        method = asset.asset_category.depreciation_method

        if method == 'straight_line':
            return DepreciationEngine.straight_line(asset, period)
        elif method == 'double_declining':
            return DepreciationEngine.double_declining(asset, period)
        elif method == 'sum_of_years':
            return DepreciationEngine.sum_of_years(asset, period)
        else:
            raise ValueError(f"不支持的折旧方法: {method}")

    @staticmethod
    def straight_line(asset: Asset, period: str) -> Dict:
        """
        直线折旧法

        月折旧额 = (原值 - 残值) / 使用月数
        """
        residual_value = asset.purchase_price * Decimal(asset.asset_category.residual_rate / 100)
        useful_months = asset.useful_life * 12  # 转换为月数

        if useful_months <= 0:
            raise ValueError("使用年限必须大于0")

        monthly_depreciation = (asset.purchase_price - residual_value) / Decimal(useful_months)

        used_months = DepreciationEngine._calculate_used_months(asset, period)
        accumulated_depreciation = monthly_depreciation * Decimal(used_months)
        net_value = asset.purchase_price - accumulated_depreciation

        # 超过使用年限不再计提
        if used_months >= useful_months:
            monthly_depreciation = Decimal('0')
            accumulated_depreciation = asset.purchase_price - residual_value
            net_value = residual_value

        return {
            'depreciation_amount': monthly_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'accumulated_depreciation': accumulated_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'net_value': net_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        }

    @staticmethod
    def double_declining(asset: Asset, period: str) -> Dict:
        """
        双倍余额递减法

        月折旧额 = 账面净值 × 2 / 使用年限 / 12
        """
        useful_life = asset.useful_life
        useful_months = useful_life * 12

        if useful_life <= 0:
            raise ValueError("使用年限必须大于0")

        used_months = DepreciationEngine._calculate_used_months(asset, period)

        # 获取累计折旧
        from apps.assets.models import AssetDepreciation
        last_depreciation = AssetDepreciation.objects.filter(
            asset=asset,
            period__lt=period
        ).order_by('-period').first()

        accumulated_depreciation = last_depreciation.accumulated_depreciation if last_depreciation else Decimal('0')
        net_value = asset.purchase_price - accumulated_depreciation

        # 计算月折旧额
        monthly_rate = Decimal(2) / Decimal(useful_life) / Decimal(12)
        monthly_depreciation = net_value * monthly_rate

        # 最后两年改用直线法
        if used_months >= useful_months - 24:
            residual_value = asset.purchase_price * Decimal(asset.asset_category.residual_rate / 100)
            remaining_months = useful_months - used_months
            if remaining_months > 0:
                monthly_depreciation = (net_value - residual_value) / Decimal(remaining_months)

        # 更新累计折旧和净值
        accumulated_depreciation += monthly_depreciation
        net_value = asset.purchase_price - accumulated_depreciation

        # 超过使用年限
        if used_months >= useful_months:
            monthly_depreciation = Decimal('0')
            net_value = max(net_value, asset.purchase_price * Decimal(asset.asset_category.residual_rate / 100))

        return {
            'depreciation_amount': monthly_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'accumulated_depreciation': accumulated_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'net_value': net_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        }

    @staticmethod
    def sum_of_years(asset: Asset, period: str) -> Dict:
        """
        年数总和法

        月折旧额 = (原值 - 残值) × 剩余月数 / 总月数
        """
        useful_life = asset.useful_life
        useful_months = useful_life * 12

        if useful_life <= 0:
            raise ValueError("使用年限必须大于0")

        # 计算总月数（年数总和）
        total_months = sum(range(1, useful_months + 1))

        used_months = DepreciationEngine._calculate_used_months(asset, period)
        remaining_months = max(0, useful_months - used_months)

        # 获取累计折旧
        from apps.assets.models import AssetDepreciation
        last_depreciation = AssetDepreciation.objects.filter(
            asset=asset,
            period__lt=period
        ).order_by('-period').first()

        accumulated_depreciation = last_depreciation.accumulated_depreciation if last_depreciation else Decimal('0')

        # 计算当月折旧
        residual_value = asset.purchase_price * Decimal(asset.asset_category.residual_rate / 100)
        depreciable_amount = asset.purchase_price - residual_value

        if remaining_months > 0:
            monthly_depreciation = depreciable_amount * Decimal(remaining_months) / Decimal(total_months)
        else:
            monthly_depreciation = Decimal('0')

        # 更新累计折旧和净值
        accumulated_depreciation += monthly_depreciation
        net_value = asset.purchase_price - accumulated_depreciation

        return {
            'depreciation_amount': monthly_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'accumulated_depreciation': accumulated_depreciation.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            'net_value': net_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
        }

    @staticmethod
    def _calculate_used_months(asset: Asset, period: str) -> int:
        """计算已使用月数"""
        from datetime import datetime

        start_date = asset.purchase_date
        current_date = datetime.strptime(period + '-01', '%Y-%m-%d')

        months = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month) + 1

        return max(0, months - 1)
```

---

## 折旧服务层

```python
# apps/assets/services/depreciation_service.py

from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import Asset, AssetDepreciation
from apps.assets.services.depreciation_engine import DepreciationEngine

class DepreciationService(BaseCRUDService):
    """折旧服务 - 继承公共 CRUD 基类"""

    def __init__(self):
        super().__init__(AssetDepreciation)

    def calculate_asset_depreciation(self, asset: Asset, period: str) -> AssetDepreciation:
        """
        计算单个资产的折旧

        Args:
            asset: 资产实例
            period: 折旧期间

        Returns:
            折旧记录
        """
        # 检查是否已计算
        existing = self.model_class.objects.filter(
            asset=asset,
            period=period
        ).first()

        if existing:
            return existing

        # 计算折旧
        result = DepreciationEngine.calculate(asset, period)

        # 创建折旧记录
        depreciation = self.create({
            'asset': asset,
            'period': period,
            'depreciation_method': asset.asset_category.depreciation_method,
            'purchase_price': asset.purchase_price,
            'residual_value': result.get('net_value', asset.purchase_price * Decimal('0.05')),
            'useful_life': asset.useful_life * 12,
            'used_months': self._calculate_used_months(asset, period),
            **result
        })

        return depreciation

    def batch_calculate_period(self, period: str) -> Dict:
        """
        批量计算某期间的所有资产折旧

        Args:
            period: 折旧期间 (YYYY-MM)

        Returns:
            批量操作结果
        """
        from apps.accounts.models import User

        # 获取需要计提折旧的资产
        assets = Asset.objects.filter(
            is_deleted=False,
            purchase_date__lte=timezone.now()
        )

        succeeded = 0
        failed = 0
        results = []

        for asset in assets:
            try:
                depreciation = self.calculate_asset_depreciation(asset, period)
                succeeded += 1
                results.append({
                    'asset_id': str(asset.id),
                    'asset_code': asset.code,
                    'success': True,
                    'depreciation_id': str(depreciation.id)
                })
            except Exception as e:
                failed += 1
                results.append({
                    'asset_id': str(asset.id),
                    'asset_code': asset.code,
                    'success': False,
                    'error': str(e)
                })

        return {
            'period': period,
            'total': len(assets),
            'succeeded': succeeded,
            'failed': failed,
            'results': results
        }

    def get_depreciation_summary(self, asset_id: str) -> Dict:
        """
        获取资产折旧汇总

        Args:
            asset_id: 资产ID

        Returns:
            折旧汇总信息
        """
        depreciations = self.query(filters={'asset_id': asset_id})

        total_depreciation = sum(d.depreciation_amount for d in depreciations)

        return {
            'asset_id': asset_id,
            'total_periods': depreciations.count(),
            'total_depreciation': total_depreciation,
            'latest_period': depreciations.first().period if depreciations.exists() else None,
            'latest_net_value': depreciations.first().net_value if depreciations.exists() else None
        }

    def _calculate_used_months(self, asset: Asset, period: str) -> int:
        """计算已使用月数（内部方法）"""
        from datetime import datetime

        start_date = asset.purchase_date
        current_date = datetime.strptime(period + '-01', '%Y-%m-%d')

        months = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month) + 1

        return max(0, months - 1)

    def submit_for_approval(self, depreciation_id: str, user) -> AssetDepreciation:
        """
        提交折旧审核

        Args:
            depreciation_id: 折旧记录ID
            user: 操作用户

        Returns:
            更新后的折旧记录
        """
        depreciation = self.get(depreciation_id)

        if depreciation.status != 'draft':
            raise ValueError("只有草稿状态的记录才能提交审核")

        return self.update(depreciation_id, {'status': 'submitted'}, user=user)

    def approve_depreciation(self, depreciation_id: str, user, voucher_no: str = None) -> AssetDepreciation:
        """
        审核通过折旧

        Args:
            depreciation_id: 折旧记录ID
            user: 操作用户
            voucher_no: 凭证号

        Returns:
            更新后的折旧记录
        """
        depreciation = self.get(depreciation_id)

        if depreciation.status != 'submitted':
            raise ValueError("只有已提交状态的记录才能审核")

        update_data = {'status': 'approved'}
        if voucher_no:
            update_data['voucher_no'] = voucher_no

        return self.update(depreciation_id, update_data, user=user)

    def post_depreciation(self, depreciation_id: str, user) -> AssetDepreciation:
        """
        过账折旧

        Args:
            depreciation_id: 折旧记录ID
            user: 操作用户

        Returns:
            更新后的折旧记录
        """
        depreciation = self.get(depreciation_id)

        if depreciation.status != 'approved':
            raise ValueError("只有已审核状态的记录才能过账")

        return self.update(depreciation_id, {'status': 'posted'}, user=user)
```

---

## 折旧视图层

```python
# apps/assets/views/depreciation.py

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.assets.models import AssetDepreciation
from apps.assets.serializers.depreciation import (
    AssetDepreciationSerializer,
    AssetDepreciationListSerializer
)
from apps.assets.filters.depreciation import AssetDepreciationFilter
from apps.assets.services.depreciation_service import DepreciationService

class AssetDepreciationViewSet(BaseModelViewSetWithBatch):
    """
    资产折旧 ViewSet - 继承公共基类

    自动获得：
    - 组织隔离
    - 软删除/恢复
    - 批量删除/恢复/更新
    - 审计字段自动设置
    """

    queryset = AssetDepreciation.objects.all()
    serializer_class = AssetDepreciationSerializer
    filterset_class = AssetDepreciationFilter
    service = DepreciationService()

    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'list':
            return AssetDepreciationListSerializer
        return AssetDepreciationSerializer

    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        计算折旧

        POST /api/assets/depreciations/calculate/
        {
            "period": "2025-01"
        }
        """
        period = request.data.get('period')

        if not period:
            return Response(
                {'detail': '请提供折旧期间'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = self.service.batch_calculate_period(period)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        提交审核

        POST /api/assets/depreciations/{id}/submit/
        """
        try:
            depreciation = self.service.submit_for_approval(pk, request.user)
            serializer = self.get_serializer(depreciation)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        审核通过

        POST /api/assets/depreciations/{id}/approve/
        {
            "voucher_no": "PZH202501001"
        }
        """
        try:
            voucher_no = request.data.get('voucher_no')
            depreciation = self.service.approve_depreciation(pk, request.user, voucher_no)
            serializer = self.get_serializer(depreciation)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def post(self, request, pk=None):
        """
        过账

        POST /api/assets/depreciations/{id}/post/
        """
        try:
            depreciation = self.service.post_depreciation(pk, request.user)
            serializer = self.get_serializer(depreciation)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        获取折旧汇总

        GET /api/assets/depreciations/summary/?asset_id={uuid}
        """
        asset_id = request.query_params.get('asset_id')

        if not asset_id:
            return Response(
                {'detail': '请提供资产ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            summary = self.service.get_depreciation_summary(asset_id)
            return Response(summary)
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

---

## URL配置

```python
# apps/assets/urls/depreciation.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.assets.views.depreciation import AssetDepreciationViewSet

router = DefaultRouter()
router.register(r'depreciations', AssetDepreciationViewSet, basename='assetdepreciation')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## Celery定时任务

```python
# apps/assets/tasks/depreciation_tasks.py

from celery import shared_task
from celery.utils.log import get_task_logger
from apps.assets.services.depreciation_service import DepreciationService
from django.utils import timezone

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3)
def calculate_monthly_depreciation_task(self, period=None):
    """
    月度折旧计算任务

    Args:
        period: 折旧期间 (YYYY-MM)，为空时使用当前月份
    """
    try:
        if not period:
            period = timezone.now().strftime('%Y-%m')

        service = DepreciationService()
        result = service.batch_calculate_period(period)

        logger.info(f"折旧计算完成: {result}")

        return result

    except Exception as e:
        logger.error(f"折旧计算失败: {str(e)}")

        # 重试机制
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        raise


@shared_task
def generate_depreciation_report_task(period):
    """
    生成折旧报表任务

    Args:
        period: 折旧期间 (YYYY-MM)
    """
    from apps.assets.services.depreciation_service import DepreciationService

    service = DepreciationService()

    # 获取期间内所有折旧记录
    depreciations = service.query(filters={'period': period})

    # TODO: 生成报表逻辑
    # - 导出 Excel
    # - 发送邮件
    # - 保存到文件存储

    logger.info(f"折旧报表生成完成: {period}, 记录数: {depreciations.count()}")

    return {
        'period': period,
        'count': depreciations.count()
    }
```

---

## Celery Beat配置

```python
# backend/config/celery.py

from celery import Celery
from celery.schedules import crontab

app = Celery('gzeams')

# 配置定时任务
app.conf.beat_schedule = {
    # 每月1日凌晨2点计算折旧
    'calculate-monthly-depreciation': {
        'task': 'apps.assets.tasks.depreciation_tasks.calculate_monthly_depreciation_task',
        'schedule': crontab(hour=2, minute=0, day_of_month=1),
        'options': {
            'expires': 3600  # 任务1小时后过期
        }
    },
}
```

---

## API接口文档

### 1. 统一响应格式

所有API接口均遵循以下统一响应格式：

#### 成功响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "asset_code": "ZC001",
        "asset_name": "笔记本电脑",
        "period": "2025-01",
        "depreciation_amount": "83.33",
        "accumulated_depreciation": "1000.00",
        "net_value": "4000.00",
        "status": "draft",
        "created_at": "2026-01-15T10:30:00Z"
    }
}
```

#### 列表响应格式（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 150,
        "next": "https://api.example.com/api/assets/depreciations/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "asset_code": "ZC001",
                "asset_name": "笔记本电脑",
                "period": "2025-01",
                "depreciation_amount": "83.33",
                ...
            }
        ]
    }
}
```

#### 错误响应格式

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "period": ["该字段不能为空"],
            "asset": ["资产不存在"]
        }
    }
}
```

### 2. 统一错误码定义

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |
| `DEPRECIATION_CALC_ERROR` | 400 | 折旧计算失败 |
| `ASSET_NOT_FOUND` | 404 | 资产不存在 |
| `PERIOD_ALREADY_CALCULATED` | 409 | 该期间已计算折旧 |
| `INVALID_DEPRECIATION_METHOD` | 400 | 无效的折旧方法 |

### 3. 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

详见 `common_base_features/api.md` 中的标准 API 规范。

AssetDepreciation 模型继承自 BaseModel，因此自动获得以下标准端点：

**折旧记录标准端点**：
- `GET /api/assets/depreciations/` - 列表查询（分页、过滤、搜索）
- `GET /api/assets/depreciations/{id}/` - 获取单条记录
- `POST /api/assets/depreciations/` - 创建新记录
- `PUT /api/assets/depreciations/{id}/` - 完整更新
- `PATCH /api/assets/depreciations/{id}/` - 部分更新
- `DELETE /api/assets/depreciations/{id}/` - 软删除
- `GET /api/assets/depreciations/deleted/` - 查看已删除记录
- `POST /api/assets/depreciations/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/assets/depreciations/batch-delete/` - 批量软删除
- `POST /api/assets/depreciations/batch-restore/` - 批量恢复
- `POST /api/assets/depreciations/batch-update/` - 批量更新

### 4. 批量操作 API 规范

#### 4.1 批量计算折旧

```http
POST /api/assets/depreciations/calculate/
Content-Type: application/json

{
    "period": "2025-01",
    "asset_ids": ["uuid1", "uuid2"]  // 可选，不提供则计算所有资产
}
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "折旧计算完成",
    "data": {
        "period": "2025-01",
        "total": 150,
        "succeeded": 148,
        "failed": 2,
        "results": [
            {
                "asset_id": "550e8400-e29b-41d4-a716-446655440000",
                "asset_code": "ZC001",
                "success": true,
                "depreciation_id": "550e8400-e29b-41d4-a716-446655440001"
            },
            {
                "asset_id": "550e8400-e29b-41d4-a716-446655440002",
                "asset_code": "ZC002",
                "success": false,
                "error": "资产已报废，停止计提折旧"
            }
        ]
    }
}
```

#### 4.2 批量提交审核

```http
POST /api/assets/depreciations/batch-submit/
Content-Type: application/json

{
    "ids": ["uuid1", "uuid2", "uuid3"],
    "remarks": "批量提交2025年1月折旧审核"
}
```

**响应格式与批量计算相同**

#### 4.3 批量审核通过

```http
POST /api/assets/depreciations/batch-approve/
Content-Type: application/json

{
    "ids": ["uuid1", "uuid2"],
    "voucher_no_prefix": "PZH202501",
    "remarks": "批量审核通过"
}
```

**响应格式与批量计算相同**

### 5. 折旧计算接口

#### 5.1 批量计算折旧

```
POST /api/assets/depreciations/calculate/

请求体：
{
    "period": "2025-01"
}

响应：
{
    "success": true,
    "message": "折旧计算完成",
    "data": {
        "period": "2025-01",
        "total": 150,
        "succeeded": 148,
        "failed": 2,
        "results": [
            {
                "asset_id": "uuid",
                "asset_code": "ZC001",
                "success": true,
                "depreciation_id": "uuid"
            }
        ]
    }
}
```

**错误响应示例**：
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请提供折旧期间",
        "details": {
            "period": ["该字段不能为空"]
        }
    }
}
```

#### 5.2 获取折旧列表

```
GET /api/assets/depreciations/

查询参数：
- period: 折旧期间
- period_gte: 期间起始
- period_lte: 期间结束
- status: 状态
- asset: 资产ID
- depreciation_method: 折旧方法
- page: 页码
- page_size: 每页数量

响应：
{
    "success": true,
    "data": {
        "count": 150,
        "next": null,
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "asset_code": "ZC001",
                "asset_name": "笔记本电脑",
                "period": "2025-01",
                "depreciation_amount": "83.33",
                "accumulated_depreciation": "1000.00",
                "net_value": "4000.00",
                "status": "draft",
                "status_display": "草稿"
            }
        ]
    }
}
```

### 6. 折旧审核流程

#### 6.1 提交审核

```
POST /api/assets/depreciations/{id}/submit/

响应：
{
    "success": true,
    "message": "提交成功",
    "data": {
        "id": "uuid",
        "status": "submitted",
        "status_display": "已提交"
    }
}
```

#### 6.2 审核通过

```
POST /api/assets/depreciations/{id}/approve/

请求体：
{
    "voucher_no": "PZH202501001"
}

响应：
{
    "success": true,
    "message": "审核成功",
    "data": {
        "id": "uuid",
        "status": "approved",
        "voucher_no": "PZH202501001"
    }
}
```

#### 6.3 过账

```
POST /api/assets/depreciations/{id}/post/

响应：
{
    "success": true,
    "message": "过账成功",
    "data": {
        "id": "uuid",
        "status": "posted",
        "status_display": "已过账"
    }
}
```

### 7. 统计汇总

#### 7.1 资产折旧汇总

```
GET /api/assets/depreciations/summary/?asset_id={uuid}

响应：
{
    "success": true,
    "data": {
        "asset_id": "uuid",
        "total_periods": 12,
        "total_depreciation": 1000.00,
        "latest_period": "2025-01",
        "latest_net_value": 4000.00
    }
}
```

#### 7.2 部门折旧汇总

```
GET /api/assets/depreciations/department-summary/

查询参数：
- period: 折旧期间（可选）
- department_id: 部门ID（可选）

响应：
{
    "success": true,
    "data": {
        "period": "2025-01",
        "summary": [
            {
                "department_id": "uuid",
                "department_name": "技术部",
                "total_depreciation": 50000.00,
                "asset_count": 50,
                "avg_depreciation": 1000.00
            }
        ]
    }
}
```

#### 7.3 分类折旧汇总

```
GET /api/assets/depreciations/category-summary/

查询参数：
- period: 折旧期间（可选）
- category_id: 分类ID（可选）

响应：
{
    "success": true,
    "data": {
        "period": "2025-01",
        "summary": [
            {
                "category_id": "uuid",
                "category_name": "电子设备",
                "total_depreciation": 80000.00,
                "asset_count": 80,
                "avg_depreciation": 1000.00
            }
        ]
    }
}
```

---

## 后续任务

所有Phase已完成！
---

## API接口规范

### 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 列表响应
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 错误响应
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

### 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |