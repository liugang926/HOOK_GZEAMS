<template>
  <el-tree-select
    :model-value="modelValue"
    :data="departmentTree"
    :props="treeProps"
    :multiple="isMultiple"
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
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'
import { referenceResolver } from '@/platform/reference/referenceResolver'

const { t } = useI18n()

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

// Support both camelCase (fieldType) and snake_case (field_type)
const isMultiple = computed(() => {
  const fieldType = props.field.fieldType || props.field.field_type
  return props.field.multiple || fieldType === 'multi_department' || fieldType === 'multiDepartment'
})

const placeholder = computed(() => {
  return props.placeholder || `${t('fields.select')}${props.field.name}`
})

const getIds = () => {
  const v = props.modelValue
  const ids = Array.isArray(v) ? v : v ? [v] : []
  return ids
    .map((entry) => {
      if (!entry) return ''
      if (typeof entry === 'object') return entry.id ? String(entry.id) : ''
      return String(entry)
    })
    .filter(Boolean)
}

let lastLoadKey = ''
const loadCurrentDepartments = async () => {
  const ids = getIds()
  if (ids.length === 0) {
    departmentTree.value = []
    return
  }

  const key = ids.slice().sort().join(',')
  if (key === lastLoadKey) return
  lastLoadKey = key

  loading.value = true
  try {
    const resolved = await referenceResolver.resolveMany('Department', ids)
    departmentTree.value = Object.values(resolved).filter(Boolean)
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.disabled, props.modelValue],
  async ([disabled]) => {
    if (disabled) {
      await loadCurrentDepartments()
      return
    }
    await loadDepartments()
  },
  { immediate: true }
)

onMounted(async () => {
  if (props.disabled) {
    await loadCurrentDepartments()
    return
  }
  await loadDepartments()
})

const buildTree = (items) => {
  const list = Array.isArray(items) ? items : []
  const map = new Map()
  const roots = []

  for (const raw of list) {
    const item = raw || {}
    const id = String(item.id || '').trim()
    if (!id) continue
    map.set(id, { ...item, children: [] })
  }

  const getParentId = (item) => {
    if (!item) return ''
    const direct = item.parentId || item.parent_id || item.parent || item.parentID
    if (typeof direct === 'string' || typeof direct === 'number') return String(direct)
    if (direct && typeof direct === 'object' && direct.id) return String(direct.id)
    return ''
  }

  for (const node of map.values()) {
    const parentId = getParentId(node)
    if (parentId && map.has(parentId)) {
      map.get(parentId).children.push(node)
    } else {
      roots.push(node)
    }
  }

  return roots
}

const loadDepartments = async () => {
  loading.value = true
  try {
    // Prefer unified object router.
    const data = await request.get('/system/objects/Department/', {
      params: { page: 1, page_size: 500 },
      silent: true
    })
    const items = data?.results || []
    departmentTree.value = buildTree(items)
  } catch (error) {
    console.error('Failed to load departments:', error)
    departmentTree.value = []
  } finally {
    loading.value = false
  }
}
</script>
