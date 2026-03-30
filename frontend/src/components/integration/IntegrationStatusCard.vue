<template>
  <el-card
    shadow="hover"
    class="integration-status-card"
  >
    <div class="card-header">
      <div class="card-header__content">
        <div class="card-title">
          {{ displayName }}
        </div>
        <div class="card-subtitle">
          {{ displayCode }}
        </div>
      </div>

      <el-tag
        size="small"
        :type="enabledTagType"
      >
        {{ enabledLabel }}
      </el-tag>
    </div>

    <div class="card-metrics">
      <div class="metric-item">
        <span class="metric-label">{{
          t("integration.statusCard.connectionStatus")
        }}</span>
        <el-tag
          size="small"
          :type="healthTagType"
        >
          {{ healthLabel }}
        </el-tag>
      </div>

      <div class="metric-item">
        <span class="metric-label">{{
          t("integration.statusCard.integrationType")
        }}</span>
        <span class="metric-value">{{ integrationTypeLabel }}</span>
      </div>

      <div class="metric-item">
        <span class="metric-label">{{
          t("integration.statusCard.recentSyncStatus")
        }}</span>
        <el-tag
          v-if="integration.lastSyncStatus"
          size="small"
          :type="syncTagType"
        >
          {{ syncStatusLabel }}
        </el-tag>
        <span
          v-else
          class="metric-value metric-value--muted"
        >
          {{ t("integration.statusCard.neverSynced") }}
        </span>
      </div>

      <div class="metric-item">
        <span class="metric-label">{{
          t("integration.statusCard.lastSyncAt")
        }}</span>
        <span class="metric-value">{{ lastSyncText }}</span>
      </div>
    </div>

    <div
      v-if="integration.enabledModules.length"
      class="module-tags"
    >
      <el-tag
        v-for="module in integration.enabledModules"
        :key="module"
        size="small"
        effect="plain"
      >
        {{ getModuleLabel(module, t) }}
      </el-tag>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { formatDateTime } from "@/utils/dateFormat";
import type { IntegrationConfig } from "@/types/integration";
import {
  getEnabledStatusLabel,
  getEnabledStatusTagType,
  getHealthStatusLabel,
  getHealthStatusTagType,
  getModuleLabel,
  getSyncStatusLabel,
  getSyncStatusTagType,
} from "@/views/integration/integrationConfig.constants";

const props = defineProps<{
  integration: IntegrationConfig;
}>();

const { t, te } = useI18n();

const resolveIntegrationTypeLabel = (value?: string) => {
  if (!value) return "-";

  const extendedKey = `integration.integrationTypes.${value}`;
  if (te(extendedKey)) {
    return t(extendedKey);
  }

  const systemKey = `integration.systemTypes.${value}`;
  if (te(systemKey)) {
    return t(systemKey);
  }

  return value;
};

const displayName = computed(() => {
  return (
    props.integration.name ||
    props.integration.systemName ||
    props.integration.code ||
    "-"
  );
});

const displayCode = computed(() => {
  return props.integration.code || props.integration.systemType || "-";
});

const enabledLabel = computed(() =>
  getEnabledStatusLabel(props.integration.isEnabled, t),
);
const enabledTagType = computed(() =>
  getEnabledStatusTagType(props.integration.isEnabled),
);
const healthLabel = computed(() =>
  getHealthStatusLabel(props.integration.healthStatus || "", t),
);
const healthTagType = computed(() =>
  getHealthStatusTagType(props.integration.healthStatus || ""),
);
const syncStatusLabel = computed(() =>
  getSyncStatusLabel(props.integration.lastSyncStatus || "", t),
);
const syncTagType = computed(() =>
  getSyncStatusTagType(props.integration.lastSyncStatus || ""),
);
const integrationTypeLabel = computed(() => {
  return resolveIntegrationTypeLabel(
    props.integration.integrationType || props.integration.systemType,
  );
});
const lastSyncText = computed(() => {
  return props.integration.lastSyncAt
    ? formatDateTime(props.integration.lastSyncAt)
    : t("integration.statusCard.neverSynced");
});
</script>

<style scoped>
.integration-status-card {
  height: 100%;
  border: 1px solid #ebeef5;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.card-header__content {
  min-width: 0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.card-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  word-break: break-all;
}

.card-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.metric-label {
  font-size: 12px;
  color: #909399;
}

.metric-value {
  font-size: 13px;
  color: #303133;
  word-break: break-word;
}

.metric-value--muted {
  color: #909399;
}

.module-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 18px;
}

@media (max-width: 768px) {
  .card-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
