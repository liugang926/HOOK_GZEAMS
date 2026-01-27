<template>
  <div class="display-field">
    <span v-if="displayText">{{ displayText }}</span>
    <span
      v-else
      class="empty-text"
    >-</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: Object,
  value: [String, Number, Boolean, Object, Array]
})

const displayText = computed(() => {
  const val = props.value
  if (val === null || val === undefined || val === '') return ''

  // Select/MultiSelect
  if (props.field.field_type === 'select' || props.field.field_type === 'multi_select') {
    if (Array.isArray(val)) {
      return val.map(v => getOptionLabel(v)).join(', ')
    }
    return getOptionLabel(val)
  }

  // Boolean
  if (props.field.field_type === 'boolean') {
    return val ? '是' : '否'
  }

  // Reference (If value is Object, use display field, else show ID)
  // Usually the backend might send the full object or just ID. 
  // For DisplayField, we prefer full object or label.
  if (props.field.field_type === 'reference') {
    if (typeof val === 'object') {
      return val[props.field.display_field || 'name'] || val.id
    }
  }

  return String(val)
})

const getOptionLabel = (val) => {
  const option = (props.field.options || []).find(o => o.value == val)
  return option ? option.label : val
}
</script>

<style scoped>
.display-text {
  color: #606266;
  line-height: 32px;
}
.empty-text {
  color: #909399;
}
</style>
