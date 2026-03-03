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

import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import BaseTable from './BaseTable.vue'
import type { FieldDefinition, TableColumn } from '@/types'
import request from '@/utils/request'

const { t, locale } = useI18n()

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
  [key: string]: unknown
}

type AnyRecord = Record<string, any>

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
const metadataColumns = ref<TableColumn[] | null>(null)

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
  const columns: TableColumn[] = [
    {
      prop: 'id',
      label: t('common.relatedObject.id'),
      width: 96,
      sortable: true
    }
  ]

  if (metadataColumns.value?.length) {
    columns.push(...metadataColumns.value)
  } else {
    columns.push(...buildFallbackColumnsFromRecords(records.value))
  }
  return columns
})

function toPositiveNumber(value: unknown): number | undefined {
  const num = Number(value)
  return Number.isFinite(num) && num > 0 ? num : undefined
}

function getFieldCode(field: AnyRecord): string {
  return String(field?.fieldCode || field?.field_code || field?.code || '').trim()
}

function shouldDisplayInRelatedTable(field: AnyRecord): boolean {
  const hidden = field?.isHidden ?? field?.is_hidden
  if (hidden === true) return false
  const showInList = field?.showInList ?? field?.show_in_list
  return showInList !== false
}

function buildColumnsFromMetadata(fields: AnyRecord[]): TableColumn[] {
  const candidates = fields
    .filter((field) => shouldDisplayInRelatedTable(field))
    .map((field) => {
      const code = getFieldCode(field)
      if (!code || code === 'id') return null
      const sortOrder = Number(field?.sortOrder ?? field?.sort_order ?? 9999)
      return {
        code,
        sortOrder,
        column: {
          prop: code,
          label: String(field?.label || field?.name || code),
          width: toPositiveNumber(field?.columnWidth ?? field?.column_width),
          minWidth: toPositiveNumber(field?.minColumnWidth ?? field?.min_column_width),
          sortable: field?.sortable !== false
        } satisfies TableColumn
      }
    })
    .filter((item): item is { code: string; sortOrder: number; column: TableColumn } => !!item)
    .sort((a, b) => {
      if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder
      return a.code.localeCompare(b.code)
    })

  return candidates.slice(0, 8).map((item) => item.column)
}

function buildFallbackColumnsFromRecords(dataRows: RelatedRecord[]): TableColumn[] {
  const first = Array.isArray(dataRows) && dataRows.length > 0 ? (dataRows[0] as AnyRecord) : null
  const allKeys = first
    ? Object.keys(first).filter((key) => key !== 'id' && typeof first[key] !== 'object')
    : []
  const preferredKeys = ['code', 'name', 'status', 'createdAt']
  const selectedKeys = [
    ...preferredKeys.filter((key) => allKeys.includes(key)),
    ...allKeys.filter((key) => !preferredKeys.includes(key))
  ].slice(0, 3)

  const fallbackKeys = selectedKeys.length > 0 ? selectedKeys : ['code', 'name', 'createdAt']

  return fallbackKeys.map((key) => {
    const labelByKey: Record<string, string> = {
      code: t('common.relatedObject.code'),
      name: t('common.relatedObject.name'),
      status: t('common.relatedObject.status'),
      createdAt: t('common.relatedObject.createdAt')
    }
    return {
      prop: key,
      label: labelByKey[key] || key,
      minWidth: 120
    }
  })
}

function extractFieldsFromResponse(payload: unknown): AnyRecord[] {
  if (!payload || typeof payload !== 'object') return []
  const unwrapped = payload as AnyRecord
  const source =
    unwrapped.success === true && unwrapped.data && typeof unwrapped.data === 'object'
      ? (unwrapped.data as AnyRecord)
      : unwrapped
  const editableFields = Array.isArray(source.editableFields)
    ? source.editableFields
    : Array.isArray(source.editable_fields)
      ? source.editable_fields
      : []

  return editableFields.filter((field: AnyRecord) => {
    const isReverse = field?.isReverseRelation ?? field?.is_reverse_relation
    return isReverse !== true
  })
}

function extractRecordPageFromResponse(payload: unknown): { results: RelatedRecord[]; count: number } {
  if (!payload || typeof payload !== 'object') {
    return { results: [], count: 0 }
  }
  const unwrapped = payload as AnyRecord
  const source =
    unwrapped.success === true && unwrapped.data && typeof unwrapped.data === 'object'
      ? (unwrapped.data as AnyRecord)
      : unwrapped
  const results = Array.isArray(source.results) ? (source.results as RelatedRecord[]) : []
  const count = Number(source.count)
  return {
    results,
    count: Number.isFinite(count) ? count : results.length
  }
}

/**
 * Fetch related object list metadata and build table columns.
 */
const fetchRelatedColumns = async () => {
  try {
    const response = await request({
      url: `/system/objects/${relatedObjectCode.value}/fields/`,
      method: 'get',
      params: {
        context: 'list',
        include_relations: false
      }
    })
    const metadataFields = extractFieldsFromResponse(response)
    const columns = buildColumnsFromMetadata(metadataFields)
    metadataColumns.value = columns.length > 0 ? columns : null
  } catch {
    metadataColumns.value = null
  }
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

    const page = extractRecordPageFromResponse(response)
    records.value = page.results
    total.value = page.count
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

// Watch for parent ID changes
watch(() => props.parentId, () => {
  if (props.parentId) {
    currentPage.value = 1
    fetchRecords()
  }
})

watch(relatedObjectCode, () => {
  metadataColumns.value = null
  currentPage.value = 1
  fetchRelatedColumns()
  fetchRecords()
}, { immediate: true })

watch(locale, () => {
  fetchRelatedColumns()
})

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
