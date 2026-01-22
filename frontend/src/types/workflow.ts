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
  COMPLETED = 'completed',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled'
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
 * Workflow Definition Interface
 */
export interface WorkflowDefinition extends BaseModel {
  name: string
  code: string
  businessObject: string
  graphData: LogicFlowGraphData
  isActive: boolean
  version: number
  description?: string
}

/**
 * Workflow Instance Interface
 */
export interface WorkflowInstance extends BaseModel {
  definitionId: string
  definition?: WorkflowDefinition
  businessDataType: string
  businessDataId: string
  status: WorkflowStatus
  currentNodeId?: string
  currentNodeName?: string
  initiatorId: string
  initiator?: User
  completedAt?: string
  variables?: Record<string, any>
}

/**
 * Workflow Node Instance Interface
 */
export interface WorkflowNodeInstance {
  id: string
  workflowInstanceId: string
  nodeId: string
  nodeName: string
  nodeType: NodeType
  status: NodeStatus
  assigneeId?: string
  assignee?: User
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
