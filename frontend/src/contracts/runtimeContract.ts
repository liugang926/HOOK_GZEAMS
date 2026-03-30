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

  const aggregate = (payload as AnyRecord).aggregate
  if (aggregate !== undefined && aggregate !== null) {
    if (!isObject(aggregate)) {
      errors.push('aggregate is not an object')
    } else {
      const detailRegions = (aggregate as AnyRecord).detailRegions ?? (aggregate as AnyRecord).detail_regions
      if (detailRegions !== undefined && !isArray(detailRegions)) {
        errors.push('aggregate.detailRegions is not an array')
      }
      if (isArray(detailRegions)) {
        for (const [index, region] of detailRegions.entries()) {
          if (!isObject(region)) {
            errors.push(`aggregate.detailRegions[${index}] is not an object`)
            continue
          }
          const relationCode = (region as AnyRecord).relationCode ?? (region as AnyRecord).relation_code
          if (relationCode !== undefined && typeof relationCode !== 'string') {
            errors.push(`aggregate.detailRegions[${index}].relationCode is not a string`)
          }
          const fieldCode = (region as AnyRecord).fieldCode ?? (region as AnyRecord).field_code
          if (fieldCode !== undefined && typeof fieldCode !== 'string') {
            errors.push(`aggregate.detailRegions[${index}].fieldCode is not a string`)
          }
        }
      }
    }
  }

  const workbench = (payload as AnyRecord).workbench
  if (workbench !== undefined && workbench !== null) {
    if (!isObject(workbench)) {
      errors.push('workbench is not an object')
    } else {
      const detailPanels = (workbench as AnyRecord).detailPanels ?? (workbench as AnyRecord).detail_panels
      const asyncIndicators = (workbench as AnyRecord).asyncIndicators ?? (workbench as AnyRecord).async_indicators
      const summaryCards = (workbench as AnyRecord).summaryCards ?? (workbench as AnyRecord).summary_cards
      const queuePanels = (workbench as AnyRecord).queuePanels ?? (workbench as AnyRecord).queue_panels
      const exceptionPanels = (workbench as AnyRecord).exceptionPanels ?? (workbench as AnyRecord).exception_panels
      const slaIndicators = (workbench as AnyRecord).slaIndicators ?? (workbench as AnyRecord).sla_indicators
      const recommendedActions = (workbench as AnyRecord).recommendedActions ?? (workbench as AnyRecord).recommended_actions
      const closurePanel = (workbench as AnyRecord).closurePanel ?? (workbench as AnyRecord).closure_panel

      if (detailPanels !== undefined && !isArray(detailPanels)) errors.push('workbench.detailPanels is not an array')
      if (asyncIndicators !== undefined && !isArray(asyncIndicators)) errors.push('workbench.asyncIndicators is not an array')
      if (summaryCards !== undefined && !isArray(summaryCards)) errors.push('workbench.summaryCards is not an array')
      if (queuePanels !== undefined && !isArray(queuePanels)) errors.push('workbench.queuePanels is not an array')
      if (exceptionPanels !== undefined && !isArray(exceptionPanels)) errors.push('workbench.exceptionPanels is not an array')
      if (slaIndicators !== undefined && !isArray(slaIndicators)) errors.push('workbench.slaIndicators is not an array')
      if (recommendedActions !== undefined && !isArray(recommendedActions)) errors.push('workbench.recommendedActions is not an array')
      if (closurePanel !== undefined && closurePanel !== null && !isObject(closurePanel)) {
        errors.push('workbench.closurePanel is not an object')
      }
    }
  }

  return { ok: errors.length === 0, errors }
}
