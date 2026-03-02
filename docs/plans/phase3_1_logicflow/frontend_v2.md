# Phase 3.1: LogicFlow Workflow Engine - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement visual workflow designer using LogicFlow for drag-and-drop BPM workflow design with node-based configuration and preview capabilities.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/workflows.ts

export interface WorkflowDefinition {
  id: string
  name: string
  code: string
  description?: string
  category: WorkflowCategory
  version: string
  graphData: LogicFlowGraphData
  status: WorkflowStatus
  organizationId: string
  createdAt: string
  updatedAt: string
  createdBy: string
}

export enum WorkflowCategory {
  ASSET_PURCHASE = 'asset_purchase',
  ASSET_TRANSFER = 'asset_transfer',
  ASSET_DISPOSAL = 'asset_disposal',
  INVENTORY_TASK = 'inventory_task',
  LEAVE_REQUEST = 'leave_request',
  PURCHASE_REQUEST = 'purchase_request'
}

export enum WorkflowStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived'
}

export interface LogicFlowGraphData {
  nodes: LogicFlowNode[]
  edges: LogicFlowEdge[]
}

export interface LogicFlowNode {
  id: string
  type: NodeType
  x: number
  y: number
  text?: string
  properties?: NodeProperties
  data?: NodeData
}

export enum NodeType {
  START = 'start',
  END = 'end',
  APPROVAL = 'approval',
  CONDITION = 'condition',
  PARALLEL = 'parallel',
  MERGE = 'merge',
  NOTIFICATION = 'notification',
  GATEWAY = 'gateway'
}

export interface NodeProperties {
  approveType?: ApproveType
  approveMode?: ApproveMode
  approvers?: ApproverConfig[]
  timeout?: number
  autoPass?: boolean
  formPermission?: FormPermissionConfig
  conditionExpression?: string
  notificationChannels?: NotificationChannel[]
}

export enum ApproveType {
  ANY = 'any',
  ALL = 'all',
  SEQUENTIAL = 'sequential'
}

export enum ApproveMode {
  OR = 'or',
  AND = 'and'
}

export interface ApproverConfig {
  type: ApproverType
  value?: string
  name?: string
}

export enum ApproverType {
  USER = 'user',
  ROLE = 'role',
  DEPARTMENT = 'department',
  LEADER = 'leader',
  INITIATOR = 'initiator',
  SPECIFIC_USER = 'specific_user'
}

export interface FormPermissionConfig {
  [fieldCode: string]: FieldPermission
}

export enum FieldPermission {
  READ_ONLY = 'read_only',
  EDITABLE = 'editable',
  HIDDEN = 'hidden'
}

export interface NodeData {
  label?: string
  nodeType?: NodeType
  [key: string]: any
}

export interface LogicFlowEdge {
  id: string
  type: string
  sourceNodeId: string
  targetNodeId: string
  startPoint?: Point
  endPoint?: Point
  text?: string
  properties?: EdgeProperties
  data?: EdgeData
}

export interface Point {
  x: number
  y: number
}

export interface EdgeProperties {
  conditionExpression?: string
  label?: string
}

export interface EdgeData {
  label?: string
  [key: string]: any
}

export interface WorkflowInstance {
  id: string
  workflowId: string
  workflowName: string
  businessType: string
  businessId: string
  status: InstanceStatus
  currentNodeId?: string
  currentStep?: string
  initiatorId: string
  initiator?: User
  approvers?: ApproverInfo[]
  formData?: Record<string, any>
  organizationId: string
  createdAt: string
  updatedAt: string
  completedAt?: string
}

export enum InstanceStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled',
  TIMEOUT = 'timeout'
}

export interface ApproverInfo {
  userId: string
  userName: string
  status: ApprovalStatus
  comment?: string
  approvedAt?: string
}

export enum ApprovalStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled'
}

export interface User {
  id: string
  username: string
  realName: string
  email?: string
  mobile?: string
}

export interface ApprovalRecord {
  id: string
  instanceId: string
  nodeId: string
  nodeName: string
  approverId: string
  approverName: string
  action: ApprovalAction
  comment?: string
  attachments?: string[]
  createdAt: string
}

export enum ApprovalAction {
  SUBMIT = 'submit',
  APPROVE = 'approve',
  REJECT = 'reject',
  RETURN = 'return',
  CANCEL = 'cancel'
}
```

### API Service

```typescript
// frontend/src/api/workflows.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  WorkflowDefinition,
  WorkflowInstance,
  ApprovalRecord,
  WorkflowDefinitionCreate,
  WorkflowDefinitionUpdate
} from '@/types/workflows'

export const workflowApi = {
  // Workflow Definitions
  listDefinitions(params?: {
    category?: string
    status?: string
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<WorkflowDefinition>> {
    return request.get('/workflows/definitions/', { params })
  },

  getDefinition(id: string): Promise<WorkflowDefinition> {
    return request.get(`/workflows/definitions/${id}/`)
  },

  createDefinition(data: WorkflowDefinitionCreate): Promise<WorkflowDefinition> {
    return request.post('/workflows/definitions/', data)
  },

  updateDefinition(id: string, data: WorkflowDefinitionUpdate): Promise<WorkflowDefinition> {
    return request.put(`/workflows/definitions/${id}/`, data)
  },

  deleteDefinition(id: string): Promise<void> {
    return request.delete(`/workflows/definitions/${id}/`)
  },

  publishDefinition(id: string): Promise<void> {
    return request.post(`/workflows/definitions/${id}/publish/`)
  },

  archiveDefinition(id: string): Promise<void> {
    return request.post(`/workflows/definitions/${id}/archive/`)
  },

  // Workflow Instances
  listInstances(params?: {
    workflowId?: string
    businessType?: string
    status?: string
    initiatorId?: string
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<WorkflowInstance>> {
    return request.get('/workflows/instances/', { params })
  },

  getInstance(id: string): Promise<WorkflowInstance> {
    return request.get(`/workflows/instances/${id}/`)
  },

  startInstance(data: {
    workflowId: string
    businessType: string
    businessId: string
    formData?: Record<string, any>
  }): Promise<WorkflowInstance> {
    return request.post('/workflows/instances/start/', data)
  },

  cancelInstance(id: string, comment?: string): Promise<void> {
    return request.post(`/workflows/instances/${id}/cancel/`, { comment })
  },

  // Approval Actions
  approve(instanceId: string, data: {
    action: 'approve' | 'reject' | 'return'
    comment?: string
    formData?: Record<string, any>
  }): Promise<void> {
    return request.post(`/workflows/instances/${instanceId}/approve/`, data)
  },

  // Approval Records
  getApprovalRecords(instanceId: string): Promise<ApprovalRecord[]> {
    return request.get(`/workflows/instances/${instanceId}/records/`)
  },

  // Delegation
  delegateDelegation(fromUserId: string, toUserId: string, startDate: string, endDate: string): Promise<void> {
    return request.post('/workflows/delegation/', {
      fromUser: fromUserId,
      toUser: toUserId,
      startDate,
      endDate
    })
  }
}
```

---

## Component: WorkflowDesigner

```vue
<!-- frontend/src/components/workflows/WorkflowDesigner.vue -->
<template>
  <div class="workflow-designer">
    <!-- Toolbar -->
    <div class="designer-toolbar">
      <el-button-group>
        <el-button :icon="Plus" @click="handleAddNode">添加节点</el-button>
        <el-button :icon="Delete" @click="handleDeleteSelected">删除</el-button>
        <el-button :icon="Download" @click="handleExport">导出</el-button>
        <el-button :icon="Upload" @click="handleImport">导入</el-button>
      </el-button-group>

      <div class="toolbar-spacer"></div>

      <el-button-group>
        <el-button :icon="ZoomOut" @click="handleZoomOut">-</el-button>
        <el-button>{{ Math.round(zoom * 100) }}%</el-button>
        <el-button :icon="ZoomIn" @click="handleZoomIn">+</el-button>
        <el-button :icon="FullScreen" @click="handleFitView">适应</el-button>
      </el-button-group>

      <el-button type="primary" :icon="Check" @click="handleSave">
        保存
      </el-button>
    </div>

    <!-- Node Palette -->
    <div class="node-palette">
      <div class="palette-title">节点类型</div>
      <div class="palette-items">
        <div
          v-for="nodeType in nodeTypes"
          :key="nodeType.type"
          class="palette-item"
          :class="`type-${nodeType.type}`"
          draggable="true"
          @dragstart="handleDragStart($event, nodeType)"
        >
          <div class="palette-icon">
            <el-icon :size="20">
              <component :is="nodeType.icon" />
            </el-icon>
          </div>
          <span class="palette-label">{{ nodeType.label }}</span>
        </div>
      </div>
    </div>

    <!-- Canvas -->
    <div class="designer-canvas" ref="canvasRef">
      <div id="logicflow-container" ref="lfContainerRef"></div>
    </div>

    <!-- Property Panel -->
    <PropertyPanel
      v-model:visible="propertyPanelVisible"
      :node="selectedNode"
      :edge="selectedEdge"
      @update="handlePropertyUpdate"
    />

    <!-- Node Config Dialog -->
    <NodeConfigDialog
      v-model:visible="nodeConfigVisible"
      :node="configNode"
      @confirm="handleNodeConfigConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, shallowRef } from 'vue'
import LogicFlow from '@logicflow/core'
import { RegisterNode } from './nodes'
import {
  Plus,
  Delete,
  Download,
  Upload,
  ZoomIn,
  ZoomOut,
  FullScreen,
  Check,
  VideoPlay,
  VideoPause,
  CircleCheck,
  CircleClose,
  Share,
  Branch,
  Bell,
  Setting
} from '@element-plus/icons-vue'
import PropertyPanel from './PropertyPanel.vue'
import NodeConfigDialog from './NodeConfigDialog.vue'
import { workflowApi } from '@/api/workflows'
import { ElMessage } from 'element-plus'
import type { LogicFlowNode, LogicFlowEdge, NodeType } from '@/types/workflows'

interface Props {
  modelValue: LogicFlowGraphData
  workflowId?: string
}

interface Emits {
  (e: 'update:modelValue', data: LogicFlowGraphData): void
  (e: 'save', data: LogicFlowGraphData): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const lfContainerRef = ref<HTMLElement>()
let lf: LogicFlow | null = null

const zoom = ref(1)
const selectedNode = ref<LogicFlowNode | null>(null)
const selectedEdge = ref<LogicFlowEdge | null>(null)
const propertyPanelVisible = ref(false)
const nodeConfigVisible = ref(false)
const configNode = ref<LogicFlowNode | null>(null)

const nodeTypes = [
  { type: 'start', label: '开始', icon: VideoPlay },
  { type: 'end', label: '结束', icon: VideoPause },
  { type: 'approval', label: '审批', icon: CircleCheck },
  { type: 'condition', label: '条件', icon: Share },
  { type: 'parallel', label: '并行', icon: Branch },
  { type: 'notification', label: '通知', icon: Bell },
  { type: 'gateway', label: '网关', icon: Setting }
]

// Initialize LogicFlow
const initLogicFlow = () => {
  lf = new LogicFlow({
    container: lfContainerRef.value!,
    width: 1000,
    height: 800,
    plugins: [],
    grid: {
      size: 20,
      visible: true,
      type: 'dot'
    },
    background: {
      backgroundColor: '#f5f7fa'
    }
  })

  // Register custom nodes
  RegisterNode(lf)

  // Load graph data
  if (props.modelValue) {
    lf.render(props.modelValue)
  }

  // Event listeners
  lf.on('node:click', handleNodeClick)
  lf.on('edge:click', handleEdgeClick)
  lf.on('blank:click', handleBlankClick)
  lf.on('node:drop', handleNodeDrop)
  lf.on('connection', handleConnection)
}

const handleNodeClick = ({ data }: { data: LogicFlowNode }) => {
  selectedNode.value = data
  selectedEdge.value = null
  propertyPanelVisible.value = true
}

const handleEdgeClick = ({ data }: { data: LogicFlowEdge }) => {
  selectedEdge.value = data
  selectedNode.value = null
  propertyPanelVisible.value = true
}

const handleBlankClick = () => {
  selectedNode.value = null
  selectedEdge.value = null
  propertyPanelVisible.value = false
}

const handleDragStart = (event: DragEvent, nodeType: { type: NodeType }) => {
  event.dataTransfer?.setData('nodeType', nodeType.type)
}

const handleNodeDrop = (event: DragEvent) => {
  const nodeType = event.dataTransfer?.getData('nodeType') as NodeType
  if (!nodeType || !lf) return

  const point = lf.getPointByClient(event.x, event.y)

  lf.addNode({
    type: nodeType,
    x: point.x,
    y: point.y,
    text: getNodeDefaultLabel(nodeType)
  })
}

const handleConnection = (data: any) => {
  // Validate connection
  if (!isValidConnection(data.sourceNodeId, data.targetNodeId)) {
    ElMessage.warning('无法连接这两个节点')
    return false
  }
}

const isValidConnection = (sourceId: string, targetId: string): boolean => {
  // Add validation logic
  return true
}

const getNodeDefaultLabel = (type: NodeType): string => {
  const labels: Record<NodeType, string> = {
    start: '开始',
    end: '结束',
    approval: '审批节点',
    condition: '条件分支',
    parallel: '并行网关',
    notification: '通知',
    gateway: '网关'
  }
  return labels[type] || '节点'
}

const handleAddNode = () => {
  if (!lf) return
  const { x, y } = lf.graphModel
  lf.addNode({
    type: 'approval',
    x: x / 2,
    y: y / 2,
    text: '审批节点'
  })
}

const handleDeleteSelected = () => {
  if (!lf) return

  const selectedElements = lf.getSelectElements(true)
  if (selectedElement.nodes.length > 0) {
    selectedElements.nodes.forEach(node => {
      lf.deleteNode(node.id)
    })
  } else if (selectedElements.edges.length > 0) {
    selectedElements.edges.forEach(edge => {
      lf.deleteEdge(edge.id)
    })
  }
}

const handleZoomIn = () => {
  if (!lf) return
  zoom.value = Math.min(zoom.value + 0.1, 2)
  lf.zoom(zoom.value)
}

const handleZoomOut = () => {
  if (!lf) return
  zoom.value = Math.max(zoom.value - 0.1, 0.5)
  lf.zoom(zoom.value)
}

const handleFitView = () => {
  if (!lf) return
  lf.fitView(20)
  zoom.value = 1
}

const handleExport = () => {
  if (!lf) return
  const data = lf.getGraphData()
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'workflow.json'
  a.click()
  URL.revokeObjectURL(url)
}

const handleImport = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file || !lf) return

    const text = await file.text()
    const data = JSON.parse(text)
    lf.render(data)
    emit('update:modelValue', data)
  }
  input.click()
}

const handleSave = async () => {
  if (!lf) return
  const data = lf.getGraphData()
  emit('save', data)

  if (props.workflowId) {
    await workflowApi.updateDefinition(props.workflowId, {
      name: '',
      graphData: data
    })
    ElMessage.success('保存成功')
  }
}

const handlePropertyUpdate = (nodeOrEdge: LogicFlowNode | LogicFlowEdge, updates: any) => {
  if (!lf) return

  if ('sourceNodeId' in nodeOrEdge) {
    // Edge
    lf.updateEdge(nodeOrEdge.id, updates)
  } else {
    // Node
    lf.updateNode(nodeOrEdge.id, updates)
  }
}

const handleNodeConfigConfirm = (config: any) => {
  if (!configNode.value || !lf) return

  lf.updateNode(configNode.value.id, {
    properties: config
  })

  nodeConfigVisible.value = false
}

onMounted(() => {
  initLogicFlow()
})

onUnmounted(() => {
  lf?.destroy()
})
</script>

<style scoped>
.workflow-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f5f7fa;
}

.designer-toolbar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  gap: 12px;
}

.toolbar-spacer {
  flex: 1;
}

.workflow-designer {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.node-palette {
  width: 200px;
  background: white;
  border-right: 1px solid #e4e7ed;
  padding: 16px;
  overflow-y: auto;
}

.palette-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 12px;
  color: #303133;
}

.palette-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.palette-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: move;
  transition: all 0.2s;
}

.palette-item:hover {
  background: #ecf5ff;
  transform: translateX(4px);
}

.palette-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 6px;
}

.palette-item.type-start .palette-icon { background: #67c23a; color: white; }
.palette-item.type-end .palette-icon { background: #f56c6c; color: white; }
.palette-item.type-approval .palette-icon { background: #409eff; color: white; }
.palette-item.type-condition .palette-icon { background: #e6a23c; color: white; }
.palette-item.type-parallel .palette-icon { background: #909399; color: white; }
.palette-item.type-notification .palette-icon { background: #67c23a; color: white; }
.palette-item.type-gateway .palette-icon { background: #909399; color: white; }

.palette-label {
  font-size: 13px;
  color: #606266;
}

.designer-canvas {
  flex: 1;
  position: relative;
}

#logicflow-container {
  width: 100%;
  height: 100%;
}
</style>
```

---

## Component: PropertyPanel

```vue
<!-- frontend/src/components/workflows/PropertyPanel.vue -->
<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="属性配置"
    size="400px"
    direction="rtl"
  >
    <div v-if="node" class="property-content">
      <!-- Node Properties -->
      <SectionBlock title="基础信息">
        <el-form label-width="80px">
          <el-form-item label="节点类型">
            <el-tag>{{ getNodeTypeLabel(node.type) }}</el-tag>
          </el-form-item>
          <el-form-item label="节点名称">
            <el-input v-model="nodeLabel" @blur="handleLabelChange" />
          </el-form-item>
        </el-form>
      </SectionBlock>

      <!-- Approval Node Properties -->
      <template v-if="node.type === 'approval'">
        <SectionBlock title="审批配置">
          <el-form label-width="100px" @submit.prevent>
            <el-form-item label="审批类型">
              <el-radio-group
                :model-value="node.properties?.approveType"
                @change="handlePropertyChange('approveType', $event)"
              >
                <el-radio label="any">或签</el-radio>
                <el-radio label="all">会签</el-radio>
                <el-radio label="sequential">依次</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="审批人">
              <div class="approver-list">
                <div
                  v-for="(approver, index) in (node.properties?.approvers || [])"
                  :key="index"
                  class="approver-item"
                >
                  <el-tag closable @close="handleRemoveApprover(index)">
                    {{ getApproverLabel(approver) }}
                  </el-tag>
                </div>
                <el-button link @click="showApproverSelector = true">
                  + 添加审批人
                </el-button>
              </div>
            </el-form-item>
            <el-form-item label="超时时间">
              <el-input-number
                :model-value="node.properties?.timeout"
                @change="handlePropertyChange('timeout', $event)"
                :min="0"
                :step="1"
              />
              <span style="margin-left: 8px; color: #909399">小时</span>
            </el-form-item>
            <el-form-item label="自动通过">
              <el-switch
                :model-value="node.properties?.autoPass"
                @change="handlePropertyChange('autoPass', $event)"
              />
            </el-form-item>
          </el-form>
        </SectionBlock>

        <SectionBlock title="表单权限">
          <div class="form-permission-config">
            <el-table
              :data="formFields"
              size="small"
              border
            >
              <el-table-column prop="code" label="字段" width="120" />
              <el-table-column prop="name" label="名称" />
              <el-table-column label="权限" width="120">
                <template #default="{ row }">
                  <el-select
                    :model-value="getFieldPermission(row.code)"
                    @change="handleFieldPermissionChange(row.code, $event)"
                    size="small"
                  >
                    <el-option label="只读" value="read_only" />
                    <el-option label="可编辑" value="editable" />
                    <el-option label="隐藏" value="hidden" />
                  </el-select>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </SectionBlock>
      </template>

      <!-- Condition Node Properties -->
      <template v-if="node.type === 'condition'">
        <SectionBlock title="条件配置">
          <el-form label-width="80px">
            <el-form-item label="条件表达式">
              <el-input
                type="textarea"
                :rows="4"
                :model-value="node.properties?.conditionExpression"
                @input="handlePropertyChange('conditionExpression', $event)"
                placeholder="如: amount > 10000 && department == 'finance'"
              />
              <div class="help-text">
                支持变量: formData.{字段名}
              </div>
            </el-form-item>
          </el-form>
        </SectionBlock>
      </template>

      <!-- Notification Node Properties -->
      <template v-if="node.type === 'notification'">
        <SectionBlock title="通知配置">
          <el-form label-width="100px">
            <el-form-item label="通知渠道">
              <el-checkbox-group
                :model-value="node.properties?.notificationChannels"
                @change="handlePropertyChange('notificationChannels', $event)"
              >
                <el-checkbox label="inbox">站内信</el-checkbox>
                <el-checkbox label="email">邮件</el-checkbox>
                <el-checkbox label="sms">短信</el-checkbox>
                <el-checkbox label="wework">企微</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </SectionBlock>
      </template>
    </div>

    <!-- Edge Properties -->
    <div v-else-if="edge" class="property-content">
      <SectionBlock title="连线配置">
        <el-form label-width="80px">
          <el-form-item label="连线名称">
            <el-input
              :model-value="edge.text"
              @input="handleEdgeLabelChange"
            />
          </el-form-item>
          <el-form-item label="条件表达式">
            <el-input
              type="textarea"
              :rows="3"
              :model-value="edge.properties?.conditionExpression"
              @input="handleEdgePropertyChange('conditionExpression', $event)"
              placeholder="条件分支表达式"
            />
          </el-form-item>
        </el-form>
      </SectionBlock>
    </div>

    <!-- Approver Selector Dialog -->
    <ApproverSelector
      v-model:visible="showApproverSelector"
      :selected="node?.properties?.approvers || []"
      @confirm="handleApproverConfirm"
    />
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import SectionBlock from '@/components/common/SectionBlock.vue'
import ApproverSelector from './ApproverSelector.vue'
import type { LogicFlowNode, LogicFlowEdge } from '@/types/workflows'

interface Props {
  visible: boolean
  node?: LogicFlowNode | null
  edge?: LogicFlowEdge | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'update', nodeOrEdge: LogicFlowNode | LogicFlowEdge, updates: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const nodeLabel = ref(props.node?.text || '')
const showApproverSelector = ref(false)

// Form fields for permission config
const formFields = ref([
  { code: 'amount', name: '金额' },
  { code: 'department', name: '部门' },
  { code: 'reason', name: '原因' },
  { code: 'remark', name: '备注' }
])

const getNodeTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    start: '开始节点',
    end: '结束节点',
    approval: '审批节点',
    condition: '条件分支',
    parallel: '并行网关',
    notification: '通知节点',
    gateway: '网关节点'
  }
  return labels[type] || type
}

const getApproverLabel = (approver: any) => {
  const typeLabels = {
    user: '用户',
    role: '角色',
    department: '部门',
    leader: '上级',
    initiator: '发起人'
  }
  return `${typeLabels[approver.type]}: ${approver.name || approver.value}`
}

const getFieldPermission = (fieldCode: string) => {
  return props.node?.properties?.formPermission?.[fieldCode] || 'read_only'
}

const handleLabelChange = () => {
  if (!props.node) return
  emit('update', props.node, { text: nodeLabel.value })
}

const handlePropertyChange = (key: string, value: any) => {
  if (!props.node) return
  const properties = { ...props.node.properties, [key]: value }
  emit('update', props.node, { properties })
}

const handleFieldPermissionChange = (fieldCode: string, permission: string) => {
  if (!props.node) return
  const formPermission = {
    ...(props.node.properties?.formPermission || {}),
    [fieldCode]: permission
  }
  emit('update', props.node, {
    properties: { ...props.node.properties, formPermission }
  })
}

const handleEdgeLabelChange = (value: string) => {
  if (!props.edge) return
  emit('update', props.edge, { text: value })
}

const handleEdgePropertyChange = (key: string, value: any) => {
  if (!props.edge) return
  const properties = { ...props.edge.properties, [key]: value }
  emit('update', props.edge, { properties })
}

const handleRemoveApprover = (index: number) => {
  if (!props.node) return
  const approvers = [...(props.node.properties?.approvers || [])]
  approvers.splice(index, 1)
  emit('update', props.node, {
    properties: { ...props.node.properties, approvers }
  })
}

const handleApproverConfirm = (approvers: any[]) => {
  if (!props.node) return
  emit('update', props.node, {
    properties: { ...props.node.properties, approvers }
  })
}
</script>

<style scoped>
.property-content {
  padding: 0 16px;
}

.property-content :deep(.section-block) {
  margin-bottom: 16px;
}

.approver-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.approver-item {
  display: inline-block;
}

.form-permission-config :deep(.el-table) {
  font-size: 12px;
}

.help-text {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/workflows.ts` | Workflow type definitions |
| `frontend/src/api/workflows.ts` | Workflow API service |
| `frontend/src/components/workflows/WorkflowDesigner.vue` | Main workflow designer |
| `frontend/src/components/workflows/PropertyPanel.vue` | Property configuration panel |
| `frontend/src/components/workflows/ApproverSelector.vue` | Approver selector |
| `frontend/src/components/workflows/NodeConfigDialog.vue` | Node configuration dialog |
| `frontend/src/components/workflows/nodes/index.ts` | Custom LogicFlow node definitions |
| `frontend/src/views/workflows/WorkflowList.vue` | Workflow list page |
| `frontend/src/views/workflows/WorkflowForm.vue` | Workflow form page |
| `frontend/src/views/workflows/MyApprovals.vue` | My approvals page |
