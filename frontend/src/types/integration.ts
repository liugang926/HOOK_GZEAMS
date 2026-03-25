type LooseString = string & Record<never, never>

export type KnownIntegrationSystemType = 'm18' | 'sap' | 'kingdee' | 'yonyou' | 'oracle' | 'odoo'
export type IntegrationSystemType = KnownIntegrationSystemType | LooseString

export type KnownIntegrationHealthStatus = 'healthy' | 'degraded' | 'unhealthy'
export type IntegrationHealthStatus = KnownIntegrationHealthStatus | LooseString

export type KnownIntegrationSyncStatus =
  | 'pending'
  | 'running'
  | 'success'
  | 'partial_success'
  | 'failed'
  | 'cancelled'
export type IntegrationSyncStatus = KnownIntegrationSyncStatus | LooseString

export type KnownIntegrationModuleType = 'procurement' | 'finance' | 'inventory' | 'hr' | 'crm'
export type IntegrationModuleType = KnownIntegrationModuleType | LooseString

export type IntegrationLogAction = 'pull' | 'push' | LooseString

export interface IntegrationConnectionConfig {
  apiUrl?: string
  apiKey?: string
  apiSecret?: string
  timeout?: number
  [key: string]: unknown
}

export interface IntegrationSyncConfig {
  autoSync?: boolean
  interval?: number
  [key: string]: unknown
}

export interface IntegrationConfig {
  id: string
  systemType: IntegrationSystemType
  systemName: string
  isEnabled: boolean
  enabledModules: IntegrationModuleType[]
  connectionConfig: IntegrationConnectionConfig
  syncConfig: IntegrationSyncConfig
  healthStatus: IntegrationHealthStatus
  lastSyncAt: string | null
  lastSyncStatus: IntegrationSyncStatus | null
}

export interface IntegrationFormData {
  systemType: IntegrationSystemType
  systemName: string
  isEnabled: boolean
  enabledModules: IntegrationModuleType[]
  connectionConfig: IntegrationConnectionConfig
  syncConfig: IntegrationSyncConfig
}

export interface IntegrationLog {
  id: string
  syncTask?: string | null
  taskId?: string | null
  createdAt: string
  integrationType: IntegrationSystemType
  action: IntegrationLogAction
  requestMethod: string
  statusCode: number
  success: boolean
  durationMs: number
  durationSeconds?: number
  requestBody: unknown
  responseBody: unknown
  errorMessage: string
  businessType: string
}

export interface IntegrationStats {
  total: number
  healthy: number
  degraded: number
  unhealthy: number
}

export interface IntegrationFilterForm {
  systemType?: IntegrationSystemType
  isEnabled?: boolean
  healthStatus?: IntegrationHealthStatus
}

export interface IntegrationConfigListParams {
  page?: number
  page_size?: number
  systemType?: IntegrationSystemType
  isEnabled?: boolean
  healthStatus?: IntegrationHealthStatus
}

export interface IntegrationConfigStatsParams {
  systemType?: IntegrationSystemType
  isEnabled?: boolean
  healthStatus?: IntegrationHealthStatus
}

export interface IntegrationLogListParams {
  page?: number
  page_size?: number
  systemType?: IntegrationSystemType
}
