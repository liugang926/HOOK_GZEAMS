const normalize = (value: unknown): string => String(value || '').trim()

const normalizePath = (value: unknown): string => {
  const raw = normalize(value)
  if (!raw) return ''
  const noQuery = raw.split('?')[0].split('#')[0]
  return noQuery.replace(/\/{2,}/g, '/').replace(/\/$/, '')
}

const isDesignerRoute = (routeName: unknown, routePath: unknown): boolean => {
  const name = normalize(routeName).toLowerCase()
  const path = normalizePath(routePath).toLowerCase()
  return name.includes('pagelayoutdesigner') || path.includes('/system/page-layouts/designer')
}

/**
 * Unified scope id for designer preview pages.
 */
export const buildDesignerPreviewScopeId = (options?: {
  mode?: unknown
  layoutId?: unknown
}): string => {
  const mode = normalize(options?.mode) || 'edit'
  const layoutId = normalize(options?.layoutId) || 'draft'
  return `designer-preview:${mode}:${layoutId}`
}

/**
 * Unified scope id for single business records.
 * Detail/Edit intentionally share one record scope.
 */
export const buildRecordScopeId = (
  recordId: unknown,
  fallbackCode?: unknown
): string => {
  const id = normalize(recordId)
  if (id) return id

  const fallback = normalize(fallbackCode)
  return fallback ? `record:${fallback}` : ''
}

export interface ObjectPageScopeInput {
  routeName?: unknown
  routePath?: unknown
  objectCode?: unknown
  recordId?: unknown
  action?: unknown
  layoutId?: unknown
  layoutMode?: unknown
}

/**
 * Unified scope id for page-level preferences (lookup/profile/recent).
 */
export const buildObjectPageScopeId = (
  input: ObjectPageScopeInput
): string => {
  const routePath = normalizePath(input.routePath)
  const routeName = normalize(input.routeName)
  const objectCode = normalize(input.objectCode)
  const recordId = normalize(input.recordId)
  const action = normalize(input.action).toLowerCase()

  if (isDesignerRoute(routeName, routePath)) {
    return buildDesignerPreviewScopeId({
      mode: input.layoutMode,
      layoutId: input.layoutId
    })
  }

  if (objectCode) {
    if (routePath.endsWith('/create')) return `object-create:${objectCode}`
    if (routePath.endsWith('/edit') || (!!recordId && routePath.includes('/edit'))) return `object-edit:${objectCode}`
    if (action === 'edit') return `object-edit:${objectCode}`
    if (recordId) return `object-detail:${objectCode}`
    return `object:${objectCode}`
  }

  if (routeName) return `route:${routeName}`
  if (routePath) return `path:${routePath}`
  return 'global'
}
