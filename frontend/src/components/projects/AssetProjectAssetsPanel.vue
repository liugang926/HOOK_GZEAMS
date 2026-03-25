<template>
  <el-card
    class="asset-project-panel"
    shadow="never"
  >
    <template #header>
      <div class="asset-project-panel__header">
        <div class="asset-project-panel__heading">
          <div class="asset-project-panel__title-row">
            <span>{{ title }}</span>
            <span class="asset-project-panel__meta">{{ displayTotalCount }}</span>
          </div>
          <p class="asset-project-panel__hint">
            {{ t('projects.panels.assetsHint') }}
          </p>
        </div>

        <div class="asset-project-panel__actions">
          <el-button
            size="small"
            @click="loadAssets"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
          <el-button
            size="small"
            @click="handleViewAll"
          >
            {{ t('projects.actions.viewAllAssets') }}
          </el-button>
          <el-button
            size="small"
            type="primary"
            @click="handleCreate"
          >
            {{ t('projects.actions.addAsset') }}
          </el-button>
        </div>
      </div>
    </template>

    <el-empty
      v-if="!loading && assets.length === 0"
      :description="t('projects.messages.emptyAssets')"
    />

    <el-table
      v-else
      v-loading="loading"
      :data="assets"
      border
      stripe
      @row-click="handleRowClick"
    >
      <el-table-column
        prop="allocationNo"
        :label="t('projects.columns.allocationNo')"
        min-width="150"
      />
      <el-table-column
        prop="assetCode"
        :label="t('projects.columns.assetCode')"
        min-width="140"
      />
      <el-table-column
        prop="assetName"
        :label="t('projects.columns.assetName')"
        min-width="180"
      />
      <el-table-column
        :label="t('projects.columns.allocationType')"
        width="140"
      >
        <template #default="{ row }">
          <el-tag type="info">
            {{ resolveAllocationTypeLabel(String(row.allocationType || '')) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.returnStatus')"
        width="130"
      >
        <template #default="{ row }">
          <el-tag :type="resolveReturnStatusType(String(row.returnStatus || ''))">
            {{ resolveReturnStatusLabel(String(row.returnStatus || '')) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.latestReturn')"
        min-width="240"
      >
        <template #default="{ row }">
          <div
            v-if="resolveLatestReturnSummary(row)"
            class="asset-project-panel__return-summary"
          >
            <el-button
              link
              type="primary"
              class="asset-project-panel__return-link"
              @click.stop="handleOpenLatestReturn(row)"
            >
              {{ resolveLatestReturnSummary(row)?.returnNo || '--' }}
            </el-button>
            <div class="asset-project-panel__return-meta">
              <el-tag
                size="small"
                :type="resolveLatestReturnStatusType(String(resolveLatestReturnSummary(row)?.status || ''))"
              >
                {{ resolveLatestReturnSummary(row)?.statusLabel || '--' }}
              </el-tag>
              <span class="asset-project-panel__return-date">
                {{ formatDate(String(resolveLatestReturnSummary(row)?.eventAt || resolveLatestReturnSummary(row)?.returnDate || '')) || '--' }}
              </span>
            </div>
            <p class="asset-project-panel__return-caption">
              {{ resolveLatestReturnCaption(row) || '--' }}
            </p>
          </div>
          <span v-else>--</span>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.custodian')"
        min-width="140"
      >
        <template #default="{ row }">
          {{ resolveUserName(row.custodianDetail) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.allocationDate')"
        width="130"
      >
        <template #default="{ row }">
          {{ formatDate(String(row.allocationDate || '')) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.allocationCost')"
        min-width="130"
        align="right"
      >
        <template #default="{ row }">
          {{ formatMoney(Number(row.allocationCost || 0)) }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.columns.actions')"
        min-width="220"
        fixed="right"
      >
        <template #default="{ row }">
          <div
            v-if="canOperateAllocation(row)"
            class="asset-project-panel__row-actions"
          >
            <el-button
              link
              type="primary"
              @click.stop="handleCreateReturn(row)"
            >
              {{ t('projects.actions.recycleAsset') }}
            </el-button>
            <el-button
              link
              type="warning"
              @click.stop="handleOpenTransfer(row)"
            >
              {{ t('projects.actions.transferToProject') }}
            </el-button>
          </div>
          <span v-else>--</span>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="transferDialogVisible"
      :title="t('projects.transferDialog.title')"
      width="480px"
    >
      <el-form
        label-position="top"
        class="asset-project-panel__transfer-form"
      >
        <el-form-item :label="t('projects.transferDialog.asset')">
          <el-input
            :model-value="transferForm.assetLabel"
            readonly
          />
        </el-form-item>
        <el-form-item :label="t('projects.transferDialog.targetProject')">
          <el-select
            v-model="transferForm.targetProjectId"
            filterable
            clearable
            :loading="projectOptionsLoading"
            :placeholder="t('projects.transferDialog.targetProjectPlaceholder')"
          >
            <el-option
              v-for="option in targetProjectOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('projects.transferDialog.reason')">
          <el-input
            v-model="transferForm.reason"
            type="textarea"
            :rows="4"
            :placeholder="t('projects.transferDialog.reasonPlaceholder')"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="asset-project-panel__dialog-footer">
          <el-button @click="transferDialogVisible = false">
            {{ t('common.actions.cancel') }}
          </el-button>
          <el-button
            type="primary"
            :loading="transferLoading"
            @click="handleConfirmTransfer"
          >
            {{ t('common.actions.confirm') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { createObjectClient, type ListResponse } from '@/api/dynamic'
import request from '@/utils/request'
import { formatDate } from '@/utils/dateFormat'
import { formatMoney } from '@/utils/numberFormat'
import {
  buildAssetProjectReturnCreateRoute,
  formatTransferProjectOptionLabel,
} from './assetProjectAssetActions'

const props = defineProps<{
  panel: Record<string, unknown>
  recordId: string
  recordData?: Record<string, unknown> | null
  refreshVersion?: number
  panelRefreshVersion?: number
  workspaceDashboard?: Record<string, unknown> | null
  workspaceDashboardEnabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'workbench-refresh-requested', payload: { summary?: boolean; detail?: boolean; panels?: string[] }): void
}>()

const { t, te } = useI18n()
const router = useRouter()
const assetProjectApi = createObjectClient('AssetProject')
const projectAssetApi = createObjectClient('ProjectAsset')
const loading = ref(false)
const totalCount = ref(0)
const assets = ref<Array<Record<string, unknown>>>([])
const transferDialogVisible = ref(false)
const transferLoading = ref(false)
const projectOptionsLoading = ref(false)
const targetProjectOptions = ref<Array<{ label: string; value: string }>>([])
const transferForm = ref({
  allocationId: '',
  assetLabel: '',
  targetProjectId: '',
  reason: '',
})

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('projects.panels.assets'))
})

const resolveUserName = (value: unknown) => {
  if (!value || typeof value !== 'object') return ''
  const candidate = value as Record<string, unknown>
  return String(
    candidate.fullName ||
    candidate.full_name ||
    candidate.name ||
    candidate.username ||
    ''
  ).trim()
}

const resolveAllocationTypeLabel = (value: string) => {
  const key = `projects.allocationType.${value}`
  return value && te(key) ? t(key) : value
}

const resolveDashboardCount = (
  segmentKey: string,
  countKeys: string[],
): number | null => {
  if (!props.workspaceDashboard || typeof props.workspaceDashboard !== 'object') {
    return null
  }
  const segment = props.workspaceDashboard[segmentKey]
  if (!segment || typeof segment !== 'object') {
    return null
  }
  const candidate = segment as Record<string, unknown>
  for (const key of countKeys) {
    const value = candidate[key]
    if (value === null || value === undefined || value === '') {
      continue
    }
    const normalized = Number(value)
    if (Number.isFinite(normalized)) {
      return normalized
    }
  }
  return null
}

const sharedTotalCount = computed(() => resolveDashboardCount('assets', ['totalCount', 'total_count']))
const displayTotalCount = computed(() => {
  return sharedTotalCount.value ?? totalCount.value
})

const resolveReturnStatusLabel = (value: string) => {
  const key = `projects.returnStatus.${value}`
  return value && te(key) ? t(key) : value
}

const resolveReturnStatusType = (value: string) => {
  if (value === 'in_use') return 'success'
  if (value === 'transferred') return 'warning'
  if (value === 'returned') return 'info'
  return 'info'
}

interface LatestReturnSummary {
  returnId?: string
  returnNo?: string
  status?: string
  statusLabel?: string
  returnDate?: string
  returnReason?: string
  rejectReason?: string
  eventAt?: string
}

interface ListEnvelope<T> {
  count?: number
  results?: T[]
}

const resolveListEnvelope = <T extends Record<string, unknown>>(
  result: ListResponse<T> | ListEnvelope<T>
): ListEnvelope<T> => {
  if ('data' in result && result.data && typeof result.data === 'object') {
    return result.data
  }
  return {
    count: 'count' in result ? result.count : undefined,
    results: 'results' in result ? result.results : undefined,
  }
}

const canOperateAllocation = (row: Record<string, unknown>) => {
  return String(row.returnStatus || row.return_status || '').trim() === 'in_use'
}

const resolveLatestReturnSummary = (row: Record<string, unknown>): LatestReturnSummary | null => {
  const candidate = row.latestReturnSummary || row.latest_return_summary
  if (!candidate || typeof candidate !== 'object') return null

  const summary = candidate as Record<string, unknown>
  return {
    returnId: String(summary.returnId || summary.return_id || '').trim(),
    returnNo: String(summary.returnNo || summary.return_no || '').trim(),
    status: String(summary.status || '').trim(),
    statusLabel: String(summary.statusLabel || summary.status_label || '').trim(),
    returnDate: String(summary.returnDate || summary.return_date || '').trim(),
    returnReason: String(summary.returnReason || summary.return_reason || '').trim(),
    rejectReason: String(summary.rejectReason || summary.reject_reason || '').trim(),
    eventAt: String(summary.eventAt || summary.event_at || '').trim(),
  }
}

const resolveLatestReturnStatusType = (value: string) => {
  if (value === 'completed') return 'success'
  if (value === 'rejected') return 'danger'
  if (value === 'pending') return 'warning'
  return 'info'
}

const resolveLatestReturnCaption = (row: Record<string, unknown>) => {
  const summary = resolveLatestReturnSummary(row)
  if (!summary) return ''
  return summary.rejectReason || summary.returnReason || ''
}

const loadTransferTargets = async () => {
  projectOptionsLoading.value = true
  try {
    const result = await assetProjectApi.list({
      status: 'active',
      page: 1,
      page_size: 50,
      ordering: 'project_code',
    })
    const envelope = resolveListEnvelope(result)
    const rows = Array.isArray(envelope.results) ? envelope.results : []
    targetProjectOptions.value = rows
      .map((row) => ({
        label: formatTransferProjectOptionLabel(row),
        value: String(row.id || '').trim(),
      }))
      .filter((option) => option.value && option.value !== props.recordId && option.label)
  } catch (error: unknown) {
    targetProjectOptions.value = []
    ElMessage.error(
      error instanceof Error ? error.message : t('projects.messages.loadTransferTargetsFailed')
    )
  } finally {
    projectOptionsLoading.value = false
  }
}

const loadAssets = async () => {
  if (!props.recordId) return
  loading.value = true
  try {
    const result = await projectAssetApi.list({
      project: props.recordId,
      page: 1,
      page_size: 6,
      ordering: '-allocation_date',
    })
    const envelope = resolveListEnvelope(result)
    totalCount.value = Number(envelope.count || 0)
    assets.value = Array.isArray(envelope.results) ? envelope.results : []
  } catch (error: unknown) {
    totalCount.value = 0
    assets.value = []
    ElMessage.error(error instanceof Error ? error.message : t('projects.messages.loadAssetsFailed'))
  } finally {
    loading.value = false
  }
}

const handleViewAll = () => {
  router.push({
    path: '/objects/ProjectAsset',
    query: { project: props.recordId },
  })
}

const handleCreate = () => {
  router.push({
    path: '/objects/ProjectAsset/create',
    query: {
      prefill_project: props.recordId,
      returnTo: `/objects/AssetProject/${props.recordId}`,
    },
  })
}

const handleCreateReturn = (row: Record<string, unknown>) => {
  router.push(
    buildAssetProjectReturnCreateRoute({
      projectId: props.recordId,
      projectRecord: props.recordData,
      row,
    })
  )
}

const handleOpenLatestReturn = (row: Record<string, unknown>) => {
  const returnId = String(resolveLatestReturnSummary(row)?.returnId || '').trim()
  if (!returnId) return
  router.push(`/objects/AssetReturn/${encodeURIComponent(returnId)}`)
}

const handleOpenTransfer = async (row: Record<string, unknown>) => {
  transferForm.value = {
    allocationId: String(row.id || '').trim(),
    assetLabel: `${String(row.assetCode || row.asset_code || '').trim()} ${String(row.assetName || row.asset_name || '').trim()}`.trim(),
    targetProjectId: '',
    reason: '',
  }
  transferDialogVisible.value = true
  await loadTransferTargets()
}

const handleConfirmTransfer = async () => {
  if (!transferForm.value.allocationId) return
  if (!transferForm.value.targetProjectId) {
    ElMessage.warning(t('projects.messages.transferTargetRequired'))
    return
  }

  transferLoading.value = true
  try {
    const response = await request.post<{
      success?: boolean
      message?: string
      error?: { message?: string }
    }>(
      `/system/objects/ProjectAsset/${transferForm.value.allocationId}/transfer/`,
      {
        target_project_id: transferForm.value.targetProjectId,
        reason: transferForm.value.reason,
      },
      { unwrap: 'none' }
    )

    if (response.success === false) {
      throw new Error(String(response.error?.message || response.message || t('projects.messages.transferFailed')))
    }

    transferDialogVisible.value = false
    ElMessage.success(String(response.message || t('projects.messages.transferSuccess')))
    await loadAssets()
    emit('workbench-refresh-requested', { summary: true })
  } catch (error: unknown) {
    ElMessage.error(error instanceof Error ? error.message : t('projects.messages.transferFailed'))
  } finally {
    transferLoading.value = false
  }
}

const handleRowClick = (row: Record<string, unknown>) => {
  const recordId = String(row.id || '').trim()
  if (!recordId) return
  router.push(`/objects/ProjectAsset/${encodeURIComponent(recordId)}`)
}

watch(
  () => [props.recordId, props.refreshVersion, props.panelRefreshVersion],
  () => {
    void loadAssets()
  },
  { immediate: true }
)
</script>

<style scoped>
.asset-project-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.asset-project-panel__heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.asset-project-panel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-project-panel__meta {
  font-size: 12px;
  color: #606266;
}

.asset-project-panel__hint {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.asset-project-panel__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.asset-project-panel__row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.asset-project-panel__return-summary {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.asset-project-panel__return-link {
  justify-content: flex-start;
  padding: 0;
}

.asset-project-panel__return-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-project-panel__return-date {
  font-size: 12px;
  color: #909399;
}

.asset-project-panel__return-caption {
  margin: 0;
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}

.asset-project-panel__transfer-form {
  display: flex;
  flex-direction: column;
}

.asset-project-panel__dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
