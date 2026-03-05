export interface RelationGroupingInput {
  code: string
  label?: string
  relatedObjectCode?: string
  sortOrder?: number
  groupKey?: string
  groupName?: string
  groupOrder?: number
  defaultExpanded?: boolean
}

export interface RelationGroupSection<T extends RelationGroupingInput = RelationGroupingInput> {
  key: string
  title: string
  order: number
  defaultExpanded: boolean
  relations: T[]
}

const normalize = (value: unknown): string => String(value || '').trim()

const DEFAULT_GROUP_ORDER: Record<string, number> = {
  business: 10,
  workflow: 20,
  finance: 30,
  inventory: 40,
  consumables: 50,
  it_assets: 60,
  insurance: 70,
  leasing: 80,
  organization: 90,
  master_data: 100,
  other: 999
}

export const inferRelationGroupKey = (relation: RelationGroupingInput): string => {
  const sample = `${normalize(relation.code).toLowerCase()}:${normalize(relation.relatedObjectCode).toLowerCase()}`

  if (/(workflow|approval|instance|task)/.test(sample)) return 'workflow'
  if (/(voucher|depreciation|finance)/.test(sample)) return 'finance'
  if (/(inventory|snapshot|difference)/.test(sample)) return 'inventory'
  if (/(consumable|issue|purchase)/.test(sample)) return 'consumables'
  if (/(itasset|itsoftware|configuration|license)/.test(sample)) return 'it_assets'
  if (/(insurance|policy|claim|premium|insured)/.test(sample)) return 'insurance'
  if (/(lease|leasing|rent)/.test(sample)) return 'leasing'
  if (/(organization|department|user)/.test(sample)) return 'organization'
  if (/(category|supplier|location)/.test(sample)) return 'master_data'
  if (/(maintenance|receipt|pickup|transfer|return|loan|disposal|asset)/.test(sample)) return 'business'
  return 'other'
}

export const defaultRelationGroupTitle = (
  groupKey: string,
  translate: (key: string, fallback: string) => string
): string => {
  const fallbackMap: Record<string, string> = {
    business: 'Business',
    workflow: 'Workflow',
    finance: 'Finance',
    inventory: 'Inventory',
    consumables: 'Consumables',
    it_assets: 'IT Assets',
    insurance: 'Insurance',
    leasing: 'Leasing',
    organization: 'Organization',
    master_data: 'Master Data',
    other: 'Other'
  }
  return translate(`common.relatedGroup.${groupKey}`, fallbackMap[groupKey] || fallbackMap.other)
}

export const defaultRelationGroupExpanded = (groupKey: string): boolean => {
  return groupKey === 'business' || groupKey === 'workflow'
}

export const groupRelations = <T extends RelationGroupingInput>(
  relations: T[],
  options: {
    getTitle: (groupKey: string) => string
  }
): RelationGroupSection<T>[] => {
  const map = new Map<string, RelationGroupSection<T>>()

  const orderedRelations = [...relations].sort((a, b) => {
    const aOrder = Number.isFinite(Number(a.sortOrder)) ? Number(a.sortOrder) : 9999
    const bOrder = Number.isFinite(Number(b.sortOrder)) ? Number(b.sortOrder) : 9999
    if (aOrder !== bOrder) return aOrder - bOrder
    return normalize(a.code).localeCompare(normalize(b.code))
  })

  for (const relation of orderedRelations) {
    const groupKey = normalize(relation.groupKey) || inferRelationGroupKey(relation)
    const section = map.get(groupKey) || {
      key: groupKey,
      title: '',
      order: Number.isFinite(Number(relation.groupOrder))
        ? Number(relation.groupOrder)
        : (DEFAULT_GROUP_ORDER[groupKey] ?? DEFAULT_GROUP_ORDER.other),
      defaultExpanded:
        relation.defaultExpanded === undefined
          ? defaultRelationGroupExpanded(groupKey)
          : Boolean(relation.defaultExpanded),
      relations: []
    }
    section.title = normalize(relation.groupName) || options.getTitle(groupKey)
    section.relations.push(relation)
    map.set(groupKey, section)
  }

  return Array.from(map.values()).sort((a, b) => {
    if (a.order !== b.order) return a.order - b.order
    return a.key.localeCompare(b.key)
  })
}

