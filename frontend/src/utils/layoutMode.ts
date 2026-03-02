import type { RuntimeMode } from '@/contracts/runtimeContract'
import type { LayoutMode } from '@/types/layout'

export type LayoutTypeValue = 'form' | 'detail' | 'list' | 'search'
export type MetadataContext = 'form' | 'detail' | 'list'

const normalizeRaw = (value?: string | null): string => String(value || '').toLowerCase()

/**
 * Normalize mixed mode/type values to backend layout_type.
 * Examples:
 * - edit/form -> form
 * - readonly/detail/search -> form (shared single-layout model)
 */
export function normalizeLayoutType(value?: string | null): LayoutTypeValue {
  const raw = normalizeRaw(value)
  if (raw === 'readonly' || raw === 'detail' || raw === 'search') return 'form'
  if (raw === 'list') return 'list'
  return 'form'
}

/**
 * Normalize route/query values to designer mode.
 * Designer currently supports edit/readonly/search.
 */
export function normalizeDesignerMode(value?: string | null): LayoutMode {
  const raw = normalizeRaw(value)
  if (raw === 'readonly' || raw === 'detail' || raw === 'search') return 'edit'
  return 'edit'
}

/**
 * Normalize mixed mode/type values to runtime mode used by /runtime endpoint.
 */
export function toRuntimeMode(value?: string | null): RuntimeMode {
  const raw = normalizeRaw(value)
  if (raw === 'readonly' || raw === 'detail') return 'readonly'
  if (raw === 'list') return 'list'
  if (raw === 'search') return 'search'
  return 'edit'
}

/**
 * Convert mode/type to fields-context for /fields endpoints.
 */
export function toMetadataContext(value?: string | null): MetadataContext {
  const runtimeMode = toRuntimeMode(value)
  if (runtimeMode === 'list') return 'list'
  return 'form'
}
