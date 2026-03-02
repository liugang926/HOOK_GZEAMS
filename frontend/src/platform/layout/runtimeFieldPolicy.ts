type AnyRecord = Record<string, any>

const readOrder = (field: AnyRecord): number | null => {
  const value = field?.sortOrder ?? field?.sort_order ?? field?.order
  if (value === null || value === undefined || value === '') return null
  const num = Number(value)
  return Number.isFinite(num) ? num : null
}

const readCode = (field: AnyRecord): string => {
  return String(field?.code || field?.fieldCode || field?.field_code || '').trim()
}

/**
 * Normalize field ordering across runtime/detail/form flows.
 * Priority:
 * 1) explicit sortOrder/sort_order/order
 * 2) stable source order
 * 3) code as deterministic tie-breaker
 */
export const sortFieldsByRuntimeOrder = <T extends AnyRecord>(fields: T[]): T[] => {
  return [...fields].sort((a, b) => {
    const orderA = readOrder(a)
    const orderB = readOrder(b)
    const hasA = orderA !== null
    const hasB = orderB !== null

    if (hasA && hasB && orderA !== orderB) return (orderA as number) - (orderB as number)
    if (hasA && !hasB) return -1
    if (!hasA && hasB) return 1

    const codeA = readCode(a)
    const codeB = readCode(b)
    if (codeA && codeB && codeA !== codeB) return codeA.localeCompare(codeB)
    return 0
  })
}

export const isCreateRuntimeContext = (instanceId?: string | null): boolean => {
  return !String(instanceId || '').trim()
}
