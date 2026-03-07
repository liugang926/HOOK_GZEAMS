<template>
  <el-form
    :model="modelValue"
    label-position="top"
    size="small"
    class="section-property-editor"
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
      >
        <div :data-testid="`section-prop-${item.key}`">
          <el-switch
            v-if="item.inputType === 'switch'"
            :data-testid="`section-prop-${item.key}`"
            :model-value="switchValue(item.key)"
            @change="handleSwitchChange(item.key, $event)"
          />

          <el-select
            v-else-if="item.inputType === 'select'"
            :data-testid="`section-prop-${item.key}`"
            :model-value="modelValue?.[item.key]"
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
    </template>
  </el-form>

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

const sectionLabels: Record<string, string> = {
  basic: 'Basic',
  display: 'Display',
  advanced: 'Advanced'
}
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
  const next = { ...(props.modelValue || {}), [key]: value }
  emit('update:modelValue', next)
  emit('update-property', { key, value })
}

const handleSwitchChange = (key: string, value: unknown) => emitUpdate(key, Boolean(value))
const handleSelectChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleTextChange = (key: string, value: unknown) => emitUpdate(key, value)

const switchValue = (key: string): boolean => Boolean(props.modelValue?.[key])
const stringValue = (key: string): string => String(props.modelValue?.[key] ?? '')

const getTabsValue = () => {
  const tabs = props.modelValue?.tabs || []
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
  .tabs-manager {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
    width: 100%;

    .tab-item-row {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
    }

    .add-tab-btn {
      width: 100%;
      margin-top: $spacing-xs;
    }
  }
}
</style>
