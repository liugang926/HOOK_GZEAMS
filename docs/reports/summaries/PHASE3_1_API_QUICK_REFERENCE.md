# LogicFlow Workflow Engine API - Quick Reference

## Base URL
```
http://localhost:8000/api
```

---

## Flow Definitions

### List Flow Definitions
```http
GET /api/process-definitions/
```

Query Parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)
- `search`: Search in name, code, description
- `status`: Filter by status (draft/published/archived)
- `category`: Filter by category
- `code`: Filter by code (icontains)
- `name`: Filter by name (icontains)
- `ordering`: Order by field (e.g., `-created_at`)

### Create Flow Definition
```http
POST /api/process-definitions/
Content-Type: application/json

{
    "code": "PROCUREMENT_APPROVAL",
    "name": "采购审批流程",
    "definition": {
        "nodes": [
            {
                "id": "node_1",
                "type": "start",
                "name": "开始"
            },
            {
                "id": "node_2",
                "type": "task",
                "name": "部门审批"
            },
            {
                "id": "node_3",
                "type": "end",
                "name": "结束"
            }
        ],
        "edges": [
            {
                "id": "edge_1",
                "sourceNodeId": "node_1",
                "targetNodeId": "node_2"
            },
            {
                "id": "edge_2",
                "sourceNodeId": "node_2",
                "targetNodeId": "node_3"
            }
        ]
    },
    "description": "资产采购审批流程",
    "version": "1.0",
    "category": "procurement",
    "tags": ["采购", "审批", "资产"]
}
```

### Get Flow Definition Detail
```http
GET /api/process-definitions/{id}/
```

### Update Flow Definition
```http
PUT /api/process-definitions/{id}/
PATCH /api/process-definitions/{id}/
```

### Delete Flow Definition
```http
DELETE /api/process-definitions/{id}/
```

### Validate Flow Definition
```http
POST /api/process-definitions/{id}/validate/
```

Response:
```json
{
    "success": true,
    "message": "流程定义验证通过"
}
```

### Publish Flow Definition
```http
POST /api/process-definitions/{id}/publish/
```

### Duplicate Flow Definition
```http
POST /api/process-definitions/{id}/duplicate/
```

### Get Categories
```http
GET /api/process-definitions/categories/
```

### Batch Operations
```http
# Batch Delete
POST /api/process-definitions/batch-delete/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}

# Batch Restore
POST /api/process-definitions/batch-restore/
{
    "ids": ["uuid1", "uuid2"]
}

# Batch Update
POST /api/process-definitions/batch-update/
{
    "ids": ["uuid1", "uuid2"],
    "data": {
        "status": "archived"
    }
}
```

---

## Flow Instances

### Create Flow Instance
```http
POST /api/workflow/instances/
Content-Type: application/json

{
    "flow_definition_id": "flow-def-uuid",
    "business_key": "ASSET-PROCUREMENT-001",
    "business_type": "asset_procurement",
    "business_data": {
        "asset_id": "asset-uuid-123",
        "requester": "user-uuid-456",
        "request_reason": "需要采购新设备"
    },
    "variables": {
        "priority": "high",
        "budget": 50000
    }
}
```

### List Flow Instances
```http
GET /api/workflow/instances/
```

Query Parameters:
- `flow_definition`: Filter by definition UUID
- `business_key`: Filter by business key
- `business_type`: Filter by business type
- `status`: Filter by status (pending/running/suspended/completed/terminated/failed)
- `started_by`: Filter by starter UUID

### Start Flow Instance
```http
POST /api/workflow/instances/{id}/start/
```

### Terminate Flow Instance
```http
POST /api/workflow/instances/{id}/terminate/
{
    "reason": "业务需求变更，取消流程"
}
```

### Get Flow History
```http
GET /api/workflow/instances/{id}/history/
```

### Get Pending Nodes
```http
GET /api/workflow/instances/{id}/pending-nodes/
```

Response:
```json
{
    "success": true,
    "data": {
        "pending_nodes": [
            {
                "id": "node-instance-uuid",
                "node_id": "node_2",
                "node_name": "部门审批",
                "status": "pending",
                "assignee": {
                    "id": "user-uuid",
                    "username": "manager"
                }
            }
        ],
        "count": 1
    }
}
```

---

## Node Instances

### Execute Node
```http
POST /api/workflow/nodes/{id}/execute/
```

### Complete Node
```http
POST /api/workflow/nodes/{id}/complete/
Content-Type: application/json

{
    "result": {
        "approved": true,
        "comments": "同意采购申请"
    },
    "comments": "预算充足，可以采购"
}
```

### Get My Tasks
```http
GET /api/workflow/nodes/my-tasks/
```

Query Parameters:
- `status`: Filter by status (default: pending)

Response:
```json
{
    "success": true,
    "data": [
        {
            "id": "node-instance-uuid",
            "node_name": "部门审批",
            "flow_instance": {
                "business_key": "ASSET-PROCUREMENT-001",
                "flow_definition": {
                    "name": "采购审批流程"
                }
            },
            "status": "pending",
            "created_at": "2026-01-16T10:30:00Z"
        }
    ]
}
```

---

## Operation Logs

### List Operation Logs
```http
GET /api/workflow/logs/
```

Query Parameters:
- `flow_definition_id`: Filter by definition UUID
- `flow_instance_id`: Filter by instance UUID
- `node_instance_id`: Filter by node UUID
- `operation`: Filter by operation type
- `created_by`: Filter by creator UUID

---

## Error Handling

### Validation Error (400)
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "流程定义验证失败",
        "details": {
            "definition": [
                "流程定义缺少nodes字段"
            ]
        }
    }
}
```

### Not Found (404)
```json
{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "流程定义不存在"
    }
}
```

### Permission Denied (403)
```json
{
    "success": false,
    "error": {
        "code": "PERMISSION_DENIED",
        "message": "当前用户无权执行此节点"
    }
}
```

---

## Node Types

### Start Node
```json
{
    "id": "node_1",
    "type": "start",
    "name": "开始",
    "properties": {}
}
```

### Task Node
```json
{
    "id": "node_2",
    "type": "task",
    "name": "部门审批",
    "properties": {
        "assigneeType": "user",
        "assigneeId": "user-uuid",
        "formKey": "approval-form"
    }
}
```

### Gateway Node
```json
{
    "id": "node_3",
    "type": "gateway",
    "name": "条件判断",
    "properties": {
        "gatewayType": "exclusive",
        "condition": "${amount > 10000}"
    }
}
```

### End Node
```json
{
    "id": "node_4",
    "type": "end",
    "name": "结束",
    "properties": {}
}
```

---

## Edge Definition

```json
{
    "id": "edge_1",
    "sourceNodeId": "node_1",
    "targetNodeId": "node_2",
    "type": "default",
    "properties": {
        "condition": "${approved == true}"
    }
}
```

---

## Workflow Execution Flow

### 1. Create Definition
```http
POST /api/process-definitions/
{
    "name": "采购审批",
    "definition": {...}
}
```

### 2. Publish Definition
```http
POST /api/process-definitions/{id}/publish/
```

### 3. Create Instance
```http
POST /api/workflow/instances/
{
    "flow_definition_id": "...",
    "business_key": "PROC-001",
    "business_type": "procurement"
}
```

### 4. Start Instance
```http
POST /api/workflow/instances/{id}/start/
```

### 5. Get Pending Tasks
```http
GET /api/workflow/nodes/my-tasks/
```

### 6. Execute Node
```http
POST /api/workflow/nodes/{node_id}/execute/
```

### 7. Complete Node
```http
POST /api/workflow/nodes/{node_id}/complete/
{
    "result": {"approved": true},
    "comments": "同意"
}
```

### 8. Repeat Steps 5-7 Until Complete

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Create flow definition
def create_flow_definition():
    response = requests.post(
        f"{BASE_URL}/process-definitions/",
        json={
            "name": "采购审批流程",
            "definition": {
                "nodes": [...],
                "edges": [...]
            }
        }
    )
    return response.json()

# Publish flow
def publish_flow(flow_id):
    response = requests.post(
        f"{BASE_URL}/process-definitions/{flow_id}/publish/"
    )
    return response.json()

# Start workflow
def start_workflow(flow_id, business_key):
    # Create instance
    response = requests.post(
        f"{BASE_URL}/workflow/instances/",
        json={
            "flow_definition_id": flow_id,
            "business_key": business_key,
            "business_type": "procurement"
        }
    )
    instance_id = response.json()['data']['id']

    # Start instance
    response = requests.post(
        f"{BASE_URL}/workflow/instances/{instance_id}/start/"
    )
    return response.json()

# Get my tasks
def get_my_tasks():
    response = requests.get(
        f"{BASE_URL}/workflow/nodes/my-tasks/"
    )
    return response.json()

# Complete task
def complete_task(node_id, approved, comments):
    response = requests.post(
        f"{BASE_URL}/workflow/nodes/{node_id}/complete/",
        json={
            "result": {"approved": approved},
            "comments": comments
        }
    )
    return response.json()
```

---

## Testing with cURL

### Create and Publish Flow
```bash
# Create flow
curl -X POST http://localhost:8000/api/process-definitions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试流程",
    "definition": {
      "nodes": [
        {"id": "start", "type": "start", "name": "开始"},
        {"id": "task1", "type": "task", "name": "任务1"},
        {"id": "end", "type": "end", "name": "结束"}
      ],
      "edges": [
        {"id": "e1", "sourceNodeId": "start", "targetNodeId": "task1"},
        {"id": "e2", "sourceNodeId": "task1", "targetNodeId": "end"}
      ]
    }
  }'

# Publish flow (use returned ID)
curl -X POST http://localhost:8000/api/process-definitions/{id}/publish/
```

### Start Workflow
```bash
# Create instance
curl -X POST http://localhost:8000/api/workflow/instances/ \
  -H "Content-Type: application/json" \
  -d '{
    "flow_definition_id": "{flow_id}",
    "business_key": "TEST-001",
    "business_type": "test"
  }'

# Start instance (use returned ID)
curl -X POST http://localhost:8000/api/workflow/instances/{instance_id}/start/
```

### Complete Tasks
```bash
# Get my tasks
curl http://localhost:8000/api/workflow/nodes/my-tasks/

# Complete node
curl -X POST http://localhost:8000/api/workflow/nodes/{node_id}/complete/ \
  -H "Content-Type: application/json" \
  -d '{
    "result": {"approved": true},
    "comments": "同意"
  }'
```

---

## Common Workflows

### Procurement Approval
1. User submits procurement request
2. Manager approves/rejects
3. Finance reviews budget
4. Purchaser creates order
5. Assets team receives items

### Asset Transfer
1. Initiator requests transfer
2. Current department approves
3. Receiving department accepts
4. Asset management updates records

### Inventory Reconciliation
1. Inventory manager creates task
2. Staff scan assets
3. System identifies discrepancies
4. Manager reviews and confirms
5. Asset records updated

---

## Status Codes

### Flow Definition Status
- `draft`: Draft (not published)
- `published`: Published (ready for use)
- `archived`: Archived (not in use)

### Flow Instance Status
- `pending`: Pending (not started)
- `running`: Running (active)
- `suspended`: Suspended (paused)
- `completed`: Completed (finished)
- `terminated`: Terminated (cancelled)
- `failed`: Failed (error)

### Node Instance Status
- `pending`: Pending (waiting)
- `active`: Active (in progress)
- `completed`: Completed (finished)
- `skipped`: Skipped (bypassed)
- `failed`: Failed (error)

---

**Last Updated**: 2026-01-16
**API Version**: 1.0.0
