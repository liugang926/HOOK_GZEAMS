<template>
  <el-select
    v-model="selectedRoles"
    multiple
    :placeholder="$t('common.selectors.selectRole')"
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
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
  { label: t('common.selectors.systemAdmin'), value: 'admin' },
  { label: t('common.selectors.assetAdmin'), value: 'asset_admin' },
  { label: t('common.selectors.deptManager'), value: 'dept_manager' },
  { label: t('common.selectors.normalUser'), value: 'user' }
])
</script>
