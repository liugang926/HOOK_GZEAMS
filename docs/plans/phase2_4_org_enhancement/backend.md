# Phase 2.4: 组织架构增强与数据权限 - PRD

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

## 1. 需求概述

### 1.1 业务背景

当前组织架构模块存在以下痛点：
- 一人只能属于一个部门，无法处理兼职/借调场景
- 无部门负责人概念，无法按部门分配审批流程
- 部门路径不完整，无法展示完整层级关系
- 无数据权限控制，用户可见范围过大

### 1.2 目标用户

| 用户角色 | 使用场景 | 权限需求 |
|---------|---------|---------|
| 系统管理员 | 管理组织架构、配置权限 | 全部权限 |
| 部门负责人 | 审批本部门业务单据 | 本部门及下级数据权限 |
| 普通用户 | 查看所属部门资产 | 本部门数据权限 |
| 兼职人员 | 在多个部门任职 | 多部门归属 |

### 1.3 功能范围

本次实现范围包括：
- 支持一人多部门（UserDepartment关联表）
- 支持部门负责人设置
- 支持完整部门路径显示
- 基于部门的数据权限控制
- 资产操作流程（调拨、归还、借用、领用）

---

## 2. 后端设计

### 2.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| ViewSet | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法 |

### 2.2 数据模型

#### 2.2.1 Department（部门）扩展

```python
# apps/organizations/models.py

from django.db import models
from apps.common.models import BaseModel

class Department(BaseModel):
    """部门模型 - 增强版"""

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='所属组织'
    )

    # 基础信息
    code = models.CharField(max_length=50, verbose_name='部门编码')
    name = models.CharField(max_length=100, verbose_name='部门名称')

    # 层级关系
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级部门'
    )
    level = models.IntegerField(default=0, verbose_name='层级')
    path = models.CharField(max_length=500, default='', verbose_name='路径')
    order = models.IntegerField(default=0, verbose_name='排序')

    # 完整路径显示（如：总部/技术部/后端组）
    full_path = models.CharField(
        max_length=500,
        default='',
        verbose_name='完整路径'
    )
    full_path_name = models.CharField(
        max_length=1000,
        default='',
        verbose_name='完整路径名称'
    )

    # 部门负责人
    leader = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_departments',
        verbose_name='部门负责人'
    )

    # 同步字段
    wework_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='企业微信部门ID'
    )
    dingtalk_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='钉钉部门ID'
    )
    feishu_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='飞书部门ID'
    )

    # 外部系统负责人ID（同步时暂存）
    wework_leader_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='企业微信负责人ID'
    )
    dingtalk_leader_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='钉钉负责人ID'
    )
    feishu_leader_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name='飞书负责人ID'
    )

    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    def save(self, *args, **kwargs):
        # 更新层级和路径
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path}/{self.code}" if self.parent else f"/{self.code}"
            self.full_path_name = f"{self.parent.full_path_name}/{self.name}" if self.parent else self.name
            self.full_path = self.parent.full_path + '/' + self.name if self.parent else self.name
        else:
            self.level = 0
            self.path = f"/{self.code}"
            self.full_path_name = self.name
            self.full_path = self.name

        super().save(*args, **kwargs)

        # 递归更新子部门路径
        self._update_children_paths()

    def _update_children_paths(self):
        """更新子部门的路径"""
        for child in self.children.all():
            child.save(update_fields=['level', 'path', 'full_path', 'full_path_name'])

    def get_descendant_ids(self):
        """获取所有后代部门ID"""
        ids = [self.id]
        for child in self.children.all():
            ids.extend(child.get_descendant_ids())
        return ids

    class Meta:
        db_table = 'departments'
        verbose_name = '部门'
        verbose_name_plural = '部门'
        unique_together = [['organization', 'code']]
        indexes = [
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'wework_dept_id']),
        ]
```

#### 2.2.2 UserDepartment（用户部门关联）

```python
class UserDepartment(BaseModel):
    """用户部门关联表 - 支持一人多部门"""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='user_departments',
        verbose_name='用户'
    )

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='user_departments',
        verbose_name='所属组织'
    )

    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='user_departments',
        verbose_name='部门'
    )

    # 是否为主部门（用于资产归属）
    is_primary = models.BooleanField(
        default=False,
        verbose_name='是否主部门'
    )

    # 是否为资产部门
    is_asset_department = models.BooleanField(
        default=False,
        verbose_name='是否资产部门'
    )

    # 职位
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='职位'
    )

    # 是否为部门负责人
    is_leader = models.BooleanField(
        default=False,
        verbose_name='是否部门负责人'
    )

    # 同步信息
    wework_department_order = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='企业微信部门排序'
    )
    is_primary_in_wework = models.BooleanField(
        default=False,
        verbose_name='企业微信主部门'
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 确保每个用户在同一组织只有一个主部门
        if self.is_primary:
            UserDepartment.objects.filter(
                user=self.user,
                organization=self.organization,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

    class Meta:
        db_table = 'user_departments'
        verbose_name = '用户部门关联'
        unique_together = [['user', 'organization', 'department']]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['is_primary']),
        ]
```

#### 2.2.3 资产操作流程模型

```python
# apps/assets/models/operations.py

from apps.common.models import BaseModel
from apps.accounts.models import User
from apps.assets.models import Asset

class AssetTransfer(BaseModel):
    """资产调拨单"""

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='transfers'
    )

    transfer_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='调拨单号'
    )

    # 调出信息
    from_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='transfers_from',
        verbose_name='调出部门'
    )
    from_custodian = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='transfers_from',
        verbose_name='调出保管人'
    )
    from_location = models.ForeignKey(
        'assets.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_from',
        verbose_name='调出位置'
    )

    # 调入信息
    to_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='transfers_to',
        verbose_name='调入部门'
    )
    to_custodian = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='transfers_to',
        verbose_name='调入保管人'
    )
    to_location = models.ForeignKey(
        'assets.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_to',
        verbose_name='调入位置'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', '草稿'),
            ('pending', '待审批'),
            ('approved', '已批准'),
            ('rejected', '已拒绝'),
            ('transferring', '调拨中'),
            ('completed', '已完成'),
            ('cancelled', '已取消'),
        ],
        default='draft',
        verbose_name='状态'
    )

    # 关联工作流
    workflow_instance = models.ForeignKey(
        'workflows.WorkflowInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers',
        verbose_name='工作流实例'
    )

    # 申请信息
    applicant = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='applied_transfers',
        verbose_name='申请人'
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')

    # 审批信息
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_transfers',
        verbose_name='审批人'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    approval_comment = models.TextField(blank=True, verbose_name='审批意见')

    # 备注
    reason = models.TextField(verbose_name='调拨原因')
    remark = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'asset_transfers'
        verbose_name = '资产调拨'
        indexes = [
            models.Index(fields=['transfer_code']),
            models.Index(fields=['status']),
            models.Index(fields=['applicant']),
        ]


class AssetTransferItem(BaseModel):
    """资产调拨明细"""

    transfer = models.ForeignKey(
        AssetTransfer,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='调拨单'
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='transfer_items',
        verbose_name='资产'
    )

    status_before = models.CharField(
        max_length=20,
        verbose_name='调出前状态'
    )

    # 确认信息
    confirmed = models.BooleanField(default=False, verbose_name='是否确认接收')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='确认时间')
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_transfer_items',
        verbose_name='确认人'
    )

    class Meta:
        db_table = 'asset_transfer_items'
        verbose_name = '调拨明细'


class AssetReturn(BaseModel):
    """资产归还单"""

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='returns'
    )

    return_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='归还单号'
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='returns',
        verbose_name='资产'
    )

    # 归还人信息
    returner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='returns',
        verbose_name='归还人'
    )
    returner_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='returns',
        verbose_name='归还人部门'
    )

    # 归还状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待确认'),
            ('confirmed', '已确认'),
            ('rejected', '已拒收'),
        ],
        default='pending',
        verbose_name='状态'
    )

    # 资产状态
    asset_status = models.CharField(
        max_length=20,
        choices=[
            ('normal', '正常'),
            ('damaged', '损坏'),
            ('lost', '丢失'),
            ('need_repair', '需维修'),
        ],
        default='normal',
        verbose_name='资产状态'
    )

    class Meta:
        db_table = 'asset_returns'
        verbose_name = '资产归还'


class AssetBorrow(BaseModel):
    """资产借用单"""

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='borrows'
    )

    borrow_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='借用单号'
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='borrows',
        verbose_name='资产'
    )

    # 借用人信息
    borrower = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='borrows',
        verbose_name='借用人'
    )
    borrower_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='borrows',
        verbose_name='借用人部门'
    )

    # 借用时间
    borrow_date = models.DateField(verbose_name='借用日期')
    expected_return_date = models.DateField(verbose_name='预计归还日期')
    actual_return_date = models.DateField(null=True, blank=True, verbose_name='实际归还日期')

    # 状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待审批'),
            ('approved', '已批准'),
            ('borrowed', '借用中'),
            ('returned', '已归还'),
            ('overdue', '已逾期'),
            ('rejected', '已拒绝'),
        ],
        default='pending',
        verbose_name='状态'
    )

    # 关联工作流
    workflow_instance = models.ForeignKey(
        'workflows.WorkflowInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='borrows',
        verbose_name='工作流实例'
    )

    class Meta:
        db_table = 'asset_borrows'
        verbose_name = '资产借用'


class AssetUse(BaseModel):
    """资产领用单"""

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='uses'
    )

    use_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='领用单号'
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.PROTECT,
        related_name='uses',
        verbose_name='资产'
    )

    # 领用人信息
    receiver = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='uses',
        verbose_name='领用人'
    )
    receiver_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='uses',
        verbose_name='领用部门'
    )

    # 领用日期
    use_date = models.DateField(auto_now_add=True, verbose_name='领用日期')

    # 状态
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '待审批'),
            ('approved', '已批准'),
            ('rejected', '已拒绝'),
            ('completed', '已完成'),
        ],
        default='pending',
        verbose_name='状态'
    )

    # 关联工作流
    workflow_instance = models.ForeignKey(
        'workflows.WorkflowInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uses',
        verbose_name='工作流实例'
    )

    class Meta:
        db_table = 'asset_uses'
        verbose_name = '资产领用'
```

### 2.3 序列化器

```python
# apps/organizations/serializers.py

from apps.common.serializers.base import BaseModelSerializer
from apps.accounts.serializers import UserSerializer
from apps.organizations.models import Organization, Department, UserDepartment

class DepartmentSerializer(BaseModelSerializer):
    """部门序列化器"""

    leader_name = serializers.CharField(source='leader.real_name', read_only=True, allow_null=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)

    class Meta(BaseModelSerializer.Meta):
        model = Department
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent', 'parent_name', 'level', 'path',
            'full_path', 'full_path_name', 'leader', 'leader_name',
            'wework_dept_id', 'dingtalk_dept_id', 'feishu_dept_id',
            'is_active', 'order'
        ]


class DepartmentTreeSerializer(DepartmentSerializer):
    """部门树序列化器"""

    children = DepartmentSerializer(many=True, read_only=True)

    class Meta(DepartmentSerializer.Meta):
        fields = DepartmentSerializer.Meta.fields + ['children']


class UserDepartmentSerializer(BaseModelSerializer):
    """用户部门关联序列化器"""

    user_name = serializers.CharField(source='user.real_name', read_only=True)
    department_name = serializers.CharField(source='department.full_path_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = UserDepartment
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'user_name', 'department', 'department_name',
            'is_primary', 'is_asset_department', 'position', 'is_leader'
        ]


# apps/assets/serializers/operations.py

from apps.common.serializers.base import BaseModelSerializer
from apps.assets.models.operations import AssetTransfer, AssetTransferItem, AssetReturn, AssetBorrow, AssetUse

class AssetTransferSerializer(BaseModelSerializer):
    """资产调拨序列化器"""

    from_department_name = serializers.CharField(source='from_department.full_path_name', read_only=True)
    to_department_name = serializers.CharField(source='to_department.full_path_name', read_only=True)
    applicant_name = serializers.CharField(source='applicant.real_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetTransfer
        fields = BaseModelSerializer.Meta.fields + [
            'transfer_code', 'from_department', 'from_department_name',
            'from_custodian', 'from_location', 'to_department',
            'to_department_name', 'to_custodian', 'to_location',
            'status', 'applicant', 'applicant_name', 'reason', 'remark'
        ]


class AssetReturnSerializer(BaseModelSerializer):
    """资产归还序列化器"""

    returner_name = serializers.CharField(source='returner.real_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetReturn
        fields = BaseModelSerializer.Meta.fields + [
            'return_code', 'asset', 'returner', 'returner_name',
            'returner_department', 'status', 'asset_status'
        ]


class AssetBorrowSerializer(BaseModelSerializer):
    """资产借用序列化器"""

    borrower_name = serializers.CharField(source='borrower.real_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetBorrow
        fields = BaseModelSerializer.Meta.fields + [
            'borrow_code', 'asset', 'borrower', 'borrower_name',
            'borrower_department', 'borrow_date', 'expected_return_date',
            'actual_return_date', 'status', 'purpose'
        ]


class AssetUseSerializer(BaseModelSerializer):
    """资产领用序列化器"""

    receiver_name = serializers.CharField(source='receiver.real_name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetUse
        fields = BaseModelSerializer.Meta.fields + [
            'use_code', 'asset', 'receiver', 'receiver_name',
            'receiver_department', 'use_date', 'status', 'purpose'
        ]
```

### 2.4 ViewSets

```python
# apps/organizations/views.py

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.organizations.models import Department, UserDepartment
from apps.organizations.serializers import (
    DepartmentSerializer,
    DepartmentTreeSerializer,
    UserDepartmentSerializer
)
from apps.organizations.filters import DepartmentFilter, UserDepartmentFilter
from apps.organizations.services import DepartmentService

class DepartmentViewSet(BaseModelViewSetWithBatch):
    """部门 ViewSet"""

    queryset = Department.objects.select_related('parent', 'leader', 'organization').all()
    serializer_class = DepartmentSerializer
    filterset_class = DepartmentFilter

    def get_serializer_class(self):
        """根据action返回不同的序列化器"""
        if self.action == 'tree':
            return DepartmentTreeSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取完整部门树"""
        org_id = get_current_organization()
        tree = Department.get_full_path_tree(org_id)
        return Response({'tree': tree})

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """获取子部门"""
        dept = self.get_object()
        children = dept.children.filter(is_active=True)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """获取部门下的用户"""
        dept = self.get_object()
        user_depts = UserDepartment.objects.filter(
            department=dept
        ).select_related('user')
        serializer = UserDepartmentSerializer(user_depts, many=True)
        return Response(serializer.data)


class UserDepartmentViewSet(BaseModelViewSetWithBatch):
    """用户部门关联 ViewSet"""

    queryset = UserDepartment.objects.select_related(
        'user', 'department', 'organization'
    ).all()
    serializer_class = UserDepartmentSerializer
```

### 2.5 服务层

```python
# apps/organizations/services/permission_service.py

from typing import List, Set, Dict
from apps.common.services.base_crud import BaseCRUDService
from apps.organizations.models import Department, UserDepartment
from apps.accounts.models import User
from apps.assets.models import Asset

class OrgDataPermissionService:
    """基于组织架构的数据权限服务"""

    def __init__(self, user: User):
        self.user = user

    def get_viewable_department_ids(self, recursive: bool = True) -> Set[int]:
        """获取用户可查看的部门ID列表"""
        dept_ids = set()

        # 用户自己所属的部门
        my_depts = UserDepartment.objects.filter(
            user=self.user
        ).values_list('department_id', flat=True)
        dept_ids.update(my_depts)

        # 用户负责的部门（及其子部门）
        led_depts = Department.objects.filter(leader=self.user)
        for dept in led_depts:
            dept_ids.add(dept.id)
            if recursive:
                dept_ids.update(dept.get_descendant_ids())

        return dept_ids

    def get_viewable_user_ids(self, department_ids: Set[int] = None) -> Set[int]:
        """获取可查看的用户ID列表"""
        if department_ids is None:
            department_ids = self.get_viewable_department_ids()

        user_ids = set(UserDepartment.objects.filter(
            department_id__in=department_ids
        ).values_list('user_id', flat=True))

        user_ids.add(self.user.id)
        return user_ids

    def can_view_asset(self, asset: Asset) -> bool:
        """判断是否可以查看资产"""
        if not asset.custodian_id:
            return True

        if asset.custodian_id == self.user.id:
            return True

        viewable_user_ids = self.get_viewable_user_ids()
        return asset.custodian_id in viewable_user_ids

    def can_manage_asset(self, asset: Asset) -> bool:
        """判断是否可以管理资产"""
        if asset.department_id:
            dept = Department.objects.filter(id=asset.department_id).first()
            if dept and dept.leader_id == self.user.id:
                return True

        viewable_dept_ids = self.get_viewable_department_ids()
        if asset.department_id in viewable_dept_ids:
            return True

        return False

    def get_managed_asset_queryset(self, Asset_model):
        """获取可管理的资产查询集"""
        dept_ids = self.get_viewable_department_ids()
        user_ids = self.get_viewable_user_ids(dept_ids)

        from django.db.models import Q
        return Asset_model.objects.filter(
            Q(custodian_id__in=user_ids) |
            Q(department_id__in=dept_ids)
        ).distinct()
```

### 2.6 过滤器

```python
# apps/organizations/filters.py

from apps.common.filters.base import BaseModelFilter
import django_filters

class DepartmentFilter(BaseModelFilter):
    """部门过滤器"""

    code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    full_path = django_filters.CharFilter(lookup_expr='icontains')
    leader = django_filters.UUIDFilter(field_name='leader_id')
    parent = django_filters.UUIDFilter(field_name='parent_id')
    level = django_filters.NumberFilter()
    wework_dept_id = django_filters.CharFilter()
    dingtalk_dept_id = django_filters.CharFilter()
    feishu_dept_id = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = Department
        fields = BaseModelFilter.Meta.fields + [
            'code', 'name', 'full_path', 'leader', 'parent', 'level',
            'wework_dept_id', 'dingtalk_dept_id', 'feishu_dept_id',
            'is_active'
        ]


class UserDepartmentFilter(BaseModelFilter):
    """用户部门关联过滤器"""

    user = django_filters.UUIDFilter(field_name='user_id')
    department = django_filters.UUIDFilter(field_name='department_id')
    is_primary = django_filters.BooleanFilter()
    is_asset_department = django_filters.BooleanFilter()
    is_leader = django_filters.BooleanFilter()
    position = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(BaseModelFilter.Meta):
        model = UserDepartment
        fields = BaseModelFilter.Meta.fields + [
            'user', 'department', 'is_primary', 'is_asset_department',
            'is_leader', 'position'
        ]
```

---

## 3. 错误处理机制

### 3.1 异常类型定义

| 异常类型 | 适用场景 | HTTP状态码 | 说明 |
|---------|---------|-------------|------|
| `NetworkException` | 第三方平台网络连接失败 | 502 | 网络超时或连接错误 |
| `APIException` | 第三方平台API调用失败 | 502 | API返回错误响应或格式错误 |
| `ValidationException` | 数据验证失败 | 400 | 必填字段缺失、格式错误 |
| `SyncException` | 数据同步失败 | 500 | 同步逻辑执行异常 |
| `PermissionException` | 权限不足 | 403 | 用户权限验证失败 |
| `OrganizationException` | 组织架构业务异常 | 400 | 部门循环引用、路径冲突等 |

### 3.2 重试策略

| 异常类型 | 重试次数 | 初始延迟 | 延迟倍数 | 最大延迟 |
|---------|---------|---------|---------|---------|
| `NetworkException` | 3 | 60s | 2x | 480s |
| `APIException` | 2 | 60s | 2x | 120s |
| `SyncException` | 3 | 60s | 2x | 480s |
| 其他异常 | 0 | - | - | - |

**重试逻辑**：
- 指数退避算法：`delay = initial_delay * (2 ^ retry_count)`
- 最大重试次数限制，避免无限重试
- 每次重试记录详细信息到日志
- 重试失败后将错误记录到 `IntegrationLog` 模型

### 3.3 错误日志记录

所有错误必须记录到 `IntegrationLog` 模型，包含以下字段：
- `request_url`: 请求的URL
- `request_body`: 请求体数据
- `response_body`: 响应体数据（如果有）
- `status_code`: HTTP状态码
- `error_message`: 错误信息
- `stack_trace`: 堆栈跟踪（如果有）
- `retry_count`: 重试次数
- `execution_time_ms`: 执行时间（毫秒）

---

## 4. API接口设计

### 4.1 标准CRUD端点

继承 `BaseModelViewSet` 自动提供，详见 `api.md`。

### 4.2 自定义端点

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/organizations/departments/tree/` | 获取完整部门树 | organizations.view_department |
| GET | `/api/organizations/departments/{id}/children/` | 获取子部门 | organizations.view_department |
| GET | `/api/organizations/departments/{id}/users/` | 获取部门用户 | organizations.view_department |
| POST | `/api/organizations/users/{id}/set-primary-department/` | 设置主部门 | organizations.change_userdepartment |

### 4.3 数据权限端点

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/organizations/my-permissions/` | 获取当前用户权限 | organizations.view_permission |
| GET | `/api/organizations/viewable-departments/` | 获取可查看部门列表 | organizations.view_permission |
| GET | `/api/organizations/viewable-users/` | 获取可查看用户列表 | organizations.view_permission |

### 4.4 资产操作端点

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/assets/transfers/` | 创建调拨单 | assets.create_transfer |
| POST | `/api/assets/transfers/{id}/approve/` | 审批调拨单 | assets.approve_transfer |
| POST | `/api/assets/returns/` | 创建归还单 | assets.create_return |
| POST | `/api/assets/borrows/` | 创建借用单 | assets.create_borrow |
| POST | `/api/assets/uses/` | 创建领用单 | assets.create_use |

---

## 5. 前端设计

### 5.1 公共组件引用

#### 页面组件
- 列表页：`BaseListPage` + `useListPage`
- 表单页：`BaseFormPage` + `useFormPage`
- 详情页：`BaseDetailPage`

#### 布局组件
- 标签页：`DynamicTabs`
- 区块容器：`SectionBlock`

### 5.2 页面布局

参考 `default_page_layouts.md` 中的默认布局规范。

### 5.3 部门选择器组件

```vue
<!-- frontend/src/components/common/DepartmentTreeSelect.vue -->

<template>
    <el-cascader
        v-model="selectedValue"
        :options="departmentTree"
        :props="cascaderProps"
        :show-all-levels="false"
        :clearable="clearable"
        :placeholder="placeholder"
        @change="handleChange"
        :disabled="disabled"
    />
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { departmentApi } from '@/api/organizations'

const props = defineProps({
    modelValue: [String, Number],
    clearable: {
        type: Boolean,
        default: true
    },
    disabled: {
        type: Boolean,
        default: false
    },
    placeholder: {
        type: String,
        default: '请选择部门'
    },
    checkable: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['update:modelValue', 'change'])

const departmentTree = ref([])
const selectedValue = ref(props.modelValue)

const cascaderProps = {
    value: 'id',
    label: 'full_path_name',
    children: 'children',
    checkStrictly: props.checkable,
    emitPath: false
}

const loadDepartmentTree = async () => {
    const response = await departmentApi.getTree()
    departmentTree.value = response.data.tree
}

const handleChange = (value) => {
    emit('update:modelValue', value)
    emit('change', value)
}

onMounted(() => {
    loadDepartmentTree()
})

defineExpose({
    load: loadDepartmentTree
})
</script>
```

### 5.4 页面路由配置

```javascript
// frontend/src/router/index.js

{
    path: '/organizations',
    name: 'OrganizationList',
    component: () => import('@/views/organizations/OrganizationList.vue')
},
{
    path: '/organizations/departments',
    name: 'DepartmentList',
    component: () => import('@/views/organizations/DepartmentList.vue')
},
{
    path: '/organizations/departments/:id',
    name: 'DepartmentDetail',
    component: () => import('@/views/organizations/DepartmentDetail.vue')
}
```

---

## 6. 权限设计

### 6.1 权限定义

| 权限代码 | 说明 | 角色 |
|---------|------|------|
| organizations.view_department | 查看部门 | 所有用户 |
| organizations.add_department | 创建部门 | 管理员 |
| organizations.change_department | 编辑部门 | 管理员 |
| organizations.delete_department | 删除部门 | 管理员 |
| organizations.manage_user_department | 管理用户部门 | 管理员 |
| assets.create_transfer | 创建调拨单 | 资产管理员、部门负责人 |
| assets.approve_transfer | 审批调拨单 | 部门负责人 |

### 6.2 数据权限规则

| 范围 | 说明 | 适用角色 |
|------|------|---------|
| 全部数据 | 所有资产 | 系统管理员 |
| 本部门及下级 | 本部门及其子部门资产 | 部门负责人 |
| 本部门 | 仅本部门资产 | 普通用户 |
| 本人 | 仅自己创建的数据 | 普通用户 |

---

## 7. 实施计划

| 阶段 | 任务 | 估时 |
|------|------|------|
| 1 | 数据模型开发 | 3天 |
| 2 | 后端API开发 | 5天 |
| 3 | 数据权限服务开发 | 4天 |
| 4 | 前端页面开发 | 5天 |
| 5 | 联调测试 | 2天 |
| 6 | 上线部署 | 1天 |

**总计**: 20天

---

## 7. 测试用例

### 7.1 部门管理测试

| 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
|---------|---------|---------|---------|
| 创建部门 | 已登录管理员权限 | 新增部门，填写编码、名称、上级部门 | 部门创建成功，路径自动生成 |
| 移动部门 | 存在子部门 | 修改部门上级 | 部门及其子部门路径自动更新 |
| 设置负责人 | 存在用户列表 | 选择用户设为负责人 | 负责人设置成功 |
| 删除部门 | 部门无子部门、无用户 | 删除部门 | 部门软删除成功 |

### 7.2 用户部门关联测试

| 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
|---------|---------|---------|---------|
| 添加用户部门 | 存在用户和部门 | 为用户添加部门关联 | 关联成功 |
| 设置主部门 | 用户有多个部门 | 将某部门设为主部门 | 其他部门主部门标识自动清除 |
| 移除部门关联 | 存在用户部门关联 | 删除关联 | 关联软删除成功 |

### 7.3 数据权限测试

| 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
|---------|---------|---------|---------|
| 部门负责人查看范围 | 用户是某部门负责人 | 查看资产列表 | 可见本部门及子部门资产 |
| 普通用户查看范围 | 用户是普通员工 | 查看资产列表 | 仅可见本部门资产 |
| 跨部门访问控制 | 用户无跨部门权限 | 访问其他部门资产 | 访问被拒绝 |

### 7.4 资产操作流程测试

| 测试场景 | 前置条件 | 操作步骤 | 预期结果 |
|---------|---------|---------|---------|
| 创建调拨单 | 存在资产 | 选择资产、填写调入部门、保管人 | 调拨单创建成功，发起审批 |
| 审批调拨单 | 有待审批调拨单 | 审批通过/拒绝 | 调拨单状态更新，资产保管人变更 |
| 创建归还单 | 资产在借出状态 | 创建归还单 | 归还单创建成功 |
| 创建借用单 | 存在可用资产 | 创建借用单，填写借用期限 | 借用单创建成功，发起审批 |
| 创建领用单 | 存在可用资产 | 创建领用单 | 领用单创建成功，发起审批 |

---

## 8. 边界条件和异常场景测试

### 8.1 部门管理异常测试

#### 8.1.1 部门创建边界测试
```python
# tests/test_organizations/test_department_exceptions.py
import pytest
from django.core.exceptions import ValidationError
from apps.organizations.models import Department
from apps.accounts.models import User

def test_department_code_too_long():
    """测试部门编码过长"""
    with pytest.raises(ValidationError) as exc_info:
        Department.objects.create(
            organization_id=uuid4(),
            code="A" * 51,  # 超过50字符限制
            name="测试部门"
        )
    assert "code" in str(exc_info.value)

def test_department_code_duplicate():
    """测试部门编码重复"""
    org_id = uuid4()
    Department.objects.create(
        organization_id=org_id,
        code="DEPT001",
        name="测试部门1"
    )
    # 创建重复编码的部门
    dept2 = Department(
        organization_id=org_id,
        code="DEPT001",  # 重复编码
        name="测试部门2"
    )
    with pytest.raises(ValidationError):
        dept2.full_clean()

def test_department_circular_reference():
    """测试部门循环引用"""
    org_id = uuid4()
    # 创建部门A
    dept_a = Department.objects.create(
        organization_id=org_id,
        code="A",
        name="部门A"
    )
    # 创建部门B
    dept_b = Department.objects.create(
        organization_id=org_id,
        code="B",
        name="部门B",
        parent=dept_a
    )
    # 尝试将A设置为B的子部门（循环引用）
    dept_a.parent = dept_b
    with pytest.raises(ValidationError):
        dept_a.full_clean()

def test_department_path_generation():
    """测试部门路径自动生成"""
    org_id = uuid4()
    # 创建根部门
    root = Department.objects.create(
        organization_id=org_id,
        code="ROOT",
        name="根部门"
    )
    assert root.path == "/ROOT"
    assert root.level == 0

    # 创建子部门
    child = Department.objects.create(
        organization_id=org_id,
        code="CHILD",
        name="子部门",
        parent=root
    )
    assert child.path == "/ROOT/CHILD"
    assert child.level == 1
    assert child.full_path == "根部门/子部门"

def test_department_max_depth_exceeded():
    """测试部门层级深度超限"""
    org_id = uuid4()
    # 创建10层深度的部门树
    parent = None
    for i in range(15):  # 超过合理限制
        parent = Department.objects.create(
            organization_id=org_id,
            code=f"LEVEL{i}",
            name=f"第{i}层",
            parent=parent
        )
    # 应该有深度限制检查
    assert parent.level >= 10
```

#### 8.1.2 部门更新异常测试
```python
def test_department_update_with_children():
    """测试更新有子部门的部门"""
    org_id = uuid4()
    parent = Department.objects.create(
        organization_id=org_id,
        code="PARENT",
        name="父部门"
    )
    child = Department.objects.create(
        organization_id=org_id,
        code="CHILD",
        name="子部门",
        parent=parent
    )
    # 修改父部门编码，子部门路径应自动更新
    parent.code = "UPDATED_PARENT"
    parent.save()

    child.refresh_from_db()
    assert child.path.startswith("/UPDATED_PARENT")

def test_department_delete_with_children():
    """测试删除有子部门的部门"""
    org_id = uuid4()
    parent = Department.objects.create(
        organization_id=org_id,
        code="PARENT",
        name="父部门"
    )
    Department.objects.create(
        organization_id=org_id,
        code="CHILD",
        name="子部门",
        parent=parent
    )

    # 尝试删除父部门
    with pytest.raises(ValidationError):
        parent.delete()

def test_department_leader_not_in_same_org():
    """测试设置非本组织的部门负责人"""
    org1_id = uuid4()
    org2_id = uuid4()
    dept = Department.objects.create(
        organization_id=org1_id,
        code="DEPT",
        name="测试部门"
    )
    # 创建不同组织的用户
    user = User.objects.create_user(
        username="test_user",
        organization_id=org2_id  # 不同组织
    )

    # 尝试设置不同组织的用户为负责人
    dept.leader = user
    with pytest.raises(ValidationError):
        dept.full_clean()
```

### 8.2 用户部门关联异常测试

#### 8.2.1 用户部门边界测试
```python
# tests/test_organizations/test_user_department_exceptions.py
def test_user_department_duplicate_primary():
    """测试重复设置主部门"""
    org_id = uuid4()
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    dept1 = Department.objects.create(organization_id=org_id, code="D1", name="部门1")
    dept2 = Department.objects.create(organization_id=org_id, code="D2", name="部门2")

    # 创建两个部门关联
    ud1 = UserDepartment.objects.create(
        user=user,
        organization=org_id,
        department=dept1,
        is_primary=True
    )
    assert ud1.is_primary is True

    # 创建第二个关联并设为主部门
    ud2 = UserDepartment.objects.create(
        user=user,
        organization=org_id,
        department=dept2,
        is_primary=True
    )

    # 第一个关联应该自动取消主部门
    ud1.refresh_from_db()
    assert ud1.is_primary is False
    assert ud2.is_primary is True

def test_user_department_cross_org():
    """测试跨组织用户部门关联"""
    org1_id = uuid4()
    org2_id = uuid4()
    user = User.objects.create_user(username="test_user", organization_id=org1_id)
    dept = Department.objects.create(organization_id=org2_id, code="DEPT", name="部门")

    # 尝试关联不同组织的部门
    with pytest.raises(ValidationError):
        UserDepartment.objects.create(
            user=user,
            organization=org1_id,
            department=dept
        )

def test_user_department_max_count():
    """测试用户部门关联数量上限"""
    org_id = uuid4()
    user = User.objects.create_user(username="test_user", organization_id=org_id)

    # 创建超过合理数量的部门关联
    for i in range(20):  # 超过正常限制
        dept = Department.objects.create(organization_id=org_id, code=f"D{i}", name=f"部门{i}")
        UserDepartment.objects.create(
            user=user,
            organization=org_id,
            department=dept
        )

    # 检查是否有数量限制
    assert UserDepartment.objects.filter(user=user).count() == 20
```

#### 8.2.2 权限验证测试
```python
def test_department_permission_validation():
    """测试部门权限验证"""
    org_id = uuid4()
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")

    # 用户无部门权限时尝试查看子部门
    with pytest.raises(PermissionDenied):
        dept.get_descendant_ids()

def test_multi_primary_department_validation():
    """测试多主部门一致性验证"""
    org_id = uuid4()
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    dept1 = Department.objects.create(organization_id=org_id, code="D1", name="部门1")
    dept2 = Department.objects.create(organization_id=org_id, code="D2", name="部门2")

    # 同时创建两个主部门关联
    UserDepartment.objects.create(
        user=user,
        organization=org_id,
        department=dept1,
        is_primary=True
    )
    ud2 = UserDepartment.objects.create(
        user=user,
        organization=org_id,
        department=dept2,
        is_primary=True
    )

    # 验证只有一个主部门
    primary_count = UserDepartment.objects.filter(
        user=user,
        organization=org_id,
        is_primary=True
    ).count()
    assert primary_count == 1
```

### 8.3 资产操作异常测试

#### 8.3.1 调拨单异常测试
```python
# tests/test_assets/test_transfer_exceptions.py
from apps.assets.models.operations import AssetTransfer, AssetTransferItem

def test_transfer_same_department():
    """测试调拨到同一部门"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    asset = Asset.objects.create(
        organization_id=org_id,
        code="TEST001",
        name="测试资产",
        department=dept,
        custodian=user
    )

    # 尝试创建同部门调拨
    transfer = AssetTransfer(
        organization=org_id,
        transfer_code="T001",
        from_department=dept,
        to_department=dept,  # 同部门
        from_custodian=user,
        to_custodian=user,
        applicant=user,
        reason="测试调拨"
    )
    with pytest.raises(ValidationError):
        transfer.full_clean()

def test_transfer_nonexistent_asset():
    """调拨不存在的资产"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)

    # 创建调拨单
    transfer = AssetTransfer.objects.create(
        organization=org_id,
        transfer_code="T001",
        from_department=dept,
        to_department=dept,
        from_custodian=user,
        to_custodian=user,
        applicant=user,
        reason="测试调拨"
    )

    # 尝试添加不存在的资产明细
    item = AssetTransferItem(
        transfer=transfer,
        asset_id=uuid4(),  # 不存在的资产ID
        status_before="normal"
    )
    with pytest.raises(ValidationError):
        item.full_clean()

def test_transfer_status_transition():
    """测试调拨单状态流转"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)

    transfer = AssetTransfer.objects.create(
        organization=org_id,
        transfer_code="T001",
        from_department=dept,
        to_department=dept,
        from_custodian=user,
        to_custodian=user,
        applicant=user,
        reason="测试调拨"
    )

    # 验证状态流转
    assert transfer.status == "draft"

    # 从草稿直接到已完成（非法跳转）
    with pytest.raises(ValidationError):
        transfer.status = "completed"
        transfer.full_clean()

def test_concurrent_transfer_approval():
    """测试并发调拨审批"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="user1", organization_id=org_id)
    approver = User.objects.create_user(username="approver", organization_id=org_id)

    transfer = AssetTransfer.objects.create(
        organization=org_id,
        transfer_code="T001",
        from_department=dept,
        to_department=dept,
        from_custodian=user,
        to_custodian=user,
        applicant=user,
        status="pending",  # 待审批状态
        reason="测试调拨"
    )

    # 模拟并发审批
    import threading
    import time

    def approve_transfer():
        time.sleep(0.1)  # 模拟延迟
        transfer.status = "approved"
        transfer.approver = approver
        transfer.approved_at = timezone.now()
        transfer.save()

    # 启动两个审批线程
    thread1 = threading.Thread(target=approve_transfer)
    thread2 = threading.Thread(target=approve_transfer)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    # 只应该有一个审批成功
    transfer.refresh_from_db()
    assert transfer.status in ["approved", "rejected"]
```

#### 8.3.2 借用单异常测试
```python
def test_borrow_asset_unavailable():
    """测试借用不可用资产"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    asset = Asset.objects.create(
        organization_id=org_id,
        code="TEST001",
        name="测试资产",
        status="borrowed",  # 已借出状态
        department=dept,
        custodian=user
    )

    # 尝试借用已借出的资产
    borrow = AssetBorrow(
        organization=org_id,
        borrow_code="B001",
        asset=asset,
        borrower=user,
        borrower_department=dept,
        borrow_date=timezone.now().date(),
        expected_return_date=timezone.now().date() + timedelta(days=7),
        purpose="测试借用"
    )
    with pytest.raises(ValidationError):
        borrow.full_clean()

def test_borrow_date_validation():
    """测试借用日期验证"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    asset = Asset.objects.create(
        organization_id=org_id,
        code="TEST001",
        name="测试资产",
        status="available",
        department=dept,
        custodian=user
    )

    borrow = AssetBorrow(
        organization=org_id,
        borrow_code="B001",
        asset=asset,
        borrower=user,
        borrower_department=dept,
        borrow_date=timezone.now().date() + timedelta(days=1),  # 未来日期
        expected_return_date=timezone.now().date() - timedelta(days=1),  # 早于借用日期
        purpose="测试借用"
    )
    with pytest.raises(ValidationError):
        borrow.full_clean()

def test_borrow_overdue_handling():
    """测试借用逾期处理"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    asset = Asset.objects.create(
        organization_id=org_id,
        code="TEST001",
        name="测试资产",
        status="available",
        department=dept,
        custodian=user
    )

    borrow = AssetBorrow.objects.create(
        organization=org_id,
        borrow_code="B001",
        asset=asset,
        borrower=user,
        borrower_department=dept,
        borrow_date=timezone.now().date() - timedelta(days=10),  # 10天前借用
        expected_return_date=timezone.now().date() - timedelta(days=3),  # 3天前到期
        status="borrowed",
        purpose="测试借用"
    )

    # 模拟逾期检查
    from django.utils import timezone
    if timezone.now().date() > borrow.expected_return_date:
        borrow.status = "overdue"
        borrow.save()

    borrow.refresh_from_db()
    assert borrow.status == "overdue"
```

#### 8.3.3 归还单异常测试
```python
def test_return_nonexistent_asset():
    """测试归还不存在的资产"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)

    # 尝试创建不存在的资产的归还单
    return_obj = AssetReturn(
        organization=org_id,
        return_code="R001",
        asset_id=uuid4(),  # 不存在的资产
        returner=user,
        returner_department=dept
    )
    with pytest.raises(ValidationError):
        return_obj.full_clean()

def test_return_asset_not_borrowed():
    """测试归还未借出的资产"""
    org_id = uuid4()
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    asset = Asset.objects.create(
        organization_id=org_id,
        code="TEST001",
        name="测试资产",
        status="available",  # 可用状态，未借出
        department=dept,
        custodian=user
    )

    # 尝试归还未借出的资产
    return_obj = AssetReturn(
        organization=org_id,
        return_code="R001",
        asset=asset,
        returner=user,
        returner_department=dept,
        asset_status="normal"
    )
    with pytest.raises(ValidationError):
        return_obj.full_clean()
```

### 8.4 数据权限异常测试

#### 8.4.1 权限边界测试
```python
# tests/test_organizations/test_permission_exceptions.py
from apps.organizations.services.permission_service import OrgDataPermissionService

def test_permission_service_user_not_in_org():
    """测试用户不在组织中的权限服务"""
    org_id = uuid4()
    # 创建不在组织中的用户
    user = User.objects.create_user(
        username="external_user",
        organization_id=uuid4()  # 不同组织
    )

    # 应该返回空集合
    permission_service = OrgDataPermissionService(user)
    dept_ids = permission_service.get_viewable_department_ids()
    assert len(dept_ids) == 0

def test_permission_service_large_org_tree():
    """测试大型组织树的性能"""
    org_id = uuid4()
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    dept = Department.objects.create(organization_id=org_id, code="ROOT", name="根部门")

    # 创建深层级的组织树
    current_dept = dept
    for i in range(100):  # 100层深度
        child_dept = Department.objects.create(
            organization_id=org_id,
            code=f"LEVEL{i}",
            name=f"第{i}层",
            parent=current_dept
        )
        UserDepartment.objects.create(
            user=user,
            organization=org_id,
            department=child_dept,
            is_primary=False
        )
        current_dept = child_dept

    # 测试权限服务的性能
    permission_service = OrgDataPermissionService(user)
    dept_ids = permission_service.get_viewable_department_ids(recursive=True)

    # 应该包含所有后代部门
    assert len(dept_ids) == 101  # 包括根部门

def test_permission_cache_invalidation():
    """测试权限缓存失效"""
    org_id = uuid4()
    user = User.objects.create_user(username="test_user", organization_id=org_id)
    dept = Department.objects.create(organization_id=org_id, code="DEPT", name="测试部门")

    # 用户加入部门
    UserDepartment.objects.create(
        user=user,
        organization=org_id,
        department=dept,
        is_primary=True
    )

    # 获取权限（应该缓存）
    permission_service = OrgDataPermissionService(user)
    dept_ids_1 = permission_service.get_viewable_department_ids()

    # 修改用户部门关系
    UserDepartment.objects.filter(user=user, department=dept).delete()

    # 应该返回空集合（缓存失效）
    dept_ids_2 = permission_service.get_viewable_department_ids()
    assert len(dept_ids_2) == 0
```

### 8.5 API接口异常测试

#### 8.5.1 部门API异常测试
```python
# tests/test_organizations/test_api_exceptions.py
from rest_framework.test import APITestCase
from rest_framework import status

class DepartmentAPIExceptionsTest(APITestCase):
    def setUp(self):
        self.org_id = uuid4()
        self.user = User.objects.create_user(
            username="test_user",
            organization_id=self.org_id,
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_create_department_missing_fields(self):
        """测试创建部门缺少必填字段"""
        url = "/api/organizations/departments/"
        data = {}  # 缺少所有必填字段

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)
        self.assertIn("name", response.data)

    def test_create_department_duplicate_code(self):
        """测试创建重复编码的部门"""
        Department.objects.create(
            organization_id=self.org_id,
            code="DUPLICATE",
            name="测试部门"
        )

        url = "/api/organizations/departments/"
        data = {
            "code": "DUPLICATE",  # 重复编码
            "name": "重复部门"
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_department_tree_large_dataset(self):
        """测试大型部门树数据"""
        # 创建1000个部门的测试数据
        dept = Department.objects.create(
            organization_id=self.org_id,
            code="ROOT",
            name="根部门"
        )

        current_dept = dept
        for i in range(1000):
            child_dept = Department.objects.create(
                organization_id=self.org_id,
                code=f"DEPT{i}",
                name=f"部门{i}",
                parent=current_dept
            )
            current_dept = child_dept

        url = "/api/organizations/departments/tree/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 验证返回的数据结构
        self.assertIn("tree", response.data)

    def test_update_department_circular_reference(self):
        """测试更新部门导致循环引用"""
        dept1 = Department.objects.create(
            organization_id=self.org_id,
            code="DEPT1",
            name="部门1"
        )
        dept2 = Department.objects.create(
            organization_id=self.org_id,
            code="DEPT2",
            name="部门2",
            parent=dept1
        )

        url = f"/api/organizations/departments/{dept2.id}/"
        data = {
            "name": "修改名称",
            "parent": str(dept1.id)  # 设置dept1为父部门（循环引用）
        }

        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

#### 8.5.2 资产操作API异常测试
```python
class AssetOperationAPIExceptionsTest(APITestCase):
    def setUp(self):
        self.org_id = uuid4()
        self.user = User.objects.create_user(
            username="test_user",
            organization_id=self.org_id
        )
        self.dept = Department.objects.create(
            organization_id=self.org_id,
            code="DEPT",
            name="测试部门"
        )
        self.asset = Asset.objects.create(
            organization_id=self.org_id,
            code="TEST001",
            name="测试资产",
            department=self.dept,
            custodian=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_transfer_missing_fields(self):
        """测试创建调拨单缺少必填字段"""
        url = "/api/assets/transfers/"
        data = {}  # 缺少所有必填字段

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("transfer_code", response.data)
        self.assertIn("from_department", response.data)

    def test_transfer_permission_denied(self):
        """测试无权限用户的调拨操作"""
        # 创建无权限用户
        other_user = User.objects.create_user(
            username="other_user",
            organization_id=self.org_id
        )

        self.client.force_authenticate(user=other_user)

        url = "/api/assets/transfers/"
        data = {
            "transfer_code": "T001",
            "from_department": str(self.dept.id),
            "to_department": str(self.dept.id),
            "from_custodian": str(self.user.id),
            "to_custodian": str(self.user.id),
            "applicant": str(self.user.id),
            "reason": "测试调拨"
        }

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_batch_operation_limit(self):
        """测试批量操作数量限制"""
        # 创建大量资产ID
        asset_ids = []
        for i in range(101):  # 超过100个限制
            asset = Asset.objects.create(
                organization_id=self.org_id,
                code=f"TEST{i}",
                name=f"测试资产{i}",
                department=self.dept,
                custodian=self.user
            )
            asset_ids.append(str(asset.id))

        url = "/api/assets/transfers/batch-delete/"
        data = {"ids": asset_ids}

        response = self.client.post(url, data, format="json")
        # 应该有数量限制检查
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
```

### 8.6 性能压力测试

#### 8.6.1 大规模数据处理测试
```python
# tests/test_organizations/test_performance.py
import time
from django.test import TestCase

class LargeScaleDataTest(TestCase):
    def setUp(self):
        self.org_id = uuid4()
        # 预测试数据
        self.departments = []
        self.users = []

    def test_large_department_tree_creation(self):
        """测试大规模部门树创建性能"""
        start_time = time.time()

        # 创建10,000个部门的组织树
        dept = Department.objects.create(
            organization_id=self.org_id,
            code="ROOT",
            name="根部门"
        )
        self.departments.append(dept)

        current_dept = dept
        for i in range(10000):
            child_dept = Department.objects.create(
                organization_id=self.org_id,
                code=f"DEPT{i}",
                name=f"部门{i}",
                parent=current_dept
            )
            self.departments.append(child_dept)
            current_dept = child_dept

            if i % 1000 == 0:
                print(f"已创建 {i+1} 个部门")

        creation_time = time.time() - start_time
        print(f"创建10,000个部门耗时: {creation_time:.2f}秒")

        # 验证路径生成
        last_dept = self.departments[-1]
        assert last_dept.level == 10000
        assert len(last_dept.path) > 100

    def test_large_user_department_mapping(self):
        """测试大规模用户部门关联性能"""
        # 创建1000个用户和100个部门
        users = []
        for i in range(1000):
            user = User.objects.create_user(
                username=f"user{i}",
                organization_id=self.org_id
            )
            users.append(user)

        departments = []
        for i in range(100):
            dept = Department.objects.create(
                organization_id=self.org_id,
                code=f"DEPT{i}",
                name=f"部门{i}"
            )
            departments.append(dept)

        # 每个用户关联5个部门
        start_time = time.time()
        for user in users:
            for i in range(5):
                UserDepartment.objects.create(
                    user=user,
                    organization=self.org_id,
                    department=departments[i % len(departments)],
                    is_primary=(i == 0)
                )

        mapping_time = time.time() - start_time
        print(f"创建{len(users)*5}个用户部门关联耗时: {mapping_time:.2f}秒")

        # 测试权限查询性能
        permission_service = OrgDataPermissionService(users[0])
        query_start = time.time()
        dept_ids = permission_service.get_viewable_department_ids(recursive=True)
        query_time = time.time() - query_start

        print(f"权限查询耗时: {query_time:.4f}秒")
        assert query_time < 1.0  # 查询应该在1秒内完成
```

---

## 10. 测试用例

1. 实现权限继承逻辑
2. 扩展钉钉、飞书适配器
3. 迁移现有代码到公共基类
4. 性能优化（权限缓存）
5. 与工作流模块集成
6. 前端权限管理界面

---

## 12. API 规范

### 12.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "DEPT001",
        "name": "技术部",
        "parent": "550e8400-e29b-41d4-a716-446655440000",
        "parent_name": "总部",
        "level": 1,
        "path": "/HQ/TECH",
        "full_path": "总部/技术部",
        "full_path_name": "总部/技术部",
        "leader": "550e8400-e29b-41d4-a716-446655440000",
        "leader_name": "张三",
        "is_active": true,
        "order": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:35:00Z",
        "created_by": "550e8400-e29b-41d4-a716-446655440000",
        "organization": "550e8400-e29b-41d4-a716-446655440000"
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/organizations/departments/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "DEPT001",
                "name": "技术部",
                "level": 1,
                "full_path_name": "总部/技术部",
                "leader_name": "张三",
                "is_active": true,
                "created_at": "2024-01-15T10:30:00Z"
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
            "code": ["该字段不能为空"],
            "name": ["该字段不能为空"]
        }
    }
}
```

### 12.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **部门列表** | GET | `/api/organizations/departments/` | 分页查询部门，支持过滤和搜索 |
| **部门详情** | GET | `/api/organizations/departments/{id}/` | 获取单个部门详情信息 |
| **创建部门** | POST | `/api/organizations/departments/` | 创建新的部门 |
| **更新部门** | PUT | `/api/organizations/departments/{id}/` | 完整更新部门信息 |
| **部分更新部门** | PATCH | `/api/organizations/departments/{id}/` | 部分更新部门信息 |
| **软删除部门** | DELETE | `/api/organizations/departments/{id}/` | 软删除部门 |
| **部门列表（已删除）** | GET | `/api/organizations/departments/deleted/` | 查看已删除的部门 |
| **恢复部门** | POST | `/api/organizations/departments/{id}/restore/` | 恢复已删除的部门 |

### 12.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量软删除部门** | POST | `/api/organizations/departments/batch-delete/` | 批量软删除部门 |
| **批量恢复部门** | POST | `/api/organizations/departments/batch-restore/` | 批量恢复部门 |
| **批量更新部门** | POST | `/api/organizations/departments/batch-update/` | 批量更新部门信息 |

#### 批量删除请求示例
```http
POST /api/organizations/departments/batch-delete/
{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

### 12.4 用户部门关联管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **用户部门关联列表** | GET | `/api/organizations/user-departments/` | 分页查询用户部门关联 |
| **用户部门关联详情** | GET | `/api/organizations/user-departments/{id}/` | 获取单个用户部门关联详情 |
| **创建用户部门关联** | POST | `/api/organizations/user-departments/` | 创建用户部门关联 |
| **更新用户部门关联** | PUT | `/api/organizations/user-departments/{id}/` | 完整更新用户部门关联 |
| **部分更新用户部门关联** | PATCH | `/api/organizations/user-departments/{id}/` | 部分更新用户部门关联 |
| **软删除用户部门关联** | DELETE | `/api/organizations/user-departments/{id}/` | 软删除用户部门关联 |
| **设置主部门** | POST | `/api/organizations/users/{user_id}/set-primary-department/` | 设置用户主部门 |

#### 设置主部门请求示例
```http
POST /api/organizations/users/550e8400-e29b-41d4-a716-446655440000/set-primary-department/
Content-Type: application/json

{
    "department_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### 12.5 部门树形结构接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **部门树结构** | GET | `/api/organizations/departments/tree/` | 获取完整部门树结构 |
| **子部门列表** | GET | `/api/organizations/departments/{id}/children/` | 获取指定部门的子部门 |
| **部门用户列表** | GET | `/api/organizations/departments/{id}/users/` | 获取指定部门的用户列表 |

#### 部门树响应示例
```json
{
    "success": true,
    "data": {
        "tree": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "HQ",
                "name": "总部",
                "level": 0,
                "full_path_name": "总部",
                "leader_name": "李四",
                "is_active": true,
                "children": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "code": "TECH",
                        "name": "技术部",
                        "level": 1,
                        "full_path_name": "总部/技术部",
                        "leader_name": "张三",
                        "is_active": true,
                        "children": []
                    }
                ]
            }
        ]
    }
}
```

### 12.6 数据权限查询接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **用户权限信息** | GET | `/api/organizations/my-permissions/` | 获取当前用户权限信息 |
| **可查看部门列表** | GET | `/api/organizations/viewable-departments/` | 获取用户可查看的部门列表 |
| **可查看用户列表** | GET | `/api/organizations/viewable-users/` | 获取用户可查看的用户列表 |

#### 用户权限响应示例
```json
{
    "success": true,
    "data": {
        "permissions": [
            "organizations.view_department",
            "organizations.add_department",
            "assets.create_transfer"
        ],
        "viewable_department_ids": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
        "viewable_user_ids": ["550e8400-e29b-41d4-a716-446655440000", "550e8400-e29b-41d4-a716-446655440001"],
        "data_scope": "department"  // 数据范围: all/all_department/department/self
    }
}
```

### 12.7 资产操作流程接口

#### 12.7.1 资产调拨接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **创建调拨单** | POST | `/api/assets/transfers/` | 创建资产调拨单 |
| **审批调拨单** | POST | `/api/assets/transfers/{id}/approve/` | 审批调拨单 |
| **获取调拨单列表** | GET | `/api/assets/transfers/` | 分页查询调拨单 |
| **获取调拨单详情** | GET | `/api/assets/transfers/{id}/` | 获取调拨单详情 |
| **更新调拨单** | PUT/PATCH | `/api/assets/transfers/{id}/` | 更新调拨单 |
| **软删除调拨单** | DELETE | `/api/assets/transfers/{id}/` | 软删除调拨单 |

#### 创建调拨单请求示例
```http
POST /api/assets/transfers/
Content-Type: application/json

{
    "transfer_code": "TRF20240115001",
    "from_department": "550e8400-e29b-41d4-a716-446655440000",
    "from_custodian": "550e8400-e29b-41d4-a716-446655440001",
    "from_location": "550e8400-e29b-41d4-a716-446655440002",
    "to_department": "550e8400-e29b-41d4-a716-446655440001",
    "to_custodian": "550e8400-e29b-41d4-a716-446655440003",
    "to_location": "550e8400-e29b-41d4-a716-446655440004",
    "applicant": "550e8400-e29b-41d4-a716-446655440001",
    "reason": "部门调动需要",
    "remark": "2024年1月调拨"
}
```

#### 12.7.2 资产归还接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **创建归还单** | POST | `/api/assets/returns/` | 创建资产归还单 |
| **获取归还单列表** | GET | `/api/assets/returns/` | 分页查询归还单 |
| **获取归还单详情** | GET | `/api/assets/returns/{id}/` | 获取归还单详情 |
| **确认归还** | POST | `/api/assets/returns/{id}/confirm/` | 确认资产归还 |
| **拒绝归还** | POST | `/api/assets/returns/{id}/reject/` | 拒绝资产归还 |

#### 12.7.3 资产借用接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **创建借用单** | POST | `/api/assets/borrows/` | 创建资产借用单 |
| **审批借用单** | POST | `/api/assets/borrows/{id}/approve/` | 审批借用单 |
| **获取借用单列表** | GET | `/api/assets/borrows/` | 分页查询借用单 |
| **归还借用资产** | POST | `/api/assets/borrows/{id}/return/` | 归还借用资产 |

#### 12.7.4 资产领用接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **创建领用单** | POST | `/api/assets/uses/` | 创建资产领用单 |
| **审批领用单** | POST | `/api/assets/uses/{id}/approve/` | 审批领用单 |
| **获取领用单列表** | GET | `/api/assets/uses/` | 分页查询领用单 |

### 12.8 资产操作明细接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **调拨明细列表** | GET | `/api/assets/transfers/{transfer_id}/items/` | 获取调拨单明细列表 |
| **确认调拨明细** | POST | `/api/assets/transfers/items/{id}/confirm/` | 确认调拨明细接收 |
| **调拨明细详情** | GET | `/api/assets/transfers/items/{id}/` | 获取调拨明细详情 |

### 12.9 标准错误码

| 错误码 | HTTP状态 | 描述 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未认证访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不被允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |
| `DEPARTMENT_NOT_FOUND` | 404 | 部门不存在 |
| `USER_NOT_IN_DEPARTMENT` | 400 | 用户不在指定部门 |
| `CIRCULAR_REFERENCE` | 400 | 循环引用错误 |
| `ASSET_UNAVAILABLE` | 400 | 资产不可用 |
| `TRANSFER_SAME_DEPARTMENT` | 400 | 调拨到同一部门 |
| `INVALID_STATUS_TRANSITION` | 400 | 无效的状态流转 |

### 12.10 扩展接口示例

#### 12.10.1 部门路径计算示例
```python
# 客端端获取部门完整路径的示例
import requests

# 获取部门树
response = requests.get('/api/organizations/departments/tree/',
                       headers={'Authorization': 'Bearer token'})

# 递归查找部门路径
def find_department_path(tree, target_id, current_path=[]):
    for dept in tree:
        if dept['id'] == target_id:
            return current_path + [dept]
        if dept['children']:
            result = find_department_path(dept['children'], target_id, current_path + [dept])
            if result:
                return result
    return None

target_dept_id = '550e8400-e29b-41d4-a716-446655440001'
path = find_department_path(response.data['tree'], target_dept_id)

print("部门完整路径:", [d['name'] for d in path])
```

#### 12.10.2 批量用户部门关联示例
```python
# 批量设置用户部门的示例
import requests

# 为用户批量添加部门关联
user_id = '550e8400-e29b-41d4-a716-446655440000'
departments = [
    '550e8400-e29b-41d4-a716-446655440001',  # 技术部
    '550e8400-e29b-41d4-a716-446655440002'   # 产品部
]

data = {
    "user_id": user_id,
    "departments": departments,
    "positions": ["工程师", "产品经理"],
    "is_primary": True  # 第一个部门为主部门
}

response = requests.post('/api/organizations/users/batch-set-departments/',
                        json=data,
                        headers={'Authorization': 'Bearer token'})

result = response.json()
print(f"成功设置 {result['data']['success_count']} 个部门关联")
```

#### 12.10.3 资产调拨流程示例
```python
# 完整的资产调拨流程示例
import requests
import time

# 1. 创建调拨单
transfer_data = {
    "transfer_code": f"TRF{int(time.time())}",
    "from_department": "550e8400-e29b-41d4-a716-446655440000",
    "from_custodian": "550e8400-e29b-41d4-a716-446655440001",
    "to_department": "550e8400-e29b-41d4-a716-446655440001",
    "to_custodian": "550e8400-e29b-41d4-a716-446655440003",
    "applicant": "550e8400-e29b-41d4-a716-446655440001",
    "reason": "部门调动需要"
}

response = requests.post('/api/assets/transfers/',
                        json=transfer_data,
                        headers={'Authorization': 'Bearer token'})

transfer = response.json()['data']
transfer_id = transfer['id']

# 2. 添加调拨明细
assets_to_transfer = ["ASSET001", "ASSET002", "ASSET003"]
for asset_code in assets_to_transfer:
    item_data = {
        "transfer": transfer_id,
        "asset": asset_code,
        "status_before": "normal"
    }
    requests.post('/api/assets/transfers/items/',
                 json=item_data,
                 headers={'Authorization': 'Bearer token'})

# 3. 审批发起
approval_data = {
    "status": "approved",
    "approval_comment": "同意调拨"
}

response = requests.post(f'/api/assets/transfers/{transfer_id}/approve/',
                        json=approval_data,
                        headers={'Authorization': 'Bearer token'})

print("调拨流程完成，状态:", response.json()['data']['status'])
```

#### 12.10.4 数据权限验证示例
```python
# 验证数据权限的示例
import requests

# 获取当前用户权限
response = requests.get('/api/organizations/my-permissions/',
                       headers={'Authorization': 'Bearer token'})

permissions = response.json()['data']

# 检查是否有资产查看权限
if 'assets.view_asset' in permissions['permissions']:
    print("用户有资产查看权限")

    # 获取可查看的资产
    viewable_assets = requests.get('/api/assets/my-viewable-assets/',
                                  headers={'Authorization': 'Bearer token'})
    print(f"可查看资产数量: {len(viewable_assets.json()['data']['results'])}")
else:
    print("用户无资产查看权限")

# 检查数据范围
data_scope = permissions['data_scope']
if data_scope == 'all':
    print("用户可查看所有数据")
elif data_scope == 'department':
    print(f"用户可查看本部门数据，部门ID: {permissions['viewable_department_ids']}")
elif data_scope == 'self':
    print("用户只能查看自己的数据")
```

### 12.11 权限和安全

#### 12.11.1 权限要求
- 所有组织架构API需要认证
- 部门管理需要 `organizations.view_department` 权限
- 部门创建/编辑需要 `organizations.add_department` / `organizations.change_department` 权限
- 资产操作需要相应的资产操作权限
- 数据权限自动根据用户角色和部门关系过滤

#### 12.11.2 安全措施
- 敏感操作需要二次验证
- 部门编码唯一性验证
- 防止循环引用和路径冲突
- 操作日志记录到审计表
- 实现操作频率限制

#### 12.11.3 速率限制
- 部门创建：每小时最多50次
- 用户部门关联：每小时最多100次
- 资产调拨：每小时最多20次
- 权限查询：每秒最多10次

### 12.12 WebSocket实时通知

#### 12.12.1 部门变更通知
```javascript
// 部门变更WebSocket连接
const socket = new WebSocket('wss://api.example.com/ws/organizations/');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);

    if (data.type === 'department_changed') {
        // 部门信息变更通知
        console.log('部门变更:', data.department);
        updateDepartmentTree();
    }

    if (data.type === 'user_department_changed') {
        // 用户部门变更通知
        console.log('用户部门变更:', data.user_department);
        updateUserDepartmentList();
    }
};

// 发送已读确认
function markNotificationAsRead(notificationId) {
    socket.send(JSON.stringify({
        type: 'mark_read',
        notification_id: notificationId
    }));
}
```

#### 12.12.2 推送消息格式
```json
{
    "type": "department_changed",
    "department": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "技术部",
        "code": "TECH",
        "action": "updated",  // created/updated/deleted
        "changed_fields": ["name", "leader"],
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

---

**版本**: 1.0.0
**更新日期**: 2026-01-15
**维护人**: GZEAMS 开发团队
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