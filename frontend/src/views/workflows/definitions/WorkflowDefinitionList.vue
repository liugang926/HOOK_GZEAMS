<template>
  <div class="workflow-definition-list">
    <el-card>
      <!-- Header with search and actions -->
      <template #header>
        <div class="card-header">
          <h2>工作流定义</h2>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索工作流..."
              clearable
              class="search-input"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button
              type="primary"
              @click="openCreatePage"
            >
              <el-icon><Plus /></el-icon>
              新建工作流
            </el-button>
            <el-button
              type="danger"
              :disabled="selectedRows.length === 0"
              @click="handleBatchDelete"
            >
              删除选中
            </el-button>
          </div>
        </div>
      </template>

      <!-- Statistics -->
      <el-row
        :gutter="16"
        class="statistics-row"
      >
        <el-col
          v-for="stat in statistics"
          :key="stat.key"
          :span="6"
        >
          <el-card
            class="stat-card"
            shadow="never"
          >
            <div class="stat-content">
              <div class="stat-value">
                {{ stat.value }}
              </div>
              <div class="stat-label">
                {{ stat.label }}
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Filters -->
      <div class="filter-section">
        <el-form
          :inline="true"
          class="filter-form"
        >
          <el-form-item label="状态">
            <el-select
              v-model="filters.status"
              placeholder="选择状态"
              clearable
              @change="handleFilterChange"
            >
              <el-option
                label="草稿"
                value="draft"
              />
              <el-option
                label="已发布"
                value="published"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="类型">
            <el-select
              v-model="filters.type"
              placeholder="选择类型"
              clearable
              @change="handleFilterChange"
            >
              <el-option
                label="审批流程"
                value="approval"
              />
              <el-option
                label="数据流转"
                value="data_flow"
              />
              <el-option
                label="通知流程"
                value="notification"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="fetchDefinitions"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Table -->
      <el-table
        v-loading="loading"
        :data="definitions"
        stripe
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column
          type="selection"
          width="55"
        />
        <el-table-column
          prop="code"
          label="编号"
          width="120"
        />
        <el-table-column
          prop="name"
          label="名称"
          min-width="150"
        />
        <el-table-column
          prop="description"
          label="描述"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="category"
          label="分类"
          width="100"
        />
        <el-table-column
          prop="type"
          label="类型"
          width="100"
        >
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.type)">
              {{ getTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="status"
          label="状态"
          width="100"
        >
          <template #default="{ row }">
            <el-tag :type="row.status === 'published' ? 'success' : 'warning'">
              {{ row.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="version"
          label="版本"
          width="80"
        />
        <el-table-column
          prop="createdAt"
          label="创建时间"
          width="160"
        >
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="200"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button-group>
              <el-button
                size="small"
                @click="viewDefinition(row)"
              >
                查看
              </el-button>
              <el-button
                size="small"
                @click="editDefinition(row)"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                :type="row.status === 'published' ? 'info' : 'primary'"
                @click="toggleStatus(row)"
              >
                {{ row.status === 'published' ? '停用' : '发布' }}
              </el-button>
            </el-button-group>
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Refresh } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/dateFormat'
import { getWorkflowDefinitions, publishWorkflow, unpublishWorkflow, deleteWorkflowDefinitions } from '@/api/workflow'
import {
  normalizeListPayload,
  readNullableString,
  readNumber,
  readString,
  type UnknownRecord
} from '../shared/listContracts'

interface WorkflowDefinitionRow {
  id: string
  code: string
  name: string
  description?: string | null
  category?: string | null
  type: string
  status: string
  version?: number | string | null
  createdAt?: string | null
}

interface WorkflowDefinitionStatistics {
  total?: number
  published?: number
  draft?: number
  active?: number
}

const router = useRouter()

const statistics = ref([
  { key: 'total', label: '总定义数', value: 0 },
  { key: 'published', label: '已发布', value: 0 },
  { key: 'draft', label: '草稿', value: 0 },
  { key: 'active', label: '使用中', value: 0 }
])

const searchQuery = ref('')
const loading = ref(false)
const definitions = ref<WorkflowDefinitionRow[]>([])
const selectedRows = ref<WorkflowDefinitionRow[]>([])

const filters = reactive({
  status: '',
  type: ''
})

const pagination = reactive({
  current: 1,
  size: 20,
  total: 0
})

const toWorkflowDefinitionRow = (item: UnknownRecord): WorkflowDefinitionRow => {
  const version = readNumber(item, ['version']) ?? readString(item, ['version']) ?? null

  return {
    id: readString(item, ['id']) ?? '',
    code: readString(item, ['code']) ?? '',
    name: readString(item, ['name']) ?? '',
    description: readNullableString(item, ['description']),
    category: readNullableString(item, ['category']),
    type: readString(item, ['type']) ?? 'approval',
    status: readString(item, ['status']) ?? 'draft',
    version,
    createdAt: readNullableString(item, ['createdAt', 'created_at'])
  }
}

const toWorkflowDefinitionStatistics = (
  stats?: UnknownRecord
): WorkflowDefinitionStatistics | undefined => {
  if (!stats) {
    return undefined
  }

  return {
    total: readNumber(stats, ['total']),
    published: readNumber(stats, ['published']),
    draft: readNumber(stats, ['draft']),
    active: readNumber(stats, ['active'])
  }
}

const isActionCancelled = (error: unknown) => error === 'cancel' || error === 'close'

const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    approval: '',
    data_flow: 'primary',
    notification: 'success'
  }
  return typeMap[type] || ''
}

const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    approval: '审批流程',
    data_flow: '数据流转',
    notification: '通知流程'
  }
  return typeMap[type] || type
}

const fetchDefinitions = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.size,
      search: searchQuery.value,
      status: filters.status || undefined,
      type: filters.type || undefined
    }

    const response = normalizeListPayload(await getWorkflowDefinitions(params), toWorkflowDefinitionRow)
    definitions.value = response.results
    pagination.total = response.count
    updateStatistics(toWorkflowDefinitionStatistics(response.statistics))
  } catch (error) {
    console.error('获取工作流定义失败:', error)
    ElMessage.error('获取工作流定义失败')
  } finally {
    loading.value = false
  }
}

const updateStatistics = (stats?: WorkflowDefinitionStatistics) => {
  statistics.value[0].value = stats?.total || 0
  statistics.value[1].value = stats?.published || 0
  statistics.value[2].value = stats?.draft || 0
  statistics.value[3].value = stats?.active || 0
}

const handleSearch = () => {
  pagination.current = 1
  fetchDefinitions()
}

const handleFilterChange = () => {
  pagination.current = 1
  fetchDefinitions()
}

const handleSelectionChange = (selection: WorkflowDefinitionRow[]) => {
  selectedRows.value = selection
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.current = 1
  fetchDefinitions()
}

const handleCurrentChange = (page: number) => {
  pagination.current = page
  fetchDefinitions()
}

const toggleStatus = async (definition: WorkflowDefinitionRow) => {
  try {
    if (definition.status === 'published') {
      await ElMessageBox.confirm('确定要停用此工作流吗？停用后将无法使用。', '确认停用', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      await unpublishWorkflow(definition.id)
      ElMessage.success('工作流已停用')
    } else {
      await ElMessageBox.confirm('确定要发布此工作流吗？发布后立即生效。', '确认发布', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'success'
      })
      await publishWorkflow(definition.id)
      ElMessage.success('工作流已发布')
    }
    fetchDefinitions()
  } catch (error) {
    if (!isActionCancelled(error)) {
      console.error('状态切换失败:', error)
      ElMessage.error('操作失败')
    }
  }
}

const openCreatePage = () => router.push({ name: 'WorkflowCreate' })

const openDefinitionEditor = (definitionId: string, newTab = false) => {
  const location = {
    name: 'WorkflowEdit',
    params: { id: definitionId }
  }

  if (newTab) {
    const route = router.resolve(location)
    window.open(route.href, '_blank', 'noopener')
    return
  }

  router.push(location)
}

const viewDefinition = (definition: WorkflowDefinitionRow) => {
  openDefinitionEditor(definition.id, true)
}

const editDefinition = (definition: WorkflowDefinitionRow) => {
  openDefinitionEditor(definition.id)
}

const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要删除的工作流')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个工作流吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await deleteWorkflowDefinitions(selectedRows.value.map((definition) => definition.id))
    ElMessage.success('删除成功')
    fetchDefinitions()
  } catch (error) {
    if (!isActionCancelled(error)) {
      console.error('批量删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchDefinitions()
})
</script>

<style scoped>
.workflow-definition-list {
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

.statistics-row {
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

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
