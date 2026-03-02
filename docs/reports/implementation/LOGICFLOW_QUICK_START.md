# LogicFlow Workflow Engine - Quick Start Guide

## Overview

This guide helps you quickly start using the LogicFlow workflow engine frontend implementation for GZEAMS.

---

## Installation Status

✅ All dependencies installed
✅ All components created
✅ Router configuration updated
✅ API module integrated

---

## Access Points

### Development Server
```bash
cd frontend
npm run dev
```

Access the application at: `http://localhost:5173`

### Workflow URLs

| Page | URL | Description |
|------|-----|-------------|
| Workflow List | `/workflows` | View and manage all workflow definitions |
| Create Workflow | `/workflows/create` | Design a new workflow |
| Edit Workflow | `/workflows/:id/edit` | Edit existing workflow |
| Workflow Instances | `/workflows/:id/instances` | View instances for a specific workflow |
| All Instances | `/workflows/instances` | View all workflow instances |
| Instance Detail | `/workflows/instances/:id` | View instance details and history |

---

## Creating Your First Workflow

### Step 1: Navigate to Workflow Designer
```
http://localhost:5173/workflows/create
```

### Step 2: Fill in Basic Information
- **流程编码**: `ASSET_APPROVAL` (unique identifier)
- **流程名称**: `资产领用审批`
- **业务对象**: Select "资产领用"
- **描述**: `Standard asset approval workflow`
- **设为默认**: Off (unless this is the default workflow)
- **启用状态**: On

### Step 3: Design the Workflow

#### Add Nodes
1. From the left palette, drag these nodes to the canvas:
   - **开始** (Start) - Green rounded node
   - **审批** (Approval) - Blue rectangular node
   - **结束** (End) - Red rounded node

#### Connect Nodes
2. Create connections by dragging from the anchor points:
   - 开始 → 审批
   - 审批 → 结束

### Step 4: Configure the Approval Node

1. Click on the "审批" node to select it
2. In the right properties panel, configure:

**基础属性** Tab:
- 节点名称: `部门主管审批`

**审批配置** Tab:
- **审批方式**: Select "或签（一人通过）"
- **审批人**: Click "指定成员" tab, search and select users
- **超时时间**: Set to `72` hours
- **超时操作**: Select "转交管理员"
- **自动通过**: Toggle ON (if approver = initiator)
- **允许转交**: Toggle ON
- **允许加签**: Toggle OFF
- **退回方式**: Select "退回到上一节点"

**字段权限** Tab:
- Configure field permissions for this approval stage:
  - `code`: Hidden
  - `name`: Read-only
  - `status`: Editable
  - `description`: Editable

### Step 5: Save the Workflow
1. Click the "保存流程" button in the top-right
2. The workflow will be validated and saved

---

## Workflow Node Types

### 1. Start Node (开始)
**Purpose**: Workflow entry point
**Color**: Green
**Shape**: Rounded rectangle
**Configuration**: Field permissions for workflow initiation

**Usage**:
- Drag from palette to canvas
- Only one start node per workflow
- Automatically has output anchor
- Configure which fields users can edit when starting workflow

### 2. Approval Node (审批)
**Purpose**: Human approval step
**Color**: Blue
**Shape**: Rectangle with type indicator

**Configuration Options**:
- **Approve Type**:
  - 或签: Any one approver can approve
  - 会签: All approvers must approve
  - 依次: Approvers approve in sequence

- **Approvers**:
  - 指定成员: Specific users
  - 指定角色: Users with specific roles
  - 发起人领导: Initiator's supervisor
  - 自选: Initiator selects approvers

- **Timeout**:
  - Duration: 1-720 hours
  - Action: Auto-approve/reject/transfer

- **Other Settings**:
  - Auto-approve if same as initiator
  - Allow transferring approval
  - Allow adding more approvers
  - Reject behavior

**Usage**:
1. Drag to canvas
2. Configure approvers and rules
3. Set field permissions
4. Connect from previous node

### 3. Condition Node (条件)
**Purpose**: Branch workflow based on conditions
**Color**: Orange
**Shape**: Diamond

**Configuration Options**:
- **Condition Branches**: Add multiple conditions
- **Field Selection**: Choose field to evaluate
- **Operator**: eq, ne, gt, gte, lt, lte, contains, not_contains
- **Value**: Expected value
- **Default Flow**: Where to go if no conditions match

**Usage Example**:
```
Branch 1: amount > 10000 → General Manager Approval
Branch 2: amount <= 10000 → Department Manager Approval
Default: Reject
```

### 4. CC Node (抄送)
**Purpose**: Send notification without approval
**Color**: Gray
**Shape**: Rectangle

**Configuration Options**:
- **CC Users**: Users to notify
- **CC Type**:
  - Specific users
  - Roles
  - Dynamic selection

**Usage**:
- For informational notifications
- No approval required
- Users receive notification but can't approve/reject

### 5. End Node (结束)
**Purpose**: Workflow completion
**Color**: Red
**Shape**: Rounded rectangle

**Usage**:
- Marks workflow completion
- Only one end node per workflow
- Can have multiple input connections

---

## Workflow Validation Rules

The designer enforces these rules:

✅ **Required Nodes**:
- Must have exactly one start node
- Must have exactly one end node

✅ **Connections**:
- All nodes must be connected
- Start node cannot be a target
- End node cannot be a source
- No orphaned nodes

✅ **Validation on Save**:
- Checks for required nodes
- Verifies connectivity
- Validates node configurations

---

## Managing Workflow Instances

### View All Instances
```
http://localhost:5173/workflows/instances
```

**Features**:
- Search by workflow, status, date range
- View progress bars
- See current node
- View status (running/completed/cancelled/rejected)

**Instance Actions**:
- **详情**: View full instance details
- **流程图**: See execution status on diagram
- **历史**: View timeline of all actions
- **取消**: Cancel running instances

### Instance Status Colors

| Status | Color | Meaning |
|--------|-------|---------|
| Running | Blue | Workflow is in progress |
| Completed | Green | Successfully completed |
| Cancelled | Gray | Cancelled by user |
| Rejected | Red | Rejected by approver |

---

## API Usage Examples

### Create Workflow Definition
```javascript
import { createFlowDefinition } from '@/api/workflows'

const workflowData = {
  code: 'ASSET_APPROVAL',
  name: 'Asset Approval',
  business_object: 'asset_requisition',
  graph_data: {
    nodes: [
      { id: 'node1', type: 'start', text: '开始', x: 100, y: 100 },
      { id: 'node2', type: 'approval', text: '审批', x: 300, y: 100 },
      { id: 'node3', type: 'end', text: '结束', x: 500, y: 100 }
    ],
    edges: [
      { id: 'edge1', source: 'node1', target: 'node2' },
      { id: 'edge2', source: 'node2', target: 'node3' }
    ]
  },
  is_enabled: true,
  is_default: false
}

await createFlowDefinition(workflowData)
```

### Start Workflow Instance
```javascript
import { startFlowInstance } from '@/api/workflows'

const instanceData = {
  workflow: 1, // workflow ID
  business_object: 'asset_requisition',
  entity_id: 'ASSET-001', // related business data ID
  variables: {
    amount: 15000,
    department: 'IT',
    applicant: 'user123'
  }
}

const instance = await startFlowInstance(instanceData)
```

### Approve a Node
```javascript
import { approveNode } from '@/api/workflows'

const approvalData = {
  action: 'approve',
  comment: 'Approved, amount is within budget',
  variables: {}
}

await approveNode(instanceId, nodeId, approvalData)
```

### Reject a Node
```javascript
import { rejectNode } from '@/api/workflows'

const rejectionData = {
  reason: 'Amount exceeds department budget',
  comment: 'Please resubmit with lower amount'
}

await rejectNode(instanceId, nodeId, rejectionData)
```

---

## Common Workflows

### Simple Approval Workflow
```
开始 → 部门审批 → 结束
```

### Multi-Level Approval
```
开始 → 部门审批 → 条件判断 → [金额>1万] → 总经理审批 → 结束
                          → [金额<=1万] → 结束
```

### Parallel Approval
```
开始 → 财务审批 ─────┐
      ↓              ↓
      人事审批 ──────→ 结束
```

### Conditional Routing
```
开始 → 部门审批 → 条件判断 → [加急] → 总监审批 → 结束
                        → [正常] → 结束
```

---

## Troubleshooting

### Issue: Canvas not displaying
**Solution**: Ensure LogicFlow CSS is imported
```javascript
import '@logicflow/core/dist/style/index.css'
import '@logicflow/extension/lib/style/index.css'
```

### Issue: Nodes not dragging
**Solution**: Check that DndPanel plugin is registered
```javascript
const lf = new LogicFlow({
  plugins: [DndPanel, Menu]
})
```

### Issue: API calls failing
**Solution**:
1. Check backend is running
2. Verify API endpoints in `src/api/workflows.js`
3. Check browser console for errors
4. Verify authentication token

### Issue: Workflow not saving
**Solution**:
1. Ensure all required fields are filled
2. Check that flow has start and end nodes
3. Verify all nodes are connected
4. Check browser console for validation errors

---

## Best Practices

### 1. Workflow Design
- Keep workflows simple and linear when possible
- Use conditions sparingly to avoid complexity
- Test workflows with sample data before production
- Document workflow purpose in description field

### 2. Node Configuration
- Set appropriate timeouts for each approval
- Configure field permissions at each stage
- Use role-based approvers for flexibility
- Enable auto-approve for efficiency

### 3. Performance
- Avoid workflows with more than 20 nodes
- Use conditions instead of parallel paths when possible
- Cache workflow definitions after loading
- Use lazy loading for large instance lists

### 4. User Experience
- Use clear node names (e.g., "财务审批" not "节点2")
- Configure informative default values
- Set reasonable timeout periods
- Provide helpful comments when rejecting

---

## Next Steps

1. **Test Your Workflow**:
   - Create a test workflow
   - Start an instance
   - Approve/reject nodes
   - View history and diagrams

2. **Customize for Your Needs**:
   - Add custom node types
   - Configure business-specific fields
   - Set up role-based permissions
   - Integrate with mobile app

3. **Deploy to Production**:
   - Test all workflows thoroughly
   - Set up monitoring
   - Configure alerts
   - Train users

---

## Additional Resources

- **Full Implementation Report**: `PHASE3_1_LOGICFLOW_FRONTEND_IMPLEMENTATION_REPORT.md`
- **File Structure**: `LOGICFLOW_FRONTEND_FILE_STRUCTURE.txt`
- **PRD Document**: `docs/plans/phase3_1_logicflow/frontend.md`
- **LogicFlow Documentation**: https://site.logic-flow.cn/

---

## Support

For issues or questions:
1. Check the implementation report
2. Review the PRD specifications
3. Consult LogicFlow documentation
4. Contact the development team

**Implementation Date**: 2026-01-16
**Version**: 1.0.0
**Status**: Production Ready ✅
