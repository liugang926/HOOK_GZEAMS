<template>
  <section :class="heroClass">
    <div :class="`${baseClass}__header`">
      <el-button
        v-if="showBack"
        text
        :class="`${baseClass}__back`"
        :icon="backIcon"
        @click="$emit('back')"
      >
        {{ backLabel }}
      </el-button>

      <div :class="`${baseClass}__identity`">
        <ObjectAvatar
          :object-code="objectCode"
          :icon="icon"
          size="xl"
        />

        <div :class="`${baseClass}__copy`">
          <p :class="`${baseClass}__eyebrow`">
            {{ eyebrow }}
          </p>
          <h1 :class="`${baseClass}__title`">
            {{ title }}
          </h1>
          <p :class="`${baseClass}__description`">
            {{ description }}
          </p>

          <div :class="`${baseClass}__chips`">
            <span
              v-for="chip in chips"
              :key="chip.label"
              :class="[chipClass, chip.kind ? `${chipClass}--${chip.kind}` : '']"
            >
              {{ chip.label }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div :class="`${baseClass}__stats`">
      <article
        v-for="stat in stats"
        :key="stat.label"
        :class="statCardClass"
      >
        <span :class="`${statCardClass}__label`">{{ stat.label }}</span>
        <strong :class="`${statCardClass}__value`">{{ stat.value }}</strong>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'

export interface ObjectWorkspaceChip {
  label: string
  kind?: 'primary' | 'muted'
}

export interface ObjectWorkspaceStat {
  label: string
  value: string | number
}

interface Props {
  variant?: 'form' | 'detail' | 'list'
  objectCode: string
  icon?: string
  eyebrow: string
  title: string
  description: string
  chips?: ObjectWorkspaceChip[]
  stats?: ObjectWorkspaceStat[]
  showBack?: boolean
  backLabel?: string
  backIcon?: any
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'list',
  icon: '',
  chips: () => [],
  stats: () => [],
  showBack: false,
  backLabel: '',
  backIcon: undefined,
})

defineEmits<{
  (e: 'back'): void
}>()

const baseClass = computed(() => `${props.variant}-hero`)
const chipClass = computed(() => {
  const prefix = props.variant === 'form' ? 'hero' : props.variant
  return `${prefix}-chip`
})
const statCardClass = computed(() => {
  const prefix = props.variant === 'form' ? 'hero' : props.variant
  return `${prefix}-stat-card`
})
const heroClass = computed(() => baseClass.value)
</script>

<style scoped lang="scss">
@use '@/styles/object-workspace.scss' as workspace;

.form-hero,
.detail-hero,
.list-hero {
  @include workspace.hero();

  &__header {
    @include workspace.hero-header();
  }

  &__back {
    @include workspace.hero-back();
  }

  &__identity {
    @include workspace.hero-identity();
  }

  &__copy {
    @include workspace.hero-copy();
  }

  &__eyebrow {
    @include workspace.eyebrow();
  }

  &__title {
    @include workspace.hero-title();
  }

  &__description {
    @include workspace.hero-description();
  }

  &__chips {
    @include workspace.chip-row();
  }

  &__stats {
    @include workspace.stats-grid();
  }
}

.hero-chip,
.detail-chip,
.list-chip {
  @include workspace.chip();

  &--primary {
    @include workspace.chip-primary();
  }

  &--muted {
    @include workspace.chip-muted();
  }
}

.hero-stat-card,
.detail-stat-card,
.list-stat-card {
  @include workspace.stat-card();

  &__label {
    @include workspace.stat-label();
  }

  &__value {
    @include workspace.stat-value();
  }
}

.detail-stat-card__value {
  @include workspace.stat-value(26px);
}

@media (max-width: 900px) {
  .form-hero,
  .detail-hero,
  .list-hero {
    @include workspace.responsive-hero();
  }
}
</style>
