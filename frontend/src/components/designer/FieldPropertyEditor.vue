<template>
  <el-form
    :model="modelDraft"
    label-position="top"
    size="small"
    class="field-property-editor"
  >
    <el-collapse
      v-model="activeGroups"
      class="property-collapse"
    >
      <template
        v-for="section in sections"
        :key="section"
      >
        <el-collapse-item
          v-if="groupedSchema[section]?.length > 0"
          :name="section"
          :title="sectionLabels[section]"
          class="property-collapse-item"
        >
          <template #title>
            <DesignerPropertySectionHeading
              :label="sectionLabels[section]"
              :count="groupedSchema[section].length"
            />
          </template>
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
                :model-value="numberValue(item.key) ?? 1"
                @change="handleSelectChange(item.key, $event)"
              >
                <el-option
                  v-for="span in availableSpans"
                  :key="span"
                  :label="`${span} Column(s) / Total ${availableSpanColumns}`"
                  :value="span"
                />
              </el-select>

              <el-switch
                v-else-if="item.inputType === 'switch'"
                :data-testid="`field-prop-${item.key}`"
                :model-value="booleanValue(item.key)"
                :disabled="isSwitchDisabled(item.key)"
                :active-text="item.key === 'readonly' && mode === 'readonly' ? readonlyDefaultHintText : ''"
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
              <div
                v-else-if="item.key === 'readonly' && isReadonlyLocked"
                class="field-inline-hint"
              >
                {{ readonlyLockedHintText }}
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

              <div
                v-else-if="item.key === 'visibilityRule'"
                class="visibility-rule-editor"
                data-testid="field-prop-visibilityRule"
              >
                <el-select
                  :model-value="visibilityRuleField"
                  :placeholder="visibilityFieldPlaceholder"
                  @change="handleVisibilityRuleFieldChange"
                >
                  <el-option
                    v-for="option in props.visibilityFieldOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
                <el-select
                  :model-value="visibilityRuleOperator"
                  :placeholder="visibilityOperatorPlaceholder"
                  @change="handleVisibilityRuleOperatorChange"
                >
                  <el-option
                    v-for="option in visibilityOperatorOptions"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                  />
                </el-select>
                <el-input
                  :model-value="visibilityRuleValueInput"
                  :placeholder="visibilityValuePlaceholder"
                  @input="handleVisibilityRuleValueChange"
                />
                <div class="visibility-rule-editor__actions">
                  <el-button
                    link
                    size="small"
                    :disabled="!hasVisibilityRule"
                    @click="clearVisibilityRule"
                  >
                    {{ visibilityRuleClearText }}
                  </el-button>
                </div>
                <div class="visibility-rule-editor__hint">
                  {{ visibilityRuleHintText }}
                </div>
              </div>

              <el-select
                v-else-if="item.inputType === 'select'"
                :data-testid="`field-prop-${item.key}`"
                :model-value="propertyValue(item.key)"
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
                :rows="item.key === 'helpText' ? 2 : 3"
                @input="handleTextChange(item.key, $event)"
              />

              <el-input
                v-else-if="item.inputType === 'json'"
                :data-testid="`field-prop-${item.key}`"
                :model-value="jsonValue(item.key)"
                type="textarea"
                :rows="3"
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
        </el-collapse-item>
      </template>
    </el-collapse>
  </el-form>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import DesignerPropertySectionHeading from '@/components/designer/DesignerPropertySectionHeading.vue'
import { getFieldPropertySchema } from '@/composables/useFieldPropertySchema'
import { usePropertyEditorDraft } from '@/components/designer/usePropertyEditorDraft'
import { normalizeFieldType } from '@/utils/fieldType'
import { getCoreFieldTypes } from '@/platform/layout/fieldCapabilityMatrix'
import { getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'

const activeGroups = ref<string[]>(['basic', 'display'])

interface Props {
  modelValue?: Record<string, any>
  fieldType?: string
  mode?: string
  translationMode?: boolean
  availableSpans?: number[]
  availableSpanColumns?: number
  visibilityFieldOptions?: Array<{ label: string; value: string }>
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  fieldType: 'text',
  mode: 'edit',
  translationMode: false,
  availableSpans: () => [1, 2],
  availableSpanColumns: 2,
  visibilityFieldOptions: () => []
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

const {
  modelDraft,
  updateDraft,
  propertyValue,
  stringValue,
  numberValue,
  booleanValue
} = usePropertyEditorDraft(() => props.modelValue)
const normalizedFieldType = computed(() => normalizeFieldType(props.fieldType || propertyValue('fieldType') || 'text'))
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

const sectionLabels = computed<Record<string, string>>(() => ({
  basic: tr('common.labels.basic', 'Basic'),
  display: tr('common.labels.display', 'Display'),
  validation: tr('common.labels.validation', 'Validation'),
  advanced: tr('common.labels.advanced', 'Advanced')
}))
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
const readonlyDefaultHintText = computed(() =>
  tr('common.messages.readonlyByDefaultInDetailMode', 'Readonly by default in detail mode')
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
const readonlyLockedHintText = computed(() =>
  tr('common.messages.systemFieldReadonlyLocked', 'System fields stay readonly in the layout designer.')
)
const visibilityRuleHintText = computed(() =>
  tr(
    'common.messages.visibilityRuleHint',
    'Show this field only when the selected field matches the condition. Use commas for multiple values.'
  )
)
const visibilityRuleClearText = computed(() => tr('common.actions.clear', 'Clear'))
const visibilityFieldPlaceholder = computed(() => tr('common.placeholders.selectField', 'Select field'))
const visibilityOperatorPlaceholder = computed(() => tr('common.placeholders.selectOperator', 'Select operator'))
const visibilityValuePlaceholder = computed(() => tr('common.placeholders.enterValue', 'Enter value'))
const visibilityOperatorOptions = computed(() => [
  { label: tr('common.operators.equals', 'Equals'), value: 'eq' },
  { label: tr('common.operators.notEquals', 'Not equals'), value: 'neq' },
  { label: tr('common.operators.in', 'In list'), value: 'in' },
  { label: tr('common.operators.notIn', 'Not in list'), value: 'notIn' }
])

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
  toBoolean(propertyValue('showShortcutHelp') ?? propertyValue('show_shortcut_help'), true)
)
const isShortcutPinnedDisabled = computed(() => !showShortcutHelpEnabled.value)
const isReadonlyLocked = computed(() => propertyValue('isSystem') === true)
const isSwitchDisabled = (key: string): boolean => {
  if (key === 'readonly') return isReadonlyLocked.value
  if (key === 'defaultShortcutHelpPinned') return isShortcutPinnedDisabled.value
  return false
}

type VisibilityOperator = 'eq' | 'neq' | 'in' | 'notIn'
type VisibilityRule = {
  field: string
  operator: VisibilityOperator
  value: unknown
}

const normalizeVisibilityOperator = (value: unknown): VisibilityOperator | undefined => {
  if (value === 'eq' || value === 'neq' || value === 'in' || value === 'notIn') return value
  return undefined
}

const currentVisibilityRule = computed<VisibilityRule | undefined>(() => {
  const raw = modelDraft.value.visibilityRule ?? modelDraft.value.visibility_rule
  if (!raw || typeof raw !== 'object') return undefined
  const field = String((raw as VisibilityRule).field || '').trim()
  const operator = normalizeVisibilityOperator((raw as VisibilityRule).operator)
  if (!field || !operator) return undefined
  return {
    field,
    operator,
    value: (raw as VisibilityRule).value
  }
})

const hasVisibilityRule = computed(() => Boolean(currentVisibilityRule.value))
const visibilityRuleField = computed(() => currentVisibilityRule.value?.field || '')
const visibilityRuleOperator = computed(() => currentVisibilityRule.value?.operator || 'eq')
const visibilityRuleValueInput = computed(() => {
  const value = currentVisibilityRule.value?.value
  if (Array.isArray(value)) return value.map((item) => String(item ?? '').trim()).filter(Boolean).join(', ')
  if (value === null || value === undefined) return ''
  return String(value)
})
const visibilityRuleDraft = ref<VisibilityRule | undefined>(currentVisibilityRule.value)

watch(
  currentVisibilityRule,
  (value) => {
    visibilityRuleDraft.value = value
  },
  { immediate: true }
)

const emitUpdate = (key: string, value: any) => {
  const next = updateDraft((draft) => {
    draft[key] = value
    if (key === 'visibilityRule') {
      visibilityRuleDraft.value = value
      if (value && typeof value === 'object') {
        draft.visibilityRule = value
        draft.visibility_rule = value
      } else {
        delete draft.visibilityRule
        delete draft.visibility_rule
      }
    }
    return draft
  })
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
const buildVisibilityRule = (patch: Partial<VisibilityRule>): VisibilityRule | undefined => {
  const existing = visibilityRuleDraft.value || currentVisibilityRule.value
  const field = String(patch.field ?? existing?.field ?? '').trim()
  const operator = normalizeVisibilityOperator(patch.operator ?? existing?.operator ?? 'eq')
  const rawValue = patch.value ?? existing?.value ?? ''

  if (!field || !operator) return undefined

  const value = operator === 'in' || operator === 'notIn'
    ? String(rawValue ?? '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    : String(rawValue ?? '').trim()

  return { field, operator, value }
}
const handleVisibilityRuleFieldChange = (value: unknown) => {
  emitUpdate('visibilityRule', buildVisibilityRule({ field: String(value || '') }))
}
const handleVisibilityRuleOperatorChange = (value: unknown) => {
  emitUpdate('visibilityRule', buildVisibilityRule({ operator: normalizeVisibilityOperator(value) }))
}
const handleVisibilityRuleValueChange = (value: unknown) => {
  emitUpdate('visibilityRule', buildVisibilityRule({ value }))
}
const clearVisibilityRule = () => emitUpdate('visibilityRule', undefined)

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

const jsonValue = (key: string): string => {
  const value = propertyValue(key)
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
  return normalizeStringArray(propertyValue(key))
}

const lookupCompactKeyOptions = computed<Array<{ label: string; value: string }>>(() => {
  const raw =
    propertyValue('lookupColumns') ??
    propertyValue('lookup_columns') ??
    modelDraft.value.componentProps?.lookupColumns ??
    modelDraft.value.componentProps?.lookup_columns ??
    modelDraft.value.component_props?.lookupColumns ??
    modelDraft.value.component_props?.lookup_columns ??
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
      { label: tr('common.labels.standard', 'Standard'), value: 'standard' },
      { label: tr('common.labels.simple', 'Simple'), value: 'simple' },
      { label: tr('common.labels.full', 'Full'), value: 'full' }
    ]
  }

  const schemaItem = schema.value.find((item) => item.key === key)
  if (schemaItem?.options) {
    return schemaItem.options.map((option) => ({
      label: String(option.label),
      value: String(option.value)
    }))
  }

  return []
}
</script>

<style scoped>
.field-property-editor {
  padding: 0;
}
.field-property-editor :deep(.el-form-item) {
  margin-bottom: 10px;
}
.field-property-editor :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}
.field-property-editor :deep(.el-form-item__label) {
  padding-bottom: 3px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.35;
  color: #5b6472;
}
.field-property-editor :deep(.el-input),
.field-property-editor :deep(.el-select),
.field-property-editor :deep(.el-input-number),
.field-property-editor :deep(.el-switch) {
  width: 100%;
}
.property-collapse {
  border: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: transparent;
}
.property-collapse :deep(.el-collapse-item) {
  margin-bottom: 0;
  overflow: hidden;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  box-shadow: 0 10px 18px rgba(15, 23, 42, 0.04);
}
.property-collapse :deep(.el-collapse-item__header) {
  padding: 0 12px;
  height: 40px;
  line-height: 40px;
  background: rgba(248, 250, 252, 0.92);
  margin-bottom: 0;
  border-bottom: 1px solid transparent;
}
.property-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
  background: #ffffff;
}
.property-collapse :deep(.el-collapse-item__content) {
  padding: 10px 12px 12px;
}
.property-collapse :deep(.el-collapse-item.is-active .el-collapse-item__header) {
  border-bottom-color: rgba(15, 23, 42, 0.08);
}
.is-translation-target {
  position: relative;
  padding: 7px 8px;
  background-color: var(--el-color-primary-light-9);
  border: 1px dashed var(--el-color-primary-light-5);
  border-radius: var(--el-border-radius-base);
  margin-bottom: 6px !important;
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
.visibility-rule-editor {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.visibility-rule-editor__actions {
  display: flex;
  justify-content: flex-end;
}
.visibility-rule-editor__hint {
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
