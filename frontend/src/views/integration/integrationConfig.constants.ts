import type {
  IntegrationFormData,
  KnownIntegrationHealthStatus,
  KnownIntegrationModuleType,
  KnownIntegrationSyncStatus,
  KnownIntegrationSystemType
} from '@/types/integration'

export type TranslateFn = (key: string) => string

export const SYSTEM_TYPE_OPTIONS: readonly KnownIntegrationSystemType[] = [
  'm18',
  'sap',
  'kingdee',
  'yonyou',
  'oracle',
  'odoo'
]

export const ENABLED_STATUS_OPTIONS = [true, false] as const

export const HEALTH_STATUS_OPTIONS: readonly KnownIntegrationHealthStatus[] = [
  'healthy',
  'degraded',
  'unhealthy'
]

export const MODULE_OPTIONS: readonly KnownIntegrationModuleType[] = [
  'procurement',
  'finance',
  'inventory',
  'hr',
  'crm'
]

const SYSTEM_TYPE_LABEL_FALLBACK: Record<KnownIntegrationSystemType, string> = {
  m18: 'M18',
  sap: 'SAP',
  kingdee: 'Kingdee',
  yonyou: 'Yonyou',
  oracle: 'Oracle EBS',
  odoo: 'Odoo'
}

const SYSTEM_TYPE_LABEL_KEYS: Record<KnownIntegrationSystemType, string> = {
  m18: 'integration.systemTypes.m18',
  sap: 'integration.systemTypes.sap',
  kingdee: 'integration.systemTypes.kingdee',
  yonyou: 'integration.systemTypes.yonyou',
  oracle: 'integration.systemTypes.oracle',
  odoo: 'integration.systemTypes.odoo'
}

export const SYSTEM_TYPE_TAG_TYPES: Record<KnownIntegrationSystemType, string> = {
  m18: 'primary',
  sap: 'success',
  kingdee: 'warning',
  yonyou: 'danger',
  oracle: 'info',
  odoo: ''
}

const HEALTH_STATUS_LABEL_FALLBACK: Record<KnownIntegrationHealthStatus, string> = {
  healthy: 'Healthy',
  degraded: 'Degraded',
  unhealthy: 'Unhealthy'
}

const HEALTH_STATUS_LABEL_KEYS: Record<KnownIntegrationHealthStatus, string> = {
  healthy: 'integration.healthStatus.healthy',
  degraded: 'integration.healthStatus.degraded',
  unhealthy: 'integration.healthStatus.unhealthy'
}

export const HEALTH_STATUS_TAG_TYPES: Record<KnownIntegrationHealthStatus, string> = {
  healthy: 'success',
  degraded: 'warning',
  unhealthy: 'danger'
}

const SYNC_STATUS_LABEL_FALLBACK: Record<KnownIntegrationSyncStatus, string> = {
  pending: 'Pending',
  running: 'Running',
  success: 'Success',
  partial_success: 'Partial',
  failed: 'Failed',
  cancelled: 'Cancelled'
}

const SYNC_STATUS_LABEL_KEYS: Record<KnownIntegrationSyncStatus, string> = {
  pending: 'integration.syncStatus.pending',
  running: 'integration.syncStatus.running',
  success: 'integration.syncStatus.success',
  partial_success: 'integration.syncStatus.partialSuccess',
  failed: 'integration.syncStatus.failed',
  cancelled: 'integration.syncStatus.cancelled'
}

export const SYNC_STATUS_TAG_TYPES: Record<KnownIntegrationSyncStatus, string> = {
  pending: 'info',
  running: 'warning',
  success: 'success',
  partial_success: 'warning',
  failed: 'danger',
  cancelled: 'info'
}

const MODULE_LABEL_FALLBACK: Record<KnownIntegrationModuleType, string> = {
  procurement: 'Procurement',
  finance: 'Finance',
  inventory: 'Inventory',
  hr: 'HR',
  crm: 'CRM'
}

const MODULE_LABEL_KEYS: Record<KnownIntegrationModuleType, string> = {
  procurement: 'integration.modules.procurement',
  finance: 'integration.modules.finance',
  inventory: 'integration.modules.inventory',
  hr: 'integration.modules.hr',
  crm: 'integration.modules.crm'
}

const translateWithFallback = <T extends string>(
  value: string,
  fallbackMap: Record<T, string>,
  keyMap: Record<T, string>,
  t?: TranslateFn
): string => {
  const typedValue = value as T
  const fallback = fallbackMap[typedValue] || value
  const translationKey = keyMap[typedValue]

  if (!translationKey || !t) {
    return fallback
  }

  const translated = t(translationKey)
  return translated === translationKey ? fallback : translated
}

export const createDefaultIntegrationFormData = (): IntegrationFormData => ({
  systemType: '',
  systemName: '',
  isEnabled: true,
  enabledModules: [],
  connectionConfig: {
    apiUrl: '',
    apiKey: '',
    apiSecret: '',
    timeout: 30
  },
  syncConfig: {
    autoSync: false,
    interval: 60
  }
})

export const getSystemTypeLabel = (type: string, t?: TranslateFn) =>
  translateWithFallback(type, SYSTEM_TYPE_LABEL_FALLBACK, SYSTEM_TYPE_LABEL_KEYS, t)

export const getSystemTypeTagType = (type: string) =>
  SYSTEM_TYPE_TAG_TYPES[type as KnownIntegrationSystemType] || ''

export const getHealthStatusLabel = (status: string, t?: TranslateFn) =>
  translateWithFallback(status, HEALTH_STATUS_LABEL_FALLBACK, HEALTH_STATUS_LABEL_KEYS, t)

export const getHealthStatusTagType = (status: string) =>
  HEALTH_STATUS_TAG_TYPES[status as KnownIntegrationHealthStatus] || ''

export const getSyncStatusLabel = (status: string, t?: TranslateFn) =>
  translateWithFallback(status, SYNC_STATUS_LABEL_FALLBACK, SYNC_STATUS_LABEL_KEYS, t)

export const getSyncStatusTagType = (status: string) =>
  SYNC_STATUS_TAG_TYPES[status as KnownIntegrationSyncStatus] || ''

export const getModuleLabel = (module: string, t?: TranslateFn) =>
  translateWithFallback(module, MODULE_LABEL_FALLBACK, MODULE_LABEL_KEYS, t)

export const getEnabledStatusLabel = (enabled: boolean, t: TranslateFn) =>
  enabled ? t('integration.status.enabled') : t('integration.status.disabled')

export const getEnabledStatusTagType = (enabled: boolean): string => (enabled ? 'success' : 'info')

export const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}
