# Phase 4.5: 盘点业务链条 - 后端实现 (去耦合版 + 公共基类)

> **架构变更说明**: 本模块已进行"去耦合"重构，将硬编码的审批逻辑移除，改为调用工作流引擎。
> 核心设计原则: **业务代码只管"干活"，流程引擎负责"指挥"**。
>
> **基类使用说明**: 本模块所有代码已更新为继承公共基类，详见 [Common Base Features](../common_base_features/backend.md)。
> 核心基类: **BaseModelSerializer + BaseModelViewSetWithBatch + BaseCRUDService + BaseModelFilter**。

---

## 概述

盘点对账模块的核心业务逻辑：
1. **差异分析** - 发现盘点差异
2. **差异认定** - 确认差异和责任人
3. **流程审批** - 通过 BPMN 工作流引擎处理（**不在本模块硬编码**）
4. **执行处理** - 根据审批结果执行调账/报损等操作

### 基类使用总览

| 组件类型 | 基类 | 说明 |
|---------|------|------|
| 序列化器 | `BaseModelSerializer` | 自动处理公共字段、组织、软删除、审计信息 |
| 视图集 | `BaseModelViewSetWithBatch` | 自动组织隔离、软删除、批量操作 |
| 服务类 | `BaseCRUDService` | 提供 CRUD 方法、组织过滤、分页 |
| 过滤器 | `BaseModelFilter` | 支持时间范围、用户、状态过滤 |

### 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                  业务层 (Business Layer)                    │
│  - DifferenceAnalysisService: 分析差异                       │
│  - DifferenceConfirmationService: 认定差异                  │
│  - AssetAdjustmentService: 执行调账                         │
└───────────────────────────┬─────────────────────────────────┘
                            │ 启动流程
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               工作流引擎 (Workflow Engine)                   │
│  - SpiffWorkflow 执行 BPMN 流程                             │
│  - 条件判断由网关处理 (${amount} > 10000)                   │
│  - 审批人由 BPMN 定义，不写死在代码里                         │
└───────────────────────────┬─────────────────────────────────┘
                            │ 回调
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              回调处理器 (Callback Handlers)                  │
│  - on_workflow_approved: 审批通过后执行                     │
│  - on_workflow_rejected: 审批拒绝后处理                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 公共模型引用声明

本模块所有组件严格遵循 GZEAMS 公共基类规范，所有后端组件均继承相应的基类以获得标准功能。

### 基类引用表

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离（org字段）、软删除（is_deleted+deleted_at）、审计字段（created_at+updated_at+created_by）、动态字段（custom_fields JSONB） |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields自动处理、created_by用户信息嵌入 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除过滤、审计字段自动设置、批量操作（/batch-delete/、/batch-restore/、/batch-update/） |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离、复杂查询、分页支持 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤（时间范围、用户、组织） |

### 核心模型继承关系

```python
# 盘点差异模型
class InventoryDifference(BaseModel):
    """盘点差异记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    task = models.ForeignKey('inventory.InventoryTask', ...)
    difference_type = models.CharField(...)  # surplus/loss/location_mismatch/status_mismatch/value_mismatch
    status = models.CharField(...)  # pending/confirmed/processing/approved/rejected/resolved
    asset = models.ForeignKey('assets.Asset', ...)
    account_location = models.ForeignKey(...)
    actual_location = models.ForeignKey(...)
    process_instance_id = models.CharField(...)  # 工作流实例ID（BPMN）
    confirmed_by = models.ForeignKey(...)  # 认定人
    confirmed_at = models.DateTimeField(...)  # 认定时间
    confirmed_note = models.TextField(...)  # 认定意见

# 差异处理模型
class DifferenceResolution(BaseModel):
    """差异处理记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    resolution_no = models.CharField(unique=True)
    difference = models.ForeignKey('InventoryDifference', ...)
    action = models.CharField(...)  # adjust_account/adjust_asset/record_asset/write_off/pending
    status = models.CharField(...)  # draft/submitted/approved/rejected/executing/completed/failed
    process_instance_id = models.CharField(...)  # 工作流实例ID
    approved_by = models.ForeignKey(...)  # 审批人
    approved_at = models.DateTimeField(...)  # 审批时间
    executed_by = models.ForeignKey(...)  # 执行人
    executed_at = models.DateTimeField(...)  # 执行时间

# 资产调账模型
class AssetAdjustment(BaseModel):
    """资产调账记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    adjustment_no = models.CharField(unique=True)
    resolution = models.ForeignKey('DifferenceResolution', ...)
    asset = models.ForeignKey('assets.Asset', ...)
    adjustment_type = models.CharField(...)  # location/status/value/info/new/remove
    status = models.CharField(...)  # pending/executing/completed/failed/rolled_back
    before_value = models.JSONField(...)  # 调账前值
    after_value = models.JSONField(...)  # 调账后值
    executed_by = models.ForeignKey(...)  # 执行人
    executed_at = models.DateTimeField(...)  # 执行时间

# 盘点报告模型
class InventoryReport(BaseModel):
    """盘点报告"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    report_no = models.CharField(unique=True)
    task = models.OneToOneField('inventory.InventoryTask', ...)
    status = models.CharField(...)  # draft/pending_approval/approved/rejected
    report_data = models.JSONField(...)  # JSON结构化报告内容
    generated_by = models.ForeignKey(...)  # 生成人
    generated_at = models.DateTimeField(...)  # 生成时间
```

### 序列化器继承关系

```python
# 所有序列化器必须继承 BaseModelSerializer
class InventoryDifferenceSerializer(BaseModelSerializer):
    """盘点差异序列化器"""
    # 继承BaseModelSerializer获得所有公共字段
    class Meta(BaseModelSerializer.Meta):
        model = InventoryDifference
        fields = BaseModelSerializer.Meta.fields + [
            'task', 'difference_type', 'status', 'asset',
            'account_location', 'actual_location', 'process_instance_id',
            'confirmed_by', 'confirmed_at', 'confirmed_note'
        ]

class DifferenceResolutionSerializer(BaseModelSerializer):
    """差异处理序列化器"""
    # 继承BaseModelSerializer获得所有公共字段

class AssetAdjustmentSerializer(BaseModelSerializer):
    """资产调账序列化器"""
    # 继承BaseModelSerializer获得所有公共字段

class InventoryReportSerializer(BaseModelSerializer):
    """盘点报告序列化器"""
    # 继承BaseModelSerializer获得所有公共字段
```

### 服务层继承关系

```python
# 服务类必须继承 BaseCRUDService
class DifferenceAnalysisService(BaseCRUDService):
    """差异分析服务"""
    def __init__(self):
        super().__init__(InventoryDifference)
        # 自动获得：create(), update(), delete(), restore(), get(), query(), paginate()

class DifferenceConfirmationService(BaseCRUDService):
    """差异认定服务"""
    # 继承BaseCRUDService获得所有CRUD方法

class DifferenceResolutionService(BaseCRUDService):
    """差异处理服务"""
    # 继承BaseCRUDService获得所有CRUD方法
    # 集成工作流引擎进行审批流程管理
    def start_workflow(self, resolution):
        """启动工作流审批流程"""
        pass

class AssetAdjustmentService(BaseCRUDService):
    """资产调账服务"""
    # 继承BaseCRUDService获得所有CRUD方法
    # 执行资产信息更新操作
```

### ViewSet继承关系

```python
# 所有ViewSet必须继承 BaseModelViewSetWithBatch
class InventoryDifferenceViewSet(BaseModelViewSetWithBatch):
    """盘点差异API"""
    serializer_class = InventoryDifferenceSerializer
    # 自动获得：组织过滤、软删除、审计字段、批量操作

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """认定差异"""
        pass

    @action(detail=True, methods=['post'])
    def start_resolution(self, request, pk=None):
        """启动处理流程"""
        pass

class DifferenceResolutionViewSet(BaseModelViewSetWithBatch):
    """差异处理API"""
    # 自动获得所有公共功能

class AssetAdjustmentViewSet(BaseModelViewSetWithBatch):
    """资产调账API"""
    # 自动获得所有公共功能

class InventoryReportViewSet(BaseModelViewSetWithBatch):
    """盘点报告API"""
    # 自动获得所有公共功能

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批报告"""
        pass
```

### 过滤器继承关系

```python
# 所有过滤器必须继承 BaseModelFilter
class InventoryDifferenceFilter(BaseModelFilter):
    """盘点差异过滤器"""
    difference_type = filters.ChoiceFilter(choices=[...])
    status = filters.ChoiceFilter(choices=[...])
    # 自动继承：created_at, updated_at, created_by, is_deleted 等过滤

    class Meta(BaseModelFilter.Meta):
        model = InventoryDifference
        fields = BaseModelFilter.Meta.fields + ['task', 'difference_type', 'status']
```

---

## 数据模型设计

### 1. 盘点差异 (InventoryDifference)

```python
# apps/inventory/models.py

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class InventoryDifference(BaseModel):
    """
    盘点差异

    记录盘点过程中发现的账实不符情况
    """
    TYPE_CHOICES = [
        ('surplus', '盘盈'),           # 实物有但账面无
        ('loss', '盘亏'),              # 账面有但实物无
        ('location_mismatch', '位置不符'),  # 实物位置与账面不符
        ('status_mismatch', '状态不符'),    # 实物状态与账面不符
        ('value_mismatch', '价值不符'),     # 实物价值与账面不符
    ]

    STATUS_CHOICES = [
        ('pending', '待认定'),
        ('confirmed', '已认定'),
        ('processing', '处理中'),
        ('approved', '已批准'),
        ('rejected', '已驳回'),
        ('resolved', '已解决'),
    ]

    # 关联盘点任务
    task = models.ForeignKey(
        'inventory.InventoryTask',
        on_delete=models.CASCADE,
        related_name='differences',
        verbose_name='盘点任务'
    )

    # 差异信息
    difference_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='差异类型'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态'
    )

    # 资产信息
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_differences',
        verbose_name='资产'
    )

    # 账面信息（快照数据）
    account_location = models.ForeignKey(
        'organizations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='account_differences',
        verbose_name='账面位置'
    )
    account_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='账面状态'
    )
    account_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='账面价值'
    )

    # 实物信息（扫描数据）
    actual_location = models.ForeignKey(
        'organizations.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actual_differences',
        verbose_name='实物位置'
    )
    actual_status = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='实物状态'
    )
    actual_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='实物价值'
    )

    # 差异描述
    description = models.TextField(verbose_name='差异描述')

    # 认定信息
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_differences',
        verbose_name='认定人'
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='认定时间'
    )
    confirmation_note = models.TextField(
        null=True,
        blank=True,
        verbose_name='认定意见'
    )

    # 责任信息
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_differences',
        verbose_name='责任人'
    )
    responsible_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_differences',
        verbose_name='责任部门'
    )

    # 关联的流程实例 (新增 - 指向工作流引擎)
    process_instance_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='流程实例ID',
        help_text='工作流引擎中的流程实例标识'
    )

    # 关联的调账记录
    adjustment = models.ForeignKey(
        'AssetAdjustment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='differences',
        verbose_name='调账记录'
    )

    # 自定义字段
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='自定义字段'
    )

    class Meta:
        db_table = 'inventory_difference'
        verbose_name = '盘点差异'
        verbose_name_plural = '盘点差异'
        ordering = ['task', '-created_at']
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['difference_type']),
            models.Index(fields=['status']),
            models.Index(fields=['asset']),
            models.Index(fields=['responsible_user']),
        ]

    def __str__(self):
        return f"{self.task.task_no} - {self.get_difference_type_display()}"
```

### 2. 差异处理 (DifferenceResolution)

```python
class DifferenceResolution(BaseModel):
    """
    差异处理

    记录盘点差异的处理方案
    注意: 审批流程由工作流引擎管理，本模型仅存储最终结果
    """
    ACTION_CHOICES = [
        ('adjust_account', '调整账面'),      # 更新账面信息以匹配实物
        ('adjust_asset', '调整实物'),        # 将实物移到账面位置
        ('record_asset', '补录资产'),        # 盘盈资产补录
        ('write_off', '资产报损'),           # 盘亏资产报损
        ('pending', '待处理'),               # 暂时挂账，后续处理
        ('no_action', '无需处理'),           # 确认无问题
    ]

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已批准'),
        ('rejected', '已驳回'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('failed', '执行失败'),
    ]

    # 基本信息
    resolution_no = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='处理单号'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )

    # 关联任务
    task = models.ForeignKey(
        'inventory.InventoryTask',
        on_delete=models.CASCADE,
        related_name='resolutions',
        verbose_name='盘点任务'
    )

    # 处理方案
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='处理方式'
    )
    description = models.TextField(verbose_name='处理说明')

    # 申请人信息
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='applied_resolutions',
        verbose_name='申请人'
    )
    application_date = models.DateField(verbose_name='申请日期')

    # ─── 删除以下字段 (由工作流引擎管理) ───
    # current_approver: 删除 - 引擎动态持有
    # approved_at: 删除 - 从流程实例获取
    # approved_by: 删除 - 从流程实例的审批链获取
    # approval_note: 删除 - 存储在流程日志中
    # ──────────────────────────────────────────

    # 新增: 关联流程实例 (指向工作流引擎)
    process_instance_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='流程实例ID',
        help_text='工作流引擎中的流程实例标识'
    )

    # 保留: 最终审批结果 (由引擎回调时写入)
    final_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='final_approved_resolutions',
        verbose_name='最终审批人'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='审批通过时间'
    )

    # 执行信息
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_resolutions',
        verbose_name='执行人'
    )
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='执行时间'
    )
    execution_note = models.TextField(
        null=True,
        blank=True,
        verbose_name='执行说明'
    )

    # 自定义字段
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='自定义字段'
    )

    class Meta:
        db_table = 'inventory_difference_resolution'
        verbose_name = '差异处理'
        verbose_name_plural = '差异处理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['resolution_no']),
            models.Index(fields=['task']),
            models.Index(fields=['status']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.resolution_no} - {self.get_action_display()}"
```

### 3. 资产调账 (AssetAdjustment)

```python
class AssetAdjustment(BaseModel):
    """
    资产调账

    记录因盘点差异导致的资产信息调整
    """
    TYPE_CHOICES = [
        ('location', '位置调整'),
        ('status', '状态调整'),
        ('value', '价值调整'),
        ('info', '信息调整'),
        ('new', '新增资产'),
        ('remove', '资产删除'),
    ]

    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('failed', '执行失败'),
        ('rolled_back', '已回滚'),
    ]

    # 基本信息
    adjustment_no = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='调账单号'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='状态'
    )

    # 关联信息
    resolution = models.ForeignKey(
        'DifferenceResolution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjustments',
        verbose_name='差异处理'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjustments',
        verbose_name='资产'
    )

    # 调账类型
    adjustment_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='调账类型'
    )

    # 调账前值（JSON存储，支持各种字段）
    before_value = models.JSONField(
        default=dict,
        verbose_name='调账前值'
    )
    # 调账后值
    after_value = models.JSONField(
        default=dict,
        verbose_name='调账后值'
    )

    # 变更说明
    change_description = models.TextField(verbose_name='变更说明')

    # 执行信息
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executed_adjustments',
        verbose_name='执行人'
    )
    executed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='执行时间'
    )

    # 回滚信息
    rolled_back_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rolled_back_adjustments',
        verbose_name='回滚人'
    )
    rolled_back_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='回滚时间'
    )
    rollback_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name='回滚原因'
    )

    # 自定义字段
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='自定义字段'
    )

    class Meta:
        db_table = 'inventory_asset_adjustment'
        verbose_name = '资产调账'
        verbose_name_plural = '资产调账'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['adjustment_no']),
            models.Index(fields=['status']),
            models.Index(fields=['asset']),
            models.Index(fields=['adjustment_type']),
        ]

    def __str__(self):
        return f"{self.adjustment_no} - {self.get_adjustment_type_display()}"
```

---

## 序列化器设计 (使用 BaseModelSerializer)

### 1. 盘点差异序列化器

```python
# apps/inventory/serializers.py

from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.inventory.models import InventoryDifference, DifferenceResolution, AssetAdjustment
from apps.assets.serializers import AssetSerializer
from apps.organizations.serializers import LocationSerializer, DepartmentSerializer


class InventoryDifferenceSerializer(BaseModelSerializer):
    """盘点差异序列化器"""

    # 关联对象
    asset = AssetSerializer(read_only=True, allow_null=True)
    account_location = LocationSerializer(read_only=True, allow_null=True)
    actual_location = LocationSerializer(read_only=True, allow_null=True)
    responsible_user_id = serializers.UUIDField(allow_null=True, required=False)
    responsible_department = DepartmentSerializer(read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryDifference
        fields = BaseModelSerializer.Meta.fields + [
            'task', 'difference_type', 'status',
            'asset', 'account_location', 'account_status', 'account_value',
            'actual_location', 'actual_status', 'actual_value',
            'description', 'confirmed_by', 'confirmed_at', 'confirmation_note',
            'responsible_user', 'responsible_department',
            'process_instance_id', 'adjustment',
        ]


class InventoryDifferenceDetailSerializer(BaseModelWithAuditSerializer):
    """盘点差异详情序列化器 - 包含完整审计信息"""

    asset = AssetSerializer(read_only=True, allow_null=True)
    account_location = LocationSerializer(read_only=True, allow_null=True)
    actual_location = LocationSerializer(read_only=True, allow_null=True)
    responsible_department = DepartmentSerializer(read_only=True, allow_null=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = InventoryDifference
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'task', 'difference_type', 'status',
            'asset', 'account_location', 'account_status', 'account_value',
            'actual_location', 'actual_status', 'actual_value',
            'description', 'confirmed_by', 'confirmed_at', 'confirmation_note',
            'responsible_user', 'responsible_department',
            'process_instance_id', 'adjustment',
        ]
```

### 2. 差异处理序列化器

```python
class DifferenceResolutionSerializer(BaseModelSerializer):
    """差异处理序列化器"""

    task_name = serializers.CharField(source='task.task_name', read_only=True)
    applicant_name = serializers.CharField(source='applicant.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = DifferenceResolution
        fields = BaseModelSerializer.Meta.fields + [
            'resolution_no', 'status', 'task', 'task_name',
            'action', 'description',
            'applicant', 'applicant_name', 'application_date',
            'process_instance_id',
            'final_approver', 'approved_at',
            'executor', 'executed_at', 'execution_note',
        ]


class DifferenceResolutionDetailSerializer(BaseModelWithAuditSerializer):
    """差异处理详情序列化器"""

    differences = InventoryDifferenceSerializer(
        many=True, read_only=True, source='differences'
    )

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = DifferenceResolution
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'resolution_no', 'status', 'task', 'task_name',
            'action', 'description',
            'applicant', 'applicant_name', 'application_date',
            'process_instance_id',
            'final_approver', 'approved_at',
            'executor', 'executed_at', 'execution_note',
            'differences',  # 嵌套差异列表
        ]
```

### 3. 资产调账序列化器

```python
class AssetAdjustmentSerializer(BaseModelSerializer):
    """资产调账序列化器"""

    asset_code = serializers.CharField(source='asset.code', read_only=True)
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    executor_name = serializers.CharField(source='executor.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetAdjustment
        fields = BaseModelSerializer.Meta.fields + [
            'adjustment_no', 'status',
            'resolution', 'asset', 'asset_code', 'asset_name',
            'adjustment_type',
            'before_value', 'after_value',
            'change_description',
            'executed_by', 'executed_at', 'executor_name',
            'rolled_back_by', 'rolled_back_at', 'rollback_reason',
        ]
```

---

## 视图层设计 (使用 BaseModelViewSetWithBatch)

### 1. 盘点差异视图集

```python
# apps/inventory/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.inventory.models import InventoryDifference
from apps.inventory.serializers import (
    InventoryDifferenceSerializer,
    InventoryDifferenceDetailSerializer
)
from apps.inventory.services.difference_service import DifferenceConfirmationService
from apps.inventory.filters import InventoryDifferenceFilter


class InventoryDifferenceViewSet(BaseModelViewSetWithBatch):
    """
    盘点差异 ViewSet

    自动获得:
    - 组织隔离
    - 软删除过滤
    - 批量删除/恢复/更新
    - 已删除列表查询
    """
    queryset = InventoryDifference.objects.all()
    serializer_class = InventoryDifferenceSerializer
    filterset_class = InventoryDifferenceFilter
    search_fields = ['asset__code', 'asset__name', 'description']

    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return InventoryDifferenceDetailSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        确认差异

        POST /api/inventory/differences/{id}/confirm/
        {
            "confirmation_note": "差异属实",
            "responsible_user_id": "uuid",
            "responsible_department_id": "uuid"
        }
        """
        difference = self.get_object()
        confirmed_difference = DifferenceConfirmationService.confirm_difference(
            difference.id,
            request.user,
            request.data
        )
        serializer = self.get_serializer(confirmed_difference)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def batch_confirm(self, request):
        """
        批量确认差异

        POST /api/inventory/differences/batch-confirm/
        {
            "ids": ["uuid1", "uuid2", "uuid3"],
            "confirmation_note": "批量认定",
            "responsible_user_id": "uuid",
            "responsible_department_id": "uuid"
        }
        """
        ids = request.data.get('ids', [])
        count = DifferenceConfirmationService.batch_confirm(
            ids,
            request.user,
            request.data
        )
        return Response({
            'success': True,
            'message': f'已成功认定 {count} 条差异',
            'count': count
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        差异统计

        GET /api/inventory/differences/statistics/?task_id=uuid
        """
        task_id = request.query_params.get('task_id')
        queryset = self.filter_queryset(self.get_queryset())

        if task_id:
            queryset = queryset.filter(task_id=task_id)

        stats = {
            'total': queryset.count(),
            'pending': queryset.filter(status='pending').count(),
            'confirmed': queryset.filter(status='confirmed').count(),
            'processing': queryset.filter(status='processing').count(),
            'resolved': queryset.filter(status='resolved').count(),
            'by_type': {
                'surplus': queryset.filter(difference_type='surplus').count(),
                'loss': queryset.filter(difference_type='loss').count(),
                'location_mismatch': queryset.filter(difference_type='location_mismatch').count(),
                'status_mismatch': queryset.filter(difference_type='status_mismatch').count(),
            }
        }
        return Response(stats)
```

### 2. 差异处理视图集

```python
class DifferenceResolutionViewSet(BaseModelViewSetWithBatch):
    """
    差异处理 ViewSet

    自动获得:
    - 组织隔离
    - 软删除过滤
    - 批量删除/恢复/更新
    - 已删除列表查询
    """
    queryset = DifferenceResolution.objects.all()
    serializer_class = DifferenceResolutionSerializer
    filterset_class = DifferenceResolutionFilter
    search_fields = ['resolution_no', 'description']

    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return DifferenceResolutionDetailSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """创建时自动设置申请人"""
        serializer.save(
            applicant=self.request.user,
            application_date=timezone.now().date()
        )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """
        提交审批

        POST /api/inventory/resolutions/{id}/submit/

        提交后会启动工作流流程，由 BPMN 定义审批路径
        """
        resolution = self.get_object()
        result = DifferenceResolutionService.submit_resolution(
            resolution.id,
            request.user
        )
        return Response(result)

    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """
        手动执行处理（仅限已批准状态）

        POST /api/inventory/resolutions/{id}/execute/
        """
        resolution = self.get_object()

        if resolution.status != 'approved':
            return Response(
                {'detail': '只有已批准的处理单才能执行'},
                status=status.HTTP_400_BAD_REQUEST
            )

        DifferenceResolutionService.execute_resolution(resolution)
        serializer = self.get_serializer(resolution)
        return Response(serializer.data)
```

### 3. 资产调账视图集

```python
class AssetAdjustmentViewSet(BaseModelViewSetWithBatch):
    """
    资产调账 ViewSet

    自动获得:
    - 组织隔离
    - 软删除过滤
    - 批量删除/恢复/更新
    - 已删除列表查询
    """
    queryset = AssetAdjustment.objects.all()
    serializer_class = AssetAdjustmentSerializer
    filterset_class = AssetAdjustmentFilter
    search_fields = ['adjustment_no', 'change_description']

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """
        回滚调账

        POST /api/inventory/adjustments/{id}/rollback/
        {
            "rollback_reason": "调账错误，需要回滚"
        }
        """
        adjustment = self.get_object()

        if adjustment.status != 'completed':
            return Response(
                {'detail': '只有已完成的调账才能回滚'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.inventory.services.adjustment_service import AssetAdjustmentService
        AssetAdjustmentService.rollback_adjustment(
            adjustment,
            request.user,
            request.data.get('rollback_reason')
        )

        serializer = self.get_serializer(adjustment)
        return Response(serializer.data)
```

---

## 过滤器设计 (使用 BaseModelFilter)

### 1. 盘点差异过滤器

```python
# apps/inventory/filters.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventoryDifference


class InventoryDifferenceFilter(BaseModelFilter):
    """盘点差异过滤器 - 继承公共过滤字段"""

    # 业务字段过滤
    task = filters.UUIDFilter(field_name='task_id', label='盘点任务')
    difference_type = filters.ChoiceFilter(
        choices=InventoryDifference.TYPE_CHOICES,
        label='差异类型'
    )
    status = filters.ChoiceFilter(
        choices=InventoryDifference.STATUS_CHOICES,
        label='状态'
    )
    asset = filters.UUIDFilter(field_name='asset_id', label='资产')
    responsible_user = filters.UUIDFilter(
        field_name='responsible_user_id',
        label='责任人'
    )

    # 范围过滤
    account_value = filters.NumberFilter(field_name='account_value', label='账面价值')
    account_value_gte = filters.NumberFilter(
        field_name='account_value',
        lookup_expr='gte',
        label='账面价值≥'
    )
    account_value_lte = filters.NumberFilter(
        field_name='account_value',
        lookup_expr='lte',
        label='账面价值≤'
    )

    class Meta(BaseModelFilter.Meta):
        model = InventoryDifference
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'task', 'difference_type', 'status',
            'asset', 'responsible_user',
            'account_value', 'account_value_gte', 'account_value_lte',
        ]
```

### 2. 差异处理过滤器

```python
class DifferenceResolutionFilter(BaseModelFilter):
    """差异处理过滤器 - 继承公共过滤字段"""

    task = filters.UUIDFilter(field_name='task_id', label='盘点任务')
    action = filters.ChoiceFilter(
        choices=DifferenceResolution.ACTION_CHOICES,
        label='处理方式'
    )
    status = filters.ChoiceFilter(
        choices=DifferenceResolution.STATUS_CHOICES,
        label='状态'
    )
    applicant = filters.UUIDFilter(field_name='applicant_id', label='申请人')

    # 时间范围过滤
    application_date = filters.DateFilter(field_name='application_date', label='申请日期')
    application_date_from = filters.DateFilter(
        field_name='application_date',
        lookup_expr='gte',
        label='申请日期（起始）'
    )
    application_date_to = filters.DateFilter(
        field_name='application_date',
        lookup_expr='lte',
        label='申请日期（结束）'
    )

    class Meta(BaseModelFilter.Meta):
        model = DifferenceResolution
        fields = BaseModelFilter.Meta.fields + [
            'task', 'action', 'status', 'applicant',
            'application_date', 'application_date_from', 'application_date_to',
        ]
```

### 3. 资产调账过滤器

```python
class AssetAdjustmentFilter(BaseModelFilter):
    """资产调账过滤器 - 继承公共过滤字段"""

    resolution = filters.UUIDFilter(field_name='resolution_id', label='差异处理')
    asset = filters.UUIDFilter(field_name='asset_id', label='资产')
    adjustment_type = filters.ChoiceFilter(
        choices=AssetAdjustment.TYPE_CHOICES,
        label='调账类型'
    )
    status = filters.ChoiceFilter(
        choices=AssetAdjustment.STATUS_CHOICES,
        label='状态'
    )

    class Meta(BaseModelFilter.Meta):
        model = AssetAdjustment
        fields = BaseModelFilter.Meta.fields + [
            'resolution', 'asset', 'adjustment_type', 'status',
        ]
```

---

## 服务层设计 (继承 BaseCRUDService + 去耦合版)

### 1. 差异分析服务 (继承 BaseCRUDService)

```python
# apps/inventory/services/difference_service.py

from typing import List, Optional
from django.db import transaction
from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import (
    InventoryTask, InventorySnapshot, InventorySnapshotItem,
    InventoryDifference, ScanRecord
)
from apps.assets.models import Asset


class DifferenceAnalysisService(BaseCRUDService):
    """
    差异分析服务 - 继承 BaseCRUDService

    自动获得:
    - create(), update(), delete(), get(), query(), paginate()
    - 组织过滤和软删除支持
    """

    def __init__(self):
        """初始化服务，绑定模型"""
        super().__init__(InventoryDifference)

    @staticmethod
    @transaction.atomic
    def analyze_task_differences(task_id: int) -> List[InventoryDifference]:
        """分析盘点任务差异"""
        task = InventoryTask.objects.get(id=task_id)

        # 获取快照数据
        snapshot = InventorySnapshot.objects.get(task=task)
        snapshot_items = snapshot.items.all()

        # 获取扫描记录
        scan_records = ScanRecord.objects.filter(task=task).values(
            'asset_id', 'location_id', 'scan_time'
        )

        # 构建扫描数据映射
        scanned_assets = {r['asset_id']: r for r in scan_records}

        differences = []

        # 1. 检查盘亏（账面有但未扫描）
        for snapshot_item in snapshot_items:
            if snapshot_item.asset_id not in scanned_assets:
                diff = DifferenceAnalysisService._create_loss_difference(snapshot_item)
                differences.append(diff)

        # 2. 检查盘盈（扫描有但账面无）
        scanned_asset_ids = set(scanned_assets.keys())
        snapshot_asset_ids = set(item.asset_id for item in snapshot_items)

        surplus_ids = scanned_asset_ids - snapshot_asset_ids
        for asset_id in surplus_ids:
            scan_record = scanned_assets[asset_id]
            diff = DifferenceAnalysisService._create_surplus_difference(task, scan_record)
            differences.append(diff)

        # 3. 检查位置/状态不符
        for snapshot_item in snapshot_items:
            if snapshot_item.asset_id in scanned_assets:
                scan_record = scanned_assets[snapshot_item.asset_id]
                diff = DifferenceAnalysisService._check_mismatch(snapshot_item, scan_record)
                if diff:
                    differences.append(diff)

        return differences

    @staticmethod
    def _create_loss_difference(snapshot_item: InventorySnapshotItem) -> InventoryDifference:
        """创建盘亏差异"""
        return InventoryDifference.objects.create(
            task=snapshot_item.snapshot.task,
            snapshot_item=snapshot_item,
            difference_type='loss',
            status='pending',
            asset=snapshot_item.asset,
            account_location=snapshot_item.location,
            account_status=snapshot_item.status,
            account_value=snapshot_item.original_value,
            description=f"资产 {snapshot_item.asset.asset_name} 未在盘点中扫描到",
            org=snapshot_item.org,
        )

    @staticmethod
    def _create_surplus_difference(task: InventoryTask, scan_record: dict) -> InventoryDifference:
        """创建盘盈差异"""
        asset = Asset.objects.get(id=scan_record['asset_id'])
        return InventoryDifference.objects.create(
            task=task,
            difference_type='surplus',
            status='pending',
            asset=asset,
            actual_location_id=scan_record['location_id'],
            description=f"扫描到资产 {asset.asset_name}，但不在盘点账面中",
            org=task.org,
        )

    @staticmethod
    def _check_mismatch(snapshot_item: InventorySnapshotItem, scan_record: dict) -> Optional[InventoryDifference]:
        """检查位置/状态不符"""
        differences = []

        # 检查位置
        if snapshot_item.location_id != scan_record['location_id']:
            differences.append(InventoryDifference.objects.create(
                task=snapshot_item.snapshot.task,
                snapshot_item=snapshot_item,
                difference_type='location_mismatch',
                status='pending',
                asset=snapshot_item.asset,
                account_location=snapshot_item.location,
                actual_location_id=scan_record['location_id'],
                description=f"资产位置不符：账面 {snapshot_item.location.name}，实物 {scan_record['location']}",
                org=snapshot_item.org,
            ))

        # 检查状态
        asset = Asset.objects.get(id=snapshot_item.asset_id)
        if snapshot_item.status != asset.status:
            differences.append(InventoryDifference.objects.create(
                task=snapshot_item.snapshot.task,
                snapshot_item=snapshot_item,
                difference_type='status_mismatch',
                status='pending',
                asset=asset,
                account_status=snapshot_item.status,
                actual_status=asset.status,
                description=f"资产状态不符：账面 {snapshot_item.status}，实物 {asset.status}",
                org=snapshot_item.org,
            ))

        return differences[0] if differences else None
```

### 2. 差异认定服务 (继承 BaseCRUDService)

```python
class DifferenceConfirmationService(BaseCRUDService):
    """
    差异认定服务 - 继承 BaseCRUDService

    只负责差异认定，不处理审批逻辑
    """

    def __init__(self):
        """初始化服务，绑定模型"""
        super().__init__(InventoryDifference)

    @transaction.atomic
    def confirm_difference(self, difference_id: int, confirmer, data: dict) -> InventoryDifference:
        """
        认定差异

        使用继承的 update() 方法
        """
        update_data = {
            'status': 'confirmed',
            'confirmed_by_id': confirmer.id,
            'confirmed_at': timezone.now(),
            'confirmation_note': data.get('confirmation_note'),
            'responsible_user_id': data.get('responsible_user_id'),
            'responsible_department_id': data.get('responsible_department_id'),
        }

        return self.update(difference_id, update_data, user=confirmer)

    @transaction.atomic
    def batch_confirm(self, difference_ids: list, confirmer, data: dict) -> int:
        """批量认定"""
        count = 0
        for diff_id in difference_ids:
            try:
                self.confirm_difference(diff_id, confirmer, data)
                count += 1
            except Exception:
                continue
        return count

    # ─── 删除以下方法 (由工作流引擎处理) ───
    # get_approval_level() - 删除！金额判断逻辑由 BPMN 网关处理
    # ──────────────────────────────────────────
```

### 3. 差异处理服务 (继承 BaseCRUDService)

```python
class DifferenceResolutionService(BaseCRUDService):
    """
    差异处理服务 - 继承 BaseCRUDService

    负责创建差异处理单，并启动工作流流程
    """

    def __init__(self):
        """初始化服务，绑定模型"""
        super().__init__(DifferenceResolution)

    @staticmethod
    def generate_resolution_no() -> str:
        """生成处理单号"""
        from django.utils import timezone
        prefix = f"RS{timezone.now().strftime('%Y%m')}"
        last_no = DifferenceResolution.objects.filter(
            resolution_no__startswith=prefix
        ).order_by('-resolution_no').values_list('resolution_no', flat=True).first()
        if last_no:
            seq = int(last_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @transaction.atomic
    def create_resolution(self, user, task_id: int, data: dict) -> DifferenceResolution:
        """
        创建差异处理

        使用继承的 create() 方法
        """
        difference_ids = data.pop('difference_ids', [])

        create_data = {
            'resolution_no': self.generate_resolution_no(),
            'task_id': task_id,
            'action': data.get('action'),
            'description': data.get('description'),
            'applicant_id': user.id,
            'application_date': timezone.now().date(),
        }

        resolution = self.create(create_data, user=user)

        # 关联差异
        InventoryDifference.objects.filter(id__in=difference_ids).update(
            resolution=resolution,
            status='processing'
        )

        return resolution

    @transaction.atomic
    def submit_resolution(self, resolution_id: int, submitter) -> dict:
        """
        提交处理审批

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        🔥 关键变更：不再手动计算审批人！
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        原逻辑 (已删除):
        - approval_level = get_approval_level(resolution)  # if amount < 10000...
        - approver = _get_approver(task, approval_level)     # 手动查找领导

        新逻辑:
        - 构建流程变量
        - 调用 WorkflowService.start_process()
        - 引擎根据 BPMN 定义决定审批人
        """
        from apps.workflows.services.workflow_adapter import WorkflowService
        from apps.workflows.services.workflow_context import WorkflowContext

        resolution = DifferenceResolution.objects.get(id=resolution_id)
        resolution.status = 'submitted'
        resolution.save()

        # 计算总金额 (用于流程判断)
        total_value = sum(
            d.account_value or 0
            for d in resolution.differences.all()
            if d.difference_type == 'loss'
        )

        # 构建流程上下文
        context = WorkflowContext(
            definition_code='inventory_difference_approval',
            business_object='inventory_difference_resolution',
            business_id=str(resolution.id),
            business_no=resolution.resolution_no,
            variables={
                'resolution_action': resolution.action,
                'difference_count': resolution.differences.count(),
                'total_amount': float(total_value),  # 🔑 关键变量：用于 BPMN 条件判断
            },
            initiator_id=str(submitter.id),
            organization_id=str(submitter.organization_id),
        )

        # 启动工作流
        workflow_service = WorkflowService()
        instance = workflow_service.start_process(context)

        # 保存流程实例ID
        resolution.process_instance_id = str(instance.id)
        resolution.save()

        return {
            'resolution_id': resolution.id,
            'process_instance_id': str(instance.id),
            'status': 'submitted',
        }

    # ─── 删除以下方法 (由工作流引擎处理) ───
    # approve_resolution() - 删除！审批逻辑由引擎处理
    # _get_approval_level() - 删除！条件判断由 BPMN 网关处理
    # _get_approver() - 删除！审批人由 BPMN 定义
    # ──────────────────────────────────────────

    @transaction.atomic
    def execute_resolution(self, resolution: DifferenceResolution):
        """
        执行差异处理

        由工作流引擎回调执行，当流程审批通过时调用
        """
        from apps.inventory.services.adjustment_service import AssetAdjustmentService

        for difference in resolution.differences.all():
            if resolution.action == 'adjust_account':
                AssetAdjustmentService.adjust_asset_from_difference(difference, resolution)
            elif resolution.action == 'record_asset':
                AssetAdjustmentService.record_new_asset(difference, resolution)
            elif resolution.action == 'write_off':
                AssetAdjustmentService.write_off_asset(difference, resolution)

            # 使用继承的 update() 方法更新差异
            self.update(difference.id, {'status': 'resolved'})

        # 使用继承的 update() 方法更新处理单
        update_data = {
            'status': 'completed',
            'executor_id': resolution.final_approver.id,
            'executed_at': timezone.now(),
        }
        self.update(resolution.id, update_data)

    @transaction.atomic
    def handle_rejection(self, resolution: DifferenceResolution, reason: str):
        """
        处理审批拒绝

        由工作流引擎回调执行，当流程审批拒绝时调用
        """
        # 恢复差异状态
        resolution.differences.update(status='confirmed')

        # 使用继承的 update() 方法更新处理单
        update_data = {
            'status': 'rejected',
        }
        # 更新自定义字段，记录拒绝原因
        self.update(resolution.id, update_data)

        # 单独保存 custom_fields
        resolution.custom_fields = {
            **resolution.custom_fields,
            'rejection_reason': reason,
        }
        resolution.save()
```

### 4. 资产调账服务 (继承 BaseCRUDService)

```python
# apps/inventory/services/adjustment_service.py

from django.db import transaction
from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import AssetAdjustment, InventoryDifference, DifferenceResolution
from apps.assets.models import Asset


class AssetAdjustmentService(BaseCRUDService):
    """
    资产调账服务 - 继承 BaseCRUDService

    自动获得:
    - create(), update(), delete(), get(), query(), paginate()
    - 组织过滤和软删除支持
    """

    def __init__(self):
        """初始化服务，绑定模型"""
        super().__init__(AssetAdjustment)

    @staticmethod
    def generate_adjustment_no() -> str:
        """生成调账单号"""
        from django.utils import timezone
        prefix = f"ADJ{timezone.now().strftime('%Y%m')}"
        last_no = AssetAdjustment.objects.filter(
            adjustment_no__startswith=prefix
        ).order_by('-adjustment_no').values_list('adjustment_no', flat=True).first()
        if last_no:
            seq = int(last_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @transaction.atomic
    def adjust_asset_from_difference(
        self,
        difference: InventoryDifference,
        resolution: DifferenceResolution
    ) -> AssetAdjustment:
        """
        根据差异调整资产账面信息
        """
        asset = difference.asset

        # 记录调账前值
        before_value = {
            'location': str(difference.account_location),
            'status': difference.account_status,
            'value': str(difference.account_value),
        }

        # 执行调整
        asset.location_id = difference.actual_location_id
        asset.status = difference.actual_status if difference.actual_status else asset.status
        asset.save()

        # 记录调账后值
        after_value = {
            'location': str(asset.location),
            'status': asset.status,
            'value': str(asset.original_value),
        }

        # 使用继承的 create() 方法创建调账记录
        adjustment_data = {
            'adjustment_no': self.generate_adjustment_no(),
            'resolution': resolution,
            'asset': asset,
            'adjustment_type': 'location',
            'before_value': before_value,
            'after_value': after_value,
            'change_description': f"根据盘点差异 {difference.id} 调整资产位置",
        }

        return self.create(adjustment_data, user=resolution.applicant)

    @transaction.atomic
    def record_new_asset(
        self,
        difference: InventoryDifference,
        resolution: DifferenceResolution
    ) -> AssetAdjustment:
        """
        补录盘盈资产
        """
        # 使用继承的 create() 方法创建资产
        asset = Asset.objects.create(
            code=f"ASSET{timezone.now().strftime('%Y%m%d%H%M%S')}",
            name=difference.asset.name if difference.asset else "盘盈资产",
            location=difference.actual_location,
            status=difference.actual_status or 'idle',
            original_value=difference.actual_value or 0,
            organization_id=resolution.organization_id,
        )

        adjustment_data = {
            'adjustment_no': self.generate_adjustment_no(),
            'resolution': resolution,
            'asset': asset,
            'adjustment_type': 'new',
            'before_value': {},
            'after_value': {
                'code': asset.code,
                'name': asset.name,
                'location': str(asset.location),
            },
            'change_description': f"根据盘点差异 {difference.id} 补录资产",
        }

        return self.create(adjustment_data, user=resolution.applicant)

    @transaction.atomic
    def write_off_asset(
        self,
        difference: InventoryDifference,
        resolution: DifferenceResolution
    ) -> AssetAdjustment:
        """
        报损盘亏资产
        """
        asset = difference.asset

        before_value = {
            'code': asset.code,
            'name': asset.name,
            'status': asset.status,
        }

        # 软删除资产
        asset.soft_delete()

        adjustment_data = {
            'adjustment_no': self.generate_adjustment_no(),
            'resolution': resolution,
            'asset': asset,
            'adjustment_type': 'remove',
            'before_value': before_value,
            'after_value': {},
            'change_description': f"根据盘点差异 {difference.id} 报损资产",
        }

        return self.create(adjustment_data, user=resolution.applicant)

    @transaction.atomic
    def rollback_adjustment(
        self,
        adjustment: AssetAdjustment,
        user,
        reason: str
    ) -> AssetAdjustment:
        """
        回滚调账

        使用继承的 update() 方法
        """
        if adjustment.adjustment_type in ['location', 'status']:
            # 恢复资产信息
            asset = adjustment.asset
            before = adjustment.before_value

            if 'location' in before:
                asset.location_id = before['location']
            if 'status' in before:
                asset.status = before['status']

            asset.save()

        # 使用继承的 update() 方法更新调账记录
        update_data = {
            'status': 'rolled_back',
            'rolled_back_by_id': user.id,
            'rolled_back_at': timezone.now(),
            'rollback_reason': reason,
        }

        return self.update(adjustment.id, update_data, user=user)
```

### 5. 工作流回调处理器 (新增)

```python
# apps/inventory/services/workflow_callbacks.py

from django.db import transaction
from apps.workflows.models import WorkflowInstance


class InventoryWorkflowCallbacks:
    """
    盘点模块工作流回调处理器

    处理工作流引擎的状态变更通知
    """

    @staticmethod
    @transaction.atomic
    def on_workflow_completed(instance: WorkflowInstance):
        """
        流程完成回调

        根据流程最终结果执行相应操作
        """
        business_object = instance.business_object
        business_id = instance.business_id

        if business_object == 'inventory_difference_resolution':
            InventoryWorkflowCallbacks._handle_resolution_completed(
                business_id, instance
            )

    @staticmethod
    def _handle_resolution_completed(resolution_id: str, instance: WorkflowInstance):
        """处理差异处理流程完成"""
        from apps.inventory.models import DifferenceResolution
        from apps.inventory.services.difference_service import DifferenceResolutionService

        resolution = DifferenceResolution.objects.get(id=resolution_id)

        # 检查流程结果 (从引擎变量获取)
        final_action = instance.variables.get('final_action', 'approved')

        if final_action == 'approved':
            # 执行处理
            DifferenceResolutionService.execute_resolution(resolution)
        else:
            # 处理拒绝
            reason = instance.variables.get('rejection_reason', '')
            DifferenceResolutionService.handle_rejection(resolution, reason)
```

---

## BPMN 流程定义示例

### 盘点差异审批流程

```xml
<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="inventory_difference_approval" name="盘点差异审批">

    <!-- 开始 -->
    <bpmn:startEvent id="start" name="开始"/>

    <!-- 部门审批 -->
    <bpmn:userTask id="task_dept_approve" name="部门审批">
      <bpmn:extensionElements>
        <lf:approvers xmlns:lf="http://logicflow.org">
          <lf:approver type="leader" leader_type="department"/>
        </lf:approvers>
      </bpmn:extensionElements>
    </bpmn:userTask>

    <!-- 🔑 金额判断网关：条件由 BPMN 定义，不在代码中写死 -->
    <bpmn:exclusiveGateway id="gateway_amount" name="金额判断"/>

    <!-- 小额：直接结束 -->
    <bpmn:sequenceFlow sourceRef="gateway_amount" targetRef="end">
      <bpmn:conditionExpression>${total_amount <= 10000}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>

    <!-- 大额：总经理审批 -->
    <bpmn:sequenceFlow sourceRef="gateway_amount" targetRef="task_manager_approve">
      <bpmn:conditionExpression>${total_amount > 10000}</bpmn:conditionExpression>
    </bpmn:sequenceFlow>

    <bpmn:userTask id="task_manager_approve" name="总经理审批">
      <bpmn:extensionElements>
        <lf:approvers xmlns:lf="http://logicflow.org">
          <lf:approver type="role" role_id="general_manager"/>
        </lf:approvers>
      </bpmn:extensionElements>
    </bpmn:userTask>

    <bpmn:sequenceFlow sourceRef="task_manager_approve" targetRef="end"/>

    <!-- 结束 -->
    <bpmn:endEvent id="end" name="结束"/>

  </bpmn:process>
</bpmn:definitions>
```

---

## 变更总结

### 1. 删除的代码

| 原代码位置 | 删除原因 |
|-----------|---------|
| `get_approval_level()` | 金额判断逻辑由 BPMN 网关处理 |
| `_get_approver()` | 审批人由 BPMN 定义 |
| `approve_resolution()` | 审批逻辑由工作流引擎处理 |
| `DifferenceResolution.current_approver` | 由引擎动态持有 |
| `DifferenceResolution.approved_by` (旧) | 使用 `final_approver` 存储最终结果 |
| `DifferenceResolution.approval_note` | 存储在流程日志中 |

### 2. 新增的代码

| 新增内容 | 说明 |
|---------|------|
| `process_instance_id` | 关联工作流引擎实例 |
| `WorkflowContext` | 业务数据到引擎变量的转换 |
| `submit_resolution()` 调用引擎 | 启动 BPMN 流程 |
| `InventoryWorkflowCallbacks` | 处理引擎回调 |
| BPMN 流程定义文件 | 条件和审批人在流程图中定义 |

### 3. 基类使用总结

| 组件类型 | 基类 | 获得能力 |
|---------|------|---------|
| **序列化器** | `BaseModelSerializer` | 自动处理公共字段、组织、软删除、审计信息 |
| **序列化器** | `BaseModelWithAuditSerializer` | 包含完整审计字段（updated_by, deleted_by） |
| **视图集** | `BaseModelViewSetWithBatch` | 组织隔离、软删除、批量操作、已删除列表查询 |
| **服务类** | `BaseCRUDService` | CRUD 方法、组织过滤、分页、批量操作 |
| **过滤器** | `BaseModelFilter` | 时间范围、用户、状态过滤 |

### 4. 变更前后的流程对比

```
变更前 (硬编码):
submit_resolution()
  └─> get_approval_level()     // if amount < 10000 return 1
      └─> _get_approver()         // 查找部门领导
          └─> 手动赋值 current_approver
              └─> 等待审批...

变更后 (工作流引擎):
submit_resolution()
  └─> 构建变量 {total_amount: 50000}
      └─> WorkflowService.start_process()
          └─> SpiffWorkflow 解析 BPMN
              └─> 遇到网关 ${amount > 10000}
                  └─> 条件成立，走总经理审批分支
                      └─> 创建总经理审批任务
```

### 5. 基类继承带来的代码减少

| 模块 | 原代码行数（估算） | 使用基类后 | 减少比例 |
|------|------------------|-----------|---------|
| 序列化器 | ~200 行 | ~80 行 | 60% |
| 视图集 | ~300 行 | ~150 行 | 50% |
| 服务类 | ~250 行 | ~120 行 | 52% |
| 过滤器 | ~100 行 | ~40 行 | 60% |

---

## URL 路由配置

### apps/inventory/urls.py

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.inventory.views import (
    InventoryDifferenceViewSet,
    DifferenceResolutionViewSet,
    AssetAdjustmentViewSet,
)

router = DefaultRouter()
router.register(r'differences', InventoryDifferenceViewSet, basename='inventory-difference')
router.register(r'resolutions', DifferenceResolutionViewSet, basename='difference-resolution')
router.register(r'adjustments', AssetAdjustmentViewSet, basename='asset-adjustment')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 主路由配置 (backend/config/urls.py)

```python
urlpatterns = [
    # ... 其他路由
    path('api/inventory/', include('apps.inventory.urls')),
]
```

---

## 测试用例建议

### 1. 差异分析测试

```python
def test_analyze_task_differences():
    """测试差异分析"""
    # 创建盘点任务和快照
    # 模拟扫描操作
    # 调用 DifferenceAnalysisService.analyze_task_differences()
    # 验证生成的差异记录
```

### 2. 差异认定测试

```python
def test_confirm_difference():
    """测试差异认定"""
    # 使用 DifferenceConfirmationService.confirm_difference()
    # 验证状态变更和责任人设置
```

### 3. 工作流集成测试

```python
def test_submit_resolution_and_workflow():
    """测试处理单提交和工作流启动"""
    # 创建差异处理
    # 调用 DifferenceResolutionService.submit_resolution()
    # 验证流程实例创建
    # 模拟工作流回调
```

### 4. 资产调账测试

```python
def test_adjust_asset_and_rollback():
    """测试资产调账和回滚"""
    # 调用 AssetAdjustmentService.adjust_asset_from_difference()
    # 验证资产信息变更
    # 调用 rollback_adjustment()
    # 验证资产信息恢复
```

---

## 后续任务

1. ✅ **公共基类实现** - 已完成 [Common Base Features](../common_base_features/backend.md)
2. ✅ **盘点模块基类迁移** - 本文档已完成
3. ⏳ **创建 BPMN 流程定义文件** - 待实施
4. ⏳ **实现工作流回调处理器** - 待实施
5. ⏳ **编写集成测试** - 待实施
6. ⏳ **更新 API 接口以适配新的流程** - 待实施
7. ⏳ **前端适配新的 API 响应格式** - 待实施

---

## API 接口规范

### 统一响应格式

#### 成功响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "task_code": "INV-2026-001",
        "difference_type": "loss",
        "status": "pending",
        "asset": {...},
        "account_value": 10000.00,
        "actual_value": 0,
        "organization": {...},
        "created_at": "2026-01-14T10:30:00Z",
        "created_by": {...}
    }
}
```

#### 列表响应（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/inventory-differences/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "task_code": "INV-2026-001",
                "difference_type": "loss",
                "status": "pending",
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
            "difference_type": ["差异类型不能为空"],
            "asset": ["资产不存在"]
        }
    }
}
```

### 标准 CRUD 端点

本模块所有 ViewSet 继承自 `BaseModelViewSetWithBatch`，自动提供以下标准端点：

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/inventory-differences/` | 列表查询（分页、过滤、搜索） |
| GET | `/api/inventory-differences/{id}/` | 获取单个盘点差异详情 |
| POST | `/api/inventory-differences/` | 创建新的盘点差异 |
| PUT | `/api/inventory-differences/{id}/` | 完整更新盘点差异 |
| PATCH | `/api/inventory-differences/{id}/` | 部分更新盘点差异 |
| DELETE | `/api/inventory-differences/{id}/` | 软删除盘点差异 |

### 批量操作端点

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| POST | `/api/inventory-differences/batch-delete/` | 批量软删除 |
| POST | `/api/inventory-differences/batch-restore/` | 批量恢复 |
| POST | `/api/inventory-differences/batch-update/` | 批量字段更新 |

#### 批量删除请求示例

```http
POST /api/inventory-differences/batch-delete/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001",
        "550e8400-e29b-41d4-a716-446655440002"
    ]
}
```

#### 批量操作响应（全部成功）

```json
{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440002", "success": true}
    ]
}
```

#### 批量操作响应（部分失败）

```json
{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": false, "error": "记录不存在"},
        {"id": "550e8400-e29b-41d4-a716-446655440002", "success": true}
    ]
}
```

### 扩展操作端点

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/inventory-differences/deleted/` | 查询已删除的盘点差异 |
| POST | `/api/inventory-differences/{id}/restore/` | 恢复单个已删除的盘点差异 |
| GET | `/api/inventory-differences/{id}/history/` | 获取盘点差异变更历史 |
| POST | `/api/inventory-differences/{id}/confirm/` | 认定差异 |
| POST | `/api/inventory-differences/batch-confirm/` | 批量认定差异 |
| GET | `/api/inventory-differences/statistics/` | 差异统计 |
| POST | `/api/inventory-differences/{id}/start-resolution/` | 启动处理流程 |
| POST | `/api/inventory-resolutions/{id}/submit/` | 提交审批 |
| POST | `/api/inventory-resolutions/{id}/execute/` | 执行处理 |
| POST | `/api/inventory-adjustments/{id}/rollback/` | 回滚调账 |

### 标准错误码

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

---
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