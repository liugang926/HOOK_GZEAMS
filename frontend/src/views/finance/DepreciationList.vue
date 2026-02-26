<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import DepreciationGenerator from './components/DepreciationGenerator.vue'
import { depreciationApi } from '@/api/depreciation'
import { formatMoney } from '@/utils/numberFormat'

const fetchRecords = async (params: any) => {
  return depreciationApi.listRecords(params)
}

const { t } = useI18n()

const showGenerator = ref(false)

const searchFields = computed(() => [
  { prop: 'period', label: t('finance.columns.period'), type: 'month', placeholder: t('common.placeholders.select') },
  { prop: 'assetId', label: t('common.labels.assetForSearch') || 'Asset', type: 'input', placeholder: t('common.placeholders.input') }
])

const columns = computed(() => [
  { prop: 'period', label: t('finance.columns.period'), width: '120' },
  { prop: 'assetCode', label: t('finance.columns.assetId'), width: '150' },
  { prop: 'assetName', label: t('common.columns.name') || 'Asset Name', minWidth: '180' },
  { prop: 'depreciationAmount', label: t('finance.columns.depreciationAmount'), width: '180', align: 'right', format: (v: any) => formatMoney(Number(v || 0)) },
  { prop: 'netValue', label: t('finance.columns.netValue') || 'Net Value', width: '180', align: 'right', format: (v: any) => formatMoney(Number(v || 0)) },
  { prop: 'status', label: t('common.columns.status'), width: '120', format: (_v: any, row: any) => row?.statusDisplay || row?.status || '-' },
  { prop: 'createdAt', label: t('common.columns.createdAt'), width: '180' },
  { prop: 'actions', label: t('common.columns.actions'), fixed: 'right', width: '100' },
])

const handleExport = async () => {
  try {
    const period = new Date().toISOString().slice(0, 7)
    const blob = await depreciationApi.exportReport({ period, format: 'csv' })
    const url = window.URL.createObjectURL(blob as any)
    const a = document.createElement('a')
    a.href = url
    a.download = `depreciation_report_${period}.csv`
    a.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success(t('common.messages.operationSuccess'))
  } catch (e: any) {
    ElMessage.error(e?.message || t('common.messages.operationFailed'))
  }
}

const handleGeneratorSuccess = () => {
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}
</script>

<template>
  <div class="depreciation-list-page">
    <BaseListPage
      :title="t('finance.depreciationList')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchRecords"
      :selectable="true"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Refresh"
          @click="showGenerator = true"
        >
          {{ t('finance.actions.calculateDepreciation') }}
        </el-button>
        <el-button
          :icon="Download"
          @click="handleExport"
        >
          {{ t('common.actions.export') }}
        </el-button>
      </template>
    </BaseListPage>

    <DepreciationGenerator
      v-model="showGenerator"
      @success="handleGeneratorSuccess"
    />
  </div>
</template>

<style scoped>
</style>
