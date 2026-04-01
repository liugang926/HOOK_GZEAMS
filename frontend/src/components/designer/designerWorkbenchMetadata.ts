import type {
  RuntimeDocumentSurfaceTab,
  RuntimeWorkbenchDocumentSummarySection,
  RuntimeWorkbenchPageMode,
  RuntimeWorkbenchSurfacePriority,
} from '@/types/runtime'

export interface DesignerWorkbenchMetadataConfig {
  defaultPageMode: RuntimeWorkbenchPageMode
  defaultDocumentSurfaceTab: RuntimeDocumentSurfaceTab
  documentSummarySections: RuntimeWorkbenchDocumentSummarySection[]
}

export const DESIGNER_DOCUMENT_SUMMARY_SECTION_CODES = [
  'process_summary',
  'record',
  'workflow',
  'batch_tools',
] as const

export const DESIGNER_WORKBENCH_PAGE_MODES: RuntimeWorkbenchPageMode[] = [
  'record',
  'workspace',
]

export const DESIGNER_DOCUMENT_SURFACE_TABS: RuntimeDocumentSurfaceTab[] = [
  'summary',
  'form',
  'activity',
]

export const DESIGNER_WORKBENCH_SURFACE_PRIORITIES: RuntimeWorkbenchSurfacePriority[] = [
  'primary',
  'context',
  'related',
  'activity',
  'admin',
]

export const DESIGNER_DEFAULT_DOCUMENT_SUMMARY_SECTIONS: RuntimeWorkbenchDocumentSummarySection[] = [
  { code: 'process_summary', surfacePriority: 'primary' },
  { code: 'record', surfacePriority: 'context' },
  { code: 'workflow', surfacePriority: 'context' },
  { code: 'batch_tools', surfacePriority: 'admin' },
]

export const DESIGNER_DEFAULT_WORKBENCH_METADATA: DesignerWorkbenchMetadataConfig = {
  defaultPageMode: 'record',
  defaultDocumentSurfaceTab: 'summary',
  documentSummarySections: DESIGNER_DEFAULT_DOCUMENT_SUMMARY_SECTIONS,
}

export const isDesignerDocumentSummarySectionCode = (
  value: unknown,
): value is typeof DESIGNER_DOCUMENT_SUMMARY_SECTION_CODES[number] => {
  return DESIGNER_DOCUMENT_SUMMARY_SECTION_CODES.includes(
    String(value || '').trim() as typeof DESIGNER_DOCUMENT_SUMMARY_SECTION_CODES[number],
  )
}

export const normalizeDesignerPageMode = (value: unknown): RuntimeWorkbenchPageMode => {
  const normalized = String(value || '').trim()
  if (DESIGNER_WORKBENCH_PAGE_MODES.includes(normalized as RuntimeWorkbenchPageMode)) {
    return normalized as RuntimeWorkbenchPageMode
  }
  return 'record'
}

export const normalizeDesignerDocumentSurfaceTab = (
  value: unknown,
): RuntimeDocumentSurfaceTab => {
  const normalized = String(value || '').trim()
  if (DESIGNER_DOCUMENT_SURFACE_TABS.includes(normalized as RuntimeDocumentSurfaceTab)) {
    return normalized as RuntimeDocumentSurfaceTab
  }
  return 'summary'
}

export const normalizeDesignerSurfacePriority = (
  value: unknown,
): RuntimeWorkbenchSurfacePriority => {
  const normalized = String(value || '').trim()
  if (DESIGNER_WORKBENCH_SURFACE_PRIORITIES.includes(normalized as RuntimeWorkbenchSurfacePriority)) {
    return normalized as RuntimeWorkbenchSurfacePriority
  }
  return 'context'
}

export const normalizeDesignerDocumentSummarySections = (
  value: unknown,
): RuntimeWorkbenchDocumentSummarySection[] => {
  const sections = Array.isArray(value) ? value : []
  const normalized: RuntimeWorkbenchDocumentSummarySection[] = []
  const seen = new Set<string>()
  const defaultsByCode = new Map(
    DESIGNER_DEFAULT_DOCUMENT_SUMMARY_SECTIONS.map((section) => [section.code, section]),
  )

  for (const item of sections) {
    if (!item || typeof item !== 'object') {
      continue
    }

    const candidate = item as Record<string, unknown>
    const code = String(candidate.code || '').trim()
    if (!isDesignerDocumentSummarySectionCode(code) || seen.has(code)) {
      continue
    }

    normalized.push({
      ...(defaultsByCode.get(code) || { code, surfacePriority: 'context' }),
      ...candidate,
      code,
      surfacePriority: normalizeDesignerSurfacePriority(
        candidate.surfacePriority ?? candidate.surface_priority,
      ),
    })
    seen.add(code)
  }

  for (const section of DESIGNER_DEFAULT_DOCUMENT_SUMMARY_SECTIONS) {
    if (seen.has(section.code)) {
      continue
    }
    normalized.push({ ...section })
  }

  return normalized
}

export const normalizeDesignerWorkbenchMetadata = (
  value: unknown,
): DesignerWorkbenchMetadataConfig => {
  const candidate = value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {}

  return {
    defaultPageMode: normalizeDesignerPageMode(
      candidate.defaultPageMode ?? candidate.default_page_mode,
    ),
    defaultDocumentSurfaceTab: normalizeDesignerDocumentSurfaceTab(
      candidate.defaultDocumentSurfaceTab ?? candidate.default_document_surface_tab,
    ),
    documentSummarySections: normalizeDesignerDocumentSummarySections(
      candidate.documentSummarySections ?? candidate.document_summary_sections,
    ),
  }
}

export const serializeDesignerDocumentSummarySections = (
  value: unknown,
): Array<Record<string, unknown>> => {
  return normalizeDesignerDocumentSummarySections(value).map((section) => ({
    code: section.code,
    surfacePriority: normalizeDesignerSurfacePriority(section.surfacePriority),
    surface_priority: normalizeDesignerSurfacePriority(section.surfacePriority),
  }))
}

export const serializeDesignerWorkbenchMetadata = (
  value: unknown,
): Record<string, unknown> => {
  const metadata = normalizeDesignerWorkbenchMetadata(value)
  const sections = serializeDesignerDocumentSummarySections(metadata.documentSummarySections)

  return {
    defaultPageMode: normalizeDesignerPageMode(metadata.defaultPageMode),
    default_page_mode: normalizeDesignerPageMode(metadata.defaultPageMode),
    defaultDocumentSurfaceTab: normalizeDesignerDocumentSurfaceTab(
      metadata.defaultDocumentSurfaceTab,
    ),
    default_document_surface_tab: normalizeDesignerDocumentSurfaceTab(
      metadata.defaultDocumentSurfaceTab,
    ),
    documentSummarySections: sections,
    document_summary_sections: sections,
  }
}
