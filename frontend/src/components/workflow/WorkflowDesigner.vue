<!--
  WorkflowDesigner Component

  Visual workflow designer using LogicFlow.
  Features:
  - Drag-and-drop node creation
  - Node connection management
  - Property panel for node configuration
  - Workflow save/load
  - Validation and export
-->

<template>
  <div class="workflow-designer">
    <!-- Toolbar -->
    <div class="designer-toolbar">
      <div class="toolbar-section">
        <span class="toolbar-title">{{ workflowName || '未命名流程' }}</span>
        <el-tag v-if="!isDirty" type="info" size="small">已保存</el-tag>
        <el-tag v-else type="warning" size="small">未保存</el-tag>
      </div>

      <div class="toolbar-section toolbar-actions">
        <el-button-group>
          <el-tooltip content="开始节点" placement="bottom">
            <el-button :icon="VideoPlay" @click="addStartNode" />
          </el-tooltip>
          <el-tooltip content="审批节点" placement="bottom">
            <el-button :icon="User" @click="addApprovalNode" />
          </el-tooltip>
          <el-tooltip content="条件分支" placement="bottom">
            <el-button :icon="Share" @click="addConditionNode" />
          </el-tooltip>
          <el-tooltip content="抄送节点" placement="bottom">
            <el-button :icon="Message" @click="addNotifyNode" />
          </el-tooltip>
          <el-tooltip content="结束节点" placement="bottom">
            <el-button :icon="VideoPause" @click="addEndNode" />
          </el-tooltip>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-button-group>
          <el-tooltip content="撤销" placement="bottom">
            <el-button :icon="RefreshLeft" @click="undo" />
          </el-tooltip>
          <el-tooltip content="重做" placement="bottom">
            <el-button :icon="RefreshRight" @click="redo" />
          </el-tooltip>
        </el-button-group>

        <el-divider direction="vertical" />

        <el-button :icon="ZoomIn" @click="zoomIn" />
        <el-button :icon="ZoomOut" @click="zoomOut" />
        <el-button @click="resetView">适配</el-button>

        <el-divider direction="vertical" />

        <el-button type="primary" :icon="Check" @click="handleSave">
          保存
        </el-button>
        <el-button :icon="Delete" @click="handleClear">
          清空
        </el-button>
      </div>
    </div>

    <!-- Canvas -->
    <div class="designer-container">
      <div ref="lfContainerRef" class="lf-container"></div>

      <!-- Mini Map -->
      <div class="mini-map" ref="miniMapRef"></div>
    </div>

    <!-- Property Panel -->
    <PropertyPanel
      v-model:visible="propertyVisible"
      :node="selectedNode"
      :users="userOptions"
      :departments="departmentOptions"
      @update="handleNodeUpdate"
    />

    <!-- Validation Dialog -->
    <el-dialog
      v-model="validationVisible"
      title="流程验证"
      width="500px"
    >
      <div class="validation-result">
        <el-alert
          v-if="validationResult.isValid"
          title="验证通过"
          type="success"
          :closable="false"
          show-icon
        >
          <template #default>
            <p>流程配置正确，可以保存并激活。</p>
          </template>
        </el-alert>
        <div v-else>
          <el-alert
            title="验证失败"
            type="error"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>请修正以下问题：</p>
            </template>
          </el-alert>
          <el-scrollbar max-height="300px">
            <ul class="error-list">
              <li v-for="(error, index) in validationResult.errors" :key="index">
                <el-icon class="error-icon"><Warning /></el-icon>
                {{ error }}
              </li>
            </ul>
          </el-scrollbar>
        </div>
      </div>
      <template #footer>
        <el-button @click="validationVisible = false">关闭</el-button>
        <el-button
          v-if="validationResult.isValid"
          type="primary"
          @click="handleSaveAfterValidation"
        >
          保存流程
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
/**
 * WorkflowDesigner Component
 *
 * Visual workflow designer using LogicFlow library.
 * Supports drag-and-drop node creation and connection.
 */

import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoPlay,
  VideoPause,
  User,
  Share,
  Message,
  RefreshLeft,
  RefreshRight,
  ZoomIn,
  ZoomOut,
  Check,
  Delete,
  Warning
} from '@element-plus/icons-vue'
import LogicFlow from '@logicflow/core'
import '@logicflow/core/dist/style/index.css'
import PropertyPanel from './PropertyPanel.vue'
import type { LogicFlowGraphData, LogicFlowNode, WorkflowDefinition } from '@/types/workflow'

// ============================================================================
// Props & Emits
// ============================================================================

interface Props {
  modelValue?: LogicFlowGraphData
  workflowName?: string
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  readonly: false
})

const emit = defineEmits<{
  'update:modelValue': [data: LogicFlowGraphData]
  'save': [data: LogicFlowGraphData]
  'change': [data: LogicFlowGraphData]
}>()

// ============================================================================
// State
// ============================================================================

const lfContainerRef = ref<HTMLElement>()
const miniMapRef = ref<HTMLElement>()
const propertyVisible = ref(false)
const selectedNode = ref<LogicFlowNode | null>(null)
const validationVisible = ref(false)
const validationResult = ref<{ isValid: boolean; errors: string[] }>({
  isValid: false,
  errors: []
})

let lf: LogicFlow | null = null
const currentZoom = ref(1)
const isDirty = ref(false)

const userOptions = ref<Array<{ label: string; value: string }>>([])
const departmentOptions = ref<Array<{ label: string; value: string }>>([])

// ============================================================================
// LogicFlow Initialization
// ============================================================================

const initLogicFlow = () => {
  if (!lfContainerRef.value) return

  lf = new LogicFlow({
    container: lfContainerRef.value,
    width: lfContainerRef.value.clientWidth,
    height: lfContainerRef.value.clientHeight,
    background: {
      backgroundImage: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImEiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTTAgNDBMMDQwIDBIMCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZDVkNWQ1IiBzdHJva2Utd2lkdGg9IjEiLz48cGF0aCBkPSJNNDAgNDBWMHgwIiBmaWxsPSJub25lIiBzdHJva2U9IiNkNWQ1ZDUiIHN0cm9rZS13aWR0aD0iMSIvPjwvcGF0dGVybj48L2RlZnM+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0idXJsKCNhKSIvPjwvc3ZnPg==',
      backgroundRepeat: 'repeat'
    },
    grid: {
      size: 20,
      visible: true,
      type: 'dot',
      config: {
        color: '#d5d5d5'
      }
    },
    keyboard: {
      enabled: true
    },
    style: {
      rect: {
        rx: 8,
        ry: 8,
        strokeWidth: 2
      },
      circle: {
        r: 40
      }
    }
  })

  // Register custom node types
  registerNodeTypes()

  // Register event handlers
  registerEventHandlers()

  // Load initial data if provided
  if (props.modelValue) {
    lf.render(props.modelValue)
  }

  // Handle window resize
  window.addEventListener('resize', handleResize)
}

/**
 * Register custom node types
 */
const registerNodeTypes = () => {
  if (!lf) return

  // Start node (circle, green)
  lf.register('start', ({ properties }: any) => ({
    type: 'circle',
    r: 30,
    fill: '#67c23a',
    stroke: '#85ce61',
    strokeWidth: 2,
    text: {
      value: properties?.text || '开始',
      x: 0,
      y: 0,
      fill: '#fff'
    }
  }))

  // End node (circle, red)
  lf.register('end', ({ properties }: any) => ({
    type: 'circle',
    r: 30,
    fill: '#f56c6c',
    stroke: '#f78989',
    strokeWidth: 2,
    text: {
      value: properties?.text || '结束',
      x: 0,
      y: 0,
      fill: '#fff'
    }
  }))

  // Approval node (rect, blue)
  lf.register('approval', ({ properties }: any) => ({
    type: 'rect',
    width: 120,
    height: 60,
    radius: 8,
    fill: '#409eff',
    stroke: '#66b1ff',
    strokeWidth: 2,
    text: {
      value: properties?.text || '审批',
      x: 0,
      y: 0,
      fill: '#fff'
    }
  }))

  // Condition node (diamond, orange)
  lf.register('condition', ({ properties }: any) => ({
    type: 'diamond',
    rx: 50,
    ry: 50,
    fill: '#e6a23c',
    stroke: '#ebb563',
    strokeWidth: 2,
    text: {
      value: properties?.text || '条件',
      x: 0,
      y: 0,
      fill: '#fff'
    }
  }))

  // Notify node (rect, purple)
  lf.register('notify', ({ properties }: any) => ({
    type: 'rect',
    width: 120,
    height: 60,
    radius: 8,
    fill: '#9c27b0',
    stroke: '#ab47bc',
    strokeWidth: 2,
    text: {
      value: properties?.text || '抄送',
      x: 0,
      y: 0,
      fill: '#fff'
    }
  }))
}

/**
 * Register event handlers
 */
const registerEventHandlers = () => {
  if (!lf) return

  // Node click
  lf.on('node:click', ({ data }) => {
    selectedNode.value = data
    propertyVisible.value = true
  })

  // Edge click
  lf.on('edge:click', ({ data }) => {
    // Handle edge selection
  })

  // Blank click
  lf.on('blank:click', () => {
    selectedNode.value = null
    propertyVisible.value = false
  })

  // Node delete
  lf.on('node:delete', () => {
    isDirty.value = true
    emitChange()
  })

  // Edge delete
  lf.on('edge:delete', () => {
    isDirty.value = true
    emitChange()
  })

  // History change
  lf.on('history:change', () => {
    emitChange()
  })
}

/**
 * Emit change event
 */
const emitChange = () => {
  const data = lf?.getGraphData()
  if (data) {
    emit('update:modelValue', data as LogicFlowGraphData)
    emit('change', data as LogicFlowGraphData)
    isDirty.value = true
  }
}

// ============================================================================
// Node Actions
// ============================================================================

const addStartNode = () => {
  lf?..addNode({
    id: `node_${Date.now()}`,
    type: 'start',
    x: 100,
    y: 300,
    properties: {
      text: '开始'
    }
  })
  emitChange()
}

const addEndNode = () => {
  lf?.addNode({
    id: `node_${Date.now()}`,
    type: 'end',
    x: 700,
    y: 300,
    properties: {
      text: '结束'
    }
  })
  emitChange()
}

const addApprovalNode = () => {
  lf?.addNode({
    id: `node_${Date.now()}`,
    type: 'approval',
    x: 300,
    y: 300,
    properties: {
      text: '审批',
      approvalType: 'or',
      approvers: []
    }
  })
  emitChange()
}

const addConditionNode = () => {
  lf?.addNode({
    id: `node_${Date.now()}`,
    type: 'condition',
    x: 400,
    y: 300,
    properties: {
      text: '条件分支',
      conditions: []
    }
  })
  emitChange()
}

const addNotifyNode = () => {
  lf?.addNode({
    id: `node_${Date.now()}`,
    type: 'notify',
    x: 500,
    y: 300,
    properties: {
      text: '抄送',
      notifyUsers: []
    }
  })
  emitChange()
}

// ============================================================================
// Toolbar Actions
// ============================================================================

const undo = () => {
  lf?.undo()
}

const redo = () => {
  lf?.redo()
}

const zoomIn = () => {
  if (!lf) return
  currentZoom.value = Math.min(currentZoom.value + 0.1, 2)
  lf.zoom(currentZoom.value)
}

const zoomOut = () => {
  if (!lf) return
  currentZoom.value = Math.max(currentZoom.value - 0.1, 0.5)
  lf.zoom(currentZoom.value)
}

const resetView = () => {
  lf?.resetZoom()
  lf?.resetTranslate()
  currentZoom.value = 1
}

// ============================================================================
// Save & Validation
// ============================================================================

const handleSave = () => {
  const validation = validateWorkflow()
  validationResult.value = validation
  validationVisible.value = true
}

const handleSaveAfterValidation = () => {
  const data = lf?.getGraphData()
  if (data) {
    emit('save', data as LogicFlowGraphData)
    isDirty.value = false
    validationVisible.value = false
    ElMessage.success('保存成功')
  }
}

const validateWorkflow = (): { isValid: boolean; errors: string[] } => {
  const errors: string[] = []
  const data = lf?.getGraphData()

  if (!data) {
    errors.push('流程数据为空')
    return { isValid: false, errors }
  }

  // Check for start node
  const hasStart = data.nodes.some((n: any) => n.type === 'start')
  if (!hasStart) {
    errors.push('缺少开始节点')
  }

  // Check for end node
  const hasEnd = data.nodes.some((n: any) => n.type === 'end')
  if (!hasEnd) {
    errors.push('缺少结束节点')
  }

  // Check for orphan nodes
  const connectedNodeIds = new Set<string>()
  data.edges.forEach((e: any) => {
    connectedNodeIds.add(e.sourceNodeId)
    connectedNodeIds.add(e.targetNodeId)
  })
  const orphanNodes = data.nodes.filter((n: any) =>
    n.type !== 'start' && n.type !== 'end' && !connectedNodeIds.has(n.id)
  )
  if (orphanNodes.length > 0) {
    errors.push(`存在 ${orphanNodes.length} 个未连接的节点`)
  }

  // Check for approval nodes without approvers
  const approvalNodes = data.nodes.filter((n: any) => n.type === 'approval')
  approvalNodes.forEach((node: any) => {
    if (!node.properties?.approvers || node.properties.approvers.length === 0) {
      errors.push(`审批节点"${node.properties?.text || ''}"未配置审批人`)
    }
  })

  return {
    isValid: errors.length === 0,
    errors
  }
}

const handleClear = () => {
  lf?.clearData()
  emitChange()
}

const handleNodeUpdate = (updates: Partial<LogicFlowNode>) => {
  if (selectedNode.value && lf) {
    lf.setNodeData(selectedNode.value.id, {
      ...selectedNode.value,
      ...updates,
      properties: {
        ...selectedNode.value.properties,
        ...updates.properties
      }
    } as any)
    emitChange()
  }
}

const handleResize = () => {
  if (lfContainerRef.value && lf) {
    lf.container.style.width = `${lfContainerRef.value.clientWidth}px`
    lf.container.style.height = `${lfContainerRef.value.clientHeight}px`
  }
}

// ============================================================================
// Watch
// ============================================================================

watch(() => props.modelValue, (newValue) => {
  if (newValue && lf && !isDirty.value) {
    lf.render(newValue)
  }
}, { deep: true })

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  initLogicFlow()
})

onUnmounted(() => {
  lf?.destroy()
  window.removeEventListener('resize', handleResize)
})

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  validate: validateWorkflow,
  getGraphData: () => lf?.getGraphData(),
  setGraphData: (data: LogicFlowGraphData) => lf?.render(data)
})
</script>

<style scoped lang="scss">
.workflow-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

.designer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-bottom: 1px solid #ebeef5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .toolbar-section {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .toolbar-title {
    font-size: 16px;
    font-weight: 500;
    color: #303133;
  }

  .toolbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.designer-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.lf-container {
  width: 100%;
  height: 100%;
}

.mini-map {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 200px;
  height: 150px;
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.validation-result {
  .error-list {
    margin-top: 16px;
    padding-left: 20px;

    li {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      color: #f56c6c;
    }

    .error-icon {
      font-size: 16px;
    }
  }
}
</style>
