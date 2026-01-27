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
      class="asset-select"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <el-option
        v-for="asset in assetOptions"
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
import { ref, computed, onMounted } from 'vue'
import { getAssets } from '@/api/assets'

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

const placeholder = computed(() => {
  return props.placeholder || `请选择${props.field.name}`
})

// Search assets asynchronously
const searchAssets = async (query = '') => {
  loading.value = true
  try {
    const params = {
      search: query || '',
      page_size: 50,
      is_deleted: false
    }

    const response = await getAssets(params)

    if (response.success && response.data) {
      assetOptions.value = (response.data.results || response.data).map(asset => ({
        id: asset.id,
        value: asset.id,
        code: asset.code || '',
        name: asset.name || '',
        label: `${asset.code || ''} - ${asset.name || ''}`
      }))
    }
  } catch (error) {
    console.error('Failed to load assets:', error)
    assetOptions.value = []
  } finally {
    loading.value = false
  }
}

// Load initial options on mount
onMounted(() => {
  searchAssets()
})
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
