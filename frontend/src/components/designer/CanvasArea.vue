<!--
  CanvasArea.vue - Center canvas of layout designer
  Renders the layout structure with interactive elements
-->

<script setup lang="tsx">
import { ref, computed } from 'vue'
import { ElButton, ElInput, ElInputNumber, ElSwitch, ElIcon, ElTooltip } from 'element-plus'
import { Delete, Plus, CopyDocument, More, Edit, Rank, Lock, Unlock, View, Hide, Grid, Tickets, Document, FolderOpened, Operation } from '@element-plus/icons-vue'
import Sortable from 'sortablejs'

type LayoutType = 'form' | 'list' | 'detail' | 'search'

interface LayoutField {
  id: string
  field_code: string
  label: string
  span: number
  readonly?: boolean
  visible?: boolean
  required?: boolean
}

interface LayoutSection {
  id: string
  type: string
  title?: string
  collapsible?: boolean
  collapsed?: boolean
  border?: boolean
  columns?: number
  fields?: LayoutField[]
  tabs?: LayoutTab[]
  items?: LayoutCollapseItem[]
  columns_array?: LayoutColumnItem[]
}

interface LayoutTab {
  id: string
  title: string
  fields?: LayoutField[]
}

interface LayoutCollapseItem {
  id: string
  title: string
  fields?: LayoutField[]
}

interface LayoutColumnItem {
  id: string
  span?: number
  fields?: LayoutField[]
}

interface LayoutConfig {
  sections?: LayoutSection[]
  columns?: Array<{ field_code: string; label: string; width?: number }>
  actions?: Array<{ code: string; label: string; type: string; position: string }>
}

const props = defineProps<{
  layoutConfig: LayoutConfig
  layoutType: LayoutType
  selectedId: string
}>()

const emit = defineEmits<{
  (e: 'select', id: string): void
  (e: 'delete', id: string): void
  (e: 'update', id: string, data: any): void
  (e: 'add-field', id: string): void
  (e: 'reorder', fromId: string, toId: string, position: 'before' | 'after'): void
  // New emits for DnD
  (e: 'drop-new', containerId: string, data: any, index: number): void
  (e: 'move-item', fromContainer: string, toContainer: string, oldIndex: number, newIndex: number): void
}>()

const hoveredId = ref('')

// Computed sections for form/detail layouts
const sections = computed(() => props.layoutConfig?.sections || [])

// Computed columns for list layouts
const listColumns = computed(() => props.layoutConfig?.columns || [])

// Computed actions
const actions = computed(() => props.layoutConfig?.actions || [])

// Check if item is selected
const isSelected = (id: string) => props.selectedId === id

// Check if item is hovered
const isHovered = (id: string) => hoveredId.value === id

// Handle selection
function handleSelect(e: Event, id: string) {
  e.stopPropagation()
  emit('select', id)
}

// Handle delete
function handleDelete(e: Event, id: string) {
  e.stopPropagation()
  emit('delete', id)
}

// Handle inline update
function handleUpdate(id: string, field: string, value: any) {
  emit('update', id, { [field]: value })
}

// Quick actions menu
function showQuickActions(e: Event, id: string) {
  e.stopPropagation()
  // Could trigger a dropdown menu here
  emit('select', id)
}

// Sortable Init
const initSortable = (el: HTMLElement | null, type: 'root' | 'container', id: string) => {
  if (!el || (el as any)._sortable) return

  ;(el as any)._sortable = new Sortable(el, {
    group: {
      name: 'shared',
      pull: true,
      put: true
    },
    animation: 150,
    handle: type === 'root' ? '.section-header' : '.field-badge', // Drag handle
    draggable: type === 'root' ? '.canvas-item' : '.field-badge',
    onAdd: (evt) => {
      const item = evt.item
      // Check if it's a new item from panel
      const isNewField = item.dataset.isField === 'true'
      const isNewSection = item.dataset.isSection === 'true'

      if (isNewField || isNewSection) {
        // It's a drops from panel
        const data = {
           code: item.dataset.code,
           type: item.dataset.type,
           label: item.dataset.label
        }
        // Remove from DOM to let Vue render
        item.remove()
        
        if (isNewField) {
           emit('drop-new', id, data, evt.newIndex || 0)
        } else if (isNewSection && type === 'root') {
           // Handle section drop
           // For now only fields drop is critical
           // emit('drop-section', data, evt.newIndex)
        }
      } else {
        // It's a move from another container
        // We need to know source container. Sortable gives evt.from
        // But we need the ID.
        // We can't easily get ID from DOM unless we store it.
        // Let's assume we handle 'onEnd' in the source instead?
        // Actually onAdd triggers in Target.
        // We need to let Vue handle state.
        item.remove() // Remove DOM, rely on state update
        // We need to emit event to move item.
        // Getting 'from' container ID is tricky without data attributes on container.
      }
    },
    onUpdate: (evt) => {
      // Reorder within same container
      emit('move-item', id, id, evt.oldIndex || 0, evt.newIndex || 0)
    },
    onEnd: (evt) => {
       // Drag between containers. 
       // onEnd triggers on Source.
       if (evt.to !== evt.from) {
          // This is a move
          // We can try to identify target container ID
          // We should add data-id to all containers
          const targetId = evt.to.dataset.containerId
          if (targetId) {
             emit('move-item', id, targetId, evt.oldIndex || 0, evt.newIndex || 0)
          }
       }
    }
  })
}

// Get item classes
function getItemClasses(id: string, type: string) {
  return [
    'canvas-item',
    `item-${type}`,
    { 'is-selected': isSelected(id), 'is-hovered': isHovered(id) }
  ]
}

// Render field badge
function renderField(field: LayoutField, parentId: string) {
  return (
    <div
      class={[
        'field-badge',
        { 'is-selected': isSelected(field.id), 'is-readonly': field.readonly }
      ]}
      onClick={(e: Event) => handleSelect(e, field.id)}
      onMouseenter={() => hoveredId.value = field.id}
      onMouseleave={() => hoveredId.value = ''}
    >
      <span class="field-icon">
        <ElIcon><Edit /></ElIcon>
      </span>
      <span class="field-label">{field.label}</span>
      <span class="field-span">{field.span}</span>
      {field.required && <span class="required-mark">*</span>}
      {field.readonly && <span class="readonly-badge"><ElIcon><Lock /></ElIcon></span>}
      {!field.visible && <span class="hidden-badge"><ElIcon><Hide /></ElIcon></span>}

      {isSelected(field.id) && (
        <div class="field-actions">
          <ElTooltip content="Edit properties">
            <ElButton size="small" icon={<Edit />} text />
          </ElTooltip>
          <ElTooltip content="Duplicate">
            <ElButton size="small" icon={<CopyDocument />} text />
          </ElTooltip>
          <ElTooltip content="Remove">
            <ElButton size="small" icon={<Delete />} text type="danger" onClick={(e: Event) => handleDelete(e, field.id)} />
          </ElTooltip>
        </div>
      )}
    </div>
  )
}

// Render basic section
function renderSection(props: { section: LayoutSection }) {
  const { section } = props
  const fieldCount = section.fields?.length || 0

  return (
    <div
      key={section.id}
      class={getItemClasses(section.id, 'section')}
      onClick={(e: Event) => handleSelect(e, section.id)}
      onMouseenter={() => hoveredId.value = section.id}
      onMouseleave={() => hoveredId.value = ''}
    >
      <div class="section-header">
        <div class="section-title-row">
          <span class="section-icon">
            <ElIcon><Rank /></ElIcon>
          </span>
          <ElInput
            modelValue={section.title}
            size="small"
            placeholder="Section Title"
            class="title-input"
            onUpdate:modelValue={(val: string) => handleUpdate(section.id, 'title', val)}
            onClick={(e: Event) => e.stopPropagation()}
          />
          <span class="field-count">{fieldCount} fields</span>
        </div>

        {isSelected(section.id) && (
          <div class="section-actions" onClick={(e: Event) => e.stopPropagation()}>
            <ElTooltip content="Add field">
              <ElButton size="small" icon={<Plus />} text type="primary" onClick={() => emit('add-field', section.id)} />
            </ElTooltip>
            <ElTooltip content="Duplicate">
              <ElButton size="small" icon={<CopyDocument />} text />
            </ElTooltip>
            <ElTooltip content="Remove">
              <ElButton size="small" icon={<Delete />} text type="danger" onClick={(e: Event) => handleDelete(e, section.id)} />
            </ElTooltip>
          </div>
        )}
      </div>

      <div 
        class="section-fields" 
        style={{ gridTemplateColumns: `repeat(${section.columns || 2}, 1fr)` }}
        ref={(el) => initSortable(el as HTMLElement, 'container', section.id)}
        data-container-id={section.id}
      >
        {section.fields?.map(field => renderField(field, section.id)) || (
          <div class="empty-fields" onClick={() => emit('add-field', section.id)}>
            <ElIcon><Plus /></ElIcon>
            <span>Drop fields here</span>
          </div>
        )}
      </div>

      {isSelected(section.id) && (
        <div class="section-props">
          <div class="prop-row">
            <span>Columns:</span>
            <ElInputNumber
              modelValue={section.columns}
              min={1}
              max={4}
              size="small"
              onUpdate:modelValue={(val: number) => handleUpdate(section.id, 'columns', val)}
            />
          </div>
          <div class="prop-row">
            <span>Collapsible:</span>
            <ElSwitch
              modelValue={section.collapsible}
              onUpdate:modelValue={(val: boolean) => handleUpdate(section.id, 'collapsible', val)}
            />
          </div>
          <div class="prop-row">
            <span>Border:</span>
            <ElSwitch
              modelValue={section.border}
              onUpdate:modelValue={(val: boolean) => handleUpdate(section.id, 'border', val)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

// Render tab section
function renderTabSection(props: { section: LayoutSection }) {
  const { section } = props
  return (
    <div
      key={section.id}
      class={getItemClasses(section.id, 'tab')}
      onClick={(e: Event) => handleSelect(e, section.id)}
      onMouseenter={() => hoveredId.value = section.id}
      onMouseleave={() => hoveredId.value = ''}
    >
      <div class="tab-header">
        <ElIcon><Tickets /></ElIcon>
        <span>Tabs</span>
        {isSelected(section.id) && (
          <ElButton size="small" icon={<Delete />} text type="danger" onClick={(e: Event) => handleDelete(e, section.id)} />
        )}
      </div>

      {section.tabs?.map(tab => (
        <div key={tab.id} class="tab-item">
          <div class="tab-title-row">
            <ElIcon><Document /></ElIcon>
            <ElInput
              modelValue={tab.title}
              size="small"
              class="title-input"
              onUpdate:modelValue={(val: string) => handleUpdate(tab.id, 'title', val)}
              onClick={(e: Event) => e.stopPropagation()}
            />
          </div>
          <div 
            class="tab-fields"
            ref={(el) => initSortable(el as HTMLElement, 'container', tab.id)}
            data-container-id={tab.id}
          >
            {tab.fields?.map(field => renderField(field, tab.id))}
          </div>
        </div>
      )) || (
        <div class="empty-tabs">No tabs configured</div>
      )}
    </div>
  )
}

// Render collapse section
function renderCollapseSection(props: { section: LayoutSection }) {
  const { section } = props
  return (
    <div
      key={section.id}
      class={getItemClasses(section.id, 'collapse')}
      onClick={(e: Event) => handleSelect(e, section.id)}
      onMouseenter={() => hoveredId.value = section.id}
      onMouseleave={() => hoveredId.value = ''}
    >
      <div class="collapse-header">
        <ElIcon><FolderOpened /></ElIcon>
        <span>Accordion</span>
        {isSelected(section.id) && (
          <ElButton size="small" icon={<Delete />} text type="danger" onClick={(e: Event) => handleDelete(e, section.id)} />
        )}
      </div>

      {section.items?.map(item => (
        <div key={item.id} class="collapse-item">
          <div class="collapse-item-title">
            <ElIcon><More /></ElIcon>
            <ElInput
              modelValue={item.title}
              size="small"
              class="title-input"
              onUpdate:modelValue={(val: string) => handleUpdate(item.id, 'title', val)}
              onClick={(e: Event) => e.stopPropagation()}
            />
          </div>
          <div 
            class="collapse-item-fields"
            ref={(el) => initSortable(el as HTMLElement, 'container', item.id)}
            data-container-id={item.id}
          >
            {item.fields?.map(field => renderField(field, item.id))}
          </div>
        </div>
      )) || (
        <div class="empty-items">No accordion items configured</div>
      )}
    </div>
  )
}

// Render column section
function renderColumnSection(props: { section: LayoutSection }) {
  const { section } = props
  return (
    <div
      key={section.id}
      class={getItemClasses(section.id, 'column')}
      onClick={(e: Event) => handleSelect(e, section.id)}
      onMouseenter={() => hoveredId.value = section.id}
      onMouseleave={() => hoveredId.value = ''}
    >
      <div class="column-header">
        <ElIcon><Operation /></ElIcon>
        <span>Column Layout</span>
        {isSelected(section.id) && (
          <ElButton size="small" icon={<Delete />} text type="danger" onClick={(e: Event) => handleDelete(e, section.id)} />
        )}
      </div>

      <div class="column-container" style={{ display: 'flex', gap: '12px' }}>
        {section.columns_array?.map(col => (
          <div
            key={col.id}
            class="column-item"
            style={{ flex: col.span || 1 }}
          >
            <div class="column-header">
              <span>Span: {col.span}</span>
            </div>
            <div 
              class="column-content"
              ref={(el) => initSortable(el as HTMLElement, 'container', col.id)}
              data-container-id={col.id}
            >
              {col.fields?.map(field => renderField(field, col.id))}
            </div>
          </div>
        )) || (
          <div class="empty-columns">No columns configured</div>
        )}
      </div>
    </div>
  )
}

// Render divider
function renderDivider(props: { section: LayoutSection }) {
  const { section } = props
  return (
    <div
      key={section.id}
      class={getItemClasses(section.id, 'divider')}
      onClick={(e: Event) => handleSelect(e, section.id)}
    >
      <hr />
      {isSelected(section.id) && (
        <ElButton size="small" icon={<Delete />} text type="danger" onClick={(e: Event) => handleDelete(e, section.id)}>
          Remove Divider
        </ElButton>
      )}
    </div>
  )
}

// Render list layout columns
function renderListLayout() {
  return (
    <div class="list-layout">
      <div class="list-header">
        <h4>List Columns</h4>
        <ElButton size="small" icon={<Plus />}>Add Column</ElButton>
      </div>
      <div class="list-columns">
        {listColumns.value.map(col => (
          <div
            key={col.field_code}
            class={['list-column', { 'is-selected': isSelected(col.field_code) }]}
            onClick={(e: Event) => handleSelect(e, col.field_code)}
          >
            <span class="column-label">{col.label}</span>
            <span class="column-code">{col.field_code}</span>
            <span class="column-width">{col.width || 'auto'}</span>
            {isSelected(col.field_code) && (
              <ElButton size="small" icon={<Delete />} text type="danger" onClick={(e: Event) => handleDelete(e, col.field_code)} />
            )}
          </div>
        )) || (
          <div class="empty-columns">No columns configured</div>
        )}
      </div>
    </div>
  )
}
</script>

<template>
  <div class="canvas-area">
    <div class="canvas-header">
      <h3>Layout Canvas</h3>
      <div class="canvas-info">
        <span v-if="layoutType === 'form' || layoutType === 'detail'">{{ sections.length }} sections</span>
        <span v-else-if="layoutType === 'list'">{{ listColumns.length }} columns</span>
      </div>
    </div>

    <div class="canvas-content">
      <!-- Empty state -->
      <!-- Empty state/Main Content -->
      <div
        v-if="(layoutType === 'form' || layoutType === 'detail') && sections.length === 0"
        class="empty-canvas"
      >
        <el-icon class="empty-icon">
          <Grid />
        </el-icon>
        <h4>No Layout Sections</h4>
        <p>Add sections from the left panel to start designing your layout</p>
      </div>
      
      <!-- Root sections container -->
      <template v-else-if="layoutType === 'form' || layoutType === 'detail'">
        <div 
          :ref="(el) => initSortable(el as HTMLElement, 'root', 'root')" 
          class="sections-container"
          data-container-id="root"
        >
          <div
            v-for="section in sections"
            :key="section.id"
            class="section-wrapper"
          >
            <component
              :is="{
                section: renderSection,
                tab: renderTabSection,
                collapse: renderCollapseSection,
                column: renderColumnSection,
                divider: renderDivider
              }[section.type]"
              :section="section"
            />
          </div>
        </div>
      </template>

      <!-- List Layout -->
      <template v-else-if="layoutType === 'list'">
        <component :is="renderListLayout()" />
      </template>
    </div>
  </div>
</template>



<style scoped>
.canvas-area {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f0f2f5;
}

.canvas-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-bottom: 1px solid #dcdfe6;
}

.canvas-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.canvas-info {
  font-size: 12px;
  color: #909399;
}

.canvas-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* Empty State */
.empty-canvas {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.3;
}

.empty-canvas h4 {
  margin: 0 0 8px 0;
  font-size: 16px;
  color: #606266;
}

.empty-canvas p {
  margin: 0;
  font-size: 13px;
}

/* Canvas Items */
.canvas-item {
  background: #fff;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  margin-bottom: 16px;
  transition: all 0.2s;
}

.canvas-item.is-selected {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

.canvas-item.is-hovered:hover {
  border-color: #c0c4cc;
}

/* Section Styles */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  border-radius: 6px 6px 0 0;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.section-icon {
  color: #409eff;
}

.title-input {
  flex: 1;
  max-width: 200px;
}

.field-count {
  font-size: 11px;
  color: #909399;
  background: #e4e7ed;
  padding: 2px 8px;
  border-radius: 10px;
}

.section-actions {
  display: flex;
  gap: 4px;
}

.section-fields {
  display: grid;
  gap: 12px;
  padding: 16px;
  min-height: 60px;
}

.empty-fields {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border: 2px dashed #dcdfe6;
  border-radius: 6px;
  color: #909399;
  cursor: pointer;
  transition: all 0.2s;
}

.empty-fields:hover {
  border-color: #409eff;
  color: #409eff;
}

.section-props {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: #fafafa;
  border-top: 1px solid #ebeef5;
  border-radius: 0 0 6px 6px;
}

.prop-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #606266;
}

/* Field Badge */
.field-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s;
}

.field-badge:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.field-badge.is-selected {
  background: #ecf5ff;
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.2);
}

.field-badge.is-readonly {
  opacity: 0.7;
}

.field-icon {
  color: #909399;
}

.field-label {
  flex: 1;
  font-size: 13px;
  color: #303133;
}

.field-span {
  font-size: 10px;
  color: #909399;
  background: #e4e7ed;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.required-mark {
  color: #f56c6c;
  font-weight: bold;
}

.readonly-badge,
.hidden-badge {
  display: flex;
  color: #909399;
  font-size: 12px;
}

.field-actions {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  display: flex;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

/* Tab Section */
.tab-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-bottom: 1px solid #dcdfe6;
  border-radius: 8px 8px 0 0;
}

.tab-item {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
}

.tab-item:last-child {
  border-bottom: none;
}

.tab-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.tab-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-left: 32px;
}

.empty-tabs {
  padding: 24px;
  text-align: center;
  color: #909399;
}

/* Collapse Section */
.collapse-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fdf6ec;
  border-bottom: 1px solid #dcdfe6;
  border-radius: 8px 8px 0 0;
}

.collapse-item {
  padding: 16px;
  border-bottom: 1px solid #ebeef5;
}

.collapse-item:last-child {
  border-bottom: none;
}

.collapse-item-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.collapse-item-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-left: 32px;
}

.empty-items {
  padding: 24px;
  text-align: center;
  color: #909399;
}

/* Column Section */
.column-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f4f4f5;
  border-bottom: 1px solid #dcdfe6;
  border-radius: 8px 8px 0 0;
}

.column-container {
  padding: 16px;
}

.column-item {
  background: #fafafa;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  padding: 12px;
  min-width: 100px;
}

.empty-columns {
  padding: 24px;
  text-align: center;
  color: #909399;
  width: 100%;
}

/* Divider */
.item-divider {
  padding: 16px;
}

.item-divider hr {
  border: none;
  border-top: 2px solid #dcdfe6;
}

/* List Layout */
.list-layout {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.list-header h4 {
  margin: 0;
  font-size: 14px;
  color: #303133;
}

.list-columns {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-column {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
}

.list-column:hover {
  background: #ecf5ff;
  border-color: #409eff;
}

.list-column.is-selected {
  background: #ecf5ff;
  border-color: #409eff;
}

.column-label {
  flex: 1;
  font-size: 13px;
  color: #303133;
}

.column-code {
  font-size: 11px;
  color: #909399;
  font-family: monospace;
}

.column-width {
  font-size: 11px;
  color: #606266;
  background: #e4e7ed;
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
