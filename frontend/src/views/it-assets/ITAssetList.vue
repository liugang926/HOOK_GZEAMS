<template>
  <div class="it-asset-list">
    <div class="page-header">
      <h3>IT Asset Management</h3>
      <el-button type="primary" @click="handleCreate">Add IT Asset</el-button>
    </div>

    <!-- Filters -->
    <el-form :model="filterForm" inline class="filter-form">
      <el-form-item label="Search">
        <el-input
          v-model="filterForm.search"
          placeholder="Asset code, name, CPU, OS..."
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        />
      </el-form-item>
      <el-form-item label="OS">
        <el-select v-model="filterForm.os" clearable placeholder="All OS" @change="handleSearch">
          <el-option label="Windows" value="windows" />
          <el-option label="macOS" value="macos" />
          <el-option label="Linux" value="linux" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">Search</el-button>
        <el-button @click="handleFilterReset">Reset</el-button>
      </el-form-item>
    </el-form>

    <!-- Asset Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column prop="asset_code" label="Asset Code" width="140" />
      <el-table-column prop="asset_name" label="Asset Name" min-width="180" />
      <el-table-column label="CPU" min-width="150">
        <template #default="{ row }">
          <span v-if="row.cpu_model">{{ row.cpu_model }}</span>
          <span v-if="row.cpu_cores" class="text-secondary">({{ row.cpu_cores }} cores)</span>
        </template>
      </el-table-column>
      <el-table-column label="RAM" width="100" align="center">
        <template #default="{ row }">
          <span v-if="row.ram_capacity">{{ row.ram_capacity }} GB</span>
        </template>
      </el-table-column>
      <el-table-column label="Disk" width="120" align="center">
        <template #default="{ row }">
          <span v-if="row.disk_capacity">{{ row.disk_capacity }} GB</span>
          <el-tag v-if="row.disk_type" size="small" type="info">{{ row.disk_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="os_name" label="OS" min-width="150">
        <template #default="{ row }">
          <span v-if="row.os_name">{{ row.os_name }}</span>
          <span v-if="row.os_version" class="text-secondary"> {{ row.os_version }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="ip_address" label="IP Address" width="140" />
      <el-table-column prop="mac_address" label="MAC Address" width="160" />
      <el-table-column label="Security" width="100" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.disk_encrypted" type="success" size="small">Encrypted</el-tag>
          <el-tag v-else type="warning" size="small">Not Encrypted</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleView(row)">View</el-button>
          <el-button link type="primary" @click="handleEdit(row)">Edit</el-button>
          <el-popconfirm
            title="Are you sure to delete this IT asset?"
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

    <!-- Asset Form Dialog -->
    <ITAssetForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />

    <!-- Asset Detail Drawer -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="IT Asset Details"
      size="600px"
    >
      <div v-if="currentRow" class="asset-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Asset Code">{{ currentRow.asset_code }}</el-descriptions-item>
          <el-descriptions-item label="Asset Name">{{ currentRow.asset_name }}</el-descriptions-item>
          <el-descriptions-item label="Status">
            <el-tag :type="currentRow.disk_encrypted ? 'success' : 'warning'">
              {{ currentRow.disk_encrypted ? 'Secure' : 'Attention Needed' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">Hardware Configuration</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="CPU">{{ currentRow.cpu_model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Cores/Threads">
            {{ currentRow.cpu_cores || '-' }} / {{ currentRow.cpu_threads || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="RAM">{{ currentRow.ram_capacity ? `${currentRow.ram_capacity} GB` : '-' }}</el-descriptions-item>
          <el-descriptions-item label="RAM Type">{{ currentRow.ram_type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Disk">{{ currentRow.disk_capacity ? `${currentRow.disk_capacity} GB` : '-' }}</el-descriptions-item>
          <el-descriptions-item label="Disk Type">{{ currentRow.disk_type_display || '-' }}</el-descriptions-item>
          <el-descriptions-item label="GPU" :span="2">{{ currentRow.gpu_model || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">Network Information</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Hostname">{{ currentRow.hostname || '-' }}</el-descriptions-item>
          <el-descriptions-item label="IP Address">{{ currentRow.ip_address || '-' }}</el-descriptions-item>
          <el-descriptions-item label="MAC Address" :span="2">{{ currentRow.mac_address || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">Operating System</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="OS Name">{{ currentRow.os_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Version">{{ currentRow.os_version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Architecture">{{ currentRow.os_architecture || '-' }}</el-descriptions-item>
          <el-descriptions-item label="License Key">{{ currentRow.os_license_key ? '******' : '-' }}</el-descriptions-item>
        </el-descriptions>

        <div class="section-title">Security</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Disk Encrypted">
            <el-tag :type="currentRow.disk_encrypted ? 'success' : 'warning'">
              {{ currentRow.disk_encrypted ? 'Yes' : 'No' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Antivirus">{{ currentRow.antivirus_software || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Antivirus Enabled">
            <el-tag :type="currentRow.antivirus_enabled ? 'success' : 'danger'">
              {{ currentRow.antivirus_enabled ? 'Yes' : 'No' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div class="section-title">Active Directory</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="Domain">{{ currentRow.ad_domain || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Computer Name">{{ currentRow.ad_computer_name || '-' }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="currentRow.full_config" class="section-title">Configuration Summary</div>
        <el-alert v-if="currentRow.full_config" type="info" :closable="false">
          {{ currentRow.full_config }}
        </el-alert>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { ITAssetInfo } from '@/api/itAssets'
import { itAssetInfoApi } from '@/api/itAssets'
import ITAssetForm from './components/ITAssetForm.vue'

const loading = ref(false)
const tableData = ref<ITAssetInfo[]>([])
const dialogVisible = ref(false)
const detailDrawerVisible = ref(false)
const currentRow = ref<ITAssetInfo | null>(null)

const filterForm = reactive({
  search: '',
  os: undefined as unknown as string
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
    if (filterForm.os) {
      params.os_name__icontains = filterForm.os
    }

    const res = await itAssetInfoApi.list(params) as any
    tableData.value = res.results || []
    pagination.total = res.count || 0
  } catch (error) {
    ElMessage.error('Failed to load IT assets')
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
  filterForm.os = undefined as unknown as string
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleView = (row: ITAssetInfo) => {
  currentRow.value = row
  detailDrawerVisible.value = true
}

const handleEdit = (row: ITAssetInfo) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: ITAssetInfo) => {
  try {
    await itAssetInfoApi.delete(row.id)
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
.it-asset-list {
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

.text-secondary {
  color: #909399;
  font-size: 12px;
}

.asset-detail .section-title {
  margin: 20px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.asset-detail .section-title:first-of-type {
  margin-top: 0;
}
</style>
