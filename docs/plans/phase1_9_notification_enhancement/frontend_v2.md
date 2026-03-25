# Phase 1.9: Unified Notification System - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement unified notification system with inbox, email, SMS, and WeWork channels. Includes notification center, template management, and user preferences.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/notification.ts

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
  link?: string
  entityId?: string
  entityType?: string
  metadata?: Record<string, any>
}

export interface NotificationListResponse {
  results: Notification[]
  count: number
  unreadCount: number
}

export interface NotificationConfig {
  recipientId: string
  enableInbox: boolean
  enableEmail: boolean
  enableSms: boolean
  enableWework: boolean
  enableDingtalk: boolean
  channelSettings: Record<string, ChannelSettings>
  quietHoursEnabled: boolean
  quietHoursStart: string
  quietHoursEnd: string
  emailAddress?: string
  phoneNumber?: string
}

export interface ChannelSettings {
  inbox: boolean
  email: boolean
  sms: boolean
  wework: boolean
  dingtalk: boolean
}

export interface NotificationTemplate {
  id: string
  code: string
  name: string
  type: NotificationType
  subjectTemplate: string
  contentTemplate: string
  channels: NotificationChannel[]
  variables: TemplateVariable[]
  isActive: boolean
  organizationId: string
  createdAt: string
}

export interface TemplateVariable {
  name: string
  description: string
  defaultValue?: string
}

export interface NotificationStatistics {
  totalSent: number
  totalByType: Record<string, number>
  totalByChannel: Record<string, number>
  successRate: number
  averageDeliveryTime: number
}
```

### API Service

```typescript
// frontend/src/api/notifications.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  Notification,
  NotificationConfig,
  NotificationTemplate,
  NotificationStatistics
} from '@/types/notification'

export const notificationApi = {
  // My Notifications
  getMyNotifications(params?: {
    page?: number
    pageSize?: number
    isRead?: boolean
  }): Promise<PaginatedResponse<Notification>> {
    return request.get('/notifications/my/', { params })
  },

  getNotificationDetail(id: string): Promise<Notification> {
    return request.get(`/notifications/my/${id}/`)
  },

  markAsRead(id: string): Promise<void> {
    return request.post(`/notifications/my/${id}/read/`)
  },

  markAllRead(): Promise<void> {
    return request.post('/notifications/my/read-all/')
  },

  deleteNotification(id: string): Promise<void> {
    return request.delete(`/notifications/my/${id}/`)
  },

  getUnreadCount(): Promise<{ unreadCount: number }> {
    return request.get('/notifications/my/unread-count/')
  },

  // Configuration
  getConfig(): Promise<NotificationConfig> {
    return request.get('/notifications/config/')
  },

  updateConfig(data: Partial<NotificationConfig>): Promise<NotificationConfig> {
    return request.patch('/notifications/config/', data)
  },

  // Admin - Templates
  getTemplates(params?: any): Promise<PaginatedResponse<NotificationTemplate>> {
    return request.get('/notifications/admin/templates/', { params })
  },

  getTemplate(id: string): Promise<NotificationTemplate> {
    return request.get(`/notifications/admin/templates/${id}/`)
  },

  createTemplate(data: Partial<NotificationTemplate>): Promise<NotificationTemplate> {
    return request.post('/notifications/admin/templates/', data)
  },

  updateTemplate(id: string, data: Partial<NotificationTemplate>): Promise<NotificationTemplate> {
    return request.put(`/notifications/admin/templates/${id}/`, data)
  },

  deleteTemplate(id: string): Promise<void> {
    return request.delete(`/notifications/admin/templates/${id}/`)
  },

  previewTemplate(id: string, data: {
    context: Record<string, any>
  }): Promise<{ subject: string; content: string }> {
    return request.post(`/notifications/admin/templates/${id}/preview/`, data)
  },

  // Admin - Notifications
  getAdminNotifications(params?: any): Promise<PaginatedResponse<Notification>> {
    return request.get('/notifications/admin/notifications/', { params })
  },

  resendNotification(id: string): Promise<void> {
    return request.post(`/notifications/admin/notifications/${id}/resend/`)
  },

  // Admin - Statistics
  getStatistics(params?: {
    startDate?: string
    endDate?: string
  }): Promise<NotificationStatistics> {
    return request.get('/notifications/admin/statistics/', { params })
  }
}
```

---

## Component: NotificationBadge

```vue
<!-- frontend/src/components/notifications/NotificationBadge.vue -->
<template>
  <div class="notification-badge">
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
      <el-button :icon="Bell" circle @click="openDrawer" />
    </el-badge>

    <!-- Notification Drawer -->
    <el-drawer
      v-model="visible"
      title="消息中心"
      size="400px"
      @close="handleClose"
    >
      <!-- Tab Navigation -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="all">
          <NotificationList
            :notifications="notifications"
            :loading="loading"
            @read="handleRead"
            @delete="handleDelete"
            @click="handleNotificationClick"
          />
        </el-tab-pane>
        <el-tab-pane label="未读" name="unread">
          <NotificationList
            :notifications="unreadNotifications"
            :loading="loading"
            @read="handleRead"
            @delete="handleDelete"
            @click="handleNotificationClick"
          />
        </el-tab-pane>
      </el-tabs>

      <!-- Footer Actions -->
      <template #footer>
        <div class="drawer-footer">
          <el-button link @click="markAllRead">全部标为已读</el-button>
          <el-button link @click="goToSettings">通知设置</el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { notificationApi } from '@/api/notifications'
import { useWebSocketStore } from '@/stores/websocket'
import type { Notification } from '@/types/notification'
import NotificationList from './NotificationList.vue'

const visible = ref(false)
const activeTab = ref('all')
const loading = ref(false)
const notifications = ref<Notification[]>([])
const unreadCount = ref(0)

const websocketStore = useWebSocketStore()

const unreadNotifications = computed(() => {
  return notifications.value.filter(n => !n.isRead)
})

const fetchNotifications = async () => {
  loading.value = true
  try {
    const response = await notificationApi.getMyNotifications({
      page: 1,
      pageSize: 20
    })
    notifications.value = response.results
    // unreadCount from separate endpoint
  } finally {
    loading.value = false
  }
}

const fetchUnreadCount = async () => {
  const response = await notificationApi.getUnreadCount()
  unreadCount.value = response.unreadCount
}

const openDrawer = () => {
  visible.value = true
  if (notifications.value.length === 0) {
    fetchNotifications()
  }
}

const handleClose = () => {
  visible.value = false
}

const handleTabChange = () => {
  // Reload filtered notifications
}

const handleRead = async (notification: Notification) => {
  await notificationApi.markAsRead(notification.id)
  notification.isRead = true
  unreadCount.value = Math.max(0, unreadCount.value - 1)
}

const handleDelete = async (notification: Notification) => {
  await notificationApi.deleteNotification(notification.id)
  notifications.value = notifications.value.filter(n => n.id !== notification.id)
  if (!notification.isRead) {
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
}

const handleNotificationClick = (notification: Notification) => {
  if (notification.data?.link) {
    window.location.href = notification.data.link
  }
}

const markAllRead = async () => {
  await notificationApi.markAllRead()
  notifications.value.forEach(n => n.isRead = true)
  unreadCount.value = 0
}

const goToSettings = () => {
  window.location.href = '/system/notifications/config'
}

// WebSocket notification handler
const handleNewNotification = (data: Notification) => {
  notifications.value.unshift(data)
  unreadCount.value += 1

  // Show desktop notification if permission granted
  showDesktopNotification(data)
}

const showDesktopNotification = (notification: Notification) => {
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification(notification.title, {
      body: notification.content,
      icon: '/logo.png',
      tag: notification.id
    })
  }
}

onMounted(() => {
  fetchUnreadCount()
  websocketStore.on('notification.created', handleNewNotification)

  // Request desktop notification permission
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission()
  }
})

onUnmounted(() => {
  websocketStore.off('notification.created', handleNewNotification)
})
</script>

<style scoped>
.notification-badge {
  display: inline-block;
}

.drawer-footer {
  display: flex;
  justify-content: space-between;
  padding: 16px;
  border-top: 1px solid #eee;
}
</style>
```

---

## Component: NotificationItem

```vue
<!-- frontend/src/components/notifications/NotificationItem.vue -->
<template>
  <div
    :class="['notification-item', {
      'is-unread': !notification.isRead,
      [`priority-${notification.priority}`]: true
    }]"
    @click="handleClick"
  >
    <div class="item-icon">
      <el-icon :size="20" :color="iconColor">
        <component :is="iconComponent" />
      </el-icon>
    </div>

    <div class="item-content">
      <div class="item-header">
        <span class="item-title">{{ notification.title }}</span>
        <span class="item-time">{{ formatTime(notification.createdAt) }}</span>
      </div>
      <div class="item-body">{{ notification.content }}</div>
      <div v-if="notification.data?.link" class="item-footer">
        <el-button link type="primary" size="small">查看详情</el-button>
      </div>
    </div>

    <div class="item-actions">
      <el-dropdown trigger="click" @command="handleCommand">
        <el-icon :size="16"><MoreFilled /></el-icon>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-if="!notification.isRead" command="read">
              标为已读
            </el-dropdown-item>
            <el-dropdown-item v-else command="unread">
              标为未读
            </el-dropdown-item>
            <el-dropdown-item command="delete" divided>
              删除
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { MoreFilled, Bell, Warning, InfoFilled, CircleCheck } from '@element-plus/icons-vue'
import type { Notification, NotificationPriority, NotificationType } from '@/types/notification'

interface Props {
  notification: Notification
}

const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'read', notification: Notification): void
  (e: 'unread', notification: Notification): void
  (e: 'delete', notification: Notification): void
  (e: 'click', notification: Notification): void
}>()

const iconComponent = computed(() => {
  const iconMap: Record<NotificationType, any> = {
    workflow_approval: Bell,
    workflow_approved: CircleCheck,
    workflow_rejected: Warning,
    inventory_assigned: Bell,
    asset_warning: Warning,
    system_announcement: InfoFilled
  }
  return iconMap[props.notification.type] || Bell
})

const iconColor = computed(() => {
  if (!props.notification.isRead) return '#409eff'
  if (props.notification.priority === 'urgent') return '#f56c6c'
  if (props.notification.priority === 'high') return '#e6a23c'
  return '#909399'
})

const formatTime = (time: string) => {
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}

const handleClick = () => {
  emit('click', props.notification)
  if (props.notification.data?.link) {
    window.location.href = props.notification.data.link
  }
}

const handleCommand = (command: string) => {
  switch (command) {
    case 'read':
      emit('read', props.notification)
      break
    case 'unread':
      emit('unread', props.notification)
      break
    case 'delete':
      emit('delete', props.notification)
      break
  }
}
</script>

<style scoped>
.notification-item {
  display: flex;
  padding: 12px;
  gap: 12px;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background-color: #f5f7fa;
}

.notification-item.is-unread {
  background-color: #ecf5ff;
}

.notification-item.priority-urgent {
  border-left: 3px solid #f56c6c;
}

.notification-item.priority-high {
  border-left: 3px solid #e6a23c;
}

.item-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 50%;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.item-title {
  font-weight: 500;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  margin-left: 8px;
}

.item-body {
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.item-actions {
  flex-shrink: 0;
}
</style>
```

---

## Component: NotificationConfig

```vue
<!-- frontend/src/views/system/notifications/Config.vue -->
<template>
  <div class="notification-config-page">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="text-large font-600">通知设置</span>
      </template>
      <template #extra>
        <el-button type="primary" @click="handleSave">保存设置</el-button>
      </template>
    </el-page-header>

    <el-card class="config-card">
      <el-form :model="form" label-width="120px">
        <!-- Global Channel Toggles -->
        <div class="config-section">
          <h3>通知渠道</h3>
          <el-form-item label="站内信">
            <el-switch v-model="form.enableInbox" />
            <span class="form-tip">系统内消息通知</span>
          </el-form-item>
          <el-form-item label="邮件通知">
            <el-switch v-model="form.enableEmail" />
            <span class="form-tip">发送到邮箱</span>
          </el-form-item>
          <el-form-item label="短信通知">
            <el-switch v-model="form.enableSms" />
            <span class="form-tip">发送到手机</span>
          </el-form-item>
          <el-form-item label="企业微信">
            <el-switch v-model="form.enableWework" />
            <span class="form-tip">推送到企业微信</span>
          </el-form-item>
        </div>

        <!-- Type-Specific Settings -->
        <div class="config-section">
          <h3>分类通知设置</h3>
          <el-table :data="typeSettings" border>
            <el-table-column prop="label" label="通知类型" width="150" />
            <el-table-column label="站内信" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.inbox" />
              </template>
            </el-table-column>
            <el-table-column label="邮件" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.email" />
              </template>
            </el-table-column>
            <el-table-column label="短信" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.sms" />
              </template>
            </el-table-column>
            <el-table-column label="企业微信" width="100">
              <template #default="{ row }">
                <el-switch v-model="row.wework" />
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- Quiet Hours -->
        <div class="config-section">
          <h3>免打扰设置</h3>
          <el-form-item label="启用免打扰">
            <el-switch v-model="form.quietHoursEnabled" />
          </el-form-item>
          <template v-if="form.quietHoursEnabled">
            <el-form-item label="免打扰时段">
              <el-time-picker
                v-model="quietHoursRange"
                is-range
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
              />
            </el-form-item>
          </template>
        </div>

        <!-- Contact Information -->
        <div class="config-section">
          <h3>联系方式</h3>
          <el-form-item label="接收邮箱">
            <el-input
              v-model="form.emailAddress"
              placeholder="留空则使用默认邮箱"
            />
          </el-form-item>
          <el-form-item label="接收手机号">
            <el-input
              v-model="form.phoneNumber"
              placeholder="留空则使用默认手机号"
            />
          </el-form-item>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { notificationApi } from '@/api/notifications'
import type { NotificationConfig } from '@/types/notification'

const router = useRouter()

const form = reactive<NotificationConfig>({
  recipientId: '',
  enableInbox: true,
  enableEmail: true,
  enableSms: false,
  enableWework: true,
  enableDingtalk: false,
  channelSettings: {},
  quietHoursEnabled: false,
  quietHoursStart: '22:00:00',
  quietHoursEnd: '08:00:00',
  emailAddress: '',
  phoneNumber: ''
})

const quietHoursRange = ref<[Date, Date]>([new Date(), new Date()])

const typeSettings = ref([
  {
    type: 'workflow_approval',
    label: '审批通知',
    inbox: true,
    email: false,
    sms: false,
    wework: true
  },
  {
    type: 'workflow_approved',
    label: '审批完成',
    inbox: true,
    email: true,
    sms: false,
    wework: false
  },
  {
    type: 'inventory_assigned',
    label: '盘点任务',
    inbox: true,
    email: false,
    sms: true,
    wework: true
  },
  {
    type: 'asset_warning',
    label: '资产预警',
    inbox: true,
    email: true,
    sms: false,
    wework: false
  },
  {
    type: 'system_announcement',
    label: '系统公告',
    inbox: true,
    email: false,
    sms: false,
    wework: false
  }
])

const loadConfig = async () => {
  try {
    const config = await notificationApi.getConfig()
    Object.assign(form, config)

    // Update type settings from channel settings
    typeSettings.value.forEach(item => {
      const settings = config.channelSettings?.[item.type]
      if (settings) {
        Object.assign(item, settings)
      }
    })
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleSave = async () => {
  try {
    // Build save data
    const saveData = { ...form }

    // Build channel settings from type settings
    saveData.channelSettings = {}
    typeSettings.value.forEach(item => {
      saveData.channelSettings[item.type] = {
        inbox: item.inbox,
        email: item.email,
        sms: item.sms,
        wework: item.wework
      }
    })

    await notificationApi.updateConfig(saveData)
    ElMessage.success('保存成功')
  } catch (error) {
    // Error handled by interceptor
  }
}

const goBack = () => {
  router.back()
}

onMounted(loadConfig)
</script>

<style scoped>
.notification-config-page {
  padding: 20px;
}

.config-card {
  margin-top: 20px;
}

.config-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #eee;
}

.config-section:last-child {
  border-bottom: none;
}

.config-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
}

.form-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/notification.ts` | Notification type definitions |
| `frontend/src/api/notifications.ts` | Notification API service |
| `frontend/src/components/notifications/NotificationBadge.vue` | Notification badge with bell icon |
| `frontend/src/components/notifications/NotificationCenter.vue` | Notification center drawer |
| `frontend/src/components/notifications/NotificationItem.vue` | Single notification item component |
| `frontend/src/components/notifications/NotificationList.vue` | Notification list component |
| `frontend/src/components/notifications/TemplateEditor.vue` | Template editor component |
| `frontend/src/views/system/notifications/Config.vue` | Notification config page |
| `frontend/src/views/system/notifications/Templates.vue` | Template management page |
| `frontend/src/views/system/notifications/Statistics.vue` | Notification statistics page |
