# Phase 2.5 权限增强模块 - 快速参考指南

**项目**: GZEAMS (钩子固定资产低代码平台)
**模块**: Phase 2.5 - 权限体系增强
**快速参考**: 开发者指南

---

## 📚 目录

1. [核心概念](#核心概念)
2. [后端使用](#后端使用)
3. [前端使用](#前端使用)
4. [API 接口](#api-接口)
5. [常见问题](#常见问题)
6. [故障排查](#故障排查)

---

## 核心概念

### 权限类型

#### 1. 字段权限 (FieldPermission)

控制用户对特定字段的访问权限:

| 权限类型 | 说明 | 示例 |
|---------|------|------|
| `read` | 只读 | 用户可以看到字段但不能修改 |
| `write` | 可写 | 用户可以查看和修改字段 |
| `hidden` | 隐藏 | 用户完全看不到该字段 |
| `masked` | 脱敏 | 用户看到的是脱敏后的值(如 `138****5678`) |

#### 2. 数据权限 (DataPermission)

控制用户可以访问的数据范围:

| 范围类型 | 说明 | 适用场景 |
|---------|------|---------|
| `all` | 全部数据 | 系统管理员 |
| `self_dept` | 本部门数据 | 部门员工 |
| `self_and_sub` | 本部门及下级数据 | 部门经理 |
| `specified` | 指定部门数据 | 跨部门协作 |
| `custom` | 自定义规则 | 复杂业务场景 |

---

## 后端使用

### 1. 权限检查

#### 获取字段权限

```python
from apps.permissions.engine import PermissionEngine

# 获取用户对资产模型的字段权限
field_perms = PermissionEngine.get_field_permissions(user, "assets.Asset", "view")
# 返回: {'original_value': 'masked', 'supplier': 'hidden', 'name': 'read'}
```

#### 获取数据范围

```python
# 获取用户的数据访问范围
data_scope = PermissionEngine.get_data_scope(user, "assets.Asset")
# 返回: {'scope_type': 'self_dept', 'scope_value': {}, 'expansions': []}
```

#### 应用数据权限到查询集

```python
# 在 ViewSet 中应用数据权限
queryset = Asset.objects.filter(org=user.org)
filtered_queryset = PermissionEngine.apply_data_scope(queryset, user, "assets.Asset")
```

#### 应用字段权限到数据

```python
# 对数据进行脱敏处理
data = [
    {'original_value': 10000, 'supplier': '供应商A', 'name': '资产1'}
]
filtered_data = PermissionEngine.apply_field_permissions(data, user, "assets.Asset", "view")
# 返回: [{'original_value': '1万~10万', 'name': '资产1'}]  # supplier 被隐藏
```

### 2. 权限管理

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
    mask_rule="range",  # 金额范围脱敏
    priority=10,
    actor=request.user
)
```

#### 批量授予字段权限

```python
# 批量配置多个字段
field_configs = [
    {'field_name': 'original_value', 'permission_type': 'masked', 'mask_rule': 'range'},
    {'field_name': 'supplier', 'permission_type': 'hidden'},
    {'field_name': 'purchase_date', 'permission_type': 'read'}
]

count = service.batch_grant_permissions(
    role_id=role.id,
    object_type="assets.Asset",
    field_configs=field_configs,
    actor=request.user
)
print(f"成功创建 {count} 条权限配置")
```

#### 创建数据权限

```python
from apps.permissions.services.data_permission_service import DataPermissionService

service = DataPermissionService()

# 为角色授予数据权限
permission = service.grant_data_permission(
    role_id=role.id,
    object_type="assets.Asset",
    scope_type="self_and_sub",  # 本部门及下级
    scope_value={},
    priority=10,
    actor=request.user
)
```

### 3. 权限继承

#### 创建角色继承关系

```python
from apps.permissions.models import PermissionInheritance

# 部门经理完全继承普通员工权限,并添加额外权限
inheritance = PermissionInheritance.objects.create(
    parent_role=employee_role,
    child_role=manager_role,
    inherit_type="full",
    org=org,
    created_by=request.user
)
```

### 4. 权限缓存管理

```python
# 清除特定用户的权限缓存
PermissionEngine.clear_cache(user_id=user.id)

# 清除所有权限缓存
PermissionEngine.clear_cache()
```

### 5. 在 ViewSet 中使用权限混合

```python
from apps.permissions.engine import PermissionEngine
from apps.permissions.permissions import FieldPermissionMixin

class AssetViewSet(BaseModelViewSetWithBatch, FieldPermissionMixin):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def get_queryset(self):
        """自动应用数据权限"""
        queryset = super().get_queryset()
        return PermissionEngine.apply_data_scope(
            queryset,
            self.request.user,
            "assets.Asset"
        )

    def list(self, request, *args, **kwargs):
        """自动应用字段权限"""
        response = super().list(request, *args, **kwargs)

        # 对返回的数据进行字段权限过滤
        response.data['results'] = PermissionEngine.apply_field_permissions(
            response.data['results'],
            request.user,
            "assets.Asset",
            "view"
        )
        return response
```

---

## 前端使用

### 1. 权限检查

```typescript
import { usePermissionStore } from '@/stores/permission'

const permissionStore = usePermissionStore()

// 获取字段权限
const fieldPerms = await permissionStore.getFieldPermissions('assets.Asset', 'view')
// 返回: {'original_value': 'masked', 'supplier': 'hidden', ...}

// 获取数据范围
const dataScope = await permissionStore.getDataScope('assets.Asset')
// 返回: {scope_type: 'self_dept', scope_value: {}, expansions: []}
```

### 2. 字段权限判断

```typescript
// 检查字段是否隐藏
const isHidden = permissionStore.isFieldHidden('assets.Asset', 'supplier')
if (isHidden) {
  // 不显示该字段
}

// 检查字段是否只读
const isReadOnly = permissionStore.isFieldReadOnly('assets.Asset', 'original_value')
if (isReadOnly) {
  // 设置字段为只读状态
}
```

### 3. 数据脱敏

```typescript
// 获取脱敏值
const maskedPhone = permissionStore.getMaskedValue('13812345678', 'phone')
// 返回: '138****5678'

const maskedIdCard = permissionStore.getMaskedValue('110101199001011234', 'id_card')
// 返回: '110***********1234'

const maskedAmount = permissionStore.getMaskedValue(5000.50, 'amount')
// 返回: '1,000~10,000'
```

### 4. API 调用

```typescript
import { fieldPermissionApi, dataPermissionApi, permissionCheckApi } from '@/api/permissions'

// 创建字段权限
await fieldPermissionApi.create({
  role_id: 'role-uuid',
  content_type: contentTypeId,
  field_name: 'original_value',
  permission_type: 'masked',
  mask_rule: 'range'
})

// 批量删除
await fieldPermissionApi.batchDelete(['uuid1', 'uuid2', 'uuid3'])

// 检查权限
const { data } = await permissionCheckApi.check({
  object_type: 'assets.Asset',
  action: 'view',
  field_name: 'price'
})
```

### 5. 在组件中使用权限指令

```vue
<template>
  <!-- 字段权限指令 -->
  <el-input
    v-field-permission="{objectType: 'assets.Asset', field: 'original_value', action: 'update'}"
    v-model="form.original_value"
  />
</template>

<script setup>
import { usePermissionStore } from '@/stores/permission'

const permissionStore = usePermissionStore()

// 组件挂载时加载权限
onMounted(async () => {
  await permissionStore.getFieldPermissions('assets.Asset', 'update')
})
</script>
```

---

## API 接口

### 字段权限接口

#### 创建字段权限

```http
POST /api/permissions/field/
Content-Type: application/json

{
    "role_id": "uuid",
    "content_type": 123,
    "field_name": "original_value",
    "permission_type": "masked",
    "mask_rule": "range",
    "priority": 10,
    "remark": "资产原价脱敏"
}
```

#### 批量删除

```http
POST /api/permissions/field/batch-delete/
Content-Type: application/json

{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 数据权限接口

#### 创建数据权限

```http
POST /api/permissions/data/
Content-Type: application/json

{
    "role_id": "uuid",
    "content_type": 123,
    "scope_type": "self_and_sub",
    "scope_value": {},
    "is_inherited": true,
    "priority": 10
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
    "action": "view"
}
```

#### 响应

```json
{
    "success": true,
    "data": {
        "field_permissions": {
            "original_value": "masked",
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

#### 获取可访问部门

```http
GET /api/permissions/check/accessible-departments/?user_id=uuid&object_type=assets.Asset
```

---

## 常见问题

### Q1: 如何配置敏感字段脱敏?

```python
# 方法1: 通过 API 创建
service.grant_field_permission(
    role_id=role.id,
    object_type="assets.Asset",
    field_name="phone",
    permission_type="masked",
    mask_rule="phone"  # 手机号脱敏: 138****5678
)

# 方法2: 批量配置
field_configs = [
    {'field_name': 'phone', 'permission_type': 'masked', 'mask_rule': 'phone'},
    {'field_name': 'id_card', 'permission_type': 'masked', 'mask_rule': 'id_card'},
    {'field_name': 'bank_card', 'permission_type': 'masked', 'mask_rule': 'bank_card'},
]
service.batch_grant_permissions(role.id, "assets.Asset", field_configs)
```

### Q2: 如何限制用户只能看到本部门数据?

```python
# 创建数据权限
service.grant_data_permission(
    role_id=role.id,
    object_type="assets.Asset",
    scope_type="self_dept",
    scope_value={}
)

# 在 ViewSet 中自动应用
class AssetViewSet(BaseModelViewSetWithBatch):
    def get_queryset(self):
        queryset = super().get_queryset()
        return PermissionEngine.apply_data_scope(
            queryset,
            self.request.user,
            "assets.Asset"
        )
```

### Q3: 如何实现权限继承?

```python
# 创建角色继承关系
PermissionInheritance.objects.create(
    parent_role=parent_role,  # 父角色
    child_role=child_role,    # 子角色
    inherit_type="full",      # 完全继承
    org=org
)

# 子角色自动拥有父角色的所有权限
# 并可以根据需要覆盖部分权限
```

### Q4: 如何清除权限缓存?

```python
# 清除特定用户缓存
PermissionEngine.clear_cache(user_id=user.id)

# 清除所有缓存
PermissionEngine.clear_cache()

# 前端清除缓存
permissionStore.clearCache('assets.Asset')
```

---

## 故障排查

### 问题1: 权限不生效

**可能原因**:
1. 权限缓存未清除
2. 优先级配置错误
3. 对象类型名称不匹配

**解决方案**:
```bash
# 1. 清除缓存
python manage.py shell
>>> from apps.permissions.engine import PermissionEngine
>>> PermissionEngine.clear_cache()

# 2. 检查权限配置
>>> from apps.permissions.models import FieldPermission
>>> FieldPermission.objects.filter(role=role).values('field_name', 'permission_type', 'priority')

# 3. 检查对象类型
>>> from django.contrib.contenttypes.models import ContentType
>>> ContentType.objects.filter(model='asset')
```

### 问题2: 脱敏规则不生效

**可能原因**:
1. 字段名不匹配脱敏规则
2. 权限类型不是 `masked`
3. 前端未应用脱敏

**解决方案**:
```python
# 检查权限配置
perm = FieldPermission.objects.get(field_name='phone')
print(perm.permission_type)  # 应该是 'masked'
print(perm.mask_rule)        # 应该是 'phone'

# 测试脱敏
from apps.permissions.engine import PermissionEngine
result = PermissionEngine._mask_field_value('phone', '13812345678', None)
print(result)  # 应该是 '138****5678'
```

### 问题3: 数据权限过滤不正确

**可能原因**:
1. 用户未设置部门
2. 部门层级关系不正确
3. 权限范围类型选择错误

**解决方案**:
```python
# 检查用户部门
user.department  # 应该不为 None

# 检查部门层级
from apps.organizations.models import Department
dept_ids = Department.get_descendant_ids(user.department.id)
print(dept_ids)  # 应该包含下级部门ID

# 测试数据权限应用
from apps.permissions.engine import PermissionEngine
data_scope = PermissionEngine.get_data_scope(user, "assets.Asset")
print(data_scope)  # 检查 scope_type 和 scope_value
```

---

## 快速命令参考

### 管理命令

```bash
# 同步所有权限
python manage.py sync_permissions

# 同步字段权限
python manage.py sync_permissions --type=field

# 同步数据权限
python manage.py sync_permissions --type=data

# 重置权限配置
python manage.py sync_permissions --reset
```

### Django Shell

```python
# 进入 shell
python manage.py shell

# 快速测试权限
>>> from apps.permissions.engine import PermissionEngine
>>> from apps.accounts.models import User
>>> user = User.objects.first()
>>> perms = PermissionEngine.get_field_permissions(user, "assets.Asset")
>>> print(perms)

# 清除缓存
>>> PermissionEngine.clear_cache()
```

---

## 相关文档

- [完整实现报告](./PHASE2_5_PERMISSION_ENHANCEMENT_IMPLEMENTATION_REPORT.md)
- [后端 PRD](./docs/plans/phase2_5_permission_enhancement/backend.md)
- [前端 PRD](./docs/plans/phase2_5_permission_enhancement/frontend.md)
- [公共基类规范](./CLAUDE.md)

---

**文档版本**: v1.0.0
**更新日期**: 2026-01-16
**维护者**: Claude Code
