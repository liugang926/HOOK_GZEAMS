<template>
  <div class="system-config-list">
    <div class="page-header">
      <h3>System Configuration</h3>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        Add Config
      </el-button>
    </div>

    <!-- Category Tabs -->
    <el-tabs
      v-model="activeCategory"
      @tab-change="handleCategoryChange"
    >
      <el-tab-pane
        label="All"
        name=""
      />
      <el-tab-pane
        label="General"
        name="general"
      />
      <el-tab-pane
        label="QR Code"
        name="qrcode"
      />
      <el-tab-pane
        label="Notification"
        name="notification"
      />
      <el-tab-pane
        label="Asset"
        name="asset"
      />
      <el-tab-pane
        label="Inventory"
        name="inventory"
      />
    </el-tabs>

    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item label="Search">
        <el-input
          v-model="filterForm.search"
          placeholder="Search by key or name"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="Type">
        <el-select
          v-model="filterForm.value_type"
          clearable
          placeholder="All"
          @change="handleSearch"
        >
          <el-option
            label="String"
            value="string"
          />
          <el-option
            label="Integer"
            value="integer"
          />
          <el-option
            label="Float"
            value="float"
          />
          <el-option
            label="Boolean"
            value="boolean"
          />
          <el-option
            label="JSON"
            value="json"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSearch"
        >
          Search
        </el-button>
        <el-button @click="handleFilterReset">
          Reset
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Config Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column
        prop="config_key"
        label="Key"
        width="200"
      />
      <el-table-column
        prop="name"
        label="Name"
        width="180"
      />
      <el-table-column
        prop="config_value"
        label="Value"
        min-width="200"
      >
        <template #default="{ row }">
          <span
            v-if="row.is_encrypted"
            type="warning"
          >******</span>
          <span v-else-if="row.value_type === 'boolean'">
            <el-tag
              :type="row.config_value === 'true' ? 'success' : 'info'"
              size="small"
            >
              {{ row.config_value === 'true' ? 'Enabled' : 'Disabled' }}
            </el-tag>
          </span>
          <span
            v-else-if="row.value_type === 'json'"
            class="json-value"
          >
            {{ formatJsonDisplay(row.config_value) }}
          </span>
          <span v-else>{{ row.config_value }}</span>
        </template>
      </el-table-column>
      <el-table-column
        label="Type"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            size="small"
            :type="getValueTypeColor(row.value_type)"
          >
            {{ row.value_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="category"
        label="Category"
        width="120"
      />
      <el-table-column
        label="System"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.is_system"
            type="warning"
            size="small"
          >
            System
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        label="Description"
        min-width="150"
        show-overflow-tooltip
      />
      <el-table-column
        label="Actions"
        width="180"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            Edit
          </el-button>
          <el-popconfirm
            v-if="!row.is_system"
            title="Are you sure to delete this config?"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
              >
                Delete
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-footer">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>

    <!-- Config Form Dialog -->
    <SystemConfigForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { SystemConfig } from '@/api/system'
import { systemConfigApi } from '@/api/system'
import SystemConfigForm from './components/SystemConfigForm.vue'

const loading = ref(false)
const tableData = ref<SystemConfig[]>([])
const dialogVisible = ref(false)
const activeCategory = ref('')
const currentRow = ref<SystemConfig | null>(null)

const filterForm = reactive({
  search: '',
  value_type: undefined as unknown as string
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getValueTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    string: '',
    integer: 'success',
    float: 'warning',
    boolean: 'info',
    json: 'danger'
  }
  return colorMap[type] || ''
}

const formatJsonDisplay = (value: string) => {
  try {
    const parsed = JSON.parse(value)
    if (typeof parsed === 'object') {
      return JSON.stringify(parsed).substring(0, 50) + '...'
    }
    return value
  } catch {
    return value.substring(0, 50) + (value.length > 50 ? '...' : '')
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (activeCategory.value) {
      params.category = activeCategory.value
    }
    if (filterForm.search) {
      params.search = filterForm.search
    }
    if (filterForm.value_type) {
      params.value_type = filterForm.value_type
    }

    const res = await systemConfigApi.list(params) as any
    tableData.value = res.results || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error('Failed to load system configs')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleFilterReset = () => {
  filterForm.search = ''
  filterForm.value_type = undefined as unknown as string
  handleSearch()
}

const handleCategoryChange = () => {
  pagination.page = 1
  fetchData()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: SystemConfig) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: SystemConfig) => {
  try {
    await systemConfigApi.delete(row.id)
    ElMessage.success('Deleted successfully')
    await fetchData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('Failed to delete')
    }
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.system-config-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  font-size: 18px;
}

.filter-form {
  margin-bottom: 20px;
}

.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.json-value {
  color: #909399;
  font-family: monospace;
  font-size: 12px;
}
</style>
