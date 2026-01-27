<!--
  ComponentPanel.vue - Left panel of layout designer
  Displays available sections and fields for drag-drop onto canvas
-->

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElInput, ElTree } from 'element-plus'
import Sortable from 'sortablejs'
import type { FieldDefinition } from '@/api/system'

interface SectionType {
  type: string
  label: string
  icon: string
  description: string
}

const props = defineProps<{
  fieldDefinitions?: FieldDefinition[]
  layoutType: 'form' | 'list' | 'detail' | 'search'
}>()

const emit = defineEmits<{
  (e: 'add-section', type: string): void
  (e: 'add-field', field: FieldDefinition): void
  (e: 'add-multiple-fields', fields: FieldDefinition[]): void
}>()

const searchQuery = ref('')
const activeTab = ref<'sections' | 'fields'>('fields')

// Available section types based on layout type
const sectionTypes = computed<SectionType[]>(() => {
  const base: SectionType[] = [
    { type: 'section', label: 'Section', icon: 'Grid', description: 'Basic section with fields' },
    { type: 'divider', label: 'Divider', icon: 'Minus', description: 'Horizontal divider' }
  ]

  if (props.layoutType === 'form' || props.layoutType === 'detail') {
    base.push(
      { type: 'tab', label: 'Tab Section', icon: 'Tickets', description: 'Tabbed content sections' },
      { type: 'collapse', label: 'Collapse', icon: 'FolderOpened', description: 'Collapsible accordion' },
      { type: 'column', label: 'Column Section', icon: 'Operation', description: 'Multi-column layout' }
    )
  }

  return base
})

// Filter fields by search query
const filteredFields = computed(() => {
  if (!props.fieldDefinitions) return []

  const query = searchQuery.value.toLowerCase().trim()
  if (!query) return props.fieldDefinitions

  return props.fieldDefinitions.filter(field =>
    field.name?.toLowerCase().includes(query) ||
    field.code?.toLowerCase().includes(query) ||
    field.field_type?.toLowerCase().includes(query)
  )
})

// Group fields by type
const fieldsByType = computed(() => {
  const groups: Record<string, FieldDefinition[]> = {}

  filteredFields.value.forEach(field => {
    const type = field.field_type || 'unknown'
    if (!groups[type]) {
      groups[type] = []
    }
    groups[type].push(field)
  })

  return groups
})

// Field type icons
const fieldTypeIcons: Record<string, string> = {
  char: 'Edit',
  text: 'Document',
  integer: 'Histogram',
  decimal: 'Histogram',
  boolean: 'CircleCheck',
  date: 'Calendar',
  datetime: 'Timer',
  email: 'Message',
  url: 'Link',
  reference: 'Connection',
  user: 'User',
  department: 'OfficeBuilding',
  file: 'Folder',
  image: 'Picture',
  select: 'Select',
  multiselect: 'Select',
  radio: 'CircleCheck',
  checkbox: 'Check',
  textarea: 'Document',
  formula: 'Magic',
  subtable: 'Grid'
}

function handleSectionClick(type: string) {
  emit('add-section', type)
}

function handleFieldClick(field: FieldDefinition) {
  emit('add-field', field)
}

function handleAddAllFields() {
  emit('add-multiple-fields', filteredFields.value)
}

// Check if field can be added to current layout type
function canAddField(field: FieldDefinition): boolean {
  // Reference fields and subtables might not work well in list layouts
  if (props.layoutType === 'list') {
    return !field.reference_object && field.field_type !== 'subtable'
  }
  return true
}

// Drag and Drop
const sectionListRef = ref<HTMLElement | null>(null)
const fieldListRefs = ref<Record<string, HTMLElement>>({})

onMounted(() => {
  // Initialize Sortable for Sections
  if (sectionListRef.value) {
    new Sortable(sectionListRef.value, {
      group: {
        name: 'shared',
        pull: 'clone',
        put: false
      },
      sort: false,
      draggable: '.section-item',
      onStart: (evt) => {
        evt.item.classList.add('is-dragging')
      },
      onEnd: (evt) => {
        evt.item.classList.remove('is-dragging')
      }
    })
  }
})

// Initialize Sortable for Fields when they are rendered
// We watch filteredFields/activeTab or just check periodically, but since lists change,
// might be better to use a directive or just init on mounted and re-init if structure changes drastically.
// simplified: init on mounted and watch activeTab. 
// Actually, using MutationObserver or just ref function is safer for v-for.
// For now, let's just expose a ref function for the v-for loop.
const setFieldListRef = (el: any, type: string) => {
  if (el) {
    fieldListRefs.value[type] = el
    initFieldSortable(el)
  }
}

function initFieldSortable(el: HTMLElement) {
    // Check if already initialized to avoid duplicates? Sortable internal check?
    // Sortable doesn't prevent double init on same element easily without checking instance.
    // We can store instance on element.
    if ((el as any)._sortable) return

    ;(el as any)._sortable = new Sortable(el, {
      group: {
        name: 'shared',
        pull: 'clone',
        put: false
      },
      sort: false,
      draggable: '.field-item:not(.disabled)',
      onStart: (evt) => {
        evt.item.classList.add('is-dragging')
      },
      onEnd: (evt) => {
        evt.item.classList.remove('is-dragging')
      }
    })
}
</script>

<template>
  <div class="component-panel">
    <div class="panel-header">
      <h3>Components</h3>
      <div class="tab-switcher">
        <button
          :class="['tab-btn', { active: activeTab === 'fields' }]"
          @click="activeTab = 'fields'"
        >
          Fields
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'sections' }]"
          @click="activeTab = 'sections'"
        >
          Sections
        </button>
      </div>
    </div>

    <!-- Fields Tab -->
    <div
      v-show="activeTab === 'fields'"
      class="panel-content fields-tab"
    >
      <div class="search-box">
        <el-input
          v-model="searchQuery"
          placeholder="Search fields..."
          clearable
          prefix-icon="Search"
        />
      </div>

      <div
        v-if="filteredFields.length === 0"
        class="empty-state"
      >
        <p>No fields available</p>
      </div>

      <div
        v-else
        class="fields-container"
      >
        <div class="fields-header">
          <span class="count">{{ filteredFields.length }} fields</span>
          <el-button
            size="small"
            text
            type="primary"
            @click="handleAddAllFields"
          >
            Add All
          </el-button>
        </div>

        <div
          v-for="(fields, type) in fieldsByType"
          :key="type"
          class="field-group"
        >
          <div class="group-header">
            <span class="group-name">{{ type }}</span>
            <span class="group-count">{{ fields.length }}</span>
          </div>

          <div
            :ref="(el) => setFieldListRef(el, type)"
            class="field-list"
          >
            <div
              v-for="field in fields"
              :key="field.id"
              :class="['field-item', { disabled: !canAddField(field) }]"
              :title="!canAddField(field) ? 'This field type is not supported for list layouts' : field.name"
              :data-id="field.id"
              :data-code="field.code"
              :data-type="field.field_type"
              :data-label="field.name || field.code"
              data-is-field="true"
              @click="canAddField(field) && handleFieldClick(field)"
            >
              <span class="field-icon">
                <el-icon>
                  <component :is="fieldTypeIcons[field.field_type] || 'Edit'" />
                </el-icon>
              </span>
              <div class="field-info">
                <span class="field-label">{{ field.name || field.code }}</span>
                <span class="field-code">{{ field.code }}</span>
              </div>
              <span
                v-if="field.is_required"
                class="required-badge"
              >Required</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sections Tab -->
    <div
      v-show="activeTab === 'sections'"
      class="panel-content sections-tab"
    >
      <div
        ref="sectionListRef"
        class="section-list"
      >
        <div
          v-for="section in sectionTypes"
          :key="section.type"
          class="section-item"
          :data-type="section.type"
          :data-label="section.label"
          data-is-section="true"
          @click="handleSectionClick(section.type)"
        >
          <span class="section-icon">
            <el-icon>
              <component :is="section.icon" />
            </el-icon>
          </span>
          <div class="section-info">
            <span class="section-label">{{ section.label }}</span>
            <span class="section-description">{{ section.description }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Edit, Document, Histogram, CircleCheck, Calendar, Timer, Message, Link, Connection, User, OfficeBuilding, Folder, Picture, Select, Grid, Minus, Tickets, FolderOpened, Operation, Search, Star } from '@element-plus/icons-vue'

export default {
  components: {
    Edit, Document, Histogram, CircleCheck, Calendar, Timer, Message, Link, Connection,
    User, OfficeBuilding, Folder, Picture, Select, Grid, Minus, Tickets, FolderOpened,
    Operation, Search, Star
  }
}
</script>

<style scoped>
.component-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
  border-right: 1px solid #dcdfe6;
}

.panel-header {
  padding: 16px;
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
}

.panel-header h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.tab-switcher {
  display: flex;
  gap: 4px;
  background: #f5f7fa;
  padding: 4px;
  border-radius: 6px;
}

.tab-btn {
  flex: 1;
  padding: 6px 12px;
  border: none;
  background: transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #409eff;
}

.tab-btn.active {
  background: #fff;
  color: #409eff;
  font-weight: 500;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

/* Fields Tab */
.search-box {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.fields-container {
  padding: 12px;
}

.fields-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 8px;
}

.count {
  font-size: 12px;
  color: #909399;
}

.field-group {
  margin-bottom: 16px;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #e4e7ed;
  border-radius: 6px;
  margin-bottom: 8px;
}

.group-name {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
  text-transform: capitalize;
}

.group-count {
  font-size: 11px;
  color: #909399;
  background: #fff;
  padding: 2px 8px;
  border-radius: 10px;
}

.field-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.field-item:hover:not(.disabled) {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
  transform: translateX(2px);
}

.field-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.field-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f5f7fa;
  border-radius: 6px;
  color: #606266;
}

.field-info {
  flex: 1;
  min-width: 0;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.field-code {
  display: block;
  font-size: 11px;
  color: #909399;
  font-family: monospace;
}

.required-badge {
  font-size: 10px;
  color: #f56c6c;
  background: #fef0f0;
  padding: 2px 6px;
  border-radius: 4px;
}

/* Sections Tab */
.section-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.section-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}

.section-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  border-radius: 8px;
  color: #fff;
}

.section-info {
  flex: 1;
}

.section-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.section-description {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: #909399;
}
</style>
