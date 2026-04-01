<template>
  <div class="workflow-designer">
    <!-- Toolbar -->
    <div class="toolbar">
      <el-button-group>
        <el-button :icon="ZoomOut" @click="handleZoomOut" />
        <el-button @click="handleZoomReset">100%</el-button>
        <el-button :icon="ZoomIn" @click="handleZoomIn" />
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button :icon="Download" @click="handleExport">
        {{ t('workflow.designer.exportJson') }}
      </el-button>
      <el-button :icon="Upload" @click="handleImport">
        {{ t('workflow.designer.importJson') }}
      </el-button>
      <el-divider direction="vertical" />
      <el-button type="primary" @click="handleSave">
        {{ t('workflow.designer.saveProcess') }}
      </el-button>
    </div>

    <!-- Node palette — HTML5 drag source (fixes broken DndPanel.setPatternItems) -->
    <div class="node-panel">
      <div class="panel-section">
        <div class="section-title">{{ t('workflow.designer.basicNodes') }}</div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onPaletteDragStart($event, 'start')"
        >
          <div class="node-icon start">{{ t('workflow.nodeType.start') }}</div>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onPaletteDragStart($event, 'end')"
        >
          <div class="node-icon end">{{ t('workflow.nodeType.end') }}</div>
        </div>
      </div>
      <div class="panel-section">
        <div class="section-title">{{ t('workflow.designer.approvalNodes') }}</div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onPaletteDragStart($event, 'approval')"
        >
          <div class="node-icon approval">{{ t('workflow.nodeType.approval') }}</div>
        </div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onPaletteDragStart($event, 'condition')"
        >
          <div class="node-icon condition">{{ t('workflow.nodeType.condition') }}</div>
        </div>
      </div>
      <div class="panel-section">
        <div class="section-title">{{ t('workflow.designer.ccNodes') }}</div>
        <div
          class="node-item"
          draggable="true"
          @dragstart="onPaletteDragStart($event, 'cc')"
        >
          <div class="node-icon cc">{{ t('workflow.nodeType.cc') }}</div>
        </div>
      </div>
    </div>

    <!-- Canvas — drop target -->
    <div
      ref="containerRef"
      class="canvas-container"
      @dragover.prevent
      @drop="onCanvasDrop"
    />

    <!-- Property panel (shown when a node is selected) -->
    <div v-if="selectedNode" class="property-panel">
      <el-tabs v-model="activeTab">
        <el-tab-pane :label="t('workflow.designer.basicProperties')" name="basic">
          <el-form
            :model="selectedNode"
            :label-width="locale === 'zh-CN' ? '80px' : '120px'"
          >
            <el-form-item :label="t('workflow.designer.nodeName')">
              <el-input v-model="selectedNode.text" @input="updateNodeName" />
            </el-form-item>
            <el-form-item :label="t('workflow.fields.nodeType')">
              <el-input :value="getNodeTypeLabel(selectedNode.type)" disabled />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane
          v-if="selectedNode.type === 'approval'"
          :label="t('workflow.designer.approvalConfig')"
          name="approval"
        >
          <ApprovalNodeConfig v-model="selectedNode.properties" />
        </el-tab-pane>

        <el-tab-pane
          v-if="selectedNode.type === 'condition'"
          :label="t('workflow.designer.conditionConfig')"
          name="condition"
        >
          <!-- Pass the live field list so condition rules use real object fields -->
          <ConditionNodeConfig
            v-model="selectedNode.properties"
            :available-fields="availableFields"
          />
        </el-tab-pane>

        <el-tab-pane
          v-if="needPermissionConfig"
          :label="t('workflow.designer.fieldPermissions')"
          name="permission"
        >
          <FieldPermissionConfig
            v-model="selectedNode.properties.fieldPermissions"
            :business-object="businessObject"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- Import JSON dialog -->
    <el-dialog
      v-model="importDialogVisible"
      :title="t('workflow.designer.importProcess')"
      width="600px"
    >
      <el-input
        v-model="importJson"
        type="textarea"
        :rows="10"
        :placeholder="t('workflow.designer.pasteJson')"
      />
      <template #footer>
        <el-button @click="importDialogVisible = false">
          {{ t('common.actions.cancel') }}
        </el-button>
        <el-button type="primary" @click="handleImportConfirm">
          {{ t('common.actions.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import LogicFlow from '@logicflow/core'
import { Menu } from '@logicflow/extension'
import '@logicflow/core/dist/style/index.css'
import '@logicflow/extension/lib/style/index.css'
import { ElMessage } from 'element-plus'
import { ZoomIn, ZoomOut, Download, Upload } from '@element-plus/icons-vue'
import ApprovalNodeConfig from './ApprovalNodeConfig.vue'
import ConditionNodeConfig from './ConditionNodeConfig.vue'
import FieldPermissionConfig from './FieldPermissionConfig.vue'
import { getFieldDefinitions } from '@/api/system'

const { t } = useI18n()
const locale = computed(() => t('locale'))

interface FieldDef {
  code: string
  name: string
}

interface Props {
  modelValue?: any
  businessObject?: string
  readonly?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: any): void
  (e: 'save', data: any): void
}

const props = withDefaults(defineProps<Props>(), {
  businessObject: '',
  readonly: false,
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLElement | null>(null)
const lf = ref<LogicFlow | null>(null)
const selectedNode = ref<any>(null)
const activeTab = ref('basic')
const importDialogVisible = ref(false)
const importJson = ref('')

// Current flow JSON (nodes + edges)
const flowData = ref(props.modelValue || { nodes: [], edges: [] })

// Available fields loaded from the business object — passed to ConditionNodeConfig
const availableFields = ref<FieldDef[]>([])

// Type of node being dragged from palette (set in dragstart)
let dragType = ''

// Debounce timer for history:change syncing
let historyDebounceTimer: ReturnType<typeof setTimeout> | null = null

// ResizeObserver to keep canvas dimensions correct
let resizeObserver: ResizeObserver | null = null

// ── Lifecycle ────────────────────────────────────────────────────────────────

onMounted(() => {
  initLogicFlow()
  loadBusinessObjectFields()
})

onUnmounted(() => {
  if (historyDebounceTimer) clearTimeout(historyDebounceTimer)
  lf.value?.destroy()
  resizeObserver?.disconnect()
})

// ── LogicFlow initialisation ─────────────────────────────────────────────────

const initLogicFlow = () => {
  if (!containerRef.value) return

  lf.value = new LogicFlow({
    container: containerRef.value,
    width: containerRef.value.clientWidth || 800,
    height: containerRef.value.clientHeight || 600,
    // Use Menu extension only (DndPanel removed — we drive drag via HTML5)
    plugins: [Menu],
    grid: { size: 20, type: 'dot', visible: true },
    background: {
      backgroundImage:
        'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjEiIGZpbGw9IiNjY2MiIGZpbGwtb3BhY2l0eT0iMC4yIi8+PC9zdmc+',
    },
    edgeTextDraggable: true,
    nodeSelectedOutline: true,
    keyboard: { enabled: true },
  })

  registerCustomNodes()

  if (flowData.value.nodes.length > 0) {
    lf.value.render(flowData.value)
  }

  // Bind canvas events
  lf.value.on('node:click', handleNodeClick)
  lf.value.on('edge:click', handleEdgeClick)
  lf.value.on('blank:click', handleBlankClick)
  lf.value.on('node:drop', handleNodeDrop)
  lf.value.on('node:add', handleNodeAdd)
  lf.value.on('edge:add', handleEdgeAdd)
  lf.value.on('history:change', handleHistoryChange)

  // Watch container resize and update canvas dimensions
  resizeObserver = new ResizeObserver((entries) => {
    const entry = entries[0]
    if (!entry || !lf.value) return
    const { width, height } = entry.contentRect
    if (width > 0 && height > 0) {
      lf.value.resize(width, height)
    }
  })
  resizeObserver.observe(containerRef.value)
}

// ── HTML5 drag-and-drop palette support ──────────────────────────────────────

/** Called on palette item dragstart to record which node type is being dragged. */
const onPaletteDragStart = (event: DragEvent, type: string) => {
  dragType = type
  event.dataTransfer?.setData('text/plain', type)
}

/**
 * Called when the user drops a palette item onto the canvas.
 * Converts viewport coordinates to LogicFlow canvas coordinates and adds the node.
 */
const onCanvasDrop = (event: DragEvent) => {
  if (!lf.value || !dragType || !containerRef.value) return

  const rect = containerRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // getPointByClient(x, y) → { domOverlayPosition, canvasOverlayPosition }
  const point = lf.value.getPointByClient(x, y)
  const graphX = point.canvasOverlayPosition.x
  const graphY = point.canvasOverlayPosition.y

  const defaultText: Record<string, string> = {
    start: t('workflow.nodeType.start'),
    end: t('workflow.nodeType.end'),
    approval: t('workflow.nodeType.approval'),
    condition: t('workflow.nodeType.condition'),
    cc: t('workflow.nodeType.cc'),
  }

  lf.value.addNode({
    type: dragType,
    x: graphX,
    y: graphY,
    text: defaultText[dragType] ?? dragType,
    properties: buildDefaultProperties(dragType),
  })

  dragType = ''
}

// ── Custom node registration ─────────────────────────────────────────────────

const registerCustomNodes = () => {
  if (!lf.value) return

  // Start node — rounded rectangle, green
  lf.value.register('start', ({ RectNode, RectNodeModel, h }: any) => {
    class StartNode extends RectNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height, radius } = model
        return h('g', {}, [
          h('rect', {
            x: x - width / 2,
            y: y - height / 2,
            rx: radius || 20,
            ry: radius || 20,
            width,
            height,
            fill: '#67C23A',
            stroke: '#67C23A',
            strokeWidth: 2,
          }),
          h(
            'text',
            {
              x,
              y,
              fill: '#fff',
              fontSize: 14,
              fontWeight: 'bold',
              textAnchor: 'middle',
              dominantBaseline: 'middle',
            },
            model.text.value || t('workflow.nodeType.start'),
          ),
        ])
      }
    }

    class StartNodeModel extends RectNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        ;(this as any).width = 100
        this.height = 40
        this.radius = 20
      }

      getDefaultAnchor() {
        return [{ id: 'right', x: this.x + this.width / 2, y: this.y }]
      }
    }

    return { view: StartNode, model: StartNodeModel }
  })

  // Approval node — rectangle, blue
  lf.value.register('approval', ({ RectNode, RectNodeModel, h }: any) => {
    class ApprovalNode extends RectNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height } = model
        const properties = model.getProperties() || {}
        const approveType = String(properties.approveType || 'or')
        const typeLabel =
          {
            or: t('workflow.approvalType.or'),
            and: t('workflow.approvalType.and'),
            seq: t('workflow.approvalType.seq'),
          }[approveType] || ''

        return h('g', {}, [
          h('rect', {
            x: x - width / 2,
            y: y - height / 2,
            width,
            height,
            fill: '#409EFF',
            stroke: '#409EFF',
            strokeWidth: 2,
            rx: 4,
          }),
          h(
            'text',
            {
              x,
              y: y - 8,
              fill: '#fff',
              fontSize: 14,
              fontWeight: 'bold',
              textAnchor: 'middle',
              dominantBaseline: 'middle',
            },
            model.text.value || t('workflow.nodeType.approval'),
          ),
          h(
            'text',
            {
              x,
              y: y + 12,
              fill: 'rgba(255,255,255,0.8)',
              fontSize: 10,
              textAnchor: 'middle',
              dominantBaseline: 'middle',
            },
            typeLabel,
          ),
        ])
      }
    }

    class ApprovalNodeModel extends RectNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        this.width = 120
        this.height = 60
      }
    }

    return { view: ApprovalNode, model: ApprovalNodeModel }
  })

  // Condition node — diamond, orange
  lf.value.register('condition', ({ PolygonNode, PolygonNodeModel, h }: any) => {
    class ConditionNode extends PolygonNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height } = model
        const points = [
          [x, y - height / 2],
          [x + width / 2, y],
          [x, y + height / 2],
          [x - width / 2, y],
        ]

        return h('g', {}, [
          h('polygon', {
            points: points.map((p) => p.join(',')).join(' '),
            fill: '#E6A23C',
            stroke: '#E6A23C',
            strokeWidth: 2,
          }),
          h(
            'text',
            {
              x,
              y,
              fill: '#fff',
              fontSize: 13,
              fontWeight: 'bold',
              textAnchor: 'middle',
              dominantBaseline: 'middle',
            },
            model.text.value || t('workflow.nodeType.condition'),
          ),
        ])
      }
    }

    class ConditionNodeModel extends PolygonNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        ;(this as any).width = 100
        ;(this as any).height = 100
      }

      getPoints() {
        const { x, y, width, height } = this
        return [
          [x, y - height / 2],
          [x + width / 2, y],
          [x, y + height / 2],
          [x - width / 2, y],
        ]
      }
    }

    return { view: ConditionNode, model: ConditionNodeModel }
  })

  // CC (carbon-copy) node — rectangle, grey
  lf.value.register('cc', ({ RectNode, RectNodeModel, h }: any) => {
    class CcNode extends RectNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height } = model
        return h('g', {}, [
          h('rect', {
            x: x - width / 2,
            y: y - height / 2,
            width,
            height,
            fill: '#909399',
            stroke: '#909399',
            strokeWidth: 2,
            rx: 4,
          }),
          h(
            'text',
            {
              x,
              y,
              fill: '#fff',
              fontSize: 14,
              fontWeight: 'bold',
              textAnchor: 'middle',
              dominantBaseline: 'middle',
            },
            model.text.value || t('workflow.nodeType.cc'),
          ),
        ])
      }
    }

    class CcNodeModel extends RectNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        this.width = 120
        this.height = 60
      }
    }

    return { view: CcNode, model: CcNodeModel }
  })

  // End node — rounded rectangle, red
  lf.value.register('end', ({ RectNode, RectNodeModel, h }: any) => {
    class EndNode extends RectNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height, radius } = model
        return h('g', {}, [
          h('rect', {
            x: x - width / 2,
            y: y - height / 2,
            rx: radius || 20,
            ry: radius || 20,
            width,
            height,
            fill: '#F56C6C',
            stroke: '#F56C6C',
            strokeWidth: 2,
          }),
          h(
            'text',
            {
              x,
              y,
              fill: '#fff',
              fontSize: 14,
              fontWeight: 'bold',
              textAnchor: 'middle',
              dominantBaseline: 'middle',
            },
            model.text.value || t('workflow.nodeType.end'),
          ),
        ])
      }
    }

    class EndNodeModel extends RectNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        ;(this as any).width = 100
        this.height = 40
        this.radius = 20
      }

      getDefaultAnchor() {
        return [{ id: 'left', x: this.x - this.width / 2, y: this.y }]
      }
    }

    return { view: EndNode, model: EndNodeModel }
  })
}

// ── Default node properties ──────────────────────────────────────────────────

const buildDefaultProperties = (type: string): Record<string, any> => {
  if (type === 'approval') {
    return {
      approvers: [],
      approveType: 'or',
      timeout: 72,
      autoApprove: false,
      allowTransfer: true,
      allowAddApprover: false,
      fieldPermissions: {},
    }
  }
  if (type === 'condition') {
    return { branches: [{ field: '', operator: 'eq', value: '' }], defaultFlow: 'reject' }
  }
  if (type === 'cc') {
    return { ccUsers: [], ccType: 'user' }
  }
  return {}
}

// ── Event handlers ───────────────────────────────────────────────────────────

const handleNodeClick = ({ data }: any) => {
  selectedNode.value = {
    id: data.id,
    type: data.type,
    text: data.text?.value ?? data.text,
    properties: data.properties || {},
  }
  activeTab.value = 'basic'
}

// Edge click reserved for future edge-label editing
const handleEdgeClick = (_payload: any) => {}

const handleBlankClick = () => {
  selectedNode.value = null
}

const handleNodeDrop = ({ data }: any) => {
  data.properties = buildDefaultProperties(data.type)
  selectedNode.value = {
    type: data.type,
    text: data.text?.value ?? data.text,
    properties: data.properties,
  }
}

const handleNodeAdd = ({ data }: any) => {
  handleNodeDrop({ data })
}

const handleEdgeAdd = ({ data }: any) => {
  // Prevent connecting TO the start node
  const targetNode = lf.value?.getNodeModelById(data.targetNodeId)
  if (targetNode?.type === 'start') {
    ElMessage.warning(t('workflow.designer.errors.cannotConnectToStart'))
    lf.value?.deleteEdge(data.id)
    return false
  }
  // Prevent the end node from being an edge source
  const sourceNode = lf.value?.getNodeModelById(data.sourceNodeId)
  if (sourceNode?.type === 'end') {
    ElMessage.warning(t('workflow.designer.errors.endNodeCannotBeSource'))
    lf.value?.deleteEdge(data.id)
    return false
  }
}

/**
 * Sync graph state to `flowData` on every history change.
 * Debounced to 300 ms to avoid excessive re-renders on rapid drag operations.
 */
const handleHistoryChange = () => {
  if (historyDebounceTimer) clearTimeout(historyDebounceTimer)
  historyDebounceTimer = setTimeout(() => {
    const graphData = lf.value?.getGraphData()
    if (graphData) {
      flowData.value = graphData
      emit('update:modelValue', graphData)
    }
  }, 300)
}

const updateNodeName = () => {
  if (!selectedNode.value || !lf.value) return
  const nodeModel = lf.value.getNodeModelById(selectedNode.value.id)
  if (nodeModel) nodeModel.updateText(selectedNode.value.text)
}

// ── Zoom controls ────────────────────────────────────────────────────────────

const handleZoomIn = () => lf.value?.zoom(true)
const handleZoomOut = () => lf.value?.zoom(false)
const handleZoomReset = () => lf.value?.resetZoom()

// ── Export / Import ──────────────────────────────────────────────────────────

const handleExport = () => {
  const data = lf.value?.getGraphData()
  if (!data) return
  const json = JSON.stringify(data, null, 2)
  const blob = new Blob([json], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `workflow_${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const handleImport = () => {
  importDialogVisible.value = true
}

const handleImportConfirm = () => {
  try {
    const data = JSON.parse(importJson.value)
    lf.value?.render(data)
    importDialogVisible.value = false
    ElMessage.success(t('workflow.messages.importSuccess'))
  } catch {
    ElMessage.error(t('workflow.messages.invalidJson'))
  }
}

// ── Save ─────────────────────────────────────────────────────────────────────

const handleSave = () => {
  const data = lf.value?.getGraphData()
  if (!data) {
    ElMessage.warning(t('workflow.designer.errors.designFlowFirst'))
    return
  }
  if (!validateFlow(data)) return
  emit('save', data)
}

const validateFlow = (data: any) => {
  const nodes = data.nodes || []
  const edges = data.edges || []

  if (!nodes.some((n: any) => n.type === 'start')) {
    ElMessage.error(t('workflow.designer.errors.requireStartNode'))
    return false
  }
  if (!nodes.some((n: any) => n.type === 'end')) {
    ElMessage.error(t('workflow.designer.errors.requireEndNode'))
    return false
  }
  if (nodes.length > 1 && edges.length === 0) {
    ElMessage.error(t('workflow.designer.errors.connectNodes'))
    return false
  }
  return true
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const getNodeTypeLabel = (type: string) => t(`workflow.nodeType.${type}`)

const needPermissionConfig = computed(() =>
  ['approval', 'start'].includes(selectedNode.value?.type),
)

// ── Business object fields ───────────────────────────────────────────────────

/**
 * Load field definitions for the current businessObject prop so that
 * ConditionNodeConfig can offer real field selectors instead of a static stub list.
 */
const loadBusinessObjectFields = async () => {
  if (!props.businessObject) return
  try {
    const response = await getFieldDefinitions(props.businessObject)
    const raw = Array.isArray(response)
      ? response
      : (response as any)?.results ?? []
    availableFields.value = raw.map((f: any) => ({
      code: f.code ?? f.field_code ?? '',
      name: f.name ?? f.label ?? f.code ?? '',
    }))
  } catch {
    // Non-fatal: ConditionNodeConfig falls back to empty list gracefully
    availableFields.value = []
  }
}

// Reload fields when the businessObject prop changes
watch(
  () => props.businessObject,
  () => void loadBusinessObjectFields(),
)

// Keep canvas in sync when the parent updates the flow externally
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && lf.value && JSON.stringify(newVal) !== JSON.stringify(flowData.value)) {
      flowData.value = newVal
      lf.value.render(newVal)
    }
  },
  { deep: true },
)
</script>

<style scoped>
.workflow-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
  position: relative;
}

.toolbar {
  display: flex;
  align-items: center;
  padding: 10px 15px;
  background: #fff;
  border-bottom: 1px solid #ddd;
  gap: 10px;
}

.node-panel {
  position: absolute;
  left: 20px;
  top: 70px;
  width: 160px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 15px;
  z-index: 100;
}

.section-title {
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
  padding-left: 5px;
  font-weight: 500;
}

.panel-section {
  margin-bottom: 20px;
}

.panel-section:last-child {
  margin-bottom: 0;
}

.node-item {
  margin-bottom: 8px;
  cursor: grab;
}

.node-item:active {
  cursor: grabbing;
}

.node-icon {
  padding: 10px 16px;
  text-align: center;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  user-select: none;
}

.node-icon.start      { background: #67C23A; }
.node-icon.end        { background: #F56C6C; }
.node-icon.approval   { background: #409EFF; }
.node-icon.condition  { background: #E6A23C; }
.node-icon.cc         { background: #909399; }

.canvas-container {
  flex: 1;
  background: #fff;
  border-radius: 4px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05);
}

.property-panel {
  position: absolute;
  right: 20px;
  top: 70px;
  width: 320px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
  max-height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
}

.property-panel :deep(.el-tabs__content) {
  padding: 15px;
  flex: 1;
  overflow-y: auto;
}

.property-panel :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 15px;
  background: #f5f5f5;
}

.property-panel :deep(.el-tabs__item) {
  padding: 0 15px;
  height: 40px;
  line-height: 40px;
}
</style>
