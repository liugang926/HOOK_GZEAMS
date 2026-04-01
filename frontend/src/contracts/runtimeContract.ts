type AnyRecord = Record<string, any>

const isObject = (v: any): v is AnyRecord => v !== null && typeof v === 'object' && !Array.isArray(v)

const isArray = Array.isArray

export type RuntimeMode = 'edit' | 'readonly' | 'list' | 'search'

export type RuntimeContractCheck = {
  ok: boolean
  errors: string[]
}

const pushIfInvalidString = (errors: string[], path: string, value: unknown) => {
  if (value !== undefined && typeof value !== 'string') {
    errors.push(`${path} is not a string`)
  }
}

const pushIfInvalidBoolean = (errors: string[], path: string, value: unknown) => {
  if (value !== undefined && typeof value !== 'boolean') {
    errors.push(`${path} is not a boolean`)
  }
}

const pushIfInvalidNumber = (errors: string[], path: string, value: unknown) => {
  if (value !== undefined && typeof value !== 'number') {
    errors.push(`${path} is not a number`)
  }
}

const pushIfInvalidEnum = (
  errors: string[],
  path: string,
  value: unknown,
  allowed: string[],
) => {
  if (value === undefined || value === null) {
    return
  }
  if (typeof value !== 'string') {
    errors.push(`${path} is not a string`)
    return
  }
  if (!allowed.includes(value)) {
    errors.push(`${path} is not one of: ${allowed.join(', ')}`)
  }
}

const WORKBENCH_SURFACE_PRIORITIES = ['primary', 'context', 'related', 'activity', 'admin']

const validateWorkbenchSurfacePriority = (
  definition: AnyRecord,
  path: string,
  errors: string[],
) => {
  pushIfInvalidEnum(
    errors,
    `${path}.surfacePriority`,
    definition.surfacePriority ?? definition.surface_priority,
    WORKBENCH_SURFACE_PRIORITIES,
  )
}

const validateWorkbenchPromptField = (
  field: unknown,
  path: string,
  errors: string[],
) => {
  if (!isObject(field)) {
    errors.push(`${path} is not an object`)
    return
  }

  if (typeof field.key !== 'string') {
    errors.push(`${path}.key is not a string`)
  }
  pushIfInvalidString(errors, `${path}.type`, field.type)
  pushIfInvalidString(errors, `${path}.payloadKey`, field.payloadKey ?? field.payload_key)
  pushIfInvalidString(errors, `${path}.valueFormat`, field.valueFormat ?? field.value_format)
  pushIfInvalidBoolean(errors, `${path}.required`, field.required)
  pushIfInvalidNumber(errors, `${path}.rows`, field.rows)
  pushIfInvalidNumber(errors, `${path}.min`, field.min)
  pushIfInvalidNumber(errors, `${path}.max`, field.max)
  pushIfInvalidNumber(errors, `${path}.precision`, field.precision)

  const options = field.options
  if (options !== undefined) {
    if (!isArray(options)) {
      errors.push(`${path}.options is not an array`)
    } else {
      for (const [index, option] of options.entries()) {
        if (!isObject(option)) {
          errors.push(`${path}.options[${index}] is not an object`)
          continue
        }
        const value = option.value
        if (
          value !== undefined &&
          !['string', 'number', 'boolean'].includes(typeof value)
        ) {
          errors.push(`${path}.options[${index}].value is not a scalar`)
        }
      }
    }
  }
}

const validateWorkbenchPrompt = (
  prompt: unknown,
  path: string,
  errors: string[],
) => {
  if (!isObject(prompt)) {
    errors.push(`${path} is not an object`)
    return
  }

  const fields = prompt.fields
  if (!isArray(fields)) {
    errors.push(`${path}.fields is not an array`)
    return
  }

  for (const [index, field] of fields.entries()) {
    validateWorkbenchPromptField(field, `${path}.fields[${index}]`, errors)
  }
}

const validateWorkbenchActionCollection = (
  actions: unknown,
  path: string,
  errors: string[],
) => {
  if (!isArray(actions)) {
    errors.push(`${path} is not an array`)
    return
  }

  for (const [index, action] of actions.entries()) {
    if (!isObject(action)) {
      errors.push(`${path}[${index}] is not an object`)
      continue
    }

    validateWorkbenchSurfacePriority(action, `${path}[${index}]`, errors)

    const prompt = action.prompt ?? action.promptConfig ?? action.prompt_config
    if (prompt !== undefined && prompt !== null) {
      validateWorkbenchPrompt(prompt, `${path}[${index}].prompt`, errors)
    }
  }
}

const validateWorkbenchSurfaceCollection = (
  collection: unknown,
  path: string,
  errors: string[],
) => {
  if (!isArray(collection)) {
    errors.push(`${path} is not an array`)
    return
  }

  for (const [index, item] of collection.entries()) {
    if (!isObject(item)) {
      errors.push(`${path}[${index}] is not an object`)
      continue
    }
    validateWorkbenchSurfacePriority(item, `${path}[${index}]`, errors)
  }
}

const validateWorkbenchDocumentSummarySections = (
  collection: unknown,
  path: string,
  errors: string[],
) => {
  if (!isArray(collection)) {
    errors.push(`${path} is not an array`)
    return
  }

  for (const [index, item] of collection.entries()) {
    if (!isObject(item)) {
      errors.push(`${path}[${index}] is not an object`)
      continue
    }
    pushIfInvalidString(errors, `${path}[${index}].code`, item.code)
    validateWorkbenchSurfacePriority(item, `${path}[${index}]`, errors)
  }
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
      const toolbar = (workbench as AnyRecord).toolbar
      const defaultPageMode = (workbench as AnyRecord).defaultPageMode ?? (workbench as AnyRecord).default_page_mode
      const defaultDetailSurfaceTab = (workbench as AnyRecord).defaultDetailSurfaceTab ?? (workbench as AnyRecord).default_detail_surface_tab
      const defaultDocumentSurfaceTab = (workbench as AnyRecord).defaultDocumentSurfaceTab ?? (workbench as AnyRecord).default_document_surface_tab
      const detailPanels = (workbench as AnyRecord).detailPanels ?? (workbench as AnyRecord).detail_panels
      const asyncIndicators = (workbench as AnyRecord).asyncIndicators ?? (workbench as AnyRecord).async_indicators
      const summaryCards = (workbench as AnyRecord).summaryCards ?? (workbench as AnyRecord).summary_cards
      const queuePanels = (workbench as AnyRecord).queuePanels ?? (workbench as AnyRecord).queue_panels
      const exceptionPanels = (workbench as AnyRecord).exceptionPanels ?? (workbench as AnyRecord).exception_panels
      const slaIndicators = (workbench as AnyRecord).slaIndicators ?? (workbench as AnyRecord).sla_indicators
      const recommendedActions = (workbench as AnyRecord).recommendedActions ?? (workbench as AnyRecord).recommended_actions
      const closurePanel = (workbench as AnyRecord).closurePanel ?? (workbench as AnyRecord).closure_panel
      const documentSummarySections = (workbench as AnyRecord).documentSummarySections ?? (workbench as AnyRecord).document_summary_sections

      pushIfInvalidEnum(errors, 'workbench.defaultPageMode', defaultPageMode, ['record', 'workspace'])
      pushIfInvalidEnum(errors, 'workbench.defaultDetailSurfaceTab', defaultDetailSurfaceTab, ['process', 'activity'])
      pushIfInvalidEnum(errors, 'workbench.defaultDocumentSurfaceTab', defaultDocumentSurfaceTab, ['summary', 'form', 'activity'])

      if (toolbar !== undefined && toolbar !== null) {
        if (!isObject(toolbar)) {
          errors.push('workbench.toolbar is not an object')
        } else {
          const primaryActions = (toolbar as AnyRecord).primaryActions ?? (toolbar as AnyRecord).primary_actions
          const secondaryActions = (toolbar as AnyRecord).secondaryActions ?? (toolbar as AnyRecord).secondary_actions

          if (primaryActions !== undefined && !isArray(primaryActions)) {
            errors.push('workbench.toolbar.primaryActions is not an array')
          }
          if (secondaryActions !== undefined && !isArray(secondaryActions)) {
            errors.push('workbench.toolbar.secondaryActions is not an array')
          }

          if (isArray(primaryActions)) {
            validateWorkbenchActionCollection(primaryActions, 'workbench.toolbar.primaryActions', errors)
          }
          if (isArray(secondaryActions)) {
            validateWorkbenchActionCollection(secondaryActions, 'workbench.toolbar.secondaryActions', errors)
          }
        }
      }

      if (detailPanels !== undefined) {
        validateWorkbenchSurfaceCollection(detailPanels, 'workbench.detailPanels', errors)
      }
      if (asyncIndicators !== undefined) {
        validateWorkbenchSurfaceCollection(asyncIndicators, 'workbench.asyncIndicators', errors)
      }
      if (summaryCards !== undefined) {
        validateWorkbenchSurfaceCollection(summaryCards, 'workbench.summaryCards', errors)
      }
      if (queuePanels !== undefined) {
        validateWorkbenchSurfaceCollection(queuePanels, 'workbench.queuePanels', errors)
      }
      if (exceptionPanels !== undefined) {
        validateWorkbenchSurfaceCollection(exceptionPanels, 'workbench.exceptionPanels', errors)
      }
      if (slaIndicators !== undefined) {
        validateWorkbenchSurfaceCollection(slaIndicators, 'workbench.slaIndicators', errors)
      }
      if (isArray(recommendedActions)) {
        validateWorkbenchActionCollection(recommendedActions, 'workbench.recommendedActions', errors)
      } else if (recommendedActions !== undefined) {
        errors.push('workbench.recommendedActions is not an array')
      }
      if (documentSummarySections !== undefined) {
        validateWorkbenchDocumentSummarySections(
          documentSummarySections,
          'workbench.documentSummarySections',
          errors,
        )
      }
      if (closurePanel !== undefined && closurePanel !== null && !isObject(closurePanel)) {
        errors.push('workbench.closurePanel is not an object')
      } else if (isObject(closurePanel)) {
        validateWorkbenchSurfacePriority(closurePanel, 'workbench.closurePanel', errors)
      }
    }
  }

  return { ok: errors.length === 0, errors }
}
