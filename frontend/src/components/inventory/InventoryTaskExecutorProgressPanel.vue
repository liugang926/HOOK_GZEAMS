<template>
  <section class="inventory-task-executor-progress-panel">
    <header class="inventory-task-executor-progress-panel__header">
      <div>
        <p class="inventory-task-executor-progress-panel__eyebrow">
          {{ t("common.workbench.labels.summary") }}
        </p>
        <h3 class="inventory-task-executor-progress-panel__title">
          {{ title }}
        </h3>
        <p class="inventory-task-executor-progress-panel__description">
          {{ description }}
        </p>
      </div>

      <el-button
        link
        :loading="loading"
        @click="void loadPanelData()"
      >
        {{ t("common.actions.refresh") }}
      </el-button>
    </header>

    <el-alert
      v-if="errorMessage"
      class="inventory-task-executor-progress-panel__alert"
      type="warning"
      :closable="false"
      :title="errorMessage"
    />

    <div
      v-loading="loading"
      class="inventory-task-executor-progress-panel__body"
    >
      <div class="inventory-task-executor-progress-panel__summary">
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.assigneeCount')"
            :value="summaryStats.assigneeCount"
          />
        </el-card>
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.totalAssets')"
            :value="summaryStats.totalAssets"
          />
        </el-card>
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.scannedCount')"
            :value="summaryStats.scannedCount"
          />
        </el-card>
        <el-card shadow="never">
          <el-statistic
            :title="t('inventory.assignment.summary.abnormalCount')"
            :value="summaryStats.abnormalCount"
          />
        </el-card>
      </div>

      <el-empty
        v-if="progressCards.length === 0 && !loading"
        :description="t('inventory.assignment.messages.noAssignments')"
      />

      <div
        v-else
        class="inventory-task-executor-progress-panel__grid"
      >
        <AssignmentProgressCard
          v-for="item in progressCards"
          :key="item.assignmentId || item.assigneeId"
          :progress="item"
          :status="resolveProgressStatus(item)"
        />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import { inventoryApi } from "@/api/inventory";
import AssignmentProgressCard from "@/components/AssignmentProgressCard.vue";
import { resolveWorkbenchText } from "@/components/common/workbenchHelpers";
import type {
  AssignmentProgress,
  InventoryAssignmentStatus,
  InventoryTaskAssignment,
} from "@/types/inventory";

interface Props {
  panel?: Record<string, unknown>;
  recordId: string;
  panelRefreshVersion?: number;
}

const props = withDefaults(defineProps<Props>(), {
  panel: () => ({}),
  panelRefreshVersion: 0,
});

const { t, te } = useI18n();

const assignments = ref<InventoryTaskAssignment[]>([]);
const progressRows = ref<AssignmentProgress[]>([]);
const loading = ref(false);
const errorMessage = ref("");

const title = computed(() => {
  return (
    resolveWorkbenchText(
      props.panel || {},
      t,
      te,
      ["titleKey", "title_key"],
      ["title"],
    ) || t("inventory.workbench.panels.executorProgress")
  );
});

const description = computed(() => {
  return (
    resolveWorkbenchText(
      props.panel || {},
      t,
      te,
      ["descriptionKey", "description_key", "hintKey", "hint_key"],
      ["description", "hint"],
    ) || t("inventory.workbench.messages.executorProgressHint")
  );
});

const progressByAssignmentId = computed(() => {
  return new Map(
    progressRows.value
      .filter((item) => item.assignmentId)
      .map((item) => [String(item.assignmentId), item]),
  );
});

const progressByAssigneeId = computed(() => {
  return new Map(
    progressRows.value
      .filter((item) => item.assigneeId)
      .map((item) => [String(item.assigneeId), item]),
  );
});

const buildCardFromAssignment = (assignment: InventoryTaskAssignment): AssignmentProgress => {
  const progress =
    progressByAssignmentId.value.get(String(assignment.id)) ||
    progressByAssigneeId.value.get(String(assignment.assigneeId));
  const totalAssets = Number(progress?.totalAssets ?? assignment.assetCount ?? 0);
  const scannedCount = Number(progress?.scannedCount ?? assignment.scanCount ?? 0);
  const abnormalCount = Number(progress?.abnormalCount ?? 0);
  const normalCount = Number(progress?.normalCount ?? Math.max(scannedCount - abnormalCount, 0));
  const progressValue =
    progress?.progress ??
    (totalAssets > 0 ? Math.round((scannedCount / totalAssets) * 100) : 0);

  return {
    assignmentId: String(progress?.assignmentId || assignment.id || assignment.assigneeId || ""),
    assigneeId: String(progress?.assigneeId || assignment.assigneeId || ""),
    assigneeName: String(progress?.assigneeName || assignment.assigneeName || assignment.assigneeId || "--"),
    totalAssets,
    scannedCount,
    normalCount,
    abnormalCount,
    progress: progressValue,
    status: progress?.status || assignment.status,
  };
};

const progressCards = computed<AssignmentProgress[]>(() => {
  const cards = assignments.value.map((assignment) => buildCardFromAssignment(assignment));
  const knownKeys = new Set(
    cards.map((item) => String(item.assignmentId || item.assigneeId || "")).filter(Boolean),
  );

  progressRows.value.forEach((item) => {
    const key = String(item.assignmentId || item.assigneeId || "");
    if (!key || knownKeys.has(key)) {
      return;
    }
    knownKeys.add(key);
    cards.push({
      assignmentId: String(item.assignmentId || item.assigneeId || ""),
      assigneeId: String(item.assigneeId || ""),
      assigneeName: String(item.assigneeName || item.assigneeId || "--"),
      totalAssets: Number(item.totalAssets || 0),
      scannedCount: Number(item.scannedCount || 0),
      normalCount: Number(item.normalCount || 0),
      abnormalCount: Number(item.abnormalCount || 0),
      progress: Number(item.progress || 0),
      status: item.status,
    });
  });

  return cards;
});

const summaryStats = computed(() => {
  return progressCards.value.reduce(
    (summary, item) => {
      summary.assigneeCount += 1;
      summary.totalAssets += Number(item.totalAssets || 0);
      summary.scannedCount += Number(item.scannedCount || 0);
      summary.abnormalCount += Number(item.abnormalCount || 0);
      return summary;
    },
    {
      assigneeCount: 0,
      totalAssets: 0,
      scannedCount: 0,
      abnormalCount: 0,
    },
  );
});

const resolveProgressStatus = (item: AssignmentProgress): InventoryAssignmentStatus => {
  if (item.status === "completed") return "completed";
  if (item.status === "in_progress" || item.progress >= 100 || item.scannedCount > 0) {
    return item.progress >= 100 ? "completed" : "in_progress";
  }
  return "pending";
};

const loadPanelData = async () => {
  const taskId = String(props.recordId || "").trim();
  if (!taskId) {
    assignments.value = [];
    progressRows.value = [];
    errorMessage.value = "";
    return;
  }

  loading.value = true;
  errorMessage.value = "";

  try {
    const [assignmentResult, progressResult] = await Promise.all([
      inventoryApi.getAssignments(taskId),
      inventoryApi.getAssignmentProgress(taskId),
    ]);
    assignments.value = Array.isArray(assignmentResult) ? assignmentResult : [];
    progressRows.value = Array.isArray(progressResult) ? progressResult : [];
  } catch {
    assignments.value = [];
    progressRows.value = [];
    errorMessage.value = t("common.messages.loadFailed");
  } finally {
    loading.value = false;
  }
};

watch(
  () => [props.recordId, props.panelRefreshVersion],
  () => {
    void loadPanelData();
  },
  { immediate: true },
);
</script>

<style scoped lang="scss">
@use "@/styles/object-workspace.scss" as workspace;

.inventory-task-executor-progress-panel {
  @include workspace.workspace-panel();
  padding: 24px;
}

.inventory-task-executor-progress-panel__header {
  @include workspace.workspace-panel-header();
  align-items: flex-start;
}

.inventory-task-executor-progress-panel__eyebrow {
  @include workspace.panel-kicker();
}

.inventory-task-executor-progress-panel__title {
  @include workspace.panel-title();
}

.inventory-task-executor-progress-panel__description {
  @include workspace.panel-text(540px);
}

.inventory-task-executor-progress-panel__alert {
  margin-bottom: 16px;
}

.inventory-task-executor-progress-panel__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.inventory-task-executor-progress-panel__summary :deep(.el-card) {
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.inventory-task-executor-progress-panel__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

@media (max-width: 960px) {
  .inventory-task-executor-progress-panel__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .inventory-task-executor-progress-panel {
    padding: 20px;
  }

  .inventory-task-executor-progress-panel__summary {
    grid-template-columns: 1fr;
  }
}
</style>
