<!--
  DynamicDetailPage Component

  A metadata-driven detail page component that:
  - Fetches field definitions with context filtering
  - Separates editable fields from reverse relations
  - Dynamically generates sections from metadata
  - Displays related objects in inline or tab mode

  Reference: docs/plans/2025-02-03-unified-field-display-design.md
-->
<script setup lang="ts">
/**
 * DynamicDetailPage Component
 *
 * A fully metadata-driven detail page that fetches field definitions
 * and generates the UI dynamically. Supports both detail context fields
 * and reverse relation display.
 */

import { ref, computed, watch, onMounted, useSlots } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import BaseDetailPage, {
  type DetailSection,
  type DetailField,
  type AuditInfo,
  type ReverseRelationField
} from './BaseDetailPage.vue'
import { useFieldMetadata } from '@/composables/useFieldMetadata'
import type { FieldDefinition } from '@/types'
import request from '@/utils/request'
import { snakeToCamel } from '@/utils/case'
import { resolveFieldValue } from '@/utils/fieldKey'
import { createObjectClient } from '@/api/dynamic'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import { orderFieldsWithSchema } from '@/platform/layout/unifiedFieldOrder'
import { projectUnifiedDetailSectionsFromLayout, shouldSkipUnifiedDetailField } from '@/platform/layout/unifiedDetailSections'
import { createModePolicyForContext } from '@/platform/layout/layoutRenderModel'
import { toUnifiedDetailField, buildRequiredFormRules } from '@/platform/layout/unifiedDetailField'
import { compileLayoutSchema } from '@/platform/layout/layoutCompiler'

const { t } = useI18n()
const slots = useSlots()

const isDetailDebugEnabled = (() => {
  if (!(import.meta as any).env?.DEV || typeof window === 'undefined') return false
  return window.localStorage.getItem('detail_debug') === '1'
})()

function debugDetailLog(event: string, payload: Record<string, any>) {
  if (!isDetailDebugEnabled) return
  console.info(`[detail-debug] ${event}`, payload)
}

// ============================================================================
// Types
// ============================================================================

export interface DynamicDetailPageProps {
  /** Business object code (e.g., 'Asset', 'Maintenance') */
  objectCode: string
  /** Record ID (from route params if not provided) */
  recordId?: string
  /** API function to fetch record detail */
  fetchRecord?: (id: string) => Promise<any>
  /** Custom title override */
  title?: string
  /** Show edit button */
  showEdit?: boolean
  /** Show delete button */
  showDelete?: boolean
  /** Custom edit route */
  editRoute?: string
  /** Custom back route */
  backRoute?: string
  /** Object display name */
  objectName?: string
  /** Object icon */
  objectIcon?: string
  /** Extra actions */
  extraActions?: Array<{
    label: string
    type?: 'primary' | 'success' | 'warning' | 'danger'
    icon?: string
    action: () => void | Promise<void>
  }>
}

interface Emits {
  (e: 'edit', record: any): void
  (e: 'delete', record: any): void
  (e: 'back'): void
  (e: 'loaded', record: any): void
  (e: 'related-record-click', relationCode: string, record: any): void
  (e: 'related-record-edit', relationCode: string, record: any): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<DynamicDetailPageProps>(), {
  showEdit: true,
  showDelete: true
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

const route = useRoute()
const loading = ref(false)
const recordData = ref<any>({})
const metadataSourceContext = ref<'detail' | 'form'>('detail')
const runtimeLayoutSections = ref<any[] | null>(null)
const runtimeEditableFields = ref<FieldDefinition[] | null>(null)
const runtimeReverseRelationFields = ref<FieldDefinition[] | null>(null)

// Use field metadata composable
const {
  editableFields,
  loading: metadataLoading,
  fetchFields,
  getRelationsByMode
} = useFieldMetadata(props.objectCode)

// API Client for updates
const apiClient = computed(() => createObjectClient(props.objectCode))

// Editing State
const isEditing = ref(false)
const formData = ref<Record<string, any>>({})
const formRules = ref<Record<string, any>>({})
const submitting = ref(false)
const baseDetailRef = ref<any>(null)

// ============================================================================
// Computed
// ============================================================================

/** Get record ID from props or route params */
const recordId = computed(() => props.recordId || route.params.id as string)

/** Page title */
const pageTitle = computed(() => {
  if (props.title) return props.title
  const sourceFields =
    (runtimeEditableFields.value && runtimeEditableFields.value.length > 0
      ? runtimeEditableFields.value
      : editableFields.value) as FieldDefinition[]
  const nameField = sourceFields.find((f: any) => f.isIdentifier || f.is_identifier || f.code === 'name')
  if (!nameField?.code) return t('common.detailPage.title')
  const resolvedTitle = resolveFieldValue(recordData.value, {
    fieldCode: nameField.code,
    includeWrappedData: true,
    includeCustomBags: true,
    treatEmptyAsMissing: true,
    returnEmptyMatch: true
  })
  if (resolvedTitle !== undefined && resolvedTitle !== null && String(resolvedTitle).trim()) {
    return String(resolvedTitle)
  }
  return t('common.detailPage.title')
})

/** Audit information */
const auditInfo = computed<AuditInfo>(() => ({
  createdBy:
    recordData.value.createdBy?.username ||
    recordData.value.createdBy?.name ||
    recordData.value.createdBy ||
    recordData.value.created_by?.username ||
    recordData.value.created_by?.name ||
    recordData.value.created_by,
  createdAt: recordData.value.createdAt || recordData.value.created_at,
  updatedBy:
    recordData.value.updatedBy?.username ||
    recordData.value.updatedBy?.name ||
    recordData.value.updatedBy ||
    recordData.value.updated_by?.username ||
    recordData.value.updated_by?.name ||
    recordData.value.updated_by,
  updatedAt: recordData.value.updatedAt || recordData.value.updated_at
}))

/** Dynamically generate Form Rules based on field attributes */
const generateFormRules = () => {
  const sourceFields = (runtimeEditableFields.value && runtimeEditableFields.value.length > 0
    ? runtimeEditableFields.value
    : editableFields.value) as FieldDefinition[]
  formRules.value = buildRequiredFormRules(sourceFields as any[])
}

const effectiveAuditInfo = computed<AuditInfo | null>(() => {
  // Single source of truth: audit info is always rendered in dedicated block,
  // never mixed into content sections.
  return auditInfo.value
})

function normalizeRecordPayload(payload: any): Record<string, any> {
  if (!payload || typeof payload !== 'object') return {}
  if (
    'success' in payload &&
    'data' in payload &&
    payload.data &&
    typeof payload.data === 'object'
  ) {
    return payload.data
  }
  return payload
}

/** Convert editable fields to detail sections */
const detailSections = computed<DetailSection[]>(() => {
  const sourceFields =
    (runtimeEditableFields.value && runtimeEditableFields.value.length > 0
      ? runtimeEditableFields.value
      : editableFields.value) as FieldDefinition[]

  if (runtimeLayoutSections.value?.length) {
    const runtimeSections = buildSectionsFromRuntimeLayout(
      runtimeLayoutSections.value,
      sourceFields,
      { strictVisibility: false }
    )
    // Respect runtime layout as single source of truth even when
    // visibility policy projects to zero visible fields.
    return runtimeSections
  }

  const sections: DetailSection[] = []
  const fieldGroups = groupFieldsBySection(sourceFields)

  for (const [sectionName, fields] of Object.entries(fieldGroups)) {
    if (fields.length === 0) continue

    sections.push({
      name: sectionName,
      title: getSectionTitle(sectionName),
      icon: getSectionIcon(sectionName),
      collapsible: sectionName !== 'basic',
      collapsed: sectionName === 'images' || sectionName === 'attachments',
      fields: fields.map(f => fieldToDetailField(f))
    })
  }

  return sections
})

/** Convert reverse relations to BaseDetailPage format */
const visibleReverseRelations = computed<ReverseRelationField[]>(() => {
  if (runtimeReverseRelationFields.value?.length) {
    return runtimeReverseRelationFields.value.map((rel: any) => ({
      code: rel.code,
      label: rel.label || rel.name,
      displayMode: rel.relationDisplayMode || rel.relation_display_mode || 'inline_readonly',
      relatedObjectCode: extractObjectCode(rel),
      reverseRelationField: rel.reverseRelationField || rel.reverse_relation_field,
      reverseRelationModel: rel.reverseRelationModel || rel.reverse_relation_model,
      title: rel.label || rel.name,
      showCreate: (rel.relationDisplayMode || rel.relation_display_mode) === 'inline_editable',
      position: rel.position
    }))
  }

  const inlineRelations = getRelationsByMode('inline_editable')
  const readonlyRelations = getRelationsByMode('inline_readonly')
  const timelineRelations = getRelationsByMode('timeline')

  return [...inlineRelations, ...readonlyRelations, ...timelineRelations].map(rel => ({
    code: rel.code,
    label: rel.label || rel.name,
    displayMode: rel.relationDisplayMode || rel.relation_display_mode || 'inline_readonly',
    relatedObjectCode: extractObjectCode(rel),
    reverseRelationField: rel.reverseRelationField || rel.reverse_relation_field,
    reverseRelationModel: rel.reverseRelationModel || rel.reverse_relation_model,
    title: rel.label || rel.name,
    showCreate: (rel.relationDisplayMode || rel.relation_display_mode) === 'inline_editable',
    position: rel.position
  }))
})

const slottedFields = computed(() => {
  return editableFields.value.filter((field) => !!slots[`field-${field.code}`])
})

const slottedSections = computed(() => {
  return detailSections.value.filter((section) => !!slots[`section-${section.name}`])
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Group fields by their section configuration
 */
function groupFieldsBySection(fields: FieldDefinition[]): Record<string, FieldDefinition[]> {
  const groups: Record<string, FieldDefinition[]> = {}

  for (const field of fields) {
    if (shouldSkipField(field)) continue

    const sectionName = (field as any).sectionName || 'basic'
    if (!groups[sectionName]) {
      groups[sectionName] = []
    }
    groups[sectionName].push(field)
  }

  for (const key of Object.keys(groups)) {
    groups[key] = orderFieldsWithSchema(groups[key] as any[], null) as FieldDefinition[]
  }

  return groups
}

/**
 * Check whether a field should be skipped from detail sections.
 *
 * In normal mode we respect detail visibility flags.
 * In fallback mode (metadata loaded from form context), we respect form visibility flags.
 */
function shouldSkipField(field: FieldDefinition): boolean {
  return shouldSkipUnifiedDetailField(field, metadataSourceContext.value)
}

/**
 * Whether current detail metadata provides any visible business fields.
 */
function hasVisibleBusinessFields(fields: FieldDefinition[]): boolean {
  return fields.some((field) => !shouldSkipField(field))
}

function buildSectionsFromRuntimeLayout(
  layoutSections: any[],
  fields: FieldDefinition[],
  options: { strictVisibility?: boolean } = {}
): DetailSection[] {
  const modePolicy = createModePolicyForContext('detail-runtime', {
    metadataContext: metadataSourceContext.value,
    strictVisibility: options.strictVisibility === true
  })
  return projectUnifiedDetailSectionsFromLayout({
    layoutSections,
    fields,
    modePolicy,
    getSectionTitle,
    getSectionIcon
  }) as DetailSection[]
}

async function loadRuntimeLayout(): Promise<void> {
  runtimeLayoutSections.value = null
  runtimeEditableFields.value = null
  runtimeReverseRelationFields.value = null
  try {
    // Single layout model: detail reuses edit runtime layout/field ordering.
    const runtime = await resolveRuntimeLayout(props.objectCode, 'edit', { includeRelations: true })
    metadataSourceContext.value = 'form'
    const layoutConfig = runtime.layoutConfig || null
    const editable = (runtime.editableFields || []) as any[]
    if (editable.length > 0) {
      const normalizedEditable = editable.map((field: any) => ({
        ...field,
        code: field.code || field.fieldName || field.field_name || '',
        name: field.name || field.displayName || field.display_name || field.code || '',
        label: field.label || field.name || field.displayName || field.code || '',
        fieldType: field.fieldType || field.field_type || field.type || 'text',
        isHidden: field.isHidden ?? field.is_hidden ?? false,
        showInDetail: field.showInDetail ?? field.show_in_detail ?? true,
        showInForm: field.showInForm ?? field.show_in_form ?? true
      }))

      const compiled = compileLayoutSchema({
        mode: 'edit',
        fields: normalizedEditable as any[],
        layoutConfig: layoutConfig || null
      })
      const sections = compiled.layoutConfig?.sections
      if (Array.isArray(sections) && sections.length > 0) {
        runtimeLayoutSections.value = sections
      }

      runtimeEditableFields.value = orderFieldsWithSchema(
        normalizedEditable as any[],
        compiled.renderSchema
      ) as FieldDefinition[]
    } else {
      const compiled = compileLayoutSchema({
        mode: 'edit',
        fields: [],
        layoutConfig: layoutConfig || null,
        keepUnknownFields: true
      })
      const sections = compiled.layoutConfig?.sections
      if (Array.isArray(sections) && sections.length > 0) {
        runtimeLayoutSections.value = sections
      }
    }
    const reverse = (runtime.reverseRelations || []) as any[]
    if (reverse.length > 0) {
      runtimeReverseRelationFields.value = reverse as FieldDefinition[]
    }
  } catch (error: any) {
    debugDetailLog('runtime-layout-load-failed', {
      objectCode: props.objectCode,
      error: error?.message || String(error)
    })
  }
}

/**
 * Get section title from section name
 */
function getSectionTitle(sectionName: string): string {
  const titles: Record<string, string> = {
    basic: t('common.basicInfo'),
    value: t('common.valueInfo'),
    usage: t('common.usageInfo'),
    images: t('common.detailPage.images'),
    attachments: t('common.detailPage.attachments'),
    details: t('common.detailInfo'),
    status: t('common.detailPage.statusInfo'),
    location: t('common.locationInfo'),
    supplier: t('common.supplierInfo'),
    warranty: t('common.warrantyInfo')
  }
  return titles[sectionName] || sectionName
}

/**
 * Get section icon name
 */
function getSectionIcon(sectionName: string): string {
  const icons: Record<string, string> = {
    basic: 'InfoFilled',
    value: 'Money',
    usage: 'UserFilled',
    images: 'Picture',
    attachments: 'Paperclip',
    details: 'Document',
    status: 'CircleCheck',
    location: 'Location',
    supplier: 'Shop',
    warranty: 'Shield'
  }
  return icons[sectionName] || 'Document'
}

/**
 * Convert field definition to detail field
 */
function fieldToDetailField(field: FieldDefinition): DetailField {
  return toUnifiedDetailField(field as any) as DetailField
}

function collectEditableFieldProps(sections: DetailSection[]): string[] {
  const props = new Set<string>()
  for (const section of sections || []) {
    const direct = Array.isArray(section.fields) ? section.fields : []
    for (const field of direct) {
      if (field?.prop) props.add(field.prop)
    }
    const tabs = Array.isArray(section.tabs) ? section.tabs : []
    for (const tab of tabs) {
      for (const field of tab.fields || []) {
        if (field?.prop) props.add(field.prop)
      }
    }
  }
  return Array.from(props)
}

function buildInlineEditFormSeed(record: Record<string, any>, sections: DetailSection[]): Record<string, any> {
  const seed: Record<string, any> = JSON.parse(JSON.stringify(record || {}))
  const props = collectEditableFieldProps(sections)

  for (const prop of props) {
    if (!prop || prop.includes('.')) continue

    const resolved = resolveFieldValue(record, {
      fieldCode: prop,
      includeWrappedData: true,
      includeCustomBags: true,
      // Prefer non-empty alias values when both snake/camel keys coexist.
      // This avoids blank edit controls when one alias is an empty placeholder.
      treatEmptyAsMissing: true,
      returnEmptyMatch: true
    })
    if (resolved === undefined) continue

    seed[prop] = resolved
    const camelKey = snakeToCamel(prop)
    if (camelKey !== prop) seed[camelKey] = resolved
  }

  return seed
}

/**
 * Extract object code from reverse relation
 */
function extractObjectCode(field: FieldDefinition): string {
  if (field.reverseRelationModel) {
    const parts = field.reverseRelationModel.split('.')
    return parts[parts.length - 1]
  }
  return field.code.replace(/(_?record|_?items|s?)$/, '')
}

/**
 * Fetch record detail
 */
async function fetchRecordDetail() {
  if (!recordId.value) {
    ElMessage.error(t('common.detailPage.recordIdNotExists'))
    return
  }

  loading.value = true
  try {
    let data: any

    if (props.fetchRecord) {
      data = await props.fetchRecord(recordId.value)
    } else {
      // Default: use dynamic object API
      data = await request.get(`/system/objects/${props.objectCode}/${recordId.value}/`)
    }

    const normalizedRecord = normalizeRecordPayload(data)
    debugDetailLog('record-loaded', {
      objectCode: props.objectCode,
      recordId: recordId.value,
      topLevelKeys: Object.keys(normalizedRecord || {}),
      hasCustomFields: !!(normalizedRecord?.customFields || normalizedRecord?.custom_fields)
    })
    recordData.value = normalizedRecord
    emit('loaded', normalizedRecord)
  } catch (error: any) {
    console.error('Failed to load record:', error)
    ElMessage.error(error.message || t('common.detailPage.loadFailed'))
  } finally {
    loading.value = false
  }
}

/**
 * Handle edit action
 */
function handleEdit() {
  emit('edit', recordData.value)

  if (props.editRoute) {
    // Legacy routing mode
    const editPath = props.editRoute.replace(':id', recordId.value)
      .replace(`{id}`, recordId.value)
    window.location.href = editPath
    return
  }

  // Inline editing mode
  formData.value = buildInlineEditFormSeed(recordData.value, detailSections.value)
  isEditing.value = true
  generateFormRules()
}

/**
 * Handle save action (Inline Edit)
 */
async function handleSave(updatedFormData: Record<string, any>) {
  if (baseDetailRef.value) {
    const valid = await baseDetailRef.value.validateForm()
    if (!valid) {
      ElMessage.warning(t('common.messages.formValidationFailed'))
      return
    }
  }

  submitting.value = true
  try {
    await apiClient.value.update(recordId.value, updatedFormData)
    ElMessage.success(t('common.detailPage.saveSuccess'))
    isEditing.value = false
    await fetchRecordDetail()
  } catch (error: any) {
    ElMessage.error(error.message || t('common.detailPage.saveFailed'))
  } finally {
    submitting.value = false
  }
}

/**
 * Handle cancel action (Inline Edit)
 */
function handleCancel() {
  isEditing.value = false
  formData.value = {}
}

/**
 * Handle delete action
 */
async function handleDelete() {
  emit('delete', recordData.value)

  // Default delete behavior (can be overridden by parent)
  try {
    await request.delete(`/system/objects/${props.objectCode}/${recordId.value}/`)
    ElMessage.success(t('common.detailPage.deleteSuccess'))
    handleBack()
  } catch (error) {
    console.error('Delete failed:', error)
    ElMessage.error(t('common.detailPage.deleteFailed'))
  }
}

/**
 * Handle back action
 */
function handleBack() {
  emit('back')
  if (props.backRoute) {
    window.location.href = props.backRoute
  } else {
    window.history.back()
  }
}

/**
 * Handle related record click
 */
function handleRelatedRecordClick(relationCode: string, record: any) {
  emit('related-record-click', relationCode, record)
}

/**
 * Handle related record edit
 */
function handleRelatedRecordEdit(relationCode: string, record: any) {
  emit('related-record-edit', relationCode, record)
}

/**
 * Handle related table refresh
 */
function handleRelatedRefresh(relationCode: string) {
  // Refresh the specific related table
  console.log('Refresh related:', relationCode)
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  await loadRuntimeLayout()

  // Legacy fallback only when runtime did not provide usable metadata at all.
  if (!runtimeEditableFields.value?.length && !runtimeReverseRelationFields.value?.length) {
    await fetchFields('form', { includeRelations: true, force: true })
    metadataSourceContext.value = 'form'
    debugDetailLog('fields-form-fallback-loaded', {
      objectCode: props.objectCode,
      editableFields: editableFields.value.length,
      visibleBusinessFields: hasVisibleBusinessFields(editableFields.value as FieldDefinition[])
    })
  }

  debugDetailLog('sections-ready', {
    objectCode: props.objectCode,
    sections: detailSections.value.length,
    sectionFields: detailSections.value.reduce((n, s) => n + (s.fields?.length || 0), 0),
    metadataSource: metadataSourceContext.value,
    runtimeLayoutSections: runtimeLayoutSections.value?.length || 0
  })

  // Fetch record detail
  await fetchRecordDetail()
  
  // Enter inline edit mode if ?action=edit is in query
  if (route.query.action === 'edit' && !props.editRoute) {
    handleEdit()
  }
})

// Watch for record ID changes
watch(recordId, () => {
  if (recordId.value) {
    fetchRecordDetail()
  }
})

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  refresh: fetchRecordDetail,
  record: recordData
})
</script>

<template>
  <div class="dynamic-detail-page">
    <BaseDetailPage
      ref="baseDetailRef"
      v-model:form-data="formData"
      :title="pageTitle"
      :object-name="objectName"
      :object-icon="objectIcon"
      :sections="detailSections"
      :data="recordData"
      :loading="loading || metadataLoading || submitting"
      :audit-info="effectiveAuditInfo"
      :show-edit="showEdit"
      :show-delete="showDelete"
      :show-back="!!backRoute"
      :edit-mode="isEditing"
      :form-rules="formRules"
      :extra-actions="extraActions"
      :object-code="objectCode"
      :reverse-relations="visibleReverseRelations"
      :show-related-objects="true"
      @edit="handleEdit"
      @save="handleSave"
      @cancel="handleCancel"
      @delete="handleDelete"
      @back="handleBack"
      @related-record-click="handleRelatedRecordClick"
      @related-record-edit="handleRelatedRecordEdit"
      @related-refresh="handleRelatedRefresh"
    >
      <!-- Slot for custom field rendering -->
      <template
        v-for="field in slottedFields"
        #[`field-${field.code}`]="slotProps"
        :key="field.code"
      >
        <slot
          :name="`field-${field.code}`"
          :field="field"
          :data="slotProps.data"
          :value="slotProps.value"
        />
      </template>

      <!-- Slot for custom sections -->
      <template
        v-for="section in slottedSections"
        #[`section-${section.name}`]="slotProps"
        :key="section.name"
      >
        <slot
          :name="`section-${section.name}`"
          :data="slotProps.data"
          :section="section"
        />
      </template>
    </BaseDetailPage>
  </div>
</template>

<style scoped lang="scss">
.dynamic-detail-page {
  height: 100%;
}
</style>
