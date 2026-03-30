type LooseString = string & Record<never, never>;

export type KnownIntegrationSystemType =
  | "m18"
  | "sap"
  | "kingdee"
  | "yonyou"
  | "oracle"
  | "odoo";
export type IntegrationSystemType = KnownIntegrationSystemType | LooseString;
export type KnownIntegrationFrameworkType = "m18" | "finance" | "oa" | "custom";
export type IntegrationFrameworkType =
  | KnownIntegrationFrameworkType
  | IntegrationSystemType
  | LooseString;

export type KnownIntegrationHealthStatus = "healthy" | "degraded" | "unhealthy";
export type IntegrationHealthStatus =
  | KnownIntegrationHealthStatus
  | LooseString;

export type KnownIntegrationSyncStatus =
  | "pending"
  | "running"
  | "success"
  | "partial_success"
  | "failed"
  | "cancelled";
export type IntegrationSyncStatus = KnownIntegrationSyncStatus | LooseString;
export type KnownSyncJobStatus = KnownIntegrationSyncStatus | "completed";
export type SyncJobStatus = KnownSyncJobStatus | LooseString;

export type KnownIntegrationModuleType =
  | "procurement"
  | "finance"
  | "inventory"
  | "hr"
  | "crm";
export type IntegrationModuleType = KnownIntegrationModuleType | LooseString;
export type KnownSyncDirection = "pull" | "push" | "bidirectional";
export type SyncDirection = KnownSyncDirection | LooseString;
export type KnownSyncJobType =
  | "purchase_orders"
  | "purchase_order"
  | "assets"
  | "asset"
  | "vendors"
  | "vendor"
  | "voucher"
  | "employee"
  | "customer"
  | "generic";
export type SyncJobType =
  | KnownSyncJobType
  | IntegrationModuleType
  | LooseString;

export type IntegrationLogAction = "pull" | "push" | "retry" | LooseString;

export interface IntegrationConnectionConfig {
  apiUrl?: string;
  apiKey?: string;
  apiSecret?: string;
  username?: string;
  password?: string;
  companyCode?: string;
  timeout?: number;
  [key: string]: unknown;
}

export interface IntegrationSyncConfig {
  autoSync?: boolean;
  interval?: number;
  syncInterval?: number;
  retryTimes?: number;
  [key: string]: unknown;
}

export interface M18Config {
  apiBaseUrl: string;
  apiKey: string;
  apiSecret: string;
  companyCode: string;
  autoSync: boolean;
  syncInterval: number;
  username?: string;
  password?: string;
  timeout?: number;
  syncOrders?: boolean;
  syncAssets?: boolean;
  syncVendors?: boolean;
  syncDepreciation?: boolean;
  startDate?: string;
}

export type M18SyncMode =
  | "purchaseOrders"
  | "vendors"
  | "assets"
  | "depreciation";

export interface M18SyncFormData {
  mode: M18SyncMode;
  dateRange: string[];
  orderNos: string;
  period: string;
}

export interface SyncJobResultError {
  record: string;
  error: string;
  businessId?: string;
}

export interface SyncJobResult {
  total: number;
  succeeded: number;
  failed: number;
  skipped: number;
  errors: SyncJobResultError[];
}

export interface IntegrationLog {
  id: string;
  syncTask?: { id?: string; taskId?: string } | string | null;
  taskId?: string | null;
  createdAt: string;
  systemType?: IntegrationSystemType;
  systemTypeDisplay?: string;
  integrationType: IntegrationFrameworkType;
  action: IntegrationLogAction;
  actionDisplay?: string;
  requestMethod: string;
  requestUrl?: string;
  statusCode: number;
  success: boolean;
  durationMs?: number;
  durationSeconds?: number;
  requestHeaders?: Record<string, unknown>;
  requestBody?: unknown;
  responseHeaders?: Record<string, unknown>;
  responseBody?: unknown;
  errorMessage?: string;
  businessType: string;
  businessId?: string;
  externalId?: string;
}

export interface IntegrationConfig {
  id: string;
  systemType: IntegrationSystemType;
  systemName: string;
  isEnabled: boolean;
  enabledModules: IntegrationModuleType[];
  connectionConfig: IntegrationConnectionConfig;
  syncConfig: IntegrationSyncConfig;
  mappingConfig?: Record<string, unknown>;
  healthStatus: IntegrationHealthStatus;
  lastSyncAt: string | null;
  lastSyncStatus: IntegrationSyncStatus | null;
  lastHealthCheckAt?: string | null;
  systemTypeDisplay?: string;
  healthStatusDisplay?: string;
  lastSyncStatusDisplay?: string;
  enabledModulesCount?: number;
  syncTasksCount?: number;
  recentLogs?: IntegrationLog[];
  name?: string;
  code?: string;
  integrationType?: IntegrationFrameworkType;
  config?: Record<string, unknown>;
  organizationId?: string;
  organization?:
    | {
        id: string;
        name?: string;
        code?: string;
      }
    | string
    | null;
}

export interface IntegrationFormData {
  systemType: IntegrationSystemType;
  systemName: string;
  isEnabled: boolean;
  enabledModules: IntegrationModuleType[];
  connectionConfig: IntegrationConnectionConfig;
  syncConfig: IntegrationSyncConfig;
  mappingConfig?: Record<string, unknown>;
}

export interface IntegrationConfigMutationPayload {
  systemName?: string;
  connectionConfig?: IntegrationConnectionConfig;
  enabledModules?: IntegrationModuleType[];
  syncConfig?: IntegrationSyncConfig;
  mappingConfig?: Record<string, unknown>;
  isEnabled?: boolean;
}

export interface SyncJob {
  id: string;
  integrationId: string;
  integrationName: string;
  jobType: SyncJobType;
  status: SyncJobStatus;
  progress: number;
  startedAt: string | null;
  completedAt?: string | null;
  result?: SyncJobResult;
  taskId?: string;
  config?:
    | {
        id: string;
        systemType?: IntegrationSystemType;
        systemName?: string;
      }
    | string
    | null;
  configId?: string;
  systemType?: IntegrationSystemType;
  systemName?: string;
  moduleType?: IntegrationModuleType | LooseString;
  moduleTypeDisplay?: string;
  direction?: SyncDirection;
  directionDisplay?: string;
  businessType?: string;
  syncParams?: Record<string, unknown>;
  statusDisplay?: string;
  status_display?: string;
  totalCount?: number;
  successCount?: number;
  failedCount?: number;
  progressPercentage?: number;
  errorSummary?: SyncJobResultError[];
  durationMs?: number | null;
  durationSeconds?: number | null;
  createdAt?: string;
  celeryTaskId?: string;
  isCompleted?: boolean;
  isRunning?: boolean;
  isFailed?: boolean;
  recentLogs?: IntegrationLog[];
}

export interface IntegrationStats {
  total: number;
  healthy: number;
  degraded: number;
  unhealthy: number;
}

export interface IntegrationFilterForm {
  systemType?: IntegrationSystemType;
  isEnabled?: boolean;
  healthStatus?: IntegrationHealthStatus;
}

export interface IntegrationConfigListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  systemType?: IntegrationSystemType;
  isEnabled?: boolean;
  healthStatus?: IntegrationHealthStatus;
  lastSyncStatus?: IntegrationSyncStatus;
  systemName?: string;
}

export interface IntegrationConfigStatsParams {
  systemType?: IntegrationSystemType;
  isEnabled?: boolean;
  healthStatus?: IntegrationHealthStatus;
  lastSyncStatus?: IntegrationSyncStatus;
  systemName?: string;
}

export interface SyncJobListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  integrationId?: string;
  configId?: string;
  systemType?: IntegrationSystemType;
  moduleType?: IntegrationModuleType | LooseString;
  status?: SyncJobStatus;
  dateFrom?: string;
  dateTo?: string;
}

export interface PurchaseOrderSync {
  startDate?: string;
  endDate?: string;
  orderNos?: string[];
  async: boolean;
  moduleType?: IntegrationModuleType | LooseString;
  direction?: SyncDirection;
  businessType?: string;
  execute?: boolean;
}

export interface TriggerSyncPayload {
  moduleType?: IntegrationModuleType | LooseString;
  businessType?: string;
  direction?: SyncDirection;
  syncParams?: Record<string, unknown>;
  async?: boolean;
  execute?: boolean;
}

export interface IntegrationLogListParams {
  page?: number;
  pageSize?: number;
  page_size?: number;
  systemType?: IntegrationSystemType;
  integrationType?: IntegrationFrameworkType;
  action?: IntegrationLogAction;
  success?: boolean;
  syncTaskId?: string;
  configId?: string;
  dateFrom?: string;
  dateTo?: string;
}
