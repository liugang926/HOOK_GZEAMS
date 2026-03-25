<template>
  <div class="task-list">
    <el-card>
      <!-- Header -->
      <template #header>
        <div class="card-header">
          <h2>待办任务</h2>
          <div class="header-actions">
            <el-badge :value="unreadCount" class="badge">
              <el-button type="primary" @click="openWorkflowCreate">
                <el-icon><Plus /></el-icon>
                新建工作流
              </el-button>
            </el-badge>
          </div>
        </div>
      </template>

      <!-- Quick Stats -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6" v-for="stat in taskStats" :key="stat.key">
          <el-card class="stat-card" shadow="never">
            <div class="stat-content">
              <div class="stat-value">{{ stat.value }}</div>
              <div class="stat-label">{{ stat.label }}</div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Filters -->
      <div class="filter-section">
        <el-form :inline="true" class="filter-form">
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="选择状态" clearable @change="handleFilterChange">
              <el-option label="待处理" value="pending" />
              <el-option label="进行中" value="in_progress" />
              <el-option label="已批准" value="approved" />
              <el-option label="已拒绝" value="rejected" />
              <el-option label="已转交" value="transferred" />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select v-model="filters.priority" placeholder="选择优先级" clearable @change="handleFilterChange">
              <el-option label="紧急" value="urgent" />
              <el-option label="高" value="high" />
              <el-option label="中" value="normal" />
              <el-option label="低" value="low" />
            </el-select>
          </el-form-item>
          <el-form-item label="截止时间">
            <el-select v-model="filters.dueStatus" placeholder="选择" clearable @change="handleFilterChange">
              <el-option label="今天到期" value="today" />
              <el-option label="即将到期" value="upcoming" />
              <el-option label="已逾期" value="overdue" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchTasks">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Task Actions -->
      <div v-if="selectedTasks.length > 0" class="task-actions">
        <span class="selected-count">已选择 {{ selectedTasks.length }} 个任务</span>
        <el-button-group>
          <el-button type="success" size="small" @click="handleBulkApprove">
            批量批准
          </el-button>
          <el-button type="danger" size="small" @click="handleBulkReject">
            批量拒绝
          </el-button>
          <el-button type="info" size="small" @click="handleBulkTransfer">
            批量转交
          </el-button>
        </el-button-group>
      </div>

      <!-- Task List -->
      <el-table
        v-loading="loading"
        :data="tasks"
        stripe
        border
        @selection-change="handleSelectionChange"
        @row-click="handleRowClick"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="dueDate" label="截止时间" width="160">
          <template #default="{ row }">
            <div class="due-date-cell">
              <el-icon
                :class="getDueDateClass(row.dueDate, row.status)"
              >
                <Clock />
              </el-icon>
              <span :class="getDueDateClass(row.dueDate, row.status)">
                {{ formatTaskDateTime(row.dueDate) }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="workflowName" label="工作流" min-width="150" />
        <el-table-column prop="nodeName" label="任务" min-width="120" />
        <el-table-column prop="business_info" label="业务信息" min-width="180">
          <template #default="{ row }">
            <div class="business-info">
              <div v-if="row.businessNo" class="business-item">
                {{ row.businessNo }}
              </div>
              <div v-if="row.assetName" class="business-item">
                {{ row.assetName }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="assigneeName" label="指派给" width="100" />
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="getPriorityTagType(row.priority)">
              {{ getPriorityLabel(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatTaskDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button 
                v-if="row.status === 'pending'"
                size="small" 
                type="primary"
                @click.stop="handleApprove(row)"
              >
                批准
              </el-button>
              <el-button 
                v-if="row.status === 'pending'"
                size="small" 
                type="danger"
                @click.stop="handleReject(row)"
              >
                拒绝
              </el-button>
              <el-button
                v-if="row.status === 'pending'"
                size="small"
                type="warning"
                @click.stop="handleTransfer(row)"
              >
                转交
              </el-button>
              <el-button 
                size="small" 
                type="info"
                @click.stop="handleView(row)"
              >
                查看
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="pagination.current"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- Quick Action Dialog -->
    <el-dialog
      v-model="quickActionDialog.visible"
      :title="quickActionDialog.title"
      width="40%"
      :before-close="handleQuickActionClose"
    >
      <div v-if="quickActionDialog.type === 'approve'">
        <el-form ref="quickForm" :model="quickActionDialog.form" :rules="quickActionDialog.rules">
          <el-form-item label="审批意见" prop="comment">
            <el-input
              v-model="quickActionDialog.form.comment"
              type="textarea"
              :rows="4"
              placeholder="请输入审批意见（可选）"
            />
          </el-form-item>
        </el-form>
      </div>
      <div v-if="quickActionDialog.type === 'reject'">
        <el-form ref="quickForm" :model="quickActionDialog.form" :rules="quickActionDialog.rules">
          <el-form-item label="拒绝原因" prop="reason" required>
            <el-input
              v-model="quickActionDialog.form.reason"
              type="textarea"
              :rows="4"
              placeholder="请输入拒绝原因"
            />
          </el-form-item>
        </el-form>
      </div>
      <div v-if="quickActionDialog.type === 'transfer'">
        <el-form ref="quickForm" :model="quickActionDialog.form" :rules="quickActionDialog.rules">
          <el-form-item label="转交给" prop="assignee" required>
            <el-select
              v-model="quickActionDialog.form.assignee"
              placeholder="选择转交对象"
              filterable
            >
              <el-option
                v-for="user in potentialAssignees"
                :key="user.id"
                :label="user.name"
                :value="user.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="转交意见" prop="comment">
            <el-input
              v-model="quickActionDialog.form.comment"
              type="textarea"
              :rows="3"
              placeholder="转交意见（可选）"
            />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleQuickActionClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="executeQuickAction"
            :loading="quickActionDialog.loading"
          >
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Clock, Plus, Refresh } from '@element-plus/icons-vue'
import { formatDateTime as formatDateTimeValue } from '@/utils/dateFormat'
import {
  approveTask,
  getPotentialAssignees,
  getUserTasks,
  rejectTask,
  transferTask,
} from '@/api/workflow'
import type { WorkflowTaskListItem } from '@/types/workflow'
import {
  isRecord,
  normalizeListPayload,
  readNullableString,
  readNumber,
  readRecord,
  readString,
  type UnknownRecord
} from '../shared/listContracts'

const router = useRouter()
const quickForm = ref<InstanceType<typeof ElForm>>()

interface WorkflowTaskRow extends WorkflowTaskListItem {
  workflowName?: string
  businessNo?: string | null
  assetName?: string | null
  assigneeName?: string
}

interface TaskStatisticsPayload {
  pending?: number
  urgent?: number
  overdue?: number
  today?: number
}

interface PotentialAssignee {
  id: string
  name: string
}

type QuickActionType = '' | 'approve' | 'reject' | 'transfer'

interface QuickActionFormState {
  comment: string
  reason: string
  assignee: string
}

const createQuickActionForm = (): QuickActionFormState => ({
  comment: '',
  reason: '',
  assignee: ''
})

const taskStats = ref([
  { key: 'pending', label: '待处理', value: 0 },
  { key: 'urgent', label: '紧急', value: 0 },
  { key: 'overdue', label: '已逾期', value: 0 },
  { key: 'today', label: '今日到期', value: 0 }
])

const loading = ref(false)
const tasks = ref<WorkflowTaskRow[]>([])
const unreadCount = ref(0)
const selectedTasks = ref<WorkflowTaskRow[]>([])

const filters = reactive({
  status: '',
  priority: '',
  dueStatus: ''
})

const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

const quickActionDialog = reactive({
  visible: false,
  type: '' as QuickActionType,
  title: '',
  loading: false,
  currentTask: null as WorkflowTaskRow | null,
  form: createQuickActionForm(),
  rules: {
    comment: [{ required: false, message: '请输入意见' }],
    reason: [{ required: true, message: '请输入拒绝原因' }],
    assignee: [{ required: true, message: '请选择转交对象' }]
  }
})

const potentialAssignees = ref<PotentialAssignee[]>([])

const isActionCancelled = (error: unknown) => error === 'cancel' || error === 'close'

const getErrorMessage = (error: unknown, fallback: string) => {
  const response = isRecord(error) ? error.response : undefined
  const responseData = isRecord(response) ? response.data : undefined
  const errorPayload = isRecord(responseData) ? responseData.error : undefined

  if (typeof errorPayload === 'string' && errorPayload.trim().length > 0) {
    return errorPayload
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}

const toWorkflowTaskRow = (item: UnknownRecord): WorkflowTaskRow => ({
  id: readString(item, ['id']) ?? '',
  instanceNo: readString(item, ['instanceNo', 'instance_no']),
  instanceTitle: readNullableString(item, ['instanceTitle', 'instance_title']),
  businessObjectCode: readString(item, ['businessObjectCode', 'business_object_code']),
  businessId: readString(item, ['businessId', 'business_id']),
  nodeId: readString(item, ['nodeId', 'node_id']),
  nodeName: readString(item, ['nodeName', 'node_name']),
  approveType: readString(item, ['approveType', 'approve_type']),
  assigneeName: readString(item, ['assigneeName', 'assignee_name']),
  status: readString(item, ['status']) ?? 'pending',
  statusDisplay: readString(item, ['statusDisplay', 'status_display']),
  sequence: readNumber(item, ['sequence']),
  dueDate: readNullableString(item, ['dueDate', 'due_date']),
  isOverdue: Boolean(item.isOverdue ?? item.is_overdue ?? false),
  remainingHours: readNumber(item, ['remainingHours', 'remaining_hours']),
  durationHours: readNumber(item, ['durationHours', 'duration_hours']),
  priority: readString(item, ['priority']),
  createdAt: readNullableString(item, ['createdAt', 'created_at']) ?? undefined,
  workflowName: readString(item, ['workflowName', 'workflow_name']),
  businessNo: readNullableString(item, ['businessNo', 'business_no']),
  assetName: readNullableString(item, ['assetName', 'asset_name'])
})

const toTaskStatistics = (stats?: UnknownRecord): TaskStatisticsPayload | undefined => {
  if (!stats) {
    return undefined
  }

  return {
    pending: readNumber(stats, ['pending']),
    urgent: readNumber(stats, ['urgent']),
    overdue: readNumber(stats, ['overdue']),
    today: readNumber(stats, ['today'])
  }
}

const mapPotentialAssignee = (item: UnknownRecord): PotentialAssignee => ({
  id: readString(item, ['id']) ?? '',
  name: readString(item, ['name']) ?? readString(item, ['fullName', 'full_name']) ?? ''
})

const normalizePotentialAssignees = (payload: unknown): PotentialAssignee[] => {
  if (Array.isArray(payload)) {
    return payload.flatMap((item) => (isRecord(item) ? [mapPotentialAssignee(item)] : []))
  }

  const root = isRecord(payload) ? payload : {}
  const data = readRecord(root, ['data'])
  const source = (
    (Array.isArray(root.results) && root.results)
    || (Array.isArray(root.items) && root.items)
    || (Array.isArray(data?.results) && data.results)
    || (Array.isArray(data?.items) && data.items)
    || []
  )

  return source.flatMap((item) => (isRecord(item) ? [mapPotentialAssignee(item)] : []))
}

const getPriorityTagType = (priority?: string) => {
  const priorityMap: Record<string, string> = {
    urgent: 'danger',
    high: 'warning',
    normal: '',
    low: 'info'
  }
  return priority ? priorityMap[priority] || '' : ''
}

const getPriorityLabel = (priority?: string) => {
  const priorityMap: Record<string, string> = {
    urgent: '紧急',
    high: '高',
    normal: '中',
    low: '低'
  }
  return priorityMap[priority || ''] || priority || '-'
}

const getStatusTagType = (status?: string) => {
  const statusMap: Record<string, string> = {
    pending: 'warning',
    in_progress: '',
    approved: 'success',
    rejected: 'danger',
    transferred: 'info'
  }
  return status ? statusMap[status] || '' : ''
}

const getStatusLabel = (status?: string) => {
  const statusMap: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    approved: '已批准',
    rejected: '已拒绝',
    transferred: '已转交'
  }
  return statusMap[status || ''] || status || '-'
}

const getDueDateClass = (dueDate?: string | null, status?: string) => {
  if (!dueDate || status !== 'pending') {
    return ''
  }

  const now = new Date()
  const due = new Date(dueDate)
  const daysDiff = Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

  if (daysDiff < 0) return 'overdue'
  if (daysDiff <= 1) return 'urgent'
  if (daysDiff <= 3) return 'warning'
  return ''
}

const formatTaskDateTime = (dateString?: string | null) => {
  return dateString ? formatDateTimeValue(dateString) : '-'
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.size,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
      due_status: filters.dueStatus || undefined
    }

    const response = normalizeListPayload(await getUserTasks(params), toWorkflowTaskRow)
    tasks.value = response.results
    pagination.total = response.count
    unreadCount.value = response.unreadCount || 0
    updateTaskStatistics(toTaskStatistics(response.statistics))
  } catch (error) {
    console.error('获取任务失败:', error)
    ElMessage.error('获取任务失败')
  } finally {
    loading.value = false
  }
}

const updateTaskStatistics = (stats?: TaskStatisticsPayload) => {
  taskStats.value[0].value = stats?.pending || 0
  taskStats.value[1].value = stats?.urgent || 0
  taskStats.value[2].value = stats?.overdue || 0
  taskStats.value[3].value = stats?.today || 0
}

const handleFilterChange = () => {
  pagination.current = 1
  fetchTasks()
}

const fetchPotentialAssignees = async (currentTask: WorkflowTaskRow) => {
  try {
    const response = await getPotentialAssignees({
      task_id: currentTask.id,
      exclude_current: true
    })
    potentialAssignees.value = normalizePotentialAssignees(response)
  } catch (error) {
    console.error('获取潜在转交对象失败:', error)
  }
}

const handleSelectionChange = (selection: WorkflowTaskRow[]) => {
  selectedTasks.value = selection
}

const handleRowClick = (row: WorkflowTaskRow) => {
  handleView(row)
}

const openWorkflowCreate = () => router.push({ name: 'WorkflowCreate' })

const handleView = (task: WorkflowTaskRow) => {
  router.push({
    name: 'TaskDetail',
    params: { id: task.id }
  })
}

const resetQuickActionForm = (overrides: Partial<QuickActionFormState> = {}) => {
  quickActionDialog.form = {
    ...createQuickActionForm(),
    ...overrides
  }
}

const handleApprove = (task: WorkflowTaskRow) => {
  quickActionDialog.currentTask = task
  quickActionDialog.type = 'approve'
  quickActionDialog.title = '批准任务'
  resetQuickActionForm()
  quickActionDialog.visible = true
}

const handleReject = (task: WorkflowTaskRow) => {
  quickActionDialog.currentTask = task
  quickActionDialog.type = 'reject'
  quickActionDialog.title = '拒绝任务'
  resetQuickActionForm()
  quickActionDialog.visible = true
}

const handleTransfer = async (task: WorkflowTaskRow) => {
  quickActionDialog.currentTask = task
  quickActionDialog.type = 'transfer'
  quickActionDialog.title = '转交任务'
  resetQuickActionForm()
  await fetchPotentialAssignees(task)
  quickActionDialog.visible = true
}

const executeQuickAction = async () => {
  try {
    if (quickForm.value) {
      await quickForm.value.validate()
    }

    quickActionDialog.loading = true
    const task = quickActionDialog.currentTask
    if (!task) {
      quickActionDialog.loading = false
      return
    }

    switch (quickActionDialog.type) {
      case 'approve':
        await approveTask(task.id, {
          comment: quickActionDialog.form.comment
        })
        ElMessage.success('任务已批准')
        break
      
      case 'reject':
        await rejectTask(task.id, {
          comment: quickActionDialog.form.reason
        })
        ElMessage.success('任务已拒绝')
        break
      
      case 'transfer':
        await transferTask(task.id, {
          to_user_id: quickActionDialog.form.assignee,
          comment: quickActionDialog.form.comment || undefined
        })
        ElMessage.success('任务已转交')
        break
    }

    handleQuickActionClose()
    fetchTasks()
  } catch (error) {
    quickActionDialog.loading = false
    console.error('操作失败:', error)
    ElMessage.error(getErrorMessage(error, '操作失败'))
  }
}

const handleQuickActionClose = () => {
  quickActionDialog.visible = false
  quickActionDialog.loading = false
  quickActionDialog.type = ''
  quickActionDialog.title = ''
  quickActionDialog.currentTask = null
  resetQuickActionForm()
  potentialAssignees.value = []
}

const handleBulkApprove = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要批量批准选中的 ${selectedTasks.value.length} 个任务吗？`,
      '批量批准',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await Promise.all(
      selectedTasks.value.map(task => 
        approveTask(task.id, { comment: '批量批准' })
      )
    )

    ElMessage.success('批量批准成功')
    fetchTasks()
  } catch (error) {
    if (!isActionCancelled(error)) {
      ElMessage.error('批量批准失败')
    }
  }
}

const handleBulkReject = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要批量拒绝选中的 ${selectedTasks.value.length} 个任务吗？`,
      '批量拒绝',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await Promise.all(
      selectedTasks.value.map(task => 
        rejectTask(task.id, { comment: '批量拒绝' })
      )
    )

    ElMessage.success('批量拒绝成功')
    fetchTasks()
  } catch (error) {
    if (!isActionCancelled(error)) {
      ElMessage.error('批量拒绝失败')
    }
  }
}

const handleBulkTransfer = async () => {
  if (selectedTasks.value.length > 10) {
    ElMessage.warning('批量转交最多支持10个任务')
    return
  }

  ElMessage.info('批量转交功能开发中')
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.current = 1
  fetchTasks()
}

const handleCurrentChange = (page: number) => {
  pagination.current = page
  fetchTasks()
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.task-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.badge {
  margin-right: 12px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border: 1px solid #e8e8e8;
}

.stat-content {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.filter-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
}

.filter-form {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.task-actions {
  margin-bottom: 16px;
  padding: 12px;
  background: #ecf5ff;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selected-count {
  color: #409eff;
  font-weight: 500;
}

.due-date-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}

.due-date-cell.overdue {
  color: #f56c6c;
}

.due-date-cell.urgent {
  color: #e6a23c;
}

.due-date-cell.warning {
  color: #409eff;
}

.business-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.business-item {
  font-size: 12px;
  color: #606266;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
