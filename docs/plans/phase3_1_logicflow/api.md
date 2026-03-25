# Phase 3.1: LogicFlow流程设计器 - API接口定义

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
| GET | `/api/workflows/workflows/` | 获取工作流列表 |
| POST | `/api/workflows/workflows/` | 创建工作流 |
| GET | `/api/workflows/workflows/{id}/` | 获取工作流详情 |
| PUT/PATCH | `/api/workflows/workflows/{id}/` | 更新工作流 |
| DELETE | `/api/workflows/workflows/{id}/` | 删除工作流 |
| POST | `/api/workflows/workflows/{id}/activate/` | 激活工作流 |
| POST | `/api/workflows/workflows/{id}/clone/` | 克隆工作流 |
| GET | `/api/workflows/workflows/by-business-object/` | 根据业务对象获取工作流 |

---

## 1. 工作流定义

### 1.1 获取工作流列表

**请求**
```
GET /api/workflows/workflows/
Authorization: Bearer <token>
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| business_object | string | 否 | 筛选业务对象 |
| is_enabled | boolean | 否 | 筛选启用状态 |
| page | integer | 否 | 页码 |
| page_size | integer | 否 | 每页数量 |

**响应**
```json
{
  "success": true,
  "data": {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "code": "asset_pickup_approval",
        "name": "资产领用审批",
        "business_object": "asset_pickup",
        "graph_data": {
          "nodes": [
            {
              "id": "node_1",
              "type": "start",
              "x": 100,
              "y": 100,
              "text": "开始",
              "properties": {}
            },
            {
              "id": "node_2",
              "type": "approval",
              "x": 300,
              "y": 100,
              "text": "部门审批",
              "properties": {
                "approveType": "or",
                "approvers": [],
                "timeout": 72
              }
            }
          ],
          "edges": [
            {
              "id": "edge_1",
              "sourceNodeId": "node_1",
              "targetNodeId": "node_2",
              "type": "polyline"
            }
          ]
        },
        "description": "资产领用审批流程",
        "version": 1,
        "is_enabled": true,
        "is_default": true,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 1.2 创建工作流

**请求**
```
POST /api/workflows/workflows/
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "asset_pickup_approval",
  "name": "资产领用审批",
  "business_object": "asset_pickup",
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  },
  "description": "资产领用审批流程"
}
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 流程编码（唯一） |
| name | string | 是 | 流程名称 |
| business_object | string | 是 | 关联业务对象 |
| graph_data | object | 是 | LogicFlow导出的JSON数据 |
| description | string | 否 | 流程描述 |
| is_enabled | boolean | 否 | 是否启用 |
| is_default | boolean | 否 | 是否为默认流程 |

**响应（成功）**
```
HTTP 201 Created

{
  "success": true,
  "message": "工作流创建成功",
  "data": {
    "id": 1,
    "code": "asset_pickup_approval",
    "name": "资产领用审批",
    "business_object": "asset_pickup",
    "graph_data": {...},
    "description": "资产领用审批流程",
    "version": 1,
    "is_enabled": true,
    "is_default": false,
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

**响应（错误）**
```
HTTP 400 Bad Request

{
  "success": false,
  "error": {
    "code": "CONFLICT",
    "message": "流程编码已存在"
  }
}
```

### 1.3 更新工作流

**请求**
```
PATCH /api/workflows/workflows/{id}/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "资产领用审批（新版）",
  "graph_data": {
    "nodes": [...],
    "edges": [...]
  }
}
```

**响应**
```json
{
  "success": true,
  "message": "工作流更新成功",
  "data": {
    "id": 1,
    "code": "asset_pickup_approval",
    "name": "资产领用审批（新版）",
    "graph_data": {...},
    "version": 1
  }
}
```

### 1.4 删除工作流

**请求**
```
DELETE /api/workflows/workflows/{id}/
Authorization: Bearer <token>
```

**响应**
```
HTTP 204 No Content
```

---

## 2. 工作流操作

### 2.1 激活工作流

**请求**
```
POST /api/workflows/workflows/{id}/activate/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "工作流 资产领用审批 已激活",
  "data": {
    "id": 1,
    "code": "asset_pickup_approval",
    "name": "资产领用审批",
    "is_enabled": true
  }
}
```

**说明**
激活工作流会将同业务对象的其他流程设为非默认（如果激活的是默认流程）。

### 2.2 克隆工作流

**请求**
```
POST /api/workflows/workflows/{id}/clone/
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "message": "工作流克隆成功",
  "data": {
    "id": 2,
    "code": "asset_pickup_approval_copy",
    "name": "资产领用审批 (副本)",
    "business_object": "asset_pickup",
    "graph_data": {...},
    "version": 1,
    "is_enabled": false
  }
}
```

### 2.3 根据业务对象获取工作流

**请求**
```
GET /api/workflows/workflows/by-business-object/?business_object=asset_pickup
Authorization: Bearer <token>
```

**响应**
```json
{
  "success": true,
  "data": {
    "count": 1,
    "results": [
      {
        "id": 1,
        "code": "asset_pickup_approval",
        "name": "资产领用审批",
        "business_object": "asset_pickup",
        "is_enabled": true,
        "is_default": true
      }
    ]
  }
}
```

---

## 3. LogicFlow 数据格式

### 3.1 节点数据结构

```json
{
  "id": "node_1",
  "type": "approval",
  "x": 300,
  "y": 200,
  "text": "部门审批",
  "properties": {
    "approveType": "or",
    "approvers": [
      {
        "type": "user",
        "user_id": 1,
        "user_name": "张三"
      }
    ],
    "timeout": 72,
    "timeoutAction": "transfer",
    "autoApprove": false,
    "allowTransfer": true,
    "allowAddApprover": false,
    "rejectType": "to_prev",
    "fieldPermissions": {
      "amount": "read_only",
      "department": "hidden"
    }
  }
}
```

### 3.2 连线数据结构

```json
{
  "id": "edge_1",
  "type": "polyline",
  "sourceNodeId": "node_1",
  "targetNodeId": "node_2",
  "properties": {
    "label": "通过",
    "condition": {
      "field": "amount",
      "operator": "gt",
      "value": "10000"
    }
  }
}
```

---

## 4. 节点类型

| 类型 | 说明 | properties |
|------|------|------------|
| start | 开始节点 | {} |
| approval | 审批节点 | approveType, approvers, timeout, autoApprove, allowTransfer |
| condition | 条件节点 | branches[], defaultFlow |
| cc | 抄送节点 | ccUsers[], ccType |
| end | 结束节点 | {} |

---

## 5. 审批方式

| 值 | 说明 |
|----|------|
| or | 或签（一人通过即可） |
| and | 会签（需全部通过） |
| seq | 依次审批 |

---

## 6. 审批人类型

| 类型 | 说明 | 配置 |
|------|------|------|
| user | 指定成员 | user_id |
| role | 指定角色 | role_id |
| leader | 发起人领导 | leader_type (direct/department/top), level |
| dynamic | 动态选择 | source_field, relation |
| self_select | 自选 | range (all/department/custom), count |

---

## 7. 错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| VALIDATION_ERROR | 400 | 流程编码已存在 |
| VALIDATION_ERROR | 400 | 流程图数据格式错误 |
| CONFLICT | 409 | 工作流正在使用中，无法删除 |
| VALIDATION_ERROR | 400 | 流程缺少开始节点 |
| VALIDATION_ERROR | 400 | 流程缺少结束节点 |
| VALIDATION_ERROR | 400 | 流程节点未连通 |

---

## 后续任务

1. Phase 3.2: 实现工作流执行引擎
2. Phase 4.1: 实现QR码扫描盘点
