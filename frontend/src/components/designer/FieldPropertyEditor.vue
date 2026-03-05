<template>
  <el-form
    :model="modelValue"
    label-position="top"
    size="small"
    class="field-property-editor"
  >
    <template
      v-for="section in sections"
      :key="section"
    >
      <el-divider>{{ sectionLabels[section] }}</el-divider>
      <el-form-item
        v-for="item in groupedSchema[section]"
        :key="item.key"
        :label="item.label"
        :data-property-key="item.key"
        :class="{ 'is-translation-target': translationMode && ['label', 'name', 'title', 'helpText', 'placeholder', 'i18nKey'].includes(item.key) }"
      >
        <div :data-testid="`field-prop-${item.key}`">
          <el-select
            v-if="item.key === 'span'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="modelValue?.span"
            @change="handleSelectChange(item.key, $event)"
          >
            <el-option
              v-for="span in availableSpans"
              :key="span"
              :label="`${span} / ${availableSpanColumns}`"
              :value="span"
            />
          </el-select>

          <el-switch
            v-else-if="item.inputType === 'switch'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="modelValue?.[item.key]"
            :disabled="isSwitchDisabled(item.key)"
            :active-text="item.key === 'readonly' && mode === 'readonly' ? 'Readonly by default in detail mode' : ''"
            :active-value="item.key === 'visible' ? true : undefined"
            :inactive-value="item.key === 'visible' ? false : undefined"
            @change="handleSwitchChange(item.key, $event)"
          />
          <div
            v-if="item.key === 'showShortcutHelp'"
            class="field-inline-hint"
          >
            {{ subtableShortcutHelpHintText }}
          </div>
          <div
            v-else-if="item.key === 'defaultShortcutHelpPinned'"
            class="field-inline-hint"
          >
            {{ isShortcutPinnedDisabled ? subtableShortcutPinnedRequiresHelpHintText : subtableShortcutPinnedHintText }}
          </div>

          <el-input-number
            v-else-if="item.inputType === 'number'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="numberValue(item.key)"
            :min="getNumberMin(item.key)"
            :step="getNumberStep(item.key)"
            @change="handleNumberChange(item.key, $event)"
          />

          <div
            v-else-if="item.key === 'lookupCompactKeys'"
            class="lookup-compact-keys"
          >
            <el-select
              :data-testid="`field-prop-${item.key}`"
              :model-value="compactKeysValue(item.key)"
              multiple
              filterable
              allow-create
              default-first-option
              @change="handleCompactKeysChange(item.key, $event)"
            >
              <el-option
                v-for="option in lookupCompactKeyOptions"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
            <div
              v-if="lookupCompactKeyOptions.length > 0"
              class="lookup-compact-keys__actions"
            >
              <el-button
                link
                type="primary"
                size="small"
                @click="handleCompactKeysSelectAll(item.key)"
              >
                {{ compactKeysSelectAllText }}
              </el-button>
              <el-button
                link
                size="small"
                :disabled="compactKeysValue(item.key).length === 0"
                @click="handleCompactKeysClear(item.key)"
              >
                {{ compactKeysClearText }}
              </el-button>
            </div>
            <div class="lookup-compact-keys__hint">
              {{ compactKeysHintText }}
            </div>
          </div>

          <el-select
            v-else-if="item.inputType === 'select'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="modelValue?.[item.key]"
            @change="handleSelectChange(item.key, $event)"
          >
            <el-option
              v-for="option in getSelectOptions(item.key)"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              :disabled="option.disabled"
            />
          </el-select>

          <el-input
            v-else-if="item.inputType === 'textarea'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="stringValue(item.key)"
            type="textarea"
            :rows="item.key === 'helpText' ? 2 : 4"
            @input="handleTextChange(item.key, $event)"
          />

          <el-input
            v-else-if="item.inputType === 'json'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="jsonValue(item.key)"
            type="textarea"
            :rows="4"
            @input="handleJsonChange(item.key, $event)"
          />

          <el-input
            v-else
            :data-testid="`field-prop-${item.key}`"
            :model-value="stringValue(item.key)"
            @input="handleTextChange(item.key, $event)"
          />
        </div>
      </el-form-item>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { getFieldPropertySchema } from '@/composables/useFieldPropertySchema'
import { normalizeFieldType } from '@/utils/fieldType'
import { getCoreFieldTypes } from '@/platform/layout/fieldCapabilityMatrix'
import { getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'

interface Props {
  modelValue?: Record<string, any>
  fieldType?: string
  mode?: string
  translationMode?: boolean
  availableSpans?: number[]
  availableSpanColumns?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  fieldType: 'text',
  mode: 'edit',
  translationMode: false,
  availableSpans: () => [1, 2],
  availableSpanColumns: 2
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'update-property', payload: { key: string; value: any }): void
}>()
const { t } = useI18n()

const tr = (key: string, fallback: string) => {
  const text = t(key, {})
  return text === key ? fallback : text
}

const normalizedFieldType = computed(() => normalizeFieldType(props.fieldType || props.modelValue?.fieldType || 'text'))
const schema = computed(() => getFieldPropertySchema(normalizedFieldType.value))
const fieldTypeOptions = computed(() => {
  const baseTypes = getCoreFieldTypes()
  const currentType = normalizedFieldType.value
  const uniqueTypes = baseTypes.includes(currentType) ? baseTypes : [currentType, ...baseTypes]

  return uniqueTypes.map((value) => {
    const reason = getFieldDisabledReason(value, props.mode)
    return {
      label: humanizeFieldType(value),
      value,
      disabled: Boolean(reason),
      reason
    }
  })
})

const sectionLabels: Record<string, string> = {
  basic: 'Basic',
  display: 'Display',
  validation: 'Validation',
  advanced: 'Advanced'
}
const sections = ['basic', 'display', 'validation', 'advanced'] as const

const groupedSchema = computed(() => {
  const map: Record<string, Array<{ key: string; label: string; inputType: string }>> = {
    basic: [],
    display: [],
    validation: [],
    advanced: []
  }
  for (const item of schema.value) {
    map[item.section].push(item)
  }
  return map
})

const compactKeysSelectAllText = computed(() => tr('common.actions.selectAll', 'Select all'))
const compactKeysClearText = computed(() => tr('common.actions.clear', 'Clear'))
const compactKeysHintText = computed(() =>
  tr('common.messages.lookupCompactKeysHint', 'Used by the lookup compact profile. Locked columns are always kept.')
)
const subtableShortcutHelpHintText = computed(() =>
  tr('common.messages.subtableShortcutHelpHint', 'Enable keyboard shortcut help panel in editable subtable.')
)
const subtableShortcutPinnedHintText = computed(() =>
  tr('common.messages.subtableShortcutPinnedHint', 'When enabled, shortcut help panel opens in pinned mode by default.')
)
const subtableShortcutPinnedRequiresHelpHintText = computed(() =>
  tr('common.messages.subtableShortcutPinnedRequiresHelpHint', 'Enable shortcut help first to use default pinned mode.')
)

const toBoolean = (value: unknown, fallback: boolean): boolean => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value !== 0
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'on'].includes(normalized)) return true
    if (['false', '0', 'no', 'off'].includes(normalized)) return false
  }
  return fallback
}

const showShortcutHelpEnabled = computed(() =>
  toBoolean(props.modelValue?.showShortcutHelp ?? props.modelValue?.show_shortcut_help, true)
)
const isShortcutPinnedDisabled = computed(() => !showShortcutHelpEnabled.value)
const isSwitchDisabled = (key: string): boolean => {
  if (key === 'defaultShortcutHelpPinned') return isShortcutPinnedDisabled.value
  return false
}

const emitUpdate = (key: string, value: any) => {
  const next = { ...(props.modelValue || {}), [key]: value }
  emit('update:modelValue', next)
  emit('update-property', { key, value })
}

const handleSelectChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleSwitchChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleNumberChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleTextChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleJsonChange = (key: string, value: unknown) => emitJsonUpdate(key, value)
const handleCompactKeysChange = (key: string, value: unknown) => {
  emitUpdate(key, normalizeStringArray(value))
}
const handleCompactKeysSelectAll = (key: string) => {
  emitUpdate(
    key,
    lookupCompactKeyOptions.value.map((option) => option.value)
  )
}
const handleCompactKeysClear = (key: string) => {
  emitUpdate(key, [])
}

const emitJsonUpdate = (key: string, value: any) => {
  let parsed: any = value
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      parsed = ''
    } else {
      try {
        parsed = JSON.parse(trimmed)
      } catch {
        parsed = value
      }
    }
  }
  emitUpdate(key, parsed)
}

const stringValue = (key: string): string => String(props.modelValue?.[key] ?? '')
const numberValue = (key: string): number | undefined => {
  const value = props.modelValue?.[key]
  if (value === null || value === undefined || value === '') return undefined
  const num = Number(value)
  return Number.isFinite(num) ? num : undefined
}
const jsonValue = (key: string): string => {
  const value = props.modelValue?.[key]
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return ''
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

const normalizeStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return []
  const out: string[] = []
  const seen = new Set<string>()
  for (const item of value) {
    const normalized = String(item ?? '').trim()
    if (!normalized) continue
    if (seen.has(normalized)) continue
    seen.add(normalized)
    out.push(normalized)
  }
  return out
}

const compactKeysValue = (key: string): string[] => {
  return normalizeStringArray(props.modelValue?.[key])
}

const lookupCompactKeyOptions = computed<Array<{ label: string; value: string }>>(() => {
  const raw =
    props.modelValue?.lookupColumns ??
    props.modelValue?.lookup_columns ??
    props.modelValue?.componentProps?.lookupColumns ??
    props.modelValue?.componentProps?.lookup_columns ??
    props.modelValue?.component_props?.lookupColumns ??
    props.modelValue?.component_props?.lookup_columns ??
    []
  if (!Array.isArray(raw)) return []

  const out: Array<{ label: string; value: string }> = []
  const seen = new Set<string>()
  for (const item of raw) {
    const key = typeof item === 'string'
      ? String(item).trim()
      : String((item as Record<string, any>)?.key || '').trim()
    if (!key || seen.has(key)) continue
    seen.add(key)
    const label = typeof item === 'string'
      ? key
      : String((item as Record<string, any>)?.label || key).trim() || key
    out.push({ label, value: key })
  }
  return out
})

const getNumberMin = (key: string): number | undefined => {
  if (key === 'minHeight') return 44
  if (key.includes('min_') || key.includes('max_')) return undefined
  return 0
}

const getNumberStep = (key: string): number => {
  if (key === 'minHeight') return 8
  return 1
}

const humanizeFieldType = (value: string): string =>
  value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

const getSelectOptions = (key: string): Array<{ label: string; value: string; disabled?: boolean }> => {
  if (key === 'fieldType') {
    return fieldTypeOptions.value.map((option) => ({
      label: option.reason ? `${option.label} (${option.reason})` : option.label,
      value: option.value,
      disabled: option.disabled
    }))
  }

  if (key === 'toolbar') {
    return [
      { label: 'Standard', value: 'standard' },
      { label: 'Simple', value: 'simple' },
      { label: 'Full', value: 'full' }
    ]
  }
  return []
}
</script>

<style scoped>
.is-translation-target {
  position: relative;
  padding: 8px;
  background-color: var(--el-color-primary-light-9);
  border: 1px dashed var(--el-color-primary-light-5);
  border-radius: var(--el-border-radius-base);
  margin-bottom: 8px !important;
}
.is-translation-target :deep(.el-form-item__label) {
  color: var(--el-color-primary);
  font-weight: 600;
}
.lookup-compact-keys {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.lookup-compact-keys__actions {
  display: flex;
  gap: 10px;
}
.lookup-compact-keys__hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
}
.field-inline-hint {
  margin-top: 6px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
}
</style>
