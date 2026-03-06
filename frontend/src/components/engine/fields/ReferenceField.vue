<template>
  <div
    class="reference-field"
    :class="{ 'is-readonly': disabled }"
  >
    <!-- ── Edit Mode ──────────────────────────────────────────────────────── -->
    <el-select
      v-if="!disabled"
      ref="selectRef"
      :model-value="normalizedValue"
      :multiple="isMultiple"
      :placeholder="placeholder"
      :remote="true"
      :reserve-keyword="false"
      :remote-method="debouncedSearch"
      :loading="loading"
      :no-match-text="noMatchText"
      filterable
      clearable
      value-key="id"
      class="reference-select"
      @visible-change="handleVisibleChange"
      @update:model-value="handleUpdate"
    >
      <el-option-group
        v-if="recentGroupOptions.length > 0"
        :label="recentGroupLabel"
      >
        <el-option
          v-for="item in recentGroupOptions"
          :key="`recent-${item.id}`"
          :label="getItemLabel(item)"
          :value="item.id"
        >
          <div class="reference-option">
            <ObjectAvatar
              :object-code="referenceObjectCode || 'Ref'"
              size="xs"
            />
            <div class="reference-option__content">
              <span class="reference-option__label">{{ getItemLabel(item) }}</span>
              <span class="reference-option__secondary">
                {{ getItemSecondary(item) || item.id }}
              </span>
            </div>
          </div>
        </el-option>
      </el-option-group>

      <el-option-group
        v-if="searchGroupOptions.length > 0"
        :label="searchGroupLabel"
      >
        <el-option
          v-for="item in searchGroupOptions"
          :key="`search-${item.id}`"
          :label="getItemLabel(item)"
          :value="item.id"
        >
          <div class="reference-option">
            <ObjectAvatar
              :object-code="referenceObjectCode || 'Ref'"
              size="xs"
            />
            <div class="reference-option__content">
              <span class="reference-option__label">{{ getItemLabel(item) }}</span>
              <span class="reference-option__secondary">
                {{ getItemSecondary(item) || item.id }}
              </span>
            </div>
          </div>
        </el-option>
      </el-option-group>

      <template #empty>
        <div class="reference-empty">
          {{ emptyText }}
        </div>
      </template>

      <template #footer>
        <div class="reference-dropdown-footer">
          <button
            type="button"
            class="reference-dropdown-footer__action is-primary"
            @mousedown.prevent="handleDropdownAdvancedLookup"
          >
            <!-- {{ advancedLookupText }} -->
            <el-icon><Search /></el-icon> {{ advancedLookupText }}
          </button>
          <button
            v-if="allowCreateRecord"
            type="button"
            class="reference-dropdown-footer__action"
            @mousedown.prevent="handleDropdownCreateRecord"
          >
            <el-icon><Plus /></el-icon> {{ createRecordText }}
          </button>
        </div>
      </template>
    </el-select>

    <!-- ── Read Mode ──────────────────────────────────────────────────────── -->
    <div
      v-else
      class="reference-read-view"
    >
      <template v-if="isMultiple">
        <ReferenceRecordPill
          v-for="item in currentValueObjects"
          :key="item.id"
          :label="getItemLabel(item)"
          :secondary="getItemSecondary(item)"
          :href="buildRecordHref(item)"
          :object-code="referenceObjectCode"
          :record-id="item.id"
          :show-popover="false"
          :id-label="idLabel"
          :open-action-text="openActionText"
        />
        <span
          v-if="currentValueObjects.length === 0"
          class="reference-empty-text"
        >-</span>
      </template>
      <template v-else>
        <ReferenceRecordPill
          v-if="selectedSingleOption"
          :label="getItemLabel(selectedSingleOption)"
          :secondary="selectedSingleSecondary"
          :href="selectedSingleHref"
          :object-code="referenceObjectCode"
          :record-id="selectedSingleOption.id"
          :loading="hoverLoading"
          :meta-items="hoverMetaItems"
          :id-label="idLabel"
          :open-action-text="openActionText"
          @show="handleSinglePillShow"
        />
        <span
          v-else
          class="reference-empty-text"
        >-</span>
      </template>
    </div>

    <ReferenceLookupDialog
      v-model="lookupDialogVisible"
      :object-code="referenceObjectCode"
      :display-field="displayField"
      :secondary-field="secondaryField"
      :columns="lookupColumns"
      :preference-key="lookupPreferenceKey"
      :user-scope="lookupUserScope"
      :preference-scope="lookupPreferenceScopeId"
      :compact-keys="lookupCompactKeys"
      :multiple="isMultiple"
      :selected-ids="selectedIdsForDialog"
      :allow-create="allowCreateRecord"
      @confirm="handleLookupConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Search, Plus } from '@element-plus/icons-vue'
import { searchReferenceData } from '@/api/system'
import { createObjectClient } from '@/api/dynamic'
import { debounce } from 'lodash-es'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'
import ReferenceRecordPill from '@/components/common/ReferenceRecordPill.vue'
import ReferenceLookupDialog from './ReferenceLookupDialog.vue'
import { useUserStore } from '@/stores/user'
import { referenceResolver } from '@/platform/reference/referenceResolver'
import {
  extractReferenceIds,
  resolveReferenceDisplayField,
  resolveReferenceObjectCode,
  resolveReferenceSecondaryField,
  resolveReferenceLabel,
  resolveReferenceSecondaryText
} from '@/platform/reference/referenceFieldMeta'
import { loadRecentReferenceIds, saveRecentReferenceIds } from '@/platform/reference/referenceLookupRecent'
import {
  resolveReferenceLookupDefaultColumns,
  type ReferenceLookupColumnConfig
} from '@/platform/reference/referenceLookupColumnPresets'
import { buildReferenceLookupScopeId } from '@/platform/reference/referenceLookupScope'

type AnyRecord = Record<string, any>
type LookupColumnConfig = ReferenceLookupColumnConfig

const props = defineProps({
  field: Object,
  // Detail endpoints may return expanded objects; edit submits IDs.
  modelValue: [String, Number, Object, Array],
  disabled: Boolean,
  placeholder: String
})

const emit = defineEmits(['update:modelValue', 'change'])
const { t } = useI18n()
const userStore = useUserStore()
const route = useRoute()

const selectRef = ref<any>(null)
const loadingSearch = ref(false)
const loadingRecent = ref(false)
const searchOptions = ref<AnyRecord[]>([])
const recentOptions = ref<AnyRecord[]>([])
const currentValueObjects = ref<AnyRecord[]>([])
const searchKeyword = ref('')
const lookupDialogVisible = ref(false)

// Hover card state
const hoverLoading = ref(false)
const hoverData = ref<AnyRecord | null>(null)
const preloadedHoverIds = new Set<string>()

const tr = (key: string, fallback: string, params?: Record<string, any>) => {
  const text = t(key, params || {})
  return text === key ? fallback : text
}

const referenceField = computed(() => (props.field || {}) as AnyRecord)

const referenceObjectCode = computed(() => resolveReferenceObjectCode(referenceField.value))

const displayField = computed(() => {
  return resolveReferenceDisplayField(referenceField.value, 'name')
})

const secondaryField = computed(() => {
  return resolveReferenceSecondaryField(referenceField.value, 'code')
})

const isMultiple = computed(() => {
  const componentProps = (referenceField.value?.componentProps || referenceField.value?.component_props || {}) as AnyRecord
  if (typeof componentProps.multiple === 'boolean') return componentProps.multiple
  if (typeof referenceField.value?.multiple === 'boolean') return referenceField.value.multiple
  const fieldType = String(referenceField.value?.fieldType || referenceField.value?.field_type || '').toLowerCase()
  return fieldType.includes('multi')
})

const loading = computed(() => loadingSearch.value || loadingRecent.value)

const placeholder = computed(() => {
  if (props.placeholder) return props.placeholder
  const key = 'common.placeholders.search'
  const text = t(key)
  return text === key ? 'Search records' : text
})

const recentGroupLabel = computed(() => {
  return tr('common.recent', 'Recent')
})

const searchGroupLabel = computed(() => {
  return tr('common.labels.searchResults', 'Search Results')
})

const advancedLookupText = computed(() => tr('common.actions.advancedSearch', 'Advanced Search'))
const createRecordText = computed(() => tr('common.actions.newRecord', 'New Record'))
const idLabel = computed(() => tr('common.columns.id', 'ID'))
const openActionText = computed(() => tr('common.actions.open', 'Open'))

const noMatchText = computed(() => {
  if (loading.value) return tr('common.messages.loading', 'Loading...')
  return searchKeyword.value
    ? tr('common.messages.noMatchingRecords', 'No matching records')
    : tr('common.messages.noRecentRecords', 'No recent records')
})

const emptyText = computed(() => {
  if (loading.value) return tr('common.messages.loading', 'Loading...')
  if (searchKeyword.value) return tr('common.messages.noMatchingRecords', 'No matching records')
  return tr('common.messages.referenceLookupHint', 'Type to search or choose a recent record')
})

const allowCreateRecord = computed(() => {
  const componentProps = (referenceField.value?.componentProps || referenceField.value?.component_props || {}) as AnyRecord
  return componentProps.allowCreate !== false && componentProps.allow_create !== false
})

const defaultLookupColumns = computed<LookupColumnConfig[]>(() => {
  return resolveReferenceLookupDefaultColumns({
    objectCode: referenceObjectCode.value,
    displayField: displayField.value,
    secondaryField: secondaryField.value
  })
})

const lookupColumns = computed<LookupColumnConfig[]>(() => {
  const componentProps = (referenceField.value?.componentProps || referenceField.value?.component_props || {}) as AnyRecord
  const raw = componentProps.lookupColumns || componentProps.lookup_columns || []
  if (!Array.isArray(raw) || raw.length === 0) {
    return defaultLookupColumns.value
  }
  const normalized = raw
    .map((item) => {
      if (!item || typeof item !== 'object') return null
      const key = String((item as AnyRecord).key || '').trim()
      if (!key) return null
      const normalized: LookupColumnConfig = { key }
      const label = String((item as AnyRecord).label || '').trim()
      if (label) normalized.label = label
      const minWidth = Number((item as AnyRecord).minWidth ?? (item as AnyRecord).min_width)
      const width = Number((item as AnyRecord).width)
      if (Number.isFinite(minWidth) && minWidth > 0) normalized.minWidth = minWidth
      if (Number.isFinite(width) && width > 0) normalized.width = width
      return normalized
    })
    .filter((item): item is LookupColumnConfig => !!item)
  return normalized.length > 0 ? normalized : defaultLookupColumns.value
})

const lookupPreferenceKey = computed(() => {
  const field = referenceField.value
  return String(
    field.code ||
    field.fieldCode ||
    field.field_code ||
    field.prop ||
    field.name ||
    ''
  ).trim()
})

const hostObjectCode = computed(() => {
  const fromParam = route.params.code
  if (Array.isArray(fromParam)) return String(fromParam[0] || '').trim()
  if (fromParam) return String(fromParam).trim()

  const fromQuery = route.query.objectCode
  if (Array.isArray(fromQuery)) return String(fromQuery[0] || '').trim()
  if (fromQuery) return String(fromQuery).trim()
  return ''
})

const hostRecordId = computed(() => {
  const id = route.params.id
  if (Array.isArray(id)) return String(id[0] || '').trim()
  return String(id || '').trim()
})

const lookupPreferenceScopeId = computed(() => {
  return buildReferenceLookupScopeId({
    routeName: route.name,
    routePath: route.path,
    hostObjectCode: hostObjectCode.value,
    hostRecordId: hostRecordId.value,
    action: route.query.action,
    layoutId: route.query.layoutId,
    layoutMode: route.query.layoutType || route.query.mode
  })
})

const lookupUserScope = computed(() => {
  return String(userStore.userInfo?.id || 'anonymous').trim() || 'anonymous'
})

const lookupCompactKeys = computed<string[]>(() => {
  const componentProps = (referenceField.value?.componentProps || referenceField.value?.component_props || {}) as AnyRecord
  const raw = componentProps.lookupCompactKeys || componentProps.lookup_compact_keys || []
  if (!Array.isArray(raw)) return []
  return raw
    .map((item) => String(item || '').trim())
    .filter(Boolean)
})

const normalizedValue = computed(() => {
  const ids = extractReferenceIds(props.modelValue)
  if (isMultiple.value) return ids
  return ids[0] || ''
})

const normalizeOption = (input: unknown): AnyRecord | null => {
  if (!input || typeof input !== 'object') return null
  const raw = input as AnyRecord
  const id = String(raw.id || raw.pk || raw.value || '').trim()
  if (!id) return null
  return {
    ...raw,
    id
  }
}

const allOptions = computed(() => {
  const merged = [...recentOptions.value, ...searchOptions.value, ...currentValueObjects.value]
  const map = new Map<string, AnyRecord>()
  for (const item of merged) {
    const normalized = normalizeOption(item)
    if (!normalized) continue
    const existing = map.get(normalized.id)
    map.set(normalized.id, existing ? { ...normalized, ...existing } : normalized)
  }
  return Array.from(map.values())
})

const recentGroupOptions = computed(() => {
  const map = new Map(allOptions.value.map((item) => [item.id, item]))
  return recentOptions.value
    .map((item) => map.get(item.id))
    .filter((item): item is AnyRecord => !!item)
})

const searchGroupOptions = computed(() => {
  const recentIds = new Set(recentGroupOptions.value.map((item) => item.id))
  return allOptions.value.filter((item) => !recentIds.has(item.id))
})

const selectedSingleOption = computed<AnyRecord | null>(() => {
  if (isMultiple.value) return null
  const id = String(normalizedValue.value || '').trim()
  if (!id) return null
  return allOptions.value.find((item) => item.id === id) || null
})

const buildRecordHref = (item: AnyRecord): string => {
  const id = String(item?.id || '').trim()
  if (!id || !referenceObjectCode.value) return ''
  return `/objects/${referenceObjectCode.value}/${encodeURIComponent(id)}`
}

const selectedSingleHref = computed(() => {
  return selectedSingleOption.value ? buildRecordHref(selectedSingleOption.value) : ''
})

const selectedSingleSecondary = computed(() => {
  if (!selectedSingleOption.value) return ''
  return getItemSecondary(selectedSingleOption.value) || selectedSingleOption.value.id
})

const selectedIdsForDialog = computed(() => {
  const ids = normalizedValue.value
  if (Array.isArray(ids)) return ids.map((item) => String(item || '').trim()).filter(Boolean)
  const id = String(ids || '').trim()
  return id ? [id] : []
})

const getItemLabel = (item: AnyRecord) => {
  return resolveReferenceLabel(item, displayField.value) || String(item?.id || '')
}

const getItemSecondary = (item: AnyRecord) => {
  return resolveReferenceSecondaryText(item, secondaryField.value, displayField.value)
}

const loadRecentReferences = async () => {
  if (!referenceObjectCode.value) {
    recentOptions.value = []
    return
  }
  const recentIds = loadRecentReferenceIds(referenceObjectCode.value, {
    limit: 8,
    scope: lookupPreferenceScopeId.value
  })
  if (!recentIds.length) {
    recentOptions.value = []
    return
  }

  loadingRecent.value = true
  try {
    const resolved = await referenceResolver.resolveMany(referenceObjectCode.value, recentIds)
    recentOptions.value = recentIds
      .map((id) => normalizeOption(resolved[id]))
      .filter((item: AnyRecord | null): item is AnyRecord => !!item)
  } catch (error) {
    console.warn('Failed to load recent reference options:', error)
    recentOptions.value = []
  } finally {
    loadingRecent.value = false
  }
}

const saveRecentSelection = (ids: string[]) => {
  if (!referenceObjectCode.value || ids.length === 0) return
  saveRecentReferenceIds(referenceObjectCode.value, ids, {
    limit: 10,
    scope: lookupPreferenceScopeId.value
  })
}

const searchReference = async (query = '') => {
  searchKeyword.value = String(query || '').trim()
  if (!referenceObjectCode.value) return

  if (!searchKeyword.value) {
    searchOptions.value = []
    await loadRecentReferences()
    return
  }

  loadingSearch.value = true
  try {
    const res = await searchReferenceData({
      reference_object: referenceObjectCode.value,
      search: searchKeyword.value,
      page_size: 50
    })
    searchOptions.value = (res.results || res.items || [])
      .map((item: unknown) => normalizeOption(item))
      .filter((item: AnyRecord | null): item is AnyRecord => !!item)
  } finally {
    loadingSearch.value = false
  }
}

const debouncedSearch = debounce(searchReference, 300)

const handleVisibleChange = (visible: boolean) => {
  if (!visible) return
  // Avoid auto-loading in read-only/disabled mode. We only need to resolve the current value.
  if (props.disabled) return
  if (loadingSearch.value) return
  if (searchKeyword.value) {
    debouncedSearch(searchKeyword.value)
    return
  }
  if (recentOptions.value.length > 0) return
  loadRecentReferences()
}

const handleUpdate = (val: unknown) => {
  emit('update:modelValue', val)
  const selectedIds = (Array.isArray(val) ? val : [val])
    .map((item) => String(item || '').trim())
    .filter(Boolean)
  saveRecentSelection(selectedIds)

  const selectedObj = isMultiple.value
    ? allOptions.value.filter((item) => Array.isArray(val) && val.includes(item.id))
    : (allOptions.value.find((item) => item.id === val) || null)
  emit('change', selectedObj)
}

const closeSelectDropdown = () => {
  if (!selectRef.value) return
  if (typeof selectRef.value.blur === 'function') {
    selectRef.value.blur()
  }
}

const openLookupDialog = () => {
  if (!referenceObjectCode.value) return
  lookupDialogVisible.value = true
}

const openCreateRecord = () => {
  if (!allowCreateRecord.value || !referenceObjectCode.value) return
  if (typeof window === 'undefined') return
  window.open(`/objects/${referenceObjectCode.value}/create`, '_blank', 'noopener,noreferrer')
}

const handleDropdownAdvancedLookup = async () => {
  closeSelectDropdown()
  await nextTick()
  openLookupDialog()
}

const handleDropdownCreateRecord = async () => {
  closeSelectDropdown()
  await nextTick()
  openCreateRecord()
}

const handleLookupConfirm = (rows: AnyRecord[]) => {
  const normalizedRows = (rows || [])
    .map((item) => normalizeOption(item))
    .filter((item: AnyRecord | null): item is AnyRecord => !!item)
  const ids = normalizedRows
    .map((item) => item.id)
    .filter(Boolean)

  if (ids.length === 0) return

  saveRecentSelection(ids)
  currentValueObjects.value = Array.from(
    new Map([...currentValueObjects.value, ...normalizedRows].map((item) => [item.id, item])).values()
  )

  const nextValue = isMultiple.value ? ids : ids[0]
  emit('update:modelValue', nextValue)
  emit('change', isMultiple.value ? normalizedRows : normalizedRows[0])
}

const fetchCurrentValue = async () => {
  const ids = extractReferenceIds(props.modelValue)
  if (!ids.length || !referenceObjectCode.value) {
    currentValueObjects.value = []
    return
  }

  try {
    const resolved = await referenceResolver.resolveMany(referenceObjectCode.value, ids)
    currentValueObjects.value = ids
      .map((id) => normalizeOption(resolved[id]))
      .filter((item: AnyRecord | null): item is AnyRecord => !!item)
  } catch (error) {
    console.warn('Failed to fetch current value for reference field:', error)
  }
}

watch(
  () => [props.modelValue, referenceObjectCode.value],
  () => {
    fetchCurrentValue()
    if (!searchKeyword.value) loadRecentReferences()
  },
  { immediate: true, deep: true }
)

watch(
  () => referenceObjectCode.value,
  () => {
    searchOptions.value = []
    recentOptions.value = []
    searchKeyword.value = ''
    preloadedHoverIds.clear()
  }
)

// -- Hover Card Logic --
const displayCompactKeys = computed(() => {
  if (lookupCompactKeys.value.length > 0) return lookupCompactKeys.value
  // Fallback generic keys if none specified in compact keys
  return ['status', 'created_at', 'department_id', 'user_id']
})

const getFieldLabel = (key: string) => {
  // Ideally resolved from metadata, for now use generic formatting
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const getFieldValue = (data: AnyRecord, key: string) => {
  const val = data[key]
  if (val === null || val === undefined) return '-'
  if (typeof val === 'object') {
    return val.name || val.label || val.id || JSON.stringify(val)
  }
  return String(val)
}

const hoverMetaItems = computed(() => {
  if (!hoverData.value) return []
  return displayCompactKeys.value
    .map((key) => ({
      label: getFieldLabel(key),
      value: getFieldValue(hoverData.value as AnyRecord, key)
    }))
    .filter((item) => item.value !== '-')
})

const handleHoverShow = async (option: AnyRecord) => {
  if (!referenceObjectCode.value || !option?.id) return
  if (preloadedHoverIds.has(option.id) && hoverData.value?.id === option.id) return

  hoverLoading.value = true
  hoverData.value = null
  
  try {
    const client = createObjectClient(referenceObjectCode.value)
    const data = await client.get(option.id)
    if (data) {
      hoverData.value = data
      preloadedHoverIds.add(option.id)
    }
  } catch (err) {
    console.warn('Failed to load deep reference data for hover card', err)
    // Fallback to basic shallow data
    hoverData.value = { ...option }
  } finally {
    hoverLoading.value = false
  }
}

const handleSinglePillShow = () => {
  if (!selectedSingleOption.value) return
  handleHoverShow(selectedSingleOption.value)
}
</script>

<style scoped lang="scss">
.reference-field {
  width: 100%;
}
.reference-select {
  width: 100%;
}

/* Edit Mode Dropdown Option */
.reference-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.reference-option__content {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.reference-option__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
  font-weight: 500;
  line-height: 1.4;
}
.reference-option__secondary {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.2;
}

/* Dropdown Footer Actions */
.reference-empty {
  padding: 10px 12px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  text-align: center;
}
.reference-dropdown-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-blank);
}
.reference-dropdown-footer__action {
  border: 0;
  background: transparent;
  color: var(--el-text-color-regular);
  font-size: 13px;
  line-height: 1;
  padding: 4px 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}
.reference-dropdown-footer__action:hover {
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}
.reference-dropdown-footer__action.is-primary {
  color: var(--el-color-primary);
}

/* Read Mode (Salesforce Style Salesforce Lightning) */
.reference-read-view {
  min-height: 32px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.reference-read-item {
  display: inline-flex;
}
.reference-link {
  font-size: 14px;
  line-height: inherit;
  color: var(--el-color-primary);
  word-break: break-all;
  white-space: normal;
  text-align: left;
  display: inline-block;
}
.reference-link:hover {
  text-decoration: underline;
}
.reference-empty-text {
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

/* Popover Hover Card Professional Styling */
:global(.reference-popover) {
  padding: 0 !important;
  border-radius: var(--sys-radius-large) !important;
  box-shadow: var(--el-box-shadow-light) !important;
  border: 1px solid var(--sys-border-color) !important;
  overflow: hidden;
}

.reference-hover-card {
  display: flex;
  flex-direction: column;
}

.reference-hover-card__header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 16px 0;
}

.reference-hover-card__content {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.reference-hover-card__title {
  color: var(--sys-color-text-main);
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.3;
}

.reference-hover-card__subtitle {
  color: var(--sys-color-text-secondary);
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-hover-card__divider {
  margin: 12px 0 0 !important;
  border-color: var(--sys-border-light);
}

.reference-hover-card__body {
  padding: 12px 16px;
  background-color: var(--sys-color-bg-base);
  min-height: 80px;

  &.is-loading {
    display: flex;
    align-items: center;
  }
}

.reference-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.reference-meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.reference-meta-item__label {
  color: var(--sys-color-text-secondary);
  font-size: 12px;
}

.reference-meta-item__value {
  color: var(--sys-color-text-regular);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.reference-hover-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px 12px;
  background-color: var(--sys-color-bg-base);
}

.reference-hover-card__meta-value {
  color: var(--sys-color-text-secondary);
  font-size: 11px;
  font-family: 'Consolas', 'Monaco', monospace;
}
</style>
