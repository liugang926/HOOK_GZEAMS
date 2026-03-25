<!-- Leasing Dashboard: contract kanban + expiring/payment tracking -->
<template>
  <div class="page-container">
    <div class="page-title-row mb-20">
      <h2 class="page-title">
        {{ $t('assets.leasing.dashboard.title') }}
      </h2>
      <el-button
        type="primary"
        :icon="Plus"
        @click="$router.push('/objects/LeasingContract/create')"
      >
        {{ $t('assets.leasing.dashboard.newContract') }}
      </el-button>
    </div>

    <!-- 鈹€鈹€ Stat Cards 鈹€鈹€ -->
    <el-row
      :gutter="20"
      class="mb-20"
    >
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-label">
            {{ $t('assets.leasing.dashboard.activeContracts') }}
          </div>
          <div class="stat-value text-success">
            {{ stats.active }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card clickable"
          @click="filterExpiry = true; loadExpiring()"
        >
          <div class="stat-label">
            {{ $t('assets.leasing.dashboard.expiringContracts') }}
          </div>
          <div class="stat-value text-warning">
            {{ stats.expiring }}
          </div>
          <div class="stat-hint">
            {{ $t('assets.leasing.dashboard.within30') }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card clickable"
          @click="$router.push('/leasing/payments')"
        >
          <div class="stat-label">
            {{ $t('assets.leasing.dashboard.pendingPayments') }}
          </div>
          <div class="stat-value text-danger">
            {{ stats.pendingPayments }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-label">
            {{ $t('assets.leasing.dashboard.monthlyRent') }}
          </div>
          <div class="stat-value">
            楼 {{ stats.monthlyRent }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 鈹€鈹€ Contract Table with status filter 鈹€鈹€ -->
    <el-card>
      <template #header>
        <div class="card-header-row">
          <span>{{ $t('assets.leasing.dashboard.contractList') }}</span>
          <div class="header-actions">
            <el-radio-group
              v-model="statusFilter"
              size="small"
              @change="loadContracts"
            >
              <el-radio-button value="">
                {{ $t('common.filter.all') }}
              </el-radio-button>
              <el-radio-button value="active">
                {{ $t('assets.leasing.status.active') }}
              </el-radio-button>
              <el-radio-button value="expiring">
                {{ $t('assets.leasing.status.expiring') }}
              </el-radio-button>
              <el-radio-button value="terminated">
                {{ $t('assets.leasing.status.terminated') }}
              </el-radio-button>
            </el-radio-group>
            <el-button
              size="small"
              @click="$router.push('/objects/LeasingContract')"
            >
              {{ $t('assets.leasing.dashboard.viewAll') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="contracts"
        border
        stripe
      >
        <el-table-column
          :label="$t('assets.leasing.columns.contractNo')"
          prop="contractNo"
          width="160"
        />
        <el-table-column
          :label="$t('assets.leasing.columns.lessor')"
          prop="lessor"
          width="140"
        />
        <el-table-column
          :label="$t('assets.leasing.columns.startDate')"
          prop="startDate"
          width="120"
        />
        <el-table-column
          :label="$t('assets.leasing.columns.endDate')"
          prop="endDate"
          width="120"
        />
        <el-table-column
          :label="$t('assets.leasing.columns.monthlyRent')"
          prop="monthlyRent"
          width="120"
          align="right"
        />
        <el-table-column
          :label="$t('assets.leasing.columns.status')"
          width="110"
        >
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="$t('common.actions.label')"
          width="130"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="$router.push(`/objects/LeasingContract/${row.id}`)"
            >
              {{ $t('common.actions.view') }}
            </el-button>
            <el-button
              v-if="row.status === 'active'"
              link
              type="warning"
              @click="handleTerminate(row)"
            >
              {{ $t('assets.leasing.actions.terminate') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { leaseContractApi, rentPaymentApi } from '@/api/leasing'

const { t } = useI18n()
const loading = ref(false)
const statusFilter = ref('')
const filterExpiry = ref(false)
const contracts = ref<any[]>([])

const stats = reactive({ active: 0, expiring: 0, pendingPayments: 0, monthlyRent: '0' })

onMounted(() => { loadStats(); loadContracts() })

const loadStats = async () => {
  await Promise.allSettled([
    (async () => {
      const res = await leaseContractApi.list({ status: 'active', page_size: 1 }) as any
      stats.active = res?.count ?? 0
    })(),
    (async () => {
      const res = await leaseContractApi.list({ expiring_within: 30, page_size: 1 }) as any
      stats.expiring = res?.count ?? 0
    })(),
    (async () => {
      const res = await rentPaymentApi.list({ status: 'pending', page_size: 1 }) as any
      stats.pendingPayments = res?.count ?? 0
    })()
  ])
}

const loadContracts = async () => {
  loading.value = true
  try {
    const params: any = { page_size: 50 }
    if (statusFilter.value) params.status = statusFilter.value
    if (filterExpiry.value) { params.expiring_within = 30; delete params.status }
    const res = await leaseContractApi.list(params) as any
    contracts.value = res?.results ?? res?.data?.results ?? []
  } finally {
    loading.value = false
  }
}

const loadExpiring = () => { statusFilter.value = ''; loadContracts() }

const getStatusType = (s: string) => {
  const map: Record<string, string> = { active: 'success', expiring: 'warning', terminated: 'info', draft: 'info' }
  return map[s] || 'info'
}
const getStatusLabel = (s: string) => t(`assets.leasing.status.${s}`) || s

const handleTerminate = async (row: any) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      t('assets.leasing.messages.terminateReason'),
      t('assets.leasing.actions.terminate'),
      { inputType: 'textarea', confirmButtonText: t('common.actions.confirm'), cancelButtonText: t('common.actions.cancel') }
    )
    await leaseContractApi.terminate(row.id, { reason })
    ElMessage.success(t('assets.leasing.messages.terminateSuccess'))
    loadContracts()
    loadStats()
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.page-title-row { display: flex; align-items: center; justify-content: space-between; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.mb-20 { margin-bottom: 20px; }
.stat-card { text-align: center; padding: 4px 0; }
.stat-card.clickable { cursor: pointer; transition: transform 0.15s; }
.stat-card.clickable:hover { transform: translateY(-3px); }
.stat-label { font-size: 13px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 36px; font-weight: 700; margin-bottom: 4px; }
.stat-hint { font-size: 12px; color: #c0c4cc; }
.text-danger { color: #F56C6C; }
.text-warning { color: #E6A23C; }
.text-success { color: #67C23A; }
.card-header-row { display: flex; align-items: center; justify-content: space-between; }
.header-actions { display: flex; gap: 8px; align-items: center; }
</style>

