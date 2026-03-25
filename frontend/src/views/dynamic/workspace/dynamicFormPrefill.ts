type QueryValue = string | string[] | null | undefined

const PREFILL_QUERY_PREFIX = 'prefill_'

const readFirstString = (value: QueryValue): string => {
  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }
  return String(value || '').trim()
}

const normalizeQueryValue = (value: QueryValue): string | string[] | undefined => {
  if (Array.isArray(value)) {
    const normalized = value
      .map((item) => String(item || '').trim())
      .filter(Boolean)
    return normalized.length > 0 ? normalized : undefined
  }

  const normalized = String(value || '').trim()
  return normalized || undefined
}

export const extractDynamicFormRoutePrefill = (query: unknown): Record<string, string | string[]> => {
  if (!query || typeof query !== 'object' || Array.isArray(query)) {
    return {}
  }

  const candidate = query as Record<string, QueryValue>
  const prefill: Record<string, string | string[]> = {}
  const jsonPrefill = readFirstString(candidate.prefill)

  if (jsonPrefill) {
    try {
      const parsed = JSON.parse(jsonPrefill)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        Object.assign(prefill, parsed as Record<string, string | string[]>)
      }
    } catch {
      // Ignore invalid JSON and continue reading prefixed query keys.
    }
  }

  for (const [key, value] of Object.entries(candidate)) {
    if (!key.startsWith(PREFILL_QUERY_PREFIX)) continue
    const normalized = normalizeQueryValue(value)
    if (normalized === undefined) continue
    prefill[key.slice(PREFILL_QUERY_PREFIX.length)] = normalized
  }

  return prefill
}

export const resolveDynamicFormReturnTo = (query: unknown): string => {
  if (!query || typeof query !== 'object' || Array.isArray(query)) {
    return ''
  }

  const candidate = query as Record<string, QueryValue>
  return readFirstString(candidate.returnTo || candidate.return_to)
}
