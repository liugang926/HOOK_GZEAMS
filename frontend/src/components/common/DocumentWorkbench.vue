<template>
  <div class="document-workbench">
    <el-card
      v-if="document && showHeaderShell"
      class="document-workbench__header"
      shadow="never"
    >
      <div class="document-workbench__header-main">
        <div class="document-workbench__header-copy">
          <p class="document-workbench__eyebrow">
            {{ t('common.documentWorkbench.sections.actions') }}
          </p>
          <h3 class="document-workbench__title">
            {{ document.context.recordLabel || objectCode }}
          </h3>
          <div class="document-workbench__chips">
            <el-tag size="small">
              {{ modeLabel }}
            </el-tag>
            <el-tag
              size="small"
              type="info"
            >
              {{ `${t('common.documentWorkbench.labels.status')}: ${recordStatusLabel}` }}
            </el-tag>
            <el-tag
              v-if="workflowStatusLabel !== '-'"
              size="small"
              type="warning"
            >
              {{ `${t('common.documentWorkbench.labels.workflowStatus')}: ${workflowStatusLabel}` }}
            </el-tag>
          </div>
        </div>

        <div class="document-workbench__header-actions">
          <StatusActionBar
            v-if="statusActions.length > 0"
            :status="recordStatusLabel"
            :actions="statusActions"
            @action-success="handleStatusActionSuccess"
            @action-error="handleStatusActionError"
          />
          <ObjectActionBar
            v-if="showObjectActions && effectiveRecordId"
            :object-code="objectCode"
            :record-id="effectiveRecordId"
            @action-success="handleObjectActionSuccess"
            @action-error="handleObjectActionError"
          />
        </div>
      </div>

      <div
        v-if="capabilityItems.length > 0"
        class="document-workbench__capabilities"
      >
        <span class="document-workbench__capabilities-label">
          {{ t('common.documentWorkbench.labels.capabilities') }}
        </span>
        <div class="document-workbench__capability-tags">
          <el-tag
            v-for="capability in capabilityItems"
            :key="capability.key"
            size="small"
            :type="capability.active ? 'success' : 'info'"
            effect="plain"
          >
            {{ capability.label }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <el-tabs
      v-model="activeSurfaceTab"
      class="document-workbench__surface-tabs"
    >
      <el-tab-pane
        v-if="hasSummarySurface"
        :label="t('common.documentWorkbench.tabs.summary')"
        name="summary"
      >
        <div class="document-workbench__surface-stack">
          <div
            v-if="document"
            class="document-workbench__summary"
          >
            <template
              v-for="section in primaryDocumentSummarySections"
              :key="`primary-${section.code}`"
            >
              <ProcessSummaryPanel
                v-if="section.code === 'process_summary'"
                class="document-workbench__process-summary"
                :stats="processSummaryStats"
                :panel="null"
                :record-data="null"
                :extra-rows="processSummaryRows"
                :navigation-section="navigationSection"
                @select="handleNavigationSelect"
              />

              <ObjectWorkspaceInfoCard
                v-else-if="section.code === 'record'"
                :variant="cardVariant"
                :eyebrow="t('common.documentWorkbench.sections.record')"
                :title="document.context.recordLabel || objectCode"
                :rows="recordRows"
              />

              <ObjectWorkspaceInfoCard
                v-else-if="section.code === 'workflow'"
                :variant="cardVariant"
                :eyebrow="t('common.documentWorkbench.sections.workflow')"
                :title="workflowTitle"
                :rows="workflowRows"
              />

              <el-card
                v-else-if="section.code === 'batch_tools'"
                class="document-workbench__batch-card"
                shadow="never"
              >
                <p class="document-workbench__activity-eyebrow">
                  {{ t('common.documentWorkbench.sections.batchTools') }}
                </p>
                <p class="document-workbench__batch-hint">
                  {{ t('common.documentWorkbench.batchTools.hint') }}
                </p>
                <div class="document-workbench__batch-actions">
                  <el-button
                    v-for="action in disposalBatchActions"
                    :key="action.key"
                    :type="action.type"
                    :disabled="action.count <= 0"
                    @click="handleDisposalBatchAction(action.key)"
                  >
                    {{ `${action.label} (${action.count})` }}
                  </el-button>
                </div>
              </el-card>
            </template>

            <el-collapse
              v-if="secondaryDocumentSummarySections.length > 0"
              v-model="expandedSummarySections"
              class="document-workbench__secondary-summary"
            >
              <el-collapse-item
                name="secondary-summary"
                :title="t('common.documentWorkbench.sections.moreSummary')"
              >
                <div class="document-workbench__secondary-summary-stack">
                  <template
                    v-for="section in secondaryDocumentSummarySections"
                    :key="`secondary-${section.code}`"
                  >
                    <ObjectWorkspaceInfoCard
                      v-if="section.code === 'record'"
                      :variant="cardVariant"
                      :eyebrow="t('common.documentWorkbench.sections.record')"
                      :title="document.context.recordLabel || objectCode"
                      :rows="recordRows"
                    />

                    <ObjectWorkspaceInfoCard
                      v-else-if="section.code === 'workflow'"
                      :variant="cardVariant"
                      :eyebrow="t('common.documentWorkbench.sections.workflow')"
                      :title="workflowTitle"
                      :rows="workflowRows"
                    />

                    <el-card
                      v-else-if="section.code === 'batch_tools'"
                      class="document-workbench__batch-card"
                      shadow="never"
                    >
                      <p class="document-workbench__activity-eyebrow">
                        {{ t('common.documentWorkbench.sections.batchTools') }}
                      </p>
                      <p class="document-workbench__batch-hint">
                        {{ t('common.documentWorkbench.batchTools.hint') }}
                      </p>
                      <div class="document-workbench__batch-actions">
                        <el-button
                          v-for="action in disposalBatchActions"
                          :key="action.key"
                          :type="action.type"
                          :disabled="action.count <= 0"
                          @click="handleDisposalBatchAction(action.key)"
                        >
                          {{ `${action.label} (${action.count})` }}
                        </el-button>
                      </div>
                    </el-card>
                  </template>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane
        :label="t('common.documentWorkbench.tabs.form')"
        name="form"
      >
        <div class="document-workbench__surface-stack">
          <div class="document-workbench__form">
            <DynamicForm
              ref="dynamicFormRef"
              :business-object="objectCode"
              layout-code="form"
              :model-value="modelValue"
              :readonly="effectiveReadonly"
              :field-permissions="fieldPermissions"
              :show-actions="false"
              :instance-id="effectiveRecordId || null"
              label-position="top"
              label-width="auto"
              @update:model-value="emit('update:modelValue', $event)"
              @request-save="emit('request-save')"
            />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane
        v-if="hasActivitySurface"
        :label="t('common.documentWorkbench.tabs.activity')"
        name="activity"
      >
        <div
          id="document-workbench-timeline"
          class="document-workbench__activity-stack"
        >
          <ObjectWorkspaceInfoCard
            v-if="auditRows.length > 0"
            :variant="cardVariant"
            :eyebrow="t('common.documentWorkbench.sections.audit')"
            :title="t('common.detailPage.auditInfo')"
            :rows="auditRows"
          />

          <el-card
            v-if="workflowActivityItems.length > 0"
            class="document-workbench__activity-card"
            shadow="never"
          >
            <p class="document-workbench__activity-eyebrow">
              {{ t('common.documentWorkbench.sections.workflowActivity') }}
            </p>
            <ul class="document-workbench__activity-list">
              <li
                v-for="item in workflowActivityItems"
                :key="item.id"
                class="document-workbench__activity-item"
              >
                <div class="document-workbench__activity-head">
                  <strong>{{ item.title }}</strong>
                  <span>{{ item.createdAt }}</span>
                </div>
                <p class="document-workbench__activity-meta">
                  {{ item.meta }}
                </p>
                <p
                  v-if="item.description"
                  class="document-workbench__activity-description"
                >
                  {{ item.description }}
                </p>
                <div
                  v-if="item.highlights && item.highlights.length > 0"
                  class="document-workbench__activity-highlights"
                >
                  <span
                    v-for="highlight in item.highlights"
                    :key="`${item.id}-${highlight.code}-${highlight.value}`"
                    class="document-workbench__activity-highlight"
                  >
                    <span class="document-workbench__activity-highlight-label">
                      {{ highlight.label || highlight.code }}
                    </span>
                    <span class="document-workbench__activity-highlight-value">
                      {{ highlight.value }}
                    </span>
                  </span>
                </div>
              </li>
            </ul>
          </el-card>

          <el-card
            v-if="timelineEntries.length > 0"
            class="document-workbench__timeline"
            shadow="never"
          >
            <ActivityTimeline
              :object-code="objectCode"
              :record-id="effectiveRecordId"
              :entries="timelineEntries"
            />
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import ActivityTimeline from '@/components/common/ActivityTimeline.vue'
import ObjectActionBar from '@/components/common/ObjectActionBar.vue'
import ProcessSummaryPanel from '@/components/common/ProcessSummaryPanel.vue'
import StatusActionBar, { type StatusAction } from '@/components/common/StatusActionBar.vue'
import ObjectWorkspaceInfoCard from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import type {
  AggregateDocumentPageMode,
  AggregateDocumentResponse,
  RuntimeWorkbench,
  RuntimeWorkbenchDocumentSummarySection,
  RuntimeWorkbenchSurfacePriority,
} from '@/types/runtime'
import { useClosedLoopNavigation } from '@/composables/useClosedLoopNavigation'
import type { ObjectActionExecutionResult } from '@/api/dynamic'
import { useDocumentWorkbenchBatchActions } from '@/components/common/useDocumentWorkbenchBatchActions'
import { useDocumentWorkbenchState } from '@/components/common/useDocumentWorkbenchState'
import { DOCUMENT_WORKBENCH_TIMELINE_ANCHOR } from '@/components/common/documentWorkbenchViewModel'

interface Props {
  objectCode: string
  recordId?: string
  mode: AggregateDocumentPageMode
  modelValue: Record<string, any>
  document?: AggregateDocumentResponse | null
  workbench?: RuntimeWorkbench | null
  readonly?: boolean
  statusActions?: StatusAction[]
  showObjectActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  recordId: '',
  document: null,
  workbench: null,
  readonly: false,
  statusActions: () => [],
  showObjectActions: true,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'request-save'): void
  (e: 'action-success', actionCode: string, result: unknown): void
  (e: 'action-error', actionCode: string, error: unknown): void
}>()

const { t, locale } = useI18n()
const { handleClosedLoopNavigation } = useClosedLoopNavigation()
const dynamicFormRef = ref<InstanceType<typeof DynamicForm> | null>(null)
const activeSurfaceTab = ref('')
const expandedSummarySections = ref<string[]>([])

type DocumentSummarySectionCode = 'process_summary' | 'record' | 'workflow' | 'batch_tools'
type DocumentSummarySectionDefinition = RuntimeWorkbenchDocumentSummarySection & {
  code: DocumentSummarySectionCode
  surfacePriority: RuntimeWorkbenchSurfacePriority
}

const DOCUMENT_SUMMARY_PRIMARY_PRIORITIES: RuntimeWorkbenchSurfacePriority[] = ['primary', 'context']
const DEFAULT_DOCUMENT_SUMMARY_SECTIONS: DocumentSummarySectionDefinition[] = [
  { code: 'process_summary', surfacePriority: 'primary' },
  { code: 'record', surfacePriority: 'context' },
  { code: 'workflow', surfacePriority: 'context' },
  { code: 'batch_tools', surfacePriority: 'admin' },
]

const isDocumentSummarySectionCode = (value: unknown): value is DocumentSummarySectionCode => {
  return ['process_summary', 'record', 'workflow', 'batch_tools'].includes(String(value || '').trim())
}

const normalizeDocumentSummarySectionPriority = (value: unknown): RuntimeWorkbenchSurfacePriority => {
  if (['primary', 'context', 'related', 'activity', 'admin'].includes(String(value || '').trim())) {
    return String(value || '').trim() as RuntimeWorkbenchSurfacePriority
  }
  return 'context'
}

const normalizeDocumentSummarySections = (
  value: unknown,
): DocumentSummarySectionDefinition[] => {
  const sections = Array.isArray(value) ? value : []
  const result: DocumentSummarySectionDefinition[] = []
  const seen = new Set<DocumentSummarySectionCode>()
  const defaultsByCode = new Map(
    DEFAULT_DOCUMENT_SUMMARY_SECTIONS.map((section) => [section.code, section]),
  )

  for (const item of sections) {
    if (!item || typeof item !== 'object') {
      continue
    }
    const candidate = item as Record<string, unknown>
    const code = String(candidate.code || '').trim()
    if (!isDocumentSummarySectionCode(code) || seen.has(code)) {
      continue
    }
    const fallback = defaultsByCode.get(code)
    result.push({
      ...(fallback || { code, surfacePriority: 'context' }),
      ...candidate,
      code,
      surfacePriority: normalizeDocumentSummarySectionPriority(
        candidate.surfacePriority ?? candidate.surface_priority ?? fallback?.surfacePriority,
      ),
    })
    seen.add(code)
  }

  for (const section of DEFAULT_DOCUMENT_SUMMARY_SECTIONS) {
    if (seen.has(section.code)) {
      continue
    }
    result.push({ ...section })
  }

  return result
}
const {
  auditRows,
  capabilityItems,
  cardVariant,
  disposalBatchActions,
  effectiveReadonly,
  effectiveRecordId,
  fieldPermissions,
  modeLabel,
  navigationSection,
  processSummaryRows,
  processSummaryStats,
  recordRows,
  recordStatusLabel,
  showHeaderShell,
  timelineEntries,
  workflowActivityItems,
  workflowRows,
  workflowStatusLabel,
  workflowTitle,
} = useDocumentWorkbenchState({
  props,
  t: t as (key: string, params?: Record<string, unknown>) => string,
  locale,
})

const documentSummarySections = computed(() => normalizeDocumentSummarySections(
  props.workbench?.documentSummarySections,
))

const hasSummarySectionContent = (code: DocumentSummarySectionCode) => {
  switch (code) {
    case 'process_summary':
      return showProcessSummaryPanel.value
    case 'record':
      return recordRows.value.length > 0
    case 'workflow':
      return workflowRows.value.length > 0
    case 'batch_tools':
      return disposalBatchActions.value.length > 0
    default:
      return false
  }
}

const visibleDocumentSummarySections = computed(() => {
  return documentSummarySections.value.filter((section) => hasSummarySectionContent(section.code))
})

const primaryDocumentSummarySections = computed(() => {
  return visibleDocumentSummarySections.value.filter((section) =>
    DOCUMENT_SUMMARY_PRIMARY_PRIORITIES.includes(section.surfacePriority),
  )
})

const secondaryDocumentSummarySections = computed(() => {
  return visibleDocumentSummarySections.value.filter((section) =>
    !DOCUMENT_SUMMARY_PRIMARY_PRIORITIES.includes(section.surfacePriority),
  )
})

const showProcessSummaryPanel = computed(() => {
  return (
    processSummaryStats.value.length > 0 ||
    processSummaryRows.value.length > 0 ||
    Boolean(navigationSection.value)
  )
})

const hasSummarySurface = computed(() => {
  return (
    visibleDocumentSummarySections.value.length > 0
  )
})
const hasActivitySurface = computed(() => {
  return (
    auditRows.value.length > 0 ||
    workflowActivityItems.value.length > 0 ||
    timelineEntries.value.length > 0
  )
})

const configuredDocumentSurfaceTab = computed(() => {
  const candidate = props.workbench?.defaultDocumentSurfaceTab
  if (candidate === 'activity' || candidate === 'form' || candidate === 'summary') {
    return candidate
  }
  return null
})

const resolveDefaultSurfaceTab = () => {
  const preferredTab = configuredDocumentSurfaceTab.value
  if (preferredTab) {
    if (preferredTab === 'activity' && hasActivitySurface.value) {
      return 'activity'
    }
    if (preferredTab === 'form') {
      return 'form'
    }
    if (preferredTab === 'summary' && hasSummarySurface.value) {
      return 'summary'
    }
  }
  if (!effectiveReadonly.value) {
    return 'form'
  }
  if (hasSummarySurface.value) {
    return 'summary'
  }
  return 'form'
}

const syncDocumentSurfaceTab = () => {
  const availableTabs = [
    ...(hasSummarySurface.value ? ['summary'] : []),
    'form',
    ...(hasActivitySurface.value ? ['activity'] : []),
  ]

  if (availableTabs.length === 0) {
    return
  }

  const currentHash = typeof window !== 'undefined' ? window.location.hash : ''
  if (currentHash === DOCUMENT_WORKBENCH_TIMELINE_ANCHOR && hasActivitySurface.value) {
    activeSurfaceTab.value = 'activity'
    return
  }

  if (!availableTabs.includes(activeSurfaceTab.value)) {
    const defaultTab = resolveDefaultSurfaceTab()
    activeSurfaceTab.value = availableTabs.includes(defaultTab) ? defaultTab : availableTabs[0] || 'form'
  }
}

const handleNavigationSelect = (item: Parameters<typeof handleClosedLoopNavigation>[0]) => {
  handleClosedLoopNavigation(item)
}

const { handleDisposalBatchAction } = useDocumentWorkbenchBatchActions({
  getDocument: () => props.document,
  getModelValue: () => props.modelValue,
  emitModelValue: (value) => emit('update:modelValue', value),
  t: t as (key: string, params?: Record<string, unknown>) => string,
})

const handleStatusActionSuccess = (actionCode: string, result: unknown) => {
  emit('action-success', actionCode, result)
}

const handleStatusActionError = (actionCode: string, error: unknown) => {
  emit('action-error', actionCode, error)
}

const handleObjectActionSuccess = (actionCode: string, result: ObjectActionExecutionResult) => {
  emit('action-success', actionCode, result)
}

const handleObjectActionError = (actionCode: string, error: unknown) => {
  emit('action-error', actionCode, error)
}

watch(
  () => [
    effectiveReadonly.value,
    hasSummarySurface.value,
    hasActivitySurface.value,
    effectiveRecordId.value,
  ],
  () => {
    syncDocumentSurfaceTab()
  },
  { immediate: true },
)

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('hashchange', syncDocumentSurfaceTab)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('hashchange', syncDocumentSurfaceTab)
  }
})

defineExpose({
  dynamicFormRef,
  validate: () => dynamicFormRef.value?.validate?.(),
  getSubmitData: () => dynamicFormRef.value?.getSubmitData?.(),
})
</script>

<style scoped lang="scss">
.document-workbench {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.document-workbench__surface-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 16px;
  }
}

.document-workbench__header {
  border: 1px solid var(--el-border-color-lighter);
}

.document-workbench__header-main {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.document-workbench__header-copy {
  min-width: 0;
}

.document-workbench__eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.document-workbench__title {
  margin: 0;
  font-size: 20px;
  line-height: 1.3;
  color: var(--el-text-color-primary);
}

.document-workbench__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.document-workbench__header-actions {
  min-width: min(100%, 420px);
}

.document-workbench__capabilities {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.document-workbench__capabilities-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.document-workbench__capability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.document-workbench__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.document-workbench__surface-stack,
.document-workbench__activity-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.document-workbench__process-summary,
.document-workbench__secondary-summary {
  grid-column: 1 / -1;
}

.document-workbench__secondary-summary-stack {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  padding-top: 8px;
}

.document-workbench__activity-card {
  border: 1px solid var(--el-border-color-lighter);
}

.document-workbench__batch-card {
  border: 1px solid var(--el-border-color-lighter);
}

.document-workbench__batch-card {
  grid-column: 1 / -1;
}

.document-workbench__activity-eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.document-workbench__activity-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-workbench__activity-item + .document-workbench__activity-item {
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.document-workbench__activity-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 6px;
}

.document-workbench__activity-head strong {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.document-workbench__activity-head span {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.document-workbench__activity-meta,
.document-workbench__activity-description {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.document-workbench__activity-description {
  margin-top: 4px;
  color: var(--el-text-color-secondary);
}

.document-workbench__activity-highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.document-workbench__activity-highlight {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.document-workbench__activity-highlight-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.document-workbench__activity-highlight-value {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-primary);
  font-size: 12px;
  font-weight: 500;
}

.document-workbench__batch-hint {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}

.document-workbench__batch-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.document-workbench__form,
.document-workbench__timeline {
  min-width: 0;
}

@media (max-width: 1280px) {
  .document-workbench__header-main {
    flex-direction: column;
  }

  .document-workbench__header-actions {
    width: 100%;
    min-width: 0;
  }

  .document-workbench__summary {
    grid-template-columns: 1fr;
  }

  .document-workbench__secondary-summary-stack {
    grid-template-columns: 1fr;
  }
}
</style>
