/**
 * Workflow Store
 *
 * Pinia store for workflow approval management.
 * Handles pending tasks, task detail with field permissions,
 * and approval/reject/return actions.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { workflowNodeApi, taskApi } from '@/api/workflow'
import type {
  MyTasksResponse,
  NodeFormPermissions,
  TaskDetailWithPermissions,
  WorkflowTaskListItem,
} from '@/types/workflow'

export type WorkflowTask = WorkflowTaskListItem
export type TaskWithPermissions = TaskDetailWithPermissions

const normalizeTaskListItem = (task: Record<string, any>): WorkflowTask => ({
  id: task.id,
  instanceNo: task.instanceNo ?? task.instance_no,
  instanceTitle: task.instanceTitle ?? task.instance_title ?? null,
  businessObjectCode: task.businessObjectCode ?? task.business_object_code,
  businessId: task.businessId ?? task.business_id,
  nodeId: task.nodeId ?? task.node_id,
  nodeName: task.nodeName ?? task.node_name,
  nodeType: task.nodeType ?? task.node_type,
  approveType: task.approveType ?? task.approve_type,
  assignee: task.assignee ?? null,
  assigneeName: task.assigneeName ?? task.assignee_name,
  status: task.status,
  statusDisplay: task.statusDisplay ?? task.status_display,
  sequence: task.sequence,
  dueDate: task.dueDate ?? task.due_date ?? null,
  isOverdue: task.isOverdue ?? task.is_overdue,
  remainingHours: task.remainingHours ?? task.remaining_hours,
  durationHours: task.durationHours ?? task.duration_hours,
  priority: task.priority,
  createdAt: task.createdAt ?? task.created_at,
})

const normalizeTaskDetail = (detail: Record<string, any>): TaskWithPermissions => {
  const instance = detail.instance ?? detail.task?.instance ?? {}
  const definition = instance.definition ?? detail.definition ?? undefined

  return {
    ...normalizeTaskListItem(detail),
    instance: {
      ...instance,
      instanceNo: instance.instanceNo ?? instance.instance_no,
      definition: definition
        ? {
            id: definition.id,
            code: definition.code,
            name: definition.name,
            version: definition.version,
          }
        : undefined,
      definitionCode:
        instance.definitionCode ?? instance.definition_code ?? definition?.code,
      businessObjectCode:
        instance.businessObjectCode ?? instance.business_object_code,
      businessId: instance.businessId ?? instance.business_id,
      businessNo: instance.businessNo ?? instance.business_no ?? null,
      currentNodeId: instance.currentNodeId ?? instance.current_node_id ?? null,
      currentNodeName: instance.currentNodeName ?? instance.current_node_name ?? null,
      startedAt: instance.startedAt ?? instance.started_at ?? null,
      completedAt: instance.completedAt ?? instance.completed_at ?? null,
      terminatedAt: instance.terminatedAt ?? instance.terminated_at ?? null,
      totalTasks: instance.totalTasks ?? instance.total_tasks,
      completedTasks: instance.completedTasks ?? instance.completed_tasks,
      graphSnapshot: instance.graphSnapshot ?? instance.graph_snapshot,
    } as TaskWithPermissions['instance'],
    assignee: detail.assignee ?? null,
    completedAt: detail.completedAt ?? detail.completed_at ?? null,
    completedBy: detail.completedBy ?? detail.completed_by ?? null,
    isPending: detail.isPending ?? detail.is_pending,
    isCompleted: detail.isCompleted ?? detail.is_completed,
    nodeProperties: detail.nodeProperties ?? detail.node_properties ?? {},
    delegatedTo: detail.delegatedTo ?? detail.delegated_to ?? null,
    delegatedFrom: detail.delegatedFrom ?? detail.delegated_from ?? null,
    delegatedAt: detail.delegatedAt ?? detail.delegated_at ?? null,
    delegationReason: detail.delegationReason ?? detail.delegation_reason ?? null,
    approvalsSummary: detail.approvalsSummary ?? detail.approvals_summary,
    updatedAt: detail.updatedAt ?? detail.updated_at,
    formPermissions: detail.formPermissions ?? detail.form_permissions ?? {},
    businessData: detail.businessData ?? detail.business_data ?? {},
    timeline: (detail.timeline ?? []).map((item: Record<string, any>) => ({
      nodeName: item.nodeName ?? item.node_name,
      action: item.action,
      operator: item.operator,
      comment: item.comment,
      createdAt: item.createdAt ?? item.created_at,
    })),
  }
}

export const useWorkflowStore = defineStore('workflow', () => {
  // === State ===
  const pendingTasks = ref<WorkflowTask[]>([])
  const overdueTasks = ref<WorkflowTask[]>([])
  const completedTasks = ref<WorkflowTask[]>([])
  const pendingCount = ref(0)
  const overdueCount = ref(0)
  const completedTodayCount = ref(0)
  const currentTask = ref<TaskWithPermissions | null>(null)
  const loading = ref(false)
  const actionLoading = ref(false)

  // === Computed ===
  const hasPendingTasks = computed(() => pendingCount.value > 0)
  const currentFormPermissions = computed<NodeFormPermissions>(
    () => currentTask.value?.formPermissions ?? {}
  )
  const currentBusinessData = computed<Record<string, any>>(
    () => currentTask.value?.businessData ?? {}
  )

  // === Actions ===

  /**
   * Fetch all tasks for current user (pending, overdue, completed today).
   */
  async function fetchMyTasks() {
    loading.value = true
    try {
      const data = (await workflowNodeApi.getMyTasks()) as MyTasksResponse & Record<string, any>
      pendingTasks.value = (data.pending || data.results || []).map(normalizeTaskListItem)
      overdueTasks.value = (data.overdue || []).map(normalizeTaskListItem)
      completedTasks.value = (data.completedToday || data.completed_today || []).map(
        normalizeTaskListItem
      )

      const summary = data.summary as Record<string, any> | undefined
      if (summary) {
        pendingCount.value = summary.pendingCount ?? summary.pending_count ?? pendingTasks.value.length
        overdueCount.value = summary.overdueCount ?? summary.overdue_count ?? overdueTasks.value.length
        completedTodayCount.value =
          summary.completedTodayCount ??
          summary.completed_today_count ??
          completedTasks.value.length
      } else {
        pendingCount.value = pendingTasks.value.length
        overdueCount.value = overdueTasks.value.length
        completedTodayCount.value = completedTasks.value.length
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single task detail with form permissions + business data.
   */
  async function fetchTaskDetail(taskId: string) {
    loading.value = true
    try {
      const res = await taskApi.getTaskDetail(taskId)
      const detail = res as Record<string, any>
      currentTask.value = normalizeTaskDetail(detail)
    } finally {
      loading.value = false
    }
  }

  /**
   * Approve a task.
   */
  async function approveCurrentTask(taskId: string, comment?: string) {
    actionLoading.value = true
    try {
      await taskApi.approveTask(taskId, { comment: comment || '' })
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * Reject a task.
   */
  async function rejectCurrentTask(taskId: string, comment: string) {
    actionLoading.value = true
    try {
      await taskApi.rejectTask(taskId, { comment })
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * Return a task to a previous step.
   */
  async function returnCurrentTask(taskId: string, comment: string) {
    actionLoading.value = true
    try {
      await taskApi.returnTask(taskId, { comment })
    } finally {
      actionLoading.value = false
    }
  }

  /**
   * Refresh only the pending count (lightweight poll).
   */
  async function refreshPendingCount() {
    try {
      const data = (await workflowNodeApi.getMyTasks({ pageSize: 1 })) as any
      pendingCount.value = data.summary?.pendingCount ?? data.summary?.pending_count ?? data.count ?? 0
    } catch {
      // Silently fail - count refresh is non-critical
    }
  }

  /**
   * Clear current task (when leaving detail page).
   */
  function clearCurrentTask() {
    currentTask.value = null
  }

  return {
    // State
    pendingTasks,
    overdueTasks,
    completedTasks,
    pendingCount,
    overdueCount,
    completedTodayCount,
    currentTask,
    loading,
    actionLoading,
    // Computed
    hasPendingTasks,
    currentFormPermissions,
    currentBusinessData,
    // Actions
    fetchMyTasks,
    fetchTaskDetail,
    approveCurrentTask,
    rejectCurrentTask,
    returnCurrentTask,
    refreshPendingCount,
    clearCurrentTask,
  }
})
