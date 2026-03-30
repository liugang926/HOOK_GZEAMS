<template>
  <section
    v-if="items.length > 0"
    class="sla-indicator-bar"
  >
    <header class="sla-indicator-bar__header">
      <div>
        <p class="sla-indicator-bar__eyebrow">
          {{ t('common.workbench.eyebrows.sla') }}
        </p>
        <h3 class="sla-indicator-bar__title">
          {{ t('common.workbench.titles.sla') }}
        </h3>
      </div>
      <p class="sla-indicator-bar__description">
        {{ t('common.workbench.messages.slaHint') }}
      </p>
    </header>

    <div class="sla-indicator-bar__list">
      <div
        v-for="item in items"
        :key="item.code"
        :class="['sla-indicator-bar__item', `sla-indicator-bar__item--${item.tone}`]"
      >
        <p class="sla-indicator-bar__label">
          {{ item.label }}
        </p>
        <strong class="sla-indicator-bar__status">
          {{ item.status }}
        </strong>
        <p
          v-if="item.meta"
          class="sla-indicator-bar__meta"
        >
          {{ item.meta }}
        </p>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ObjectSlaSummary, RuntimeWorkbenchSlaIndicator } from '@/types/runtime'
import {
  readWorkbenchRecordValue,
  resolveWorkbenchText,
} from './workbenchHelpers'

const props = withDefaults(defineProps<{
  indicators?: RuntimeWorkbenchSlaIndicator[]
  recordData?: Record<string, unknown> | null
  slaData?: ObjectSlaSummary | null
}>(), {
  indicators: () => [],
  recordData: null,
  slaData: null,
})

const { t, te } = useI18n()

const resolveSlaTone = (status: string) => {
  const normalized = status.trim().toLowerCase()
  if (['overdue', 'escalated'].includes(normalized)) {
    return 'danger'
  }
  if (normalized === 'approaching_sla') {
    return 'warning'
  }
  if (['completed', 'within_sla'].includes(normalized)) {
    return 'success'
  }
  return 'neutral'
}

const resolveSlaStatusText = (status: unknown) => {
  const normalized = String(status || '').trim().toLowerCase()
  if (!normalized) {
    return t('common.workbench.status.unknown')
  }

  const translationKey = `common.workbench.status.${normalized}`
  if (te(translationKey)) {
    return t(translationKey)
  }

  return normalized
}

const items = computed(() => {
  return props.indicators.map((indicator) => {
    const hasWorkflowInstance = Boolean(props.slaData?.hasInstance)
    const status = indicator.status ??
      readWorkbenchRecordValue(props.recordData, indicator.statusField || indicator.status_field) ??
      (hasWorkflowInstance ? props.slaData?.status : null)
    const dueDate = indicator.dueDate ??
      readWorkbenchRecordValue(props.recordData, indicator.dueDateField || indicator.due_date_field) ??
      (hasWorkflowInstance ? props.slaData?.dueDate : null)
    const assignee = readWorkbenchRecordValue(
      props.recordData,
      indicator.assigneeField || indicator.assignee_field,
    ) ?? (hasWorkflowInstance ? props.slaData?.assignee?.displayName : null)
    if (!status && !hasWorkflowInstance) {
      return null
    }

    const metaParts = [
      dueDate ? `${t('common.workbench.labels.dueDate')}: ${String(dueDate)}` : '',
      assignee ? `${t('common.workbench.labels.owner')}: ${String(assignee)}` : '',
    ].filter(Boolean)

    return {
      code: indicator.code,
      label: resolveWorkbenchText(
        indicator,
        t,
        te,
        ['labelKey', 'label_key', 'titleKey', 'title_key'],
        ['label', 'title', 'code'],
      ) || indicator.code,
      status: resolveSlaStatusText(status),
      meta: metaParts.join(' · '),
      tone: resolveSlaTone(String(status || '')),
    }
  }).filter((item): item is {
    code: string
    label: string
    status: string
    meta: string
    tone: string
  } => Boolean(item))
})
</script>

<style scoped lang="scss">
@use '@/styles/object-workspace.scss' as workspace;

.sla-indicator-bar {
  @include workspace.workspace-panel();
  padding: 24px;
}

.sla-indicator-bar__header {
  @include workspace.workspace-panel-header();
}

.sla-indicator-bar__eyebrow {
  @include workspace.panel-kicker();
}

.sla-indicator-bar__title {
  @include workspace.panel-title();
}

.sla-indicator-bar__description {
  @include workspace.panel-text(360px);
}

.sla-indicator-bar__list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
}

.sla-indicator-bar__item {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.14);

  &--warning {
    background: linear-gradient(180deg, rgba(255, 251, 235, 0.96), rgba(255, 255, 255, 0.96));
  }

  &--danger {
    background: linear-gradient(180deg, rgba(254, 242, 242, 0.96), rgba(255, 255, 255, 0.96));
  }

  &--success {
    background: linear-gradient(180deg, rgba(236, 253, 245, 0.96), rgba(255, 255, 255, 0.96));
  }
}

.sla-indicator-bar__label {
  margin: 0;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(71, 85, 105, 0.88);
}

.sla-indicator-bar__status {
  display: block;
  margin-top: 10px;
  font-size: 20px;
  line-height: 1.3;
  color: rgba(15, 23, 42, 0.96);
}

.sla-indicator-bar__meta {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(71, 85, 105, 0.92);
}
</style>
