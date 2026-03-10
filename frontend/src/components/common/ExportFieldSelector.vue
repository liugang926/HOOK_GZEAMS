<!--
  ExportFieldSelector.vue

  Modal dialog that lets users pick which fields to include in an export.
  Renders a checkbox list from field metadata, with select-all / deselect-all,
  and emits the confirmed `ExportColumn[]` when the user clicks "Export".

  Usage:
    <ExportFieldSelector
      v-model="showSelector"
      :fields="allFields"
      :object-name="objectDisplayName"
      @confirm="handleExportConfirm"
    />
-->
<template>
  <el-dialog
    v-model="visible"
    :title="t('reports.export.selectFields', { name: objectName })"
    width="520px"
    destroy-on-close
    class="export-field-selector"
  >
    <div class="selector-actions">
      <el-button
        link
        type="primary"
        @click="selectAll"
      >
        {{ t('common.actions.selectAll') }}
      </el-button>
      <el-divider direction="vertical" />
      <el-button
        link
        @click="deselectAll"
      >
        {{ t('common.actions.deselectAll') }}
      </el-button>
      <span class="selected-count">
        {{ t('reports.export.selectedCount', { count: selectedCodes.size, total: fieldItems.length }) }}
      </span>
    </div>

    <el-scrollbar max-height="400px">
      <el-checkbox-group
        v-model="selectedList"
        class="field-checkbox-list"
      >
        <el-checkbox
          v-for="field in fieldItems"
          :key="field.code"
          :value="field.code"
          class="field-checkbox-item"
        >
          <span class="field-label">{{ field.label }}</span>
          <span class="field-code">{{ field.code }}</span>
        </el-checkbox>
      </el-checkbox-group>
    </el-scrollbar>

    <template #footer>
      <el-button @click="visible = false">
        {{ t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :disabled="selectedCodes.size === 0"
        @click="handleConfirm"
      >
        {{ t('common.actions.export') }} ({{ selectedCodes.size }})
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ExportColumn } from '@/utils/exportService'

interface FieldItem {
  code: string
  label: string
}

const props = defineProps<{
  modelValue: boolean
  fields: FieldItem[]
  objectName?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', columns: ExportColumn[]): void
}>()

const { t } = useI18n()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const fieldItems = computed<FieldItem[]>(() => {
  return (props.fields || [])
    .filter(f => f.code && f.label)
})

const selectedList = ref<string[]>([])

const selectedCodes = computed(() => new Set(selectedList.value))

// Initialize: select all fields when dialog opens
watch(() => props.modelValue, (val) => {
  if (val) {
    selectedList.value = fieldItems.value.map(f => f.code)
  }
})

const selectAll = () => {
  selectedList.value = fieldItems.value.map(f => f.code)
}

const deselectAll = () => {
  selectedList.value = []
}

const handleConfirm = () => {
  const columns: ExportColumn[] = fieldItems.value
    .filter(f => selectedCodes.value.has(f.code))
    .map(f => ({
      label: f.label,
      prop: f.code,
      width: 20
    }))
  emit('confirm', columns)
  visible.value = false
}
</script>

<style scoped lang="scss">
.selector-actions {
  display: flex;
  align-items: center;
  margin-bottom: 12px;

  .selected-count {
    margin-left: auto;
    font-size: 13px;
    color: var(--el-text-color-secondary);
  }
}

.field-checkbox-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-checkbox-item {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background-color 0.15s;

  &:hover {
    background-color: var(--el-fill-color-light);
  }

  .field-label {
    flex: 1;
  }

  .field-code {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
    font-family: monospace;
  }
}
</style>
