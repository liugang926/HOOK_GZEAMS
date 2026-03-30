<template>
  <div
    class="section-block"
    :class="{
      'is-collapsed': isCollapsed,
      'no-border': noBorder,
      [`section-${variant}`]: variant,
      [`section-${size}`]: size
    }"
  >
    <div
      class="section-header"
      :class="{
        'clickable': collapsible || !collapsible,
        'no-padding': headerNoPadding
      }"
      @click="handleHeaderClick"
    >
      <div class="title">
        <el-icon
          v-if="collapsible"
          :class="{ 'is-collapsed': isCollapsed }"
          class="collapse-icon"
          :aria-label="collapseButtonLabel"
        >
          <ArrowDown />
        </el-icon>
        <el-icon
          v-else-if="icon"
          :class="`icon-${icon}`"
        >
          <component :is="icon" />
        </el-icon>
        <span class="text">{{ title }}</span>
        <el-tag
          v-if="tag"
          :type="tagType"
          size="small"
          class="title-tag"
        >
          {{ tag }}
        </el-tag>
      </div>
      <div class="actions">
        <slot
          name="actions"
          :collapsed="isCollapsed"
          :toggle="toggle"
        />
        <el-tooltip
          v-if="showTooltip"
          :content="tooltip"
          placement="top"
        >
          <el-icon class="info-icon">
            <InfoFilled />
          </el-icon>
        </el-tooltip>
      </div>
    </div>
    <el-collapse-transition>
      <div
        v-show="!isCollapsed"
        class="section-body"
        :class="{
          'no-padding': noPadding
        }"
      >
        <slot />
        <slot name="body" />
      </div>
    </el-collapse-transition>
    <div
      v-if="$slots.footer"
      class="section-footer"
    >
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown, InfoFilled } from '@element-plus/icons-vue'

/**
 * SectionBlock Component
 *
 * A collapsible section container for grouping related content.
 *
 * Features:
 * - Collapsible with animated transition
 * - Multiple visual variants (default/primary/success/warning/danger)
 * - Size variations (small/medium/large)
 * - Icon and tag support for title
 * - Optional footer slot
 * - Configurable border and padding
 * - i18n support for internationalization
 *
 * PRD Reference: docs/plans/common_base_features/section_block_layout.md
 */

const { t } = useI18n()

export interface Props {
  /** Section title */
  title: string
  /** Initial collapsed state */
  collapsed?: boolean
  /** Enable/disable collapsible functionality */
  collapsible?: boolean
  /** Visual variant */
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info'
  /** Size variant */
  size?: 'small' | 'medium' | 'large'
  /** Header icon (component) */
  icon?: any
  /** Tag text to display after title */
  tag?: string | number
  /** Tag type */
  tagType?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  /** Tooltip text */
  tooltip?: string
  /** Remove border */
  noBorder?: boolean
  /** Remove body padding */
  noPadding?: boolean
  /** Remove header padding */
  headerNoPadding?: boolean
  /** Model value for two-way binding (collapsed state) */
  modelValue?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  collapsible: true,
  variant: 'default',
  size: 'medium',
  tagType: 'info',
  noBorder: false,
  noPadding: false,
  headerNoPadding: false,
  modelValue: undefined
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'collapse', value: boolean): void
  (e: 'toggle'): void
}>()

const isCollapsed = ref(props.collapsed)

/**
 * Show tooltip if text is provided
 */
const showTooltip = computed(() => Boolean(props.tooltip))

/**
 * Get aria-label for collapse button based on state
 */
const collapseButtonLabel = computed(() =>
  isCollapsed.value ? t('common.actions.expand') : t('common.actions.collapse')
)

/**
 * Toggle collapsed state
 */
const toggle = () => {
  if (!props.collapsible) return
  isCollapsed.value = !isCollapsed.value
  emit('collapse', isCollapsed.value)
  emit('toggle')
  if (props.modelValue !== undefined) {
    emit('update:modelValue', isCollapsed.value)
  }
}

/**
 * Handle header click
 */
const handleHeaderClick = () => {
  toggle()
}

/**
 * Sync with modelValue prop changes
 */
watch(() => props.modelValue, (newValue) => {
  if (newValue !== undefined) {
    isCollapsed.value = newValue
  }
})

/**
 * Sync with collapsed prop changes
 */
watch(() => props.collapsed, (newValue) => {
  isCollapsed.value = newValue
})
</script>

<style scoped>
.section-block {
  margin-bottom: 16px;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  background: var(--el-bg-color);
  transition: all 0.3s;
}

.section-block.no-border {
  border: none;
}

.section-block.is-collapsed {
  border-radius: 4px;
}

/* Size variants */
.section-small .section-header {
  padding: 8px 12px;
}

.section-small .section-body {
  padding: 12px;
}

.section-large .section-header {
  padding: 14px 18px;
}

.section-large .section-body {
  padding: 18px;
}

/* Variant styles */
.section-primary .section-header {
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-color-primary-light-8) 100%);
  border-bottom-color: var(--el-color-primary-light-5);
}

.section-success .section-header {
  background: linear-gradient(135deg, var(--el-color-success-light-9) 0%, var(--el-color-success-light-8) 100%);
  border-bottom-color: var(--el-color-success-light-5);
}

.section-warning .section-header {
  background: linear-gradient(135deg, var(--el-color-warning-light-9) 0%, var(--el-color-warning-light-8) 100%);
  border-bottom-color: var(--el-color-warning-light-5);
}

.section-danger .section-header {
  background: linear-gradient(135deg, var(--el-color-danger-light-9) 0%, var(--el-color-danger-light-8) 100%);
  border-bottom-color: var(--el-color-danger-light-5);
}

.section-info .section-header {
  background: linear-gradient(135deg, var(--el-color-info-light-9) 0%, var(--el-color-info-light-8) 100%);
  border-bottom-color: var(--el-color-info-light-5);
}

.section-header {
  padding: 12px 16px;
  background-color: var(--el-fill-color-light);
  border-bottom: 1px solid var(--el-border-color-lighter);
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.3s;
}

.section-header.clickable {
  cursor: pointer;
  user-select: none;
}

.section-header.clickable:hover {
  background-color: var(--el-fill-color);
}

.section-header.no-padding {
  padding: 0;
}

.title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.text {
  font-size: 14px;
}

.collapse-icon {
  transition: transform 0.3s;
  color: var(--el-text-color-regular);
}

.collapse-icon.is-collapsed {
  transform: rotate(-90deg);
}

.title-tag {
  font-size: 12px;
  height: 20px;
  line-height: 20px;
  padding: 0 8px;
}

.info-icon {
  color: var(--el-color-info);
  cursor: help;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-body {
  padding: 16px;
}

.section-body.no-padding {
  padding: 0;
}

.section-footer {
  padding: 12px 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-lighter);
}

/* Icon styling */
[class^="icon-"] {
  font-size: 16px;
  color: var(--el-color-primary);
}
</style>
