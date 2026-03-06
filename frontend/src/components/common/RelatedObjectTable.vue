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
import { Plus, Refresh, Link } from '@element-plus/icons-vue'
import BaseTable from './BaseTable.vue'
import type { FieldDefinition, TableColumn } from '@/types'
import request from '@/utils/request'
import { dynamicApi } from '@/api/dynamic'
import { resolveRelationTargetObjectCode } from '@/platform/reference/relationObjectCode'

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
  /** Explicit target object code (recommended for stable routing) */
  targetObjectCode?: string
}

interface RelatedRecord {
  id: string
  [key: string]: unknown
}

type AnyRecord = Record<string, unknown>

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<RelatedObjectTableProps>(), {
  mode: 'inline_readonly',
  title: '',
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
const showAll = ref(false)
const metadataColumns = ref<TableColumn[] | null>(null)
const relationTargetObjectCode = ref('')

const relationCode = computed(() => {
  return String(props.field.code || '').trim()
})

// Extract related object info from relation/field metadata
const relatedObjectCode = computed(() => {
  const fieldAny = props.field as unknown as AnyRecord
  return resolveRelationTargetObjectCode({
    explicitTarget:
      props.targetObjectCode ||
      fieldAny.targetObjectCode ||
      fieldAny.target_object_code ||
      relationTargetObjectCode.value,
    reverseRelationModel: props.field.reverseRelationModel,
    relationCode: props.field.code
  })
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

function toErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return ''
}

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
  const candidates: Array<{ code: string; sortOrder: number; column: TableColumn }> = []

  fields
    .filter((field) => shouldDisplayInRelatedTable(field))
    .forEach((field) => {
      const code = getFieldCode(field)
      if (!code || code === 'id') return

      candidates.push({
        code,
        sortOrder: Number(field?.sortOrder ?? field?.sort_order ?? 9999),
        column: {
          prop: code,
          label: String(field?.label || field?.name || code),
          width: toPositiveNumber(field?.columnWidth ?? field?.column_width),
          minWidth: toPositiveNumber(field?.minColumnWidth ?? field?.min_column_width),
          sortable: field?.sortable !== false
        }
      })
    })

  candidates.sort((a, b) => {
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

function extractRecordPageFromResponse(payload: unknown): {
  results: RelatedRecord[]
  count: number
  targetObjectCode: string
} {
  if (!payload || typeof payload !== 'object') {
    return { results: [], count: 0, targetObjectCode: '' }
  }
  const unwrapped = payload as AnyRecord
  const source =
    unwrapped.success === true && unwrapped.data && typeof unwrapped.data === 'object'
      ? (unwrapped.data as AnyRecord)
      : unwrapped
  const results = Array.isArray(source.results) ? (source.results as RelatedRecord[]) : []
  const count = Number(source.count)
  const targetObjectCode = String(
    source.targetObjectCode ||
    source.target_object_code ||
    ((source.relation as AnyRecord | undefined)?.targetObjectCode) ||
    ((source.relation as AnyRecord | undefined)?.target_object_code) ||
    ''
  ).trim()
  return {
    results,
    count: Number.isFinite(count) ? count : results.length,
    targetObjectCode
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
  if (!props.parentObjectCode || !props.parentId || !relationCode.value) {
    records.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    const response = await dynamicApi.getRelated(
      props.parentObjectCode,
      props.parentId,
      relationCode.value,
      {
        page: currentPage.value,
        page_size: showAll.value ? pageSize.value : 5
      }
    )

    const page = extractRecordPageFromResponse(response)
    records.value = page.results
    total.value = page.count
    if (page.targetObjectCode && page.targetObjectCode !== relationTargetObjectCode.value) {
      relationTargetObjectCode.value = page.targetObjectCode
    }
  } catch (error: unknown) {
    ElMessage.error(toErrorMessage(error) || t('common.relatedObject.loadFailed'))
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
  const objectCode = relatedObjectCode.value
  if (!objectCode) return

  // Navigate via unified dynamic route and keep legacy prefill query key.
  router.push({
    path: `/objects/${objectCode}/create`,
    query: {
      [props.field.reverseRelationField || props.parentObjectCode.toLowerCase()]: props.parentId
    }
  })
}

/**
 * Handle view all
 */
const handleViewAll = () => {
  showAll.value = true
  currentPage.value = 1
  fetchRecords()
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
  fetchRelatedColumns()
}, { immediate: true })

watch(
  () => [props.parentObjectCode, props.parentId, relationCode.value] as const,
  () => {
    currentPage.value = 1
    fetchRecords()
  },
  { immediate: true }
)

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
    class="related-object-card"
  >
    <!-- Card Header -->
    <div class="card-header">
      <div class="header-left">
        <div class="header-icon-wrapper">
          <el-icon><Link /></el-icon>
        </div>
        <h3 class="card-title">
          {{ title || relatedObjectDisplay }}
        </h3>
        <span
          v-if="total > 0"
          class="card-count"
        >
          ({{ total > 5 && !showAll ? '5+' : total }})
        </span>
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
    <div class="card-body">
      <BaseTable
        :data="records"
        :columns="tableColumns"
        :loading="loading"
        :show-header="true"
        :border="false"
        :stripe="false"
        row-key="id"
        class="related-list-table"
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
    </div>

    <!-- View All Footer -->
    <div
      v-if="total > 5 && !showAll"
      class="card-footer"
    >
      <a
        class="view-all-link"
        @click="handleViewAll"
      >
        {{ $t('common.actions.viewAll', 'View All') }}
      </a>
    </div>

    <!-- Pagination (hidden unless showAll is active) -->
    <div
      v-if="showAll && total > pageSize"
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
@use '@/styles/variables.scss' as *;

.related-object-card {
  background-color: var(--el-bg-color-overlay, #ffffff);
  border-radius: var(--el-border-radius-base, 8px);
  border: 1px solid var(--el-border-color-lighter, #ebeef5);
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
  overflow: hidden;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background-color: var(--el-bg-color-page, #f9fafc);
    border-bottom: 1px solid var(--el-border-color-lighter, #ebeef5);

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .header-icon-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        background-color: var(--el-color-primary-light-9, #ecf5ff);
        color: var(--el-color-primary, #409eff);
        border-radius: 4px;
        font-size: 16px;
      }

      .card-title {
        margin: 0;
        font-size: 15px;
        font-weight: 600;
        color: var(--el-text-color-primary, #303133);
      }

      .card-count {
        font-size: 14px;
        color: var(--el-text-color-secondary, #909399);
      }
    }

    .header-actions {
      display: flex;
      gap: 8px;
    }
  }

  .card-body {
    padding: 0;
    
    :deep(.el-table) {
      border: none;
      
      .el-table__inner-wrapper::before {
        display: none; // remove bottom border from table wrapper
      }
      
      th.el-table__cell {
        background-color: transparent !important;
        font-weight: 600;
        color: var(--el-text-color-regular, #606266);
      }
    }
  }

  .card-footer {
    border-top: 1px solid var(--el-border-color-lighter, #ebeef5);
    background-color: var(--el-fill-color-blank, #ffffff);
    padding: 0;
    
    .view-all-link {
      display: block;
      width: 100%;
      padding: 12px 0;
      text-align: center;
      color: var(--el-color-primary, #409eff);
      font-size: 14px;
      font-weight: 500;
      text-decoration: none;
      cursor: pointer;
      transition: background-color 0.2s;
      
      &:hover {
        background-color: var(--el-fill-color-light, #f5f7fa);
      }
    }
  }

  .table-pagination {
    display: flex;
    justify-content: flex-end;
    padding: 12px 16px;
    background-color: var(--el-fill-color-blank, #ffffff);
    border-top: 1px solid var(--el-border-color-lighter, #ebeef5);
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .related-object-card {
    .card-header {
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
