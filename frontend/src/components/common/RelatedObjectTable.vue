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
 *
 * The related table now resolves the target object's list runtime model first,
 * so columns/search behave like the standalone list page instead of falling
 * back to raw record keys and opaque IDs.
 */

import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Link, Plus, Refresh, Search } from '@element-plus/icons-vue'
import BaseTable from './BaseTable.vue'
import FieldRenderer from './FieldRenderer.vue'
import type { FieldDefinition } from '@/types'
import type { SearchField, TableColumn } from '@/types/common'
import request from '@/utils/request'
import { dynamicApi } from '@/api/dynamic'
import { extractLayoutConfig } from '@/adapters/layoutAdapter'
import { compileLayoutSchema } from '@/platform/layout/layoutCompiler'
import {
  projectListColumnsFromRenderSchema,
  projectListLayoutConfigForRenderSchema,
  projectSearchFieldsFromRenderSchema,
} from '@/platform/layout/renderSchemaProjector'
import { buildSearchFields } from '@/platform/layout/searchFieldBuilder'
import { resolveRelationTargetObjectCode } from '@/platform/reference/relationObjectCode'
import { filterSystemFields } from '@/utils/transform'
import { resolveListFieldValue } from '@/utils/listFieldValue'

const { t, locale } = useI18n()

export interface RelatedObjectTableProps {
  parentObjectCode: string
  parentId: string
  field: FieldDefinition
  mode?: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  title?: string
  showCreate?: boolean
  pageSize?: number
  targetObjectCode?: string
  position?: 'main' | 'sidebar'
  disableDataFetch?: boolean
}

interface RelatedRecord {
  id: string
  [key: string]: unknown
}

type AnyRecord = Record<string, any>
type SortOrder = 'ascending' | 'descending' | null

const props = withDefaults(defineProps<RelatedObjectTableProps>(), {
  mode: 'inline_readonly',
  title: '',
  showCreate: true,
  targetObjectCode: '',
  position: 'main',
  disableDataFetch: false
})

const emit = defineEmits<{
  (e: 'record-click', record: RelatedRecord): void
  (e: 'record-edit', record: RelatedRecord): void
  (e: 'refresh'): void
}>()

const router = useRouter()
const loading = ref(false)
const records = ref<RelatedRecord[]>([])
const total = ref(0)
const currentPage = ref(1)
const showAll = ref(false)
const relationTargetObjectCode = ref('')
const modelFields = ref<AnyRecord[]>([])
const modelColumns = ref<TableColumn[] | null>(null)
const modelSearchFields = ref<SearchField[]>([])
const searchKeyword = ref('')
const searchField = ref('__all')
const sortState = ref<{ prop: string; order: SortOrder } | null>(null)

const defaultPageSize = computed(() => {
  return props.position === 'sidebar' ? 3 : (props.pageSize || 10)
})

const pageSize = ref(defaultPageSize.value)
const isSidebarMode = computed(() => props.position === 'sidebar')
const relationCode = computed(() => String(props.field.code || '').trim())

const relatedObjectCode = computed(() => {
  const fieldAny = props.field as unknown as AnyRecord
  return resolveRelationTargetObjectCode({
    explicitTarget:
      props.targetObjectCode ||
      fieldAny.targetObjectCode ||
      relationTargetObjectCode.value,
    reverseRelationModel: props.field.reverseRelationModel,
    relationCode: props.field.code
  })
})

const relatedObjectDisplay = computed(() => {
  return props.field.label || props.field.name || relatedObjectCode.value
})

const modelFieldMap = computed(() => {
  const map = new Map<string, AnyRecord>()
  for (const field of modelFields.value) {
    const code = getFieldCode(field)
    if (code && !map.has(code)) map.set(code, field)
  }
  return map
})

const searchableFieldOptions = computed(() => {
  return modelSearchFields.value
    .map((field) => {
      const value = String(field?.prop || field?.field || '').trim()
      if (!value) return null
      return {
        label: String(field?.label || value),
        value
      }
    })
    .filter((item): item is { label: string; value: string } => !!item)
})

const showSearchToolbar = computed(() => {
  return !isSidebarMode.value && searchableFieldOptions.value.length > 0
})

const searchPlaceholder = computed(() => {
  if (searchField.value !== '__all') {
    const option = searchableFieldOptions.value.find((item) => item.value === searchField.value)
    if (option) {
      return t('common.placeholders.search', { field: option.label })
    }
  }
  return t('common.placeholders.search', { field: t('common.actions.search') })
})

const tableColumns = computed<TableColumn[]>(() => {
  const fromModel = Array.isArray(modelColumns.value) ? modelColumns.value : []
  if (fromModel.length > 0) {
    return fromModel
  }

  const fallback = buildFallbackColumnsFromRecords(records.value)
  if (fallback.length > 0) return fallback

  return [
    {
      prop: 'id',
      fieldCode: 'id',
      label: t('common.relatedObject.id'),
      minWidth: 160,
      sortable: true
    }
  ]
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
  return String(field?.fieldCode || field?.field_code || field?.code || field?.field || '').trim()
}

function normalizeFieldProp(column: TableColumn): string {
  return String(column.fieldCode || column.prop || '').trim()
}

function limitColumns(columns: TableColumn[]): TableColumn[] {
  const maxColumns = props.position === 'sidebar' ? 2 : 8
  return columns.slice(0, maxColumns)
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
      if (!code) return

      candidates.push({
        code,
        sortOrder: Number(field?.sortOrder ?? field?.sort_order ?? 9999),
        column: {
          prop: code,
          fieldCode: code,
          dataKey: String(field?.dataKey || field?.data_key || code),
          label: String(field?.label || field?.name || code),
          fieldType: String(field?.fieldType || field?.field_type || field?.type || 'text'),
          type: String(field?.fieldType || field?.field_type || field?.type || 'text'),
          options: field?.options || field?.choices || [],
          referenceObject: field?.referenceObject || field?.reference_object || field?.targetObjectCode || field?.target_object_code || field?.reference_model_path || field?.relatedObject,
          targetObjectCode: field?.targetObjectCode || field?.target_object_code || field?.referenceObject || field?.reference_object,
          referenceDisplayField: field?.referenceDisplayField || field?.reference_display_field || field?.displayField || field?.display_field,
          referenceSecondaryField: field?.referenceSecondaryField || field?.reference_secondary_field,
          width: toPositiveNumber(field?.columnWidth ?? field?.column_width),
          minWidth: toPositiveNumber(field?.minColumnWidth ?? field?.min_column_width),
          sortable: field?.sortable !== false,
          visible: true
        }
      })
    })

  candidates.sort((a, b) => {
    if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder
    return a.code.localeCompare(b.code)
  })

  const filtered = candidates
    .map((item) => item.column)
    .filter((column) => normalizeFieldProp(column) !== 'id')

  return limitColumns(filtered)
}

function buildFallbackColumnsFromRecords(dataRows: RelatedRecord[]): TableColumn[] {
  const first = Array.isArray(dataRows) && dataRows.length > 0 ? (dataRows[0] as AnyRecord) : null
  const allKeys = first
    ? Object.keys(first).filter((key) => key !== 'id' && typeof first[key] !== 'object')
    : []

  const preferredKeys = ['code', 'name', 'status', 'createdAt']
  const prioritizedKeys = [
    ...preferredKeys.filter((key) => allKeys.includes(key)),
    ...allKeys.filter((key) => !preferredKeys.includes(key))
  ]

  return limitColumns(
    prioritizedKeys.map((key) => {
      const labelByKey: Record<string, string> = {
        code: t('common.relatedObject.code'),
        name: t('common.relatedObject.name'),
        status: t('common.relatedObject.status'),
        createdAt: t('common.relatedObject.createdAt')
      }

      return {
        prop: key,
        fieldCode: key,
        label: labelByKey[key] || key,
        minWidth: 120,
        sortable: true
      } as TableColumn
    })
  )
}

function extractEditableFields(payload: unknown): AnyRecord[] {
  if (!payload || typeof payload !== 'object') return []
  const raw = payload as AnyRecord
  const source = (raw.data && typeof raw.data === 'object' ? raw.data : raw) as AnyRecord
  const fieldSource = (source.fields && typeof source.fields === 'object' ? source.fields : source) as AnyRecord
  const editableFields = Array.isArray(fieldSource.editableFields)
    ? fieldSource.editableFields
    : Array.isArray(fieldSource.editable_fields)
      ? fieldSource.editable_fields
      : Array.isArray(fieldSource.fields)
        ? fieldSource.fields
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
    ''
  ).trim()
  return {
    results,
    count: Number.isFinite(count) ? count : results.length,
    targetObjectCode
  }
}

function buildColumnsFromListModel(fields: AnyRecord[], layoutPayload: AnyRecord | null): TableColumn[] {
  const businessFields = filterSystemFields(fields)
  if (!businessFields.length) return []

  const schemaLayout = projectListLayoutConfigForRenderSchema(layoutPayload)
  if (!schemaLayout) {
    return buildColumnsFromMetadata(businessFields)
  }

  const { renderSchema } = compileLayoutSchema({
    layoutConfig: schemaLayout,
    fields: businessFields,
    mode: 'list',
    keepUnknownFields: true
  })

  const projectedColumns = projectListColumnsFromRenderSchema(renderSchema, businessFields)
  const visibleColumns = projectedColumns.filter((column) => column.visible !== false)
  const sourceColumns = visibleColumns.length > 0 ? visibleColumns : projectedColumns

  const filtered = sourceColumns.filter((column) => normalizeFieldProp(column) !== 'id')
  if (filtered.length > 0) {
    return limitColumns(filtered)
  }

  return buildColumnsFromMetadata(businessFields)
}

function buildSearchFieldsFromListModel(fields: AnyRecord[], layoutPayload: AnyRecord | null): SearchField[] {
  const businessFields = filterSystemFields(fields)
  if (!businessFields.length) return []

  const schemaLayout = projectListLayoutConfigForRenderSchema(layoutPayload)
  if (!schemaLayout) {
    return buildSearchFields(businessFields)
  }

  const { renderSchema } = compileLayoutSchema({
    layoutConfig: schemaLayout,
    fields: businessFields,
    mode: 'list',
    keepUnknownFields: true
  })

  const projected = projectSearchFieldsFromRenderSchema(renderSchema, businessFields)
  return projected.length > 0 ? projected : buildSearchFields(businessFields)
}

async function loadRelatedListModel() {
  const objectCode = relatedObjectCode.value
  if (!objectCode) {
    modelFields.value = []
    modelColumns.value = null
    modelSearchFields.value = []
    return
  }

  try {
    const runtime = await dynamicApi.getRuntime(objectCode, 'list', {
      include_relations: false
    })
    const fields = extractEditableFields(runtime)
    const layoutConfig = extractLayoutConfig((runtime as AnyRecord)?.layout || runtime)
    modelFields.value = fields
    modelColumns.value = buildColumnsFromListModel(fields, layoutConfig)
    modelSearchFields.value = buildSearchFieldsFromListModel(fields, layoutConfig)
    return
  } catch {
    // Fall through to legacy metadata endpoint.
  }

  try {
    const response = await request({
      url: `/system/objects/${objectCode}/fields/`,
      method: 'get',
      params: {
        context: 'list',
        include_relations: false
      }
    })
    const fields = extractEditableFields(response)
    modelFields.value = fields
    modelColumns.value = buildColumnsFromMetadata(fields)
    modelSearchFields.value = buildSearchFields(filterSystemFields(fields))
  } catch {
    modelFields.value = []
    modelColumns.value = null
    modelSearchFields.value = []
  }
}

function getColumnValue(row: RelatedRecord, column: TableColumn): unknown {
  const fieldCode = normalizeFieldProp(column)
  if (!fieldCode) return undefined

  if (fieldCode.includes('.')) {
    return fieldCode.split('.').reduce((acc: any, key) => acc?.[key], row as AnyRecord)
  }

  const resolved = resolveListFieldValue(row, {
    fieldCode,
    prop: column.prop || fieldCode,
    dataKey: column.dataKey || column.prop || fieldCode,
    fieldType: column.fieldType || column.type,
    referenceObject: column.referenceObject || column.targetObjectCode,
    referenceDisplayField: column.referenceDisplayField
  })

  if (resolved !== undefined) return resolved
  return (row as AnyRecord)?.[column.prop]
}

function getRendererField(column: TableColumn): Record<string, unknown> {
  const fieldCode = normalizeFieldProp(column)
  const field = modelFieldMap.value.get(fieldCode) || {}
  const fieldType = String(
    column.fieldType ||
    column.type ||
    field.fieldType ||
    field.field_type ||
    field.type ||
    'text'
  )

  return {
    prop: column.prop,
    dataKey: column.dataKey || column.prop,
    fieldCode,
    code: fieldCode,
    label: column.label,
    type: fieldType,
    fieldType,
    options: column.options || field.options || field.choices || [],
    referenceObject: column.referenceObject || column.targetObjectCode || field.referenceObject || field.reference_object || field.targetObjectCode || field.target_object_code || field.reference_model_path || field.relatedObject,
    targetObjectCode: column.targetObjectCode || column.referenceObject || field.targetObjectCode || field.target_object_code || field.referenceObject || field.reference_object,
    referenceRoute: field.referenceRoute || field.reference_route,
    referenceDisplayField:
      column.referenceDisplayField ||
      field.referenceDisplayField ||
      field.reference_display_field ||
      field.displayField ||
      field.display_field,
    referenceSecondaryField:
      column.referenceSecondaryField ||
      field.referenceSecondaryField ||
      field.reference_secondary_field
  }
}

function buildRelatedQueryParams(): Record<string, unknown> {
  const params: Record<string, unknown> = {
    page: currentPage.value,
    page_size: showAll.value ? pageSize.value : defaultPageSize.value
  }

  if (sortState.value?.prop && sortState.value.order) {
    params.ordering = sortState.value.order === 'descending'
      ? `-${sortState.value.prop}`
      : sortState.value.prop
  }

  const keyword = searchKeyword.value.trim()
  if (keyword) {
    if (searchField.value && searchField.value !== '__all') {
      params[searchField.value] = keyword
    } else {
      params.search = keyword
      const fieldCodes = searchableFieldOptions.value.map((item) => item.value)
      if (fieldCodes.length > 0) {
        params.searchFields = fieldCodes.join(',')
      }
    }
  }

  return params
}

async function fetchRecords() {
  if (props.mode === 'hidden') return
  if (props.disableDataFetch) {
    records.value = []
    total.value = 0
    loading.value = false
    return
  }
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
      buildRelatedQueryParams()
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

function handleRowClick(row: RelatedRecord) {
  emit('record-click', row)
}

function handleEdit(row: RelatedRecord) {
  emit('record-edit', row)
}

function handleCreate() {
  const objectCode = relatedObjectCode.value
  if (!objectCode) return

  router.push({
    path: `/objects/${objectCode}/create`,
    query: {
      [props.field.reverseRelationField || props.parentObjectCode.toLowerCase()]: props.parentId
    }
  })
}

function handleViewAll() {
  showAll.value = true
  currentPage.value = 1
  fetchRecords()
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchRecords()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchRecords()
}

function handleSearch() {
  currentPage.value = 1
  fetchRecords()
}

function handleSearchReset() {
  searchKeyword.value = ''
  searchField.value = '__all'
  currentPage.value = 1
  fetchRecords()
}

function handleSortChange(sort: { prop?: string; order?: SortOrder }) {
  const prop = String(sort?.prop || '').trim()
  const order = sort?.order || null
  sortState.value = prop && order ? { prop, order } : null
  currentPage.value = 1
  fetchRecords()
}

function refresh() {
  fetchRecords()
  emit('refresh')
}

watch(
  relatedObjectCode,
  () => {
    modelFields.value = []
    modelColumns.value = null
    modelSearchFields.value = []
    loadRelatedListModel()
  },
  { immediate: true }
)

watch(
  () => searchableFieldOptions.value.map((item) => item.value).join(','),
  (value) => {
    const valid = value.split(',').filter(Boolean)
    if (searchField.value !== '__all' && !valid.includes(searchField.value)) {
      searchField.value = '__all'
    }
  },
  { immediate: true }
)

watch(
  () => [props.parentObjectCode, props.parentId, relationCode.value] as const,
  () => {
    currentPage.value = 1
    fetchRecords()
  },
  { immediate: true }
)

watch(locale, () => {
  loadRelatedListModel()
})

defineExpose({
  refresh,
  fetchRecords
})
</script>

<template>
  <div
    v-if="mode !== 'hidden'"
    class="related-object-card"
    :class="{ 'related-object-card--sidebar': isSidebarMode }"
  >
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
          ({{ total > defaultPageSize && !showAll ? `${defaultPageSize}+` : total }})
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

    <div
      v-if="showSearchToolbar"
      class="search-toolbar"
    >
      <el-select
        v-model="searchField"
        class="search-field-select"
      >
        <el-option
          value="__all"
          :label="t('common.selectors.allFields')"
        />
        <el-option
          v-for="option in searchableFieldOptions"
          :key="option.value"
          :label="option.label"
          :value="option.value"
        />
      </el-select>
      <el-input
        v-model="searchKeyword"
        class="search-input"
        clearable
        :placeholder="searchPlaceholder"
        @keyup.enter="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button
        type="primary"
        @click="handleSearch"
      >
        {{ t('common.actions.search') }}
      </el-button>
      <el-button @click="handleSearchReset">
        {{ t('common.actions.reset') }}
      </el-button>
    </div>

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
        @sort-change="handleSortChange"
        @action="(action: string, row: RelatedRecord) => action === 'edit' && handleEdit(row)"
      >
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
            <FieldRenderer
              :field="getRendererField(column)"
              :model-value="getColumnValue(row, column)"
              mode="read"
            />
          </slot>
        </template>
      </BaseTable>
    </div>

    <div
      v-if="total > defaultPageSize && !showAll"
      class="card-footer"
    >
      <a
        class="view-all-link"
        @click="handleViewAll"
      >
        {{ $t('common.actions.viewAll', 'View All') }}
      </a>
    </div>

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

  &.related-object-card--sidebar {
    box-shadow: none;
    border: none;
    background-color: transparent;
    border-bottom: 1px solid var(--el-border-color-lighter, #ebeef5);
    border-radius: 0;
    margin-bottom: 0;

    .card-header {
      background-color: transparent;
      padding: 12px 0;
      border-bottom: none;

      .header-icon-wrapper {
        width: 24px;
        height: 24px;
        font-size: 14px;
        border-radius: 4px;
      }

      .card-title {
        font-size: 14px;
      }
    }
  }

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

  .search-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--el-border-color-lighter, #ebeef5);
    background-color: var(--el-fill-color-blank, #ffffff);

    .search-field-select {
      width: 180px;
      flex-shrink: 0;
    }

    .search-input {
      min-width: 0;
      flex: 1;
    }
  }

  .card-body {
    padding: 0;

    :deep(.el-table) {
      border: none;

      .el-table__inner-wrapper::before {
        display: none;
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

    .search-toolbar {
      flex-wrap: wrap;

      .search-field-select,
      .search-input {
        width: 100%;
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
