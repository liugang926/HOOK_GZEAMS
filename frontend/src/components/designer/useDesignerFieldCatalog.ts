import { computed, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { normalizeFieldType } from '@/utils/fieldType'
import { cloneLayoutConfig, generateId } from '@/utils/layoutValidation'
import { resolveRelationTargetObjectCode } from '@/platform/reference/relationObjectCode'
import { getDesignerFieldArrayRef } from '@/components/designer/designerContainerUtils'
import { collectAddedFieldCodes } from '@/components/designer/designerTreeUtils'
import type { ReverseRelationField } from '@/components/common/BaseDetailPage.vue'
import type {
  ContainerMeta,
  DesignerAnyRecord,
  DesignerFieldDefinition,
  LayoutConfig,
  LayoutField
} from '@/components/designer/designerTypes'

interface UseDesignerFieldCatalogOptions {
  mode: string
  layoutConfig: Ref<LayoutConfig>
  sampleData: Ref<Record<string, unknown>>
  readComponentProps: (field: Partial<DesignerFieldDefinition & LayoutField> | null | undefined) => DesignerAnyRecord
  canAddField: (field: DesignerFieldDefinition) => boolean
  getDisabledReason: (field: DesignerFieldDefinition) => string | null
  commitLayoutChange: (newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) => void
  getSampleValue: (field: LayoutField) => unknown
  t: (key: string, params?: Record<string, unknown>) => string
}

export function useDesignerFieldCatalog(options: UseDesignerFieldCatalogOptions) {
  const addedFieldCodes = computed(() => collectAddedFieldCodes(options.layoutConfig.value))

  function isFieldAdded(code: string): boolean {
    return addedFieldCodes.value.includes(code)
  }

  function notifyUnsupportedField(field: DesignerFieldDefinition): void {
    const reason = options.getDisabledReason(field)
    if (!reason) return
    ElMessage.warning(options.t('system.pageLayout.designer.messages.cannotAddField', { name: field.name, reason }))
  }

  function buildLayoutField(field: DesignerFieldDefinition): LayoutField {
    const fieldType = normalizeFieldType(field.fieldType || 'text')
    const componentProps = options.readComponentProps(field)

    return {
      id: generateId('field'),
      fieldCode: field.code,
      label: field.name,
      span: 1,
      readonly: field.isReadonly || options.mode === 'readonly',
      visible: true,
      required: field.isRequired,
      fieldType,
      options: field.options,
      referenceObject: field.referenceObject || field.relatedObject,
      componentProps,
      dictionaryType: field.dictionaryType,
      defaultValue: field.defaultValue,
      placeholder: field.placeholder,
      helpText: field.helpText
    }
  }

  function addFieldToContainer(field: DesignerFieldDefinition, meta: ContainerMeta) {
    if (!options.canAddField(field)) {
      notifyUnsupportedField(field)
      return
    }

    if (isFieldAdded(field.code)) {
      ElMessage.warning(options.t('system.pageLayout.designer.messages.fieldAlreadyAdded'))
      return
    }

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const newConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const targetArr = getDesignerFieldArrayRef(newConfig, meta)
    if (!targetArr) return

    const newField = buildLayoutField(field)
    targetArr.push(newField)
    options.commitLayoutChange(newConfig, `Add field ${field.code}`, previousConfig)

    if (newField.fieldCode && options.sampleData.value[newField.fieldCode] === undefined) {
      options.sampleData.value[newField.fieldCode] = options.getSampleValue(newField)
    }
  }

  function extractRelatedObjectCode(field: DesignerAnyRecord): string {
    return resolveRelationTargetObjectCode({
      explicitTarget: field.relatedObjectCode || field.related_object_code || field.referenceObject,
      reverseRelationModel: field.reverseRelationModel || field.reverse_relation_model,
      relationCode: String(field.code || field.fieldCode || field.field_code || '').trim()
    })
  }

  function mapPreviewReverseRelations(fields: DesignerAnyRecord[]): ReverseRelationField[] {
    return (fields || []).map((rel) => ({
      code: rel.code,
      label: rel.label || rel.name || rel.code,
      displayMode: rel.relationDisplayMode || rel.relation_display_mode || 'inline_readonly',
      relatedObjectCode: extractRelatedObjectCode(rel),
      reverseRelationField: rel.reverseRelationField || rel.reverse_relation_field,
      reverseRelationModel: rel.reverseRelationModel || rel.reverse_relation_model,
      sortOrder: Number(rel.sortOrder || rel.sort_order || 0) || 0,
      groupKey: rel.groupKey || rel.group_key || '',
      groupName: rel.groupName || rel.group_name || '',
      groupOrder: Number(rel.groupOrder || rel.group_order || 0) || undefined,
      defaultExpanded:
        rel.defaultExpanded === undefined && rel.default_expanded === undefined
          ? undefined
          : Boolean(rel.defaultExpanded ?? rel.default_expanded),
      title: rel.label || rel.name || rel.code,
      showCreate: (rel.relationDisplayMode || rel.relation_display_mode) === 'inline_editable',
      position: rel.position
    })) as ReverseRelationField[]
  }

  return {
    addedFieldCodes,
    isFieldAdded,
    notifyUnsupportedField,
    buildLayoutField,
    addFieldToContainer,
    mapPreviewReverseRelations
  }
}
