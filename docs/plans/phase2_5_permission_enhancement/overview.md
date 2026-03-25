# Phase 2.5: 权限体系增强 - 总览

## 概述

本模块在现有RBAC权限系统基础上，增强为更细粒度的权限控制能力，支持字段级权限和数据级权限（行级权限），满足企业复杂的权限管理需求。

---

## 1. 业务背景

### 1.1 当前痛点

| 痛点 | 说明 | 影响 |
|------|------|------|
| **权限粒度粗** | 仅支持对象级权限，无法控制字段级别 | 敏感信息可能泄露 |
| **数据无隔离** | 所有数据可见，无法按部门/区域隔离 | 跨部门数据访问冲突 |
| **权限不可继承** | 无法基于组织架构自动继承权限 | 权限配置工作量大 |
| **审计不完善** | 缺少权限变更审计记录 | 安全合规风险 |

### 1.2 业务目标

- **字段级控制**：支持对单个字段的读/写/隐藏权限
- **数据级隔离**：基于组织架构实现数据行级权限
- **权限可继承**：支持权限的自动继承机制
- **完整审计**：记录所有权限变更和访问日志

---

## 2. 权限模型架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         增强权限体系                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │
│  │  用户          │   │  角色          │   │  权限          │         │
│  │  User          │ → │  Role          │ → │  Permission    │         │
│  └───────────────┘   └───────────────┘   └───────────────┘         │
│           ↓                   ↓                   ↓                     │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │
│  │  字段权限      │   │  数据权限      │   │  继承关系      │         │
│  │  FieldPerm    │   │  DataPerm     │   │  Inheritance   │         │
│  └───────────────┘   └───────────────┘   └───────────────┘         │
│           ↓                   ↓                   ↓                     │
│  ┌───────────────────────────┴───────────────────────────┐         │
│  │                    权限引擎                        │         │
│  │  - 权限检查                                        │         │
│  │  - 数据过滤                                        │         │
│  │  - 字段脱敏                                        │         │
│  └─────────────────────────────────────────────────────┘         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 功能范围

### 3.1 字段级权限 (Field Permission)

| 功能点 | 说明 |
|--------|------|
| 字段权限配置 | 为角色/用户配置单个字段的读/写/隐藏权限 |
| 权限类型 | 只读(read)、可写(write)、隐藏(hidden)、脱敏(masked) |
| 权限优先级 | 用户级 > 角色级 > 默认 |
| 动态权限 | 根据数据内容动态控制权限 |
| 批量配置 | 支持批量配置多个字段的权限 |

### 3.2 数据级权限 (Row-Level Permission)

| 功能点 | 说明 |
|--------|------|
| 基于部门的权限 | 用户只能访问本部门及下属部门的数据 |
| 基于区域的权限 | 用户只能访问所属区域的数据 |
| 自定义数据权限 | 支持自定义数据范围规则 |
| 权限继承 | 支持权限从上级部门继承 |
| 权限扩展 | 可授予跨部门访问权限 |

### 3.3 权限继承 (Permission Inheritance)

| 功能点 | 说明 |
|--------|------|
| 组织继承 | 子部门继承父部门权限 |
| 角色继承 | 子角色继承父角色权限 |
| 传递控制 | 可控制权限是否向下传递 |
| 继承查看 | 可查看权限继承关系树 |

### 3.4 权限审计 (Permission Audit)

| 功能点 | 说明 |
|--------|------|
| 变更记录 | 记录权限配置变更历史 |
| 访问日志 | 记录用户访问敏感数据的日志 |
| 异常检测 | 检测异常的权限访问行为 |
| 审计报告 | 生成权限审计报告 |

---

## 4. 字段级权限设计

### 4.1 权限类型定义

| 类型 | 代码 | 说明 |
|------|------|------|
| 只读 | read | 可以查看字段，但不能修改 |
| 可写 | write | 可以查看和修改字段 |
| 隐藏 | hidden | 字段不可见 |
| 脱敏 | masked | 可以查看但敏感内容脱敏显示 |

### 4.2 脱敏规则

| 字段类型 | 脱敏规则 | 示例 |
|----------|----------|------|
| 手机号 | 保留前3后4位 | 138****1234 |
| 身份证 | 保留前3后4位 | 110***********1234 |
| 银行卡 | 保留后4位 | ************5678 |
| 金额 | 显示范围 | 1,000~10,000 |
| 姓名 | 隐藏姓氏 | *三 |

### 4.3 字段权限配置示例

```json
{
  "object": "Asset",
  "fields": [
    {
      "name": "original_value",
      "permission": "masked",
      "mask_rule": "range",
      "mask_params": {"show_digits": false}
    },
    {
      "name": "supplier",
      "permission": "hidden",
      "condition": "user.role != 'admin'"
    },
    {
      "name": "description",
      "permission": "read"
    }
  ]
}
```

---

## 5. 数据级权限设计

### 5.1 权限范围类型

| 类型 | 代码 | 说明 |
|------|------|------|
| 全部数据 | all | 可以访问所有数据 |
| 本部门 | self_dept | 只能访问本部门数据 |
| 本部门及下级 | self_and_sub | 访问本部门及下级部门数据 |
| 自定义 | custom | 自定义数据范围 |
| 指定部门 | specified | 访问指定部门数据 |

### 5.2 数据权限规则

```python
# 数据权限规则配置
DATA_PERMISSION_RULES = {
    'Asset': {
        'default': 'self_dept',
        'inherit_from': 'department',
        'fields': ['department'],
        'permissions': [
            {
                'role': 'dept_admin',
                'scope': 'self_and_sub'
            },
            {
                'role': 'asset_user',
                'scope': 'self_dept'
            },
            {
                'role': 'admin',
                'scope': 'all'
            }
        ]
    },
    'PurchaseRequest': {
        'default': 'self_dept',
        'inherit_from': 'department',
        'fields': ['applicant_department'],
        'expand_permissions': [
            {
                'field': 'current_approver',
                'scope': 'specified',
                'when': 'is_approver'
            }
        ]
    }
}
```

---

## 6. 权限引擎设计

### 6.1 权限检查流程

```
用户请求
    ↓
┌─────────────────┐
│  身份认证        │
│  Authentication  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  加载用户权限    │
│  Load Permissions│
│  - 角色权限      │
│  - 用户权限      │
│  - 继承权限      │
└────────┬────────┘
         ↓
┌─────────────────┐
│  数据级权限过滤  │
│  Row Filtering   │
│  - 应用数据范围  │
│  - 过滤可见数据  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  字段级权限处理  │
│  Field Processing│
│  - 移除隐藏字段  │
│  - 应用脱敏规则  │
│  - 设置只读字段  │
└────────┬────────┘
         ↓
┌─────────────────┐
│  返回处理后的数据│
│  Return Data     │
└─────────────────┘
```

### 6.2 权限缓存机制

```python
# 权限缓存设计
PERMISSION_CACHE_KEYS = {
    'user_permissions': 'perm:user:{user_id}',
    'role_permissions': 'perm:role:{role_id}',
    'data_scope': 'perm:datascope:{user_id}:{object}',
    'field_permissions': 'perm:field:{role_id}:{object}',
}

# 缓存策略
- 用户权限缓存：1小时
- 数据权限缓存：30分钟
- 字段权限缓存：直到配置变更
```

---

## 7. 数据模型关系

```
Permission (系统权限) [Django内置]
    │
    ├── RolePermission (角色权限关联)
    │   └── role → Role
    │   └── permission → Permission
    │
    └── UserPermission (用户权限关联)
        └── user → User
        └── permission → Permission

FieldPermission (字段权限)
    ├── role → Role
    ├── object_type ( ContentType)
    ├── field_name
    ├── permission_type (read/write/hidden/masked)
    └── condition (JSON)

DataPermission (数据权限)
    ├── role → Role
    ├── object_type
    ├── scope_type (all/self_dept/custom)
    ├── scope_value (JSON)
    └── is_inherited

PermissionInheritance (权限继承)
    ├── ancestor_role → Role
    ├── descendant_role → Role
    └── inherit_type (full/partial)

PermissionAuditLog (权限审计日志)
    ├── user → User
    ├── action (create/update/delete/grant/revoke)
    ├── target_type (role/permission/user)
    ├── target_id
    ├── changes (JSON)
    └── ip_address
```

---

## 8. 与其他模块的集成

| 集成点 | 关联模块 | 集成方式 |
|--------|---------|---------|
| 用户角色 | accounts | 复用现有User/Role模型 |
| 组织架构 | organizations | 基于部门树实现数据权限继承 |
| 工作流 | workflows | 流程节点权限控制 |
| API接口 | DRF | 自定义权限类实现 |
| 前端渲染 | Vue3 | 基于权限控制字段显示 |

---

## 9. API权限控制示例

```python
# 视图层权限控制示例

class AssetViewSet(ModelViewSet):
    """资产视图集 - 增强权限控制"""

    def get_queryset(self):
        """应用数据级权限"""
        queryset = Asset.objects.all()

        # 获取用户数据权限范围
        data_scope = PermissionEngine.get_data_scope(
            user=self.request.user,
            object_type='Asset'
        )

        # 应用数据过滤
        queryset = PermissionEngine.apply_data_scope(
            queryset,
            data_scope,
            self.request.user
        )

        return queryset

    def get_serializer(self, *args, **kwargs):
        """应用字段级权限"""
        serializer_class = super().get_serializer_class(*args, **kwargs)

        # 获取字段权限
        field_permissions = PermissionEngine.get_field_permissions(
            user=self.request.user,
            object_type='Asset',
            action=self.action
        )

        # 动态调整字段
        if hasattr(serializer_class, 'Meta'):
            # 移除隐藏字段
            hidden_fields = [
                f for f, p in field_permissions.items()
                if p == 'hidden'
            ]
            serializer_class.Meta.exclude = hidden_fields

        return serializer_class(*args, **kwargs)
```

---

## 10. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 模型设计、权限引擎、API |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 权限管理界面 |
| [test.md](./test.md) | 测试计划 |

---

## 11. 后续任务

1. 实现字段权限模型和服务
2. 实现数据权限模型和服务
3. 实现权限继承机制
4. 实现权限审计日志
5. 集成到现有API
6. 前端权限管理界面
7. 权限测试和验证
