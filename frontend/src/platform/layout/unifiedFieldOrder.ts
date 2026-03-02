import { sortFieldsByRuntimeOrder } from '@/platform/layout/runtimeFieldPolicy'
import { buildRenderSchema, type RenderSchema } from '@/platform/layout/renderSchema'
import { orderFieldsByRenderSchema } from '@/platform/layout/renderSchemaProjector'
import type { RuntimeMode } from '@/contracts/runtimeContract'

type AnyRecord = Record<string, any>

export const getFieldCode = (field: AnyRecord | null | undefined): string => {
  if (!field || typeof field !== 'object') return ''
  return String(field.code || field.fieldCode || field.field_code || field.fieldName || '').trim()
}

export const mergeFieldSources = (primary: AnyRecord[], fallback: AnyRecord[]): AnyRecord[] => {
  const merged = new Map<string, AnyRecord>()

  for (const field of fallback || []) {
    const code = getFieldCode(field)
    if (!code) continue
    merged.set(code, { ...field, code })
  }

  for (const field of primary || []) {
    const code = getFieldCode(field)
    if (!code) continue
    const prev = merged.get(code)
    merged.set(code, prev ? { ...prev, ...field, code } : { ...field, code })
  }

  return Array.from(merged.values())
}

export const orderFieldsWithSchema = (
  fields: AnyRecord[],
  schema: RenderSchema | null | undefined
): AnyRecord[] => {
  const runtimeOrdered = sortFieldsByRuntimeOrder(fields || [])
  if (!schema?.fieldOrder?.length) return runtimeOrdered
  return orderFieldsByRenderSchema(runtimeOrdered, schema)
}

export const buildAndOrderFields = (input: {
  fields: AnyRecord[]
  layoutConfig: AnyRecord | null | undefined
  mode: RuntimeMode
}): AnyRecord[] => {
  const schema = buildRenderSchema({
    fields: input.fields || [],
    layoutConfig: input.layoutConfig,
    mode: input.mode
  })
  return orderFieldsWithSchema(input.fields || [], schema)
}

