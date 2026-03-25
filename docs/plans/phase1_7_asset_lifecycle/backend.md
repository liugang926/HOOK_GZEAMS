# Phase 1.7: 资产生命周期管理 - 后端实现

## 公共模型引用

> 本模块所有后端组件必须继承以下公共基类

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法 |

---

## 功能概述与业务场景

资产生命周期管理模块涵盖资产从采购申请到最终处置的完整生命周期管理流程：

1. **采购申请管理**：员工发起资产需求申请，经过审批流程后推送至M18采购系统，实现从需求到采购的全流程管理
2. **资产入库验收**：资产到货后进行质量检验和数量核对，验收通过后自动生成资产卡片，确保账实相符
3. **维护保养管理**：支持故障报修、维修派单、保养计划制定与任务执行，延长资产使用寿命
4. **报废处置管理**：支持多种处置方式（报废/出售/捐赠/调拨/销毁），包含技术鉴定、审批执行和财务凭证生成

## 用户角色与权限

| 角色 | 权限说明 |
|------|---------|
| 普通员工 | 发起采购申请、故障报修、查看自己的申请记录 |
| 部门主管 | 审批本部门的采购申请和报废申请 |
| 资产管理员 | 资产验收、维护派单、保养计划管理、报废鉴定 |
| 维修人员 | 接收维修工单、执行维修任务、完成任务验收 |
| 财务人员 | 查看采购预算、确认报废处置、生成财务凭证 |
| 系统管理员 | 全部权限，包括配置管理、数据维护 |

## 公共模型引用声明

本模块严格遵循GZEAMS公共基类架构规范，所有组件均继承相应的公共基类：

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离（org字段）、软删除（is_deleted+deleted_at）、审计字段（created_at+updated_at+created_by）、动态扩展（custom_fields JSONField） |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 自动序列化公共字段（id/org/is_deleted/deleted_at/created_at/updated_at/created_by）、custom_fields处理 |
| Serializer (带审计) | BaseModelWithAuditSerializer | apps.common.serializers.base.BaseModelWithAuditSerializer | 包含updated_by和deleted_by的完整审计信息 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除过滤、自动设置审计字段、批量操作（batch-delete/batch-restore/batch-update）、已删除记录查询（deleted/restore） |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤（created_at/updated_at/created_by/is_deleted）、时间范围查询（created_at_from/to、updated_at_from/to） |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法（create/update/delete/restore/get/query/paginate）、自动组织隔离、软删除处理、批量操作支持 |

### 继承关系示例

```python
# Model继承
from apps.common.models import BaseModel

class PurchaseRequest(BaseModel):
    """自动继承：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields"""
    request_no = models.CharField(max_length=50, unique=True)
    # ... 其他业务字段

# Serializer继承
from apps.common.serializers.base import BaseModelSerializer

class PurchaseRequestSerializer(BaseModelSerializer):
    """自动序列化：id, org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields"""
    class Meta(BaseModelSerializer.Meta):
        model = PurchaseRequest
        fields = BaseModelSerializer.Meta.fields + ['request_no', 'status', ...]

# ViewSet继承
from apps.common.viewsets.base import BaseModelViewSetWithBatch

class PurchaseRequestViewSet(BaseModelViewSetWithBatch):
    """自动获得：组织过滤、软删除、审计字段设置、批量操作、已删除记录查询"""
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer
    # 自动提供：list, create, retrieve, update, destroy, batch-delete, batch-restore, deleted, restore

# Filter继承
from apps.common.filters.base import BaseModelFilter

class PurchaseRequestFilter(BaseModelFilter):
    """自动支持：created_at_from, created_at_to, updated_at_from, updated_at_to, created_by, is_deleted"""
    class Meta(BaseModelFilter.Meta):
        model = PurchaseRequest
        fields = BaseModelFilter.Meta.fields + ['request_no', 'status', ...]

# Service继承
from apps.common.services.base_crud import BaseCRUDService

class PurchaseRequestService(BaseCRUDService):
    """自动获得：create(), update(), delete(), restore(), get(), query(), paginate(), batch_delete()"""
    def __init__(self):
        super().__init__(PurchaseRequest)
    # 所有方法自动处理组织隔离和软删除
```

## 数据模型设计

### 1.1 采购申请 (PurchaseRequest)

**PurchaseRequest Model**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| request_no | string | max_length=50, unique | 申请单号 (自动生成: PR+YYYYMM+序号) |
| status | string | max_length=20, choices | 状态: draft/submitted/approved/rejected/processing/completed/cancelled |
| applicant | FK(User) | PROTECT, related_name='purchase_requests' | 申请人 |
| department | FK(Department) | PROTECT, related_name='purchase_requests' | 申请部门 |
| request_date | date | - | 需求日期 |
| expected_date | date | - | 期望到货日期 |
| reason | text | - | 申请原因 |
| budget_amount | decimal | max_digits=15, decimal_places=2, null=True | 预算金额 |
| cost_center | FK(CostCenter) | PROTECT, null=True, related_name='purchase_requests' | 成本中心 |
| current_approver | FK(User) | SET_NULL, null=True, related_name='pending_purchase_approvals' | 当前审批人 |
| approved_at | datetime | null=True | 审批时间 |
| approved_by | FK(User) | SET_NULL, null=True, related_name='approved_purchase_requests' | 审批人 |
| m18_purchase_order_no | string | max_length=100, null=True | M18采购单号 |
| pushed_to_m18_at | datetime | null=True | 推送M18时间 |
| m18_sync_status | string | max_length=20, null=True | M18同步状态 |

*状态流程: draft → submitted → approved → processing → completed / rejected*

**PurchaseRequestItem (采购申请明细)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| purchase_request | FK(PurchaseRequest) | CASCADE, related_name='items' | 采购申请 |
| sequence | int | default=1 | 序号 |
| asset_category | FK(AssetCategory) | PROTECT, related_name='purchase_request_items' | 资产类别 |
| item_name | string | max_length=200 | 物品名称 |
| specification | text | - | 规格型号 |
| brand | string | max_length=100, null=True | 品牌 |
| quantity | int | - | 数量 |
| unit | string | max_length=20 | 单位 |
| unit_price | decimal | max_digits=12, decimal_places=2 | 单价 |
| total_amount | decimal | max_digits=15, decimal_places=2 | 金额 |
| suggested_supplier | string | max_length=200, null=True | 建议供应商 |
| remark | text | blank=True | 备注 |

### 1.2 资产入库 (AssetReceipt)

```python
class AssetReceipt(BaseModel):
    """
    资产验收单
    资产到货后创建验收单，验收通过后自动生成资产卡片
    """
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('inspecting', '检验中'),
        ('passed', '验收通过'),
        ('rejected', '验收不通过'),
        ('cancelled', '已取消'),
    ]

    # 基本信息
    receipt_no = models.CharField(max_length=50, unique=True, verbose_name='验收单号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')

    # 关联采购申请
    purchase_request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='receipts',
        verbose_name='采购申请'
    )
    m18_purchase_order_no = models.CharField(max_length=100, null=True, blank=True, verbose_name='M18采购单号')

    # 验收信息
    receipt_date = models.DateField(verbose_name='验收日期')
    receipt_type = models.CharField(
        max_length=20,
        choices=[('purchase', '采购入库'), ('transfer', '调拨入库'), ('return', '退回入库')],
        default='purchase',
        verbose_name='入库类型'
    )

    # 供应商/来源信息
    supplier = models.CharField(max_length=200, null=True, blank=True, verbose_name='供应商')
    delivery_no = models.CharField(max_length=100, null=True, blank=True, verbose_name='送货单号')

    # 验收人员
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_receipts',
        verbose_name='验收人'
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='inspected_receipts',
        null=True, blank=True,
        verbose_name='质检员'
    )

    # 验收结果
    inspection_result = models.TextField(null=True, blank=True, verbose_name='检验结果')
    passed_at = models.DateTimeField(null=True, blank=True, verbose_name='验收通过时间')

    # 自定义字段
    custom_fields = models.JSONField(default=dict, blank=True, verbose_name='自定义字段')

    class Meta:
        db_table = 'lifecycle_asset_receipt'
        verbose_name = '资产验收单'
        verbose_name_plural = '资产验收单'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['receipt_no']),
            models.Index(fields=['status']),
            models.Index(fields=['purchase_request']),
            models.Index(fields=['m18_purchase_order_no']),
        ]

    def __str__(self):
        return f"{self.receipt_no} - {self.get_status_display()}"


class AssetReceiptItem(BaseModel):
    """
    验收明细
    """
    asset_receipt = models.ForeignKey(
        AssetReceipt,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='验收单'
    )

    # 物品信息
    sequence = models.IntegerField(default=1, verbose_name='序号')
    asset_category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.PROTECT,
        related_name='receipt_items',
        verbose_name='资产类别'
    )
    item_name = models.CharField(max_length=200, verbose_name='物品名称')
    specification = models.TextField(verbose_name='规格型号')
    brand = models.CharField(max_length=100, null=True, blank=True, verbose_name='品牌')

    # 数量检验
    ordered_quantity = models.IntegerField(verbose_name='订购数量')
    received_quantity = models.IntegerField(verbose_name='实收数量')
    qualified_quantity = models.IntegerField(default=0, verbose_name='合格数量')
    defective_quantity = models.IntegerField(default=0, verbose_name='不合格数量')

    # 金额信息
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='单价')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='金额')

    # 资产卡片生成
    asset_generated = models.BooleanField(default=False, verbose_name='已生成资产卡片')

    # 备注
    remark = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'lifecycle_asset_receipt_item'
        verbose_name = '验收明细'
        verbose_name_plural = '验收明细'
        ordering = ['sequence']

    def __str__(self):
        return f"{self.asset_receipt.receipt_no} - {self.item_name}"
```

### 1.3 维护保养 (Maintenance)

```python
class Maintenance(BaseModel):
    """
    维修记录
    记录资产故障报修、维修过程、维修费用
    """
    STATUS_CHOICES = [
        ('reported', '已报修'),
        ('assigned', '已派单'),
        ('processing', '维修中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]

    # 基本信息
    maintenance_no = models.CharField(max_length=50, unique=True, verbose_name='维修单号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported', verbose_name='状态')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal', verbose_name='优先级')

    # 资产信息
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='maintenance_records',
        verbose_name='资产'
    )

    # 报修信息
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reported_maintenance',
        verbose_name='报修人'
    )
    report_time = models.DateTimeField(verbose_name='报修时间')
    fault_description = models.TextField(verbose_name='故障描述')
    fault_photo_urls = models.JSONField(default=list, blank=True, verbose_name='故障照片')

    # 维修人员
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='assigned_maintenance',
        null=True, blank=True,
        verbose_name='维修人员'
    )
    assigned_at = models.DateTimeField(null=True, blank=True, verbose_name='派单时间')

    # 维修信息
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    work_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='工时')

    # 维修结果
    fault_cause = models.TextField(null=True, blank=True, verbose_name='故障原因')
    repair_method = models.TextField(null=True, blank=True, verbose_name='维修方法')
    replaced_parts = models.TextField(null=True, blank=True, verbose_name='更换配件')
    repair_result = models.TextField(null=True, blank=True, verbose_name='维修结果')

    # 费用信息
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='人工费')
    material_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='材料费')
    other_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='其他费用')
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='总费用')

    # 验收信息
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='verified_maintenance',
        null=True, blank=True,
        verbose_name='验收人'
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='验收时间')
    verification_result = models.TextField(null=True, blank=True, verbose_name='验收结果')

    # 自定义字段
    custom_fields = models.JSONField(default=dict, blank=True, verbose_name='自定义字段')

    class Meta:
        db_table = 'lifecycle_maintenance'
        verbose_name = '维修记录'
        verbose_name_plural = '维修记录'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['maintenance_no']),
            models.Index(fields=['status']),
            models.Index(fields=['asset']),
            models.Index(fields=['priority']),
        ]

    def __str__(self):
        return f"{self.maintenance_no} - {self.asset.asset_name}"


class MaintenancePlan(BaseModel):
    """
    保养计划
    按周期生成保养任务
    """
    STATUS_CHOICES = [
        ('active', '启用'),
        ('paused', '暂停'),
        ('archived', '归档'),
    ]

    CYCLE_CHOICES = [
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('quarterly', '每季度'),
        ('yearly', '每年'),
        ('custom', '自定义'),
    ]

    # 基本信息
    plan_name = models.CharField(max_length=200, verbose_name='计划名称')
    plan_code = models.CharField(max_length=50, unique=True, verbose_name='计划编号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='状态')

    # 保养对象
    target_type = models.CharField(
        max_length=20,
        choices=[('category', '按类别'), ('asset', '按资产'), ('location', '按位置')],
        default='category',
        verbose_name='保养对象类型'
    )
    asset_categories = models.ManyToManyField(
        'assets.AssetCategory',
        blank=True,
        related_name='maintenance_plans',
        verbose_name='资产类别'
    )
    assets = models.ManyToManyField(
        'assets.Asset',
        blank=True,
        related_name='maintenance_plans',
        verbose_name='指定资产'
    )
    locations = models.ManyToManyField(
        'organizations.Location',
        blank=True,
        related_name='maintenance_plans',
        verbose_name='位置'
    )

    # 保养周期
    cycle_type = models.CharField(max_length=20, choices=CYCLE_CHOICES, verbose_name='周期类型')
    cycle_value = models.IntegerField(default=1, verbose_name='周期值')
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')

    # 提醒设置
    remind_days_before = models.IntegerField(default=3, verbose_name='提前提醒天数')
    remind_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='maintenance_plans_reminded',
        verbose_name='提醒人员'
    )

    # 保养内容
    maintenance_content = models.TextField(verbose_name='保养内容')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='预计工时')

    # 自定义字段
    custom_fields = models.JSONField(default=dict, blank=True, verbose_name='自定义字段')

    class Meta:
        db_table = 'lifecycle_maintenance_plan'
        verbose_name = '保养计划'
        verbose_name_plural = '保养计划'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['plan_code']),
            models.Index(fields=['status']),
            models.Index(fields=['cycle_type']),
        ]

    def __str__(self):
        return f"{self.plan_code} - {self.plan_name}"


class MaintenanceTask(BaseModel):
    """
    保养任务
    根据保养计划生成的具体任务
    """
    STATUS_CHOICES = [
        ('pending', '待执行'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('skipped', '已跳过'),
        ('overdue', '已逾期'),
    ]

    # 基本信息
    task_no = models.CharField(max_length=50, unique=True, verbose_name='任务编号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')

    # 关联计划
    plan = models.ForeignKey(
        MaintenancePlan,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='保养计划'
    )

    # 任务信息
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='maintenance_tasks',
        verbose_name='资产'
    )

    # 计划时间
    scheduled_date = models.DateField(verbose_name='计划日期')
    deadline_date = models.DateField(verbose_name='截止日期')

    # 执行信息
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='maintenance_tasks',
        null=True, blank=True,
        verbose_name='执行人'
    )
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank_time, verbose_name='完成时间')

    # 执行结果
    execution_content = models.TextField(null=True, blank=True, verbose_name='执行内容')
    execution_photo_urls = models.JSONField(default=list, blank=True, verbose_name='执行照片')
    finding = models.TextField(null=True, blank=True, verbose_name='发现的问题')
    next_maintenance_suggestion = models.TextField(null=True, blank=True, verbose_name='下次保养建议')

    # 验收信息
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='verified_maintenance_tasks',
        null=True, blank=True,
        verbose_name='验收人'
    )
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name='验收时间')

    # 自定义字段
    custom_fields = models.JSONField(default=dict, blank=True, verbose_name='自定义字段')

    class Meta:
        db_table = 'lifecycle_maintenance_task'
        verbose_name = '保养任务'
        verbose_name_plural = '保养任务'
        ordering = ['scheduled_date', '-created_at']
        indexes = [
            models.Index(fields=['task_no']),
            models.Index(fields=['status']),
            models.Index(fields=['plan']),
            models.Index(fields=['asset']),
            models.Index(fields=['scheduled_date']),
        ]

    def __str__(self):
        return f"{self.task_no} - {self.asset.asset_name}"
```

### 1.4 报废处置 (DisposalRequest)

```python
class DisposalRequest(BaseModel):
    """
    报废申请单
    发起资产报废申请，经过技术鉴定和审批后执行处置
    """
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('appraising', '鉴定中'),
        ('approved', '已审批'),
        ('rejected', '已拒绝'),
        ('executing', '处置中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    DISPOSAL_TYPE_CHOICES = [
        ('scrap', '报废'),
        ('sale', '出售'),
        ('donation', '捐赠'),
        ('transfer', '调拨'),
        ('destroy', '销毁'),
    ]

    # 基本信息
    request_no = models.CharField(max_length=50, unique=True, verbose_name='报废单号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    disposal_type = models.CharField(max_length=20, choices=DISPOSAL_TYPE_CHOICES, default='scrap', verbose_name='处置方式')

    # 申请人信息
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='disposal_requests',
        verbose_name='申请人'
    )
    department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='disposal_requests',
        verbose_name='申请部门'
    )
    request_date = models.DateField(verbose_name='申请日期')

    # 申请原因
    disposal_reason = models.TextField(verbose_name='处置原因')
    reason_type = models.CharField(
        max_length=50,
        choices=[
            ('damage', '损坏无法修复'),
            ('obsolete', '技术淘汰'),
            ('expired', '使用年限到期'),
            ('excess', '闲置多余'),
            ('other', '其他原因'),
        ],
        verbose_name='原因类型'
    )

    # 审批信息
    current_approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pending_disposal_approvals',
        verbose_name='当前审批人'
    )

    # 自定义字段
    custom_fields = models.JSONField(default=dict, blank=True, verbose_name='自定义字段')

    class Meta:
        db_table = 'lifecycle_disposal_request'
        verbose_name = '报废申请'
        verbose_name_plural = '报废申请'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['request_no']),
            models.Index(fields=['status']),
            models.Index(fields=['applicant']),
        ]

    def __str__(self):
        return f"{self.request_no} - {self.get_disposal_type_display()}"


class DisposalItem(BaseModel):
    """
    报废资产明细
    """
    disposal_request = models.ForeignKey(
        DisposalRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='报废申请'
    )

    # 资产信息
    sequence = models.IntegerField(default=1, verbose_name='序号')
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='disposal_items',
        verbose_name='资产'
    )

    # 原值信息
    original_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='原值')
    accumulated_depreciation = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name='累计折旧')
    net_value = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='净值')

    # 鉴定信息
    appraisal_result = models.TextField(null=True, blank=True, verbose_name='鉴定结果')
    residual_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='预估残值')
    appraised_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='appraised_disposal_items',
        null=True, blank=True,
        verbose_name='鉴定人'
    )
    appraised_at = models.DateTimeField(null=True, blank=True, verbose_name='鉴定时间')

    # 处置执行
    disposal_executed = models.BooleanField(default=False, verbose_name='已处置')
    executed_at = models.DateTimeField(null=True, blank=True, verbose_name='处置时间')
    actual_residual_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='实际残值')
    buyer_info = models.TextField(null=True, blank=True, verbose_name='买方信息')

    # 备注
    remark = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'lifecycle_disposal_item'
        verbose_name = '报废明细'
        verbose_name_plural = '报废明细'
        ordering = ['sequence']

    def __str__(self):
        return f"{self.disposal_request.request_no} - {self.asset.asset_name}"
```

---

## 2. 序列化器设计

所有序列化器继承公共基类，自动序列化公共字段。

### 2.1 采购申请序列化器 (PurchaseRequestSerializer)

| 序列化器 | 继承 | 业务字段 |
|---------|------|---------|
| PurchaseRequestItemSerializer | BaseModelSerializer | purchase_request, sequence, asset_category, item_name, specification, brand, quantity, unit, unit_price, total_amount, suggested_supplier, remark |
| PurchaseRequestListSerializer | BaseModelSerializer | request_no, status, applicant, department, request_date, expected_date, budget_amount, items_count, current_approver, approved_at |
| PurchaseRequestDetailSerializer | BaseModelWithAuditSerializer | request_no, status, applicant, department, request_date, expected_date, reason, budget_amount, cost_center, current_approver, approved_at, approved_by, m18_purchase_order_no, pushed_to_m18_at, m18_sync_status, items |

### 2.2 资产入库序列化器 (AssetReceiptSerializer)

| 序列化器 | 继承 | 业务字段 |
|---------|------|---------|
| AssetReceiptItemSerializer | BaseModelSerializer | asset_receipt, sequence, asset_category, item_name, specification, brand, ordered_quantity, received_quantity, qualified_quantity, defective_quantity, unit_price, total_amount, asset_generated, remark |
| AssetReceiptSerializer | BaseModelSerializer | receipt_no, status, purchase_request, m18_purchase_order_no, receipt_date, receipt_type, supplier, delivery_no, receiver, inspector, inspection_result, passed_at, items |

### 2.3 维护保养序列化器 (MaintenanceSerializer)

| 序列化器 | 继承 | 业务字段 |
|---------|------|---------|
| MaintenanceSerializer | BaseModelSerializer | maintenance_no, status, priority, asset, reporter, report_time, fault_description, fault_photo_urls, technician, assigned_at, start_time, end_time, work_hours, fault_cause, repair_method, replaced_parts, repair_result, labor_cost, material_cost, other_cost, total_cost, verified_by, verified_at, verification_result |
| MaintenancePlanSerializer | BaseModelSerializer | plan_name, plan_code, status, target_type, asset_categories, cycle_type, cycle_value, start_date, end_date, remind_days_before, remind_users, maintenance_content, estimated_hours |
| MaintenanceTaskSerializer | BaseModelSerializer | task_no, status, plan, asset, scheduled_date, deadline_date, executor, start_time, end_time, execution_content, execution_photo_urls, finding, next_maintenance_suggestion, verified_by, verified_at |

### 2.4 报废处置序列化器 (DisposalRequestSerializer)

| 序列化器 | 继承 | 业务字段 |
|---------|------|---------|
| DisposalItemSerializer | BaseModelSerializer | disposal_request, sequence, asset, original_value, accumulated_depreciation, net_value, appraisal_result, residual_value, appraised_by, appraised_at, disposal_executed, executed_at, actual_residual_value, buyer_info, remark |
| DisposalRequestSerializer | BaseModelSerializer | request_no, status, disposal_type, applicant, department, request_date, disposal_reason, reason_type, current_approver, items |

*注: 所有序列化器自动包含 BaseModelSerializer.Meta.fields (id, organization, is_deleted, deleted_at, created_at, updated_at, created_by)*

---

## 3. 过滤器设计

### 3.1 生命周期过滤器

所有过滤器继承 `BaseModelFilter`，自动支持公共字段过滤。

| 过滤器 | 继承 | 业务过滤字段 |
|-------|------|------------|
| PurchaseRequestFilter | BaseModelFilter | request_no (icontains), status (choices), applicant (UUID), department (UUID), request_date_from/to, expected_date_from/to |
| AssetReceiptFilter | BaseModelFilter | receipt_no (icontains), status (choices), receipt_type (choices), purchase_request (UUID), receiver (UUID), receipt_date_from/to |
| MaintenanceFilter | BaseModelFilter | maintenance_no (icontains), status (choices), priority (choices), asset (UUID), reporter (UUID), technician (UUID), report_time_from/to |
| MaintenanceTaskFilter | BaseModelFilter | task_no (icontains), status (choices), plan (UUID), asset (UUID), executor (UUID), scheduled_date_from/to |
| DisposalRequestFilter | BaseModelFilter | request_no (icontains), status (choices), disposal_type (choices), applicant (UUID), department (UUID), request_date_from/to |

*注: 所有过滤器自动支持 created_at_from/to, updated_at_from/to, created_by, is_deleted 等公共字段过滤*

---

## 4. 视图层设计

### 4.1 生命周期 ViewSet

所有 ViewSet 继承 `BaseModelViewSetWithBatch`，自动获得组织过滤、软删除、批量操作。

| ViewSet | 继承 | Serializer | Filter | 自定义Actions |
|---------|------|-----------|--------|--------------|
| PurchaseRequestViewSet | BaseModelViewSetWithBatch | List/Detail (动态) | PurchaseRequestFilter | submit() - 提交审批<br>approve() - 审批<br>my_requests() - 我的申请<br>pending_approvals() - 待我审批 |
| AssetReceiptViewSet | BaseModelViewSetWithBatch | AssetReceiptSerializer | AssetReceiptFilter | pass_inspection() - 验收通过<br>reject_inspection() - 验收不通过 |
| MaintenanceViewSet | BaseModelViewSetWithBatch | MaintenanceSerializer | MaintenanceFilter | assign() - 派单<br>complete() - 完成维修 |
| MaintenancePlanViewSet | BaseModelViewSetWithBatch | MaintenancePlanSerializer | BaseModelFilter | generate_tasks() - 手动生成任务<br>active_plans() - 启用的计划 |
| MaintenanceTaskViewSet | BaseModelViewSetWithBatch | MaintenanceTaskSerializer | MaintenanceTaskFilter | start() - 开始任务<br>complete() - 完成任务<br>my_tasks() - 我的任务 |
| DisposalRequestViewSet | BaseModelViewSetWithBatch | DisposalRequestSerializer | DisposalRequestFilter | submit_appraisal() - 提交鉴定<br>complete_appraisal() - 完成鉴定<br>execute() - 执行处置 |

*注: 所有 ViewSet 自动提供 list, create, retrieve, update, destroy, batch-delete, batch-restore, deleted, restore 等标准 CRUD 操作*

---

## 5. 服务层设计

### 5.1 采购申请服务 (PurchaseRequestService)

```python
# apps/lifecycle/services/purchase_service.py

from typing import Dict
from django.db import transaction
from django.utils import timezone
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import PurchaseRequest, PurchaseRequestItem
from apps.m18_adapter.tasks import push_purchase_to_m18


class PurchaseRequestService(BaseCRUDService):
    """采购申请业务服务 - 继承 BaseCRUDService"""

    def __init__(self):
        super().__init__(PurchaseRequest)

    @staticmethod
    def generate_request_no() -> str:
        """生成申请单号"""
        from django.utils import timezone
        prefix = f"PR{timezone.now().strftime('%Y%m')}"
        last_no = PurchaseRequest.objects.filter(
            request_no__startswith=prefix
        ).order_by('-request_no').values_list('request_no', flat=True).first()
        if last_no:
            seq = int(last_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @transaction.atomic
    def create_with_items(self, user, data: Dict) -> PurchaseRequest:
        """创建采购申请（含明细）"""
        items_data = data.pop('items', [])

        # 使用基类的 create 方法
        purchase_request = self.create(
            data={
                'request_no': self.generate_request_no(),
                'applicant_id': user.id,
                'department_id': data.get('department_id'),
                'request_date': data.get('request_date'),
                'expected_date': data.get('expected_date'),
                'reason': data.get('reason'),
                'budget_amount': data.get('budget_amount'),
                'cost_center_id': data.get('cost_center_id'),
                'custom_fields': data.get('custom_fields', {}),
            },
            user=user
        )

        # 创建明细
        for idx, item_data in enumerate(items_data, 1):
            PurchaseRequestItem.objects.create(
                purchase_request=purchase_request,
                sequence=idx,
                asset_category_id=item_data.get('asset_category_id'),
                item_name=item_data.get('item_name'),
                specification=item_data.get('specification'),
                brand=item_data.get('brand'),
                quantity=item_data.get('quantity'),
                unit=item_data.get('unit'),
                unit_price=item_data.get('unit_price'),
                total_amount=item_data.get('quantity', 0) * item_data.get('unit_price', 0),
                suggested_supplier=item_data.get('suggested_supplier'),
                remark=item_data.get('remark', ''),
                organization_id=purchase_request.organization_id,
                created_by=user,
            )

        return purchase_request

    @transaction.atomic
    def submit_for_approval(self, request_id: int) -> PurchaseRequest:
        """提交审批"""
        request = self.get(request_id)
        request.status = 'submitted'
        request.save()

        # 启动工作流
        from apps.workflows.services import WorkflowService
        workflow = WorkflowService.start_workflow(
            workflow_code='purchase_approval',
            entity_id=request.id,
            initiator=request.applicant
        )

        return request

    @transaction.atomic
    def approve_request(self, request_id: int, approver, approved: bool, comment: str = None) -> PurchaseRequest:
        """审批采购申请"""
        request = self.get(request_id)

        if approved:
            request.status = 'approved'
            request.approved_by = approver
            request.approved_at = timezone.now()

            # 审批通过后推送M18
            push_purchase_to_m18.delay(request.id)
        else:
            request.status = 'rejected'

        request.save()
        return request

    def sync_m18_status(self, request_id: int, m18_status: str, m18_order_no: str = None) -> PurchaseRequest:
        """同步M18状态"""
        request = self.get(request_id)

        if m18_order_no:
            request.m18_purchase_order_no = m18_order_no

        request.m18_sync_status = m18_status

        # 根据M18状态更新本地状态
        status_mapping = {
            'processing': 'processing',
            'completed': 'completed',
        }
        if m18_status in status_mapping:
            request.status = status_mapping[m18_status]

        request.save()
        return request
```

### 5.2 资产入库服务 (AssetReceiptService)

```python
# apps/lifecycle/services/receipt_service.py

from typing import Dict
from django.db import transaction
from django.utils import timezone
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import AssetReceipt, AssetReceiptItem
from apps.assets.models import Asset
from apps.assets.services import AssetService


class AssetReceiptService(BaseCRUDService):
    """资产入库业务服务 - 继承 BaseCRUDService"""

    def __init__(self):
        super().__init__(AssetReceipt)

    @staticmethod
    def generate_receipt_no() -> str:
        """生成验收单号"""
        from django.utils import timezone
        prefix = f"RC{timezone.now().strftime('%Y%m')}"
        last_no = AssetReceipt.objects.filter(
            receipt_no__startswith=prefix
        ).order_by('-receipt_no').values_list('receipt_no', flat=True).first()
        if last_no:
            seq = int(last_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @transaction.atomic
    def create_with_items(self, user, data: Dict) -> AssetReceipt:
        """创建验收单（含明细）"""
        items_data = data.pop('items', [])

        # 使用基类的 create 方法
        receipt = self.create(
            data={
                'receipt_no': self.generate_receipt_no(),
                'receipt_date': data.get('receipt_date'),
                'receipt_type': data.get('receipt_type', 'purchase'),
                'purchase_request_id': data.get('purchase_request_id'),
                'm18_purchase_order_no': data.get('m18_purchase_order_no'),
                'supplier': data.get('supplier'),
                'delivery_no': data.get('delivery_no'),
                'receiver_id': user.id,
                'custom_fields': data.get('custom_fields', {}),
            },
            user=user
        )

        # 创建明细
        for idx, item_data in enumerate(items_data, 1):
            AssetReceiptItem.objects.create(
                asset_receipt=receipt,
                sequence=idx,
                asset_category_id=item_data.get('asset_category_id'),
                item_name=item_data.get('item_name'),
                specification=item_data.get('specification'),
                brand=item_data.get('brand'),
                ordered_quantity=item_data.get('ordered_quantity'),
                received_quantity=item_data.get('received_quantity'),
                qualified_quantity=item_data.get('received_quantity'),
                defective_quantity=item_data.get('defective_quantity', 0),
                unit_price=item_data.get('unit_price'),
                total_amount=item_data.get('received_quantity', 0) * item_data.get('unit_price', 0),
                remark=item_data.get('remark', ''),
                organization_id=receipt.organization_id,
                created_by=user,
            )

        return receipt

    @transaction.atomic
    def pass_inspection(self, receipt_id: int, inspector, inspection_result: str = None) -> AssetReceipt:
        """验收通过"""
        receipt = self.get(receipt_id)
        receipt.status = 'passed'
        receipt.inspector = inspector
        receipt.inspection_result = inspection_result
        receipt.passed_at = timezone.now()
        receipt.save()

        # 生成资产卡片
        self._generate_assets_from_receipt(receipt)

        return receipt

    def _generate_assets_from_receipt(self, receipt: AssetReceipt):
        """从验收单生成资产卡片"""
        for item in receipt.items.all():
            if item.qualified_quantity > 0 and not item.asset_generated:
                for i in range(item.qualified_quantity):
                    AssetService.create_asset_from_receipt(item, i + 1)

                item.asset_generated = True
                item.save()

    @transaction.atomic
    def reject_inspection(self, receipt_id: int, inspector, reason: str) -> AssetReceipt:
        """验收不通过"""
        receipt = self.get(receipt_id)
        receipt.status = 'rejected'
        receipt.inspector = inspector
        receipt.inspection_result = reason
        receipt.save()
        return receipt
```

### 5.3 维护保养服务 (MaintenanceService)

```python
# apps/lifecycle/services/maintenance_service.py

from typing import Dict, List
from django.db import transaction
from django.utils import timezone
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import Maintenance, MaintenancePlan, MaintenanceTask
from apps.assets.models import Asset


class MaintenanceService(BaseCRUDService):
    """维护保养业务服务 - 继承 BaseCRUDService"""

    def __init__(self):
        super().__init__(Maintenance)

    @staticmethod
    def generate_maintenance_no() -> str:
        """生成维修单号"""
        from django.utils import timezone
        prefix = f"MT{timezone.now().strftime('%Y%m')}"
        last_no = Maintenance.objects.filter(
            maintenance_no__startswith=prefix
        ).order_by('-maintenance_no').values_list('maintenance_no', flat=True).first()
        if last_no:
            seq = int(last_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @transaction.atomic
    def create_request(self, user, data: Dict) -> Maintenance:
        """创建维修申请"""
        # 使用基类的 create 方法
        maintenance = self.create(
            data={
                'maintenance_no': self.generate_maintenance_no(),
                'asset_id': data.get('asset_id'),
                'reporter_id': user.id,
                'report_time': timezone.now(),
                'fault_description': data.get('fault_description'),
                'fault_photo_urls': data.get('fault_photo_urls', []),
                'priority': data.get('priority', 'normal'),
            },
            user=user
        )

        # 更新资产状态
        asset = maintenance.asset
        asset.status = 'maintenance'
        asset.save()

        return maintenance

    @transaction.atomic
    def assign_technician(self, maintenance_id: int, technician_id: int) -> Maintenance:
        """派单"""
        maintenance = self.get(maintenance_id)
        maintenance.status = 'assigned'
        maintenance.technician_id = technician_id
        maintenance.assigned_at = timezone.now()
        maintenance.save()
        return maintenance

    @transaction.atomic
    def complete_maintenance(self, maintenance_id: int, data: Dict) -> Maintenance:
        """完成维修"""
        maintenance = self.get(maintenance_id)
        maintenance.status = 'processing'
        maintenance.start_time = data.get('start_time')
        maintenance.end_time = timezone.now()
        maintenance.work_hours = data.get('work_hours')
        maintenance.fault_cause = data.get('fault_cause')
        maintenance.repair_method = data.get('repair_method')
        maintenance.replaced_parts = data.get('replaced_parts')
        maintenance.repair_result = data.get('repair_result')
        maintenance.labor_cost = data.get('labor_cost', 0)
        maintenance.material_cost = data.get('material_cost', 0)
        maintenance.other_cost = data.get('other_cost', 0)
        maintenance.total_cost = (
            maintenance.labor_cost +
            maintenance.material_cost +
            maintenance.other_cost
        )
        maintenance.save()

        # 更新资产状态
        asset = maintenance.asset
        asset.status = 'in_use'
        asset.save()

        return maintenance

    @staticmethod
    def create_maintenance_plan(user, data: Dict) -> MaintenancePlan:
        """创建保养计划"""
        plan_code = data.get('plan_code') or f"MP{timezone.now().strftime('%Y%m%H%M%S')}"

        plan = MaintenancePlan.objects.create(
            plan_code=plan_code,
            plan_name=data.get('plan_name'),
            target_type=data.get('target_type', 'category'),
            cycle_type=data.get('cycle_type'),
            cycle_value=data.get('cycle_value', 1),
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            remind_days_before=data.get('remind_days_before', 3),
            maintenance_content=data.get('maintenance_content'),
            estimated_hours=data.get('estimated_hours'),
            organization_id=user.organization_id,
            created_by=user,
        )

        # 设置关联对象
        if data.get('asset_category_ids'):
            plan.asset_categories.set(data['asset_category_ids'])
        if data.get('asset_ids'):
            plan.assets.set(data['asset_ids'])
        if data.get('location_ids'):
            plan.locations.set(data['location_ids'])
        if data.get('remind_user_ids'):
            plan.remind_users.set(data['remind_user_ids'])

        return plan

    @staticmethod
    def generate_maintenance_tasks():
        """生成保养任务（定时任务）"""
        from datetime import date, timedelta

        active_plans = MaintenancePlan.objects.filter(status='active')

        for plan in active_plans:
            # 计算下次保养日期
            next_date = MaintenanceService._calculate_next_date(plan)

            if next_date:
                # 获取需要保养的资产
                assets = MaintenanceService._get_plan_assets(plan)

                for asset in assets:
                    # 检查是否已有任务
                    existing = MaintenanceTask.objects.filter(
                        plan=plan,
                        asset=asset,
                        scheduled_date=next_date
                    ).exists()

                    if not existing:
                        MaintenanceTask.objects.create(
                            task_no=f"TSK{timezone.now().strftime('%Y%m%d%H%M%S')}{asset.id}",
                            plan=plan,
                            asset=asset,
                            scheduled_date=next_date,
                            deadline_date=next_date + timedelta(days=7),
                            status='pending',
                            organization_id=plan.organization_id,
                        )

    @staticmethod
    def _calculate_next_date(plan: MaintenancePlan) -> date:
        """计算下次保养日期"""
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta

        today = date.today()

        if plan.end_date and today > plan.end_date:
            return None

        cycle_map = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': relativedelta(months=1),
            'quarterly': relativedelta(months=3),
            'yearly': relativedelta(years=1),
        }

        if plan.cycle_type in cycle_map:
            # 简化逻辑，实际应根据上次任务日期计算
            return today + cycle_map[plan.cycle_type] * plan.cycle_value

        return None

    @staticmethod
    def _get_plan_assets(plan: MaintenancePlan) -> List[Asset]:
        """获取计划关联的资产"""
        if plan.target_type == 'category':
            return Asset.objects.filter(
                category__in=plan.asset_categories.all(),
                status__in=['in_use', 'idle'],
                organization_id=plan.organization_id
            )
        elif plan.target_type == 'asset':
            return list(plan.assets.filter(status__in=['in_use', 'idle']))
        elif plan.target_type == 'location':
            return Asset.objects.filter(
                location__in=plan.locations.all(),
                status__in=['in_use', 'idle'],
                organization_id=plan.organization_id
            )
        return []
```

### 5.4 报废处置服务 (DisposalService)

```python
# apps/lifecycle/services/disposal_service.py

from typing import Dict, List
from django.db import transaction
from django.utils import timezone
from apps.common.services.base_crud import BaseCRUDService
from apps.lifecycle.models import DisposalRequest, DisposalItem
from apps.assets.models import Asset
from apps.finance_integration.services import VoucherService


class DisposalService(BaseCRUDService):
    """报废处置业务服务 - 继承 BaseCRUDService"""

    def __init__(self):
        super().__init__(DisposalRequest)

    @staticmethod
    def generate_request_no() -> str:
        """生成报废单号"""
        from django.utils import timezone
        prefix = f"DS{timezone.now().strftime('%Y%m')}"
        last_no = DisposalRequest.objects.filter(
            request_no__startswith=prefix
        ).order_by('-request_no').values_list('request_no', flat=True).first()
        if last_no:
            seq = int(last_no[-4:]) + 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @transaction.atomic
    def create_with_assets(self, user, data: Dict) -> DisposalRequest:
        """创建报废申请（含资产明细）"""
        asset_ids = data.pop('asset_ids', [])

        # 使用基类的 create 方法
        request = self.create(
            data={
                'request_no': self.generate_request_no(),
                'applicant_id': user.id,
                'department_id': data.get('department_id'),
                'request_date': timezone.now().date(),
                'disposal_type': data.get('disposal_type', 'scrap'),
                'disposal_reason': data.get('disposal_reason'),
                'reason_type': data.get('reason_type'),
                'custom_fields': data.get('custom_fields', {}),
            },
            user=user
        )

        # 添加资产明细
        for idx, asset_id in enumerate(asset_ids, 1):
            asset = Asset.objects.get(id=asset_id)
            DisposalItem.objects.create(
                disposal_request=request,
                sequence=idx,
                asset=asset,
                original_value=asset.original_value,
                accumulated_depreciation=asset.accumulated_depreciation,
                net_value=asset.net_value,
                organization_id=request.organization_id,
            )

        return request

    @transaction.atomic
    def submit_for_appraisal(self, request_id: int) -> DisposalRequest:
        """提交鉴定"""
        request = self.get(request_id)
        request.status = 'appraising'
        request.save()

        # 更新资产状态
        for item in request.items.all():
            item.asset.status = 'scrapped'
            item.asset.save()

        return request

    @transaction.atomic
    def complete_appraisal(self, item_id: int, appraiser, data: Dict) -> DisposalItem:
        """完成鉴定"""
        item = DisposalItem.objects.get(id=item_id)
        item.appraisal_result = data.get('appraisal_result')
        item.residual_value = data.get('residual_value', 0)
        item.appraised_by = appraiser
        item.appraised_at = timezone.now()
        item.save()

        # 检查是否所有明细都已完成鉴定
        request = item.disposal_request
        if request.items.filter(appraised_by__isnull=True).count() == 0:
            request.status = 'approved'
            request.save()

        return item

    @transaction.atomic
    def execute_disposal(self, request_id: int, executor, data: Dict) -> DisposalRequest:
        """执行处置"""
        request = self.get(request_id)
        request.status = 'executing'

        for item in request.items.all():
            item_data = next(
                (i for i in data.get('items', []) if i.get('item_id') == item.id),
                {}
            )
            item.disposal_executed = True
            item.executed_at = timezone.now()
            item.actual_residual_value = item_data.get('actual_residual_value', 0)
            item.buyer_info = item_data.get('buyer_info', '')
            item.save()

            # 更新资产状态
            asset = item.asset
            asset.status = 'disposed'
            asset.disposal_date = timezone.now().date()
            asset.save()

        request.status = 'completed'
        request.save()

        # 生成财务凭证
        VoucherService.generate_disposal_voucher(request)

        return request
```

---

## 6. 定时任务配置

```python
# apps/lifecycle/tasks.py

from celery import shared_task
from apps.lifecycle.services import MaintenanceService


@shared_task
def generate_daily_maintenance_tasks():
    """每日生成保养任务"""
    MaintenanceService.generate_maintenance_tasks()


@shared_task
def check_overdue_maintenance_tasks():
    """检查逾期保养任务"""
    from apps.lifecycle.models import MaintenanceTask
    from django.utils import timezone

    overdue_tasks = MaintenanceTask.objects.filter(
        status__in=['pending'],
        deadline_date__lt=timezone.now().date()
    )

    for task in overdue_tasks:
        task.status = 'overdue'
        task.save()

        # 发送逾期提醒
        # TODO: 调用通知服务


@shared_task
def send_reminder_notifications():
    """发送保养提醒通知"""
    from apps.lifecycle.models import MaintenanceTask
    from datetime import date, timedelta

    remind_date = date.today() + timedelta(days=3)

    tasks_to_remind = MaintenanceTask.objects.filter(
        status='pending',
        scheduled_date=remind_date
    ).select_related('plan', 'executor').prefetch_related('plan__remind_users')

    for task in tasks_to_remind:
        # TODO: 调用通知服务发送提醒
        pass
```

```python
# config/celery.py - Celery Beat配置

from celery.schedules import crontab

beat_schedule = {
    'generate-daily-maintenance-tasks': {
        'task': 'apps.lifecycle.tasks.generate_daily_maintenance_tasks',
        'schedule': crontab(hour=1, minute=0),  # 每天凌晨1点
    },
    'check-overdue-maintenance-tasks': {
        'task': 'apps.lifecycle.tasks.check_overdue_maintenance_tasks',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
    'send-reminder-notifications': {
        'task': 'apps.lifecycle.tasks.send_reminder_notifications',
        'schedule': crontab(hour=8, minute=0),  # 每天早上8点
    },
}
```

---

## 7. 信号处理器

```python
# apps/lifecycle/signals.py

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from apps.lifecycle.models import Maintenance, DisposalRequest
from apps.assets.models import Asset


@receiver(post_save, sender=Maintenance)
def update_asset_status_on_maintenance(sender, instance, created, **kwargs):
    """维修完成后更新资产状态"""
    if instance.status == 'completed':
        asset = instance.asset
        asset.status = 'in_use'
        asset.save()


@receiver(post_save, sender=DisposalRequest)
def update_asset_status_on_disposal(sender, instance, created, **kwargs):
    """报废申请审批通过后更新资产状态"""
    if instance.status == 'approved':
        for item in instance.items.all():
            asset = item.asset
            asset.status = 'scrapped'
            asset.save()
```

---

## 8. 权限配置

```python
# apps/lifecycle/permissions.py

from rest_framework import permissions


class IsPurchaseRequestApplicant(permissions.BasePermission):
    """采购申请申请人权限"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.applicant == request.user or request.user.is_admin


class IsMaintenanceRequesterOrTechnician(permissions.BasePermission):
    """维修报修人或维修人员权限"""
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.reporter == request.user or obj.technician == request.user
```

---

## 9. 路由配置

```python
# apps/lifecycle/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PurchaseRequestViewSet, AssetReceiptViewSet,
    MaintenanceViewSet, MaintenancePlanViewSet, MaintenanceTaskViewSet,
    DisposalRequestViewSet
)

router = DefaultRouter()
router.register(r'purchase-requests', PurchaseRequestViewSet, basename='purchaserequest')
router.register(r'asset-receipts', AssetReceiptViewSet, basename='assetreceipt')
router.register(r'maintenance', MaintenanceViewSet, basename='maintenance')
router.register(r'maintenance-plans', MaintenancePlanViewSet, basename='maintenanceplan')
router.register(r'maintenance-tasks', MaintenanceTaskViewSet, basename='maintenancetask')
router.register(r'disposal-requests', DisposalRequestViewSet, basename='disposalrequest')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## 10. 后续任务

1. 实现工作流集成服务
2. 实现财务凭证生成集成
3. 实现通知服务集成
4. 编写单元测试
5. API性能优化

---

## 11. 核心变更总结

### 11.1 公共基类继承

所有生命周期模块的代码现在继承公共基类，获得统一能力：

1. **序列化器**：继承 `BaseModelSerializer` / `BaseModelWithAuditSerializer`
   - 自动处理公共字段（id, organization, created_at, updated_at, created_by, custom_fields）
   - 自动处理软删除字段（is_deleted, deleted_at）
   - 完整审计信息（updated_by, deleted_by）

2. **ViewSet**：继承 `BaseModelViewSetWithBatch`
   - 自动应用组织隔离和软删除过滤
   - 自动设置审计字段（created_by）
   - 自动使用软删除
   - 提供批量操作接口（batch-delete, batch-restore, batch-update）
   - 提供已删除记录查询接口（deleted, restore）

3. **Service**：继承 `BaseCRUDService`
   - 统一的 CRUD 操作（create, update, delete, restore, get, query, paginate）
   - 自动处理组织隔离
   - 自动处理软删除
   - 批量操作支持

4. **过滤器**：继承 `BaseModelFilter`
   - 自动支持公共字段过滤（created_at, updated_at, created_by, is_deleted）
   - 时间范围查询（created_at_from/to, updated_at_from/to）
   - 统一的字段命名规范

### 11.2 代码简化效果

**修改前**（手动实现所有公共逻辑）：
- 序列化器需要手动定义所有公共字段
- ViewSet 需要手动实现组织过滤、软删除、审计
- Service 需要手动处理 CRUD、组织隔离
- 过滤器需要重复定义公共过滤字段

**修改后**（继承公共基类）：
- 序列化器只需定义业务字段，公共字段自动继承
- ViewSet 只需定义 queryset 和 serializer_class，公共功能自动获得
- Service 只需调用基类方法，专注业务逻辑
- 过滤器只需定义业务过滤字段，公共过滤自动继承

### 11.3 统一性提升

所有模块（accounts, assets, lifecycle, inventory, procurement, workflows）现在：
- 使用相同的序列化器基类
- 使用相同的 ViewSet 基类
- 使用相同的 Service 基类
- 使用相同的过滤器基类
- 统一的错误处理和响应格式
- 统一的批量操作接口
- 统一的组织隔离和软删除逻辑

这将大大提高代码的可维护性、一致性和开发效率。

---

## 12. 测试用例

### 12.1 模型测试

#### 12.1.1 组织隔离测试
```python
def test_purchase_request_org_isolation(self):
    """测试采购申请的组织隔离"""
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")
    user1 = self.create_user(organization=org1)
    user2 = self.create_user(organization=org2)

    # 创建采购申请
    request1 = PurchaseRequestService().create_with_items(user1, {
        'department_id': org1.departments.first().id,
        'request_date': '2024-01-01',
        'reason': '测试需求',
        'items': [
            {
                'asset_category_id': self.asset_category.id,
                'item_name': '测试资产',
                'specification': '规格1',
                'quantity': 1,
                'unit': '个',
                'unit_price': 1000
            }
        ]
    })

    # 验证组织隔离
    self.assertEqual(request1.organization, org1)
    self.assertEqual(request1.created_by, user1)
    self.assertEqual(PurchaseRequest.objects.filter(organization=org1).count(), 1)
    self.assertEqual(PurchaseRequest.objects.filter(organization=org2).count(), 0)

def test_asset_receipt_soft_delete(self):
    """测试资产验收单的软删除"""
    receipt = self.create_asset_receipt()

    # 软删除
    receipt.soft_delete()

    # 验证软删除
    self.assertTrue(receipt.is_deleted)
    self.assertIsNotNone(receipt.deleted_at)
    self.assertEqual(AssetReceipt.objects.filter(organization=receipt.organization).count(), 0)
    self.assertEqual(AssetReceipt.objects.filter(is_deleted=False, organization=receipt.organization).count(), 0)

    # 恢复
    receipt.restore()
    self.assertFalse(receipt.is_deleted)
    self.assertIsNone(receipt.deleted_at)

def test_maintenance_audit_fields(self):
    """测试维修记录的审计字段"""
    maintenance = self.create_maintenance()
    old_created_by = maintenance.created_by
    old_created_at = maintenance.created_at

    # 修改记录
    maintenance.status = 'completed'
    maintenance.save()

    # 验证审计字段
    maintenance.refresh_from_db()
    self.assertEqual(maintenance.created_by, old_created_by)
    self.assertEqual(maintenance.created_at, old_created_at)
    self.assertIsNotNone(maintenance.updated_at)
    self.assertIsNotNone(maintenance.updated_by)

def test_disposal_custom_fields(self):
    """测试报废申请的自定义字段"""
    custom_data = {
        'custom_field_1': '自定义值1',
        'custom_field_2': 123,
        'nested_field': {'key': 'value'}
    }

    disposal_request = self.create_disposal_request()
    disposal_request.custom_fields = custom_data
    disposal_request.save()

    # 验证自定义字段
    disposal_request.refresh_from_db()
    self.assertEqual(disposal_request.custom_fields, custom_data)
    self.assertEqual(disposal_request.custom_fields['custom_field_1'], '自定义值1')
    self.assertEqual(disposal_request.custom_fields['nested_field']['key'], 'value')

def test_crud_service_batch_operations(self):
    """测试采购申请服务的批量操作"""
    org = self.create_organization()
    user = self.create_user(organization=org)
    department = org.departments.first()

    # 创建多个采购申请
    requests = []
    for i in range(3):
        request = PurchaseRequestService().create_with_items(user, {
            'department_id': department.id,
            'request_date': '2024-01-01',
            'reason': f'测试需求{i}',
            'items': [
                {
                    'asset_category_id': self.asset_category.id,
                    'item_name': f'测试资产{i}',
                    'quantity': 1,
                    'unit': '个',
                    'unit_price': 1000
                }
            ]
        })
        requests.append(request)

    request_ids = [r.id for r in requests]

    # 测试批量查询
    result = PurchaseRequestService().query(ids=request_ids)
    self.assertEqual(len(result['results']), 3)

    # 测试批量删除
    result = PurchaseRequestService().batch_delete(request_ids)
    self.assertEqual(result['succeeded'], 3)
    self.assertEqual(result['failed'], 0)

    # 验证软删除
    for request in requests:
        self.assertTrue(request.is_deleted)
```

#### 12.1.2 边界条件测试
```python
def test_empty_value_handling(self):
    """测试空值处理"""
    request = PurchaseRequestService().create_with_items(self.user, {
        'department_id': self.department.id,
        'request_date': '2024-01-01',
        'reason': '测试需求',
        'items': [
            {
                'asset_category_id': self.asset_category.id,
                'item_name': '',
                'specification': None,
                'quantity': 0,
                'unit': '',
                'unit_price': 0
            }
        ]
    })

    # 验证空值处理
    self.assertIsNotNone(request.request_no)
    self.assertEqual(request.status, 'draft')
    self.assertEqual(request.items.first().quantity, 0)
    self.assertEqual(request.items.first().unit_price, 0)

def test_concurrent_operations(self):
    """测试并发操作"""
    receipt = self.create_asset_receipt()

    # 模拟并发更新
    def update_receipt():
        receipt.status = 'passed'
        receipt.save()

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=update_receipt)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 验证并发后的状态
    receipt.refresh_from_db()
    self.assertIn(receipt.status, ['passed'])

def test_data_consistency(self):
    """测试数据一致性"""
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")

    # 创建组织隔离的测试数据
    request1 = self.create_purchase_request(organization=org1)
    request2 = self.create_purchase_request(organization=org2)

    # 验证组织隔离
    self.assertNotEqual(list(PurchaseRequest.objects.all()), [])
    self.assertNotEqual(PurchaseRequest.objects.filter(organization=org1), [])
    self.assertNotEqual(PurchaseRequest.objects.filter(organization=org2), [])

    # 验证关联数据也遵循组织隔离
    self.assertEqual(PurchaseRequestItem.objects.filter(purchase_request=request1).count(), 1)
    self.assertEqual(PurchaseRequestItem.objects.filter(purchase_request=request2).count(), 1)
```

### 12.2 API测试

#### 12.2.1 采购申请API测试
```python
def test_purchase_request_creation_api(self):
    """测试创建采购申请API"""
    org = self.create_organization()
    user = self.create_user(organization=org)
    department = org.departments.first()

    data = {
        'department_id': department.id,
        'request_date': '2024-01-01',
        'reason': '测试需求',
        'items': [
            {
                'asset_category_id': self.asset_category.id,
                'item_name': '测试资产',
                'specification': '规格1',
                'quantity': 1,
                'unit': '个',
                'unit_price': 1000
            }
        ]
    }

    response = self.client.post('/api/lifecycle/purchase-requests/', data, format='json')
    self.assertEqual(response.status_code, 201)

    request = PurchaseRequest.objects.get(id=response.data['data']['id'])
    self.assertEqual(request.organization, org)
    self.assertEqual(request.status, 'draft')

def test_purchase_request_approval_flow(self):
    """测试采购申请审批流程"""
    request = self.create_purchase_request()
    approver = self.create_user()

    # 提交审批
    response = self.client.post(f'/api/lifecycle/purchase-requests/{request.id}/submit/')
    self.assertEqual(response.status_code, 200)

    request.refresh_from_db()
    self.assertEqual(request.status, 'submitted')

    # 审批
    response = self.client.post(f'/api/lifecycle/purchase-requests/{request.id}/approve/', {
        'approved': True,
        'comment': '批准'
    })
    self.assertEqual(response.status_code, 200)

    request.refresh_from_db()
    self.assertEqual(request.status, 'approved')

def test_purchase_request_batch_operations(self):
    """测试采购申请批量操作"""
    requests = [self.create_purchase_request() for _ in range(3)]
    request_ids = [str(r.id) for r in requests]

    # 批量删除
    response = self.client.post('/api/lifecycle/purchase-requests/batch-delete/', {
        'ids': request_ids
    }, format='json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data['summary']['succeeded'], 3)

    # 验证软删除
    for request in requests:
        self.assertTrue(request.is_deleted)

def test_purchase_request_query_with_filters(self):
    """测试采购申请查询过滤"""
    # 创建测试数据
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")
    user1 = self.create_user(organization=org1)
    user2 = self.create_user(organization=org2)

    request1 = self.create_purchase_request(organization=org1, applicant=user1, status='approved')
    request2 = self.create_purchase_request(organization=org2, applicant=user2, status='submitted')

    # 测试按状态过滤
    response = self.client.get('/api/lifecycle/purchase-requests/', {'status': 'approved'})
    self.assertEqual(response.data['data']['count'], 1)

    # 测试按申请人过滤
    response = self.client.get(f'/api/lifecycle/purchase-requests/', {'applicant': str(user1.id)})
    self.assertEqual(response.data['data']['count'], 1)

    # 测试按日期范围过滤
    response = self.client.get('/api/lifecycle/purchase-requests/', {
        'request_date_from': '2024-01-01',
        'request_date_to': '2024-12-31'
    })
    self.assertEqual(response.data['data']['count'], 2)
```

#### 12.2.2 维护保养API测试
```python
def test_maintenance_creation_api(self):
    """测试创建维修记录API"""
    data = {
        'asset_id': self.asset.id,
        'fault_description': '测试故障',
        'fault_photo_urls': ['url1', 'url2'],
        'priority': 'high'
    }

    response = self.client.post('/api/lifecycle/maintenance/', data, format='json')
    self.assertEqual(response.status_code, 201)

    maintenance = Maintenance.objects.get(id=response.data['data']['id'])
    self.assertEqual(maintenance.asset, self.asset)
    self.assertEqual(maintenance.status, 'reported')

def test_maintenance_task_assignment(self):
    """测试维修任务派单API"""
    maintenance = self.create_maintenance()
    technician = self.create_user()

    response = self.client.post(f'/api/lifecycle/maintenance/{maintenance.id}/assign/', {
        'technician_id': technician.id
    })
    self.assertEqual(response.status_code, 200)

    maintenance.refresh_from_db()
    self.assertEqual(maintenance.technician, technician)
    self.assertEqual(maintenance.status, 'assigned')

def test_maintenance_plan_generation(self):
    """测试保养计划生成任务API"""
    plan = self.create_maintenance_plan()

    response = self.client.post(f'/api/lifecycle/maintenance-plans/{plan.id}/generate-tasks/')
    self.assertEqual(response.status_code, 200)

    # 验证任务是否生成
    tasks = MaintenanceTask.objects.filter(plan=plan)
    self.assertTrue(tasks.exists())

def test_disposal_request_appraisal(self):
    """测试报废鉴定API"""
    disposal = self.create_disposal_request()
    item = disposal.items.first()

    response = self.client.post(f'/api/lifecycle/disposal-requests/{disposal.id}/submit-appraisal/')
    self.assertEqual(response.status_code, 200)

    disposal.refresh_from_db()
    self.assertEqual(disposal.status, 'appraising')

    # 完成鉴定
    response = self.client.post(f'/api/lifecycle/disposal-requests/{disposal.id}/complete-appraisal/', {
        'item_id': item.id,
        'appraisal_result': '鉴定完成',
        'residual_value': 100
    })
    self.assertEqual(response.status_code, 200)

    item.refresh_from_db()
    self.assertEqual(item.appraisal_result, '鉴定完成')
```

### 12.3 边界条件测试

#### 12.3.1 权限测试
```python
def test_organization_isolation_permissions(self):
    """测试组织隔离权限"""
    org1 = self.create_organization(name="公司A")
    org2 = self.create_organization(name="公司B")
    user1 = self.create_user(organization=org1)
    user2 = self.create_user(organization=org2)

    # 创建测试数据
    request1 = self.create_purchase_request(organization=org1, applicant=user1)
    request2 = self.create_purchase_request(organization=org2, applicant=user2)

    # 验证用户只能访问自己组织的数据
    self.client.force_authenticate(user=user2)
    response = self.client.get('/api/lifecycle/purchase-requests/')
    self.assertEqual(response.data['data']['count'], 1)
    self.assertEqual(response.data['data']['results'][0]['id'], str(request2.id))

def test_permission_enforcement(self):
    """测试权限执行"""
    # 创建普通用户和管理员
    user = self.create_user()
    admin = self.create_user(is_staff=True)

    # 创建测试数据
    request = self.create_purchase_request(applicant=self.user)

    # 普通用户尝试修改其他人的申请
    self.client.force_authenticate(user=user)
    response = self.client.patch(f'/api/lifecycle/purchase-requests/{request.id}/', {
        'status': 'approved'
    })
    self.assertEqual(response.status_code, 403)  # 禁止访问

def test_empty_value_handling_api(self):
    """测试API空值处理"""
    data = {
        'asset_id': self.asset.id,
        'fault_description': '',
        'fault_photo_urls': [],
        'priority': 'normal'
    }

    response = self.client.post('/api/lifecycle/maintenance/', data, format='json')
    self.assertEqual(response.status_code, 201)

    maintenance = Maintenance.objects.get(id=response.data['data']['id'])
    self.assertEqual(maintenance.fault_description, '')
    self.assertEqual(maintenance.fault_photo_urls, [])

def test_concurrent_request_handling(self):
    """测试并发请求处理"""
    org = self.create_organization()
    user = self.create_user(organization=org)

    def create_request():
        data = {
            'department_id': org.departments.first().id,
            'request_date': '2024-01-01',
            'reason': '并发测试',
            'items': [
                {
                    'asset_category_id': self.asset_category.id,
                    'item_name': '测试资产',
                    'quantity': 1,
                    'unit': '个',
                    'unit_price': 1000
                }
            ]
        }
        response = self.client.post('/api/lifecycle/purchase-requests/', data, format='json')
        return response

    # 并发创建请求
    threads = []
    responses = []

    def capture_response():
        response = create_request()
        responses.append(response)

    for _ in range(10):
        thread = threading.Thread(target=capture_response)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # 验证所有请求都成功
    for response in responses:
        self.assertEqual(response.status_code, 201)

    # 验证单号唯一性
    request_nos = [PurchaseRequest.objects.get(id=r.data['data']['id']).request_no
                   for r in responses]
    self.assertEqual(len(set(request_nos)), 10)  # 所有单号都不同

def test_data_consistency_across_operations(self):
    """测试跨操作数据一致性"""
    # 创建完整的数据流程
    org = self.create_organization()
    user = self.create_user(organization=org)

    # 1. 创建采购申请
    request = PurchaseRequestService().create_with_items(user, {
        'department_id': org.departments.first().id,
        'request_date': '2024-01-01',
        'reason': '测试需求',
        'items': [
            {
                'asset_category_id': self.asset_category.id,
                'item_name': '测试资产',
                'quantity': 1,
                'unit_price': 1000
            }
        ]
    })

    # 2. 创建验收单
    receipt = AssetReceiptService().create_with_items(user, {
        'receipt_date': '2024-01-02',
        'items': [
            {
                'asset_category_id': self.asset_category.id,
                'item_name': '测试资产',
                'ordered_quantity': 1,
                'received_quantity': 1,
                'unit_price': 1000
            }
        ]
    })

    # 3. 验证关联关系
    self.assertEqual(request.organization, org)
    self.assertEqual(receipt.organization, org)

    # 4. 创建维修记录
    maintenance = MaintenanceService().create_request(user, {
        'asset_id': self.asset.id,
        'fault_description': '测试故障'
    })

    # 5. 验证所有数据都属于同一组织
    self.assertEqual(maintenance.organization, org)
    self.assertEqual(maintenance.asset.organization, org)

    # 6. 软删除测试
    request.soft_delete()
    self.assertTrue(request.is_deleted)
    self.assertEqual(request.organization, org)  # 组织信息仍然保持
```

---

**测试用例总结**：

以上测试用例覆盖了资产生命周期管理模块的所有核心功能点：

1. **模型测试**：
   - 组织隔离验证
   - 软删除和恢复
   - 审计字段追踪
   - 自定义字段存储
   - 批量操作支持

2. **API测试**：
   - 采购申请全流程测试
   - 维护保养操作测试
   - 报废处置流程测试
   - 批量操作接口测试
   - 查询过滤功能测试

3. **边界条件测试**：
   - 组织隔离权限验证
   - 空值处理验证
   - 并发操作处理
   - 数据一致性验证
   - 权限边界测试

所有测试用例都遵循GZEAMS的公共基类架构规范，确保了系统的稳定性、安全性和一致性。

---

## 13. API接口规范

### 13.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "request_no": "PR2026010001",
        "status": "draft",
        ...
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 50,
        "next": "https://api.example.com/api/lifecycle/purchase-requests/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "request_no": "PR2026010001",
                "status": "draft",
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
            "items.0.item_name": ["该字段不能为空"],
            "budget_amount": ["金额必须大于0"]
        }
    }
}
```

### 13.2 采购申请接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **申请列表** | GET | `/api/lifecycle/purchase-requests/` | 分页查询采购申请列表，支持状态、申请人、日期过滤 |
| **申请详情** | GET | `/api/lifecycle/purchase-requests/{id}/` | 获取采购申请详情（含明细） |
| **创建申请** | POST | `/api/lifecycle/purchase-requests/` | 创建新的采购申请（含明细） |
| **更新申请** | PUT | `/api/lifecycle/purchase-requests/{id}/` | 完整更新采购申请 |
| **部分更新** | PATCH | `/api/lifecycle/purchase-requests/{id}/` | 部分更新采购申请 |
| **提交审批** | POST | `/api/lifecycle/purchase-requests/{id}/submit/` | 提交采购申请审批 |
| **审批申请** | POST | `/api/lifecycle/purchase-requests/{id}/approve/` | 审批采购申请 |
| **我的申请** | GET | `/api/lifecycle/purchase-requests/my_requests/` | 查询当前用户的申请列表 |
| **待我审批** | GET | `/api/lifecycle/purchase-requests/pending_approvals/` | 查询需要当前用户审批的申请 |

### 13.3 资产验收接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **验收单列表** | GET | `/api/lifecycle/asset-receipts/` | 分页查询资产验收单列表 |
| **验收单详情** | GET | `/api/lifecycle/asset-receipts/{id}/` | 获取资产验收单详情（含明细） |
| **创建验收单** | POST | `/api/lifecycle/asset-receipts/` | 创建新的资产验收单 |
| **验收通过** | POST | `/api/lifecycle/asset-receipts/{id}/pass_inspection/` | 验收通过，自动生成资产卡片 |
| **验收不通过** | POST | `/api/lifecycle/asset-receipts/{id}/reject_inspection/` | 验收不通过 |

### 13.4 维护保养接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **维修记录列表** | GET | `/api/lifecycle/maintenance/` | 分页查询维修记录列表 |
| **维修详情** | GET | `/api/lifecycle/maintenance/{id}/` | 获取维修记录详情 |
| **创建维修申请** | POST | `/api/lifecycle/maintenance/` | 创建新的维修申请 |
| **派单** | POST | `/api/lifecycle/maintenance/{id}/assign/` | 指派维修人员 |
| **完成维修** | POST | `/api/lifecycle/maintenance/{id}/complete/` | 完成维修任务 |

### 13.5 保养管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **保养计划列表** | GET | `/api/lifecycle/maintenance-plans/` | 分页查询保养计划列表 |
| **保养详情** | GET | `/api/lifecycle/maintenance-plans/{id}/` | 获取保养计划详情 |
| **创建保养计划** | POST | `/api/lifecycle/maintenance-plans/` | 创建新的保养计划 |
| **生成任务** | POST | `/api/lifecycle/maintenance-plans/{id}/generate_tasks/` | 手动生成保养任务 |
| **启用的计划** | GET | `/api/lifecycle/maintenance-plans/active_plans/` | 查询启用的保养计划 |

### 13.6 维修任务接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **任务列表** | GET | `/api/lifecycle/maintenance-tasks/` | 分页查询维修任务列表 |
| **任务详情** | GET | `/api/lifecycle/maintenance-tasks/{id}/` | 获取维修任务详情 |
| **开始任务** | POST | `/api/lifecycle/maintenance-tasks/{id}/start/` | 开始执行维修任务 |
| **完成任务** | POST | `/api/lifecycle/maintenance-tasks/{id}/complete/` | 完成维修任务 |
| **我的任务** | GET | `/api/lifecycle/maintenance-tasks/my_tasks/` | 查询当前用户的任务列表 |

### 13.7 报废处置接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **报废申请列表** | GET | `/api/lifecycle/disposal-requests/` | 分页查询报废申请列表 |
| **报废详情** | GET | `/api/lifecycle/disposal-requests/{id}/` | 获取报废申请详情（含明细） |
| **创建报废申请** | POST | `/api/lifecycle/disposal-requests/` | 创建新的报废申请（含资产） |
| **提交鉴定** | POST | `/api/lifecycle/disposal-requests/{id}/submit_appraisal/` | 提交技术鉴定 |
| **完成鉴定** | POST | `/api/lifecycle/disposal-requests/{id}/complete_appraisal/` | 完成资产鉴定 |
| **执行处置** | POST | `/api/lifecycle/disposal-requests/{id}/execute/` | 执行资产处置 |

### 13.8 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量删除** | POST | `/api/lifecycle/purchase-requests/batch-delete/` | 批量软删除采购申请 |
| **批量恢复** | POST | `/api/lifecycle/purchase-requests/batch-restore/` | 批量恢复已删除的采购申请 |
| **批量更新** | POST | `/api/lifecycle/purchase-requests/batch-update/` | 批量更新采购申请字段 |

**批量删除请求格式**：
```json
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 13.9 标准错误码

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

### 13.10 扩展接口示例

#### 采购申请审批进度查询
```http
GET /api/lifecycle/purchase-requests/{id}/approval_history/
```

**响应格式**：
```json
{
    "success": true,
    "data": [
        {
            "step": "提交审批",
            "approver": "张三",
            "action": "submit",
            "comment": "",
            "action_time": "2024-01-01 10:00:00"
        },
        {
            "step": "部门审批",
            "approver": "李四",
            "action": "approve",
            "comment": "同意申请",
            "action_time": "2024-01-01 14:00:00"
        }
    ]
}
```

#### 维修统计接口
```http
GET /api/lifecycle/maintenance/statistics/
```

**响应格式**：
```json
{
    "success": true,
    "data": {
        "total_maintenance": 100,
        "by_status": [
            {"status": "completed", "count": 80},
            {"status": "processing", "count": 15},
            {"status": "reported", "count": 5}
        ],
        "by_priority": [
            {"priority": "urgent", "count": 10},
            {"priority": "high", "count": 20},
            {"priority": "normal", "count": 60},
            {"priority": "low", "count": 10}
        ],
        "total_cost": "50000.00",
        "avg_repair_time": "3.5 days"
    }
}
```

#### 保养任务到期提醒
```http
GET /api/lifecycle/maintenance-tasks/due_reminders/?days=7
```

---

**版本**: 1.0.0
**更新日期**: 2026-01-15
**维护人**: GZEAMS 开发团队

