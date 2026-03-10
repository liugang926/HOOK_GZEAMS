<template>
  <div
    v-loading="loading"
    class="dynamic-list-page"
  >
    <el-alert
      v-if="objectMetadata && hasNoBusinessFields"
      class="list-health-alert"
      type="warning"
      :closable="false"
      :title="t('system.businessObject.messages.noBusinessFields')"
      show-icon
    />

    <div
      v-if="showListTitleProxy && canView && !loadError"
      class="base-list-page list-title-loading-proxy"
    >
      <h2 class="page-title">
        {{ objectDisplayName || t('common.status.loading') || '...' }}
      </h2>
    </div>

    <BaseListPage
      v-if="!loadError && canView"
      ref="tableRef"
      :title="objectDisplayName || t('common.status.loading') || '...'"
      :api="fetchData"
      :table-columns="tableColumns"
      :search-fields="unifiedSearchFields"
      :batch-actions="batchActions"
      :object-code="objectCode"
      :object-icon="objectMetadata?.icon"
      @row-click="handleRowClick"
    >
      <!-- Toolbar slot for create button -->
      <template #toolbar>
        <el-button
          v-if="canAdd"
          type="primary"
          @click="handleCreate"
        >
          {{ t('common.actions.create') }}
        </el-button>
        <ExportButton
          v-if="defaultExportColumns.length > 0"
          :columns="defaultExportColumns"
          :fetch-all="(params: any) => apiClient.list({ ...params, ...currentSearchParams })"
          :filename="objectDisplayName || objectCode"
        />
        <el-button
          v-if="exportableFields.length > 0"
          @click="showFieldSelector = true"
        >
          {{ t('reports.export.customExport', '自定义导出') }}
        </el-button>
        <ImportButton
          v-if="canAdd && defaultExportColumns.length > 0"
          :columns="defaultExportColumns"
          :required="requiredFieldCodes"
          :filename="objectDisplayName || objectCode"
          @import="handleImport"
        />
        <el-button
          v-if="objectCode"
          @click="handleLayoutSettings"
        >
          {{ t('system.businessObject.actions.layouts') }}
        </el-button>
      </template>

      <template #search-__unifiedKeyword="{ getValue, setValue, search }">
        <div class="unified-search">
          <el-select
            :model-value="getValue('__unifiedField') ?? '__all'"
            class="unified-search-field"
            clearable
            :placeholder="t('common.select')"
            @update:model-value="setValue('__unifiedField', $event || '__all')"
          >
            <el-option
              :label="unifiedAllFieldsLabel"
              value="__all"
            />
            <el-option
              v-for="option in unifiedSearchFieldOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input
            :model-value="getValue('__unifiedKeyword') || ''"
            class="unified-search-keyword"
            clearable
            :placeholder="searchKeywordPlaceholder"
            @update:model-value="setValue('__unifiedKeyword', $event || '')"
            @keyup.enter="search()"
          />
        </div>
      </template>

      <!-- Dynamic slot rendering for custom fields -->
      <template
        v-for="field in slotFields"
        #[field.slotName]="slotProps"
        :key="field.fieldCode"
      >
        <FieldRenderer
          :field="getFieldDefinition(field)"
          :model-value="getSlotFieldValue((slotProps as any).row, field)"
          :form-data="(slotProps as any).row"
          :disabled="true"
        />
      </template>

      <!-- Status badge slot -->
      <template
        v-if="hasStatusField"
        #status="{ row }"
      >
        <el-tag :type="getStatusType(row.status)">
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <!-- Actions slot -->
      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click.stop="handleView(row)"
        >
          {{ t('common.actions.view') }}
        </el-button>
        <el-button
          v-if="canChange"
          link
          type="primary"
          @click.stop="handleEdit(row)"
        >
          {{ t('common.actions.edit') }}
        </el-button>
        <el-button
          v-if="canDelete"
          link
          type="danger"
          @click.stop="handleDelete(row)"
        >
          {{ t('common.actions.delete') }}
        </el-button>
      </template>
    </BaseListPage>

    <el-result
      v-else-if="!loadError && !canView"
      icon="warning"
      :title="t('common.messages.permissionDenied')"
      :sub-title="t('common.messages.permissionDeniedHint')"
    >
      <template #extra>
        <el-button @click="$router.back()">
          {{ t('common.actions.back') }}
        </el-button>
      </template>
    </el-result>

    <!-- Error state for failed metadata loads -->
    <el-result
      v-else-if="loadError"
      icon="error"
      :title="t('common.messages.loadFailed')"
      :sub-title="loadError"
    >
      <template #extra>
        <el-button
          type="primary"
          @click="retryLoad"
        >
          {{ t('common.actions.refresh') }}
        </el-button>
        <el-button @click="$router.back()">
          {{ t('common.actions.back') }}
        </el-button>
      </template>
    </el-result>

    <!-- Loading skeleton -->
    <el-skeleton
      v-else
      :rows="5"
      animated
    />
    
    <!-- Context Drawer for Create/Edit -->
    <ContextDrawer
      v-model="drawerVisible"
      :object-code="objectCode"
      :record-id="activeRecordId"
      @success="handleDrawerSuccess"
    />

    <!-- Export Field Selector Dialog -->
    <ExportFieldSelector
      v-model="showFieldSelector"
      :fields="exportableFields"
      :object-name="objectDisplayName || objectCode"
      @confirm="handleCustomExport"
    />

    <!-- Import Config + Progress Dialog -->
    <ImportConfigDialog
      v-model="showImportConfig"
      :parse-result="importParseResult"
      :fields="exportableFields"
      :object-code="objectCode"
      :field-source="orderedVisibleFieldsSource"
      @complete="handleImportComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'
import ContextDrawer from '@/components/common/ContextDrawer.vue'
import ExportButton from '@/components/common/ExportButton.vue'
import ImportButton from '@/components/common/ImportButton.vue'
import ExportFieldSelector from '@/components/common/ExportFieldSelector.vue'
import ImportConfigDialog from '@/components/common/ImportConfigDialog.vue'
import { exportAllPages } from '@/utils/exportService'
import type { ExportColumn } from '@/utils/exportService'
import type { ImportResult } from '@/utils/importService'
import { useExportColumns } from '@/composables/useExportColumns'
import type { ObjectMetadata } from '@/types'
import { createObjectClient } from '@/api/dynamic'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'
import type { TableColumn, SearchField } from '@/types/common'
import { filterSystemFields } from '@/utils/transform'
import { extractRuntimeListColumns } from '@/adapters/runtimeListLayoutAdapter'
import { buildSearchFields } from '@/platform/layout/searchFieldBuilder'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import { resolveFieldType } from '@/utils/fieldType'
import {
  projectListLayoutConfigForRenderSchema,
  projectSearchFieldsFromRenderSchema,
} from '@/platform/layout/renderSchemaProjector'
import { mergeFieldSources, orderFieldsWithSchema } from '@/platform/layout/unifiedFieldOrder'
import { compileLayoutSchema } from '@/platform/layout/layoutCompiler'
import { resolveListFieldValue } from '@/utils/listFieldValue'
import { isReferenceLikeFieldType } from '@/platform/reference/referenceFieldMeta'

interface BatchAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  icon?: any
  action: (selectedRows: any[]) => void | Promise<void>
  confirm?: boolean
  confirmMessage?: string
}

const route = useRoute()
const router = useRouter()
const { t, te } = useI18n()

// Get object code from route
const objectCode = ref<string>((route.params.code as string) || '')
const objectMetadata = ref<ObjectMetadata | null>(null)
const runtimeFields = ref<any[]>([])
const runtimeColumns = ref<any[]>([])
const runtimeLayoutConfig = ref<Record<string, any> | null>(null)
const runtimePermissions = ref<RuntimePermissions | null>(null)
const loading = ref(false)
const loadError = ref<string | null>(null)
const tableRef = ref()
const showListTitleProxy = computed(() => !tableRef.value)

// Drawer State
const drawerVisible = ref(false)
const activeRecordId = ref('')
const showFieldSelector = ref(false)
const showImportConfig = ref(false)
const importParseResult = ref<ImportResult>({ data: [], errors: [], unknownHeaders: [], missingHeaders: [] })

const objectDisplayName = computed(() => {
  return resolveObjectDisplayName(
    objectCode.value,
    objectMetadata.value?.name || '',
    t as (key: string) => string,
    te
  )
})

const searchKeywordPlaceholder = computed(() => {
  return t('common.selectors.searchKeyword')
})

const unifiedAllFieldsLabel = computed(() => {
  return t('common.selectors.allFields')
})

const buildFallbackMetadata = (): ObjectMetadata => ({
  code: objectCode.value,
  name: objectCode.value,
  isHardcoded: true,
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  fields: [],
  layouts: {},
  permissions: {
    view: true,
    add: true,
    change: true,
    delete: true
  }
} as ObjectMetadata)

const withTimeout = async <T>(promise: Promise<T>, timeoutMs = 2500): Promise<T> => {
  let timer: ReturnType<typeof setTimeout> | null = null
  try {
    return await Promise.race([
      promise,
      new Promise<T>((_, reject) => {
        timer = setTimeout(() => reject(new Error(t('common.messages.requestTimeout'))), timeoutMs)
      })
    ])
  } finally {
    if (timer) clearTimeout(timer)
  }
}

// Watch route changes to refresh data when navigating back from form page
watch(() => route.params.code, (newCode) => {
  if (newCode && newCode !== objectCode.value) {
    objectCode.value = newCode as string
    loadMetadata()
    // Refresh table data via BaseListPage
    tableRef.value?.refresh()
  }
}, { immediate: false })

// Also watch the full route for navigation within the same object
// (e.g., returning from create/edit form)
watch(() => route.path, (newPath, oldPath) => {
  // Only trigger if we're navigating back to the list page
  // and the object code hasn't changed (same list page)
  if (oldPath && newPath !== oldPath) {
    const pattern = new RegExp(`/objects/${objectCode.value}$`)
    if (pattern.test(newPath) && !pattern.test(oldPath)) {
      // Coming from form page back to list page - refresh data
      tableRef.value?.refresh()
    }
  }
}, { immediate: false })

// Create API client for this object
const apiClient = computed(() => createObjectClient(objectCode.value))

const effectivePermissions = computed<RuntimePermissions>(() => {
  const metadataPermissions = objectMetadata.value?.permissions
  return runtimePermissions.value || metadataPermissions || {
    view: true,
    add: true,
    change: true,
    delete: true
  }
})

const canView = computed(() => effectivePermissions.value.view !== false)
const canAdd = computed(() => effectivePermissions.value.add !== false)
const canChange = computed(() => effectivePermissions.value.change !== false)
const canDelete = computed(() => effectivePermissions.value.delete !== false)

const visibleFieldsSource = computed<any[]>(() => {
  const runtime = Array.isArray(runtimeFields.value) ? runtimeFields.value : []
  const metadata = Array.isArray(objectMetadata.value?.fields) ? objectMetadata.value?.fields || [] : []
  return mergeFieldSources(runtime, metadata)
})

const effectiveListLayoutConfig = computed<Record<string, any> | null>(() => {
  if (runtimeLayoutConfig.value) return runtimeLayoutConfig.value
  const metadataListLayout = (objectMetadata.value as any)?.layouts?.list
  return metadataListLayout && typeof metadataListLayout === 'object' ? metadataListLayout : null
})

const schemaLayoutConfig = computed<Record<string, any> | null>(() => {
  return projectListLayoutConfigForRenderSchema(effectiveListLayoutConfig.value, runtimeColumns.value)
})

const listRenderSchema = computed(() => {
  if (!visibleFieldsSource.value.length) return null
  return compileLayoutSchema({
    layoutConfig: schemaLayoutConfig.value,
    fields: visibleFieldsSource.value as Record<string, unknown>[],
    mode: 'list'
  }).renderSchema
})

const orderedVisibleFieldsSource = computed<any[]>(() => {
  if (!visibleFieldsSource.value.length) return []
  return orderFieldsWithSchema(
    visibleFieldsSource.value as Record<string, unknown>[],
    listRenderSchema.value
  )
})

const businessFieldCandidates = computed<any[]>(() => {
  return filterSystemFields(orderedVisibleFieldsSource.value || [])
})

const hasNoBusinessFields = computed(() => {
  return businessFieldCandidates.value.length === 0
})

const buildFieldColumn = (field: any, visible = false): TableColumn | null => {
  const fieldCode = String(field?.code || field?.fieldCode || field?.field_code || '').trim()
  if (!fieldCode) return null

  const fieldType = resolveFieldType(field, 'text')
  return {
    prop: fieldCode,
    fieldCode,
    dataKey: field?.dataKey || field?.data_key || fieldCode,
    label: field?.name || field?.label || fieldCode,
    type: fieldType,
    fieldType,
    options: field?.options || field?.choices || [],
    referenceObject: field?.referenceObject || field?.reference_object || field?.targetObjectCode || field?.target_object_code || field?.reference_model_path || field?.relatedObject,
    targetObjectCode: field?.targetObjectCode || field?.target_object_code || field?.referenceObject || field?.reference_object,
    referenceDisplayField: field?.referenceDisplayField || field?.reference_display_field || field?.displayField || field?.display_field,
    referenceSecondaryField: field?.referenceSecondaryField || field?.reference_secondary_field,
    sortable: field?.sortable !== false,
    visible
  } as TableColumn
}


const selectDefaultVisibleFieldCodes = (fields: any[], maxVisible = 8): Set<string> => {
  const candidates = filterSystemFields(fields || [])
    .map((field) => ({
      code: String(field?.code || field?.fieldCode || field?.field_code || '').trim(),
      score: (() => {
        let score = 0
        const showInList = field?.showInList ?? field?.show_in_list
        const isIdentifier = field?.isIdentifier ?? field?.is_identifier
        const code = String(field?.code || '').trim()
        if (showInList === true) score += 100
        if (isIdentifier === true) score += 60
        if (code === 'name' || code.endsWith('_name')) score += 40
        if (code === 'code' || code.endsWith('_code')) score += 30
        if (code.includes('status')) score += 20
        if (code.includes('date')) score += 5
        return score
      })(),
      sortOrder: Number(field?.sortOrder ?? field?.sort_order ?? 9999)
    }))
    .filter((item) => item.code)

  if (!candidates.length) return new Set<string>()

  const ranked = [...candidates].sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score
    return a.sortOrder - b.sortOrder
  })

  return new Set(ranked.slice(0, maxVisible).map((item) => item.code))
}

/**
 * Build columns from ALL business fields.
 * Layout is used only for default visibility and ordering hints,
 * NOT for restricting which fields can appear as columns.
 */
const buildAllFieldColumns = (
  fields: any[],
  schema: RenderSchema | null
): TableColumn[] => {
  const businessFields = filterSystemFields(fields || [])
  if (!businessFields.length) return []

  // Collect field codes that the layout explicitly declares (used for default visibility)
  const layoutFieldCodes = new Set<string>()
  if (schema?.sections?.length) {
    for (const section of schema.sections) {
      for (const field of section.fields) {
        const code = String(field.code || '').trim()
        if (code) layoutFieldCodes.add(code)
      }
    }
  }

  // Determine which fields should be visible by default
  const hasLayoutFields = layoutFieldCodes.size > 0
  // When no layout is present, use heuristic scoring to pick sensible defaults
  const heuristicVisibleCodes = hasLayoutFields
    ? new Set<string>()
    : selectDefaultVisibleFieldCodes(businessFields)

  const columns: TableColumn[] = []
  const seen = new Set<string>()

  for (const field of businessFields) {
    const code = String(field?.code || field?.fieldCode || field?.field_code || '').trim()
    if (!code || seen.has(code)) continue
    seen.add(code)

    // A field is visible by default if:
    //   - it is declared in the layout, OR
    //   - (when no layout exists) it passes heuristic scoring
    const visible = hasLayoutFields
      ? layoutFieldCodes.has(code)
      : heuristicVisibleCodes.has(code)

    const column = buildFieldColumn(field, visible)
    if (column) columns.push(column)
  }

  return columns
}

// Computed table columns from metadata (matching BaseListPage's TableColumn interface)
const tableColumns = computed<TableColumn[]>(() => {
  return buildAllFieldColumns(
    orderedVisibleFieldsSource.value,
    listRenderSchema.value
  )
})

// Search fields - fields marked as searchable (excluding system fields)
const rawSearchFields = computed<SearchField[]>(() => {
  if (!visibleFieldsSource.value.length) return []

  if (listRenderSchema.value) {
    return projectSearchFieldsFromRenderSchema(
      listRenderSchema.value,
      filterSystemFields(orderedVisibleFieldsSource.value) as Record<string, unknown>[]
    ) as SearchField[]
  }

  return buildSearchFields(filterSystemFields(orderedVisibleFieldsSource.value) as Record<string, unknown>[]) as SearchField[]
})

const unifiedSearchFieldCandidates = computed(() => {
  const candidates = filterSystemFields(orderedVisibleFieldsSource.value || [])
  const seen = new Set<string>()
  const options: Array<{ label: string; value: string }> = []
  for (const field of candidates as any[]) {
    const value = String(field?.code || field?.fieldCode || field?.field_code || '').trim()
    if (!value || seen.has(value)) continue
    seen.add(value)
    options.push({
      label: String(field?.name || field?.label || value),
      value
    })
  }
  return options
})

const visibleUnifiedSearchFieldCandidates = computed(() => {
  const visibleCodes = new Set(
    (tableColumns.value || [])
      .filter((column) => column?.visible !== false)
      .map((column) => String(column?.fieldCode || column?.prop || '').trim())
      .filter(Boolean)
  )

  if (!visibleCodes.size) return unifiedSearchFieldCandidates.value

  return unifiedSearchFieldCandidates.value.filter((item) => visibleCodes.has(item.value))
})

const unifiedSearchFieldOptions = computed(() => {
  const candidateOptions = visibleUnifiedSearchFieldCandidates.value.length
    ? visibleUnifiedSearchFieldCandidates.value
    : unifiedSearchFieldCandidates.value
  const candidateCodeSet = new Set(candidateOptions.map((item) => item.value))

  if (!rawSearchFields.value.length) return candidateOptions

  const bySearchable = rawSearchFields.value
    .map((field) => ({
      label: String(field?.label || field?.prop || field?.field || ''),
      value: String(field?.prop || field?.field || '').trim()
    }))
    .filter((item) => item.value && candidateCodeSet.has(item.value))

  return bySearchable.length ? bySearchable : candidateOptions
})

const unifiedSearchFields = computed<SearchField[]>(() => {
  return [
    {
      prop: '__unifiedKeyword',
      label: t('common.actions.search'),
      type: 'slot',
      defaultValue: ''
    }
  ]
})

// Batch actions
const batchActions = computed<BatchAction[]>(() => {
  if (!canDelete.value) return []
  return [
    {
      label: t('common.actions.batchDelete'),
      type: 'danger',
      action: async (selectedRows: any[]) => {
        try {
          await ElMessageBox.confirm(
            t('common.messages.confirmDelete'),
            t('common.dialog.confirmTitle'),
            {
              type: 'warning'
            }
          )
          const ids = selectedRows.map((row: any) => row.id)
          await apiClient.value.batchDelete(ids)
          ElMessage.success(t('common.messages.deleteSuccess'))
          tableRef.value?.refresh()
        } catch (error: any) {
          if (error !== 'cancel') {
            ElMessage.error(error.message || t('common.messages.deleteFailed'))
          }
        }
      }
    }
  ]
})


// Fields that need slot rendering (excluding system fields)
const slotFields = computed(() => {
  if (!orderedVisibleFieldsSource.value.length) return []

  return filterSystemFields(orderedVisibleFieldsSource.value)
    .filter((f: any) => {
      const fieldType = String(f.fieldType || f.field_type || f.type || '').trim()
      if (isReferenceLikeFieldType(fieldType)) return false
      if (f.referenceObject || f.reference_object || f.reference_model_path || f.relatedObject) return false
      return f.requiresSlot || f.requires_slot
    })
    .map((f: any) => ({
      fieldCode: f.code,
      field_code: f.code,
      dataKey: f.dataKey || f.data_key || f.code,
      slotName: f.code,
      fieldType: f.fieldType || f.field_type,
      field_type: f.fieldType || f.field_type,
      options: f.options,
      referenceObject: f.referenceObject || f.reference_object || f.targetObjectCode || f.target_object_code || f.reference_model_path || f.relatedObject,
      targetObjectCode: f.targetObjectCode || f.target_object_code || f.referenceObject || f.reference_object,
      referenceDisplayField: f.referenceDisplayField || f.reference_display_field || f.displayField || f.display_field,
      referenceSecondaryField: f.referenceSecondaryField || f.reference_secondary_field
    }))
})

// Check if has status field
const hasStatusField = computed(() => {
  return orderedVisibleFieldsSource.value?.some((f: any) => f.code === 'status')
})

// Data fetching method (matching BaseListPage's api prop signature)
const fetchData = async (params: any) => {
  const nextParams = { ...(params || {}) }
  const keyword = String(nextParams.__unifiedKeyword || '').trim()
  const selectedField = String(nextParams.__unifiedField || '__all').trim()
  const visibleFieldCodeSet = new Set(
    (Array.isArray(nextParams.__visibleFieldCodes) ? nextParams.__visibleFieldCodes : [])
      .map((item: any) => String(item || '').trim())
      .filter(Boolean)
  )
  const constrainedFieldCodes = unifiedSearchFieldOptions.value
    .map((item) => String(item?.value || '').trim())
    .filter((value) => !visibleFieldCodeSet.size || visibleFieldCodeSet.has(value))
  delete nextParams.__unifiedKeyword
  delete nextParams.__unifiedField
  delete nextParams.__unifiedSearch
  delete nextParams.__visibleFieldCodes
  delete nextParams.searchFields
  delete nextParams.search_fields

  if (keyword) {
    if (selectedField && selectedField !== '__all') {
      nextParams[selectedField] = keyword
    } else if (constrainedFieldCodes.length) {
      nextParams.search = keyword
      nextParams.searchFields = constrainedFieldCodes.join(',')
    } else {
      nextParams.search = keyword
    }
  }

  const response = await apiClient.value.list(nextParams)
  // Response interceptor already unwraps {success: true, data: {...}} to return data directly
  // For list endpoints, response is {count, results, next, previous}
  return response
}

// Event handlers
const handleRowClick = (row: any) => {
  handleView(row)
}

const handleView = (row: any) => {
  router.push(`/objects/${objectCode.value}/${row.id || row.id}`)
}

const handleCreate = () => {
  activeRecordId.value = ''
  drawerVisible.value = true
}

const handleLayoutSettings = () => {
  router.push({
    path: '/system/page-layouts',
    query: {
      objectCode: objectCode.value,
      objectName: objectDisplayName.value || objectCode.value
    }
  })
}

const handleEdit = (row: any) => {
  const recordId = row?.id || row?._id
  if (!recordId) {
    ElMessage.error(t('common.messages.operationFailed'))
    return
  }

  router.push(`/objects/${encodeURIComponent(objectCode.value)}/${encodeURIComponent(String(recordId))}/edit`)
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('common.messages.confirmDeleteMessage'),
      t('common.dialog.confirmTitle'), {
      type: 'warning'
    })
    await apiClient.value.delete(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    // Refresh list
    tableRef.value?.refresh()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || t('common.messages.deleteFailed'))
    }
  }
}

const handleDrawerSuccess = () => {
  tableRef.value?.refresh()
}

// ── Export / Import ────────────────────────────────────────────────────────

const {
  exportableFields,
  defaultExportColumns,
  requiredFieldCodes,
  buildExportColumns
} = useExportColumns(orderedVisibleFieldsSource)

/** Track current search/filter params for filter-aware export */
const currentSearchParams = ref<Record<string, any>>({})

/** Handle custom export with user-selected fields + smart formatting */
const handleCustomExport = async (columns: ExportColumn[]) => {
  try {
    // Re-build with smart formatters for the user-selected field codes
    const selectedCodes = columns.map(c => c.prop)
    const smartColumns = buildExportColumns(selectedCodes)
    await exportAllPages(
      objectDisplayName.value || objectCode.value,
      smartColumns,
      (params: any) => apiClient.value.list({ ...params, ...currentSearchParams.value })
    )
    ElMessage.success(t('reports.export.successMessage'))
  } catch (e: any) {
    ElMessage.error(e?.message || t('reports.export.errorMessage'))
  }
}

/** Handle import: open config dialog with parsed data */
const handleImport = (result: ImportResult) => {
  importParseResult.value = result
  showImportConfig.value = true
}

/** Handle import completion from config dialog */
const handleImportComplete = (result: { created: number; updated: number; skipped: number; failed: number }) => {
  const { created, updated, skipped, failed } = result
  if (failed > 0) {
    ElMessage.warning(
      t('reports.import.partialSuccess', { success: created + updated, fail: failed })
    )
  } else {
    const total = created + updated + skipped
    ElMessage.success(
      t('reports.import.readyMessage', { count: total })
    )
  }
  tableRef.value?.refresh()
}

// Status helper methods
const getStatusType = (status: string) => {
  const typeMap: Record<string, any> = {
    active: 'success',
    enabled: 'success',
    draft: 'info',
    pending: 'warning',
    disabled: 'danger',
    deleted: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const normalized = String(status || '').trim().toLowerCase()
  if (!normalized) return ''
  const statusKey = `common.status.${normalized}`
  return te(statusKey) ? t(statusKey) : normalized
}

// Helper to get full field definition for FieldRenderer
const getFieldDefinition = (slotField: any) => {
  // Find the original field from metadata
  const originalField = visibleFieldsSource.value?.find((f: any) => f.code === slotField.fieldCode)

  // Merge the slot field with original metadata for FieldRenderer
  return {
    code: slotField.fieldCode,
    name: slotField.fieldCode,
    dataKey: originalField?.dataKey || originalField?.data_key || slotField.dataKey || slotField.fieldCode,
    fieldType: originalField?.fieldType || originalField?.field_type || slotField.fieldType || 'text',
    field_type: originalField?.fieldType || originalField?.field_type || slotField.fieldType || 'text',
    placeholder: '',
    isRequired: false,
    is_required: false,
    isReadonly: true,
    is_readonly: true,
    options: slotField.options,
    referenceObject: originalField?.referenceObject || originalField?.reference_object || originalField?.targetObjectCode || originalField?.target_object_code || originalField?.reference_model_path || originalField?.relatedObject || slotField.referenceObject || slotField.targetObjectCode,
    targetObjectCode: originalField?.targetObjectCode || originalField?.target_object_code || originalField?.referenceObject || originalField?.reference_object || slotField.targetObjectCode || slotField.referenceObject,
    referenceDisplayField: originalField?.referenceDisplayField || originalField?.reference_display_field || originalField?.displayField || originalField?.display_field || slotField.referenceDisplayField,
    referenceSecondaryField: originalField?.referenceSecondaryField || originalField?.reference_secondary_field || slotField.referenceSecondaryField,
    description: undefined
  }
}

const getSlotFieldValue = (row: any, slotField: any) => {
  return resolveListFieldValue(row, {
    fieldCode: slotField.fieldCode,
    prop: slotField.fieldCode,
    dataKey: slotField.dataKey || slotField.fieldCode,
    fieldType: slotField.fieldType || slotField.field_type || 'text',
    referenceObject: slotField.referenceObject || slotField.reference_object || slotField.targetObjectCode || slotField.target_object_code || slotField.reference_model_path || slotField.relatedObject,
    referenceDisplayField: slotField.referenceDisplayField
  })
}

// Load metadata on mount
const loadMetadata = async () => {
  loading.value = true
  loadError.value = null
  runtimeFields.value = []
  runtimeColumns.value = []
  runtimeLayoutConfig.value = null
  runtimePermissions.value = null
  try {
    const [runtimeResult, metadataResult] = await Promise.allSettled([
      withTimeout(resolveRuntimeLayout(objectCode.value, 'list', { includeRelations: false })),
      apiClient.value.getMetadata()
    ])

    if (runtimeResult.status === 'fulfilled') {
      const resolved = runtimeResult.value
      runtimeFields.value = Array.isArray(resolved.fields)
        ? resolved.fields
        : (Array.isArray(resolved.editableFields) ? resolved.editableFields : [])
      runtimeColumns.value = extractRuntimeListColumns({
        layout: {
          layoutConfig: resolved.layoutConfig
        }
      })
      runtimeLayoutConfig.value = resolved.layoutConfig || null
      runtimePermissions.value = resolved.permissions
    }

    if (metadataResult.status === 'fulfilled') {
      const metadataPayload = ((metadataResult.value as any)?.data ?? metadataResult.value) as ObjectMetadata
      objectMetadata.value = metadataPayload || buildFallbackMetadata()
    } else {
      objectMetadata.value = buildFallbackMetadata()
    }

    if (runtimeResult.status === 'rejected') {
      if (metadataResult.status === 'fulfilled') {
        const fallbackFields = objectMetadata.value?.fields || []
        runtimeFields.value = Array.isArray(fallbackFields) ? fallbackFields : []
        const fallbackLayout = (objectMetadata.value as any)?.layouts?.list || null
        runtimeLayoutConfig.value = fallbackLayout && typeof fallbackLayout === 'object' ? fallbackLayout : null
        runtimeColumns.value = (fallbackLayout as any)?.columns || []
      } else {
        throw runtimeResult.reason
      }
    }
  } catch (error: any) {
    loadError.value = error.message || t('system.businessObject.messages.loadMetadataFailed')
    ElMessage.error(loadError.value || t('system.businessObject.messages.loadMetadataFailed'))
  } finally {
    loading.value = false
  }
}

const retryLoad = () => {
  loadMetadata()
}

onMounted(() => {
  loadMetadata()
})
</script>

<style scoped lang="scss">
.dynamic-list-page {
  height: 100%;
}

.list-health-alert {
  margin-bottom: 12px;
}

.list-title-loading-proxy {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

:deep(.unified-search) {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.unified-search-field) {
  width: 180px;
}

:deep(.unified-search-keyword) {
  width: 280px;
}
</style>


