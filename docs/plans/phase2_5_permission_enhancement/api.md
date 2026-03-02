# Phase 2.5: 权限体系增强 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 1. 字段权限 API

### 1.1 字段权限列表

```
GET /api/permissions/field/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role_id | int | 否 | 角色ID筛选 |
| user_id | int | 否 | 用户ID筛选 |
| object_type | string | 否 | 对象类型筛选 (如 assets.Asset) |
| permission_type | string | 否 | 权限类型筛选 |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "role": {
        "id": 2,
        "name": "资产用户",
        "code": "asset_user"
      },
      "user": null,
      "object_type": "assets.Asset",
      "object_type_display": "资产",
      "field_name": "original_value",
      "field_label": "原值",
      "permission_type": "masked",
      "permission_type_display": "脱敏",
      "mask_rule": "range",
      "condition": null,
      "priority": 10,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 1.2 创建字段权限

```
POST /api/permissions/field/
```

**Request:**
```json
{
  "role_id": 2,
  "object_type": "assets.Asset",
  "field_name": "supplier",
  "permission_type": "hidden",
  "condition": {
    "type": "eq",
    "field": "role_code",
    "value": "asset_user"
  },
  "priority": 10
}
```

**Response:** `201 Created`
```json
{
  "id": 2,
  "role": {
    "id": 2,
    "name": "资产用户",
    "code": "asset_user"
  },
  "object_type": "assets.Asset",
  "field_name": "supplier",
  "permission_type": "hidden",
  "priority": 10,
  "created_at": "2024-01-15T10:05:00Z"
}
```

### 1.3 更新字段权限

```
PUT /api/permissions/field/{id}/
PATCH /api/permissions/field/{id}/
```

**Request (PATCH):**
```json
{
  "permission_type": "read",
  "mask_rule": null
}
```

### 1.4 删除字段权限

```
DELETE /api/permissions/field/{id}/
```

**Response:** `204 No Content`

### 1.5 批量创建字段权限

```
POST /api/permissions/field/batch/
```

**Request:**
```json
{
  "role_id": 2,
  "object_type": "assets.Asset",
  "permissions": [
    {
      "field_name": "original_value",
      "permission_type": "masked",
      "mask_rule": "range"
    },
    {
      "field_name": "supplier",
      "permission_type": "hidden"
    },
    {
      "field_name": "description",
      "permission_type": "read"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "created": 3,
  "results": [
    {"id": 1, "field_name": "original_value"},
    {"id": 2, "field_name": "supplier"},
    {"id": 3, "field_name": "description"}
  ]
}
```

### 1.6 获取对象可配置字段

```
GET /api/permissions/field/available-fields/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| object_type | string | 是 | 对象类型 |

**Response:**
```json
{
  "object_type": "assets.Asset",
  "object_label": "资产",
  "fields": [
    {
      "name": "asset_no",
      "label": "资产编号",
      "type": "char",
      "sensitive": false
    },
    {
      "name": "original_value",
      "label": "原值",
      "type": "decimal",
      "sensitive": true
    },
    {
      "name": "supplier",
      "label": "供应商",
      "type": "foreignkey",
      "sensitive": false
    }
  ]
}
```

---

## 2. 数据权限 API

### 2.1 数据权限列表

```
GET /api/permissions/data/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role_id | int | 否 | 角色ID筛选 |
| user_id | int | 否 | 用户ID筛选 |
| object_type | string | 否 | 对象类型筛选 |
| scope_type | string | 否 | 范围类型筛选 |
| is_active | bool | 否 | 是否启用 |

**Response:**
```json
{
  "count": 20,
  "results": [
    {
      "id": 1,
      "role": {
        "id": 3,
        "name": "部门管理员",
        "code": "dept_admin"
      },
      "user": null,
      "object_type": "assets.Asset",
      "object_type_display": "资产",
      "scope_type": "self_and_sub",
      "scope_type_display": "本部门及下级",
      "scope_value": {
        "department_field": "department"
      },
      "is_inherited": true,
      "is_active": true,
      "expansions_count": 2,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 2.2 创建数据权限

```
POST /api/permissions/data/
```

**Request:**
```json
{
  "role_id": 3,
  "object_type": "assets.Asset",
  "scope_type": "self_and_sub",
  "scope_value": {
    "department_field": "department"
  },
  "is_inherited": true,
  "is_active": true
}
```

**Response:** `201 Created`

### 2.3 更新数据权限

```
PUT /api/permissions/data/{id}/
PATCH /api/permissions/data/{id}/
```

### 2.4 删除数据权限

```
DELETE /api/permissions/data/{id}/
```

### 2.5 添加数据权限扩展

```
POST /api/permissions/data/{id}/expansions/
```

**Request:**
```json
{
  "expand_type": "department",
  "expand_value": {
    "department_ids": [5, 6, 7]
  },
  "condition": {
    "type": "action",
    "actions": ["view"]
  }
}
```

**Response:** `201 Created`
```json
{
  "id": 10,
  "expand_type": "department",
  "expand_value": {
    "department_ids": [5, 6, 7]
  },
  "condition": {
    "type": "action",
    "actions": ["view"]
  },
  "created_at": "2024-01-15T11:00:00Z"
}
```

### 2.6 删除数据权限扩展

```
DELETE /api/permissions/data/expansions/{expansion_id}/
```

---

## 3. 权限继承 API

### 3.1 角色继承关系列表

```
GET /api/permissions/inheritance/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| parent_role_id | int | 否 | 父角色ID |
| child_role_id | int | 否 | 子角色ID |
| is_active | bool | 否 | 是否启用 |

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "parent_role": {
        "id": 1,
        "name": "系统管理员",
        "code": "admin"
      },
      "child_role": {
        "id": 3,
        "name": "部门管理员",
        "code": "dept_admin"
      },
      "inherit_type": "partial",
      "inherit_type_display": "部分继承",
      "is_active": true,
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### 3.2 创建继承关系

```
POST /api/permissions/inheritance/
```

**Request:**
```json
{
  "parent_role_id": 1,
  "child_role_id": 3,
  "inherit_type": "partial",
  "is_active": true
}
```

**Response:** `201 Created`

### 3.3 更新继承关系

```
PUT /api/permissions/inheritance/{id}/
PATCH /api/permissions/inheritance/{id}/
```

### 3.4 删除继承关系

```
DELETE /api/permissions/inheritance/{id}/
```

### 3.5 获取继承关系树

```
GET /api/permissions/inheritance/tree/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role_id | int | 否 | 角色ID，查看特定角色的继承树 |

**Response:**
```json
{
  "tree": [
    {
      "role": {
        "id": 1,
        "name": "系统管理员",
        "code": "admin"
      },
      "children": [
        {
          "role": {
            "id": 3,
            "name": "部门管理员",
            "code": "dept_admin"
          },
          "inherit_type": "partial",
          "children": [
            {
              "role": {
                "id": 5,
                "name": "资产专员",
                "code": "asset_user"
              },
              "inherit_type": "full",
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

### 3.6 获取角色权限汇总

```
GET /api/permissions/inheritance/role-summary/{role_id}/
```

**Response:**
```json
{
  "role": {
    "id": 5,
    "name": "资产专员",
    "code": "asset_user"
  },
  "inherited_from": [
    {
      "role": {
        "id": 3,
        "name": "部门管理员",
        "code": "dept_admin"
      },
      "inherit_type": "partial",
      "permissions": ["view_asset", "edit_asset"]
    },
    {
      "role": {
        "id": 1,
        "name": "系统管理员",
        "code": "admin"
      },
      "inherit_type": "full",
      "permissions": []
    }
  ],
  "direct_permissions": ["scan_asset"],
  "effective_permissions": [
    "view_asset",
    "edit_asset",
    "scan_asset"
  ]
}
```

---

## 4. 权限审计 API

### 4.1 审计日志列表

```
GET /api/permissions/audit/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| actor_id | int | 否 | 操作人ID |
| action | string | 否 | 操作类型 |
| target_type | string | 否 | 目标类型 |
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**Response:**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "actor": {
        "id": 1,
        "username": "admin",
        "full_name": "系统管理员"
      },
      "action": "grant",
      "action_display": "授权",
      "target_type": "field_permission",
      "target_type_display": "字段权限",
      "target_id": 10,
      "target_name": "assets.Asset.original_value",
      "changes": {
        "permission_type": "masked"
      },
      "ip_address": "192.168.1.100",
      "success": true,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 4.2 敏感操作日志

```
GET /api/permissions/audit/sensitive/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "count": 20,
  "results": [
    {
      "id": 5,
      "actor": {
        "id": 2,
        "username": "dept_admin",
        "full_name": "部门管理员"
      },
      "action": "access",
      "action_display": "访问",
      "target_type": "sensitive_data",
      "target_name": "访问敏感字段: original_value",
      "ip_address": "192.168.1.105",
      "success": true,
      "created_at": "2024-01-15T14:20:00Z"
    }
  ]
}
```

### 4.3 权限变更历史

```
GET /api/permissions/audit/history/{target_type}/{target_id}/
```

**路径参数:**

| 参数 | 说明 |
|------|------|
| target_type | 目标类型 (role/user) |
| target_id | 目标ID |

**Response:**
```json
{
  "target": {
    "type": "role",
    "id": 3,
    "name": "部门管理员"
  },
  "history": [
    {
      "id": 1,
      "actor": {
        "username": "admin"
      },
      "action": "update",
      "changes": {
        "old": {"scope_type": "self_dept"},
        "new": {"scope_type": "self_and_sub"}
      },
      "created_at": "2024-01-15T10:00:00Z"
    },
    {
      "id": 2,
      "actor": {
        "username": "admin"
      },
      "action": "grant",
      "changes": {
        "field": "original_value",
        "permission": "masked"
      },
      "created_at": "2024-01-14T15:30:00Z"
    }
  ]
}
```

### 4.4 异常访问检测

```
GET /api/permissions/audit/anomalies/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| date_from | date | 否 | 开始日期 |
| date_to | date | 否 | 结束日期 |

**Response:**
```json
{
  "anomalies": [
    {
      "type": "excessive_denied_access",
      "description": "频繁访问被拒绝",
      "user_id": 5,
      "username": "user001",
      "deny_count": 15,
      "last_occurred_at": "2024-01-15T16:00:00Z"
    },
    {
      "type": "unusual_time_access",
      "description": "非工作时间访问敏感数据",
      "user_id": 3,
      "username": "dept_admin",
      "access_count": 8,
      "time_range": "22:00-06:00"
    }
  ]
}
```

---

## 5. 权限检查 API

### 5.1 检查用户权限

```
POST /api/permissions/check/
```

**Request:**
```json
{
  "object_type": "assets.Asset",
  "action": "view"
}
```

**Response:**
```json
{
  "has_permission": true,
  "permissions": {
    "object": "assets.Asset",
    "action": "view",
    "granted": true,
    "source": "role:dept_admin"
  },
  "field_permissions": {
    "asset_no": "read",
    "asset_name": "read",
    "original_value": "masked",
    "supplier": "hidden",
    "department": "read"
  },
  "data_scope": {
    "scope_type": "self_and_sub",
    "scope_value": {
      "department_field": "department"
    }
  }
}
```

### 5.2 批量权限检查

```
POST /api/permissions/check/batch/
```

**Request:**
```json
{
  "checks": [
    {"object_type": "assets.Asset", "action": "view"},
    {"object_type": "assets.Asset", "action": "edit"},
    {"object_type": "inventory.InventoryTask", "action": "create"}
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "object_type": "assets.Asset",
      "action": "view",
      "granted": true
    },
    {
      "object_type": "assets.Asset",
      "action": "edit",
      "granted": true
    },
    {
      "object_type": "inventory.InventoryTask",
      "action": "create",
      "granted": false,
      "reason": "缺少权限: create_inventory_task"
    }
  ]
}
```

### 5.3 获取用户可访问部门

```
GET /api/permissions/accessible-departments/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| object_type | string | 否 | 对象类型 |

**Response:**
```json
{
  "department_ids": [1, 2, 3, 5, 6, 7],
  "departments": [
    {"id": 1, "name": "总部", "parent_id": null},
    {"id": 2, "name": "财务部", "parent_id": 1},
    {"id": 3, "name": "IT部", "parent_id": 1},
    {"id": 5, "name": "财务部-一组", "parent_id": 2}
  ],
  "scope_type": "self_and_sub"
}
```

---

## 6. 权限配置模板 API

### 6.1 权限模板列表

```
GET /api/permissions/templates/
```

**Response:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "template_code": "ASSET_USER",
      "template_name": "资产用户权限模板",
      "description": "标准资产用户权限配置",
      "is_system": true,
      "config": {
        "field_permissions": [
          {
            "object_type": "assets.Asset",
            "fields": [
              {"field": "original_value", "permission": "masked"},
              {"field": "supplier", "permission": "hidden"}
            ]
          }
        ],
        "data_permissions": [
          {
            "object_type": "assets.Asset",
            "scope_type": "self_dept"
          }
        ]
      },
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 6.2 应用权限模板

```
POST /api/permissions/templates/{template_code}/apply/
```

**Request:**
```json
{
  "role_id": 5,
  "user_id": null
}
```

**Response:** `200 OK`
```json
{
  "template_code": "ASSET_USER",
  "applied_to": {
    "type": "role",
    "id": 5,
    "name": "资产用户"
  },
  "field_permissions_created": 2,
  "data_permissions_created": 1
}
```

---

## 7. 错误码定义

| 错误码 | 说明 |
|--------|------|
| 52001 | 权限不存在 |
| 52002 | 权限已存在 |
| 52003 | 权限类型无效 |
| 52004 | 对象类型无效 |
| 52005 | 字段不存在 |
| 52006 | 数据范围类型无效 |
| 52007 | 继承关系已存在 |
| 52008 | 继承关系冲突（循环继承） |
| 52009 | 无权限修改此配置 |
| 52010 | 条件表达式无效 |
| 52011 | 模板不存在 |
| 52012 | 批量操作部分失败 |

---

## 8. WebSocket 事件

### 8.1 权限变更事件

```json
{
  "event": "permission.changed",
  "data": {
    "type": "field_permission",
    "action": "updated",
    "affected_users": [1, 2, 3],
    "object_type": "assets.Asset",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### 8.2 权限撤销事件

```json
{
  "event": "permission.revoked",
  "data": {
    "type": "data_permission",
    "permission_id": 10,
    "affected_users": [5],
    "reason": "权限调整",
    "timestamp": "2024-01-15T11:00:00Z"
  }
}
```
