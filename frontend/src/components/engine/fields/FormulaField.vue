<template>
  <div class="formula-field">
    <el-input
      :model-value="displayValue"
      readonly
      disabled
      placeholder="自动计算"
    >
      <template #prefix>
        <el-icon><Calculator /></el-icon>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Operation as Calculator } from '@element-plus/icons-vue'

const props = defineProps<{
  modelValue: any
  field: any
}>()

const displayValue = computed(() => {
  return props.modelValue
})
</script>

<style scoped>
.formula-field {
  width: 100%;
}
</style>
