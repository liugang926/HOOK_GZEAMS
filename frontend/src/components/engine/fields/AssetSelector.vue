<template>
  <div class="asset-selector">
    <el-select
      :model-value="selectValue"
      :disabled="disabled"
      :placeholder="placeholder"
      :multiple="multiple"
      :remote="true"
      :remote-method="searchAssets"
      :loading="loading"
      :clearable="true"
      filterable
      value-key="id"
      class="asset-select"
      @visible-change="handleVisibleChange"
      @update:model-value="handleModelValueUpdate"
    >
      <el-option
        v-for="asset in allAssetOptions"
        :key="asset.id"
        :label="asset.label"
        :value="asset.value"
      >
        <div class="asset-option">
          <div class="asset-option__main">
            <span class="asset-code">{{ asset.code }}</span>
            <span class="asset-name">{{ asset.name }}</span>
          </div>
          <div class="asset-option__meta">
            <span v-if="asset.specification">{{ asset.specification }}</span>
            <span v-if="asset.locationPath">{{ asset.locationPath }}</span>
          </div>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { referenceResolver } from '@/platform/reference/referenceResolver'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const userStore = useUserStore()

type AnyRecord = Record<string, any>
type AssetOption = {
  id: string
  value: string
  code: string
  name: string
  label: string
  specification: string
  location: string
  locationPath: string
  custodian: string
  custodianUsername: string
  department: string
  assetStatus: string
  raw: AnyRecord
}

const props = defineProps({
  field: { type: Object, default: () => ({}) },
  modelValue: [String, Number, Object, Array],
  formData: { type: Object, default: () => ({}) },
  disabled: Boolean,
  placeholder: String,
  multiple: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const assetOptions = ref<AssetOption[]>([])
const currentAssets = ref<AssetOption[]>([])

const fieldComponentProps = computed<AnyRecord>(() => {
  const field = (props.field || {}) as AnyRecord
  return {
    ...(field.component_props || {}),
    ...(field.componentProps || {})
  }
})

const parentContext = computed<AnyRecord>(() => {
  const formData = (props.formData || {}) as AnyRecord
  return (formData.__parent || formData) as AnyRecord
})

const rowContext = computed<AnyRecord | null>(() => {
  const formData = (props.formData || {}) as AnyRecord
  return (formData.__row || null) as AnyRecord | null
})

const rowCollection = computed<AnyRecord[]>(() => {
  const formData = (props.formData || {}) as AnyRecord
  return Array.isArray(formData.__rows) ? formData.__rows : []
})

const placeholder = computed(() => {
  return props.placeholder || t('assets.selector.selectAsset')
})

const readFirstValue = (source: AnyRecord | null | undefined, keys: string[]): any => {
  if (!source || typeof source !== 'object') return undefined
  for (const key of keys) {
    if (source[key] !== undefined && source[key] !== null && source[key] !== '') {
      return source[key]
    }
  }
  return undefined
}

const normalizeId = (value: unknown): string => {
  if (value === null || value === undefined || value === '') return ''
  if (typeof value === 'object') {
    const record = value as AnyRecord
    return String(record.id || record.value || record.code || '')
  }
  return String(value)
}

const resolveAssetId = (value: unknown): string => {
  return normalizeId(value)
}

const normalizeAssetRecord = (asset: AnyRecord): AssetOption | null => {
  const id = normalizeId(asset?.id)
  if (!id) return null

  const code = String(readFirstValue(asset, ['assetCode', 'asset_code', 'code']) || '')
  const name = String(readFirstValue(asset, ['assetName', 'asset_name', 'name']) || '')
  const specification = String(readFirstValue(asset, ['specification']) || '')
  const location = normalizeId(readFirstValue(asset, ['location']))
  const locationPath = String(readFirstValue(asset, ['locationPath', 'location_path']) || '')
  const custodian = normalizeId(readFirstValue(asset, ['custodian']))
  const custodianUsername = String(readFirstValue(asset, ['custodianUsername', 'custodian_username']) || '')
  const department = normalizeId(readFirstValue(asset, ['department']))
  const assetStatus = String(readFirstValue(asset, ['assetStatus', 'asset_status']) || '')
  const labelParts = [code, name].filter(Boolean)

  return {
    id,
    value: id,
    code,
    name,
    label: labelParts.length > 0 ? labelParts.join(' - ') : id,
    specification,
    location,
    locationPath,
    custodian,
    custodianUsername,
    department,
    assetStatus,
    raw: asset
  }
}

const extractResults = (payload: AnyRecord): AnyRecord[] => {
  if (Array.isArray(payload?.results)) return payload.results
  if (Array.isArray(payload?.data?.results)) return payload.data.results
  if (Array.isArray(payload?.data)) return payload.data
  return []
}

const currentSelectionIds = computed<string[]>(() => {
  if (Array.isArray(props.modelValue)) {
    return props.modelValue.map((value) => resolveAssetId(value)).filter(Boolean)
  }
  const id = resolveAssetId(props.modelValue)
  return id ? [id] : []
})

const selectedSiblingAssetIds = computed<Set<string>>(() => {
  const ids = new Set<string>()
  const currentRow = rowContext.value
  for (const row of rowCollection.value) {
    if (!row || row === currentRow) continue
    const id = resolveAssetId(row.asset)
    if (id) ids.add(id)
  }
  return ids
})

// Combine search results with current selected assets
const allAssetOptions = computed(() => {
  const result = [...assetOptions.value]
  for (const asset of currentAssets.value) {
    if (!result.find((option) => option.id === asset.id)) {
      result.push(asset)
    }
  }

  const currentIds = new Set(currentSelectionIds.value)
  return result.filter((asset) => {
    if (currentIds.has(asset.id)) return true
    return !selectedSiblingAssetIds.value.has(asset.id)
  })
})

const selectValue = computed(() => {
  if (props.multiple) {
    return currentSelectionIds.value
  }
  return currentSelectionIds.value[0] || null
})

const resolveContextValue = (source: unknown): unknown => {
  if (Array.isArray(source)) {
    for (const item of source) {
      const resolved = resolveContextValue(item)
      if (resolved !== undefined && resolved !== null && resolved !== '') return resolved
    }
    return undefined
  }

  if (typeof source === 'string') {
    if (source === '$currentUser') {
      return userStore.userInfo?.id || undefined
    }
    return readFirstValue(parentContext.value, [source, source.replace(/_([a-z])/g, (_, char) => char.toUpperCase())])
  }

  if (source && typeof source === 'object') {
    const config = source as AnyRecord
    if (config.value !== undefined) return config.value
    const resolvedFromParent = config.fromParent !== undefined
      ? resolveContextValue(config.fromParent)
      : undefined
    if (resolvedFromParent !== undefined && resolvedFromParent !== null && resolvedFromParent !== '') {
      return resolvedFromParent
    }
    if (config.fallback !== undefined) {
      return resolveContextValue(config.fallback)
    }
  }

  return source
}

const buildQueryParams = (query = ''): AnyRecord => {
  const filters = (fieldComponentProps.value.filters || fieldComponentProps.value.filter || {}) as AnyRecord
  const params: AnyRecord = {
    page: 1,
    page_size: 20,
    is_deleted: false
  }

  const trimmedQuery = String(query || '').trim()
  if (trimmedQuery.length >= 2 || trimmedQuery.length === 0) {
    params.search = trimmedQuery
  }

  const assetStatus = resolveContextValue(filters.assetStatus || filters.asset_status)
  const department = resolveContextValue(filters.department)
  const custodian = resolveContextValue(filters.custodian)
  const location = resolveContextValue(filters.location)

  if (assetStatus) params.asset_status = assetStatus
  if (department) params.department = normalizeId(department)
  if (custodian) params.custodian = normalizeId(custodian)
  if (location) params.location = normalizeId(location)

  return params
}

const searchAssets = async (query = '') => {
  const trimmedQuery = String(query || '').trim()
  if (trimmedQuery.length > 0 && trimmedQuery.length < 2) {
    assetOptions.value = []
    return
  }

  loading.value = true
  try {
    const response = await request.get('/system/objects/Asset/', {
      params: {
        ...buildQueryParams(trimmedQuery)
      },
      silent: true
    })

    assetOptions.value = extractResults(response)
      .map((asset) => normalizeAssetRecord(asset))
      .filter((asset): asset is AssetOption => !!asset)
  } catch (error) {
    console.error('Failed to load assets:', error)
    assetOptions.value = []
  } finally {
    loading.value = false
  }
}

const resolveAssetMappingValue = (asset: AssetOption, sourceKey: string): unknown => {
  if (!sourceKey) return undefined
  const raw = asset.raw || {}
  const normalizedKey = String(sourceKey).trim()

  const aliases: Record<string, string[]> = {
    assetCode: ['assetCode', 'asset_code', 'code'],
    assetName: ['assetName', 'asset_name', 'name'],
    specification: ['specification'],
    location: ['location'],
    locationPath: ['locationPath', 'location_path'],
    custodian: ['custodian'],
    custodianUsername: ['custodianUsername', 'custodian_username'],
    department: ['department'],
    assetStatus: ['assetStatus', 'asset_status']
  }

  const candidates = aliases[normalizedKey] || [normalizedKey]
  const value = readFirstValue(raw, candidates)
  return value !== undefined ? value : (asset as AnyRecord)[normalizedKey]
}

const applyAutofillMappings = (asset: AssetOption | null) => {
  if (!asset || !rowContext.value) return
  const mappings = (fieldComponentProps.value.autoFillMappings || fieldComponentProps.value.auto_fill_mappings || {}) as Record<string, string>
  for (const [sourceKey, targetKey] of Object.entries(mappings)) {
    if (!targetKey) continue
    rowContext.value[targetKey] = resolveAssetMappingValue(asset, sourceKey)
  }
}

const isDuplicateSelection = (value: unknown): boolean => {
  const nextId = resolveAssetId(value)
  if (!nextId) return false
  return selectedSiblingAssetIds.value.has(nextId)
}

const handleModelValueUpdate = (value: unknown) => {
  if (!props.multiple && isDuplicateSelection(value)) {
    ElMessage.warning('This asset is already selected in another row.')
    return
  }

  const selected = allAssetOptions.value.find((asset) => asset.id === resolveAssetId(value)) || null
  emit('update:modelValue', value)
  applyAutofillMappings(selected)
}

const handleVisibleChange = (visible: boolean) => {
  if (!visible) return
  if (props.disabled) return
  if (loading.value) return
  if (assetOptions.value.length > 0) return
  searchAssets('')
}

const fetchCurrentAssets = async () => {
  const rawValues = Array.isArray(props.modelValue)
    ? props.modelValue
    : (props.modelValue ? [props.modelValue] : [])

  if (rawValues.length === 0) {
    currentAssets.value = []
    return
  }

  loading.value = true
  try {
    const items = await Promise.all(
      rawValues.map(async (value) => {
        if (value && typeof value === 'object') {
          return normalizeAssetRecord(value as AnyRecord)
        }

        const assetId = resolveAssetId(value)
        if (!assetId) return null
        const asset = await referenceResolver.resolve({ objectCode: 'Asset', id: assetId })
        return asset ? normalizeAssetRecord(asset as AnyRecord) : null
      })
    )
    currentAssets.value = items.filter((item): item is AssetOption => !!item)
    if (currentAssets.value.length > 0) {
      applyAutofillMappings(currentAssets.value[0])
    }
  } catch (e) {
    console.error('Failed to fetch current assets:', e)
    currentAssets.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    fetchCurrentAssets()
  } else {
    currentAssets.value = []
  }
}, { immediate: true })
</script>

<style scoped>
.asset-selector {
  width: 100%;
}

.asset-select {
  width: 100%;
}

.asset-option {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.asset-option__main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-option__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.asset-code {
  font-family: 'Monaco', 'Consolas', monospace;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.asset-name {
  color: var(--el-text-color-primary);
}
</style>
