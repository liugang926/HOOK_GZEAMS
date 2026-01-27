<template>
  <div class="reference-field">
    <el-select
      :model-value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :remote="true"
      :remote-method="searchReference"
      :loading="loading"
      filterable
      clearable
      value-key="id"
      style="width: 100%"
      @update:model-value="handleUpdate"
    >
      <el-option
        v-for="item in options"
        :key="item.id"
        :label="item[field.display_field || 'name']"
        :value="item.id"
      />
    </el-select>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { searchReferenceData } from '@/api/system'
import { debounce } from 'lodash-es'

const props = defineProps({
  field: Object,
  modelValue: [String, Number],
  disabled: Boolean,
  placeholder: String
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)
const options = ref([])

// 搜索方法
const searchReference = async (query) => {
  if (!props.field.reference_object) return
  
  loading.value = true
  try {
    const res = await searchReferenceData({
      reference_object: props.field.reference_object,
      search: query
    })
    options.value = res.results || res.items || []
  } finally {
    loading.value = false
  }
}

// 防抖搜索
const debouncedSearch = debounce(searchReference, 300)

const handleUpdate = (val) => {
  emit('update:modelValue', val)
  // Find the selected object and emit full change
  const selectedObj = options.value.find(o => o.id === val)
  emit('change', selectedObj)
}

// 初始加载 (如果有值，需要加载对应的选项)
// 这里简化处理，实际可能需要 fetchById 接口
onMounted(() => {
  // 默认加载一些选项
  searchReference('')
})
</script>
