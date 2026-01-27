<template>
  <div
    v-loading="loading"
    class="dynamic-form"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-width="labelWidth"
      :label-position="labelPosition"
    >
      <!-- Iterate through layout sections -->
      <template
        v-for="section in layoutSections"
        :key="section.id"
      >
        <!-- CARD MODE: Renders as el-card if strictly configured -->
        <el-card
          v-if="section.visible !== false && (section.render_as_card === true)"
          class="form-section card-mode"
          :shadow="section.shadow || 'hover'"
        >
          <template
            v-if="section.title && section.show_title !== false"
            #header
          >
            <div class="section-header">
              <span>{{ section.title }}</span>
              <div class="header-actions">
                <el-button
                  v-if="section.collapsible"
                  link
                  @click="toggleSection(section.id)"
                >
                  <el-icon>
                    <component :is="isSectionCollapsed(section.id) ? 'ArrowDown' : 'ArrowUp'" />
                  </el-icon>
                </el-button>
              </div>
            </div>
          </template>

          <!-- Field grid within section -->
          <el-row
            v-show="!isSectionCollapsed(section.id)"
            :gutter="20"
          >
            <template
                v-for="fieldCode in section.fields"
                :key="fieldCode"
            >
                <el-col
                  v-show="isFieldVisible(getFieldDef(fieldCode))"
                  :xs="24"
                  :span="getFieldSpan(fieldCode)"
                >
                  <template v-if="getFieldDef(fieldCode)">
                    <!-- Field permission: read-only -->
                    <template v-if="isFieldReadonly(getFieldDef(fieldCode))">
                      <el-form-item
                        :label="getFieldDef(fieldCode).name"
                        :prop="fieldCode"
                      >
                        <DisplayField
                          :field="getFieldDef(fieldCode)"
                          :value="getFormFieldValue(fieldCode)"
                        />
                      </el-form-item>
                    </template>
    
                    <!-- Field permission: editable -->
                    <template v-else>
                      <el-form-item
                        :label="getFieldDef(fieldCode).name"
                        :prop="fieldCode"
                      >
                        <FieldRenderer
                          :field="getFieldDef(fieldCode)"
                          :model-value="getFormFieldValue(fieldCode)"
                          :form-data="formData"
                          @update:model-value="handleFieldValueChange(fieldCode, $event)"
                        />
                      </el-form-item>
                    </template>
                  </template>
                </el-col>
            </template>
          </el-row>
        </el-card>

        <!-- CLEAN MODE: Default rendering (Flat DIV) -->
        <div
          v-else-if="section.visible !== false"
          class="form-section clean-mode"
          :class="{ 'has-border': section.border }"
        >
            <div 
                v-if="section.title && section.show_title !== false"
                class="section-header clean-header"
                @click="section.collapsible && toggleSection(section.id)"
                :class="{ clickable: section.collapsible }"
            >
                <div class="header-title">
                    <span v-if="section.icon" class="section-icon">
                        <el-icon><component :is="section.icon" /></el-icon>
                    </span>
                    <span>{{ section.title }}</span>
                </div>
                <div class="header-actions">
                    <el-icon v-if="section.collapsible" class="collapse-icon">
                        <component :is="isSectionCollapsed(section.id) ? 'ArrowRight' : 'ArrowDown'" />
                    </el-icon>
                </div>
            </div>
            
            <el-divider v-if="section.border && !isSectionCollapsed(section.id)" class="clean-divider" />

            <div v-show="!isSectionCollapsed(section.id)" class="section-body">
                <el-row :gutter="24">
                    <template
                        v-for="fieldCode in section.fields"
                        :key="fieldCode"
                    >
                        <el-col
                          v-show="isFieldVisible(getFieldDef(fieldCode))"
                          :xs="24"
                          :span="getFieldSpan(fieldCode)"
                        >
                          <template v-if="getFieldDef(fieldCode)">
                            <!-- Field permission: read-only -->
                            <template v-if="isFieldReadonly(getFieldDef(fieldCode))">
                              <el-form-item
                                :label="getFieldDef(fieldCode).name"
                                :prop="fieldCode"
                              >
                                <DisplayField
                                  :field="getFieldDef(fieldCode)"
                                  :value="getFormFieldValue(fieldCode)"
                                />
                              </el-form-item>
                            </template>
            
                            <!-- Field permission: editable -->
                            <template v-else>
                              <el-form-item
                                :label="getFieldDef(fieldCode).name"
                                :prop="fieldCode"
                              >
                                <FieldRenderer
                                  :field="getFieldDef(fieldCode)"
                                  :model-value="getFormFieldValue(fieldCode)"
                                  :form-data="formData"
                                  @update:model-value="handleFieldValueChange(fieldCode, $event)"
                                />
                              </el-form-item>
                            </template>
                          </template>
                        </el-col>
                    </template>
                </el-row>
            </div>
        </div>
      </template>

      <!-- Fallback if no sections -->
      <div v-if="!layoutSections.length && !loading">
        <el-empty description="暂无表单配置" />
      </div>
    </el-form>

    <!-- Form Actions Footer -->
    <div
      v-if="finalActions && finalActions.length > 0"
      class="form-actions"
    >
      <el-button
        v-for="action in finalActions"
        :key="action.code"
        :type="action.type === 'primary' ? 'primary' : 'default'"
        @click="handleAction(action)"
      >
        {{ action.label }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useDynamicForm } from './hooks/useDynamicForm'
import { useFieldPermissions } from './hooks/useFieldPermissions'
import { useFormula } from './hooks/useFormula'
import { useAction } from './hooks/useAction'
import FieldRenderer from './FieldRenderer.vue'
import DisplayField from './fields/DisplayField.vue'

const props = defineProps({
  businessObject: { type: String, required: true },
  layoutCode: { type: String, default: 'form' },
  modelValue: { type: Object, default: () => ({}) },
  fieldPermissions: { type: Object, default: () => ({}) },
  labelWidth: { type: String, default: '120px' },
  labelPosition: { type: String, default: 'right' },
  enableFormulas: { type: Boolean, default: true },
  // Optional local config for preview mode
  layoutConfig: { type: Object, default: null },
  availableFields: { type: Array, default: null },
  // Runtime Actions
  actions: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'change', 'loaded', 'formula-calculated'])

// Use dynamic form hook
const {
  formRef,
  formData,
  formRules,
  fieldDefinitions,
  layoutSections,
  loading,
  loadMetadata,
  validate,
  resetFields,
  businessObjectActions
} = useDynamicForm(props.businessObject, props.layoutCode, props.layoutConfig, props.availableFields)

// Ensure fallback for render_as_card if not in config
watch(layoutSections, (sections) => {
    if (sections) {
        sections.forEach(s => {
            // Apply PRD defaults if missing
            if (s.render_as_card === undefined) s.render_as_card = false
            if (s.border === undefined) s.border = false
        })
    }
}, { immediate: true, deep: true })

// Use field permissions hook
const {
  getFieldPermission,
  isFieldReadonly,
  isFieldVisible
} = useFieldPermissions(ref(props.fieldPermissions), fieldDefinitions)

// Formula calculation
const formulaHook = props.enableFormulas
  ? useFormula(formData, fieldDefinitions)
  : null



// Action Handler
const { executeAction } = useAction()

const finalActions = computed(() => {
    if (props.actions && props.actions.length > 0) return props.actions
    return businessObjectActions.value || []
})

const handleAction = async (action) => {
    await executeAction(action, { formData, formRef })
}

// Collapsed sections tracking
const collapsedSections = ref(new Set())

// Helper to find field definition
const getFieldDef = (code) => {
  return fieldDefinitions.value.find(f => f.code === code) || { code, name: code, field_type: 'text' }
}

// Helper for colspan (default to 12 for 2-column layout)
const getFieldSpan = (code) => {
  const field = getFieldDef(code)
  // Check if field has custom span in layout config
  if (field.component_props && field.component_props.span) {
    return field.component_props.span
  }
  // Larger fields get full width
  if (field.field_type === 'textarea' || field.field_type === 'rich_text' ||
      field.field_type === 'code' || field.field_type === 'sub_table') {
    return 24
  }
  return 12
}

// Toggle section collapse
const toggleSection = (sectionId) => {
  if (collapsedSections.value.has(sectionId)) {
    collapsedSections.value.delete(sectionId)
  } else {
    collapsedSections.value.add(sectionId)
  }
}

// Check if section is collapsed
const isSectionCollapsed = (sectionId) => {
  const section = layoutSections.value.find(s => s.id === sectionId)
  return (section && section.collapsed) || collapsedSections.value.has(sectionId)
}

// Get field value from form data or calculated value
const getFormFieldValue = (fieldCode) => {
  // Check if this is a formula field with calculated value
  if (formulaHook && formulaHook.isFormulaField(fieldCode)) {
    const calculated = formulaHook.getCalculatedValue(fieldCode)
    if (calculated !== undefined) {
      return calculated
    }
  }
  return formData[fieldCode]
}

// Load metadata on mount
onMounted(async () => {
  await loadMetadata()

  // Initialize with passed model value
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    Object.assign(formData, props.modelValue)
  }

  // Initialize formula calculations
  if (formulaHook) {
    formulaHook.initFormulas()
  }

  emit('loaded', { fieldDefinitions: fieldDefinitions.value })
})

// Handle field value changes
const handleFieldValueChange = (fieldCode, value) => {
  formData[fieldCode] = value

  // Recalculate formulas that depend on this field
  if (formulaHook) {
    const dependentFormulas = formulaHook.getDependentFormulas(fieldCode)
    if (dependentFormulas.size > 0) {
      formulaHook.calculateFormulas()

      // Update form data with calculated values
      dependentFormulas.forEach(formulaFieldCode => {
        const calculatedValue = formulaHook.getCalculatedValue(formulaFieldCode)
        if (calculatedValue !== undefined) {
          formData[formulaFieldCode] = calculatedValue
        }
      })

      // Emit formula calculated event with all calculated values
      emit('formula-calculated', formulaHook.calculatedValues)
    }
  }

  // Convert reactive object to plain object for emit
  const plainFormData = JSON.parse(JSON.stringify(formData))
  emit('update:modelValue', plainFormData)
  emit('change', { fieldCode, value })
}

// Watch for external model value changes
watch(() => props.modelValue, (newValue) => {
  if (newValue && Object.keys(newValue).length > 0) {
    Object.assign(formData, newValue)
  }
}, { deep: true })

// Sync formula values to form data before validation/submit
const syncFormulas = () => {
  if (formulaHook) {
    formulaHook.syncFormulasToFormData()
  }
}

// Override validate to sync formulas first
const validateForm = async () => {
  syncFormulas()
  return await validate()
}

// Expose methods to parent component
defineExpose({
  validate: validateForm,
  resetFields,
  formData,
  loading,
  syncFormulas,
  calculateFormulas: () => {
    if (formulaHook) {
      return formulaHook.calculateFormulas()
    }
  },
  calculatedValues: () => {
    if (formulaHook) {
      return formulaHook.calculatedValues.value
    }
    return {}
  }
})
</script>

<style scoped>
.dynamic-form {
  width: 100%;
}

.form-section {
  margin-bottom: 24px;
}

/* Card Mode Styles (Legacy/Specific) */
.form-section.card-mode {
  border-radius: 4px;
}

.form-section.card-mode .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 15px;
}

/* Clean Mode Styles (Default/Modern) */
.form-section.clean-mode {
  padding: 0 4px;
}

.form-section.clean-mode.has-border {
    border: 1px solid #ebeef5;
    border-radius: 4px;
    padding: 16px;
}

.section-header.clean-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-size: 16px; /* Slightly larger for emphasis */
  font-weight: 600;
  color: #303133;
  line-height: 24px;
}

.section-header.clean-header.clickable {
    cursor: pointer;
    user-select: none;
}

.section-header.clean-header.clickable:hover {
    color: var(--el-color-primary);
}

.header-title {
    display: flex;
    align-items: center;
    gap: 8px;
}

.clean-divider {
    margin: 8px 0 20px 0;
}

.section-icon {
    display: flex;
    align-items: center;
    font-size: 18px;
    color: var(--el-text-color-secondary);
}

.collapse-icon {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    transition: transform 0.3s;
}

.form-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}
</style>
