import request from '@/utils/request'

export type WorkbenchTranslate = (key: string) => string
export type WorkbenchHasTranslation = (key: string) => boolean

export type WorkbenchAction = Record<string, unknown> & {
  code: string
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
