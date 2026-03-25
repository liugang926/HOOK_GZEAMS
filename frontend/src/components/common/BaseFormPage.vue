<template>
  <div class="base-form-page">
    <slot name="hero" />

    <div class="form-layout">
      <section class="form-panel form-panel--main">
        <header
          v-if="showHeader"
          class="form-panel__header"
        >
          <div>
            <p
              v-if="panelKicker"
              class="form-panel__kicker"
            >
              {{ panelKicker }}
            </p>
            <h2
              v-if="panelTitle"
              class="form-panel__title"
            >
              {{ panelTitle }}
            </h2>
          </div>
          <p
            v-if="panelDescription"
            class="form-panel__text"
          >
            {{ panelDescription }}
          </p>
        </header>

        <div class="form-panel__renderer">
          <slot />
        </div>
      </section>

      <aside
        v-if="hasAside"
        class="form-panel form-panel--aside"
      >
        <slot name="aside" />
      </aside>
    </div>

    <div
      v-if="showFooter"
      class="form-actions"
    >
      <div
        v-if="hasSummary"
        class="form-actions__summary"
      >
        <slot name="summary">
          <span
            v-if="summaryBadge"
            class="form-actions__badge"
          >
            {{ summaryBadge }}
          </span>
          <p
            v-if="summaryText"
            class="form-actions__text"
          >
            {{ summaryText }}
          </p>
        </slot>
      </div>

      <div
        v-if="hasFooterActions"
        class="form-actions__buttons"
      >
        <slot name="actions">
          <el-button
            v-if="cancelVisible"
            :icon="cancelIcon"
            :disabled="cancelDisabled"
            @click="emit('cancel')"
          >
            {{ cancelLabel }}
          </el-button>
          <el-button
            v-if="submitVisible"
            type="primary"
            :icon="submitIcon"
            :loading="submitLoading"
            :disabled="submitDisabled"
            @click="emit('submit')"
          >
            {{ submitLabel }}
          </el-button>
        </slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue'

interface Props {
  panelKicker?: string
  panelTitle?: string
  panelDescription?: string
  summaryBadge?: string
  summaryText?: string
  cancelLabel?: string
  cancelDisabled?: boolean
  cancelVisible?: boolean
  cancelIcon?: unknown
  submitLabel?: string
  submitLoading?: boolean
  submitDisabled?: boolean
  submitVisible?: boolean
  submitIcon?: unknown
  showFooter?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  panelKicker: '',
  panelTitle: '',
  panelDescription: '',
  summaryBadge: '',
  summaryText: '',
  cancelLabel: 'Cancel',
  cancelDisabled: false,
  cancelVisible: true,
  cancelIcon: undefined,
  submitLabel: 'Save',
  submitLoading: false,
  submitDisabled: false,
  submitVisible: true,
  submitIcon: undefined,
  showFooter: true,
})

const emit = defineEmits<{
  (e: 'cancel'): void
  (e: 'submit'): void
}>()

const slots = useSlots()

const hasAside = computed(() => Boolean(slots.aside))
const showHeader = computed(() => Boolean(props.panelKicker || props.panelTitle || props.panelDescription))
const hasSummary = computed(() => Boolean(slots.summary || props.summaryBadge || props.summaryText))
const hasFooterActions = computed(() => {
  if (slots.actions) return true
  return Boolean(props.cancelVisible || props.submitVisible)
})
const showFooter = computed(() => Boolean(props.showFooter && (hasSummary.value || hasFooterActions.value)))
</script>

<style scoped lang="scss">
@use '@/views/dynamic/styles/dynamic-form-page' as formPage;

@include formPage.dynamic-form-page-styles();
</style>
