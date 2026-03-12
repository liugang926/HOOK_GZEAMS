<template>
  <el-form
    :model="modelDraft"
    label-position="top"
    size="small"
    class="section-property-editor"
  >
    <template
      v-for="section in sections"
      :key="section"
    >
      <section
        v-if="groupedSchema[section]?.length > 0"
        class="property-section-card"
        :data-section-group="section"
      >
        <header class="property-section-card__header">
          <DesignerPropertySectionHeading
            :label="sectionLabels[section]"
            :count="groupedSchema[section].length"
          />
        </header>
        <div class="property-section-card__content">
          <el-form-item
            v-for="item in groupedSchema[section]"
            :key="item.key"
            :label="item.label"
            :data-property-key="item.key"
          >
            <div :data-testid="item.inputType !== 'select' ? `section-prop-${item.key}` : undefined">
              <div
                v-if="item.inputType === 'switch'"
                :data-testid="`section-prop-${item.key}`"
              >
                <el-switch
                  :model-value="switchValue(item.key)"
                  @change="handleSwitchChange(item.key, $event)"
                />
              </div>

              <el-radio-group
                v-else-if="item.key === 'columns'"
                :data-testid="`section-prop-${item.key}`"
                :model-value="Number(propertyValue(item.key) ?? 2)"
                class="section-column-choice"
                size="small"
                @change="handleSelectChange(item.key, $event)"
              >
                <el-radio-button
                  v-for="option in item.options || []"
                  :key="option.value"
                  :label="option.value"
                >
                  {{ option.label }}
                </el-radio-button>
              </el-radio-group>

              <el-select
                v-else-if="item.inputType === 'select'"
                :data-testid="`section-prop-${item.key}`"
                :model-value="propertyValue(item.key)"
                popper-class="section-property-editor__select-popper"
                style="width: 100%"
                @change="handleSelectChange(item.key, $event)"
              >
                <el-option
                  v-for="option in item.options || []"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>

              <div
                v-else-if="item.inputType === 'tabs'"
                :data-testid="`section-prop-${item.key}`"
                class="tabs-manager"
              >
                <div
                  v-for="(tab, index) in getTabsValue()"
                  :key="tab.id"
                  class="tab-item-row"
                >
                  <el-input
                    v-model="tab.title"
                    size="small"
                    @change="handleTabsChange"
                  />
                  <el-button
                    type="danger"
                    link
                    size="small"
                    icon="Delete"
                    :disabled="getTabsValue().length <= 1"
                    @click="removeTab(index)"
                  />
                </div>
                <el-button
                  type="primary"
                  plain
                  size="small"
                  icon="Plus"
                  class="add-tab-btn"
                  @click="addTab"
                >
                  Add Tab Page
                </el-button>
              </div>

              <el-input
                v-else
                :data-testid="`section-prop-${item.key}`"
                :model-value="stringValue(item.key)"
                @input="handleTextChange(item.key, $event)"
              />
            </div>
          </el-form-item>
        </div>
      </section>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import DesignerPropertySectionHeading from '@/components/designer/DesignerPropertySectionHeading.vue'
import { getSectionPropertySchema } from '@/composables/useSectionPropertySchema'
import { usePropertyEditorDraft } from '@/components/designer/usePropertyEditorDraft'

interface Props {
  modelValue?: Record<string, any>
  sectionType?: string
  isCompactMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  sectionType: 'section',
  isCompactMode: false
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
  booleanValue
} = usePropertyEditorDraft(() => props.modelValue)

const schema = computed(() => {
  const base = getSectionPropertySchema(props.sectionType || 'section')
  if (!props.isCompactMode) return base
  // In Compact mode: filter out tab/collapse from type options, keep only 'section'
  return base.map(item => {
    if (item.key === 'type' && item.options) {
      return {
        ...item,
        options: item.options.filter((opt: { value: unknown }) => opt.value === 'section')
      }
    }
    // Hide tab management in compact mode
    if (item.key === 'tabs') return null
    return item
  }).filter(Boolean) as typeof base
})

const sectionLabels = computed<Record<string, string>>(() => ({
  basic: tr('common.labels.basic', 'Basic'),
  display: tr('common.labels.display', 'Display'),
  advanced: tr('common.labels.advanced', 'Advanced')
}))
const sections = ['basic', 'display', 'advanced'] as const

const groupedSchema = computed(() => {
  const map: Record<string, Array<{ key: string; label: string; inputType: string; options?: Array<{ label: string; value: any }> }>> = {
    basic: [],
    display: [],
    advanced: []
  }
  for (const item of schema.value) {
    map[item.section].push(item)
  }
  return map
})

const emitUpdate = (key: string, value: any) => {
  const next = updateDraft((draft) => ({ ...draft, [key]: value }))
  emit('update:modelValue', next)
  emit('update-property', { key, value })
}

const handleSwitchChange = (key: string, value: unknown) => emitUpdate(key, Boolean(value))
const handleSelectChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleTextChange = (key: string, value: unknown) => emitUpdate(key, value)

const switchValue = (key: string): boolean => booleanValue(key)

const getTabsValue = () => {
  const tabs = propertyValue('tabs') || []
  return Array.isArray(tabs) ? tabs as Array<{ id: string, title: string, name?: string, fields: any[] }> : []
}

const handleTabsChange = () => {
  emitUpdate('tabs', [...getTabsValue()])
}

const addTab = () => {
  const currentTabs = [...getTabsValue()]
  const newId = `tab_${Date.now()}`
  currentTabs.push({
    id: newId,
    title: `New Tab`,
    name: newId,
    fields: []
  })
  emitUpdate('tabs', currentTabs)
}

const removeTab = (index: number) => {
  const currentTabs = [...getTabsValue()]
  if (currentTabs.length > 1) {
    currentTabs.splice(index, 1)
    emitUpdate('tabs', currentTabs)
  }
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.section-property-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;

  :deep(.el-form-item) {
    margin-bottom: 10px;
  }

  :deep(.el-form-item:last-child) {
    margin-bottom: 0;
  }

  :deep(.el-form-item__label) {
    padding-bottom: 3px;
    color: #5b6472;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.35;
  }

  :deep(.el-input),
  :deep(.el-select),
  :deep(.el-input-number) {
    width: 100%;
  }

  :deep(.section-column-choice) {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    width: 100%;
    gap: 6px;
  }

  :deep(.section-column-choice .el-radio-button) {
    width: 100%;
  }

  :deep(.section-column-choice .el-radio-button__inner) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    min-height: 32px;
    padding: 0 10px;
    border: 1px solid rgba(15, 23, 42, 0.12);
    border-radius: 10px;
    box-shadow: none;
    font-size: 12px;
    font-weight: 700;
  }

  :deep(.section-column-choice .el-radio-button__original-radio:checked + .el-radio-button__inner) {
    border-color: #2563eb;
    background: rgba(37, 99, 235, 0.1);
    color: #1d4ed8;
  }

  :deep(.section-column-choice .el-radio-button:first-child .el-radio-button__inner),
  :deep(.section-column-choice .el-radio-button:last-child .el-radio-button__inner) {
    border-radius: 10px;
  }

  :deep(.section-property-editor__select-popper.el-zoom-in-top-leave-active),
  :deep(.section-property-editor__select-popper.el-zoom-in-top-leave-from),
  :deep(.section-property-editor__select-popper.el-zoom-in-top-leave-to) {
    pointer-events: none !important;
  }

  .property-section-card {
    overflow: hidden;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 14px;
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    box-shadow: 0 10px 18px rgba(15, 23, 42, 0.04);
  }

  .property-section-card__header {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    background: rgba(248, 250, 252, 0.92);
  }

  .property-section-card__content {
    padding: 10px 12px 12px;
  }

  .tabs-manager {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;

    .tab-item-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 8px;
      padding: 8px;
      border: 1px solid rgba(15, 23, 42, 0.08);
      border-radius: 10px;
      background: #f8fafc;
    }

    .add-tab-btn {
      width: 100%;
      margin-top: 2px;
    }
  }
}
</style>
