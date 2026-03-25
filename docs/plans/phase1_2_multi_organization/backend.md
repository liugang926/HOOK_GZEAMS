# Phase 1.2: 多组织数据隔离 - 后端实现

## 功能概述

实现严格的多组织数据隔离机制,通过BaseModel基类、TenantManager管理器、OrganizationMiddleware中间件三层防护,确保SaaS模式下不同租户间的数据完全隔离。

---

## 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Response | BaseResponse | apps.common.responses.base.BaseResponse | 统一响应格式 |
| Exception | BusinessLogicError | apps.common.handlers.exceptions.BusinessLogicError | 统一异常处理 |

---

## 架构设计

### 1.1 数据隔离流程

```
┌─────────────────────────────────────────────────────────────┐
│                     请求进入                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              OrganizationMiddleware                          │
│  - 从JWT/Session提取组织ID                                   │
│  - set_current_organization(org_id)                         │
│  - 验证用户组织权限                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              ThreadLocal Context                            │
│  _thread_locals.organization_id = org_id                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              TenantManager (BaseModel.objects)              │
│  - 自动添加 organization_id 过滤                            │
│  - 自动添加 is_deleted=False 过滤                            │
│  - 防止跨组织数据访问                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              数据库查询 (自动隔离)                            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 跨组织操作流程

```
┌─────────────────────────────────────────────────────────────┐
│              跨组织调拨审批流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. 创建调拨单 (在调出组织上下文)                             │
│     with OrganizationContext.switch(from_org_id):           │
│         assets = Asset.objects.filter(id__in=asset_ids)      │
│     # 使用 all_objects 创建调拨单(跨组织)                     │
│                                                               │
│  2. 审批调拨单 (在调入组织上下文)                             │
│     transfer = AssetTransfer.all_objects.get(id=xxx)         │
│     if transfer.to_organization_id != current_org:           │
│         raise PermissionDenied                              │
│                                                               │
│  3. 执行资产转移 (事务保护)                                  │
│     @transaction.atomic                                      │
│     def approve_transfer(...):                               │
│         with OrganizationContext.switch(from_org):           │
│             asset.organization_id = to_org_id                │
│             asset.save()                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据模型设计

### 2.1 BaseModel (核心基类)

**重要**: BaseModel不适用于Organization模型,避免循环引用。

#### 线程本地存储

| 函数 | 说明 |
|------|------|
| get_current_organization() | 获取当前请求的组织ID |
| set_current_organization(org_id) | 设置当前请求的组织ID |
| clear_current_organization() | 清除当前请求的组织ID |

#### TenantManager (租户管理器)

| 功能 | 实现方式 |
|------|---------|
| 自动添加 organization_id 过滤 | get_queryset() 中调用 get_current_organization() |
| 自动添加 is_deleted=False 过滤 | filter(is_deleted=False) |
| 防止跨组织数据访问 | 基于线程本地上下文自动过滤 |

#### BaseModel (基础模型)

| 字段 | 类型 | 说明 |
|------|------|------|
| **组织隔离** |
| organization | ForeignKey(Organization) | 所属组织，用于数据隔离 |
| **软删除** |
| is_deleted | BooleanField(default=False) | 软删除标记 |
| deleted_at | DateTimeField(null=True) | 删除时间 |
| **审计字段** |
| created_at | DateTimeField(auto_now_add=True) | 记录创建时间 |
| updated_at | DateTimeField(auto_now=True) | 记录更新时间 |
| created_by | ForeignKey(User) | 记录创建人 |
| **低代码扩展** |
| custom_fields | JSONField(default=dict) | 低代码定义的动态字段数据 |

**管理器**:
- `objects = TenantManager()` - 带组织过滤
- `all_objects = models.Manager()` - 不带过滤(仅特殊场景使用)

**核心方法**:
- `soft_delete()`: 软删除（设置 is_deleted=True, deleted_at=now）
- `restore()`: 恢复软删除（设置 is_deleted=False, deleted_at=None）
- `delete()`: 重写为强制软删除
- `hard_delete()`: 物理删除（慎用！永久删除数据）

**数据库索引**:
- `organization + is_deleted`
- `created_at`

### 2.2 User 模型扩展 (支持多组织)

#### User 模型字段

| 字段 | 类型 | 说明 |
|------|------|------|
| **当前组织** |
| current_organization | ForeignKey(Organization) | 用户当前选中的组织 |
| **所属组织** |
| organizations | ManyToManyField(through='UserOrganization') | 用户加入的组织列表 |
| **企业微信** |
| wework_userid | string(max_length=64, unique) | 企业微信UserID |
| wework_unionid | string(max_length=64, unique) | 企业微信应用间统一标识 |
| **钉钉** |
| dingtalk_userid | string(max_length=64, unique) | 钉钉UserID |
| dingtalk_unionid | string(max_length=64, unique) | 钉钉应用间统一标识 |
| **飞书** |
| feishu_userid | string(max_length=64, unique) | 飞书UserID |
| feishu_unionid | string(max_length=64, unique) | 飞书应用间统一标识 |

#### User 核心方法

| 方法 | 说明 |
|------|------|
| switch_organization(org_id) | 切换当前组织（设置 is_primary=True） |
| get_accessible_organizations() | 获取可访问的组织列表（QuerySet） |
| get_org_roles(org_id) | 获取在指定组织的角色（返回角色列表） |

#### UserOrganization (用户-组织关联表)

| 字段 | 类型 | 说明 |
|------|------|------|
| user | ForeignKey(User) | 用户 |
| organization | ForeignKey(Organization) | 组织 |
| role | string(choices=[admin, member, auditor]) | 角色，默认member |
| is_active | boolean(default=True) | 是否激活该组织成员资格 |
| is_primary | boolean(default=False) | 是否为用户的默认组织 |
| joined_at | DateTimeField(auto_now_add=True) | 加入时间 |
| invited_by | ForeignKey(User) | 邀请人 |

**约束**:
- unique_together: ['user', 'organization']
- 索引: ['user', 'is_active'], ['organization', 'is_active']

**业务逻辑** (save方法):
- 确保 is_primary=True 时，用户只有一个默认组织（其他自动设为False）

### 2.3 Organization 模型 (不继承BaseModel)

**重要**: Organization模型不继承BaseModel,避免 `organization.organization` 循环引用。

#### Organization 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| **基础信息** |
| id | UUIDField(primary_key) | 主键（UUID） |
| name | string(max_length=200) | 组织名称 |
| code | string(max_length=50, unique, db_index) | 组织编码 |
| **层级关系** |
| parent | ForeignKey(self) | 上级组织 |
| level | int(default=0) | 层级 |
| path | string(max_length=500) | 路径 |
| **组织类型** |
| org_type | string(choices=[group, company, branch, department]) | 组织类型，默认company |
| **联系信息** |
| contact_person | string(max_length=100) | 联系人 |
| contact_phone | string(max_length=20) | 联系电话 |
| email | EmailField | 邮箱 |
| address | TextField | 地址 |
| **财务信息** |
| credit_code | string(max_length=50) | 统一社会信用代码（用于财务集成） |
| **状态** |
| is_active | boolean(default=True) | 是否启用 |
| is_deleted | boolean(default=False) | 已删除 |
| **配置** |
| settings | JSONField(default=dict) | 组织级别配置项 |
| **邀请码** |
| invite_code | string(max_length=20, unique) | 邀请码 |
| invite_code_expires_at | DateTimeField | 邀请码过期时间 |
| **审计字段** |
| created_at | DateTimeField(auto_now_add=True) | 创建时间 |
| updated_at | DateTimeField(auto_now=True) | 更新时间 |
| created_by | ForeignKey(User) | 创建人 |

**数据库索引**:
- `code`
- `parent`
- `is_active`

**核心方法**:
- `save()`: 自动更新层级和路径（递归更新子组织）
- `_update_children_paths()`: 递归更新子组织的路径（私有）
- `get_all_children()`: 获取所有子组织（递归返回列表）
- `regenerate_invite_code()`: 重新生成8位随机邀请码（30天有效期）

**层级自动计算**:
- 有父组织: `level = parent.level + 1`, `path = parent.path + / + code`
- 无父组织: `level = 0`, `path = / + code`

---

## 中间件实现

### 3.1 OrganizationMiddleware

```python
# apps/common/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from apps.common.models import (
    set_current_organization,
    clear_current_organization
)
from apps.organizations.models import Organization


class OrganizationMiddleware(MiddlewareMixin):
    """
    组织上下文中间件

    功能:
    1. 从请求中提取组织ID
    2. 设置线程本地上下文
    3. 验证用户组织权限
    4. 请求完成后清理上下文

    组织ID提取优先级:
    1. HTTP头 X-Organization-ID (最高优先级)
    2. JWT Token中的organization_id
    3. Session中的current_organization_id
    4. URL查询参数org_id (仅DEBUG模式)
    5. 用户的current_organization (最后兜底)
    """

    def process_request(self, request):
        """处理请求 - 提取并设置组织上下文"""
        org_id = self._extract_organization_id(request)

        if org_id:
            # 验证用户是否属于该组织
            if request.user and request.user.is_authenticated:
                if not request.user.organizations.filter(id=org_id).exists():
                    # 用户不属于该组织,拒绝访问
                    from apps.common.responses.base import BaseResponse
                    from apps.common.handlers.exceptions import ErrorCode

                    return BaseResponse.organization_mismatch(
                        message=f"用户不属于组织ID: {org_id}"
                    )

            set_current_organization(org_id)
            request.current_organization_id = org_id

            # 添加懒加载的当前组织对象
            request.current_organization = SimpleLazyObject(
                lambda: self._get_organization(request)
            )

    def process_response(self, request, response):
        """处理响应 - 清理组织上下文"""
        clear_current_organization()
        return response

    def process_exception(self, request, exception):
        """处理异常 - 清理组织上下文"""
        clear_current_organization()
        raise exception

    def _extract_organization_id(self, request):
        """从请求中提取组织ID (按优先级)"""

        # 1. HTTP头 (优先级最高 - 用于API调用)
        org_id = request.META.get('HTTP_X_ORGANIZATION_ID')
        if org_id:
            if not org_id.isdigit():
                raise ValueError(f"Invalid organization ID in header: {org_id}")
            return int(org_id)

        # 2. JWT Token
        if hasattr(request, 'auth') and request.auth:
            org_id = request.auth.get('organization_id')
            if org_id:
                return org_id

        # 3. Session
        org_id = request.session.get('current_organization_id')
        if org_id:
            return org_id

        # 4. URL查询参数 (仅用于调试)
        from django.conf import settings
        org_id = request.GET.get('org_id')
        if org_id and settings.DEBUG:
            return int(org_id)

        # 5. 从当前用户的默认组织获取
        if request.user and request.user.is_authenticated:
            if request.user.current_organization_id:
                return request.user.current_organization_id

        return None

    def _get_organization(self, request):
        """获取当前组织对象"""
        org_id = getattr(request, 'current_organization_id', None)
        if org_id:
            try:
                return Organization.objects.get(id=org_id)
            except Organization.DoesNotExist:
                pass
        return None
```

### 3.2 JWT认证增强

```python
# apps/accounts/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
import jwt


class OrganizationJWTAuthentication(JWTAuthentication):
    """
    带组织信息的JWT认证

    JWT Payload 包含:
    {
        "user_id": 1,
        "organization_id": 2,
        "exp": 1234567890
    }
    """

    def get_user(self, validated_token):
        """从token获取用户并设置组织上下文"""
        user_id = validated_token.get('user_id')
        organization_id = validated_token.get('organization_id')

        if not user_id:
            raise InvalidToken("Token contained no recognizable user identification")

        try:
            from apps.accounts.models import User
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise InvalidToken("User not found")

        # 更新用户的当前组织
        if organization_id:
            if user.organizations.filter(id=organization_id).exists():
                user.current_organization_id = organization_id
                user.save(update_fields=['current_organization'])

        return user
```

---

## 服务层设计

### 4.1 组织上下文服务

```python
# apps/common/services/organization_service.py

from threading import local
from contextlib import contextmanager
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_thread_locals = local()


class OrganizationContext:
    """
    组织上下文管理器

    提供线程安全的组织上下文管理
    """

    @staticmethod
    def set(org_id):
        """
        设置当前组织

        Args:
            org_id: 组织ID
        """
        _thread_locals.organization_id = org_id
        logger.debug(f"Set organization context: {org_id}")

    @staticmethod
    def get() -> Optional[int]:
        """
        获取当前组织ID

        Returns:
            当前组织ID,如果未设置则返回None
        """
        return getattr(_thread_locals, 'organization_id', None)

    @staticmethod
    def clear():
        """清除组织上下文"""
        if hasattr(_thread_locals, 'organization_id'):
            delattr(_thread_locals, 'organization_id')
            logger.debug("Cleared organization context")

    @staticmethod
    @contextmanager
    def switch(org_id):
        """
        临时切换组织上下文

        用途:
        - 后台任务
        - 跨组织调拨
        - 数据迁移

        Example:
            with OrganizationContext.switch(target_org_id):
                # 在目标组织上下文中执行操作
                assets = Asset.objects.all()
                # 操作完成后自动恢复原上下文
        """
        old_org_id = OrganizationContext.get()
        try:
            OrganizationContext.set(org_id)
            logger.debug(f"Switched organization context: {old_org_id} -> {org_id}")
            yield
        finally:
            if old_org_id:
                OrganizationContext.set(old_org_id)
                logger.debug(f"Restored organization context: {org_id} -> {old_org_id}")
            else:
                OrganizationContext.clear()


# 为了向后兼容,保留原有的函数接口
def get_current_organization():
    """获取当前请求的组织ID"""
    return OrganizationContext.get()


def set_current_organization(org_id):
    """设置当前请求的组织ID"""
    OrganizationContext.set(org_id)


def clear_current_organization():
    """清除当前请求的组织ID"""
    OrganizationContext.clear()
```

### 4.2 跨组织调拨服务

```python
# apps/assets/services/transfer_service.py

from apps.common.services.organization_service import OrganizationContext
from apps.assets.models import Asset, AssetTransfer, TransferItem
from django.db import transaction


class CrossOrganizationTransferService:
    """
    跨组织资产调拨服务

    功能:
    1. 创建跨组织调拨单
    2. 审批调拨单
    3. 执行资产转移
    """

    @transaction.atomic
    def create_transfer_order(self, from_org_id, to_org_id, asset_ids, **kwargs):
        """
        创建跨组织调拨单

        Args:
            from_org_id: 调出组织ID
            to_org_id: 调入组织ID
            asset_ids: 资产ID列表
            **kwargs: 其他调拨信息

        Returns:
            AssetTransfer: 调拨单对象

        Raises:
            ValueError: 调出组织和调入组织相同
            ValueError: 资产不存在或无权访问
            ValueError: 资产状态不允许调拨
        """
        from django.utils import timezone

        if from_org_id == to_org_id:
            raise ValueError("调出组织和调入组织不能相同")

        # 切换到调出组织上下文验证资产
        with OrganizationContext.switch(from_org_id):
            assets = Asset.objects.filter(id__in=asset_ids)

            if assets.count() != len(asset_ids):
                found_ids = list(assets.values_list('id', flat=True))
                missing = set(asset_ids) - set(found_ids)
                raise ValueError(f"以下资产不存在或无权访问: {missing}")

            # 检查资产状态
            for asset in assets:
                if asset.status not in ['idle', 'in_use']:
                    raise ValueError(f"资产 {asset.code} 当前状态不允许调拨")

        # 使用 all_objects 跨越组织过滤创建调拨单
        transfer = AssetTransfer.all_objects.create(
            from_organization_id=from_org_id,
            to_organization_id=to_org_id,
            status='pending_approval',
            created_by_id=kwargs.get('creator_id'),
            **{k: v for k, v in kwargs.items() if k != 'creator_id'}
        )

        # 创建调拨明细
        items = []
        for asset in assets:
            items.append(TransferItem(
                transfer=transfer,
                asset=asset,
                from_location=asset.location,
                from_custodian=asset.custodian,
                asset_status_before=asset.status
            ))

        TransferItem.objects.bulk_create(items)

        return transfer

    @transaction.atomic
    def approve_transfer(self, transfer_id, org_id, approval_data):
        """
        审批调拨单

        Args:
            transfer_id: 调拨单ID
            org_id: 审批人所在组织ID
            approval_data: 审批数据

        Returns:
            AssetTransfer: 更新后的调拨单

        Raises:
            PermissionError: 只能审批调入组织的调拨单
            ValueError: 调拨单状态不允许审批
        """
        from django.utils import timezone

        # 使用 all_objects 查询 (可能不在当前组织)
        transfer = AssetTransfer.all_objects.get(id=transfer_id)

        # 验证权限
        if transfer.to_organization_id != org_id:
            raise PermissionError("只能审批调入组织的调拨单")

        if transfer.status != 'pending_approval':
            raise ValueError(f"调拨单状态不允许审批: {transfer.status}")

        if approval_data['decision'] == 'approved':
            # 执行资产转移
            with OrganizationContext.switch(transfer.from_organization_id):
                for item in transfer.items.all():
                    asset = item.asset

                    # 变更组织
                    asset.organization_id = transfer.to_organization_id
                    asset.location = transfer.to_location
                    asset.custodian = transfer.to_custodian
                    asset.status = 'transferred'

                    # 记录转移历史
                    asset.transfer_history.append({
                        'transfer_id': str(transfer_id),
                        'from_org': str(transfer.from_organization_id),
                        'to_org': str(transfer.to_organization_id),
                        'at': timezone.now().isoformat()
                    })

                    asset.save()

            transfer.status = 'completed'
            transfer.completed_at = timezone.now()
        else:
            transfer.status = 'rejected'
            transfer.rejection_reason = approval_data.get('reason', '')

        transfer.save()
        return transfer
```

---

## 配置更新

### 5.1 Django Settings

```python
# backend/config/settings.py

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.common.middleware.OrganizationMiddleware',  # 组织上下文中间件
    'django.contrib.messages.middleware.MessageMiddleware',
]

# JWT配置
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
    ),
    'BLACKLIST_AFTER_ROTATION': True,
}

# 自定义JWT认证
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.accounts.authentication.OrganizationJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

---

## 迁移文件

### 6.1 User模型扩展迁移

```python
# apps/accounts/migrations/0002_add_organization_fields.py

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('organizations', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        # 添加 current_organization 字段
        migrations.AddField(
            model_name='user',
            name='current_organization',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='current_users',
                to='organizations.organization'
            ),
        ),

        # 创建 UserOrganization 中间表
        migrations.CreateModel(
            name='UserOrganization',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID'
                )),
                ('role', models.CharField(
                    choices=[
                        ('admin', '管理员'),
                        ('member', '普通成员'),
                        ('auditor', '审计员')
                    ],
                    default='member',
                    max_length=20
                )),
                ('is_active', models.BooleanField(default=True)),
                ('is_primary', models.BooleanField(default=False)),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('invited_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='invited_user_organizations',
                    to='accounts.user'
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='organizations.organization'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='accounts.user'
                )),
            ],
            options={
                'db_table': 'user_organizations',
                'verbose_name': '用户组织关联',
                'verbose_name_plural': '用户组织关联',
            },
        ),

        # 添加唯一约束
        migrations.AlterUniqueTogether(
            name='userorganization',
            unique_together={('user', 'organization')},
        ),
    ]
```

---

## 实施步骤

1. ✅ 创建 `TenantManager` 和更新 `BaseModel`
2. ✅ 实现组织上下文服务 `organization_service.py`
3. ✅ 实现 `OrganizationMiddleware`
4. ✅ 扩展 `User` 模型支持多组织
5. ✅ 实现 `Organization` 模型 (不继承BaseModel)
6. ✅ 实现跨组织调拨服务
7. ✅ 更新 Django settings 配置
8. ✅ 创建数据库迁移文件

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

---

## 输出产物

| 文件 | 说明 |
|------|------|
| `apps/common/models.py` | BaseModel + TenantManager |
| `apps/common/middleware.py` | OrganizationMiddleware |
| `apps/common/services/organization_service.py` | 组织上下文管理器 |
| `apps/accounts/models.py` | User模型扩展 + UserOrganization |
| `apps/accounts/authentication.py` | JWT认证增强 |
| `apps/organizations/models.py` | Organization模型 (不继承BaseModel) |
| `apps/assets/services/transfer_service.py` | 跨组织调拨服务 |
| `backend/config/settings.py` | 中间件和JWT配置 |
| `apps/accounts/migrations/0002_add_organization_fields.py` | 迁移文件 |
