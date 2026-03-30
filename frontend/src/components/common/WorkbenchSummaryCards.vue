<template>
  <section
    v-if="items.length > 0"
    class="workbench-summary-cards"
  >
    <div
      v-for="item in items"
      :key="item.code"
      :class="['workbench-summary-cards__item', `workbench-summary-cards__item--${item.tone}`]"
    >
      <p class="workbench-summary-cards__label">
        {{ item.label }}
      </p>
      <strong class="workbench-summary-cards__value">
        {{ item.value }}
      </strong>
      <p
        v-if="item.description"
        class="workbench-summary-cards__description"
      >
        {{ item.description }}
      </p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { RuntimeWorkbenchSummaryCard } from '@/types/runtime'
import {
  formatWorkbenchValue,
  readWorkbenchRecordValue,
  resolveWorkbenchText,
} from './workbenchHelpers'

const props = withDefaults(defineProps<{
  cards?: RuntimeWorkbenchSummaryCard[]
  recordData?: Record<string, unknown> | null
}>(), {
  cards: () => [],
  recordData: null,
})

const { t, te } = useI18n()

const resolveTone = (definition: RuntimeWorkbenchSummaryCard) => {
  const tone = String(definition.tone || 'neutral').trim().toLowerCase()
  if (['neutral', 'info', 'success', 'warning', 'danger'].includes(tone)) {
    return tone
  }
  return 'neutral'
}

const items = computed(() => {
  return props.cards.map((card) => {
    const label = resolveWorkbenchText(
      card,
      t,
      te,
      ['labelKey', 'label_key', 'titleKey', 'title_key'],
      ['label', 'title', 'code'],
    ) || t('common.workbench.labels.summary')
    const description = resolveWorkbenchText(
      card,
      t,
      te,
      ['descriptionKey', 'description_key'],
      ['description'],
    )
    const value = card.value ?? readWorkbenchRecordValue(props.recordData, card.valueField || card.value_field)

    return {
      code: card.code,
      label,
      description,
      tone: resolveTone(card),
      value: formatWorkbenchValue(
        value,
        t('common.workbench.messages.notAvailable'),
        String(card.suffix || ''),
        {
          trueLabel: t('common.yes'),
          falseLabel: t('common.no'),
        },
      ),
    }
  })
})
</script>

<style scoped lang="scss">
@use '@/styles/object-workspace.scss' as workspace;

.workbench-summary-cards {
  @include workspace.stats-grid();
}

.workbench-summary-cards__item {
  @include workspace.stat-card();

  &--info {
    background: linear-gradient(180deg, rgba(239, 246, 255, 0.96), rgba(255, 255, 255, 0.96));
  }

  &--success {
    background: linear-gradient(180deg, rgba(236, 253, 245, 0.96), rgba(255, 255, 255, 0.96));
  }

  &--warning {
    background: linear-gradient(180deg, rgba(255, 251, 235, 0.96), rgba(255, 255, 255, 0.96));
  }

  &--danger {
    background: linear-gradient(180deg, rgba(254, 242, 242, 0.96), rgba(255, 255, 255, 0.96));
  }
}

.workbench-summary-cards__label {
  @include workspace.stat-label();
}

.workbench-summary-cards__value {
  @include workspace.stat-value(30px);
}

.workbench-summary-cards__description {
  margin: 10px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(71, 85, 105, 0.92);
}

@media (max-width: 960px) {
  .workbench-summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>
