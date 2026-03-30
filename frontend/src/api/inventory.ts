/**
 * Inventory API Service
 *
 * Now using unified Dynamic Object Routing for all inventory-related operations.
 * Reference: docs/plans/phase4_1_inventory_qr/frontend_v2.md
 */

import request from "@/utils/request";
import {
  normalizeQueryParams,
  rejectUnsupportedApi,
  toData,
  toPaginated,
} from "@/api/contract";
import { BaseApiService } from "@/api/base";
import type { BatchResponse, PaginatedResponse } from "@/types/api";
import type {
  AssignmentProgress,
  CreateInventoryReconciliationPayload,
  DifferenceAdjustment,
  DifferenceResolution,
  GenerateInventoryReportPayload,
  InventoryDifference,
  InventoryReport,
  InventoryReconciliation,
  InventoryTaskAssignment,
  InventoryTask,
  InventorySnapshot,
  ReconciliationAdjustment,
  ReassignmentRequest,
  TaskAssignment,
} from "@/types/inventory";
import {
  inventoryReconciliationApi,
  inventoryReportApi,
  inventorySnapshotApi,
  inventoryTaskApi,
} from "@/api/dynamic";

const asRecord = (value: unknown): Record<string, unknown> => {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
};

const resolveExecutorName = (value: Record<string, unknown>) => {
  return String(
    value.assigneeName ||
      value.assignee_name ||
      value.executorName ||
      value.executor_name ||
      value.executorUsername ||
      value.executor_username ||
      "",
  ).trim();
};

const mapExecutorAssignment = (
  taskId: string,
  payload: unknown,
): InventoryTaskAssignment => {
  const data = asRecord(payload);
  const assigneeId = String(
    data.assigneeId || data.assignee_id || data.executorId || data.executor_id || "",
  );
  const completedCount = Number(
    data.scanCount || data.scan_count || data.completedCount || data.completed_count || 0,
  );

  return {
    id: String(data.id || assigneeId),
    taskId,
    assigneeId,
    assigneeName: resolveExecutorName(data),
    assignedBy: "",
    assignedAt: String(data.assignedAt || data.assigned_at || data.createdAt || data.created_at || ""),
    status: completedCount > 0 ? "in_progress" : "pending",
    scanCount: completedCount,
    assetCount: Number(data.assetCount || data.asset_count || 0),
    region: String(data.region || ""),
    locationIds: Array.isArray(data.locationIds)
      ? data.locationIds.map((item) => String(item))
      : Array.isArray(data.location_ids)
        ? data.location_ids.map((item) => String(item))
        : [],
    locationNames: Array.isArray(data.locationNames)
      ? data.locationNames.map((item) => String(item))
      : Array.isArray(data.location_names)
        ? data.location_names.map((item) => String(item))
        : [],
  };
};

const normalizeDifferenceType = (value?: string) => {
  if (!value) return value;
  return value === "extra" ? "surplus" : value;
};

const normalizeDifferenceQuery = (params?: Record<string, unknown>) => {
  const next = { ...(params || {}) };
  if (typeof next.differenceType === "string") {
    next.differenceType = normalizeDifferenceType(next.differenceType);
  }
  return normalizeQueryParams(next, {
    aliases: {
      pageSize: "page_size",
      taskId: "task",
      differenceType: "difference_type",
      assetCode: "asset_code",
      assetName: "asset_name",
    },
  });
};

const normalizeBatchResponse = (
  payload: unknown,
  ids: string[],
): BatchResponse => {
  const data = asRecord(payload);

  if (
    asRecord(data.summary).total !== undefined &&
    Array.isArray(data.results)
  ) {
    return {
      summary: {
        total: Number(asRecord(data.summary).total ?? ids.length),
        succeeded: Number(asRecord(data.summary).succeeded ?? 0),
        failed: Number(asRecord(data.summary).failed ?? 0),
      },
      results: data.results.map((entry) => {
        const item = asRecord(entry);
        return {
          id: String(item.id || item.differenceId || item.difference_id || ""),
          success: Boolean(item.success),
          error: item.error ? String(item.error) : undefined,
        };
      }),
    };
  }

  const errors = Array.isArray(data.errors)
    ? data.errors.map((item) => asRecord(item))
    : [];
  const errorMap = new Map(
    errors
      .map((item) => ({
        id: String(item.id || item.differenceId || item.difference_id || ""),
        error: String(item.error || item.message || "Operation failed"),
      }))
      .filter((item) => item.id)
      .map((item) => [item.id, item.error]),
  );

  const results = ids.map((id) => ({
    id,
    success: !errorMap.has(id),
    error: errorMap.get(id),
  }));

  const failed = Number(data.failed ?? errorMap.size);
  const succeeded = Number(data.succeeded ?? Math.max(ids.length - failed, 0));

  return {
    summary: {
      total: Number(data.total ?? ids.length),
      succeeded,
      failed,
    },
    results,
  };
};

/**
 * Inventory Task API service using Dynamic Object Routing
 */
class InventoryTaskApiService extends BaseApiService<InventoryTask> {
  constructor() {
    super("inventory/tasks");
  }

  /**
   * List inventory tasks (delegates to dynamic API)
   */
  async list(params?: any): Promise<PaginatedResponse<InventoryTask>> {
    return toPaginated<InventoryTask>(await inventoryTaskApi.list(params));
  }

  /**
   * Get single task (delegates to dynamic API)
   */
  async get(id: string, params?: any): Promise<InventoryTask> {
    return toData<InventoryTask>(await inventoryTaskApi.get(id, params));
  }

  /**
   * Create task (delegates to dynamic API)
   */
  async create(data: Partial<InventoryTask>): Promise<InventoryTask> {
    return toData<InventoryTask>(await inventoryTaskApi.create(data));
  }

  /**
   * Update task (delegates to dynamic API)
   */
  async update(
    id: string,
    data: Partial<InventoryTask>,
  ): Promise<InventoryTask> {
    return toData<InventoryTask>(await inventoryTaskApi.update(id, data));
  }

  /**
   * Delete task (delegates to dynamic API)
   */
  async delete(id: string): Promise<void> {
    await inventoryTaskApi.delete(id);
  }

  // ---------------------------------------------------------------------------
  // Low-code runtime compatibility helpers
  // ---------------------------------------------------------------------------
  // Some pages/components (e.g. BaseListPage-based views) expect the unified
  // object-router pagination shape: `{ count, next, previous, results }`.
  // These helpers bridge that expectation without forcing a full UI refactor.

  async listTasks(params?: any): Promise<any> {
    const next = { ...(params || {}) };
    if (next.pageSize !== undefined && next.page_size === undefined) {
      next.page_size = next.pageSize;
      delete next.pageSize;
    }
    return inventoryTaskApi.list(next);
  }

  async getTask(id: string, params?: any): Promise<any> {
    return inventoryTaskApi.get(id, params);
  }

  async createTask(data: Partial<InventoryTask>): Promise<any> {
    return inventoryTaskApi.create(data as any);
  }

  async updateTask(id: string, data: Partial<InventoryTask>): Promise<any> {
    return inventoryTaskApi.update(id, data as any);
  }

  async deleteTask(id: string): Promise<void> {
    await inventoryTaskApi.delete(id);
  }

  async batchDeleteTasks(ids: string[]): Promise<any> {
    return inventoryTaskApi.batchDelete(ids);
  }

  /**
   * Start inventory task (custom action endpoint)
   */
  start(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryTask/${id}/start/`);
  }

  /**
   * Complete inventory task (custom action endpoint)
   */
  complete(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryTask/${id}/complete/`);
  }

  /**
   * Get assignment records for a task.
   */
  async getAssignments(taskId: string): Promise<InventoryTaskAssignment[]> {
    const payload = toData<unknown[]>(
      await request.get(`/inventory/tasks/${taskId}/executors/`),
      [],
    );
    return Array.isArray(payload)
      ? payload.map((item) => mapExecutorAssignment(taskId, item))
      : [];
  }

  /**
   * Create task assignments.
   */
  async createAssignment(data: TaskAssignment): Promise<void> {
    await request.post(`/inventory/tasks/${data.taskId}/executors/`, {
      executorIds: data.assigneeIds,
    });
  }

  /**
   * Remove a task assignment by assignee.
   */
  async removeAssignment(taskId: string, assigneeId: string): Promise<void> {
    await request.delete(
      `/inventory/tasks/${taskId}/executors/${assigneeId}/`,
    );
  }

  /**
   * Reassign task ownership.
   */
  async reassign(data: ReassignmentRequest): Promise<void> {
    const taskIds = Array.from(new Set((data.taskIds || []).map((item) => String(item)).filter(Boolean)));
    for (const taskId of taskIds) {
      await this.createAssignment({
        taskId,
        assigneeIds: [data.toAssigneeId],
      });
      await this.removeAssignment(taskId, data.fromAssigneeId);
    }
  }

  /**
   * Get assignment progress for a task.
   */
  async getAssignmentProgress(taskId: string): Promise<AssignmentProgress[]> {
    return toData<AssignmentProgress[]>(
      await request.get(`/inventory/tasks/${taskId}/executors/progress/`),
      [],
    );
  }

  /**
   * Cancel inventory task (custom action endpoint)
   */
  cancel(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryTask/${id}/cancel/`);
  }

  /**
   * Get task snapshots (custom action endpoint)
   */
  getSnapshots(
    taskId: string,
    params?: {
      page?: number;
      pageSize?: number;
      filter?: "all" | "scanned" | "unscanned" | "abnormal";
    },
  ): Promise<PaginatedResponse<InventorySnapshot>> {
    return request.get(`/system/objects/InventoryTask/${taskId}/snapshots/`, {
      params,
    });
  }

  /**
   * Scan asset during inventory (custom action endpoint)
   */
  scanAsset(
    taskId: string,
    data: {
      qrCode: string;
      actualLocation?: string;
      actualLocationId?: string;
    },
  ): Promise<InventorySnapshot> {
    return request.post(`/system/objects/InventoryTask/${taskId}/scan/`, data);
  }

  /**
   * Confirm/Update snapshot result (custom action endpoint)
   */
  confirmSnapshot(
    taskId: string,
    snapshotId: string,
    data: {
      result: string;
      remark?: string;
      imageUrl?: string;
      userId?: string;
    },
  ): Promise<void> {
    return request.post(
      `/system/objects/InventoryTask/${taskId}/snapshots/${snapshotId}/confirm/`,
      data,
    );
  }

  /**
   * Get recent scanned items for real-time updates (custom endpoint)
   */
  getRecentTags(taskId: string): Promise<{
    items: InventorySnapshot[];
    scannedCount: number;
  }> {
    return request.get(`/system/objects/InventoryTask/${taskId}/recent-tags/`);
  }

  /**
   * Download task-level inventory report file.
   */
  downloadTaskReport(taskId: string): Promise<Blob> {
    return request.get(`/system/objects/InventoryTask/${taskId}/report/`, {
      responseType: "blob",
    });
  }

  /**
   * Create a task snapshot.
   */
  async createSnapshot(taskId: string): Promise<InventorySnapshot> {
    const response = await request.post(
      `/inventory/tasks/${taskId}/snapshot/`,
      {},
    );
    const payload = asRecord(response);
    const snapshotId = payload.snapshotId || payload.snapshot_id || payload.id;

    if (snapshotId) {
      return this.getSnapshot(String(snapshotId));
    }

    if (payload.id || payload.taskId || payload.task || payload.snapshotData) {
      return response as InventorySnapshot;
    }

    return this.getSnapshotByTask(taskId);
  }

  /**
   * Get a snapshot by ID.
   */
  async getSnapshot(id: string): Promise<InventorySnapshot> {
    return request.get(`/inventory/snapshots/${id}/`);
  }

  /**
   * Get the latest snapshot for a task.
   */
  async getSnapshotByTask(taskId: string): Promise<InventorySnapshot> {
    const response = await request.get("/inventory/snapshots/", {
      params: normalizeQueryParams(
        { taskId, pageSize: 1 },
        {
          aliases: {
            taskId: "task",
            pageSize: "page_size",
          },
        },
      ),
    });

    const payload = asRecord(response);
    if (payload.id && !Array.isArray(payload.results)) {
      return response as InventorySnapshot;
    }

    const paginated = toPaginated<InventorySnapshot>(response);
    const snapshot = paginated.results[0];

    if (!snapshot) {
      throw new Error("Inventory snapshot not found.");
    }

    return snapshot;
  }

  /**
   * Get paginated differences.
   */
  async getDifferences(
    params?: Record<string, unknown>,
  ): Promise<PaginatedResponse<InventoryDifference>> {
    return toPaginated<InventoryDifference>(
      await request.get("/inventory/differences/", {
        params: normalizeDifferenceQuery(params),
      }),
    );
  }

  /**
   * Resolve differences in batch.
   *
   * The frontend action model keeps `confirm` and `adjust` semantics.
   * Internally this method maps them to the available backend actions.
   */
  async resolveDifferences(data: DifferenceResolution): Promise<BatchResponse> {
    const differenceIds = Array.from(
      new Set(
        (data.differenceIds || []).map((id) => String(id)).filter(Boolean),
      ),
    );

    if (differenceIds.length === 0) {
      return {
        summary: {
          total: 0,
          succeeded: 0,
          failed: 0,
        },
        results: [],
      };
    }

    if (data.action === "confirm") {
      const settled = await Promise.allSettled(
        differenceIds.map((id) => this.confirmDifference(id, data.remark)),
      );

      const results = settled.map((item, index) => {
        const reason = item.status === "rejected" ? asRecord(item.reason) : {};
        return {
          id: differenceIds[index],
          success: item.status === "fulfilled",
          error:
            item.status === "rejected"
              ? String(reason.message || "Operation failed")
              : undefined,
        };
      });

      const failed = results.filter((item) => !item.success).length;

      return {
        summary: {
          total: differenceIds.length,
          succeeded: differenceIds.length - failed,
          failed,
        },
        results,
      };
    }

    const response = await request.post(
      "/inventory/differences/batch-resolve/",
      {
        ids: differenceIds,
        status: "resolved",
        resolution: data.remark || "",
      },
    );

    return normalizeBatchResponse(response, differenceIds);
  }

  /**
   * Confirm a single difference.
   */
  async confirmDifference(
    id: string,
    remark?: string,
    ownerId?: string,
  ): Promise<InventoryDifference> {
    return request.post(`/inventory/differences/${id}/confirm/`, {
      remark,
      ownerId,
    });
  }

  /**
   * Execute an asset adjustment for a difference.
   */
  async adjustAsset(
    differenceId: string,
    adjustData: DifferenceAdjustment = {},
  ): Promise<InventoryDifference> {
    const resolution = String(
      adjustData.resolution || adjustData.remark || "",
    ).trim();

    return request.post(
      `/inventory/differences/${differenceId}/execute-resolution/`,
      {
        resolution: resolution || "Inventory difference adjusted.",
        syncAsset: adjustData.syncAsset ?? true,
        linkedActionCode: adjustData.linkedActionCode,
      },
    );
  }

  /**
   * List reconciliation records.
   */
  async getReconciliations(
    params?: Record<string, unknown>,
  ): Promise<PaginatedResponse<InventoryReconciliation>> {
    return toPaginated<InventoryReconciliation>(
      await inventoryReconciliationApi.list(
        normalizeQueryParams(params, {
          aliases: {
            pageSize: "page_size",
            taskId: "task",
            dateFrom: "reconciled_at_from",
            dateTo: "reconciled_at_to",
          },
        }),
      ),
    );
  }

  /**
   * Create a reconciliation record.
   */
  async createReconciliation(
    data: CreateInventoryReconciliationPayload,
  ): Promise<InventoryReconciliation> {
    return toData<InventoryReconciliation>(
      await inventoryReconciliationApi.create({
        task: data.taskId,
        note: data.note,
      }),
    );
  }

  /**
   * List adjustment records.
   */
  async getAdjustments(
    _params?: Record<string, unknown>,
  ): Promise<PaginatedResponse<ReconciliationAdjustment>> {
    return rejectUnsupportedApi(
      "inventory adjustment",
      "/inventory/adjustments/",
    );
  }

  /**
   * List inventory reports.
   */
  async getReports(
    params?: Record<string, unknown>,
  ): Promise<PaginatedResponse<InventoryReport>> {
    return toPaginated<InventoryReport>(
      await inventoryReportApi.list(
        normalizeQueryParams(params, {
          aliases: {
            pageSize: "page_size",
            taskId: "task",
            dateFrom: "generated_at_from",
            dateTo: "generated_at_to",
          },
        }),
      ),
    );
  }

  /**
   * Generate an inventory report record.
   */
  async generateReport(
    data: GenerateInventoryReportPayload,
  ): Promise<InventoryReport> {
    return toData<InventoryReport>(
      await inventoryReportApi.create({
        task: data.taskId,
        templateId: data.templateId,
      }),
    );
  }

  /**
   * Export an inventory report file.
   */
  async exportReport(
    id: string,
    format: "pdf" | "excel" = "pdf",
  ): Promise<Blob> {
    return request.get(`/system/objects/InventoryReport/${id}/export/`, {
      params: {
        fileFormat: format,
      },
      responseType: "blob",
      unwrap: "none",
    });
  }

  /**
   * Submit a generated report for approval.
   */
  async submitReport(id: string): Promise<InventoryReport> {
    return request.post(`/system/objects/InventoryReport/${id}/submit/`);
  }
}

export const inventoryApi = new InventoryTaskApiService();

export const getReconciliations = (params?: Record<string, unknown>) =>
  inventoryApi.getReconciliations(params);

export const createReconciliation = (
  data: CreateInventoryReconciliationPayload,
) => inventoryApi.createReconciliation(data);

export const getAdjustments = (params?: Record<string, unknown>) =>
  inventoryApi.getAdjustments(params);

export const getReports = (params?: Record<string, unknown>) =>
  inventoryApi.getReports(params);

export const generateReport = (data: GenerateInventoryReportPayload) =>
  inventoryApi.generateReport(data);

export const exportReport = (id: string, format: "pdf" | "excel" = "pdf") =>
  inventoryApi.exportReport(id, format);

/**
 * Inventory Snapshot API service using Dynamic Object Routing
 */
export const snapshotApi = {
  /**
   * List snapshots (delegates to dynamic API)
   */
  async list(params?: any): Promise<PaginatedResponse<InventorySnapshot>> {
    return toPaginated<InventorySnapshot>(
      await inventorySnapshotApi.list(params),
    );
  },

  /**
   * Get single snapshot (delegates to dynamic API)
   */
  async get(id: string): Promise<InventorySnapshot> {
    return toData<InventorySnapshot>(await inventorySnapshotApi.get(id));
  },
};

/**
 * Inventory Reconciliation API service
 */
class ReconciliationApiService extends BaseApiService<InventoryReconciliation> {
  constructor() {
    super("system/objects/InventoryReconciliation");
  }

  /**
   * List reconciliation records with normalized query parameters.
   */
  async list(
    params?: Record<string, unknown>,
  ): Promise<PaginatedResponse<InventoryReconciliation>> {
    return inventoryApi.getReconciliations(params);
  }

  /**
   * Create a reconciliation record.
   */
  async create(
    data: Partial<InventoryReconciliation>,
  ): Promise<InventoryReconciliation> {
    return inventoryApi.createReconciliation(
      data as CreateInventoryReconciliationPayload,
    );
  }

  /**
   * Submit reconciliation for approval (custom endpoint)
   */
  submit(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryReconciliation/${id}/submit/`);
  }

  /**
   * Approve reconciliation (custom endpoint)
   */
  approve(id: string, data?: { comment?: string }): Promise<void> {
    return request.post(`/system/objects/InventoryReconciliation/${id}/approve/`, data || {});
  }

  /**
   * Reject reconciliation (custom endpoint)
   */
  reject(id: string, reason: string): Promise<void> {
    return request.post(`/system/objects/InventoryReconciliation/${id}/reject/`, { reason });
  }
}

export const reconciliationApi = new ReconciliationApiService();

/**
 * QR Code Scan API service (custom endpoints)
 */
export const qrScanApi = {
  /**
   * Get asset info by QR code
   */
  async getAssetByQrCode(qrCode: string): Promise<{
    id: string;
    code: string;
    name: string;
    categoryName: string;
    status: string;
    location: string;
    custodian: string;
  }> {
    const asset: any = await request.get("/system/objects/Asset/lookup/", {
      params: { qr_code: qrCode },
    });
    return {
      id: asset?.id || "",
      code: asset?.assetCode || asset?.asset_code || "",
      name: asset?.assetName || asset?.asset_name || "",
      categoryName:
        asset?.assetCategoryName || asset?.asset_category_name || "",
      status: asset?.assetStatus || asset?.asset_status || "",
      location: asset?.locationName || asset?.location_name || "",
      custodian: asset?.custodianName || asset?.custodian_name || "",
    };
  },

  /**
   * Verify QR code validity
   */
  async verifyQrCode(qrCode: string): Promise<{
    valid: boolean;
    assetId?: string;
    error?: string;
  }> {
    try {
      const asset: any = await request.get("/system/objects/Asset/lookup/", {
        params: { qr_code: qrCode },
      });
      return {
        valid: true,
        assetId: asset?.id,
      };
    } catch (error: any) {
      const message =
        error?.message ||
        error?.response?.data?.error?.message ||
        "Invalid QR code";
      return {
        valid: false,
        error: message,
      };
    }
  },
};
