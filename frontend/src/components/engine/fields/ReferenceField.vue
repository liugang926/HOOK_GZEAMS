<template>
  <div class="reference-field">
    <el-select
      ref="selectRef"
      :model-value="normalizedValue"
      :multiple="isMultiple"
      :placeholder="placeholder"
      :disabled="disabled"
      :remote="true"
      :reserve-keyword="false"
      :remote-method="debouncedSearch"
      :loading="loading"
      :no-match-text="noMatchText"
      filterable
      clearable
      value-key="id"
      style="width: 100%"
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
            <span class="reference-option__flag">{{ recentItemFlag }}</span>
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
            <span class="reference-option__flag">{{ searchItemFlag }}</span>
          </div>
        </el-option>
      </el-option-group>

      <template #empty>
        <div class="reference-empty">
          {{ emptyText }}
        </div>
      </template>

      <template #footer>
        <div
          v-if="!disabled"
          class="reference-dropdown-footer"
          @mousedown.prevent
        >
          <button
            type="button"
            class="reference-dropdown-footer__action is-primary"
            @click.stop="handleDropdownAdvancedLookup"
          >
            {{ advancedLookupText }}
          </button>
          <button
            v-if="allowCreateRecord"
            type="button"
            class="reference-dropdown-footer__action"
            @click.stop="handleDropdownCreateRecord"
          >
            {{ createRecordText }}
          </button>
        </div>
      </template>
    </el-select>

    <el-popover
      v-if="selectedSingleOption && !isMultiple"
      trigger="hover"
      placement="top-start"
      :width="320"
    >
      <template #reference>
        <div class="reference-selected">
          <ObjectAvatar
            :object-code="referenceObjectCode || 'Ref'"
            size="xs"
          />
          <div class="reference-selected__content">
            <span class="reference-selected__label">{{ getItemLabel(selectedSingleOption) }}</span>
            <span class="reference-selected__secondary">
              {{ getItemSecondary(selectedSingleOption) || selectedSingleOption.id }}
            </span>
          </div>
          <el-link
            v-if="selectedSingleHref"
            :href="selectedSingleHref"
            target="_blank"
            type="primary"
          >
            {{ openActionText }}
          </el-link>
        </div>
      </template>
      <div class="reference-hover-card">
        <div class="reference-hover-card__header">
          <ObjectAvatar
            :object-code="referenceObjectCode || 'Ref'"
            size="sm"
          />
          <div class="reference-hover-card__content">
            <span class="reference-hover-card__title">{{ getItemLabel(selectedSingleOption) }}</span>
            <span class="reference-hover-card__subtitle">
              {{ getItemSecondary(selectedSingleOption) || selectedSingleOption.id }}
            </span>
          </div>
          <el-tag
            v-if="referenceObjectCode"
            size="small"
            effect="plain"
          >
            {{ referenceObjectCode }}
          </el-tag>
        </div>
        <div class="reference-hover-card__meta">
          <span class="reference-hover-card__meta-label">{{ idLabel }}</span>
          <span class="reference-hover-card__meta-value">{{ selectedSingleOption.id }}</span>
        </div>
        <div class="reference-hover-card__actions">
          <el-link
            v-if="selectedSingleHref"
            :href="selectedSingleHref"
            target="_blank"
            type="primary"
          >
            {{ openActionText }}
          </el-link>
          <el-link
            type="primary"
            @click.prevent="openLookupDialog"
          >
            {{ advancedLookupText }}
          </el-link>
        </div>
      </div>
    </el-popover>

    <ReferenceLookupDialog
      v-model="lookupDialogVisible"
      :object-code="referenceObjectCode"
      :display-field="displayField"
      :secondary-field="secondaryField"
      :multiple="isMultiple"
      :selected-ids="selectedIdsForDialog"
      :allow-create="allowCreateRecord"
      @confirm="handleLookupConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { searchReferenceData } from '@/api/system'
import { debounce } from 'lodash-es'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'
import ReferenceLookupDialog from './ReferenceLookupDialog.vue'
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

type AnyRecord = Record<string, any>

const props = defineProps({
  field: Object,
  // Detail endpoints may return expanded objects; edit submits IDs.
  modelValue: [String, Number, Object, Array],
  disabled: Boolean,
  placeholder: String
})

const emit = defineEmits(['update:modelValue', 'change'])
const { t } = useI18n()

const selectRef = ref<any>(null)
const loadingSearch = ref(false)
const loadingRecent = ref(false)
const searchOptions = ref<AnyRecord[]>([])
const recentOptions = ref<AnyRecord[]>([])
const currentValueObjects = ref<AnyRecord[]>([])
const searchKeyword = ref('')
const lookupDialogVisible = ref(false)

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

const recentItemFlag = computed(() => tr('common.recent', 'Recent'))
const searchItemFlag = computed(() => tr('common.labels.searchResult', 'Result'))
const idLabel = computed(() => tr('common.columns.id', 'ID'))
const openActionText = computed(() => tr('common.actions.open', 'Open'))
const advancedLookupText = computed(() => tr('common.actions.advancedSearch', 'Advanced Search'))
const createRecordText = computed(() => tr('common.actions.newRecord', 'New Record'))

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

const selectedSingleHref = computed(() => {
  if (!selectedSingleOption.value?.id || !referenceObjectCode.value) return ''
  return `/objects/${referenceObjectCode.value}/${encodeURIComponent(selectedSingleOption.value.id)}`
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
  const recentIds = loadRecentReferenceIds(referenceObjectCode.value, { limit: 8 })
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
  saveRecentReferenceIds(referenceObjectCode.value, ids, { limit: 10 })
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
  }
)
</script>

<style scoped lang="scss">
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
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.reference-option__secondary {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-option__flag {
  color: var(--el-text-color-placeholder);
  font-size: 11px;
  line-height: 18px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 0 8px;
  white-space: nowrap;
}

.reference-empty {
  padding: 10px 12px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.reference-dropdown-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.reference-dropdown-footer__action {
  border: 0;
  background: transparent;
  color: var(--el-text-color-regular);
  font-size: 12px;
  line-height: 18px;
  padding: 2px 4px;
  cursor: pointer;
}

.reference-dropdown-footer__action:hover {
  color: var(--el-color-primary);
}

.reference-dropdown-footer__action.is-primary {
  color: var(--el-color-primary);
  font-weight: 500;
}

.reference-selected {
  margin-top: 8px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 8px 10px;
  background: var(--el-fill-color-blank);
  display: flex;
  align-items: center;
  gap: 10px;
}

.reference-selected__content {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 2px;
}

.reference-selected__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-primary);
  font-weight: 500;
}

.reference-selected__secondary {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.reference-hover-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reference-hover-card__header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.reference-hover-card__content {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.reference-hover-card__title {
  color: var(--el-text-color-primary);
  font-size: 14px;
  font-weight: 600;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-hover-card__subtitle {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reference-hover-card__meta {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.reference-hover-card__meta-label {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.reference-hover-card__meta-value {
  color: var(--el-text-color-regular);
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  padding: 1px 6px;
}

.reference-hover-card__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
