# Phase 1.2: Organizations 独立模块 - 后端实现

## 公共模型引用

> 本模块所有后端组件必须继承以下公共基类

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法 |

### 自动获得功能说明

#### BaseModel 自动字段
- `organization`: 组织外键 (自动设置)
- `is_deleted`: 软删除标记
- `deleted_at`: 删除时间
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `created_by`: 创建人 (自动设置)
- `custom_fields`: 动态字段 (JSONB)

#### BaseModelViewSet 自动端点
- 标准 CRUD: GET/POST/PUT/PATCH/DELETE
- 软删除: DELETE 软删除, GET /deleted/, POST /{id}/restore/
- 批量操作: POST /batch-delete/, /batch-restore/, /batch-update/

---

## 概述

将组织和部门相关功能从 accounts 模块独立出来，创建专门的 organizations 模块，支持多组织架构、部门树形结构、一人多部门等核心功能。

---

## 模块结构

```
backend/apps/organizations/
├── __init__.py
├── apps.py                      # Django App 配置
├── models.py                    # 数据模型
├── admin.py                     # Admin 后台配置
├── serializers.py               # DRF 序列化器
├── views.py                     # API 视图
├── urls.py                      # URL 路由
├── permissions.py               # 权限控制
├── services/                    # 业务服务层
│   ├── __init__.py
│   ├── organization_service.py  # 组织服务
│   ├── department_service.py    # 部门服务
│   └── permission_service.py    # 数据权限服务
├── migrations/                  # 数据库迁移
│   ├── 0001_initial.py
│   └── ...
└── tests/                       # 单元测试
    ├── __init__.py
    ├── test_models.py
    ├── test_services.py
    └── test_api.py
```

---

## 数据模型

### 1. Organization 模型（组织/公司）

```python
# apps/organizations/models.py

from django.db import models
from apps.common.models import BaseModel


class Organization(BaseModel):
    """组织/公司模型

    支持多层级组织结构（集团 > 公司 > 分公司）
    """

    class Meta:
        db_table = 'organizations'
        verbose_name = '组织'
        verbose_name_plural = '组织'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
        ]

    # 基础信息
    name = models.CharField(
        max_length=200,
        verbose_name='组织名称'
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='组织编码'
    )

    # 层级关系
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级组织'
    )

    level = models.IntegerField(
        default=0,
        verbose_name='层级'
    )

    path = models.CharField(
        max_length=500,
        default='',
        verbose_name='路径'
    )

    # 组织类型
    class OrganizationType(models.TextChoices):
        GROUP = 'group', '集团'
        COMPANY = 'company', '公司'
        BRANCH = 'branch', '分公司'
        DEPARTMENT = 'department', '部门级组织'

    org_type = models.CharField(
        max_length=20,
        choices=OrganizationType.choices,
        default=OrganizationType.COMPANY,
        verbose_name='组织类型'
    )

    # 联系信息
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='联系人'
    )

    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='联系电话'
    )

    email = models.EmailField(
        blank=True,
        verbose_name='邮箱'
    )

    address = models.TextField(
        blank=True,
        verbose_name='地址'
    )

    # 统一社会信用代码（用于财务集成）
    credit_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='统一社会信用代码'
    )

    # 状态
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    # 配置
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='组织配置',
        help_text='存储组织级别的配置项'
    )

    # 邀请码（用于用户加入组织）
    invite_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name='邀请码'
    )

    invite_code_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='邀请码过期时间'
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 更新层级
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path}/{self.code}"
        else:
            self.level = 0
            self.path = f"/{self.code}"

        super().save(*args, **kwargs)

        # 递归更新子组织
        self._update_children_paths()

    def _update_children_paths(self):
        """更新子组织的路径"""
        for child in self.children.all():
            child.save(update_fields=['level', 'path'])

    def get_all_children(self):
        """获取所有子组织（递归）"""
        children = []
        for child in self.children.filter(is_active=True):
            children.append(child)
            children.extend(child.get_all_children())
        return children

    def get_all_parent_ids(self):
        """获取所有上级组织ID"""
        ids = []
        if self.parent:
            ids.append(self.parent.id)
            ids.extend(self.parent.get_all_parent_ids())
        return ids

    def regenerate_invite_code(self):
        """重新生成邀请码"""
        import random
        import string
        from django.utils import timezone

        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        # 确保唯一
        while Organization.objects.filter(invite_code=code).exists():
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        self.invite_code = code
        self.invite_code_expires_at = timezone.now() + timezone.timedelta(days=30)
        self.save(update_fields=['invite_code', 'invite_code_expires_at'])

        return code

    @property
    def full_name(self):
        """获取完整名称（包含上级组织）"""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name
```

### 2. Department 模型（部门）

```python
class Department(BaseModel):
    """部门模型

    支持树形结构、完整路径显示、一人多部门
    """

    class Meta:
        db_table = 'departments'
        verbose_name = '部门'
        verbose_name_plural = '部门'
        unique_together = [['organization', 'code']]
        indexes = [
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'level']),
            models.Index(fields=['organization', 'wework_dept_id']),
            models.Index(fields=['organization', 'dingtalk_dept_id']),
            models.Index(fields=['organization', 'feishu_dept_id']),
        ]

    # 所属组织
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='departments',
        verbose_name='所属组织'
    )

    # 基础信息
    code = models.CharField(
        max_length=50,
        verbose_name='部门编码'
    )

    name = models.CharField(
        max_length=100,
        verbose_name='部门名称'
    )

    # 层级关系
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级部门'
    )

    level = models.IntegerField(
        default=0,
        verbose_name='层级'
    )

    path = models.CharField(
        max_length=500,
        default='',
        verbose_name='路径'
    )

    order = models.IntegerField(
        default=0,
        verbose_name='排序'
    )

    # 完整路径显示（如：总部/技术部/后端组）
    full_path = models.CharField(
        max_length=500,
        default='',
        verbose_name='完整路径',
        help_text='从根部门到当前部门的完整路径，用/分隔'
    )

    full_path_name = models.CharField(
        max_length=1000,
        default='',
        verbose_name='完整路径名称',
        help_text='从根部门到当前部门的完整名称路径，用/分隔'
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

    # 第三方平台同步字段
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

    # 状态
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    def __str__(self):
        return self.full_path_name or self.name

    def save(self, *args, **kwargs):
        # 更新层级
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0

        # 更新路径
        self.path = f"{self.parent.path}/{self.code}" if self.parent else f"/{self.code}"

        # 更新完整路径名称
        self.full_path_name = (
            f"{self.parent.full_path_name}/{self.name}" if self.parent else self.name
        )

        # 更新 full_path
        if self.parent:
            self.full_path = self.parent.full_path + '/' + self.name
        else:
            self.full_path = self.name

        super().save(*args, **kwargs)

        # 递归更新子部门的路径
        self._update_children_paths()

    def _update_children_paths(self):
        """更新子部门的路径"""
        for child in self.children.all():
            child.save(update_fields=['level', 'path', 'full_path', 'full_path_name'])

    def get_all_children(self):
        """获取所有子部门（递归）"""
        children = []
        for child in self.children.filter(is_active=True):
            children.append(child)
            children.extend(child.get_all_children())
        return children

    def get_all_parent_ids(self):
        """获取所有上级部门ID"""
        ids = []
        if self.parent:
            ids.append(self.parent.id)
            ids.extend(self.parent.get_all_parent_ids())
        return ids

    def get_descendant_ids(self):
        """获取所有后代部门ID"""
        ids = [self.id]
        for child in self.children.filter(is_active=True):
            ids.extend(child.get_descendant_ids())
        return ids

    @classmethod
    def get_full_tree(cls, organization):
        """获取组织的完整部门树"""
        roots = cls.objects.filter(
            organization=organization,
            parent__isnull=True,
            is_active=True
        ).order_by('order')

        def build_tree(dept):
            return {
                'id': str(dept.id),
                'code': dept.code,
                'name': dept.name,
                'full_path': dept.full_path,
                'full_path_name': dept.full_path_name,
                'level': dept.level,
                'leader_id': str(dept.leader_id) if dept.leader_id else None,
                'leader_name': dept.leader.get_full_name() if dept.leader else None,
                'is_active': dept.is_active,
                'children': [build_tree(child) for child in dept.children.filter(is_active=True).order_by('order')]
            }

        return [build_tree(root) for root in roots]
```

### 3. UserOrganization 模型（用户-组织关联）

```python
class UserOrganization(BaseModel):
    """用户-组织关联表

    支持一个用户加入多个组织，每个组织可以有不同角色
    """

    class Meta:
        db_table = 'user_organizations'
        verbose_name = '用户组织关联'
        verbose_name_plural = '用户组织关联'
        unique_together = [['user', 'organization']]
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['organization', 'is_active']),
        ]

    class Role(models.TextChoices):
        ADMIN = 'admin', '管理员'
        MEMBER = 'member', '普通成员'
        AUDITOR = 'auditor', '审计员'

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='user_organizations',
        verbose_name='用户'
    )

    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='user_organizations',
        verbose_name='组织'
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name='角色'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='是否激活'
    )

    # 是否为当前默认组织
    is_primary = models.BooleanField(
        default=False,
        verbose_name='是否为默认组织'
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='加入时间'
    )

    invited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_user_organizations',
        verbose_name='邀请人'
    )

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.organization.name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # 确保用户只有一个默认组织
        if self.is_primary:
            UserOrganization.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
```

### 4. UserDepartment 模型（用户-部门关联）

```python
class UserDepartment(BaseModel):
    """用户部门关联表

    支持一人多部门、主部门设置
    """

    class Meta:
        db_table = 'user_departments'
        verbose_name = '用户部门关联'
        verbose_name_plural = '用户部门关联'
        unique_together = [['user', 'organization', 'department']]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['department']),
            models.Index(fields=['is_primary']),
        ]

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='user_departments',
        verbose_name='用户'
    )

    organization = models.ForeignKey(
        'Organization',
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
        verbose_name='是否主部门',
        help_text='主部门作为用户的默认资产归属部门'
    )

    # 是否为资产部门（用于资产管理和盘点）
    is_asset_department = models.BooleanField(
        default=True,
        verbose_name='是否资产部门',
        help_text='该部门是否用于资产管理和盘点'
    )

    # 在部门中的职位
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

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department.full_path_name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # 确保每个用户在同一组织只有一个主部门
        if self.is_primary:
            UserDepartment.objects.filter(
                user=self.user,
                organization=self.organization,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
```

---

## 服务层设计

### OrganizationService

```python
# apps/organizations/services/organization_service.py

from typing import Optional, List
from django.db import transaction
from apps.organizations.models import Organization, UserOrganization


class OrganizationService:
    """组织服务"""

    @staticmethod
    def create_organization(name: str, code: str, creator, **kwargs) -> Organization:
        """创建组织"""
        org = Organization.objects.create(
            name=name,
            code=code,
            **kwargs
        )

        # 创建者自动成为管理员
        UserOrganization.objects.create(
            user=creator,
            organization=org,
            role=UserOrganization.Role.ADMIN,
            is_primary=True
        )

        # 生成邀请码
        org.regenerate_invite_code()

        return org

    @staticmethod
    @transaction.atomic
    def add_member(organization: Organization, user, role: str = UserOrganization.Role.MEMBER):
        """添加组织成员"""
        user_org, created = UserOrganization.objects.get_or_create(
            user=user,
            organization=organization,
            defaults={'role': role, 'is_active': True}
        )

        if not created and not user_org.is_active:
            user_org.is_active = True
            user_org.role = role
            user_org.save()

        return user_org

    @staticmethod
    @transaction.atomic
    def remove_member(organization: Organization, user):
        """移除组织成员（软删除）"""
        user_org = UserOrganization.objects.get(
            user=user,
            organization=organization
        )
        user_org.is_active = False
        user_org.save()

    @staticmethod
    def get_user_organizations(user) -> List[dict]:
        """获取用户加入的组织列表"""
        user_orgs = UserOrganization.objects.filter(
            user=user,
            is_active=True
        ).select_related('organization')

        return [
            {
                'id': str(uo.organization.id),
                'name': uo.organization.name,
                'code': uo.organization.code,
                'role': uo.role,
                'is_primary': uo.is_primary,
                'joined_at': uo.joined_at.isoformat(),
            }
            for uo in user_orgs
        ]

    @staticmethod
    def switch_organization(user, organization_id) -> bool:
        """切换用户当前组织"""
        try:
            user_org = UserOrganization.objects.get(
                user=user,
                organization_id=organization_id,
                is_active=True
            )

            # 设置为默认组织
            UserOrganization.objects.filter(
                user=user
            ).update(is_primary=False)

            user_org.is_primary = True
            user_org.save()

            # 更新用户的当前组织（如果 User 模型有该字段）
            # user.current_organization_id = organization_id
            # user.save(update_fields=['current_organization'])

            return True
        except UserOrganization.DoesNotExist:
            return False

    @staticmethod
    def validate_invite_code(invite_code: str) -> Optional[Organization]:
        """验证邀请码"""
        from django.utils import timezone

        try:
            org = Organization.objects.get(
                invite_code=invite_code,
                is_active=True
            )

            if org.invite_code_expires_at and org.invite_code_expires_at < timezone.now():
                return None

            return org
        except Organization.DoesNotExist:
            return None
```

### DepartmentService

```python
# apps/organizations/services/department_service.py

from typing import List, Dict
from apps.organizations.models import Department, UserDepartment


class DepartmentService:
    """部门服务"""

    @staticmethod
    def create_department(organization, name: str, code: str, parent=None, **kwargs) -> Department:
        """创建部门"""
        department = Department.objects.create(
            organization=organization,
            name=name,
            code=code,
            parent=parent,
            **kwargs
        )
        return department

    @staticmethod
    def get_department_tree(organization, include_inactive: bool = False) -> List[dict]:
        """获取部门树"""
        return Department.get_full_tree(organization)

    @staticmethod
    @transaction.atomic
    def add_user_to_department(user, department, organization,
                              is_primary: bool = False,
                              position: str = '') -> UserDepartment:
        """添加用户到部门"""
        user_dept, created = UserDepartment.objects.get_or_create(
            user=user,
            organization=organization,
            department=department,
            defaults={
                'is_primary': is_primary,
                'position': position
            }
        )

        if not created and is_primary:
            # 更新为主部门
            UserDepartment.objects.filter(
                user=user,
                organization=organization
            ).update(is_primary=False)
            user_dept.is_primary = is_primary
            user_dept.save()

        return user_dept

    @staticmethod
    def get_department_members(department: Department) -> List[dict]:
        """获取部门成员"""
        user_depts = UserDepartment.objects.filter(
            department=department
        ).select_related('user')

        return [
            {
                'user_id': str(ud.user.id),
                'name': ud.user.get_full_name(),
                'position': ud.position,
                'is_leader': ud.is_leader,
                'is_primary': ud.is_primary,
            }
            for ud in user_depts
        ]

    @staticmethod
    @transaction.atomic
    def set_department_leader(department: Department, leader) -> Department:
        """设置部门负责人"""
        department.leader = leader
        department.save(update_fields=['leader'])

        # 更新用户部门关联
        UserDepartment.objects.filter(
            user=leader,
            department=department
        ).update(is_leader=True)

        return department
```

---

## 权限控制

```python
# apps/organizations/permissions.py

from rest_framework import permissions


class IsOrganizationMember(permissions.BasePermission):
    """组织成员权限"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 检查用户是否是该组织成员
        if hasattr(obj, 'organization'):
            org_id = obj.organization_id
        else:
            org_id = obj.id

        return request.user.user_organizations.filter(
            organization_id=org_id,
            is_active=True
        ).exists()


class IsOrganizationAdmin(permissions.BasePermission):
    """组织管理员权限"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        from apps.organizations.models import UserOrganization

        org_id = obj.organization_id if hasattr(obj, 'organization') else obj.id

        return UserOrganization.objects.filter(
            user=request.user,
            organization_id=org_id,
            role=UserOrganization.Role.ADMIN,
            is_active=True
        ).exists()
```

---

## 数据迁移

```python
# apps/organizations/migrations/0001_initial.py

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        # Organization 模型
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_organizations', to='accounts.user')),
                ('custom_fields', models.JSONField(default=dict, blank=True)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=50, unique=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='organizations.organization')),
                ('level', models.IntegerField(default=0)),
                ('path', models.CharField(default='', max_length=500)),
                ('org_type', models.CharField(choices=[('group', '集团'), ('company', '公司'), ('branch', '分公司'), ('department', '部门级组织')], default='company', max_length=20)),
                ('contact_person', models.CharField(blank=True, max_length=100)),
                ('contact_phone', models.CharField(blank=True, max_length=20)),
                ('email', models.EmailField(blank=True)),
                ('address', models.TextField(blank=True)),
                ('credit_code', models.CharField(blank=True, max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('settings', models.JSONField(default=dict, blank=True)),
                ('invite_code', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('invite_code_expires_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'organizations',
                'verbose_name': '组织',
                'verbose_name_plural': '组织',
                'indexes': [
                    models.Index(fields=['code']),
                    models.Index(fields=['parent']),
                    models.Index(fields=['is_active']),
                ],
            },
        ),

        # Department 模型
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_departments', to='accounts.user')),
                ('custom_fields', models.JSONField(default=dict, blank=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departments', to='organizations.organization')),
                ('code', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='organizations.department')),
                ('level', models.IntegerField(default=0)),
                ('path', models.CharField(default='', max_length=500)),
                ('order', models.IntegerField(default=0)),
                ('full_path', models.CharField(default='', max_length=500)),
                ('full_path_name', models.CharField(default='', max_length=1000)),
                ('leader', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='led_departments', to='accounts.user')),
                ('wework_dept_id', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('dingtalk_dept_id', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('feishu_dept_id', models.CharField(blank=True, db_index=True, max_length=50, null=True)),
                ('wework_leader_id', models.CharField(blank=True, max_length=64, null=True)),
                ('dingtalk_leader_id', models.CharField(blank=True, max_length=64, null=True)),
                ('feishu_leader_id', models.CharField(blank=True, max_length=64, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'departments',
                'verbose_name': '部门',
                'verbose_name_plural': '部门',
                'indexes': [
                    models.Index(fields=['organization', 'parent']),
                    models.Index(fields=['organization', 'level']),
                    models.Index(fields=['organization', 'wework_dept_id']),
                ],
            },
        ),

        # 其他模型...
    ]
```

---

## 配置更新

```python
# backend/config/settings.py

INSTALLED_APPS = [
    # ... 其他应用
    'organizations',  # 新增
]

# 更新用户模型引用（如果需要）
# AUTH_USER_MODEL = 'accounts.User'  # 保持不变
```

---

## 与现有代码的迁移策略

1. **数据迁移**：将 accounts.Organization 和 accounts.Department 的数据迁移到新模块
2. **模型引用更新**：更新所有外键引用
3. **API 路由更新**：保持 API 路径兼容

```python
# apps/organizations/migrations/0002_migrate_from_accounts.py

def migrate_organizations_from_accounts(apps, schema_editor):
    """从 accounts 模块迁移组织数据"""
    Organization = apps.get_model('organizations', 'Organization')
    OldOrganization = apps.get_model('accounts', 'Organization')

    for old_org in OldOrganization.objects.all():
        Organization.objects.create(
            id=old_org.id,
            name=old_org.name,
            code=old_org.code,
            # ... 其他字段映射
        )
```

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
