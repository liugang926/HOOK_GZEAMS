<template>
  <el-select
    v-model="selectedRoles"
    multiple
    placeholder="请选择角色"
    style="width: 100%"
  >
    <el-option
      v-for="role in roles"
      :key="role.value"
      :label="role.label"
      :value="role.value"
    />
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const selectedRoles = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// Mock roles
const roles = ref([
  { label: '系统管理员', value: 'admin' },
  { label: '资产管理员', value: 'asset_admin' },
  { label: '部门主管', value: 'dept_manager' },
  { label: '普通用户', value: 'user' }
])
</script>
