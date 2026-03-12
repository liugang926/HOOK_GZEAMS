import { computed, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { dynamicApi } from '@/api/dynamic'
import {
  defaultRelationGroupTitle,
  groupRelations
} from '@/platform/reference/relationGrouping'
import { useRelationGroupExpansion } from '@/composables/useRelationGroupExpansion'

interface ReverseRelationFieldLike {
  code: string
  label: string
  displayMode: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  displayTier?: 'L1' | 'L2' | 'L3'
  relationKind?: string
  relatedObjectCode?: string
  reverseRelationField?: string
  sortOrder?: number
  groupKey?: string
  groupName?: string
  groupOrder?: number
  defaultExpanded?: boolean
  title?: string
  showCreate?: boolean
}

interface RelationPropsLike {
  data: Record<string, any>
  objectCode?: string
  reverseRelations?: ReverseRelationFieldLike[]
  showRelatedObjects: boolean
  resolveRuntimeRelations: boolean
  relationGroupScopeId?: string
}

interface UseBaseDetailPageRelationsOptions {
  props: RelationPropsLike
  runtimeRelations: Ref<ReverseRelationFieldLike[]>
}

export function useBaseDetailPageRelations(options: UseBaseDetailPageRelationsOptions) {
  const { props, runtimeRelations } = options
  const { t } = useI18n()

  const isLineItemRelation = (relation: ReverseRelationFieldLike) => {
    if (relation.displayTier !== 'L1') {
      return false
    }

    const rawRelation = relation as ReverseRelationFieldLike & Record<string, any>
    return String(rawRelation.relationKind || rawRelation.relation_kind || '').trim() !== 'through_line_item'
  }

  const allVisibleRelations = computed(() => {
    if (!props.showRelatedObjects) {
      return []
    }
    const source = runtimeRelations.value.length > 0 ? runtimeRelations.value : (props.reverseRelations || [])
    return source
      .filter((rel) => rel.displayMode !== 'hidden')
      .slice()
      .sort((a, b) => {
        const aOrder = Number.isFinite(Number(a.sortOrder)) ? Number(a.sortOrder) : 9999
        const bOrder = Number.isFinite(Number(b.sortOrder)) ? Number(b.sortOrder) : 9999
        if (aOrder !== bOrder) return aOrder - bOrder
        return String(a.code || '').localeCompare(String(b.code || ''))
      })
  })

  // L1 relations → inline in Details tab
  const lineItemRelations = computed(() =>
    allVisibleRelations.value.filter((rel) => isLineItemRelation(rel))
  )

  // L2/L3 relations → Related tab (excludes L1 to avoid duplication)
  const visibleReverseRelations = computed(() =>
    allVisibleRelations.value.filter((rel) => !isLineItemRelation(rel))
  )

  const mapRuntimeRelation = (raw: Record<string, any>): ReverseRelationFieldLike | null => {
    const code = String(raw.relationCode || '').trim()
    if (!code) return null

    const displayMode = String(raw.displayMode || raw.display_mode || 'inline_readonly') as ReverseRelationFieldLike['displayMode']
    const relatedObjectCode = String(raw.targetObjectCode || raw.target_object_code || '').trim()
    const label = String(raw.relationName || raw.relation_name || relatedObjectCode || code).trim()
    const defaultExpandedRaw = raw.defaultExpanded

    return {
      code,
      label,
      displayMode,
      displayTier: (String(raw.displayTier || raw.display_tier || 'L2').trim() as ReverseRelationFieldLike['displayTier']),
      relationKind: String(raw.relationKind || raw.relation_kind || '').trim(),
      relatedObjectCode,
      reverseRelationField: String(raw.targetFkField || raw.target_fk_field || '').trim(),
      sortOrder: Number(raw.sortOrder || raw.sort_order || 0) || 0,
      groupKey: String(raw.groupKey || raw.group_key || '').trim(),
      groupName: String(raw.groupName || raw.group_name || '').trim(),
      groupOrder: Number(raw.groupOrder || raw.group_order || 0) || undefined,
      defaultExpanded:
        defaultExpandedRaw === undefined
          ? undefined
          : String(defaultExpandedRaw).toLowerCase() === 'true' || defaultExpandedRaw === true || defaultExpandedRaw === 1,
      title: label,
      showCreate: displayMode === 'inline_editable'
    }
  }

  const resolveRelationGroupTitle = (groupKey: string): string => {
    return defaultRelationGroupTitle(groupKey, (key, fallback) => {
      const translated = t(key as any)
      return translated && translated !== key ? translated : fallback
    })
  }

  const groupedReverseRelationSections = computed(() => {
    return groupRelations(visibleReverseRelations.value, {
      getTitle: resolveRelationGroupTitle
    })
  })

  const relationGroupItems = computed(() => {
    return groupedReverseRelationSections.value.map((group) => ({
      key: group.key,
      defaultExpanded: group.defaultExpanded
    }))
  })

  const relationGroupExpansion = useRelationGroupExpansion({
    groups: () => relationGroupItems.value,
    objectCode: () => String(props.objectCode || ''),
    scopeId: () => String(props.relationGroupScopeId || (props.data && (props.data.id ?? props.data.code)) || '')
  })

  const fetchRuntimeRelations = async () => {
    if (!props.showRelatedObjects || !props.resolveRuntimeRelations) {
      runtimeRelations.value = []
      return
    }

    const objectCode = String(props.objectCode || '').trim()
    if (!objectCode) {
      runtimeRelations.value = []
      return
    }

    try {
      const payload = await dynamicApi.getRelations(objectCode)
      const rows = Array.isArray((payload as any)?.relations) ? (payload as any).relations : []
      runtimeRelations.value = rows
        .map((row: Record<string, any>) => mapRuntimeRelation(row))
        .filter((item: ReverseRelationFieldLike | null): item is ReverseRelationFieldLike => Boolean(item))
    } catch {
      runtimeRelations.value = []
    }
  }

  return {
    lineItemRelations,
    visibleReverseRelations,
    groupedReverseRelationSections,
    isRelationGroupExpanded: relationGroupExpansion.isExpanded,
    toggleRelationGroup: relationGroupExpansion.toggle,
    fetchRuntimeRelations
  }
}
