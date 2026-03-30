import request from "@/utils/request";
import type { PaginatedResponse } from "@/types/api";
import type {
  IntegrationConfig,
  IntegrationConfigListParams,
  IntegrationConfigMutationPayload,
  IntegrationConfigStatsParams,
  IntegrationFormData,
  IntegrationLog,
  IntegrationLogListParams,
  IntegrationStats,
  PurchaseOrderSync,
  SyncJob,
  SyncJobListParams,
  SyncJobResult,
  SyncJobResultError,
  TriggerSyncPayload,
} from "@/types/integration";
import {
  normalizeQueryParams,
  toActionResult,
  toCamelDeep,
  toData,
  toPaginated,
  type ApiActionResult,
} from "@/api/contract";

type IntegrationLooseRecord = Record<string, unknown>;
type IntegrationLooseParams = Record<string, unknown>;

const isRecord = (value: unknown): value is IntegrationLooseRecord => {
  return value !== null && typeof value === "object" && !Array.isArray(value);
};

const toNumber = (value: unknown, fallback = 0): number => {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
};

function normalizeSyncJobResultError(value: unknown): SyncJobResultError {
  const record = toCamelDeep(value) as IntegrationLooseRecord;
  const sourceRecord =
    record.record ?? record.businessId ?? record.businessID ?? record.id ?? "";

  return {
    record: String(sourceRecord || ""),
    error: String(record.error ?? record.message ?? ""),
    businessId: record.businessId ? String(record.businessId) : undefined,
  };
}

function normalizeSyncJobResult(value: unknown): SyncJobResult {
  const record = toCamelDeep(value) as IntegrationLooseRecord;
  const total = toNumber(record.total ?? record.totalCount);
  const succeeded = toNumber(record.succeeded ?? record.successCount);
  const failed = toNumber(record.failed ?? record.failedCount);
  const errors = Array.isArray(record.errors)
    ? record.errors.map(normalizeSyncJobResultError)
    : Array.isArray(record.errorSummary)
      ? record.errorSummary.map(normalizeSyncJobResultError)
      : [];
  const skipped = toNumber(
    record.skipped ?? record.skippedCount,
    Math.max(total - succeeded - failed, 0),
  );

  return {
    total,
    succeeded,
    failed,
    skipped,
    errors,
  };
}

function normalizeIntegrationLog(value: unknown): IntegrationLog {
  const record = toCamelDeep(value) as IntegrationLooseRecord;
  const syncTask = isRecord(record.syncTask)
    ? {
        id: record.syncTask.id ? String(record.syncTask.id) : undefined,
        taskId: record.syncTask.taskId
          ? String(record.syncTask.taskId)
          : undefined,
      }
    : record.syncTask
      ? String(record.syncTask)
      : null;
  const durationValue = record.durationMs ?? record.durationSeconds;

  return {
    ...(record as Partial<IntegrationLog>),
    id: String(record.id ?? ""),
    syncTask,
    taskId: record.taskId
      ? String(record.taskId)
      : isRecord(record.taskInfo) && record.taskInfo.taskId
        ? String(record.taskInfo.taskId)
        : isRecord(syncTask) && syncTask.taskId
          ? String(syncTask.taskId)
          : null,
    createdAt: String(record.createdAt ?? ""),
    systemType: record.systemType ? String(record.systemType) : undefined,
    systemTypeDisplay: record.systemTypeDisplay
      ? String(record.systemTypeDisplay)
      : undefined,
    integrationType: String(record.integrationType ?? record.systemType ?? ""),
    action: String(record.action ?? ""),
    actionDisplay: record.actionDisplay
      ? String(record.actionDisplay)
      : undefined,
    requestMethod: String(record.requestMethod ?? ""),
    requestUrl: record.requestUrl ? String(record.requestUrl) : undefined,
    statusCode: toNumber(record.statusCode),
    success: Boolean(record.success),
    durationMs:
      durationValue === undefined || durationValue === null
        ? undefined
        : toNumber(durationValue),
    durationSeconds:
      record.durationSeconds === undefined || record.durationSeconds === null
        ? undefined
        : toNumber(record.durationSeconds),
    requestHeaders: isRecord(record.requestHeaders)
      ? record.requestHeaders
      : undefined,
    requestBody: record.requestBody,
    responseHeaders: isRecord(record.responseHeaders)
      ? record.responseHeaders
      : undefined,
    responseBody: record.responseBody,
    errorMessage: record.errorMessage ? String(record.errorMessage) : "",
    businessType: String(record.businessType ?? ""),
    businessId: record.businessId ? String(record.businessId) : undefined,
    externalId: record.externalId ? String(record.externalId) : undefined,
  };
}

function normalizeIntegrationConfig(value: unknown): IntegrationConfig {
  const record = toCamelDeep(value) as IntegrationLooseRecord;
  const organization = isRecord(record.organization)
    ? record.organization
    : undefined;
  const configRecord = isRecord(record.config) ? record.config : undefined;
  const connectionConfig = isRecord(record.connectionConfig)
    ? record.connectionConfig
    : isRecord(configRecord?.connectionConfig)
      ? (configRecord.connectionConfig as IntegrationLooseRecord)
      : {};
  const syncConfig = isRecord(record.syncConfig)
    ? record.syncConfig
    : isRecord(configRecord?.syncConfig)
      ? (configRecord.syncConfig as IntegrationLooseRecord)
      : {};
  const mappingConfig = isRecord(record.mappingConfig)
    ? record.mappingConfig
    : isRecord(configRecord?.mappingConfig)
      ? (configRecord.mappingConfig as IntegrationLooseRecord)
      : {};
  const recentLogs = Array.isArray(record.recentLogs)
    ? record.recentLogs.map(normalizeIntegrationLog)
    : [];
  const systemType = String(
    record.systemType ?? record.integrationType ?? record.code ?? "",
  );
  const systemName = String(record.systemName ?? record.name ?? systemType);

  return {
    ...(record as Partial<IntegrationConfig>),
    id: String(record.id ?? ""),
    systemType,
    systemName,
    isEnabled: Boolean(record.isEnabled),
    enabledModules: Array.isArray(record.enabledModules)
      ? record.enabledModules.map((module) => String(module))
      : [],
    connectionConfig,
    syncConfig,
    mappingConfig,
    healthStatus: String(record.healthStatus ?? "unhealthy"),
    lastSyncAt: record.lastSyncAt ? String(record.lastSyncAt) : null,
    lastSyncStatus: record.lastSyncStatus
      ? String(record.lastSyncStatus)
      : null,
    lastHealthCheckAt: record.lastHealthCheckAt
      ? String(record.lastHealthCheckAt)
      : null,
    systemTypeDisplay: record.systemTypeDisplay
      ? String(record.systemTypeDisplay)
      : undefined,
    healthStatusDisplay: record.healthStatusDisplay
      ? String(record.healthStatusDisplay)
      : undefined,
    lastSyncStatusDisplay: record.lastSyncStatusDisplay
      ? String(record.lastSyncStatusDisplay)
      : undefined,
    enabledModulesCount:
      record.enabledModulesCount === undefined
        ? undefined
        : toNumber(record.enabledModulesCount),
    syncTasksCount:
      record.syncTasksCount === undefined
        ? undefined
        : toNumber(record.syncTasksCount),
    recentLogs,
    name: String(record.name ?? systemName),
    code: String(record.code ?? systemType),
    integrationType: String(record.integrationType ?? systemType),
    config: {
      connectionConfig,
      syncConfig,
      mappingConfig,
      ...(configRecord || {}),
    },
    organizationId: record.organizationId
      ? String(record.organizationId)
      : organization?.id
        ? String(organization.id)
        : undefined,
    organization: organization
      ? {
          id: String(organization.id ?? ""),
          name: organization.name ? String(organization.name) : undefined,
          code: organization.code ? String(organization.code) : undefined,
        }
      : null,
  };
}

function normalizeSyncJob(value: unknown): SyncJob {
  const record = toCamelDeep(value) as IntegrationLooseRecord;
  const config = isRecord(record.config)
    ? {
        id: String(record.config.id ?? ""),
        systemType: record.config.systemType
          ? String(record.config.systemType)
          : undefined,
        systemName: record.config.systemName
          ? String(record.config.systemName)
          : undefined,
      }
    : null;
  const integrationId = String(
    record.integrationId ?? record.configId ?? config?.id ?? "",
  );
  const integrationName = String(
    record.integrationName ?? record.systemName ?? config?.systemName ?? "",
  );
  const totalCount = toNumber(record.totalCount ?? record.total);
  const successCount = toNumber(record.successCount ?? record.succeeded);
  const failedCount = toNumber(record.failedCount ?? record.failed);
  const errorSummary = Array.isArray(record.errorSummary)
    ? record.errorSummary.map(normalizeSyncJobResultError)
    : Array.isArray(record.errors)
      ? record.errors.map(normalizeSyncJobResultError)
      : [];
  const progressPercentage = toNumber(
    record.progressPercentage ?? record.progress,
    totalCount > 0
      ? Math.round(((successCount + failedCount) / totalCount) * 100)
      : 0,
  );
  const result = record.result
    ? normalizeSyncJobResult(record.result)
    : totalCount > 0 ||
        successCount > 0 ||
        failedCount > 0 ||
        errorSummary.length > 0
      ? {
          total: totalCount,
          succeeded: successCount,
          failed: failedCount,
          skipped: Math.max(totalCount - successCount - failedCount, 0),
          errors: errorSummary,
        }
      : undefined;
  const durationValue = record.durationMs ?? record.durationSeconds;

  return {
    ...(record as Partial<SyncJob>),
    id: String(record.id ?? ""),
    integrationId,
    integrationName,
    jobType: String(
      record.jobType ?? record.businessType ?? record.moduleType ?? "generic",
    ),
    status: String(record.status ?? "pending"),
    progress: Math.min(100, Math.max(0, progressPercentage)),
    startedAt: record.startedAt ? String(record.startedAt) : null,
    completedAt: record.completedAt ? String(record.completedAt) : null,
    result,
    taskId: record.taskId ? String(record.taskId) : undefined,
    config,
    configId: integrationId || undefined,
    systemType: record.systemType
      ? String(record.systemType)
      : config?.systemType,
    systemName: record.systemName
      ? String(record.systemName)
      : config?.systemName,
    moduleType: record.moduleType ? String(record.moduleType) : undefined,
    moduleTypeDisplay: record.moduleTypeDisplay
      ? String(record.moduleTypeDisplay)
      : undefined,
    direction: record.direction ? String(record.direction) : undefined,
    directionDisplay: record.directionDisplay
      ? String(record.directionDisplay)
      : undefined,
    businessType: record.businessType ? String(record.businessType) : undefined,
    syncParams: isRecord(record.syncParams) ? record.syncParams : undefined,
    statusDisplay: record.statusDisplay
      ? String(record.statusDisplay)
      : undefined,
    totalCount,
    successCount,
    failedCount,
    progressPercentage,
    errorSummary,
    durationMs:
      durationValue === undefined || durationValue === null
        ? null
        : toNumber(durationValue),
    durationSeconds:
      record.durationSeconds === undefined || record.durationSeconds === null
        ? null
        : toNumber(record.durationSeconds),
    createdAt: record.createdAt ? String(record.createdAt) : undefined,
    celeryTaskId: record.celeryTaskId ? String(record.celeryTaskId) : undefined,
    isCompleted:
      record.isCompleted === undefined
        ? undefined
        : Boolean(record.isCompleted),
    isRunning:
      record.isRunning === undefined ? undefined : Boolean(record.isRunning),
    isFailed:
      record.isFailed === undefined ? undefined : Boolean(record.isFailed),
    recentLogs: Array.isArray(record.recentLogs)
      ? record.recentLogs.map(normalizeIntegrationLog)
      : undefined,
  };
}

const mapPaginatedResponse = <T>(
  raw: unknown,
  normalizer: (value: unknown) => T,
): PaginatedResponse<T> => {
  const page = toPaginated(raw);
  return {
    ...page,
    results: page.results.map(normalizer),
  };
};

const toNormalizedActionResult = <T>(
  raw: unknown,
  normalizer?: (value: unknown) => T,
): ApiActionResult<T> => {
  const result = toActionResult(raw);
  return {
    ...result,
    data:
      result.data === undefined
        ? undefined
        : normalizer
          ? normalizer(result.data)
          : (toCamelDeep(result.data) as T),
  };
};

const ensureActionData = <T>(
  result: ApiActionResult<T>,
  fallbackMessage: string,
): T => {
  if (result.success && result.data !== undefined) {
    return result.data;
  }

  throw new Error(result.message || fallbackMessage);
};

const normalizeConfigParams = (
  params?: IntegrationConfigListParams | IntegrationConfigStatsParams,
) => {
  return normalizeQueryParams(params as IntegrationLooseParams | undefined, {
    aliases: {
      pageSize: "page_size",
    },
    preserveKeys: ["page", "page_size"],
  });
};

const normalizeSyncJobParams = (
  params?: SyncJobListParams | IntegrationLooseParams,
) => {
  return normalizeQueryParams(params, {
    aliases: {
      pageSize: "page_size",
      integrationId: "config",
      configId: "config",
      dateFrom: "started_at_from",
      dateTo: "started_at_to",
    },
    preserveKeys: ["page", "page_size"],
  });
};

const normalizeLogParams = (params?: IntegrationLogListParams) => {
  return normalizeQueryParams(params as IntegrationLooseParams | undefined, {
    aliases: {
      pageSize: "page_size",
      syncTaskId: "sync_task",
      dateFrom: "created_at_from",
      dateTo: "created_at_to",
    },
    preserveKeys: ["page", "page_size"],
  });
};

export const integrationConfigApi = {
  list(
    params?: IntegrationConfigListParams,
  ): Promise<PaginatedResponse<IntegrationConfig>> {
    return request
      .get("/integration/configs/", {
        params: normalizeConfigParams(params),
      })
      .then((res) => mapPaginatedResponse(res, normalizeIntegrationConfig));
  },

  stats(params?: IntegrationConfigStatsParams): Promise<IntegrationStats> {
    return request
      .get("/integration/configs/stats/", {
        params: normalizeConfigParams(params),
      })
      .then((res) => toCamelDeep(toData(res)) as IntegrationStats);
  },

  detail(id: string): Promise<IntegrationConfig> {
    return request
      .get(`/integration/configs/${id}/`)
      .then((res) => normalizeIntegrationConfig(toData(res)));
  },

  create(
    data: IntegrationFormData | IntegrationConfigMutationPayload,
  ): Promise<ApiActionResult<IntegrationConfig>> {
    return request
      .post("/integration/configs/", data, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res, normalizeIntegrationConfig));
  },

  update(
    id: string,
    data: IntegrationFormData | IntegrationConfigMutationPayload,
  ): Promise<ApiActionResult<IntegrationConfig>> {
    return request
      .put(`/integration/configs/${id}/`, data, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res, normalizeIntegrationConfig));
  },

  delete(id: string): Promise<ApiActionResult<void>> {
    return request
      .delete(`/integration/configs/${id}/`, { unwrap: "none" })
      .then((res) => toActionResult(res));
  },

  test(id: string): Promise<ApiActionResult<Record<string, unknown>>> {
    return request
      .post(`/integration/configs/${id}/test/`, undefined, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res));
  },

  sync(
    id: string,
    data?: TriggerSyncPayload,
  ): Promise<ApiActionResult<SyncJob>> {
    return request
      .post(`/integration/configs/${id}/sync/`, data, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res, normalizeSyncJob));
  },
};

export const syncTaskApi = {
  list(
    params?: SyncJobListParams | IntegrationLooseParams,
  ): Promise<PaginatedResponse<SyncJob>> {
    return request
      .get("/integration/sync-tasks/", {
        params: normalizeSyncJobParams(params),
      })
      .then((res) => mapPaginatedResponse(res, normalizeSyncJob));
  },

  detail(id: string): Promise<SyncJob> {
    return request
      .get(`/integration/sync-tasks/${id}/`)
      .then((res) => normalizeSyncJob(toData(res)));
  },

  execute(id: string): Promise<ApiActionResult<Record<string, unknown>>> {
    return request
      .post(`/integration/sync-tasks/${id}/execute/`, undefined, {
        unwrap: "none",
      })
      .then((res) => toNormalizedActionResult(res));
  },

  cancel(id: string): Promise<ApiActionResult<Record<string, unknown>>> {
    return request
      .post(`/integration/sync-tasks/${id}/cancel/`, undefined, {
        unwrap: "none",
      })
      .then((res) => toNormalizedActionResult(res));
  },

  retry(id: string): Promise<ApiActionResult<SyncJob>> {
    return request
      .post(`/integration/sync-tasks/${id}/retry/`, undefined, {
        unwrap: "none",
      })
      .then((res) => toNormalizedActionResult(res, normalizeSyncJob));
  },
};

export const integrationLogApi = {
  list(
    params?: IntegrationLogListParams,
  ): Promise<PaginatedResponse<IntegrationLog>> {
    return request
      .get("/integration/logs/", {
        params: normalizeLogParams(params),
      })
      .then((res) => mapPaginatedResponse(res, normalizeIntegrationLog));
  },

  detail(id: string): Promise<IntegrationLog> {
    return request
      .get(`/integration/logs/${id}/`)
      .then((res) => normalizeIntegrationLog(toData(res)));
  },

  retry(id: string): Promise<ApiActionResult<Record<string, unknown>>> {
    return request
      .post(`/integration/logs/${id}/retry/`, undefined, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res));
  },
};

export const dataMappingApi = {
  list(
    params?: IntegrationLooseParams,
  ): Promise<PaginatedResponse<IntegrationLooseRecord>> {
    return request
      .get("/integration/mappings/", {
        params: normalizeQueryParams(params, {
          preserveKeys: ["page", "page_size"],
        }),
      })
      .then((res) => {
        const page = toPaginated(res);
        return {
          ...page,
          results: toCamelDeep(page.results) as IntegrationLooseRecord[],
        };
      });
  },

  detail(id: string): Promise<IntegrationLooseRecord> {
    return request
      .get(`/integration/mappings/${id}/`)
      .then((res) => toCamelDeep(toData(res)) as IntegrationLooseRecord);
  },

  create(
    data: IntegrationLooseRecord,
  ): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .post("/integration/mappings/", data, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res));
  },

  update(
    id: string,
    data: IntegrationLooseRecord,
  ): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .put(`/integration/mappings/${id}/`, data, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res));
  },

  delete(id: string): Promise<ApiActionResult<void>> {
    return request
      .delete(`/integration/mappings/${id}/`, { unwrap: "none" })
      .then((res) => toActionResult(res));
  },

  test(
    id: string,
    data: IntegrationLooseRecord,
  ): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .post(`/integration/mappings/${id}/test/`, data, { unwrap: "none" })
      .then((res) => toNormalizedActionResult(res));
  },
};

export const getConfigs = async (
  params?: IntegrationConfigListParams,
): Promise<IntegrationConfig[]> => {
  const response = await integrationConfigApi.list(params);
  return response.results;
};

export const getConfig = (id: string): Promise<IntegrationConfig> => {
  return integrationConfigApi.detail(id);
};

export const createConfig = async (
  data: IntegrationFormData | IntegrationConfigMutationPayload,
): Promise<IntegrationConfig> => {
  return ensureActionData(
    await integrationConfigApi.create(data),
    "Failed to create integration config.",
  );
};

export const updateConfig = async (
  id: string,
  data: IntegrationFormData | IntegrationConfigMutationPayload,
): Promise<IntegrationConfig> => {
  return ensureActionData(
    await integrationConfigApi.update(id, data),
    "Failed to update integration config.",
  );
};

export const testConnection = (
  id: string,
): Promise<ApiActionResult<Record<string, unknown>>> => {
  return integrationConfigApi.test(id);
};

export const getSyncJobs = (
  params?: SyncJobListParams,
): Promise<PaginatedResponse<SyncJob>> => {
  return syncTaskApi.list(params);
};

export const getSyncJob = (id: string): Promise<SyncJob> => {
  return syncTaskApi.detail(id);
};

export const triggerSync = async (
  integrationId: string,
  data?: PurchaseOrderSync | TriggerSyncPayload,
): Promise<SyncJob> => {
  return ensureActionData(
    await integrationConfigApi.sync(integrationId, data),
    "Failed to trigger sync job.",
  );
};

export const retrySyncJob = async (id: string): Promise<SyncJob> => {
  return ensureActionData(
    await syncTaskApi.retry(id),
    "Failed to retry sync job.",
  );
};

export const getLogs = (
  params?: IntegrationLogListParams,
): Promise<PaginatedResponse<IntegrationLog>> => {
  return integrationLogApi.list(params);
};

export const getLog = (id: string): Promise<IntegrationLog> => {
  return integrationLogApi.detail(id);
};

export const integrationApi = {
  getConfigs,
  getConfig,
  createConfig,
  updateConfig,
  testConnection,
  getSyncJobs,
  getSyncJob,
  triggerSync,
  retrySyncJob,
  getLogs,
  getLog,
};

export const getIntegrationConfigList = integrationConfigApi.list;
export const getIntegrationConfigStats = integrationConfigApi.stats;
export const getIntegrationConfigDetail = integrationConfigApi.detail;
export const createIntegrationConfig = integrationConfigApi.create;
export const updateIntegrationConfig = integrationConfigApi.update;
export const deleteIntegrationConfig = integrationConfigApi.delete;
export const testIntegrationConnection = integrationConfigApi.test;
export const syncIntegrationData = integrationConfigApi.sync;

export const getSyncTaskList = syncTaskApi.list;
export const getSyncTaskDetail = syncTaskApi.detail;
export const executeSyncTask = syncTaskApi.execute;
export const cancelSyncTask = syncTaskApi.cancel;

export const getIntegrationLogList = integrationLogApi.list;
export const getIntegrationLogDetail = integrationLogApi.detail;
export const retryIntegrationLog = integrationLogApi.retry;

export const getDataMappingTemplateList = dataMappingApi.list;
export const getDataMappingTemplateDetail = dataMappingApi.detail;
export const createDataMappingTemplate = dataMappingApi.create;
export const updateDataMappingTemplate = dataMappingApi.update;
export const deleteDataMappingTemplate = dataMappingApi.delete;
export const testDataMapping = dataMappingApi.test;
