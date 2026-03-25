import { userApi } from '@/api/users'
import { businessObjectApi } from '@/api/system'
import type { User } from '@/types/common'
import type { BusinessObject } from '@/types/businessObject'

export interface PermissionUserOption {
  label: string
  value: string
}

export interface PermissionObjectOption {
  label: string
  value: string
  appLabel: string
  model: string
}

interface BusinessObjectRegistryPayload {
  hardcoded?: unknown[]
  custom?: unknown[]
}

interface BusinessObjectPaginatedPayload {
  results?: unknown[]
}

const isRecord = (value: unknown): value is Record<string, unknown> => {
  return typeof value === 'object' && value !== null
}

const toBusinessObject = (value: unknown): BusinessObject | null => {
  if (!isRecord(value)) return null

  const code = typeof value.code === 'string' ? value.code : ''
  if (!code) return null

  return {
    id: typeof value.id === 'string' ? value.id : '',
    code,
    name: typeof value.name === 'string' ? value.name : code,
    nameEn: typeof value.nameEn === 'string' ? value.nameEn : undefined,
    djangoModelPath: typeof value.djangoModelPath === 'string' ? value.djangoModelPath : undefined,
    tableName: typeof value.tableName === 'string' ? value.tableName : undefined
  }
}

const resolveBusinessObjectList = (payload: unknown): BusinessObject[] => {
  if (Array.isArray(payload)) {
    return payload.map(toBusinessObject).filter((item): item is BusinessObject => !!item)
  }

  if (!isRecord(payload)) {
    return []
  }

  const paginated = payload as BusinessObjectPaginatedPayload
  if (Array.isArray(paginated.results)) {
    return paginated.results
      .map(toBusinessObject)
      .filter((item): item is BusinessObject => !!item)
  }

  const registry = payload as BusinessObjectRegistryPayload
  const hardcoded = Array.isArray(registry.hardcoded) ? registry.hardcoded : []
  const custom = Array.isArray(registry.custom) ? registry.custom : []

  return [...hardcoded, ...custom]
    .map(toBusinessObject)
    .filter((item): item is BusinessObject => !!item)
}

const parseModelFromTableName = (tableName?: string): { appLabel: string; model: string } | null => {
  if (!tableName) return null
  const parts = tableName.split('_').filter(Boolean)
  if (parts.length < 2) return null
  const appLabel = parts[0].toLowerCase()
  const model = parts.slice(1).join('_').toLowerCase()
  return { appLabel, model }
}

const parseModelFromDjangoPath = (djangoModelPath?: string): { appLabel: string; model: string } | null => {
  if (!djangoModelPath) return null

  const parts = djangoModelPath.split('.').filter(Boolean)
  if (parts.length < 2) return null

  const modelIndex = parts.indexOf('models')
  if (modelIndex > 0 && modelIndex < parts.length - 1) {
    const appLabel = parts[modelIndex - 1].toLowerCase()
    const model = parts[parts.length - 1].toLowerCase()
    return { appLabel, model }
  }

  const appLabel = parts[parts.length - 2].toLowerCase()
  const model = parts[parts.length - 1].toLowerCase()
  return { appLabel, model }
}

const toObjectOption = (object: BusinessObject): PermissionObjectOption => {
  const parsed = parseModelFromDjangoPath(object.djangoModelPath) || parseModelFromTableName(object.tableName)
  const appLabel = parsed?.appLabel || 'objects'
  const model = parsed?.model || object.code.toLowerCase()
  const value = `${appLabel}.${model}`
  return {
    label: `${object.name} (${object.code})`,
    value,
    appLabel,
    model
  }
}

const toUserOption = (user: User): PermissionUserOption => {
  const displayName = user.fullName || user.username
  return {
    label: `${displayName} (${user.username})`,
    value: user.username
  }
}

export const fetchPermissionUserOptions = async (search = ''): Promise<PermissionUserOption[]> => {
  const response = await userApi.list({
    page: 1,
    pageSize: 200,
    search: search.trim() || undefined
  })

  const users = Array.isArray(response.results) ? response.results : []
  return users.map(toUserOption)
}

export const fetchPermissionObjectOptions = async (search = ''): Promise<PermissionObjectOption[]> => {
  const payload = await businessObjectApi.list({
    page_size: 500,
    is_active: true,
    search: search.trim() || undefined
  })
  const objects = resolveBusinessObjectList(payload)
  return objects.map(toObjectOption)
}
