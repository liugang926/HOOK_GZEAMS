<template>
  <div class="formula-field">
    <el-input
      :model-value="displayValue"
      readonly
      disabled
      :placeholder="$t('fields.autoCalculated')"
    >
      <template #prefix>
        <el-icon><Calculator /></el-icon>
      </template>
    </el-input>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Operation as Calculator } from '@element-plus/icons-vue'

const { t } = useI18n()

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
