<template>
  <div class="difference-list">
    <el-card shadow="never">
      <template #header>
        <div class="difference-list__header">
          <div class="difference-list__header-main">
            <span class="difference-list__title">
              {{ t('inventory.differenceList.title') }}
            </span>
            <el-tag
              v-if="currentTaskId"
              type="info"
            >
              {{ t('inventory.differenceList.taskFilter', { taskId: currentTaskId }) }}
            </el-tag>
          </div>

          <div class="difference-list__header-actions">
            <el-select
              v-model="filterStatus"
              clearable
              style="width: 180px"
              :placeholder="t('inventory.differenceList.filters.status')"
              @change="handleFilterChange"
            >
              <el-option
                :label="t('inventory.differenceList.statuses.all')"
                value=""
              />
              <el-option
                :label="t('inventory.differenceList.statuses.pending')"
                value="pending"
              />
              <el-option
                :label="t('inventory.differenceList.statuses.confirmed')"
                value="confirmed"
              />
              <el-option
                :label="t('inventory.differenceList.statuses.inReview')"
                value="in_review"
              />
              <el-option
                :label="t('inventory.differenceList.statuses.approved')"
                value="approved"
              />
              <el-option
                :label="t('inventory.differenceList.statuses.executing')"
                value="executing"
              />
              <el-option
                :label="t('inventory.differenceList.statuses.resolved')"
                value="resolved"
              />
              <el-option
                :label="t('inventory.differenceList.statuses.ignored')"
                value="ignored"
              />
              <el-option
                :label="t('inventory.differenceList.statuses.closed')"
                value="closed"
              />
            </el-select>

            <el-select
              v-model="filterType"
              clearable
              style="width: 180px"
              :placeholder="t('inventory.differenceList.filters.type')"
              @change="handleFilterChange"
            >
              <el-option
                :label="t('inventory.differenceList.types.all')"
                value=""
              />
              <el-option
                :label="t('inventory.differenceList.types.normal')"
                value="normal"
              />
              <el-option
                :label="t('inventory.differenceList.types.missing')"
                value="missing"
              />
              <el-option
                :label="t('inventory.differenceList.types.extra')"
                value="extra"
              />
              <el-option
                :label="t('inventory.differenceList.types.damaged')"
                value="damaged"
              />
              <el-option
                :label="t('inventory.differenceList.types.locationMismatch')"
                value="location_mismatch"
              />
              <el-option
                :label="t('inventory.differenceList.types.custodianMismatch')"
                value="custodian_mismatch"
              />
            </el-select>

            <el-button @click="handleBatchResolve">
              {{ t('inventory.differenceList.actions.batchHandle') }}
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="differences"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column
          type="selection"
          width="52"
        />

        <el-table-column
          prop="taskCode"
          :label="t('inventory.differenceList.columns.taskCode')"
          min-width="150"
        />

        <el-table-column
          prop="assetCode"
          :label="t('inventory.differenceList.columns.assetCode')"
          min-width="150"
        >
          <template #default="{ row }">
            {{ getAssetCode(row) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="assetName"
          :label="t('inventory.differenceList.columns.assetName')"
          min-width="180"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ getAssetName(row) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="differenceType"
          :label="t('inventory.differenceList.columns.differenceType')"
          width="150"
        >
          <template #default="{ row }">
            <el-tag :type="getDifferenceTagType(row.differenceType)">
              {{ getDifferenceLabel(row.differenceType, row.differenceTypeLabel) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="expectedLocation"
          :label="t('inventory.differenceList.columns.expectedLocation')"
          min-width="160"
          show-overflow-tooltip
        />

        <el-table-column
          prop="actualLocation"
          :label="t('inventory.differenceList.columns.actualLocation')"
          min-width="160"
          show-overflow-tooltip
        />

        <el-table-column
          prop="status"
          :label="t('inventory.differenceList.columns.status')"
          width="130"
        >
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status, row.statusLabel) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="resolution"
          :label="t('inventory.differenceList.columns.remark')"
          min-width="240"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ row.resolution || row.description || row.remark || '--' }}
          </template>
        </el-table-column>

        <el-table-column
          prop="createdAt"
          :label="t('inventory.differenceList.columns.createdAt')"
          width="180"
        >
          <template #default="{ row }">
            {{ row.createdAt ? formatDateTime(row.createdAt) : '--' }}
          </template>
        </el-table-column>

        <el-table-column
          :label="t('common.table.operations')"
          width="180"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              link
              type="primary"
              @click="handleConfirm(row)"
            >
              {{ t('inventory.differenceList.actions.confirm') }}
            </el-button>
            <el-button
              v-if="canAdjustDifference(row)"
              link
              type="warning"
              @click="handleAdjust(row)"
            >
              {{ t('inventory.differenceList.actions.adjust') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="difference-list__pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50, 100]"
          @current-change="loadDifferences"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>

    <BatchResolveDialog
      v-model="batchDialogVisible"
      :differences="selectedDifferences"
      @resolved="handleResolved"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { inventoryApi } from '@/api/inventory'
import type {
  InventoryDifference,
  InventoryDifferenceStatus,
  InventoryDifferenceType,
} from '@/types/inventory'
import { formatDateTime } from '@/utils/dateFormat'
import BatchResolveDialog from './BatchResolveDialog.vue'

const route = useRoute()
const { t } = useI18n()

const loading = ref(false)
const differences = ref<InventoryDifference[]>([])
const selectedDifferences = ref<InventoryDifference[]>([])
const filterStatus = ref('')
const filterType = ref('')
const batchDialogVisible = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const currentTaskId = computed(() => {
  const routeTaskId = route.query.taskId || route.params.taskId
  return typeof routeTaskId === 'string' && routeTaskId.trim() ? routeTaskId.trim() : ''
})

const getErrorMessage = (error: unknown, fallbackKey: string) => {
  if (error && typeof error === 'object' && 'message' in error && typeof error.message === 'string') {
    return error.message
  }
  return t(fallbackKey)
}

const getAssetCode = (difference: InventoryDifference) => {
  if (difference.assetCode) return difference.assetCode
  if (difference.asset && typeof difference.asset === 'object' && 'assetCode' in difference.asset) {
    return String(difference.asset.assetCode || '--')
  }
  if (difference.asset && typeof difference.asset === 'object' && 'code' in difference.asset) {
    return String(difference.asset.code || '--')
  }
  return '--'
}

const getAssetName = (difference: InventoryDifference) => {
  if (difference.assetName) return difference.assetName
  if (difference.asset && typeof difference.asset === 'object' && 'assetName' in difference.asset) {
    return String(difference.asset.assetName || '--')
  }
  if (difference.asset && typeof difference.asset === 'object' && 'name' in difference.asset) {
    return String(difference.asset.name || '--')
  }
  return '--'
}

const getDifferenceTagType = (type: InventoryDifferenceType | string) => {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    normal: 'success',
    missing: 'danger',
    extra: 'warning',
    surplus: 'warning',
    damaged: 'danger',
    location_mismatch: 'info',
    custodian_mismatch: 'info',
  }
  return typeMap[type] || 'info'
}

const getDifferenceLabel = (type: InventoryDifferenceType | string, fallback?: string) => {
  if (fallback) return fallback

  const keyMap: Record<string, string> = {
    normal: 'inventory.differenceList.types.normal',
    missing: 'inventory.differenceList.types.missing',
    extra: 'inventory.differenceList.types.extra',
    surplus: 'inventory.differenceList.types.extra',
    damaged: 'inventory.differenceList.types.damaged',
    location_mismatch: 'inventory.differenceList.types.locationMismatch',
    custodian_mismatch: 'inventory.differenceList.types.custodianMismatch',
  }

  return keyMap[type] ? t(keyMap[type]) : type
}

const getStatusTagType = (status: InventoryDifferenceStatus | string) => {
  const typeMap: Record<string, 'warning' | 'info' | 'primary' | 'success' | 'danger'> = {
    pending: 'warning',
    confirmed: 'info',
    in_review: 'primary',
    approved: 'primary',
    executing: 'primary',
    resolved: 'success',
    ignored: 'danger',
    closed: 'success',
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: InventoryDifferenceStatus | string, fallback?: string) => {
  if (fallback) return fallback

  const keyMap: Record<string, string> = {
    pending: 'inventory.differenceList.statuses.pending',
    confirmed: 'inventory.differenceList.statuses.confirmed',
    in_review: 'inventory.differenceList.statuses.inReview',
    approved: 'inventory.differenceList.statuses.approved',
    executing: 'inventory.differenceList.statuses.executing',
    resolved: 'inventory.differenceList.statuses.resolved',
    ignored: 'inventory.differenceList.statuses.ignored',
    closed: 'inventory.differenceList.statuses.closed',
  }

  return keyMap[status] ? t(keyMap[status]) : status
}

const canAdjustDifference = (difference: InventoryDifference) => {
  return ['pending', 'confirmed', 'approved'].includes(difference.status)
}

const loadDifferences = async () => {
  loading.value = true
  try {
    const response = await inventoryApi.getDifferences({
      page: pagination.page,
      pageSize: pagination.pageSize,
      taskId: currentTaskId.value || undefined,
      status: filterStatus.value || undefined,
      differenceType: filterType.value || undefined,
      ordering: '-created_at',
    })

    differences.value = response.results
    pagination.total = response.count
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, 'inventory.differenceList.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleFilterChange = () => {
  pagination.page = 1
  loadDifferences()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  loadDifferences()
}

const handleSelectionChange = (selection: InventoryDifference[]) => {
  selectedDifferences.value = selection
}

const handleConfirm = async (difference: InventoryDifference) => {
  try {
    await inventoryApi.confirmDifference(difference.id)
    ElMessage.success(t('inventory.differenceList.messages.confirmSuccess'))
    await loadDifferences()
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, 'inventory.differenceList.messages.confirmFailed'))
  }
}

const handleAdjust = async (difference: InventoryDifference) => {
  try {
    const result = await ElMessageBox.prompt(
      t('inventory.differenceList.dialogs.adjustMessage'),
      t('inventory.differenceList.dialogs.adjustTitle'),
      {
        inputType: 'textarea',
        inputPlaceholder: t('inventory.differenceList.dialogs.adjustPlaceholder'),
        inputValidator: (value) => {
          return String(value || '').trim()
            ? true
            : t('inventory.differenceList.validation.adjustRemarkRequired')
        },
      }
    )

    if (difference.status === 'pending') {
      await inventoryApi.confirmDifference(difference.id)
    }

    await inventoryApi.adjustAsset(difference.id, {
      resolution: result.value,
      syncAsset: true,
    })

    ElMessage.success(t('inventory.differenceList.messages.adjustSuccess'))
    await loadDifferences()
  } catch (error: unknown) {
    const action = error && typeof error === 'object' && 'action' in error ? String(error.action || '') : ''
    if (error === 'cancel' || action === 'cancel' || action === 'close') {
      return
    }
    ElMessage.error(getErrorMessage(error, 'inventory.differenceList.messages.adjustFailed'))
  }
}

const handleBatchResolve = () => {
  if (selectedDifferences.value.length === 0) {
    ElMessage.warning(t('inventory.differenceList.messages.selectRequired'))
    return
  }
  batchDialogVisible.value = true
}

const handleResolved = async () => {
  batchDialogVisible.value = false
  selectedDifferences.value = []
  await loadDifferences()
}

watch(
  () => currentTaskId.value,
  () => {
    pagination.page = 1
    loadDifferences()
  }
)

onMounted(() => {
  loadDifferences()
})
</script>

<style scoped lang="scss">
.difference-list {
  padding: 20px;
}

.difference-list__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.difference-list__header-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.difference-list__title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.difference-list__header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.difference-list__pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
