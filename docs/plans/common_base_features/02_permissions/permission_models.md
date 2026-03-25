# 权限模型设计

## 任务概述

为 GZEAMS 低代码平台设计完整的权限模型，支持基于角色的访问控制（RBAC）、字段级权限、工作流节点权限，以及前端权限指令和组件。

---

## 权限数据模型定义

### Role 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | string | max=100, unique | 角色名称 |
| code | string | max=50, unique | 角色编码 |
| description | text | nullable | 角色描述 |
| is_system | boolean | default=False | 是否系统角色 |

### UserRole 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user | ForeignKey | User | 关联用户 |
| role | ForeignKey | Role | 关联角色 |
| organization | ForeignKey | Organization | 所属组织 |

### FieldPermission 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| role | ForeignKey | Role | 关联角色 |
| business_object_code | string | max=50 | 业务对象编码 |
| field_code | string | max=50 | 字段编码 |
| permission_type | string | max=20 | 权限类型(read/write/hidden) |

### PermissionCache 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| user_id | UUID | indexed | 用户ID |
| cache_key | string | max=200 | 缓存键 |
| permissions | JSONB | default={} | 权限数据 |
| expires_at | datetime | indexed | 过期时间 |

---

## 1. 设计背景

### 1.1 当前权限设计

`backend.md` 中已定义 `BasePermission` 基础权限类：

```python
# 已有的权限类
class BasePermission(permissions.BasePermission):
    """基础权限类 - 提供组织隔离、软删除检查、所有权检查"""

class IsAdminOrReadOnly(BasePermission):
    """管理员或只读权限"""

class IsOwnerOrReadOnly(BasePermission):
    """所有者或只读权限"""

class IsOrganizationMember(BasePermission):
    """组织成员权限"""
```

### 1.2 当前设计的局限性

| 局限性 | 说明 |
|-------|------|
| 权限检查分散 | 各模块自行实现权限逻辑，缺乏统一服务层 |
| 前端权限缺失 | 没有统一的权限指令、组件和组合函数 |
| 字段级权限不足 | 仅有工作流字段权限，缺乏通用字段级权限配置 |
| 缺少权限缓存 | 权限检查每次查询数据库，性能欠佳 |

### 1.3 设计目标

1. **统一权限服务层** - 集中处理所有权限逻辑
2. **前端权限控制** - 提供指令、组件和组合函数
3. **字段级权限配置** - 支持非工作流场景的字段权限
4. **权限缓存优化** - 提升权限检查性能

---

## 2. 后端权限模型扩展

### 2.1 权限相关模型关系

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           权限模型架构                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    Django 内置权限模型                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │ │
│  │  │   User       │  │   Permission │  │   Group/Role          │  │ │
│  │  │  (用户)      │──│(权限)       │──│  (分组/角色)          │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    GZEAMS 扩展权限模型                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │ │
│  │  │ Role         │  │FieldPermission│  │  WorkflowNodePermission│  │ │
│  │  │  (扩展角色)  │  │ (字段权限)    │  │  (工作流节点权限)      │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    权限服务层                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────┐  │ │
│  │  │              PermissionService                              │  │ │
│  │  │  - check_permission()    - check_field_permission()        │  │ │
│  │  │  - get_user_permissions() - get_role_permissions()          │  │ │
│  │  │  - grant_permission()     - revoke_permission()            │  │ │
│  │  │  - cache_permissions()     - invalidate_cache()             │  │ │
│  │  └─────────────────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Role 扩展模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| code | CharField(50) | unique, not_null | 角色编码（如：admin、manager、user） |
| name | CharField(100) | not_null | 角色名称 |
| description | TextField | blank | 角色描述 |
| permissions | ManyToManyField | blank, to='auth.Permission' | Django 系统权限关联 |
| custom_permissions | JSONField | default=list, blank | 自定义权限列表 `["assets.view_all", "assets.export"]` |
| data_scope | CharField(20) | choices, default='self' | 数据范围：all/org/dept/self/custom |
| field_permissions | JSONField | default=dict, blank | 字段权限配置 `{"Asset": {"code": {"read": true}}}` |
| sort_order | IntegerField | default=0 | 排序字段 |
| is_active | BooleanField | default=True | 是否启用 |

**Meta 配置：**
- `db_table`: accounts_role
- `ordering`: ['sort_order', 'id']

**核心方法：**

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| get_all_permissions() | - | set | 获取角色所有权限（系统权限 + 自定义权限） |
| has_field_permission() | business_object_code, field_code, action='read' | bool | 检查字段级权限 |

### 2.3 用户角色关联

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| user | ForeignKey | CASCADE, to='accounts.User' | 关联用户 |
| role | ForeignKey | CASCADE, to='accounts.Role' | 关联角色 |
| organization | ForeignKey | CASCADE, to='organizations.Organization' | 关联组织 |
| department | ForeignKey | CASCADE, null, blank, to='organizations.Department' | 关联部门（可选） |
| is_primary | BooleanField | default=False | 是否主角色 |
| effective_from | DateTimeField | default=timezone.now | 生效时间 |
| effective_until | DateTimeField | null, blank | 失效时间 |

**Meta 配置：**
- `db_table`: accounts_user_role
- `unique_together`: ['user', 'role', 'organization']

### 2.4 FieldPermission 字段权限模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| business_object | ForeignKey | CASCADE, to='system.BusinessObject' | 关联业务对象 |
| field_code | CharField(100) | not_null | 字段代码 |
| permissions | JSONField | default=dict, blank | 权限配置 `{"role_code": {"read": true}}` |
| default_permission | CharField(20) | choices, default='inherit' | 默认权限：inherit/readonly/hidden/editable |

**Meta 配置：**
- `db_table`: system_field_permission
- `unique_together`: ['business_object', 'field_code']

**核心方法：**

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| get_permission_for_role() | role_code | dict | 获取指定角色的字段权限 |
| is_readable() | role_code | bool | 检查字段是否可读 |
| is_writable() | role_code | bool | 检查字段是否可写 |
| is_required() | role_code | bool | 检查字段是否必填 |

### 2.5 BusinessObject 模型扩展

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| enable_field_permission | BooleanField | default=False | 启用字段级权限（启用后由 FieldPermission 控制） |
| default_field_permission | JSONField | default=dict, blank | 默认字段权限 `{"role_code": {"create": true}}` |

---

## 3. 权限服务层设计

详见：[permission_service.md](./permission_service.md)

---

## 4. 前端权限组件设计

详见：[permission_frontend.md](./permission_frontend.md)

---

## 5. 权限检查流程

### 5.1 完整权限检查流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        权限检查流程                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. API 请求到达                                                        │
│     │                                                                   │
│     ▼                                                                   │
│  2. 认证检查 (IsAuthenticated?)                                         │
│     │                                                                   │
│     ▼                                                                   │
│  3. BasePermission.has_permission()                                    │
│     │                                                                   │
│     ├──► 3.1 超级管理员跳过                                            │
│     │                                                                   │
│     ├──► 3.2 组织访问权限检查                                          │
│     │     └──► _check_organization_access()                            │
│     │                                                                   │
│     ├──► 3.3 角色权限检查                                              │
│     │     └──► _check_role_permission()                                │
│     │         └──► PermissionService.check_permission()               │
│     │             └──► 缓存查询 → 数据库查询                            │
│     │                                                                   │
│     └──► 3.4 对象级权限检查（如有）                                    │
│           └──► has_object_permission()                                 │
│               └──► 所有权检查 / 部门检查 / 管理员检查                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 字段权限检查流程

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     字段权限检查流程                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  前端请求: GET /api/assets/{id}/                                        │
│                                                                         │
│  1. 获取用户角色                                                        │
│     │                                                                   │
│     ▼                                                                   │
│  2. 查询字段权限配置                                                    │
│     │                                                                   │
│     ├──► WorkflowFieldPermission (如果启用工作流)                       │
│     │     └──► 根据 wf_visible/wf_editable/wf_required 判断            │
│     │                                                                   │
│     └──► FieldPermission (如果启用字段权限)                             │
│           └──► 根据 permissions[role_code][action] 判断                 │
│                                                                         │
│  3. 返回字段权限信息                                                    │
│     {                                                                   │
│       "field_permissions": {                                            │
│         "asset_code": {"readable": true, "writable": false},           │
│         "purchase_price": {"readable": false, "writable": false}        │
│       }                                                                 │
│     }                                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 权限缓存策略

### 6.1 缓存设计

**PermissionCache 类方法：**

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| get_user_permissions() | user_id | Optional[set] | 获取用户权限缓存 |
| set_user_permissions() | user_id, permissions | None | 设置用户权限缓存（1小时超时） |
| invalidate_user() | user_id | None | 清除用户权限缓存 |
| invalidate_role() | role_id | None | 清除角色相关缓存 |

**缓存配置：**
- `CACHE_PREFIX`: permission
- `CACHE_TIMEOUT`: 3600秒（1小时）
- `cache_key` 格式: `permission:user:{user_id}`

### 6.2 缓存失效时机

| 事件 | 失效策略 |
|------|---------|
| 用户角色变更 | 清除用户权限缓存 |
| 角色权限变更 | 清除该角色下所有用户缓存 |
| 字段权限配置变更 | 清除相关业务对象缓存 |
| 组织关系变更 | 清除用户权限缓存 |

---

## 7. 权限配置示例

### 7.1 角色权限配置

| 角色 | data_scope | custom_permissions | field_permissions |
|------|------------|-------------------|-------------------|
| **超级管理员** | all | `["*"]` | 无限制 |
| **资产管理员** | org | `["assets.view_all", "assets.create", "assets.update", "assets.delete", "assets.export", "assets.import"]` | `{"Asset": {"purchase_price": {"read": true, "write": true}, "depreciation": {"read": true, "write": true}}}` |
| **普通用户** | self | `["assets.view", "assets.view_own"]` | `{"Asset": {"purchase_price": {"read": false, "write": false}, "depreciation": {"read": false, "write": false}}}` |

### 7.2 字段权限配置

| 业务对象 | 字段 | 权限配置 | 默认权限 |
|---------|------|---------|---------|
| Asset | purchase_price | `{"admin": {"read": true, "write": true}, "asset_manager": {"read": true, "write": true}, "user": {"read": false, "write": false}}` | hidden |
| Asset | asset_code | `{"admin": {"read": true, "write": true}, "asset_manager": {"read": true, "write": true}, "user": {"read": true, "write": false}}` | readonly |

---

## 8. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/accounts/models.py` | Role、UserRole 模型扩展 |
| `backend/apps/system/models.py` | FieldPermission 模型、BusinessObject 扩展 |
| `backend/apps/common/services/permission_service.py` | 权限服务实现 |
| `backend/apps/common/permissions/base.py` | BasePermission 扩展 |

---

## 9. 迁移步骤

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1 | `python manage.py makemigrations accounts system` | 生成迁移文件 |
| 2 | `python manage.py migrate` | 执行迁移 |
| 3 | `python manage.py create_default_roles` | 创建默认角色 |

---

## 10. 与现有代码的关系

### 10.1 兼容性

- **不影响现有代码**：现有权限类继续可用
- **渐进式迁移**：可逐步将各模块迁移到新权限模型
- **向后兼容**：未配置字段权限时使用原有行为

### 10.2 替换关系

| 原有组件 | 新组件 | 迁移建议 |
|---------|-------|---------|
| 硬编码权限检查 | PermissionService | 逐步替换 |
| 分散的权限逻辑 | 统一权限服务 | 逐步迁移 |
| 前端手动权限判断 | v-permission 指令 | 全局替换 |
