import { buildObjectPageScopeId } from '@/platform/reference/pageScope'

export interface ReferenceLookupScopeInput {
  routeName?: unknown
  routePath?: unknown
  hostObjectCode?: unknown
  hostRecordId?: unknown
  action?: unknown
  layoutId?: unknown
  layoutMode?: unknown
}

/**
 * Build a deterministic scope id for lookup preference persistence.
 * Scope is page-level (detail/edit/create/designer), not record-level.
 */
export const buildReferenceLookupScopeId = (
  input: ReferenceLookupScopeInput
): string => {
  return buildObjectPageScopeId({
    routeName: input.routeName,
    routePath: input.routePath,
    objectCode: input.hostObjectCode,
    recordId: input.hostRecordId,
    action: input.action,
    layoutId: input.layoutId,
    layoutMode: input.layoutMode
  })
}
