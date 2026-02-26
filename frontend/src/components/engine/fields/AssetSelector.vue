<template>
  <div class="asset-selector">
    <el-select
      :model-value="modelValue"
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
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <el-option
        v-for="asset in allAssetOptions"
        :key="asset.id"
        :label="asset.label"
        :value="asset.value"
      >
        <div class="asset-option">
          <span class="asset-code">{{ asset.code }}</span>
          <span class="asset-name">{{ asset.name }}</span>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'
import { referenceResolver } from '@/platform/reference/referenceResolver'

const { t } = useI18n()

const props = defineProps({
  field: Object,
  modelValue: [String, Number, Array],
  formData: Object,
  disabled: Boolean,
  placeholder: String,
  multiple: { type: Boolean, default: false }
})

defineEmits(['update:modelValue'])

const loading = ref(false)
const assetOptions = ref([])
const currentAssets = ref([])

const placeholder = computed(() => {
  return props.placeholder || t('assets.selector.selectAsset')
})

// Combine search results with current selected assets
const allAssetOptions = computed(() => {
  const result = [...assetOptions.value]
  // Add current assets if not in options
  if (currentAssets.value.length > 0) {
    currentAssets.value.forEach(asset => {
      if (!result.find(o => o.id === asset.id)) {
        result.push(asset)
      }
    })
  }
  return result
})

// Search assets asynchronously
const searchAssets = async (query = '') => {
  loading.value = true
  try {
    const data = await request.get('/system/objects/Asset/', {
      params: {
        search: query || '',
        page: 1,
        page_size: 50,
        is_deleted: false
      },
      silent: true
    })

    const results = data?.results || []
    assetOptions.value = results.map((asset) => {
      const code = asset.code || asset.assetCode || asset.asset_code || ''
      const name = asset.name || asset.assetName || asset.asset_name || ''
      return {
        id: asset.id,
        value: asset.id,
        code,
        name,
        label: `${code || ''} - ${name || ''}`.trim()
      }
    })
  } catch (error) {
    console.error('Failed to load assets:', error)
    assetOptions.value = []
  } finally {
    loading.value = false
  }
}

const handleVisibleChange = (visible) => {
  if (!visible) return
  if (props.disabled) return
  if (loading.value) return
  if ((assetOptions.value || []).length > 0) return
  searchAssets('')
}

// Fetch current selected assets by IDs for display
const fetchCurrentAssets = async () => {
  const ids = Array.isArray(props.modelValue)
    ? props.modelValue
    : props.modelValue ? [props.modelValue] : []

  if (ids.length === 0) return

  loading.value = true
  try {
    const items = await Promise.all(
      ids.map(async (id) => {
        const strId = String(id)
        const asset = await referenceResolver.resolve({ objectCode: 'Asset', id: strId })
        if (!asset) return null
        const code = asset.code || asset.assetCode || asset.asset_code || ''
        const name = asset.name || asset.assetName || asset.asset_name || ''
        return {
          id: asset.id,
          value: asset.id,
          code,
          name,
          label: `${code || ''} - ${name || ''}`.trim()
        }
      })
    )
    currentAssets.value = items.filter(Boolean)
  } catch (e) {
    console.error('Failed to fetch current assets:', e)
  } finally {
    loading.value = false
  }
}

// Watch for model value changes
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    fetchCurrentAssets()
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
  align-items: center;
  gap: 8px;
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
