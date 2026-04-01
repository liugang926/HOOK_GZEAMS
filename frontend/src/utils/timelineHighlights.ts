export interface TimelineHighlightLike {
  code?: string
  label?: string
  value?: string
  tone?: string
}

export interface TimelineHighlightEntryLike {
  createdAt?: string | null
  timestamp?: string | null
  source?: string
  sourceCode?: string
  sourceLabel?: string
  title?: string
  actionLabel?: string
  objectCode?: string
  objectId?: string
  recordLabel?: string
  highlights?: TimelineHighlightLike[] | null
}

export interface TimelineHighlightSummary {
  code: string
  label: string
  value: string
  tone?: string
  createdAt?: string | null
  source?: string
  sourceCode?: string
  sourceLabel?: string
  title?: string
  objectCode?: string
  objectId?: string
  recordLabel?: string
}

const normalizeText = (value: unknown) => String(value || '').trim()
export const DETAIL_ACTIVITY_ANCHOR = '#detail-activity'

export const collectTimelineHighlights = (
  entries: Array<TimelineHighlightEntryLike | null | undefined>,
  limit = Number.POSITIVE_INFINITY,
): TimelineHighlightSummary[] => {
  const highlights: TimelineHighlightSummary[] = []

  for (const entry of entries || []) {
    if (!entry || !Array.isArray(entry.highlights)) continue

    for (const highlight of entry.highlights) {
      const code = normalizeText(highlight?.code)
      const label = normalizeText(highlight?.label) || code
      const value = normalizeText(highlight?.value)

      if (!code || !value) continue

      highlights.push({
        code,
        label,
        value,
        tone: normalizeText(highlight?.tone) || undefined,
        createdAt: entry.createdAt || entry.timestamp || null,
        source: normalizeText(entry.source) || undefined,
        sourceCode: normalizeText(entry.sourceCode) || undefined,
        sourceLabel: normalizeText(entry.sourceLabel) || undefined,
        title: normalizeText(entry.title || entry.actionLabel) || undefined,
        objectCode: normalizeText(entry.objectCode) || undefined,
        objectId: normalizeText(entry.objectId) || undefined,
        recordLabel: normalizeText(entry.recordLabel) || undefined,
      })

      if (highlights.length >= limit) {
        return highlights
      }
    }
  }

  return highlights
}

export const resolveLatestTimelineHighlight = (
  entries: Array<TimelineHighlightEntryLike | null | undefined>,
) => {
  return collectTimelineHighlights(entries, 1)[0]
}

export const summarizeTimelineHighlightValue = (
  value: string,
  maxLength = 42,
) => {
  const normalizedValue = normalizeText(value)
  if (normalizedValue.length <= maxLength) {
    return normalizedValue
  }
  return `${normalizedValue.slice(0, Math.max(0, maxLength - 3))}...`
}

export const formatTimelineHighlightSummary = (
  highlight: Pick<TimelineHighlightSummary, 'label' | 'value'> | null | undefined,
) => {
  if (!highlight) return ''
  const label = normalizeText(highlight.label)
  const value = normalizeText(highlight.value)
  if (!label || !value) return ''
  return `${label}: ${value}`
}

export const resolveTimelineHighlightSourceLabel = (
  highlight: Pick<
    TimelineHighlightSummary,
    'sourceLabel' | 'recordLabel' | 'source' | 'objectCode'
  > | null | undefined,
) => {
  if (!highlight) return ''
  return normalizeText(
    highlight.sourceLabel || highlight.recordLabel || highlight.source || highlight.objectCode,
  )
}

export const formatTimelineHighlightTimestamp = (
  value: string | null | undefined,
  locale = 'en-US',
) => {
  const normalizedValue = normalizeText(value)
  if (!normalizedValue) return ''
  const candidate = new Date(normalizedValue)
  if (Number.isNaN(candidate.getTime())) return normalizedValue
  return new Intl.DateTimeFormat(locale || 'en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(candidate)
}

export const formatTimelineHighlightContext = (
  highlight: Pick<
    TimelineHighlightSummary,
    'createdAt' | 'sourceLabel' | 'recordLabel' | 'source' | 'objectCode'
  > | null | undefined,
  locale = 'en-US',
) => {
  if (!highlight) return ''
  const sourceLabel = resolveTimelineHighlightSourceLabel(highlight)
  const timestamp = formatTimelineHighlightTimestamp(highlight.createdAt, locale)
  return [sourceLabel, timestamp].filter(Boolean).join(' · ')
}

export const buildTimelineHighlightSourceLocation = ({
  highlight,
  currentObjectCode,
  currentRecordId,
}: {
  highlight: Pick<TimelineHighlightSummary, 'objectCode' | 'objectId'> | null | undefined
  currentObjectCode?: string
  currentRecordId?: string
}) => {
  const objectCode = normalizeText(highlight?.objectCode)
  const objectId = normalizeText(highlight?.objectId)
  if (!objectCode || !objectId) return null

  if (
    objectCode === normalizeText(currentObjectCode) &&
    objectId === normalizeText(currentRecordId)
  ) {
    return null
  }

  return `/objects/${encodeURIComponent(objectCode)}/${encodeURIComponent(objectId)}`
}
