const normalize = (value: unknown): string => String(value || '').trim()

const SNAKE_SUFFIX_RE = /(?:_records?|_items?|_orders?)$/i
const CAMEL_SUFFIX_RE = /(?:Records?|Items?|Orders?|Record|Item|Order)$/

export const extractObjectCodeFromModelPath = (modelPath: unknown): string => {
  const value = normalize(modelPath)
  if (!value) return ''
  const parts = value.split('.').map((item) => item.trim()).filter(Boolean)
  return parts.length > 0 ? parts[parts.length - 1] : ''
}

export const deriveObjectCodeFromRelationCode = (relationCode: unknown): string => {
  const raw = normalize(relationCode)
  if (!raw) return ''

  let candidate = raw.replace(SNAKE_SUFFIX_RE, '')
  if (candidate === raw) {
    candidate = candidate.replace(CAMEL_SUFFIX_RE, '')
  }
  if (candidate === raw && /^[a-z0-9]+s$/.test(candidate)) {
    candidate = candidate.slice(0, -1)
  }
  if (!candidate) return ''

  if (/[_\-\s]/.test(candidate)) {
    return candidate
      .split(/[_\-\s]+/)
      .filter(Boolean)
      .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
      .join('')
  }

  if (/^[a-z]/.test(candidate)) {
    return candidate.charAt(0).toUpperCase() + candidate.slice(1)
  }

  return candidate
}

export const resolveRelationTargetObjectCode = (params: {
  explicitTarget?: unknown
  reverseRelationModel?: unknown
  relationCode?: unknown
}): string => {
  const explicit = normalize(params.explicitTarget)
  if (explicit) return explicit

  const byModel = extractObjectCodeFromModelPath(params.reverseRelationModel)
  if (byModel) return byModel

  return deriveObjectCodeFromRelationCode(params.relationCode)
}
