<template>
  <el-card
    class="finance-voucher-panel"
    shadow="never"
  >
    <template #header>
      <div class="finance-voucher-panel__header">
        <span>{{ title }}</span>
        <span class="finance-voucher-panel__meta">
          {{ entries.length }}
        </span>
      </div>
    </template>

    <el-empty
      v-if="entries.length === 0"
      :description="t('common.messages.noData')"
    />

    <el-table
      v-else
      :data="entries"
      border
      stripe
    >
      <el-table-column
        prop="lineNo"
        :label="t('finance.columns.lineNo')"
        width="80"
      />
      <el-table-column
        prop="accountCode"
        :label="t('finance.columns.accountCode')"
        width="140"
      />
      <el-table-column
        prop="accountName"
        :label="t('finance.columns.accountName')"
        min-width="180"
      />
      <el-table-column
        prop="debitAmount"
        :label="t('finance.columns.debitAmount')"
        width="140"
        align="right"
      >
        <template #default="{ row }">
          {{ formatMoney(Number(row.debitAmount || 0)) }}
        </template>
      </el-table-column>
      <el-table-column
        prop="creditAmount"
        :label="t('finance.columns.creditAmount')"
        width="140"
        align="right"
      >
        <template #default="{ row }">
          {{ formatMoney(Number(row.creditAmount || 0)) }}
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        :label="t('finance.columns.description')"
        min-width="220"
      />
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatMoney } from '@/utils/numberFormat'

const props = defineProps<{
  panel: Record<string, unknown>
  recordData?: Record<string, unknown> | null
}>()

const { t, te } = useI18n()

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('finance.panels.entries'))
})

const entries = computed(() => {
  const value = props.recordData?.entries
  return Array.isArray(value) ? value : []
})
</script>

<style scoped>
.finance-voucher-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.finance-voucher-panel__meta {
  font-size: 12px;
  color: #606266;
}
</style>
