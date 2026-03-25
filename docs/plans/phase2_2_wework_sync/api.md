# Phase 2.2: 企业微信通讯录同步 - API接口定义

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
| GET | `/api/sso/sync/config/` | 获取同步配置 |
| GET | `/api/sso/sync/status/` | 获取同步状态 |
| GET | `/api/sso/sync/logs/` | 获取同步日志列表 |
| POST | `/api/sso/sync/trigger/` | 手动触发同步 |

---

## 1. 获取同步配置

### GET /api/sso/sync/config/

获取当前组织的企业微信同步配置状态。

**请求**

```http
GET /api/sso/sync/config/
Authorization: Bearer <token>
```

**响应（已启用）**

```json
{
  "success": true,
  "data": {
    "enabled": true,
    "corp_name": "示例企业",
    "agent_id": 1000001,
    "auto_sync_enabled": true
  }
}
```

**响应（未启用）**

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "企业微信未配置或未启用"
  }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| enabled | boolean | 企业微信同步是否启用 |
| corp_name | string | 企业名称 |
| agent_id | number | 应用ID |
| auto_sync_enabled | boolean | 是否启用自动同步 |

---

## 2. 获取同步状态

### GET /api/sso/sync/status/

获取最近的同步状态和统计信息。

**请求**

```http
GET /api/sso/sync/status/
Authorization: Bearer <token>
```

**响应（已同步）**

```json
{
  "success": true,
  "data": {
    "status": "success",
    "last_sync_time": "2024-01-15T10:30:00Z",
    "stats": {
      "total": 156,
      "created": 12,
      "updated": 144,
      "deleted": 0,
      "failed": 0
    }
  }
}
```

**响应（从未同步）**

```json
{
  "success": true,
  "data": {
    "status": "never_synced",
    "last_sync_time": null,
    "stats": {}
  }
}
```

**响应（同步中）**

```json
{
  "success": true,
  "data": {
    "status": "running",
    "last_sync_time": "2024-01-15T11:00:00Z",
    "stats": {
      "total": 0,
      "created": 0,
      "updated": 0,
      "deleted": 0,
      "failed": 0
    }
  }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 同步状态：never_synced/running/success/failed/partial |
| last_sync_time | string | 最后同步时间（ISO 8601） |
| stats.total | number | 处理的总记录数 |
| stats.created | number | 新增的记录数 |
| stats.updated | number | 更新的记录数 |
| stats.deleted | number | 删除的记录数 |
| stats.failed | number | 失败的记录数 |

---

## 3. 获取同步日志列表

### GET /api/sso/sync/logs/

获取同步日志历史记录。

**请求**

```http
GET /api/sso/sync/logs/?limit=20
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | integer | 否 | 返回数量限制，默认20 |
| offset | integer | 否 | 偏移量 |
| status | string | 否 | 筛选状态：running/success/failed/partial |
| sync_type | string | 否 | 筛选类型：full/department/user |

**响应**

```json
{
  "success": true,
  "data": {
    "count": 45,
    "next": null,
    "previous": "/api/sso/sync/logs/?limit=10&offset=10",
    "results": [
      {
        "id": 123,
        "sync_type": "full",
        "sync_type_display": "全量同步",
        "sync_source": "wework",
        "status": "success",
        "status_display": "成功",
        "started_at": "2024-01-15T10:30:00Z",
        "finished_at": "2024-01-15T10:32:15Z",
        "duration": 135,
        "total_count": 156,
        "created_count": 12,
        "updated_count": 144,
        "deleted_count": 0,
        "failed_count": 0,
        "error_message": ""
      },
      {
        "id": 122,
        "sync_type": "department",
        "sync_type_display": "部门同步",
        "sync_source": "wework",
        "status": "success",
        "status_display": "成功",
        "started_at": "2024-01-14T02:00:00Z",
        "finished_at": "2024-01-14T02:00:45Z",
        "duration": 45,
        "total_count": 25,
        "created_count": 2,
        "updated_count": 23,
        "deleted_count": 0,
        "failed_count": 0,
        "error_message": ""
      }
    ]
  }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 日志ID |
| sync_type | string | 同步类型：full/department/user |
| sync_type_display | string | 同步类型显示名称 |
| sync_source | string | 同步来源：wework/dingtalk/feishu |
| status | string | 状态：running/success/failed/partial |
| status_display | string | 状态显示名称 |
| started_at | string | 开始时间（ISO 8601） |
| finished_at | string | 结束时间（ISO 8601），运行中为null |
| duration | integer | 耗时（秒） |
| total_count | integer | 处理总数 |
| created_count | integer | 新增数量 |
| updated_count | integer | 更新数量 |
| deleted_count | integer | 删除数量 |
| failed_count | integer | 失败数量 |
| error_message | string | 错误信息 |

---

## 4. 获取同步日志详情

### GET /api/sso/sync/logs/{id}/

获取单条同步日志的详细信息。

**请求**

```http
GET /api/sso/sync/logs/123/
Authorization: Bearer <token>
```

**响应**

```json
{
  "success": true,
  "data": {
    "id": 123,
    "sync_type": "full",
    "sync_type_display": "全量同步",
    "sync_source": "wework",
    "status": "success",
    "status_display": "成功",
    "started_at": "2024-01-15T10:30:00Z",
    "finished_at": "2024-01-15T10:32:15Z",
    "duration": 135,
    "total_count": 156,
    "created_count": 12,
    "updated_count": 144,
    "deleted_count": 0,
    "failed_count": 0,
    "error_message": "",
    "error_details": {}
  }
}
```

---

## 5. 手动触发同步

### POST /api/sso/sync/trigger/

手动触发企业微信通讯录同步。

**请求**

```http
POST /api/sso/sync/trigger/
Content-Type: application/json
Authorization: Bearer <token>

{
  "sync_type": "full"
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| sync_type | string | 否 | 同步类型：full（全量，默认）/department（仅部门）/user（仅用户） |

**响应（成功启动）**

```json
{
  "success": true,
  "message": "同步任务已启动",
  "data": {
    "task_id": "1a2b3c4d-5e6f-7g8h-9i0j-k1l2m3n4o5p6",
    "sync_type": "full"
  }
}
```

**响应（已有任务运行中）**

```http
HTTP/1.1 409 Conflict

{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "已有同步任务正在运行中",
    "details": {
      "log_id": 123
    }
  }
}
```

**响应（未配置企业微信）**

```http
HTTP/1.1 404 Not Found

{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "企业微信未配置或未启用"
  }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | string | Celery异步任务ID，可用于查询任务状态 |
| message | string | 提示信息 |
| sync_type | string | 同步类型 |

---

## 企业微信API端点

以下是企业微信通讯录同步相关的API端点：

| 功能 | 端点 | 说明 |
|------|------|------|
| 获取access_token | /cgi-bin/gettoken | 获取应用凭证 |
| 获取部门列表 | /cgi-bin/department/list | 获取全部部门 |
| 获取部门成员 | /cgi-bin/user/list | 获取部门成员详情 |
| 获取成员详情 | /cgi-bin/user/get | 获取单个成员详细信息 |
| 批量获取成员 | /cgi-bin/user/batchget | 批量获取成员详情 |

## API基础URL

```
https://qyapi.weixin.qq.com/cgi-bin
```

---

## 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| wework_not_enabled | 404 | 企业微信未启用 |
| sync_already_running | 409 | 已有同步任务运行中 |
| invalid_sync_type | 400 | 无效的同步类型 |
| sync_failed | 500 | 同步执行失败 |

---

## 同步状态流转图

```
                     ┌─────────────┐
                     │ never_synced│
                     └──────┬──────┘
                            │ 触发同步
                            ▼
                     ┌─────────────┐
                     │   running   │ ◄─────────┐
                     └──────┬──────┘          │
                            │ 完成            │ 定时任务
            ┌───────────────┼───────────────┐ │
            ▼               ▼               ▼ │
      ┌──────────┐    ┌──────────┐    ┌──────────┐
      │ success  │    │  failed  │    │ partial  │
      └──────────┘    └──────────┘    └──────────┘
           │               │               │
           └───────────────┴───────────────┘
                           │
                    下次触发同步
```

---

## 轮询建议

前端在触发同步后，建议使用以下轮询策略获取同步结果：

1. **初始阶段**：每2秒轮询一次
2. **同步中**：每3秒轮询一次
3. **超时处理**：超过5分钟未完成视为超时

示例代码：

```typescript
const pollSyncStatus = async (taskId: string) => {
  const maxAttempts = 150 // 5分钟 / 2秒
  let attempts = 0

  const poll = async () => {
    const status = await getSyncStatus()

    if (status.status !== 'running') {
      return status // 同步完成或失败
    }

    if (attempts++ < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 2000))
      return poll()
    }

    throw new Error('同步超时')
  }

  return poll()
}
```

---

## 后续任务

1. Phase 2.3: 实现企业微信消息推送通知API
2. 扩展支持钉钉、飞书的通讯录同步API
