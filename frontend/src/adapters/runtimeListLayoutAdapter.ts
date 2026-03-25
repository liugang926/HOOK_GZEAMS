import { buildRenderSchema } from '@/platform/layout/renderSchema'
import {
  projectListColumnsFromRenderSchema,
  projectListLayoutConfigForRenderSchema
} from '@/platform/layout/renderSchemaProjector'

const resolveLayoutConfig = (runtimePayload: any): any => {
  const layoutPayload = runtimePayload?.layout || {}
  return layoutPayload?.layoutConfig || layoutPayload?.layout_config || layoutPayload?.layout || {}
}

export const extractRuntimeListColumns = (runtimePayload: any): any[] => {
  const layoutConfig = resolveLayoutConfig(runtimePayload)
  const schemaLayoutConfig = projectListLayoutConfigForRenderSchema(layoutConfig)
  if (!schemaLayoutConfig) return []

  const renderSchema = buildRenderSchema({
    mode: 'list',
    fields: [],
    layoutConfig: schemaLayoutConfig
  })

  return projectListColumnsFromRenderSchema(renderSchema, [])
}
