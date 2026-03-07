<!--
  ReportCenter.vue

  Central reporting hub. Each card launches a preset export with the correct
  column definitions and i18n labels. Users always see field names in Chinese
  (or English when locale is en-US) — never raw prop keys.

  Architecture:
  - Each report card defines its own ExportColumn[] via composable helpers
  - All exports delegate to exportService.ts (label-aware)
  - One-click download with auto-pagination (all pages)
-->
<template>
  <div class="page-container">
    <div class="page-title-row mb-20">
      <h2 class="page-title">
        {{ $t('reports.center.title') }}
      </h2>
    </div>

    <!-- ── Module selector tabs ────────────────────────────────── -->
    <el-tabs
      v-model="activeTab"
      type="border-card"
    >
      <!-- Asset Reports -->
      <el-tab-pane
        :label="$t('reports.center.tabs.assets')"
        name="assets"
      >
        <el-row
          :gutter="20"
          class="report-grid"
        >
          <el-col
            v-for="report in assetReports"
            :key="report.key"
            :span="8"
          >
            <el-card
              shadow="hover"
              class="report-card"
            >
              <div class="report-icon">
                <el-icon
                  :size="32"
                  :color="report.color"
                >
                  <component :is="report.icon" />
                </el-icon>
              </div>
              <div class="report-name">
                {{ report.name }}
              </div>
              <div class="report-desc">
                {{ report.desc }}
              </div>
              <div class="report-actions">
                <el-button
                  size="small"
                  type="primary"
                  :loading="loadingKey === report.key"
                  @click="runReport(report)"
                >
                  <el-icon><Download /></el-icon>{{ $t('reports.center.downloadXlsx') }}
                </el-button>
                <el-button
                  size="small"
                  @click="runReport(report, 'csv')"
                >
                  CSV
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Lifecycle Reports -->
      <el-tab-pane
        :label="$t('reports.center.tabs.lifecycle')"
        name="lifecycle"
      >
        <el-row
          :gutter="20"
          class="report-grid"
        >
          <el-col
            v-for="report in lifecycleReports"
            :key="report.key"
            :span="8"
          >
            <el-card
              shadow="hover"
              class="report-card"
            >
              <div class="report-icon">
                <el-icon
                  :size="32"
                  :color="report.color"
                >
                  <component :is="report.icon" />
                </el-icon>
              </div>
              <div class="report-name">
                {{ report.name }}
              </div>
              <div class="report-desc">
                {{ report.desc }}
              </div>
              <div class="report-actions">
                <el-button
                  size="small"
                  type="primary"
                  :loading="loadingKey === report.key"
                  @click="runReport(report)"
                >
                  <el-icon><Download /></el-icon>{{ $t('reports.center.downloadXlsx') }}
                </el-button>
                <el-button
                  size="small"
                  @click="runReport(report, 'csv')"
                >
                  CSV
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Insurance Reports -->
      <el-tab-pane
        :label="$t('reports.center.tabs.insurance')"
        name="insurance"
      >
        <el-row
          :gutter="20"
          class="report-grid"
        >
          <el-col
            v-for="report in insuranceReports"
            :key="report.key"
            :span="8"
          >
            <el-card
              shadow="hover"
              class="report-card"
            >
              <div class="report-icon">
                <el-icon
                  :size="32"
                  :color="report.color"
                >
                  <component :is="report.icon" />
                </el-icon>
              </div>
              <div class="report-name">
                {{ report.name }}
              </div>
              <div class="report-desc">
                {{ report.desc }}
              </div>
              <div class="report-actions">
                <el-button
                  size="small"
                  type="primary"
                  :loading="loadingKey === report.key"
                  @click="runReport(report)"
                >
                  <el-icon><Download /></el-icon>{{ $t('reports.center.downloadXlsx') }}
                </el-button>
                <el-button
                  size="small"
                  @click="runReport(report, 'csv')"
                >
                  CSV
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <!-- Leasing Reports -->
      <el-tab-pane
        :label="$t('reports.center.tabs.leasing')"
        name="leasing"
      >
        <el-row
          :gutter="20"
          class="report-grid"
        >
          <el-col
            v-for="report in leasingReports"
            :key="report.key"
            :span="8"
          >
            <el-card
              shadow="hover"
              class="report-card"
            >
              <div class="report-icon">
                <el-icon
                  :size="32"
                  :color="report.color"
                >
                  <component :is="report.icon" />
                </el-icon>
              </div>
              <div class="report-name">
                {{ report.name }}
              </div>
              <div class="report-desc">
                {{ report.desc }}
              </div>
              <div class="report-actions">
                <el-button
                  size="small"
                  type="primary"
                  :loading="loadingKey === report.key"
                  @click="runReport(report)"
                >
                  <el-icon><Download /></el-icon>{{ $t('reports.center.downloadXlsx') }}
                </el-button>
                <el-button
                  size="small"
                  @click="runReport(report, 'csv')"
                >
                  CSV
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Files, Tickets, ShoppingCart, Tools,
  Document, Wallet, Download, DataLine, Delete
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { assetApi } from '@/api/assets'
import { purchaseRequestApi, maintenanceApi, disposalRequestApi } from '@/api/lifecycle'
import { insurancePolicyApi, claimRecordApi } from '@/api/insurance'
import { leaseContractApi, rentPaymentApi } from '@/api/leasing'
import { exportAllPages, exportToCSV, type ExportColumn } from '@/utils/exportService'

const { t } = useI18n()
const activeTab = ref('assets')
const loadingKey = ref<string | null>(null)

// ─── Report definition interface ──────────────────────────────────────────────
interface ReportDef {
  key: string
  name: string
  desc: string
  icon: any
  color: string
  columns: ExportColumn[]
  api: (params?: any) => Promise<any>
}

// ─── Asset column definitions ─────────────────────────────────────────────────
const assetReports = computed<ReportDef[]>(() => [
  {
    key: 'asset-list',
    name: t('reports.presets.assetList.name'),
    desc: t('reports.presets.assetList.desc'),
    icon: Files, color: '#409EFF',
    columns: [
      { prop: 'assetNo', label: t('reports.presets.assetList.cols.assetNo') },
      { prop: 'name', label: t('reports.presets.assetList.cols.name') },
      { prop: 'category', label: t('reports.presets.assetList.cols.category') },
      { prop: 'status', label: t('reports.presets.assetList.cols.status'), format: v => t(`assets.status.${v}`) || v },
      { prop: 'location', label: t('reports.presets.assetList.cols.location') },
      { prop: 'department', label: t('reports.presets.assetList.cols.department') },
      { prop: 'purchaseDate', label: t('reports.presets.assetList.cols.purchaseDate') },
      { prop: 'originalValue', label: t('reports.presets.assetList.cols.originalValue') },
      { prop: 'netValue', label: t('reports.presets.assetList.cols.netValue') },
    ],
    api: assetApi.list.bind(assetApi)
  },
  {
    key: 'asset-depreciation',
    name: t('reports.presets.depreciation.name'),
    desc: t('reports.presets.depreciation.desc'),
    icon: DataLine, color: '#E6A23C',
    columns: [
      { prop: 'assetNo', label: t('reports.presets.assetList.cols.assetNo') },
      { prop: 'name', label: t('reports.presets.assetList.cols.name') },
      { prop: 'originalValue', label: t('reports.presets.assetList.cols.originalValue') },
      { prop: 'accumulatedDepreciation', label: t('reports.presets.depreciation.cols.accumulated') },
      { prop: 'netValue', label: t('reports.presets.assetList.cols.netValue') },
      { prop: 'depreciationRate', label: t('reports.presets.depreciation.cols.rate') },
      { prop: 'usefulLife', label: t('reports.presets.depreciation.cols.usefulLife') },
    ],
    api: assetApi.list.bind(assetApi)
  }
])

// ─── Lifecycle column definitions ─────────────────────────────────────────────
const lifecycleReports = computed<ReportDef[]>(() => [
  {
    key: 'purchase-requests',
    name: t('reports.presets.purchaseRequests.name'),
    desc: t('reports.presets.purchaseRequests.desc'),
    icon: ShoppingCart, color: '#409EFF',
    columns: [
      { prop: 'requestNo', label: t('reports.presets.purchaseRequests.cols.requestNo') },
      { prop: 'title', label: t('reports.presets.purchaseRequests.cols.title') },
      { prop: 'status', label: t('reports.presets.purchaseRequests.cols.status'), format: v => t(`assets.lifecycle.purchaseRequest.status.${v}`) || v },
      { prop: 'requestedBy', label: t('reports.presets.purchaseRequests.cols.requestedBy') },
      { prop: 'totalAmount', label: t('reports.presets.purchaseRequests.cols.totalAmount') },
      { prop: 'createdAt', label: t('reports.presets.purchaseRequests.cols.createdAt') },
    ],
    api: purchaseRequestApi.list.bind(purchaseRequestApi)
  },
  {
    key: 'maintenance-orders',
    name: t('reports.presets.maintenance.name'),
    desc: t('reports.presets.maintenance.desc'),
    icon: Tools, color: '#E6A23C',
    columns: [
      { prop: 'maintenanceNo', label: t('reports.presets.maintenance.cols.maintenanceNo') },
      { prop: 'assetName', label: t('reports.presets.maintenance.cols.asset') },
      { prop: 'type', label: t('reports.presets.maintenance.cols.type'), format: v => t(`assets.lifecycle.maintenance.type.${v}`) || v },
      { prop: 'status', label: t('reports.presets.maintenance.cols.status'), format: v => t(`assets.lifecycle.maintenance.status.${v}`) || v },
      { prop: 'reportedDate', label: t('reports.presets.maintenance.cols.reportedDate') },
      { prop: 'completedDate', label: t('reports.presets.maintenance.cols.completedDate') },
      { prop: 'actualCost', label: t('reports.presets.maintenance.cols.cost') },
    ],
    api: maintenanceApi.list.bind(maintenanceApi)
  },
  {
    key: 'disposal-requests',
    name: t('reports.presets.disposal.name'),
    desc: t('reports.presets.disposal.desc'),
    icon: Delete, color: '#909399',
    columns: [
      { prop: 'requestNo', label: t('reports.presets.disposal.cols.requestNo') },
      { prop: 'assetName', label: t('reports.presets.disposal.cols.asset') },
      { prop: 'disposalType', label: t('reports.presets.disposal.cols.type') },
      { prop: 'status', label: t('reports.presets.disposal.cols.status') },
      { prop: 'expectedValue', label: t('reports.presets.disposal.cols.expectedValue') },
      { prop: 'actualValue', label: t('reports.presets.disposal.cols.actualValue') },
      { prop: 'createdAt', label: t('reports.presets.disposal.cols.createdAt') },
    ],
    api: disposalRequestApi.list.bind(disposalRequestApi)
  }
])

// ─── Insurance column definitions ────────────────────────────────────────────
const insuranceReports = computed<ReportDef[]>(() => [
  {
    key: 'insurance-policies',
    name: t('reports.presets.insurancePolicies.name'),
    desc: t('reports.presets.insurancePolicies.desc'),
    icon: Document, color: '#67C23A',
    columns: [
      { prop: 'policyNo', label: t('assets.insurance.columns.policyNo') },
      { prop: 'insuranceCompany', label: t('assets.insurance.columns.insuranceCompany') },
      { prop: 'expiryDate', label: t('assets.insurance.columns.expiryDate') },
      { prop: 'annualPremium', label: t('assets.insurance.columns.premium') },
      { prop: 'status', label: t('reports.presets.insurancePolicies.cols.status') },
      { prop: 'insuredAmount', label: t('reports.presets.insurancePolicies.cols.insuredAmount') },
    ],
    api: insurancePolicyApi.list.bind(insurancePolicyApi)
  },
  {
    key: 'claim-records',
    name: t('reports.presets.claimRecords.name'),
    desc: t('reports.presets.claimRecords.desc'),
    icon: Tickets, color: '#F56C6C',
    columns: [
      { prop: 'claimNo', label: t('assets.insurance.claim.columns.claimNo') },
      { prop: 'policyDisplay', label: t('assets.insurance.claim.columns.policy') },
      { prop: 'incidentDate', label: t('assets.insurance.claim.columns.incidentDate') },
      { prop: 'claimAmount', label: t('assets.insurance.claim.columns.claimAmount') },
      { prop: 'approvedAmount', label: t('assets.insurance.claim.columns.approvedAmount') },
      { prop: 'status', label: t('assets.insurance.claim.columns.status'), format: v => t(`assets.insurance.claim.status.${v}`) || v },
    ],
    api: claimRecordApi.list.bind(claimRecordApi)
  }
])

// ─── Leasing column definitions ───────────────────────────────────────────────
const leasingReports = computed<ReportDef[]>(() => [
  {
    key: 'lease-contracts',
    name: t('reports.presets.leaseContracts.name'),
    desc: t('reports.presets.leaseContracts.desc'),
    icon: Document, color: '#409EFF',
    columns: [
      { prop: 'contractNo', label: t('assets.leasing.columns.contractNo') },
      { prop: 'lessor', label: t('assets.leasing.columns.lessor') },
      { prop: 'startDate', label: t('assets.leasing.columns.startDate') },
      { prop: 'endDate', label: t('assets.leasing.columns.endDate') },
      { prop: 'monthlyRent', label: t('assets.leasing.columns.monthlyRent') },
      { prop: 'status', label: t('assets.leasing.columns.status'), format: v => t(`assets.leasing.status.${v}`) || v },
    ],
    api: leaseContractApi.list.bind(leaseContractApi)
  },
  {
    key: 'rent-payments',
    name: t('reports.presets.rentPayments.name'),
    desc: t('reports.presets.rentPayments.desc'),
    icon: Wallet, color: '#E6A23C',
    columns: [
      { prop: 'contractDisplay', label: t('assets.leasing.payment.columns.contract') },
      { prop: 'dueDate', label: t('assets.leasing.payment.columns.dueDate') },
      { prop: 'amount', label: t('assets.leasing.payment.columns.amount') },
      { prop: 'period', label: t('assets.leasing.payment.columns.period') },
      { prop: 'status', label: t('assets.leasing.payment.columns.status'), format: v => t(`assets.leasing.payment.status.${v}`) || v },
    ],
    api: rentPaymentApi.list.bind(rentPaymentApi)
  }
])

// ─── Export runner ────────────────────────────────────────────────────────────
const runReport = async (report: ReportDef, format: 'xlsx' | 'csv' = 'xlsx') => {
  loadingKey.value = report.key
  try {
    if (format === 'xlsx') {
      await exportAllPages(report.name, report.columns, report.api, {}, { sheetName: report.name.slice(0, 31) })
    } else {
      // CSV: fetch first 2000 rows
      const res = await report.api({ page: 1, page_size: 2000 }) as any
      const data = res?.results ?? (Array.isArray(res) ? res : [])
      exportToCSV(report.name, report.columns, data)
    }
    ElMessage.success(t('reports.export.successMessage'))
  } catch (e: any) {
    ElMessage.error(t('reports.export.errorMessage'))
  } finally {
    loadingKey.value = null
  }
}
</script>

<style scoped>
.page-title-row { display: flex; align-items: center; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.mb-20 { margin-bottom: 20px; }

.report-grid { margin-top: 20px; }
.report-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 12px 0; text-align: center; min-height: 180px;
  transition: transform 0.15s;
}
.report-card:hover { transform: translateY(-3px); }
.report-icon { margin-bottom: 12px; }
.report-name { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 6px; }
.report-desc { font-size: 12px; color: #909399; margin-bottom: 14px; min-height: 32px; }
.report-actions { display: flex; gap: 8px; justify-content: center; }
</style>
