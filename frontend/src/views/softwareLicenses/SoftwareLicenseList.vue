<!-- frontend/src/views/softwareLicenses/SoftwareLicenseList.vue -->

<template>
  <div class="software-license-page">
    <el-row :gutter="20">
      <!-- License List -->
      <el-col :span="16">
        <BaseListPage
          title="软件许可证"
          :api="softwareLicenseApi.list"
          :table-columns="columns"
          :search-fields="searchFields"
          :batch-actions="batchActions"
          @row-click="handleRowClick"
        >
          <template #toolbar>
            <el-button
              type="primary"
              @click="handleCreate"
            >
              <el-icon><Plus /></el-icon>
              新建许可证
            </el-button>
            <el-button @click="loadComplianceReport">
              <el-icon><Refresh /></el-icon>
              刷新统计
            </el-button>
          </template>
          <template #utilization="{ row }">
            <el-progress
              :percentage="Math.round(row.utilizationRate || 0)"
              :status="getUtilizationStatus(row.utilizationRate)"
              :stroke-width="8"
            />
          </template>
          <template #expiry="{ row }">
            <el-tag
              v-if="!row.expiryDate"
              type="success"
            >
              永久
            </el-tag>
            <el-tag
              v-else-if="row.isExpired"
              type="danger"
            >
              已过期
            </el-tag>
            <el-tag
              v-else-if="isExpiringSoon(row.expiryDate)"
              type="warning"
            >
              {{ formatDate(row.expiryDate) }}
            </el-tag>
            <el-tag
              v-else
              type="info"
            >
              {{ formatDate(row.expiryDate) }}
            </el-tag>
          </template>
          <template #status="{ row }">
            <el-tag :type="getStatusColor(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
          <template #actions="{ row }">
            <el-button
              link
              type="primary"
              @click.stop="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              link
              type="primary"
              @click.stop="handleAllocate(row)"
            >
              分配
            </el-button>
          </template>
        </BaseListPage>
      </el-col>

      <!-- Compliance Panel -->
      <el-col :span="8">
        <el-card
          shadow="hover"
          class="compliance-card"
        >
          <template #header>
            <span>合规概览</span>
          </template>
          <div v-loading="loadingCompliance">
            <el-statistic
              title="许可证总数"
              :value="complianceData.totalLicenses"
            />
            <el-divider />
            <el-statistic
              title="即将过期"
              :value="complianceData.expiringLicenses"
            >
              <template #suffix>
                <el-text
                  type="warning"
                  size="small"
                >
                  30天内
                </el-text>
              </template>
            </el-statistic>
            <el-divider />
            <div class="over-utilized-section">
              <div class="section-title">
                过度分配
              </div>
              <el-tag
                v-for="item in complianceData.overUtilized"
                :key="item.id"
                type="danger"
                size="small"
                class="over-tag"
              >
                {{ item.software }}: {{ item.utilization }}%
              </el-tag>
              <el-text
                v-if="complianceData.overUtilized.length === 0"
                type="success"
                size="small"
              >
                无过度分配
              </el-text>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Allocation Dialog -->
    <AllocationDialog
      v-model="allocationDialogVisible"
      :license="selectedLicense"
      @allocated="handleAllocated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import AllocationDialog from '@/components/softwareLicenses/AllocationDialog.vue'
import { softwareLicenseApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import type { SoftwareLicense, ComplianceReport } from '@/types/softwareLicenses'
import { Plus, Refresh } from '@element-plus/icons-vue'

const router = useRouter()

const columns: TableColumn[] = [
  { prop: 'licenseNo', label: '许可证编号', width: 150 },
  { prop: 'softwareName', label: '软件名称', minWidth: 150 },
  { prop: 'totalUnits', label: '总数量', width: 100, align: 'right' },
  { prop: 'usedUnits', label: '已用', width: 80, align: 'right' },
  { prop: 'availableUnits', label: '可用', width: 80, align: 'right' },
  { prop: 'utilization', label: '使用率', width: 150, slot: true },
  { prop: 'expiry', label: '到期日', width: 120, slot: true },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]

const searchFields: SearchField[] = [
  { prop: 'search', label: '搜索', placeholder: '许可证号/软件名称' },
  { prop: 'status', label: '状态', type: 'select', options: [
    { label: '生效中', value: 'active' },
    { label: '已过期', value: 'expired' },
    { label: '暂停', value: 'suspended' },
    { label: '撤销', value: 'revoked' }
  ]},
  { prop: 'expiringSoon', label: '即将过期', type: 'boolean' }
]

const batchActions = [
  {
    label: '批量删除',
    type: 'danger' as const,
    action: async (selectedRows: any[]) => {
      const ids = selectedRows.map(row => row.id)
      await softwareLicenseApi.batchDelete(ids)
    },
    confirm: true,
    confirmMessage: '确定要删除选中的许可证吗？'
  }
]

const complianceData = ref<ComplianceReport>({
  totalLicenses: 0,
  expiringLicenses: 0,
  overUtilized: []
})
const loadingCompliance = ref(false)
const allocationDialogVisible = ref(false)
const selectedLicense = ref<SoftwareLicense | null>(null)

const getUtilizationStatus = (rate?: number) => {
  if (!rate) return undefined
  if (rate > 100) return 'exception'
  if (rate > 90) return 'warning'
  return 'success'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const isExpiringSoon = (date: string) => {
  const days = Math.ceil((new Date(date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return days <= 30 && days >= 0
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    active: '生效中',
    expired: '已过期',
    suspended: '暂停',
    revoked: '撤销'
  }
  return labels[status] || status
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    active: 'success',
    expired: 'danger',
    suspended: 'warning',
    revoked: 'info'
  }
  return colors[status] || ''
}

const loadComplianceReport = async () => {
  loadingCompliance.value = true
  try {
    const response = await softwareLicenseApi.complianceReport()
    complianceData.value = response.data
  } catch (error) {
    console.error('Failed to load compliance report:', error)
  } finally {
    loadingCompliance.value = false
  }
}

const handleRowClick = (row: any) => {
  // Navigate to detail or edit
}

const handleCreate = () => {
  router.push('/software-licenses/licenses/create')
}

const handleEdit = (row: any) => {
  router.push(`/software-licenses/licenses/${row.id}/edit`)
}

const handleAllocate = (row: any) => {
  selectedLicense.value = row
  allocationDialogVisible.value = true
}

const handleAllocated = () => {
  // Refresh list after allocation
  loadComplianceReport()
}

onMounted(() => {
  loadComplianceReport()
})
</script>

<style scoped>
.software-license-page {
  padding: 20px;
}

.compliance-card {
  position: sticky;
  top: 20px;
}

.over-utilized-section {
  max-height: 300px;
  overflow-y: auto;
}

.section-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: var(--el-text-color-primary);
}

.over-tag {
  margin: 5px 5px 5px 0;
}
</style>
