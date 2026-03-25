# Common Base Features: 后端实现

## 任务概述

实现基于 BaseModel 的公共基类，为所有业务模块提供统一的序列化、视图、服务和过滤能力。

---

## 后端基础模型定义

### BaseModel 字段定义

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| organization | ForeignKey | NOT NULL | 关联组织 |
| is_deleted | boolean | default=False | 软删除标记 |
| deleted_at | datetime | nullable | 删除时间 |
| created_at | datetime | auto_now_add | 创建时间 |
| updated_at | datetime | auto_now | 更新时间 |
| created_by | ForeignKey | nullable | 创建人 |
| custom_fields | JSONB | default={} | 动态字段 |

### BaseModelSerializer 自动序列化字段

| 字段 | 说明 | 来源 |
|------|------|------|
| id | 主键ID | BaseModel |
| organization | 组织信息 | 嵌套 OrganizationSerializer |
| is_deleted | 软删除标记 | BaseModel |
| deleted_at | 删除时间 | BaseModel |
| created_at | 创建时间 | BaseModel |
| updated_at | 更新时间 | BaseModel |
| created_by | 创建人信息 | 嵌套 UserSerializer |
| custom_fields | 动态字段 | BaseModel JSONB |

### BaseModelViewSet 自动实现方法

| 方法 | 功能 | 自动处理 |
|------|------|---------|
| get_queryset() | 查询过滤 | 软删除过滤 + 组织隔离 |
| perform_create() | 创建钩子 | 自动设置 organization_id, created_by |
| perform_update() | 更新钩子 | 自动设置 updated_by |
| perform_destroy() | 删除钩子 | 调用 soft_delete() 软删除 |
| deleted() | 查询已删除 | GET /{resource}/deleted/ |
| restore() | 恢复记录 | POST /{resource}/{id}/restore/ |
| batch_delete() | 批量删除 | POST /{resource}/batch-delete/ |
| batch_restore() | 批量恢复 | POST /{resource}/batch-restore/ |
| batch_update() | 批量更新 | POST /{resource}/batch-update/ |

### BaseCRUDService 自动实现方法

| 方法 | 说明 | 自动处理 |
|------|------|---------|
| create(data, user, **kwargs) | 创建记录 | organization_id, created_by_id |
| update(instance_id, data, user) | 更新记录 | 组织隔离验证 |
| delete(instance_id, user) | 软删除记录 | 调用 soft_delete() |
| restore(instance_id) | 恢复记录 | 使用 all_objects 查询 |
| get(instance_id, allow_deleted) | 获取单条 | 组织隔离验证 |
| query(filters, search, order_by) | 复杂查询 | 支持过滤、搜索、排序 |
| paginate(queryset, page, page_size) | 分页查询 | 返回标准分页格式 |
| batch_delete(ids, user) | 批量删除 | 返回详细结果统计 |

### BaseModelFilter 自动支持过滤字段

| 过滤字段 | 类型 | 说明 |
|---------|------|------|
| created_at | DateFromToRangeFilter | 创建时间范围 |
| created_at_from | DateTimeFilter (gte) | 创建时间起始 |
| created_at_to | DateTimeFilter (lte) | 创建时间结束 |
| updated_at_from | DateTimeFilter (gte) | 更新时间起始 |
| updated_at_to | DateTimeFilter (lte) | 更新时间结束 |
| created_by | UUIDFilter | 创建人ID |
| is_deleted | BooleanFilter | 是否已删除 |

---

## 1. 文件结构

```
backend/apps/common/
├── serializers/
│   ├── __init__.py
│   └── base.py                 # BaseModelSerializer
├── viewsets/
│   ├── __init__.py
│   └── base.py                 # BaseModelViewSet + BatchOperationMixin
├── services/
│   ├── __init__.py
│   ├── base_crud.py            # BaseCRUDService
│   └── organization_service.py # BaseOrganizationService
├── middleware/
│   ├── __init__.py
│   └── organization_middleware.py # OrganizationMiddleware
├── utils/
│   ├── __init__.py
│   └── organization.py         # 组织工具函数和装饰器
├── filters/
│   ├── __init__.py
│   └── base.py                 # BaseModelFilter
├── permissions/
│   ├── __init__.py
│   ├── base.py                 # BasePermission
│   └── decorators.py           # 权限装饰器
├── mixins/
│   ├── __init__.py
│   └── cache.py                # BaseCacheMixin
├── responses/
│   ├── __init__.py
│   └── base.py                 # BaseResponse
├── handlers/
│   ├── __init__.py
│   └── exceptions.py           # BaseExceptionHandler
└── models.py                   # 已有 BaseModel
```

---

## 2. BaseModelSerializer

### 2.1 设计目标

- 自动序列化 BaseModel 的公共字段
- 自动处理 custom_fields 动态字段
- 统一审计字段的用户信息输出

### 2.2 BaseModelSerializer

| 功能 | 说明 |
|------|------|
| **自动序列化公共字段** | id, organization, is_deleted, deleted_at, created_at, updated_at, created_by |
| **custom_fields处理** | 自动序列化JSONB动态字段 |
| **嵌套序列化** | organization → OrganizationSerializer, created_by → UserSerializer |
| **字段展开** | 支持通过 `flatten_custom_fields=True` 将custom_fields展开到顶层 |

### 2.3 BaseModelWithAuditSerializer

| 扩展字段 | 说明 |
|---------|------|
| `updated_by` | 更新人信息（嵌套UserSerializer） |
| `deleted_by` | 删除人信息（嵌套UserSerializer） |

### 2.4 BaseListSerializer

| 功能 | 说明 |
|------|------|
| 分页处理 | 自动识别Page对象并返回标准分页格式 |
| 元数据 | 自动添加count, next, previous字段 |

### 2.5 使用示例

```python
# apps/assets/serializers.py
from apps.common.serializers.base import BaseModelSerializer

class AssetSerializer(BaseModelSerializer):
    """资产序列化器 - 自动继承所有公共字段"""

    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name', 'category', 'status']
```

---

## 3. BaseModelViewSet

### 3.1 设计目标

- 自动应用组织过滤和软删除过滤
- 自动设置审计字段（创建人、更新人）
- 自动使用软删除而非物理删除
- 提供统一的批量操作接口

### 3.2 BaseModelViewSet

| 方法 | 功能 | 说明 |
|------|------|------|
| `get_queryset()` | 自动过滤 | 软删除过滤 + 组织隔离 |
| `perform_create()` | 创建钩子 | 自动设置 organization_id, created_by |
| `perform_update()` | 更新钩子 | 自动设置 updated_by |
| `perform_destroy()` | 删除钩子 | 调用 `soft_delete()` 而非物理删除 |
| `deleted()` | 查询已删除 | `GET /{resource}/deleted/` |
| `restore()` | 恢复记录 | `POST /{resource}/{id}/restore/` |

### 3.3 BatchOperationMixin

| 方法 | 端点 | 说明 |
|------|------|------|
| `batch_delete()` | `POST /{resource}/batch-delete/` | 批量软删除 |
| `batch_restore()` | `POST /{resource}/batch-restore/` | 批量恢复 |
| `batch_update()` | `POST /{resource}/batch-update/` | 批量更新 |

**批量操作响应格式**:
```json
{
    "success": true,
    "message": "批量删除完成",
    "summary": {"total": 3, "succeeded": 3, "failed": 0},
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": true}
    ]
}
```

### 3.4 BaseModelViewSetWithBatch

| 继承 | 说明 |
|------|------|
| `BatchOperationMixin` + `BaseModelViewSet` | 包含完整批量操作的ViewSet基类 |

### 3.5 使用示例

```python
# apps/assets/views.py
from apps.common.viewsets.base import BaseModelViewSetWithBatch

class AssetViewSet(BaseModelViewSetWithBatch):
    """资产 ViewSet - 自动获得所有公共功能"""
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
```

---

## 4. BaseCRUDService

### 4.1 设计目标

- 提供统一的 CRUD 操作方法
- 自动处理组织隔离和软删除
- 支持复杂查询场景
- 可被各模块 Service 继承

### 4.2 BaseCRUDService

| 方法 | 说明 | 自动处理 |
|------|------|---------|
| `create(data, user, **kwargs)` | 创建记录 | organization_id, created_by_id |
| `update(instance_id, data, user)` | 更新记录 | 组织隔离验证 |
| `delete(instance_id, user)` | 软删除记录 | 调用 `soft_delete()` |
| `restore(instance_id)` | 恢复记录 | 使用 `all_objects` 查询 |
| `get(instance_id, allow_deleted)` | 获取单条 | 组织隔离验证 |
| `query(filters, search, order_by)` | 复杂查询 | 支持过滤、搜索、排序 |
| `paginate(queryset, page, page_size)` | 分页查询 | 返回标准分页格式 |
| `batch_delete(ids, user)` | 批量删除 | 返回详细结果统计 |

### 4.3 使用示例

```python
# apps/assets/services/asset_service.py
from apps.common.services.base_crud import BaseCRUDService

class AssetService(BaseCRUDService):
    """资产服务 - 继承 CRUD 基类"""

    def __init__(self):
        super().__init__(Asset)

    def get_by_code(self, code: str):
        """根据编码查询资产"""
        return self.model_class.objects.get(code=code)
```

---

## 5. BaseModelFilter

### 5.1 设计目标

- 提供公共字段过滤
- 支持时间范围查询
- 支持用户过滤
- 支持组织过滤

### 5.2 BaseModelFilter

| 过滤字段 | 类型 | 说明 |
|---------|------|------|
| `created_at` | `DateFromToRangeFilter` | 创建时间范围 |
| `created_at_from` | `DateTimeFilter` (gte) | 创建时间起始 |
| `created_at_to` | `DateTimeFilter` (lte) | 创建时间结束 |
| `updated_at_from` | `DateTimeFilter` (gte) | 更新时间起始 |
| `updated_at_to` | `DateTimeFilter` (lte) | 更新时间结束 |
| `created_by` | `UUIDFilter` | 创建人ID |
| `is_deleted` | `BooleanFilter` | 是否已删除 |

### 5.3 使用示例

```python
# apps/assets/filters.py

from apps.common.filters.base import BaseModelFilter
from apps.assets.models import Asset

class AssetFilter(BaseModelFilter):
    """资产过滤器 - 自动继承公共过滤字段"""

    # 额外业务字段过滤
    code = filters.CharFilter(lookup_expr='icontains', label='资产编码')
    name = filters.CharFilter(lookup_expr='icontains', label='资产名称')
    status = filters.ChoiceFilter(choices=Asset.Status.choices, label='状态')
    category = filters.UUIDFilter(field_name='category_id', label='分类')

    class Meta(BaseModelFilter.Meta):
        model = Asset
        # 继承公共字段 + 业务字段
        fields = BaseModelFilter.Meta.fields + [
            'code', 'name', 'status', 'category'
        ]
```

---

## 6. BaseOrganizationService - 多组织公共处理服务

### 6.1 设计目标

- 统一多组织数据隔离逻辑处理
- 提供组织上下文管理（获取/设置/清除）
- 支持组织树操作（祖先/子孙/完整路径）
- 提供按组织过滤查询集的统一方法
- 支持跨组织权限检查
- 支持组织切换功能
- 提供组织相关工具函数和装饰器

### 6.2 文件结构

```
backend/apps/common/
├── services/
│   ├── __init__.py
│   ├── base_crud.py               # BaseCRUDService (已有)
│   └── organization_service.py    # BaseOrganizationService (新增)
├── middleware/
│   ├── __init__.py
│   └── organization_middleware.py # OrganizationMiddleware (新增)
└── utils/
    ├── __init__.py
    └── organization.py            # 组织工具函数 (新增)
```

### 6.3 BaseOrganizationService

| 方法 | 说明 |
|------|------|
| **组织上下文** | |
| `get_current_organization_id()` | 获取当前组织ID |
| `set_organization_context(org_id)` | 设置组织上下文 |
| `clear_organization_context()` | 清除组织上下文 |
| **组织信息** | |
| `get_organization_info(org_id)` | 获取组织基本信息 |
| `get_organization_tree(org_id)` | 获取组织树（含祖先/子孙/部门） |
| `get_department_tree(org_id)` | 获取部门树结构 |
| **组织查询** | |
| `get_descendant_ids(org_id)` | 获取所有子孙组织ID（不含自身） |
| `get_all_family_ids(org_id, include_self)` | 获取家族ID列表（自身+子孙） |
| `filter_by_organization(queryset, org_id, include_descendants)` | 按组织过滤查询集 |
| **权限检查** | |
| `check_organization_access(user, target_org_id, allow_cross_org)` | 检查组织访问权限 |
| `check_data_organization(instance, user, allow_cross_org)` | 检查数据对象权限 |
| `validate_organization_user(user, org_id)` | 验证用户是否属于组织 |
| **用户组织** | |
| `get_user_accessible_organizations(user)` | 获取用户可访问组织列表 |

### 6.4 OrganizationMiddleware

| 功能 | 说明 |
|------|------|
| **组织ID来源优先级** | Header > URL参数 > Token解析 > 用户默认组织 |
| **自动验证** | 验证组织存在性、激活状态、用户权限 |
| **请求头** | `X-Organization-Id` |
| **URL参数** | `?org_id=xxx` |
| **上下文管理** | 请求开始设置，请求结束清理 |

### 6.5 组织工具函数

| 工具 | 说明 | 使用场景 |
|------|------|---------|
| `OrganizationContext` | 上下文管理器类 | 需要临时切换组织上下文 |
| `organization_context(org_id)` | 上下文管理器函数 | 同上（函数版本） |
| `@with_organization(org_id)` | 组织上下文装饰器 | Celery任务、管理脚本 |
| `@with_organization_from_arg(arg_name)` | 从参数获取组织ID装饰器 | 动态组织ID |
| `@require_organization` | 要求组织上下文装饰器 | 确保必须有组织 |
| `switch_organization(user, org_id)` | 组织切换函数 | 用户切换组织 |

### 6.6 配置更新

在 Django settings 中添加中间件配置：

```python
# backend/config/settings.py

MIDDLEWARE = [
    # ... 其他中间件
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.common.middleware.organization_middleware.OrganizationMiddleware',  # 添加此行
    # ... 其他中间件
]
```

### 6.7 使用示例

```python
# 场景1：在Service中使用组织过滤
from apps.common.services.organization_service import BaseOrganizationService

class AssetService(BaseCRUDService):
    def get_org_assets(self, include_children=False):
        """获取当前组织资产"""
        queryset = self.model_class.objects.all()
        return BaseOrganizationService.filter_by_organization(
            queryset,
            include_descendants=include_children
        )

# 场景2：在Celery任务中使用组织上下文
from apps.common.utils.organization import with_organization

@with_organization(org_id='xxx-uuid')
def process_inventory_report():
    # 此函数内所有查询自动过滤指定组织
    assets = Asset.objects.all()
    # ...

# 场景3：使用上下文管理器
from apps.common.utils.organization import organization_context

def sync_organization_data(org_id: str):
    with organization_context(org_id):
        # 在此上下文中，所有操作都是针对指定组织的
        assets = Asset.objects.all()
        users = User.objects.all()

# 场景4：验证组织访问权限
from apps.common.services.organization_service import BaseOrganizationService

def cross_org_transfer(request, asset_id, target_org_id):
    # 检查源组织权限
    if not BaseOrganizationService.check_data_organization(asset, request.user):
        raise PermissionDenied("无权操作该资产")

    # 检查目标组织权限
    if not BaseOrganizationService.check_organization_access(
        request.user, target_org_id, allow_cross_org=False
    ):
        raise PermissionDenied("无权转移到目标组织")

# 场景5：获取用户可访问组织列表
def get_user_orgs(request):
    orgs = BaseOrganizationService.get_user_accessible_organizations(request.user)
    return Response({'organizations': orgs})
```

### 6.8 API端点（可选）

可以添加一个组织相关的API端点：

```python
# backend/apps/common/viewsets/organization.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.services.organization_service import BaseOrganizationService


class OrganizationInfoViewSet(viewsets.ViewSet):
    """组织信息相关API"""

    def list(self, request):
        """获取用户可访问的组织列表"""
        orgs = BaseOrganizationService.get_user_accessible_organizations(request.user)
        return Response({'organizations': orgs})

    @action(detail=False, methods=['get'])
    def current(self, request):
        """获取当前组织信息"""
        org_id = BaseOrganizationService.get_current_organization_id()
        if not org_id:
            return Response({'organization': None})
        org_info = BaseOrganizationService.get_organization_tree(org_id)
        return Response({'organization': org_info})

    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """获取组织树结构"""
        org_info = BaseOrganizationService.get_organization_tree(pk)
        return Response({'organization': org_info})

    @action(detail=True, methods=['get'])
    def departments(self, request, pk=None):
        """获取组织部门树"""
        dept_tree = BaseOrganizationService.get_department_tree(pk)
        return Response({'departments': dept_tree})
```

---

## 8. 配置更新

### 8.1 导入路径更新

```python
# backend/config/settings.py

# 添加公共模块导入路径
SYSTEM_MODULES = [
    'apps.common.serializers',
    'apps.common.viewsets',
    'apps.common.services',
    'apps.common.filters',
    'apps.common.responses',
    'apps.common.handlers',
]
```

### 8.2 Django REST Framework 配置

```python
# backend/config/settings.py

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'apps.common.handlers.exceptions.custom_exception_handler',
}
```

---

## 9. 迁移指南

### 9.1 逐步迁移现有代码

```python
# 步骤1: 创建新基类（不影响现有代码）
# apps/common/serializers/base.py (新建)

# 步骤2: 逐模块迁移
# 旧代码：
class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'organization', 'created_at', ...]

# 新代码：
class AssetSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name', ...]
```

### 9.2 向后兼容

- 不强制要求立即迁移
- 新模块必须使用新基类
- 旧模块可逐步迁移

---

## 10. BasePermission - 权限基类

### 10.1 设计目标

- 提供统一的权限检查机制
- 支持基于角色的访问控制（RBAC）
- 支持对象级权限（所有权检查）
- 支持组织隔离权限检查
- 可扩展的自定义权限

### 10.2 BasePermission

| 方法 | 检查项 | 说明 |
|------|--------|------|
| `has_permission(request, view)` | 全局权限 | 认证状态、组织访问、角色权限 |
| `has_object_permission(request, view, obj)` | 对象权限 | 组织隔离、软删除、所有权 |

**权限动作映射**:
| HTTP方法 | 权限类型 |
|----------|----------|
| GET | view |
| POST | create |
| PUT | update |
| PATCH | partial_update |
| DELETE | delete |

**所有权检查规则**:
| 角色 | 权限 |
|------|------|
| 创建者 | 完全权限 |
| 部门主管 | 本部门资源 |
| 管理员 | 所有资源 |
| 只读操作 | 允许 |

### 10.3 预定义权限类

| 权限类 | 说明 |
|--------|------|
| `IsAdminOrReadOnly` | 管理员或只读 |
| `IsOwnerOrReadOnly` | 所有者或只读 |
| `IsOrganizationMember` | 组织成员 |
| `AllowOptionsPermission` | 允许OPTIONS请求（CORS预检） |

### 10.4 权限装饰器

| 装饰器 | 说明 | 示例 |
|--------|------|------|
| `@require_permissions('perm1', 'perm2')` | 权限检查 | `@require_permissions('assets.view_asset')` |
| `@require_roles('admin', 'manager')` | 角色检查 | `@require_roles('admin')` |

### 10.5 ViewSet 权限配置示例

```python
from apps.common.permissions.base import (
    BasePermission,
    IsOrganizationMember
)

class AssetViewSet(BaseModelViewSetWithBatch):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    # 多权限组合（AND 关系）
    permission_classes = [
        IsOrganizationMember,  # 必须是组织成员
        BasePermission,         # 基础权限检查
    ]
```

### 10.6 扩展权限模型

> 详见：[permission_models.md](./permission_models.md) | [permission_service.md](./permission_service.md)

上述基础权限类提供了组织隔离、所有权检查等基本能力。对于更复杂的权限场景，GZEAMS 提供了扩展权限模型：

| 扩展能力 | 文档 | 说明 |
|---------|------|------|
| **Role 扩展模型** | [permission_models.md §2.2](./permission_models.md#22-role-扩展模型) | 支持数据范围、字段级权限配置 |
| **FieldPermission** | [permission_models.md §2.4](./permission_models.md#24-fieldpermission-字段权限模型) | 非工作流场景的字段权限控制 |
| **PermissionService** | [permission_service.md §3](./permission_service.md#3-permissionservice-实现) | 统一权限服务层 |
| **权限缓存** | [permission_service.md §6](./permission_service.md#6-权限缓存策略) | 提升权限检查性能 |

#### 10.5.1 使用 PermissionService

```python
# 在 ViewSet 中使用 PermissionService
from apps.common.services.permission_service import PermissionService

class AssetViewSet(BaseModelViewSetWithBatch):
    def get_queryset(self):
        """根据用户数据范围过滤数据"""
        queryset = super().get_queryset()
        return PermissionService.filter_queryset_by_data_scope(
            self.request.user,
            queryset
        )

    @action(detail=False, methods=['post'])
    def export(self, request):
        """检查特殊权限"""
        if not PermissionService.check_permission(
            request.user,
            'assets.export'
        ):
            return Response({'error': '无导出权限'}, status=403)
        # ...
```

#### 10.5.2 字段权限检查

```python
# 检查字段级权限
field_perms = PermissionService.get_field_permissions(request.user, 'Asset')
if not field_perms.get('purchase_price', {}).get('read', False):
    # 用户无权查看采购价格字段
    pass
```

---

## 11. BaseI18nMixin - 多语言基类

### 11.1 设计目标

- 统一的多语言翻译接口
- 支持动态语言包加载
- 翻译缓存优化
- 模型字段多语言支持

> 详见：[i18n_models.md](./i18n_models.md) | [i18n_service.md](./i18n_service.md)

### 11.2 TranslatedModelSerializer

```python
# backend/apps/common/serializers/translation.py

from apps.common.services.i18n_service import TranslationService

class TranslatedFieldMixin:
    """
    翻译字段 Mixin

    为序列化器自动添加翻译后的字段
    """

    def to_representation(self, instance):
        """自动翻译多语言字段"""
        data = super().to_representation(instance)

        # 获取语言
        lang_code = self.context.get('request').META.get(
            'HTTP_ACCEPT_LANGUAGE', 'zh-CN'
        )

        # 翻译 *_translations 字段
        translated = TranslationService.translate_object(instance, lang_code)

        # 添加翻译字段 (如 name_i18n, description_i18n)
        for field, value in translated.items():
            data[f'{field}_i18n'] = value

        return data
```

### 11.3 使用示例

```python
# 在 ViewSet 中使用 TranslationService
from apps.common.services.i18n_service import TranslationService

class AssetViewSet(BaseModelViewSet):
    def list(self, request, *args, **kwargs):
        """获取资产列表，翻译状态显示"""
        response = super().list(request, *args, **kwargs)

        lang_code = request.META.get('HTTP_ACCEPT_LANGUAGE', 'zh-CN')

        # 翻译状态值
        for item in response.data['results']:
            status = item['status']
            item['status_display'] = TranslationService.get_text_auto(
                f'asset.status.{status}',
                lang_code,
                default=status
            )

        return response

    @action(detail=False, methods=['get'])
    def language_pack(self, request):
        """获取前端语言包"""
        lang_code = request.query_params.get('lang', 'zh-CN')
        pack = TranslationService.get_language_pack(lang_code)
        return Response({'success': True, 'data': pack})
```

---

## 12. BaseCacheMixin - 缓存基类

### 11.1 设计目标

- 提供统一的缓存抽象
- 支持多种缓存后端（Redis/Memory）
- 自动缓存失效策略
- 缓存预热功能

### 12.2 BaseCacheMixin

| 属性 | 说明 | 默认值 |
|------|------|--------|
| `cache_timeout` | 缓存超时时间（秒） | 300（5分钟） |
| `cache_key_prefix` | 缓存键前缀 | '' |
| `cache_enabled` | 是否启用缓存 | True |

| 方法 | 说明 |
|------|------|
| `get_cache_key(*args, **kwargs)` | 生成缓存键（格式：`cache:{prefix}:{hash}`） |
| `cache_get(key)` | 获取缓存 |
| `cache_set(key, value, timeout)` | 设置缓存 |
| `cache_delete(key)` | 删除缓存 |
| `cache_delete_pattern(pattern)` | 批量删除（Redis支持） |
| `cache_clear()` | 清空所有缓存 |

### 12.3 缓存Mixin类

| Mixin | 用途 | 缓存内容 |
|-------|------|---------|
| `CachedQuerySetMixin` | 列表视图 | QuerySet结果 |
| `CachedObjectMixin` | 详情视图 | 单个对象数据 |
| `@cache_view(timeout, key_prefix)` | 视图装饰器 | 整个响应 |

---

## 12. 元数据驱动扩展

### 12.1 概述

GZEAMS 作为低代码平台，除了传统的代码继承模式外，还提供了元数据驱动的扩展方式。

详见：[metadata_driven.md](./metadata_driven.md)

### 12.2 两种模式对比

| 维度 | 传统模式（代码继承） | 元数据驱动模式（配置生成） |
|------|---------------------|--------------------------|
| **适用场景** | 复杂业务逻辑、已有模型 | 简单CRUD、动态业务对象 |
| **扩展方式** | 继承基类 + 编写代码 | 配置元数据 + 零代码 |
| **序列化器** | `BaseModelSerializer` | `MetadataDrivenSerializer` |
| **ViewSet** | `BaseModelViewSet` | `MetadataDrivenViewSet` |
| **数据存储** | 传统Django模型表 | `DynamicData` + `custom_fields` |
| **字段变更** | 需要修改代码/迁移 | 配置元数据即可 |

### 12.3 元数据驱动组件

| 组件 | 说明 | 文档 |
|------|------|------|
| `MetadataDrivenSerializer` | 基于元数据的序列化器 | [metadata_driven.md](./metadata_driven.md) |
| `MetadataDrivenViewSet` | 基于元数据的ViewSet | [metadata_driven.md](./metadata_driven.md) |
| `MetadataDrivenFilter` | 基于元数据的过滤器 | [metadata_driven.md](./metadata_driven.md) |
| `MetadataDrivenService` | 动态数据CRUD服务 | [dynamic_data_service.md](./dynamic_data_service.md) |
| `DynamicFieldValidator` | 动态字段验证器 | [metadata_validators.md](./metadata_validators.md) |

### 12.4 使用示例

```python
# 传统模式：需要为每个业务对象编写代码
class AssetSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name']

# 元数据驱动模式：仅需配置元数据
# 1. 配置 BusinessObject（在管理后台或通过API）
BusinessObject.objects.create(code='Asset', name='资产')

# 2. 配置 FieldDefinition
FieldDefinition.objects.create(
    business_object=obj,
    code='asset_code',
    name='资产编码',
    field_type='text',
    is_required=True
)

# 3. 自动生成序列化器、ViewSet（无需编写代码）
AssetSerializer = MetadataDrivenSerializer.for_business_object('Asset')
```

---

## 13. 输出产物

### 13.1 传统模式文件

| 文件 | 说明 |
|------|------|
| `apps/common/serializers/base.py` | BaseModelSerializer |
| `apps/common/viewsets/base.py` | BaseModelViewSet + BatchOperationMixin |
| `apps/common/services/base_crud.py` | BaseCRUDService |
| `apps/common/services/organization_service.py` | BaseOrganizationService |
| `apps/common/middleware/organization_middleware.py` | OrganizationMiddleware |
| `apps/common/utils/organization.py` | 组织工具函数和装饰器 |
| `apps/common/filters/base.py` | BaseModelFilter |
| `apps/common/responses/base.py` | BaseResponse |
| `apps/common/handlers/exceptions.py` | BaseExceptionHandler |
| `apps/common/permissions/base.py` | BasePermission |
| `apps/common/permissions/decorators.py` | 权限装饰器 |
| `apps/common/mixins/cache.py` | BaseCacheMixin |
| `backend/config/settings.py` | 配置更新 |

### 13.2 元数据驱动文件

| 文件 | 说明 |
|------|------|
| `apps/common/serializers/metadata_driven.py` | MetadataDrivenSerializer |
| `apps/common/viewsets/metadata_driven.py` | MetadataDrivenViewSet |
| `apps/common/filters/metadata_driven.py` | MetadataDrivenFilter |
| `apps/common/services/metadata_driven.py` | MetadataDrivenService |
| `apps/common/validators/dynamic_field.py` | DynamicFieldValidator |
| `apps/common/generators/code_generator.py` | MetadataCodeGenerator |
