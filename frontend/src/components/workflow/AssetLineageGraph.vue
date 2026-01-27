<template>
  <div class="asset-lineage-graph">
    <div
      ref="containerRef"
      class="graph-container"
    />
    
    <!-- Time Travel Tooltip/Panel could go here -->
    <div
      v-if="selectedNode"
      class="node-detail-panel glass-card"
    >
      <h4>{{ selectedNode.text?.value || selectedNode.text }}</h4>
      <p class="timestamp">
        {{ selectedNode.properties?.date }}
      </p>
      <p class="description">
        {{ selectedNode.properties?.description }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import LogicFlow from '@logicflow/core'
import { Menu, Snapshot } from '@logicflow/extension'
import '@logicflow/core/dist/style/index.css'

interface LineageEvent {
  id: string
  type: 'purchase' | 'pickup' | 'loan' | 'return' | 'repair' | 'dispose'
  label: string
  date: string
  operator: string
  description?: string
}

interface Props {
  events?: LineageEvent[]
}

const props = defineProps<Props>()
const containerRef = ref<HTMLElement | null>(null)
const lf = ref<LogicFlow | null>(null)
const selectedNode = ref<any>(null)

// Custom Theme Colors (Matching our new variables)
const colors = {
  primary: '#2563eb',
  success: '#10b981', 
  warning: '#f59e0b',
  danger: '#ef4444', 
  gray: '#9ca3af',
  line: '#cbd5e1'
}

const initLogicFlow = () => {
  if (!containerRef.value) return

  lf.value = new LogicFlow({
    container: containerRef.value,
    width: containerRef.value.clientWidth,
    height: 400, // Fixed height or responsive
    isSilentMode: true, // View-only essentially
    grid: false,
    keyboard: { enabled: true }
  })

  // Register Custom Nodes (Simplified for concise UI)
  registerNodes()

  // Event Listeners
  lf.value.on('node:click', ({ data }) => {
    selectedNode.value = data
  })
  
  lf.value.on('blank:click', () => {
    selectedNode.value = null
  })

  renderGraph()
}

const registerNodes = () => {
  if (!lf.value) return
  const { CircleNode, CircleNodeModel, h } = lf.value

  // Generic Event Node
  lf.value.register('event-node', ({ CircleNode, CircleNodeModel, h }) => {
    class EventNode extends CircleNode {
      getShape() {
        const { model } = this.props
        const { x, y, r } = model
        const style = model.getNodeStyle()
        const prop = model.getProperties()
        
        // Icon based on type (simplified as text for now, could be SVG icons)
        const iconMap: any = {
          purchase: '🛒',
          pickup: '🙋',
          loan: '🤝',
          return: '↩️',
          repair: '🔧',
          dispose: '🗑️'
        }

        return h('g', {}, [
          h('circle', {
            cx: x,
            cy: y,
            r: 25,
            fill: prop.color || colors.primary,
            stroke: 'white',
            strokeWidth: 3,
            cursor: 'pointer',
            ...style
          }),
          h('text', {
            x: x,
            y: y + 5, // visually centered
            fontSize: 16,
            textAnchor: 'middle',
            fill: 'white',
            cursor: 'pointer'
          }, iconMap[prop.eventType] || '●')
        ])
      }
    }
    
    class EventNodeModel extends CircleNodeModel {
      initNodeData(data: any) {
        super.initNodeData(data)
        this.r = 25
      }
    }

    return { view: EventNode, model: EventNodeModel }
  })
}

// The "Algorithm": Transform flat events into a graph structure
const renderGraph = () => {
  if (!lf.value || !props.events) return

  const nodes: any[] = []
  const edges: any[] = []
  
  const startX = 100
  const startY = 200
  const gap = 150

  props.events.forEach((event, index) => {
    // Determine color based on type
    let color = colors.primary
    if (['return', 'pickup'].includes(event.type)) color = colors.success
    if (['repair'].includes(event.type)) color = colors.warning
    if (['dispose'].includes(event.type)) color = colors.danger

    // Node
    const nodeId = `node-${index}`
    nodes.push({
      id: nodeId,
      type: 'event-node',
      x: startX + (index * gap),
      y: startY,
      text: {
        value: `${event.label}\n${event.date}`,
        x: startX + (index * gap),
        y: startY + 45
      },
      properties: {
        eventType: event.type,
        color: color,
        ...event
      }
    })

    // Edge (link to previous)
    if (index > 0) {
      edges.push({
        id: `edge-${index}`,
        type: 'polyline',
        sourceNodeId: `node-${index-1}`,
        targetNodeId: nodeId,
        text: { value: '▶', x: 0, y: 0 }, // optional label
        properties: {
          style: { stroke: colors.line, strokeWidth: 2 }
        }
      })
    }
  })

  lf.value.render({ nodes, edges })
}

watch(() => props.events, renderGraph, { deep: true })

onMounted(() => {
  initLogicFlow()
})

onUnmounted(() => {
  if (lf.value) {
    // lf.value.destroy() // LogicFlow destroy method might vary in versions, keeping safe
  }
})
</script>

<style scoped lang="scss">
.asset-lineage-graph {
  position: relative;
  width: 100%;
  height: 400px;
  background: #f8fafc; // Matches our new variables
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.graph-container {
  width: 100%;
  height: 100%;
}

.node-detail-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 250px;
  padding: 16px;
  z-index: 10;
  
  h4 {
    margin: 0 0 8px 0;
    color: var(--el-text-color-primary);
  }
  
  .timestamp {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-bottom: 8px;
  }
  
  .description {
    font-size: 14px;
    color: var(--el-text-color-regular);
    line-height: 1.5;
  }
}
</style>
