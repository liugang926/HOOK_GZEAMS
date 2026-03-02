<template>
  <div class="notification-center">
    <el-card class="center-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2 class="title">
              {{ t('notifications.center.title') }}
            </h2>
            <p class="subtitle">
              {{ t('notifications.center.subtitle') }}
            </p>
          </div>
          <div class="header-actions">
            <el-button @click="goToPreferences">
              {{ t('notifications.actions.preferences') }}
            </el-button>
            <el-button
              type="warning"
              :disabled="summary.unread <= 0"
              :loading="actionLoading"
              @click="handleMarkAllAsRead"
            >
              {{ t('notifications.actions.markAllRead') }}
            </el-button>
            <el-button
              type="primary"
              :loading="store.loading"
              @click="reload"
            >
              {{ t('common.actions.refresh') }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="summary-bar">
        <el-tag
          type="info"
          effect="light"
        >
          {{ t('notifications.summary.total') }}: {{ summary.total }}
        </el-tag>
        <el-tag
          type="warning"
          effect="light"
        >
          {{ t('notifications.summary.unread') }}: {{ summary.unread }}
        </el-tag>
        <el-tag
          type="danger"
          effect="light"
        >
          {{ t('notifications.summary.urgent') }}: {{ summary.urgent }}
        </el-tag>
      </div>

      <div class="filter-bar">
        <el-radio-group
          v-model="filterMode"
          size="small"
          @change="handleFilterChange"
        >
          <el-radio-button label="all">
            {{ t('notifications.filters.all') }}
          </el-radio-button>
          <el-radio-button label="unread">
            {{ t('notifications.filters.unread') }}
          </el-radio-button>
        </el-radio-group>
      </div>

      <el-table
        v-loading="store.loading"
        :data="rows"
        class="notification-table"
        row-key="id"
        @row-click="handleRowClick"
      >
        <el-table-column
          prop="title"
          :label="t('notifications.columns.title')"
          min-width="320"
        >
          <template #default="{ row }">
            <div class="title-cell">
              <div class="title-line">
                <span class="title-text">{{ row.title || t('notifications.fallback.untitled') }}</span>
                <el-tag
                  v-if="!row.readAt"
                  size="small"
                  type="warning"
                  effect="plain"
                >
                  {{ t('notifications.status.unread') }}
                </el-tag>
              </div>
              <div
                v-if="row.content"
                class="content-line"
              >
                {{ row.content }}
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          prop="notificationType"
          :label="t('notifications.columns.type')"
          min-width="160"
        />

        <el-table-column
          prop="priority"
          :label="t('notifications.columns.priority')"
          width="120"
        >
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="resolvePriorityType(row.priority)"
            >
              {{ row.priority || '-' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="createdAt"
          :label="t('notifications.columns.createdAt')"
          width="180"
        >
          <template #default="{ row }">
            <span>{{ formatDisplayDate(row.createdAt) }}</span>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('notifications.columns.status')"
          width="110"
        >
          <template #default="{ row }">
            <el-tag
              size="small"
              :type="row.readAt ? 'success' : 'warning'"
              effect="light"
            >
              {{ row.readAt ? t('notifications.status.read') : t('notifications.status.unread') }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          :label="t('common.table.operations')"
          width="220"
          fixed="right"
        >
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              @click.stop="openNotification(row)"
            >
              {{ t('notifications.actions.open') }}
            </el-button>
            <el-button
              v-if="!row.readAt"
              link
              type="warning"
              @click.stop="handleMarkAsRead(row)"
            >
              {{ t('notifications.actions.markRead') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          :page-sizes="[10, 20, 50, 100]"
          @current-change="loadList"
          @size-change="handlePageSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { notificationApi } from '@/api/notifications'
import {
  useNotificationStore,
  resolveNotificationRoute,
  type NotificationItem
} from '@/stores/notification'
import { formatDate } from '@/utils/dateFormat'

type FilterMode = 'all' | 'unread'

const router = useRouter()
const { t } = useI18n()
const store = useNotificationStore()

const rows = ref<NotificationItem[]>([])
const filterMode = ref<FilterMode>('all')
const actionLoading = ref(false)
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const summary = reactive({
  total: 0,
  unread: 0,
  urgent: 0,
  high: 0
})

const requestParams = computed(() => {
  const params: Record<string, any> = {
    page: pagination.page,
    page_size: pagination.pageSize,
    ordering: '-created_at'
  }
  if (filterMode.value === 'unread') {
    params.read_at__isnull = true
  }
  return params
})

const asRecord = (value: any): Record<string, any> => {
  return value && typeof value === 'object' ? value : {}
}

const unwrapPayload = (payload: any): any => {
  const root = asRecord(payload)
  if ('data' in root && root.data !== undefined) return root.data
  return payload
}

const loadSummary = async () => {
  try {
    const response = await notificationApi.getSummary()
    const data = asRecord(unwrapPayload(response))
    summary.total = Number(data.total) || 0
    summary.unread = Number(data.unread) || 0
    summary.urgent = Number(data.urgent) || 0
    summary.high = Number(data.high) || 0
  } catch (error) {
    const [all, unread] = await Promise.all([
      store.fetchNotificationPage({ page: 1, page_size: 1 }),
      store.fetchNotificationPage({ page: 1, page_size: 1, read_at__isnull: true })
    ])
    summary.total = all.count
    summary.unread = unread.count
    summary.urgent = 0
    summary.high = 0
    console.warn('Summary endpoint unavailable, fallback to list count', error)
  }
}

const loadList = async () => {
  const pageData = await store.fetchNotificationPage(requestParams.value)
  rows.value = pageData.results
  pagination.total = pageData.count
}

const reload = async () => {
  await Promise.all([
    loadSummary(),
    loadList(),
    store.refreshHeaderNotifications()
  ])
}

const handleFilterChange = () => {
  pagination.page = 1
  loadList()
}

const handlePageSizeChange = () => {
  pagination.page = 1
  loadList()
}

const resolvePriorityType = (priority?: string) => {
  const mapping: Record<string, 'danger' | 'warning' | 'primary' | 'info'> = {
    urgent: 'danger',
    high: 'warning',
    normal: 'primary',
    low: 'info'
  }
  return mapping[String(priority || '').toLowerCase()] || 'info'
}

const formatDisplayDate = (value?: string) => {
  if (!value) return '-'
  return formatDate(value)
}

const handleMarkAsRead = async (item: NotificationItem) => {
  if (item.readAt) return
  actionLoading.value = true
  try {
    await store.markAsRead(item.id)
    rows.value = rows.value.map((row) => {
      if (row.id !== item.id) return row
      return { ...row, readAt: row.readAt || new Date().toISOString() }
    })
    if (summary.unread > 0) summary.unread -= 1
  } finally {
    actionLoading.value = false
  }
}

const handleMarkAllAsRead = async () => {
  actionLoading.value = true
  try {
    await store.markAllAsRead()
    rows.value = rows.value.map((item) => ({
      ...item,
      readAt: item.readAt || new Date().toISOString()
    }))
    summary.unread = 0
    ElMessage.success(t('notifications.messages.markAllReadSuccess'))
  } finally {
    actionLoading.value = false
  }
}

const openNotification = async (item: NotificationItem) => {
  if (!item.readAt) {
    await handleMarkAsRead(item)
  }

  const targetRoute = resolveNotificationRoute(item)
  if (targetRoute) {
    router.push(targetRoute)
    return
  }
}

const handleRowClick = (row: NotificationItem) => {
  openNotification(row)
}

const goToPreferences = () => {
  router.push('/notifications/preferences')
}

onMounted(() => {
  reload()
})
</script>

<style scoped lang="scss">
.notification-center {
  min-height: 100%;
}

.center-card {
  border-radius: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.subtitle {
  margin: 6px 0 0;
  color: #909399;
  font-size: 13px;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.summary-bar {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.filter-bar {
  margin-bottom: 12px;
}

.notification-table {
  width: 100%;
}

.title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-line {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-weight: 600;
  color: #303133;
}

.content-line {
  font-size: 12px;
  color: #606266;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

@media (max-width: 900px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
