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
        <el-dropdown
          v-if="renderMode === 'design' && detailRegionOptions.length > 0"
          trigger="click"
          @command="handleDetailRegionCommand"
        >
          <el-button
            size="small"
            text
            data-testid="layout-add-detail-region"
          >
            <el-icon><Grid /></el-icon>
            {{ detailRegionActionLabel }}
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="option in detailRegionOptions"
                :key="option.value"
                :command="option.value"
              >
                {{ option.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
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
import { computed, ref, type CSSProperties } from 'vue'
import { useI18n } from 'vue-i18n'
import { Grid, Plus } from '@element-plus/icons-vue'
import type { DesignerDetailRegionOption } from '@/components/designer/designerTypes'
import type { ResizeHintState } from '@/components/designer/designerTypes'

const props = defineProps<{
  renderMode: 'design' | 'preview'
  layoutMode: 'Detail' | 'Compact'
  isDragOverCanvas: boolean
  resizeHint: ResizeHintState | null
  resizeHintStyle: CSSProperties
  totalFields?: number
  requiredFields?: number
  sectionCount?: number
  detailRegionOptions?: Array<{ label: string; value: string | DesignerDetailRegionOption }>
}>()

const emit = defineEmits<{
  (e: 'canvasDrop', event: DragEvent): void
  (e: 'canvasDragOver', event: DragEvent): void
  (e: 'canvasDragLeave', event: DragEvent): void
  (e: 'addSection'): void
  (e: 'addDetailRegion', relationCode: string | DesignerDetailRegionOption): void
}>()

const { t } = useI18n()
const canvasAreaRef = ref<HTMLElement | null>(null)
const canvasContentRef = ref<HTMLElement | null>(null)
const detailRegionOptions = computed(() => props.detailRegionOptions || [])
const detailRegionActionLabel = computed(() => `${t('common.actions.add')} ${t('system.pageLayout.designer.defaults.detailRegion')}`)

const handleDetailRegionCommand = (relationCode: string | number | object) => {
  if (relationCode && typeof relationCode === 'object' && 'relationCode' in relationCode) {
    emit('addDetailRegion', relationCode as DesignerDetailRegionOption)
    return
  }
  if (typeof relationCode !== 'string' || !relationCode.trim()) return
  emit('addDetailRegion', relationCode)
}

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
  background: linear-gradient(180deg, #f7f8fb 0%, #eef2f7 100%);
}

.canvas-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.94);
  border-bottom: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.canvas-header-left {
  min-width: 0;
}

.canvas-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.canvas-hint-text {
  font-size: 12px;
  color: #475569;
  letter-spacing: 0.01em;
}

.canvas-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 22px clamp(18px, 2vw, 28px) 180px;
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
  width: min(100%, 1280px);
  margin: 0 auto;
  min-height: calc(100% - 60px);
}

.compact-canvas-mode {
  max-width: 680px;
  margin: 0 auto;
  width: 100%;
}

.canvas-stats-bar {
  flex-shrink: 0;
}
</style>
