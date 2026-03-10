<template>
  <!--
    SubTablePanel.vue
    Reusable sub-table component for rendering parent-child line items
    (e.g., PurchaseRequestItem, AssetReceiptItem, DisposalItem).
  -->
  <div class="sub-table-panel">
    <div class="sub-table-panel__header">
      <span class="sub-table-panel__title">{{ title }}</span>
      <span
        v-if="!loading"
        class="sub-table-panel__count"
      >{{ data.length }} {{ countLabel }}</span>
      <slot name="header-actions" />
    </div>

    <el-table
      v-loading="loading"
      :data="data"
      :border="border"
      :stripe="true"
      :show-summary="showSummary"
      :summary-method="summaryMethod"
      size="small"
      class="sub-table-panel__table"
    >
      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :min-width="col.minWidth"
        :align="col.align || 'left'"
        :formatter="col.formatter"
        show-overflow-tooltip
      >
        <template
          v-if="col.slot"
          #default="scope"
        >
          <slot
            :name="col.slot"
            v-bind="scope"
          />
        </template>
      </el-table-column>

      <template #empty>
        <div class="sub-table-panel__empty">
          {{ emptyText }}
        </div>
      </template>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

export interface SubTableColumn {
  /** Data property key */
  prop: string
  /** Column header label */
  label: string
  /** Fixed column width */
  width?: number | string
  /** Minimum column width */
  minWidth?: number | string
  /** Text alignment */
  align?: 'left' | 'center' | 'right'
  /** Custom cell formatter function */
  formatter?: (row: any, column: any, cellValue: any, index: number) => string
  /** Named slot for custom cell rendering */
  slot?: string
}

const props = withDefaults(defineProps<{
  /** Panel title */
  title: string
  /** Column definitions */
  columns: SubTableColumn[]
  /** Table row data */
  data: any[]
  /** Loading state */
  loading?: boolean
  /** Show table border */
  border?: boolean
  /** Text when data is empty */
  emptyText?: string
  /** Show summary footer row (e.g., for totals) */
  showSummary?: boolean
  /** Custom summary method for el-table */
  summaryMethod?: (params: { columns: any[]; data: any[] }) => any[]
}>(), {
  loading: false,
  border: true,
  emptyText: '',
  showSummary: false,
})

const { t } = useI18n()
const countLabel = t('common.labels.items') || 'items'
</script>

<style scoped>
.sub-table-panel {
  margin-top: 16px;
}

.sub-table-panel__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 0 4px;
}

.sub-table-panel__title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.sub-table-panel__count {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.sub-table-panel__table {
  width: 100%;
}

.sub-table-panel__empty {
  padding: 24px;
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
}
</style>
