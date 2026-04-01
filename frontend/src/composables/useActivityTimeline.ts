import { ref, computed, watch } from 'vue'
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

export interface ActivityChange {
  fieldCode: string
  fieldLabel: string
  oldValue: any
  newValue: any
}

export interface ActivityHighlight {
  code: string
  label?: string
  value: string
  tone?: string
}

export interface ActivityLogEntry {
  id: string
  action: string
  actionLabel?: string
  sourceCode?: string
  sourceLabel?: string
  objectCode?: string
  objectId?: string
  recordLabel?: string
  userName?: string
  createdAt?: string
  timestamp?: string
  description?: string
  changes?: ActivityChange[]
  highlights?: ActivityHighlight[]
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
  fetchUrlGetter: () => string = () => '',
) {
  type ActivityResponseEnvelope = {
    data?: PaginatedResponse<any> | any[]
    results?: any[]
    next?: string | null
  }

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
      sourceCode: String(item?.sourceCode || item?.source_code || '') || undefined,
      sourceLabel: String(item?.sourceLabel || item?.source_label || '') || undefined,
      objectCode: String(item?.objectCode || item?.object_code || '') || undefined,
      objectId: String(item?.objectId || item?.object_id || '') || undefined,
      recordLabel: String(item?.recordLabel || item?.record_label || '') || undefined,
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
      highlights: Array.isArray(item?.highlights)
        ? item.highlights
          .map((highlight: any) => ({
            code: String(highlight?.code || ''),
            label: String(highlight?.label || highlight?.code || '') || undefined,
            value: String(highlight?.value || ''),
            tone: String(highlight?.tone || '') || undefined,
          }))
          .filter((highlight: ActivityHighlight) => highlight.code && highlight.value)
        : [],
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
      const fetchUrl = fetchUrlGetter()
      const res = fetchUrl
        ? await request.get<PaginatedResponse<any> | any[]>(fetchUrl)
        : await request.get<PaginatedResponse<any> | any[]>(`/system/objects/${objectCode}/${recordId}/history/`, {
            params: {
              page: currentPage.value,
              page_size: pageSize.value,
            },
          })

      const response = res as (PaginatedResponse<any> | any[] | ActivityResponseEnvelope)
      const responseEnvelope = !Array.isArray(response) && response && typeof response === 'object'
        ? (response as ActivityResponseEnvelope)
        : null
      const responseData = responseEnvelope?.data
      const paginatedResponseData = !Array.isArray(responseData) && responseData && typeof responseData === 'object'
        ? (responseData as PaginatedResponse<any>)
        : null

      const responseRows = Array.isArray(response)
        ? response
        : Array.isArray(response?.results)
          ? response.results
          : Array.isArray(responseData)
            ? responseData
            : Array.isArray(responseData?.results)
              ? responseData.results
              : []
      const newItems = responseRows.map(normalizeEntry)

      if (isLoadMore) {
        activities.value = [...activities.value, ...newItems]
      } else {
        activities.value = newItems
      }

      const nextPage = responseEnvelope?.next || paginatedResponseData?.next || null

      if (!fetchUrl && nextPage) {
        hasMore.value = true
      } else if (!fetchUrl && newItems.length === pageSize.value) {
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
          dateLabel = 'Today'
        } else if (day.getTime() === yesterday.getTime()) {
          dateKey = 'yesterday'
          dateLabel = 'Yesterday'
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

  watch(
    [objectCodeGetter, recordIdGetter, fetchUrlGetter],
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
