# Phase 1.2: Organizations 独立模块 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 接口概览

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 组织管理 | GET | `/api/organizations/` | 获取组织列表 |
| 组织管理 | POST | `/api/organizations/` | 创建组织 |
| 组织管理 | GET | `/api/organizations/{id}/` | 获取组织详情 |
| 组织管理 | PUT | `/api/organizations/{id}/` | 更新组织 |
| 组织管理 | DELETE | `/api/organizations/{id}/` | 删除组织（软删除） |
| 组织管理 | POST | `/api/organizations/{id}/regenerate-invite-code/` | 重新生成邀请码 |
| 部门管理 | GET | `/api/organizations/departments/` | 获取部门列表 |
| 部门管理 | POST | `/api/organizations/departments/` | 创建部门 |
| 部门管理 | GET | `/api/organizations/departments/tree/` | 获取部门树 |
| 部门管理 | GET | `/api/organizations/departments/{id}/` | 获取部门详情 |
| 部门管理 | PUT | `/api/organizations/departments/{id}/` | 更新部门 |
| 部门管理 | DELETE | `/api/organizations/departments/{id}/` | 删除部门 |
| 部门管理 | PUT | `/api/organizations/departments/{id}/leader/` | 设置部门负责人 |
| 部门管理 | GET | `/api/organizations/departments/{id}/members/` | 获取部门成员 |
| 用户组织 | GET | `/api/organizations/user/organizations/` | 获取用户组织列表 |
| 用户组织 | POST | `/api/organizations/user/organizations/` | 加入组织 |
| 用户组织 | DELETE | `/api/organizations/user/organizations/{id}/` | 退出组织 |
| 用户组织 | POST | `/api/organizations/user/switch-organization/` | 切换当前组织 |
| 用户部门 | GET | `/api/organizations/user/departments/` | 获取用户部门列表 |
| 用户部门 | POST | `/api/organizations/user/departments/` | 添加用户部门 |
| 用户部门 | DELETE | `/api/organizations/user/departments/{id}/` | 移除用户部门 |
| 用户部门 | PUT | `/api/organizations/user/departments/{id}/primary/` | 设置主部门 |

---

## 1. 组织管理

### 1.1 获取组织列表

**请求**
```
GET /api/organizations/
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| page | integer | 页码 |
| page_size | integer | 每页数量 |
| search | string | 搜索关键词（名称/编码） |
| is_active | boolean | 是否启用 |
| org_type | string | 组织类型 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "总部",
      "code": "HQ",
      "org_type": "company",
      "org_type_display": "公司",
      "parent_id": null,
      "level": 0,
      "full_name": "总部",
      "contact_person": "张三",
      "contact_phone": "13800138000",
      "email": "contact@example.com",
      "address": "北京市朝阳区",
      "is_active": true,
      "member_count": 150,
      "department_count": 12,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
  }
}
```

### 1.2 创建组织

**请求**
```
POST /api/organizations/
Content-Type: application/json

{
  "name": "上海分公司",
  "code": "SH_BRANCH",
  "org_type": "branch",
  "parent_id": "550e8400-e29b-41d4-a716-446655440000",
  "contact_person": "李四",
  "contact_phone": "13900139000",
  "email": "sh@example.com",
  "address": "上海市浦东新区"
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "上海分公司",
    "code": "SH_BRANCH",
    "org_type": "branch",
    "parent_id": "550e8400-e29b-41d4-a716-446655440000",
    "level": 1,
    "full_name": "总部 > 上海分公司",
    "contact_person": "李四",
    "contact_phone": "13900139000",
    "email": "sh@example.com",
    "address": "上海市浦东新区",
    "is_active": true,
    "invite_code": "ABCD1234",
    "invite_code_expires_at": "2024-02-01T00:00:00Z",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

**错误响应**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "组织编码已存在",
    "details": {
      "field": "code",
      "value": "SH_BRANCH"
    }
  }
}
```

### 1.3 更新组织

**请求**
```
PUT /api/organizations/{id}/
Content-Type: application/json

{
  "name": "上海分公司（更新）",
  "contact_person": "王五"
}
```

### 1.4 重新生成邀请码

**请求**
```
POST /api/organizations/{id}/regenerate-invite-code/
```

**响应**
```json
{
  "success": true,
  "message": "生成成功",
  "data": {
    "invite_code": "XYZW9876",
    "expires_at": "2024-02-15T00:00:00Z"
  }
}
```

---

## 2. 部门管理

### 2.1 获取部门树

**请求**
```
GET /api/organizations/departments/tree/
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| organization_id | string | 组织ID（可选，默认当前用户组织） |
| include_inactive | boolean | 是否包含已禁用部门 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": [
    {
    "id": "dept-001",
    "code": "HQ",
    "name": "总部",
    "full_path": "总部",
    "full_path_name": "总部",
    "level": 0,
    "order": 0,
    "leader_id": "user-001",
    "leader_name": "张三",
    "is_active": true,
    "member_count": 50,
    "children": [
      {
        "id": "dept-002",
        "code": "TECH",
        "name": "技术部",
        "full_path": "总部/技术部",
        "full_path_name": "总部/技术部",
        "level": 1,
        "order": 1,
        "leader_id": "user-002",
        "leader_name": "李四",
        "is_active": true,
        "member_count": 20,
        "children": [
          {
            "id": "dept-004",
            "code": "BACKEND",
            "name": "后端组",
            "full_path": "总部/技术部/后端组",
            "full_path_name": "总部/技术部/后端组",
            "level": 2,
            "order": 1,
            "leader_id": null,
            "leader_name": null,
            "is_active": true,
            "member_count": 8,
            "children": []
          }
        ]
      }
    ]
  }
  ]
}
```

### 2.2 创建部门

**请求**
```
POST /api/organizations/departments/
Content-Type: application/json

{
  "organization_id": "org-001",
  "name": "市场部",
  "code": "MARKETING",
  "parent_id": "dept-001",
  "leader_id": "user-003",
  "order": 2
}
```

### 2.3 设置部门负责人

**请求**
```
PUT /api/organizations/departments/{id}/leader/
Content-Type: application/json

{
  "leader_id": "user-004"
}
```

**响应**
```json
{
  "success": true,
  "message": "设置成功",
  "data": {
    "id": "dept-003",
    "name": "市场部",
    "leader_id": "user-004",
    "leader_name": "王五"
  }
}
```

### 2.4 获取部门成员

**请求**
```
GET /api/organizations/departments/{id}/members/
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| include_children | boolean | 是否包含子部门成员 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "department_id": "dept-002",
    "department_name": "技术部",
    "direct_members": [
    {
      "user_id": "user-002",
      "name": "李四",
      "avatar": "https://example.com/avatar/user-002.jpg",
      "position": "技术总监",
      "is_leader": true,
      "is_primary": true
    },
    {
      "user_id": "user-005",
      "name": "赵六",
      "avatar": null,
      "position": "高级工程师",
      "is_leader": false,
      "is_primary": false
    }
  ],
    "total_count": 20,
    "including_children_count": 35
  }
}
```

---

## 3. 用户组织关联

### 3.1 获取用户组织列表

**请求**
```
GET /api/organizations/user/organizations/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "organizations": [
    {
      "id": "org-001",
      "name": "总部",
      "code": "HQ",
      "role": "admin",
      "role_display": "管理员",
      "is_primary": true,
      "is_active": true,
      "joined_at": "2024-01-01T00:00:00Z",
      "member_count": 150
    },
    {
      "id": "org-002",
      "name": "上海分公司",
      "code": "SH",
      "role": "member",
      "role_display": "普通成员",
      "is_primary": false,
      "is_active": true,
      "joined_at": "2024-02-01T00:00:00Z",
      "member_count": 50
    }
  ]
}
```

### 3.2 加入组织（通过邀请码）

**请求**
```
POST /api/organizations/user/organizations/
Content-Type: application/json

{
  "invite_code": "ABCD1234"
}
```

**响应**
```
HTTP 201 Created

{
  "id": "org-002",
  "name": "上海分公司",
  "role": "member",
  "joined_at": "2024-06-01T10:00:00Z"
}
```

**错误响应**
```
HTTP 400 Bad Request

{
  "code": "invalid_invite_code",
  "message": "邀请码无效或已过期"
}
```

### 3.3 切换当前组织

**请求**
```
POST /api/organizations/user/switch-organization/
Content-Type: application/json

{
  "organization_id": "org-002"
}
```

**响应**
```json
{
  "current_organization": {
    "id": "org-002",
    "name": "上海分公司",
    "code": "SH"
  },
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "permissions": [
    "assets.view",
    "assets.create",
    "assets.edit"
  ]
}
```

### 3.4 退出组织

**请求**
```
DELETE /api/organizations/user/organizations/{id}/
```

**响应**
```
HTTP 204 No Content
```

---

## 4. 用户部门关联

### 4.1 获取用户部门列表

**请求**
```
GET /api/organizations/user/departments/
```

**响应**
```json
{
  "departments": [
    {
      "id": "user-dept-001",
      "department_id": "dept-002",
      "department_name": "技术部",
      "department_full_path": "总部/技术部",
      "organization_id": "org-001",
      "organization_name": "总部",
      "is_primary": true,
      "is_asset_department": true,
      "is_leader": false,
      "position": "高级工程师"
    },
    {
      "id": "user-dept-002",
      "department_id": "dept-005",
      "department_name": "项目管理办公室",
      "department_full_path": "总部/项目管理办公室",
      "organization_id": "org-001",
      "organization_name": "总部",
      "is_primary": false,
      "is_asset_department": false,
      "is_leader": false,
      "position": "项目经理"
    }
  ]
}
```

### 4.2 添加用户部门

**请求**
```
POST /api/organizations/user/departments/
Content-Type: application/json

{
  "user_id": "user-005",
  "department_id": "dept-003",
  "organization_id": "org-001",
  "is_primary": false,
  "position": "市场专员"
}
```

### 4.3 设置主部门

**请求**
```
PUT /api/organizations/user/departments/{id}/primary/
Content-Type: application/json

{
  "is_primary": true
}
```

### 4.4 移除用户部门

**请求**
```
DELETE /api/organizations/user/departments/{id}/
```

---

## 5. 数据权限相关

### 5.1 获取可查看的部门列表

**请求**
```
GET /api/organizations/permissions/viewable-departments/
```

**响应**
```json
{
  "departments": [
    {
      "id": "dept-001",
      "name": "总部",
      "full_path_name": "总部",
      "level": 0,
      "reason": "所在部门"
    },
    {
      "id": "dept-002",
      "name": "技术部",
      "full_path_name": "总部/技术部",
      "level": 1,
      "reason": "负责部门"
    }
  ]
}
```

### 5.2 获取可查看的用户列表

**请求**
```
GET /api/organizations/permissions/viewable-users/
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| department_id | string | 部门ID（可选） |
| keyword | string | 搜索关键词 |

**响应**
```json
{
  "users": [
    {
      "id": "user-001",
      "name": "张三",
      "avatar": "https://example.com/avatar.jpg",
      "department": "技术部",
      "department_path": "总部/技术部",
      "position": "技术总监"
    }
  ],
  "total": 150
}
```

### 5.3 获取下属用户列表

**请求**
```
GET /api/organizations/permissions/subordinate-users/
```

**响应**
```json
{
  "subordinates": [
    {
      "id": "user-005",
      "name": "赵六",
      "department": "技术部",
      "department_path": "总部/技术部",
      "is_direct_report": true,
      "indirect_level": 0
    }
  ]
}
```

### 5.4 获取资产统计（按部门）

**请求**
```
GET /api/organizations/permissions/asset-statistics/
```

**响应**
```json
{
  "statistics": [
    {
      "department_id": "dept-002",
      "department_name": "技术部",
      "total_assets": 150,
      "in_use": 120,
      "idle": 25,
      "maintenance": 5
    }
  ]
}
```

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| duplicate_code | 400 | 编码已存在 |
| invalid_parent | 400 | 父级不存在 |
| has_children | 400 | 有子级，无法删除 |
| not_org_member | 403 | 不是组织成员 |
| not_org_admin | 403 | 不是组织管理员 |
| invalid_invite_code | 400 | 邀请码无效 |
| expired_invite_code | 400 | 邀请码已过期 |
| department_has_members | 400 | 部门有成员，无法删除 |
| circular_reference | 400 | 存在循环引用 |

---

## 数据字典

### 组织类型 (org_type)

| 值 | 说明 |
|----|------|
| group | 集团 |
| company | 公司 |
| branch | 分公司 |
| department | 部门级组织 |

### 用户角色 (role)

| 值 | 说明 | 权限 |
|----|------|------|
| admin | 管理员 | 全部权限 |
| member | 普通成员 | 基础操作权限 |
| auditor | 审计员 | 查看权限 |

### 权限说明 (permissions)

| 权限码 | 说明 |
|--------|------|
| organizations.view | 查看组织信息 |
| organizations.manage | 管理组织 |
| departments.view | 查看部门 |
| departments.manage | 管理部门 |
| members.view | 查看成员 |
| members.manage | 管理成员 |

---

## JWT Token 格式

### Access Token Payload

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "zhangsan",
  "organization_id": "org-001",
  "org_role": "admin",
  "exp": 1717200000,
  "iat": 1717192800
}
```

### 请求头格式

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
X-Organization-ID: org-001
```
