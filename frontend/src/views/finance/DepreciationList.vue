<template>
  <div class="depreciation-list-page">
    <BaseListPage
      title="折旧管理"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchRecords"
      :selectable="true"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Calculator"
          @click="showGenerator = true"
        >
          计提折旧
        </el-button>
        <el-button
          :icon="Download"
          @click="handleExport"
        >
          导出报表
        </el-button>
      </template>

      <template #cell-depreciationAmount="{ row }">
        <span class="money-text">¥{{ formatMoney(row.depreciationAmount) }}</span>
      </template>

      <template #status="{ row }">
        <el-tag>{{ row.status }}</el-tag>
      </template>
    </BaseListPage>

    <DepreciationGenerator
      v-model="showGenerator"
      @success="handleGenerateSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import DepreciationGenerator from './components/DepreciationGenerator.vue'
import { depreciationApi } from '@/api/depreciation'
import { formatMoney } from '@/utils/numberFormat'

// Mock icon for Calculator if not available, or import specific
import { VideoPlay as Calculator } from '@element-plus/icons-vue' 

const showGenerator = ref(false)

const columns = [
  { prop: 'assetCode', label: '资产编码', width: 140 },
  { prop: 'assetName', label: '资产名称', minWidth: 150 },
  { prop: 'period', label: '期间', width: 100 },
  { prop: 'depreciationAmount', label: '本期折旧', width: 120, slot: true, align: 'right' },
  { prop: 'accumulatedDepreciation', label: '累计折旧', width: 120, align: 'right' },
  { prop: 'netValue', label: '净值', width: 120, align: 'right' },
  { prop: 'status', label: '状态', width: 100 } // posted, draft
]

const searchFields = [
  { field: 'period', label: '期间', type: 'month', placeholder: '选择月份' },
  { field: 'assetId', label: '资产', type: 'input', placeholder: '输入资产编码/名称' } // Ideally AssetSelector
]

const fetchRecords = async (params: any) => {
  return await depreciationApi.listRecords(params)
}

const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

const handleGenerateSuccess = () => {
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}
</script>

<style scoped>
.money-text {
  font-family: monospace;
}
</style>
