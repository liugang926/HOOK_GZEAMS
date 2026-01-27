<template>
  <div class="workflow-designer">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button-group>
        <el-button
          :icon="ZoomOut"
          @click="handleZoomOut"
        />
        <el-button @click="handleZoomReset">
          100%
        </el-button>
        <el-button
          :icon="ZoomIn"
          @click="handleZoomIn"
        />
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button
        :icon="Download"
        @click="handleExport"
      >
        导出JSON
      </el-button>
      <el-button
        :icon="Upload"
        @click="handleImport"
      >
        导入JSON
      </el-button>
      <el-divider direction="vertical" />
      <el-button
        type="primary"
        @click="handleSave"
      >
        保存流程
      </el-button>
    </div>

    <!-- 节点面板 -->
    <div class="node-panel">
      <div class="panel-section">
        <div class="section-title">
          基础节点
        </div>
        <div
          class="node-item"
          data-type="start"
        >
          <div class="node-icon start">
            开始
          </div>
        </div>
        <div
          class="node-item"
          data-type="end"
        >
          <div class="node-icon end">
            结束
          </div>
        </div>
      </div>
      <div class="panel-section">
        <div class="section-title">
          审批节点
        </div>
        <div
          class="node-item"
          data-type="approval"
        >
          <div class="node-icon approval">
            审批
          </div>
        </div>
        <div
          class="node-item"
          data-type="condition"
        >
          <div class="node-icon condition">
            条件
          </div>
        </div>
      </div>
      <div class="panel-section">
        <div class="section-title">
          抄送节点
        </div>
        <div
          class="node-item"
          data-type="cc"
        >
          <div class="node-icon cc">
            抄送
          </div>
        </div>
      </div>
    </div>

    <!-- 画布区域 -->
    <div
      ref="containerRef"
      class="canvas-container"
    />

    <!-- 属性面板 -->
    <div
      v-if="selectedNode"
      class="property-panel"
    >
      <el-tabs v-model="activeTab">
        <el-tab-pane
          label="基础属性"
          name="basic"
        >
          <el-form
            :model="selectedNode"
            label-width="80px"
          >
            <el-form-item label="节点名称">
              <el-input
                v-model="selectedNode.text"
                @input="updateNodeName"
              />
            </el-form-item>
            <el-form-item label="节点类型">
              <el-input
                :value="getNodeTypeLabel(selectedNode.type)"
                disabled
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane
          v-if="selectedNode.type === 'approval'"
          label="审批配置"
          name="approval"
        >
          <ApprovalNodeConfig v-model="selectedNode.properties" />
        </el-tab-pane>

        <el-tab-pane
          v-if="selectedNode.type === 'condition'"
          label="条件配置"
          name="condition"
        >
          <ConditionNodeConfig v-model="selectedNode.properties" />
        </el-tab-pane>

        <el-tab-pane
          v-if="needPermissionConfig"
          label="字段权限"
          name="permission"
        >
          <FieldPermissionConfig
            v-model="selectedNode.properties.fieldPermissions"
            :business-object="businessObject"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 导入弹窗 -->
    <el-dialog
      v-model="importDialogVisible"
      title="导入流程"
      width="600px"
    >
      <el-input
        v-model="importJson"
        type="textarea"
        :rows="10"
        placeholder="请粘贴流程JSON数据"
      />
      <template #footer>
        <el-button @click="importDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="handleImportConfirm"
        >
          导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import LogicFlow from '@logicflow/core'
import { DndPanel, Menu } from '@logicflow/extension'
import '@logicflow/core/dist/style/index.css'
import '@logicflow/extension/lib/style/index.css'
import { ElMessage } from 'element-plus'
import { ZoomIn, ZoomOut, Download, Upload } from '@element-plus/icons-vue'
import ApprovalNodeConfig from './ApprovalNodeConfig.vue'
import ConditionNodeConfig from './ConditionNodeConfig.vue'
import FieldPermissionConfig from './FieldPermissionConfig.vue'

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
  readonly: false
})

const emit = defineEmits<Emits>()

const containerRef = ref<HTMLElement | null>(null)
const lf = ref<LogicFlow | null>(null)
const selectedNode = ref<any>(null)
const activeTab = ref('basic')
const importDialogVisible = ref(false)
const importJson = ref('')

// 流程定义数据
const flowData = ref(props.modelValue || {
  nodes: [],
  edges: []
})

onMounted(() => {
  initLogicFlow()
})

onUnmounted(() => {
  lf.value?.destroy()
})

const initLogicFlow = () => {
  if (!containerRef.value) return

  lf.value = new LogicFlow({
    container: containerRef.value,
    width: containerRef.value.clientWidth,
    height: containerRef.value.clientHeight || 800,
    plugins: [DndPanel, Menu],
    grid: {
      size: 20,
      type: 'dot',
      visible: true
    },
    background: {
      backgroundImage: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMiIgY3k9IjIiIHI9IjEiIGZpbGw9IiNjY2MiIGZpbGwtb3BhY2l0eT0iMC4yIi8+PC9zdmc+'
    },
    edgeTextDraggable: true,
    nodeSelectedOutline: true,
    keyboard: {
      enabled: true
    }
  })

  // 注册自定义节点
  registerCustomNodes()

  // 设置数据
  if (flowData.value.nodes.length > 0) {
    lf.value.render(flowData.value)
  }

  // 监听事件
  lf.value.on('node:click', handleNodeClick)
  lf.value.on('edge:click', handleEdgeClick)
  lf.value.on('blank:click', handleBlankClick)
  lf.value.on('node:drop', handleNodeDrop)
  lf.value.on('node:add', handleNodeAdd)
  lf.value.on('edge:add', handleEdgeAdd)
  lf.value.on('history:change', handleHistoryChange)

  // 设置拖拽面板
  setupDndPanel()
}

// 注册自定义节点
const registerCustomNodes = () => {
  if (!lf.value) return

  const { RectNode, RectNodeModel, h } = lf.value

  // 开始节点
  lf.value.register('start', ({ RectNode, RectNodeModel, h }) => {
    class StartNode extends RectNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height, radius } = model
        const style = model.getNodeStyle()
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
            ...style
          }),
          h('text', {
            x: x,
            y: y,
            fill: '#fff',
            fontSize: 14,
            fontWeight: 'bold',
            textAnchor: 'middle',
            dominantBaseline: 'middle'
          }, model.text.value || '开始')
        ])
      }
    }

    class StartNodeModel extends RectNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        this.width = 100
        this.height = 40
        this.radius = 20
      }

      getDefaultAnchor() {
        return [
          { id: 'right', x: this.x + this.width / 2, y: this.y }
        ]
      }
    }

    return {
      view: StartNode,
      model: StartNodeModel
    }
  })

  // 审批节点
  lf.value.register('approval', ({ RectNode, RectNodeModel, h }) => {
    class ApprovalNode extends RectNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height } = model
        const properties = model.getProperties() || {}
        const approveType = properties.approveType || 'or'

        // 审批类型标识
        const typeLabel = {
          'or': '或签',
          'and': '会签',
          'seq': '依次'
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
            rx: 4
          }),
          h('text', {
            x: x,
            y: y - 8,
            fill: '#fff',
            fontSize: 14,
            fontWeight: 'bold',
            textAnchor: 'middle',
            dominantBaseline: 'middle'
          }, model.text.value || '审批'),
          h('text', {
            x: x,
            y: y + 12,
            fill: 'rgba(255,255,255,0.8)',
            fontSize: 10,
            textAnchor: 'middle',
            dominantBaseline: 'middle'
          }, typeLabel)
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

    return {
      view: ApprovalNode,
      model: ApprovalNodeModel
    }
  })

  // 条件节点
  lf.value.register('condition', ({ PolygonNode, PolygonNodeModel, h }) => {
    class ConditionNode extends PolygonNode {
      getShape() {
        const { model } = this.props
        const { x, y, width, height } = model
        const points = [
          [x, y - height / 2],
          [x + width / 2, y],
          [x, y + height / 2],
          [x - width / 2, y]
        ]

        return h('g', {}, [
          h('polygon', {
            points: points.map(p => p.join(',')).join(' '),
            fill: '#E6A23C',
            stroke: '#E6A23C',
            strokeWidth: 2
          }),
          h('text', {
            x: x,
            y: y,
            fill: '#fff',
            fontSize: 14,
            fontWeight: 'bold',
            textAnchor: 'middle',
            dominantBaseline: 'middle'
          }, model.text.value || '条件')
        ])
      }
    }

    class ConditionNodeModel extends PolygonNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        this.width = 100
        this.height = 100
      }

      getPoints() {
        const { x, y, width, height } = this
        return [
          [x, y - height / 2],
          [x + width / 2, y],
          [x, y + height / 2],
          [x - width / 2, y]
        ]
      }
    }

    return {
      view: ConditionNode,
      model: ConditionNodeModel
    }
  })

  // 抄送节点
  lf.value.register('cc', ({ RectNode, RectNodeModel, h }) => {
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
            rx: 4
          }),
          h('text', {
            x: x,
            y: y,
            fill: '#fff',
            fontSize: 14,
            fontWeight: 'bold',
            textAnchor: 'middle',
            dominantBaseline: 'middle'
          }, model.text.value || '抄送')
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

    return {
      view: CcNode,
      model: CcNodeModel
    }
  })

  // 结束节点
  lf.value.register('end', ({ RectNode, RectNodeModel, h }) => {
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
            strokeWidth: 2
          }),
          h('text', {
            x: x,
            y: y,
            fill: '#fff',
            fontSize: 14,
            fontWeight: 'bold',
            textAnchor: 'middle',
            dominantBaseline: 'middle'
          }, model.text.value || '结束')
        ])
      }
    }

    class EndNodeModel extends RectNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        this.width = 100
        this.height = 40
        this.radius = 20
      }

      getDefaultAnchor() {
        return [
          { id: 'left', x: this.x - this.width / 2, y: this.y }
        ]
      }
    }

    return {
      view: EndNode,
      model: EndNodeModel
    }
  })
}

// 设置拖拽面板
const setupDndPanel = () => {
  if (!lf.value) return

  const nodeItems = document.querySelectorAll('.node-item')

  nodeItems.forEach(item => {
    lf.value?.dndPanel.setPatternItems([
      {
        type: item.getAttribute('data-type'),
        text: item.querySelector('.node-icon')?.textContent || '',
      }
    ])
  })
}

// 事件处理
const handleNodeClick = ({ data }: any) => {
  selectedNode.value = {
    id: data.id,
    type: data.type,
    text: data.text?.value || data.text,
    properties: data.properties || {}
  }
  activeTab.value = 'basic'
}

const handleEdgeClick = ({ data }: any) => {
  // 可以添加连线选择逻辑
}

const handleBlankClick = () => {
  selectedNode.value = null
}

const handleNodeDrop = ({ data }: any) => {
  // 拖拽节点到画布时自动添加默认属性
  if (data.type === 'approval') {
    data.properties = {
      approvers: [],
      approveType: 'or',
      timeout: 72,
      autoApprove: false,
      allowTransfer: true,
      allowAddApprover: false,
      fieldPermissions: {}
    }
  } else if (data.type === 'condition') {
    data.properties = {
      conditions: [],
      defaultFlow: ''
    }
  } else if (data.type === 'cc') {
    data.properties = {
      ccUsers: [],
      ccType: 'user'
    }
  }

  selectedNode.value = {
    type: data.type,
    text: data.text?.value || data.text,
    properties: data.properties
  }
}

const handleNodeAdd = ({ data }: any) => {
  handleNodeDrop({ data })
}

const handleEdgeAdd = ({ data }: any) => {
  // 验证连线规则
  const sourceNode = lf.value?.getNodeModelById(data.sourceNodeId)
  const targetNode = lf.value?.getNodeModelById(data.targetNodeId)

  // 不允许开始节点作为目标
  if (targetNode?.type === 'start') {
    ElMessage.warning('不允许连接到开始节点')
    // Remove unsupported edge if needed (LogicFlow usually blocks? Need to implement validation logic properly or use hook)
    lf.value?.deleteEdge(data.id)
    return false
  }

  // 不允许结束节点作为源
  if (sourceNode?.type === 'end') {
    ElMessage.warning('结束节点不能作为连线起点')
    lf.value?.deleteEdge(data.id)
    return false
  }
}

const handleHistoryChange = () => {
  // 流程变化时同步数据
  const graphData = lf.value?.getGraphData()
  if (graphData) {
    flowData.value = graphData
    emit('update:modelValue', graphData)
  }
}

const updateNodeName = () => {
  if (!selectedNode.value || !lf.value) return

  const nodeModel = lf.value.getNodeModelById(selectedNode.value.id)
  if (nodeModel) {
    nodeModel.updateText(selectedNode.value.text)
  }
}

// 缩放控制
const handleZoomIn = () => {
  lf.value?.zoom(true)
}

const handleZoomOut = () => {
  lf.value?.zoom(false)
}

const handleZoomReset = () => {
  lf.value?.resetZoom()
}

// 导出/导入
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
    ElMessage.success('导入成功')
  } catch (e) {
    ElMessage.error('JSON格式错误')
  }
}

// 保存
const handleSave = () => {
  const data = lf.value?.getGraphData()
  if (!data) {
    ElMessage.warning('请先设计流程')
    return
  }

  // 验证流程
  if (!validateFlow(data)) {
    return
  }

  emit('save', data)
}

// 验证流程
const validateFlow = (data: any) => {
  const nodes = data.nodes || []
  const edges = data.edges || []

  // 必须有开始和结束节点
  const hasStart = nodes.some((n: any) => n.type === 'start')
  const hasEnd = nodes.some((n: any) => n.type === 'end')

  if (!hasStart) {
    ElMessage.error('流程必须包含开始节点')
    return false
  }

  if (!hasEnd) {
    ElMessage.error('流程必须包含结束节点')
    return false
  }

  // 检查所有节点是否连通
  if (nodes.length > 1 && edges.length === 0) {
    ElMessage.error('请连接节点')
    return false
  }

  return true
}

const getNodeTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    start: '开始',
    end: '结束',
    approval: '审批',
    condition: '条件',
    cc: '抄送'
  }
  return labels[type] || type
}

const needPermissionConfig = computed(() => {
  return ['approval', 'start'].includes(selectedNode.value?.type)
})

// 监听外部数据变化
watch(() => props.modelValue, (newVal) => {
  if (newVal && lf.value && JSON.stringify(newVal) !== JSON.stringify(flowData.value)) {
    flowData.value = newVal
    lf.value.render(newVal)
  }
}, { deep: true })
</script>

<style scoped>
.workflow-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
  position: relative; /* Ensure absolute children are relative to this */
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
  cursor: move;
}

.node-icon {
  padding: 10px 16px;
  text-align: center;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: grab;
  user-select: none;
}

.node-icon:active {
  cursor: grabbing;
}

.node-icon.start { background: #67C23A; }
.node-icon.end { background: #F56C6C; }
.node-icon.approval { background: #409EFF; }
.node-icon.condition { background: #E6A23C; }
.node-icon.cc { background: #909399; }

.canvas-container {
  flex: 1;
  /* Adjust margin to accommodate panels */
  margin: 0;
  background: #fff;
  border-radius: 4px;
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.05); /* inset for canvas feel */
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
