import { buildRenderSchema } from '@/platform/layout/renderSchema'
import {
  projectDetailSectionsFromRenderSchema,
  type ProjectedDetailField,
  type ProjectedDetailSection
} from '@/platform/layout/detailSchemaProjector'
import { isAuditFieldCode, normalizeDetailSpan, toUnifiedDetailField } from '@/platform/layout/unifiedDetailField'
import { isSystemField } from '@/utils/transform'
import type { FieldDefinition } from '@/types'
import {
  buildLayoutRenderModel,
  createModePolicyForContext,
  type FieldViewModel,
  type ModePolicy,
  type RenderMetadataContext
} from '@/platform/layout/layoutRenderModel'

export type DetailMetadataContext = RenderMetadataContext

const isHiddenField = (field: FieldDefinition | FieldViewModel): boolean => {
  return ((field as any).isHidden ?? (field as any).is_hidden) === true
}

/**
 * Unified detail visibility policy used by both runtime detail pages
 * and designer preview rendering.
 */
export const shouldSkipUnifiedDetailField = (
  field: FieldDefinition | FieldViewModel,
  metadataContext: DetailMetadataContext = 'form'
): boolean => {
  if (isHiddenField(field)) return true
  if (isSystemField(field)) return true

  if (metadataContext === 'form') {
    const showInForm = (field as any).showInForm ?? (field as any).show_in_form
    return showInForm === false
  }

  const showInDetail = (field as any).showInDetail ?? (field as any).show_in_detail
  return showInDetail === false
}

export interface UnifiedDetailSectionsInput {
  layoutSections: Record<string, any>[]
  fields: FieldDefinition[]
  modePolicy?: ModePolicy
  metadataContext?: DetailMetadataContext
  strictVisibility?: boolean
  getSectionTitle?: (sectionName: string) => string
  getSectionIcon?: (sectionName: string) => string
}

export const projectUnifiedDetailSectionsFromLayout = (
  input: UnifiedDetailSectionsInput
): ProjectedDetailSection[] => {
  const modePolicy = input.modePolicy || createModePolicyForContext('detail-runtime', {
    metadataContext: input.metadataContext || 'form',
    strictVisibility: input.strictVisibility === true
  })
  const model = buildLayoutRenderModel({
    sections: input.layoutSections || [],
    fields: input.fields || [],
    modePolicy
  })

  const renderSchema = buildRenderSchema({
    // Single layout model: detail rendering follows edit layout structure.
    mode: 'edit',
    fields: model.fields as any[],
    layoutConfig: { sections: model.sections || [] }
  })
  const knownFieldCodes = new Set(
    (model.fields || [])
      .map((field) => String(field?.code || '').trim())
      .filter(Boolean)
  )

  return projectDetailSectionsFromRenderSchema(renderSchema, model.fields as any[], {
    strictVisibility: model.modePolicy.strictVisibility === true,
    isAuditFieldCode,
    mustSkipField: (field) => {
      // Runtime metadata field map is the source of truth.
      // Layout-only injected fields (often system/legacy artifacts) should not
      // occupy grid slots in detail rendering.
      if (!knownFieldCodes.has(String(field?.code || '').trim())) return true
      if (isSystemField(field) || isAuditFieldCode(field.code)) return true
      return isHiddenField(field)
    },
    shouldSkipField: (field) => shouldSkipUnifiedDetailField(
      field,
      model.modePolicy.metadataContext || 'form'
    ),
    fieldToDetailField: (field) => toUnifiedDetailField(field as any) as unknown as ProjectedDetailField,
    getSectionTitle: input.getSectionTitle,
    getSectionIcon: input.getSectionIcon,
    normalizeSpan: normalizeDetailSpan
  })
}
