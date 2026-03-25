# Phase 1.2: 多组织数据隔离架构 - 总览

## 功能概述

实现严格的多组织数据隔离机制,确保SaaS模式下不同租户间的数据完全隔离,防止跨组织数据泄露,支持集团管控、独立核算、跨组织调拨等复杂业务场景。

---

## 业务场景

### 1.1 集团管控场景

| 场景 | 说明 | 数据隔离需求 |
|------|------|-------------|
| **集团总部** | 管理多个子公司资产 | 总部可查看所有子公司数据(需权限) |
| **子公司独立运营** | 各公司独立核算资产 | 子公司只能查看本公司数据 |
| **跨公司调拨** | 资产在子公司间流转 | 需审批流程,数据归属变更 |
| **数据安全** | 防止商业机密泄露 | 严格隔离不同组织数据 |

### 1.2 核心业务流程

```
┌─────────────────────────────────────────────────────────────┐
│                     集团管控场景                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  集团总部 (Organization A)                                    │
│  ├── 资产: [A001, A002, A003]                                │
│  ├── 用户: [张三(管理员), 李四(财务)]                        │
│  └── 权限: 可查看所有子公司数据                               │
│                                                               │
│  子公司B (Organization B)                                    │
│  ├── 资产: [B001, B002]                                      │
│  ├── 用户: [王五(管理员), 赵六(资产)]                         │
│  └── 权限: 只能查看本公司数据                                 │
│                                                               │
│  跨组织调拨流程:                                              │
│  1. 王五发起: A001 资产从 A 调拨到 B                         │
│  2. 张三审批: 集团总部批准                                   │
│  3. 王五确认: 子公司B接收                                    │
│  4. 数据变更: A001.organization = B                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 用户角色与权限

### 2.1 角色定义

| 角色 | 权限范围 | 组织切换权限 |
|------|---------|------------|
| **集团管理员** | 管理所有组织 | 可切换到任意组织 |
| **组织管理员** | 管理本组织 | 只能切换到所属组织 |
| **普通成员** | 查看本组织数据 | 只能切换到所属组织 |
| **审计员** | 查看所有组织(只读) | 可切换到任意组织(只读) |

### 2.2 权限矩阵

| 操作 | 集团管理员 | 组织管理员 | 普通成员 | 审计员 |
|------|-----------|-----------|---------|--------|
| 查看本组织数据 | ✅ | ✅ | ✅ | ✅ |
| 查看其他组织数据 | ✅ | ❌ | ❌ | ✅ |
| 切换组织 | ✅ | 本组织 | 本组织 | ✅ |
| 跨组织调拨 | ✅ | ✅ | ❌ | ❌ |
| 审批跨组织调拨 | ✅ | 接收方 | ❌ | ❌ |

---

## 公共模型引用声明

本模块所有组件均继承自 `apps.common` 公共基类,自动获得以下能力:

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

### 3.1 数据隔离架构

```
┌─────────────────────────────────────────────────────────────┐
│                    多组织数据隔离架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
││              Request Context Layer                     │    │
││  OrganizationMiddleware                                │    │
││  - 从JWT/Session提取组织ID                              │    │
││  - set_current_organization(org_id)                    │    │
││  - 验证用户组织权限                                      │    │
│└─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
││              ThreadLocal Context                       │    │
││  _thread_locals.organization_id = org_id               │    │
│└─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
││              TenantManager (BaseModel.objects)         │    │
││  - 自动添加 organization_id 过滤                        │    │
││  - 自动添加 is_deleted=False 过滤                        │    │
││  - 防止跨组织数据访问                                    │    │
│└─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
││              Database Query (自动隔离)                   │    │
││  SELECT * FROM assets WHERE                             │    │
││    organization_id = ? AND is_deleted = false           │    │
│└─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
││              跨组织操作 (特殊处理)                       │    │
││  - 使用 all_objects 绕过过滤                            │    │
││  - OrganizationContext.switch() 临时切换                │    │
││  - 严格权限校验                                          │    │
│└─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 组织切换流程

```
┌─────────────────────────────────────────────────────────────┐
│                  组织切换流程                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. 用户触发切换                                              │
│     │                                                         │
│     ▼                                                         │
│  2. 前端调用 POST /api/accounts/switch-organization/         │
│     │                                                         │
│     ▼                                                         │
│  3. 后端验证                                                  │
│     ├── 验证用户是否属于目标组织                               │
│     ├── 验证用户账户状态                                      │
│     └── 更新 UserOrganization.is_primary = True              │
│     │                                                         │
│     ▼                                                         │
│  4. 生成新JWT Token (含新组织ID)                              │
│     │                                                         │
│     ▼                                                         │
│  5. 前端更新本地存储                                          │
│     ├── localStorage.setItem('token', newToken)              │
│     └── Pinia store 更新 currentOrganization                 │
│     │                                                         │
│     ▼                                                         │
│  6. 前端刷新页面或重新加载数据                                │
│     │                                                         │
│     ▼                                                         │
│  7. 后续请求自动使用新组织上下文                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据模型设计

### 4.1 核心模型继承关系

```python
# 所有业务模型继承 BaseModel
class Asset(BaseModel):
    """资产模型 - 自动继承组织隔离"""
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    # 自动获得: organization, is_deleted, created_at, updated_at, created_by, custom_fields

# User 模型扩展
class User(AbstractUser):
    """用户模型 - 支持多组织"""
    current_organization = models.ForeignKey('Organization', ...)
    organizations = models.ManyToManyField('Organization', through='UserOrganization')

# 用户-组织关联
class UserOrganization(BaseModel):
    """用户组织关联"""
    user = models.ForeignKey('accounts.User', ...)
    organization = models.ForeignKey('Organization', ...)
    role = models.CharField(...)  # admin/member/auditor
    is_primary = models.BooleanField(...)  # 是否默认组织
```

### 4.2 关键字段说明

| 模型 | 字段 | 说明 |
|------|------|------|
| BaseModel | organization | 所属组织 (自动过滤) |
| BaseModel | is_deleted | 软删除标记 |
| BaseModel | created_by | 创建人 (审计) |
| User | current_organization | 当前选中组织 |
| UserOrganization | role | 在组织中的角色 |
| UserOrganization | is_primary | 是否为默认组织 |

---

## 核心功能

### 5.1 自动数据隔离

- **查询隔离**: 所有查询自动添加 `organization_id` 过滤
- **写入隔离**: 创建时自动设置当前组织ID
- **删除隔离**: 使用软删除,数据仍在但不可见
- **权限隔离**: 验证用户是否有权访问数据

### 5.2 组织切换

- **多组织成员**: 用户可加入多个组织
- **快速切换**: 通过组织选择器切换当前组织
- **权限同步**: 切换后自动加载新组织权限
- **数据隔离**: 切换后只能看到新组织数据

### 5.3 跨组织调拨

- **审批流程**: 调出方申请 → 接收方审批 → 资产转移
- **数据安全**: 审批前资产仍在原组织
- **权限控制**: 只有双方管理员可操作
- **审计日志**: 记录所有跨组织操作

---

## 安全措施

### 6.1 多层防护

| 层级 | 措施 | 说明 | 实现位置 |
|------|------|------|---------|
| **中间件层** | 组织上下文设置 | 请求级隔离 | OrganizationMiddleware |
| **模型层** | 自动过滤 | 查询级隔离 | TenantManager |
| **API层** | 权限校验 | 接口级校验 | IsOrganizationMember |
| **服务层** | 业务校验 | 逻辑级校验 | Service层 |
| **数据库层** | 行级约束 | 存储级约束 | DB Constraints |

### 6.2 跨组织操作控制

- **严格权限验证**: 只有特定角色可执行跨组织操作
- **审批流程**: 跨组织调拨必须双方审批
- **审计日志**: 记录所有跨组织操作
- **临时上下文**: 使用 `OrganizationContext.switch()` 控制作用域

---

## 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - BaseModel、TenantManager、中间件 |
| [api.md](./api.md) | API接口定义 - 组织切换、跨组织调拨 |
| [frontend.md](./frontend.md) | 前端实现 - 组织选择器、上下文管理 |
| [test.md](./test.md) | 测试计划 - 数据隔离安全测试 |

---

## 后续任务

1. ✅ 实现BaseModel和TenantManager
2. ✅ 实现OrganizationMiddleware
3. ✅ 扩展User模型支持多组织
4. ✅ 实现组织切换API
5. ✅ 实现跨组织调拨服务
6. ⏳ 编写数据隔离安全测试
7. ⏳ 前端组织选择器实现
