<template>
  <div class="task-center">
    <div class="page-header">
      <h3>{{ $t("workflow.taskCenter.title") }}</h3>
    </div>

    <div
      v-if="drilldownMode"
      class="task-center__drilldown-banner"
    >
      <div class="task-center__drilldown-meta">
        <strong>{{ $t("workflow.taskCenter.drilldown.title") }}</strong>
        <div class="task-center__drilldown-chips">
          <span
            v-for="chip in drilldownChips"
            :key="chip.code"
            class="task-center__drilldown-chip"
          >
            {{ chip.label }}
          </span>
        </div>
      </div>
      <div class="task-center__drilldown-actions">
        <button
          type="button"
          class="task-center__drilldown-button"
          @click="toggleOverdueMode"
        >
          {{
            overdueOnly
              ? $t("workflow.taskCenter.drilldown.showOpen")
              : $t("workflow.taskCenter.drilldown.showOverdue")
          }}
        </button>
        <button
          type="button"
          class="task-center__drilldown-button task-center__drilldown-button--ghost"
          @click="clearDrilldownFilters"
        >
          {{ $t("workflow.taskCenter.drilldown.clear") }}
        </button>
      </div>
    </div>

    <el-tabs
      v-model="activeTab"
      @tab-click="handleTabClick"
    >
      <el-tab-pane
        :label="$t('workflow.taskCenter.tabs.pending')"
        name="pending"
      >
        <el-table
          v-loading="loading"
          :data="pendingTasks"
          border
        >
          <el-table-column
            prop="title"
            :label="$t('workflow.columns.taskTitle')"
          />
          <el-table-column
            prop="process_name"
            :label="$t('workflow.columns.processType')"
          />
          <el-table-column
            prop="create_time"
            :label="$t('workflow.columns.receiveTime')"
          />
          <el-table-column
            prop="initiator"
            :label="$t('workflow.columns.initiator')"
          />
          <el-table-column :label="$t('workflow.columns.operation')">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleProcess(row)"
              >
                {{ $t("workflow.actions.process") }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane
        :label="$t('workflow.taskCenter.tabs.processed')"
        name="processed"
      >
        <el-table
          v-loading="loading"
          :data="processedTasks"
          border
        >
          <el-table-column
            prop="title"
            :label="$t('workflow.columns.taskTitle')"
          />
          <el-table-column
            prop="process_name"
            :label="$t('workflow.columns.processType')"
          />
          <el-table-column
            prop="process_time"
            :label="$t('workflow.columns.processTime')"
          />
          <el-table-column
            prop="result"
            :label="$t('workflow.columns.result')"
          />
          <el-table-column :label="$t('workflow.columns.operation')">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                @click="handleView(row)"
              >
                {{ $t("common.actions.view") }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from "vue";
import { useRoute, useRouter, type LocationQueryRaw } from "vue-router";
import { getUserTasks, workflowNodeApi } from "@/api/workflow";
import { useI18n } from "vue-i18n";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const activeTab = ref("pending");
const loading = ref(false);
const pendingTasks = ref<any[]>([]);
const processedTasks = ref<any[]>([]);

const readQueryString = (value: unknown) => {
  return typeof value === "string" ? value : "";
};

const readQueryBoolean = (value: unknown) => {
  return value === "true" || value === "1" || value === true;
};

const normalizeTaskList = (payload: any) => {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.results)) {
    return payload.results;
  }
  if (Array.isArray(payload?.data?.results)) {
    return payload.data.results;
  }
  return [];
};

const isDrilldownMode = () => {
  return Boolean(
    readQueryString(route.query.assignee) ||
    readQueryString(route.query.department) ||
    readQueryBoolean(route.query.overdue_only),
  );
};

const drilldownMode = computed(() => isDrilldownMode());
const overdueOnly = computed(() => readQueryBoolean(route.query.overdue_only));

const drilldownChips = computed(() => {
  const chips: Array<{ code: string; label: string }> = [];
  const sourceLabel = readQueryString(route.query.source_label);
  const assigneeLabel =
    readQueryString(route.query.assignee_label) ||
    readQueryString(route.query.owner_label);
  const departmentLabel = readQueryString(route.query.department_label);

  if (sourceLabel) {
    chips.push({
      code: "source",
      label: t("workflow.taskCenter.drilldown.source", { value: sourceLabel }),
    });
  }
  if (assigneeLabel) {
    chips.push({
      code: "assignee",
      label: t("workflow.taskCenter.drilldown.assignee", {
        value: assigneeLabel,
      }),
    });
  }
  if (departmentLabel) {
    chips.push({
      code: "department",
      label: t("workflow.taskCenter.drilldown.department", {
        value: departmentLabel,
      }),
    });
  }
  if (overdueOnly.value) {
    chips.push({
      code: "overdue",
      label: t("workflow.taskCenter.drilldown.overdueOnly"),
    });
  }

  return chips;
});

const buildTaskListParams = () => {
  const params: Record<string, string | number | boolean> = {
    page: 1,
    page_size: 20,
    status: activeTab.value === "pending" ? "pending" : "approved",
  };

  const assignee = readQueryString(route.query.assignee);
  const department = readQueryString(route.query.department);
  const overdueOnly = readQueryBoolean(route.query.overdue_only);

  if (assignee) {
    params.assignee = assignee;
  }
  if (department) {
    params.department = department;
  }
  if (overdueOnly && activeTab.value === "pending") {
    params.overdue_only = true;
  }

  return params;
};

const fetchData = async () => {
  loading.value = true;
  try {
    if (isDrilldownMode()) {
      const response = await getUserTasks(buildTaskListParams());
      const results = normalizeTaskList(response);
      if (activeTab.value === "pending") {
        pendingTasks.value = results;
      } else {
        processedTasks.value = results;
      }
      return;
    }

    if (activeTab.value === "pending") {
      const res = await workflowNodeApi.getMyTasks({
        page: 1,
        pageSize: 20,
        status: "pending",
      });
      pendingTasks.value = res.results || [];
    } else {
      const res = await workflowNodeApi.getMyTasks({
        page: 1,
        pageSize: 20,
        status: "approved",
      });
      processedTasks.value = res.results || [];
    }
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const handleTabClick = () => {
  fetchData();
};

const handleProcess = (row: any) => {
  router.push(`/workflow/task/${row.id}`);
};

const handleView = (row: any) => {
  router.push(`/workflow/process/${row.process_instance_id}`);
};

const clearDrilldownFilters = () => {
  router.push("/workflow/tasks");
};

const toggleOverdueMode = () => {
  const nextQuery: LocationQueryRaw = { ...route.query };
  if (overdueOnly.value) {
    delete nextQuery.overdue_only;
  } else {
    nextQuery.overdue_only = "true";
  }
  router.push({
    path: "/workflow/tasks",
    query: nextQuery,
  });
};

onMounted(() => {
  fetchData();
});

watch(
  () => route.query,
  () => {
    fetchData();
  },
);
</script>

<style scoped>
.task-center {
  padding: 20px;
}

.task-center__drilldown-banner {
  margin-bottom: 16px;
  padding: 14px 16px;
  border: 1px solid #dbeafe;
  border-radius: 16px;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.task-center__drilldown-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-center__drilldown-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-center__drilldown-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 600;
}

.task-center__drilldown-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.task-center__drilldown-button {
  border: 1px solid #1d4ed8;
  background: #1d4ed8;
  color: #ffffff;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.task-center__drilldown-button--ghost {
  background: #ffffff;
  color: #1d4ed8;
}
</style>
