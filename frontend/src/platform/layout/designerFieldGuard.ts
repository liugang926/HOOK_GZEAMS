import { normalizeFieldType } from '@/utils/fieldType'
import { isFieldSupportedInMode, type FieldRenderMode } from '@/platform/layout/fieldCapabilityMatrix'

const MODE_LABEL: Record<FieldRenderMode, string> = {
  edit: 'edit',
  readonly: 'readonly',
  list: 'list',
  search: 'search',
}

/**
 * Shared form layouts are used by both edit and readonly pages.
 * So designer mode=edit must ensure field types work in both modes.
 */
export const getRequiredModesForDesigner = (mode?: string | null): FieldRenderMode[] => {
  const raw = String(mode || '').toLowerCase()
  if (raw === 'readonly' || raw === 'detail') return ['readonly']
  if (raw === 'list') return ['list']
  if (raw === 'search') return ['search']
  return ['edit', 'readonly']
}

export const getUnsupportedModesForField = (rawType: string | undefined, mode?: string | null): FieldRenderMode[] => {
  const normalizedType = normalizeFieldType(rawType || 'text')
  return getRequiredModesForDesigner(mode).filter((runtimeMode) => !isFieldSupportedInMode(normalizedType, runtimeMode))
}

export const canAddFieldInDesigner = (rawType: string | undefined, mode?: string | null): boolean =>
  getUnsupportedModesForField(rawType, mode).length === 0

export const getFieldDisabledReason = (rawType: string | undefined, mode?: string | null): string | null => {
  const unsupported = getUnsupportedModesForField(rawType, mode)
  if (unsupported.length === 0) return null
  const modeList = unsupported.map((item) => MODE_LABEL[item]).join(', ')
  return `Not supported in ${modeList} mode`
}
