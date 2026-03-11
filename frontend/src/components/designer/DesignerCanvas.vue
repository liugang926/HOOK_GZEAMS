<template>
  <div
    ref="canvasAreaRef"
    class="canvas-area"
    data-testid="layout-canvas"
    :class="{ 'drag-over': isDragOverCanvas }"
    @drop="$emit('canvasDrop', $event)"
    @dragover="$emit('canvasDragOver', $event)"
    @dragleave="$emit('canvasDragLeave', $event)"
  >
    <div class="canvas-header">
      <div class="canvas-header-left">
        <span class="canvas-hint-text">
          {{ renderMode === 'design'
            ? t('system.pageLayout.designer.hints.designCanvas')
            : t('system.pageLayout.designer.hints.previewCanvas') }}
        </span>
      </div>
      <div class="canvas-header-right">
        <el-button
          v-if="renderMode === 'design'"
          size="small"
          text
          @click="$emit('addSection')"
        >
          <el-icon><Plus /></el-icon>
          {{ t('system.pageLayout.designer.actions.addSection') }}
        </el-button>
      </div>
    </div>

    <div
      ref="canvasContentRef"
      class="canvas-content"
      :class="{ 'compact-canvas-mode': layoutMode === 'Compact' }"
    >
      <div class="canvas-render-shell">
        <slot />
      </div>
    </div>

    <div
      v-if="resizeHint"
      class="field-resize-hint"
      data-testid="layout-field-resize-hint"
      :style="resizeHintStyle"
    >
      <span data-testid="layout-field-resize-hint-span">{{ resizeHint.span }} / {{ resizeHint.columns }}</span>
      <span data-testid="layout-field-resize-hint-height">{{ resizeHint.minHeight }}px</span>
    </div>

    <div
      v-if="renderMode === 'design'"
      class="canvas-stats-bar"
      data-testid="layout-canvas-stats"
    >
      <span>{{ totalFields }} {{ t('system.pageLayout.designer.stats.fields', '个字段') }}</span>
      <span class="stats-separator">·</span>
      <span>{{ requiredFields }} {{ t('system.pageLayout.designer.stats.required', '个必填') }}</span>
      <span class="stats-separator">·</span>
      <span>{{ sectionCount }} {{ t('system.pageLayout.designer.stats.sections', '个分组') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'
import type { ResizeHintState } from '@/components/designer/designerTypes'

const props = defineProps<{
  renderMode: 'design' | 'preview'
  layoutMode: 'Detail' | 'Compact'
  isDragOverCanvas: boolean
  resizeHint: ResizeHintState | null
  resizeHintStyle: Record<string, string>
  totalFields?: number
  requiredFields?: number
  sectionCount?: number
}>()

defineEmits<{
  (e: 'canvasDrop', event: DragEvent): void
  (e: 'canvasDragOver', event: DragEvent): void
  (e: 'canvasDragLeave', event: DragEvent): void
  (e: 'addSection'): void
}>()

const { t } = useI18n()
const canvasAreaRef = ref<HTMLElement | null>(null)
const canvasContentRef = ref<HTMLElement | null>(null)

defineExpose({
  canvasAreaRef,
  canvasContentRef,
  canvasAreaElement: computed(() => canvasAreaRef.value),
  canvasContentElement: computed(() => canvasContentRef.value)
})
</script>

<style scoped lang="scss">
.canvas-area {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f0f2f5;
}

.canvas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 20px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.canvas-header-left {
  min-width: 0;
}

.canvas-hint-text {
  font-size: 12px;
  color: #606266;
}

.canvas-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 24px 24px 200px;
  overscroll-behavior: contain;
}

.canvas-content::-webkit-scrollbar {
  width: 8px;
}

.canvas-content::-webkit-scrollbar-thumb {
  background: rgba(15, 23, 42, 0.16);
  border-radius: 999px;
}

.canvas-render-shell {
  min-height: calc(100% - 60px);
}

.compact-canvas-mode {
  max-width: 640px;
  margin: 0 auto;
  width: 100%;
}

.canvas-stats-bar {
  flex-shrink: 0;
}
</style>
