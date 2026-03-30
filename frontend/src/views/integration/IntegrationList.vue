<template>
  <div class="integration-list-page">
    <div class="page-header">
      <div>
        <h3>{{ t("integration.list.title") }}</h3>
        <p>{{ t("integration.list.subtitle") }}</p>
      </div>

      <el-button
        :icon="Refresh"
        @click="loadConfigs"
      >
        {{ t("integration.actions.refresh") }}
      </el-button>
    </div>

    <el-row
      v-if="configs.length"
      :gutter="16"
      class="status-card-grid"
    >
      <el-col
        v-for="config in configs"
        :key="config.id"
        :xs="24"
        :sm="12"
        :xl="8"
      >
        <IntegrationStatusCard :integration="config" />
      </el-col>
    </el-row>

    <el-card
      shadow="never"
      class="table-card"
    >
      <template #header>
        <div class="table-card__header">
          <span>{{ t("integration.list.tableTitle") }}</span>
          <el-tag type="info">
            {{ configs.length }}
          </el-tag>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="configs"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column
          prop="name"
          :label="t('integration.list.columns.name')"
          min-width="200"
        >
          <template #default="{ row }">
            <div class="name-cell">
              <span class="name-cell__primary">{{
                row.name || row.systemName
              }}</span>
              <span class="name-cell__secondary">{{
                row.code || row.systemType
              }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.list.columns.type')"
          width="150"
        >
          <template #default="{ row }">
            <el-tag :type="getSystemTypeTagType(row.systemType)">
              {{
                resolveIntegrationTypeLabel(
                  row.integrationType || row.systemType,
                )
              }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.list.columns.connectionStatus')"
          width="150"
        >
          <template #default="{ row }">
            <el-tag :type="getHealthStatusTagType(row.healthStatus || '')">
              {{ getHealthStatusLabel(row.healthStatus || "", t) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.list.columns.enabled')"
          width="120"
        >
          <template #default="{ row }">
            <el-switch
              :model-value="row.isEnabled"
              :loading="statusUpdating[row.id]"
              @change="handleStatusChange(row, $event)"
            />
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.list.columns.lastSyncStatus')"
          width="150"
        >
          <template #default="{ row }">
            <el-tag
              v-if="row.lastSyncStatus"
              :type="getSyncStatusTagType(row.lastSyncStatus)"
            >
              {{ getSyncStatusLabel(row.lastSyncStatus, t) }}
            </el-tag>
            <span v-else>
              {{ t("integration.statusCard.neverSynced") }}
            </span>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.list.columns.lastSyncAt')"
          width="180"
        >
          <template #default="{ row }">
            {{
              row.lastSyncAt
                ? formatDateTime(row.lastSyncAt)
                : t("integration.statusCard.neverSynced")
            }}
          </template>
        </el-table-column>

        <el-table-column
          :label="t('integration.list.columns.actions')"
          fixed="right"
          width="280"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click="handleConfigure(row)"
            >
              {{ t("integration.actions.configure") }}
            </el-button>

            <el-button
              link
              type="success"
              :loading="testing[row.id]"
              @click="handleTest(row)"
            >
              {{ t("integration.actions.testConnection") }}
            </el-button>

            <el-button
              link
              :loading="syncing[row.id]"
              @click="handleSync(row)"
            >
              {{ t("integration.actions.syncNow") }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="!loading && configs.length === 0"
        :description="t('integration.list.empty')"
      />
    </el-card>

    <el-drawer
      v-model="configDrawerVisible"
      :title="
        selectedConfig
          ? selectedConfig.name || selectedConfig.systemName
          : t('integration.list.drawerTitle')
      "
      size="540px"
    >
      <template v-if="selectedConfig">
        <el-descriptions
          :column="1"
          border
        >
          <el-descriptions-item :label="t('integration.list.columns.name')">
            {{ selectedConfig.name || selectedConfig.systemName }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('integration.list.columns.code')">
            {{ selectedConfig.code || selectedConfig.systemType }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('integration.list.columns.type')">
            {{
              resolveIntegrationTypeLabel(
                selectedConfig.integrationType || selectedConfig.systemType,
              )
            }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="t('integration.list.columns.connectionStatus')"
          >
            {{ getHealthStatusLabel(selectedConfig.healthStatus || "", t) }}
          </el-descriptions-item>
          <el-descriptions-item :label="t('integration.list.columns.enabled')">
            {{ getEnabledStatusLabel(selectedConfig.isEnabled, t) }}
          </el-descriptions-item>
          <el-descriptions-item
            :label="t('integration.list.columns.lastSyncAt')"
          >
            {{
              selectedConfig.lastSyncAt
                ? formatDateTime(selectedConfig.lastSyncAt)
                : t("integration.statusCard.neverSynced")
            }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider>
          {{
            t("integration.list.sections.connectionConfig")
          }}
        </el-divider>
        <pre class="config-block">{{
          stringifyConfig(selectedConfig.connectionConfig)
        }}</pre>

        <el-divider>{{ t("integration.list.sections.syncConfig") }}</el-divider>
        <pre class="config-block">{{
          stringifyConfig(selectedConfig.syncConfig)
        }}</pre>

        <el-divider>
          {{
            t("integration.list.sections.mappingConfig")
          }}
        </el-divider>
        <pre class="config-block">{{
          stringifyConfig(selectedConfig.mappingConfig || {})
        }}</pre>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { Refresh } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import IntegrationStatusCard from "@/components/integration/IntegrationStatusCard.vue";
import {
  getConfigs,
  testConnection,
  triggerSync,
  updateConfig,
} from "@/api/integration";
import type {
  IntegrationConfig,
  IntegrationConfigMutationPayload,
} from "@/types/integration";
import { formatDateTime } from "@/utils/dateFormat";
import {
  getEnabledStatusLabel,
  getHealthStatusLabel,
  getHealthStatusTagType,
  getSyncStatusLabel,
  getSyncStatusTagType,
  getSystemTypeTagType,
} from "@/views/integration/integrationConfig.constants";

const { t, te } = useI18n();

const loading = ref(false);
const configs = ref<IntegrationConfig[]>([]);
const selectedConfig = ref<IntegrationConfig | null>(null);
const configDrawerVisible = ref(false);
const testing = ref<Record<string, boolean>>({});
const syncing = ref<Record<string, boolean>>({});
const statusUpdating = ref<Record<string, boolean>>({});

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

const buildUpdatePayload = (
  row: IntegrationConfig,
  patch: IntegrationConfigMutationPayload = {},
): IntegrationConfigMutationPayload => {
  return {
    systemName: row.systemName,
    connectionConfig: row.connectionConfig || {},
    enabledModules: row.enabledModules || [],
    syncConfig: row.syncConfig || {},
    mappingConfig: row.mappingConfig || {},
    isEnabled: row.isEnabled,
    ...patch,
  };
};

const setLoadingState = (
  state: Record<string, boolean>,
  id: string,
  value: boolean,
) => {
  state[id] = value;
};

const loadConfigs = async () => {
  loading.value = true;

  try {
    configs.value = await getConfigs();
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.loadConfigsFailed"),
    );
  } finally {
    loading.value = false;
  }
};

const handleConfigure = (row: IntegrationConfig) => {
  selectedConfig.value = row;
  configDrawerVisible.value = true;
};

const handleStatusChange = async (
  row: IntegrationConfig,
  nextValue: string | number | boolean,
) => {
  setLoadingState(statusUpdating.value, row.id, true);

  try {
    await updateConfig(
      row.id,
      buildUpdatePayload(row, { isEnabled: Boolean(nextValue) }),
    );
    ElMessage.success(t("integration.messages.statusUpdated"));
    await loadConfigs();
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.operationFailed"),
    );
  } finally {
    setLoadingState(statusUpdating.value, row.id, false);
  }
};

const handleTest = async (row: IntegrationConfig) => {
  setLoadingState(testing.value, row.id, true);

  try {
    const result = await testConnection(row.id);

    if (result.success) {
      ElMessage.success(
        result.message || t("integration.messages.connectionTestSuccess"),
      );
    } else {
      ElMessage.error(
        result.message || t("integration.messages.connectionTestFailed"),
      );
    }

    await loadConfigs();
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.connectionTestFailed"),
    );
  } finally {
    setLoadingState(testing.value, row.id, false);
  }
};

const handleSync = async (row: IntegrationConfig) => {
  setLoadingState(syncing.value, row.id, true);

  try {
    await triggerSync(row.id, { async: true });
    ElMessage.success(t("integration.messages.syncTaskCreated"));
    await loadConfigs();
  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : t("integration.messages.syncFailed"),
    );
  } finally {
    setLoadingState(syncing.value, row.id, false);
  }
};

const stringifyConfig = (value: Record<string, unknown>) => {
  return Object.keys(value).length ? JSON.stringify(value, null, 2) : "{}";
};

onMounted(() => {
  void loadConfigs();
});
</script>

<style scoped>
.integration-list-page {
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

.status-card-grid {
  margin-bottom: 20px;
}

.table-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.name-cell__primary {
  font-weight: 600;
  color: #303133;
}

.name-cell__secondary {
  font-size: 12px;
  color: #909399;
}

.config-block {
  margin: 0;
  padding: 12px;
  border-radius: 8px;
  background: #f5f7fa;
  color: #303133;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 768px) {
  .integration-list-page {
    padding: 16px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
