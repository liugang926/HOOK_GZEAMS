<template>
  <div
    class="layout-designer"
    :class="{ 'preview-mode': previewMode }"
  >
    <!-- Designer Toolbar -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <el-button
          link
          @click="handleCancel"
        >
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <el-divider direction="vertical" />
        <span class="layout-info">{{ layoutName }} ({{ layoutTypeLabel }})</span>
        <el-tag
          v-if="!isDefault"
          type="warning"
          size="small"
          style="margin-left: 8px"
        >
          自定义布局
        </el-tag>
        <el-tag
          v-else
          type="info"
          size="small"
          style="margin-left: 8px"
        >
          默认布局
        </el-tag>
      </div>
      <div class="toolbar-center">
        <el-button-group>
          <el-button
            :disabled="!canUndo"
            @click="undo"
          >
            <el-icon><RefreshLeft /></el-icon>
            撤销
          </el-button>
          <el-button
            :disabled="!canRedo"
            @click="redo"
          >
            <el-icon><RefreshRight /></el-icon>
            重做
          </el-button>
        </el-button-group>
        <el-button-group style="margin-left: 16px">
          <el-button
            :type="previewMode ? 'primary' : ''"
            @click="togglePreview"
          >
            <el-icon><View /></el-icon>
            预览
          </el-button>
          <el-button @click="validateConfig">
            <el-icon><CircleCheck /></el-icon>
            验证
          </el-button>
        </el-button-group>
        <el-button-group style="margin-left: 16px">
          <el-button @click="handleImport">
            <el-icon><Upload /></el-icon>
            导入
          </el-button>
          <el-button @click="handleExport">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </el-button-group>
      </div>
      <div class="toolbar-right">
        <el-button @click="handleReset">
          重置
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSave"
        >
          保存
        </el-button>
        <el-button
          type="success"
          :loading="publishing"
          @click="handlePublish"
        >
          {{ isPublished ? '重新发布' : '发布' }}
        </el-button>
      </div>
    </div>

    <!-- Main Designer Area -->
    <div
      v-show="!previewMode"
      class="designer-main"
    >
      <!-- Component Panel (Left) -->
      <ComponentPanel
        :layout-type="layoutType"
        :field-definitions="availableFields"
        @add-section="handleAddSection"
        @add-field="handleAddField"
        @add-multiple-fields="handleAddMultipleFields"
      />

      <!-- Canvas Area (Center) -->
      <CanvasArea
        :layout-config="layoutConfig"
        :layout-type="layoutType"
        :selected-id="selectedId"
        @select="handleSelect"
        @update="handleUpdateConfig"
        @delete="handleDelete"
        @drop-new="handleDropNew"
        @move-item="handleMoveItem"
      />

      <!-- Property Panel (Right) -->
      <PropertyPanel
        :selected-item="selectedItem"
        :layout-type="layoutType"
        :available-fields="availableFields"
        @update="handleUpdateProperty"
      />
    </div>

    <!-- Preview Panel -->
    <div
      v-show="previewMode"
      class="designer-preview"
    >
      <div class="preview-header">
        <span>预览模式 - 布局预览</span>
        <el-button
          size="small"
          @click="previewMode = false"
        >
          关闭预览
        </el-button>
      </div>
      <div class="preview-content">
        <div class="preview-container">
          <!-- Page Card Simulation -->
          <el-card class="page-card" shadow="never">
            <template #header>
               <div class="card-header">
                 <span>{{ layoutName || '表单预览' }}</span>
               </div>
            </template>
            <DynamicForm
              :business-object="objectCode"
              :layout-code="layoutType"
              :layout-config="layoutConfig"
              :available-fields="availableFields"
              :model-value="sampleData"
            />
          </el-card>
        </div>
      </div>
    </div>

    <!-- Validation Dialog -->
    <el-dialog
      v-model="validationVisible"
      title="布局验证结果"
      width="500px"
    >
      <div
        v-if="validationErrors.length > 0"
        class="validation-errors"
      >
        <el-alert
          v-for="(error, index) in validationErrors.slice(0, 5)"
          :key="index"
          :title="`${error.path}: ${error.message}`"
          type="error"
          :closable="false"
          style="margin-bottom: 8px"
        />
        <div
          v-if="validationErrors.length > 5"
          class="more-errors"
        >
          还有 {{ validationErrors.length - 5 }} 个错误...
        </div>
      </div>
      <el-alert
        v-else
        type="success"
        :closable="false"
      >
        布局配置验证通过！
      </el-alert>
      <template #footer>
        <el-button @click="validationVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>

    <!-- History Dialog -->
    <el-dialog
      v-model="historyVisible"
      title="版本历史"
      width="700px"
    >
      <div class="history-list">
        <el-timeline>
          <el-timeline-item
            v-for="(item, index) in layoutHistory"
            :key="item.id"
            :timestamp="formatTimestamp(item.timestamp)"
            :type="index === 0 ? 'primary' : ''"
          >
            <div class="history-item">
              <span class="history-version">v{{ item.version }}</span>
              <span class="history-action">{{ item.action_display }}</span>
              <span
                v-if="item.change_summary"
                class="history-summary"
              >{{ item.change_summary }}</span>
              <el-button
                v-if="item.version !== layoutVersion"
                size="small"
                link
                type="primary"
                @click="handleRollback(item.version)"
              >
                回滚
              </el-button>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
      <template #footer>
        <el-button @click="historyVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import {
  ArrowLeft,
  RefreshLeft,
  RefreshRight,
  View,
  CircleCheck,
  Upload,
  Download
} from '@element-plus/icons-vue'
import { pageLayoutApi } from '@/api/system'
import { useLayoutHistory } from '@/composables/useLayoutHistory'
import {
  validateLayoutConfig,
  getDefaultLayoutConfig,
  cloneLayoutConfig,
  generateId,
  type LayoutType,
  type ValidationResult
} from '@/utils/layoutValidation'
import ComponentPanel from './ComponentPanel.vue'
import CanvasArea from './CanvasArea.vue'
import PropertyPanel from './PropertyPanel.vue'
import DynamicForm from '@/components/engine/DynamicForm.vue'

// Props
interface Props {
  layoutId?: string
  layoutType?: LayoutType
  objectCode?: string
  layoutName?: string
  businessObjectId?: string
}

const props = withDefaults(defineProps<Props>(), {
  layoutType: 'form',
  layoutName: '布局设计',
  objectCode: '',
  businessObjectId: ''
})

// Emits
const emit = defineEmits<{
  save: [data: Record<string, unknown>]
  cancel: []
  published: [data: Record<string, unknown>]
}>()

// State
const layoutConfig = ref<Record<string, unknown>>(getDefaultLayoutConfig(props.layoutType))
const selectedId = ref<string>('')
const previewMode = ref(false)
const saving = ref(false)
const publishing = ref(false)
const validationVisible = ref(false)
const validationErrors = ref<Array<{path: string; message: string}>>([])
const historyVisible = ref(false)

// Layout metadata
const isDefault = ref(false)
const isPublished = ref(false)
const layoutVersion = ref('1.0.0')
const layoutHistory = ref<any[]>([])

// Available fields (from business object)
const availableFields = ref<any[]>([])

// Sample data for preview
const sampleData = ref<Record<string, unknown>>({})

// History management
const history = useLayoutHistory(layoutConfig, { maxHistory: 50 })
const { canUndo, canRedo, undo, redo } = history

// Computed
const layoutTypeLabel = computed(() => {
  const labels: Record<LayoutType, string> = {
    form: '表单布局',
    list: '列表布局',
    detail: '详情布局',
    search: '搜索布局'
  }
  return labels[props.layoutType] || props.layoutType
})

const selectedItem = computed(() => {
  if (!selectedId.value) return null

  // Find selected item in config
  return findItemById(layoutConfig.value, selectedId.value)
})

// Methods
function findItemById(config: Record<string, unknown>, id: string): any {
  // Search in sections
  const sections = (config.sections as any[]) || []
  for (const section of sections) {
    if (section.id === id) return section

    // Search in nested structures
    if (section.type === 'tab') {
      const tabs = section.tabs || []
      for (const tab of tabs) {
        if (tab.id === id) return tab
      }
    } else if (section.type === 'collapse') {
      const items = section.items || []
      for (const item of items) {
        if (item.id === id) return item
      }
    } else if (section.type === 'column') {
      const columns = section.columns || []
      for (const column of columns) {
        if (column.id === id) return column
      }
    }

    // Search fields in section
    const fields = section.fields || []
    for (const field of fields) {
      if (field.id === id) return field
    }
  }

  // Search in columns (for list layout)
  if (config.columns) {
    for (const column of config.columns as any[]) {
      if (column.id === id) return column
    }
  }

  return null
}

function handleSelect(id: string) {
  selectedId.value = id
}

function handleUpdateConfig(newConfig: Record<string, unknown>) {
  layoutConfig.value = newConfig
  history.push(newConfig, 'Update layout')
}

function handleUpdateProperty(path: string, value: unknown) {
  const newConfig = cloneLayoutConfig(layoutConfig.value)

  // Simple path resolution (e.g., "sections.0.title")
  const parts = path.split('.')
  let current: any = newConfig

  for (let i = 0; i < parts.length - 1; i++) {
    if (!current[parts[i]]) {
      current[parts[i]] = {}
    }
    current = current[parts[i]]
  }

  current[parts[parts.length - 1]] = value

  layoutConfig.value = newConfig
  history.push(newConfig, `Update ${path}`)
}

function handleDelete(id: string) {
  ElMessageBox.confirm('确定要删除此元素吗？', '确认删除', {
    type: 'warning'
  }).then(() => {
    const newConfig = cloneLayoutConfig(layoutConfig.value)
    deleteItemById(newConfig, id)
    layoutConfig.value = newConfig

    if (selectedId.value === id) {
      selectedId.value = ''
    }

    history.push(newConfig, `Delete ${id}`)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

function deleteItemById(config: Record<string, unknown>, id: string): boolean {
  const sections = (config.sections as any[]) || []
  for (let i = sections.length - 1; i >= 0; i--) {
    const section = sections[i]

    // Delete section if matches
    if (section.id === id) {
      sections.splice(i, 1)
      return true
    }

    // Delete from nested structures
    if (section.type === 'tab') {
      const tabs = section.tabs || []
      for (let j = tabs.length - 1; j >= 0; j--) {
        if (tabs[j].id === id) {
          tabs.splice(j, 1)
          return true
        }
        // Delete fields from tab
        if (tabs[j].fields) {
          tabs[j].fields = tabs[j].fields.filter((f: any) => f.id !== id)
        }
      }
    } else if (section.type === 'collapse') {
      const items = section.items || []
      for (let j = items.length - 1; j >= 0; j--) {
        if (items[j].id === id) {
          items.splice(j, 1)
          return true
        }
        // Delete fields from collapse item
        if (items[j].fields) {
          items[j].fields = items[j].fields.filter((f: any) => f.id !== id)
        }
      }
    } else if (section.type === 'column') {
      const columns = section.columns || []
      for (let j = columns.length - 1; j >= 0; j--) {
        if (columns[j].id === id) {
          columns.splice(j, 1)
          return true
        }
        // Delete fields from column
        if (columns[j].fields) {
          columns[j].fields = columns[j].fields.filter((f: any) => f.id !== id)
        }
      }
    } else {
      // Delete fields from basic section
      if (section.fields) {
        section.fields = section.fields.filter((f: any) => f.id !== id)
      }
    }
  }

  // For list layout columns
  if (config.columns) {
    (config.columns as any[]) = (config.columns as any[]).filter((c: any) => c.id !== id)
  }

  return false
}

function handleAddSection(type: string) {
  const newConfig = cloneLayoutConfig(layoutConfig.value)

  if (!newConfig.sections) {
    newConfig.sections = []
  }

  const newSection: any = {
    id: generateId(type),
    type
  }

  switch (type) {
    case 'section':
      newSection.title = '新区块'
      newSection.collapsible = true
      newSection.collapsed = false
      newSection.columns = 2
      newSection.border = true
      newSection.fields = []
      break
    case 'tab':
      newSection.title = '标签页'
      newSection.tabs = [
        {
          id: generateId('tab'),
          title: '标签1',
          fields: []
        },
        {
          id: generateId('tab'),
          title: '标签2',
          fields: []
        }
      ]
      break
    case 'divider':
      // Divider doesn't need extra properties
      break
    case 'collapse':
      newSection.items = [
        {
          id: generateId('collapse-item'),
          title: '折叠项',
          fields: []
        }
      ]
      break
    case 'column':
      newSection.columns = [
        {
          id: generateId('column'),
          span: 12,
          fields: []
        },
        {
          id: generateId('column'),
          span: 12,
          fields: []
        }
      ]
      break
  }

  newConfig.sections.push(newSection)
  layoutConfig.value = newConfig
  selectedId.value = newSection.id
  history.push(newConfig, `Add ${type} section`)
}

function handleAddField(field: any) {
  if (!selectedId.value) {
    ElMessage.warning('请先选择要添加字段的位置')
    return
  }

  const newConfig = cloneLayoutConfig(layoutConfig.value)
  const target = findItemById(newConfig, selectedId.value)

  if (!target) {
    ElMessage.error('未找到目标位置')
    return
  }

  // Check if target can contain fields
  if (!target.fields) {
    ElMessage.warning('所选位置不能添加字段')
    return
  }

  // Check if field already exists
  const exists = target.fields.some((f: any) => f.field_code === field.code)
  if (exists) {
    ElMessage.warning('字段已存在')
    return
  }

  target.fields.push({
    id: generateId('field'),
    field_code: field.code,
    label: field.name || field.label || field.code,
    span: 12,
    readonly: false,
    visible: true,
    required: field.is_required || false
  })

  layoutConfig.value = newConfig
  history.push(newConfig, `Add field ${field.code}`)
}

function handleAddMultipleFields(fields: any[]) {
  if (!selectedId.value) {
    ElMessage.warning('请先选择要添加字段的位置')
    return
  }

  const newConfig = cloneLayoutConfig(layoutConfig.value)
  const target = findItemById(newConfig, selectedId.value)

  if (!target || !target.fields) {
    ElMessage.warning('所选位置不能添加字段')
    return
  }

  let addedCount = 0
  fields.forEach(field => {
    const exists = target.fields.some((f: any) => f.field_code === field.code)
    if (!exists) {
      target.fields.push({
        id: generateId('field'),
        field_code: field.code,
        label: field.name || field.label || field.code,
        span: 12,
        readonly: field.is_readonly || false,
        visible: true,
        required: field.is_required || false
      })
      addedCount++
    }
  })

  if (addedCount > 0) {
    layoutConfig.value = newConfig
    history.push(newConfig, `Add ${addedCount} fields`)
    ElMessage.success(`成功添加 ${addedCount} 个字段`)
  } else {
    ElMessage.warning('所有字段已存在')
  }
}

function handleDropNew(containerId: string, data: any, index: number) {
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  
  // Create the new field object
  const newField = {
    id: generateId('field'),
    field_code: data.code,
    label: data.label || data.code,
    span: 12,
    readonly: false,
    visible: true,
    required: false // We can't easily get is_required from data unless passed
  }

  // Find target container
  let targetList: any[] | null = null

  if (containerId === 'root') {
     // Check if dropping a section (not a field)
     const sectionTypes = ['section', 'tab', 'divider', 'collapse', 'column']
     if (data.type && sectionTypes.includes(data.type)) {
       handleAddSection(data.type)
       return
     }
     ElMessage.warning('请将字段拖入区块中，而不是根容器')
     return
  } else {
     const container = findItemById(newConfig, containerId)
     if (container) {
       // Determine where fields are stored based on container type
       if (container.type === 'section') targetList = container.fields
       else if (container.type === 'tab') targetList = container.fields // Tab item has fields? Wait, Tab Section has Tabs. Tab Item has fields.
       // findItemById returns the item. If ID matches a TAB ITEM, it has fields.
       // Let's check structure:
       // Tab Section -> tabs (Array of TabItem) -> fields
       // So if containerId is a TabITEM id, it has fields.
       // If containerId is Section, it has fields.
       // If containerId is CollapseITEM, it has fields.
       // If containerId is ColumnITEM, it has fields (implied by content structure)
       
       // Ideally we check if container has 'fields' array
       if (Array.isArray(container.fields)) {
         targetList = container.fields
       }
     }
  }

  if (targetList) {
    targetList.splice(index, 0, newField)
    layoutConfig.value = newConfig
    selectedId.value = newField.id
    history.push(newConfig, `Drop new field ${newField.field_code}`)
  } else {
    ElMessage.error(`Target container ${containerId} not found or invalid`)
  }
}

function handleMoveItem(fromContainerId: string, toContainerId: string, oldIndex: number, newIndex: number) {
  const newConfig = cloneLayoutConfig(layoutConfig.value)
  
  let sourceList: any[] | null = null
  let targetList: any[] | null = null

  // Helpers to get list from container ID
  const getList = (id: string): any[] | null => {
    if (id === 'root') return newConfig.sections || []
    const item = findItemById(newConfig, id)
    if (item && Array.isArray(item.fields)) return item.fields
    return null
  }

  sourceList = getList(fromContainerId)
  targetList = getList(toContainerId)

  if (sourceList && targetList) {
    // Remove from source
    // Safety check indices
    if (oldIndex >= 0 && oldIndex < sourceList.length) {
      const [item] = sourceList.splice(oldIndex, 1)
      
      // Insert to target
      // Safety check index (allow pushing to end)
      const actualNewIndex = Math.min(Math.max(0, newIndex), targetList.length)
      targetList.splice(actualNewIndex, 0, item)
      
      layoutConfig.value = newConfig
      history.push(newConfig, 'Move item')
    }
  }
}

function validateConfig() {
  const result: ValidationResult = validateLayoutConfig(layoutConfig.value, props.layoutType)

  validationErrors.value = result.errors
  validationVisible.value = true

  if (result.valid) {
    ElNotification.success({
      title: '验证通过',
      message: '布局配置验证通过！'
    })
  }
}

function handleReset() {
  ElMessageBox.confirm('确定要重置布局吗？所有未保存的更改将丢失。', '确认重置', {
    type: 'warning'
  }).then(() => {
    layoutConfig.value = getDefaultLayoutConfig(props.layoutType)
    selectedId.value = ''
    history.clear()
    ElMessage.success('已重置')
  }).catch(() => {})
}

async function handleSave() {
  // Validate first
  const result: ValidationResult = validateLayoutConfig(layoutConfig.value, props.layoutType)
  if (!result.valid) {
    validateConfig()
    return
  }

  saving.value = true

  try {
    const data = {
      layoutConfig: layoutConfig.value,
      status: 'draft'
    }

    if (props.layoutId) {
      await pageLayoutApi.partialUpdate(props.layoutId, data)
    } else {
      await pageLayoutApi.create({
        ...data,
        layoutCode: `${props.objectCode}_${props.layoutType}_${Date.now()}`,
        layoutName: props.layoutName,
        layoutType: props.layoutType,
        business_object: props.businessObjectId
      })
    }

    ElMessage.success('保存成功')
    emit('save', data)
  } catch (error: any) {
    console.error('Save failed:', error)
    ElMessage.error(error.response?.data?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handlePublish() {
  // Validate first
  const result: ValidationResult = validateLayoutConfig(layoutConfig.value, props.layoutType)
  if (!result.valid) {
    validateConfig()
    return
  }

  publishing.value = true

  try {
    if (props.layoutId) {
      await pageLayoutApi.publish(props.layoutId, {
        change_summary: '发布布局'
      })
    } else {
      // Save first then publish
      const createResult = await pageLayoutApi.create({
        layoutConfig: layoutConfig.value,
        layoutCode: `${props.objectCode}_${props.layoutType}_${Date.now()}`,
        layoutName: props.layoutName,
        layoutType: props.layoutType,
        business_object: props.businessObjectId,
        status: 'published'
      })

      // The request interceptor unwraps the response, so createResult is already the data
      await pageLayoutApi.publish(createResult.id, {
        set_as_default: true
      })
    }

    isPublished.value = true
    ElMessage.success('发布成功')
    emit('published', layoutConfig.value)
  } catch (error: any) {
    console.error('Publish failed:', error)
    ElMessage.error(error.response?.data?.message || '发布失败')
  } finally {
    publishing.value = false
  }
}

function handleRollback(version: string) {
  ElMessageBox.confirm(`确定要回滚到版本 ${version} 吗？`, '确认回滚', {
    type: 'warning'
  }).then(async () => {
    if (!props.layoutId) return

    try {
      await pageLayoutApi.rollback(props.layoutId, version)
      ElMessage.success('回滚成功，请查看并重新发布')
      historyVisible.value = false
      // Reload layout
      loadLayout()
    } catch (error: any) {
      console.error('Rollback failed:', error)
      ElMessage.error('回滚失败')
    }
  }).catch(() => {})
}

function handleCancel() {
  emit('cancel')
}

function togglePreview() {
  previewMode.value = !previewMode.value
}

function formatTimestamp(timestamp: string): string {
  return new Date(timestamp).toLocaleString()
}

async function loadLayout() {
  if (!props.layoutId) return

  try {
    // The request interceptor unwraps { success: true, data: ... } automatically
    // So the response is already the layout data
    const layout = await pageLayoutApi.detail(props.layoutId)

    layoutConfig.value = layout.layoutConfig || getDefaultLayoutConfig(props.layoutType)
    isDefault.value = layout.isDefault
    isPublished.value = layout.status === 'published'
    layoutVersion.value = layout.version

    // Load history - also unwrapped by interceptor
    const history = await pageLayoutApi.history(props.layoutId)
    layoutHistory.value = history || []
  } catch (error) {
    console.error('Failed to load layout:', error)
  }
}

async function loadAvailableFields() {
  if (!props.objectCode) return

  try {
    // Try to get field definitions from business object
    const response = await fetch(`/api/system/business-objects/fields/?object_code=${props.objectCode}`)
    const data = await response.json()

    if (data.success && data.data) {
      availableFields.value = data.data.field_definitions || data.data.fields || []
    }
  } catch (error) {
    console.error('Failed to load fields:', error)
    // Use mock data as fallback
    availableFields.value = [
      { code: 'name', name: '名称', field_type: 'text', is_required: true },
      { code: 'code', name: '编码', field_type: 'text', is_required: true },
      { code: 'status', name: '状态', field_type: 'select', is_required: false },
      { code: 'description', name: '描述', field_type: 'textarea', is_required: false }
    ]
  }
}

// Import/Export Functions
async function handleImport() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    try {
      const file = (e.target as HTMLInputElement).files?.[0]
      if (!file) return

      const text = await file.text()
      const config = JSON.parse(text)

      const result: ValidationResult = validateLayoutConfig(config, props.layoutType)
      if (!result.valid) {
        ElMessage.error(`布局配置无效: ${result.errors.map(e => e.message).join(', ')}`)
        return
      }

      layoutConfig.value = config
      history.push(config, 'Import layout')
      ElMessage.success('布局导入成功')
    } catch (err) {
      ElMessage.error('导入失败: 无效的JSON文件')
    }
  }
  input.click()
}

function handleExport() {
  const dataStr = JSON.stringify(layoutConfig.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `layout-${props.objectCode || 'custom'}-${props.layoutType}-${Date.now()}.json`
  link.click()

  URL.revokeObjectURL(url)
  ElMessage.success('布局导出成功')
}

// Keyboard Shortcuts
function handleKeydown(e: KeyboardEvent) {
  // Ignore if typing in input
  if ((e.target as HTMLElement).tagName === 'INPUT' ||
      (e.target as HTMLElement).tagName === 'TEXTAREA') {
    return
  }

  if (e.ctrlKey && e.key === 'z') {
    e.preventDefault()
    undo()
  } else if (e.ctrlKey && e.key === 'y') {
    e.preventDefault()
    redo()
  } else if (e.key === 'Delete' && selectedId.value) {
    e.preventDefault()
    handleDelete(selectedId.value)
  }
}

// Lifecycle
onMounted(() => {
  loadLayout()
  loadAvailableFields()
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// Watch for prop changes
watch(() => props.layoutType, (newType) => {
  layoutConfig.value = getDefaultLayoutConfig(newType)
})
</script>

<style scoped lang="scss">
.layout-designer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.designer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 12px;

    .layout-info {
      font-size: 16px;
      font-weight: 500;
      color: #303133;
    }
  }

  .toolbar-center {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.designer-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.designer-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  margin: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .preview-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    border-bottom: 1px solid #e4e7ed;
  }

  .preview-content {
    flex: 1;
    overflow: auto;
    padding: 20px;
  }

  .preview-container {
    max-width: 1000px;
    margin: 0 auto;
  }
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;

  .preview-icon {
    font-size: 64px;
    margin-bottom: 16px;
    opacity: 0.3;
  }

  p {
    margin: 4px 0;
  }

  .preview-note {
    font-size: 12px;
    color: #c0c4cc;
  }
}

.validation-errors {
  .more-errors {
    margin-top: 12px;
    color: #909399;
    font-size: 14px;
  }
}

.history-list {
  max-height: 400px;
  overflow-y: auto;

  .history-item {
    display: flex;
    align-items: center;
    gap: 12px;

    .history-version {
      font-weight: 500;
      color: #409eff;
    }

    .history-action {
      padding: 2px 8px;
      background: #f0f9ff;
      border-radius: 4px;
      font-size: 12px;
      color: #67c23a;
    }

    .history-summary {
      color: #606266;
      font-size: 14px;
    }
  }
}

.preview-mode {
  .designer-toolbar {
    .toolbar-center {
      display: none;
    }
  }
}
</style>
