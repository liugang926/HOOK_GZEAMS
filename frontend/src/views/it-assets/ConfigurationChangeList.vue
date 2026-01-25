<template>
  <div class="configuration-change-list">
    <div class="page-header">
      <h3>Configuration Changes</h3>
      <el-button type="primary" @click="handleCreate">Add Change</el-button>
    </div>

    <!-- Filters -->
    <el-form :model="filterForm" inline class="filter-form">
      <el-form-item label="Search">
        <el-input
          v-model="filterForm.search"
          placeholder="Asset code, field name..."
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="Field">
        <el-select v-model="filterForm.field_name" clearable placeholder="All Fields" @change="handleSearch">
          <el-option label="CPU Model" value="cpu_model" />
          <el-option label="RAM" value="ram_capacity" />
          <el-option label="Disk" value="disk_capacity" />
          <el-option label="OS" value="os_name" />
          <el-option label="IP Address" value="ip_address" />
        </el-select>
      </el-form-item>
      <el-form-item label="Date Range">
        <el-date-picker
          v-model="filterForm.date_range"
          type="daterange"
          placeholder="Select range"
          clearable
          @change="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">Search</el-button>
        <el-button @click="handleFilterReset">Reset</el-button>
      </el-form-item>
    </el-form>

    <!-- Changes Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column prop="asset_code" label="Asset" width="140" />
      <el-table-column prop="field_name" label="Field" width="180" />
      <el-table-column label="Change" min-width="300">
        <template #default="{ row }">
          <div class="change-display">
            <span class="old-value">{{ row.old_value || '(empty)' }}</span>
            <el-icon class="arrow-icon"><Right /></el-icon>
            <span class="new-value">{{ row.new_value || '(empty)' }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="change_reason" label="Reason" min-width="200" show-overflow-tooltip />
      <el-table-column prop="change_date" label="Date" width="120" />
      <el-table-column prop="changed_by_username" label="Changed By" width="120" />
      <el-table-column label="Actions" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleView(row)">View</el-button>
          <el-button link type="primary" @click="handleEdit(row)">Edit</el-button>
          <el-popconfirm
            title="Are you sure to delete this record?"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger">Delete</el-button>
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

    <!-- Configuration Change Form Dialog -->
    <ConfigurationChangeForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />

    <!-- Detail Drawer -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="Configuration Change Details"
      size="600px"
    >
      <div v-if="currentRow" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Asset">{{ currentRow.asset_code }} - {{ currentRow.asset_name }}</el-descriptions-item>
          <el-descriptions-item label="Field">{{ currentRow.field_name }}</el-descriptions-item>
          <el-descriptions-item label="Date">{{ currentRow.change_date }}</el-descriptions-item>
          <el-descriptions-item label="Changed By">{{ currentRow.changed_by_username || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">Change Details</div>
        <div class="change-comparison">
          <div class="change-side old">
            <div class="change-label">Old Value</div>
            <div class="change-value">{{ currentRow.old_value || '(empty)' }}</div>
          </div>
          <el-icon class="change-arrow"><Right /></el-icon>
          <div class="change-side new">
            <div class="change-label">New Value</div>
            <div class="change-value">{{ currentRow.new_value || '(empty)' }}</div>
          </div>
        </div>

        <div v-if="currentRow.change_reason" class="section-title">Reason</div>
        <div v-if="currentRow.change_reason" class="reason-text">{{ currentRow.change_reason }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Right } from '@element-plus/icons-vue'
import type { ConfigurationChange } from '@/api/itAssets'
import { configurationChangeApi } from '@/api/itAssets'
import ConfigurationChangeForm from './components/ConfigurationChangeForm.vue'

const loading = ref(false)
const tableData = ref<ConfigurationChange[]>([])
const dialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentRow = ref<ConfigurationChange | null>(null)

const filterForm = reactive({
  search: '',
  field_name: undefined as unknown as string,
  date_range: null as any
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filterForm.search) {
      params.search = filterForm.search
    }
    if (filterForm.field_name) {
      params.field_name = filterForm.field_name
    }
    if (filterForm.date_range && filterForm.date_range.length === 2) {
      params.change_date_from = filterForm.date_range[0]
      params.change_date_to = filterForm.date_range[1]
    }

    const res = await configurationChangeApi.list(params) as any
    tableData.value = res.results || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error('Failed to load configuration changes')
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
  filterForm.field_name = undefined as unknown as string
  filterForm.date_range = null
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleView = (row: ConfigurationChange) => {
  currentRow.value = row
  detailDrawerVisible.value = true
}

const handleEdit = (row: ConfigurationChange) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: ConfigurationChange) => {
  try {
    await configurationChangeApi.delete(row.id)
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
.configuration-change-list {
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

.change-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.old-value {
  color: #f56c6c;
  text-decoration: line-through;
}

.new-value {
  color: #67c23a;
  font-weight: 500;
}

.arrow-icon {
  color: #909399;
}

.detail-content .section-title {
  margin: 20px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.change-comparison {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
}

.change-side {
  flex: 1;
}

.change-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.change-value {
  padding: 10px;
  background: white;
  border-radius: 4px;
  min-height: 40px;
  word-break: break-all;
}

.change-side.old .change-value {
  color: #f56c6c;
  text-decoration: line-through;
}

.change-side.new .change-value {
  color: #67c23a;
  font-weight: 500;
}

.change-arrow {
  font-size: 20px;
  color: #409eff;
}

.reason-text {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
