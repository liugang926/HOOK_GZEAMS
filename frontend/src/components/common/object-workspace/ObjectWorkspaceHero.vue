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

    <div
      v-if="stats.length > 0"
      :class="`${baseClass}__stats`"
    >
      <article
        v-for="stat in stats"
        :key="stat.label"
        :class="statCardClass"
      >
        <span :class="`${statCardClass}__label`">{{ stat.label }}</span>
        <strong
          :class="`${statCardClass}__value`"
          :title="stat.tooltip || undefined"
        >{{ stat.value }}</strong>
        <p
          v-if="stat.meta"
          :class="`${statCardClass}__meta`"
        >
          {{ stat.meta }}
        </p>
        <div
          v-if="stat.actions && stat.actions.length > 0"
          :class="`${statCardClass}__actions`"
        >
          <RouterLink
            v-for="action in stat.actions"
            :key="`${stat.label}-${action.label}`"
            :to="action.to"
            :class="`${statCardClass}__action`"
          >
            {{ action.label }}
          </RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { RouteLocationRaw } from 'vue-router'
import { RouterLink } from 'vue-router'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'

export interface ObjectWorkspaceChip {
  label: string
  kind?: 'primary' | 'muted'
}

export interface ObjectWorkspaceActionLink {
  label: string
  to: RouteLocationRaw
}

export interface ObjectWorkspaceStat {
  label: string
  value: string | number
  tooltip?: string
  meta?: string
  actions?: ObjectWorkspaceActionLink[]
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

  &__meta {
    margin: 10px 0 0;
    font-size: 12px;
    line-height: 1.6;
    color: #64748b;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 12px;
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
