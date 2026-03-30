<template>
  <div class="sync-job-list-page">
    <div class="page-header">
      <div>
        <h3>{{ t("integration.syncJobs.title") }}</h3>
        <p>{{ t("integration.syncJobs.subtitle") }}</p>
      </div>

      <el-button
        :icon="Refresh"
        @click="loadJobs"
      >
        {{ t("integration.actions.refresh") }}
      </el-button>
    </div>

    <el-card
      shadow="never"
      class="filter-card"
    >
      <el-form
        :model="filters"
        inline
      >
        <el-form-item :label="t('integration.syncJobs.filters.integration')">
          <el-select
            v-model="filters.integrationId"
            clearable
            filterable
            :placeholder="t('integration.syncJobs.placeholders.integration')"
            style="width: 220px"
          >
            <el-option
              v-for="config in configs"
              :key="config.id"
              :label="config.name || config.systemName"
              :value="config.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="t('integration.syncJobs.filters.moduleType')">
          <el-select
            v-model="filters.moduleType"
            clearable
            :placeholder="t('integration.syncJobs.placeholders.moduleType')"
            style="width: 180px"
          >
            <el-option
              v-for="option in moduleOptions"
              :key="option"
              :label="getModuleLabel(option, t)"
              :value="option"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="t('integration.syncJobs.filters.status')">
          <el-select
            v-model="filters.status"
            clearable
            :placeholder="t('integration.syncJobs.placeholders.status')"
            style="width: 180px"
          >
            <el-option
              v-for="status in statusOptions"
              :key="status"
              :label="resolveStatusLabel(status)"
              :value="status"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="t('integration.syncJobs.filters.dateRange')">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="~"
            :start-placeholder="
              t('integration.syncJobs.placeholders.startDate')
            "
            :end-placeholder="t('integration.syncJobs.placeholders.endDate')"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            @click="handleSearch"
          >
            {{ t("integration.actions.search") }}
          </el-button>

          <el-button @click="handleReset">
            {{ t("integration.actions.reset") }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card
      shadow="never"
      class="table-card"
    >
      <el-table
        v-loading="loading"
        :data="jobs"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column
          prop="taskId"
          :label="t('integration.syncJobs.columns.taskId')"
          min-width="180"
        />

        <el-table-column
          :label="t('integration.syncJobs.columns.integration')"
          min-width="180"
        >
          <template #default="{ row }">
            {{ resolveIntegrationName(row) }}
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.syncJobs.columns.jobType')"
          min-width="180"
        >
          <template #default="{ row }">
            <div class="job-type-cell">
              <span>{{ resolveJobTypeLabel(row) }}</span>
              <span class="job-type-cell__sub">
                {{ row.moduleType ? getModuleLabel(row.moduleType, t) : "-" }}
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.syncJobs.columns.status')"
          width="140"
        >
          <template #default="{ row }">
            <el-tag :type="resolveStatusTagType(row.status)">
              {{ resolveStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.syncJobs.columns.progress')"
          width="180"
        >
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress"
              :status="resolveProgressStatus(row)"
              :stroke-width="10"
            />
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.syncJobs.columns.summary')"
          width="160"
        >
          <template #default="{ row }">
            <div class="summary-cell">
              <span>{{ t("integration.syncJobs.summary.total") }}:
                {{ resolveTotal(row) }}</span>
              <span>{{ t("integration.syncJobs.summary.succeeded") }}:
                {{ resolveSucceeded(row) }}</span>
              <span>{{ t("integration.syncJobs.summary.failed") }}:
                {{ resolveFailed(row) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.syncJobs.columns.startedAt')"
          width="180"
        >
          <template #default="{ row }">
            {{ row.startedAt ? formatDateTime(row.startedAt) : "-" }}
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.syncJobs.columns.completedAt')"
          width="180"
        >
          <template #default="{ row }">
            {{ row.completedAt ? formatDateTime(row.completedAt) : "-" }}
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.syncJobs.columns.actions')"
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleViewDetail(row)"
            >
              {{ t("integration.actions.view") }}
            </el-button>

            <el-button
              v-if="isRetryable(row)"
              link
              type="warning"
              :loading="retrying[row.id]"
              @click="handleRetry(row)"
            >
              {{ t("integration.actions.retry") }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && jobs.length === 0"
        :description="t('integration.syncJobs.empty')"
      />

      <div class="pagination-footer">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <el-drawer
      v-model="detailVisible"
      :title="t('integration.syncJobs.drawerTitle')"
      size="680px"
    >
      <div
        v-loading="detailLoading"
        class="detail-drawer"
      >
        <template v-if="selectedJob">
          <el-descriptions
            :column="1"
            border
          >
            <el-descriptions-item
              :label="t('integration.syncJobs.columns.taskId')"
            >
              {{ selectedJob.taskId || "-" }}
            </el-descriptions-item>
            <el-descriptions-item
              :label="t('integration.syncJobs.columns.integration')"
            >
              {{ resolveIntegrationName(selectedJob) }}
            </el-descriptions-item>
            <el-descriptions-item
              :label="t('integration.syncJobs.columns.jobType')"
            >
              {{ resolveJobTypeLabel(selectedJob) }}
            </el-descriptions-item>
            <el-descriptions-item
              :label="t('integration.syncJobs.columns.status')"
            >
              {{ resolveStatusLabel(selectedJob.status) }}
            </el-descriptions-item>
            <el-descriptions-item
              :label="t('integration.syncJobs.columns.progress')"
            >
              {{ selectedJob.progress }}%
            </el-descriptions-item>
            <el-descriptions-item
              :label="t('integration.syncJobs.columns.direction')"
            >
              {{ resolveDirectionLabel(selectedJob.direction) }}
            </el-descriptions-item>
            <el-descriptions-item
              :label="t('integration.syncJobs.columns.duration')"
            >
              {{ resolveDurationText(selectedJob) }}
            </el-descriptions-item>
          </el-descriptions>

          <el-divider>
            {{
              t("integration.syncJobs.detailSummaryTitle")
            }}
          </el-divider>

          <div class="detail-summary-grid">
            <el-card shadow="never">
              <el-statistic
                :title="t('integration.syncJobs.summary.total')"
                :value="resolveTotal(selectedJob)"
              />
            </el-card>
            <el-card shadow="never">
              <el-statistic
                :title="t('integration.syncJobs.summary.succeeded')"
                :value="resolveSucceeded(selectedJob)"
              />
            </el-card>
            <el-card shadow="never">
              <el-statistic
                :title="t('integration.syncJobs.summary.failed')"
                :value="resolveFailed(selectedJob)"
              />
            </el-card>
          </div>

          <template v-if="resolveErrors(selectedJob).length">
            <el-divider>
              {{
                t("integration.syncJobs.detailErrorsTitle")
              }}
            </el-divider>

            <el-table
              :data="resolveErrors(selectedJob)"
              size="small"
              border
            >
              <el-table-column
                prop="record"
                :label="t('integration.syncJobs.errorColumns.record')"
                min-width="180"
              />
              <el-table-column
                prop="error"
                :label="t('integration.syncJobs.errorColumns.error')"
                min-width="260"
              />
            </el-table>
          </template>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import { Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import {
  getConfigs,
  getSyncJob,
  getSyncJobs,
  retrySyncJob,
} from "@/api/integration";
import type {
  IntegrationConfig,
  SyncJob,
  SyncJobResultError,
} from "@/types/integration";
import { formatDateTime } from "@/utils/dateFormat";
import {
  getModuleLabel,
  getSyncStatusLabel,
  getSyncStatusTagType,
  MODULE_OPTIONS,
} from "@/views/integration/integrationConfig.constants";

const { t, te } = useI18n();

const statusOptions = [
  "pending",
  "running",
  "success",
  "partial_success",
  "failed",
  "cancelled",
];
const moduleOptions = MODULE_OPTIONS;

const loading = ref(false);
const detailLoading = ref(false);
const jobs = ref<SyncJob[]>([]);
const configs = ref<IntegrationConfig[]>([]);
const selectedJob = ref<SyncJob | null>(null);
const detailVisible = ref(false);
const retrying = ref<Record<string, boolean>>({});

const filters = reactive({
  integrationId: "",
  moduleType: "",
  status: "",
  dateRange: [] as string[],
});

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
});

const setLoadingState = (
  state: Record<string, boolean>,
  id: string,
  value: boolean,
) => {
  state[id] = value;
};

const resolveStatusLabel = (status?: string) => {
  if (!status) return "-";

  if (status === "completed") {
    return te("integration.syncStatus.completed")
      ? t("integration.syncStatus.completed")
      : status;
  }

  return getSyncStatusLabel(status, t);
};

const resolveStatusTagType = (status?: string) => {
  if (!status) return "info";
  if (status === "completed") return "success";
  return getSyncStatusTagType(status);
};

const resolveDirectionLabel = (direction?: string) => {
  if (!direction) return "-";

  const translationKey = `integration.directions.${direction}`;
  return te(translationKey) ? t(translationKey) : direction;
};

const resolveConfigSystemName = (job: SyncJob) => {
  return job.config && typeof job.config !== "string"
    ? job.config.systemName
    : undefined;
};

const resolveIntegrationName = (job: SyncJob) => {
  return (
    job.integrationName || job.systemName || resolveConfigSystemName(job) || "-"
  );
};

const resolveJobTypeLabel = (job: SyncJob) => {
  const candidates = [job.jobType, job.businessType];

  for (const candidate of candidates) {
    if (!candidate) continue;
    const translationKey = `integration.jobTypes.${candidate}`;
    if (te(translationKey)) {
      return t(translationKey);
    }
  }

  if (job.moduleType) {
    return getModuleLabel(job.moduleType, t);
  }

  return job.jobType || job.businessType || "-";
};

const resolveTotal = (job: SyncJob) => {
  return job.result?.total ?? job.totalCount ?? 0;
};

const resolveSucceeded = (job: SyncJob) => {
  return job.result?.succeeded ?? job.successCount ?? 0;
};

const resolveFailed = (job: SyncJob) => {
  return job.result?.failed ?? job.failedCount ?? 0;
};

const resolveErrors = (job: SyncJob | null): SyncJobResultError[] => {
  if (!job) return [];
  return job.result?.errors || job.errorSummary || [];
};

const resolveProgressStatus = (job: SyncJob) => {
  if (job.status === "failed") return "exception";
  if (job.status === "success" || job.status === "completed") return "success";
  if (job.status === "partial_success") return "warning";
  return undefined;
};

const resolveDurationText = (job: SyncJob) => {
  const durationMs = job.durationMs ?? job.durationSeconds;
  if (!durationMs) return "-";
  return `${(Number(durationMs) / 1000).toFixed(1)}s`;
};

const isRetryable = (job: SyncJob) => {
  return ["failed", "partial_success"].includes(job.status);
};

const loadConfigOptions = async () => {
  try {
    configs.value = await getConfigs();
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.loadConfigsFailed"),
    );
  }
};

const loadJobs = async () => {
  loading.value = true;

  try {
    const response = await getSyncJobs({
      page: pagination.page,
      pageSize: pagination.pageSize,
      integrationId: filters.integrationId || undefined,
      moduleType: filters.moduleType || undefined,
      status: filters.status || undefined,
      dateFrom: filters.dateRange[0],
      dateTo: filters.dateRange[1],
    });

    jobs.value = response.results;
    pagination.total = response.count;
  } catch (error) {
    jobs.value = [];
    pagination.total = 0;
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.loadJobsFailed"),
    );
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  pagination.page = 1;
  void loadJobs();
};

const handleReset = () => {
  filters.integrationId = "";
  filters.moduleType = "";
  filters.status = "";
  filters.dateRange = [];
  pagination.page = 1;
  void loadJobs();
};

const handlePageChange = (page: number) => {
  pagination.page = page;
  void loadJobs();
};

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize;
  pagination.page = 1;
  void loadJobs();
};

const handleViewDetail = async (job: SyncJob) => {
  detailVisible.value = true;
  detailLoading.value = true;
  selectedJob.value = job;

  try {
    selectedJob.value = await getSyncJob(job.id);
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.loadJobDetailFailed"),
    );
  } finally {
    detailLoading.value = false;
  }
};

const handleRetry = async (job: SyncJob) => {
  setLoadingState(retrying.value, job.id, true);

  try {
    await retrySyncJob(job.id);
    ElMessage.success(t("integration.messages.jobRetried"));
    await loadJobs();
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.retryFailed"),
    );
  } finally {
    setLoadingState(retrying.value, job.id, false);
  }
};

onMounted(async () => {
  await Promise.all([loadConfigOptions(), loadJobs()]);
});
</script>

<style scoped>
.sync-job-list-page {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h3 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.page-header p {
  margin: 8px 0 0;
  color: #909399;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  overflow: hidden;
}

.job-type-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.job-type-cell__sub {
  font-size: 12px;
  color: #909399;
}

.summary-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.pagination-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.detail-drawer {
  min-height: 240px;
}

.detail-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

@media (max-width: 768px) {
  .sync-job-list-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .detail-summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
