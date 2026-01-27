<template>
  <div class="status-log-list">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <span class="title-text">资产状态日志</span>
      </div>
    </div>

    <!-- Filters -->
    <el-card
      class="filter-card"
      shadow="never"
    >
      <el-form
        :model="filterForm"
        inline
      >
        <el-form-item label="资产">
          <el-select
            v-model="filterForm.assetId"
            filterable
            remote
            clearable
            placeholder="请选择资产"
            :remote-method="searchAssets"
            :loading="assetSearchLoading"
            @change="handleSearch"
          >
            <el-option
              v-for="asset in assetOptions"
              :key="asset.id"
              :label="`${asset.code} - ${asset.name}`"
              :value="asset.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态变更">
          <el-select
            v-model="filterForm.changeType"
            clearable
            placeholder="全部类型"
            @change="handleSearch"
          >
            <el-option
              label="入库"
              value="inbound"
            />
            <el-option
              label="领用"
              value="pickup"
            />
            <el-option
              label="调拨"
              value="transfer"
            />
            <el-option
              label="退库"
              value="return"
            />
            <el-option
              label="借出"
              value="loan"
            />
            <el-option
              label="归还"
              value="loan_return"
            />
            <el-option
              label="报废"
              value="disposal"
            />
            <el-option
              label="盘点"
              value="inventory"
            />
            <el-option
              label="维修"
              value="maintenance"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filterForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleSearch"
          />
        </el-form-item>
        <el-form-item label="搜索">
          <el-input
            v-model="filterForm.search"
            placeholder="资产编码/名称"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button
                :icon="Search"
                @click="handleSearch"
              />
            </template>
          </el-input>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Table -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="tableData"
        style="width: 100%"
      >
        <el-table-column
          prop="asset.code"
          label="资产编码"
          width="150"
        />
        <el-table-column
          prop="asset.name"
          label="资产名称"
          width="200"
        />
        <el-table-column
          label="状态变更"
          width="100"
        >
          <template #default="{ row }">
            <el-tag :type="getChangeTypeColor(row.changeType)">
              {{ getChangeTypeLabel(row.changeType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="fromStatus"
          label="变更前状态"
          width="120"
        >
          <template #default="{ row }">
            {{ row.fromStatus ? getStatusLabel(row.fromStatus) : '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="toStatus"
          label="变更后状态"
          width="120"
        >
          <template #default="{ row }">
            {{ row.toStatus ? getStatusLabel(row.toStatus) : '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="operator.realName"
          label="操作人"
          width="100"
        />
        <el-table-column
          prop="operationTime"
          label="操作时间"
          width="160"
        />
        <el-table-column
          prop="remark"
          label="备注"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column
          prop="relatedBusinessType"
          label="关联业务"
          width="120"
        >
          <template #default="{ row }">
            {{ row.relatedBusinessType ? getBusinessTypeLabel(row.relatedBusinessType) : '-' }}
          </template>
        </el-table-column>
        <el-table-column
          label="操作"
          width="100"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleView(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-footer">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailDialogVisible"
      title="状态变更详情"
      width="700px"
    >
      <el-descriptions
        v-if="currentLog"
        :column="2"
        border
      >
        <el-descriptions-item label="资产编码">
          {{ currentLog.asset?.code }}
        </el-descriptions-item>
        <el-descriptions-item label="资产名称">
          {{ currentLog.asset?.name }}
        </el-descriptions-item>
        <el-descriptions-item label="变更类型">
          <el-tag :type="getChangeTypeColor(currentLog.changeType)">
            {{ getChangeTypeLabel(currentLog.changeType) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="操作时间">
          {{ currentLog.operationTime }}
        </el-descriptions-item>
        <el-descriptions-item label="变更前状态">
          {{ currentLog.fromStatus ? getStatusLabel(currentLog.fromStatus) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="变更后状态">
          {{ currentLog.toStatus ? getStatusLabel(currentLog.toStatus) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="操作人">
          {{ currentLog.operator?.realName }}
        </el-descriptions-item>
        <el-descriptions-item label="关联业务">
          {{ currentLog.relatedBusinessType ? getBusinessTypeLabel(currentLog.relatedBusinessType) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item
          label="关联单号"
          :span="2"
        >
          {{ currentLog.relatedBusinessNo || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="IP地址">
          {{ currentLog.ipAddress || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用户代理">
          {{ currentLog.userAgent || '-' }}
        </el-descriptions-item>
        <el-descriptions-item
          label="备注"
          :span="2"
        >
          {{ currentLog.remark || '-' }}
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getStatusLogList } from '@/api/assets/statusLogs'
import { getAssets } from '@/api/assets'

const loading = ref(false)
const assetSearchLoading = ref(false)
const tableData = ref([])
const assetOptions = ref([])
const detailDialogVisible = ref(false)
const currentLog = ref<any>(null)

const filterForm = reactive({
  assetId: '',
  changeType: '',
  dateRange: null,
  search: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const getChangeTypeColor = (type: string) => {
  const map: any = {
    inbound: 'success',
    pickup: 'warning',
    transfer: 'primary',
    return: 'info',
    loan: 'warning',
    loan_return: 'success',
    disposal: 'danger',
    inventory: 'primary',
    maintenance: 'warning'
  }
  return map[type] || ''
}

const getChangeTypeLabel = (type: string) => {
  const map: any = {
    inbound: '入库',
    pickup: '领用',
    transfer: '调拨',
    return: '退库',
    loan: '借出',
    loan_return: '归还',
    disposal: '报废',
    inventory: '盘点',
    maintenance: '维修'
  }
  return map[type] || type
}

const getStatusLabel = (status: string) => {
  const map: any = {
    idle: '空闲',
    in_use: '在用',
    pickup_pending: '待领用',
    transfer_pending: '待调拨',
    return_pending: '待退库',
    on_loan: '借出',
    maintenance: '维修中',
    disposal: '报废',
    lost: '丢失'
  }
  return map[status] || status
}

const getBusinessTypeLabel = (type: string) => {
  const map: any = {
    pickup: '领用单',
    transfer: '调拨单',
    return: '退库单',
    loan: '借出单',
    inventory: '盘点任务',
    maintenance: '维修单'
  }
  return map[type] || type
}

const searchAssets = async (query: string) => {
  if (!query) return
  assetSearchLoading.value = true
  try {
    const res = await getAssets({ search: query, page_size: 20 })
    assetOptions.value = res.results || res.items || []
  } finally {
    assetSearchLoading.value = false
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (filterForm.assetId) {
      params.asset = filterForm.assetId
    }
    if (filterForm.changeType) {
      params.changeType = filterForm.changeType
    }
    if (filterForm.dateRange && filterForm.dateRange.length === 2) {
      params.operationTimeFrom = filterForm.dateRange[0]
      params.operationTimeTo = filterForm.dateRange[1]
    }
    if (filterForm.search) {
      params.search = filterForm.search
    }

    const res = await getStatusLogList(params)
    tableData.value = res.results || res.items || []
    pagination.total = res.count || res.total || 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleView = (row: any) => {
  currentLog.value = row
  detailDialogVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.status-log-list {
    padding: 20px;
}
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}
.title-text {
    font-size: 20px;
    font-weight: 500;
}
.filter-card {
    margin-bottom: 20px;
}
.pagination-footer {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}
</style>
