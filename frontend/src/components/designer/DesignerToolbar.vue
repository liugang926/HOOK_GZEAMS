<template>
  <div class="designer-toolbar">
    <div class="toolbar-left">
      <el-button
        link
        @click="$emit('cancel')"
      >
        <el-icon><ArrowLeft /></el-icon>
        {{ t('common.actions.back') }}
      </el-button>
      <el-divider direction="vertical" />
      <span class="layout-info">{{ layoutName }}</span>
      <el-tag
        v-if="!isDefault"
        type="warning"
        size="small"
        effect="light"
        round
      >
        {{ t('system.pageLayout.designer.badges.customLayout') }}
      </el-tag>
    </div>

    <div class="toolbar-center">
      <el-segmented
        :model-value="viewMode"
        :options="viewModeOptions"
        size="small"
        data-testid="layout-view-mode-toggle"
        @update:model-value="$emit('update:viewMode', $event as string)"
      />
      <el-segmented
        :model-value="viewport"
        :options="viewportOptions"
        size="small"
        data-testid="layout-viewport-toggle"
        @update:model-value="$emit('update:viewport', $event as string)"
      />
      <el-segmented
        :model-value="renderMode"
        :options="renderModeOptions"
        size="small"
        data-testid="layout-render-mode-toggle"
        @update:model-value="$emit('update:renderMode', $event as string)"
      />
    </div>

    <div class="toolbar-right">
      <el-button-group data-testid="layout-preview-mode-toggle">
        <el-button
          size="small"
          data-testid="layout-preview-current-button"
          :type="previewMode === 'current' ? 'primary' : undefined"
          :plain="previewMode !== 'current'"
          :disabled="previewLoading || previewMode === 'current'"
          @click="$emit('setPreviewMode', 'current')"
        >
          {{ t('system.pageLayout.designer.actions.custom') }}
        </el-button>
        <el-button
          size="small"
          data-testid="layout-preview-active-button"
          :type="previewMode === 'active' ? 'primary' : undefined"
          :plain="previewMode !== 'active'"
          :loading="previewLoading && previewMode === 'active'"
          :disabled="previewLoading || previewMode === 'active'"
          @click="$emit('setPreviewMode', 'active')"
        >
          {{ t('system.pageLayout.designer.actions.preview') }}
        </el-button>
      </el-button-group>
      <el-divider direction="vertical" />
      <el-button-group>
        <el-tooltip :content="t('system.pageLayout.designer.actions.undo') + ' (Ctrl+Z)'" placement="bottom" :show-after="400">
          <el-button
            size="small"
            data-testid="layout-undo-button"
            :aria-label="t('system.pageLayout.designer.actions.undo')"
            :disabled="!canUndo"
            @click="$emit('undo')"
          >
            <el-icon><RefreshLeft /></el-icon>
          </el-button>
        </el-tooltip>
        <el-tooltip :content="t('system.pageLayout.designer.actions.redo') + ' (Ctrl+Shift+Z)'" placement="bottom" :show-after="400">
          <el-button
            size="small"
            data-testid="layout-redo-button"
            :aria-label="t('system.pageLayout.designer.actions.redo')"
            :disabled="!canRedo"
            @click="$emit('redo')"
          >
            <el-icon><RefreshRight /></el-icon>
          </el-button>
        </el-tooltip>
      </el-button-group>
      <el-divider direction="vertical" />
      <el-dropdown trigger="click" @command="handleMoreCommand">
        <el-button
          size="small"
          text
          data-testid="layout-more-button"
          :aria-label="t('common.actions.more', 'More')"
        >
          <el-icon><MoreFilled /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="translationMode" data-testid="layout-translation-mode-item">
              {{ translationMode ? '✓ ' : '' }}{{ t('system.pageLayout.designer.actions.translationMode', 'Trans Mode') }}
            </el-dropdown-item>
            <el-dropdown-item command="reset" divided data-testid="layout-reset-menu-item">
              {{ t('system.pageLayout.designer.actions.reset') }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-divider direction="vertical" />
      <el-button
        size="small"
        :disabled="previewMode === 'active'"
        data-testid="layout-save-button"
        plain
        @click="$emit('save')"
      >
        {{ t('system.pageLayout.designer.actions.saveDraft') }}
      </el-button>
      <el-button
        size="small"
        type="primary"
        :loading="publishing"
        :disabled="previewMode === 'active'"
        data-testid="layout-publish-button"
        @click="$emit('publish')"
      >
        {{ t('system.pageLayout.designer.actions.publish') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowLeft, RefreshLeft, RefreshRight, MoreFilled } from '@element-plus/icons-vue'

const props = defineProps<{
  layoutName: string
  modeLabel: string
  isDefault: boolean
  translationMode: boolean
  canUndo: boolean
  canRedo: boolean
  renderMode: 'design' | 'preview'
  previewLoading: boolean
  previewMode: 'current' | 'active'
  publishing: boolean
  viewMode: 'Detail' | 'Compact'
  viewport?: 'desktop' | 'mobile'
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'undo'): void
  (e: 'redo'): void
  (e: 'update:renderMode', value: string): void
  (e: 'reset'): void
  (e: 'save'): void
  (e: 'publish'): void
  (e: 'setPreviewMode', mode: 'current' | 'active'): void
  (e: 'update:translationMode', value: boolean): void
  (e: 'update:viewMode', value: string): void
  (e: 'update:viewport', value: string): void
}>()

function handleMoreCommand(command: string) {
  if (command === 'translationMode') {
    emit('update:translationMode', !props.translationMode)
  } else if (command === 'reset') {
    emit('reset')
  }
}

const { t } = useI18n()

const viewModeOptions = computed(() => [
  { label: t('system.pageLayout.viewMode.detail', 'Detail'), value: 'Detail' },
  { label: t('system.pageLayout.viewMode.compact', 'Compact'), value: 'Compact' }
])

const viewportOptions = computed(() => [
  { label: t('system.pageLayout.viewport.desktop', 'Desktop'), value: 'desktop' },
  { label: t('system.pageLayout.viewport.mobile', 'Mobile'), value: 'mobile' }
])

const renderModeOptions = computed(() => [
  { label: t('system.pageLayout.designer.status.designState', 'Design'), value: 'design' },
  { label: t('system.pageLayout.designer.status.previewState', 'Preview'), value: 'preview' }
])
</script>

<style scoped lang="scss">
.designer-toolbar {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) auto minmax(320px, 1fr);
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.98) 100%);
  border-bottom: 1px solid #dcdfe6;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
}

.toolbar-left,
.toolbar-center,
.toolbar-right {
  display: flex;
  align-items: center;
  min-width: 0;
  min-height: 52px;
  padding: 6px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
}

.toolbar-left {
  gap: 8px;
}

.toolbar-center {
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-right {
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

.layout-info {
  display: inline-block;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

@media (max-width: 1440px) {
  .designer-toolbar {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    justify-content: flex-start;
  }
}
</style>
