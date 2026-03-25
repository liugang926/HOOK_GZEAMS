/**
 * Workflow Module Type Definitions
 *
 * Types for BPM workflow engine including definitions, instances, and nodes.
 * Reference: docs/plans/phase3_1_logicflow/frontend_v2.md
 */

import type { BaseModel, User } from './common'

/**
 * Workflow Status Enum
 */
export enum WorkflowStatus {
  DRAFT = 'draft',
  RUNNING = 'running',
  PENDING_APPROVAL = 'pending_approval',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled',
  TERMINATED = 'terminated',
}

/**
 * Node Type Enum
 */
export enum NodeType {
  START = 'start',
  END = 'end',
  APPROVAL = 'approval',
  CONDITION = 'condition',
  PARALLEL = 'parallel',
  NOTIFY = 'notify'
}

/**
 * LogicFlow Graph Data Interface
 */
export interface LogicFlowGraphData {
  nodes: LogicFlowNode[]
  edges: LogicFlowEdge[]
}

/**
 * LogicFlow Node Interface
 */
export interface LogicFlowNode {
  id: string
  type: string
  x: number
  y: number
  text?: string
  properties?: Record<string, any>
}

/**
 * LogicFlow Edge Interface
 */
export interface LogicFlowEdge {
  id: string
  sourceNodeId: string
  targetNodeId: string
  type?: string
  text?: string
  properties?: Record<string, any>
}

/**
 * Workflow Definition Summary Interface
 *
 * Used when instances/tasks embed a lightweight definition object.
 */
export interface WorkflowDefinitionSummary {
  id: string
  code: string
  name: string
  version?: number
}

/**
 * Workflow Definition Interface
 */
export interface WorkflowDefinition extends BaseModel {
  name: string
  code: string
  businessObjectCode: string
  graphData: LogicFlowGraphData
  status?: 'draft' | 'published' | 'archived' | 'deprecated'
  isActive: boolean
  version: number
  description?: string
  publishedAt?: string | null
  formPermissions?: FormPermissionsMap
}

/**
 * Workflow Instance Interface
 */
export interface WorkflowInstance extends BaseModel {
  instanceNo: string
  definition?: WorkflowDefinitionSummary
  definitionCode?: string
  businessObjectCode: string
  businessId: string
  businessNo?: string | null
  status: WorkflowStatus
  currentNodeId?: string | null
  currentNodeName?: string | null
  initiator?: User
  title?: string | null
  description?: string | null
  priority?: 'low' | 'normal' | 'high' | 'urgent'
  variables?: Record<string, any>
  totalTasks?: number
  completedTasks?: number
  startedAt?: string | null
  completedAt?: string | null
  terminatedAt?: string | null
  graphSnapshot?: LogicFlowGraphData | Record<string, any>
}

/**
 * Workflow Task Status Enum
 */
export enum WorkflowTaskStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  RETURNED = 'returned',
  CANCELLED = 'cancelled',
  TERMINATED = 'terminated',
  DELEGATED = 'delegated',
  WITHDRAWN = 'withdrawn',
}

/**
 * Workflow Task List Item Interface
 *
 * Matches GET /api/workflows/tasks/my_tasks/ and list responses.
 */
export interface WorkflowTaskListItem {
  id: string
  instanceNo?: string
  instanceTitle?: string | null
  businessObjectCode?: string
  businessId?: string
  nodeId?: string
  nodeName?: string
  nodeType?: NodeType | string
  approveType?: 'or' | 'and' | 'sequence' | string
  assignee?: User | string | null
  assigneeName?: string
  status: WorkflowTaskStatus | string
  statusDisplay?: string
  sequence?: number
  dueDate?: string | null
  isOverdue?: boolean
  remainingHours?: number | null
  durationHours?: number | null
  priority?: string
  createdAt?: string
}

/**
 * Workflow Node Instance Interface
 *
 * Kept as a compatibility alias for existing imports.
 */
export interface WorkflowNodeInstance extends WorkflowTaskListItem {
  instance?: WorkflowInstance
  assigneeId?: string
  approvedAt?: string
  approverComment?: string
}

/**
 * Node Status Enum
 */
export enum NodeStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  SKIPPED = 'skipped'
}

/**
 * Approval Action Interface
 */
export interface ApprovalAction {
  action: 'approve' | 'reject'
  comment?: string
}

/**
 * Workflow Variable Interface
 */
export interface WorkflowVariable {
  key: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'date' | 'user' | 'dept'
  defaultValue?: any
  required?: boolean
}

/**
 * Node Approval Configuration
 */
export interface NodeApprovalConfig {
  nodeId: string
  nodeName: string
  approvalType: 'or' | 'and' | 'sequence'
  approvers: ApproverConfig[]
  autoApprove?: boolean
  timeoutHours?: number
}

/**
 * Approver Configuration
 */
export interface ApproverConfig {
  type: 'user' | 'dept' | 'role' | 'superior'
  userId?: string
  deptId?: string
  roleId?: string
  level?: number
}

/**
 * Field Permission Level
 *
 * Controls what an approver can do with each field on a workflow task.
 */
export type FieldPermissionLevel = 'editable' | 'read_only' | 'hidden'

/**
 * Per-node field permissions mapping.
 * Keys are field codes, values are permission levels.
 */
export type NodeFormPermissions = Record<string, FieldPermissionLevel>

/**
 * Full form permissions map stored on WorkflowDefinition.
 * Keys are node IDs, values are per-field permission mappings.
 */
export type FormPermissionsMap = Record<string, NodeFormPermissions>

/**
 * Task approval summary object from task detail responses.
 */
export interface WorkflowTaskApprovalSummary {
  total?: number
  approved?: number
  pending?: number
  rejected?: number
  latest?: Record<string, any> | null
  [key: string]: unknown
}

/**
 * Detailed workflow task response.
 */
export interface WorkflowTaskDetail extends WorkflowTaskListItem {
  instance: WorkflowInstance
  assignee?: User | null
  completedAt?: string | null
  completedBy?: User | string | null
  isPending?: boolean
  isCompleted?: boolean
  nodeProperties?: Record<string, any>
  delegatedTo?: User | string | null
  delegatedFrom?: User | string | null
  delegatedAt?: string | null
  delegationReason?: string | null
  approvalsSummary?: WorkflowTaskApprovalSummary
  updatedAt?: string
}

/**
 * Task timeline entry used by the approval detail page.
 */
export interface WorkflowTaskTimelineEntry {
  nodeName: string
  action: string
  operator?: string
  comment?: string
  createdAt: string
}

/**
 * Task Detail with resolved field permissions.
 *
 * Returned by GET /api/workflows/tasks/{id}/
 * Extends standard task fields with form_permissions and filtered business data.
 */
export interface TaskDetailWithPermissions extends WorkflowTaskDetail {
  formPermissions: NodeFormPermissions
  businessData: Record<string, any>
  timeline?: WorkflowTaskTimelineEntry[]
}

/**
 * My tasks grouped response.
 */
export interface MyTasksResponse {
  pending: WorkflowTaskListItem[]
  overdue: WorkflowTaskListItem[]
  completedToday: WorkflowTaskListItem[]
  summary: {
    pendingCount: number
    overdueCount: number
    completedTodayCount: number
  }
  count?: number
  next?: string | null
  previous?: string | null
  results?: WorkflowTaskListItem[]
}

/**
 * Workflow instance start payload.
 */
export interface WorkflowInstanceStartPayload {
  definitionId: string
  businessObjectCode: string
  businessId: string
  businessNo?: string
  variables?: Record<string, any>
  title?: string
  description?: string
  priority?: 'low' | 'normal' | 'high' | 'urgent'
}

/**
 * Approval Status for business documents (WorkflowStatusMixin)
 */
export enum ApprovalStatus {
  DRAFT = 'draft',
  PENDING = 'pending_approval',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled',
}
