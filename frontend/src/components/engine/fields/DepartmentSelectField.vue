<template>
  <el-tree-select
    :model-value="modelValue"
    :data="departmentTree"
    :props="treeProps"
    :multiple="field.multiple || field.field_type === 'multi_department'"
    :disabled="disabled"
    :placeholder="placeholder"
    clearable
    filterable
    check-strictly
    :render-after-expand="false"
    style="width: 100%"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { deptApi } from '@/api/organizations'

const props = defineProps({
  field: Object,
  modelValue: [String, Number, Array],
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])

const departmentTree = ref([])
const loading = ref(false)

const treeProps = {
  label: 'name',
  children: 'children',
  value: 'id'
}

const placeholder = computed(() => {
  return props.placeholder || `请选择${props.field.name}`
})

onMounted(async () => {
  await loadDepartments()
})

const loadDepartments = async () => {
  loading.value = true
  try {
    const data = await deptApi.tree()
    // API already returns tree structure
    departmentTree.value = data || []
  } catch (error) {
    console.error('Failed to load departments:', error)
  } finally {
    loading.value = false
  }
}
</script>
