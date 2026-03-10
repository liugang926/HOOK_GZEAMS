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
      <span class="layout-info">{{ layoutName }} ({{ modeLabel }})</span>
      <el-tag
        v-if="!isDefault"
        type="warning"
        size="small"
      >
        {{ t('system.pageLayout.designer.badges.customLayout') }}
      </el-tag>
      <el-divider direction="vertical" />
      <el-segmented
        :model-value="viewMode"
        :options="viewModeOptions"
        size="small"
        data-testid="layout-view-mode-toggle"
        @update:model-value="$emit('update:viewMode', $event as string)"
      />
      <el-divider direction="vertical" />
      <el-segmented
        :model-value="viewport"
        :options="viewportOptions"
        size="small"
        data-testid="layout-viewport-toggle"
        @update:model-value="$emit('update:viewport', $event as string)"
      />
    </div>

    <div class="toolbar-center">
      <el-button-group>
        <el-button
          data-testid="layout-undo-button"
          :disabled="!canUndo"
          @click="$emit('undo')"
        >
          <el-icon><RefreshLeft /></el-icon>
          {{ t('system.pageLayout.designer.actions.undo') }}
        </el-button>
        <el-button
          data-testid="layout-redo-button"
          :disabled="!canRedo"
          @click="$emit('redo')"
        >
          <el-icon><RefreshRight /></el-icon>
          {{ t('system.pageLayout.designer.actions.redo') }}
        </el-button>
      </el-button-group>
    </div>

    <div class="toolbar-right">
      <el-switch
        :model-value="translationMode"
        :active-text="t('system.pageLayout.designer.actions.translationMode', 'Trans Mode')"
        inline-prompt
        style="margin-right: 12px"
        @update:model-value="$emit('update:translationMode', Boolean($event))"
      />
      <el-button
        data-testid="layout-reset-button"
        @click="$emit('reset')"
      >
        {{ t('system.pageLayout.designer.actions.reset') }}
      </el-button>
      <el-button-group>
        <el-button
          size="small"
          data-testid="layout-preview-current-button"
          :disabled="previewLoading"
          :type="previewMode === 'current' ? 'primary' : 'default'"
          @click="$emit('setPreviewMode', 'current')"
        >
          {{ t('system.pageLayout.designer.actions.custom') }}
        </el-button>
        <el-button
          size="small"
          data-testid="layout-preview-active-button"
          :loading="previewLoading && previewMode === 'active'"
          :disabled="previewLoading"
          :type="previewMode === 'active' ? 'primary' : 'default'"
          @click="$emit('setPreviewMode', 'active')"
        >
          {{ t('system.pageLayout.designer.actions.preview') }}
        </el-button>
      </el-button-group>
      <el-tag
        size="small"
        effect="plain"
      >
        {{ previewMode === 'active' ? t('system.pageLayout.designer.status.previewMode') : t('system.pageLayout.designer.status.customMode') }}
      </el-tag>
      <el-button
        :disabled="previewMode === 'active'"
        data-testid="layout-save-button"
        @click="$emit('save')"
      >
        {{ t('system.pageLayout.designer.actions.saveDraft') }}
      </el-button>
      <el-button
        type="success"
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
import { ArrowLeft, RefreshLeft, RefreshRight } from '@element-plus/icons-vue'

defineProps<{
  layoutName: string
  modeLabel: string
  isDefault: boolean
  translationMode: boolean
  canUndo: boolean
  canRedo: boolean
  previewLoading: boolean
  previewMode: 'current' | 'active'
  publishing: boolean
  viewMode: 'Detail' | 'Compact'
  viewport?: 'desktop' | 'mobile'
}>()

defineEmits<{
  (e: 'cancel'): void
  (e: 'undo'): void
  (e: 'redo'): void
  (e: 'reset'): void
  (e: 'save'): void
  (e: 'publish'): void
  (e: 'setPreviewMode', mode: 'current' | 'active'): void
  (e: 'update:translationMode', value: boolean): void
  (e: 'update:viewMode', value: string): void
  (e: 'update:viewport', value: string): void
}>()

const { t } = useI18n()

const viewModeOptions = computed(() => [
  { label: t('system.pageLayout.viewMode.detail', 'Detail'), value: 'Detail' },
  { label: t('system.pageLayout.viewMode.compact', 'Compact'), value: 'Compact' }
])

const viewportOptions = computed(() => [
  { label: t('system.pageLayout.viewport.desktop', 'Desktop'), value: 'desktop' },
  { label: t('system.pageLayout.viewport.mobile', 'Mobile'), value: 'mobile' }
])
</script>
