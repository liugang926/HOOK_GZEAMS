export type ReferenceLookupColumnConfig = {
  key: string
  label?: string
  minWidth?: number
  width?: number
}

const normalize = (value: unknown): string => String(value || '').trim()

const EXTRA_COLUMNS_BY_OBJECT: Record<string, ReferenceLookupColumnConfig[]> = {
  user: [
    { key: 'email', minWidth: 220 },
    { key: 'mobile', minWidth: 160 }
  ],
  department: [
    { key: 'managerName', minWidth: 160 },
    { key: 'status', minWidth: 120 }
  ],
  location: [
    { key: 'address', minWidth: 220 },
    { key: 'status', minWidth: 120 }
  ],
  asset: [
    { key: 'assetCode', minWidth: 180 },
    { key: 'status', minWidth: 120 }
  ]
}

const dedupeColumns = (columns: ReferenceLookupColumnConfig[]): ReferenceLookupColumnConfig[] => {
  const map = new Map<string, ReferenceLookupColumnConfig>()
  for (const column of columns) {
    const key = normalize(column?.key)
    if (!key) continue
    if (map.has(key)) continue
    map.set(key, {
      ...column,
      key
    })
  }
  return Array.from(map.values())
}

export const resolveReferenceLookupDefaultColumns = (params: {
  objectCode: unknown
  displayField: unknown
  secondaryField: unknown
}): ReferenceLookupColumnConfig[] => {
  const objectCode = normalize(params.objectCode).toLowerCase()
  if (!objectCode) return []

  const displayField = normalize(params.displayField) || 'name'
  const secondaryField = normalize(params.secondaryField) || 'code'

  const base: ReferenceLookupColumnConfig[] = [
    { key: displayField, minWidth: 220 },
    { key: secondaryField, minWidth: 180 },
    { key: 'id', minWidth: 180 }
  ]
  const extras = EXTRA_COLUMNS_BY_OBJECT[objectCode] || []
  return dedupeColumns([...base, ...extras])
}
