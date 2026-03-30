<template>
  <el-card
    class="assignment-progress-card"
    shadow="hover"
  >
    <div class="assignment-progress-card__header">
      <div class="assignment-progress-card__heading">
        <h4 class="assignment-progress-card__title">
          {{ progress.assigneeName }}
        </h4>
        <p class="assignment-progress-card__subtitle">
          {{
            t("inventory.assignment.labels.progressSummary", {
              scanned: progress.scannedCount,
              total: progress.totalAssets,
            })
          }}
        </p>
      </div>

      <el-tag :type="statusTagType">
        {{ statusLabel }}
      </el-tag>
    </div>

    <el-progress
      :percentage="percentage"
      :color="progressColor"
      :stroke-width="10"
    />

    <div class="assignment-progress-card__metrics">
      <div class="assignment-progress-card__metric">
        <span>{{ t("inventory.assignment.fields.totalAssets") }}</span>
        <strong>{{ progress.totalAssets }}</strong>
      </div>
      <div class="assignment-progress-card__metric">
        <span>{{ t("inventory.assignment.fields.scannedCount") }}</span>
        <strong>{{ progress.scannedCount }}</strong>
      </div>
      <div class="assignment-progress-card__metric">
        <span>{{ t("inventory.assignment.fields.normalCount") }}</span>
        <strong>{{ progress.normalCount }}</strong>
      </div>
      <div class="assignment-progress-card__metric">
        <span>{{ t("inventory.assignment.fields.abnormalCount") }}</span>
        <strong
          :class="{
            'assignment-progress-card__metric-value--danger':
              progress.abnormalCount > 0,
          }"
        >
          {{ progress.abnormalCount }}
        </strong>
      </div>
    </div>

    <div class="assignment-progress-card__footer">
      <el-tag
        size="small"
        type="success"
      >
        {{ t("inventory.assignment.fields.normalCount") }}
        {{ progress.normalCount }}
      </el-tag>
      <el-tag
        size="small"
        :type="progress.abnormalCount > 0 ? 'danger' : 'info'"
      >
        {{ t("inventory.assignment.fields.abnormalCount") }}
        {{ progress.abnormalCount }}
      </el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type {
  AssignmentProgress,
  InventoryAssignmentStatus,
} from "@/types/inventory";

interface Props {
  progress: AssignmentProgress;
  status?: InventoryAssignmentStatus | string;
}

const props = defineProps<Props>();

const { t } = useI18n();

const normalizeProgress = (value?: number) => {
  const safeValue = Number.isFinite(value) ? Number(value) : 0;
  return Math.min(Math.max(Math.round(safeValue), 0), 100);
};

const resolveStatusKey = (status?: string) => {
  if (status === "completed") return "completed";
  if (status === "in_progress" || status === "inProgress") return "inProgress";
  return "pending";
};

const percentage = computed(() => normalizeProgress(props.progress.progress));

const resolvedStatus = computed(() => {
  if (props.status) return props.status;
  if (percentage.value >= 100) return "completed";
  if ((props.progress.scannedCount || 0) > 0) return "in_progress";
  return "pending";
});

const statusLabel = computed(() => {
  return t(
    `inventory.assignment.status.${resolveStatusKey(resolvedStatus.value)}`,
  );
});

const statusTagType = computed(() => {
  if (resolvedStatus.value === "completed") return "success";
  if (resolvedStatus.value === "in_progress") return "warning";
  return "info";
});

const progressColor = computed(() => {
  if (percentage.value >= 100) return "#67c23a";
  if (props.progress.abnormalCount > 0) return "#f56c6c";
  if (percentage.value >= 60) return "#409eff";
  return "#e6a23c";
});
</script>

<style scoped lang="scss">
.assignment-progress-card {
  height: 100%;
  border: 1px solid var(--el-border-color-light);
}

.assignment-progress-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.assignment-progress-card__heading {
  min-width: 0;
}

.assignment-progress-card__title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.assignment-progress-card__subtitle {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.assignment-progress-card__metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.assignment-progress-card__metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  border-radius: 10px;
  background: var(--el-fill-color-light);
}

.assignment-progress-card__metric span {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.assignment-progress-card__metric strong {
  font-size: 18px;
  color: var(--el-text-color-primary);
}

.assignment-progress-card__metric-value--danger {
  color: var(--el-color-danger);
}

.assignment-progress-card__footer {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

@media (max-width: 767px) {
  .assignment-progress-card__metrics {
    grid-template-columns: 1fr;
  }
}
</style>
