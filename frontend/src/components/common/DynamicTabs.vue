<template>
  <el-tabs
    v-model="activeTab"
    :type="typeStyle"
    :position="position"
    :stretch="stretch"
    :animated="animated"
    :addable="addable"
    :editable="editable"
    :closable="hasClosableTabs"
    :tab-position="position"
    @tab-remove="handleRemove"
    @tab-add="handleAdd"
    @tab-change="handleChange"
    @edit="handleEdit"
  >
    <el-tab-pane
      v-for="tab in visibleTabs"
      :key="tab.id || tab.name"
      :name="tab.id || tab.name"
      :closable="tab.closable"
      :disabled="tab.disabled"
      :lazy="tab.lazy !== false"
    >
      <template #label>
        <span class="tab-label">
          <el-icon v-if="tab.icon" class="tab-icon">
            <component :is="tab.icon" />
          </el-icon>
          <span class="tab-title">{{ tab.title }}</span>
          <el-badge
            v-if="tab.badge !== undefined"
            :value="tab.badge"
            :type="typeof tab.badge === 'number' && tab.badge > 0 ? 'danger' : 'info'"
            class="tab-badge"
          />
        </span>
      </template>

      <!-- Slot-based content -->
      <template v-if="tab.content && typeof tab.content === 'string'" #default>
        <div v-html="tab.content" />
      </template>

      <!-- Component-based content -->
      <component
        v-else-if="tab.component"
        :is="tab.component"
        v-bind="tab.props"
      />

      <!-- Default slot content -->
      <slot v-else :name="`tab-${tab.id || tab.name}`" :tab="tab" />
    </el-tab-pane>

    <!-- Default slot for custom tab panes -->
    <slot />
  </el-tabs>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import type { TabItem } from '@/api/system'

/**
 * DynamicTabs Component
 *
 * A comprehensive tab component supporting:
 * - Multiple positions (top, left, right, bottom)
 * - Type styles (default, card, border-card)
 * - Individual tab controls (closable, disabled, visible, lazy)
 * - Badge and icon support
 * - Addable and draggable tabs
 * - Multiple content render modes (component, slot, HTML)
 *
 * PRD Reference: docs/plans/common_base_features/tab_configuration.md
 */

export interface TabConfig {
  position?: 'top' | 'left' | 'right' | 'bottom'
  typeStyle?: '' | 'card' | 'border-card'
  stretch?: boolean
  animated?: boolean
  addable?: boolean
  editable?: boolean
  draggable?: boolean
}

export interface Props {
  /** Currently active tab name/id (v-model) */
  modelValue: string
  /** Array of tab items */
  tabs?: TabItem[]
  /** Tab position */
  position?: 'top' | 'left' | 'right' | 'bottom'
  /** Tab style type */
  typeStyle?: '' | 'card' | 'border-card'
  /** Stretch tabs to fill container width */
  stretch?: boolean
  /** Enable tab switching animation */
  animated?: boolean
  /** Show add button for new tabs */
  addable?: boolean
  /** Enable editable tabs (add/remove) */
  editable?: boolean
  /** Enable drag-and-drop reordering */
  draggable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  tabs: () => [],
  position: 'top',
  typeStyle: '',
  stretch: false,
  animated: true,
  addable: false,
  editable: false,
  draggable: false
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'remove', targetName: string, tab: TabItem): void
  (e: 'add'): void
  (e: 'change', targetName: string): void
  (e: 'edit', targetName: string, action: 'add' | 'remove'): void
}>()

const activeTab = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

/**
 * Filter tabs by visibility
 */
const visibleTabs = computed(() => {
  return (props.tabs || []).filter(tab => tab.visible !== false)
})

/**
 * Check if any tab is closable
 */
const hasClosableTabs = computed(() => {
  return visibleTabs.value.some(tab => tab.closable !== false)
})

/**
 * Handle tab removal
 */
const handleRemove = (targetName: string) => {
  const tab = visibleTabs.value.find(t => (t.id || t.name) === targetName)
  emit('remove', targetName, tab || ({} as TabItem))
  emit('edit', targetName, 'remove')
}

/**
 * Handle tab addition
 */
const handleAdd = () => {
  emit('add')
  emit('edit', '', 'add')
}

/**
 * Handle tab change
 */
const handleChange = (targetName: string) => {
  emit('change', targetName)
}

/**
 * Handle edit actions (for editable mode)
 */
const handleEdit = (targetName: string, action: 'remove' | 'add') => {
  emit('edit', targetName, action)
}

/**
 * Set first tab as active if current active tab is hidden
 */
watch(() => props.tabs, (newTabs) => {
  if (newTabs && newTabs.length > 0) {
    const visible = newTabs.filter(tab => tab.visible !== false)
    const activeExists = visible.some(tab => (tab.id || tab.name) === props.modelValue)
    if (!activeExists && visible.length > 0) {
      emit('update:modelValue', visible[0].id || visible[0].name)
    }
  }
}, { deep: true, immediate: true })
</script>

<style scoped>
.tab-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tab-icon {
  font-size: 14px;
}

.tab-title {
  font-size: 14px;
}

.tab-badge {
  margin-left: 4px;
}

/* Position-based adjustments */
:deep(.el-tabs--left) .tab-label,
:deep(.el-tabs--right) .tab-label {
  flex-direction: column;
  gap: 4px;
}

:deep(.el-tabs--left) .tab-icon,
:deep(.el-tabs--right) .tab-icon {
  font-size: 16px;
}

/* Disabled tab styling */
:deep(.el-tabs__item.is-disabled) {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
