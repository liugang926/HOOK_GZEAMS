<template>
  <div class="maintenance-list">
    <div class="page-header">
      <h3>IT Maintenance Records</h3>
      <el-button type="primary" @click="handleCreate">Add Record</el-button>
    </div>

    <!-- Filters -->
    <el-form :model="filterForm" inline class="filter-form">
      <el-form-item label="Search">
        <el-input
          v-model="filterForm.search"
          placeholder="Asset code, title, vendor..."
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="Type">
        <el-select v-model="filterForm.maintenance_type" clearable placeholder="All Types" @change="handleSearch">
          <el-option label="Preventive" value="preventive" />
          <el-option label="Corrective" value="corrective" />
          <el-option label="Upgrade" value="upgrade" />
          <el-option label="Replacement" value="replacement" />
          <el-option label="Inspection" value="inspection" />
          <el-option label="Cleaning" value="cleaning" />
          <el-option label="Other" value="other" />
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

    <!-- Records Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column prop="asset_code" label="Asset" width="140" />
      <el-table-column label="Type" width="120">
        <template #default="{ row }">
          <el-tag :type="getMaintenanceTypeColor(row.maintenance_type)" size="small">
            {{ row.maintenance_type_display }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="Title" min-width="200" />
      <el-table-column prop="maintenance_date" label="Date" width="120" />
      <el-table-column label="Cost" width="100" align="right">
        <template #default="{ row }">
          <span v-if="row.cost">${{ row.cost }}</span>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="vendor" label="Vendor" min-width="150" show-overflow-tooltip />
      <el-table-column prop="performed_by_username" label="Performed By" width="120" />
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

    <!-- Maintenance Form Dialog -->
    <MaintenanceForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />

    <!-- Detail Drawer -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="Maintenance Record Details"
      size="600px"
    >
      <div v-if="currentRow" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Asset">{{ currentRow.asset_code }} - {{ currentRow.asset_name }}</el-descriptions-item>
          <el-descriptions-item label="Type">
            <el-tag :type="getMaintenanceTypeColor(currentRow.maintenance_type)">
              {{ currentRow.maintenance_type_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Title" :span="2">{{ currentRow.title }}</el-descriptions-item>
          <el-descriptions-item label="Date">{{ currentRow.maintenance_date }}</el-descriptions-item>
          <el-descriptions-item label="Cost">{{ currentRow.cost ? `$${currentRow.cost}` : '-' }}</el-descriptions-item>
          <el-descriptions-item label="Vendor">{{ currentRow.vendor || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Performed By">{{ currentRow.performed_by_username || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentRow.description" class="section-title">Description</div>
        <div v-if="currentRow.description" class="description-text">{{ currentRow.description }}</div>

        <div v-if="currentRow.notes" class="section-title">Notes</div>
        <div v-if="currentRow.notes" class="description-text">{{ currentRow.notes }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { ITMaintenanceRecord } from '@/api/itAssets'
import { itMaintenanceApi } from '@/api/itAssets'
import MaintenanceForm from './components/MaintenanceForm.vue'

const loading = ref(false)
const tableData = ref<ITMaintenanceRecord[]>([])
const dialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentRow = ref<ITMaintenanceRecord | null>(null)

const filterForm = reactive({
  search: '',
  maintenance_type: undefined as unknown as string,
  date_range: null as any
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getMaintenanceTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    preventive: 'success',
    corrective: 'warning',
    upgrade: 'primary',
    replacement: 'danger',
    inspection: 'info',
    cleaning: '',
    other: ''
  }
  return colorMap[type] || ''
}

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
    if (filterForm.maintenance_type) {
      params.maintenance_type = filterForm.maintenance_type
    }
    if (filterForm.date_range && filterForm.date_range.length === 2) {
      params.maintenance_date_from = filterForm.date_range[0]
      params.maintenance_date_to = filterForm.date_range[1]
    }

    const res = await itMaintenanceApi.list(params) as any
    tableData.value = res.results || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error('Failed to load maintenance records')
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
  filterForm.maintenance_type = undefined as unknown as string
  filterForm.date_range = null
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleView = (row: ITMaintenanceRecord) => {
  currentRow.value = row
  detailDrawerVisible.value = true
}

const handleEdit = (row: ITMaintenanceRecord) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: ITMaintenanceRecord) => {
  try {
    await itMaintenanceApi.delete(row.id)
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
.maintenance-list {
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

.detail-content .section-title {
  margin: 20px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.detail-content .description-text {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  line-height: 1.6;
}
</style>
