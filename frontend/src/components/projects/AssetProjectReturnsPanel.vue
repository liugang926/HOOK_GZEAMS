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
            {{ t('projects.panels.returnsHint') }}
          </p>
        </div>

        <div class="asset-project-panel__actions">
          <el-button
            size="small"
            @click="loadReturns"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
          <el-button
            size="small"
            @click="handleViewAll"
          >
            {{ t('projects.actions.viewAllReturns') }}
          </el-button>
        </div>
      </div>
    </template>

    <el-empty
      v-if="!loading && returns.length === 0"
      :description="t('projects.messages.emptyReturns')"
    />

    <el-table
      v-else
      v-loading="loading"
      :data="returns"
      border
      stripe
      @row-click="handleRowClick"
    >
      <el-table-column
        :label="t('projects.columns.returnNo')"
        min-width="160"
      >
        <template #default="{ row }">
          {{ resolveText(row, ['returnNo', 'return_no']) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.returner')"
        min-width="150"
      >
        <template #default="{ row }">
          {{ resolveUserName(row.returner) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.returnDate')"
        width="130"
      >
        <template #default="{ row }">
          {{ formatDate(resolveText(row, ['returnDate', 'return_date'])) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.itemsCount')"
        width="110"
        align="center"
      >
        <template #default="{ row }">
          {{ Number(row.itemsCount || row.items_count || 0) }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.returnReason')"
        min-width="240"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          {{ resolveText(row, ['returnReason', 'return_reason']) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.columns.actions')"
        width="220"
        fixed="right"
      >
        <template #default="{ row }">
          <div class="asset-project-panel__row-actions">
            <el-button
              link
              type="success"
              :loading="loadingReturnId === String(row.id || '')"
              @click.stop="handleConfirm(row)"
            >
              {{ t('projects.actions.confirmReturnOrder') }}
            </el-button>
            <el-button
              link
              type="danger"
              :loading="loadingReturnId === String(row.id || '')"
              @click.stop="handleReject(row)"
            >
              {{ t('common.actions.reject') }}
            </el-button>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { createObjectClient, type ListResponse } from '@/api/dynamic'
import request from '@/utils/request'
import { formatDate } from '@/utils/dateFormat'

const props = defineProps<{
  panel: Record<string, unknown>
  recordId: string
  refreshVersion?: number
  panelRefreshVersion?: number
  workspaceDashboard?: Record<string, unknown> | null
  workspaceDashboardEnabled?: boolean
}>()

const emit = defineEmits<{
  (e: 'workbench-refresh-requested', payload: { summary?: boolean; detail?: boolean; panels?: string[] }): void
}>()

interface ReturnOrderRecord extends Record<string, unknown> {
  id?: string
}

interface ListEnvelope<T> {
  count?: number
  results?: T[]
}

const { t, te } = useI18n()
const router = useRouter()
const assetReturnApi = createObjectClient('AssetReturn')
const loading = ref(false)
const loadingReturnId = ref('')
const totalCount = ref(0)
const returns = ref<ReturnOrderRecord[]>([])

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('projects.panels.pendingReturns'))
})

const resolveText = (row: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    const value = String(row[key] || '').trim()
    if (value) return value
  }
  return ''
}

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

const sharedTotalCount = computed(() => resolveDashboardCount('returns', ['pendingCount', 'pending_count']))
const displayTotalCount = computed(() => {
  return sharedTotalCount.value ?? totalCount.value
})

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

const loadReturns = async () => {
  if (!props.recordId) return
  loading.value = true
  try {
    const result = await assetReturnApi.list({
      project: props.recordId,
      status: 'pending',
      page: 1,
      page_size: 6,
    })
    const envelope = resolveListEnvelope(result)
    totalCount.value = Number(envelope.count || 0)
    returns.value = Array.isArray(envelope.results) ? envelope.results : []
  } catch (error: unknown) {
    totalCount.value = 0
    returns.value = []
    ElMessage.error(error instanceof Error ? error.message : t('projects.messages.loadReturnsFailed'))
  } finally {
    loading.value = false
  }
}

const handleViewAll = () => {
  router.push({
    path: '/objects/AssetReturn',
    query: { project: props.recordId },
  })
}

const handleRowClick = (row: ReturnOrderRecord) => {
  const recordId = String(row.id || '').trim()
  if (!recordId) return
  router.push(`/objects/AssetReturn/${encodeURIComponent(recordId)}`)
}

const handleConfirm = async (row: ReturnOrderRecord) => {
  const recordId = String(row.id || '').trim()
  if (!recordId) return

  try {
    await ElMessageBox.confirm(
      t('projects.messages.confirmReturnOrder'),
      t('common.dialog.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel'),
      }
    )
  } catch {
    return
  }

  loadingReturnId.value = recordId
  try {
    const response = await request<{
      success?: boolean
      message?: string
      error?: { message?: string }
    }>({
      url: `/system/objects/AssetReturn/${recordId}/confirm/`,
      method: 'post',
      data: {},
      unwrap: 'none',
    })

    if (response.success === false) {
      throw new Error(String(response.error?.message || response.message || t('projects.messages.loadReturnsFailed')))
    }

    ElMessage.success(String(response.message || t('projects.messages.confirmReturnSuccess')))
    await loadReturns()
    emit('workbench-refresh-requested', {
      summary: true,
      panels: ['project_assets', 'project_return_history'],
    })
  } catch (error: unknown) {
    ElMessage.error(error instanceof Error ? error.message : t('common.messages.operationFailed'))
  } finally {
    loadingReturnId.value = ''
  }
}

const handleReject = async (row: ReturnOrderRecord) => {
  const recordId = String(row.id || '').trim()
  if (!recordId) return

  let reason = ''
  try {
    const result = await ElMessageBox.prompt(
      t('projects.messages.confirmRejectReturnOrder'),
      t('common.actions.reject'),
      {
        inputPattern: /\S+/,
        inputErrorMessage: t('projects.messages.rejectReasonRequired'),
      }
    )
    reason = String(result.value || '').trim()
  } catch {
    return
  }

  loadingReturnId.value = recordId
  try {
    const response = await request<{
      success?: boolean
      message?: string
      error?: { message?: string }
    }>({
      url: `/system/objects/AssetReturn/${recordId}/reject/`,
      method: 'post',
      data: { reason },
      unwrap: 'none',
    })

    if (response.success === false) {
      throw new Error(String(response.error?.message || response.message || t('projects.messages.loadReturnsFailed')))
    }

    ElMessage.success(String(response.message || t('projects.messages.rejectReturnSuccess')))
    await loadReturns()
    emit('workbench-refresh-requested', {
      summary: true,
      panels: ['project_assets', 'project_return_history'],
    })
  } catch (error: unknown) {
    ElMessage.error(error instanceof Error ? error.message : t('common.messages.operationFailed'))
  } finally {
    loadingReturnId.value = ''
  }
}

watch(
  () => [props.recordId, props.refreshVersion, props.panelRefreshVersion],
  () => {
    void loadReturns()
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
  align-items: center;
  gap: 8px;
}

.asset-project-panel__row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
