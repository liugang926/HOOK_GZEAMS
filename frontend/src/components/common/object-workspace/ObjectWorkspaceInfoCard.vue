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
        <dd>{{ row.value }}</dd>
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

export interface ObjectWorkspaceInfoRow {
  label: string
  value: string | number
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
    }
  }

  &__tips {
    @include workspace.info-tips();
  }
}
</style>
