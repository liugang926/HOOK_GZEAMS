<template>
  <ObjectWorkspaceInfoCard
    v-if="rows.length > 0 || title"
    variant="detail"
    :eyebrow="eyebrow"
    :title="title"
    :rows="rows"
    :tips="tips"
    soft
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { RuntimeWorkbenchClosurePanel } from '@/types/runtime'
import ObjectWorkspaceInfoCard, {
  type ObjectWorkspaceInfoRow,
} from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import {
  formatWorkbenchValue,
  readWorkbenchRecordValue,
  resolveWorkbenchText,
} from './workbenchHelpers'

const props = defineProps<{
  panel: RuntimeWorkbenchClosurePanel | null
  recordData?: Record<string, unknown> | null
}>()

const { t, te } = useI18n()

const eyebrow = computed(() => {
  const panel = props.panel || {}
  return resolveWorkbenchText(
    panel,
    t,
    te,
    ['eyebrowKey', 'eyebrow_key'],
    ['eyebrow'],
  ) || t('common.workbench.eyebrows.closure')
})

const title = computed(() => {
  const panel = props.panel || {}
  return resolveWorkbenchText(
    panel,
    t,
    te,
    ['titleKey', 'title_key'],
    ['title'],
  ) || t('common.workbench.titles.closure')
})

const rows = computed<ObjectWorkspaceInfoRow[]>(() => {
  if (!props.panel) return []

  const stageValue = readWorkbenchRecordValue(props.recordData, props.panel.stageField || props.panel.stage_field)
  const ownerValue = readWorkbenchRecordValue(props.recordData, props.panel.ownerField || props.panel.owner_field)
  const blockerValue = readWorkbenchRecordValue(props.recordData, props.panel.blockerField || props.panel.blocker_field)
  const progressValue = readWorkbenchRecordValue(props.recordData, props.panel.progressField || props.panel.progress_field)

  return [
    {
      label: t('common.workbench.labels.stage'),
      value: formatWorkbenchValue(stageValue, t('common.workbench.messages.notAvailable'), '', {
        trueLabel: t('common.yes'),
        falseLabel: t('common.no'),
      }),
    },
    {
      label: t('common.workbench.labels.owner'),
      value: formatWorkbenchValue(ownerValue, t('common.workbench.messages.notAvailable'), '', {
        trueLabel: t('common.yes'),
        falseLabel: t('common.no'),
      }),
    },
    {
      label: t('common.workbench.labels.blocker'),
      value: formatWorkbenchValue(blockerValue, t('common.workbench.messages.notAvailable'), '', {
        trueLabel: t('common.yes'),
        falseLabel: t('common.no'),
      }),
    },
    {
      label: t('common.workbench.labels.completion'),
      value: formatWorkbenchValue(progressValue, t('common.workbench.messages.notAvailable'), '', {
        trueLabel: t('common.yes'),
        falseLabel: t('common.no'),
      }),
    },
  ].filter((row) => row.value !== t('common.workbench.messages.notAvailable'))
})

const tips = computed(() => {
  if (!props.panel) return []
  const blocker = readWorkbenchRecordValue(props.recordData, props.panel.blockerField || props.panel.blocker_field)
  if (!blocker) return []
  return [t('common.workbench.messages.blockerHint')]
})
</script>
