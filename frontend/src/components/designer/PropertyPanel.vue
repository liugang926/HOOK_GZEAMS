<!--
  PropertyPanel.vue - Right panel of layout designer
  Displays and edits properties of selected element
-->

<script setup lang="ts">
import { computed, watch } from 'vue'
import {
  ElForm, ElFormItem, ElInput, ElInputNumber, ElSwitch, ElSelect, ElOption,
  ElButton, ElDivider, ElColorPicker, ElSlider, ElCheckbox, ElRadioGroup, ElRadio
} from 'element-plus'
import { Delete, RefreshLeft } from '@element-plus/icons-vue'

type LayoutType = 'form' | 'list' | 'detail' | 'search'

interface LayoutField {
  id: string
  field_code: string
  label: string
  span: number
  readonly?: boolean
  visible?: boolean
  required?: boolean
  placeholder?: string
  default_value?: any
  help_text?: string
  width?: string
  custom_class?: string
  visible_rules?: Array<{field: string; value: any}>
  validation_rules?: Array<{logic: string; message: string}>
  regex_pattern?: string
  min_value?: number
  max_value?: number
  reference_filters?: Record<string, any>
}

interface LayoutSection {
  id: string
  type: string
  title?: string
  collapsible?: boolean
  collapsed?: boolean
  border?: boolean
  columns?: number
  background_color?: string
  icon?: string
  custom_class?: string
}

interface LayoutTab {
  id: string
  title: string
}

interface LayoutColumnItem {
  id: string
  span: number
}

interface ListColumn {
  field_code: string
  label: string
  width?: number
  fixed?: string
  sortable?: boolean
}

const props = defineProps<{
  selectedId: string
  selectedItem: LayoutField | LayoutSection | LayoutTab | LayoutColumnItem | ListColumn | null
  layoutType: LayoutType
}>()

const emit = defineEmits<{
  (e: 'update', data: Record<string, any>): void
  (e: 'delete'): void
  (e: 'duplicate'): void
}>()

// Local form state
const formData = computed({
  get: () => props.selectedItem || {},
  set: (val) => emit('update', val)
})

// Detect element type
const elementType = computed(() => {
  if (!props.selectedItem) return null

  if ('field_code' in props.selectedItem) {
    if ('span' in props.selectedItem) return 'field'
    return 'listColumn'
  }
  if ('tabs' in props.selectedItem) return 'tabSection'
  if ('items' in props.selectedItem) return 'collapseSection'
  if ('columns_array' in props.selectedItem) return 'columnSection'
  if ('title' in props.selectedItem && 'fields' in props.selectedItem === false) return 'tab'
  if ('columns' in props.selectedItem || 'fields' in props.selectedItem) return 'section'
  if (props.selectedItem.type === 'divider') return 'divider'
  if (props.selectedItem.type === 'column') return 'columnItem'

  return 'section'
})

// Field properties template
const fieldProps = computed(() => elementType.value === 'field')

// Section properties template
const sectionProps = computed(() => elementType.value === 'section')

// Tab properties template
const tabProps = computed(() => elementType.value === 'tab')

// Column item properties template
const columnItemProps = computed(() => elementType.value === 'columnItem')

// List column properties template
const listColumnProps = computed(() => elementType.value === 'listColumn')

// Valid span values
const spanOptions = [1, 2, 3, 4, 6, 8, 12, 24]

// Handle field update
function handleFieldUpdate(field: string, value: any) {
  // Convert number inputs
  if (['min_value', 'max_value'].includes(field) && value === '') {
    value = null
  }
  emit('update', { [field]: value })
}

// Handle delete
function handleDelete() {
  emit('delete')
}

// Handle duplicate
function handleDuplicate() {
  emit('duplicate')
}

// Reset to defaults
function handleReset() {
  if (elementType.value === 'field') {
    emit('update', {
      span: 12,
      readonly: false,
      visible: true,
      required: false
    })
  }
}
</script>

<template>
  <div class="property-panel">
    <div class="panel-header">
      <h3>Properties</h3>
      <div class="header-actions">
        <el-button
          v-if="selectedItem"
          size="small"
          :icon="RefreshLeft"
          text
          title="Reset to defaults"
          @click="handleReset"
        />
      </div>
    </div>

    <div class="panel-content">
      <!-- No selection -->
      <div
        v-if="!selectedItem"
        class="empty-state"
      >
        <svg
          viewBox="0 0 64 64"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          class="empty-icon"
        >
          <rect
            x="8"
            y="8"
            width="48"
            height="48"
            rx="4"
            stroke="#dcdfe6"
            stroke-width="2"
          />
          <path
            d="M8 20h48M20 8v12"
            stroke="#dcdfe6"
            stroke-width="2"
          />
        </svg>
        <p>Select an element to edit its properties</p>
      </div>

      <!-- Field Properties -->
      <el-form
        v-else-if="fieldProps"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Field Properties
        </div>

        <el-form-item label="Field Code">
          <el-input
            :model-value="formData.field_code"
            disabled
          />
        </el-form-item>

        <el-form-item label="Label">
          <el-input
            :model-value="formData.label"
            @update:model-value="handleFieldUpdate('label', $event)"
          />
        </el-form-item>

        <el-form-item label="Column Span">
          <el-select
            :model-value="formData.span"
            style="width: 100%"
            @update:model-value="handleFieldUpdate('span', $event)"
          >
            <el-option
              v-for="span in spanOptions"
              :key="span"
              :label="`${span}/24`"
              :value="span"
            />
          </el-select>
        </el-form-item>

        <el-divider />

        <div class="prop-group-title">
          Display Options
        </div>

        <el-form-item>
          <template #label>
            <span>Visible</span>
          </template>
          <el-switch
            :model-value="formData.visible ?? true"
            @update:model-value="handleFieldUpdate('visible', $event)"
          />
        </el-form-item>

        <el-form-item>
          <template #label>
            <span>Read Only</span>
          </template>
          <el-switch
            :model-value="formData.readonly ?? false"
            @update:model-value="handleFieldUpdate('readonly', $event)"
          />
        </el-form-item>

        <el-form-item>
          <template #label>
            <span>Required</span>
          </template>
          <el-switch
            :model-value="formData.required ?? false"
            :disabled="formData.readonly"
            @update:model-value="handleFieldUpdate('required', $event)"
          />
        </el-form-item>

        <el-divider />

        <div class="prop-group-title">
          Input Options
        </div>

        <el-form-item label="Placeholder">
          <el-input
            :model-value="formData.placeholder"
            placeholder="Enter placeholder text"
            @update:model-value="handleFieldUpdate('placeholder', $event)"
          />
        </el-form-item>

        <el-form-item label="Default Value">
          <el-input
            :model-value="formData.default_value"
            placeholder="Enter default value"
            @update:model-value="handleFieldUpdate('default_value', $event)"
          />
        </el-form-item>

        <el-form-item label="Help Text">
          <el-input
            :model-value="formData.help_text"
            placeholder="Field help text tooltip"
            @update:model-value="handleFieldUpdate('help_text', $event)"
          />
        </el-form-item>

        <el-form-item label="Label Width">
          <el-input
            :model-value="formData.width"
            placeholder="e.g. 120px or auto"
            @update:model-value="handleFieldUpdate('width', $event)"
          />
        </el-form-item>

        <el-divider />

        <div class="prop-group-title">
          Validation
        </div>

        <el-form-item label="Regex Pattern">
          <el-input
            :model-value="formData.regex_pattern"
            placeholder="e.g. ^[0-9]+$"
            @update:model-value="handleFieldUpdate('regex_pattern', $event)"
          >
            <template #prefix>
              <span style="color: #909399; font-size: 12px">/</span>
            </template>
            <template #suffix>
              <span style="color: #909399; font-size: 12px">/</span>
            </template>
          </el-input>
        </el-form-item>

        <template v-if="['number', 'currency', 'percent'].includes(formData.field_type)">
          <el-form-item label="Min Value">
            <el-input-number
              :model-value="formData.min_value"
              style="width: 100%"
              @update:model-value="handleFieldUpdate('min_value', $event)"
            />
          </el-form-item>
          <el-form-item label="Max Value">
            <el-input-number
              :model-value="formData.max_value"
              style="width: 100%"
              @update:model-value="handleFieldUpdate('max_value', $event)"
            />
          </el-form-item>
        </template>

        <el-divider />

        <div class="prop-group-title">
          Advanced Logic
        </div>

        <el-form-item label="Custom CSS Class">
          <el-input
            :model-value="formData.custom_class"
            placeholder="css-class-name"
            @update:model-value="handleFieldUpdate('custom_class', $event)"
          />
        </el-form-item>

        <el-form-item label="Visible Rules (JSON)">
          <div
            class="info-box"
            style="margin-bottom: 8px"
          >
            <p>Show/hide field based on conditions</p>
          </div>
          <el-input
            type="textarea"
            :rows="3"
            :model-value="JSON.stringify(formData.visible_rules || [], null, 2)"
            placeholder="[{&quot;field&quot;: &quot;status&quot;, &quot;value&quot;: &quot;active&quot;}]"
            @change="(val) => {
              try {
                handleFieldUpdate('visible_rules', JSON.parse(val))
              } catch (e) {
                // Ignore
              }
            }"
          />
        </el-form-item>

        <el-form-item label="Validation Rules (JSON)">
          <div
            class="info-box"
            style="margin-bottom: 8px"
          >
            <p>Examples: [{"logic": "data.amount > 1000", "message": "Too high"}]</p>
          </div>
          <el-input
            type="textarea"
            :rows="4"
            :model-value="JSON.stringify(formData.validation_rules || [], null, 2)"
            placeholder="[{&quot;logic&quot;: &quot;...&quot;, &quot;message&quot;: &quot;...&quot;}]"
            @change="(val) => {
              try {
                handleFieldUpdate('validation_rules', JSON.parse(val))
              } catch (e) {
                // Ignore
              }
            }"
          />
        </el-form-item>

        <template v-if="formData.field_type === 'reference'">
          <el-divider />
          <div class="prop-group-title">
            Reference Options
          </div>
          <el-form-item label="Filters (JSON)">
            <el-input
              type="textarea"
              :rows="3"
              :model-value="JSON.stringify(formData.reference_filters || {}, null, 2)"
              placeholder="{&quot;department&quot;: &quot;current_user.department&quot;}"
              @change="(val) => {
                try {
                  handleFieldUpdate('reference_filters', JSON.parse(val))
                } catch (e) {
                  // Ignore parse error, maybe show alert
                }
              }"
            />
          </el-form-item>
        </template>

        <el-divider />

        <div class="prop-actions">
          <el-button
            type="danger"
            :icon="Delete"
            size="small"
            @click="handleDelete"
          >
            Remove Field
          </el-button>
        </div>
      </el-form>

      <!-- Section Properties -->
      <el-form
        v-else-if="sectionProps"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Section Properties
        </div>

        <el-form-item label="Section ID">
          <el-input
            :model-value="formData.id"
            disabled
          />
        </el-form-item>

        <el-form-item label="Title">
          <el-input
            :model-value="formData.title"
            @update:model-value="handleFieldUpdate('title', $event)"
          />
        </el-form-item>

        <el-form-item label="Columns">
          <el-slider
            :model-value="formData.columns || 2"
            :min="1"
            :max="4"
            :marks="{ 1: '1', 2: '2', 3: '3', 4: '4' }"
            @update:model-value="handleFieldUpdate('columns', $event)"
          />
        </el-form-item>

        <el-divider />

        <div class="prop-group-title">
          Display Options
        </div>

        <el-form-item>
          <template #label>
            <span>Collapsible</span>
          </template>
          <el-switch
            :model-value="formData.collapsible ?? false"
            @update:model-value="handleFieldUpdate('collapsible', $event)"
          />
        </el-form-item>

        <el-form-item v-if="formData.collapsible">
          <template #label>
            <span>Collapsed by Default</span>
          </template>
          <el-switch
            :model-value="formData.collapsed ?? false"
            @update:model-value="handleFieldUpdate('collapsed', $event)"
          />
        </el-form-item>

        <el-form-item>
          <template #label>
            <span>Show Border</span>
          </template>
          <el-switch
            :model-value="formData.border ?? true"
            @update:model-value="handleFieldUpdate('border', $event)"
          />
        </el-form-item>

        <el-form-item label="Icon">
          <el-input
            :model-value="formData.icon"
            placeholder="e.g. Folder, Document, Star"
            @update:model-value="handleFieldUpdate('icon', $event)"
          />
        </el-form-item>

        <el-form-item label="Background Color">
          <el-color-picker
            :model-value="formData.background_color"
            show-alpha
            @update:model-value="handleFieldUpdate('background_color', $event)"
          />
        </el-form-item>

        <el-form-item label="Custom CSS Class">
          <el-input
            :model-value="formData.custom_class"
            placeholder="css-class-name"
            @update:model-value="handleFieldUpdate('custom_class', $event)"
          />
        </el-form-item>

        <el-divider />

        <div class="prop-actions">
          <el-button
            :icon="Delete"
            type="danger"
            size="small"
            @click="handleDelete"
          >
            Remove Section
          </el-button>
        </div>
      </el-form>

      <!-- Tab Section Properties -->
      <el-form
        v-else-if="elementType === 'tabSection'"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Tab Section Properties
        </div>

        <el-form-item label="Section ID">
          <el-input
            :model-value="formData.id"
            disabled
          />
        </el-form-item>

        <div class="info-box">
          <p>Edit individual tab properties by clicking on the tab in the canvas.</p>
        </div>

        <el-divider />

        <div class="prop-actions">
          <el-button
            :icon="Delete"
            type="danger"
            size="small"
            @click="handleDelete"
          >
            Remove Tab Section
          </el-button>
        </div>
      </el-form>

      <!-- Tab Item Properties -->
      <el-form
        v-else-if="tabProps"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Tab Properties
        </div>

        <el-form-item label="Tab ID">
          <el-input
            :model-value="formData.id"
            disabled
          />
        </el-form-item>

        <el-form-item label="Tab Title">
          <el-input
            :model-value="formData.title"
            @update:model-value="handleFieldUpdate('title', $event)"
          />
        </el-form-item>
      </el-form>

      <!-- Column Section Properties -->
      <el-form
        v-else-if="elementType === 'columnSection'"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Column Section Properties
        </div>

        <el-form-item label="Section ID">
          <el-input
            :model-value="formData.id"
            disabled
          />
        </el-form-item>

        <div class="info-box">
          <p>Edit individual column properties by clicking on the column in the canvas.</p>
        </div>

        <el-divider />

        <div class="prop-actions">
          <el-button
            :icon="Delete"
            type="danger"
            size="small"
            @click="handleDelete"
          >
            Remove Column Section
          </el-button>
        </div>
      </el-form>

      <!-- Column Item Properties -->
      <el-form
        v-else-if="columnItemProps"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Column Properties
        </div>

        <el-form-item label="Column ID">
          <el-input
            :model-value="formData.id"
            disabled
          />
        </el-form-item>

        <el-form-item label="Column Span">
          <el-slider
            :model-value="formData.span || 12"
            :min="1"
            :max="24"
            :marks="{ 6: '1/4', 12: '1/2', 24: 'Full' }"
            @update:model-value="handleFieldUpdate('span', $event)"
          />
        </el-form-item>
      </el-form>

      <!-- Collapse Section Properties -->
      <el-form
        v-else-if="elementType === 'collapseSection'"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Collapse Section Properties
        </div>

        <el-form-item label="Section ID">
          <el-input
            :model-value="formData.id"
            disabled
          />
        </el-form-item>

        <div class="info-box">
          <p>Edit individual accordion item properties by clicking on the item in the canvas.</p>
        </div>

        <el-divider />

        <div class="prop-actions">
          <el-button
            :icon="Delete"
            type="danger"
            size="small"
            @click="handleDelete"
          >
            Remove Accordion Section
          </el-button>
        </div>
      </el-form>

      <!-- List Column Properties -->
      <el-form
        v-else-if="listColumnProps"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          List Column Properties
        </div>

        <el-form-item label="Column Code">
          <el-input
            :model-value="formData.field_code"
            disabled
          />
        </el-form-item>

        <el-form-item label="Column Label">
          <el-input
            :model-value="formData.label"
            @update:model-value="handleFieldUpdate('label', $event)"
          />
        </el-form-item>

        <el-form-item label="Column Width">
          <el-input-number
            :model-value="formData.width"
            :min="50"
            :max="500"
            :step="10"
            style="width: 100%"
            @update:model-value="handleFieldUpdate('width', $event)"
          />
        </el-form-item>

        <el-form-item label="Fixed Position">
          <el-select
            :model-value="formData.fixed"
            clearable
            placeholder="Not fixed"
            style="width: 100%"
            @update:model-value="handleFieldUpdate('fixed', $event)"
          >
            <el-option
              label="Left"
              value="left"
            />
            <el-option
              label="Right"
              value="right"
            />
          </el-select>
        </el-form-item>

        <el-form-item>
          <template #label>
            <span>Sortable</span>
          </template>
          <el-switch
            :model-value="formData.sortable ?? true"
            @update:model-value="handleFieldUpdate('sortable', $event)"
          />
        </el-form-item>

        <el-divider />

        <div class="prop-actions">
          <el-button
            :icon="Delete"
            type="danger"
            size="small"
            @click="handleDelete"
          >
            Remove Column
          </el-button>
        </div>
      </el-form>

      <!-- Divider Properties -->
      <el-form
        v-else-if="elementType === 'divider'"
        label-position="top"
        size="small"
      >
        <div class="prop-group-title">
          Divider Properties
        </div>

        <el-form-item label="Divider ID">
          <el-input
            :model-value="formData.id"
            disabled
          />
        </el-form-item>

        <el-divider />

        <div class="prop-actions">
          <el-button
            :icon="Delete"
            type="danger"
            size="small"
            @click="handleDelete"
          >
            Remove Divider
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.property-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
  border-left: 1px solid #dcdfe6;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 4px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: #909399;
}

.empty-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.3;
}

.prop-group-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
}

.info-box {
  background: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.info-box p {
  margin: 0;
  font-size: 12px;
  color: #409eff;
  line-height: 1.5;
}

.prop-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.prop-actions .el-button {
  width: 100%;
}

:deep(.el-form-item) {
  margin-bottom: 16px;
}

:deep(.el-form-item__label) {
  font-size: 12px;
  color: #606266;
  padding-bottom: 4px;
}

:deep(.el-divider) {
  margin: 20px 0;
}

:deep(.el-input-number) {
  width: 100%;
}
</style>
