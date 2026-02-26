<!--
  BaseDetailPage Component

  A reusable detail page component that provides:
  - Section-based data display
  - Audit trail (created/updated info)
  - Edit/Back/Delete actions
  - Slot-based customization
  - Loading and error states

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

import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowLeft, ArrowDown } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/dateFormat'
import { camelToSnake, snakeToCamel } from '@/utils/case'
import { isPlainObject, isEmptyValue, resolveFieldValue } from '@/utils/fieldKey'
import RelatedObjectTable from './RelatedObjectTable.vue'
import FieldDisplay from './FieldDisplay.vue'
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

export interface DetailSection {
  /** Section identifier */
  name: string
  /** Section title */
  title: string
  /** Fields in this section */
  fields: DetailField[]
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
  /** Reverse relation fields to display (related objects) */
  reverseRelations?: ReverseRelationField[]
  /** Whether to show related objects inline */
  showRelatedObjects?: boolean
}

interface Emits {
  (e: 'edit'): void
  (e: 'delete'): void
  (e: 'back'): void
  (e: 'related-record-click', relationCode: string, record: any): void
  (e: 'related-record-edit', relationCode: string, record: any): void
  (e: 'related-refresh', relationCode: string): void
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
  showRelatedObjects: true
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

const collapsedSections = ref<Set<string>>(new Set())
const { t } = useI18n()

// ============================================================================
// Computed
// ============================================================================

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
  const actions: Array<{ label: string; type?: string; icon?: string; action: () => void }> = []

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

/**
 * Check if section is collapsed
 */
const isSectionCollapsed = (section: DetailSection) => {
  return section.collapsed || collapsedSections.value.has(section.name)
}

/**
 * Handle edit action
 */
const handleEdit = () => {
  emit('edit')
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

defineExpose({
  toggleSection,
  isSectionCollapsed
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
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <el-button
            v-if="showBack"
            :icon="ArrowLeft"
            link
            @click="handleBack"
          >
            {{ backText || $t('common.actions.back') }}
          </el-button>
          <h1 class="page-title">
            {{ title }}
          </h1>
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

      <!-- Detail Sections -->
      <div class="detail-sections">
        <template
          v-for="section in sections"
          :key="section.name"
        >
          <div :class="['detail-section', { 'is-collapsed': isSectionCollapsed(section) }]">
            <!-- Section Header -->
            <div
              v-if="section.title"
              class="section-header"
              @click="section.collapsible ? toggleSection(section.name) : null"
            >
              <div class="section-title">
                <el-icon
                  v-if="section.icon"
                  class="section-icon"
                >
                  <component :is="section.icon" />
                </el-icon>
                <span>{{ section.title }}</span>
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
                        <FieldDisplay
                          :field="field"
                          :value="getFieldValue(field)"
                        />
                      </div>
                    </div>
                  </el-col>
                </el-row>
              </template>
            </div>
          </div>
        </template>
      </div>

      <!-- Audit Info -->
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
            {{ formatDate(auditInfo?.createdAt) }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.labels.updatedBy')">
            {{ auditInfo?.updatedBy || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('common.labels.updatedAt')">
            {{ formatDate(auditInfo?.updatedAt) }}
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
.base-detail-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.loading-container {
  padding: 40px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.detail-content {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 16px 20px;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .page-title {
      margin: 0;
      font-size: 20px;
      font-weight: 500;
      color: #303133;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
  }

  .detail-sections {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .detail-section {
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    overflow: hidden;

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
      padding: 16px 20px;
      background-color: #f5f7fa;
      border-bottom: 1px solid #ebeef5;
      cursor: default;

      &:hover {
        background-color: #ecf5ff;
      }

      .section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 16px;
        font-weight: 500;
        color: #303133;

        .section-icon {
          font-size: 18px;
          color: #409eff;
        }
      }

      .collapse-icon {
        transition: transform 0.3s;
        color: #909399;
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
          font-size: 14px;
          color: #606266;
          line-height: 22px;
          flex-shrink: 0;
        }

        .field-value {
          flex: 1;
          font-size: 14px;
          color: #303133;
          line-height: 22px;
          word-break: break-all;
        }
      }
    }
  }

  .audit-info {
    margin-top: 20px;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    overflow: hidden;

    .audit-title {
      padding: 16px 20px;
      background-color: #f5f7fa;
      border-bottom: 1px solid #ebeef5;
      font-size: 16px;
      font-weight: 500;
      color: #303133;
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
    margin-top: 20px;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    overflow: hidden;

    .related-objects-header {
      padding: 16px 20px;
      background-color: #f5f7fa;
      border-bottom: 1px solid #ebeef5;

      .related-objects-title {
        margin: 0;
        font-size: 16px;
        font-weight: 500;
        color: #303133;
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
