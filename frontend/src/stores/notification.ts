import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { notificationApi } from '@/api/notifications'

export interface NotificationItem {
  id: string
  title: string
  content?: string
  notificationType?: string
  priority?: string
  status?: string
  channel?: string
  createdAt?: string
  sentAt?: string
  readAt?: string | null
  data?: Record<string, any>
  relatedObjectId?: string | number | null
}

const DEFAULT_POLL_INTERVAL_MS = 60 * 1000

const asRecord = (value: any): Record<string, any> => {
  return value && typeof value === 'object' ? value : {}
}

const unwrapPayload = (payload: any): any => {
  const root = asRecord(payload)
  if ('data' in root && root.data !== undefined) return root.data
  return payload
}

const normalizeNotificationItem = (raw: any): NotificationItem => {
  const item = asRecord(raw)
  return {
    id: String(item.id || ''),
    title: String(item.title || ''),
    content: String(item.content || ''),
    notificationType: item.notificationType || item.notification_type || '',
    priority: item.priority || '',
    status: item.status || '',
    channel: item.channel || '',
    createdAt: item.createdAt || item.created_at || '',
    sentAt: item.sentAt || item.sent_at || '',
    readAt: item.readAt ?? item.read_at ?? null,
    data: asRecord(item.data),
    relatedObjectId: item.relatedObjectId ?? item.related_object_id ?? null
  }
}

const parsePaginatedList = (payload: any): {
  count: number
  results: NotificationItem[]
} => {
  const data = unwrapPayload(payload)

  if (Array.isArray(data)) {
    const items = data.map(normalizeNotificationItem)
    return {
      count: items.length,
      results: items
    }
  }

  const record = asRecord(data)
  const results = Array.isArray(record.results) ? record.results.map(normalizeNotificationItem) : []
  const count = Number(record.count)
  return {
    count: Number.isFinite(count) ? count : results.length,
    results
  }
}

const parseCountResponse = (payload: any): number => {
  const data = unwrapPayload(payload)
  const record = asRecord(data)
  const count = Number(record.count)
  return Number.isFinite(count) ? count : 0
}

const normalizeWorkflowRoute = (route: string): string => {
  return route.replace(/^\/workflows\//, '/workflow/')
}

export const resolveNotificationRoute = (item: NotificationItem): string | null => {
  const data = asRecord(item.data)
  const variables = asRecord(data.variables)
  const source = {
    ...variables,
    ...data
  }

  const actionUrl = source.actionUrl || source.action_url || source.url
  if (typeof actionUrl === 'string' && actionUrl.trim()) {
    return normalizeWorkflowRoute(actionUrl.trim())
  }

  const taskId = source.taskId || source.task_id || source.workflowTaskId || source.workflow_task_id
  if (taskId) {
    return normalizeWorkflowRoute(`/workflow/task/${taskId}`)
  }

  const objectCode = source.objectCode || source.object_code
  const objectId = source.objectId || source.object_id || source.id || item.relatedObjectId
  if (objectCode && objectId) {
    return `/objects/${encodeURIComponent(String(objectCode))}/${encodeURIComponent(String(objectId))}`
  }

  return null
}

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const recentNotifications = ref<NotificationItem[]>([])
  const loading = ref(false)
  const syncing = ref(false)
  const initialized = ref(false)
  let timer: ReturnType<typeof setInterval> | null = null

  const hasUnread = computed(() => unreadCount.value > 0)

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationApi.getUnreadCount()
      unreadCount.value = parseCountResponse(response)
    } catch (error) {
      const fallback = await notificationApi.list({
        page: 1,
        page_size: 1,
        read_at__isnull: true
      })
      unreadCount.value = parsePaginatedList(fallback).count
      console.warn('Unread count endpoint unavailable, fallback to list count', error)
    }
    return unreadCount.value
  }

  const fetchRecentNotifications = async (limit = 8) => {
    const response = await notificationApi.list({
      page: 1,
      page_size: limit,
      ordering: '-created_at'
    })
    const { results } = parsePaginatedList(response)
    recentNotifications.value = results
    return results
  }

  const refreshHeaderNotifications = async () => {
    if (syncing.value) return
    syncing.value = true
    try {
      await Promise.all([
        fetchUnreadCount(),
        fetchRecentNotifications()
      ])
      initialized.value = true
    } catch (error) {
      console.error('Failed to refresh notifications', error)
      if (!initialized.value) {
        unreadCount.value = 0
        recentNotifications.value = []
      }
    } finally {
      syncing.value = false
    }
  }

  const fetchNotificationPage = async (params: Record<string, any>) => {
    loading.value = true
    try {
      const response = await notificationApi.list(params)
      const parsed = parsePaginatedList(response)
      return parsed
    } finally {
      loading.value = false
    }
  }

  const markAsRead = async (id: string) => {
    if (!id) return
    await notificationApi.markAsRead(id)
    recentNotifications.value = recentNotifications.value.map((item) => {
      if (item.id !== id) return item
      return { ...item, readAt: item.readAt || new Date().toISOString() }
    })
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  const markAllAsRead = async () => {
    try {
      await notificationApi.markAllAsRead()
    } catch (error) {
      const unread = await notificationApi.list({
        page: 1,
        page_size: 200,
        read_at__isnull: true
      })
      const unreadItems = parsePaginatedList(unread).results
      await Promise.all(unreadItems.map((item) => notificationApi.markAsRead(item.id)))
      console.warn('mark_all_read endpoint unavailable, fallback to batch mark_read', error)
    }
    const now = new Date().toISOString()
    recentNotifications.value = recentNotifications.value.map((item) => ({
      ...item,
      readAt: item.readAt || now
    }))
    unreadCount.value = 0
  }

  const startPolling = (intervalMs = DEFAULT_POLL_INTERVAL_MS) => {
    refreshHeaderNotifications()
    if (!timer) {
      timer = setInterval(() => {
        refreshHeaderNotifications()
      }, intervalMs)
    }
  }

  const stopPolling = () => {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  return {
    unreadCount,
    recentNotifications,
    loading,
    syncing,
    initialized,
    hasUnread,
    fetchUnreadCount,
    fetchRecentNotifications,
    refreshHeaderNotifications,
    fetchNotificationPage,
    markAsRead,
    markAllAsRead,
    startPolling,
    stopPolling
  }
})
