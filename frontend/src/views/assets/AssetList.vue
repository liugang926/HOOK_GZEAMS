<!--
  AssetList View

  Main asset management list page with:
  - Search and filter functionality
  - Batch operations (export, delete)
  - Create/Edit/Delete actions
  - Status visualization
  - Integration with BaseListPage component
-->

<template>
  <div class="asset-list-page">
    <BaseListPage
      :title="$t('assets.list.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchAssets"
      :batch-actions="batchActions"
      :selectable="true"
      object-code="Asset"
      @row-click="handleRowClick"
    >
      <template #search-search="{ form, setValue, search }">
        <div class="smart-search-field">
          <div class="smart-search-field__row">
            <el-autocomplete
              v-model="form.search"
              :fetch-suggestions="loadSmartSuggestions"
              :trigger-on-focus="true"
              :debounce="250"
              :placeholder="t('assets.search.keywordPlaceholder')"
              clearable
              @select="(item: SmartSearchSuggestionOption) => handleSuggestionSelect(item, setValue, search)"
              @keyup.enter="search()"
            >
              <template #default="{ item }">
                <div class="smart-search-suggestion">
                  <span class="smart-search-suggestion__label">{{ item.label }}</span>
                  <span
                    v-if="item.meta"
                    class="smart-search-suggestion__meta"
                  >
                    {{ item.meta }}
                  </span>
                </div>
              </template>
            </el-autocomplete>

            <el-button
              :icon="Star"
              circle
              @click="saveCurrentSearch(form)"
            />

            <el-dropdown
              @command="(id: string | number) => handleSavedSearchCommand(String(id), setValue, search)"
              @visible-change="handleSavedSearchVisibleChange"
            >
              <el-button
                :icon="CollectionTag"
                circle
              />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="item in savedSearches"
                    :key="item.id"
                    :command="item.id"
                  >
                    <div class="saved-search-option">
                      <span>{{ item.name }}</span>
                      <span class="saved-search-option__meta">
                        {{ item.keyword || t('assets.search.savedFilterOnly') }}
                      </span>
                    </div>
                  </el-dropdown-item>
                  <el-dropdown-item
                    v-if="!savedSearches.length"
                    disabled
                  >
                    {{ t('assets.search.noSavedSearches') }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div
            v-if="aggregationChips.length"
            class="smart-search-field__aggregations"
          >
            <span class="smart-search-field__aggregations-label">
              {{ t('assets.search.quickFilters') }}
            </span>
            <el-tag
              v-for="chip in aggregationChips"
              :key="chip.key"
              size="small"
              effect="plain"
              class="smart-search-field__chip"
              @click="applyAggregationChip(chip, setValue, search)"
            >
              {{ chip.label }} ({{ chip.count }})
            </el-tag>
          </div>
        </div>
      </template>

      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ $t('assets.list.createButton') }}
        </el-button>
        <el-button
          :icon="Download"
          @click="handleExport()"
        >
          {{ $t('common.actions.export') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click="handleEdit(row)"
        >
          {{ $t('common.actions.edit') }}
        </el-button>
        <el-button
          link
          type="danger"
          @click="handleDelete(row)"
        >
          {{ $t('common.actions.delete') }}
        </el-button>
      </template>

      <template #cell-assetCode="{ row }">
        <ResultHighlight
          :highlight="row.highlight?.assetCode"
          :fallback="row.assetCode"
        />
      </template>

      <template #cell-assetName="{ row }">
        <ResultHighlight
          :highlight="row.highlight?.assetName"
          :fallback="row.assetName"
        />
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
/**
 * AssetList View Component
 *
 * Main list view for asset management with search, filter,
 * and CRUD operations.
 */

import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus, Download, CollectionTag, Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetApi } from '@/api/assets'
import { categoryApi } from '@/api/assets'
import type { Asset, AssetStatus } from '@/types/assets'
import type { TableColumn, SearchField } from '@/types/common'
import { useCrud } from '@/composables/useCrud'
import ResultHighlight from '@/components/common/ResultHighlight.vue'
import {
  createSavedSearch,
  getSavedSearches,
  getSearchHistory,
  getSearchSuggestions,
  searchAssetsForList,
  useSavedSearch,
  type SavedSearchRecord,
} from '@/api/search'

const router = useRouter()
const { t } = useI18n()

type SmartSearchSuggestionOption = {
  value?: string
  label?: string
  meta?: string
  filters?: Record<string, unknown>
  type?: 'history' | 'suggestion'
}

// ============================================================================
// State
// ============================================================================

const categoryOptions = ref<Array<{ label: string; value: string }>>([])
const searchAggregations = ref<Record<string, any>>({})
const savedSearches = ref<SavedSearchRecord[]>([])

// ============================================================================
// API wrapper (bound function to preserve 'this' context)
// ============================================================================

const fetchAssets = async (params: any) => {
  const response = await searchAssetsForList(params)
  searchAggregations.value = response.aggregations || {}
  return response
}

// ============================================================================
// CRUD Composable
// ============================================================================

const { 
  handleDelete: crudDelete,
  handleBatchDelete: crudBatchDelete,
  handleExport: crudExport,
  handleBatchExport: crudBatchExport
} = useCrud({
  name: t('assets.detail.title'), // Use a generic name or "Asset"
  api: {
    list: assetApi.list,
    delete: (id: string | number) => assetApi.delete(String(id)),
    batchDelete: (ids: (string | number)[]) => assetApi.batchDelete(ids.map((id) => String(id))),
    export: (params: any) => {
      // Adapter for assetApi.export which expects assetIds for batch
      if (params && params.ids) {
        return assetApi.export({ ...params, assetIds: params.ids })
      }
      return assetApi.export(params)
    }
  }
})

// Wrappers or Direct usage
const handleDelete = (row: Asset) => crudDelete(row).then((success) => {
  if (success) refreshList()
})

const handleExport = (ids?: any[]) => crudExport(ids as any)

// ============================================================================
// Table Columns
// ============================================================================

const columns = computed<TableColumn[]>(() => [
  { prop: 'assetCode', label: t('assets.fields.assetCode'), width: 140, fixed: 'left', slot: true },
  { prop: 'assetName', label: t('assets.fields.assetName'), minWidth: 180, slot: true },
  { prop: 'assetCategoryName', label: t('assets.fields.category'), width: 120, tagType: () => 'info', format: (value: any) => value || '-' },
  { prop: 'purchasePrice', label: t('assets.fields.purchasePrice'), width: 120, align: 'right' },
  { prop: 'purchaseDate', label: t('assets.fields.purchaseDate'), width: 120 },
  { prop: 'locationPath', label: t('assets.fields.location'), width: 140 },
  { prop: 'custodianName', label: t('assets.fields.user'), width: 100 },
  { prop: 'assetStatus', label: t('common.labels.status'), width: 100, tagType: (row: any) => getStatusType(row.assetStatus), format: (value: any, row: any) => row?.statusLabel || getStatusLabel(value), fixed: 'right' },
  // Hidden columns (available in settings)
  { prop: 'brand', label: t('assets.fields.brand'), width: 120, visible: false },
  { prop: 'model', label: t('assets.fields.model'), width: 120, visible: false },
  { prop: 'serialNumber', label: t('assets.fields.serialNumber'), width: 140, visible: false },
  { prop: 'supplierName', label: t('assets.fields.supplier'), width: 150, visible: false },
  { prop: 'departmentName', label: t('assets.fields.department'), width: 120, visible: false },
  { prop: 'currentValue', label: t('assets.fields.currentValue'), width: 120, visible: false, type: 'currency' },
  { prop: 'usefulLife', label: t('assets.fields.usefulLife'), width: 100, visible: false },
  { prop: 'remarks', label: t('common.labels.remark'), minWidth: 200, visible: false }
])

// ============================================================================
// Search Fields
// ============================================================================

const searchFields = computed<SearchField[]>(() => [
  {
    prop: 'search',
    label: t('assets.search.keyword'),
    type: 'slot',
    placeholder: t('assets.search.keywordPlaceholder')
  },
  {
    prop: 'categoryId',
    label: t('assets.fields.category'),
    type: 'select',
    options: categoryOptions.value,
    multiple: true
  },
  {
    prop: 'status',
    label: t('assets.search.status'),
    type: 'select',
    options: [
      { label: t('assets.status.inUse'), value: 'in_use' },
      { label: t('assets.status.idle'), value: 'idle' },
      { label: t('assets.status.maintenance'), value: 'maintenance' },
      { label: t('assets.status.scrapped'), value: 'scrapped' },
      { label: t('assets.status.draft'), value: 'draft' }
    ]
  },
  {
    prop: 'locationId',
    label: t('assets.fields.location'),
    type: 'select',
    options: [] // Will be loaded from API
  },
  {
    prop: 'purchaseDateRange',
    label: t('assets.search.dateRange'),
    type: 'daterange'
  }
])

// ============================================================================
// Batch Actions
// ============================================================================

const batchActions = computed(() => [
  {
    label: t('assets.list.batchDelete'),
    type: 'danger' as const,
    action: async (rows: Asset[]) => {
      const success = await crudBatchDelete(rows)
      if (success) refreshList()
    }
  },
  {
    label: t('assets.list.batchExport'),
    type: 'primary' as const,
    action: (rows: Asset[]) => crudBatchExport(rows)
  }
])

const buildSearchFiltersFromForm = (form: Record<string, any>) => {
  const filters: Record<string, any> = {}

  if (form.categoryId) filters.category = form.categoryId
  if (form.status) filters.status = form.status
  if (form.locationId) filters.location = form.locationId

  if (Array.isArray(form.purchaseDateRange)) {
    if (form.purchaseDateRange[0]) filters.purchaseDateFrom = form.purchaseDateRange[0]
    if (form.purchaseDateRange[1]) filters.purchaseDateTo = form.purchaseDateRange[1]
  }

  return filters
}

const applySearchPayload = (
  payload: { keyword?: string; filters?: Record<string, any> },
  setValue: (key: string, value: any) => void,
  search: () => void
) => {
  const filters = payload.filters || {}
  setValue('search', payload.keyword || '')
  setValue('categoryId', filters.category ?? undefined)
  setValue('status', filters.status ?? undefined)
  setValue('locationId', filters.location ?? undefined)

  if (filters.purchaseDateFrom || filters.purchaseDateTo) {
    setValue('purchaseDateRange', [
      filters.purchaseDateFrom || '',
      filters.purchaseDateTo || '',
    ])
  } else {
    setValue('purchaseDateRange', undefined)
  }

  search()
}

const loadSavedSearches = async () => {
  const response = await getSavedSearches({ type: 'asset', limit: 20 })
  savedSearches.value = response.results || []
}

const handleSavedSearchVisibleChange = async (visible: boolean) => {
  if (!visible) return
  try {
    await loadSavedSearches()
  } catch (error) {
    ElMessage.error(t('common.messages.loadFailed'))
  }
}

const handleSavedSearchCommand = async (
  id: string,
  setValue: (key: string, value: any) => void,
  search: () => void
) => {
  try {
    const savedSearch = await useSavedSearch(id)
    applySearchPayload(savedSearch, setValue, search)
  } catch (error: any) {
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  }
}

const loadSmartSuggestions = async (
  queryString: string,
  callback: (items: Array<Record<string, any>>) => void
) => {
  try {
    if (!queryString.trim()) {
      const history = await getSearchHistory({ type: 'asset', limit: 5 })
      callback(
        (history.results || []).map((item) => ({
          value: item.keyword,
          label: item.keyword,
          meta: t('assets.search.historySuggestion', { count: item.searchCount }),
          filters: item.filters,
          type: 'history',
        }))
      )
      return
    }

    const suggestions = await getSearchSuggestions({
      keyword: queryString,
      type: 'asset',
      limit: 8,
    })
    callback(
      suggestions.map((item) => ({
        value: item.suggestion,
        label: item.suggestion,
        meta: t('assets.search.resultCount', { count: item.count }),
        type: 'suggestion',
      }))
    )
  } catch (error) {
    callback([])
  }
}

const handleSuggestionSelect = (
  item: SmartSearchSuggestionOption,
  setValue: (key: string, value: any) => void,
  search: () => void
) => {
  applySearchPayload(
    {
      keyword: String(item.value || item.label || ''),
      filters: item.filters || {},
    },
    setValue,
    search
  )
}

const saveCurrentSearch = async (form: Record<string, any>) => {
  const keyword = String(form.search || '').trim()
  const filters = buildSearchFiltersFromForm(form)

  if (!keyword && Object.keys(filters).length === 0) {
    ElMessage.warning(t('assets.search.saveValidation'))
    return
  }

  try {
    const { value } = await ElMessageBox.prompt(
      t('assets.search.saveNamePrompt'),
      t('assets.search.saveNameTitle'),
      {
        inputPattern: /\S+/,
        inputErrorMessage: t('assets.search.saveNameRequired'),
      }
    )

    await createSavedSearch({
      name: value,
      searchType: 'asset',
      keyword,
      filters,
      isShared: false,
    })
    ElMessage.success(t('common.messages.saveSuccess'))
    await loadSavedSearches()
  } catch (error: any) {
    if (error === 'cancel' || error === 'close' || error?.message === 'cancel') {
      return
    }
    ElMessage.error(error?.message || t('common.messages.operationFailed'))
  }
}

const aggregationChips = computed(() => {
  const chips: Array<{ key: string; field: string; value: string; count: number; label: string }> = []
  const categoryLabels = searchAggregations.value.categoryLabels || {}

  Object.entries(searchAggregations.value.status || {})
    .slice(0, 3)
    .forEach(([status, count]) => {
      chips.push({
        key: `status-${status}`,
        field: 'status',
        value: String(status),
        count: Number(count),
        label: getStatusLabel(String(status) as AssetStatus),
      })
    })

  Object.entries(searchAggregations.value.category || {})
    .slice(0, 3)
    .forEach(([categoryId, count]) => {
      chips.push({
        key: `category-${categoryId}`,
        field: 'categoryId',
        value: String(categoryId),
        count: Number(count),
        label: categoryLabels[categoryId] || String(categoryId),
      })
    })

  return chips
})

const applyAggregationChip = (
  chip: { field: string; value: string },
  setValue: (key: string, value: any) => void,
  search: () => void
) => {
  setValue(chip.field, chip.value)
  search()
}

// ============================================================================
// Methods
// ============================================================================

/**
 * Get status tag type
 */
const getStatusType = (status: AssetStatus) => {
  const typeMap: Record<AssetStatus, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    draft: 'info',
    in_use: 'success',
    idle: 'warning',
    maintenance: 'danger',
    scrapped: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * Get status label
 */
const getStatusLabel = (status: AssetStatus) => {
  const keyMap: Record<AssetStatus, string> = {
    draft: 'assets.status.draft',
    in_use: 'assets.status.inUse',
    idle: 'assets.status.idle',
    maintenance: 'assets.status.maintenance',
    scrapped: 'assets.status.scrapped'
  }
  return keyMap[status] ? t(keyMap[status]) : status
}

/**
 * Load category options
 */
const loadCategories = async () => {
  try {
    const res: any = await categoryApi.list()
    // Handle both array and paginated response
    const categories = Array.isArray(res) ? res : (res.results || [])
    
    categoryOptions.value = categories.map((cat: any) => ({
      label: cat.name,
      value: cat.id
    }))
    
    // Note: Since searchFields is computed, we don't need to manually update it anymore
    // strict reactivity will handle it, provided searchFields depends on categoryOptions.value using computed
    // But currently searchFields is a computed that returns a new array, it should be fine.
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

/**
 * Handle row click
 */
const handleRowClick = (row: Asset) => {
  handleView(row)
}

/**
 * Handle create button click
 */
const handleCreate = () => {
  router.push('/assets/create')
}

/**
 * Handle view button click
 */
const handleView = (row: Asset) => {
  router.push(`/assets/${row.id}`)
}

/**
 * Handle edit button click
 */
const handleEdit = (row: Asset) => {
  router.push(`/assets/${row.id}?action=edit`)
}

/**
 * Refresh list
 */
const refreshList = () => {
  // Emit custom event that BaseListPage will catch
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadCategories()
  loadSavedSearches().catch(() => undefined)
})
</script>

<style scoped lang="scss">
.asset-list-page {
  height: 100%;
}

.smart-search-field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.smart-search-field__row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.smart-search-field__row :deep(.el-autocomplete) {
  flex: 1;
}

.smart-search-field__aggregations {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.smart-search-field__aggregations-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.smart-search-field__chip {
  cursor: pointer;
}

.smart-search-suggestion {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.smart-search-suggestion__label {
  font-weight: 600;
}

.smart-search-suggestion__meta,
.saved-search-option__meta {
  color: #64748b;
  font-size: 12px;
}

.saved-search-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.selection-info {
  margin-right: 16px;
  color: #409eff;
  font-size: 14px;
}
</style>
