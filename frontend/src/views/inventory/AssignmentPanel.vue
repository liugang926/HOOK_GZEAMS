<template>
  <div class="assignment-panel">
    <el-card
      class="assignment-panel__card"
      shadow="never"
    >
      <template #header>
        <div class="assignment-panel__section-header">
          <div>
            <h3 class="assignment-panel__title">
              {{ t("inventory.assignment.title") }}
            </h3>
            <p class="assignment-panel__subtitle">
              {{ t("inventory.assignment.subtitle") }}
            </p>
          </div>

          <el-button
            link
            :loading="loadingAssignments || loadingProgress"
            @click="loadData"
          >
            {{ t("common.actions.refresh") }}
          </el-button>
        </div>
      </template>

      <el-form
        :model="assignmentForm"
        label-position="top"
      >
        <el-row :gutter="16">
          <el-col
            :xs="24"
            :md="24"
          >
            <el-form-item
              :label="t('inventory.assignment.fields.assigneeIds')"
              required
            >
              <UserSelector
                v-model="assignmentForm.assigneeIds"
                :multiple="true"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          class="assignment-panel__hint-alert"
          type="info"
          :closable="false"
          :title="t('inventory.assignment.messages.executorScopeOnly')"
        />

        <div class="assignment-panel__form-actions">
          <el-button
            type="primary"
            :loading="submitting"
            @click="handleAssign"
          >
            {{ t("inventory.assignment.actions.assign") }}
          </el-button>
          <el-button @click="handleReset">
            {{ t("common.actions.reset") }}
          </el-button>
        </div>
      </el-form>
    </el-card>

    <el-row
      :gutter="16"
      class="assignment-panel__summary"
    >
      <el-col
        :xs="12"
        :md="6"
      >
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.assigneeCount')"
            :value="summaryStats.assigneeCount"
          />
        </el-card>
      </el-col>
      <el-col
        :xs="12"
        :md="6"
      >
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.totalAssets')"
            :value="summaryStats.totalAssets"
          />
        </el-card>
      </el-col>
      <el-col
        :xs="12"
        :md="6"
      >
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.scannedCount')"
            :value="summaryStats.scannedCount"
          />
        </el-card>
      </el-col>
      <el-col
        :xs="12"
        :md="6"
      >
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.abnormalCount')"
            :value="summaryStats.abnormalCount"
          />
        </el-card>
      </el-col>
    </el-row>

    <el-card
      class="assignment-panel__card"
      shadow="never"
    >
      <template #header>
        <div class="assignment-panel__section-header">
          <span>{{ t("inventory.assignment.listTitle") }}</span>
          <el-tag type="info">
            {{ assignmentRows.length }}
          </el-tag>
        </div>
      </template>

      <div v-loading="loadingAssignments">
        <el-table
          :data="assignmentRows"
          :empty-text="t('inventory.assignment.messages.noAssignments')"
        >
          <el-table-column
            prop="assigneeName"
            :label="t('inventory.assignment.fields.assignee')"
            min-width="160"
          />

          <el-table-column
            prop="status"
            :label="t('inventory.assignment.fields.status')"
            width="120"
          >
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="region"
            :label="t('inventory.assignment.fields.region')"
            min-width="140"
          >
            <template #default="{ row }">
              {{ row.region || t("inventory.assignment.scope.allRegions") }}
            </template>
          </el-table-column>

          <el-table-column
            prop="locationNames"
            :label="t('inventory.assignment.fields.locations')"
            min-width="180"
          >
            <template #default="{ row }">
              {{ formatLocationNames(row.locationNames) }}
            </template>
          </el-table-column>

          <el-table-column
            prop="assetCount"
            :label="t('inventory.assignment.fields.totalAssets')"
            width="120"
          />

          <el-table-column
            prop="scanCount"
            :label="t('inventory.assignment.fields.scannedCount')"
            width="120"
          />

          <el-table-column
            prop="progress"
            :label="t('inventory.assignment.fields.progress')"
            min-width="200"
          >
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress"
                :color="getProgressColor(row.progress)"
              />
            </template>
          </el-table-column>

          <el-table-column
            prop="abnormalCount"
            :label="t('inventory.assignment.fields.abnormalCount')"
            width="120"
          >
            <template #default="{ row }">
              <el-tag :type="row.abnormalCount > 0 ? 'danger' : 'info'">
                {{ row.abnormalCount }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="assignedAt"
            :label="t('inventory.assignment.fields.assignedAt')"
            min-width="180"
          >
            <template #default="{ row }">
              {{ formatAssignedAt(row.assignedAt) }}
            </template>
          </el-table-column>

          <el-table-column
            fixed="right"
            :label="t('common.actions.operation')"
            width="120"
          >
            <template #default="{ row }">
              <el-button
                link
                type="danger"
                :loading="removingAssigneeId === row.assigneeId"
                @click="handleRemove(row)"
              >
                {{ t("inventory.assignment.actions.remove") }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <el-card
      class="assignment-panel__card"
      shadow="never"
    >
      <template #header>
        <div class="assignment-panel__section-header">
          <span>{{ t("inventory.assignment.progressTitle") }}</span>
          <el-button
            link
            :loading="loadingProgress"
            @click="loadProgress"
          >
            {{ t("common.actions.refresh") }}
          </el-button>
        </div>
      </template>

      <div v-loading="loadingProgress">
        <el-empty
          v-if="progressCards.length === 0"
          :description="t('inventory.assignment.messages.noAssignments')"
        />

        <div
          v-else
          class="assignment-panel__progress-grid"
        >
          <AssignmentProgressCard
            v-for="item in progressCards"
            :key="item.assignmentId || item.assigneeId"
            :progress="item"
            :status="resolveProgressStatus(item)"
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useI18n } from "vue-i18n";
import { inventoryApi } from "@/api/inventory";
import AssignmentProgressCard from "@/components/AssignmentProgressCard.vue";
import UserSelector from "@/components/common/UserSelector.vue";
import type {
  AssignmentProgress,
  InventoryAssignmentStatus,
  InventoryTaskAssignment,
  TaskAssignment,
} from "@/types/inventory";
import { formatDateTime } from "@/utils/dateFormat";

interface Props {
  taskId: string;
}

interface Emits {
  (event: "updated"): void;
}

interface AssignmentRow {
  id: string;
  assigneeId: string;
  assigneeName: string;
  status: string;
  region?: string;
  locationNames: string[];
  assetCount: number;
  scanCount: number;
  abnormalCount: number;
  progress: number;
  assignedAt?: string;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const { t } = useI18n();

const assignmentForm = reactive<TaskAssignment>({
  taskId: props.taskId,
  assigneeIds: [],
  region: "",
  locationIds: [],
});

const assignments = ref<InventoryTaskAssignment[]>([]);
const progressData = ref<AssignmentProgress[]>([]);

const loadingAssignments = ref(false);
const loadingProgress = ref(false);
const submitting = ref(false);
const removingAssigneeId = ref("");

const uniqueStrings = (values: Array<string | null | undefined>) => {
  return Array.from(
    new Set(
      (values || []).map((value) => String(value || "").trim()).filter(Boolean),
    ),
  );
};

const normalizeProgress = (value?: number) => {
  const safeValue = Number.isFinite(value) ? Number(value) : 0;
  return Math.min(Math.max(Math.round(safeValue), 0), 100);
};

const resolveStatusKey = (status?: string) => {
  if (status === "completed") return "completed";
  if (status === "in_progress" || status === "inProgress") return "inProgress";
  return "pending";
};

const extractUserName = (value: unknown) => {
  if (!value || typeof value !== "object") return "";
  const user = value as Record<string, unknown>;
  return String(
    user.fullName ||
      user.full_name ||
      user.realName ||
      user.real_name ||
      user.username ||
      user.email ||
      "",
  );
};

const resolveAssignmentName = (
  assignment?: Partial<InventoryTaskAssignment>,
  progress?: Partial<AssignmentProgress>,
) => {
  return (
    progress?.assigneeName ||
    assignment?.assigneeName ||
    extractUserName(assignment?.assignee) ||
    assignment?.assigneeId ||
    "--"
  );
};

const progressByAssignmentId = computed(() => {
  return new Map(
    progressData.value
      .filter((item) => item.assignmentId)
      .map((item) => [String(item.assignmentId), item]),
  );
});

const progressByAssigneeId = computed(() => {
  return new Map(
    progressData.value
      .filter((item) => item.assigneeId)
      .map((item) => [String(item.assigneeId), item]),
  );
});

const assignedAssigneeIds = computed(() => {
  return assignments.value
    .map((item) => String(item.assigneeId || "").trim())
    .filter(Boolean);
});

const assignmentRows = computed<AssignmentRow[]>(() => {
  return assignments.value.map((assignment) => {
    const progress =
      progressByAssignmentId.value.get(assignment.id) ||
      progressByAssigneeId.value.get(assignment.assigneeId);

    const assetCount = progress?.totalAssets ?? assignment.assetCount ?? 0;
    const scanCount = progress?.scannedCount ?? assignment.scanCount ?? 0;
    const abnormalCount = progress?.abnormalCount ?? 0;
    const progressValue =
      progress?.progress ??
      (assetCount > 0 ? Math.round((scanCount / assetCount) * 100) : 0);

    return {
      id: assignment.id,
      assigneeId: assignment.assigneeId,
      assigneeName: resolveAssignmentName(assignment, progress),
      status: assignment.status,
      region: assignment.region,
      locationNames: assignment.locationNames || [],
      assetCount,
      scanCount,
      abnormalCount,
      progress: normalizeProgress(progressValue),
      assignedAt: assignment.assignedAt,
    };
  });
});

const progressCards = computed<AssignmentProgress[]>(() => {
  const cards = assignmentRows.value.map((row) => {
    const progress =
      progressByAssignmentId.value.get(row.id) ||
      progressByAssigneeId.value.get(row.assigneeId);

    return {
      assignmentId: row.id,
      assigneeId: row.assigneeId,
      assigneeName: row.assigneeName,
      totalAssets: row.assetCount,
      scannedCount: row.scanCount,
      normalCount:
        progress?.normalCount ?? Math.max(row.scanCount - row.abnormalCount, 0),
      abnormalCount: row.abnormalCount,
      progress: row.progress,
      status: (progress?.status || row.status) as InventoryAssignmentStatus,
    };
  });

  const existingKeys = new Set(
    cards.map((item) => String(item.assignmentId || item.assigneeId)),
  );

  progressData.value.forEach((item) => {
    const key = String(item.assignmentId || item.assigneeId);
    if (!key || existingKeys.has(key)) return;
    cards.push({
      ...item,
      progress: normalizeProgress(item.progress),
      status: resolveProgressStatus(item),
    });
  });

  return cards;
});

const summaryStats = computed(() => {
  return progressCards.value.reduce(
    (summary, item) => {
      summary.totalAssets += Number(item.totalAssets || 0);
      summary.scannedCount += Number(item.scannedCount || 0);
      summary.abnormalCount += Number(item.abnormalCount || 0);
      return summary;
    },
    {
      assigneeCount: progressCards.value.length || assignments.value.length,
      totalAssets: 0,
      scannedCount: 0,
      abnormalCount: 0,
    },
  );
});

const getStatusLabel = (status?: string) => {
  return t(`inventory.assignment.status.${resolveStatusKey(status)}`);
};

const getStatusTagType = (status?: string) => {
  if (status === "completed") return "success";
  if (status === "in_progress") return "warning";
  return "info";
};

const getProgressColor = (value: number) => {
  if (value >= 100) return "#67c23a";
  if (value >= 60) return "#409eff";
  if (value >= 30) return "#e6a23c";
  return "#f56c6c";
};

const formatAssignedAt = (value?: string) => {
  return value ? formatDateTime(value) : "--";
};

const formatLocationNames = (locationNames: string[]) => {
  return locationNames.length > 0
    ? locationNames.join(", ")
    : t("inventory.assignment.scope.allLocations");
};

const resolveProgressStatus = (
  item: AssignmentProgress,
): InventoryAssignmentStatus => {
  if (item.status) return item.status;
  if (normalizeProgress(item.progress) >= 100) return "completed";
  if ((item.scannedCount || 0) > 0) return "in_progress";
  return "pending";
};

const handleReset = () => {
  assignmentForm.assigneeIds = [];
  assignmentForm.region = "";
  assignmentForm.locationIds = [];
};

const loadAssignments = async () => {
  if (!props.taskId) {
    assignments.value = [];
    return;
  }

  loadingAssignments.value = true;
  try {
    assignments.value = await inventoryApi.getAssignments(props.taskId);
  } catch (error) {
    console.error("Failed to load inventory assignments:", error);
    assignments.value = [];
  } finally {
    loadingAssignments.value = false;
  }
};

const loadProgress = async () => {
  if (!props.taskId) {
    progressData.value = [];
    return;
  }

  loadingProgress.value = true;
  try {
    progressData.value = await inventoryApi.getAssignmentProgress(props.taskId);
  } catch (error) {
    console.error("Failed to load assignment progress:", error);
    progressData.value = [];
  } finally {
    loadingProgress.value = false;
  }
};

const loadData = async () => {
  if (!props.taskId) {
    assignments.value = [];
    progressData.value = [];
    return;
  }

  await Promise.all([loadAssignments(), loadProgress()]);
};

const handleAssign = async () => {
  const assigneeIds = uniqueStrings(assignmentForm.assigneeIds);
  if (assigneeIds.length === 0) {
    ElMessage.warning(t("inventory.assignment.validation.assigneeRequired"));
    return;
  }

  const newAssigneeIds = assigneeIds.filter(
    (id) => !assignedAssigneeIds.value.includes(id),
  );
  if (newAssigneeIds.length === 0) {
    ElMessage.warning(t("inventory.assignment.validation.noNewAssignees"));
    return;
  }

  submitting.value = true;
  try {
    await inventoryApi.createAssignment({
      taskId: props.taskId,
      assigneeIds: newAssigneeIds,
    });

    ElMessage.success(t("inventory.assignment.messages.assignSuccess"));
    handleReset();
    await loadData();
    emit("updated");
  } catch (error) {
    console.error("Failed to create inventory assignments:", error);
  } finally {
    submitting.value = false;
  }
};

const handleRemove = async (row: AssignmentRow) => {
  try {
    await ElMessageBox.confirm(
      t("inventory.assignment.confirm.removeAssignment", {
        name: row.assigneeName,
      }),
      t("common.messages.confirmTitle"),
      {
        type: "warning",
        confirmButtonText: t("common.actions.confirm"),
        cancelButtonText: t("common.actions.cancel"),
      },
    );

    removingAssigneeId.value = row.assigneeId;
    await inventoryApi.removeAssignment(props.taskId, row.assigneeId);
    ElMessage.success(t("inventory.assignment.messages.removeSuccess"));
    await loadData();
    emit("updated");
  } catch (error) {
    if (error !== "cancel" && error !== "close") {
      console.error("Failed to remove inventory assignment:", error);
    }
  } finally {
    removingAssigneeId.value = "";
  }
};

watch(
  () => props.taskId,
  (taskId) => {
    assignmentForm.taskId = taskId;
    handleReset();
    if (!taskId) {
      assignments.value = [];
      progressData.value = [];
      return;
    }
    loadData();
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
.assignment-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.assignment-panel__card {
  border: 1px solid var(--el-border-color-light);
}

.assignment-panel__hint-alert {
  margin-bottom: 16px;
}

.assignment-panel__section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.assignment-panel__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.assignment-panel__subtitle {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.assignment-panel__form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.assignment-panel__summary :deep(.el-card) {
  border: 1px solid var(--el-border-color-light);
}

.assignment-panel__location-select,
.assignment-panel__location-select :deep(.el-select__wrapper) {
  width: 100%;
}

.assignment-panel__progress-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

@media (max-width: 767px) {
  .assignment-panel__section-header {
    flex-direction: column;
    align-items: stretch;
  }

  .assignment-panel__form-actions {
    justify-content: stretch;
    flex-direction: column;
  }
}
</style>
