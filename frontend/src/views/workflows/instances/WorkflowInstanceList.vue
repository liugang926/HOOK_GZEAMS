<template>
  <div class="workflow-instance-list">
    <el-card>
      <!-- Header -->
      <template #header>
        <div class="card-header">
          <h2>工作流实例</h2>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索实例..."
              clearable
              class="search-input"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-select v-model="viewMode" style="width: 120px;" @change="handleViewModeChange">
              <el-option label="全部" value="all" />
              <el-option label="我的" value="mine" />
            </el-select>
          </div>
        </div>
      </template>

      <!-- Quick Actions -->
      <el-row :gutter="16" class="quick-actions">
        <el-col :span="24">
          <el-button-group>
            <el-button type="primary" @click="openWorkflowCreate">
              <el-icon><Plus /></el-icon>
              新建工作流
            </el-button>
            <el-button @click="refreshData">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </el-button-group>
        </el-col>
      </el-row>

      <!-- Filters -->
      <div class="filter-section">
        <el-form :inline="true" class="filter-form">
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="选择状态" clearable @change="handleFilterChange">
              <el-option label="运行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="已拒绝" value="rejected" />
              <el-option label="已取消" value="cancelled" />
              <el-option label="已驳回" value="returned" />
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
          <el-form-item label="时间范围">
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              @change="handleDateChange"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- List -->
      <div v-loading="loading" class="instance-list">
        <div v-if="instances.length === 0" class="empty-state">
          <el-empty description="暂无工作流实例" />
        </div>

        <div v-else class="instance-grid">
          <div
            v-for="instance in instances"
            :key="instance.id"
            class="instance-card"
            :class="getPriorityClass(instance.priority)"
            @click="viewInstance(instance)"
          >
            <!-- Instance Header -->
            <div class="instance-header">
              <div class="instance-title">
                <h3>{{ instance.name || `工作流 #${instance.instanceNo || instance.id}` }}</h3>
                <el-tag :type="getStatusTagType(instance.status)" size="small">
                  {{ getStatusLabel(instance.status) }}
                </el-tag>
              </div>
              <div class="instance-date">
                {{ instance.createdAt ? formatDate(instance.createdAt) : '-' }}
              </div>
            </div>

            <!-- Instance Body -->
            <div class="instance-body">
              <div class="business-info">
                <div class="business-ref">
                  <span class="label">业务编号:</span>
                  <span class="value">{{ instance.businessNo || '-' }}</span>
                </div>
                <div class="business-id">
                  <span class="label">业务ID:</span>
                  <span class="value">{{ instance.businessId || '-' }}</span>
                </div>
              </div>
            </div>

            <!-- Instance Footer -->
            <div class="instance-footer">
              <div class="progress-info">
                <div class="progress-text">
                  进度: {{ getCurrentStep(instance) }}/{{ getTotalSteps(instance) }}
                </div>
                <el-progress
                  :percentage="getProgressPercentage(instance)"
                  :show-text="false"
                  :stroke-width="4"
                />
              </div>

              <div class="quick-actions">
                <el-button
                  v-if="instance.status === 'running'"
                  size="small"
                  type="primary"
                  @click.stop="viewInstance(instance)"
                >
                  查看详情
                </el-button>
                <el-button
                  v-if="instance.status === 'running'"
                  size="small"
                  type="danger"
                  @click.stop="cancelInstance(instance)"
                >
                  取消
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div class="pagination-section">
          <el-pagination
            v-model:current-page="pagination.current"
            v-model:page-size="pagination.size"
            :page-sizes="[12, 24, 48, 96]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/dateFormat'
import { cancelWorkflowInstance, getWorkflowInstances } from '@/api/workflow'
import {
  isRecord,
  normalizeListPayload,
  readNullableString,
  readNumber,
  readRecord,
  readString,
  type UnknownRecord
} from '../shared/listContracts'

type ViewMode = 'all' | 'mine'
type DateRangeValue = [Date, Date] | null

interface WorkflowInstanceRow {
  id: string
  name?: string | null
  instanceNo?: string | null
  createdAt?: string | null
  businessNo?: string | null
  businessId?: string | number | null
  priority?: string
  status: string
  currentStepPosition: number
  totalSteps: number
}

const router = useRouter()

const searchQuery = ref('')
const loading = ref(false)
const viewMode = ref<ViewMode>('all')
const instances = ref<WorkflowInstanceRow[]>([])

const filters = reactive<{
  status: string
  priority: string
  dateRange: DateRangeValue
}>({
  status: '',
  priority: '',
  dateRange: null
})

const pagination = reactive({
  current: 1,
  size: 12,
  total: 0
})

const isActionCancelled = (error: unknown) => error === 'cancel' || error === 'close'

const countGraphNodes = (definition?: UnknownRecord): number => {
  const graph = readRecord(definition, ['graph', 'graphData', 'graph_data'])
  const nodes = graph?.nodes

  if (Array.isArray(nodes)) {
    return nodes.length
  }

  if (isRecord(nodes)) {
    return Object.keys(nodes).length
  }

  return 0
}

const toWorkflowInstanceRow = (item: UnknownRecord): WorkflowInstanceRow => {
  const currentStep = readRecord(item, ['currentStep', 'current_step'])
  const definition = readRecord(item, ['definition'])
  const businessId = readNumber(item, ['businessId', 'business_id']) ?? readString(item, ['businessId', 'business_id']) ?? null

  return {
    id: readString(item, ['id']) ?? '',
    name: readNullableString(item, ['name', 'title']),
    instanceNo: readNullableString(item, ['instanceNo', 'instance_no']),
    createdAt: readNullableString(item, ['createdAt', 'created_at', 'startedAt', 'started_at']),
    businessNo: readNullableString(item, ['businessNo', 'business_no']),
    businessId,
    priority: readString(item, ['priority']),
    status: readString(item, ['status']) ?? 'running',
    currentStepPosition: readNumber(currentStep, ['position']) ?? 0,
    totalSteps: countGraphNodes(definition)
  }
}

const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    running: 'primary',
    completed: 'success',
    rejected: 'danger',
    cancelled: 'info',
    returned: 'warning'
  }
  return statusMap[status] || ''
}

const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    running: '运行中',
    completed: '已完成',
    rejected: '已拒绝',
    cancelled: '已取消',
    returned: '已驳回'
  }
  return statusMap[status] || status
}

const getPriorityClass = (priority?: string) => {
  const priorityMap: Record<string, string> = {
    urgent: 'priority-urgent',
    high: 'priority-high',
    normal: 'priority-normal',
    low: 'priority-low'
  }
  return priority ? priorityMap[priority] || '' : ''
}

const getCurrentStep = (instance: WorkflowInstanceRow) => instance.currentStepPosition

const getTotalSteps = (instance: WorkflowInstanceRow) => instance.totalSteps

const getProgressPercentage = (instance: WorkflowInstanceRow) => {
  const current = getCurrentStep(instance)
  const total = getTotalSteps(instance)
  return total > 0 ? Math.round((current / total) * 100) : 0
}

const fetchInstances = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.size,
      search: searchQuery.value,
      status: filters.status || undefined,
      priority: filters.priority || undefined,
      start_date: filters.dateRange?.[0]?.toISOString(),
      end_date: filters.dateRange?.[1]?.toISOString(),
      view_mode: viewMode.value,
      initiator_id: viewMode.value === 'mine' ? 'current_user' : undefined
    }

    const response = normalizeListPayload(await getWorkflowInstances(params), toWorkflowInstanceRow)
    instances.value = response.results
    pagination.total = response.count
  } catch (error) {
    console.error('获取工作流实例失败:', error)
    ElMessage.error('获取工作流实例失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  fetchInstances()
}

const handleViewModeChange = () => {
  pagination.current = 1
  fetchInstances()
}

const handleFilterChange = () => {
  pagination.current = 1
  fetchInstances()
}

const handleDateChange = () => {
  pagination.current = 1
  fetchInstances()
}

const openWorkflowCreate = () => router.push({ name: 'WorkflowCreate' })

const viewInstance = (instance: WorkflowInstanceRow) => {
  router.push({
    name: 'ApprovalDetail',
    params: { taskId: instance.id }
  })
}

const cancelInstance = async (instance: WorkflowInstanceRow) => {
  try {
    await ElMessageBox.confirm(
      '确定要取消此工作流实例吗？',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await cancelWorkflowInstance(instance.id)
    ElMessage.success('工作流已取消')
    fetchInstances()
  } catch (error) {
    if (!isActionCancelled(error)) {
      console.error('取消失败:', error)
      ElMessage.error('取消失败')
    }
  }
}

const refreshData = () => {
  fetchInstances()
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.current = 1
  fetchInstances()
}

const handleCurrentChange = (page: number) => {
  pagination.current = page
  fetchInstances()
}

onMounted(() => {
  fetchInstances()
})
</script>

<style scoped>
.workflow-instance-list {
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

.search-input {
  width: 200px;
}

.quick-actions {
  margin-bottom: 20px;
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

.instance-list {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
}

.instance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.instance-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.instance-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.instance-card.priority-urgent {
  border-left: 4px solid #f56c6c;
}

.instance-card.priority-high {
  border-left: 4px solid #e6a23c;
}

.instance-card.priority-normal {
  border-left: 4px solid #409eff;
}

.instance-card.priority-low {
  border-left: 4px solid #67c23a;
}

.instance-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.instance-title {
  flex: 1;
}

.instance-title h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.instance-date {
  font-size: 12px;
  color: #909399;
}

.instance-body {
  margin-bottom: 12px;
}

.business-info {
  display: grid;
  gap: 8px;
}

.business-ref,
.business-id {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.label {
  color: #909399;
  margin-right: 8px;
  min-width: 80px;
}

.value {
  color: #303133;
  font-weight: 500;
}

.instance-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e8e8e8;
}

.progress-info {
  flex: 1;
}

.progress-text {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.quick-actions {
  display: flex;
  gap: 8px;
}

.pagination-section {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
