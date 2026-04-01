<template>
  <section
    class="designer-workbench-metadata"
    data-testid="layout-workbench-metadata"
  >
    <div class="designer-workbench-metadata__header">
      <div>
        <div class="designer-workbench-metadata__title">
          {{ t('system.pageLayout.designer.workbench.title') }}
        </div>
        <p class="designer-workbench-metadata__description">
          {{ t('system.pageLayout.designer.workbench.description') }}
        </p>
      </div>
      <el-button
        text
        size="small"
        data-testid="layout-workbench-metadata-reset"
        @click="handleReset"
      >
        {{ t('system.pageLayout.designer.workbench.actions.reset') }}
      </el-button>
    </div>

    <div class="designer-workbench-metadata__settings">
      <div class="designer-workbench-metadata__setting">
        <span class="designer-workbench-metadata__setting-label">
          {{ t('system.pageLayout.designer.workbench.fields.defaultPageMode') }}
        </span>
        <el-select
          :model-value="normalizedMetadata.defaultPageMode"
          size="small"
          data-testid="layout-workbench-default-page-mode"
          @update:model-value="handlePageModeChange"
        >
          <el-option
            v-for="option in pageModeOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </div>

      <div class="designer-workbench-metadata__setting">
        <span class="designer-workbench-metadata__setting-label">
          {{ t('system.pageLayout.designer.workbench.fields.defaultDocumentSurfaceTab') }}
        </span>
        <el-select
          :model-value="normalizedMetadata.defaultDocumentSurfaceTab"
          size="small"
          data-testid="layout-workbench-default-document-surface-tab"
          @update:model-value="handleDocumentSurfaceTabChange"
        >
          <el-option
            v-for="option in documentSurfaceTabOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </div>
    </div>

    <div class="designer-workbench-metadata__section-title">
      {{ t('system.pageLayout.designer.workbench.fields.documentSummarySections') }}
    </div>

    <div class="designer-workbench-metadata__rows">
      <div
        v-for="(section, index) in normalizedMetadata.documentSummarySections"
        :key="section.code"
        class="designer-workbench-metadata__row"
      >
        <div class="designer-workbench-metadata__summary">
          <span class="designer-workbench-metadata__label">
            {{ resolveSectionLabel(section.code) }}
          </span>
          <span class="designer-workbench-metadata__order">
            {{ t('system.pageLayout.designer.workbench.labels.order', { index: index + 1 }) }}
          </span>
        </div>

        <div class="designer-workbench-metadata__controls">
          <el-select
            :model-value="section.surfacePriority"
            size="small"
            class="designer-workbench-metadata__priority"
            :data-testid="`layout-workbench-priority-${section.code}`"
            @update:model-value="handlePriorityChange(section.code, $event)"
          >
            <el-option
              v-for="option in priorityOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-button
            text
            size="small"
            :disabled="index === 0"
            :data-testid="`layout-workbench-move-up-${section.code}`"
            :aria-label="t('system.pageLayout.designer.workbench.actions.moveUp')"
            @click="moveSection(section.code, -1)"
          >
            <el-icon><ArrowUp /></el-icon>
          </el-button>
          <el-button
            text
            size="small"
            :disabled="index === normalizedMetadata.documentSummarySections.length - 1"
            :data-testid="`layout-workbench-move-down-${section.code}`"
            :aria-label="t('system.pageLayout.designer.workbench.actions.moveDown')"
            @click="moveSection(section.code, 1)"
          >
            <el-icon><ArrowDown /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import {
  DESIGNER_DEFAULT_WORKBENCH_METADATA,
  DESIGNER_DOCUMENT_SURFACE_TABS,
  DESIGNER_WORKBENCH_PAGE_MODES,
  DESIGNER_WORKBENCH_SURFACE_PRIORITIES,
  normalizeDesignerDocumentSurfaceTab,
  normalizeDesignerPageMode,
  normalizeDesignerSurfacePriority,
  normalizeDesignerWorkbenchMetadata,
  type DesignerWorkbenchMetadataConfig,
} from '@/components/designer/designerWorkbenchMetadata'

const props = defineProps<{
  metadata?: DesignerWorkbenchMetadataConfig
}>()

const emit = defineEmits<{
  (e: 'update:metadata', value: DesignerWorkbenchMetadataConfig): void
}>()

const { t } = useI18n()

const normalizedMetadata = computed(() => normalizeDesignerWorkbenchMetadata(props.metadata))

const pageModeOptions = computed(() =>
  DESIGNER_WORKBENCH_PAGE_MODES.map((value) => ({
    value,
    label: t(`system.pageLayout.designer.workbench.pageModes.${value}`),
  })),
)

const documentSurfaceTabOptions = computed(() =>
  DESIGNER_DOCUMENT_SURFACE_TABS.map((value) => ({
    value,
    label: t(`system.pageLayout.designer.workbench.documentSurfaceTabs.${value}`),
  })),
)

const priorityOptions = computed(() =>
  DESIGNER_WORKBENCH_SURFACE_PRIORITIES.map((value) => ({
    value,
    label: t(`system.pageLayout.designer.workbench.priorities.${value}`),
  })),
)

const emitMetadata = (value: DesignerWorkbenchMetadataConfig) => {
  emit('update:metadata', normalizeDesignerWorkbenchMetadata(value))
}

const resolveSectionLabel = (code: string) => {
  return t(`system.pageLayout.designer.workbench.sections.${code}`)
}

const handlePageModeChange = (rawValue: unknown) => {
  emitMetadata({
    ...normalizedMetadata.value,
    defaultPageMode: normalizeDesignerPageMode(rawValue),
  })
}

const handleDocumentSurfaceTabChange = (rawValue: unknown) => {
  emitMetadata({
    ...normalizedMetadata.value,
    defaultDocumentSurfaceTab: normalizeDesignerDocumentSurfaceTab(rawValue),
  })
}

const handlePriorityChange = (code: string, rawValue: unknown) => {
  const nextSections = normalizedMetadata.value.documentSummarySections.map((section) => (
    section.code === code
      ? {
          ...section,
          surfacePriority: normalizeDesignerSurfacePriority(rawValue),
        }
      : { ...section }
  ))

  emitMetadata({
    ...normalizedMetadata.value,
    documentSummarySections: nextSections,
  })
}

const moveSection = (code: string, offset: -1 | 1) => {
  const nextSections = normalizedMetadata.value.documentSummarySections.map((section) => ({ ...section }))
  const index = nextSections.findIndex((section) => section.code === code)
  const targetIndex = index + offset
  if (index < 0 || targetIndex < 0 || targetIndex >= nextSections.length) {
    return
  }

  const [item] = nextSections.splice(index, 1)
  nextSections.splice(targetIndex, 0, item)
  emitMetadata({
    ...normalizedMetadata.value,
    documentSummarySections: nextSections,
  })
}

const handleReset = () => {
  emitMetadata(DESIGNER_DEFAULT_WORKBENCH_METADATA)
}
</script>

<style scoped lang="scss">
.designer-workbench-metadata {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
}

.designer-workbench-metadata__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.designer-workbench-metadata__title {
  font-size: 13px;
  font-weight: 700;
  color: #1f2937;
}

.designer-workbench-metadata__description {
  margin: 4px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: #6b7280;
}

.designer-workbench-metadata__settings {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.designer-workbench-metadata__setting {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.designer-workbench-metadata__setting-label,
.designer-workbench-metadata__section-title {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}

.designer-workbench-metadata__rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.designer-workbench-metadata__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.designer-workbench-metadata__summary {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.designer-workbench-metadata__label {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.designer-workbench-metadata__order {
  font-size: 12px;
  color: #64748b;
}

.designer-workbench-metadata__controls {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.designer-workbench-metadata__priority {
  width: 128px;
}
</style>
