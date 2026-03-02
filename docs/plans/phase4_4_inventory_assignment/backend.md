# Phase 4.4: 盘点任务分配与执行 - 后端实现

## 概述

在现有盘点模型基础上，封装**盘点分配机制**，支持多种盘点模式的统一调度，区分管理端（任务分配与追踪）和用户端（任务执行与反馈）。

---

## 核心设计理念

```
┌─────────────────────────────────────────────────────────────┐
│                    InventoryTask (盘点任务)                    │
│                   现有模型保持不变                             │
│  - inventory_type, department, category, location等          │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ 引用
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 InventoryAssignment (盘点分配)                 │
│                       新增模型                                │
│  - 将任务拆分为可分配的单元                                    │
│  - 支持多种分配模式                                           │
│  - 关联具体资产和执行人                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │ 区域分配  │  │ 类型分配  │  │ 人员分配  │
         │ 模式     │  │ 模式     │  │ 模式     │
         └──────────┘  └──────────┘  └──────────┘
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
# 所有盘点分配模型必须继承 BaseModel
class InventoryAssignment(BaseModel):
    """盘点任务分配记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    task = models.ForeignKey('InventoryTask', ...)
    executor = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    mode = models.CharField(...)  # region/category/custodian/random/manual
    scope_config = models.JSONField(...)
    assigned_snapshot_ids = models.JSONField(...)
    total_assigned = models.IntegerField(default=0)
    completed_count = models.IntegerField(default=0)
    status = models.CharField(...)  # pending/in_progress/completed/overdue

class InventoryAssignmentTemplate(BaseModel):
    """盘点分配模板（可复用的分配规则）"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    template_name = models.CharField(max_length=200)
    rules = models.JSONField(...)
    is_active = models.BooleanField(default=True)

class InventoryAssignmentRule(BaseModel):
    """自动分配规则（基于条件自动触发分配）"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    rule_code = models.CharField(max_length=50)
    trigger_condition = models.JSONField(...)
    executor_config = models.JSONField(...)
    priority = models.IntegerField(default=100)

class InventoryTaskViewer(BaseModel):
    """盘点任务查看者"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    task = models.ForeignKey('InventoryTask', ...)
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    source = models.CharField(...)  # manual/department_leader/department_member/role
    scope = models.CharField(...)  # all/department/assignment
    scope_config = models.JSONField(...)

class InventoryTaskViewConfig(BaseModel):
    """盘点任务查看配置"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    task = models.OneToOneField('InventoryTask', ...)
    allow_department_leader = models.BooleanField(default=True)
    allow_asset_admin = models.BooleanField(default=False)

class InventoryViewLog(BaseModel):
    """盘点查看日志"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    task = models.ForeignKey('InventoryTask', ...)
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    view_method = models.CharField(...)  # web/mobile/export
    ip_address = models.GenericIPAddressField(...)
```

### 序列化器继承关系

```python
# 所有序列化器必须继承 BaseModelSerializer
class InventoryAssignmentSerializer(BaseModelSerializer):
    """盘点分配序列化器"""
    executor = UserSerializer(read_only=True)
    task_code = serializers.CharField(source='task.task_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryAssignment
        # 自动继承公共字段: id, organization, is_deleted, deleted_at,
        #                 created_at, updated_at, created_by, custom_fields
        fields = BaseModelSerializer.Meta.fields + [
            'task', 'task_code', 'executor', 'mode', 'status',
            'total_assigned', 'completed_count', 'progress'
        ]

class MyAssignmentSerializer(BaseModelSerializer):
    """用户端我的任务序列化器"""
    # 继承BaseModelSerializer获得所有公共字段

class InventoryAssignmentTemplateSerializer(BaseModelSerializer):
    """分配模板序列化器"""
    # 继承BaseModelSerializer获得所有公共字段
```

### 服务层继承关系

```python
# 服务类必须继承 BaseCRUDService
class InventoryAssignmentService(BaseCRUDService):
    """盘点分配服务"""
    def __init__(self, task: InventoryTask):
        super().__init__(InventoryAssignment)
        # 自动获得：create(), update(), delete(), restore(), get(), query(), paginate()

class InventoryExecutorService:
    """执行人盘点服务（用户端）"""
    # 此服务不继承BaseCRUDService，因为主要用于业务逻辑而非CRUD操作
```

### ViewSet继承关系

```python
# 所有ViewSet必须继承 BaseModelViewSetWithBatch
class InventoryAssignmentViewSet(BaseModelViewSetWithBatch):
    """盘点分配API（管理端）"""
    serializer_class = InventoryAssignmentSerializer
    # 自动获得：组织过滤、软删除、审计字段、批量操作

class MyInventoryViewSet(BaseModelViewSetWithBatch):
    """我的盘点API（用户端）"""
    # 自动获得所有公共功能

class InventoryAssignmentTemplateViewSet(BaseModelViewSetWithBatch):
    """盘点分配模板API"""
    # 自动获得所有公共功能
```

### 过滤器继承关系

```python
# 所有过滤器必须继承 BaseModelFilter
class InventoryAssignmentFilter(BaseModelFilter):
    """盘点分配过滤器"""
    status = filters.ChoiceFilter(choices=[...])
    # 自动继承：created_at, updated_at, created_by, is_deleted 等过滤

    class Meta(BaseModelFilter.Meta):
        model = InventoryAssignment
        fields = BaseModelFilter.Meta.fields + ['status', 'mode', 'task', 'executor']
```

---

## 1. 盘点分配模型

```python
# apps/inventory/models/assignment.py

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class InventoryAssignment(BaseModel):
    """盘点分配

    将盘点任务拆分为可分配给执行人的单元
    一个任务可以拆分为多个分配
    """

    class Meta:
        db_table = 'inventory_assignment'
        verbose_name = '盘点分配'
        verbose_name_plural = '盘点分配'
        unique_together = [['task', 'executor']]
        indexes = [
            models.Index(fields=['task', 'executor']),
            models.Index(fields=['executor', '-created_at']),
            models.Index(fields=['status']),
        ]

    # 关联任务
    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='盘点任务'
    )

    # 执行人
    executor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inventory_assignments',
        verbose_name='执行人'
    )

    # 分配模式
    mode = models.CharField(
        max_length=20,
        choices=[
            ('region', '区域分配'),
            ('category', '分类分配'),
            ('custodian', '保管人分配/自盘'),
            ('random', '盲抽分配'),
            ('manual', '手动分配'),
        ],
        verbose_name='分配模式'
    )

    # 分配范围定义（JSON）
    # 根据mode不同，存储不同的筛选条件
    scope_config = models.JSONField(
        default=dict,
        verbose_name='范围配置',
        help_text='''
        region模式: {"location_ids": [1,2,3]}
        category模式: {"category_ids": [1,2,3]}
        custodian模式: {"custodian_ids": [1,2,3]}
        random模式: {"asset_count": 100}
        manual模式: {"asset_ids": [1,2,3]}
        '''
    )

    # 分配的资产快照ID列表（继承自task.snapshots）
    # 实际盘点时，executor只能看到这些资产
    assigned_snapshot_ids = models.JSONField(
        default=list,
        verbose_name='分配的快照ID列表'
    )

    # 统计
    total_assigned = models.IntegerField(
        default=0,
        verbose_name='分配数量'
    )
    completed_count = models.IntegerField(
        default=0,
        verbose_name='已完成数量'
    )
    missing_count = models.IntegerField(
        default=0,
        verbose_name='盘亏数量'
    )
    extra_count = models.IntegerField(
        default=0,
        verbose_name='盘盈数量'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待执行'),
            ('in_progress', '执行中'),
            ('completed', '已完成'),
            ('overdue', '已逾期'),
        ],
        default='pending',
        verbose_name='状态'
    )

    # 时间
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='分配时间'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='开始时间'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='完成时间'
    )
    deadline_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='截止时间'
    )

    # 说明
    instruction = models.TextField(
        blank=True,
        verbose_name='盘点说明',
        help_text='给执行人的说明或注意事项'
    )

    def __str__(self):
        return f"{self.task.task_code} - {self.executor.real_name}"

    @property
    def progress(self):
        """完成进度"""
        if self.total_assigned == 0:
            return 0
        return int(self.completed_count / self.total_assigned * 100)

    def get_assigned_snapshots(self):
        """获取分配的资产快照"""
        from apps.inventory.models import InventorySnapshot
        return InventorySnapshot.objects.filter(
            id__in=self.assigned_snapshot_ids
        )

    def get_my_scanned_assets(self):
        """获取我已扫描的资产"""
        from apps.inventory.models import InventoryScan
        return InventoryScan.objects.filter(
            task=self.task,
            scanned_by=self.executor
        ).select_related('asset')

    def get_my_unscanned_assets(self):
        """获取我未扫描的资产"""
        scanned_asset_ids = self.get_my_scanned_assets().filter(
            asset__isnull=True
        ).values_list('asset_id', flat=True)

        return self.get_assigned_snapshots().exclude(
            asset_id__in=scanned_asset_ids
        )


class InventoryAssignmentTemplate(BaseModel):
    """盘点分配模板

    可复用的分配规则配置
    """

    class Meta:
        db_table = 'inventory_assignment_template'
        verbose_name = '盘点分配模板'

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='assignment_templates'
    )

    template_name = models.CharField(
        max_length=100,
        verbose_name='模板名称'
    )

    # 分配规则
    rules = models.JSONField(
        verbose_name='分配规则',
        help_text='''
        [
            {
                "mode": "region",
                "condition": {"location_ids": [1, 2, 3]},
                "executor_type": "department",
                "executor_value": "dept_id_1"
            },
            {
                "mode": "category",
                "condition": {"category_ids": [10, 11]},
                "executor_type": "user",
                "executor_value": "user_id_1"
            },
            {
                "mode": "custodian",
                "condition": {"auto_assign": true},
                "executor_type": "custodian",  # 自动分配给保管人
                "executor_value": null
            }
        ]
        '''
    )

    # 默认说明
    default_instruction = models.TextField(
        blank=True,
        verbose_name='默认说明'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    def __str__(self):
        return self.template_name


class InventoryAssignmentRule(BaseModel):
    """盘点分配规则

    定义资产到执行人的自动分配规则
    """

    class Meta:
        db_table = 'inventory_assignment_rule'
        verbose_name = '盘点分配规则'
        unique_together = [['organization', 'rule_code']]

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='assignment_rules'
    )

    rule_code = models.CharField(
        max_length=50,
        verbose_name='规则编码'
    )

    rule_name = models.CharField(
        max_length=100,
        verbose_name='规则名称'
    )

    # 触发条件
    trigger_condition = models.JSONField(
        default=dict,
        verbose_name='触发条件',
        help_text='''
        {
            "location_id": 1,           # 地点ID
            "department_id": 2,          # 部门ID
            "category_id": 3,            # 分类ID
            "custodian_id": null         # 保管人ID（null表示任意）
        }
        '''
    )

    # 执行人配置
    executor_config = models.JSONField(
        verbose_name='执行人配置',
        help_text='''
        {
            "type": "custodian",         # custodian(保管人)/department(部门)/user(指定用户)/role(角色)
            "value": null,               # 根据type不同，值含义不同
            "fallback_user_id": null     # 找不到执行人时的兜底
        }
        '''
    )

    # 分配模式
    assignment_mode = models.CharField(
        max_length=20,
        choices=[
            ('custodian', '保管人自盘'),
            ('cross', '交叉盘点'),
            ('random', '随机分配'),
        ],
        default='custodian',
        verbose_name='分配模式'
    )

    # 优先级（数字越小优先级越高）
    priority = models.IntegerField(
        default=100,
        verbose_name='优先级'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    def __str__(self):
        return f"{self.rule_code} - {self.rule_name}"
```

---

## 2. 盘点分配服务

```python
# apps/inventory/services/assignment_service.py

from typing import List, Dict, Optional
from django.db import transaction
from django.utils import timezone
from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import (
    InventoryTask, InventorySnapshot, InventoryAssignment,
    InventoryAssignmentTemplate, InventoryAssignmentRule
)
from apps.accounts.models import User, Department


class InventoryAssignmentService(BaseCRUDService):
    """盘点分配服务"""

    def __init__(self, task: InventoryTask):
        super().__init__(InventoryAssignment)
        self.task = task

    @transaction.atomic
    def create_assignments(
        self,
        assignment_data: List[Dict],
        clear_existing: bool = True
    ) -> List[InventoryAssignment]:
        """
        创建盘点分配

        Args:
            assignment_data: 分配数据列表
                [
                    {
                        "executor_id": 1,
                        "mode": "region",
                        "scope_config": {"location_ids": [1, 2, 3]},
                        "instruction": "请盘点A区资产"
                    },
                    ...
                ]
            clear_existing: 是否清除现有分配

        Returns:
            创建的分配列表
        """
        # 清除现有分配
        if clear_existing:
            self.task.assignations.all().delete()

        assignments = []
        for data in assignment_data:
            # 获取范围快照
            snapshot_ids = self._get_snapshots_by_scope(data['mode'], data['scope_config'])

            assignment = InventoryAssignment.objects.create(
                task=self.task,
                executor_id=data['executor_id'],
                mode=data['mode'],
                scope_config=data['scope_config'],
                assigned_snapshot_ids=snapshot_ids,
                total_assigned=len(snapshot_ids),
                instruction=data.get('instruction', '')
            )
            assignments.append(assignment)

        return assignments

    @transaction.atomic
    def auto_assign_by_template(self, template: InventoryAssignmentTemplate) -> List[InventoryAssignment]:
        """
        使用模板自动分配

        Args:
            template: 分配模板

        Returns:
            创建的分配列表
        """
        assignments = []

        for rule in template.rules:
            executor = self._resolve_executor(rule['executor_type'], rule.get('executor_value'))
            if not executor:
                continue

            # 获取快照
            snapshot_ids = self._get_snapshots_by_condition(rule.get('condition', {}))

            assignment = InventoryAssignment.objects.create(
                task=self.task,
                executor=executor,
                mode=rule['mode'],
                scope_config=rule.get('condition', {}),
                assigned_snapshot_ids=snapshot_ids,
                total_assigned=len(snapshot_ids),
                instruction=template.default_instruction
            )
            assignments.append(assignment)

        return assignments

    @transaction.atomic
    def auto_assign_by_rules(self) -> List[InventoryAssignment]:
        """
        按组织的分配规则自动分配

        Returns:
            创建的分配列表
        """
        rules = InventoryAssignmentRule.objects.filter(
            organization=self.task.organization,
            is_active=True
        ).order_by('priority')

        # 按优先级处理
        assigned_snapshot_ids = set()
        assignments = []

        for rule in rules:
            # 检查规则是否匹配当前任务
            if not self._rule_matches_task(rule):
                continue

            # 获取符合条件的未分配快照
            available_snapshots = self.task.snapshots.exclude(
                id__in=assigned_snapshot_ids
            )

            # 进一步筛选
            filtered_snapshots = self._filter_snapshots_by_rule(
                available_snapshots,
                rule.trigger_condition
            )

            if not filtered_snapshots.exists():
                continue

            # 解析执行人
            executor_configs = self._resolve_executors_by_rule(
                rule,
                filtered_snapshots
            )

            # 为每个执行人创建分配
            for executor_config in executor_configs:
                executor_snapshot_ids = list(
                    filtered_snapshots.filter(
                        id__in=executor_config['snapshot_ids']
                    ).values_list('id', flat=True)
                )

                if executor_snapshot_ids:
                    assignment = InventoryAssignment.objects.create(
                        task=self.task,
                        executor=executor_config['executor'],
                        mode=rule.assignment_mode,
                        scope_config=rule.trigger_condition,
                        assigned_snapshot_ids=executor_snapshot_ids,
                        total_assigned=len(executor_snapshot_ids)
                    )
                    assignments.append(assignment)
                    assigned_snapshot_ids.update(executor_snapshot_ids)

        return assignments

    @transaction.atomic
    def assign_by_custodian(self) -> List[InventoryAssignment]:
        """
        按保管人分配（自盘模式）

        将资产自动分配给各自的保管人
        """
        assignments = []
        snapshots = self.task.snapshots.select_related('asset').all()

        # 按保管人分组
        custodian_groups = {}
        for snapshot in snapshots:
            custodian_id = snapshot.custodian_id
            if custodian_id:
                if custodian_id not in custodian_groups:
                    custodian_groups[custodian_id] = []
                custodian_groups[custodian_id].append(snapshot.id)

        # 为每个保管人创建分配
        for custodian_id, snapshot_ids in custodian_groups.items():
            try:
                executor = User.objects.get(id=custodian_id)
            except User.DoesNotExist:
                continue

            assignment = InventoryAssignment.objects.create(
                task=self.task,
                executor=executor,
                mode='custodian',
                scope_config={'custodian_id': custodian_id},
                assigned_snapshot_ids=snapshot_ids,
                total_assigned=len(snapshot_ids),
                instruction='请盘点您名下的资产'
            )
            assignments.append(assignment)

        return assignments

    @transaction.atomic
    def assign_random(self, executors: List[User], per_executor: int = None) -> List[InventoryAssignment]:
        """
        随机盲抽分配

        Args:
            executors: 执行人列表
            per_executor: 每人分配数量（None表示平均分配）

        Returns:
            创建的分配列表
        """
        import random

        all_snapshot_ids = list(
            self.task.snapshots.values_list('id', flat=True)
        )
        random.shuffle(all_snapshot_ids)

        if per_executor:
            # 按指定数量分配
            chunks = []
            for i in range(0, len(all_snapshot_ids), per_executor):
                chunks.append(all_snapshot_ids[i:i + per_executor])
        else:
            # 平均分配
            chunk_size = len(all_snapshot_ids) // len(executors)
            chunks = []
            for i in range(len(executors)):
                start = i * chunk_size
                end = start + chunk_size if i < len(executors) - 1 else len(all_snapshot_ids)
                chunks.append(all_snapshot_ids[start:end])

        assignments = []
        for executor, snapshot_ids in zip(executors, chunks):
            if snapshot_ids:
                assignment = InventoryAssignment.objects.create(
                    task=self.task,
                    executor=executor,
                    mode='random',
                    scope_config={},
                    assigned_snapshot_ids=snapshot_ids,
                    total_assigned=len(snapshot_ids),
                    instruction='请盘点分配给您的资产'
                )
                assignments.append(assignment)

        return assignments

    def _get_snapshots_by_scope(self, mode: str, scope_config: dict) -> List[int]:
        """根据范围模式获取快照ID"""
        snapshots = self.task.snapshots.all()

        if mode == 'region':
            location_ids = scope_config.get('location_ids', [])
            if location_ids:
                snapshots = snapshots.filter(location_id__in=location_ids)

        elif mode == 'category':
            category_ids = scope_config.get('category_ids', [])
            if category_ids:
                # 通过资产的category筛选
                from apps.assets.models import Asset
                asset_ids = Asset.objects.filter(
                    asset_category_id__in=category_ids
                ).values_list('id', flat=True)
                snapshots = snapshots.filter(asset_id__in=asset_ids)

        elif mode == 'custodian':
            custodian_ids = scope_config.get('custodian_ids', [])
            if custodian_ids:
                snapshots = snapshots.filter(custodian_id__in=custodian_ids)

        elif mode == 'manual':
            asset_ids = scope_config.get('asset_ids', [])
            if asset_ids:
                snapshots = snapshots.filter(asset_id__in=asset_ids)

        return list(snapshots.values_list('id', flat=True))

    def _get_snapshots_by_condition(self, condition: dict) -> List[int]:
        """根据条件获取快照ID"""
        return self._get_snapshots_by_scope('manual', condition)

    def _filter_snapshots_by_rule(self, snapshots, condition: dict):
        """根据规则条件筛选快照"""
        location_id = condition.get('location_id')
        if location_id:
            snapshots = snapshots.filter(location_id=location_id)

        department_id = condition.get('department_id')
        if department_id:
            snapshots = snapshots.filter(department_id=department_id)

        category_id = condition.get('category_id')
        if category_id:
            from apps.assets.models import Asset
            asset_ids = Asset.objects.filter(
                asset_category_id=category_id
            ).values_list('id', flat=True)
            snapshots = snapshots.filter(asset_id__in=asset_ids)

        custodian_id = condition.get('custodian_id')
        if custodian_id:
            snapshots = snapshots.filter(custodian_id=custodian_id)

        return snapshots

    def _rule_matches_task(self, rule: InventoryAssignmentRule) -> bool:
        """判断规则是否匹配当前任务"""
        # 检查任务类型是否匹配
        if self.task.inventory_type == 'department':
            if rule.trigger_condition.get('department_id') != self.task.department_id:
                return False
        elif self.task.inventory_type == 'category':
            if rule.trigger_condition.get('category_id') != self.task.asset_category_id:
                return False
        elif self.task.inventory_type == 'region':
            if rule.trigger_condition.get('location_id') != self.task.location_id:
                return False

        return True

    def _resolve_executor(self, executor_type: str, executor_value):
        """解析执行人"""
        if executor_type == 'user':
            return User.objects.filter(id=executor_value).first()
        elif executor_type == 'department':
            # 返回部门负责人，这里简化处理
            dept = Department.objects.filter(id=executor_value).first()
            return dept.leader if dept else None
        elif executor_type == 'role':
            # 返回具有该角色的用户
            return User.objects.filter(roles__contains=executor_value).first()
        return None

    def _resolve_executors_by_rule(self, rule, snapshots) -> List[Dict]:
        """根据规则解析执行人列表"""
        executor_config = rule.executor_config
        executor_type = executor_config.get('type')
        result = []

        if executor_type == 'custodian':
            # 按保管人分组
            custodian_map = {}
            for snap in snapshots:
                custodian_id = snap.custodian_id
                if custodian_id:
                    if custodian_id not in custodian_map:
                        custodian_map[custodian_id] = []
                    custodian_map[custodian_id].append(snap.id)

            for custodian_id, snapshot_ids in custodian_map.items():
                try:
                    executor = User.objects.get(id=custodian_id)
                    result.append({
                        'executor': executor,
                        'snapshot_ids': snapshot_ids
                    })
                except User.DoesNotExist:
                    continue

        elif executor_type == 'department':
            # 按部门分组
            dept_id = executor_config.get('value')
            dept_users = User.objects.filter(department_id=dept_id)

            # 平均分配给部门成员
            snapshot_ids = list(snapshots.values_list('id', flat=True))
            chunk_size = len(snapshot_ids) // len(dept_users) if dept_users.exists() else len(snapshot_ids)

            for i, user in enumerate(dept_users):
                start = i * chunk_size
                end = start + chunk_size if i < len(dept_users) - 1 else len(snapshot_ids)
                result.append({
                    'executor': user,
                    'snapshot_ids': snapshot_ids[start:end]
                })

        elif executor_type == 'user':
            # 指定用户
            user_id = executor_config.get('value')
            executor = User.objects.filter(id=user_id).first()
            if executor:
                result.append({
                    'executor': executor,
                    'snapshot_ids': list(snapshots.values_list('id', flat=True))
                })

        # 如果没有找到执行人，使用兜底用户
        if not result and executor_config.get('fallback_user_id'):
            executor = User.objects.filter(id=executor_config['fallback_user_id']).first()
            if executor:
                result.append({
                    'executor': executor,
                    'snapshot_ids': list(snapshots.values_list('id', flat=True))
                })

        return result


class InventoryExecutorService:
    """执行人盘点服务（用户端）"""

    def __init__(self, executor: User):
        self.executor = executor

    def get_my_assignments(self, status: str = None) -> List[InventoryAssignment]:
        """
        获取我的盘点分配

        Args:
            status: 状态筛选 (pending/in_progress/completed/overdue)

        Returns:
            我的分配列表
        """
        assignments = InventoryAssignment.objects.filter(
            executor=self.executor
        ).select_related('task')

        if status:
            if status == 'overdue':
                from django.utils import timezone
                assignments = assignments.filter(
                    status__in=['pending', 'in_progress'],
                    deadline_at__lt=timezone.now()
                )
            else:
                assignments = assignments.filter(status=status)

        return assignments.order_by('-created_at')

    def get_my_pending_assets(self, assignment: InventoryAssignment) -> List[Dict]:
        """
        获取我在某分配下待盘点的资产

        Args:
            assignment: 盘点分配

        Returns:
            待盘点资产列表
        """
        # 已扫描的资产ID
        scanned_asset_ids = assignment.get_my_scanned_assets().filter(
            asset__isnull=False
        ).values_list('asset_id', flat=True)

        # 待盘点资产
        snapshots = assignment.get_assigned_snapshots().exclude(
            asset_id__in=scanned_asset_ids
        )

        return [
            {
                'snapshot_id': snap.id,
                'asset_id': snap.asset_id,
                'asset_code': snap.asset_code,
                'asset_name': snap.asset_name,
                'location': snap.location_name,
                'custodian': snap.custodian_name,
                'expected_status': snap.asset_status,
            }
            for snap in snapshots
        ]

    def get_my_today_tasks(self) -> Dict:
        """
        获取我今天的盘点任务汇总

        Returns:
            今日任务统计
        """
        from django.utils import timezone
        from django.db.models import Sum, Q

        today = timezone.now().date()
        start_of_day = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))

        # 今天的待完成任务
        pending_assignments = InventoryAssignment.objects.filter(
            executor=self.executor,
            status__in=['pending', 'in_progress'],
            created_at__gte=start_of_day
        ).select_related('task')

        return {
            'total_count': pending_assignments.count(),
            'total_assets': pending_assignments.aggregate(
                total=Sum('total_assigned')
            )['total'] or 0,
            'completed_assets': pending_assignments.aggregate(
                total=Sum('completed_count')
            )['total'] or 0,
            'assignments': [
                {
                    'task_code': a.task.task_code,
                    'task_name': a.task.task_name,
                    'assignment_id': a.id,
                    'total': a.total_assigned,
                    'completed': a.completed_count,
                    'progress': a.progress,
                    'deadline': a.deadline_at,
                }
                for a in pending_assignments
            ]
        }

    def start_assignment(self, assignment: InventoryAssignment):
        """开始执行分配"""
        if assignment.status != 'pending':
            raise ValueError("只有待执行状态的分配可以开始")

        assignment.status = 'in_progress'
        assignment.started_at = timezone.now()
        assignment.save(update_fields=['status', 'started_at'])

    def complete_assignment(self, assignment: InventoryAssignment):
        """完成分配"""
        if assignment.status != 'in_progress':
            raise ValueError("只有执行中的分配可以完成")

        # 更新完成统计
        scanned_asset_ids = assignment.get_my_scanned_assets().filter(
            asset__isnull=False
        ).values_list('asset_id', flat=True)

        assignment.completed_count = len(scanned_asset_ids)

        # 检查盘亏（在分配范围内的未扫描资产）
        missing_snapshots = assignment.get_assigned_snapshots().exclude(
            asset_id__in=scanned_asset_ids
        )
        assignment.missing_count = missing_snapshots.count()

        assignment.status = 'completed'
        assignment.completed_at = timezone.now()
        assignment.save()

        # 检查任务是否全部完成
        self._check_task_completion(assignment.task)

    def _check_task_completion(self, task: InventoryTask):
        """检查任务是否全部完成"""
        total_assigned = task.assignments.aggregate(
            total=Sum('total_assigned')
        )['total'] or 0

        total_completed = task.assignments.aggregate(
            total=Sum('completed_count')
        )['total'] or 0

        # 如果所有分配都完成，更新任务状态
        if task.assignments.filter(status__in=['pending', 'in_progress']).count() == 0:
            from apps.inventory.services.inventory_service import InventoryService
            service = InventoryService()
            service.complete_task(task, task.planned_by)
```

---

## 3. API接口

```python
# apps/inventory/views/assignment.py

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.models import get_current_organization
from apps.inventory.models import InventoryTask, InventoryAssignment
from apps.inventory.services.assignment_service import (
    InventoryAssignmentService,
    InventoryExecutorService
)
from apps.inventory.serializers.assignment import (
    InventoryAssignmentSerializer,
    MyAssignmentSerializer,
    InventoryAssignmentTemplateSerializer
)


class InventoryAssignmentViewSet(BaseModelViewSetWithBatch):
    """盘点分配API（管理端）"""

    serializer_class = InventoryAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取查询集"""
        return InventoryAssignment.objects.all()

    @action(detail=True, methods=['post'])
    def create_assignments(self, request, pk=None):
        """创建盘点分配"""
        task = get_object_or_404(InventoryTask, pk=pk)

        assignment_data = request.data.get('assignments', [])
        clear_existing = request.data.get('clear_existing', True)

        service = InventoryAssignmentService(task)
        assignments = service.create_assignments(assignment_data, clear_existing)

        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def auto_assign_template(self, request, pk=None):
        """使用模板自动分配"""
        task = get_object_or_404(InventoryTask, pk=pk)
        template_id = request.data.get('template_id')

        from apps.inventory.models import InventoryAssignmentTemplate
        template = get_object_or_404(InventoryAssignmentTemplate, id=template_id)

        service = InventoryAssignmentService(task)
        assignments = service.auto_assign_by_template(template)

        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def auto_assign_rules(self, request, pk=None):
        """按规则自动分配"""
        task = get_object_or_404(InventoryTask, pk=pk)

        service = InventoryAssignmentService(task)
        assignments = service.auto_assign_by_rules()

        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_custodian(self, request, pk=None):
        """按保管人分配（自盘模式）"""
        task = get_object_or_404(InventoryTask, pk=pk)

        service = InventoryAssignmentService(task)
        assignments = service.assign_by_custodian()

        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_random(self, request, pk=None):
        """随机盲抽分配"""
        task = get_object_or_404(InventoryTask, pk=pk)

        executor_ids = request.data.get('executor_ids', [])
        per_executor = request.data.get('per_executor')

        from apps.accounts.models import User
        executors = User.objects.filter(id__in=executor_ids)

        service = InventoryAssignmentService(task)
        assignments = service.assign_random(executors, per_executor)

        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """获取任务的所有分配"""
        task = get_object_or_404(InventoryTask, pk=pk)

        assignments = task.assignments.select_related('executor').all()
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)


class MyInventoryViewSet(BaseModelViewSetWithBatch):
    """我的盘点API（用户端）"""

    serializer_class = MyAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取当前用户的盘点分配"""
        return InventoryAssignment.objects.filter(executor=self.request.user)

    def list(self, request):
        """获取我的盘点任务列表"""
        service = InventoryExecutorService(request.user)
        status_filter = request.query_params.get('status')

        assignments = service.get_my_assignments(status_filter)
        serializer = self.get_serializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """获取今日盘点任务"""
        service = InventoryExecutorService(request.user)
        data = service.get_my_today_tasks()
        return Response(data)

    @action(detail=False, methods=['get'])
    def pending_assets(self, request):
        """获取待盘点资产"""
        assignment_id = request.query_params.get('assignment_id')

        assignment = get_object_or_404(
            InventoryAssignment,
            id=assignment_id,
            executor=request.user
        )

        service = InventoryExecutorService(request.user)
        assets = service.get_my_pending_assets(assignment)

        return Response(assets)

    @action(detail=False, methods=['post'])
    def start(self, request):
        """开始盘点"""
        assignment_id = request.data.get('assignment_id')
        assignment = get_object_or_404(
            InventoryAssignment,
            id=assignment_id,
            executor=request.user
        )

        service = InventoryExecutorService(request.user)
        service.start_assignment(assignment)

        return Response({'message': '盘点已开始'})

    @action(detail=False, methods=['post'])
    def complete(self, request):
        """完成盘点"""
        assignment_id = request.data.get('assignment_id')
        assignment = get_object_or_404(
            InventoryAssignment,
            id=assignment_id,
            executor=request.user
        )

        service = InventoryExecutorService(request.user)
        service.complete_assignment(assignment)

        return Response({'message': '盘点已完成'})


class InventoryAssignmentTemplateViewSet(BaseModelViewSetWithBatch):
    """盘点分配模板API"""

    serializer_class = InventoryAssignmentTemplateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取查询集"""
        return InventoryAssignmentTemplate.objects.all()
```

---

## Serializers

```python
# apps/inventory/serializers/assignment.py

from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.accounts.serializers import UserSerializer
from apps.inventory.models import (
    InventoryAssignment, InventoryAssignmentTemplate
)


class InventoryAssignmentSerializer(BaseModelSerializer):
    """盘点分配序列化器"""

    # 关联字段
    task_code = serializers.CharField(source='task.task_code', read_only=True)
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    executor = UserSerializer(read_only=True)
    executor_name = serializers.CharField(source='executor.real_name', read_only=True)

    # 显示字段
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryAssignment
        fields = BaseModelSerializer.Meta.fields + [
            'task', 'task_code', 'task_name',
            'executor', 'executor_name',
            'mode', 'mode_display',
            'scope_config',
            'total_assigned', 'completed_count',
            'missing_count', 'extra_count',
            'status', 'status_display',
            'progress',
            'assigned_at', 'started_at', 'completed_at', 'deadline_at',
            'instruction'
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + ['assigned_at', 'progress']


class MyAssignmentSerializer(BaseModelSerializer):
    """用户端我的任务序列化器"""

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress = serializers.IntegerField(read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InventoryAssignment
        fields = BaseModelSerializer.Meta.fields + [
            'task_code', 'task_name',
            'mode', 'mode_display',
            'total_assigned', 'completed_count',
            'status', 'status_display',
            'progress', 'is_overdue',
            'deadline_at', 'instruction'
        ]

    def get_is_overdue(self, obj):
        if obj.deadline_at and obj.status in ['pending', 'in_progress']:
            from django.utils import timezone
            return timezone.now() > obj.deadline_at
        return False


class InventoryAssignmentTemplateSerializer(BaseModelSerializer):
    """分配模板序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = InventoryAssignmentTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'template_name', 'rules', 'default_instruction', 'is_active'
        ]
```

---

## 4. 盘点任务查看权限模型

```python
# apps/inventory/models/task_viewer.py

from django.db import models
from django.conf import settings
from apps.common.models import BaseModel


class InventoryTaskViewer(BaseModel):
    """盘点任务查看者

    配置谁可以查看盘点任务的进度和情况
    支持部门负责人自动查看 + 指定人员查看
    """

    class Meta:
        db_table = 'inventory_task_viewer'
        verbose_name = '盘点任务查看者'
        verbose_name_plural = '盘点任务查看者'
        unique_together = [['task', 'viewer']]
        indexes = [
            models.Index(fields=['task']),
            models.Index(fields=['viewer']),
        ]

    # 关联任务
    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='viewers',
        verbose_name='盘点任务'
    )

    # 查看人
    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='viewable_tasks',
        verbose_name='查看人'
    )

    # 查看权限来源
    source = models.CharField(
        max_length=20,
        choices=[
            ('manual', '手动指定'),
            ('department_leader', '部门负责人'),
            ('department_member', '部门成员'),
            ('role', '角色权限'),
        ],
        default='manual',
        verbose_name='权限来源'
    )

    # 查看范围
    scope = models.CharField(
        max_length=20,
        choices=[
            ('all', '全部资产'),
            ('department', '本部门资产'),
            ('assignment', '指定分配'),
        ],
        default='all',
        verbose_name='查看范围',
        help_text='限制查看者只能看到特定范围的盘点数据'
    )

    # 范围配置（JSON）
    scope_config = models.JSONField(
        default=dict,
        verbose_name='范围配置',
        help_text='''
        department模式: {"department_id": 1}
        assignment模式: {"assignment_ids": [1, 2, 3]}
        '''
    )

    # 说明
    remark = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='说明'
    )

    def __str__(self):
        return f"{self.task.task_code} - {self.viewer.real_name}"

    def get_viewable_assignments(self):
        """获取可查看的分配列表"""
        from apps.inventory.models import InventoryAssignment

        if self.scope == 'all':
            return self.task.assignments.all()
        elif self.scope == 'department':
            dept_id = self.scope_config.get('department_id')
            # 只看本部门人员的分配
            return self.task.assignments.filter(
                executor__department_id=dept_id
            )
        elif self.scope == 'assignment':
            assignment_ids = self.scope_config.get('assignment_ids', [])
            return self.task.assignments.filter(id__in=assignment_ids)
        return InventoryAssignment.objects.none()


class InventoryTaskViewConfig(BaseModel):
    """盘点任务查看配置

    在任务级别配置查看权限规则
    """

    class Meta:
        db_table = 'inventory_task_view_config'
        verbose_name = '盘点任务查看配置'

    # 关联任务（一对一）
    task = models.OneToOneField(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='view_config',
        verbose_name='盘点任务'
    )

    # 是否允许部门负责人自动查看
    allow_department_leader = models.BooleanField(
        default=True,
        verbose_name='允许部门负责人查看',
        help_text='开启后，相关部门负责人可自动查看本部门资产盘点进度'
    )

    # 部门负责人查看范围
    department_leader_scope = models.CharField(
        max_length=20,
        choices=[
            ('department_assets', '仅本部门资产'),
            ('department_assignments', '本部门人员分配'),
        ],
        default='department_assets',
        verbose_name='部门负责人查看范围'
    )

    # 是否允许资产管理员查看
    allow_asset_admin = models.BooleanField(
        default=False,
        verbose_name='允许资产管理员查看',
        help_text='开启后，具有资产管理员角色的用户可查看'
    )

    # 备注
    remark = models.TextField(
        blank=True,
        verbose_name='备注'
    )

    def __str__(self):
        return f"{self.task.task_code} 查看配置"


class InventoryViewLog(BaseModel):
    """盘点查看日志

    记录用户查看盘点任务的日志
    """

    class Meta:
        db_table = 'inventory_view_log'
        verbose_name = '盘点查看日志'
        indexes = [
            models.Index(fields=['task', 'viewer']),
            models.Index(fields=['-created_at']),
        ]

    task = models.ForeignKey(
        'InventoryTask',
        on_delete=models.CASCADE,
        related_name='view_logs',
        verbose_name='盘点任务'
    )

    viewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='inventory_view_logs',
        verbose_name='查看人'
    )

    # 查看方式
    view_method = models.CharField(
        max_length=20,
        choices=[
            ('web', '网页'),
            ('mobile', '移动端'),
            ('export', '导出'),
        ],
        default='web',
        verbose_name='查看方式'
    )

    # 查看的分配ID（可选）
    viewed_assignment_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name='查看的分配ID'
    )

    # IP地址
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP地址'
    )

    # 用户代理
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='用户代理'
    )

    def __str__(self):
        return f"{self.viewer.real_name} 查看 {self.task.task_code}"
```

---

## 5. 盘点查看权限服务

```python
# apps/inventory/services/view_permission_service.py

from typing import List, Dict, Optional
from django.db import transaction
from django.utils import timezone
from apps.inventory.models import (
    InventoryTask, InventoryAssignment,
    InventoryTaskViewer, InventoryTaskViewConfig, InventoryViewLog
)
from apps.accounts.models import User, Department


class InventoryViewPermissionService:
    """盘点查看权限服务"""

    def __init__(self, task: InventoryTask):
        self.task = task

    def get_or_create_config(self) -> InventoryTaskViewConfig:
        """获取或创建查看配置"""
        config, created = InventoryTaskViewConfig.objects.get_or_create(
            task=self.task
        )
        return config

    @transaction.atomic
    def update_config(self, config_data: dict) -> InventoryTaskViewConfig:
        """
        更新查看配置

        Args:
            config_data: 配置数据
                {
                    "allow_department_leader": true,
                    "department_leader_scope": "department_assets",
                    "allow_asset_admin": false,
                    "remark": ""
                }
        """
        config = self.get_or_create_config()

        for key, value in config_data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        config.save()

        # 自动同步部门负责人查看权限
        if config.allow_department_leader:
            self._sync_department_leaders(config)

        return config

    @transaction.atomic
    def add_viewers(
        self,
        viewer_ids: List[str],
        scope: str = 'all',
        scope_config: dict = None,
        source: str = 'manual'
    ) -> List[InventoryTaskViewer]:
        """
        添加查看者

        Args:
            viewer_ids: 查看者用户ID列表
            scope: 查看范围 (all/department/assignment)
            scope_config: 范围配置
            source: 权限来源

        Returns:
            创建的查看者列表
        """
        viewers = []
        for viewer_id in viewer_ids:
            viewer, created = InventoryTaskViewer.objects.get_or_create(
                task=self.task,
                viewer_id=viewer_id,
                defaults={
                    'source': source,
                    'scope': scope,
                    'scope_config': scope_config or {}
                }
            )
            if not created:
                # 更新现有记录
                viewer.scope = scope
                viewer.scope_config = scope_config or {}
                viewer.source = source
                viewer.save()
            viewers.append(viewer)

        return viewers

    @transaction.atomic
    def remove_viewers(self, viewer_ids: List[str]):
        """移除查看者"""
        InventoryTaskViewer.objects.filter(
            task=self.task,
            viewer_id__in=viewer_ids
        ).delete()

    def get_viewable_assignments(self, user: User) -> List[InventoryAssignment]:
        """
        获取用户可查看的分配列表

        Args:
            user: 查看用户

        Returns:
            可查看的分配列表
        """
        # 1. 检查是否是任务创建者
        if self.task.planned_by_id == user.id:
            return self.task.assignments.all()

        # 2. 检查是否是分配的执行人
        my_assignments = self.task.assignments.filter(executor=user)
        if my_assignments.exists():
            return list(my_assignments)

        # 3. 检查显式指定的查看权限
        viewer_record = InventoryTaskViewer.objects.filter(
            task=self.task,
            viewer=user
        ).first()

        if viewer_record:
            return list(viewer_record.get_viewable_assignments())

        # 4. 检查自动权限（部门负责人、资产管理员）
        auto_assignments = self._check_auto_permissions(user)
        if auto_assignments:
            return auto_assignments

        # 无权限
        return []

    def can_view_task(self, user: User) -> bool:
        """
        检查用户是否可以查看任务

        Returns:
            是否有查看权限
        """
        # 任务创建者
        if self.task.planned_by_id == user.id:
            return True

        # 执行人
        if self.task.assignments.filter(executor=user).exists():
            return True

        # 显式查看权限
        if InventoryTaskViewer.objects.filter(
            task=self.task,
            viewer=user
        ).exists():
            return True

        # 自动权限
        return self._has_auto_permission(user)

    def get_view_permission_summary(self, user: User) -> Dict:
        """
        获取用户查看权限摘要

        Returns:
            权限摘要信息
        """
        can_view = self.can_view_task(user)
        if not can_view:
            return {
                'can_view': False,
                'reason': '无查看权限'
            }

        assignments = self.get_viewable_assignments(user)
        config = self.get_or_create_config()

        return {
            'can_view': True,
            'permission_source': self._get_permission_source(user),
            'viewable_count': len(assignments),
            'total_count': self.task.assignments.count(),
            'scope': self._get_user_scope(user),
            'config': {
                'allow_department_leader': config.allow_department_leader,
                'allow_asset_admin': config.allow_asset_admin,
            }
        }

    def log_view(self, user: User, view_method: str = 'web', request=None):
        """记录查看日志"""
        log_data = {
            'task': self.task,
            'viewer': user,
            'view_method': view_method,
        }

        if request:
            log_data['ip_address'] = self._get_client_ip(request)
            log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]

        InventoryViewLog.objects.create(**log_data)

    def _sync_department_leaders(self, config: InventoryTaskViewConfig):
        """同步部门负责人查看权限"""
        # 删除旧的自动生成的部门负责人权限
        InventoryTaskViewer.objects.filter(
            task=self.task,
            source='department_leader'
        ).delete()

        if not config.allow_department_leader:
            return

        # 获取任务涉及的所有部门
        department_ids = set()
        if self.task.inventory_type == 'department':
            department_ids.add(self.task.department_id)
        else:
            # 从快照中获取涉及的部门
            department_ids.update(
                self.task.snapshots.values_list('department_id', flat=True).distinct()
            )

        # 为每个部门负责人添加查看权限
        for dept_id in department_ids:
            if not dept_id:
                continue

            try:
                dept = Department.objects.get(id=dept_id)
                leader = dept.leader
                if leader:
                    scope = 'department' if config.department_leader_scope == 'department_assets' else 'all'
                    InventoryTaskViewer.objects.get_or_create(
                        task=self.task,
                        viewer=leader,
                        defaults={
                            'source': 'department_leader',
                            'scope': scope,
                            'scope_config': {'department_id': dept_id},
                            'remark': f'作为{dept.name}负责人自动获得查看权限'
                        }
                    )
            except Department.DoesNotExist:
                continue

    def _check_auto_permissions(self, user: User) -> Optional[List[InventoryAssignment]]:
        """检查自动权限"""
        config = self.get_or_create_config()

        # 1. 检查部门负责人权限
        if config.allow_department_leader:
            # 获取用户负责的部门
            led_departments = Department.objects.filter(leader=user)
            for dept in led_departments:
                # 检查任务是否涉及该部门
                if self._task_involves_department(dept.id):
                    if config.department_leader_scope == 'department_assets':
                        # 返回本部门相关的分配
                        return list(self.task.assignments.filter(
                            executor__department=dept
                        ))
                    else:
                        # 返回涉及本部门资产的分配
                        return list(self.task.assignments.filter(
                            task__snapshots__department_id=dept.id
                        ).distinct())

        # 2. 检查资产管理员权限
        if config.allow_asset_admin:
            if user.roles and 'asset_admin' in user.roles:
                return list(self.task.assignments.all())

        return None

    def _has_auto_permission(self, user: User) -> bool:
        """检查是否有自动权限"""
        return self._check_auto_permissions(user) is not None

    def _get_permission_source(self, user: User) -> str:
        """获取权限来源描述"""
        if self.task.planned_by_id == user.id:
            return '任务创建者'

        if self.task.assignments.filter(executor=user).exists():
            return '执行人'

        viewer = InventoryTaskViewer.objects.filter(
            task=self.task,
            viewer=user
        ).first()
        if viewer:
            source_map = {
                'manual': '手动指定',
                'department_leader': '部门负责人',
                'department_member': '部门成员',
                'role': '角色权限',
            }
            return source_map.get(viewer.source, '其他')

        if self._has_auto_permission(user):
            return '自动权限'

        return '未知'

    def _get_user_scope(self, user: User) -> str:
        """获取用户查看范围"""
        viewer = InventoryTaskViewer.objects.filter(
            task=self.task,
            viewer=user
        ).first()

        if viewer:
            scope_map = {
                'all': '全部',
                'department': '本部门',
                'assignment': '指定分配',
            }
            return scope_map.get(viewer.scope, '全部')

        if self.task.planned_by_id == user.id:
            return '全部'

        return '部分'

    def _task_involves_department(self, department_id) -> bool:
        """检查任务是否涉及指定部门"""
        if self.task.inventory_type == 'department':
            return self.task.department_id == department_id

        return self.task.snapshots.filter(
            department_id=department_id
        ).exists()

    def _get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

---

## 6. 过滤器

```python
# apps/inventory/filters/assignment.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventoryAssignment


class InventoryAssignmentFilter(BaseModelFilter):
    """盘点分配过滤器"""

    # 任务过滤
    task = filters.UUIDFilter(field_name='task_id', label='盘点任务')

    # 执行人过滤
    executor = filters.UUIDFilter(field_name='executor_id', label='执行人')

    # 状态过滤
    status = filters.ChoiceFilter(
        choices=InventoryAssignment._meta.get_field('status').choices,
        label='状态'
    )

    # 分配模式过滤
    mode = filters.ChoiceFilter(
        choices=InventoryAssignment._meta.get_field('mode').choices,
        label='分配模式'
    )

    # 时间范围过滤
    assigned_at_from = filters.DateTimeFilter(
        field_name='assigned_at',
        lookup_expr='gte',
        label='分配时间（起始）'
    )

    assigned_at_to = filters.DateTimeFilter(
        field_name='assigned_at',
        lookup_expr='lte',
        label='分配时间（结束）'
    )

    deadline_at_from = filters.DateTimeFilter(
        field_name='deadline_at',
        lookup_expr='gte',
        label='截止时间（起始）'
    )

    deadline_at_to = filters.DateTimeFilter(
        field_name='deadline_at',
        lookup_expr='lte',
        label='截止时间（结束）'
    )

    class Meta(BaseModelFilter.Meta):
        model = InventoryAssignment
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'task', 'executor', 'status', 'mode',
            'assigned_at_from', 'assigned_at_to',
            'deadline_at_from', 'deadline_at_to'
        ]
```

---

## 7. 完整示例

### 7.1 使用新基类的完整示例

```python
# apps/inventory/serializers/assignment.py

from apps.common.serializers.base import BaseModelSerializer
from apps.accounts.serializers import UserSerializer
from apps.inventory.models import InventoryAssignment

class InventoryAssignmentSerializer(BaseModelSerializer):
    """盘点分配序列化器 - 继承公共基类"""

    executor = UserSerializer(read_only=True)
    task_code = serializers.CharField(source='task.task_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryAssignment
        # 自动继承: id, organization, is_deleted, deleted_at,
        #          created_at, updated_at, created_by, custom_fields
        fields = BaseModelSerializer.Meta.fields + [
            'task', 'task_code', 'executor', 'mode', 'status',
            'total_assigned', 'completed_count', 'progress'
        ]


# apps/inventory/views/assignment.py

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.inventory.filters.assignment import InventoryAssignmentFilter

class InventoryAssignmentViewSet(BaseModelViewSetWithBatch):
    """盘点分配ViewSet - 自动获得所有公共功能"""

    serializer_class = InventoryAssignmentSerializer
    filterset_class = InventoryAssignmentFilter
    # 自动获得:
    # - 组织隔离
    # - 软删除/恢复
    # - 批量删除/恢复/更新
    # - 审计字段自动设置


# apps/inventory/services/assignment_service.py

from apps.common.services.base_crud import BaseCRUDService

class InventoryAssignmentService(BaseCRUDService):
    """盘点分配服务 - 继承公共CRUD服务"""

    def __init__(self):
        super().__init__(InventoryAssignment)
        # 自动获得: create, update, delete, restore, get, query, paginate


# apps/inventory/filters/assignment.py

from apps.common.filters.base import BaseModelFilter

class InventoryAssignmentFilter(BaseModelFilter):
    """盘点分配过滤器 - 继承公共过滤字段"""

    status = filters.ChoiceFilter(choices=[...])
    # 自动继承: created_at, updated_at, created_by, is_deleted 等过滤
```

---

## 8. 迁移检查清单

### 8.1 已完成的更新

- [x] 所有序列化器继承 `BaseModelSerializer`
- [x] 所有 ViewSet 继承 `BaseModelViewSetWithBatch`
- [x] 所有 Service 类继承 `BaseCRUDService`
- [x] 所有过滤器继承 `BaseModelFilter`
- [x] 移除重复的公共字段定义
- [x] 移除重复的公共方法实现
- [x] 更新导入路径

### 8.2 代码简化对比

```python
# 迁移前 (旧代码)
class InventoryAssignmentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    # ... 重复定义所有公共字段

    class Meta:
        model = InventoryAssignment
        fields = '__all__'


# 迁移后 (新代码)
class InventoryAssignmentSerializer(BaseModelSerializer):
    # 公共字段自动继承，只需定义业务字段

    class Meta(BaseModelSerializer.Meta):
        model = InventoryAssignment
        fields = BaseModelSerializer.Meta.fields + ['task', 'executor', 'status']
```

---

## 错误处理与重试机制

### 异常处理策略

#### 1. 分配操作异常处理

**连接超时处理**
- 数据库操作超时：设置30秒超时，超时后记录错误并重试
- 审批流程超时：设置60秒超时，触发重试机制
- 外部通知超时：设置10秒超时，异步发送失败

**数据格式异常处理**
- 审批记录JSON格式错误：验证JSON格式，记录错误信息
- 分配参数缺失：提供默认值或抛出业务异常
- 用户关系错误：检测用户组织关系，拒绝越权操作

**业务异常处理**
- 重复分配：检测重复分配，抛出业务异常
- 权限不足：抛出PERMISSION_DENIED异常
- 库存不足：检查资产可用数量，提供错误信息

#### 2. 重试策略

**指数退避重试**
```python
import time
from random import randint

def retry_with_backoff(func, max_retries=3, base_delay=60):
    """指数退避重试策略"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + randint(0, 10)
            time.sleep(delay)
    raise Exception("重试次数超限")
```

**重试配置**
- 最大重试次数：3次
- 基础延迟：60秒
- 指数因子：2倍递增
- 随机抖动：0-10秒避免雪崩

#### 3. 集成日志记录

所有分配操作均记录到InventoryAssignment模型，包括：
- 操作时间戳
- 操作类型（创建/更新/删除）
- 操作结果（成功/失败）
- 错误详情
- 操作人信息
- 审批流程记录

---

## 测试用例

### 1. 盘点分配服务测试

```python
# backend/apps/inventory/tests/test_assignment_service.py

import pytest
from django.db import transaction
from django.utils import timezone
from apps.inventory.models import InventoryTask, InventoryAssignment
from apps.inventory.services.assignment_service import InventoryAssignmentService
from apps.accounts.models import User, Department


@pytest.mark.django_db
class TestInventoryAssignmentService:
    """盘点分配服务测试"""

    def test_create_assignments(self, organization, user):
        """测试创建盘点分配"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK001',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        # 创建测试快照
        for i in range(5):
            snapshot = InventorySnapshot.objects.create(
                task=task,
                asset_id=i+1,
                asset_code=f'ASSET00{i+1}',
                asset_name=f'测试资产{i+1}',
                location_id=1,
                custodian_id=1,
                asset_status='active',
                created_by=user
            )

        # 分配数据
        assignment_data = [
            {
                'executor_id': user.id,
                'mode': 'manual',
                'scope_config': {'asset_ids': [1, 2, 3]},
                'instruction': '请盘点前三个资产'
            }
        ]

        # 创建分配
        service = InventoryAssignmentService(task)
        assignments = service.create_assignments(assignment_data)

        # 验证结果
        assert len(assignments) == 1
        assert assignments[0].task == task
        assert assignments[0].executor == user
        assert assignments[0].mode == 'manual'
        assert assignments[0].total_assigned == 3
        assert len(assignments[0].assigned_snapshot_ids) == 3

    def test_auto_assign_by_template(self, organization, user):
        """测试使用模板自动分配"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK002',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        # 创建测试快照
        for i in range(4):
            snapshot = InventorySnapshot.objects.create(
                task=task,
                asset_id=i+1,
                asset_code=f'ASSET00{i+1}',
                asset_name=f'测试资产{i+1}',
                location_id=1,
                custodian_id=1,
                asset_status='active',
                created_by=user
            )

        # 创建模板
        template = InventoryAssignmentTemplate.objects.create(
            organization=organization,
            template_name='测试模板',
            rules=[
                {
                    'mode': 'manual',
                    'condition': {'asset_ids': [1, 2]},
                    'executor_type': 'user',
                    'executor_value': str(user.id)
                },
                {
                    'mode': 'manual',
                    'condition': {'asset_ids': [3, 4]},
                    'executor_type': 'user',
                    'executor_value': str(user.id)
                }
            ],
            created_by=user
        )

        # 使用模板自动分配
        service = InventoryAssignmentService(task)
        assignments = service.auto_assign_by_template(template)

        # 验证结果
        assert len(assignments) == 2
        # 每个分配应该包含2个资产
        assert assignments[0].total_assigned == 2
        assert assignments[1].total_assigned == 2
        assert assignments[0].executor == user
        assert assignments[1].executor == user

    def test_assign_by_custodian(self, organization, user):
        """测试按保管人分配"""
        # 创建不同保管人的快照
        user2 = User.objects.create(
            organization=organization,
            username='user2',
            real_name='用户2'
        )

        task = InventoryTask.objects.create(
            task_code='TASK003',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        # 为user1创建快照
        for i in range(3):
            snapshot = InventorySnapshot.objects.create(
                task=task,
                asset_id=i+1,
                asset_code=f'ASSET00{i+1}',
                asset_name=f'测试资产{i+1}',
                location_id=1,
                custodian_id=user.id,
                asset_status='active',
                created_by=user
            )

        # 为user2创建快照
        for i in range(2):
            snapshot = InventorySnapshot.objects.create(
                task=task,
                asset_id=i+4,
                asset_code=f'ASSET00{i+4}',
                asset_name=f'测试资产{i+4}',
                location_id=1,
                custodian_id=user2.id,
                asset_status='active',
                created_by=user
            )

        # 按保管人分配
        service = InventoryAssignmentService(task)
        assignments = service.assign_by_custodian()

        # 验证结果
        assert len(assignments) == 2
        # user1应该有3个资产
        user1_assignments = [a for a in assignments if a.executor == user]
        user2_assignments = [a for a in assignments if a.executor == user2]

        assert len(user1_assignments) == 1
        assert user1_assignments[0].total_assigned == 3
        assert user1_assignments[0].mode == 'custodian'

        assert len(user2_assignments) == 1
        assert user2_assignments[0].total_assigned == 2
        assert user2_assignments[0].mode == 'custodian'

    def test_assign_random(self, organization, user):
        """测试随机分配"""
        # 创建用户
        user2 = User.objects.create(
            organization=organization,
            username='user2',
            real_name='用户2'
        )

        task = InventoryTask.objects.create(
            task_code='TASK004',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        # 创建6个快照
        for i in range(6):
            snapshot = InventorySnapshot.objects.create(
                task=task,
                asset_id=i+1,
                asset_code=f'ASSET00{i+1}',
                asset_name=f'测试资产{i+1}',
                location_id=1,
                custodian_id=user.id,
                asset_status='active',
                created_by=user
            )

        # 随机分配给2个用户
        service = InventoryAssignmentService(task)
        assignments = service.assign_random([user, user2])

        # 验证结果
        assert len(assignments) == 2
        assert assignments[0].executor in [user, user2]
        assert assignments[1].executor in [user, user2]
        assert assignments[0].executor != assignments[1].executor

        # 每个用户应该分配到3个资产
        for assignment in assignments:
            assert assignment.total_assigned == 3
            assert assignment.mode == 'random'
```

### 2. 执行人服务测试

```python
# backend/apps/inventory/tests/test_executor_service.py

import pytest
from django.utils import timezone
from apps.inventory.models import InventoryTask, InventoryAssignment, InventorySnapshot
from apps.inventory.services.assignment_service import InventoryExecutorService


@pytest.mark.django_db
class TestInventoryExecutorService:
    """执行人盘点服务测试"""

    def test_get_my_assignments(self, organization, user):
        """测试获取我的分配"""
        # 创建任务和分配
        task = InventoryTask.objects.create(
            task_code='TASK005',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            total_assigned=10,
            completed_count=5,
            status='in_progress',
            created_by=user
        )

        # 获取我的分配
        service = InventoryExecutorService(user)
        my_assignments = service.get_my_assignments()

        # 验证结果
        assert len(my_assignments) == 1
        assert my_assignments[0] == assignment

    def test_get_my_assignments_status_filter(self, organization, user):
        """测试按状态筛选我的分配"""
        # 创建多个分配
        task1 = InventoryTask.objects.create(
            task_code='TASK006',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        task2 = InventoryTask.objects.create(
            task_code='TASK007',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        assignment1 = InventoryAssignment.objects.create(
            task=task1,
            executor=user,
            mode='manual',
            status='in_progress',
            created_by=user
        )

        assignment2 = InventoryAssignment.objects.create(
            task=task2,
            executor=user,
            mode='manual',
            status='completed',
            created_by=user
        )

        # 获取执行中的分配
        service = InventoryExecutorService(user)
        in_progress_assignments = service.get_my_assignments('in_progress')

        # 验证结果
        assert len(in_progress_assignments) == 1
        assert in_progress_assignments[0] == assignment1

        # 获取已完成的分配
        completed_assignments = service.get_my_assignments('completed')
        assert len(completed_assignments) == 1
        assert completed_assignments[0] == assignment2

    def test_start_assignment(self, organization, user):
        """测试开始执行分配"""
        # 创建任务和分配
        task = InventoryTask.objects.create(
            task_code='TASK008',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            status='pending',
            created_by=user
        )

        # 开始执行
        service = InventoryExecutorService(user)
        service.start_assignment(assignment)

        # 验证状态
        assignment.refresh_from_db()
        assert assignment.status == 'in_progress'
        assert assignment.started_at is not None

    def test_complete_assignment(self, organization, user):
        """测试完成分配"""
        # 创建任务、资产和分配
        task = InventoryTask.objects.create(
            task_code='TASK009',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        asset1 = Asset.objects.create(
            organization=organization,
            asset_code='ASSET001',
            asset_name='测试资产1',
            created_by=user
        )

        asset2 = Asset.objects.create(
            organization=organization,
            asset_code='ASSET002',
            asset_name='测试资产2',
            created_by=user
        )

        # 创建快照
        snapshot1 = InventorySnapshot.objects.create(
            task=task,
            asset=asset1,
            asset_code=asset1.asset_code,
            asset_name=asset1.asset_name,
            location_id=1,
            custodian_id=user.id,
            asset_status='active',
            created_by=user
        )

        snapshot2 = InventorySnapshot.objects.create(
            task=task,
            asset=asset2,
            asset_code=asset2.asset_code,
            asset_name=asset2.asset_name,
            location_id=1,
            custodian_id=user.id,
            asset_status='active',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            assigned_snapshot_ids=[snapshot1.id, snapshot2.id],
            total_assigned=2,
            status='in_progress',
            created_by=user
        )

        # 创建扫描记录（只扫描了1个资产）
        InventoryScan.objects.create(
            task=task,
            scanned_by=user,
            scan_status='normal',
            asset=asset1,
            created_by=user
        )

        # 完成分配
        service = InventoryExecutorService(user)
        service.complete_assignment(assignment)

        # 验证结果
        assignment.refresh_from_db()
        assert assignment.status == 'completed'
        assert assignment.completed_at is not None
        assert assignment.completed_count == 1
        assert assignment.missing_count == 1

    def test_get_my_today_tasks(self, organization, user):
        """测试获取今日任务统计"""
        # 创建今天的任务
        today = timezone.now().date()
        task = InventoryTask.objects.create(
            task_code='TASK010',
            organization=organization,
            inventory_type='full',
            created_at=timezone.now(),
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            total_assigned=10,
            completed_count=3,
            status='in_progress',
            created_by=user
        )

        # 获取今日任务
        service = InventoryExecutorService(user)
        today_tasks = service.get_my_today_tasks()

        # 验证结果
        assert today_tasks['total_count'] == 1
        assert today_tasks['total_assets'] == 10
        assert today_tasks['completed_assets'] == 3
        assert len(today_tasks['assignments']) == 1
        assert today_tasks['assignments'][0]['task_code'] == 'TASK010'
```

### 3. 查看权限服务测试

```python
# backend/apps/inventory/tests/test_view_permission_service.py

import pytest
from django.utils import timezone
from apps.inventory.models import (
    InventoryTask, InventoryAssignment, InventoryTaskViewer,
    InventoryTaskViewConfig, InventoryViewLog
)
from apps.inventory.services.view_permission_service import InventoryViewPermissionService


@pytest.mark.django_db
class TestInventoryViewPermissionService:
    """盘点查看权限服务测试"""

    def test_get_or_create_config(self, organization, user):
        """测试获取或创建配置"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK011',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        service = InventoryViewPermissionService(task)
        config = service.get_or_create_config()

        # 验证创建
        assert config.task == task
        assert isinstance(config, InventoryTaskViewConfig)

    def test_update_config(self, organization, user):
        """测试更新配置"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK012',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        service = InventoryViewPermissionService(task)

        # 更新配置
        config_data = {
            'allow_department_leader': True,
            'department_leader_scope': 'department_assets',
            'allow_asset_admin': False,
        }

        config = service.update_config(config_data)

        # 验证更新
        assert config.allow_department_leader is True
        assert config.department_leader_scope == 'department_assets'
        assert config.allow_asset_admin is False

    def test_add_viewers(self, organization, user):
        """测试添加查看者"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK013',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        service = InventoryViewPermissionService(task)

        # 添加查看者
        viewer_ids = [str(user.id)]
        viewers = service.add_viewers(
            viewer_ids=viewer_ids,
            scope='all',
            source='manual'
        )

        # 验证结果
        assert len(viewers) == 1
        assert viewers[0].task == task
        assert viewers[0].viewer == user
        assert viewers[0].scope == 'all'
        assert viewers[0].source == 'manual'

    def test_can_view_task_as_creator(self, organization, user):
        """测试任务创建者查看权限"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK014',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        service = InventoryViewPermissionService(task)

        # 验证创建者有查看权限
        assert service.can_view_task(user) is True

    def test_can_view_task_as_executor(self, organization, user):
        """测试执行人查看权限"""
        # 创建任务和分配
        task = InventoryTask.objects.create(
            task_code='TASK015',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            created_by=user
        )

        service = InventoryViewPermissionService(task)

        # 验证执行人有查看权限
        assert service.can_view_task(user) is True

    def test_can_view_task_as_viewer(self, organization, user):
        """测试显式指定的查看者"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK016',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        service = InventoryViewPermissionService(task)

        # 添加查看者
        service.add_viewers([str(user.id)], scope='all', source='manual')

        # 验证查看权限
        assert service.can_view_task(user) is True

    def test_log_view(self, organization, user):
        """测试记录查看日志"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK017',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        service = InventoryViewPermissionService(task)

        # 模拟request对象
        class MockRequest:
            def __init__(self):
                self.META = {
                    'HTTP_X_FORWARDED_FOR': '192.168.1.1',
                    'HTTP_USER_AGENT': 'Mozilla/5.0'
                }

        request = MockRequest()

        # 记录日志
        service.log_view(user, 'web', request)

        # 验证日志
        log = InventoryViewLog.objects.filter(
            task=task,
            viewer=user
        ).first()

        assert log is not None
        assert log.view_method == 'web'
        assert log.ip_address == '192.168.1.1'
        assert 'Mozilla' in log.user_agent
```

### 4. API接口测试

```python
# backend/apps/inventory/tests/test_assignment_api.py

import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from apps.inventory.models import InventoryTask, InventoryAssignment
from apps.accounts.models import User


@pytest.mark.django_db
class TestAssignmentAPI:
    """盘点分配API测试"""

    def test_list_assignments_api(self, auth_client, organization, user):
        """测试查询分配列表API"""
        # 创建任务和分配
        task = InventoryTask.objects.create(
            task_code='TASK018',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            status='pending',
            created_by=user
        )

        url = reverse('inventory-assignment-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['results']) == 1

    def test_create_assignments_api(self, auth_client, organization, user):
        """测试创建分配API"""
        # 创建任务
        task = InventoryTask.objects.create(
            task_code='TASK019',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        # 创建快照
        for i in range(3):
            snapshot = InventorySnapshot.objects.create(
                task=task,
                asset_id=i+1,
                asset_code=f'ASSET00{i+1}',
                asset_name=f'测试资产{i+1}',
                location_id=1,
                custodian_id=1,
                asset_status='active',
                created_by=user
            )

        url = reverse('inventory-assignment-create-assignments', kwargs={'pk': str(task.id)})
        data = {
            'assignments': [
                {
                    'executor_id': str(user.id),
                    'mode': 'manual',
                    'scope_config': {'asset_ids': [1, 2, 3]},
                    'instruction': '测试分配'
                }
            ]
        }

        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']) == 1

    def test_my_assignments_api(self, auth_client, organization, user):
        """测试我的分配API"""
        # 创建任务和分配
        task = InventoryTask.objects.create(
            task_code='TASK020',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            status='pending',
            created_by=user
        )

        url = reverse('my-inventory-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['results']) == 1

    def test_start_assignment_api(self, auth_client, organization, user):
        """测试开始分配API"""
        # 创建任务和分配
        task = InventoryTask.objects.create(
            task_code='TASK021',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            status='pending',
            created_by=user
        )

        url = reverse('my-inventory-start')
        data = {'assignment_id': str(assignment.id)}
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '盘点已开始'

        # 验证状态
        assignment.refresh_from_db()
        assert assignment.status == 'in_progress'

    def test_complete_assignment_api(self, auth_client, organization, user):
        """测试完成分配API"""
        # 创建任务、资产和分配
        task = InventoryTask.objects.create(
            task_code='TASK022',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ASSET001',
            asset_name='测试资产',
            created_by=user
        )

        snapshot = InventorySnapshot.objects.create(
            task=task,
            asset=asset,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            location_id=1,
            custodian_id=1,
            asset_status='active',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            assigned_snapshot_ids=[snapshot.id],
            total_assigned=1,
            status='in_progress',
            created_by=user
        )

        # 创建扫描记录
        InventoryScan.objects.create(
            task=task,
            scanned_by=user,
            scan_status='normal',
            asset=asset,
            created_by=user
        )

        url = reverse('my-inventory-complete')
        data = {'assignment_id': str(assignment.id)}
        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == '盘点已完成'

        # 验证状态
        assignment.refresh_from_db()
        assert assignment.status == 'completed'
        assert assignment.completed_count == 1

    def test_pending_assets_api(self, auth_client, organization, user):
        """测试获取待盘点资产API"""
        # 创建任务、资产和分配
        task = InventoryTask.objects.create(
            task_code='TASK023',
            organization=organization,
            inventory_type='full',
            created_by=user
        )

        asset = Asset.objects.create(
            organization=organization,
            asset_code='ASSET001',
            asset_name='测试资产',
            created_by=user
        )

        snapshot = InventorySnapshot.objects.create(
            task=task,
            asset=asset,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            location_id=1,
            custodian_id=1,
            asset_status='active',
            created_by=user
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=user,
            mode='manual',
            assigned_snapshot_ids=[snapshot.id],
            total_assigned=1,
            status='in_progress',
            created_by=user
        )

        url = reverse('my-inventory-pending-assets')
        response = auth_client.get(url, {'assignment_id': str(assignment.id)})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['asset_code'] == 'ASSET001'
```

---

## 后续任务

所有Phase已完成！

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
        "executor": {...},
        "mode": "manual",
        "status": "in_progress",
        "total_assigned": 100,
        "completed_count": 50,
        "progress": 50,
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
        "next": "https://api.example.com/api/inventory-assignments/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "task_code": "INV-2026-001",
                "executor_name": "张三",
                "mode": "manual",
                "status": "in_progress",
                "progress": 50,
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
            "executor": ["执行人不能为空"],
            "task": ["盘点任务不存在"]
        }
    }
}
```

### 标准 CRUD 端点

本模块所有 ViewSet 继承自 `BaseModelViewSetWithBatch`，自动提供以下标准端点：

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/inventory-assignments/` | 列表查询（分页、过滤、搜索） |
| GET | `/api/inventory-assignments/{id}/` | 获取单个盘点分配详情 |
| POST | `/api/inventory-assignments/` | 创建新的盘点分配 |
| PUT | `/api/inventory-assignments/{id}/` | 完整更新盘点分配 |
| PATCH | `/api/inventory-assignments/{id}/` | 部分更新盘点分配 |
| DELETE | `/api/inventory-assignments/{id}/` | 软删除盘点分配 |

### 批量操作端点

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| POST | `/api/inventory-assignments/batch-delete/` | 批量软删除 |
| POST | `/api/inventory-assignments/batch-restore/` | 批量恢复 |
| POST | `/api/inventory-assignments/batch-update/` | 批量字段更新 |

#### 批量删除请求示例

```http
POST /api/inventory-assignments/batch-delete/
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
| GET | `/api/inventory-assignments/deleted/` | 查询已删除的盘点分配 |
| POST | `/api/inventory-assignments/{id}/restore/` | 恢复单个已删除的盘点分配 |
| GET | `/api/inventory-assignments/{id}/history/` | 获取盘点分配变更历史 |
| POST | `/api/inventory-tasks/{id}/create-assignments/` | 为盘点任务创建分配 |
| POST | `/api/inventory-tasks/{id}/auto-assign/` | 自动分配（按模板/规则） |
| GET | `/api/my-inventory/` | 获取我的盘点任务列表 |
| GET | `/api/my-inventory/today/` | 获取今日盘点任务统计 |
| POST | `/api/my-inventory/start/` | 开始执行盘点任务 |
| POST | `/api/my-inventory/complete/` | 完成盘点任务 |

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