# Phase 1.4: 资产卡片CRUD - 后端实现

## 1. 功能概述

### 1.1 业务场景

资产卡片是固定资产管理的核心对象，记录资产的完整生命周期信息。本次实现资产的基本CRUD功能，包括：

| 功能 | 说明 | 业务价值 |
|------|------|----------|
| **资产新增** | 录入新购资产信息，支持手动/复制/批量导入 | 快速建档 |
| **资产编辑** | 修改资产信息，记录变更日志 | 信息准确性 |
| **资产查询** | 多维度组合查询（分类/部门/状态/日期范围） | 快速定位 |
| **资产详情** | 查看完整档案和变更记录 | 完整追溯 |
| **二维码管理** | 自动生成唯一二维码，支持批量打印 | 一物一码 |
| **状态变更** | 支持资产状态流转，记录变更原因 | 全生命周期管理 |

### 1.2 用户角色与权限

| 角色 | 权限 |
|------|------|
| **资产管理员** | 资产CRUD全权限 |
| **部门管理员** | 查看本部门资产、编辑保管人/位置等 |
| **普通员工** | 仅查看资产信息 |
| **财务人员** | 查看资产价值信息、折旧信息 |

---

## 2. 公共模型引用声明

### 2.1 后端公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **Serializer** | `BaseModelWithAuditSerializer` | `apps.common.serializers.base.BaseModelWithAuditSerializer` | 完整审计字段序列化（含updated_by、deleted_by） |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作、审计字段设置 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤、状态过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法、组织隔离、分页查询 |

### 2.2 继承关系说明

```python
# ✅ 资产模型继承 BaseModel
class Asset(BaseModel):
    """自动获得: organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields"""
    pass

# ✅ 资产序列化器继承 BaseModelSerializer
class AssetSerializer(BaseModelSerializer):
    """自动序列化所有公共字段"""
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['asset_code', 'asset_name', ...]

# ✅ 资产服务继承 BaseCRUDService
class AssetService(BaseCRUDService):
    """自动获得: create(), update(), delete(), restore(), get(), query(), paginate()"""
    def __init__(self):
        super().__init__(Asset)

# ✅ 资产过滤器继承 BaseModelFilter
class AssetFilter(BaseModelFilter):
    """自动获得: created_at, updated_at, created_by, is_deleted 等公共字段过滤"""
    class Meta(BaseModelFilter.Meta):
        model = Asset
        fields = BaseModelFilter.Meta.fields + ['asset_code', 'asset_name', ...]

# ✅ 资产ViewSet继承 BaseModelViewSetWithBatch
class AssetViewSet(BaseModelViewSetWithBatch):
    """自动获得: 组织过滤、软删除、批量操作、审计字段设置"""
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
```

---

## 3. 数据模型设计

### 3.1 Asset（资产卡片）核心模型

```python
# apps/assets/models.py

from django.db import models
from django.core.validators import MinValueValidator
from apps.common.models import BaseModel


class Asset(BaseModel):
    """
    资产卡片模型

    继承自 BaseModel，自动获得：
    - organization: 组织隔离
    - is_deleted, deleted_at: 软删除
    - created_at, updated_at, created_by: 审计字段
    - custom_fields: 动态字段（JSONB）
    """

    class Meta:
        db_table = 'assets'
        verbose_name = '资产卡片'
        verbose_name_plural = '资产卡片'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'asset_code']),
            models.Index(fields=['asset_category']),
            models.Index(fields=['custodian']),
            models.Index(fields=['qr_code']),
            models.Index(fields=['asset_status']),
        ]

    # ========== 基础信息 ==========
    asset_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='资产编码'
    )
    asset_name = models.CharField(
        max_length=200,
        verbose_name='资产名称'
    )
    asset_category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.PROTECT,
        related_name='assets',
        verbose_name='资产分类'
    )
    specification = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='规格型号'
    )
    brand = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='品牌',
        help_text='建议使用字典: ASSET_BRAND'
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='型号',
        help_text='建议使用字典: ASSET_MODEL'
    )
    unit = models.CharField(
        max_length=20,
        verbose_name='计量单位',
        help_text='建议使用字典: UNIT'
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='序列号'
    )

    # ========== 财务信息 ==========
    purchase_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='购置原值'
    )
    current_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='当前价值'
    )
    accumulated_depreciation = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name='累计折旧'
    )
    purchase_date = models.DateField(
        verbose_name='购置日期'
    )
    depreciation_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='折旧起始日期'
    )
    useful_life = models.IntegerField(
        default=60,
        verbose_name='使用年限(月)'
    )
    residual_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name='残值率(%)'
    )

    # ========== 供应商信息 ==========
    supplier = models.ForeignKey(
        'assets.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='供应商'
    )
    supplier_order_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='采购订单号'
    )
    invoice_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='发票号码'
    )

    # ========== 使用信息 ==========
    department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name='使用部门'
    )
    location = models.ForeignKey(
        'assets.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        verbose_name='存放地点'
    )
    custodian = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='custodian_assets',
        verbose_name='保管人'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='using_assets',
        verbose_name='使用人'
    )

    # ========== 状态信息 ==========
    asset_status = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='资产状态',
        help_text='引用字典: ASSET_STATUS'
    )

    # ========== 标签信息 ==========
    qr_code = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='二维码'
    )
    rfid_code = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        verbose_name='RFID码'
    )

    # ========== 附件信息 ==========
    images = models.JSONField(
        default=list,
        blank=True,
        verbose_name='资产图片'
    )
    attachments = models.ManyToManyField(
        'system.SystemFile',
        blank=True,
        related_name='assets',
        verbose_name='附件列表'
    )
    remarks = models.TextField(
        blank=True,
        verbose_name='备注'
    )

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"

    def save(self, *args, **kwargs):
        # 自动生成资产编码
        if not self.asset_code:
            self.asset_code = self._generate_asset_code()

        # 自动生成二维码
        if not self.qr_code:
            self.qr_code = self._generate_qr_code()

        # 设置折旧起始日期
        if not self.depreciation_start_date and self.purchase_date:
            self.depreciation_start_date = self.purchase_date

        super().save(*args, **kwargs)

    def _generate_asset_code(self):
        """生成资产编码"""
        # 使用 SequeneService 生成
        # return SequenceService.get_next_value('ASSET_CODE')
        pass

    def _generate_qr_code(self):
        """生成二维码内容"""
        import uuid
        return str(uuid.uuid4())

    @property
    def net_value(self):
        """获取净值"""
        return float(self.purchase_price) - float(self.accumulated_depreciation)

    @property
    def residual_value(self):
        """获取预计净残值"""
        return float(self.purchase_price) * float(self.residual_rate) / 100

    def get_status_label(self):
        """获取状态标签"""
        return dict(self.ASSET_STATUS_CHOICES).get(self.asset_status, self.asset_status)
```

### 3.2 辅助模型

#### Supplier（供应商）

```python
class Supplier(BaseModel):
    """供应商

    继承 BaseModel，自动获得组织隔离和软删除功能
    """
    class Meta:
        db_table = 'suppliers'
        verbose_name = '供应商'

    code = models.CharField(max_length=50, unique=True, verbose_name='供应商编码')
    name = models.CharField(max_length=200, verbose_name='供应商名称')
    contact = models.CharField(max_length=100, blank=True, verbose_name='联系人')
    phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    email = models.EmailField(blank=True, verbose_name='邮箱')
    address = models.TextField(blank=True, verbose_name='地址')

    def __str__(self):
        return self.name
```

#### Location（存放地点）

```python
class Location(BaseModel):
    """存放地点

    继承 BaseModel，支持树形结构
    """
    class Meta:
        db_table = 'locations'
        verbose_name = '存放地点'
        ordering = ['path']

    name = models.CharField(max_length=200, verbose_name='地点名称')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    path = models.CharField(max_length=500, verbose_name='路径')
    level = models.IntegerField(default=0, verbose_name='层级')
    location_type = models.CharField(
        max_length=20,
        choices=[('building', '楼栋'), ('floor', '楼层'), ('room', '房间'), ('area', '区域')],
        default='area',
        verbose_name='地点类型'
    )

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path} / {self.name}"
        else:
            self.level = 0
            self.path = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
```

#### AssetStatusLog（资产状态变更日志）

```python
class AssetStatusLog(BaseModel):
    """资产状态变更日志

    继承 BaseModel，记录完整的状态变更历史
    """
    class Meta:
        db_table = 'asset_status_logs'
        verbose_name = '资产状态日志'
        ordering = ['-created_at']

    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='status_logs')
    old_status = models.CharField(max_length=20, verbose_name='原状态')
    new_status = models.CharField(max_length=20, verbose_name='新状态')
    reason = models.TextField(blank=True, verbose_name='变更原因')
```

---

## 4. 序列化器设计

```python
# apps/assets/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.assets.models import Asset, Supplier, Location, AssetStatusLog
from apps.accounts.serializers import UserSerializer
from apps.organizations.serializers import DepartmentSerializer


class AssetCategorySerializer(serializers.ModelSerializer):
    """资产分类序列化器"""
    class Meta:
        model = 'assets.AssetCategory'
        fields = ['id', 'code', 'name', 'parent', 'level']


class SupplierSerializer(BaseModelSerializer):
    """供应商序列化器

    继承 BaseModelSerializer，自动序列化公共字段
    """
    class Meta(BaseModelSerializer.Meta):
        model = Supplier
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'contact', 'phone', 'email', 'address'
        ]


class LocationSerializer(BaseModelSerializer):
    """存放地点序列化器"""
    children = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = Location
        fields = BaseModelSerializer.Meta.fields + [
            'name', 'parent', 'path', 'level', 'location_type', 'children'
        ]

    def get_children(self, obj):
        """获取子地点"""
        if obj.children.exists():
            return LocationSerializer(obj.children.all(), many=True).data
        return []


class AssetStatusLogSerializer(BaseModelSerializer):
    """资产状态变更日志序列化器"""
    old_status_label = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_label = serializers.CharField(source='get_new_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetStatusLog
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'old_status', 'old_status_label',
            'new_status', 'new_status_label', 'reason'
        ]


class AssetListSerializer(BaseModelSerializer):
    """资产列表序列化器（轻量级）"""
    asset_category_name = serializers.CharField(source='asset_category.name', read_only=True)
    custodian_name = serializers.CharField(source='custodian.username', read_only=True)
    location_path = serializers.CharField(source='location.path', read_only=True)
    asset_status_label = serializers.CharField(source='get_asset_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'asset_category', 'asset_category_name',
            'specification', 'brand', 'model',
            'purchase_price', 'current_value', 'net_value',
            'department', 'custodian', 'custodian_name',
            'location', 'location_path',
            'asset_status', 'asset_status_label',
            'qr_code'
        ]


class AssetDetailSerializer(BaseModelWithAuditSerializer):
    """资产详情序列化器（完整版）

    继承 BaseModelWithAuditSerializer，包含完整审计字段
    """
    asset_category = AssetCategorySerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True, allow_null=True)
    department = DepartmentSerializer(read_only=True, allow_null=True)
    location = LocationSerializer(read_only=True, allow_null=True)
    custodian = UserSerializer(read_only=True, allow_null=True)
    user = UserSerializer(read_only=True, allow_null=True)
    asset_status_label = serializers.CharField(source='get_asset_status_display', read_only=True)
    status_logs = AssetStatusLogSerializer(many=True, read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = Asset
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'asset_category',
            'specification', 'brand', 'model', 'unit', 'serial_number',
            'purchase_price', 'current_value', 'accumulated_depreciation',
            'net_value', 'residual_value',
            'purchase_date', 'depreciation_start_date',
            'useful_life', 'residual_rate',
            'supplier', 'supplier_order_no', 'invoice_no',
            'department', 'location', 'custodian', 'user',
            'asset_status', 'asset_status_label',
            'qr_code', 'rfid_code', 'images', 'attachments', 'remarks',
            'status_logs'
        ]


class AssetSerializer(BaseModelSerializer):
    """资产创建/更新序列化器"""
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + [
            'asset_code', 'asset_name', 'asset_category',
            'specification', 'brand', 'model', 'unit', 'serial_number',
            'purchase_price', 'current_value', 'accumulated_depreciation',
            'purchase_date', 'depreciation_start_date',
            'useful_life', 'residual_rate',
            'supplier', 'supplier_order_no', 'invoice_no',
            'department', 'location', 'custodian', 'user',
            'asset_status',
            'qr_code', 'rfid_code', 'images', 'attachments', 'remarks'
        ]


class AssetStatusSerializer(serializers.Serializer):
    """资产状态变更序列化器"""
    status = serializers.ChoiceField(choices=Asset.ASSET_STATUS_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)
```

---

## 5. 服务层设计

```python
# apps/assets/services/asset_service.py

from typing import Dict, List, Optional
from django.db.models import Q, Count, Sum, Prefetch
from django.core.paginator import Paginator
from apps.assets.models import Asset, AssetStatusLog
from apps.common.services.base_crud import BaseCRUDService


class AssetService(BaseCRUDService):
    """
    资产服务 - 继承 BaseCRUDService

    自动获得：
    - create(data, user) - 创建资产（自动设置组织和创建人）
    - update(instance_id, data, user) - 更新资产
    - delete(instance_id, user) - 软删除资产
    - restore(instance_id) - 恢复已删除资产
    - get(instance_id) - 获取单条资产
    - query(filters, search, search_fields, order_by) - 查询资产
    - paginate(queryset, page, page_size) - 分页查询
    """

    def __init__(self):
        """初始化服务"""
        super().__init__(Asset)

    def create_asset(self, data: Dict, user) -> Asset:
        """
        创建资产（处理关联字段）

        Args:
            data: 资产数据
            user: 创建用户

        Returns:
            创建的资产实例
        """
        from apps.accounts.models import User
        from apps.assets.models import AssetCategory, Location

        # 处理关联字段
        if 'asset_category' in data:
            data['asset_category'] = AssetCategory.objects.get(id=data['asset_category'])

        if 'location' in data and data['location']:
            data['location'] = Location.objects.get(id=data['location'])

        if 'custodian' in data and data['custodian']:
            data['custodian'] = User.objects.get(id=data['custodian'])

        if 'department' in data and data['department']:
            from apps.organizations.models import Department
            data['department'] = Department.objects.get(id=data['department'])

        # 调用基类 create 方法（自动处理组织和创建人）
        return self.create(data, user)

    def update_asset(self, asset_id: int, data: Dict) -> Asset:
        """
        更新资产（处理关联字段）

        Args:
            asset_id: 资产ID
            data: 更新数据

        Returns:
            更新后的资产实例
        """
        # 处理关联字段
        if 'asset_category' in data:
            from apps.assets.models import AssetCategory
            data['asset_category'] = AssetCategory.objects.get(id=data['asset_category'])

        if 'location' in data:
            from apps.assets.models import Location
            if data['location']:
                data['location'] = Location.objects.get(id=data['location'])
            else:
                data['location'] = None

        if 'custodian' in data:
            from apps.accounts.models import User
            if data['custodian']:
                data['custodian'] = User.objects.get(id=data['custodian'])
            else:
                data['custodian'] = None

        # 调用基类 update 方法
        return self.update(asset_id, data)

    def query_assets(self, filters: Dict = None, search: str = None,
                    order_by: str = None, page: int = 1, page_size: int = 20) -> Dict:
        """
        查询资产列表

        Args:
            filters: 过滤条件
            search: 搜索关键词
            order_by: 排序字段
            page: 页码
            page_size: 每页数量

        Returns:
            分页结果
        """
        # 构建查询字段
        search_fields = ['asset_code', 'asset_name', 'serial_number']

        # 调用基类 query 方法（自动应用组织和软删除过滤）
        queryset = self.query(
            filters=filters,
            search=search,
            search_fields=search_fields,
            order_by=order_by or '-created_at'
        )

        # 优化查询（关联查询）
        queryset = queryset.select_related(
            'asset_category', 'custodian', 'location', 'department'
        )

        # 调用基类 paginate 方法
        return self.paginate(queryset, page, page_size)

    def change_status(self, asset_id: int, new_status: str, reason: str, user) -> Asset:
        """
        变更资产状态

        Args:
            asset_id: 资产ID
            new_status: 新状态
            reason: 变更原因
            user: 操作用户

        Returns:
            更新后的资产实例
        """
        asset = self.get(asset_id)

        # 记录原状态
        old_status = asset.asset_status

        # 更新状态
        asset.asset_status = new_status
        asset.save()

        # 记录状态变更日志
        AssetStatusLog.objects.create(
            asset=asset,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            created_by=user
        )

        return asset

    def get_statistics(self) -> Dict:
        """
        获取资产统计

        Returns:
            统计数据
        """
        qs = self.model_class.objects.filter(is_deleted=False)

        return {
            'total': qs.count(),
            'by_status': list(qs.values('asset_status').annotate(
                count=Count('id')
            ).order_by('-count')),
            'by_category': list(qs.values('asset_category__name').annotate(
                count=Count('id')
            ).order_by('-count')),
            'total_value': qs.aggregate(
                total=Sum('purchase_price')
            )['total'] or 0,
            'total_depreciation': qs.aggregate(
                total=Sum('accumulated_depreciation')
            )['total'] or 0,
        }

    def get_by_code(self, code: str) -> Optional[Asset]:
        """
        根据编码查询资产

        Args:
            code: 资产编码

        Returns:
            资产实例或None
        """
        try:
            return self.model_class.objects.get(asset_code=code)
        except Asset.DoesNotExist:
            return None

    def get_idle_assets(self, location_id: str = None):
        """
        获取闲置资产

        Args:
            location_id: 地点ID（可选）

        Returns:
            查询集
        """
        filters = {'asset_status': 'idle'}
        if location_id:
            filters['location_id'] = location_id
        return self.query(filters=filters)
```

---

## 6. 过滤器设计

```python
# apps/assets/filters.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.assets.models import Asset


class AssetFilter(BaseModelFilter):
    """
    资产过滤器 - 继承 BaseModelFilter

    自动获得：
    - created_at, created_at_from, created_at_to: 创建时间范围过滤
    - updated_at_from, updated_at_to: 更新时间范围过滤
    - created_by: 创建人过滤
    - is_deleted: 软删除状态过滤
    """

    # 资产基础字段过滤
    asset_code = filters.CharFilter(lookup_expr='icontains', label='资产编码')
    asset_name = filters.CharFilter(lookup_expr='icontains', label='资产名称')
    serial_number = filters.CharFilter(lookup_expr='icontains', label='序列号')

    # 关联字段过滤
    asset_category = filters.UUIDFilter(field_name='asset_category_id', label='资产分类')
    department = filters.UUIDFilter(field_name='department_id', label='使用部门')
    custodian = filters.UUIDFilter(field_name='custodian_id', label='保管人')
    location = filters.UUIDFilter(field_name='location_id', label='存放地点')
    supplier = filters.UUIDFilter(field_name='supplier_id', label='供应商')

    # 财务字段过滤
    purchase_price = filters.NumberFilter(field_name='purchase_price', label='购置原值')
    purchase_price_gte = filters.NumberFilter(
        field_name='purchase_price', lookup_expr='gte', label='购置原值(起始)'
    )
    purchase_price_lte = filters.NumberFilter(
        field_name='purchase_price', lookup_expr='lte', label='购置原值(结束)'
    )

    purchase_date_from = filters.DateFilter(
        field_name='purchase_date', lookup_expr='gte', label='购置日期(起始)'
    )
    purchase_date_to = filters.DateFilter(
        field_name='purchase_date', lookup_expr='lte', label='购置日期(结束)'
    )

    # 状态过滤
    asset_status = filters.ChoiceFilter(
        choices=Asset.ASSET_STATUS_CHOICES,
        label='资产状态'
    )

    class Meta(BaseModelFilter.Meta):
        model = Asset
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'asset_code', 'asset_name', 'serial_number',
            'asset_category', 'department', 'custodian', 'location', 'supplier',
            'purchase_price', 'purchase_price_gte', 'purchase_price_lte',
            'purchase_date_from', 'purchase_date_to',
            'asset_status'
        ]
```

---

## 7. API视图设计

```python
# apps/assets/views.py

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.assets.models import Asset
from apps.assets.serializers import (
    AssetListSerializer,
    AssetDetailSerializer,
    AssetSerializer,
    AssetStatusSerializer
)
from apps.assets.services.asset_service import AssetService
from apps.assets.filters import AssetFilter


class AssetViewSet(BaseModelViewSetWithBatch):
    """
    资产 ViewSet - 继承 BaseModelViewSetWithBatch

    自动获得：
    - 标准CRUD操作：list, retrieve, create, update, partial_update, destroy
    - 软删除：destroy() 自动调用 soft_delete()
    - 批量操作：batch_delete, batch_restore, batch_update
    - 已删除记录查询：deleted action
    - 恢复记录：restore action
    - 组织过滤：get_queryset() 自动应用组织过滤
    - 审计字段：perform_create/perform_update 自动设置created_by
    """

    queryset = Asset.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    filterset_class = AssetFilter

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = AssetService()

    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'list':
            return AssetListSerializer
        if self.action == 'retrieve':
            return AssetDetailSerializer
        return AssetSerializer

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        资产统计

        GET /api/assets/assets/statistics/
        """
        stats = self.service.get_statistics()
        return Response(stats)

    @action(detail=True, methods=['get'])
    def qr_code(self, request, id=None):
        """
        获取资产二维码图片

        GET /api/assets/assets/{id}/qr_code/
        """
        asset = self.get_object()
        from apps.assets.utils.qrcode import generate_qr_code

        image_buffer = generate_qr_code(asset.qr_code, asset.asset_code)
        return HttpResponse(image_buffer, content_type='image/png')

    @action(detail=True, methods=['post'])
    def change_status(self, request, id=None):
        """
        变更资产状态

        POST /api/assets/assets/{id}/change_status/
        {
            "status": "in_use",
            "reason": "领用投入使用"
        }
        """
        asset = self.get_object()
        serializer = AssetStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        asset = self.service.change_status(
            asset.id,
            serializer.validated_data['status'],
            serializer.validated_data.get('reason', ''),
            request.user
        )

        return Response({
            'status': asset.asset_status,
            'status_label': asset.get_status_label()
        })

    @action(detail=False, methods=['post'])
    def batch_change_status(self, request):
        """
        批量变更状态

        POST /api/assets/assets/batch_change_status/
        {
            "asset_ids": ["uuid1", "uuid2"],
            "status": "in_use",
            "reason": "批量启用"
        }
        """
        asset_ids = request.data.get('asset_ids', [])
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')

        results = []
        for asset_id in asset_ids:
            try:
                asset = self.service.change_status(asset_id, new_status, reason, request.user)
                results.append({'id': asset_id, 'success': True})
            except Exception as e:
                results.append({'id': asset_id, 'success': False, 'error': str(e)})

        return Response({'results': results})
```

---

## 8. URL配置

```python
# backend/config/urls.py

from rest_framework.routers import DefaultRouter
from apps.assets.views import AssetViewSet

router = DefaultRouter()
router.register(r'assets/assets', AssetViewSet, basename='asset')

urlpatterns = [
    # ... 其他路由
    path('api/', include(router.urls)),
]
```

---

## 9. 二维码工具

```python
# apps/assets/utils/qrcode.py

import io
from django.conf import settings


def generate_qr_code(qr_content: str, text: str = None) -> bytes:
    """
    生成二维码图片

    Args:
        qr_content: 二维码内容
        text: 显示文本（默认为qr_content）

    Returns:
        图片字节数据
    """
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # 添加文字
        if text:
            # 创建新图片（底部留白放文字）
            w, h = img.size
            new_img = Image.new('RGB', (w, h + 40), 'white')
            new_img.paste(img, (0, 0))

            draw = ImageDraw.Draw(new_img)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            position = ((w - text_width) // 2, h + 10)
            draw.text(position, text, fill='black', font=font)

            img = new_img

        # 转为字节
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()

    except ImportError:
        # 如果没有qrcode库，返回占位图
        from PIL import Image, ImageDraw

        img = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 190, 190], outline='black', width=2)
        draw.text((50, 90), "QR Code", fill='black')

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
```

---

## 10. 实施步骤

| 阶段 | 任务 | 状态 |
|------|------|------|
| 1 | 创建 Asset 数据模型（继承 BaseModel） | ✅ |
| 2 | 创建序列化器（继承 BaseModelSerializer） | ✅ |
| 3 | 创建 AssetService 服务层（继承 BaseCRUDService） | ✅ |
| 4 | 创建 AssetFilter 过滤器（继承 BaseModelFilter） | ✅ |
| 5 | 创建 AssetViewSet API视图（继承 BaseModelViewSetWithBatch） | ✅ |
| 6 | 实现二维码生成工具 | ✅ |
| 7 | 配置 URL 路由 | ✅ |
| 8 | 编写单元测试 | 待开发 |
| 9 | 编写API文档 | 待开发 |

---

## 11. 核心优势

### 11.1 使用公共基类的优势

通过使用公共基类，资产模块获得了以下开箱即用的功能：

#### 序列化器（BaseModelSerializer）
- ✅ 自动序列化所有公共字段（id, organization, created_at, updated_at, created_by, custom_fields等）
- ✅ 自动处理嵌套序列化（organization, created_by）
- ✅ 支持完整审计信息序列化（BaseModelWithAuditSerializer）

#### 服务层（BaseCRUDService）
- ✅ 自动处理组织隔离（通过 get_current_organization）
- ✅ 自动设置创建人信息
- ✅ 标准化 CRUD 操作（create, update, delete, restore, get, query, paginate）
- ✅ 支持复杂查询（搜索、过滤、排序、分页）
- ✅ 自动软删除

#### 视图层（BaseModelViewSetWithBatch）
- ✅ 自动应用组织过滤和软删除过滤
- ✅ 自动设置审计字段（创建人、更新人）
- ✅ 批量操作接口（batch_delete, batch_restore, batch_update）
- ✅ 软删除支持（perform_destroy）
- ✅ 已删除记录查询（deleted action）
- ✅ 恢复已删除记录（restore action）

#### 过滤器（BaseModelFilter）
- ✅ 公共字段过滤（创建时间范围、更新时间范围、创建人、软删除状态）
- ✅ 时间范围查询支持（DateFromToRangeFilter）
- ✅ 统一过滤接口

### 11.2 代码对比

#### 迁移前（旧代码）
```python
# 旧序列化器 - 需要手动定义所有字段
class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            'id', 'organization', 'is_deleted', 'deleted_at',
            'created_at', 'updated_at', 'created_by', 'custom_fields',
            'asset_code', 'asset_name', ...  # 需要手动列出所有字段
        ]

# 旧服务 - 需要手动处理组织、创建人
class AssetService:
    def create_asset(self, data, user):
        data['organization'] = get_current_organization()  # 手动处理
        data['created_by'] = user  # 手动处理
        return Asset.objects.create(**data)
```

#### 迁移后（新代码）
```python
# 新序列化器 - 自动继承公共字段
class AssetSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + [
            'asset_code', 'asset_name', ...  # 只需定义业务字段
        ]

# 新服务 - 自动处理组织、创建人
class AssetService(BaseCRUDService):
    def __init__(self):
        super().__init__(Asset)  # 自动获得所有 CRUD 功能

    def create_asset(self, data, user):
        return self.create(data, user)  # 基类自动处理组织和创建人
```

---

## 12. 输出产物

| 文件 | 说明 | 继承关系 |
|------|------|---------|
| `apps/assets/models.py` | Asset 模型 | BaseModel |
| `apps/assets/serializers.py` | 资产序列化器 | BaseModelSerializer / BaseModelWithAuditSerializer |
| `apps/assets/services/asset_service.py` | 资产服务 | BaseCRUDService |
| `apps/assets/filters.py` | 资产过滤器 | BaseModelFilter |
| `apps/assets/views.py` | 资产API | BaseModelViewSetWithBatch |
| `apps/assets/utils/qrcode.py` | 二维码工具 | 无 |
| `backend/config/urls.py` | 路由配置 | 无 |

---

## 13. 迁移检查清单

- [x] AssetSerializer 继承 BaseModelSerializer
- [x] AssetDetailSerializer 继承 BaseModelWithAuditSerializer
- [x] AssetService 继承 BaseCRUDService
- [x] AssetFilter 继承 BaseModelFilter
- [x] AssetViewSet 继承 BaseModelViewSetWithBatch
- [x] 移除重复的公共字段定义
- [x] 使用基类的 CRUD 方法
- [x] 配置 filterset_class
- [x] 测试组织隔离功能
- [x] 测试软删除功能
- [x] 测试批量操作功能
- [ ] 单元测试覆盖
- [ ] API文档完善

---

## 14. API接口规范

### 14.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "ZC2026010001",
        "name": "办公笔记本",
        ...
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/assets/assets/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "ZC2026010001",
                "name": "办公笔记本",
                ...
            }
        ]
    }
}
```

#### 错误响应格式
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "asset_name": ["该字段不能为空"],
            "purchase_price": ["请输入有效的金额"]
        }
    }
}
```

### 14.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **列表查询** | GET | `/api/assets/assets/` | 分页查询资产列表，支持过滤和搜索 |
| **详情查询** | GET | `/api/assets/assets/{id}/` | 获取单个资产详情信息 |
| **创建资产** | POST | `/api/assets/assets/` | 创建新资产 |
| **更新资产** | PUT | `/api/assets/assets/{id}/` | 完整更新资产信息 |
| **部分更新** | PATCH | `/api/assets/assets/{id}/` | 部分更新资产信息 |
| **软删除** | DELETE | `/api/assets/assets/{id}/` | 软删除资产（标记为已删除） |
| **已删除列表** | GET | `/api/assets/assets/deleted/` | 查询已删除的资产列表 |
| **恢复资产** | POST | `/api/assets/assets/{id}/restore/` | 恢复已删除的资产 |

### 14.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量删除** | POST | `/api/assets/assets/batch-delete/` | 批量软删除多个资产 |
| **批量恢复** | POST | `/api/assets/assets/batch-restore/` | 批量恢复多个已删除的资产 |
| **批量更新** | POST | `/api/assets/assets/batch-update/` | 批量更新资产字段 |

**批量删除请求格式**：
```json
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 14.4 标准错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 14.5 扩展接口

#### 资产统计接口
```http
GET /api/assets/assets/statistics/
```

**响应格式**：
```json
{
    "success": true,
    "data": {
        "total": 1000,
        "by_status": [
            {"asset_status": "in_use", "count": 800},
            {"asset_status": "idle", "count": 150},
            ...
        ],
        "by_category": [
            {"category": "电子产品", "count": 500},
            ...
        ],
        "total_value": "5000000.00",
        "total_depreciation": "1000000.00"
    }
}
```

#### 二维码生成接口
```http
GET /api/assets/assets/{id}/qr_code/
```

#### 状态变更接口
```http
POST /api/assets/assets/{id}/change_status/
```

**请求体**：
```json
{
    "status": "in_use",
    "reason": "领用投入使用"
}
```

#### 批量状态变更接口
```http
POST /api/assets/assets/batch_change_status/
```

**请求体**：
```json
{
    "asset_ids": ["uuid1", "uuid2"],
    "status": "in_use",
    "reason": "批量启用"
}
```

---

## 15. API接口规范

### 15.1 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 15.1.1 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 15.1.2 列表响应
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

#### 15.1.3 错误响应
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

### 15.2 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |

**版本**: 1.0.0
**更新日期**: 2026-01-15
**维护人**: GZEAMS 开发团队
