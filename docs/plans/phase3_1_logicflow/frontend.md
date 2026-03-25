# Phase 3.1: LogicFlow流程设计器 - 前端实现

## 前端公共组件引用

| 组件名 | 组件路径 | 用途 |
|--------|---------|------|
| BaseListPage | @/components/common/BaseListPage.vue | 列表页面 |
| BaseFormPage | @/components/common/BaseFormPage.vue | 表单页面 |
| BaseDetailPage | @/components/common/BaseDetailPage.vue | 详情页面 |

---

## 安装依赖

```bash
# frontend/
npm install @logicflow/core @logicflow/extension --save
```

---

---

## 公共组件引用

### 页面组件
本模块使用以下公共页面组件（详见 `common_base_features/frontend.md`）：

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseListPage` | 标准列表页面 | `@/components/common/BaseListPage.vue` |
| `BaseFormPage` | 标准表单页面 | `@/components/common/BaseFormPage.vue` |
| `BaseDetailPage` | 标准详情页面 | `@/components/common/BaseDetailPage.vue` |

### 基础组件

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseTable` | 统一表格 | `@/components/common/BaseTable.vue` |
| `BaseSearchBar` | 搜索栏 | `@/components/common/BaseSearchBar.vue` |
| `BasePagination` | 分页 | `@/components/common/BasePagination.vue` |
| `BaseAuditInfo` | 审计信息 | `@/components/common/BaseAuditInfo.vue` |
| `BaseFileUpload` | 文件上传 | `@/components/common/BaseFileUpload.vue` |

### 列表字段显示管理（推荐）

| 组件 | Hook | 参考文档 |
|------|------|---------|
| `ColumnManager` | 列显示/隐藏/排序/列宽配置 | `list_column_configuration.md` |
| `useColumnConfig` | 列配置Hook（获取/保存/重置） | `list_column_configuration.md` |

**功能包括**:
- ✓ 列的显示/隐藏
- ✓ 列的拖拽排序
- ✓ 列宽调整
- ✓ 列固定（左/右）
- ✓ 用户个性化配置保存

### 布局组件

| 组件 | 用途 | 参考文档 |
|------|------|---------|
| `DynamicTabs` | 动态标签页 | `tab_configuration.md` |
| `SectionBlock` | 区块容器 | `section_block_layout.md` |
| `FieldRenderer` | 动态字段渲染 | `field_configuration_layout.md` |

### Composables/Hooks

| Hook | 用途 | 引用路径 |
|------|------|---------|
| `useListPage` | 列表页面逻辑 | `@/composables/useListPage.js` |
| `useFormPage` | 表单页面逻辑 | `@/composables/useFormPage.js` |
| `usePermission` | 权限检查 | `@/composables/usePermission.js` |

### 组件继承关系

```vue
<!-- 列表页面 -->
<BaseListPage
    title="页面标题"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
>
    <!-- 自定义列插槽 -->
</BaseListPage>

<!-- 表单页面 -->
<BaseFormPage
    title="表单标题"
    :submit-method="handleSubmit"
    :initial-data="formData"
    :rules="rules"
>
    <!-- 自定义表单项 -->
</BaseFormPage>
```

---

## 1. 流程设计器主组件

### WorkflowDesigner.vue

```vue
<template>
  <div class="workflow-designer">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button-group>
        <el-button :icon="ZoomOut" @click="handleZoomOut" />
        <el-button @click="handleZoomReset">100%</el-button>
        <el-button :icon="ZoomIn" @click="handleZoomIn" />
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button :icon="Download" @click="handleExport">导出JSON</el-button>
      <el-button :icon="Upload" @click="handleImport">导入JSON</el-button>
      <el-divider direction="vertical" />
      <el-button type="primary" @click="handleSave">保存流程</el-button>
    </div>

    <!-- 节点面板 -->
    <div class="node-panel">
      <div class="panel-section">
        <div class="section-title">基础节点</div>
        <div class="node-item" data-type="start">
          <div class="node-icon start">开始</div>
        </div>
        <div class="node-item" data-type="end">
          <div class="node-icon end">结束</div>
        </div>
      </div>
      <div class="panel-section">
        <div class="section-title">审批节点</div>
        <div class="node-item" data-type="approval">
          <div class="node-icon approval">审批</div>
        </div>
        <div class="node-item" data-type="condition">
          <div class="node-icon condition">条件</div>
        </div>
      </div>
      <div class="panel-section">
        <div class="section-title">抄送节点</div>
        <div class="node-item" data-type="cc">
          <div class="node-icon cc">抄送</div>
        </div>
      </div>
    </div>

    <!-- 画布区域 -->
    <div class="canvas-container" ref="containerRef"></div>

    <!-- 属性面板 -->
    <div class="property-panel" v-if="selectedNode">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="基础属性" name="basic">
          <el-form :model="selectedNode" label-width="80px">
            <el-form-item label="节点名称">
              <el-input v-model="selectedNode.text" @input="updateNodeName" />
            </el-form-item>
            <el-form-item label="节点类型">
              <el-input :value="getNodeTypeLabel(selectedNode.type)" disabled />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="审批配置" name="approval" v-if="selectedNode.type === 'approval'">
          <ApprovalNodeConfig v-model="selectedNode.properties" />
        </el-tab-pane>

        <el-tab-pane label="条件配置" name="condition" v-if="selectedNode.type === 'condition'">
          <ConditionNodeConfig v-model="selectedNode.properties" />
        </el-tab-pane>

        <el-tab-pane label="字段权限" name="permission" v-if="needPermissionConfig">
          <FieldPermissionConfig
            v-model="selectedNode.properties.fieldPermissions"
            :business-object="businessObject"
          />
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importDialogVisible" title="导入流程" width="600px">
      <el-input
        v-model="importJson"
        type="textarea"
        :rows="10"
        placeholder="请粘贴流程JSON数据"
      />
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleImportConfirm">导入</el-button>
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
            rx: radius,
            ry: radius,
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
            rx: radius,
            ry: radius,
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
    lf.value?.value.dndPanel.setPatternItems([
      {
        type: item.getAttribute('data-type'),
        text: item.querySelector('.node-icon')?.textContent || '',
        icon: ''
      }
    ])
  })
}

// 事件处理
const handleNodeClick = ({ data }) => {
  selectedNode.value = {
    id: data.id,
    type: data.type,
    text: data.text,
    properties: data.properties || {}
  }
  activeTab.value = 'basic'
}

const handleEdgeClick = ({ data }) => {
  // 可以添加连线选择逻辑
}

const handleBlankClick = () => {
  selectedNode.value = null
}

const handleNodeDrop = ({ data }) => {
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
    text: data.text,
    properties: data.properties
  }
}

const handleNodeAdd = ({ data }) => {
  handleNodeDrop({ data })
}

const handleEdgeAdd = ({ data }) => {
  // 验证连线规则
  const sourceNode = lf.value?.getNodeModelById(data.sourceNodeId)
  const targetNode = lf.value?.getNodeModelById(data.targetNodeId)

  // 不允许开始节点作为目标
  if (targetNode?.type === 'start') {
    ElMessage.warning('不允许连接到开始节点')
    return false
  }

  // 不允许结束节点作为源
  if (sourceNode?.type === 'end') {
    ElMessage.warning('结束节点不能作为连线起点')
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
    nodeModel.text.value = selectedNode.value.text
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
  margin: 70px 330px 20px 180px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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
```

---

## 2. 审批节点配置组件

### ApprovalNodeConfig.vue

```vue
<template>
  <div class="approval-config">
    <el-form :model="localValue" label-width="90px" size="small">
      <el-form-item label="审批方式">
        <el-radio-group v-model="localValue.approveType">
          <el-radio value="or">或签（一人通过）</el-radio>
          <el-radio value="and">会签（全部通过）</el-radio>
          <el-radio value="seq">依次审批</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="审批人">
        <ApproverSelector v-model="localValue.approvers" />
      </el-form-item>

      <el-form-item label="超时时间">
        <el-input-number
          v-model="localValue.timeout"
          :min="1"
          :max="720"
          controls-position="right"
        />
        <span class="unit">小时</span>
      </el-form-item>

      <el-form-item label="超时操作">
        <el-select v-model="localValue.timeoutAction">
          <el-option label="自动通过" value="approve" />
          <el-option label="自动拒绝" value="reject" />
          <el-option label="转交管理员" value="transfer" />
        </el-select>
      </el-form-item>

      <el-form-item label="自动通过">
        <el-switch v-model="localValue.autoApprove" />
        <span class="tip">审批人与发起人相同时自动通过</span>
      </el-form-item>

      <el-form-item label="允许转交">
        <el-switch v-model="localValue.allowTransfer" />
      </el-form-item>

      <el-form-item label="允许加签">
        <el-switch v-model="localValue.allowAddApprover" />
      </el-form-item>

      <el-form-item label="退回方式">
        <el-radio-group v-model="localValue.rejectType">
          <el-radio value="to_start">退回到发起人</el-radio>
          <el-radio value="to_prev">退回到上一节点</el-radio>
        </el-radio-group>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ApproverSelector from './ApproverSelector.vue'

interface Props {
  modelValue: Record<string, any>
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localValue = computed({
  get: () => props.modelValue || {
    approveType: 'or',
    approvers: [],
    timeout: 72,
    timeoutAction: 'transfer',
    autoApprove: false,
    allowTransfer: true,
    allowAddApprover: false,
    rejectType: 'to_prev'
  },
  set: (val) => emit('update:modelValue', val)
})
</script>

<style scoped>
.approval-config {
  padding: 5px 0;
}

.unit {
  margin-left: 8px;
  color: #909399;
  font-size: 13px;
}

.tip {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}
</style>
```

---

## 3. 审批人选择器组件

### ApproverSelector.vue

```vue
<template>
  <div class="approver-selector">
    <el-tabs v-model="activeTab" type="card" size="small">
      <el-tab-pane label="指定成员" name="user">
        <UserSelector v-model="approvers" :multiple="true" />
      </el-tab-pane>

      <el-tab-pane label="指定角色" name="role">
        <RoleSelector v-model="approvers" />
      </el-tab-pane>

      <el-tab-pane label="发起人领导" name="leader">
        <div class="leader-config">
          <el-radio-group v-model="leaderConfig.type">
            <el-radio value="direct">直属领导</el-radio>
            <el-radio value="department">部门负责人</el-radio>
            <el-radio value="top">第N上级</el-radio>
          </el-radio-group>

          <el-input-number
            v-if="leaderConfig.type === 'top'"
            v-model="leaderConfig.level"
            :min="1"
            :max="5"
            size="small"
            style="margin-left: 10px"
          />
          <span v-if="leaderConfig.type === 'top'" style="margin-left: 5px">级</span>
        </div>
      </el-tab-pane>

      <el-tab-pane label="动态选择" name="dynamic">
        <el-form size="small">
          <el-form-item label="来源字段">
            <el-select v-model="dynamicConfig.field">
              <el-option label="申请人" value="applicant" />
              <el-option label="部门" value="department" />
              <el-option label="领用部门" value="pickup_department" />
            </el-select>
          </el-form-item>
          <el-form-item label="关系">
            <el-select v-model="dynamicConfig.relation">
              <el-option label="的直属领导" value="leader" />
              <el-option label="的部门负责人" value="manager" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane label="自选" name="self_select">
        <el-form size="small">
          <el-form-item label="可选范围">
            <el-radio-group v-model="selfSelectConfig.range">
              <el-radio value="all">全员</el-radio>
              <el-radio value="department">本部门</el-radio>
              <el-radio value="custom">自定义</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="选择人数">
            <el-input-number
              v-model="selfSelectConfig.count"
              :min="1"
              :max="10"
              size="small"
            />
            <span style="margin-left: 5px">人</span>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import UserSelector from '@/components/common/UserSelector.vue'
import RoleSelector from '@/components/common/RoleSelector.vue'

interface Props {
  modelValue: any[]
}

interface Emits {
  (e: 'update:modelValue', value: any[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const activeTab = ref('user')

const approvers = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val)
})

const leaderConfig = ref({
  type: 'direct',
  level: 1
})

const dynamicConfig = ref({
  field: 'applicant',
  relation: 'leader'
})

const selfSelectConfig = ref({
  range: 'department',
  count: 1
})
</script>

<style scoped>
.approver-selector {
  padding: 10px 0;
}

.leader-config {
  display: flex;
  align-items: center;
}
</style>
```

---

## 4. 条件节点配置组件

### ConditionNodeConfig.vue

```vue
<template>
  <div class="condition-config">
    <el-form :model="localValue" label-width="80px" size="small">
      <el-form-item label="条件分支">
        <div class="condition-branches">
          <div
            v-for="(branch, index) in localValue.branches"
            :key="index"
            class="condition-branch"
          >
            <div class="branch-header">
              <span class="branch-label">分支 {{ index + 1 }}</span>
              <el-button
                v-if="localValue.branches.length > 1"
                :icon="Delete"
                circle
                size="small"
                type="danger"
                @click="removeBranch(index)"
              />
            </div>

            <el-form-item label="条件">
              <el-select
                v-model="branch.field"
                placeholder="选择字段"
                style="width: 100%"
              >
                <el-option
                  v-for="field in availableFields"
                  :key="field.code"
                  :label="field.name"
                  :value="field.code"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="运算符">
              <el-select v-model="branch.operator" style="width: 100%">
                <el-option label="等于" value="eq" />
                <el-option label="不等于" value="ne" />
                <el-option label="大于" value="gt" />
                <el-option label="大于等于" value="gte" />
                <el-option label="小于" value="lt" />
                <el-option label="小于等于" value="lte" />
                <el-option label="包含" value="contains" />
                <el-option label="不包含" value="not_contains" />
              </el-select>
            </el-form-item>

            <el-form-item label="值">
              <el-input v-model="branch.value" placeholder="条件值" />
            </el-form-item>
          </div>
        </div>
      </el-form-item>

      <el-form-item>
        <el-button :icon="Plus" @click="addBranch">添加分支</el-button>
      </el-form-item>

      <el-form-item label="默认分支">
        <el-select
          v-model="localValue.defaultFlow"
          placeholder="条件不满足时的去向"
          style="width: 100%"
        >
          <el-option label="拒绝" value="reject" />
          <el-option label="通过" value="approve" />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'

interface Props {
  modelValue: Record<string, any>
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const localValue = computed({
  get: () => props.modelValue || {
    branches: [
      { field: '', operator: 'eq', value: '' }
    ],
    defaultFlow: 'reject'
  },
  set: (val) => emit('update:modelValue', val)
})

// 可用字段（从业务对象获取）
const availableFields = ref([
  { code: 'amount', name: '金额' },
  { code: 'department', name: '部门' },
  { code: 'applicant', name: '申请人' }
])

const addBranch = () => {
  if (!localValue.value.branches) {
    localValue.value.branches = []
  }
  localValue.value.branches.push({
    field: '',
    operator: 'eq',
    value: ''
  })
  emit('update:modelValue', localValue.value)
}

const removeBranch = (index: number) => {
  localValue.value.branches.splice(index, 1)
  emit('update:modelValue', localValue.value)
}
</script>

<style scoped>
.condition-config {
  padding: 5px 0;
}

.condition-branches {
  width: 100%;
}

.condition-branch {
  padding: 10px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  margin-bottom: 10px;
}

.branch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.branch-label {
  font-weight: 500;
  color: #606266;
}
</style>
```

---

## 5. 字段权限配置组件

### FieldPermissionConfig.vue

```vue
<template>
  <div class="field-permission-config">
    <el-table :data="fields" border size="small" :show-header="true">
      <el-table-column prop="label" label="字段" width="140" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column label="权限" width="140">
        <template #default="{ row }">
          <el-select v-model="row.permission" size="small">
            <el-option label="可编辑" value="editable" />
            <el-option label="只读" value="read_only" />
            <el-option label="隐藏" value="hidden" />
          </el-select>
        </template>
      </el-table-column>
    </el-table>

    <div class="batch-actions">
      <el-button size="small" @click="setAll('editable')">全部可编辑</el-button>
      <el-button size="small" @click="setAll('read_only')">全部只读</el-button>
      <el-button size="small" @click="setAll('hidden')">全部隐藏</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { getFieldDefinitions } from '@/api/system'

interface Props {
  modelValue: Record<string, string>
  businessObject: string
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, string>): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

interface Field {
  code: string
  label: string
  permission: string
}

const fields = ref<Field[]>([])

onMounted(async () => {
  try {
    const res = await getFieldDefinitions(props.businessObject)
    fields.value = res.map((field: any) => ({
      code: field.code,
      label: field.name,
      permission: props.modelValue?.[field.code] || 'editable'
    }))
  } catch (error) {
    console.error('获取字段定义失败', error)
  }
})

const setAll = (permission: string) => {
  fields.value.forEach(f => f.permission = permission)
}

watch(fields, (newVal) => {
  const permissions: Record<string, string> = {}
  newVal.forEach(f => {
    permissions[f.code] = f.permission
  })
  emit('update:modelValue', permissions)
}, { deep: true })
</script>

<style scoped>
.field-permission-config {
  padding: 5px 0;
}

.batch-actions {
  margin-top: 15px;
  padding-top: 10px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
}
</style>
```

---

## 6. API 集成

```typescript
// src/api/workflows.ts

import request from '@/utils/request'

export interface WorkflowDefinition {
  id?: number
  code: string
  name: string
  business_object: string
  graph_data: any
  description?: string
  version?: number
  is_enabled?: boolean
  is_default?: boolean
}

/**
 * 获取工作流列表
 */
export const getWorkflows = (params?: { business_object?: string }) => {
  return request.get('/api/workflows/workflows/', { params })
}

/**
 * 获取工作流详情
 */
export const getWorkflow = (id: number) => {
  return request.get(`/api/workflows/workflows/${id}/`)
}

/**
 * 创建工作流
 */
export const createWorkflow = (data: WorkflowDefinition) => {
  return request.post('/api/workflows/workflows/', data)
}

/**
 * 更新工作流
 */
export const updateWorkflow = (id: number, data: Partial<WorkflowDefinition>) => {
  return request.patch(`/api/workflows/workflows/${id}/`, data)
}

/**
 * 删除工作流
 */
export const deleteWorkflow = (id: number) => {
  return request.delete(`/api/workflows/workflows/${id}/`)
}

/**
 * 激活工作流
 */
export const activateWorkflow = (id: number) => {
  return request.post(`/api/workflows/workflows/${id}/activate/`)
}

/**
 * 克隆工作流
 */
export const cloneWorkflow = (id: number) => {
  return request.post(`/api/workflows/workflows/${id}/clone/`)
}
```

---

## 7. 路由配置

```typescript
// src/router/index.ts

const routes: RouteRecordRaw[] = [
  // ... 其他路由
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'workflows',
        name: 'WorkflowList',
        component: () => import('@/views/admin/WorkflowList.vue'),
        meta: { title: '工作流管理', permission: 'workflow.manage' }
      },
      {
        path: 'workflows/:id/edit',
        name: 'WorkflowEdit',
        component: () => import('@/views/admin/WorkflowEdit.vue'),
        meta: { title: '编辑工作流', permission: 'workflow.manage' }
      },
      {
        path: 'workflows/create',
        name: 'WorkflowCreate',
        component: () => import('@/views/admin/WorkflowEdit.vue'),
        meta: { title: '创建工作流', permission: 'workflow.manage' }
      }
    ]
  }
]
```

---

## 后续任务

1. Phase 3.2: 实现工作流执行引擎
2. Phase 4.1: 实现QR码扫描盘点
