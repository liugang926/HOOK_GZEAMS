type AnyRecord = Record<string, any>

const isObject = (v: any): v is AnyRecord => v !== null && typeof v === 'object' && !Array.isArray(v)

const isArray = Array.isArray

export type RuntimeMode = 'edit' | 'readonly' | 'list' | 'search'

export type RuntimeContractCheck = {
  ok: boolean
  errors: string[]
}

/**
 * Lightweight runtime DTO validation.
 *
 * Goals:
 * - Detect incompatible backend payloads early.
 * - Trigger safe fallbacks (legacy endpoints) instead of rendering blank pages.
 * - Avoid adding new runtime deps (zod/ajv).
 */
export function checkRuntimeContract(payload: any): RuntimeContractCheck {
  const errors: string[] = []

  if (!isObject(payload)) {
    return { ok: false, errors: ['runtime payload is not an object'] }
  }

  const runtimeVersion = (payload as AnyRecord).runtimeVersion ?? (payload as AnyRecord).runtime_version
  if (runtimeVersion !== undefined && runtimeVersion !== 1) {
    errors.push(`unsupported runtimeVersion: ${String(runtimeVersion)}`)
  }

  const fields = (payload as AnyRecord).fields
  if (!isObject(fields)) errors.push('missing fields object')
  else {
    const editable = (fields as AnyRecord).editableFields ?? (fields as AnyRecord).editable_fields ?? (fields as AnyRecord).fields
    const reverse = (fields as AnyRecord).reverseRelations ?? (fields as AnyRecord).reverse_relations
    if (editable !== undefined && !isArray(editable)) errors.push('fields.editableFields is not an array')
    if (reverse !== undefined && !isArray(reverse)) errors.push('fields.reverseRelations is not an array')
  }

  const layout = (payload as AnyRecord).layout
  if (!isObject(layout)) errors.push('missing layout object')
  else {
    const layoutConfig = (layout as AnyRecord).layoutConfig ?? (layout as AnyRecord).layout_config ?? (layout as AnyRecord).layout
    if (layoutConfig !== undefined && !isObject(layoutConfig)) errors.push('layout.layoutConfig is not an object')
  }

  const permissions = (payload as AnyRecord).permissions
  if (permissions !== undefined) {
    if (!isObject(permissions)) {
      errors.push('permissions is not an object')
    } else {
      const requiredFlags = ['view', 'add', 'change', 'delete']
      for (const key of requiredFlags) {
        if (key in permissions && typeof (permissions as AnyRecord)[key] !== 'boolean') {
          errors.push(`permissions.${key} is not a boolean`)
        }
      }
    }
  }

  return { ok: errors.length === 0, errors }
}
