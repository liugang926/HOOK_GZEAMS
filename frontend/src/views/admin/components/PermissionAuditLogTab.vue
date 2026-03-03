<template>
  <div class="permission-audit-log-tab">
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.permission.audit.toolbar.action')">
        <el-select
          v-model="filterForm.action"
          clearable
          :placeholder="$t('system.permission.audit.toolbar.actionPlaceholder')"
          @change="handleSearch"
        >
          <el-option
            :label="$t('system.permission.audit.actions.grant')"
            value="grant"
          />
          <el-option
            :label="$t('system.permission.audit.actions.revoke')"
            value="revoke"
          />
          <el-option
            :label="$t('system.permission.audit.actions.update')"
            value="update"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('system.permission.audit.toolbar.timeRange')">
        <el-date-picker
          v-model="filterForm.dateRange"
          type="daterange"
          range-separator="-"
          :start-placeholder="$t('system.permission.audit.toolbar.startDate')"
          :end-placeholder="$t('system.permission.audit.toolbar.endDate')"
          @change="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSearch"
        >
          {{ $t('common.actions.search') }}
        </el-button>
        <el-button @click="handleReset">
          {{ $t('common.actions.reset') }}
        </el-button>
      </el-form-item>
    </el-form>

    <el-row
      :gutter="20"
      class="stats-row"
    >
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.todayGrants') }}
            </div>
            <div class="stat-value">
              {{ stats.todayGrants }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.todayRevokes') }}
            </div>
            <div class="stat-value">
              {{ stats.todayRevokes }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.weekTotal') }}
            </div>
            <div class="stat-value">
              {{ stats.weekTotal }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.activeUsers') }}
            </div>
            <div class="stat-value">
              {{ stats.activeUsers }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%; margin-top: 20px"
    >
      <el-table-column
        prop="createdAt"
        :label="$t('system.permission.audit.columns.time')"
        width="180"
      />
      <el-table-column
        prop="operatorName"
        :label="$t('system.permission.audit.columns.operator')"
        width="140"
      />
      <el-table-column
        :label="$t('system.permission.audit.columns.action')"
        width="110"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="getActionTag(row.action)"
            size="small"
          >
            {{ getActionLabel(row.action, row.actionLabel) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.permission.audit.columns.type')"
        width="120"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.permissionType === 'field' ? 'primary' : (row.permissionType === 'data' ? 'success' : 'info')"
            size="small"
          >
            {{ row.permissionTypeLabel }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="targetName"
        :label="$t('system.permission.audit.columns.target')"
        width="140"
      />
      <el-table-column
        prop="details"
        :label="$t('system.permission.audit.columns.details')"
        min-width="250"
        show-overflow-tooltip
      />
      <el-table-column
        prop="ipAddress"
        :label="$t('system.permission.audit.columns.ip')"
        width="140"
      />
      <el-table-column
        :label="$t('system.permission.audit.columns.operation')"
        width="100"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleViewDetail(row)"
          >
            {{ $t('common.actions.detail') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-footer">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      :title="$t('system.permission.audit.dialog.title')"
      width="600px"
    >
      <el-descriptions
        :column="2"
        border
      >
        <el-descriptions-item :label="$t('system.permission.audit.dialog.time')">
          {{ currentLog?.createdAt }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.operator')">
          {{ currentLog?.operatorName }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.action')">
          <el-tag :type="getActionTag(currentLog?.action)">
            {{ getActionLabel(currentLog?.action, currentLog?.actionLabel) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.type')">
          <el-tag :type="currentLog?.permissionType === 'field' ? 'primary' : (currentLog?.permissionType === 'data' ? 'success' : 'info')">
            {{ currentLog?.permissionTypeLabel }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('system.permission.audit.dialog.target')"
          :span="2"
        >
          {{ currentLog?.targetName }}
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('system.permission.audit.dialog.details')"
          :span="2"
        >
          {{ currentLog?.details }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.ip')">
          {{ currentLog?.ipAddress }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.userAgent')">
          {{ currentLog?.userAgent }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import {
  permissionAuditLogApi,
  type PermissionAuditLogRecord,
  type PermissionAuditStatistics,
  type PermissionListParams
} from '@/api/permissions'

const { t } = useI18n()

const loading = ref(false)
interface AuditLogViewRow {
  id: string
  createdAt: string
  operatorName: string
  action: 'grant' | 'revoke' | 'update' | 'check' | 'deny'
  actionLabel: string
  permissionType: 'field' | 'data' | 'other'
  permissionTypeLabel: string
  targetName: string
  details: string
  ipAddress: string
  userAgent: string
}

const tableData = ref<AuditLogViewRow[]>([])
const detailVisible = ref(false)
const currentLog = ref<AuditLogViewRow | null>(null)

const filterForm = reactive({
  action: '' as '' | 'grant' | 'revoke' | 'update',
  dateRange: [] as Date[]
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const stats = ref({
  todayGrants: 0,
  todayRevokes: 0,
  weekTotal: 0,
  activeUsers: 0
})

const normalizeAction = (operationType: PermissionAuditLogRecord['operationType']): AuditLogViewRow['action'] => {
  if (operationType === 'modify') {
    return 'update'
  }
  return operationType
}

const mapActionFilter = (action: '' | 'grant' | 'revoke' | 'update') => {
  if (action === 'update') {
    return 'modify'
  }
  return action
}

const getActionLabel = (action: AuditLogViewRow['action'], fallbackLabel?: string) => {
  const labels: Record<string, string> = {
    grant: t('system.permission.audit.actions.grant'),
    revoke: t('system.permission.audit.actions.revoke'),
    update: t('system.permission.audit.actions.update')
  }
  return labels[action] || fallbackLabel || action || '-'
}

const getActionTag = (action: string) => {
  const tags: Record<string, string> = {
    grant: 'success',
    revoke: 'danger',
    update: 'warning',
    check: 'info',
    deny: 'danger'
  }
  return tags[action] || 'info'
}

const resolvePermissionType = (targetType: PermissionAuditLogRecord['targetType']) => {
  if (targetType === 'field_permission') {
    return {
      type: 'field' as const,
      label: t('system.permission.audit.types.field')
    }
  }

  if (targetType === 'data_permission') {
    return {
      type: 'data' as const,
      label: t('system.permission.audit.types.data')
    }
  }

  return {
    type: 'other' as const,
    label: targetType || '-'
  }
}

const formatPermissionDetails = (details: unknown) => {
  if (details === null || details === undefined) {
    return '-'
  }

  if (typeof details === 'string') {
    return details
  }

  try {
    return JSON.stringify(details)
  } catch {
    return String(details)
  }
}

const resolveTargetName = (item: PermissionAuditLogRecord) => {
  if (item.targetUserDisplay) {
    return item.targetUserDisplay
  }

  if (item.objectId) {
    return `${item.targetTypeDisplay || item.targetType}#${item.objectId}`
  }

  return item.targetTypeDisplay || item.targetType || '-'
}

const mapRow = (item: PermissionAuditLogRecord): AuditLogViewRow => {
  const permissionType = resolvePermissionType(item.targetType)
  const action = normalizeAction(item.operationType)

  return {
    id: item.id,
    createdAt: item.createdAt,
    operatorName: item.actorDisplay || '-',
    action,
    actionLabel: item.operationTypeDisplay,
    permissionType: permissionType.type,
    permissionTypeLabel: permissionType.label,
    targetName: resolveTargetName(item),
    details: formatPermissionDetails(item.permissionDetails),
    ipAddress: item.ipAddress || '-',
    userAgent: item.userAgent || '-'
  }
}

const extractOperationCount = (statData: PermissionAuditStatistics | null, operationType: string) => {
  const list = Array.isArray(statData?.byOperation) ? statData.byOperation : []
  const match = list.find((item) => item.operationType === operationType)
  return Number(match?.count || 0)
}

const toDateRangeParams = (): Partial<Pick<PermissionListParams, 'created_at_from' | 'created_at_to'>> => {
  if (!Array.isArray(filterForm.dateRange) || filterForm.dateRange.length !== 2) {
    return {}
  }

  const [start, end] = filterForm.dateRange
  if (!start || !end) {
    return {}
  }

  return {
    created_at_from: dayjs(start).startOf('day').toISOString(),
    created_at_to: dayjs(end).endOf('day').toISOString()
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: PermissionListParams = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...toDateRangeParams()
    }

    if (filterForm.action) {
      params.operation_type = mapActionFilter(filterForm.action)
    }

    const [res, todayStat, weekStat] = await Promise.all([
      permissionAuditLogApi.list(params),
      permissionAuditLogApi.statistics({ days: 1 }).catch(() => null),
      permissionAuditLogApi.statistics({ days: 7 }).catch(() => null)
    ])

    const results = Array.isArray(res?.results) ? res.results : []
    tableData.value = results.map(mapRow)
    pagination.total = Number(res?.count || 0)

    stats.value.todayGrants = extractOperationCount(todayStat, 'grant')
    stats.value.todayRevokes = extractOperationCount(todayStat, 'revoke')
    stats.value.weekTotal = Number(weekStat?.totalCount || 0)

    const actorSet = new Set(
      results
        .map((item) => item.actor)
        .filter((id: string | null | undefined) => !!id)
    )
    stats.value.activeUsers = actorSet.size
  } catch (error) {
    ElMessage.error(t('common.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  filterForm.action = ''
  filterForm.dateRange = []
  handleSearch()
}

const handleViewDetail = (row: AuditLogViewRow) => {
  currentLog.value = row
  detailVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.permission-audit-log-tab {
  padding: 10px 0;
}

.filter-form {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
