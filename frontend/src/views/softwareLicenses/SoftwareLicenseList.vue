<!-- frontend/src/views/softwareLicenses/SoftwareLicenseList.vue -->

<template>
  <div class="software-license-page">
    <el-row :gutter="20">
      <!-- License List -->
      <el-col :span="16">
        <BaseListPage
          :title="$t('softwareLicenses.licenses.title')"
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
              {{ $t('softwareLicenses.licenses.add') }}
            </el-button>
            <el-button @click="loadComplianceReport">
              <el-icon><Refresh /></el-icon>
              {{ $t('softwareLicenses.licenses.refreshStats') }}
            </el-button>
          </template>
          <template #actions="{ row }">
            <el-button
              link
              type="primary"
              @click.stop="handleEdit(row)"
            >
              {{ $t('common.actions.edit') }}
            </el-button>
            <el-button
              link
              type="primary"
              @click.stop="handleAllocate(row)"
            >
              {{ $t('softwareLicenses.licenses.allocate') }}
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
            <span>{{ $t('softwareLicenses.licenses.compliance.title') }}</span>
          </template>
          <div v-loading="loadingCompliance">
            <el-statistic
              :title="$t('softwareLicenses.licenses.compliance.totalLicenses')"
              :value="complianceData.totalLicenses"
            />
            <el-divider />
            <el-statistic
              :title="$t('softwareLicenses.licenses.compliance.expiringLicenses')"
              :value="complianceData.expiringLicenses"
            >
              <template #suffix>
                <el-text
                  type="warning"
                  size="small"
                >
                  {{ $t('softwareLicenses.licenses.compliance.days30') }}
                </el-text>
              </template>
            </el-statistic>
            <el-divider />
            <div class="over-utilized-section">
              <div class="section-title">
                {{ $t('softwareLicenses.licenses.compliance.overUtilized') }}
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
                {{ $t('softwareLicenses.licenses.compliance.noOverUtilized') }}
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import BaseListPage from '@/components/common/BaseListPage.vue'
import AllocationDialog from '@/components/softwareLicenses/AllocationDialog.vue'
import { softwareLicenseApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import type { SoftwareLicense, ComplianceReport } from '@/types/softwareLicenses'
import { Plus, Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const { t } = useI18n()

const columns = computed<TableColumn[]>(() => [
  { prop: 'licenseNo', label: t('softwareLicenses.licenses.fields.licenseNo'), width: 150 },
  { prop: 'softwareName', label: t('softwareLicenses.licenses.fields.software'), minWidth: 150 },
  { prop: 'totalUnits', label: t('softwareLicenses.licenses.fields.totalUnits'), width: 100, align: 'right' },
  { prop: 'usedUnits', label: t('softwareLicenses.licenses.fields.usedUnits'), width: 80, align: 'right' },
  { prop: 'availableUnits', label: t('softwareLicenses.licenses.fields.availableUnits'), width: 80, align: 'right' },
  { prop: 'utilization', label: t('softwareLicenses.licenses.fields.utilization'), width: 150, format: (_value: any, row: any) => `${Math.round(row?.utilizationRate || 0)}%` },
  { prop: 'expiry', label: t('softwareLicenses.licenses.fields.expiryDate'), width: 120,
    tagType: (row: any) => {
      if (!row?.expiryDate) return 'success'
      if (row?.isExpired) return 'danger'
      if (isExpiringSoon(row.expiryDate)) return 'warning'
      return 'info'
    },
    format: (_value: any, row: any) => {
      if (!row?.expiryDate) return t('softwareLicenses.licenses.tags.perpetual')
      if (row?.isExpired) return t('softwareLicenses.licenses.tags.expired')
      return formatDate(row.expiryDate)
    }
  },
  { prop: 'status', label: t('softwareLicenses.licenses.fields.status'), width: 100, tagType: (row: any) => getStatusColor(row.status), format: (value: any) => getStatusLabel(value) },
  { prop: 'actions', label: t('common.labels.operation'), width: 150, slot: true, fixed: 'right' }
])

const searchFields = computed<SearchField[]>(() => [
  { prop: 'search', label: t('common.actions.search'), placeholder: t('softwareLicenses.licenses.placeholders.search') },
  { prop: 'status', label: t('softwareLicenses.licenses.fields.status'), type: 'select', options: [
    { label: t('softwareLicenses.licenses.status.active'), value: 'active' },
    { label: t('softwareLicenses.licenses.status.expired'), value: 'expired' },
    { label: t('softwareLicenses.licenses.status.suspended'), value: 'suspended' },
    { label: t('softwareLicenses.licenses.status.revoked'), value: 'revoked' }
  ]},
  { prop: 'expiringSoon', label: t('softwareLicenses.licenses.tags.expiringSoon'), type: 'boolean' }
])

const batchActions = computed(() => [
  {
    label: t('common.actions.batchDelete'),
    type: 'danger' as const,
    action: async (selectedRows: any[]) => {
      const ids = selectedRows.map(row => row.id)
      await softwareLicenseApi.batchDelete(ids)
    },
    confirm: true,
    confirmMessage: t('softwareLicenses.licenses.messages.deleteConfirm')
  }
])

const complianceData = ref<ComplianceReport>({
  totalLicenses: 0,
  expiringLicenses: 0,
  overUtilized: []
})
const loadingCompliance = ref(false)
const allocationDialogVisible = ref(false)
const selectedLicense = ref<SoftwareLicense | null>(null)

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString(t('common.locale'))
}

const isExpiringSoon = (date: string) => {
  const days = Math.ceil((new Date(date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return days <= 30 && days >= 0
}

const getStatusLabel = (status: string) => {
  return t(`softwareLicenses.licenses.status.${status}`)
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
  handleEdit(row)
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

