type AnyRecord = Record<string, any>

export const normalizeReferenceOption = (input: unknown): AnyRecord | null => {
  if (!input || typeof input !== 'object') return null
  const raw = input as AnyRecord
  const id = String(raw.id || raw.pk || raw.value || '').trim()
  if (!id) return null
  return {
    ...raw,
    id
  }
}

export const extractEmbeddedReferenceOptions = (input: unknown): AnyRecord[] => {
  if (input === null || input === undefined || input === '') return []

  const out: AnyRecord[] = []
  const push = (value: unknown) => {
    const normalized = normalizeReferenceOption(value)
    if (normalized) out.push(normalized)
  }

  if (Array.isArray(input)) {
    input.forEach(push)
  } else {
    push(input)
  }

  return Array.from(new Map(out.map((item) => [item.id, item])).values())
}

export const buildReferenceValueMap = (input: unknown): Record<string, AnyRecord> => {
  return Object.fromEntries(
    extractEmbeddedReferenceOptions(input).map((item) => [item.id, item])
  )
}

export const mergeReferenceOptionsByIds = (
  ids: string[],
  ...sources: Array<Record<string, AnyRecord | null | undefined> | null | undefined>
): AnyRecord[] => {
  const resolved: AnyRecord[] = []
  for (const id of ids) {
    let candidate: AnyRecord | null = null
    for (const source of sources) {
      const value = source?.[id]
      if (value && typeof value === 'object') {
        candidate = normalizeReferenceOption(value)
        if (candidate) break
      }
    }
    if (candidate) resolved.push(candidate)
  }
  return resolved
}
