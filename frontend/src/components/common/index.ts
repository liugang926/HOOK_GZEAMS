/**
 * Common Components Index
 *
 * Centralized exports for all common/shared components.
 * These components follow the PRD specifications found in:
 * - docs/plans/common_base_features/tab_configuration.md
 * - docs/plans/common_base_features/section_block_layout.md
 * - docs/plans/common_base_features/list_column_configuration.md
 */

// Layout Components
export { default as ColumnManager } from './ColumnManager.vue'
export { default as DynamicTabs } from './DynamicTabs.vue'
export { default as SectionBlock } from './SectionBlock.vue'

// Page Components
export { default as BaseListPage } from './BaseListPage.vue'
export { default as BaseDetailPage } from './BaseDetailPage.vue'
export { default as DynamicDetailPage } from './DynamicDetailPage.vue'
export { default as RelatedObjectTable } from './RelatedObjectTable.vue'

// UI Components
export { default as BaseForm } from './BaseForm.vue'
export { default as BaseTable } from './BaseTable.vue'

// Picker Components
export { default as UserPicker } from './UserPicker.vue'
export { default as UserSelector } from './UserSelector.vue'
export { default as DeptPicker } from './DeptPicker.vue'
export { default as RoleSelector } from './RoleSelector.vue'

// Dynamic Components
export { default as FieldRenderer } from './FieldRenderer.vue'
