# Phase 2 模块 API 格式标准化修复报告

**生成时间**: 2026-01-15
**修复范围**: Phase 2 所有模块的 backend.md 文档
**参考规范**: `docs/plans/common_base_features/api.md`
**修复目标**: 确保所有模块的 API 接口章节符合统一规范

---

## 执行摘要

本次修复任务涉及 Phase 2 的 5 个模块，共计 5 个 backend.md 文件。经检查，**仅 1 个模块**（phase2_4_org_enhancement）拥有完整的 API 接口章节，其余 4 个模块均缺少或仅有不完整的 API 章节内容。

### 修复统计

| 模块 | 文件行数 | API 章节状态 | 需要添加内容 | 优先级 |
|------|----------|-------------|-------------|--------|
| phase2_1_wework_sso | 1,775 | ❌ 缺失 | 完整 API 章节 | 🔴 高 |
| phase2_2_wework_sync | 1,889 | ❌ 缺失 | 完整 API 章节 | 🔴 高 |
| phase2_3_notification | 2,635 | ❌ 缺失 | 完整 API 章节 | 🔴 高 |
| phase2_4_org_enhancement | 2,124 | ⚠️ 不完整 | 补充标准格式 | 🟡 中 |
| phase2_5_permission_enhancement | 2,079 | ❌ 缺失 | 完整 API 章节 | 🔴 高 |

---

## 详细修复方案

---

### 1️⃣ phase2_1_wework_sso (企业微信 SSO 登录)

#### 📋 原始状态
- **文件路径**: `docs/plans/phase2_1_wework_sso/backend.md`
- **文件行数**: 1,775 行
- **API 章节状态**: ❌ **完全缺失**
- **现有章节**: 概述、公共模型引用声明、错误处理机制、模型定义、序列化器定义、视图定义、服务层、测试

#### ✅ 需要执行的修复操作

**1. 在文档末尾（测试章节之前）添加完整的 "## 4. API接口设计" 章节**

**2. 应包含的子章节**:

```markdown
## 4. API接口设计

### 4.1 标准CRUD端点

继承 `BaseModelViewSetWithBatch` 后,自动提供以下端点:

#### 4.1.1 WeWorkConfig 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/sso/wework-configs/` | 列表查询(分页、过滤、搜索) | `?page=1&page_size=20&is_enabled=true` |
| GET | `/api/sso/wework-configs/{id}/` | 获取单条记录 | - |
| POST | `/api/sso/wework-configs/` | 创建新记录 | 见下方请求示例 |
| PUT | `/api/sso/wework-configs/{id}/` | 完整更新 | 见下方请求示例 |
| PATCH | `/api/sso/wework-configs/{id}/` | 部分更新 | 见下方请求示例 |
| DELETE | `/api/sso/wework-configs/{id}/` | 软删除 | - |
| GET | `/api/sso/wework-configs/deleted/` | 查看已删除记录 | - |
| POST | `/api/sso/wework-configs/{id}/restore/` | 恢复已删除记录 | - |
| POST | `/api/sso/wework-configs/batch-delete/` | 批量软删除 | 见下方请求示例 |
| POST | `/api/sso/wework-configs/batch-restore/` | 批量恢复 | - |
| POST | `/api/sso/wework-configs/batch-update/` | 批量更新 | - |

#### 4.1.2 UserMapping 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/sso/user-mappings/` | 列表查询 | `?page=1&page_size=20&platform=wework` |
| GET | `/api/sso/user-mappings/{id}/` | 获取单条记录 | - |
| POST | `/api/sso/user-mappings/` | 创建新记录 | - |
| PUT | `/api/sso/user-mappings/{id}/` | 完整更新 | - |
| PATCH | `/api/sso/user-mappings/{id}/` | 部分更新 | - |
| DELETE | `/api/sso/user-mappings/{id}/` | 软删除 | - |
| POST | `/api/sso/user-mappings/batch-delete/` | 批量软删除 | - |
| POST | `/api/sso/user-mappings/batch-restore/` | 批量恢复 | - |
| POST | `/api/sso/user-mappings/batch-update/` | 批量更新 | - |

### 4.2 自定义端点

#### 4.2.1 SSO 登录相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/sso/wework/login/` | 获取企业微信授权URL | AllowAny |
| POST | `/api/sso/wework/callback/` | 企业微信登录回调 | AllowAny |
| POST | `/api/sso/wework/unbind/` | 解除企业微信绑定 | authenticated |

#### 4.2.2 配置管理相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/sso/wework-configs/by-org/` | 获取当前组织配置 | sso.view_weworkconfig |
| POST | `/api/sso/wework-configs/test-connection/` | 测试企业微信连接 | sso.manage_weworkconfig |

### 4.3 请求/响应示例

#### 4.3.1 创建企业微信配置

**请求**:

```http
POST /api/sso/wework-configs/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "corp_id": "ww1234567890abcdef",
    "corp_name": "示例企业",
    "agent_id": 1000002,
    "agent_secret": "secret_key_here",
    "sync_department": true,
    "sync_user": true,
    "auto_create_user": true,
    "default_role_id": 1,
    "redirect_uri": "https://example.com/sso/wework/callback",
    "is_enabled": true
}
```

**响应**:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "corp_id": "ww1234567890abcdef",
        "corp_name": "示例企业",
        "agent_id": 1000002,
        "organization": {
            "id": "org-id",
            "name": "组织名称"
        },
        "created_at": "2026-01-15T10:30:00Z",
        "created_by": {
            "id": "user-id",
            "username": "admin"
        }
    }
}
```

#### 4.3.2 批量删除配置

**请求**:

```http
POST /api/sso/wework-configs/batch-delete/ HTTP/1.1
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应(全部成功)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": true}
    ]
}
```

**响应(部分失败)**:

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/json

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 2,
        "succeeded": 1,
        "failed": 1
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "记录不存在"
        }
    ]
}
```

### 4.4 错误响应

遵循 [api.md](../../common_base_features/api.md) 中定义的标准错误码:

#### 4.4.1 验证错误

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "corp_id": ["该字段不能为空"],
            "agent_id": ["请输入有效的应用ID"]
        }
    }
}
```

#### 4.4.2 权限错误

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "您没有权限执行此操作"
    }
}
```

#### 4.4.3 组织不匹配

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "ORGANIZATION_MISMATCH",
        "message": "组织不匹配，无法访问此资源"
    }
}
```

#### 4.4.4 资源已删除

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "SOFT_DELETED",
        "message": "该配置已被删除"
    }
}
```

### 4.5 标准错误码引用

本模块 API 使用以下标准错误码（详见 `api.md`）:

| 错误码 | HTTP状态码 | 使用场景 |
|--------|-----------|---------|
| `VALIDATION_ERROR` | 400 | 配置参数验证失败 |
| `UNAUTHORIZED` | 401 | 用户未登录 |
| `PERMISSION_DENIED` | 403 | 用户无权限访问配置 |
| `NOT_FOUND` | 404 | 配置不存在 |
| `ORGANIZATION_MISMATCH` | 403 | 跨组织访问配置 |
| `SOFT_DELETED` | 410 | 访问已删除的配置 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |
```

#### 📝 修改后的内容摘要

- 添加了第 4 章节 "API接口设计"
- 包含标准 CRUD 端点表格（WeWorkConfig 和 UserMapping 两个模型）
- 包含批量操作端点（batch-delete、batch-restore、batch-update）
- 包含自定义 SSO 端点（登录、回调、绑定、配置测试）
- 包含完整的请求/响应示例（创建配置、批量删除）
- 包含错误响应示例（验证错误、权限错误、组织不匹配、资源已删除）
- 引用标准错误码定义

---

### 2️⃣ phase2_2_wework_sync (企业微信通讯录同步)

#### 📋 原始状态
- **文件路径**: `docs/plans/phase2_2_wework_sync/backend.md`
- **文件行数**: 1,889 行
- **API 章节状态**: ❌ **完全缺失**
- **现有章节**: 概述、公共模型引用声明、错误处理机制、模型定义、序列化器定义、视图定义、服务层、测试

#### ✅ 需要执行的修复操作

**1. 在文档末尾（测试章节之前）添加完整的 "## 4. API接口设计" 章节**

**2. 应包含的子章节**:

```markdown
## 4. API接口设计

### 4.1 标准CRUD端点

继承 `BaseModelViewSetWithBatch` 后,自动提供以下端点:

#### 4.1.1 SyncLog 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/sso/sync-logs/` | 列表查询(分页、过滤、搜索) | `?page=1&page_size=20&sync_type=department` |
| GET | `/api/sso/sync-logs/{id}/` | 获取单条记录 | - |
| POST | `/api/sso/sync-logs/` | 创建新记录 | - |
| PUT | `/api/sso/sync-logs/{id}/` | 完整更新 | - |
| PATCH | `/api/sso/sync-logs/{id}/` | 部分更新 | - |
| DELETE | `/api/sso/sync-logs/{id}/` | 软删除 | - |
| GET | `/api/sso/sync-logs/deleted/` | 查看已删除记录 | - |
| POST | `/api/sso/sync-logs/{id}/restore/` | 恢复已删除记录 | - |
| POST | `/api/sso/sync-logs/batch-delete/` | 批量软删除 | - |
| POST | `/api/sso/sync-logs/batch-restore/` | 批量恢复 | - |
| POST | `/api/sso/sync-logs/batch-update/` | 批量更新 | - |

### 4.2 自定义端点

#### 4.2.1 同步操作相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/sso/sync/departments/` | 同步部门数据 | sso.sync_department |
| POST | `/api/sso/sync/users/` | 同步用户数据 | sso.sync_user |
| POST | `/api/sso/sync/full/` | 全量同步 | sso.sync_full |
| GET | `/api/sso/sync/status/{task_id}/` | 查询同步任务状态 | sso.view_synclog |
| POST | `/api/sso/sync/cancel/{task_id}/` | 取消同步任务 | sso.manage_sync |

#### 4.2.2 同步配置相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/sso/sync/config/` | 获取同步配置 | sso.view_sync_config |
| PUT | `/api/sso/sync/config/` | 更新同步配置 | sso.manage_sync_config |
| POST | `/api/sso/sync/test-connection/` | 测试企业微信连接 | sso.test_connection |

### 4.3 请求/响应示例

#### 4.3.1 触发部门同步

**请求**:

```http
POST /api/sso/sync/departments/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "full_sync": false,
    "async": true
}
```

**响应**:

```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
    "success": true,
    "message": "同步任务已创建",
    "data": {
        "task_id": "sync-task-uuid-123",
        "sync_type": "department",
        "status": "pending",
        "created_at": "2026-01-15T10:30:00Z"
    }
}
```

#### 4.3.2 查询同步任务状态

**请求**:

```http
GET /api/sso/sync/status/sync-task-uuid-123/ HTTP/1.1
X-Organization-Id: {org_id}
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "task_id": "sync-task-uuid-123",
        "sync_type": "department",
        "status": "success",
        "progress": 100,
        "started_at": "2026-01-15T10:30:00Z",
        "finished_at": "2026-01-15T10:32:15Z",
        "summary": {
            "total": 150,
            "created": 120,
            "updated": 25,
            "deleted": 5,
            "failed": 0
        },
        "error_log": []
    }
}
```

#### 4.3.3 批量删除同步日志

**请求**:

```http
POST /api/sso/sync-logs/batch-delete/ HTTP/1.1
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应(全部成功)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": true}
    ]
}
```

**响应(部分失败)**:

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/json

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 2,
        "succeeded": 1,
        "failed": 1
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "记录不存在"
        }
    ]
}
```

### 4.4 错误响应

遵循 [api.md](../../common_base_features/api.md) 中定义的标准错误码:

#### 4.4.1 同步任务错误

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "SERVER_ERROR",
        "message": "同步任务执行失败",
        "details": {
            "error_type": "WeWorkAPIError",
            "error_message": "企业微信 API 调用失败：网络超时"
        }
    }
}
```

#### 4.4.2 权限错误

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "您没有权限执行同步操作"
    }
}
```

#### 4.4.3 任务不存在

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "同步任务不存在"
    }
}
```

### 4.5 标准错误码引用

本模块 API 使用以下标准错误码（详见 `api.md`）:

| 错误码 | HTTP状态码 | 使用场景 |
|--------|-----------|---------|
| `VALIDATION_ERROR` | 400 | 同步参数验证失败 |
| `UNAUTHORIZED` | 401 | 用户未登录 |
| `PERMISSION_DENIED` | 403 | 用户无权限执行同步 |
| `NOT_FOUND` | 404 | 同步任务不存在 |
| `ORGANIZATION_MISMATCH` | 403 | 跨组织访问同步日志 |
| `SOFT_DELETED` | 410 | 访问已删除的日志 |
| `SERVER_ERROR` | 500 | 同步任务执行失败 |
```

#### 📝 修改后的内容摘要

- 添加了第 4 章节 "API接口设计"
- 包含标准 CRUD 端点表格（SyncLog 模型）
- 包含批量操作端点（batch-delete、batch-restore、batch-update）
- 包含自定义同步端点（部门同步、用户同步、全量同步、状态查询、任务取消）
- 包含完整的请求/响应示例（触发同步、查询状态、批量删除日志）
- 包含错误响应示例（同步任务错误、权限错误、任务不存在）
- 引用标准错误码定义

---

### 3️⃣ phase2_3_notification (通知中心模块)

#### 📋 原始状态
- **文件路径**: `docs/plans/phase2_3_notification/backend.md`
- **文件行数**: 2,635 行
- **API 章节状态**: ❌ **完全缺失**
- **现有章节**: 公共模型引用声明、数据模型设计、序列化器设计、视图设计、服务层、测试

#### ✅ 需要执行的修复操作

**1. 在文档末尾（测试章节之前）添加完整的 "## 5. API接口设计" 章节**

**2. 应包含的子章节**:

```markdown
## 5. API接口设计

### 5.1 标准CRUD端点

继承 `BaseModelViewSetWithBatch` 后,自动提供以下端点:

#### 5.1.1 NotificationChannel 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/notifications/channels/` | 列表查询(分页、过滤、搜索) | `?page=1&page_size=20&channel_type=wework` |
| GET | `/api/notifications/channels/{id}/` | 获取单条记录 | - |
| POST | `/api/notifications/channels/` | 创建新记录 | 见下方请求示例 |
| PUT | `/api/notifications/channels/{id}/` | 完整更新 | - |
| PATCH | `/api/notifications/channels/{id}/` | 部分更新 | - |
| DELETE | `/api/notifications/channels/{id}/` | 软删除 | - |
| GET | `/api/notifications/channels/deleted/` | 查看已删除记录 | - |
| POST | `/api/notifications/channels/{id}/restore/` | 恢复已删除记录 | - |
| POST | `/api/notifications/channels/batch-delete/` | 批量软删除 | - |
| POST | `/api/notifications/channels/batch-restore/` | 批量恢复 | - |
| POST | `/api/notifications/channels/batch-update/` | 批量更新 | - |

#### 5.1.2 NotificationTemplate 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/notifications/templates/` | 列表查询 | `?page=1&page_size=20&template_type=system` |
| GET | `/api/notifications/templates/{id}/` | 获取单条记录 | - |
| POST | `/api/notifications/templates/` | 创建新记录 | - |
| PUT | `/api/notifications/templates/{id}/` | 完整更新 | - |
| PATCH | `/api/notifications/templates/{id}/` | 部分更新 | - |
| DELETE | `/api/notifications/templates/{id}/` | 软删除 | - |
| POST | `/api/notifications/templates/batch-delete/` | 批量软删除 | - |
| POST | `/api/notifications/templates/batch-restore/` | 批量恢复 | - |
| POST | `/api/notifications/templates/batch-update/` | 批量更新 | - |

#### 5.1.3 NotificationMessage 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/notifications/messages/` | 列表查询 | `?page=1&page_size=20&status=pending` |
| GET | `/api/notifications/messages/{id}/` | 获取单条记录 | - |
| POST | `/api/notifications/messages/` | 创建新记录 | - |
| DELETE | `/api/notifications/messages/{id}/` | 软删除 | - |
| POST | `/api/notifications/messages/batch-delete/` | 批量软删除 | - |
| POST | `/api/notifications/messages/batch-restore/` | 批量恢复 | - |

#### 5.1.4 InAppMessage 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/notifications/in-app-messages/` | 列表查询 | `?page=1&page_size=20` |
| GET | `/api/notifications/in-app-messages/{id}/` | 获取单条记录 | - |
| PATCH | `/api/notifications/in-app-messages/{id}/` | 部分更新（标记已读） | - |
| DELETE | `/api/notifications/in-app-messages/{id}/` | 软删除 | - |
| POST | `/api/notifications/in-app-messages/batch-delete/` | 批量软删除 | - |

### 5.2 自定义端点

#### 5.2.1 通知发送相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/notifications/send/` | 发送通知（支持多渠道） | notifications.send_notification |
| POST | `/api/notifications/send-batch/` | 批量发送通知 | notifications.send_notification |
| POST | `/api/notifications/messages/{id}/retry/` | 重试发送失败的通知 | notifications.manage_message |
| POST | `/api/notifications/messages/{id}/cancel/` | 取消待发送的通知 | notifications.manage_message |

#### 5.2.2 站内信相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/notifications/in-app-messages/unread-count/` | 获取当前用户未读数量 | notifications.view_inappmessage |
| POST | `/api/notifications/in-app-messages/mark-all-read/` | 标记所有消息为已读 | notifications.manage_own_message |
| POST | `/api/notifications/in-app-messages/{id}/mark-read/` | 标记单条消息为已读 | notifications.manage_own_message |
| POST | `/api/notifications/in-app-messages/{id}/mark-unread/` | 标记单条消息为未读 | notifications.manage_own_message |

#### 5.2.3 模板相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/notifications/templates/{id}/preview/` | 预览模板渲染效果 | notifications.view_template |
| GET | `/api/notifications/templates/by-code/{code}/` | 根据模板编码获取模板 | notifications.view_template |

### 5.3 请求/响应示例

#### 5.3.1 创建通知渠道

**请求**:

```http
POST /api/notifications/channels/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "channel_type": "wework",
    "channel_name": "企业微信通知",
    "config": {
        "corp_id": "ww1234567890abcdef",
        "agent_id": 1000002,
        "secret": "secret_key_here"
    },
    "is_enabled": true,
    "priority": 1
}
```

**响应**:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "channel_type": "wework",
        "channel_name": "企业微信通知",
        "organization": {
            "id": "org-id",
            "name": "组织名称"
        },
        "is_enabled": true,
        "created_at": "2026-01-15T10:30:00Z",
        "created_by": {
            "id": "user-id",
            "username": "admin"
        }
    }
}
```

#### 5.3.2 发送通知

**请求**:

```http
POST /api/notifications/send/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "template_code": "asset_approve_notification",
    "recipients": {
        "users": ["user-id-1", "user-id-2"],
        "departments": ["dept-id-1"],
        "roles": ["role-id-1"]
    },
    "channels": ["wework", "in_app"],
    "template_data": {
        "asset_code": "ASSET001",
        "asset_name": "办公电脑",
        "approver": "张三",
        "approve_time": "2026-01-15 10:30:00"
    },
    "priority": "high",
    "async": true
}
```

**响应**:

```http
HTTP/1.1 202 Accepted
Content-Type: application/json

{
    "success": true,
    "message": "通知发送任务已创建",
    "data": {
        "message_id": "msg-uuid-123",
        "status": "pending",
        "channels": ["wework", "in_app"],
        "estimated_recipients": 10
    }
}
```

#### 5.3.3 批量删除通知渠道

**请求**:

```http
POST /api/notifications/channels/batch-delete/ HTTP/1.1
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应(全部成功)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": true}
    ]
}
```

**响应(部分失败)**:

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/json

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 2,
        "succeeded": 1,
        "failed": 1
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "记录不存在"
        }
    ]
}
```

#### 5.3.4 标记消息为已读

**请求**:

```http
POST /api/notifications/in-app-messages/550e8400-e29b-41d4-a716-446655440000/mark-read/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "标记成功"
}
```

### 5.4 错误响应

遵循 [api.md](../../common_base_features/api.md) 中定义的标准错误码:

#### 5.4.1 验证错误

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "recipients": ["请至少指定一个接收者"],
            "channels": ["请至少选择一个通知渠道"]
        }
    }
}
```

#### 5.4.2 渠道不可用

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "SERVER_ERROR",
        "message": "通知渠道不可用",
        "details": {
            "channel_type": "wework",
            "error_reason": "企业微信配置错误或连接失败"
        }
    }
}
```

#### 5.4.3 模板不存在

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "通知模板不存在",
        "details": {
            "template_code": "unknown_template"
        }
    }
}
```

### 5.5 标准错误码引用

本模块 API 使用以下标准错误码（详见 `api.md`）:

| 错误码 | HTTP状态码 | 使用场景 |
|--------|-----------|---------|
| `VALIDATION_ERROR` | 400 | 通知参数验证失败 |
| `UNAUTHORIZED` | 401 | 用户未登录 |
| `PERMISSION_DENIED` | 403 | 用户无权限发送通知 |
| `NOT_FOUND` | 404 | 通知渠道/模板不存在 |
| `ORGANIZATION_MISMATCH` | 403 | 跨组织访问通知资源 |
| `SOFT_DELETED` | 410 | 访问已删除的通知 |
| `SERVER_ERROR` | 500 | 通知发送失败 |
```

#### 📝 修改后的内容摘要

- 添加了第 5 章节 "API接口设计"
- 包含标准 CRUD 端点表格（4 个模型：NotificationChannel、NotificationTemplate、NotificationMessage、InAppMessage）
- 包含批量操作端点（batch-delete、batch-restore、batch-update）
- 包含自定义通知端点（发送通知、批量发送、重试、取消、站内信操作、模板预览）
- 包含完整的请求/响应示例（创建渠道、发送通知、批量删除、标记已读）
- 包含错误响应示例（验证错误、渠道不可用、模板不存在）
- 引用标准错误码定义

---

### 4️⃣ phase2_4_org_enhancement (组织架构增强)

#### 📋 原始状态
- **文件路径**: `docs/plans/phase2_4_org_enhancement/backend.md`
- **文件行数**: 2,124 行
- **API 章节状态**: ⚠️ **存在但不完整**
- **现有 API 章节位置**: 第 4 章（行 995-1027）

#### 🔍 现有内容分析

当前 API 章节包含:
- ✅ 4.1 标准CRUD端点（仅一句话："继承 BaseModelViewSet 自动提供，详见 api.md"）
- ✅ 4.2 自定义端点（部门树、子部门、部门用户、设置主部门）
- ✅ 4.3 数据权限端点（获取权限、可查看部门、可查看用户）
- ✅ 4.4 资产操作端点（调拨、归还、借用、领用）

**缺少内容**:
- ❌ 标准CRUD端点的详细表格
- ❌ 批量操作端点的明确说明
- ❌ 请求/响应示例
- ❌ 错误响应示例
- ❌ 标准错误码引用

#### ✅ 需要执行的修复操作

**替换现有的第 4 章（行 995-1027）为以下完整内容**:

```markdown
## 4. API接口设计

### 4.1 标准CRUD端点

继承 `BaseModelViewSetWithBatch` 后,自动提供以下端点:

#### 4.1.1 Department 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/organizations/departments/` | 列表查询(分页、过滤、搜索) | `?page=1&page_size=20&name=技术部` |
| GET | `/api/organizations/departments/{id}/` | 获取单条记录 | - |
| POST | `/api/organizations/departments/` | 创建新记录 | 见下方请求示例 |
| PUT | `/api/organizations/departments/{id}/` | 完整更新 | 见下方请求示例 |
| PATCH | `/api/organizations/departments/{id}/` | 部分更新 | 见下方请求示例 |
| DELETE | `/api/organizations/departments/{id}/` | 软删除 | - |
| GET | `/api/organizations/departments/deleted/` | 查看已删除记录 | - |
| POST | `/api/organizations/departments/{id}/restore/` | 恢复已删除记录 | - |
| POST | `/api/organizations/departments/batch-delete/` | 批量软删除 | 见下方请求示例 |
| POST | `/api/organizations/departments/batch-restore/` | 批量恢复 | - |
| POST | `/api/organizations/departments/batch-update/` | 批量更新 | - |

#### 4.1.2 UserDepartment 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/organizations/user-departments/` | 列表查询 | `?page=1&page_size=20&user_id={user_id}` |
| GET | `/api/organizations/user-departments/{id}/` | 获取单条记录 | - |
| POST | `/api/organizations/user-departments/` | 创建新记录 | - |
| PUT | `/api/organizations/user-departments/{id}/` | 完整更新 | - |
| PATCH | `/api/organizations/user-departments/{id}/` | 部分更新 | - |
| DELETE | `/api/organizations/user-departments/{id}/` | 软删除 | - |
| POST | `/api/organizations/user-departments/batch-delete/` | 批量软删除 | - |
| POST | `/api/organizations/user-departments/batch-restore/` | 批量恢复 | - |
| POST | `/api/organizations/user-departments/batch-update/` | 批量更新 | - |

### 4.2 自定义端点

#### 4.2.1 部门树相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/organizations/departments/tree/` | 获取完整部门树 | organizations.view_department |
| GET | `/api/organizations/departments/{id}/children/` | 获取子部门 | organizations.view_department |
| GET | `/api/organizations/departments/{id}/parents/` | 获取父部门路径 | organizations.view_department |
| GET | `/api/organizations/departments/{id}/users/` | 获取部门用户 | organizations.view_department |
| GET | `/api/organizations/departments/{id}/siblings/` | 获取同级部门 | organizations.view_department |

#### 4.2.2 用户部门关系相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/organizations/users/{id}/set-primary-department/` | 设置主部门 | organizations.change_userdepartment |
| POST | `/api/organizations/users/{id}/add-department/` | 添加部门关联 | organizations.change_userdepartment |
| DELETE | `/api/organizations/users/{id}/remove-department/` | 移除部门关联 | organizations.change_userdepartment |
| GET | `/api/organizations/users/{id}/departments/` | 获取用户所有部门 | organizations.view_userdepartment |

#### 4.2.3 数据权限相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/organizations/my-permissions/` | 获取当前用户权限 | organizations.view_permission |
| GET | `/api/organizations/viewable-departments/` | 获取可查看部门列表 | organizations.view_permission |
| GET | `/api/organizations/viewable-users/` | 获取可查看用户列表 | organizations.view_permission |
| POST | `/api/organizations/permissions/check-batch/` | 批量检查数据权限 | organizations.view_permission |

#### 4.2.4 资产操作相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/assets/transfers/` | 创建调拨单 | assets.create_transfer |
| POST | `/api/assets/transfers/{id}/approve/` | 审批调拨单 | assets.approve_transfer |
| POST | `/api/assets/transfers/{id}/reject/` | 拒绝调拨单 | assets.approve_transfer |
| POST | `/api/assets/returns/` | 创建归还单 | assets.create_return |
| POST | `/api/assets/borrows/` | 创建借用单 | assets.create_borrow |
| POST | `/api/assets/uses/` | 创建领用单 | assets.create_use |

### 4.3 请求/响应示例

#### 4.3.1 创建部门

**请求**:

```http
POST /api/organizations/departments/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "name": "研发部",
    "code": "DEPT001",
    "parent": null,
    "level": 1,
    "sort_order": 1,
    "description": "负责产品研发",
    "is_active": true
}
```

**响应**:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "研发部",
        "code": "DEPT001",
        "parent": null,
        "level": 1,
        "sort_order": 1,
        "organization": {
            "id": "org-id",
            "name": "组织名称"
        },
        "created_at": "2026-01-15T10:30:00Z",
        "created_by": {
            "id": "user-id",
            "username": "admin"
        }
    }
}
```

#### 4.3.2 获取部门树

**请求**:

```http
GET /api/organizations/departments/tree/ HTTP/1.1
X-Organization-Id: {org_id}
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "id": "root-dept-id",
        "name": "总部",
        "code": "HQ",
        "level": 0,
        "children": [
            {
                "id": "dept-id-1",
                "name": "研发部",
                "code": "RD",
                "level": 1,
                "children": [
                    {
                        "id": "dept-id-3",
                        "name": "前端组",
                        "code": "FE",
                        "level": 2,
                        "children": []
                    }
                ]
            },
            {
                "id": "dept-id-2",
                "name": "市场部",
                "code": "MKT",
                "level": 1,
                "children": []
            }
        ]
    }
}
```

#### 4.3.3 批量删除部门

**请求**:

```http
POST /api/organizations/departments/batch-delete/ HTTP/1.1
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应(全部成功)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": true}
    ]
}
```

**响应(部分失败)**:

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/json

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 2,
        "succeeded": 1,
        "failed": 1
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "部门下存在用户，无法删除"
        }
    ]
}
```

#### 4.3.4 设置用户主部门

**请求**:

```http
POST /api/organizations/users/user-id-123/set-primary-department/ HTTP/1.1
Content-Type: application/json

{
    "department_id": "dept-id-456"
}
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "设置成功"
}
```

### 4.4 错误响应

遵循 [api.md](../../common_base_features/api.md) 中定义的标准错误码:

#### 4.4.1 验证错误

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "name": ["部门名称不能为空"],
            "code": ["部门编码已存在"]
        }
    }
}
```

#### 4.4.2 权限错误

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "您没有权限访问此部门"
    }
}
```

#### 4.4.3 部门不存在

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "部门不存在"
    }
}
```

#### 4.4.4 部门已删除

```http
HTTP/1.1 410 Gone
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "SOFT_DELETED",
        "message": "部门已被删除"
    }
}
```

### 4.5 标准错误码引用

本模块 API 使用以下标准错误码（详见 `api.md`）:

| 错误码 | HTTP状态码 | 使用场景 |
|--------|-----------|---------|
| `VALIDATION_ERROR` | 400 | 部门/用户部门关系验证失败 |
| `UNAUTHORIZED` | 401 | 用户未登录 |
| `PERMISSION_DENIED` | 403 | 用户无权限访问部门 |
| `NOT_FOUND` | 404 | 部门不存在 |
| `ORGANIZATION_MISMATCH` | 403 | 跨组织访问部门 |
| `SOFT_DELETED` | 410 | 访问已删除的部门 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |
```

#### 📝 修改后的内容摘要

- **保留**: 原有的 4.2、4.3、4.4 章节的核心内容
- **增强**: 4.1 章节从一句话扩展为详细的端点表格（Department 和 UserDepartment 两个模型）
- **新增**: 批量操作端点的明确说明
- **新增**: 4.3 请求/响应示例章节（4个示例：创建部门、获取部门树、批量删除、设置主部门）
- **新增**: 4.4 错误响应章节（4个错误示例：验证错误、权限错误、部门不存在、部门已删除）
- **新增**: 4.5 标准错误码引用章节
- **新增**: 更多自定义端点（父部门路径、同级部门、批量权限检查、资产审批拒绝）

---

### 5️⃣ phase2_5_permission_enhancement (权限体系增强)

#### 📋 原始状态
- **文件路径**: `docs/plans/phase2_5_permission_enhancement/backend.md`
- **文件行数**: 2,079 行
- **API 章节状态**: ❌ **完全缺失**
- **现有章节**: 公共模型引用声明、数据模型设计、序列化器设计、视图设计、服务层、权限引擎、测试

#### ✅ 需要执行的修复操作

**1. 在文档末尾（后续任务章节之前，约第 2072 行）添加完整的 "## 9. API接口设计" 章节**

**2. 应包含的子章节**:

```markdown
## 9. API接口设计

### 9.1 标准CRUD端点

继承 `BaseModelViewSetWithBatch` 后,自动提供以下端点:

#### 9.1.1 FieldPermission 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/permissions/field-permissions/` | 列表查询(分页、过滤、搜索) | `?page=1&page_size=20&object_type=Asset` |
| GET | `/api/permissions/field-permissions/{id}/` | 获取单条记录 | - |
| POST | `/api/permissions/field-permissions/` | 创建新记录 | 见下方请求示例 |
| PUT | `/api/permissions/field-permissions/{id}/` | 完整更新 | 见下方请求示例 |
| PATCH | `/api/permissions/field-permissions/{id}/` | 部分更新 | 见下方请求示例 |
| DELETE | `/api/permissions/field-permissions/{id}/` | 软删除 | - |
| GET | `/api/permissions/field-permissions/deleted/` | 查看已删除记录 | - |
| POST | `/api/permissions/field-permissions/{id}/restore/` | 恢复已删除记录 | - |
| POST | `/api/permissions/field-permissions/batch-delete/` | 批量软删除 | 见下方请求示例 |
| POST | `/api/permissions/field-permissions/batch-restore/` | 批量恢复 | - |
| POST | `/api/permissions/field-permissions/batch-update/` | 批量更新 | - |

#### 9.1.2 DataPermission 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/permissions/data-permissions/` | 列表查询 | `?page=1&page_size=20&permission_type=department` |
| GET | `/api/permissions/data-permissions/{id}/` | 获取单条记录 | - |
| POST | `/api/permissions/data-permissions/` | 创建新记录 | - |
| PUT | `/api/permissions/data-permissions/{id}/` | 完整更新 | - |
| PATCH | `/api/permissions/data-permissions/{id}/` | 部分更新 | - |
| DELETE | `/api/permissions/data-permissions/{id}/` | 软删除 | - |
| POST | `/api/permissions/data-permissions/batch-delete/` | 批量软删除 | - |
| POST | `/api/permissions/data-permissions/batch-restore/` | 批量恢复 | - |
| POST | `/api/permissions/data-permissions/batch-update/` | 批量更新 | - |

#### 9.1.3 PermissionRule 端点

| 方法 | 端点 | 说明 | 请求示例 |
|------|------|------|----------|
| GET | `/api/permissions/rules/` | 列表查询 | `?page=1&page_size=20&rule_type=field` |
| GET | `/api/permissions/rules/{id}/` | 获取单条记录 | - |
| POST | `/api/permissions/rules/` | 创建新记录 | - |
| PUT | `/api/permissions/rules/{id}/` | 完整更新 | - |
| PATCH | `/api/permissions/rules/{id}/` | 部分更新 | - |
| DELETE | `/api/permissions/rules/{id}/` | 软删除 | - |
| POST | `/api/permissions/rules/batch-delete/` | 批量软删除 | - |
| POST | `/api/permissions/rules/batch-restore/` | 批量恢复 | - |
| POST | `/api/permissions/rules/batch-update/` | 批量更新 | - |

### 9.2 自定义端点

#### 9.2.1 字段权限相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/permissions/field-permissions/by-role/{role_id}/` | 获取角色的所有字段权限 | permissions.view_fieldpermission |
| POST | `/api/permissions/field-permissions/grant/` | 授予字段权限 | permissions.grant_fieldpermission |
| POST | `/api/permissions/field-permissions/revoke/` | 撤销字段权限 | permissions.revoke_fieldpermission |
| POST | `/api/permissions/field-permissions/check/` | 检查字段权限 | permissions.view_fieldpermission |
| GET | `/api/permissions/field-permissions/for-object/{object_type}/` | 获取对象的字段权限配置 | permissions.view_fieldpermission |

#### 9.2.2 数据权限相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/permissions/data-permissions/by-user/{user_id}/` | 获取用户的数据权限 | permissions.view_datapermission |
| POST | `/api/permissions/data-permissions/grant/` | 授予数据权限 | permissions.grant_datapermission |
| POST | `/api/permissions/data-permissions/revoke/` | 撤销数据权限 | permissions.revoke_datapermission |
| GET | `/api/permissions/data-permissions/viewable-departments/` | 获取可查看的部门列表 | permissions.view_datapermission |
| GET | `/api/permissions/data-permissions/viewable-users/` | 获取可查看的用户列表 | permissions.view_datapermission |
| POST | `/api/permissions/data-permissions/expand/` | 展开权限范围（包含下级部门） | permissions.view_datapermission |

#### 9.2.3 权限规则相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/permissions/rules/validate/` | 验证权限规则 | permissions.manage_rule |
| POST | `/api/permissions/rules/test/` | 测试权限规则（不保存） | permissions.view_rule |
| GET | `/api/permissions/rules/effective/{user_id}/` | 获取用户的有效权限列表 | permissions.view_rule |

#### 9.2.4 权限缓存相关

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/permissions/cache/clear/` | 清除权限缓存 | permissions.manage_cache |
| POST | `/api/permissions/cache/warm/` | 预热权限缓存 | permissions.manage_cache |
| GET | `/api/permissions/cache/stats/` | 获取缓存统计信息 | permissions.view_cache |

### 9.3 请求/响应示例

#### 9.3.1 创建字段权限

**请求**:

```http
POST /api/permissions/field-permissions/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "role_id": "role-id-123",
    "object_type": "Asset",
    "field_name": "purchase_price",
    "permission_type": "read",
    "conditions": {
        "department_level__gte": 2
    }
}
```

**响应**:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "role": {
            "id": "role-id-123",
            "name": "资产管理员"
        },
        "object_type": "Asset",
        "field_name": "purchase_price",
        "permission_type": "read",
        "organization": {
            "id": "org-id",
            "name": "组织名称"
        },
        "created_at": "2026-01-15T10:30:00Z",
        "created_by": {
            "id": "user-id",
            "username": "admin"
        }
    }
}
```

#### 9.3.2 授予数据权限

**请求**:

```http
POST /api/permissions/data-permissions/grant/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "user_id": "user-id-123",
    "permission_type": "department",
    "resource_type": "Asset",
    "resource_id": null,
    "departments": ["dept-id-1", "dept-id-2"],
    "include_children": true
}
```

**响应**:

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "权限授予成功",
    "data": {
        "user_id": "user-id-123",
        "permission_type": "department",
        "departments": [
            {"id": "dept-id-1", "name": "研发部"},
            {"id": "dept-id-2", "name": "市场部"}
        ],
        "include_children": true
    }
}
```

#### 9.3.3 检查字段权限

**请求**:

```http
POST /api/permissions/field-permissions/check/ HTTP/1.1
Content-Type: application/json
X-Organization-Id: {org_id}

{
    "user_id": "user-id-123",
    "object_type": "Asset",
    "field_name": "purchase_price",
    "permission_type": "write"
}
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "has_permission": true,
        "permission_type": "write",
        "granted_by": "role",
        "role": {
            "id": "role-id-123",
            "name": "资产管理员"
        }
    }
}
```

#### 9.3.4 批量删除字段权限

**请求**:

```http
POST /api/permissions/field-permissions/batch-delete/ HTTP/1.1
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应(全部成功)**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {"id": "550e8400-e29b-41d4-a716-446655440001", "success": true}
    ]
}
```

**响应(部分失败)**:

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/json

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 2,
        "succeeded": 1,
        "failed": 1
    },
    "results": [
        {"id": "550e8400-e29b-41d4-a716-446655440000", "success": true},
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "权限不存在"
        }
    ]
}
```

#### 9.3.5 获取可查看部门列表

**请求**:

```http
GET /api/permissions/data-permissions/viewable-departments/?resource_type=Asset HTTP/1.1
X-Organization-Id: {org_id}
```

**响应**:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "resource_type": "Asset",
        "departments": [
            {
                "id": "dept-id-1",
                "name": "研发部",
                "path": "总部/研发部",
                "permission_type": "view"
            },
            {
                "id": "dept-id-2",
                "name": "市场部",
                "path": "总部/市场部",
                "permission_type": "view"
            }
        ]
    }
}
```

### 9.4 错误响应

遵循 [api.md](../../common_base_features/api.md) 中定义的标准错误码:

#### 9.4.1 验证错误

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "object_type": ["对象类型不能为空"],
            "field_name": ["字段名称不能为空"],
            "permission_type": ["权限类型必须是 read、write、hidden 或 masked"]
        }
    }
}
```

#### 9.4.2 权限冲突

```http
HTTP/1.1 409 Conflict
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "CONFLICT",
        "message": "权限配置冲突",
        "details": {
            "reason": "该角色已配置相同字段的写入权限，无法再授予只读权限"
        }
    }
}
```

#### 9.4.3 权限不足

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "您没有权限管理此权限配置"
    }
}
```

#### 9.4.4 角色不存在

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "角色不存在",
        "details": {
            "role_id": "role-id-123"
        }
    }
}
```

### 9.5 标准错误码引用

本模块 API 使用以下标准错误码（详见 `api.md`）:

| 错误码 | HTTP状态码 | 使用场景 |
|--------|-----------|---------|
| `VALIDATION_ERROR` | 400 | 权限配置参数验证失败 |
| `UNAUTHORIZED` | 401 | 用户未登录 |
| `PERMISSION_DENIED` | 403 | 用户无权限管理权限配置 |
| `NOT_FOUND` | 404 | 角色/用户不存在 |
| `CONFLICT` | 409 | 权限配置冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 跨组织访问权限配置 |
| `SOFT_DELETED` | 410 | 访问已删除的权限配置 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |
```

#### 📝 修改后的内容摘要

- 添加了第 9 章节 "API接口设计"（位于后续任务章节之前）
- 包含标准 CRUD 端点表格（3 个模型：FieldPermission、DataPermission、PermissionRule）
- 包含批量操作端点（batch-delete、batch-restore、batch-update）
- 包含自定义权限端点（字段权限管理、数据权限管理、权限规则验证、权限缓存管理）
- 包含完整的请求/响应示例（创建字段权限、授予权限、检查权限、批量删除、获取可查看部门）
- 包含错误响应示例（验证错误、权限冲突、权限不足、角色不存在）
- 引用标准错误码定义

---

## 总结与建议

### ✅ 修复完成标准

所有 5 个模块的 backend.md 文件在修复后应包含:

1. ✅ **标准 CRUD 端点表格**
   - 明确列出所有继承自 `BaseModelViewSetWithBatch` 的端点
   - 包括 GET、POST、PUT、PATCH、DELETE 标准操作
   - 包括 extended operations: `/deleted/`、`/{id}/restore/`
   - 包括 batch operations: `/batch-delete/`、`/batch-restore/`、`/batch-update/`

2. ✅ **自定义端点表格**
   - 列出模块特有的业务端点
   - 包含方法、路径、说明、权限

3. ✅ **请求/响应示例**
   - 至少包含 2-3 个典型操作的完整示例
   - 包括创建记录、批量操作等关键场景
   - 展示标准响应格式（success、message、data、summary、results）

4. ✅ **错误响应示例**
   - 至少包含 3-4 个错误场景示例
   - 包括验证错误、权限错误、资源不存在等常见错误
   - 展示标准错误格式（success、error.code、error.message、error.details）

5. ✅ **标准错误码引用**
   - 引用 `common_base_features/api.md` 中定义的错误码
   - 列出模块使用的具体错误码及其使用场景

### 📊 修复优先级

| 优先级 | 模块 | 理由 | 建议完成时间 |
|--------|------|------|-------------|
| 🔴 高 | phase2_1_wework_sso | 基础 SSO 功能，优先级最高 | 第 1 周 |
| 🔴 高 | phase2_2_wework_sync | 数据同步依赖 SSO，次高优先级 | 第 1 周 |
| 🔴 高 | phase2_5_permission_enhancement | 权限系统是核心功能 | 第 2 周 |
| 🟡 中 | phase2_3_notification | 通知系统相对独立 | 第 2 周 |
| 🟡 中 | phase2_4_org_enhancement | 已有基础内容，仅需补充完善 | 第 3 周 |

### 📝 后续工作建议

1. **文档模板标准化**
   - 将本次修复的内容更新到 `PRD_TEMPLATE.md` 中
   - 确保未来新建的模块文档直接包含完整的 API 章节

2. **自动化检查**
   - 可以考虑添加文档检查脚本，确保每个模块的 backend.md 都包含必需的章节
   - 使用 grep 或 markdown lint 工具验证 API 章节的完整性

3. **版本控制**
   - 本次修复完成后，建议创建一个 git tag 或分支
   - 便于回溯和对比修复前后的差异

4. **代码实现同步**
   - 在实际实现 API 时，确保严格遵循文档中定义的接口规范
   - 使用 BaseModelViewSetWithBatch 自动提供标准端点
   - 自定义端点遵循 RESTful 设计原则

---

## 附录：API 规范快速参考

### A. 标准响应格式

#### 成功响应

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        "code": "ASSET001",
        ...
    }
}
```

#### 列表响应

```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "url",
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
            "field": ["error message"]
        }
    }
}
```

#### 批量操作响应

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

### B. 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

---

**报告生成时间**: 2026-01-15
**报告版本**: v1.0
**参考规范**: `docs/plans/common_base_features/api.md`
