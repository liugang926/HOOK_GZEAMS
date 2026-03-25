# Phase 2.3: Notification Center - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement notification center with inbox management, real-time notifications, and user preferences configuration.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/notifications.ts

export interface Notification {
  id: string
  recipientId: string
  type: NotificationType
  priority: NotificationPriority
  title: string
  content: string
  isRead: boolean
  data?: NotificationData
  channels: NotificationChannel[]
  organizationId: string
  createdAt: string
  readAt?: string
}

export enum NotificationType {
  WORKFLOW_APPROVAL = 'workflow_approval',
  WORKFLOW_APPROVED = 'workflow_approved',
  WORKFLOW_REJECTED = 'workflow_rejected',
  INVENTORY_ASSIGNED = 'inventory_assigned',
  ASSET_WARNING = 'asset_warning',
  SYSTEM_ANNOUNCEMENT = 'system_announcement'
}

export enum NotificationPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum NotificationChannel {
  INBOX = 'inbox',
  EMAIL = 'email',
  SMS = 'sms',
  WEWORK = 'wework',
  DINGTALK = 'dingtalk'
}

export interface NotificationData {
  businessType?: string
  businessId?: string
  url?: string
  metadata?: Record<string, any>
}

export interface NotificationChannel {
  id: string
  channelType: NotificationChannelType
  displayName: string
  isEnabled: boolean
  priority: number
  config?: Record<string, any>
}

export enum NotificationChannelType {
  INBOX = 'inbox',
  EMAIL = 'email',
  SMS = 'sms',
  WEWORK = 'wework',
  DINGTALK = 'dingtalk',
  FEISHU = 'feishu'
}

export interface NotificationTemplate {
  id: string
  code: string
  name: string
  title: string
  content: string
  businessCategory: string
  channels: NotificationChannelType[]
  variables?: TemplateVariable[]
}

export interface TemplateVariable {
  name: string
  description: string
  defaultValue?: string
}

export interface NotificationStats {
  totalCount: number
  unreadCount: number
  approvalCount: number
  systemCount: number
}
```

### API Service

```typescript
// frontend/src/api/notifications.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  Notification,
  NotificationChannel,
  NotificationTemplate,
  NotificationStats
} from '@/types/notifications'

export const notificationApi = {
  // Notifications
  list(params?: {
    unread_only?: boolean
    type?: string
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<Notification>> {
    return request.get('/notifications/my-messages/', { params })
  },

  get(id: string): Promise<Notification> {
    return request.get(`/notifications/my-messages/${id}/`)
  },

  markAsRead(id: string): Promise<void> {
    return request.post(`/notifications/my-messages/${id}/mark-read/`)
  },

  markAllAsRead(): Promise<void> {
    return request.post('/notifications/my-messages/mark-all-read/')
  },

  getUnreadCount(): Promise<{ count: number }> {
    return request.get('/notifications/my-messages/unread-count/')
  },

  getStats(): Promise<NotificationStats> {
    return request.get('/notifications/my-messages/stats/')
  },

  // Channels
  getChannels(): Promise<NotificationChannel[]> {
    return request.get('/notifications/channels/')
  },

  updateChannel(id: string, data: {
    isEnabled?: boolean
    priority?: number
    config?: Record<string, any>
  }): Promise<NotificationChannel> {
    return request.patch(`/notifications/channels/${id}/`, data)
  },

  // Templates
  getTemplates(params?: { category?: string }): Promise<NotificationTemplate[]> {
    return request.get('/notifications/templates/', { params })
  },

  updateTemplate(id: string, data: Partial<NotificationTemplate>): Promise<NotificationTemplate> {
    return request.patch(`/notifications/templates/${id}/`, data)
  },

  // Send Test
  sendTestNotification(data: {
    recipients: Array<{ userId: string }>
    channels?: NotificationChannelType[]
    title: string
    content: string
  }): Promise<void> {
    return request.post('/notifications/send/', data)
  }
}
```

---

## Component: NotificationCenter

```vue
<!-- frontend/src/components/NotificationCenter.vue -->
<template>
  <div class="notification-center">
    <!-- Notification Icon Button -->
    <el-badge
      :value="unreadCount"
      :hidden="unreadCount === 0"
      :max="99"
    >
      <el-button
        :icon="Bell"
        @click="handleOpen"
        circle
        class="notification-button"
      />
    </el-badge>

    <!-- Notification Drawer -->
    <NotificationDrawer
      v-model:visible="drawerVisible"
      @read="handleMessageRead"
      @read-all="handleReadAll"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { useNotificationStore } from '@/stores/notification'
import { useWebSocketStore } from '@/stores/websocket'
import NotificationDrawer from './NotificationDrawer.vue'

const notificationStore = useNotificationStore()
const websocketStore = useWebSocketStore()
const drawerVisible = ref(false)

// Unread count
const unreadCount = computed(() => notificationStore.unreadCount)

// Open notification drawer
const handleOpen = () => {
  drawerVisible.value = true
  // Refresh messages when opening
  notificationStore.fetchMessages()
}

// Message read
const handleMessageRead = (messageId: string) => {
  notificationStore.markAsRead(messageId)
}

// Mark all as read
const handleReadAll = async () => {
  await notificationStore.markAllAsRead()
}

let refreshTimer: number | null = null

onMounted(() => {
  // Initialize messages
  notificationStore.fetchMessages()

  // Refresh every 30 seconds
  refreshTimer = window.setInterval(() => {
    notificationStore.fetchMessages()
  }, 30000)

  // Setup WebSocket listener
  websocketStore.on('notification.created', handleNewNotification)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
  websocketStore.off('notification.created', handleNewNotification)
})

const handleNewNotification = (data: Notification) => {
  notificationStore.addMessage(data)
  // Show desktop notification
  showDesktopNotification(data)
}

const showDesktopNotification = (message: Notification) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(message.title, {
      body: message.content,
      icon: '/logo.png',
      tag: message.id
    })
  }
}
</script>

<style scoped>
.notification-center {
  display: inline-block;
}

.notification-button {
  font-size: 18px;
}

:deep(.el-badge__content) {
  background-color: #f56c6c;
}
</style>
```

---

## Component: NotificationDrawer

```vue
<!-- frontend/src/components/NotificationDrawer.vue -->
<template>
  <el-drawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="消息中心"
    size="450px"
    class="notification-drawer"
  >
    <template #header>
      <div class="drawer-header">
        <span>消息中心</span>
        <el-button
          v-if="unreadCount > 0"
          link
          type="primary"
          @click="handleReadAll"
        >
          全部已读
        </el-button>
      </div>
    </template>

    <!-- Message Category Tabs -->
    <el-tabs v-model="activeTab" class="notification-tabs">
      <el-tab-pane name="all">
        <template #label>
          <span class="tab-label">
            全部
            <el-badge
              v-if="totalCount > 0"
              :value="totalCount"
              :max="99"
              type="primary"
            />
          </span>
        </template>
        <NotificationList
          :messages="allMessages"
          :loading="loading"
          @read="$emit('read', $event)"
        />
      </el-tab-pane>

      <el-tab-pane name="unread">
        <template #label>
          <span class="tab-label">
            未读
            <el-badge
              v-if="unreadCount > 0"
              :value="unreadCount"
              :max="99"
              type="danger"
            />
          </span>
        </template>
        <NotificationList
          :messages="unreadMessages"
          :loading="loading"
          @read="$emit('read', $event)"
        />
      </el-tab-pane>

      <el-tab-pane name="approval">
        <template #label>
          <span class="tab-label">
            审批
            <el-badge
              v-if="approvalUnreadCount > 0"
              :value="approvalUnreadCount"
              :max="99"
              type="warning"
            />
          </span>
        </template>
        <NotificationList
          :messages="approvalMessages"
          :loading="loading"
          @read="$emit('read', $event)"
        />
      </el-tab-pane>

      <el-tab-pane name="system">
        <template #label>
          <span class="tab-label">系统</span>
        </template>
        <NotificationList
          :messages="systemMessages"
          :loading="loading"
          @read="$emit('read', $event)"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- Empty State -->
    <el-empty
      v-if="currentMessages.length === 0 && !loading"
      description="暂无消息"
      :image-size="100"
    />
  </el-drawer>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import NotificationList from './NotificationList.vue'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'read', messageId: string): void
  (e: 'read-all'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const activeTab = ref('unread')
const loading = ref(false)

// Use Pinia store for messages
import { useNotificationStore } from '@/stores/notification'
const notificationStore = useNotificationStore()

const allMessages = computed(() => notificationStore.messages)
const unreadMessages = computed(() => notificationStore.unreadMessages)
const approvalMessages = computed(() => notificationStore.approvalMessages)
const systemMessages = computed(() => notificationStore.systemMessages)

// Statistics
const totalCount = computed(() => allMessages.value.length)
const unreadCount = computed(() => unreadMessages.value.length)
const approvalUnreadCount = computed(() =>
  approvalMessages.value.filter(m => !m.isRead).length
)

// Current tab messages
const currentMessages = computed(() => {
  switch (activeTab.value) {
    case 'all':
      return allMessages.value
    case 'unread':
      return unreadMessages.value
    case 'approval':
      return approvalMessages.value
    case 'system':
      return systemMessages.value
    default:
      return []
  }
})

const handleReadAll = () => {
  emit('read-all')
}
</script>

<style scoped>
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.notification-tabs :deep(.el-tabs__header) {
  margin-bottom: 10px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

:deep(.el-badge__content) {
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 4px;
}
</style>
```

---

## Component: NotificationList

```vue
<!-- frontend/src/components/NotificationList.vue -->
<template>
  <div class="notification-list" v-loading="loading">
    <div
      v-for="message in messages"
      :key="message.id"
      class="notification-item"
      :class="{ unread: !message.isRead }"
      @click="handleClick(message)"
    >
      <!-- Icon -->
      <div class="notification-icon">
        <el-icon :size="20" :color="getTypeColor(message.type)">
          <component :is="getTypeIcon(message.type)" />
        </el-icon>
      </div>

      <!-- Content -->
      <div class="notification-content">
        <div class="notification-title">
          <span class="title-text">{{ message.title }}</span>
          <el-tag
            v-if="!message.isRead"
            size="small"
            type="danger"
            effect="plain"
          >
            未读
          </el-tag>
        </div>
        <div class="notification-desc">{{ message.content }}</div>
        <div class="notification-time">{{ formatTime(message.createdAt) }}</div>
      </div>

      <!-- Actions -->
      <div class="notification-actions">
        <el-button
          v-if="!message.isRead"
          link
          type="primary"
          size="small"
          @click.stop="handleMarkRead(message)"
        >
          标为已读
        </el-button>
      </div>
    </div>

    <!-- Load More -->
    <div v-if="hasMore" class="load-more">
      <el-button link @click="$emit('load-more')">加载更多</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Bell,
  Document,
  Box,
  Warning,
  InfoFilled,
  CircleCheck
} from '@element-plus/icons-vue'
import { useNotificationStore } from '@/stores/notification'
import { ElMessage } from 'element-plus'
import type { Notification } from '@/types/notifications'

interface Props {
  messages: Notification[]
  loading?: boolean
}

interface Emits {
  (e: 'read', messageId: string): void
  (e: 'load-more'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()
const notificationStore = useNotificationStore()

const hasMore = computed(() => props.messages.length >= 20)

const getTypeIcon = (type: string) => {
  const icons = {
    system: InfoFilled,
    approval: Document,
    asset: Box,
    inventory: Warning,
    reminder: Bell
  }
  return icons[type] || InfoFilled
}

const getTypeColor = (type: string) => {
  const colors = {
    system: '#909399',
    approval: '#409EFF',
    asset: '#67C23A',
    inventory: '#E6A23C',
    reminder: '#F56C6C'
  }
  return colors[type] || '#909399'
}

const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`

  return date.toLocaleDateString('zh-CN')
}

const handleClick = (message: Notification) => {
  // Mark as read
  if (!message.isRead) {
    handleMarkRead(message)
  }

  // Navigate to related page
  if (message.data?.url) {
    router.push(message.data.url)
  }
}

const handleMarkRead = async (message: Notification) => {
  await notificationStore.markAsRead(message.id)
  emit('read', message.id)
  ElMessage.success('已标记为已读')
}
</script>

<style scoped>
.notification-list {
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background-color: #f5f7fa;
}

.notification-item.unread {
  background-color: #ecf5ff;
}

.notification-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
  border-radius: 50%;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.title-text {
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-desc {
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 4px;
}

.notification-time {
  font-size: 12px;
  color: #909399;
}

.notification-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.load-more {
  text-align: center;
  padding: 12px 0;
}
</style>
```

---

## Store: Notification

```typescript
// frontend/src/stores/notification.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notificationApi } from '@/api/notifications'
import type { Notification } from '@/types/notifications'

export const useNotificationStore = defineStore('notification', () => {
  const messages = ref<Notification[]>([])
  const stats = ref({
    totalCount: 0,
    unreadCount: 0,
    approvalCount: 0,
    systemCount: 0
  })
  const loading = ref(false)

  // All messages
  const allMessages = computed(() => messages.value)

  // Unread messages
  const unreadMessages = computed(() =>
    messages.value.filter(m => !m.isRead)
  )

  // Approval messages
  const approvalMessages = computed(() =>
    messages.value.filter(m => m.type.startsWith('workflow_'))
  )

  // System messages
  const systemMessages = computed(() =>
    messages.value.filter(m => m.type === 'system_announcement')
  )

  // Unread count
  const unreadCount = computed(() => stats.value.unreadCount)

  // Fetch messages
  const fetchMessages = async () => {
    loading.value = true
    try {
      const response = await notificationApi.list()
      messages.value = response.results || []

      // Fetch stats
      const statsData = await notificationApi.getStats()
      stats.value = statsData
    } catch (error) {
      console.error('Failed to fetch messages', error)
    } finally {
      loading.value = false
    }
  }

  // Mark as read
  const markAsRead = async (messageId: string) => {
    try {
      await notificationApi.markAsRead(messageId)

      // Update local state
      const message = messages.value.find(m => m.id === messageId)
      if (message) {
        message.isRead = true
        message.readAt = new Date().toISOString()
      }

      // Update stats
      if (stats.value.unreadCount > 0) {
        stats.value.unreadCount--
      }
    } catch (error) {
      console.error('Failed to mark as read', error)
      throw error
    }
  }

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await notificationApi.markAllAsRead()

      // Update local state
      messages.value.forEach(m => {
        if (!m.isRead) {
          m.isRead = true
          m.readAt = new Date().toISOString()
        }
      })

      stats.value.unreadCount = 0
    } catch (error) {
      console.error('Failed to mark all as read', error)
      throw error
    }
  }

  // Add new message (for WebSocket)
  const addMessage = (message: Notification) => {
    messages.value.unshift(message)
    if (!message.isRead) {
      stats.value.unreadCount++
      stats.value.totalCount++
    }
  }

  return {
    messages,
    stats,
    loading,
    allMessages,
    unreadMessages,
    approvalMessages,
    systemMessages,
    unreadCount,
    fetchMessages,
    markAsRead,
    markAllAsRead,
    addMessage
  }
})
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/notifications.ts` | Notification type definitions |
| `frontend/src/api/notifications.ts` | Notification API service |
| `frontend/src/stores/notification.ts` | Notification Pinia store |
| `frontend/src/components/NotificationCenter.vue` | Notification center entry component |
| `frontend/src/components/NotificationDrawer.vue` | Notification drawer |
| `frontend/src/components/NotificationList.vue` | Notification list |
| `frontend/src/views/admin/NotificationSettings.vue` | Notification settings page |
