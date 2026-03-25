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

    <div
      v-if="document"
      class="document-workbench__summary"
    >
      <el-card
        v-if="workflowProgress"
        class="document-workbench__progress-card"
        shadow="never"
      >
        <p class="document-workbench__activity-eyebrow">
          {{ t('common.documentWorkbench.sections.workflowProgress') }}
        </p>
        <DocumentWorkflowProgress
          :current-status="workflowProgress.currentStatus"
          :steps="workflowProgress.steps"
        />
      </el-card>

      <ObjectWorkspaceInfoCard
        v-if="stageRows.length > 0"
        :variant="cardVariant"
        :eyebrow="t('common.documentWorkbench.sections.stageInsights')"
        :title="document.context.recordLabel || objectCode"
        :rows="stageRows"
      />

      <ObjectWorkspaceInfoCard
        :variant="cardVariant"
        :eyebrow="t('common.documentWorkbench.sections.record')"
        :title="document.context.recordLabel || objectCode"
        :rows="recordRows"
      />

      <ObjectWorkspaceInfoCard
        :variant="cardVariant"
        :eyebrow="t('common.documentWorkbench.sections.workflow')"
        :title="workflowTitle"
        :rows="workflowRows"
      />

      <ObjectWorkspaceInfoCard
        :variant="cardVariant"
        :eyebrow="t('common.documentWorkbench.sections.audit')"
        :title="t('common.detailPage.auditInfo')"
        :rows="auditRows"
      />

      <ClosedLoopNavigationCard
        v-if="navigationSection"
        class="document-workbench__navigation-card"
        :title="navigationSection.title"
        :hint="navigationSection.hint"
        :items="navigationSection.items"
        @select="handleNavigationSelect"
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
          </li>
        </ul>
      </el-card>

      <el-card
        v-if="disposalBatchActions.length > 0"
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
    </div>

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
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import ActivityTimeline from '@/components/common/ActivityTimeline.vue'
import ClosedLoopNavigationCard from '@/components/common/ClosedLoopNavigationCard.vue'
import DocumentWorkflowProgress from '@/components/common/DocumentWorkflowProgress.vue'
import ObjectActionBar from '@/components/common/ObjectActionBar.vue'
import StatusActionBar, { type StatusAction } from '@/components/common/StatusActionBar.vue'
import ObjectWorkspaceInfoCard from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import type {
  AggregateDocumentPageMode,
  AggregateDocumentResponse,
} from '@/types/runtime'
import { useClosedLoopNavigation } from '@/composables/useClosedLoopNavigation'
import type { ObjectActionExecutionResult } from '@/api/dynamic'
import { useDocumentWorkbenchBatchActions } from '@/components/common/useDocumentWorkbenchBatchActions'
import { useDocumentWorkbenchState } from '@/components/common/useDocumentWorkbenchState'

interface Props {
  objectCode: string
  recordId?: string
  mode: AggregateDocumentPageMode
  modelValue: Record<string, any>
  document?: AggregateDocumentResponse | null
  readonly?: boolean
  statusActions?: StatusAction[]
  showObjectActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  recordId: '',
  document: null,
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
  recordRows,
  recordStatusLabel,
  showHeaderShell,
  stageRows,
  timelineEntries,
  workflowActivityItems,
  workflowProgress,
  workflowRows,
  workflowStatusLabel,
  workflowTitle,
} = useDocumentWorkbenchState({
  props,
  t: t as (key: string, params?: Record<string, unknown>) => string,
  locale,
})

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

.document-workbench__progress-card {
  grid-column: 1 / -1;
  border: 1px solid var(--el-border-color-lighter);
}

.document-workbench__activity-card {
  border: 1px solid var(--el-border-color-lighter);
}

.document-workbench__navigation-card,
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
}
</style>
