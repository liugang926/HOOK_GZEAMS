import request from '@/utils/request'

export type WorkbenchTranslate = (key: string) => string
export type WorkbenchHasTranslation = (key: string) => boolean

export type WorkbenchAction = Record<string, unknown> & {
  code: string
}

export interface WorkbenchPromptFieldOption {
  label: string
  value: string | number | boolean
}

export interface WorkbenchPromptField {
  key: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'date' | 'number'
  placeholder?: string
  required?: boolean
  rows?: number
  defaultValue?: string | number | boolean | null
  options?: WorkbenchPromptFieldOption[]
  valueFormat?: string
  min?: number
  max?: number
  precision?: number
  payloadKey?: string
}

export interface WorkbenchPrompt {
  title?: string
  message?: string
  confirmButtonText?: string
  cancelButtonText?: string
  fields: WorkbenchPromptField[]
}

const toNonEmptyString = (value: unknown) => {
  if (typeof value !== 'string') return ''
  return value.trim()
}

const toRecord = (value: unknown): Record<string, unknown> | null => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null
  return value as Record<string, unknown>
}

export const resolveWorkbenchText = (
  definition: Record<string, unknown>,
  t: WorkbenchTranslate,
  te: WorkbenchHasTranslation,
  keyCandidates: string[],
  fallbackCandidates: string[],
) => {
  for (const key of keyCandidates) {
    const translationKey = toNonEmptyString(definition[key])
    if (translationKey && te(translationKey)) {
      return t(translationKey)
    }
  }

  for (const key of fallbackCandidates) {
    const fallback = toNonEmptyString(definition[key])
    if (fallback) {
      return fallback
    }
  }

  return ''
}

export const resolveWorkbenchButtonType = (action: WorkbenchAction) => {
  const candidate = toNonEmptyString(action.buttonType || action.button_type || 'default')
  if (['primary', 'success', 'warning', 'danger', 'info', 'default'].includes(candidate)) {
    return candidate as 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  }
  return 'default'
}

export const resolveWorkbenchActionLabel = (
  action: WorkbenchAction,
  t: WorkbenchTranslate,
  te: WorkbenchHasTranslation,
) => {
  return resolveWorkbenchText(
    action,
    t,
    te,
    ['labelKey', 'label_key', 'titleKey', 'title_key'],
    ['label', 'title', 'code'],
  )
}

export const resolveWorkbenchActionDescription = (
  action: WorkbenchAction,
  t: WorkbenchTranslate,
  te: WorkbenchHasTranslation,
) => {
  return resolveWorkbenchText(
    action,
    t,
    te,
    ['descriptionKey', 'description_key', 'hintKey', 'hint_key'],
    ['description', 'hint'],
  )
}

export const resolveWorkbenchConfirmMessage = (
  action: WorkbenchAction,
  t: WorkbenchTranslate,
  te: WorkbenchHasTranslation,
) => {
  return resolveWorkbenchText(
    action,
    t,
    te,
    ['confirmMessageKey', 'confirm_message_key'],
    ['confirmMessage', 'confirm_message'],
  )
}

const resolvePromptFieldOptions = (
  field: Record<string, unknown>,
  t: WorkbenchTranslate,
  te: WorkbenchHasTranslation,
): WorkbenchPromptFieldOption[] => {
  const rawOptions = Array.isArray(field.options) ? field.options : []
  return rawOptions
    .map((option) => {
      const optionRecord = toRecord(option)
      if (!optionRecord) return null
      const label = resolveWorkbenchText(
        optionRecord,
        t,
        te,
        ['labelKey', 'label_key', 'titleKey', 'title_key'],
        ['label', 'title'],
      )
      const value = optionRecord.value
      if (!label || typeof value === 'object' || value === null || value === undefined) {
        return null
      }
      if (!['string', 'number', 'boolean'].includes(typeof value)) {
        return null
      }
      return {
        label,
        value: value as string | number | boolean,
      }
    })
    .filter((option): option is WorkbenchPromptFieldOption => Boolean(option))
}

export const resolveWorkbenchPrompt = (
  action: WorkbenchAction,
  t: WorkbenchTranslate,
  te: WorkbenchHasTranslation,
): WorkbenchPrompt | null => {
  const prompt = toRecord(action.prompt || action.promptConfig || action.prompt_config)
  if (!prompt) {
    return null
  }

  const fields = (Array.isArray(prompt.fields) ? prompt.fields : [])
    .map((field) => {
      const fieldRecord = toRecord(field)
      if (!fieldRecord) return null
      const key = toNonEmptyString(fieldRecord.key)
      if (!key) return null
      const label = resolveWorkbenchText(
        fieldRecord,
        t,
        te,
        ['labelKey', 'label_key', 'titleKey', 'title_key'],
        ['label', 'title', 'key'],
      ) || key
      const typeCandidate = toNonEmptyString(fieldRecord.type || 'text')
      const type = ['text', 'textarea', 'select', 'date', 'number'].includes(typeCandidate)
        ? typeCandidate as WorkbenchPromptField['type']
        : 'text'

      return {
        key,
        label,
        type,
        placeholder: resolveWorkbenchText(
          fieldRecord,
          t,
          te,
          ['placeholderKey', 'placeholder_key'],
          ['placeholder'],
        ),
        required: Boolean(fieldRecord.required),
        rows: typeof fieldRecord.rows === 'number' ? fieldRecord.rows : undefined,
        defaultValue: (
          fieldRecord.defaultValue ??
          fieldRecord.default_value ??
          null
        ) as WorkbenchPromptField['defaultValue'],
        options: resolvePromptFieldOptions(fieldRecord, t, te),
        valueFormat: toNonEmptyString(fieldRecord.valueFormat || fieldRecord.value_format || ''),
        min: typeof fieldRecord.min === 'number' ? fieldRecord.min : undefined,
        max: typeof fieldRecord.max === 'number' ? fieldRecord.max : undefined,
        precision: typeof fieldRecord.precision === 'number' ? fieldRecord.precision : undefined,
        payloadKey: toNonEmptyString(fieldRecord.payloadKey || fieldRecord.payload_key || key),
      }
    })
    .filter((field): field is WorkbenchPromptField => Boolean(field))

  if (fields.length === 0) {
    return null
  }

  return {
    title: resolveWorkbenchText(
      prompt,
      t,
      te,
      ['titleKey', 'title_key'],
      ['title'],
    ),
    message: resolveWorkbenchText(
      prompt,
      t,
      te,
      ['messageKey', 'message_key'],
      ['message'],
    ),
    confirmButtonText: resolveWorkbenchText(
      prompt,
      t,
      te,
      ['confirmButtonTextKey', 'confirm_button_text_key'],
      ['confirmButtonText', 'confirm_button_text'],
    ),
    cancelButtonText: resolveWorkbenchText(
      prompt,
      t,
      te,
      ['cancelButtonTextKey', 'cancel_button_text_key'],
      ['cancelButtonText', 'cancel_button_text'],
    ),
    fields,
  }
}

export const resolveWorkbenchActionPath = (action: WorkbenchAction) => {
  const raw = toNonEmptyString(action.actionPath || action.action_path || action.code || '')
  return raw.replace(/^\/+/, '').replace(/\/+$/, '')
}

export const resolveWorkbenchRoute = (
  definition: Record<string, unknown>,
  recordData?: Record<string, unknown> | null,
) => {
  const template = toNonEmptyString(
    definition.route ||
    definition.route_path ||
    definition.path ||
    '',
  )
  if (!template) {
    return ''
  }

  return template.replace(/\{([^}]+)\}/g, (_match, path) => {
    const value = readWorkbenchRecordValue(recordData, String(path).trim())
    if (value === null || value === undefined || value === '') {
      return ''
    }
    return encodeURIComponent(String(value))
  })
}

export const resolveWorkbenchCountValue = (
  definition: Record<string, unknown>,
  recordData?: Record<string, unknown> | null,
) => {
  if (definition.count !== undefined) {
    return definition.count
  }

  return readWorkbenchRecordValue(recordData, definition.countField || definition.count_field)
}

export const resolveWorkbenchSyncTaskId = (payload: unknown) => {
  const candidate = toRecord(payload)
  if (!candidate) return ''
  return toNonEmptyString(candidate.syncTaskId || candidate.sync_task_id || '')
}

export const executeWorkbenchAction = async ({
  action,
  objectCode,
  recordId,
  data,
}: {
  action: WorkbenchAction
  objectCode: string
  recordId: string
  data?: Record<string, unknown>
}) => {
  const actionPath = resolveWorkbenchActionPath(action)
  if (!actionPath) {
    throw new Error('Workbench action path is required')
  }

  const method = toNonEmptyString(action.method || 'post').toLowerCase()
  const response = await request<{
    success?: boolean
    message?: string
    data?: unknown
    error?: unknown
  }>({
    url: `/system/objects/${objectCode}/${recordId}/${actionPath}/`,
    method,
    data: data || {},
    unwrap: 'none',
  })

  const success = response.success !== false
  if (!success) {
    const error = response.error as Record<string, unknown> | undefined
    throw new Error(String(error?.message || response.message || 'Operation failed'))
  }

  return {
    data: (response.data as Record<string, unknown> | undefined) || {},
    message: String(response.message || ''),
  }
}

const hasPromptValue = (value: unknown) => {
  if (typeof value === 'string') {
    return value.trim() !== ''
  }
  return value !== null && value !== undefined && value !== ''
}

export const buildWorkbenchActionPayload = (
  action: WorkbenchAction,
  promptValues: Record<string, unknown> = {},
  prompt?: WorkbenchPrompt | null,
) => {
  const payload = {
    ...(toRecord(action.payload || action.staticPayload || action.static_payload || action.requestData || action.request_data) || {}),
  }

  if (!prompt) {
    return payload
  }

  prompt.fields.forEach((field) => {
    const value = promptValues[field.key]
    if (!hasPromptValue(value)) {
      return
    }
    payload[field.payloadKey || field.key] = value
  })

  return payload
}

export const readWorkbenchRecordValue = (
  recordData: Record<string, unknown> | null | undefined,
  path: unknown,
) => {
  const normalizedPath = toNonEmptyString(path)
  if (!recordData || !normalizedPath) return undefined

  const segments = normalizedPath.split('.').filter(Boolean)
  let current: unknown = recordData

  for (const segment of segments) {
    if (!current || typeof current !== 'object') {
      return undefined
    }
    current = (current as Record<string, unknown>)[segment]
  }

  return current
}

export const formatWorkbenchValue = (
  value: unknown,
  fallback: string,
  suffix = '',
  options?: {
    trueLabel?: string
    falseLabel?: string
  },
) => {
  if (value === null || value === undefined || value === '') {
    return fallback
  }

  if (typeof value === 'number') {
    return `${new Intl.NumberFormat().format(value)}${suffix}`
  }

  if (typeof value === 'boolean') {
    return value
      ? (options?.trueLabel || 'Yes')
      : (options?.falseLabel || 'No')
  }

  if (Array.isArray(value)) {
    return value.join(', ') || fallback
  }

  return `${String(value)}${suffix}`
}
