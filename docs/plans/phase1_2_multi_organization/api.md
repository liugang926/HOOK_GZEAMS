# Phase 1.2: 多组织数据隔离 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/organizations/user/organizations/` | 获取用户组织列表 |
| POST | `/api/accounts/switch-organization/` | 切换当前组织 |
| GET | `/api/organizations/available-for-transfer/` | 获取可调拨组织列表 |
| POST | `/api/organizations/join/` | 加入组织（邀请码） |
| GET | `/api/assets/transfers/cross-org/` | 获取跨组织调拨单列表 |
| POST | `/api/assets/transfers/cross-org/` | 创建跨组织调拨单 |
| GET | `/api/assets/transfers/cross-org/{id}/` | 获取调拨单详情 |
| PUT | `/api/assets/transfers/cross-org/{id}/` | 更新调拨单 |
| POST | `/api/assets/transfers/cross-org/{id}/approve/` | 审批调拨单 |

---

## 1. 获取用户组织列表

**请求**
```
GET /api/organizations/user/organizations/
```

**响应**
```json
{
  "success": true,
  "data": {
    "organizations": [
      {
        "id": 1,
        "name": "总部",
        "code": "HQ",
        "role": "admin",
        "is_current": true,
        "joined_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": 2,
        "name": "上海分公司",
        "code": "SH",
        "role": "member",
        "is_current": false,
        "joined_at": "2024-02-01T00:00:00Z"
      }
    ]
  }
}
```

---

## 2. 切换当前组织

**请求**
```
POST /api/accounts/switch-organization/
Content-Type: application/json

{
  "organization_id": 2
}
```

**响应**
```json
{
  "success": true,
  "message": "切换成功",
  "data": {
    "current_organization": {
      "id": 2,
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
}
```

**错误响应**
```
HTTP 403 Forbidden

{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "您不是该组织的成员"
  }
}
```

---

## 3. 获取可调拨组织列表

**请求**
```
GET /api/organizations/available-for-transfer/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "organizations": [
    {
      "id": 2,
      "name": "上海分公司",
      "code": "SH"
    },
    {
      "id": 3,
      "name": "北京分公司",
      "code": "BJ"
    }
  ]
  }
}
```

**说明**: 返回当前用户有权限进行跨组织调拨的组织列表（排除当前组织）

---

## 4. 加入组织（邀请码）

**请求**
```
POST /api/organizations/join/
Content-Type: application/json

{
  "invite_code": "ABCD1234"
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "加入成功",
  "data": {
    "id": 5,
    "name": "新加入的公司",
    "role": "member",
    "joined_at": "2024-06-01T00:00:00Z"
  }
}
```

**错误响应**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "邀请码无效或已过期"
  }
}
```

---

## 5. 创建跨组织调拨单

**请求**
```
POST /api/assets/transfers/cross-org/
Content-Type: application/json

{
  "to_organization_id": 2,
  "expected_date": "2024-06-15",
  "reason": "设备调配使用",
  "asset_ids": [101, 102, 103],
  "to_location_id": 10,
  "to_custodian_id": 25
}
```

**响应**
```
HTTP 201 Created

{
  "success": true,
  "message": "创建成功",
  "data": {
    "id": 1,
    "code": "TF202406010001",
    "from_organization": {
      "id": 1,
      "name": "总部"
    },
    "to_organization": {
      "id": 2,
      "name": "上海分公司"
    },
    "status": "pending_approval",
    "expected_date": "2024-06-15",
    "reason": "设备调配使用",
    "items": [
      {
        "id": 1,
        "asset": {
          "id": 101,
          "code": "ASSET001",
          "name": "MacBook Pro",
          "category": "计算机设备"
        },
        "from_location": "总部-3楼-研发部",
        "from_custodian": "张三"
      }
    ],
    "created_at": "2024-06-01T10:00:00Z"
  }
}
```

**错误响应**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "资产不存在或无权访问",
    "details": {
      "missing_assets": [104]
    }
  }
}
```

---

## 6. 获取跨组织调拨单列表

**请求**
```
GET /api/assets/transfers/cross-org/?status=pending_approval&page=1&page_size=20
```

**查询参数**
| 参数 | 类型 | 说明 |
|------|------|------|
| status | string | 状态筛选: pending_approval, completed, rejected |
| direction | string | 方向: outgoing(调出), incoming(调入) |
| page | integer | 页码 |
| page_size | integer | 每页数量 |

**响应**
```json
{
  "success": true,
  "data": {
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "code": "TF202406010001",
        "from_organization": "总部",
        "to_organization": "上海分公司",
        "status": "pending_approval",
        "item_count": 3,
        "created_at": "2024-06-01T10:00:00Z"
      }
    ]
  }
}
```

---

## 7. 获取调拨单详情

**请求**
```
GET /api/assets/transfers/cross-org/{id}/
```

**响应**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "code": "TF202406010001",
    "from_organization": {
      "id": 1,
      "name": "总部"
    },
    "to_organization": {
      "id": 2,
      "name": "上海分公司"
    },
    "status": "pending_approval",
    "expected_date": "2024-06-15",
    "reason": "设备调配使用",
    "to_location": {
      "id": 10,
      "name": "上海分公司-5楼",
      "path": "上海分公司-5楼"
    },
    "to_custodian": {
      "id": 25,
      "name": "李四"
    },
    "items": [
      {
        "id": 1,
        "asset": {
          "id": 101,
          "code": "ASSET001",
          "name": "MacBook Pro",
          "category": "计算机设备",
          "status": "in_use"
        },
        "from_location": "总部-3楼-研发部",
        "from_custodian": "张三",
        "asset_status_before": "in_use"
      }
    ],
    "approval_logs": [],
    "created_at": "2024-06-01T10:00:00Z",
    "created_by": {
      "id": 5,
      "name": "王五"
    }
  }
}
```

---

## 8. 审批调拨单

**请求**
```
POST /api/assets/transfers/cross-org/{id}/approve/
Content-Type: application/json

{
  "decision": "approved",
  "to_location_id": 10,
  "to_custodian_id": 25,
  "comment": "确认接收"
}
```

**参数说明**
| 参数 | 类型 | 说明 |
|------|------|------|
| decision | string | approved(同意) 或 rejected(拒绝) |
| to_location_id | integer | 接收位置ID (decision=approved时必填) |
| to_custodian_id | integer | 接收保管人ID (decision=approved时必填) |
| comment | string | 审批意见 (decision=rejected时必填) |

**响应**
```
HTTP 200 OK

{
  "success": true,
  "message": "审批成功",
  "data": {
    "id": 1,
    "status": "completed",
    "completed_at": "2024-06-01T14:30:00Z",
    "approval_logs": [
      {
        "id": 1,
        "approver_name": "李四",
        "decision": "approved",
        "comment": "确认接收",
        "created_at": "2024-06-01T14:30:00Z"
      }
    ]
  }
}
```

**错误响应**
```
HTTP 403 Forbidden

{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "只能审批调入组织的调拨单"
  }
}
```

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| not_org_member | 403 | 不是该组织成员 |
| invalid_org_switch | 403 | 无权切换到目标组织 |
| invalid_invite_code | 400 | 邀请码无效 |
| asset_not_accessible | 400 | 资产不存在或无权访问 |
| invalid_asset_status | 400 | 资产状态不允许调拨 |
| same_org_transfer | 400 | 不能在同一组织内调拨 |
| approval_not_allowed | 403 | 无权审批此调拨单 |
| transfer_completed | 400 | 调拨单已完成，无法修改 |

---

## 数据字典

### 调拨单状态 (status)

| 值 | 说明 |
|----|------|
| pending_approval | 待审批 |
| completed | 已完成 |
| rejected | 已拒绝 |
| cancelled | 已取消 |

### 用户角色 (role)

| 值 | 说明 |
|----|------|
| admin | 管理员 |
| member | 普通成员 |
| auditor | 审计员 |

### 调拨方向 (direction)

| 值 | 说明 |
|----|------|
| outgoing | 调出（从当前组织调出） |
| incoming | 调入（调入当前组织） |

---

## JWT Token格式

### Access Token Payload
```json
{
  "user_id": 1,
  "username": "admin",
  "organization_id": 2,
  "org_role": "admin",
  "exp": 1717200000,
  "iat": 1717192800
}
```

### 请求头格式
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
X-Organization-ID: 2
```

---

## 权限控制

### 组织切换权限
- 用户必须是目标组织的成员
- 用户账户状态必须为激活

### 跨组织调拨权限
| 操作 | 需要权限 |
|------|----------|
| 创建调拨单 | 资产所在组织的 `assets.transfer_out` |
| 审批调拨单 | 调入组织的 `assets.transfer_in` |
| 查看调拨单 | 调出或调入组织的 `assets.view_transfer` |
