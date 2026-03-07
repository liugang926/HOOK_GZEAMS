import { ref, computed, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { camelToSnake, snakeToCamel } from '@/utils/case'
import { resolveFieldValue } from '@/utils/fieldKey'
import { dynamicApi, type ObjectRelationDefinition } from '@/api/dynamic'
import { defaultRelationGroupTitle, groupRelations } from '@/platform/reference/relationGrouping'
import type {
  DetailField,
  DetailSection,
  ReverseRelationField
} from '@/components/common/BaseDetailPage.vue'

type AnyRecord = Record<string, unknown>
type DetailDataEmit = (event: 'update:formData', data: AnyRecord) => void

interface UseDetailDataProps {
  data: Ref<AnyRecord>
  formData: Ref<AnyRecord>
  sections: Ref<DetailSection[]>
  reverseRelations: Ref<ReverseRelationField[]>
  showRelatedObjects: Ref<boolean>
  objectCode: Ref<string | undefined>
  activeTabs: Ref<Record<string, string>>
}

export function useDetailData(props: UseDetailDataProps, emit: DetailDataEmit) {
  const { t } = useI18n()
  const runtimeRelations = ref<ReverseRelationField[]>([])

  const visibleReverseRelations = computed(() => {
    if (!props.showRelatedObjects.value) return []

    const source = runtimeRelations.value.length > 0
      ? runtimeRelations.value
      : (props.reverseRelations.value || [])

    return source
      .filter((relation) => relation.displayMode !== 'hidden')
      .slice()
      .sort((a, b) => {
        const aOrder = Number.isFinite(Number(a.sortOrder)) ? Number(a.sortOrder) : 9999
        const bOrder = Number.isFinite(Number(b.sortOrder)) ? Number(b.sortOrder) : 9999
        if (aOrder !== bOrder) return aOrder - bOrder
        return String(a.code || '').localeCompare(String(b.code || ''))
      })
  })

  const resolveRelationGroupTitle = (groupKey: string): string => {
    if (!groupKey) return defaultRelationGroupTitle('', t)
    return t(`relationGroup.${groupKey}`, groupKey)
  }

  const groupedReverseRelationSections = computed(() => {
    const mainRelations = visibleReverseRelations.value.filter(rel => rel.position !== 'sidebar')
    return groupRelations(mainRelations, {
      getTitle: resolveRelationGroupTitle
    })
  })

  const sidebarReverseRelations = computed(() => {
    return visibleReverseRelations.value.filter((relation) => relation.position === 'sidebar')
  })

  const mapRuntimeRelation = (raw: ObjectRelationDefinition): ReverseRelationField | null => {
    const code = String(raw.relationCode || '').trim()
    if (!code) return null

    const displayMode = String(raw.displayMode || 'inline_readonly') as ReverseRelationField['displayMode']
    const relatedObjectCode = String(raw.targetObjectCode || '').trim()
    const label = String(raw.relationName || relatedObjectCode || code).trim()

    return {
      code,
      label,
      displayMode,
      relatedObjectCode,
      reverseRelationField: String(raw.targetFkField || '').trim(),
      sortOrder: Number(raw.sortOrder || 0) || 0,
      groupKey: String(raw.groupKey || '').trim(),
      groupName: String(raw.groupName || '').trim(),
      groupOrder: Number(raw.groupOrder || 0) || undefined,
      defaultExpanded: raw.defaultExpanded,
      title: label,
      showCreate: displayMode === 'inline_editable',
      position: 'main'
    }
  }

  watch(
    () => props.objectCode.value,
    async (objectCode) => {
      if (!objectCode) {
        runtimeRelations.value = []
        return
      }

      try {
        const payload = await dynamicApi.getRelations(objectCode)
        const rows = Array.isArray(payload?.relations) ? payload.relations : []
        runtimeRelations.value = rows
          .map((row) => mapRuntimeRelation(row))
          .filter((item): item is ReverseRelationField => Boolean(item))
      } catch {
        runtimeRelations.value = []
      }
    },
    { immediate: true }
  )

  const editDrawerProxyFields = computed<DetailField[]>(() => {
    const out: DetailField[] = []

    for (const section of props.sections.value || []) {
      if (section.type === 'tab' && Array.isArray(section.tabs) && section.tabs.length > 0) {
        const activeId = props.activeTabs.value[section.name] || section.tabs[0].id
        const activeTab = section.tabs.find((tab) => tab.id === activeId) || section.tabs[0]
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

  const readValue = (record: AnyRecord, prop: string, includeWrappedData = true) => {
    const value = resolveFieldValue(record, {
      fieldCode: prop,
      includeWrappedData,
      includeCustomBags: true,
      treatEmptyAsMissing: true,
      returnEmptyMatch: true
    })
    return value
  }

  const getFieldValue = (field: DetailField) => {
    const value = readValue(props.data.value, field.prop, true)
    return value !== undefined && value !== null ? value : '-'
  }

  const getEditFieldValue = (field: DetailField) => {
    const value = readValue(props.formData.value, field.prop, false)
    return value !== undefined ? value : null
  }

  const resolveEditFieldType = (field: DetailField): string => {
    const explicitType = String(field.editorType || '').trim()
    if (explicitType) return explicitType

    const fallbackType = String(field.type || 'text').trim()
    if (fallbackType === 'tag') return 'select'
    if (fallbackType === 'link') return 'text'
    return fallbackType || 'text'
  }

  const toInlineEditRuntimeField = (field: DetailField): AnyRecord => {
    return {
      code: field.prop,
      name: field.label,
      label: field.label,
      fieldType: resolveEditFieldType(field),
      options: field.options,
      readonly: field.readonly === true,
      referenceObject: field.referenceObject,
      referenceDisplayField: field.referenceDisplayField,
      referenceSecondaryField: field.referenceSecondaryField,
      componentProps: {
        ...(field.componentProps || {})
      }
    }
  }

  const updateFormData = (prop: string, value: unknown) => {
    const next = { ...props.formData.value }
    next[prop] = value

    const camelKey = snakeToCamel(prop)
    const snakeKey = camelToSnake(prop)

    if (camelKey && camelKey !== prop) next[camelKey] = value
    if (snakeKey && snakeKey !== prop) next[snakeKey] = value

    emit('update:formData', next)
  }

  return {
    groupedReverseRelationSections,
    sidebarReverseRelations,
    editDrawerProxyFields,
    getFieldValue,
    getEditFieldValue,
    toInlineEditRuntimeField,
    updateFormData
  }
}
