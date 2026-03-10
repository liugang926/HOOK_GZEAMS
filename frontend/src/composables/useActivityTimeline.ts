import { ref, computed, watch } from 'vue'
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

export interface ActivityChange {
  fieldCode: string
  fieldLabel: string
  oldValue: any
  newValue: any
}

export interface ActivityLogEntry {
  id: string
  action: string
  actionLabel?: string
  userName?: string
  createdAt?: string
  timestamp?: string
  description?: string
  changes?: ActivityChange[]
}

export interface DateGroup {
  dateLabel: string
  dateKey: string
  entries: ActivityLogEntry[]
}

/**
 * Composable for fetching and managing activity timeline data.
 * Extracts data logic from ActivityTimeline.vue for reuse.
 */
export function useActivityTimeline(
  objectCodeGetter: () => string,
  recordIdGetter: () => string,
) {
  const activities = ref<ActivityLogEntry[]>([])
  const loading = ref(false)
  const loadingMore = ref(false)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const hasMore = ref(false)

  const normalizeEntry = (item: any): ActivityLogEntry => {
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
      createdAt: String(item?.createdAt || item?.created_at || item?.timestamp || '') || undefined,
      timestamp: String(item?.timestamp || item?.createdAt || item?.created_at || '') || undefined,
      description: String(item?.description || '') || undefined,
      changes: Array.isArray(item?.changes) ? item.changes : [],
    }
  }

  const fetchActivities = async (isLoadMore = false) => {
    const objectCode = objectCodeGetter()
    const recordId = recordIdGetter()
    if (!objectCode || !recordId) return

    if (isLoadMore) {
      loadingMore.value = true
    } else {
      loading.value = true
      currentPage.value = 1
    }

    try {
      const res = await request.get<PaginatedResponse<any> | any[]>('/system/activity-logs/', {
        params: {
          object_code: objectCode,
          object_id: recordId,
          page: currentPage.value,
          page_size: pageSize.value,
        },
      })

      const responseRows = Array.isArray(res) ? res : (Array.isArray(res?.results) ? res.results : [])
      const newItems = responseRows.map(normalizeEntry)

      if (isLoadMore) {
        activities.value = [...activities.value, ...newItems]
      } else {
        activities.value = newItems
      }

      if (!Array.isArray(res) && res?.next) {
        hasMore.value = true
      } else if (newItems.length === pageSize.value) {
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

  const refresh = () => fetchActivities(false)

  // ── Date grouping ──────────────────────────────────────────
  const groupedByDate = computed<DateGroup[]>(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    const groups = new Map<string, { label: string; entries: ActivityLogEntry[] }>()

    for (const entry of activities.value) {
      const raw = entry.createdAt || entry.timestamp || ''
      const d = raw ? new Date(raw) : null
      let dateKey: string
      let dateLabel: string

      if (!d || isNaN(d.getTime())) {
        dateKey = 'unknown'
        dateLabel = '-'
      } else {
        const day = new Date(d)
        day.setHours(0, 0, 0, 0)

        if (day.getTime() === today.getTime()) {
          dateKey = 'today'
          dateLabel = '今天'
        } else if (day.getTime() === yesterday.getTime()) {
          dateKey = 'yesterday'
          dateLabel = '昨天'
        } else {
          dateKey = day.toISOString().slice(0, 10)
          dateLabel = dateKey
        }
      }

      if (!groups.has(dateKey)) {
        groups.set(dateKey, { label: dateLabel, entries: [] })
      }
      groups.get(dateKey)!.entries.push(entry)
    }

    return Array.from(groups.entries()).map(([key, val]) => ({
      dateKey: key,
      dateLabel: val.label,
      entries: val.entries,
    }))
  })

  // Auto-fetch on param change
  watch(
    [objectCodeGetter, recordIdGetter],
    () => fetchActivities(),
    { immediate: true },
  )

  return {
    activities,
    loading,
    loadingMore,
    hasMore,
    groupedByDate,
    loadMore,
    refresh,
  }
}
