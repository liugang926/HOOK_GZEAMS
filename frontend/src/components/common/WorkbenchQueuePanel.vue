<template>
  <section
    v-if="items.length > 0"
    class="workbench-queue-panel"
  >
    <header class="workbench-queue-panel__header">
      <div>
        <p class="workbench-queue-panel__eyebrow">
          {{ eyebrow }}
        </p>
        <h3 class="workbench-queue-panel__title">
          {{ title }}
        </h3>
      </div>
      <p class="workbench-queue-panel__description">
        {{ description }}
      </p>
    </header>

    <ul class="workbench-queue-panel__list">
      <li
        v-for="item in items"
        :key="item.code"
        :class="['workbench-queue-panel__item', `workbench-queue-panel__item--${item.tone}`]"
      >
        <div class="workbench-queue-panel__copy">
          <strong>{{ item.label }}</strong>
          <p v-if="item.description">
            {{ item.description }}
          </p>
        </div>

        <div class="workbench-queue-panel__meta">
          <span class="workbench-queue-panel__count">{{ item.count }}</span>
          <el-button
            v-if="item.route"
            text
            type="primary"
            @click="router.push(item.route)"
          >
            {{ t('common.actions.view') }}
          </el-button>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { RuntimeWorkbenchQueuePanel } from '@/types/runtime'
import {
  formatWorkbenchValue,
  resolveWorkbenchCountValue,
  resolveWorkbenchRoute,
  resolveWorkbenchText,
} from './workbenchHelpers'

const props = withDefaults(defineProps<{
  panels?: RuntimeWorkbenchQueuePanel[]
  recordData?: Record<string, unknown> | null
  variant?: 'queue' | 'exception'
}>(), {
  panels: () => [],
  recordData: null,
  variant: 'queue',
})

const router = useRouter()
const { t, te } = useI18n()

const eyebrow = computed(() => {
  return props.variant === 'exception'
    ? t('common.workbench.eyebrows.exceptionQueues')
    : t('common.workbench.eyebrows.pendingQueues')
})

const title = computed(() => {
  return props.variant === 'exception'
    ? t('common.workbench.titles.exceptionQueues')
    : t('common.workbench.titles.pendingQueues')
})

const description = computed(() => {
  return props.variant === 'exception'
    ? t('common.workbench.messages.exceptionQueueHint')
    : t('common.workbench.messages.queueHint')
})

const resolveTone = (definition: RuntimeWorkbenchQueuePanel) => {
  const fallback = props.variant === 'exception' ? 'danger' : 'warning'
  const tone = String(definition.tone || fallback).trim().toLowerCase()
  if (['neutral', 'info', 'success', 'warning', 'danger'].includes(tone)) {
    return tone
  }
  return fallback
}

const items = computed(() => {
  return props.panels.map((panel) => {
    const value = resolveWorkbenchCountValue(panel, props.recordData)

    return {
      code: panel.code,
      label: resolveWorkbenchText(
        panel,
        t,
        te,
        ['titleKey', 'title_key', 'labelKey', 'label_key'],
        ['title', 'label', 'code'],
      ) || panel.code,
      description: resolveWorkbenchText(
        panel,
        t,
        te,
        ['descriptionKey', 'description_key', 'hintKey', 'hint_key'],
        ['description', 'hint'],
      ),
      count: formatWorkbenchValue(value, t('common.workbench.messages.notAvailable')),
      route: resolveWorkbenchRoute(panel, props.recordData),
      tone: resolveTone(panel),
    }
  })
})
</script>

<style scoped lang="scss">
@use '@/styles/object-workspace.scss' as workspace;

.workbench-queue-panel {
  @include workspace.workspace-panel();
  padding: 24px;
}

.workbench-queue-panel__header {
  @include workspace.workspace-panel-header();
}

.workbench-queue-panel__eyebrow {
  @include workspace.panel-kicker();
}

.workbench-queue-panel__title {
  @include workspace.panel-title();
}

.workbench-queue-panel__description {
  @include workspace.panel-text(380px);
}

.workbench-queue-panel__list {
  display: grid;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.workbench-queue-panel__item {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  padding: 16px 18px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.9);

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

.workbench-queue-panel__copy {
  min-width: 0;

  strong {
    display: block;
    font-size: 15px;
    font-weight: 700;
    color: rgba(15, 23, 42, 0.96);
  }

  p {
    margin: 8px 0 0;
    font-size: 13px;
    line-height: 1.6;
    color: rgba(71, 85, 105, 0.92);
  }
}

.workbench-queue-panel__meta {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-shrink: 0;
}

.workbench-queue-panel__count {
  font-size: 28px;
  font-weight: 700;
  color: rgba(15, 23, 42, 0.96);
}

@media (max-width: 768px) {
  .workbench-queue-panel__header,
  .workbench-queue-panel__item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
