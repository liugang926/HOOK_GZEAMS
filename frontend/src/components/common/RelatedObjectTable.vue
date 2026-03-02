<!--
  RelatedObjectTable Component

  Displays related objects (reverse relations) in a detail view.
  Supports multiple display modes: inline_editable, inline_readonly, tab_readonly.

  Reference: docs/plans/2025-02-03-unified-field-display-design.md
-->
<script setup lang="ts">
/**
 * RelatedObjectTable Component
 *
 * Displays reverse relation data (e.g., maintenance_records for an Asset)
 * in various display modes configured on the field definition.
 */

import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import BaseTable from './BaseTable.vue'
import type { FieldDefinition, TableColumn } from '@/types'
import { useFieldMetadata } from '@/composables/useFieldMetadata'
import request from '@/utils/request'

const { t } = useI18n()

// ============================================================================
// Types
// ============================================================================

export interface RelatedObjectTableProps {
  /** Parent object code (e.g., 'Asset') */
  parentObjectCode: string
  /** Parent record ID */
  parentId: string
  /** Field definition for the reverse relation */
  field: FieldDefinition
  /** Display mode */
  mode?: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  /** Custom title (overrides field name) */
  title?: string
  /** Show create button (for inline_editable mode) */
  showCreate?: boolean
  /** Default page size */
  pageSize?: number
}

interface RelatedRecord {
  id: string
  [key: string]: any
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<RelatedObjectTableProps>(), {
  mode: 'inline_readonly',
  showCreate: true,
  pageSize: 10
})

const emit = defineEmits<{
  (e: 'record-click', record: RelatedRecord): void
  (e: 'record-edit', record: RelatedRecord): void
  (e: 'refresh'): void
}>()

// ============================================================================
// State
// ============================================================================

const router = useRouter()
const loading = ref(false)
const records = ref<RelatedRecord[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(props.pageSize)

// Extract related object info from field definition
const relatedObjectCode = computed(() => {
  // Extract object code from reverse relation model path
  // e.g., "apps.lifecycle.models.Maintenance" -> "Maintenance"
  if (props.field.reverseRelationModel) {
    const parts = props.field.reverseRelationModel.split('.')
    return parts[parts.length - 1]
  }
  // Fallback: try to derive from field code
  // e.g., "maintenance_records" -> "Maintenance"
  const singular = props.field.code.replace(/(_?record|_?items|s?)$/, '')
  return singular.charAt(0).toUpperCase() + singular.slice(1)
})

const relatedObjectDisplay = computed(() => {
  return props.field.label || props.field.name || relatedObjectCode.value
})

// ============================================================================
// Computed Columns
// ============================================================================

const tableColumns = computed<TableColumn[]>(() => {
  // Build columns from field definition or use defaults
  const columns: TableColumn[] = [
    {
      prop: 'id',
      label: t('common.relatedObject.id'),
      width: 80,
      sortable: true
    }
  ]

  // Add common display fields based on related object type
  // This can be enhanced to fetch actual field definitions
  const commonFields = getCommonDisplayFields(relatedObjectCode.value)
  columns.push(...commonFields)

  return columns
})

// Get common display fields for known object types
function getCommonDisplayFields(objectCode: string): TableColumn[] {
  const fieldMap: Record<string, TableColumn[]> = {
    Maintenance: [
      { prop: 'code', label: t('common.relatedObject.code'), width: 120 },
      { prop: 'maintenanceType', label: t('common.relatedObject.type'), width: 100 },
      { prop: 'maintenanceDate', label: t('common.relatedObject.maintenance.date'), width: 120 },
      { prop: 'status', label: t('common.relatedObject.status'), width: 100 },
      { prop: 'cost', label: t('common.relatedObject.maintenance.cost'), width: 100 }
    ],
    AssetLoan: [
      { prop: 'code', label: t('common.relatedObject.code'), width: 120 },
      { prop: 'loanDate', label: t('common.relatedObject.loan.loanDate'), width: 120 },
      { prop: 'returnDate', label: t('common.relatedObject.loan.returnDate'), width: 120 },
      { prop: 'loanUser', label: t('common.relatedObject.loan.loanUser'), width: 120 },
      { prop: 'status', label: t('common.relatedObject.status'), width: 100 }
    ],
    AssetPickup: [
      { prop: 'code', label: t('common.relatedObject.code'), width: 120 },
      { prop: 'pickupDate', label: t('common.relatedObject.pickup.pickupDate'), width: 120 },
      { prop: 'pickupUser', label: t('common.relatedObject.pickup.pickupUser'), width: 120 },
      { prop: 'status', label: t('common.relatedObject.status'), width: 100 }
    ],
    AssetReturn: [
      { prop: 'code', label: t('common.relatedObject.code'), width: 120 },
      { prop: 'returnDate', label: t('common.relatedObject.return.returnDate'), width: 120 },
      { prop: 'returnUser', label: t('common.relatedObject.return.returnUser'), width: 120 },
      { prop: 'condition', label: t('common.relatedObject.return.condition'), width: 100 }
    ],
    InventoryTaskItem: [
      { prop: 'code', label: t('common.relatedObject.code'), width: 120 },
      { prop: 'status', label: t('common.relatedObject.status'), width: 100 },
      { prop: 'quantity', label: t('common.relatedObject.quantity'), width: 80 },
      { prop: 'location', label: t('common.relatedObject.location'), width: 120 }
    ]
  }

  return fieldMap[objectCode] || [
    { prop: 'code', label: t('common.relatedObject.code'), width: 150 },
    { prop: 'name', label: t('common.relatedObject.name'), width: 200 },
    { prop: 'createdAt', label: t('common.relatedObject.createdAt'), width: 150 }
  ]
}

// ============================================================================
// Data Fetching
// ============================================================================

/**
 * Fetch related records
 */
const fetchRecords = async () => {
  if (props.mode === 'hidden') return

  loading.value = true
  try {
    // Query related object records filtered by parent
    const response = await request({
      url: `/system/objects/${relatedObjectCode.value}/`,
      method: 'get',
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        // Filter by the FK field pointing to parent
        [props.field.reverseRelationField || props.parentObjectCode.toLowerCase()]: props.parentId
      }
    })

    if (response.success) {
      records.value = response.data.results || []
      total.value = response.data.count || 0
    } else {
      ElMessage.error(response.error?.message || t('common.relatedObject.loadFailed'))
    }
  } catch (error: any) {
    ElMessage.error(error.message || t('common.relatedObject.loadFailed'))
    records.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// ============================================================================
// Actions
// ============================================================================

/**
 * Handle row click
 */
const handleRowClick = (row: RelatedRecord) => {
  emit('record-click', row)
}

/**
 * Handle edit action
 */
const handleEdit = (row: RelatedRecord) => {
  emit('record-edit', row)
}

/**
 * Handle create new record
 */
const handleCreate = () => {
  // Navigate to create page with parent pre-filled
  router.push({
    name: `${relatedObjectCode.value}Create`,
    query: {
      [props.field.reverseRelationField || props.parentObjectCode.toLowerCase()]: props.parentId
    }
  })
}

/**
 * Handle pagination change
 */
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchRecords()
}

/**
 * Handle page size change
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchRecords()
}

/**
 * Refresh table data
 */
const refresh = () => {
  fetchRecords()
  emit('refresh')
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  fetchRecords()
})

// Watch for parent ID changes
watch(() => props.parentId, () => {
  if (props.parentId) {
    currentPage.value = 1
    fetchRecords()
  }
}, { immediate: true })

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  refresh,
  fetchRecords
})
</script>

<template>
  <div
    v-if="mode !== 'hidden'"
    class="related-object-table"
  >
    <!-- Table Header -->
    <div class="table-header">
      <div class="header-left">
        <h3 class="table-title">
          {{ title || relatedObjectDisplay }}
        </h3>
        <el-badge
          :value="total"
          :max="9999"
          class="count-badge"
        />
      </div>
      <div class="header-actions">
        <el-button
          v-if="mode === 'inline_editable' && showCreate"
          type="primary"
          size="small"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ t('common.actions.create') }}
        </el-button>
        <el-button
          size="small"
          :icon="Refresh"
          @click="refresh"
        >
          {{ t('common.actions.refresh') }}
        </el-button>
      </div>
    </div>

    <!-- Table -->
    <BaseTable
      :data="records"
      :columns="tableColumns"
      :loading="loading"
      :show-header="true"
      :border="true"
      :stripe="true"
      row-key="id"
      @row-click="handleRowClick"
      @action="(action: string, row: RelatedRecord) => action === 'edit' && handleEdit(row)"
    >
      <!-- Custom slot for specific columns can be added here -->
      <template
        v-for="column in tableColumns"
        #[`column-${column.prop}`]="{ row }"
        :key="column.prop"
      >
        <slot
          :name="`cell-${column.prop}`"
          :row="row"
          :column="column"
        >
          {{ row[column.prop] || '-' }}
        </slot>
      </template>
    </BaseTable>

    <!-- Pagination -->
    <div
      v-if="total > pageSize"
      class="table-pagination"
    >
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.related-object-table {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;

  .table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background-color: #f5f7fa;
    border-bottom: 1px solid #ebeef5;

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;

      .table-title {
        margin: 0;
        font-size: 16px;
        font-weight: 500;
        color: #303133;
      }

      .count-badge {
        :deep(.el-badge__content) {
          background-color: #409eff;
        }
      }
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .table-pagination {
    display: flex;
    justify-content: flex-end;
    padding: 16px 20px;
    background-color: #fff;
    border-top: 1px solid #ebeef5;
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .related-object-table {
    .table-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;

      .header-actions {
        width: 100%;
        justify-content: flex-start;
      }
    }

    .table-pagination {
      :deep(.el-pagination) {
        flex-wrap: wrap;
        justify-content: center;

        .el-pagination__sizes,
        .el-pagination__jump {
          display: none;
        }
      }
    }
  }
}
</style>
