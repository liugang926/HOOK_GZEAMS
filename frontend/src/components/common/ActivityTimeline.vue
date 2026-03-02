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
        :title="$t('common.messages.noTimelineData', 'No activity history yet')"
        :description="$t('common.messages.timelineHint', 'Activity logs will appear here once actions are taken on this record.')"
      />
    </div>

    <el-timeline v-else>
      <el-timeline-item
        v-for="(activity, index) in activities"
        :key="activity.id || index"
        :type="getActivityType(activity.action)"
        :color="getActivityColor(activity.action)"
        :size="size"
        hide-timestamp
      >
        <div class="timeline-content">
          <div class="timeline-header">
            <div class="header-main">
              <span class="user-name">{{ activity.userName || activity.createdBy || $t('common.labels.system', 'System') }}</span>
              <el-tag
                :type="getActivityType(activity.action) as any"
                size="small"
                effect="light"
                class="action-badge"
              >
                {{ activity.actionLabel || activity.action }}
              </el-tag>
            </div>
            <span class="timestamp">{{ formatDate(activity.createdAt) }}</span>
          </div>
          <div
            v-if="activity.description"
            class="timeline-body"
          >
            {{ activity.description }}
          </div>
          <div
            v-if="activity.changes && activity.changes.length > 0"
            class="timeline-changes"
          >
            <div
              v-for="(change, idx) in activity.changes"
              :key="idx"
              class="change-item"
            >
              <span class="field-name">{{ change.fieldLabel }}</span>
              <div class="diff-container">
                <span class="old-value">{{ change.oldValue || '�? }}</span>
                <el-icon class="arrow-icon">
                  <ArrowRight />
                </el-icon>
                <span class="new-value">{{ change.newValue || '�? }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>

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
        {{ $t('common.actions.loadMore', '加载更多...') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import { formatDate } from '@/utils/dateFormat'
import BaseEmptyState from '@/components/common/BaseEmptyState.vue'
import request from '@/utils/request'

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
  createdBy: string
  userName?: string
  createdAt: string
  description?: string
  changes?: ActivityChange[]
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

const loading = ref(false)
const loadingMore = ref(false)
const activities = ref<ActivityLog[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const hasMore = ref(false)

const fetchActivities = async (isLoadMore = false) => {
  if (!props.objectCode || !props.recordId) return
  
  if (isLoadMore) {
    loadingMore.value = true
  } else {
    loading.value = true
    currentPage.value = 1
  }

  try {
    const res = await request.get('/system/activity-logs/', {
      params: {
        object_code: props.objectCode,
        object_id: props.recordId,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    
    // Support dual DRF pagination styles (List / Pagination JSON Payload)
    const newItems = res.data?.results || res.data || []
    
    if (isLoadMore) {
      activities.value = [...activities.value, ...newItems]
    } else {
      activities.value = newItems
    }
    
    // Check if there's a `.next` pagination cursor or we've received exactly the page_size threshold
    if (res.data?.next) {
      hasMore.value = true
    } else if (Array.isArray(newItems) && newItems.length === pageSize.value) {
      hasMore.value = true // Possible extra page
    } else {
      hasMore.value = false
    }

  } catch (error) {
    console.error('Failed to load activities', error)
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
    approve: 'success',
    reject: 'danger',
    comment: 'info'
  }
  return mapping[action.toLowerCase()] || 'primary'
}

const getActivityColor = (action: string) => {
  const mapping: Record<string, string> = {
    create: '#10b981', // Emerald 500
    update: '#3b82f6', // Blue 500
    delete: '#ef4444', // Red 500
    approve: '#10b981',
    reject: '#ef4444',
    comment: '#64748b' // Slate 500
  }
  return mapping[action.toLowerCase()] || '#cbd5e1'
}
</script>

<style scoped lang="scss">
@import '@/styles/variables.scss';

.activity-timeline-container {
  padding: $spacing-md 0;

  .timeline-loading {
    padding: $spacing-lg;
  }

  .timeline-content {
    padding-bottom: 2px;

    .timeline-header {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 8px;
      
      .header-main {
        display: flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;

        .user-name {
          font-weight: 600;
          color: $text-main;
          font-size: 13px;
        }

        .action-badge {
          font-weight: 500;
          border-radius: 4px;
        }
      }
      
      .timestamp {
        font-size: 12px;
        color: #94a3b8;
      }
    }

    .timeline-body {
      font-size: 13px;
      color: $text-regular;
      margin-bottom: 8px;
      line-height: 1.5;
    }

    .timeline-changes {
      background-color: #f8fafc;
      border: 1px solid #f1f5f9;
      border-radius: 6px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;

      .change-item {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .field-name {
          font-size: 12px;
          font-weight: 600;
          color: $text-secondary;
        }

        .diff-container {
          display: flex;
          align-items: center;
          flex-wrap: wrap;
          gap: 6px;
          font-family: monospace;
          font-size: 12px;

          .old-value {
            color: $danger-color;
            background-color: #fef2f2;
            padding: 2px 6px;
            border-radius: 4px;
            text-decoration: line-through;
            word-break: break-all;
          }

          .arrow-icon {
            color: #cbd5e1;
            font-size: 12px;
          }

          .new-value {
            color: $success-color;
            background-color: #f0fdf4;
            padding: 2px 6px;
            border-radius: 4px;
            word-break: break-all;
            font-weight: 500;
          }
        }
      }
    }
  }

  .load-more-container {
    display: flex;
    justify-content: center;
    padding: $spacing-md 0 0;
    margin-top: $spacing-sm;
    border-top: 1px dashed $border-light;
  }
}
</style>
