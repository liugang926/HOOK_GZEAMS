<template>
  <section :class="cardClass">
    <p :class="`${baseClass}__eyebrow`">
      {{ eyebrow }}
    </p>

    <h3
      v-if="title"
      :class="`${baseClass}__title`"
    >
      {{ title }}
    </h3>

    <dl
      v-if="rows.length > 0"
      :class="`${baseClass}__list`"
    >
      <div
        v-for="row in rows"
        :key="row.label"
        :class="`${baseClass}__row`"
      >
        <dt>{{ row.label }}</dt>
        <dd>
          <span
            :class="`${baseClass}__value`"
            :title="row.tooltip || undefined"
          >
            {{ row.value }}
          </span>
          <span
            v-if="row.meta"
            :class="`${baseClass}__meta`"
          >
            {{ row.meta }}
          </span>
          <span
            v-if="row.actions && row.actions.length > 0"
            :class="`${baseClass}__actions`"
          >
            <RouterLink
              v-for="action in row.actions"
              :key="`${row.label}-${action.label}`"
              :to="action.to"
              :class="`${baseClass}__action`"
            >
              {{ action.label }}
            </RouterLink>
          </span>
        </dd>
      </div>
    </dl>

    <ul
      v-if="tips.length > 0"
      :class="`${baseClass}__tips`"
    >
      <li
        v-for="tip in tips"
        :key="tip"
      >
        {{ tip }}
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import type { ObjectWorkspaceActionLink } from './ObjectWorkspaceHero.vue'

export interface ObjectWorkspaceInfoRow {
  label: string
  value: string | number
  tooltip?: string
  meta?: string
  actions?: ObjectWorkspaceActionLink[]
}

interface Props {
  variant?: 'form' | 'detail'
  eyebrow: string
  title?: string
  rows?: ObjectWorkspaceInfoRow[]
  tips?: string[]
  soft?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'form',
  title: '',
  rows: () => [],
  tips: () => [],
  soft: false,
})

const baseClass = computed(() => `${props.variant}-info-card`)
const cardClass = computed(() => [
  baseClass.value,
  { [`${baseClass.value}--soft`]: props.soft },
])
</script>

<style scoped lang="scss">
@use '@/styles/object-workspace.scss' as workspace;

.form-info-card,
.detail-info-card {
  @include workspace.info-card();

  &--soft {
    @include workspace.info-card-soft();
  }

  &__eyebrow {
    @include workspace.panel-kicker();
  }

  &__title {
    @include workspace.info-title();
  }

  &__row {
    @include workspace.info-row();

    dt {
      @include workspace.info-row-term();
    }

    dd {
      @include workspace.info-row-value();
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
    }
  }

  &__value {
    display: block;
  }

  &__meta {
    font-size: 12px;
    font-weight: 500;
    line-height: 1.5;
    color: #64748b;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 10px;
  }

  &__action {
    color: #2563eb;
    font-size: 12px;
    font-weight: 700;
    text-decoration: none;
  }

  &__action:hover {
    color: #1d4ed8;
    text-decoration: underline;
  }

  @media (max-width: 900px) {
    &__row {
      align-items: flex-start;
    }

    &__row dd {
      align-items: flex-start;
      text-align: left;
    }
  }

  &__tips {
    @include workspace.info-tips();
  }
}
</style>
