import type { FieldDefinition } from '@/types'
import type { RuntimeLayoutConfig } from '@/types/runtime'
import { adaptFieldDefinition } from './fieldAdapter'
import { normalizeLayoutConfig } from './layoutNormalizer'
import { buildRenderSchema } from '@/platform/layout/renderSchema'
import {
  projectListLayoutConfigForRenderSchema,
  projectRuntimeLayoutFromRenderSchema
} from '@/platform/layout/renderSchemaProjector'

type AnyRecord = Record<string, any>

export function extractLayoutConfig(layoutResponse: AnyRecord | null | undefined): AnyRecord | null {
  if (!layoutResponse) return null
  const data = layoutResponse.data ?? layoutResponse
  return data.layoutConfig || data.layout_config || data.layout || data
}

const buildDefaultLayout = (fields: FieldDefinition[]): RuntimeLayoutConfig => ({
  sections: [
    {
      id: 'default',
      name: 'default',
      title: '',
      type: 'section',
      columns: 2,
      visible: true,
      showTitle: false,
      fields: fields.map(adaptFieldDefinition)
    }
  ]
})

/**
 * Legacy adapter kept for backward compatibility.
 * Runtime pages should prefer RenderSchema + projector directly.
 */
export function adaptLayoutConfig(
  layoutConfig: AnyRecord | null | undefined,
  fields: FieldDefinition[]
): RuntimeLayoutConfig {
  if (!layoutConfig) {
    return buildDefaultLayout(fields)
  }

  const normalizedLayout = Array.isArray(layoutConfig?.sections)
    ? normalizeLayoutConfig(layoutConfig)
    : layoutConfig

  const runtimeFields = fields.map(adaptFieldDefinition)
  const schemaLayout = projectListLayoutConfigForRenderSchema(normalizedLayout)
  const renderSchema = buildRenderSchema({
    mode: 'edit',
    layoutConfig: schemaLayout,
    fields: runtimeFields as AnyRecord[]
  })
  const projected = projectRuntimeLayoutFromRenderSchema(renderSchema)

  if (!projected.sections.length) {
    return buildDefaultLayout(fields)
  }
  return projected
}
