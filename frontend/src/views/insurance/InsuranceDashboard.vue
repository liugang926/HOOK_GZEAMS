<!-- Insurance Dashboard: expiring policies + claim overview -->
<template>
  <div class="page-container">
    <div class="page-title-row">
      <h2 class="page-title">
        {{ $t('assets.insurance.dashboard.title') }}
      </h2>
    </div>

    <!-- 鈹€鈹€ Stat Cards 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
    <el-row
      :gutter="20"
      class="mb-20"
    >
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card clickable"
          @click="filterExpiry('30')"
        >
          <div class="stat-label">
            {{ $t('assets.insurance.dashboard.expiring30') }}
          </div>
          <div class="stat-value text-danger">
            {{ stats.expiring30 }}
          </div>
          <div class="stat-hint">
            {{ $t('assets.insurance.dashboard.days30') }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card clickable"
          @click="filterExpiry('90')"
        >
          <div class="stat-label">
            {{ $t('assets.insurance.dashboard.expiring90') }}
          </div>
          <div class="stat-value text-warning">
            {{ stats.expiring90 }}
          </div>
          <div class="stat-hint">
            {{ $t('assets.insurance.dashboard.days90') }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card clickable"
          @click="$router.push('/insurance/claims')"
        >
          <div class="stat-label">
            {{ $t('assets.insurance.dashboard.pendingClaims') }}
          </div>
          <div class="stat-value text-warning">
            {{ stats.pendingClaims }}
          </div>
          <div class="stat-hint">
            {{ $t('assets.insurance.dashboard.viewClaims') }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="stat-card"
        >
          <div class="stat-label">
            {{ $t('assets.insurance.dashboard.activePolicies') }}
          </div>
          <div class="stat-value text-success">
            {{ stats.activePolicies }}
          </div>
          <div class="stat-hint">
            {{ $t('assets.insurance.dashboard.totalActive') }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 鈹€鈹€ Expiring Policies Table 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
    <el-card>
      <template #header>
        <div class="card-header-row">
          <span>{{ $t('assets.insurance.dashboard.expiringPolicies') }}</span>
          <div class="header-actions">
            <el-select
              v-model="expiryDays"
              size="small"
              style="width:120px"
              @change="loadExpiringPolicies"
            >
              <el-option
                :label="$t('assets.insurance.dashboard.days30')"
                value="30"
              />
              <el-option
                :label="$t('assets.insurance.dashboard.days60')"
                value="60"
              />
              <el-option
                :label="$t('assets.insurance.dashboard.days90')"
                value="90"
              />
            </el-select>
            <el-button
              size="small"
              type="primary"
              @click="$router.push('/objects/InsurancePolicy')"
            >
              {{ $t('assets.insurance.dashboard.allPolicies') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="expiringPolicies"
        border
        stripe
      >
        <el-table-column
          :label="$t('assets.insurance.columns.policyNo')"
          prop="policyNo"
          width="160"
        />
        <el-table-column
          :label="$t('assets.insurance.columns.insuredObject')"
          prop="insuredObject"
          min-width="160"
        />
        <el-table-column
          :label="$t('assets.insurance.columns.insuranceCompany')"
          prop="insuranceCompany"
          width="140"
        />
        <el-table-column
          :label="$t('assets.insurance.columns.expiryDate')"
          prop="expiryDate"
          width="120"
        />
        <el-table-column
          :label="$t('assets.insurance.columns.daysLeft')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-tag
              :type="getDaysLeftType(row.daysLeft)"
              size="small"
            >
              {{ row.daysLeft }}天
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          :label="$t('assets.insurance.columns.premium')"
          prop="annualPremium"
          width="120"
          align="right"
        />
        <el-table-column
          :label="$t('common.actions.label')"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="$router.push(`/objects/InsurancePolicy/${row.id}`)"
            >
              {{ $t('common.actions.view') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { insurancePolicyApi, claimRecordApi } from '@/api/insurance'


const loading = ref(false)
const expiryDays = ref('30')
const expiringPolicies = ref<any[]>([])

const stats = reactive({
  expiring30: 0,
  expiring90: 0,
  pendingClaims: 0,
  activePolicies: 0
})

onMounted(() => {
  loadStats()
  loadExpiringPolicies()
})

const loadStats = async () => {
  await Promise.allSettled([
    (async () => {
      const res = await insurancePolicyApi.list({ expiring_within: 30, page_size: 1 }) as any
      stats.expiring30 = res?.count ?? 0
    })(),
    (async () => {
      const res = await insurancePolicyApi.list({ expiring_within: 90, page_size: 1 }) as any
      stats.expiring90 = res?.count ?? 0
    })(),
    (async () => {
      const res = await claimRecordApi.list({ status: 'reported', page_size: 1 }) as any
      stats.pendingClaims = res?.count ?? 0
    })(),
    (async () => {
      const res = await insurancePolicyApi.list({ status: 'active', page_size: 1 }) as any
      stats.activePolicies = res?.count ?? 0
    })()
  ])
}

const loadExpiringPolicies = async () => {
  loading.value = true
  try {
    const res = await insurancePolicyApi.list({ expiring_within: expiryDays.value, page_size: 50 }) as any
    const list = res?.results ?? res?.data?.results ?? []
    const today = new Date()
    expiringPolicies.value = list.map((p: any) => ({
      ...p,
      daysLeft: p.expiryDate || p.expiry_date
        ? Math.ceil((new Date(p.expiryDate || p.expiry_date).getTime() - today.getTime()) / 86400000)
        : null
    }))
  } finally {
    loading.value = false
  }
}

const filterExpiry = (days: string) => {
  expiryDays.value = days
  loadExpiringPolicies()
}

const getDaysLeftType = (days: number | null) => {
  if (days === null) return 'info'
  if (days <= 30) return 'danger'
  if (days <= 60) return 'warning'
  return 'success'
}
</script>

<style scoped>
.page-title-row { display: flex; align-items: center; margin-bottom: 20px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.mb-20 { margin-bottom: 20px; }
.stat-card { text-align: center; padding: 4px 0; cursor: default; }
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

