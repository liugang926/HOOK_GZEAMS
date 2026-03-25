## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

# Phase 1.8: 移动端功能增强 - API接口定义

## 1. 设备管理 API

### 1.1 注册设备

```
POST /api/mobile/device/register/
```

**Request:**
```json
{
  "device_id": "uuid-xxxx-xxxx",
  "device_info": {
    "device_name": "iPhone 13",
    "device_type": "ios",
    "os_version": "16.0",
    "app_version": "1.0.0",
    "screen_size": "390x844",
    "model": "iPhone14,5"
  }
}
```

**响应**
```json
{
  "success": true,
  "message": "设备注册成功",
  "data": {
    "id": 1,
    "device_id": "uuid-xxxx-xxxx",
    "device_name": "iPhone 13",
    "device_type": "ios",
    "is_bound": true,
    "is_active": true,
    "allow_offline": true,
    "last_login_at": "2024-01-15T10:00:00Z"
  }
}
```

### 1.2 获取设备列表

```
GET /api/mobile/device/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "device_name": "iPhone 13",
        "device_type": "ios",
        "app_version": "1.0.0",
        "is_bound": true,
        "is_active": true,
        "last_login_at": "2024-01-15T10:00:00Z",
        "last_sync_at": "2024-01-15T11:30:00Z"
      }
    ]
  }
}
```

### 1.3 解绑设备

```
POST /api/mobile/device/{id}/unbind/
```

**响应**
```json
{
  "success": true,
  "message": "设备已解绑"
}
```

### 1.4 更新设备设置

```
PATCH /api/mobile/device/{id}/
```

**Request:**
```json
{
  "enable_biometric": true,
  "allow_offline": false
}
```

---

## 2. 数据同步 API

### 2.1 上传离线数据

```
POST /api/mobile/sync/upload/
```

**Request:**
```json
{
  "device_id": "uuid-xxxx-xxxx",
  "data": [
    {
      "table_name": "inventory.InventoryScan",
      "record_id": "local-1",
      "operation": "create",
      "data": {
        "asset_no": "ZC001",
        "scan_time": "2024-01-15T10:30:00Z",
        "location": "A区-01-01"
      },
      "version": 1,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "table_name": "assets.Asset",
      "record_id": "123",
      "operation": "update",
      "data": {
        "location": "A区-01-02"
      },
      "old_data": {
        "location": "A区-01-01"
      },
      "version": 5,
      "created_at": "2024-01-14T10:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**响应**
```json
{
  "success": true,
  "message": "数据上传完成",
  "data": {
    "success": 15,
    "failed": 0,
    "conflicts": 1,
    "errors": [],
    "server_version": 1705316400
  }
}
```

### 2.2 下载变更数据

```
POST /api/mobile/sync/download/
```

**Request:**
```json
{
  "last_sync_version": 1705316400,
  "tables": [
    "assets.Asset",
    "inventory.InventoryTask",
    "organizations.Department"
  ]
}
```

**响应**
```json
{
  "success": true,
  "message": "数据下载完成",
  "data": {
    "version": 1705317000,
    "changes": {
      "assets.Asset": [
        {
          "id": "100",
          "asset_no": "ZC100",
          "asset_name": "新资产",
          "version": 10
        }
      ],
      "inventory.InventoryTask": [
        {
          "id": "5",
          "task_no": "PD2024005",
          "status": "completed"
        }
      ]
    }
  }
}
```

### 2.3 全量同步

```
POST /api/mobile/sync/full/
```

**Request:**
```json
{
  "device_id": "uuid-xxxx-xxxx",
  "tables": ["assets.Asset", "organizations.Department"]
}
```

**响应**
```json
{
  "success": true,
  "message": "全量同步完成",
  "data": {
    "version": 1705317000,
    "data": {
      "assets.Asset": [...],
      "organizations.Department": [...]
    },
    "has_more": false,
    "next_page": null
  }
}
```

### 2.4 获取同步状态

```
GET /api/mobile/sync/status/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "last_sync_at": "2024-01-15T11:30:00Z",
    "server_version": 1705317000,
    "pending_upload": 0,
    "pending_download": 5,
    "conflicts": 1
  }
}
```

### 2.5 解决冲突

```
POST /api/mobile/sync/resolve-conflict/
```

**Request:**
```json
{
  "conflict_id": 10,
  "resolution": "merge",
  "merged_data": {
    "location": "A区-01-03",
    "status": "in_use"
  }
}
```

**响应**
```json
{
  "success": true,
  "message": "冲突已解决"
}
```

### 2.6 获取冲突列表

```
GET /api/mobile/sync/conflicts/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 10,
        "conflict_type": "version_mismatch",
        "conflict_type_display": "版本不匹配",
        "table_name": "assets.Asset",
        "record_id": "123",
        "local_data": {
          "location": "A区-01-02"
        },
        "server_data": {
          "location": "A区-01-03"
        },
        "resolution": "pending",
        "created_at": "2024-01-15T11:00:00Z"
      }
    ]
  }
}
```

---

## 3. 移动审批 API

### 3.1 获取待审批列表

```
GET /api/mobile/approval/pending/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量，默认20 |

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 100,
        "title": "资产采购申请-笔记本电脑",
        "workflow_name": "资产采购流程",
        "current_node": "部门审批",
        "created_by": "张三",
        "created_at": "2024-01-14T10:00:00Z",
        "urgent": true
      }
    ]
  }
}
```

### 3.2 审批操作

```
POST /api/mobile/approval/approve/
```

**Request:**
```json
{
  "instance_id": 100,
  "action": "approve",
  "comment": "同意采购"
}
```

**响应**
```json
{
  "success": true,
  "message": "审批成功",
  "data": {
    "next_node": {
      "name": "财务审批",
      "assignees": ["财务主管"]
    }
  }
}
```

**action 参数:**

| 值 | 说明 |
|----|------|
| approve | 同意 |
| reject | 拒绝 |
| transfer | 转办 |
| return | 驳回 |

### 3.3 批量审批

```
POST /api/mobile/approval/batch-approve/
```

**Request:**
```json
{
  "instance_ids": [100, 101, 102],
  "action": "approve",
  "comment": "批量同意"
}
```

**响应**
```json
{
  "success": true,
  "message": "批量审批完成",
  "data": {
    "success": 3,
    "failed": 0,
    "errors": []
  }
}
```

### 3.4 获取审批详情

```
GET /api/mobile/approval/{instance_id}/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "id": 100,
    "title": "资产采购申请-笔记本电脑",
    "workflow_name": "资产采购流程",
    "status": "in_progress",
    "current_node": {
      "id": 5,
      "name": "部门审批",
      "assignees": ["当前用户"]
    },
    "flow_chart": {
      "nodes": [...],
      "edges": [...]
    },
    "form_data": {
      "asset_name": "笔记本电脑",
      "quantity": 10,
      "budget": 50000
    },
    "approval_history": [
      {
        "node_name": "发起",
        "approver": "张三",
        "action": "submit",
        "comment": "",
        "approved_at": "2024-01-14T10:00:00Z"
      }
    ]
  }
}
```

### 3.5 添加审批意见

```
POST /api/mobile/approval/{instance_id}/comment/
```

**Request:**
```json
{
  "comment": "请补充预算明细"
}
```

### 3.6 设置审批代理

```
POST /api/mobile/approval/delegate/
```

**Request:**
```json
{
  "delegate_user_id": 5,
  "config": {
    "delegate_type": "temporary",
    "delegate_scope": "all",
    "start_time": "2024-01-15T00:00:00Z",
    "end_time": "2024-01-20T00:00:00Z",
    "reason": "出差期间"
  }
}
```

**响应**
```json
{
  "success": true,
  "message": "审批代理设置成功",
  "data": {
    "id": 1,
    "delegator": {
      "id": 1,
      "username": "admin"
    },
    "delegate": {
      "id": 5,
      "username": "delegate_user"
    },
    "delegate_type": "temporary",
    "start_time": "2024-01-15T00:00:00Z",
    "end_time": "2024-01-20T00:00:00Z",
    "is_active": true
  }
}
```

### 3.7 获取代理列表

```
GET /api/mobile/approval/delegates/
```

**响应**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "delegate": "李四",
        "delegate_type": "temporary",
        "start_time": "2024-01-15T00:00:00Z",
        "end_time": "2024-01-20T00:00:00Z",
        "is_active": true,
        "approved_count": 5
      }
    ]
  }
}
```

### 3.8 撤销代理

```
POST /api/mobile/approval/delegate/{id}/revoke/
```

**响应**
```json
{
  "success": true,
  "message": "代理已撤销"
}
```

---

## 4. 基础数据 API

### 4.1 获取基础数据配置

```
GET /api/mobile/baseline/config/
```

**Response:**
```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "tables": [
      {
        "name": "assets.Asset",
        "label": "资产",
        "fields": ["id", "asset_no", "asset_name", "category", "location"],
        "sync_enabled": true,
        "offline_enabled": true
      },
      {
        "name": "organizations.Department",
        "label": "部门",
        "fields": ["id", "name", "parent_id"],
        "sync_enabled": true,
        "offline_enabled": true
      }
    ],
    "max_storage": 52428800,
    "max_record_count": 10000
  }
}
```

### 4.2 获取数据字典

```
GET /api/mobile/baseline/dict/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | 否 | 字典类型 |

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "asset_status": [
      {"value": "normal", "label": "正常"},
      {"value": "scrapped", "label": "已报废"},
      {"value": "lost", "label": "丢失"}
    ],
    "asset_category": [
      {"value": "1", "label": "电子设备"},
      {"value": "2", "label": "办公家具"}
    ]
  }
}
```

---

## 5. 同步日志 API

### 5.1 获取同步日志

```
GET /api/mobile/sync/logs/
```

**Query Parameters:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |

**Response:**
```json
{
  "success": true,
  "message": "查询成功",
  "data": {
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 100,
        "sync_type": "incremental",
        "sync_type_display": "增量同步",
        "sync_direction": "upload",
        "sync_direction_display": "上传",
        "status": "success",
        "upload_count": 10,
        "download_count": 0,
        "conflict_count": 0,
        "duration": 3,
        "started_at": "2024-01-15T11:30:00Z"
      }
    ]
  }
}
```

---

## 6. WebSocket 推送

### 6.1 同步完成推送

```json
{
  "event": "sync.completed",
  "data": {
    "sync_type": "incremental",
    "upload_count": 10,
    "download_count": 5,
    "conflict_count": 0
  }
}
```

### 6.2 新待办推送

```json
{
  "event": "approval.created",
  "data": {
    "instance_id": 100,
    "title": "资产采购申请",
    "workflow_name": "资产采购流程"
  }
}
```

### 6.3 冲突提醒推送

```json
{
  "event": "sync.conflict",
  "data": {
    "conflict_count": 2,
    "conflicts": [
      {
        "id": 10,
        "table_name": "assets.Asset",
        "record_id": "123"
      }
    ]
  }
}
```

---

## 7. 错误码定义

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| NOT_FOUND | 404 | 设备未注册 |
| VALIDATION_ERROR | 400 | 设备数量超限 |
| VALIDATION_ERROR | 400 | 设备已解绑 |
| VALIDATION_ERROR | 400 | 设备不匹配 |
| SERVER_ERROR | 500 | 同步失败 |
| CONFLICT | 409 | 数据版本不匹配 |
| CONFLICT | 409 | 冲突解决失败 |
| VALIDATION_ERROR | 400 | 存储空间不足 |
| VALIDATION_ERROR | 400 | 离线模式未启用 |
| PERMISSION_DENIED | 403 | 无审批权限 |
| NOT_FOUND | 404 | 流程不存在 |
| CONFLICT | 409 | 流程已结束 |
| VALIDATION_ERROR | 400 | 代理设置失败 |

---

## 8. 离线支持

以下API支持离线操作（数据会缓存到本地队列）：

| API | 离线支持 |
|-----|----------|
| POST /api/mobile/sync/upload/ | 是（网络恢复后自动上传） |
| POST /api/mobile/approval/approve/ | 是 |
| POST /api/mobile/approval/batch-approve/ | 是 |
| GET /api/mobile/approval/pending/ | 部分（返回缓存数据） |
| GET /api/assets/assets/ | 部分（返回缓存数据） |

---

## 9. 数据压缩

为减少流量消耗，以下接口支持gzip压缩：

- POST /api/mobile/sync/download/
- POST /api/mobile/sync/full/

请求头设置：
```
Accept-Encoding: gzip
```
