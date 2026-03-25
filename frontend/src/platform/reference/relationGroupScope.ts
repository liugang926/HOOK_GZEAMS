import {
  buildDesignerPreviewScopeId,
  buildRecordScopeId
} from '@/platform/reference/pageScope'

export const buildRecordRelationGroupScopeId = (
  recordId: unknown,
  fallbackCode?: unknown
): string => buildRecordScopeId(recordId, fallbackCode)

export const buildDesignerRelationGroupScopeId = (options?: {
  mode?: unknown
  layoutId?: unknown
}): string => buildDesignerPreviewScopeId(options)
