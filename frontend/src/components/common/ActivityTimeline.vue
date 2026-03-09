<template>
  <div class="activity-timeline-container">
    <div
      v-if="loading"
      class="timeline-loading"
    >
      <el-skeleton
        :rows="5"
        animated
      />
    </div>

    <div v-else-if="activities.length === 0">
      <BaseEmptyState
        :title="$t('common.messages.noTimelineData')"
        :description="$t('common.messages.timelineHint')"
      />
    </div>

    <div
      v-else
      class="history-table-shell"
    >
      <div class="history-table-header">
        <div class="header-copy">
          <h3>{{ $t('common.history.title') }}</h3>
          <p>{{ $t('common.history.description') }}</p>
        </div>
      </div>

      <el-table
        :data="historyRows"
        row-key="rowKey"
        stripe
        border
        class="history-table"
      >
        <el-table-column
          prop="timestamp"
          :label="$t('common.history.columns.changedAt')"
          min-width="168"
        >
          <template #default="{ row }">
            {{ formatDate(row.timestamp || '') }}
          </template>
        </el-table-column>
        <el-table-column
          prop="userName"
          :label="$t('common.history.columns.changedBy')"
          min-width="140"
        >
          <template #default="{ row }">
            {{ row.userName || $t('common.labels.system') }}
          </template>
        </el-table-column>
        <el-table-column
          prop="actionLabel"
          :label="$t('common.history.columns.action')"
          min-width="132"
        >
          <template #default="{ row }">
            <el-tag
              :type="getActivityType(row.action) as any"
              effect="light"
              class="action-badge"
            >
              {{ row.actionLabel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="fieldLabel"
          :label="$t('common.history.columns.field')"
          min-width="160"
        >
          <template #default="{ row }">
            {{ row.fieldLabel || $t('common.history.labels.recordLevel') }}
          </template>
        </el-table-column>
        <el-table-column
          prop="oldValue"
          :label="$t('common.history.columns.oldValue')"
          min-width="180"
        >
          <template #default="{ row }">
            <span class="value-chip old-value">{{ formatHistoryValue(row.oldValue) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="newValue"
          :label="$t('common.history.columns.newValue')"
          min-width="180"
        >
          <template #default="{ row }">
            <span class="value-chip new-value">{{ formatHistoryValue(row.newValue) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="description"
          :label="$t('common.history.columns.description')"
          min-width="220"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div
      v-if="hasMore"
      class="load-more-container"
    >
      <el-button
        :loading="loadingMore"
        type="primary"
        link
        @click="loadMore"
      >
        {{ $t('common.actions.loadMore') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/dateFormat'
import BaseEmptyState from '@/components/common/BaseEmptyState.vue'
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

interface ActivityChange {
  fieldCode: string
  fieldLabel: string
  oldValue: any
  newValue: any
}

export interface ActivityLog {
  id: string
  action: string
  actionLabel?: string
  createdBy?: string
  userName?: string
  createdAt?: string
  timestamp?: string
  description?: string
  changes?: ActivityChange[]
}

interface HistoryRow {
  rowKey: string
  action: string
  actionLabel: string
  userName?: string
  timestamp?: string
  fieldLabel?: string
  oldValue: any
  newValue: any
  description?: string
}

interface Props {
  objectCode: string
  recordId: string
  placement?: 'top' | 'bottom'
  size?: 'normal' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  placement: 'top',
  size: 'normal'
})

const { t } = useI18n()
const loading = ref(false)
const loadingMore = ref(false)
const activities = ref<ActivityLog[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const hasMore = ref(false)

const resolveActionLabel = (action: string, actionLabel?: string) => {
  if (actionLabel && actionLabel.trim()) {
    return actionLabel
  }
  const normalized = String(action || '').toLowerCase()
  const key = `common.history.actions.${normalized}`
  const translated = t(key)
  return translated !== key ? translated : normalized
}

const formatHistoryValue = (value: unknown) => {
  if (value === undefined || value === null || value === '') {
    return '-'
  }
  if (Array.isArray(value)) {
    return value.map(item => formatHistoryValue(item)).join(', ')
  }
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch (_error) {
      return String(value)
    }
  }
  return String(value)
}

const normalizeActivities = (payload: unknown): ActivityLog[] => {
  const rows = Array.isArray(payload) ? payload : []
  return rows.map((item: any) => {
    const actor = item?.actor && typeof item.actor === 'object' ? item.actor : null
    return {
      id: String(item?.id || ''),
      action: String(item?.action || 'update'),
      actionLabel: String(item?.actionLabel || item?.action || ''),
      userName:
        String(
          item?.userName ||
          actor?.fullName ||
          actor?.full_name ||
          actor?.username ||
          ''
        ) || undefined,
      createdBy:
        String(
          item?.createdBy ||
          item?.created_by ||
          actor?.fullName ||
          actor?.full_name ||
          actor?.username ||
          ''
        ) || undefined,
      createdAt: String(item?.createdAt || item?.created_at || item?.timestamp || '') || undefined,
      timestamp: String(item?.timestamp || item?.createdAt || item?.created_at || '') || undefined,
      description: String(item?.description || '') || undefined,
      changes: Array.isArray(item?.changes) ? item.changes : []
    }
  })
}

const historyRows = computed<HistoryRow[]>(() => {
  return activities.value.flatMap((activity, activityIndex) => {
    const baseRow = {
      action: activity.action,
      actionLabel: resolveActionLabel(activity.action, activity.actionLabel),
      userName: activity.userName || activity.createdBy,
      timestamp: activity.createdAt || activity.timestamp,
      description: activity.description
    }

    if (!Array.isArray(activity.changes) || activity.changes.length === 0) {
      return [{
        rowKey: `${activity.id || activityIndex}-summary`,
        ...baseRow,
        fieldLabel: '',
        oldValue: '',
        newValue: ''
      }]
    }

    return activity.changes.map((change, changeIndex) => ({
      rowKey: `${activity.id || activityIndex}-${change.fieldCode || changeIndex}`,
      ...baseRow,
      fieldLabel: change.fieldLabel || change.fieldCode,
      oldValue: change.oldValue,
      newValue: change.newValue
    }))
  })
})

const fetchActivities = async (isLoadMore = false) => {
  if (!props.objectCode || !props.recordId) return

  if (isLoadMore) {
    loadingMore.value = true
  } else {
    loading.value = true
    currentPage.value = 1
  }

  try {
    const res = await request.get<PaginatedResponse<any> | any[]>('/system/activity-logs/', {
      params: {
        object_code: props.objectCode,
        object_id: props.recordId,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })

    const responseRows = Array.isArray(res) ? res : (Array.isArray(res?.results) ? res.results : [])
    const newItems = normalizeActivities(responseRows)

    if (isLoadMore) {
      activities.value = [...activities.value, ...newItems]
    } else {
      activities.value = newItems
    }

    if (!Array.isArray(res) && res?.next) {
      hasMore.value = true
    } else if (Array.isArray(newItems) && newItems.length === pageSize.value) {
      hasMore.value = true
    } else {
      hasMore.value = false
    }
  } catch (error) {
    console.error('Failed to load activities', error)
    activities.value = []
    hasMore.value = false
  } finally {
    if (isLoadMore) {
      loadingMore.value = false
    } else {
      loading.value = false
    }
  }
}

const loadMore = () => {
  if (loadingMore.value || !hasMore.value) return
  currentPage.value++
  fetchActivities(true)
}

onMounted(() => {
  fetchActivities()
})

watch(() => [props.objectCode, props.recordId], () => {
  fetchActivities()
})

const getActivityType = (action: string) => {
  const mapping: Record<string, string> = {
    create: 'success',
    update: 'primary',
    delete: 'danger',
    status_change: 'warning',
    assign: 'warning',
    unassign: 'info',
    approve: 'success',
    reject: 'danger',
    comment: 'info',
    custom: 'info'
  }
  return mapping[String(action || '').toLowerCase()] || 'primary'
}
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.activity-timeline-container {
  padding: $spacing-md 0;

  .timeline-loading {
    padding: $spacing-lg;
  }

  .history-table-shell {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
  }

  .history-table-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: $spacing-md;
    padding: 4px 0;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: $text-main;
    }

    p {
      margin: 4px 0 0;
      font-size: 13px;
      color: $text-regular;
      line-height: 1.5;
    }
  }

  .history-table {
    :deep(.el-table__cell) {
      vertical-align: top;
    }

    :deep(.cell) {
      line-height: 1.6;
    }
  }

  .action-badge {
    font-weight: 500;
    border-radius: 999px;
  }

  .value-chip {
    display: inline-flex;
    max-width: 100%;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 12px;
    word-break: break-word;
    white-space: normal;
  }

  .old-value {
    color: $danger-color;
    background-color: #fef2f2;
    text-decoration: line-through;
  }

  .new-value {
    color: $success-color;
    background-color: #f0fdf4;
    font-weight: 500;
  }

  .load-more-container {
    display: flex;
    justify-content: center;
    padding: $spacing-md 0 0;
    margin-top: $spacing-sm;
    border-top: 1px dashed $border-light;
  }

  @media (max-width: 900px) {
    .history-table-header {
      flex-direction: column;
    }
  }
}
</style>
