# 权限服务层设计

## 任务概述

提供统一的权限服务层（PermissionService），集中处理所有权限逻辑，包括用户权限、角色权限、字段权限、数据权限等。

---

## 权限服务API模型

### CheckPermission 请求模型

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| user_id | UUID | 是 | 用户ID |
| resource | string | 是 | 资源标识 |
| action | string | 是 | 操作类型(read/write/delete) |
| organization_id | UUID | 是 | 组织ID |

### CheckPermission 响应模型

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| data.granted | boolean | 是否授权 |
| data.reason | string | 拒绝原因(如有) |

---

## 1. 设计目标

### 1.1 核心功能

| 功能 | 说明 |
|------|------|
| 统一权限检查 | 提供统一的权限检查接口 |
| 权限缓存优化 | 减少数据库查询，提升性能 |
| 字段权限控制 | 支持字段级读写权限 |
| 数据权限过滤 | 根据角色数据范围过滤数据 |
| 权限继承支持 | 支持权限继承和覆盖 |

### 1.2 设计原则

1. **单一职责** - 每个方法只负责一种权限检查
2. **可缓存** - 权限计算结果可缓存
3. **可扩展** - 支持自定义权限规则
4. **性能优先** - 批量检查时减少查询次数

---

## 2. 文件结构

```
backend/apps/common/services/
├── permission_service.py      # 核心权限服务
├── permission_cache.py        # 权限缓存管理
└── permission_decorators.py   # 权限装饰器
```

---

## 3. PermissionService 实现

### 3.1 核心服务类

**PermissionCache 类：**

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| _make_key() | *parts: str | str | 生成缓存键 |
| get_user_permissions() | user_id | Optional[Set[str]] | 获取用户权限缓存 |
| set_user_permissions() | user_id, permissions | None | 设置用户权限缓存 |
| invalidate_user() | user_id | None | 清除用户权限缓存 |
| get_user_roles() | user_id | Optional[List[Dict]] | 获取用户角色缓存 |
| set_user_roles() | user_id, roles | None | 设置用户角色缓存 |
| invalidate_user_roles() | user_id | None | 清除用户角色缓存 |
| get_field_permissions() | business_object_code, role_codes | Optional[Dict] | 获取字段权限缓存 |
| set_field_permissions() | business_object_code, role_codes, permissions | None | 设置字段权限缓存 |
| invalidate_field_permissions() | business_object_code (可选) | None | 清除字段权限缓存 |

**缓存配置：**
- `CACHE_PREFIX`: gzeams:permission
- `CACHE_TIMEOUT`: 3600秒（1小时）

**PermissionService 类常量：**

| 常量 | 值 | 说明 |
|------|------|------|
| DATA_SCOPE_ALL | 'all' | 全部数据 |
| DATA_SCOPE_ORG | 'org' | 本组织及下级 |
| DATA_SCOPE_DEPT | 'dept' | 本部门 |
| DATA_SCOPE_SELF | 'self' | 仅本人 |
| DATA_SCOPE_CUSTOM | 'custom' | 自定义 |
| ACTION_CREATE | 'create' | 创建操作 |
| ACTION_READ | 'read' | 读取操作 |
| ACTION_UPDATE | 'update' | 更新操作 |
| ACTION_DELETE | 'delete' | 删除操作 |
| ACTION_EXPORT | 'export' | 导出操作 |
| ACTION_IMPORT | 'import' | 导入操作 |
| ACTION_APPROVE | 'approve' | 审批操作 |

**PermissionService 核心方法：**

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| get_user_permissions() | user, use_cache=True | Set[str] | 获取用户所有权限（系统权限 + 自定义权限） |
| get_user_roles() | user, organization (可选), use_cache=True | List[Role] | 获取用户角色列表 |
| check_permission() | user, permission_code, use_cache=True | bool | 检查用户是否拥有指定权限（支持通配符） |
| check_any_permission() | user, permission_codes, use_cache=True | bool | 检查用户是否拥有任一指定权限 |
| check_all_permissions() | user, permission_codes, use_cache=True | bool | 检查用户是否拥有所有指定权限 |
| get_field_permissions() | user, business_object_code, use_cache=True | Dict[str, Dict[str, bool]] | 获取用户对业务对象的字段权限 |
| check_field_permission() | user, business_object_code, field_code, action='read', use_cache=True | bool | 检查用户对指定字段的权限 |
| filter_queryset_by_data_scope() | user, queryset, organization_field='organization', department_field='department', user_field='created_by' | QuerySet | 根据用户角色的数据范围过滤查询集 |
| grant_permission() | user, role, organization, department (可选) | UserRole | 授予用户角色 |
| revoke_permission() | user, role, organization | bool | 撤销用户角色 |
| invalidate_cache() | user_id (可选) | None | 清除权限缓存 |

### 3.2 使用示例

**ViewSet 中使用权限服务：**

```python
from apps.common.services.permission_service import PermissionService
from apps.common.viewsets.base import BaseModelViewSet

class AssetViewSet(BaseModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def get_queryset(self):
        """根据用户数据范围过滤数据"""
        queryset = super().get_queryset()
        return PermissionService.filter_queryset_by_data_scope(
            self.request.user,
            queryset
        )

    def check_permissions(self, request):
        """自定义权限检查"""
        super().check_permissions(request)

        if request.method == 'DELETE':
            if not PermissionService.check_permission(
                request.user,
                'assets.delete_asset'
            ):
                self.permission_denied(request, message='无删除权限')

    @action(detail=False, methods=['post'])
    def export(self, request):
        """导出需要特殊权限"""
        if not PermissionService.check_permission(
            request.user,
            'assets.export'
        ):
            return Response({'error': '无导出权限'}, status=403)
```

---

## 4. 权限装饰器

| 装饰器 | 参数 | 说明 | 使用示例 |
|--------|------|------|----------|
| @require_permission() | permission_code | 要求用户拥有指定权限 | `@require_permission('assets.create_asset')` |
| @require_any_permission() | *permission_codes | 要求用户拥有任一指定权限 | `@require_any_permission('assets.view_own', 'assets.view_all')` |
| @require_role() | *role_codes | 要求用户拥有指定角色 | `@require_role('admin', 'manager')` |
| @require_data_scope() | data_scope | 要求用户拥有指定的数据范围 | `@require_data_scope('org')` |

---

## 5. BasePermission 扩展

**BasePermission 类：**

| 属性/方法 | 说明 |
|----------|------|
| permission_map | 权限代码映射表 |
| get_permission_code(action) | 获取操作对应的权限代码 |
| has_permission(request, view) | 检查基础权限（使用 PermissionService） |
| has_object_permission(request, view, obj) | 检查对象级权限（根据数据范围） |

**IsAuthenticatedWithPermission 类：**

| 属性/方法 | 说明 |
|----------|------|
| required_permission | 需要的权限代码（在 ViewSet 中设置） |
| has_permission(request, view) | 检查用户认证状态和指定权限 |

---

## 6. 权限 API 扩展

**UserPermissionViewSet API 端点：**

| 端点 | 方法 | 说明 | 请求参数 | 响应 |
|------|------|------|----------|------|
| /api/permissions/my_permissions/ | GET | 获取当前用户所有权限 | 无 | `{"success": true, "data": {"permissions": [...], "count": N}}` |
| /api/permissions/my_roles/ | GET | 获取当前用户所有角色 | 无 | `{"success": true, "data": {"roles": [{"code": "...", "name": "...", "id": "..."}]}}` |
| /api/permissions/field_permissions/ | GET | 获取当前用户字段权限 | object_code (查询参数) | `{"success": true, "data": {"field_permissions": {...}}}` |
| /api/permissions/refresh_cache/ | POST | 刷新当前用户权限缓存 | 无 | `{"success": true, "message": "缓存已刷新"}` |

---

## 7. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/common/services/permission_service.py` | 权限服务核心实现 |
| `backend/apps/common/services/permission_cache.py` | 权限缓存管理 |
| `backend/apps/common/services/permission_decorators.py` | 权限装饰器 |
| `backend/apps/common/permissions/base.py` | BasePermission 扩展 |
| `backend/apps/common/viewsets/permission_viewsets.py` | 权限查询 API |

---

## 8. 使用场景总结

| 场景 | 使用方式 | 示例 |
|------|---------|------|
| ViewSet 权限控制 | `permission_classes = [BasePermission]` | 自动检查 CRUD 权限 |
| 自定义权限检查 | `PermissionService.check_permission()` | 特殊操作权限验证 |
| 数据范围过滤 | `PermissionService.filter_queryset_by_data_scope()` | 按角色过滤可见数据 |
| 字段权限控制 | `PermissionService.check_field_permission()` | 字段级读写权限 |
| 函数权限装饰 | `@require_permission()` | 视图函数权限控制 |
| 前端权限查询 | `/api/permissions/my_permissions/` | 获取用户权限列表 |
