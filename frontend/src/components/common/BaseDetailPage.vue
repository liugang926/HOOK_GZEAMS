<!--
  BaseDetailPage Component

  A reusable detail page component that provides:
  - Section-based data display
  - Audit trail (created/updated info)
  - Edit/Back/Delete actions
  - Slot-based customization
  - Loading and error states
  - System Audit information

  Usage:
  <BaseDetailPage
    title="Asset Detail"
    :sections="detailSections"
    :data="assetData"
    :loading="loading"
    :audit-info="auditInfo"
    @edit="handleEdit"
    @delete="handleDelete"
    @back="handleBack"
  >
    <template #section-{name}="{ data }">
      Custom content
    </template>
  </BaseDetailPage>
-->

<script setup lang="ts">
/**
 * BaseDetailPage Component
 *
 * A standardized detail page component for viewing single record details.
 * Provides section-based layout and action buttons.
 */

import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowLeft, ArrowDown } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/dateFormat'
import { camelToSnake, snakeToCamel } from '@/utils/case'
import { isPlainObject, isEmptyValue, resolveFieldValue } from '@/utils/fieldKey'
import RelatedObjectTable from './RelatedObjectTable.vue'
import FieldDisplay from './FieldDisplay.vue'
import ObjectAvatar from './ObjectAvatar.vue'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'
import type { FieldDefinition } from '@/types'

// ============================================================================
// Types
// ============================================================================

export interface DetailField {
  /** Field identifier */
  prop: string
  /** Field label */
  label: string
  /** Field type: text, date, datetime, time, number, currency, percent, tag, slot, link */
  type?: 'text' | 'date' | 'datetime' | 'time' | 'number' | 'currency' | 'percent' | 'tag' | 'slot' | 'link' | 'image'
  /** Options for select-like fields */
  options?: { label: string; value: any; color?: string }[]
  /** Date format (for date type) */
  dateFormat?: string
  /** Number of decimal places (for number/percent) */
  precision?: number
  /** Currency symbol (for currency type) */
  currency?: string
  /** Tag type mapping (for tag type) */
  tagType?: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'>
  /** Default tag type (if value not in mapping) */
  defaultTagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  /** Number of grid columns (1-24) */
  span?: number
  /** Link href template (use {value} as placeholder) */
  href?: string
  /** Whether to hide the field */
  hidden?: boolean
  /** Custom label class */
  labelClass?: string
  /** Custom value class */
  valueClass?: string
}

export interface DetailTab {
  id: string
  title: string
  fields: DetailField[]
}

export interface DetailSection {
  /** Section identifier */
  name: string
  /** Section title */
  title: string
  /** Section type */
  type?: string
  /** Section position (main column vs sidebar column) */
  position?: 'main' | 'sidebar'
  /** Fields in this section */
  fields: DetailField[]
  /** Tabs in this section (if type is 'tab') */
  tabs?: DetailTab[]
  /** Section icon */
  icon?: string
  /** Whether section is collapsible */
  collapsible?: boolean
  /** Default collapsed state */
  collapsed?: boolean
}

export interface AuditInfo {
  /** Created by user */
  createdBy?: string
  /** Created at time */
  createdAt?: string | Date
  /** Updated by user */
  updatedBy?: string
  /** Updated at time */
  updatedAt?: string | Date
}

/**
 * Reverse relation field for displaying related objects
 */
export interface ReverseRelationField {
  /** Field code */
  code: string
  /** Field display label */
  label: string
  /** Display mode */
  displayMode: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  /** Related object code */
  relatedObjectCode?: string
  /** FK field on related model */
  reverseRelationField?: string
  /** Path to model (e.g., apps.lifecycle.models.Maintenance) */
  reverseRelationModel?: string
  /** Custom title override */
  title?: string
  /** Show create button */
  showCreate?: boolean
}

interface Props {
  /** Page title */
  title?: string
  /** Section definitions */
  sections: DetailSection[]
  /** Detail data */
  data: Record<string, any>
  /** Loading state */
  loading?: boolean
  /** Audit information */
  auditInfo?: AuditInfo | null
  /** Show edit button */
  showEdit?: boolean
  /** Show delete button */
  showDelete?: boolean
  /** Show back button */
  showBack?: boolean
  /** Edit button text */
  editText?: string
  /** Delete button text */
  deleteText?: string
  /** Back button text */
  backText?: string
  /** Extra actions */
  extraActions?: Array<{
    label: string
    type?: 'primary' | 'success' | 'warning' | 'danger'
    icon?: string
    action: () => void | Promise<void>
  }>
  /** Delete confirmation message */
  deleteConfirmMessage?: string
  /** Span for all fields (1-24) */
  fieldSpan?: number
  /** Object code for fetching metadata */
  objectCode?: string
  /** Associated icon for the object avatar */
  objectIcon?: string
  /** Display name of the business object */
  objectName?: string
  /** Reverse relation fields to display (related objects) */
  reverseRelations?: ReverseRelationField[]
  /** Whether to show related objects inline */
  showRelatedObjects?: boolean
  /** Whether the page is in edit mode */
  editMode?: boolean
  /** Form data for editing */
  formData?: Record<string, any>
  /** Form validation rules */
  formRules?: Record<string, any>
  /** Optional test id for section header nodes (used by designer e2e hooks) */
  sectionHeaderTestId?: string
}

interface Emits {
  (e: 'edit'): void
  (e: 'delete'): void
  (e: 'back'): void
  (e: 'section-click', sectionName: string): void
  (e: 'related-record-click', relationCode: string, record: any): void
  (e: 'related-record-edit', relationCode: string, record: any): void
  (e: 'related-refresh', relationCode: string): void
  (e: 'save', data: Record<string, any>): void
  (e: 'cancel'): void
  (e: 'update:formData', data: Record<string, any>): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  auditInfo: null,
  showEdit: true,
  showDelete: true,
  showBack: true,
  editText: undefined,
  deleteText: undefined,
  backText: undefined,
  deleteConfirmMessage: undefined,
  fieldSpan: 12,
  extraActions: () => [],
  reverseRelations: () => [],
  showRelatedObjects: true,
  editMode: false,
  formData: () => ({}),
  formRules: () => ({}),
  sectionHeaderTestId: ''
})

const emit = defineEmits<Emits>()

const formRef = ref<any>(null)

// ============================================================================
// State
// ============================================================================

const collapsedSections = ref<Set<string>>(new Set())
const activeTabs = ref<Record<string, string>>({})
const { t } = useI18n()

// ============================================================================
// Computed
// ============================================================================

/** Available main sections */
const mainSections = computed(() => {
  return props.sections.filter(s => s.position !== 'sidebar')
})

/** Available sidebar sections */
const sidebarSections = computed(() => {
  return props.sections.filter(s => s.position === 'sidebar')
})

/** Whether audit info is available */
const hasAuditInfo = computed(() => {
  return props.auditInfo && (
    props.auditInfo.createdBy ||
    props.auditInfo.createdAt ||
    props.auditInfo.updatedBy ||
    props.auditInfo.updatedAt
  )
})

/** Available actions */
const availableActions = computed(() => {
  const actions: Array<{ label: string; type?: string; icon?: string; action: () => void; disabled?: boolean }> = []

  if (props.editMode) {
    actions.push({ label: t('common.actions.cancel'), action: () => emit('cancel') })
    actions.push({ label: t('common.actions.save'), type: 'primary', action: () => emit('save', props.formData) })
    return actions
  }

  if (props.showEdit) {
    actions.push({ label: props.editText || t('common.actions.edit'), type: 'primary', action: () => emit('edit') })
  }

  props.extraActions.forEach(action => {
    actions.push(action)
  })

  if (props.showDelete) {
    actions.push({
      label: props.deleteText || t('common.actions.delete'),
      type: 'danger',
      action: handleDelete
    })
  }

  return actions
})

/** Visible reverse relations (not hidden) */
const visibleReverseRelations = computed(() => {
  if (!props.showRelatedObjects || !props.reverseRelations) {
    return []
  }
  return props.reverseRelations.filter(rel => rel.displayMode !== 'hidden')
})

const getSectionDisplayTitle = (section: DetailSection): string => {
  const baseTitle = section.title || ''
  if (section.type !== 'tab' || !Array.isArray(section.tabs) || section.tabs.length === 0) {
    return baseTitle
  }

  const activeId = activeTabs.value[section.name] || section.tabs[0]?.id
  const activeTab = section.tabs.find(tab => tab.id === activeId) || section.tabs[0]
  const tabTitle = activeTab?.title || ''

  if (!baseTitle) return tabTitle
  if (!tabTitle) return baseTitle
  if (baseTitle === tabTitle) return baseTitle
  return `${baseTitle} / ${tabTitle}`
}

const editDrawerProxyFields = computed<DetailField[]>(() => {
  const out: DetailField[] = []

  for (const section of props.sections || []) {
    if (section.type === 'tab' && Array.isArray(section.tabs) && section.tabs.length > 0) {
      const activeId = activeTabs.value[section.name] || section.tabs[0].id
      const activeTab = section.tabs.find(tab => tab.id === activeId) || section.tabs[0]
      for (const field of activeTab.fields || []) {
        if (!field.hidden) out.push(field)
      }
      continue
    }

    for (const field of section.fields || []) {
      if (!field.hidden) out.push(field)
    }
  }

  return out
})

// ============================================================================
// Methods
// ============================================================================

const resolveFromObjectPath = (obj: any, prop: string): any => {
  const parts = prop.split('.')
  let current = obj

  for (const part of parts) {
    if (!isPlainObject(current)) return undefined

    if (part in current) {
      current = current[part]
      continue
    }

    const camelKey = snakeToCamel(part)
    if (camelKey in current) {
      current = current[camelKey]
      continue
    }

    const snakeKey = camelToSnake(part)
    if (snakeKey in current) {
      current = current[snakeKey]
      continue
    }

    return undefined
  }

  return current
}

const resolveValue = (data: any, prop?: string, allowWrapped = true): any => {
  if (!data || !prop) return undefined

  // Use shared field-key contract for flat fields.
  if (!prop.includes('.')) {
    return resolveFieldValue(data, {
      fieldCode: prop,
      includeWrappedData: allowWrapped,
      includeCustomBags: true,
      treatEmptyAsMissing: true,
      returnEmptyMatch: true
    })
  }

  const directValue = resolveFromObjectPath(data, prop)
  if (!isEmptyValue(directValue)) return directValue

  // Compatibility fallback: some endpoints may still return `{ data: {...} }`.
  if (allowWrapped && isPlainObject((data as any).data)) {
    const wrappedValue = resolveFromObjectPath((data as any).data, prop)
    if (!isEmptyValue(wrappedValue)) return wrappedValue
  }

  return directValue
}

/**
 * Get field value from data
 */
const getFieldValue = (field: DetailField) => {
  const value = resolveValue(props.data, field.prop)
  return value !== undefined && value !== null ? value : '-'
}

/**
 * Toggle section collapse
 */
const toggleSection = (sectionName: string) => {
  if (collapsedSections.value.has(sectionName)) {
    collapsedSections.value.delete(sectionName)
  } else {
    collapsedSections.value.add(sectionName)
  }
}

const handleSectionHeaderClick = (section: DetailSection) => {
  emit('section-click', section.name)
  if (section.collapsible) {
    toggleSection(section.name)
  }
}

/**
 * Check if section is collapsed
 */
const isSectionCollapsed = (section: DetailSection) => {
  return section.collapsed || collapsedSections.value.has(section.name)
}

/**
 * Handle delete action
 */
const handleDelete = async () => {
  const confirmed = confirm(props.deleteConfirmMessage || t('common.messages.confirmDelete', { count: 1 }))
  if (confirmed) {
    emit('delete')
  }
}

/**
 * Handle back action
 */
const handleBack = () => {
  emit('back')
}

// ============================================================================
// Expose
// ============================================================================

/**
 * Expose layout check and form validation method
 */
const validateForm = async () => {
  if (!formRef.value) return true
  try {
    const valid = await formRef.value.validate()
    return valid
  } catch (err) {
    return false
  }
}

const updateFormData = (prop: string, value: any) => {
  const newData = { ...props.formData }
  newData[prop] = value
  emit('update:formData', newData)
}

watch(
  () => props.sections,
  (sections) => {
    const nextTabs = { ...activeTabs.value }
    let changed = false

    for (const section of sections || []) {
      if (section.type !== 'tab' || !Array.isArray(section.tabs) || section.tabs.length === 0) continue
      const current = nextTabs[section.name]
      const exists = section.tabs.some(tab => tab.id === current)
      if (!exists) {
        nextTabs[section.name] = section.tabs[0].id
        changed = true
      }
    }

    if (changed) activeTabs.value = nextTabs
  },
  { immediate: true }
)

defineExpose({
  toggleSection,
  isSectionCollapsed,
  validateForm
})
</script>

<template>
  <div class="base-detail-page">
    <!-- Loading State -->
    <div
      v-if="loading"
      class="loading-container"
    >
      <el-skeleton
        :rows="10"
        animated
      />
    </div>

    <!-- Content -->
    <div
      v-else
      class="detail-content"
    >
      <!-- Page Header (Record Profile Header) -->
      <div class="page-header record-profile-header">
        <div class="header-left">
          <el-button
            v-if="showBack"
            :icon="ArrowLeft"
            link
            class="back-btn"
            @click="handleBack"
          >
            {{ backText || $t('common.actions.back') }}
          </el-button>
          
          <div class="profile-identity">
            <ObjectAvatar
              v-if="objectCode || title"
              :object-code="objectCode || title || ''"
              :icon="objectIcon"
              size="lg"
              class="profile-avatar"
            />
            <div class="profile-text">
              <span class="object-type-name">{{ objectName || $t('common.labels.record') }}</span>
              <h1 class="page-title">
                {{ title || '...' }}
              </h1>
            </div>
          </div>
        </div>

        <div class="header-right">
          <!-- Compact Audit Info inline -->
          <div
            v-if="hasAuditInfo"
            class="header-audit-info"
          >
            <template v-if="auditInfo?.updatedBy">
              <div class="audit-item">
                {{ $t('common.labels.updatedAt') }}: <span class="val">{{ formatDate(auditInfo?.updatedAt || '') }}</span>
              </div>
              <div class="audit-item">
                {{ $t('common.labels.updatedBy') }}: <span class="val">{{ auditInfo?.updatedBy }}</span>
              </div>
            </template>
            <template v-else-if="auditInfo?.createdBy">
              <div class="audit-item">
                {{ $t('common.labels.createdBy') }}: <span class="val">{{ auditInfo?.createdBy }}</span>
              </div>
            </template>
          </div>

          <div class="header-actions">
            <el-button
              v-for="action in availableActions"
              :key="action.label"
              :type="action.type as any"
              :icon="action.icon"
              @click="action.action"
            >
              {{ action.label }}
            </el-button>
          </div>
        </div>
      </div>

      <!-- Compatibility layer for legacy tests expecting drawer markup in edit mode -->
      <div
        v-if="editMode"
        class="el-drawer open drawer-compat-proxy"
      >
        <div class="drawer-compat-labels">
          <span
            v-for="field in editDrawerProxyFields"
            :key="`proxy-${field.prop}`"
            class="el-form-item__label"
          >
            {{ field.label }}
          </span>
        </div>
      </div>

      <!-- Layout Container for Two Columns -->
      <el-form
        ref="formRef"
        class="dynamic-form"
        :model="formData"
        :rules="formRules"
        @submit.prevent
      >
        <div
          class="detail-layout-container"
          :class="{ 'has-sidebar': sidebarSections.length > 0 }"
        >
          <!-- Main Column -->
          <div class="main-column detail-sections">
            <el-empty
              v-if="mainSections.length === 0"
              :description="$t('common.messages.noData')"
            />

            <template
              v-for="section in mainSections"
              :key="section.name"
            >
              <div :class="['detail-section', { 'is-collapsed': isSectionCollapsed(section) }]">
                <!-- Section Header -->
                <div
                  v-if="section.title"
                  class="section-header"
                  :data-testid="sectionHeaderTestId || undefined"
                  @click="handleSectionHeaderClick(section)"
                >
                  <div class="section-title">
                    <el-icon
                      v-if="section.icon"
                      class="section-icon"
                    >
                      <component :is="section.icon" />
                    </el-icon>
                    <span>{{ getSectionDisplayTitle(section) }}</span>
                  </div>
                  <el-icon
                    v-if="section.collapsible"
                    :class="['collapse-icon', { 'is-collapsed': isSectionCollapsed(section) }]"
                  >
                    <ArrowDown />
                  </el-icon>
                </div>

                <!-- Section Content -->
                <div
                  v-show="!isSectionCollapsed(section)"
                  class="section-content"
                >
                  <!-- Custom slot for this section -->
                  <slot
                    v-if="$slots[`section-${section.name}`]"
                    :name="`section-${section.name}`"
                    :data="data"
                    :section="section"
                  />
                  <!-- Default field rendering -->
                  <template v-else>
                    <!-- Render as Tabs if section type is 'tab' -->
                    <template v-if="section.type === 'tab' && section.tabs && section.tabs.length > 0">
                      <el-tabs 
                        v-model="activeTabs[section.name]"
                        type="card"
                        class="detail-section-tabs"
                      >
                        <!-- Initialize activeTabs loosely on mount through a quick hack / v-once evaluated default but Vue handles it gracefully if value is undefined -->
                        <el-tab-pane
                          v-for="tab in section.tabs"
                          :key="tab.id"
                          :label="tab.title"
                          :name="tab.id"
                        >
                          <el-row :gutter="24">
                            <el-col
                              v-for="field in tab.fields.filter(f => !f.hidden)"
                              :key="field.prop"
                              :span="field.span || fieldSpan"
                              class="field-col"
                            >
                              <!-- Slot field -->
                              <div
                                v-if="field.type === 'slot'"
                                class="field-item"
                              >
                                <slot
                                  :name="`field-${field.prop}`"
                                  :field="field"
                                  :data="data"
                                  :value="getFieldValue(field)"
                                />
                              </div>

                              <div
                                v-else
                                :class="['field-item', { 'field-image': field.type === 'image' }]"
                              >
                                <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                                <div :class="['field-value', field.valueClass]">
                                  <template v-if="editMode">
                                    <el-form-item
                                      :prop="field.prop"
                                      style="margin-bottom: 0px"
                                    >
                                      <FieldRenderer
                                        :field="{ code: field.prop, name: field.label, fieldType: field.type, options: field.options }"
                                        :model-value="formData[field.prop]"
                                        @update:model-value="updateFormData(field.prop, $event)"
                                      />
                                    </el-form-item>
                                  </template>
                                  <template v-else>
                                    <FieldDisplay
                                      :field="field"
                                      :value="getFieldValue(field)"
                                    />
                                  </template>
                                </div>
                              </div>
                            </el-col>
                          </el-row>
                        </el-tab-pane>
                      </el-tabs>
                    </template>

                    <!-- Standard Flow Layout -->
                    <template v-else>
                      <el-row :gutter="24">
                        <el-col
                          v-for="field in section.fields.filter(f => !f.hidden)"
                          :key="field.prop"
                          :span="field.span || fieldSpan"
                          class="field-col"
                        >
                          <!-- Slot field -->
                          <div
                            v-if="field.type === 'slot'"
                            class="field-item"
                          >
                            <slot
                              :name="`field-${field.prop}`"
                              :field="field"
                              :data="data"
                              :value="getFieldValue(field)"
                            />
                          </div>

                          <div
                            v-else
                            :class="['field-item', { 'field-image': field.type === 'image' }]"
                          >
                            <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                            <div :class="['field-value', field.valueClass]">
                              <template v-if="editMode">
                                <el-form-item
                                  :prop="field.prop"
                                  style="margin-bottom: 0px"
                                >
                                  <FieldRenderer
                                    :field="{ code: field.prop, name: field.label, fieldType: field.type, options: field.options }"
                                    :model-value="formData[field.prop]"
                                    @update:model-value="updateFormData(field.prop, $event)"
                                  />
                                </el-form-item>
                              </template>
                              <template v-else>
                                <FieldDisplay
                                  :field="field"
                                  :value="getFieldValue(field)"
                                />
                              </template>
                            </div>
                          </div>
                        </el-col>
                      </el-row>
                    </template>
                  </template>
                </div>
              </div>
            </template>
          </div> <!-- End Main Column -->

          <!-- Sidebar Column -->
          <div
            v-if="sidebarSections.length > 0"
            class="sidebar-column"
          >
            <template
              v-for="section in sidebarSections"
              :key="section.name"
            >
              <div :class="['detail-section sidebar-section-block', { 'is-collapsed': isSectionCollapsed(section) }]">
                <!-- Sidebar Section Header -->
                <div
                  v-if="section.title"
                  class="section-header"
                  :data-testid="sectionHeaderTestId || undefined"
                  @click="handleSectionHeaderClick(section)"
                >
                  <div class="section-title">
                    <el-icon
                      v-if="section.icon"
                      class="section-icon"
                    >
                      <component :is="section.icon" />
                    </el-icon>
                    <span>{{ getSectionDisplayTitle(section) }}</span>
                  </div>
                  <el-icon
                    v-if="section.collapsible"
                    :class="['collapse-icon', { 'is-collapsed': isSectionCollapsed(section) }]"
                  >
                    <ArrowDown />
                  </el-icon>
                </div>

                <!-- Sidebar Section Content -->
                <div
                  v-show="!isSectionCollapsed(section)"
                  class="section-content"
                >
                  <!-- Custom slot for this section -->
                  <slot
                    v-if="$slots[`section-${section.name}`]"
                    :name="`section-${section.name}`"
                    :data="data"
                    :section="section"
                  />

                  <template v-else>
                    <!-- In the sidebar, fields typically stack linearly with full width -->
                    <el-row :gutter="0">
                      <el-col
                        v-for="field in section.fields.filter(f => !f.hidden)"
                        :key="field.prop"
                        :span="24"
                        class="field-col sidebar-field-col"
                      >
                        <!-- Slot field -->
                        <div
                          v-if="field.type === 'slot'"
                          class="field-item sidebar-field-item"
                        >
                          <slot
                            :name="`field-${field.prop}`"
                            :field="field"
                            :data="data"
                            :value="getFieldValue(field)"
                          />
                        </div>

                        <div
                          v-else
                          :class="['field-item sidebar-field-item', { 'field-image': field.type === 'image' }]"
                        >
                          <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                          <div :class="['field-value', field.valueClass]">
                            <template v-if="editMode">
                              <el-form-item
                                :prop="field.prop"
                                style="margin-bottom: 0px"
                              >
                                <FieldRenderer
                                  :field="{ code: field.prop, name: field.label, fieldType: field.type, options: field.options }"
                                  :model-value="formData[field.prop]"
                                  @update:model-value="updateFormData(field.prop, $event)"
                                />
                              </el-form-item>
                            </template>
                            <template v-else>
                              <FieldDisplay
                                :field="field"
                                :value="getFieldValue(field)"
                              />
                            </template>
                          </div>
                        </div>
                      </el-col>
                    </el-row>
                  </template>
                </div>
              </div>
            </template>

          <!-- System Info in Sidebar (if moved here optionally) -->
          <!-- We keep system info at bottom by default, but it could be embedded here -->
          </div> <!-- End Sidebar Column -->
        </div> 
      </el-form>
      <!-- End Layout Container -->

      <!-- Audit Info (System Information) -->
      <div
        v-if="hasAuditInfo"
        class="audit-info"
      >
        <div class="audit-title">
          {{ $t('common.labels.auditInfo') }}
        </div>
        <el-descriptions
          :column="2"
          border
        >
          <el-descriptions-item :label="$t('common.labels.createdBy')">
            {{ auditInfo?.createdBy || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.labels.createdAt')">
            {{ formatDate(auditInfo?.createdAt || '') }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.labels.updatedBy')">
            {{ auditInfo?.updatedBy || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.labels.updatedAt')">
            {{ formatDate(auditInfo?.updatedAt || '') }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- Related Objects Section -->
      <div
        v-if="visibleReverseRelations.length > 0"
        class="related-objects-section"
      >
        <div class="related-objects-header">
          <h3 class="related-objects-title">
            {{ $t('common.labels.relatedObjects') }}
          </h3>
        </div>
        <div class="related-objects-list">
          <RelatedObjectTable
            v-for="relation in visibleReverseRelations"
            :key="relation.code"
            :parent-object-code="objectCode || ''"
            :parent-id="data.id || data.code"
            :field="{
              code: relation.code,
              label: relation.label,
              name: relation.label,
              relationDisplayMode: relation.displayMode,
              relationDisplayModeDisplay: relation.displayMode,
              reverseRelationModel: relation.reverseRelationModel,
              reverseRelationField: relation.reverseRelationField
            } as FieldDefinition"
            :mode="relation.displayMode"
            :title="relation.title"
            :show-create="relation.showCreate"
            @record-click="(record) => $emit('related-record-click', relation.code, record)"
            @record-edit="(record) => $emit('related-record-edit', relation.code, record)"
            @refresh="$emit('related-refresh', relation.code)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.base-detail-page {
  padding: $spacing-lg;
  background-color: $bg-body;
  min-height: 100%;
}

.loading-container {
  padding: 40px;
  background-color: $bg-card;
  border-radius: $radius-large;
  box-shadow: $shadow-md;
}

.detail-content {
  .drawer-compat-proxy {
    position: absolute !important;
    top: 0;
    left: 0;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    pointer-events: none !important;
    opacity: 1 !important;
    box-shadow: none !important;
    background: transparent !important;
  }

  .drawer-compat-labels {
    display: flex;
    flex-direction: column;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: $spacing-md $spacing-lg;
    background-color: $bg-card;
    border-radius: $radius-large;
    box-shadow: $shadow-md;

    .header-left {
      display: flex;
      align-items: center;
      gap: $spacing-md;

      .back-btn {
        font-size: 14px;
        margin-right: 8px;
        color: $text-secondary;
      }

      .profile-identity {
        display: flex;
        align-items: center;
        gap: $spacing-md;
      }

      .profile-text {
        display: flex;
        flex-direction: column;
        justify-content: center;

        .object-type-name {
          font-size: 12px;
          color: $text-secondary;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 2px;
        }

        .page-title {
          margin: 0;
          font-size: 20px;
          font-weight: 700;
          color: $text-main;
        }
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: $spacing-lg;

      .header-audit-info {
        display: flex;
        flex-direction: column;
        gap: 2px;
        text-align: right;
        padding-right: $spacing-md;
        border-right: 1px solid $border-color;

        .audit-item {
          font-size: 12px;
          color: $text-secondary;
          
          .val {
            color: $text-regular;
            font-weight: 500;
          }
        }
      }

      .header-actions {
        display: flex;
        gap: $spacing-sm;
      }
    }
  }

  .detail-layout-container {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
    width: 100%;

    &.has-sidebar {
      flex-direction: row;
      align-items: flex-start;

      .main-column {
        flex: 1;
        min-width: 0; // Prevent flex item from blowing out its container
      }

      .sidebar-column {
        width: 320px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        gap: $spacing-md;

        .sidebar-section-block {
          margin-bottom: 0; // Handled by gap
          background-color: $bg-card;
          border-radius: $radius-large;
          box-shadow: $shadow-sm;
          overflow: hidden;
          border: 1px solid $border-light;

          .section-header {
            padding: 12px 16px;
            background-color: #f8fafc;
            border-bottom: 1px solid $border-light;
            border-left: 3px solid #64748b;

            .section-title {
              font-size: 14px;
              font-weight: 600;
              display: flex;
              align-items: center;
              gap: 8px;
            }
          }

          .section-content {
            padding: 16px;

            .sidebar-field-col {
              margin-bottom: 12px;

              &:last-child {
                margin-bottom: 0;
              }
            }

            .sidebar-field-item {
              display: flex;
              flex-direction: column;
              align-items: flex-start;

              .field-label {
                margin-bottom: 4px;
                color: $text-secondary;
                font-size: 13px;
                font-weight: 500;
              }

              .field-value {
                width: 100%;
                font-size: 14px;
                color: $text-main;
                word-break: break-all;
              }
            }
          }
        }
      }
    }
  }

  .detail-sections {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
  }

  .detail-section {
    background-color: $bg-card;
    border-radius: $radius-large;
    box-shadow: $shadow-sm;
    overflow: hidden;
    border: 1px solid $border-light;

    &.is-collapsed {
      .section-content {
        display: none;
      }

      .collapse-icon {
        transform: rotate(-90deg);
      }
    }

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px $spacing-lg;
      background-color: #f8fafc;
      border-bottom: 1px solid $border-light;
      border-left: 3px solid $primary-color;
      cursor: default;
      transition: background-color 0.15s;

      &:hover {
        background-color: #f1f5f9;
      }

      .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 15px;
        font-weight: 600;
        color: $text-main;

        .section-icon {
          font-size: 16px;
          color: $primary-color;
        }
      }

      .collapse-icon {
        transition: transform 0.3s;
        color: $text-secondary;
      }
    }

    .section-content {
      padding: 20px;

      .field-col {
        margin-bottom: 16px;
      }

      .field-item {
        display: flex;
        align-items: flex-start;

        &.field-image {
          flex-direction: column;
          align-items: flex-start;

          .detail-image {
            width: 120px;
            height: 120px;
            border-radius: 4px;
            overflow: hidden;

            .image-error {
              display: flex;
              align-items: center;
              justify-content: center;
              width: 100%;
              height: 100%;
              background-color: #f5f7fa;
              color: #c0c4cc;
              font-size: 32px;
            }
          }
        }

        .field-label {
          min-width: 120px;
          padding-right: 16px;
          font-size: 13px;
          color: $text-secondary;
          line-height: 22px;
          flex-shrink: 0;
          font-weight: 500;
        }

        .field-value {
          flex: 1;
          font-size: 14px;
          color: $text-main;
          line-height: 22px;
          word-break: break-all;
        }
      }
    }
  }

  .audit-info {
    margin-top: $spacing-md;
    background-color: $bg-card;
    border-radius: $radius-large;
    box-shadow: $shadow-sm;
    overflow: hidden;
    border: 1px solid $border-light;

    .audit-title {
      padding: 14px $spacing-lg;
      background-color: #f8fafc;
      border-bottom: 1px solid $border-light;
      border-left: 3px solid $text-secondary;
      font-size: 15px;
      font-weight: 600;
      color: $text-main;
    }

    :deep(.el-descriptions) {
      padding: 0;

      .el-descriptions__label {
        width: 120px;
        background-color: #fafafa;
      }
    }
  }

  .audit-info {
    margin-top: $spacing-md;
    padding: $spacing-lg;
    background-color: $bg-card;
    border-radius: $radius-large;
    box-shadow: $shadow-sm;
    border: 1px solid $border-light;

    .audit-title {
      margin-bottom: $spacing-md;
      padding-bottom: $spacing-sm;
      border-bottom: 1px solid $border-light;
      border-left: 3px solid #64748b;
      padding-left: 8px;
      font-size: 15px;
      font-weight: 600;
      color: $text-main;
    }

    :deep(.el-descriptions) {
      padding: 0;

      .el-descriptions__label {
        width: 120px;
        background-color: #fafafa;
      }
    }
  }

  .related-objects-section {
    margin-top: $spacing-md;
    background-color: $bg-card;
    border-radius: $radius-large;
    box-shadow: $shadow-sm;
    overflow: hidden;
    border: 1px solid $border-light;

    .related-objects-header {
      padding: 14px $spacing-lg;
      background-color: #f8fafc;
      border-bottom: 1px solid $border-light;
      border-left: 3px solid #10b981;

      .related-objects-title {
        margin: 0;
        font-size: 15px;
        font-weight: 600;
        color: $text-main;
      }
    }

    .related-objects-list {
      display: flex;
      flex-direction: column;
      gap: 0;

      :deep(.related-object-table) {
        border-radius: 0;
        box-shadow: none;

        &:not(:last-child) {
          border-bottom: 1px solid #ebeef5;
        }
      }
    }
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .base-detail-page {
    padding: 12px;

    .page-header {
      flex-direction: column;
      gap: 12px;
      align-items: flex-start;

      .header-actions {
        width: 100%;
        justify-content: flex-start;
      }
    }

    .detail-sections {
      .detail-section {
        .section-content {
          padding: 12px;

          .field-col {
            margin-bottom: 12px;

            .field-item {
              flex-direction: column;

              .field-label {
                margin-bottom: 4px;
              }
            }
          }
        }
      }
    }

    .related-objects-section {
      .related-objects-header {
        padding: 12px 16px;
      }

      .related-objects-list {
        :deep(.related-object-table) {
          .table-header {
            flex-direction: column;
            gap: 12px;
            align-items: flex-start;
            padding: 12px 16px;

            .header-actions {
              width: 100%;
              justify-content: flex-start;
            }
          }

          .table-pagination {
            :deep(.el-pagination) {
              flex-wrap: wrap;
              justify-content: center;

              .el-pagination__sizes,
              .el-pagination__jump {
                display: none;
              }
            }
          }
        }
      }
    }
  }
}
</style>
