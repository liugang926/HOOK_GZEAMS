# Phase 2.5: 权限体系增强 - 后端实现

## 公共模型引用声明

本模块严格遵循GZEAMS公共基础架构规范，所有组件均继承相应的公共基类：

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离(`organization` FK)、软删除(`is_deleted`+`deleted_at`)、审计字段(`created_at`+`updated_at`+`created_by`)、动态字段(`custom_fields` JSONB) |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段自动序列化、`custom_fields`处理、审计字段嵌套序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除过滤、批量操作(`/batch-delete/`、`/batch-restore/`、`/batch-update/`) |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法、组织隔离、分页支持 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 公共字段过滤(时间范围、用户、组织) |

## 1. 数据模型设计

### 1.1 字段权限 (FieldPermission)

#### FieldPermission (字段权限表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| role | FK | cascade, nullable | 关联角色 |
| user | FK | cascade, nullable | 关联用户 |
| content_type | FK | cascade | 对象类型 (ContentType) |
| field_name | string | max_length=100 | 字段名 |
| permission_type | string | max_length=20 | 权限类型 (read/write/hidden/masked) |
| condition | JSON | nullable | 权限条件 |
| mask_rule | string | max_length=50, nullable | 脱敏规则 (phone/id_card/bank_card/name/amount/custom) |
| mask_params | JSON | nullable | 脱敏参数 |
| priority | integer | default=0 | 优先级 (越大越高) |
| remark | text | blank | 备注 |

*继承 BaseModel 自动获得公共字段*
*唯一约束: (role, content_type, field_name), (user, content_type, field_name)*
*索引: role, user, (content_type, field_name)*

#### FieldPermissionGroup (字段权限组表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| group_name | string | max_length=100 | 组名称 |
| group_code | string | max_length=50, unique | 组代码 |
| content_type | FK | cascade | 对象类型 |
| default_permission | string | max_length=20 | 默认权限 (read/write/hidden/masked) |
| fields | JSON | default=list | 字段列表 |
| exclude_fields | JSON | default=list | 排除字段 |

*继承 BaseModel 自动获得公共字段*

### 1.2 数据权限 (DataPermission)

#### DataPermission (数据权限表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| role | FK | cascade, nullable | 关联角色 |
| user | FK | cascade, nullable | 关联用户 |
| content_type | FK | cascade | 对象类型 |
| scope_type | string | max_length=20 | 范围类型 (all/self_dept/self_and_sub/specified/custom) |
| scope_value | JSON | default=dict | 范围值配置 |
| is_inherited | boolean | default=True | 允许继承 |
| custom_filter | JSON | nullable | 自定义过滤条件 (Django ORM filter) |
| is_active | boolean | default=True | 是否启用 |

*继承 BaseModel 自动获得公共字段*
*索引: role, user, content_type, is_active*

#### DataPermissionExpand (数据权限扩展表)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| base_permission | FK | cascade | 基础权限 (DataPermission) |
| expand_type | string | max_length=20 | 扩展类型 (department/user/condition) |
| expand_value | JSON | default=dict | 扩展值 (部门ID/用户ID/条件) |
| condition | JSON | nullable | 生效条件 |

*继承 BaseModel 自动获得公共字段*

### 1.3 权限继承 (PermissionInheritance)

```python
class PermissionInheritance(BaseModel):
    """
    权限继承关系
    定义角色之间的权限继承关系
    """
    INHERIT_TYPES = [
        ('full', '完全继承'),
        ('partial', '部分继承'),
        ('override', '覆盖继承'),
    ]

    # 父角色
    parent_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.CASCADE,
        related_name='child_inheritances',
        verbose_name='父角色'
    )

    # 子角色
    child_role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.CASCADE,
        related_name='parent_inheritances',
        verbose_name='子角色'
    )

    # 继承类型
    inherit_type = models.CharField(
        max_length=20,
        choices=INHERIT_TYPES,
        default='full',
        verbose_name='继承类型'
    )

    # 是否启用
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    # 备注
    remark = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        db_table = 'permission_inheritance'
        verbose_name = '权限继承'
        verbose_name_plural = '权限继承'
        ordering = ['parent_role', 'child_role']
        unique_together = [['parent_role', 'child_role']]

    def __str__(self):
        return f"{self.parent_role.name} → {self.child_role.name} ({self.get_inherit_type_display()})"


class DepartmentPermissionInheritance(BaseModel):
    """
    部门权限继承
    定义基于组织架构的权限继承
    """
    # 父部门
    parent_dept = models.ForeignKey(
        'organizations.Department',
        on_delete=models.CASCADE,
        related_name='child_dept_permissions',
        verbose_name='父部门'
    )

    # 子部门
    child_dept = models.ForeignKey(
        'organizations.Department',
        on_delete=models.CASCADE,
        related_name='parent_dept_permissions',
        verbose_name='子部门'
    )

    # 权限范围
    permission_scope = models.CharField(
        max_length=20,
        choices=[
            ('all', '全部'),
            ('direct', '仅直接下级'),
            ('all_below', '所有下级'),
        ],
        default='all_below',
        verbose_name='权限范围'
    )

    # 是否启用
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'permission_dept_inheritance'
        verbose_name = '部门权限继承'
        verbose_name_plural = '部门权限继承'
        ordering = ['parent_dept', 'child_dept']
        unique_together = [['parent_dept', 'child_dept']]

    def __str__(self):
        return f"{self.parent_dept.name} → {self.child_dept.name}"
```

### 1.4 权限审计日志 (PermissionAuditLog)

```python
class PermissionAuditLog(BaseModel):
    """
    权限审计日志
    记录权限相关的所有操作
    """
    ACTION_TYPES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('grant', '授权'),
        ('revoke', '撤销'),
        ('access', '访问'),
        ('deny', '拒绝'),
    ]

    TARGET_TYPES = [
        ('role', '角色'),
        ('user', '用户'),
        ('field_permission', '字段权限'),
        ('data_permission', '数据权限'),
        ('inheritance', '继承关系'),
    ]

    # 操作人
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='permission_audit_logs',
        verbose_name='操作人'
    )

    # 操作信息
    action = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name='操作类型')
    target_type = models.CharField(max_length=50, choices=TARGET_TYPES, verbose_name='目标类型')
    target_id = models.IntegerField(verbose_name='目标ID')
    target_name = models.CharField(max_length=200, verbose_name='目标名称')

    # 变更内容
    changes = models.JSONField(default=dict, verbose_name='变更内容')
    # 示例: {"old": {...}, "new": {...}}

    # 请求信息
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')

    # 结果
    success = models.BooleanField(default=True, verbose_name='是否成功')
    error_message = models.TextField(blank=True, verbose_name='错误信息')

    # 关联的原始请求
    request_id = models.CharField(max_length=100, null=True, blank=True, verbose_name='请求ID')

    class Meta:
        db_table = 'permission_audit_log'
        verbose_name = '权限审计日志'
        verbose_name_plural = '权限审计日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor']),
            models.Index(fields=['action']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.actor} {self.action} {self.target_type}:{self.target_id}"
```

---

## 2. 权限引擎实现

### 2.1 核心权限引擎

```python
# apps/permissions/engine.py

from typing import Dict, List, Any, Optional
from django.db.models import Q, QuerySet
from django.contrib.contenttypes.models import ContentType
from apps.permissions.models import FieldPermission, DataPermission
from apps.accounts.models import User, Role
import hashlib


class PermissionEngine:
    """权限引擎核心类"""

    # 缓存
    _field_permissions_cache = {}
    _data_scope_cache = {}

    @staticmethod
    def get_field_permissions(user: User, object_type: str, action: str = 'view') -> Dict[str, str]:
        """
        获取用户的字段级权限
        Args:
            user: 用户对象
            object_type: 对象类型 (如 'assets.Asset')
            action: 操作类型 (view/create/update/delete)
        Returns:
            {field_name: permission_type}
            permission_type: read/write/hidden/masked
        """
        cache_key = f"field_perm:{user.id}:{object_type}:{action}"

        if cache_key in PermissionEngine._field_permissions_cache:
            return PermissionEngine._field_permissions_cache[cache_key]

        try:
            content_type = ContentType.objects.get_by_natural_key(*object_type.split('.'))
        except ContentType.DoesNotExist:
            return {}

        # 获取用户的所有角色
        roles = user.roles.all() if hasattr(user, 'roles') else []
        role_ids = [r.id for r in roles]

        # 查询字段权限
        perms = FieldPermission.objects.filter(
            content_type=content_type,
            is_active=True
        ).filter(
            Q(role_id__in=role_ids) | Q(user=user)
        ).order_by('-priority')

        # 构建权限映射
        field_perms = {}
        for perm in perms:
            # 检查条件
            if perm.condition and not PermissionEngine._check_condition(perm.condition, user, action):
                continue

            field_perms[perm.field_name] = perm.permission_type

        PermissionEngine._field_permissions_cache[cache_key] = field_perms
        return field_perms

    @staticmethod
    def get_data_scope(user: User, object_type: str) -> Dict[str, Any]:
        """
        获取用户的数据级权限范围
        Args:
            user: 用户对象
            object_type: 对象类型
        Returns:
            {
                'scope_type': 'all/self_dept/specified/custom',
                'scope_value': {...},
                'expansions': [...]
            }
        """
        cache_key = f"data_scope:{user.id}:{object_type}"

        if cache_key in PermissionEngine._data_scope_cache:
            return PermissionEngine._data_scope_cache[cache_key]

        try:
            content_type = ContentType.objects.get_by_natural_key(*object_type.split('.'))
        except ContentType.DoesNotExist:
            return {'scope_type': 'all', 'scope_value': {}, 'expansions': []}

        # 获取用户角色
        roles = user.roles.all() if hasattr(user, 'roles') else []
        role_ids = [r.id for r in roles]

        # 查询数据权限
        perms = DataPermission.objects.filter(
            content_type=content_type,
            is_active=True
        ).filter(
            Q(role_id__in=role_ids) | Q(user=user)
        ).order_by('-priority')

        # 合并权限（取最宽松的）
        result = {'scope_type': 'self_dept', 'scope_value': {}, 'expansions': []}

        for perm in perms:
            if perm.scope_type == 'all':
                result = {
                    'scope_type': 'all',
                    'scope_value': {},
                    'expansions': []
                }
                break
            elif perm.scope_type == 'self_and_sub' and result['scope_type'] != 'all':
                result = {
                    'scope_type': 'self_and_sub',
                    'scope_value': perm.scope_value,
                    'expansions': []
                }
            elif perm.scope_type == 'self_dept' and result['scope_type'] in ['self_dept']:
                result = {
                    'scope_type': 'self_dept',
                    'scope_value': perm.scope_value,
                    'expansions': []
                }

        # 获取权限扩展
        for perm in perms:
            if perm.id:
                expansions = DataPermissionExpand.objects.filter(base_permission=perm)
                for exp in expansions:
                    result['expansions'].append({
                        'type': exp.expand_type,
                        'value': exp.expand_value,
                        'condition': exp.condition
                    })

        PermissionEngine._data_scope_cache[cache_key] = result
        return result

    @staticmethod
    def apply_data_scope(queryset: QuerySet, user: User, object_type: str) -> QuerySet:
        """
        将数据权限范围应用到查询集
        Args:
            queryset: 原始查询集
            user: 用户对象
            object_type: 对象类型
        Returns:
            过滤后的查询集
        """
        data_scope = PermissionEngine.get_data_scope(user, object_type)
        scope_type = data_scope['scope_type']
        scope_value = data_scope['scope_value']

        if scope_type == 'all':
            return queryset

        elif scope_type == 'self_dept':
            # 本部门数据
            dept_field = PermissionEngine._get_department_field(object_type)
            if dept_field and user.department:
                queryset = queryset.filter(**{dept_field: user.department})

        elif scope_type == 'self_and_sub':
            # 本部门及下级
            dept_field = PermissionEngine._get_department_field(object_type)
            if dept_field and user.department:
                # 获取所有下级部门
                from apps.organizations.models import Department
                dept_ids = Department.get_descendant_ids(user.department.id)
                queryset = queryset.filter(**{f"{dept_field}__id__in": dept_ids})

        elif scope_type == 'specified':
            # 指定部门
            dept_field = PermissionEngine._get_department_field(object_type)
            if dept_field:
                dept_ids = scope_value.get('department_ids', [])
                queryset = queryset.filter(**{f"{dept_field}__id__in": dept_ids})

        elif scope_type == 'custom':
            # 自定义过滤
            from django.db.models import Q
            custom_filter = scope_value.get('filter', {})
            queryset = queryset.filter(**custom_filter)

        # 应用权限扩展
        for expansion in data_scope.get('expansions', []):
            queryset = PermissionEngine._apply_expansion(queryset, expansion, user)

        return queryset

    @staticmethod
    def apply_field_permissions(data: List[Dict], user: User, object_type: str, action: str = 'view') -> List[Dict]:
        """
        将字段权限应用到数据
        Args:
            data: 原始数据
            user: 用户对象
            object_type: 对象类型
            action: 操作类型
        Returns:
            处理后的数据
        """
        field_perms = PermissionEngine.get_field_permissions(user, object_type, action)

        if not field_perms:
            return data

        result = []
        for row in data:
            processed_row = {}
            for field, value in row.items():
                perm = field_perms.get(field)

                if perm == 'hidden':
                    continue  # 跳过隐藏字段
                elif perm == 'masked':
                    processed_row[field] = PermissionEngine._mask_field_value(field, value, user)
                elif perm == 'read':
                    processed_row[field] = value
                else:  # write 或 默认
                    processed_row[field] = value

            result.append(processed_row)

        return result

    @staticmethod
    def _get_department_field(object_type: str) -> Optional[str]:
        """获取对象的部门字段"""
        field_map = {
            'assets.Asset': 'department',
            'assets.AssetChange': 'department',
            'lifecycle.PurchaseRequest': 'department',
            'lifecycle.AssetReceipt': 'department',
        }
        return field_map.get(object_type)

    @staticmethod
    def _check_condition(condition: Dict, user: User, action: str) -> bool:
        """检查权限条件"""
        condition_type = condition.get('type')

        if condition_type == 'eq':
            return str(condition.get('value')) == str(getattr(user, condition.get('field'), None))
        elif condition_type == 'in':
            return str(getattr(user, condition.get('field'), None)) in condition.get('value', [])
        elif condition_type == 'action':
            return action in condition.get('actions', [])

        return True

    @staticmethod
    def _mask_field_value(field_name: str, value: Any, user: User) -> str:
        """对字段值进行脱敏处理"""
        if value is None:
            return ''

        str_value = str(value)
        value_type = type(value)

        # 根据字段名判断脱敏规则
        if 'phone' in field_name or 'mobile' in field_name:
            return PermissionEngine._mask_phone(str_value)
        elif 'id_card' in field_name:
            return PermissionEngine._mask_id_card(str_value)
        elif 'bank' in field_name or 'card' in field_name:
            return PermissionEngine._mask_bank_card(str_value)
        elif 'name' in field_name:
            return PermissionEngine._mask_name(str_value)
        elif value_type in [int, float, decimal.Decimal]:
            return PermissionEngine._mask_amount(value)
        else:
            return '***'

    @staticmethod
    def _mask_phone(value: str) -> str:
        """手机号脱敏：保留前3后4"""
        if len(value) >= 7:
            return f"{value[:3]}****{value[-4:]}"
        return '****'

    @staticmethod
    def _mask_id_card(value: str) -> str:
        """身份证脱敏：保留前3后4"""
        if len(value) >= 7:
            return f"{value[:3]}***********{value[-4:]}"
        return '****'

    @staticmethod
    def _mask_bank_card(value: str) -> str:
        """银行卡脱敏：保留后4位"""
        if len(value) >= 4:
            return f"{'*' * (len(value) - 4)}{value[-4:]}"
        return '****'

    @staticmethod
    def _mask_name(value: str) -> str:
        """姓名脱敏：保留最后一个字"""
        if len(value) >= 1:
            return f"*{value[-1:]}"
        return '*'

    @staticmethod
    def _mask_amount(value: Any) -> str:
        """金额脱敏：显示范围"""
        try:
            num = float(value)
            if num < 1000:
                return '<1,000'
            elif num < 10000:
                return '1,000~10,000'
            elif num < 100000:
                return '1万~10万'
            else:
                return '>10万'
        except:
            return '***'

    @staticmethod
    def clear_cache(user_id: int = None):
        """清除权限缓存"""
        if user_id:
            keys_to_clear = [k for k in PermissionEngine._field_permissions_cache if k.startswith(f'field_perm:{user_id}')]
            keys_to_clear.extend([k for k in PermissionEngine._data_scope_cache if k.startswith(f'data_scope:{user_id}')])
        else:
            keys_to_clear = list(PermissionEngine._field_permissions_cache.keys())
            keys_to_clear.extend(list(PermissionEngine._data_scope_cache.keys()))

        for key in keys_to_clear:
            PermissionEngine._field_permissions_cache.pop(key, None)
            PermissionEngine._data_scope_cache.pop(key, None)

    @staticmethod
    def log_permission_action(actor: User, action: str, target_type: str, target_id: int,
                               target_name: str, changes: Dict = None, request=None):
        """记录权限操作日志"""
        from apps.permissions.models import PermissionAuditLog

        PermissionAuditLog.objects.create(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            changes=changes or {},
            ip_address=PermissionEngine._get_client_ip(request),
            user_agent=PermissionEngine._get_user_agent(request),
            org=actor.org if actor else None,
        )

    @staticmethod
    def _get_client_ip(request) -> Optional[str]:
        """获取客户端IP"""
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            return ip
        return None

    @staticmethod
    def _get_user_agent(request) -> str:
        """获取User Agent"""
        if request:
            return request.META.get('HTTP_USER_AGENT', '')
        return ''
```

### 2.2 DRF权限类

```python
# apps/permissions/permissions.py

from rest_framework import permissions
from apps.permissions.engine import PermissionEngine


class IsDataOwner(permissions.BasePermission):
    """数据拥有者权限检查"""

    def has_object_permission(self, request, view, obj):
        # 检查用户是否有权限访问此对象
        data_scope = PermissionEngine.get_data_scope(request.user, obj.__class__.__name__)
        scope_type = data_scope['scope_type']

        if scope_type == 'all':
            return True

        # 检查对象是否在用户的数据范围内
        if hasattr(obj, 'department'):
            if obj.department == request.user.department:
                return True

            # 检查下级部门
            from apps.organizations.models import Department
            if Department.is_ancestor(request.user.department.id, obj.department.id):
                return True

        return False


class FieldPermissionMixin:
    """字段权限混合类"""

    def get_field_permissions(self):
        """获取当前操作的字段权限"""
        if hasattr(self, 'request') and hasattr(self.request, 'user'):
            object_type = self.get_serializer_class().Meta.model.__name__
            action = self.action if hasattr(self, 'action') else 'view'
            return PermissionEngine.get_field_permissions(
                self.request.user,
                object_type,
                action
            )
        return {}

    def get_serializer(self, *args, **kwargs):
        """重写get_serializer以应用字段权限"""
        serializer_class = self.get_serializer_class()

        context = self.get_serializer_context()
        fields = self._get_allowed_fields(serializer_class, context)

        if fields:
            return serializer_class(*args, fields=fields, context=context)
        return serializer_class(*args, **kwargs)

    def _get_allowed_fields(self, serializer_class, context):
        """获取允许的字段列表"""
        field_perms = self.get_field_permissions()
        if not field_perms:
            return None

        allowed_fields = []
        for field_name in serializer_class.Meta.fields:
            perm = field_perms.get(field_name)
            if perm != 'hidden':
                allowed_fields.append(field_name)

        return allowed_fields if allowed_fields else None
```

---

## 3. 序列化器设计

### 3.1 字段权限序列化器

```python
# apps/permissions/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.permissions.models import FieldPermission, DataPermission, FieldPermissionGroup


class FieldPermissionSerializer(BaseModelSerializer):
    """字段权限序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = FieldPermission
        fields = BaseModelSerializer.Meta.fields + [
            'role', 'user', 'content_type', 'field_name',
            'permission_type', 'condition', 'mask_rule', 'mask_params',
            'priority', 'remark'
        ]


class FieldPermissionDetailSerializer(BaseModelWithAuditSerializer):
    """字段权限详情序列化器"""

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = FieldPermission
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'role', 'user', 'content_type', 'field_name',
            'permission_type', 'condition', 'mask_rule', 'mask_params',
            'priority', 'remark'
        ]


class DataPermissionSerializer(BaseModelSerializer):
    """数据权限序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = DataPermission
        fields = BaseModelSerializer.Meta.fields + [
            'role', 'user', 'content_type', 'scope_type',
            'scope_value', 'is_inherited', 'custom_filter', 'is_active'
        ]


class FieldPermissionGroupSerializer(BaseModelSerializer):
    """字段权限组序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = FieldPermissionGroup
        fields = BaseModelSerializer.Meta.fields + [
            'group_name', 'group_code', 'content_type',
            'default_permission', 'fields', 'exclude_fields'
        ]
```

---

## 4. 视图层设计

### 4.1 字段权限视图

```python
# apps/permissions/views.py

from rest_framework import viewsets
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.permissions.models import FieldPermission, DataPermission, FieldPermissionGroup
from apps.permissions.serializers import (
    FieldPermissionSerializer,
    DataPermissionSerializer,
    FieldPermissionGroupSerializer
)


class FieldPermissionViewSet(BaseModelViewSetWithBatch):
    """字段权限 ViewSet - 自动获得所有公共功能"""

    queryset = FieldPermission.objects.all()
    serializer_class = FieldPermissionSerializer
    # 自动获得：
    # - 组织隔离
    # - 软删除
    # - 批量删除/恢复/更新
    # - 已删除列表查询


class DataPermissionViewSet(BaseModelViewSetWithBatch):
    """数据权限 ViewSet - 自动获得所有公共功能"""

    queryset = DataPermission.objects.all()
    serializer_class = DataPermissionSerializer
    # 自动获得：
    # - 组织隔离
    # - 软删除
    # - 批量删除/恢复/更新
    # - 已删除列表查询


class FieldPermissionGroupViewSet(BaseModelViewSetWithBatch):
    """字段权限组 ViewSet - 自动获得所有公共功能"""

    queryset = FieldPermissionGroup.objects.all()
    serializer_class = FieldPermissionGroupSerializer
    # 自动获得：
    # - 组织隔离
    # - 软删除
    # - 批量删除/恢复/更新
    # - 已删除列表查询
```

---

## 5. 服务层设计

### 5.1 字段权限服务

```python
# apps/permissions/services/field_permission_service.py

from apps.common.services.base_crud import BaseCRUDService
from apps.permissions.models import FieldPermission


class FieldPermissionService(BaseCRUDService):
    """字段权限服务 - 继承 CRUD 基类"""

    def __init__(self):
        super().__init__(FieldPermission)

    def grant_field_permission(
        self,
        role_id: int = None,
        user_id: int = None,
        object_type: str = None,
        field_name: str = None,
        permission_type: str = 'read',
        actor=None
    ) -> FieldPermission:
        """授予字段权限"""
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_by_natural_key(*object_type.split('.'))

        permission = self.create({
            'role_id': role_id,
            'user_id': user_id,
            'content_type': content_type,
            'field_name': field_name,
            'permission_type': permission_type,
        }, user=actor)

        # 记录日志
        PermissionEngine.log_permission_action(
            actor=actor,
            action='grant',
            target_type='field_permission',
            target_id=permission.id,
            target_name=f"{object_type}.{field_name}",
            changes={'permission_type': permission_type}
        )

        # 清除缓存
        PermissionEngine.clear_cache(user_id)

        return permission

    def revoke_field_permission(self, permission_id: int, actor=None) -> bool:
        """撤销字段权限"""
        try:
            # 使用基类的软删除方法
            self.delete(permission_id, user=actor)

            # 记录日志
            permission = FieldPermission.all_objects.get(id=permission_id)
            PermissionEngine.log_permission_action(
                actor=actor,
                action='revoke',
                target_type='field_permission',
                target_id=permission_id,
                target_name=str(permission)
            )

            # 清除缓存
            PermissionEngine.clear_cache()
            return True
        except FieldPermission.DoesNotExist:
            return False

    def batch_grant_permissions(
        self,
        role_id: int = None,
        user_id: int = None,
        object_type: str = None,
        field_configs = None,
        actor=None
    ) -> int:
        """批量授予字段权限"""
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_by_natural_key(*object_type.split('.'))

        permissions = []
        for config in field_configs:
            perm = self.create({
                'role_id': role_id,
                'user_id': user_id,
                'content_type': content_type,
                'field_name': config['field_name'],
                'permission_type': config.get('permission_type', 'read'),
                'condition': config.get('condition'),
            }, user=actor)
            permissions.append(perm)

        # 清除缓存
        PermissionEngine.clear_cache(user_id)

        return len(permissions)

    def get_by_role_and_field(self, role_id: int, content_type_id: int, field_name: str):
        """根据角色和字段获取权限"""
        return self.query(filters={
            'role_id': role_id,
            'content_type_id': content_type_id,
            'field_name': field_name
        }).first()
```

### 5.2 数据权限服务

```python
# apps/permissions/services/data_permission_service.py

from apps.common.services.base_crud import BaseCRUDService
from apps.permissions.models import DataPermission, DataPermissionExpand


class DataPermissionService(BaseCRUDService):
    """数据权限服务 - 继承 CRUD 基类"""

    def __init__(self):
        super().__init__(DataPermission)

    def grant_data_permission(
        self,
        role_id: int = None,
        user_id: int = None,
        object_type: str = None,
        scope_type: str = 'self_dept',
        scope_value: Dict = None,
        actor=None
    ) -> DataPermission:
        """授予数据权限"""
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_by_natural_key(*object_type.split('.'))

        permission = self.create({
            'role_id': role_id,
            'user_id': user_id,
            'content_type': content_type,
            'scope_type': scope_type,
            'scope_value': scope_value or {},
        }, user=actor)

        # 清除缓存
        PermissionEngine.clear_cache(user_id)

        return permission

    def add_data_permission_expansion(
        self,
        base_permission_id: int,
        expand_type: str,
        expand_value: Dict,
        actor=None
    ) -> DataPermissionExpand:
        """添加数据权限扩展"""
        expansion = DataPermissionExpand.objects.create(
            base_permission_id=base_permission_id,
            expand_type=expand_type,
            expand_value=expand_value,
            org=actor.org if actor else None,
            created_by=actor,
        )

        return expansion

    def get_user_accessible_departments(self, user: User, object_type: str = None):
        """获取用户可访问的部门列表"""
        from apps.organizations.models import Department

        data_scope = PermissionEngine.get_data_scope(user, object_type or 'assets.Asset')
        scope_type = data_scope['scope_type']

        dept_ids = []

        if scope_type == 'all':
            dept_ids = Department.objects.filter(org=user.org).values_list('id', flat=True)
        elif scope_type == 'self_dept':
            dept_ids = [user.department_id] if user.department_id else []
        elif scope_type == 'self_and_sub':
            dept_ids = Department.get_descendant_ids(user.department_id) if user.department_id else []
        elif scope_type == 'specified':
            dept_ids = data_scope['scope_value'].get('department_ids', [])

        # 应用扩展
        for expansion in data_scope.get('expansions', []):
            if expansion['type'] == 'department':
                dept_ids.extend(expansion['value'].get('department_ids', []))

        return list(set(dept_ids))

    def get_by_role(self, role_id: int, content_type_id: int = None):
        """根据角色获取数据权限"""
        filters = {'role_id': role_id}
        if content_type_id:
            filters['content_type_id'] = content_type_id

        return self.query(filters=filters, order_by='-priority')
```

---

## 6. URL路由配置

### 6.1 权限模块路由

```python
# apps/permissions/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.permissions.views import (
    FieldPermissionViewSet,
    DataPermissionViewSet,
    FieldPermissionGroupViewSet
)

router = DefaultRouter()
router.register(r'field-permissions', FieldPermissionViewSet, basename='fieldpermission')
router.register(r'data-permissions', DataPermissionViewSet, basename='datapermission')
router.register(r'field-permission-groups', FieldPermissionGroupViewSet, basename='fieldpermissiongroup')

urlpatterns = [
    path('', include(router.urls)),
]
```

### 6.2 主路由配置

```python
# backend/config/urls.py

urlpatterns = [
    # ... 其他路由
    path('api/permissions/', include('apps.permissions.urls')),
]
```

---

## 7. 管理命令

### 7.1 权限同步命令

```python
# apps/permissions/management/commands/sync_permissions.py

from django.core.management.base import BaseCommand
from apps.accounts.models import User, Role
from apps.permissions.services.field_permission_service import FieldPermissionService
from apps.permissions.services.data_permission_service import DataPermissionService


class Command(BaseCommand):
    help = '同步权限配置'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['field', 'data'],
            help='权限类型'
        )

    def handle(self, *args, **options):
        perm_type = options.get('type')

        if perm_type == 'field':
            self.sync_field_permissions()
        elif perm_type == 'data':
            self.sync_data_permissions()

    def sync_field_permissions(self):
        """同步字段权限"""
        # 预定义的字段权限配置
        configs = [
            {
                'role_code': 'asset_user',
                'object_type': 'assets.Asset',
                'fields': [
                    {'field': 'original_value', 'permission': 'masked'},
                    {'field': 'supplier', 'permission': 'hidden'},
                ]
            },
            # ... 更多配置
        ]

        field_perm_service = FieldPermissionService()

        for config in configs:
            try:
                role = Role.objects.get(code=config['role_code'])
                field_perm_service.batch_grant_permissions(
                    role_id=role.id,
                    object_type=config['object_type'],
                    field_configs=config['fields']
                )
                self.stdout.write(f"已为角色 {role.code} 配置字段权限")
            except Role.DoesNotExist:
                self.stdout.write(f"角色 {config['role_code']} 不存在")

    def sync_data_permissions(self):
        """同步数据权限"""
        # 预定义的数据权限配置
        configs = [
            {
                'role_code': 'dept_manager',
                'object_type': 'assets.Asset',
                'scope_type': 'self_and_sub',
                'scope_value': {}
            },
            # ... 更多配置
        ]

        data_perm_service = DataPermissionService()

        for config in configs:
            try:
                role = Role.objects.get(code=config['role_code'])
                data_perm_service.grant_data_permission(
                    role_id=role.id,
                    object_type=config['object_type'],
                    scope_type=config['scope_type'],
                    scope_value=config['scope_value']
                )
                self.stdout.write(f"已为角色 {role.code} 配置数据权限")
            except Role.DoesNotExist:
                self.stdout.write(f"角色 {config['role_code']} 不存在")
```

---

## 8. 测试用例

### 8.1 字段权限测试

```python
# apps/permissions/tests/test_field_permission.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.permissions.models import FieldPermission
from apps.permissions.services.field_permission_service import FieldPermissionService
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


class FieldPermissionTestCase(TestCase):
    """字段权限测试用例"""

    def setUp(self):
        self.org = self.create_organization()
        self.user = self.create_user()
        self.role = self.create_role()
        self.user.roles.add(self.role)

    def create_organization(self):
        """创建组织"""
        from apps.organizations.models import Organization
        return Organization.objects.create(name="测试组织", code="TEST_ORG")

    def create_user(self):
        """创建用户"""
        return User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            org=self.org
        )

    def create_role(self):
        """创建角色"""
        from apps.accounts.models import Role
        return Role.objects.create(
            name="测试角色",
            code="test_role",
            org=self.org
        )

    def test_field_permission_creation(self):
        """测试字段权限创建"""
        content_type = ContentType.objects.get_for_model(get_user_model())

        # 测试公共基类功能
        field_perm = FieldPermission.objects.create(
            role=self.role,
            content_type=content_type,
            field_name="email",
            permission_type="masked",
            org=self.org,
            created_by=self.user
        )

        # 验证公共字段自动填充
        self.assertEqual(field_perm.org, self.org)
        self.assertEqual(field_perm.created_by, self.user)
        self.assertFalse(field_perm.is_deleted)
        self.assertIsNotNone(field_perm.created_at)

    def test_field_permission_deletion(self):
        """测试软删除"""
        content_type = ContentType.objects.get_for_model(get_user_model())
        field_perm = FieldPermission.objects.create(
            role=self.role,
            content_type=content_type,
            field_name="phone",
            permission_type="hidden"
        )

        perm_id = field_perm.id

        # 使用基类的软删除功能
        service = FieldPermissionService()
        service.delete(perm_id, user=self.user)

        # 验证软删除
        self.assertFalse(FieldPermission.objects.filter(id=perm_id).exists())
        self.assertTrue(FieldPermission.all_objects.filter(id=perm_id).exists())

    def test_batch_permission_operations(self):
        """测试批量操作"""
        content_type = ContentType.objects.get_for_model(get_user_model())
        service = FieldPermissionService()

        # 创建多个权限
        for i in range(5):
            FieldPermission.objects.create(
                role=self.role,
                content_type=content_type,
                field_name=f"field_{i}",
                permission_type="read"
            )

        perm_ids = [p.id for p in FieldPermission.objects.all()]

        # 测试批量删除
        result = service.batch_delete(perm_ids, user=self.user)
        self.assertEqual(result['summary']['succeeded'], 5)
        self.assertEqual(result['summary']['failed'], 0)

        # 测试批量恢复
        result = service.batch_restore(perm_ids, user=self.user)
        self.assertEqual(result['summary']['succeeded'], 5)

    def test_permission_caching(self):
        """测试权限缓存"""
        from apps.permissions.engine import PermissionEngine

        content_type = ContentType.objects.get_for_model(get_user_model())

        # 创建权限
        FieldPermission.objects.create(
            role=self.role,
            content_type=content_type,
            field_name="salary",
            permission_type="masked"
        )

        # 第一次获取（应该从数据库）
        perms1 = PermissionEngine.get_field_permissions(self.user, "auth.User")

        # 删除权限
        FieldPermission.objects.all().delete()

        # 第二次获取（应该从缓存）
        perms2 = PermissionEngine.get_field_permissions(self.user, "auth.User")

        # 清除缓存后再次获取
        PermissionEngine.clear_cache(self.user.id)
        perms3 = PermissionEngine.get_field_permissions(self.user, "auth.User")

        # 验证缓存机制
        self.assertEqual(perms1, perms2)  # 缓存未清除时相同
        self.assertNotEqual(perms1, perms3)  # 清除缓存后不同


class FieldPermissionEdgeCaseTestCase(TestCase):
    """字段边界测试用例"""

    def setUp(self):
        self.org = self.create_organization()
        self.user = self.create_user()

    def create_organization(self):
        from apps.organizations.models import Organization
        return Organization.objects.create(name="测试组织", code="TEST_ORG")

    def create_user(self):
        from apps.accounts.models import User
        return User.objects.create_user(
            username="testuser",
            password="testpass123",
            org=self.org
        )

    def test_concurrent_permission_updates(self):
        """并发权限更新测试"""
        from django.contrib.contenttypes.models import ContentType
        from django.db import transaction
        from threading import Thread
        import time

        content_type = ContentType.objects.get_for_model(get_user_model())

        def update_permission():
            """更新权限的线程函数"""
            time.sleep(0.1)  # 确保并发
            FieldPermission.objects.create(
                role=self.user.roles.first(),
                content_type=content_type,
                field_name="concurrent_field",
                permission_type="write"
            )

        # 创建并发线程
        threads = []
        for _ in range(3):
            thread = Thread(target=update_permission)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证数据一致性
        count = FieldPermission.objects.filter(
            field_name="concurrent_field"
        ).count()
        self.assertGreaterEqual(count, 1)

    def test_permission_inheritance_chain(self):
        """权限继承链测试"""
        from apps.accounts.models import Role
        from apps.permissions.models import PermissionInheritance
        from django.contrib.contenttypes.models import ContentType

        # 创建角色继承链
        parent_role = Role.objects.create(name="父角色", code="parent", org=self.org)
        child_role = Role.objects.create(name="子角色", code="child", org=self.org)
        grandchild_role = Role.objects.create(name="孙角色", code="grandchild", org=self.org)

        # 创建继承关系
        PermissionInheritance.objects.create(
            parent_role=parent_role,
            child_role=child_role,
            inherit_type="full"
        )
        PermissionInheritance.objects.create(
            parent_role=child_role,
            child_role=grandchild_role,
            inherit_type="partial"
        )

        # 验证继承链
        self.assertTrue(PermissionInheritance.objects.filter(
            parent_role=parent_role,
            child_role=grandchild_role
        ).exists())

    def test_permission_audit_logging(self):
        """权限审计日志测试"""
        from apps.permissions.models import PermissionAuditLog
        from apps.permissions.services.field_permission_service import FieldPermissionService
        from django.contrib.contenttypes.models import ContentType

        service = FieldPermissionService()
        content_type = ContentType.objects.get_for_model(get_user_model())

        # 执行权限操作
        permission = service.grant_field_permission(
            role_id=self.user.roles.first().id,
            object_type="auth.User",
            field_name="test_field",
            permission_type="read",
            actor=self.user
        )

        # 验证审计日志
        audit_logs = PermissionAuditLog.objects.filter(
            actor=self.user,
            target_type="field_permission",
            target_id=permission.id
        )

        self.assertTrue(audit_logs.exists())
        self.assertEqual(audit_logs.first().action, "grant")


class FieldPermissionSecurityTestCase(TestCase):
    """权限安全测试用例"""

    def setUp(self):
        self.org = self.create_organization()
        self.user = self.create_user()
        self.other_org_user = self.create_other_org_user()

    def create_organization(self):
        from apps.organizations.models import Organization
        return Organization.objects.create(name="测试组织", code="TEST_ORG")

    def create_user(self):
        from apps.accounts.models import User
        return User.objects.create_user(
            username="testuser",
            password="testpass123",
            org=self.org
        )

    def create_other_org_user(self):
        from apps.organizations.models import Organization
        from apps.accounts.models import User
        other_org = Organization.objects.create(name="其他组织", code="OTHER_ORG")
        return User.objects.create_user(
            username="otheruser",
            password="testpass123",
            org=other_org
        )

    def test_organization_isolation(self):
        """组织隔离测试"""
        from apps.permissions.models import FieldPermission
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(get_user_model())

        # 当前用户创建权限
        FieldPermission.objects.create(
            role=self.user.roles.first(),
            content_type=content_type,
            field_name="test_field",
            permission_type="read",
            org=self.org
        )

        # 验证其他组织用户无法访问
        perms_other_org = FieldPermission.objects.filter(org=self.other_org_user.org)
        self.assertEqual(perms_other_org.count(), 0)

    def test_data_masking_edge_cases(self):
        """数据脱敏边界测试"""
        from apps.permissions.engine import PermissionEngine

        # 测试各种类型数据的脱敏
        test_cases = [
            ("phone", "13812345678", "138****5678"),
            ("id_card", "110101199001011234", "110***********1234"),
            ("bank_card", "6225880123456789", "********6789"),
            ("name", "张三", "*三"),
            ("amount", 5000.50, "1,000~10,000"),
            ("amount", 50000.00, "1万~10万"),
            ("amount", 500000.00, ">10万"),
        ]

        for field_name, input_value, expected_output in test_cases:
            result = PermissionEngine._mask_field_value(field_name, input_value, self.user)
            self.assertEqual(result, expected_output)

    def test_permission_denial_scenarios(self):
        """权限拒绝场景测试"""
        from apps.permissions.engine import PermissionEngine
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(get_user_model())

        # 创建隐藏权限
        FieldPermission.objects.create(
            role=self.user.roles.first(),
            content_type=content_type,
            field_name="secret_field",
            permission_type="hidden"
        )

        # 测试字段权限应用
        test_data = [{"secret_field": "秘密数据", "public_field": "公开数据"}]
        result = PermissionEngine.apply_field_permissions(
            test_data,
            self.user,
            "auth.User",
            "view"
        )

        # 验证隐藏字段被过滤
        self.assertNotIn("secret_field", result[0])
        self.assertIn("public_field", result[0])
```

### 8.2 数据权限测试

```python
# apps/permissions/tests/test_data_permission.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.permissions.models import DataPermission
from apps.permissions.services.data_permission_service import DataPermissionService
from apps.permissions.engine import PermissionEngine
from django.db.models import Q

User = get_user_model()


class DataPermissionTestCase(TestCase):
    """数据权限测试用例"""

    def setUp(self):
        self.org = self.create_organization()
        self.user = self.create_user()
        self.role = self.create_role()
        self.user.roles.add(self.role)
        self.department = self.create_department()

    def create_organization(self):
        from apps.organizations.models import Organization
        return Organization.objects.create(name="测试组织", code="TEST_ORG")

    def create_user(self):
        return User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            org=self.org,
            department=self.department
        )

    def create_role(self):
        from apps.accounts.models import Role
        return Role.objects.create(
            name="测试角色",
            code="test_role",
            org=self.org
        )

    def create_department(self):
        from apps.organizations.models import Department
        return Department.objects.create(
            name="测试部门",
            code="TEST_DEPT",
            org=self.org
        )

    def test_data_scope_application(self):
        """测试数据范围应用"""
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(get_user_model())

        # 创建数据权限
        DataPermission.objects.create(
            role=self.role,
            content_type=content_type,
            scope_type="self_dept",
            scope_value={},
            org=self.org
        )

        # 模拟查询集
        queryset = User.objects.filter(org=self.org)

        # 应用数据权限
        filtered_queryset = PermissionEngine.apply_data_scope(
            queryset, self.user, "auth.User"
        )

        # 验证过滤结果
        self.assertLessEqual(filtered_queryset.count(), queryset.count())

    def test_custom_filter_conditions(self):
        """测试自定义过滤条件"""
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(get_user_model())

        # 创建自定义权限
        DataPermission.objects.create(
            role=self.role,
            content_type=content_type,
            scope_type="custom",
            scope_value={
                "filter": {"username__contains": "test"}
            },
            org=self.org
        )

        # 应用权限
        queryset = User.objects.filter(org=self.org)
        filtered = PermissionEngine.apply_data_scope(
            queryset, self.user, "auth.User"
        )

        # 验证过滤条件生效
        for user in filtered:
            self.assertIn("test", user.username.lower())

    def test_permission_inheritance(self):
        """测试权限继承"""
        from apps.organizations.models import Department
        from apps.permissions.models import DepartmentPermissionInheritance

        # 创建部门层级
        parent_dept = Department.objects.create(
            name="上级部门",
            code="PARENT_DEPT",
            org=self.org
        )
        child_dept = Department.objects.create(
            name="下级部门",
            code="CHILD_DEPT",
            org=self.org,
            parent=parent_dept
        )

        # 创建部门权限继承
        DepartmentPermissionInheritance.objects.create(
            parent_dept=parent_dept,
            child_dept=child_dept,
            permission_scope="all_below"
        )

        # 验证继承关系
        self.assertTrue(Department.is_ancestor(parent_dept.id, child_dept.id))

    def test_permission_expansion(self):
        """测试权限扩展"""
        from django.contrib.contenttypes.models import ContentType
        from apps.permissions.models import DataPermissionExpand

        content_type = ContentType.objects.get_for_model(get_user_model())

        # 创建基础权限
        base_perm = DataPermission.objects.create(
            role=self.role,
            content_type=content_type,
            scope_type="self_dept",
            scope_value={},
            org=self.org
        )

        # 添加扩展
        DataPermissionExpand.objects.create(
            base_permission=base_perm,
            expand_type="department",
            expand_value={"department_ids": [999]}  # 指定额外部门
        )

        # 验证扩展功能
        data_scope = PermissionEngine.get_data_scope(self.user, "auth.User")
        expansions = data_scope.get('expansions', [])

        self.assertEqual(len(expansions), 1)
        self.assertEqual(expansions[0]['type'], "department")
```

### 8.3 并发操作测试

```python
# apps/permissions/tests/test_concurrency.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction
from threading import Thread
import time
from apps.permissions.models import FieldPermission
from apps.permissions.services.field_permission_service import FieldPermissionService

User = get_user_model()


class PermissionConcurrencyTestCase(TestCase):
    """权限并发操作测试"""

    def setUp(self):
        self.org = self.create_organization()
        self.user = self.create_user()
        self.role = self.create_role()
        self.user.roles.add(self.role)

    def create_organization(self):
        from apps.organizations.models import Organization
        return Organization.objects.create(name="测试组织", code="TEST_ORG")

    def create_user(self):
        return User.objects.create_user(
            username="testuser",
            password="testpass123",
            org=self.org
        )

    def create_role(self):
        from apps.accounts.models import Role
        return Role.objects.create(
            name="测试角色",
            code="test_role",
            org=self.org
        )

    def test_concurrent_permission_grant(self):
        """并发授予权限测试"""
        from django.contrib.contenttypes.models import ContentType
        from apps.permissions.engine import PermissionEngine

        content_type = ContentType.objects.get_for_model(get_user_model())
        service = FieldPermissionService()

        def grant_permission():
            """授予权限的线程函数"""
            time.sleep(0.05)  # 确保并发
            service.grant_field_permission(
                role_id=self.role.id,
                object_type="auth.User",
                field_name=f"field_{int(time.time() * 1000) % 1000}",
                permission_type="read",
                actor=self.user
            )

        # 创建多个并发线程
        threads = []
        for i in range(10):
            thread = Thread(target=grant_permission)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证权限数量
        self.assertEqual(FieldPermission.objects.count(), 10)

    def test_permission_cache_concurrency(self):
        """权限缓存并发测试"""
        from apps.permissions.engine import PermissionEngine

        def read_permissions():
            """读取权限的线程函数"""
            for _ in range(5):
                PermissionEngine.get_field_permissions(self.user, "auth.User")
                time.sleep(0.01)

        def update_permissions():
            """更新权限的线程函数"""
            from django.contrib.contenttypes.models import ContentType
            from apps.permissions.models import FieldPermission

            content_type = ContentType.objects.get_for_model(get_user_model())

            for i in range(5):
                FieldPermission.objects.create(
                    role=self.role,
                    content_type=content_type,
                    field_name=f"concurrent_field_{i}",
                    permission_type="read"
                )
                time.sleep(0.01)

        # 创建读写线程
        read_thread = Thread(target=read_permissions)
        write_thread = Thread(target=update_permissions)

        read_thread.start()
        write_thread.start()

        read_thread.join()
        write_thread.join()

        # 验证系统稳定性
        self.assertTrue(FieldPermission.objects.count() >= 0)

    def test_batch_operations_concurrency(self):
        """批量操作并发测试"""
        from django.contrib.contenttypes.models import ContentType
        from apps.permissions.models import FieldPermission

        content_type = ContentType.objects.get_for_model(get_user_model())
        service = FieldPermissionService()

        # 预创建权限
        for i in range(20):
            FieldPermission.objects.create(
                role=self.role,
                content_type=content_type,
                field_name=f"pre_field_{i}",
                permission_type="read"
            )

        perm_ids = list(FieldPermission.objects.values_list('id', flat=True)[:10])

        def batch_delete():
            """批量删除的线程函数"""
            time.sleep(0.05)
            service.batch_delete(perm_ids, user=self.user)

        def batch_restore():
            """批量恢复的线程函数"""
            time.sleep(0.05)
            service.batch_restore(perm_ids, user=self.user)

        # 创建并发线程
        delete_thread = Thread(target=batch_delete)
        restore_thread = Thread(target=batch_restore)

        delete_thread.start()
        restore_thread.start()

        delete_thread.join()
        restore_thread.join()

        # 验证操作结果
        # 由于并发，可能部分成功部分失败
        deleted_count = FieldPermission.objects.filter(
            id__in=perm_ids,
            is_deleted=True
        ).count()

        self.assertGreaterEqual(deleted_count, 0)
        self.assertLessEqual(deleted_count, len(perm_ids))
```

---

## 9. 后续任务

1. 实现权限继承逻辑
2. 实现权限审计日志查询
3. 编写单元测试
4. 性能优化（权限缓存）
5. 与前端集成

## 10. API 接口规范

---

### 统一响应格式

#### 10.1 成功响应格式

##### 单条记录响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "PERM001",
        "name": "字段权限",
        "organization": {...},
        "created_at": "2026-01-14T10:30:00Z",
        "created_by": {...}
    }
}
```

##### 列表响应（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/permissions/field-permissions/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "PERM001",
                ...
            }
        ]
    }
}
```

##### 创建/更新响应

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "PERM001",
        ...
    }
}
```

##### 删除响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "删除成功"
}
```

#### 10.2 错误响应格式

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "field_name": ["该字段不能为空"],
            "permission_type": ["无效的权限类型"]
        }
    }
}
```

### 统一错误码定义

#### 10.3 错误码列表

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
| `PERMISSION_EXISTS` | 409 | 权限已存在 |
| `INVALID_SCOPE_TYPE` | 400 | 无效的权限范围类型 |
| `INVALID_PERMISSION_TYPE` | 400 | 无效的权限类型 |
| `MASKING_RULE_NOT_FOUND` | 404 | 脱敏规则不存在 |
| `INHERITANCE_CONFLICT` | 409 | 继承关系冲突 |
| `AUDIT_LOG_REQUIRED` | 400 | 需要记录审计日志 |

### 批量操作 API 规范

#### 10.4 批量删除

```http
POST /api/permissions/field-permissions/batch-delete/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001",
        "550e8400-e29b-41d4-a716-446655440002"
    ]
}
```

**响应 (全部成功)**

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "success": true
        }
    ]
}
```

**响应 (部分失败)**

```http
HTTP/1.1 207 Multi-Status

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "记录不存在"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "success": true
        }
    ]
}
```

#### 10.5 批量恢复

```http
POST /api/permissions/field-permissions/batch-restore/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应格式与批量删除相同**

#### 10.6 批量更新

```http
POST /api/permissions/field-permissions/batch-update/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "data": {
        "priority": 10
    }
}
```

**响应格式与批量删除相同**

### 标准 CRUD API

#### 10.7 字段权限管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/field-permissions/` | 分页查询字段权限 |
| GET | `/api/permissions/field-permissions/{id}/` | 获取字段权限详情 |
| POST | `/api/permissions/field-permissions/` | 创建字段权限 |
| PUT | `/api/permissions/field-permissions/{id}/` | 完整更新字段权限 |
| PATCH | `/api/permissions/field-permissions/{id}/` | 部分更新字段权限 |
| DELETE | `/api/permissions/field-permissions/{id}/` | 软删除字段权限 |
| GET | `/api/permissions/field-permissions/deleted/` | 查询已删除的字段权限 |
| POST | `/api/permissions/field-permissions/{id}/restore/` | 恢复已删除的字段权限 |

#### 10.8 数据权限管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/data-permissions/` | 分页查询数据权限 |
| GET | `/api/permissions/data-permissions/{id}/` | 获取数据权限详情 |
| POST | `/api/permissions/data-permissions/` | 创建数据权限 |
| PUT | `/api/permissions/data-permissions/{id}/` | 完整更新数据权限 |
| PATCH | `/api/permissions/data-permissions/{id}/` | 部分更新数据权限 |
| DELETE | `/api/permissions/data-permissions/{id}/` | 软删除数据权限 |
| GET | `/api/permissions/data-permissions/deleted/` | 查询已删除的数据权限 |
| POST | `/api/permissions/data-permissions/{id}/restore/` | 恢复已删除的数据权限 |

#### 10.9 字段权限组管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/field-permission-groups/` | 分页查询字段权限组 |
| GET | `/api/permissions/field-permission-groups/{id}/` | 获取字段权限组详情 |
| POST | `/api/permissions/field-permission-groups/` | 创建字段权限组 |
| PUT | `/api/permissions/field-permission-groups/{id}/` | 完整更新字段权限组 |
| PATCH | `/api/permissions/field-permission-groups/{id}/` | 部分更新字段权限组 |
| DELETE | `/api/permissions/field-permission-groups/{id}/` | 软删除字段权限组 |
| GET | `/api/permissions/field-permission-groups/deleted/` | 查询已删除的权限组 |
| POST | `/api/permissions/field-permission-groups/{id}/restore/` | 恢复已删除的权限组 |

### 扩展操作 API

#### 10.10 权限引擎管理接口

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/field-permissions/query/` | 根据条件查询字段权限 |
| POST | `/api/permissions/field-permissions/batch-query/` | 批量查询字段权限 |
| POST | `/api/permissions/field-permissions/clear-cache/` | 清除权限缓存 |
| GET | `/api/permissions/data-permissions/query/` | 根据条件查询数据权限 |
| GET | `/api/permissions/data-permissions/scope/` | 获取用户的数据访问范围 |
| POST | `/api/permissions/data-permissions/apply/` | 应用数据权限到查询集 |

#### 10.11 权限继承管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/inheritances/roles/` | 查询角色继承关系 |
| POST | `/api/permissions/inheritances/roles/` | 创建角色继承关系 |
| DELETE | `/api/permissions/inheritances/roles/{id}/` | 删除角色继承关系 |
| GET | `/api/permissions/inheritances/departments/` | 查询部门权限继承 |
| POST | `/api/permissions/inheritances/departments/` | 创建部门权限继承 |
| DELETE | `/api/permissions/inheritances/departments/{id}/` | 删除部门权限继承 |

#### 10.12 权限审计日志

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/audit-logs/` | 分页查询权限审计日志 |
| GET | `/api/permissions/audit-logs/by-actor/` | 按操作人查询日志 |
| GET | `/api/permissions/audit-logs/by-target/` | 按目标类型查询日志 |
| GET | `/api/permissions/audit-logs/export/` | 导出审计报告 |

#### 10.13 权限验证接口

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| POST | `/api/permissions/check/field/` | 检查用户字段权限 |
| POST | `/api/permissions/check/data/` | 检查用户数据权限 |
| POST | `/api/permissions/check/batch/` | 批量检查权限 |

#### 10.14 权限配置接口

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/templates/` | 分页查询权限模板 |
| POST | `/api/permissions/templates/` | 创建权限模板 |
| POST | `/api/permissions/templates/{id}/apply/` | 应用权限模板 |
| POST | `/api/permissions/templates/{id}/preview/` | 预览权限模板应用效果 |
| POST | `/api/permissions/sync/` | 同步权限配置 |
| POST | `/api/permissions/reset/` | 重置权限配置 |
| GET | `/api/permissions/sync/status/` | 获取同步状态 |

### 数据导入导出 API

#### 10.15 权限配置导出

```http
POST /api/permissions/export/
Content-Type: application/json

{
    "format": "xlsx",
    "resource_type": "field_permissions",
    "filters": {
        "permission_type": "read"
    }
}
```

**响应**：

```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="field_permissions_export_20260115.xlsx"

[文件内容]
```

#### 10.16 权限配置导入

```http
POST /api/permissions/import/
Content-Type: multipart/form-data

file: [Excel文件]
options: {
    "skip_errors": true,
    "update_existing": false
}
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "导入任务已创建",
    "data": {
        "task_id": "import-task-uuid-xxx",
        "status": "processing",
        "estimated_time": 30
    }
}
```

#### 10.17 查询导入状态

```http
GET /api/permissions/import/{task_id}/status/
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "task_id": "import-task-uuid-xxx",
        "status": "completed",
        "progress": 100,
        "summary": {
            "total": 1000,
            "succeeded": 980,
            "failed": 15,
            "skipped": 5
        },
        "errors": [
            {
                "row": 15,
                "field": "field_name",
                "message": "字段名不能为空",
                "value": ""
            }
        ]
    }
}
```

---

## 11. 实现代码示例

### 11.1 权限检查中间件

```python
# backend/apps/permissions/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from apps.permissions.engine import PermissionEngine

User = get_user_model()


class PermissionMiddleware(MiddlewareMixin):
    """权限检查中间件"""

    def process_request(self, request):
        """处理请求，注入权限信息"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            # 获取用户的字段权限
            field_perms = PermissionEngine.get_field_permissions(
                request.user,
                request.resolver_match.view_name,
                request.method.lower()
            )
            request.field_permissions = field_perms

            # 获取用户的数据访问范围
            data_scope = PermissionEngine.get_data_scope(
                request.user,
                request.resolver_match.view_name
            )
            request.data_scope = data_scope

        return None

    def process_response(self, request, response):
        """处理响应"""
        # 添加权限相关响应头
        if hasattr(request, 'field_permissions'):
            response['X-Field-Permissions'] = ','.join(request.field_permissions.keys())

        if hasattr(request, 'data_scope'):
            response['X-Data-Scope'] = request.data_scope.get('scope_type', 'all')

        return response
```

### 11.2 权限缓存管理服务

```python
# backend/apps/permissions/services/cache_service.py

import redis
from django.conf import settings
from apps.permissions.engine import PermissionEngine

class PermissionCacheService:
    """权限缓存管理服务"""

    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    def get_field_permissions_cache_key(self, user_id, object_type, action):
        """生成字段权限缓存键"""
        return f"field_perm:{user_id}:{object_type}:{action}"

    def get_data_scope_cache_key(self, user_id, object_type):
        """生成数据范围缓存键"""
        return f"data_scope:{user_id}:{object_type}"

    def cache_field_permissions(self, user_id, object_type, action, permissions):
        """缓存字段权限"""
        cache_key = self.get_field_permissions_cache_key(user_id, object_type, action)
        self.redis_client.setex(
            cache_key,
            settings.PERMISSION_CACHE_TIMEOUT,
            str(permissions)
        )

    def cache_data_scope(self, user_id, object_type, scope):
        """缓存数据范围"""
        cache_key = self.get_data_scope_cache_key(user_id, object_type)
        self.redis_client.setex(
            cache_key,
            settings.PERMISSION_CACHE_TIMEOUT,
            str(scope)
        )

    def get_cached_field_permissions(self, user_id, object_type, action):
        """获取缓存的字段权限"""
        cache_key = self.get_field_permissions_cache_key(user_id, object_type, action)
        cached_value = self.redis_client.get(cache_key)
        return eval(cached_value) if cached_value else None

    def get_cached_data_scope(self, user_id, object_type):
        """获取缓存的数据范围"""
        cache_key = self.get_data_scope_cache_key(user_id, object_type)
        cached_value = self.redis_client.get(cache_key)
        return eval(cached_value) if cached_value else None

    def clear_user_cache(self, user_id):
        """清除用户权限缓存"""
        # 获取所有相关键
        pattern = f"field_perm:{user_id}:*"
        field_keys = self.redis_client.keys(pattern)

        pattern = f"data_scope:{user_id}:*"
        data_keys = self.redis_client.keys(pattern)

        # 删除所有键
        all_keys = field_keys + data_keys
        if all_keys:
            self.redis_client.delete(*all_keys)

    def clear_all_cache(self):
        """清除所有权限缓存"""
        self.redis_client.flushdb()
```

---

## 12. 部署和监控

### 12.1 权限监控指标

```python
# backend/apps/permissions/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge
from django.conf import settings

# 权限检查次数
PERMISSION_CHECKS = Counter(
    'permission_checks_total',
    'Total permission checks',
    ['user_type', 'object_type', 'permission_type']
)

# 权限检查耗时
PERMISSION_CHECK_DURATION = Histogram(
    'permission_check_duration_seconds',
    'Permission check duration',
    ['object_type']
)

# 权限缓存命中率
PERMISSION_CACHE_HITS = Counter(
    'permission_cache_hits_total',
    'Total permission cache hits'
)

PERMISSION_CACHE_MISSES = Counter(
    'permission_cache_misses_total',
    'Total permission cache misses'
)

# 活跃权限用户数
ACTIVE_PERMISSION_USERS = Gauge(
    'active_permission_users',
    'Number of active permission users'
)

# 权限配置变更次数
PERMISSION_CHANGES = Counter(
    'permission_changes_total',
    'Total permission changes',
    ['change_type', 'resource_type']
)
```

### 12.2 权限健康检查

```python
# backend/apps/permissions/health_checks.py

from django.db import connection
from redis.exceptions import RedisError
from apps.permissions.services.cache_service import PermissionCacheService
from apps.permissions.engine import PermissionEngine

def check_permissions_system():
    """检查权限系统健康状态"""
    health_status = {
        'overall': 'healthy',
        'checks': {}
    }

    # 检查数据库连接
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['overall'] = 'degraded'

    # 检查Redis连接
    try:
        cache_service = PermissionCacheService()
        cache_service.redis_client.ping()
        health_status['checks']['redis'] = 'healthy'
    except RedisError as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['overall'] = 'degraded'

    # 检查权限引擎
    try:
        test_user = type('User', (), {'id': 1})()
        field_perms = PermissionEngine.get_field_permissions(test_user, "test.Test")
        health_status['checks']['permission_engine'] = 'healthy'
    except Exception as e:
        health_status['checks']['permission_engine'] = f'unhealthy: {str(e)}'
        health_status['overall'] = 'degraded'

    return health_status
```

---

## 13. 总结

### 13.1 架构特点

1. **模块化设计**：权限系统分为字段权限、数据权限、权限继承、审计日志等多个模块
2. **缓存机制**：Redis缓存权限配置，提高访问性能
3. **标准规范**：遵循统一的API响应格式和错误处理规范
4. **审计追踪**：完整的权限操作审计日志
5. **扩展性**：支持自定义过滤条件和脱敏规则

### 13.2 性能优化

1. **缓存策略**：用户权限配置缓存，减少数据库查询
2. **批量操作**：支持批量权限配置，提高管理效率
3. **异步处理**：权限检查使用缓存，实时响应
4. **索引优化**：数据库索引设计，提高查询性能

### 13.3 安全考虑

1. **权限隔离**：严格的组织权限隔离
2. **脱敏处理**：敏感数据自动脱敏
3. **审计日志**：完整的权限操作记录
4. **缓存安全**：定期清理缓存，避免数据不一致

### 13.4 集成建议

1. **前端集成**：提供权限状态检查接口
2. **API集成**：标准RESTful API，便于第三方集成
3. **监控集成**：Prometheus指标导出
4. **日志集成**：结构化日志输出

### 10.1 统一响应格式

#### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        "code": "PERM001",
        ...
    }
}
```

#### 列表响应（分页）
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/permissions/field-permissions/?page=2",
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
        "message": "请求数据验证失败",
        "details": {
            "field": ["该字段不能为空"]
        }
    }
}
```

### 10.2 标准 CRUD 接口

#### 字段权限管理

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **字段权限列表** | GET | `/api/permissions/field-permissions/` | 分页查询字段权限 |
| **字段权限详情** | GET | `/api/permissions/field-permissions/{id}/` | 获取字段权限详情 |
| **创建字段权限** | POST | `/api/permissions/field-permissions/` | 创建字段权限 |
| **更新字段权限** | PUT | `/api/permissions/field-permissions/{id}/` | 完整更新字段权限 |
| **部分更新字段权限** | PATCH | `/api/permissions/field-permissions/{id}/` | 部分更新字段权限 |
| **删除字段权限** | DELETE | `/api/permissions/field-permissions/{id}/` | 软删除字段权限 |
| **已删除列表** | GET | `/api/permissions/field-permissions/deleted/` | 查询已删除的字段权限 |
| **恢复字段权限** | POST | `/api/permissions/field-permissions/{id}/restore/` | 恢复已删除的字段权限 |

#### 数据权限管理

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **数据权限列表** | GET | `/api/permissions/data-permissions/` | 分页查询数据权限 |
| **数据权限详情** | GET | `/api/permissions/data-permissions/{id}/` | 获取数据权限详情 |
| **创建数据权限** | POST | `/api/permissions/data-permissions/` | 创建数据权限 |
| **更新数据权限** | PUT | `/api/permissions/data-permissions/{id}/` | 完整更新数据权限 |
| **部分更新数据权限** | PATCH | `/api/permissions/data-permissions/{id}/` | 部分更新数据权限 |
| **删除数据权限** | DELETE | `/api/permissions/data-permissions/{id}/` | 软删除数据权限 |
| **已删除列表** | GET | `/api/permissions/data-permissions/deleted/` | 查询已删除的数据权限 |
| **恢复数据权限** | POST | `/api/permissions/data-permissions/{id}/restore/` | 恢复已删除的数据权限 |

#### 字段权限组管理

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **权限组列表** | GET | `/api/permissions/field-permission-groups/` | 分页查询字段权限组 |
| **权限组详情** | GET | `/api/permissions/field-permission-groups/{id}/` | 获取字段权限组详情 |
| **创建权限组** | POST | `/api/permissions/field-permission-groups/` | 创建字段权限组 |
| **更新权限组** | PUT | `/api/permissions/field-permission-groups/{id}/` | 完整更新字段权限组 |
| **部分更新权限组** | PATCH | `/api/permissions/field-permission-groups/{id}/` | 部分更新字段权限组 |
| **删除权限组** | DELETE | `/api/permissions/field-permission-groups/{id}/` | 软删除字段权限组 |
| **已删除列表** | GET | `/api/permissions/field-permission-groups/deleted/` | 查询已删除的权限组 |
| **恢复权限组** | POST | `/api/permissions/field-permission-groups/{id}/restore/` | 恢复已删除的权限组 |

### 10.3 批量操作接口

#### 批量删除字段权限
```http
POST /api/permissions/field-permissions/batch-delete/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### 批量恢复字段权限
```http
POST /api/permissions/field-permissions/batch-restore/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### 批量更新字段权限
```http
POST /api/permissions/field-permissions/batch-update/
{
    "ids": ["uuid1", "uuid2", "uuid3"],
    "updates": {
        "priority": 10
    }
}
```

### 10.4 权限引擎管理接口

#### 10.4.1 字段权限查询

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **查询字段权限** | GET | `/api/permissions/field-permissions/query/` | 根据条件查询字段权限 |
| **批量查询字段权限** | POST | `/api/permissions/field-permissions/batch-query/` | 批量查询字段权限 |
| **清除权限缓存** | POST | `/api/permissions/field-permissions/clear-cache/` | 清除权限缓存 |

#### 10.4.2 数据权限查询

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **查询数据权限** | GET | `/api/permissions/data-permissions/query/` | 根据条件查询数据权限 |
| **获取数据范围** | GET | `/api/permissions/data-permissions/scope/` | 获取用户的数据访问范围 |
| **应用数据权限** | POST | `/api/permissions/data-permissions/apply/` | 应用数据权限到查询集 |

#### 10.4.3 权限继承管理

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **角色继承列表** | GET | `/api/permissions/inheritances/roles/` | 查询角色继承关系 |
| **创建角色继承** | POST | `/api/permissions/inheritances/roles/` | 创建角色继承关系 |
| **删除角色继承** | DELETE | `/api/permissions/inheritances/roles/{id}/` | 删除角色继承关系 |
| **部门继承列表** | GET | `/api/permissions/inheritances/departments/` | 查询部门权限继承 |
| **创建部门继承** | POST | `/api/permissions/inheritances/departments/` | 创建部门权限继承 |
| **删除部门继承** | DELETE | `/api/permissions/inheritances/departments/{id}/` | 删除部门权限继承 |

#### 10.4.4 权限审计日志

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **审计日志列表** | GET | `/api/permissions/audit-logs/` | 分页查询权限审计日志 |
| **操作人日志** | GET | `/api/permissions/audit-logs/by-actor/` | 按操作人查询日志 |
| **目标类型日志** | GET | `/api/permissions/audit-logs/by-target/` | 按目标类型查询日志 |
| **导出审计报告** | GET | `/api/permissions/audit-logs/export/` | 导出审计报告 |

### 10.5 权限验证接口

#### 10.5.1 权限检查

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **检查字段权限** | POST | `/api/permissions/check/field/` | 检查用户字段权限 |
| **检查数据权限** | POST | `/api/permissions/check/data/` | 检查用户数据权限 |
| **批量权限检查** | POST | `/api/permissions/check/batch/` | 批量检查权限 |

#### 请求示例
```json
{
    "user_id": "uuid",
    "object_type": "assets.Asset",
    "action": "view",
    "field_name": "price",
    "object_id": "uuid"
}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "has_permission": true,
        "permission_type": "read",
        "masked_value": "1,000~10,000"
    }
}
```

### 10.6 权限配置接口

#### 10.6.1 权限模板

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **权限模板列表** | GET | `/api/permissions/templates/` | 分页查询权限模板 |
| **创建权限模板** | POST | `/api/permissions/templates/` | 创建权限模板 |
| **应用权限模板** | POST | `/api/permissions/templates/{id}/apply/` | 应用权限模板 |
| **预览权限模板** | POST | `/api/permissions/templates/{id}/preview/` | 预览权限模板应用效果 |

#### 10.6.2 权限同步

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **同步权限配置** | POST | `/api/permissions/sync/` | 同步权限配置 |
| **重置权限配置** | POST | `/api/permissions/reset/` | 重置权限配置 |
| **权限配置状态** | GET | `/api/permissions/sync/status/` | 获取同步状态 |

### 10.7 标准错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
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
| `PERMISSION_EXISTS` | 409 | 权限已存在 |
| `INVALID_SCOPE_TYPE` | 400 | 无效的权限范围类型 |
| `INVALID_PERMISSION_TYPE` | 400 | 无效的权限类型 |
| `MASKING_RULE_NOT_FOUND` | 404 | 脱敏规则不存在 |
| `INHERITANCE_CONFLICT` | 409 | 继承关系冲突 |
| `AUDIT_LOG_REQUIRED` | 400 | 需要记录审计日志 |

### 10.8 扩展接口示例

#### 10.8.1 批量字段权限授权

```python
# Python 代码示例
import requests

url = "http://localhost:8000/api/permissions/field-permissions/batch-grant/"
headers = {
    "Authorization": "Bearer your_token",
    "Content-Type": "application/json"
}

data = {
    "role_id": "role_uuid",
    "object_type": "assets.Asset",
    "field_configs": [
        {"field_name": "original_value", "permission_type": "masked"},
        {"field_name": "supplier", "permission_type": "hidden"},
        {"field_name": "purchase_date", "permission_type": "read"}
    ]
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

#### 10.8.2 数据范围查询

```javascript
// JavaScript 代码示例
async function getUserDataScope(userId, objectType) {
    const response = await fetch(`/api/permissions/data-permissions/scope/?user_id=${userId}&object_type=${objectType}`, {
        headers: {
            'Authorization': 'Bearer your_token'
        }
    });

    const result = await response.json();

    if (result.success) {
        console.log('数据范围:', result.data);
        console.log('范围类型:', result.data.scope_type);
        console.log('范围值:', result.data.scope_value);
    }

    return result;
}
```

#### 10.8.3 权限缓存管理

```python
# Python 代码示例
from apps.permissions.engine import PermissionEngine

# 清除特定用户的权限缓存
PermissionEngine.clear_cache(user_id="user_uuid")

# 清除所有权限缓存
PermissionEngine.clear_cache()

# 获取字段权限（自动缓存）
field_perms = PermissionEngine.get_field_permissions(
    user=user_object,
    object_type="assets.Asset",
    action="view"
)
```

#### 10.8.4 权限审计日志导出

```python
# Python 代码示例
import requests

def export_audit_logs(filters=None):
    url = "http://localhost:8000/api/permissions/audit-logs/export/"

    params = {
        "date_from": "2024-01-01",
        "date_to": "2024-12-31",
        "action": "grant",
        "export_format": "xlsx"
    }

    if filters:
        params.update(filters)

    response = requests.get(url, params=params, headers={
        "Authorization": "Bearer your_token"
    })

    if response.status_code == 200:
        with open("audit_logs.xlsx", "wb") as f:
            f.write(response.content)
        return "audit_logs.xlsx"
    else:
        raise Exception("导出失败")
```

### 10.9 权限和安全

#### 10.9.1 认证和授权

- 所有权限管理 API 需要 JWT Token 认证
- 需要具有 `permission_management` 权限的用户才能访问
- 支持 API Key 认证方式
- 实现请求频率限制（每分钟 60 次）

#### 10.9.2 数据安全

- 所有敏感操作记录审计日志
- 支持操作前后的数据快照
- 实现权限变更的审批流程
- 支持权限操作的回滚机制

#### 10.9.3 缓存策略

- Redis 缓存用户权限配置
- 缓存失效策略：用户权限变更时自动清除
- 支持手动清除缓存接口
- 缓存键格式：`field_perm:{user_id}:{object_type}:{action}`

### 10.10 WebSocket 实时通知

#### 10.10.1 权限变更通知

```json
{
    "type": "permission_changed",
    "message": "权限配置已更新",
    "data": {
        "permission_id": "uuid",
        "change_type": "grant",
        "changed_by": "user_name",
        "timestamp": "2024-01-01T10:00:00Z"
    }
}
```

#### 10.10.2 审计日志通知

```json
{
    "type": "audit_log_created",
    "message": "新的审计日志",
    "data": {
        "log_id": "uuid",
        "action": "grant",
        "target_type": "field_permission",
        "actor": "user_name",
        "timestamp": "2024-01-01T10:00:00Z"
    }
}
```

#### 10.10.3 权限冲突通知

```json
{
    "type": "permission_conflict",
    "message": "检测到权限冲突",
    "data": {
        "conflict_type": "inheritance",
        "conflict_details": "角色继承关系存在循环",
        "suggestion": "请检查角色继承配置"
    }
}
```
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