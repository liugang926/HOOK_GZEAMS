<template>
  <div
    v-if="extension"
    class="lifecycle-detail-renderer"
  >
    <!-- Slot: action-bar — StatusActionBar replaces default edit/delete buttons -->
    <template v-if="$slots['action-bar']">
      <!-- Parent provides the slot, we just render inside it -->
    </template>

    <!-- Slot: header-extra — el-steps workflow progress -->
    <el-card
      v-if="extension.workflowSteps && currentStatus"
      class="steps-card mb-4"
      shadow="never"
    >
      <el-steps
        :active="getStepIndex(currentStatus)"
        finish-status="success"
      >
        <el-step
          v-for="step in extension.workflowSteps.steps"
          :key="step"
          :title="t(`${extension.workflowSteps.i18nPrefix}.${step}`)"
        />
      </el-steps>
    </el-card>

    <!-- Slot: after-sections — SubTablePanel + Cost Breakdown -->
    <div
      v-if="extension.subTable"
      class="lifecycle-sub-table mt-4"
    >
      <SubTablePanel
        :title="t('common.labels.items')"
        :columns="subTableColumns"
        :data="subTableItems"
        :loading="subTableLoading"
        :empty-text="t('common.messages.noData')"
        :show-summary="!!extension.subTable.summaryMethod"
        :summary-method="extension.subTable.summaryMethod"
      />
    </div>

    <!-- Cost Breakdown (Maintenance only) -->
    <el-card
      v-if="extension.showCostBreakdown && recordData"
      class="info-card mt-4"
      shadow="never"
    >
      <template #header>
        <span>{{ t('assets.lifecycle.maintenance.form.costBreakdown') }}</span>
      </template>
      <el-descriptions
        :column="4"
        border
      >
        <el-descriptions-item :label="t('assets.lifecycle.maintenance.form.laborCost')">
          ¥ {{ recordData.laborCost || recordData.labor_cost || 0 }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('assets.lifecycle.maintenance.form.materialCost')">
          ¥ {{ recordData.materialCost || recordData.material_cost || 0 }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('assets.lifecycle.maintenance.form.otherCost')">
          ¥ {{ recordData.otherCost || recordData.other_cost || 0 }}
        </el-descriptions-item>
        <el-descriptions-item :label="t('assets.lifecycle.maintenance.form.totalCost')">
          <span class="cost-total">¥ {{ recordData.totalCost || recordData.total_cost || 0 }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import SubTablePanel from '@/components/common/SubTablePanel.vue'
import { getLifecycleExtension, type LifecycleDetailExtension } from '@/platform/lifecycle/lifecycleDetailExtensions'
import type { StatusAction } from '@/components/common/StatusActionBar.vue'

const props = defineProps<{
  objectCode: string
  recordId: string
  recordData: Record<string, any> | null
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const { t } = useI18n()

const extension = computed<LifecycleDetailExtension | null>(() =>
  getLifecycleExtension(props.objectCode)
)

const currentStatus = computed(() => {
  if (!props.recordData) return ''
  return String(
    props.recordData.status ||
    props.recordData.state ||
    ''
  ).trim()
})

// ── StatusActionBar ──────────────────────────────────────────────────

const workflowActions = computed<StatusAction[]>(() => {
  if (!extension.value) return []
  return extension.value.statusActions(props.recordId, t as unknown as (key: string) => string)
})

// ── el-steps ─────────────────────────────────────────────────────────

const getStepIndex = (status: string): number => {
  if (!extension.value?.workflowSteps) return 0
  const idx = extension.value.workflowSteps.steps.indexOf(status)
  return idx >= 0 ? idx : 0
}

// ── SubTable ─────────────────────────────────────────────────────────

const subTableLoading = ref(false)
const subTableItems = ref<any[]>([])

const subTableColumns = computed(() => {
  if (!extension.value?.subTable) return []
  return extension.value.subTable.columns(t as unknown as (key: string) => string)
})

const fetchSubTableItems = async () => {
  if (!extension.value?.subTable) return
  subTableLoading.value = true
  try {
    subTableItems.value = await extension.value.subTable.fetchItems(props.recordId)
  } catch {
    subTableItems.value = []
  } finally {
    subTableLoading.value = false
  }
}

// ── Lifecycle ────────────────────────────────────────────────────────

watch(
  () => props.recordId,
  () => { if (props.recordId) fetchSubTableItems() }
)

onMounted(() => {
  if (props.recordId && extension.value?.subTable) {
    fetchSubTableItems()
  }
})

// Expose for parent (DynamicDetailPage) to access
defineExpose({
  workflowActions,
  currentStatus,
  getStepIndex,
  fetchSubTableItems,
})
</script>

<style scoped lang="scss">
.lifecycle-detail-renderer {
  width: 100%;
}

.steps-card {
  margin-bottom: 16px;

  :deep(.el-card__body) {
    padding: 20px 24px;
  }
}

.info-card {
  margin-top: 16px;
}

.cost-total {
  font-weight: 700;
  color: var(--el-color-danger);
  font-size: 16px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mt-4 {
  margin-top: 16px;
}
</style>
