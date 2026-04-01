<template>
  <el-card
    v-if="hasContent"
    class="process-summary-panel"
    shadow="never"
  >
    <div class="process-summary-panel__header">
      <div class="process-summary-panel__copy">
        <p class="process-summary-panel__eyebrow">
          {{ eyebrow }}
        </p>
        <h3 class="process-summary-panel__title">
          {{ title }}
        </h3>
      </div>
      <p
        v-if="hint"
        class="process-summary-panel__hint"
      >
        {{ hint }}
      </p>
    </div>

    <div
      v-if="stats.length > 0"
      class="process-summary-panel__stats"
    >
      <article
        v-for="stat in stats"
        :key="stat.label"
        class="process-summary-panel__stat"
      >
        <span class="process-summary-panel__stat-label">{{ stat.label }}</span>
        <strong
          class="process-summary-panel__stat-value"
          :title="stat.tooltip || undefined"
        >
          {{ stat.value }}
        </strong>
        <span
          v-if="stat.meta"
          class="process-summary-panel__stat-meta"
        >
          {{ stat.meta }}
        </span>
        <span
          v-if="stat.actions && stat.actions.length > 0"
          class="process-summary-panel__stat-actions"
        >
          <RouterLink
            v-for="action in stat.actions"
            :key="`${stat.label}-${action.label}`"
            :to="action.to"
            class="process-summary-panel__stat-action"
          >
            {{ action.label }}
          </RouterLink>
        </span>
      </article>
    </div>

    <dl
      v-if="rows.length > 0"
      class="process-summary-panel__rows"
    >
      <div
        v-for="row in rows"
        :key="row.label"
        class="process-summary-panel__row"
      >
        <dt>{{ row.label }}</dt>
        <dd>
          <span
            class="process-summary-panel__row-value"
            :title="row.tooltip || undefined"
          >
            {{ row.value }}
          </span>
          <span
            v-if="row.meta"
            class="process-summary-panel__row-meta"
          >
            {{ row.meta }}
          </span>
          <span
            v-if="row.actions && row.actions.length > 0"
            class="process-summary-panel__row-actions"
          >
            <RouterLink
              v-for="action in row.actions"
              :key="`${row.label}-${action.label}`"
              :to="action.to"
              class="process-summary-panel__row-action"
            >
              {{ action.label }}
            </RouterLink>
          </span>
        </dd>
      </div>
    </dl>

    <div
      v-if="visibleItems.length > 0"
      class="process-summary-panel__nav"
    >
      <el-button
        v-for="item in visibleItems"
        :key="item.key || item.label"
        :type="item.type || 'primary'"
        :plain="item.plain ?? true"
        :disabled="item.disabled"
        @click="emit('select', item)"
      >
        {{ item.label }}
      </el-button>
    </div>

    <ul
      v-if="tips.length > 0"
      class="process-summary-panel__tips"
    >
      <li
        v-for="tip in tips"
        :key="tip"
      >
        {{ tip }}
      </li>
    </ul>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { RuntimeWorkbenchClosurePanel } from '@/types/runtime'
import type { ClosedLoopNavigationItem } from '@/composables/useClosedLoopNavigation'
import type { DynamicDetailNavigationSection } from '@/views/dynamic/workspace/detailNavigationModel'
import type {
  ObjectWorkspaceInfoRow,
} from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import type { ObjectWorkspaceStat } from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import {
  formatWorkbenchValue,
  readWorkbenchRecordValue,
} from './workbenchHelpers'

const props = withDefaults(defineProps<{
  stats?: ObjectWorkspaceStat[]
  panel: RuntimeWorkbenchClosurePanel | null
  recordData?: Record<string, unknown> | null
  extraRows?: ObjectWorkspaceInfoRow[]
  navigationSection?: DynamicDetailNavigationSection | null
}>(), {
  stats: () => [],
  recordData: null,
  extraRows: () => [],
  navigationSection: null,
})

const emit = defineEmits<{
  (e: 'select', item: ClosedLoopNavigationItem): void
}>()

const { t } = useI18n()

const eyebrow = computed(() => t('common.workbench.eyebrows.processSummary'))
const title = computed(() => t('common.workbench.titles.processSummary'))
const hint = computed(() => {
  return props.navigationSection?.hint || t('common.workbench.messages.processSummaryHint')
})

const rows = computed<ObjectWorkspaceInfoRow[]>(() => {
  const panel = props.panel
  const baseRows: ObjectWorkspaceInfoRow[] = []

  if (panel) {
    const stageValue = readWorkbenchRecordValue(props.recordData, panel.stageField || panel.stage_field)
    const ownerValue = readWorkbenchRecordValue(props.recordData, panel.ownerField || panel.owner_field)
    const blockerValue = readWorkbenchRecordValue(props.recordData, panel.blockerField || panel.blocker_field)
    const progressValue = readWorkbenchRecordValue(props.recordData, panel.progressField || panel.progress_field)

    const addRow = (label: string, value: unknown) => {
      const formatted = formatWorkbenchValue(value, t('common.workbench.messages.notAvailable'), '', {
        trueLabel: t('common.yes'),
        falseLabel: t('common.no'),
      })
      if (formatted === t('common.workbench.messages.notAvailable')) {
        return
      }
      baseRows.push({ label, value: formatted })
    }

    addRow(t('common.workbench.labels.stage'), stageValue)
    addRow(t('common.workbench.labels.owner'), ownerValue)
    addRow(t('common.workbench.labels.blocker'), blockerValue)
    addRow(t('common.workbench.labels.completion'), progressValue)
  }

  return [...baseRows, ...(props.extraRows || [])]
})

const visibleItems = computed(() => {
  return (props.navigationSection?.items || []).filter((item) => item && item.visible !== false)
})

const tips = computed(() => {
  const blocker = props.panel
    ? readWorkbenchRecordValue(props.recordData, props.panel.blockerField || props.panel.blocker_field)
    : null
  return blocker ? [t('common.workbench.messages.blockerHint')] : []
})

const hasContent = computed(() => {
  return (
    props.stats.length > 0 ||
    rows.value.length > 0 ||
    visibleItems.value.length > 0
  )
})
</script>

<style scoped lang="scss">
.process-summary-panel {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 24px;
  background:
    linear-gradient(135deg, rgba(248, 250, 252, 0.96), rgba(255, 255, 255, 0.98)),
    #ffffff;

  &__header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    flex-wrap: wrap;
  }

  &__copy {
    min-width: 0;
  }

  &__eyebrow {
    margin: 0 0 8px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #475569;
  }

  &__title {
    margin: 0;
    font-size: 20px;
    line-height: 1.3;
    color: #0f172a;
  }

  &__hint {
    margin: 0;
    max-width: 420px;
    font-size: 13px;
    line-height: 1.7;
    color: #64748b;
  }

  &__stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
    margin-top: 20px;
  }

  &__stat {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 16px 18px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.14);
  }

  &__stat-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #64748b;
  }

  &__stat-value {
    font-size: 24px;
    line-height: 1.2;
    color: #0f172a;
  }

  &__stat-meta {
    font-size: 12px;
    line-height: 1.6;
    color: #64748b;
  }

  &__stat-actions,
  &__row-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  &__stat-action,
  &__row-action {
    color: #2563eb;
    font-size: 12px;
    font-weight: 700;
    text-decoration: none;
  }

  &__stat-action:hover,
  &__row-action:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }

  &__rows {
    display: grid;
    gap: 12px;
    margin: 20px 0 0;
  }

  &__row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(226, 232, 240, 0.88);

    dt {
      flex: 0 0 160px;
      font-size: 13px;
      font-weight: 600;
      color: #475569;
    }

    dd {
      margin: 0;
      min-width: 0;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
      text-align: right;
      color: #0f172a;
    }
  }

  &__row:last-child {
    border-bottom: 0;
    padding-bottom: 0;
  }

  &__row-value {
    font-weight: 600;
  }

  &__row-meta {
    font-size: 12px;
    line-height: 1.6;
    color: #64748b;
  }

  &__nav {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 20px;
  }

  &__tips {
    margin: 16px 0 0;
    padding-left: 18px;
    color: #64748b;
    font-size: 13px;
    line-height: 1.8;
  }
}

@media (max-width: 900px) {
  .process-summary-panel {
    &__row {
      flex-direction: column;

      dt,
      dd {
        flex: none;
        text-align: left;
        align-items: flex-start;
      }
    }
  }
}
</style>
