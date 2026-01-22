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

import { computed } from 'vue'
import type { ElMessageBox } from 'element-plus'
import { formatDate } from '@/utils/dateFormat'

// ============================================================================
// Types
// ============================================================================

export interface DetailField {
  /** Field identifier */
  prop: string
  /** Field label */
  label: string
  /** Field type: text, date, number, currency, percent, tag, slot, link */
  type?: 'text' | 'date' | 'number' | 'currency' | 'percent' | 'tag' | 'slot' | 'link' | 'image'
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
}

interface Emits {
  (e: 'edit'): void
  (e: 'delete'): void
  (e: 'back'): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  auditInfo: null,
  showEdit: true,
  showDelete: true,
  showBack: true,
  editText: '编辑',
  deleteText: '删除',
  backText: '返回',
  deleteConfirmMessage: '确定要删除这条记录吗？',
  fieldSpan: 12,
  extraActions: () => []
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

const collapsedSections = ref<Set<string>>(new Set())

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
    actions.push({ label: props.editText, type: 'primary', action: () => emit('edit') })
  }

  props.extraActions.forEach(action => {
    actions.push(action)
  })

  if (props.showDelete) {
    actions.push({
      label: props.deleteText,
      type: 'danger',
      action: handleDelete
    })
  }

  return actions
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Get field value from data
 */
const getFieldValue = (field: DetailField) => {
  const value = props.data[field.prop]
  return value !== undefined && value !== null ? value : '-'
}

/**
 * Format field value for display
 */
const formatFieldValue = (field: DetailField) => {
  const value = props.data[field.prop]

  if (value === undefined || value === null) {
    return '-'
  }

  switch (field.type) {
    case 'date':
      return formatDate(value, field.dateFormat)

    case 'number':
      return field.precision !== undefined
        ? Number(value).toFixed(field.precision)
        : value

    case 'currency':
      const num = Number(value)
      const formatted = field.precision !== undefined
        ? num.toFixed(field.precision)
        : num.toFixed(2)
      return `${field.currency || '¥'}${formatted}`

    case 'percent':
      return `${Number(value).toFixed(field.precision || 2)}%`

    case 'tag':
      return value

    case 'link':
      return value

    case 'image':
      return value

    default:
      return value
  }
}

/**
 * Get tag type for value
 */
const getTagType = (field: DetailField) => {
  if (field.type !== 'tag') return undefined
  const value = props.data[field.prop]
  return field.tagType?.[value] || field.defaultTagType || 'info'
}

/**
 * Get link href
 */
const getLinkHref = (field: DetailField) => {
  if (field.type !== 'link' || !field.href) return undefined
  const value = props.data[field.prop]
  return field.href.replace('{value}', value)
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
  const confirmed = confirm(props.deleteConfirmMessage)
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
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <!-- Content -->
    <div v-else class="detail-content">
      <!-- Page Header -->
      <div class="page-header">
        <div class="header-left">
          <el-button
            v-if="showBack"
            :icon="ArrowLeft"
            link
            @click="handleBack"
          >
            {{ backText }}
          </el-button>
          <h1 class="page-title">{{ title }}</h1>
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
        <template v-for="section in sections" :key="section.name">
          <div :class="['detail-section', { 'is-collapsed': isSectionCollapsed(section) }]">
            <!-- Section Header -->
            <div
              v-if="section.title"
              class="section-header"
              @click="section.collapsible ? toggleSection(section.name) : null"
            >
              <div class="section-title">
                <el-icon v-if="section.icon" class="section-icon">
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
            <div v-show="!isSectionCollapsed(section)" class="section-content">
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
                    <div v-if="field.type === 'slot'" class="field-item">
                      <slot
                        :name="`field-${field.prop}`"
                        :field="field"
                        :data="data"
                        :value="getFieldValue(field)"
                      />
                    </div>

                    <!-- Image field -->
                    <div v-else-if="field.type === 'image'" class="field-item field-image">
                      <span class="field-label">{{ field.label }}</span>
                      <div class="field-value">
                        <el-image
                          :src="data[field.prop]"
                          fit="cover"
                          :preview-src-list="[data[field.prop]]"
                          class="detail-image"
                        >
                          <template #error>
                            <div class="image-error">
                              <el-icon><Picture /></el-icon>
                            </div>
                          </template>
                        </el-image>
                      </div>
                    </div>

                    <!-- Link field -->
                    <div v-else-if="field.type === 'link'" class="field-item">
                      <span class="field-label">{{ field.label }}</span>
                      <div class="field-value">
                        <el-link
                          :href="getLinkHref(field)"
                          target="_blank"
                          type="primary"
                        >
                          {{ formatFieldValue(field) }}
                        </el-link>
                      </div>
                    </div>

                    <!-- Tag field -->
                    <div v-else-if="field.type === 'tag'" class="field-item">
                      <span class="field-label">{{ field.label }}</span>
                      <div class="field-value">
                        <el-tag :type="getTagType(field)">
                          {{ formatFieldValue(field) }}
                        </el-tag>
                      </div>
                    </div>

                    <!-- Standard field -->
                    <div v-else class="field-item">
                      <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                      <span :class="['field-value', field.valueClass]">
                        {{ formatFieldValue(field) }}
                      </span>
                    </div>
                  </el-col>
                </el-row>
              </template>
            </div>
          </div>
        </template>
      </div>

      <!-- Audit Info -->
      <div v-if="hasAuditInfo" class="audit-info">
        <div class="audit-title">审计信息</div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="创建人">
            {{ auditInfo?.createdBy || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(auditInfo?.createdAt) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新人">
            {{ auditInfo?.updatedBy || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDate(auditInfo?.updatedAt) }}
          </el-descriptions-item>
        </el-descriptions>
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
  }
}
</style>
