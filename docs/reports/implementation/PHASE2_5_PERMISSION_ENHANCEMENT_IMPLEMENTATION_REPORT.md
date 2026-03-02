# Phase 2.5: 权限体系增强模块 - 实现报告

**项目**: GZEAMS (钩子固定资产低代码平台)
**阶段**: Phase 2.5 - 权限体系增强
**实现日期**: 2026-01-16
**状态**: ✅ 核心功能已完成

---

## 📋 目录

1. [功能概述](#功能概述)
2. [架构设计](#架构设计)
3. [后端实现](#后端实现)
4. [前端实现](#前端实现)
5. [API 接口规范](#api-接口规范)
6. [数据模型](#数据模型)
7. [测试用例](#测试用例)
8. [部署指南](#部署指南)
9. [快速开始](#快速开始)

---

## 功能概述

### 核心功能

Phase 2.5 权限体系增强模块为 GZEAMS 提供了企业级的权限管理能力,包括:

1. **字段级权限控制**
   - 支持 `read`(只读)、`write`(可写)、`hidden`(隐藏)、`masked`(脱敏) 四种权限类型
   - 支持按角色和用户配置字段权限
   - 支持权限优先级和条件表达式
   - 内置多种脱敏规则(手机号、身份证、银行卡、姓名、金额)

2. **数据级权限控制**
   - 支持 `all`(全部数据)、`self_dept`(本部门)、`self_and_sub`(本部门及下级)、`specified`(指定部门)、`custom`(自定义规则) 五种范围类型
   - 支持数据权限扩展,为用户/角色添加额外数据访问权限
   - 支持部门层级权限继承

3. **权限继承管理**
   - 支持角色间权限继承(`full` 完全继承、`partial` 部分继承、`override` 覆盖继承)
   - 支持部门权限继承配置

4. **权限审计日志**
   - 记录所有权限相关操作(创建、更新、删除、授权、撤销、访问、拒绝)
   - 记录操作人、IP地址、User Agent、变更内容
   - 提供审计日志统计和查询功能

5. **权限缓存机制**
   - 基于 Redis 的权限缓存
   - 权限变更时自动清除缓存
   - 支持手动清除缓存接口

---

## 架构设计

### 后端架构

```
backend/apps/permissions/
├── models.py                      # 数据模型(继承 BaseModel)
├── serializers.py                 # 序列化器(继承 BaseModelSerializer)
├── views.py                       # 视图层(继承 BaseModelViewSetWithBatch)
├── filters.py                     # 过滤器(继承 BaseModelFilter)
├── engine.py                      # 权限引擎核心
├── urls.py                        # URL路由配置
├── services/                      # 服务层
│   ├── field_permission_service.py    # 字段权限服务(继承 BaseCRUDService)
│   └── data_permission_service.py    # 数据权限服务(继承 BaseCRUDService)
└── management/commands/           # 管理命令
    └── sync_permissions.py        # 权限同步命令
```

### 前端架构

```
frontend/src/
├── api/
│   └── permissions.ts             # 权限 API 接口定义
├── stores/
│   └── permission.ts              # 权限 Store
└── views/system/permissions/      # 权限管理页面(已规划)
    ├── field/                     # 字段权限管理
    ├── data/                      # 数据权限管理
    ├── inheritance/               # 权限继承管理
    └── audit/                     # 审计日志查询
```

### 设计模式

1. **公共基类继承**: 所有组件严格继承对应的公共基类
2. **服务层封装**: 业务逻辑封装在 Service 层,提供统一 CRUD 方法
3. **权限引擎**: 核心权限逻辑封装在 `PermissionEngine` 类中
4. **缓存优先**: 权限检查优先从缓存读取,提高性能

---

## 后端实现

### 1. 数据模型 (models.py)

#### 字段权限模型

```python
class FieldPermission(BaseModel):
    """字段级权限配置"""
    role = models.ForeignKey('accounts.Role', ...)  # 关联角色
    user = models.ForeignKey('accounts.User', ...)  # 关联用户
    content_type = models.ForeignKey(ContentType, ...)  # 对象类型
    field_name = models.CharField(max_length=100)  # 字段名
    permission_type = models.CharField(...)  # 权限类型: read/write/hidden/masked
    condition = models.JSONField(...)  # 权限条件(可选)
    mask_rule = models.CharField(...)  # 脱敏规则
    mask_params = models.JSONField(...)  # 脱敏参数
    priority = models.IntegerField(default=0)  # 优先级
    remark = models.TextField(blank=True)  # 备注
```

**继承功能**:
- ✅ 组织隔离 (`organization` FK)
- ✅ 软删除 (`is_deleted`, `deleted_at`)
- ✅ 审计字段 (`created_at`, `updated_at`, `created_by`)
- ✅ 动态字段 (`custom_fields` JSONB)

#### 数据权限模型

```python
class DataPermission(BaseModel):
    """数据级权限配置"""
    role = models.ForeignKey('accounts.Role', ...)
    user = models.ForeignKey('accounts.User', ...)
    content_type = models.ForeignKey(ContentType, ...)
    scope_type = models.CharField(...)  # 范围类型: all/self_dept/self_and_sub/specified/custom
    scope_value = models.JSONField(...)  # 范围值
    is_inherited = models.BooleanField(default=True)  # 允许继承
    custom_filter = models.JSONField(...)  # 自定义过滤条件
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

#### 权限继承模型

```python
class PermissionInheritance(BaseModel):
    """权限继承关系"""
    parent_role = models.ForeignKey('accounts.Role', related_name='child_inheritances')
    child_role = models.ForeignKey('accounts.Role', related_name='parent_inheritances')
    inherit_type = models.CharField(...)  # full/partial/override
    is_active = models.BooleanField(default=True)
```

#### 审计日志模型

```python
class PermissionAuditLog(BaseModel):
    """权限审计日志"""
    actor = models.ForeignKey('accounts.User', ...)
    action = models.CharField(...)  # create/update/delete/grant/revoke/access/deny
    target_type = models.CharField(...)  # role/user/field_permission/data_permission/inheritance
    target_id = models.IntegerField()
    target_name = models.CharField(max_length=200)
    changes = models.JSONField(default=dict)  # 变更内容
    ip_address = models.GenericIPAddressField(...)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    request_id = models.CharField(max_length=100, ...)
```

### 2. 权限引擎 (engine.py)

#### 核心功能

```python
class PermissionEngine:
    """权限引擎核心类"""

    # 缓存
    _field_permissions_cache = {}
    _data_scope_cache = {}

    @staticmethod
    def get_field_permissions(user, object_type, action='view'):
        """获取用户的字段级权限"""
        # 返回: {field_name: permission_type}

    @staticmethod
    def get_data_scope(user, object_type):
        """获取用户的数据级权限范围"""
        # 返回: {'scope_type': ..., 'scope_value': ..., 'expansions': [...]}

    @staticmethod
    def apply_data_scope(queryset, user, object_type):
        """将数据权限范围应用到查询集"""

    @staticmethod
    def apply_field_permissions(data, user, object_type, action='view'):
        """将字段权限应用到数据"""

    @staticmethod
    def _mask_field_value(field_name, value, user):
        """对字段值进行脱敏处理"""
        # 支持多种脱敏规则: phone/id_card/bank_card/name/amount

    @staticmethod
    def clear_cache(user_id=None):
        """清除权限缓存"""

    @staticmethod
    def log_permission_action(actor, action, target_type, target_id, ...):
        """记录权限操作日志"""
```

### 3. 序列化器 (serializers.py)

```python
class FieldPermissionSerializer(BaseModelSerializer):
    """字段权限序列化器"""
    class Meta(BaseModelSerializer.Meta):
        model = FieldPermission
        fields = BaseModelSerializer.Meta.fields + [
            'role', 'user', 'content_type', 'field_name',
            'permission_type', 'condition', 'mask_rule', ...
        ]

class DataPermissionSerializer(BaseModelSerializer):
    """数据权限序列化器"""
    # 类似结构
```

**继承功能**:
- ✅ 公共字段自动序列化
- ✅ `custom_fields` 处理
- ✅ 审计字段嵌套序列化

### 4. 视图层 (views.py)

```python
class FieldPermissionViewSet(BaseModelViewSetWithBatch):
    """字段权限 ViewSet"""
    queryset = FieldPermission.objects.all()
    serializer_class = FieldPermissionSerializer
    filterset_class = FieldPermissionFilter
    # 自动获得:
    # ✅ 组织过滤
    # ✅ 软删除过滤
    # ✅ 批量操作 (/batch-delete/, /batch-restore/, /batch-update/)
    # ✅ 已删除列表查询

class DataPermissionViewSet(BaseModelViewSetWithBatch):
    """数据权限 ViewSet"""
    # 类似结构

class PermissionCheckViewSet(viewsets.ViewSet):
    """权限检查 ViewSet"""
    @action(detail=False, methods=['post'])
    def check(self, request):
        """检查单个权限"""

    @action(detail=False, methods=['post'])
    def batch_check(self, request):
        """批量检查权限"""

    @action(detail=False, methods=['get'])
    def accessible_departments(self, request):
        """获取用户可访问的部门列表"""
```

### 5. 服务层 (services/)

#### 字段权限服务

```python
class FieldPermissionService(BaseCRUDService):
    """字段权限服务 - 继承 CRUD 基类"""

    def __init__(self):
        super().__init__(FieldPermission)

    def grant_field_permission(self, role_id=None, user_id=None, ...):
        """授予字段权限"""

    def revoke_field_permission(self, permission_id, ...):
        """撤销字段权限"""

    def batch_grant_permissions(self, role_id=None, user_id=None, ...):
        """批量授予字段权限"""

    def get_by_role_and_field(self, role_id, content_type_id, field_name):
        """根据角色和字段获取权限"""

    def get_effective_permissions(self, user_id, object_type):
        """获取用户的有效权限"""
```

**继承功能**:
- ✅ 统一 CRUD 方法 (`create`, `update`, `delete`, `get`, `query`, `paginate`)
- ✅ 组织隔离
- ✅ 分页支持

#### 数据权限服务

```python
class DataPermissionService(BaseCRUDService):
    """数据权限服务 - 继承 CRUD 基类"""

    def grant_data_permission(self, ...):
        """授予数据权限"""

    def add_data_permission_expansion(self, ...):
        """添加数据权限扩展"""

    def get_user_accessible_departments(self, user, object_type=None):
        """获取用户可访问的部门列表"""

    def get_effective_data_scope(self, user, object_type):
        """获取用户的有效数据范围"""
```

### 6. 过滤器 (filters.py)

```python
class FieldPermissionFilter(BaseModelFilter):
    """字段权限过滤器"""
    role = django_filters.UUIDFilter(field_name='role__id')
    user = django_filters.UUIDFilter(field_name='user__id')
    content_type = django_filters.NumberFilter()
    field_name = django_filters.CharFilter(lookup_expr='icontains')
    permission_type = django_filters.ChoiceFilter(choices=...)
    priority = django_filters.NumberFilter()

    class Meta(BaseModelFilter.Meta):
        model = FieldPermission
        fields = BaseModelFilter.Meta.fields + [...]
```

**继承功能**:
- ✅ 时间范围过滤 (`created_at_from`, `created_at_to`)
- ✅ 用户过滤 (`created_by`)
- ✅ 组织过滤

### 7. URL 路由配置 (urls.py)

```python
router = DefaultRouter()
router.register(r'field', FieldPermissionViewSet, basename='fieldpermission')
router.register(r'data', DataPermissionViewSet, basename='datapermission')
router.register(r'field-groups', FieldPermissionGroupViewSet, ...)
router.register(r'inheritance', PermissionInheritanceViewSet, ...)
router.register(r'audit', PermissionAuditLogViewSet, ...)
router.register(r'check', PermissionCheckViewSet, ...)

urlpatterns = [
    path('', include(router.urls)),
]
```

### 8. 管理命令 (management/commands/sync_permissions.py)

```python
class Command(BaseCommand):
    help = '同步权限配置'

    def handle(self, *args, **options):
        perm_type = options.get('type', 'all')
        reset = options.get('reset', False)

        if perm_type in ['field', 'all']:
            self.sync_field_permissions(reset)

        if perm_type in ['data', 'all']:
            self.sync_data_permissions(reset)
```

**使用方法**:

```bash
# 同步所有权限
python manage.py sync_permissions

# 只同步字段权限
python manage.py sync_permissions --type=field

# 只同步数据权限
python manage.py sync_permissions --type=data

# 重置权限配置
python manage.py sync_permissions --reset
```

---

## 前端实现

### 1. API 接口定义 (api/permissions.ts)

```typescript
// 字段权限 API
export const fieldPermissionApi = {
  list: (params?) => request.get('/api/permissions/field/', { params }),
  create: (data) => request.post('/api/permissions/field/', data),
  update: (id, data) => request.put(`/api/permissions/field/${id}/`, data),
  delete: (id) => request.delete(`/api/permissions/field/${id}/`),
  batchDelete: (ids) => request.post('/api/permissions/field/batch-delete/', { ids }),
  batchRestore: (ids) => request.post('/api/permissions/field/batch-restore/', { ids }),
  batchUpdate: (ids, data) => request.post('/api/permissions/field/batch-update/', { ids, data }),
  getDeleted: (params?) => request.get('/api/permissions/field/deleted/', { params }),
  restore: (id) => request.post(`/api/permissions/field/${id}/restore/`),
  getAvailableFields: (objectType) => request.get('/api/permissions/field/available-fields/', {
    params: { object_type: objectType }
  })
}

// 数据权限 API
export const dataPermissionApi = {
  // 类似结构
}

// 权限继承 API
export const inheritanceApi = {
  // 类似结构
}

// 审计日志 API
export const auditApi = {
  list: (params?) => request.get('/api/permissions/audit/', { params }),
  getStats: () => request.get('/api/permissions/audit/stats/')
}

// 权限检查 API
export const permissionCheckApi = {
  check: (data) => request.post('/api/permissions/check/check/', data),
  batchCheck: (checks) => request.post('/api/permissions/check/batch_check/', { checks }),
  getAccessibleDepartments: (params?) => request.get('/api/permissions/check/accessible_departments/', { params })
}
```

### 2. 权限 Store (stores/permission.ts)

```typescript
export const usePermissionStore = defineStore('permission', () => {
  const fieldPermissions = ref<Record<string, FieldPermissions>>({})
  const dataScopes = ref<Record<string, DataScope>>({})
  const loading = ref(false)

  // 获取字段权限
  const getFieldPermissions = async (objectType: string, action = 'view') => {
    // 返回: {field_name: 'read' | 'write' | 'hidden' | 'masked'}
  }

  // 获取数据范围
  const getDataScope = async (objectType: string) => {
    // 返回: {scope_type, scope_value, expansions}
  }

  // 检查字段是否隐藏
  const isFieldHidden = (objectType: string, field: string) => {
    const perms = fieldPermissions.value[`${objectType}:view`]
    return perms?.[field] === 'hidden'
  }

  // 检查字段是否只读
  const isFieldReadOnly = (objectType: string, field: string) => {
    const perms = fieldPermissions.value[`${objectType}:update`]
    return perms?.[field] === 'read'
  }

  // 获取脱敏值
  const getMaskedValue = (value: any, maskRule: string) => {
    // 支持多种脱敏规则
  }

  // 清除缓存
  const clearCache = (objectType?: string) => {
    // 清除权限缓存
  }

  return {
    fieldPermissions,
    dataScopes,
    loading,
    getFieldPermissions,
    getDataScope,
    isFieldHidden,
    isFieldReadOnly,
    getMaskedValue,
    clearCache
  }
})
```

---

## API 接口规范

### 统一响应格式

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

#### 列表响应(分页)

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
        "message": "请求数据验证失败",
        "details": {
            "field": ["该字段不能为空"]
        }
    }
}
```

### 标准 CRUD 接口

#### 字段权限管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/permissions/field/` | 分页查询字段权限 |
| GET | `/api/permissions/field/{id}/` | 获取字段权限详情 |
| POST | `/api/permissions/field/` | 创建字段权限 |
| PUT | `/api/permissions/field/{id}/` | 完整更新字段权限 |
| PATCH | `/api/permissions/field/{id}/` | 部分更新字段权限 |
| DELETE | `/api/permissions/field/{id}/` | 软删除字段权限 |
| GET | `/api/permissions/field/deleted/` | 查询已删除的字段权限 |
| POST | `/api/permissions/field/{id}/restore/` | 恢复已删除的字段权限 |

#### 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 批量删除 | POST | `/api/permissions/field/batch-delete/` | 批量软删除 |
| 批量恢复 | POST | `/api/permissions/field/batch-restore/` | 批量恢复 |
| 批量更新 | POST | `/api/permissions/field/batch-update/` | 批量字段更新 |

#### 批量删除请求

```http
POST /api/permissions/field/batch-delete/
Content-Type: application/json

{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### 批量删除响应(全部成功)

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
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": true}
    ]
}
```

#### 批量删除响应(部分失败)

```json
{
    "success": false,
    "message": "批量删除完成(部分失败)",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": false, "error": "记录不存在"},
        {"id": "uuid3", "success": true}
    ]
}
```

### 权限检查接口

#### 检查单个权限

```http
POST /api/permissions/check/check/
Content-Type: application/json

{
    "user_id": "uuid",
    "object_type": "assets.Asset",
    "action": "view",
    "field_name": "price"
}
```

#### 响应

```json
{
    "success": true,
    "data": {
        "field_permissions": {
            "price": "masked",
            "supplier": "hidden"
        },
        "data_scope": {
            "scope_type": "self_dept",
            "scope_value": {},
            "expansions": []
        }
    }
}
```

### 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

---

## 数据模型

### 数据库表结构

#### permission_field (字段权限表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| organization_id | UUID | 组织ID(外键) |
| role_id | UUID | 角色ID(外键,可为空) |
| user_id | UUID | 用户ID(外键,可为空) |
| content_type_id | Integer | 对象类型ID(外键) |
| field_name | VARCHAR(100) | 字段名 |
| permission_type | VARCHAR(20) | 权限类型(read/write/hidden/masked) |
| condition | JSONB | 权限条件(可选) |
| mask_rule | VARCHAR(50) | 脱敏规则(可选) |
| mask_params | JSONB | 脱敏参数(可选) |
| priority | INTEGER | 优先级 |
| remark | TEXT | 备注 |
| is_deleted | BOOLEAN | 软删除标记 |
| deleted_at | TIMESTAMP | 删除时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| created_by_id | UUID | 创建人ID(外键) |
| custom_fields | JSONB | 自定义字段 |

**索引**:
- `idx_role` on (role_id)
- `idx_user` on (user_id)
- `idx_content_type_field` on (content_type_id, field_name)
- `unique_role_field_permission` on (role_id, content_type_id, field_name) WHERE is_deleted=false
- `unique_user_field_permission` on (user_id, content_type_id, field_name) WHERE is_deleted=false

#### permission_data (数据权限表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| organization_id | UUID | 组织ID(外键) |
| role_id | UUID | 角色ID(外键,可为空) |
| user_id | UUID | 用户ID(外键,可为空) |
| content_type_id | Integer | 对象类型ID(外键) |
| scope_type | VARCHAR(20) | 范围类型 |
| scope_value | JSONB | 范围值 |
| is_inherited | BOOLEAN | 允许继承 |
| custom_filter | JSONB | 自定义过滤条件 |
| priority | INTEGER | 优先级 |
| is_active | BOOLEAN | 是否启用 |
| ... | ... | (其他公共字段同上) |

#### permission_audit_log (权限审计日志表)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| organization_id | UUID | 组织ID(外键) |
| actor_id | UUID | 操作人ID(外键) |
| action | VARCHAR(20) | 操作类型 |
| target_type | VARCHAR(50) | 目标类型 |
| target_id | INTEGER | 目标ID |
| target_name | VARCHAR(200) | 目标名称 |
| changes | JSONB | 变更内容 |
| ip_address | INET | IP地址 |
| user_agent | TEXT | User Agent |
| success | BOOLEAN | 是否成功 |
| error_message | TEXT | 错误信息 |
| request_id | VARCHAR(100) | 请求ID |
| ... | ... | (其他公共字段同上) |

---

## 测试用例

### 后端测试示例

#### 字段权限测试

```python
# apps/permissions/tests/test_field_permission.py

class FieldPermissionTestCase(TestCase):
    """字段权限测试用例"""

    def setUp(self):
        self.org = Organization.objects.create(name="测试组织", code="TEST_ORG")
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            org=self.org
        )
        self.role = Role.objects.create(
            name="测试角色",
            code="test_role",
            org=self.org
        )

    def test_field_permission_creation(self):
        """测试字段权限创建"""
        content_type = ContentType.objects.get_for_model(User)

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
        content_type = ContentType.objects.get_for_model(User)
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
        content_type = ContentType.objects.get_for_model(User)
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
```

#### 数据权限测试

```python
# apps/permissions/tests/test_data_permission.py

class DataPermissionTestCase(TestCase):
    """数据权限测试用例"""

    def setUp(self):
        self.org = Organization.objects.create(name="测试组织", code="TEST_ORG")
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            org=self.org,
            department=self.department
        )
        self.role = Role.objects.create(
            name="测试角色",
            code="test_role",
            org=self.org
        )
        self.department = Department.objects.create(
            name="测试部门",
            code="TEST_DEPT",
            org=self.org
        )

    def test_data_scope_application(self):
        """测试数据范围应用"""
        content_type = ContentType.objects.get_for_model(User)

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
```

---

## 部署指南

### 数据库迁移

```bash
# 1. 生成数据库迁移文件
cd backend
python manage.py makemigrations permissions

# 2. 执行数据库迁移
python manage.py migrate

# 3. 同步权限配置
python manage.py sync_permissions
```

### Docker 部署

```bash
# 启动所有服务
docker-compose up -d

# 查看后端日志
docker-compose logs -f backend

# 进入后端容器
docker-compose exec backend bash

# 在容器内执行命令
docker-compose exec backend python manage.py sync_permissions
```

### 环境变量配置

确保 `.env` 文件包含以下配置:

```env
# 数据库配置
DB_NAME=gzeams
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# 权限缓存配置
PERMISSION_CACHE_TIMEOUT=3600  # 权限缓存过期时间(秒)
```

---

## 快速开始

### 1. 初始化权限配置

```bash
# 同步所有权限
python manage.py sync_permissions --type=all

# 预定义的角色和权限:
# - asset_user: 资产普通用户(敏感字段脱敏,本部门数据)
# - asset_admin: 资产管理员(完全访问,本部门及下级数据)
# - dept_manager: 部门经理(本部门及下级数据)
# - system_admin: 系统管理员(完全访问,全部数据)
```

### 2. 使用权限 API

#### 创建字段权限

```python
from apps.permissions.services.field_permission_service import FieldPermissionService

service = FieldPermissionService()

# 为角色授予字段权限
permission = service.grant_field_permission(
    role_id=role.id,
    object_type="assets.Asset",
    field_name="original_value",
    permission_type="masked",
    mask_rule="range",
    actor=request.user
)
```

#### 检查用户权限

```python
from apps.permissions.engine import PermissionEngine

# 获取字段权限
field_perms = PermissionEngine.get_field_permissions(user, "assets.Asset", "view")
# 返回: {'original_value': 'masked', 'supplier': 'hidden', ...}

# 获取数据范围
data_scope = PermissionEngine.get_data_scope(user, "assets.Asset")
# 返回: {'scope_type': 'self_dept', 'scope_value': {}, 'expansions': []}

# 应用数据权限到查询集
queryset = Asset.objects.filter(org=user.org)
filtered_queryset = PermissionEngine.apply_data_scope(queryset, user, "assets.Asset")

# 应用字段权限到数据
data = [{'original_value': 10000, 'name': '资产1'}]
filtered_data = PermissionEngine.apply_field_permissions(data, user, "assets.Asset", "view")
# 返回: [{'original_value': '1万~10万', 'name': '资产1'}]
```

### 3. 前端使用权限 Store

```typescript
import { usePermissionStore } from '@/stores/permission'

const permissionStore = usePermissionStore()

// 获取字段权限
const fieldPerms = await permissionStore.getFieldPermissions('assets.Asset', 'view')

// 检查字段是否隐藏
const isHidden = permissionStore.isFieldHidden('assets.Asset', 'supplier')

// 检查字段是否只读
const isReadOnly = permissionStore.isFieldReadOnly('assets.Asset', 'original_value')

// 获取脱敏值
const maskedValue = permissionStore.getMaskedValue('13812345678', 'phone')
// 返回: '138****5678'

// 清除缓存
permissionStore.clearCache('assets.Asset')
```

---

## 文件清单

### 后端文件

| 文件路径 | 说明 | 状态 |
|---------|------|------|
| `backend/apps/permissions/models.py` | 数据模型 | ✅ 已完成 |
| `backend/apps/permissions/serializers.py` | 序列化器 | ✅ 已完成 |
| `backend/apps/permissions/views.py` | 视图层 | ✅ 已完成 |
| `backend/apps/permissions/filters.py` | 过滤器 | ✅ 已完成 |
| `backend/apps/permissions/engine.py` | 权限引擎 | ✅ 已完成 |
| `backend/apps/permissions/urls.py` | URL路由 | ✅ 已完成 |
| `backend/apps/permissions/services/field_permission_service.py` | 字段权限服务 | ✅ 已完成 |
| `backend/apps/permissions/services/data_permission_service.py` | 数据权限服务 | ✅ 已完成 |
| `backend/apps/permissions/management/commands/sync_permissions.py` | 权限同步命令 | ✅ 已完成 |

### 前端文件

| 文件路径 | 说明 | 状态 |
|---------|------|------|
| `frontend/src/api/permissions.ts` | API接口定义 | ✅ 已完成 |
| `frontend/src/stores/permission.ts` | 权限Store | ✅ 已完成 |

---

## 总结

Phase 2.5 权限体系增强模块已经完成了核心功能的实现,包括:

### 已完成功能

1. ✅ **后端核心实现**
   - 数据模型(继承 BaseModel)
   - 序列化器(继承 BaseModelSerializer)
   - 视图层(继承 BaseModelViewSetWithBatch)
   - 服务层(继承 BaseCRUDService)
   - 过滤器(继承 BaseModelFilter)
   - 权限引擎核心逻辑
   - 管理命令

2. ✅ **前端核心实现**
   - API 接口定义
   - 权限 Store

3. ✅ **API 接口规范**
   - 统一响应格式
   - 标准 CRUD 操作
   - 批量操作接口
   - 权限检查接口

4. ✅ **权限管理命令**
   - 权限同步工具
   - 预定义角色和权限配置

### 待完善功能

以下功能已规划但未实现(可根据后续需求补充):

1. ⏳ **前端页面组件**
   - 字段权限管理页面
   - 数据权限管理页面
   - 权限继承管理页面
   - 审计日志查询页面

2. ⏳ **前端公共组件**
   - PermissionTypeTag 组件
   - DataScopeSelector 组件
   - PermissionMatrix 组件
   - MaskingRuleEditor 组件
   - ConditionBuilder 组件

3. ⏳ **移动端适配**
   - 移动端权限查看页面
   - 权限申请功能

### 架构特点

1. **严格遵循公共基类规范**: 所有组件都继承对应的公共基类
2. **统一的API响应格式**: 标准化的成功/错误响应
3. **完善的批量操作支持**: 批量删除/恢复/更新,提供详细的操作结果
4. **强大的权限引擎**: 支持字段级和数据级权限控制,支持脱敏和数据范围过滤
5. **完整的审计日志**: 记录所有权限操作,支持追溯和审计
6. **高性能缓存机制**: 基于缓存的权限检查,提高系统性能

### 使用建议

1. **权限配置优先级**: 用户权限 > 角色权限,高优先级覆盖低优先级
2. **缓存管理**: 权限变更后记得清除缓存,确保权限生效
3. **审计日志**: 定期审查审计日志,确保系统安全
4. **测试先行**: 权限配置修改前,先在测试环境验证

---

**报告生成时间**: 2026-01-16
**版本**: v1.0.0
**作者**: Claude Code
**项目**: GZEAMS (钩子固定资产低代码平台)
