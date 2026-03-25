import type { RuntimePermissions } from '@/platform/layout/runtimeLayoutResolver'
import type { SearchField } from '@/types/common'

export interface DynamicListResolvedPermissions {
  view: boolean
  add: boolean
  change: boolean
  delete: boolean
}

const fallbackPermissions: DynamicListResolvedPermissions = {
  view: true,
  add: true,
  change: true,
  delete: true,
}

const reservedRouteFilterKeys = new Set([
  'action',
  'layoutId',
  'layoutType',
  'mode',
  'objectCode',
  'objectName',
])

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

export const extractDynamicListRouteFilters = (routeQuery: unknown): Record<string, any> => {
  if (!routeQuery || typeof routeQuery !== 'object') return {}

  return Object.entries(routeQuery).reduce((acc, [key, value]) => {
    if (reservedRouteFilterKeys.has(key) || value === undefined || value === null || value === '') {
      return acc
    }
    acc[key] = Array.isArray(value) ? value[0] : value
    return acc
  }, {} as Record<string, any>)
}

export const shouldRefreshDynamicListOnPathChange = ({
  newPath,
  oldPath,
  objectCode,
}: {
  newPath?: string | null
  oldPath?: string | null
  objectCode: string
}) => {
  if (!oldPath || !newPath || newPath === oldPath || !objectCode) return false

  const pattern = new RegExp(`/objects/${escapeRegExp(objectCode)}$`)
  return pattern.test(newPath) && !pattern.test(oldPath)
}

export const resolveDynamicListEffectivePermissions = (
  runtimePermissions?: RuntimePermissions | null,
  metadataPermissions?: Partial<DynamicListResolvedPermissions> | null,
): DynamicListResolvedPermissions => {
  if (runtimePermissions) {
    return runtimePermissions
  }

  if (metadataPermissions) {
    return {
      view: metadataPermissions.view !== false,
      add: metadataPermissions.add !== false,
      change: metadataPermissions.change !== false,
      delete: metadataPermissions.delete !== false,
    }
  }

  return fallbackPermissions
}

export const buildDynamicListUnifiedSearchFields = (
  rawSearchFields: SearchField[],
  searchLabel: string,
): SearchField[] => {
  return [
    ...rawSearchFields,
    {
      prop: '__unifiedKeyword',
      label: searchLabel,
      type: 'slot',
      defaultValue: '',
    },
  ]
}
