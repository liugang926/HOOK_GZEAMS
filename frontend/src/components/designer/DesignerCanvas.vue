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
        <span v-if="renderMode === 'design'">{{ t('system.pageLayout.designer.hints.designCanvas') }}</span>
        <span v-else>{{ t('system.pageLayout.designer.hints.previewCanvas') }}</span>
      </div>
      <div class="canvas-header-right">
        <el-radio-group
          :model-value="layoutMode"
          size="small"
          class="layout-mode-toggle"
          style="margin-right: 16px;"
          @update:model-value="$emit('update:layoutMode', $event as 'Detail' | 'Compact')"
        >
          <el-radio-button label="Detail">
            {{ t('system.pageLayout.designer.modes.detail', 'Detail View') }}
          </el-radio-button>
          <el-radio-button label="Compact">
            {{ t('system.pageLayout.designer.modes.compact', 'Compact View') }}
          </el-radio-button>
        </el-radio-group>

        <el-radio-group
          :model-value="renderMode"
          size="small"
          @update:model-value="$emit('setRenderMode', $event as 'design' | 'preview')"
        >
          <el-radio-button
            label="design"
            data-testid="layout-render-design-button"
          >
            {{ t('system.pageLayout.designer.status.designState') }}
          </el-radio-button>
          <el-radio-button
            label="preview"
            data-testid="layout-render-preview-button"
          >
            {{ t('system.pageLayout.designer.status.previewState') }}
          </el-radio-button>
        </el-radio-group>

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
}>()

defineEmits<{
  (e: 'canvasDrop', event: DragEvent): void
  (e: 'canvasDragOver', event: DragEvent): void
  (e: 'canvasDragLeave', event: DragEvent): void
  (e: 'setRenderMode', value: 'design' | 'preview'): void
  (e: 'update:layoutMode', value: 'Detail' | 'Compact'): void
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
