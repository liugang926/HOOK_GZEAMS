# Phase 2.3: 通知中心模块 - 前端实现

## 前端公共组件引用

| 组件名 | 组件路径 | 用途 |
|--------|---------|------|
| BaseListPage | @/components/common/BaseListPage.vue | 列表页面 |
| BaseFormPage | @/components/common/BaseFormPage.vue | 表单页面 |
| BaseDetailPage | @/components/common/BaseDetailPage.vue | 详情页面 |

---

## 组件结构

```
src/components/
├── NotificationCenter.vue       # 通知中心入口组件
├── NotificationDrawer.vue      # 通知抽屉
├── NotificationList.vue        # 通知列表
└── NotificationBadge.vue       # 通知角标

src/views/admin/
└── NotificationSettings.vue    # 通知配置管理页面

src/stores/
└── notification.ts             # 通知状态管理
```

---

---

## 公共组件引用

### 页面组件
本模块使用以下公共页面组件（详见 `common_base_features/frontend.md`）：

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseListPage` | 标准列表页面 | `@/components/common/BaseListPage.vue` |
| `BaseFormPage` | 标准表单页面 | `@/components/common/BaseFormPage.vue` |
| `BaseDetailPage` | 标准详情页面 | `@/components/common/BaseDetailPage.vue` |

### 基础组件

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseTable` | 统一表格 | `@/components/common/BaseTable.vue` |
| `BaseSearchBar` | 搜索栏 | `@/components/common/BaseSearchBar.vue` |
| `BasePagination` | 分页 | `@/components/common/BasePagination.vue` |
| `BaseAuditInfo` | 审计信息 | `@/components/common/BaseAuditInfo.vue` |
| `BaseFileUpload` | 文件上传 | `@/components/common/BaseFileUpload.vue` |

### 列表字段显示管理（推荐）

| 组件 | Hook | 参考文档 |
|------|------|---------|
| `ColumnManager` | 列显示/隐藏/排序/列宽配置 | `list_column_configuration.md` |
| `useColumnConfig` | 列配置Hook（获取/保存/重置） | `list_column_configuration.md` |

**功能包括**:
- ✓ 列的显示/隐藏
- ✓ 列的拖拽排序
- ✓ 列宽调整
- ✓ 列固定（左/右）
- ✓ 用户个性化配置保存

### 布局组件

| 组件 | 用途 | 参考文档 |
|------|------|---------|
| `DynamicTabs` | 动态标签页 | `tab_configuration.md` |
| `SectionBlock` | 区块容器 | `section_block_layout.md` |
| `FieldRenderer` | 动态字段渲染 | `field_configuration_layout.md` |

### Composables/Hooks

| Hook | 用途 | 引用路径 |
|------|------|---------|
| `useListPage` | 列表页面逻辑 | `@/composables/useListPage.js` |
| `useFormPage` | 表单页面逻辑 | `@/composables/useFormPage.js` |
| `usePermission` | 权限检查 | `@/composables/usePermission.js` |

### 组件继承关系

```vue
<!-- 列表页面 -->
<BaseListPage
    title="页面标题"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
>
    <!-- 自定义列插槽 -->
</BaseListPage>

<!-- 表单页面 -->
<BaseFormPage
    title="表单标题"
    :submit-method="handleSubmit"
    :initial-data="formData"
    :rules="rules"
>
    <!-- 自定义表单项 -->
</BaseFormPage>
```

---

## 1. 通知中心组件

### NotificationCenter.vue

```vue
<template>
  <div class="notification-center">
    <!-- 通知图标按钮 -->
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

    <!-- 通知抽屉 -->
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
import NotificationDrawer from './NotificationDrawer.vue'

const notificationStore = useNotificationStore()
const drawerVisible = ref(false)

// 未读数量
const unreadCount = computed(() => notificationStore.unreadCount)

// 打开通知抽屉
const handleOpen = () => {
  drawerVisible.value = true
  // 打开时刷新消息
  notificationStore.fetchMessages()
}

// 消息已读
const handleMessageRead = (messageId: number) => {
  notificationStore.markAsRead(messageId)
}

// 全部已读
const handleReadAll = async () => {
  await notificationStore.markAllAsRead()
}

let refreshTimer: number | null = null

onMounted(() => {
  // 初始化时获取消息
  notificationStore.fetchMessages()

  // 每30秒刷新一次
  refreshTimer = window.setInterval(() => {
    notificationStore.fetchMessages()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
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

## 2. 通知抽屉组件

### NotificationDrawer.vue

```vue
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

    <!-- 消息分类Tab -->
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

    <!-- 空状态 -->
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
  (e: 'read', messageId: number): void
  (e: 'read-all'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const activeTab = ref('unread')
const loading = ref(false)

// 使用 Pinia store 获取消息
import { useNotificationStore } from '@/stores/notification'
const notificationStore = useNotificationStore()

const allMessages = computed(() => notificationStore.messages)
const unreadMessages = computed(() => notificationStore.unreadMessages)
const approvalMessages = computed(() => notificationStore.approvalMessages)
const systemMessages = computed(() => notificationStore.systemMessages)

// 统计
const totalCount = computed(() => allMessages.value.length)
const unreadCount = computed(() => unreadMessages.value.length)
const approvalUnreadCount = computed(() =>
  approvalMessages.value.filter(m => !m.is_read).length
)

// 当前Tab显示的消息
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

## 3. 通知列表组件

### NotificationList.vue

```vue
<template>
  <div class="notification-list" v-loading="loading">
    <div
      v-for="message in messages"
      :key="message.id"
      class="notification-item"
      :class="{ unread: !message.is_read }"
      @click="handleClick(message)"
    >
      <!-- 图标 -->
      <div class="notification-icon">
        <el-icon :size="20" :color="getTypeColor(message.message_type)">
          <component :is="getTypeIcon(message.message_type)" />
        </el-icon>
      </div>

      <!-- 内容 -->
      <div class="notification-content">
        <div class="notification-title">
          <span class="title-text">{{ message.title }}</span>
          <el-tag
            v-if="!message.is_read"
            size="small"
            type="danger"
            effect="plain"
          >
            未读
          </el-tag>
        </div>
        <div class="notification-desc">{{ message.content }}</div>
        <div class="notification-time">{{ formatTime(message.created_at) }}</div>
      </div>

      <!-- 操作 -->
      <div class="notification-actions">
        <el-button
          v-if="!message.is_read"
          link
          type="primary"
          size="small"
          @click.stop="handleMarkRead(message)"
        >
          标为已读
        </el-button>
      </div>
    </div>

    <!-- 加载更多 -->
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
  InfoFilled
} from '@element-plus/icons-vue'
import { useNotificationStore } from '@/stores/notification'
import { ElMessage } from 'element-plus'

interface Message {
  id: number
  message_type: string
  title: string
  content: string
  url: string
  button_text: string
  button_url: string
  is_read: boolean
  created_at: string
}

interface Props {
  messages: Message[]
  loading?: boolean
}

interface Emits {
  (e: 'read', messageId: number): void
  (e: 'load-more'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()
const notificationStore = useNotificationStore()

const hasMore = computed(() => props.messages.length >= 20)

const getTypeIcon = (type: string) => {
  const icons = {
    'system': InfoFilled,
    'approval': Document,
    'asset': Box,
    'inventory': Warning,
    'reminder': Bell
  }
  return icons[type] || InfoFilled
}

const getTypeColor = (type: string) => {
  const colors = {
    'system': '#909399',
    'approval': '#409EFF',
    'asset': '#67C23A',
    'inventory': '#E6A23C',
    'reminder': '#F56C6C'
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

const handleClick = (message: Message) => {
  // 标记为已读
  if (!message.is_read) {
    handleMarkRead(message)
  }

  // 跳转到对应页面
  if (message.button_url || message.url) {
    router.push(message.button_url || message.url)
  }
}

const handleMarkRead = async (message: Message) => {
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

## 4. 通知状态管理

```typescript
// src/stores/notification.ts

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getMyMessages,
  markMessageRead,
  markAllMessagesRead,
  getUnreadCount
} from '@/api/notifications'

export interface NotificationMessage {
  id: number
  message_type: string
  title: string
  content: string
  url: string
  button_text: string
  button_url: string
  business_type: string
  business_id: string
  is_read: boolean
  read_at: string | null
  created_at: string
}

export const useNotificationStore = defineStore('notification', () => {
  const messages = ref<NotificationMessage[]>([])
  const unreadCount = ref(0)
  const loading = ref(false)

  // 全部消息
  const allMessages = computed(() => messages.value)

  // 未读消息
  const unreadMessages = computed(() =>
    messages.value.filter(m => !m.is_read)
  )

  // 审批消息
  const approvalMessages = computed(() =>
    messages.value.filter(m => m.message_type === 'approval')
  )

  // 系统消息
  const systemMessages = computed(() =>
    messages.value.filter(m => m.message_type === 'system')
  )

  // 获取消息列表
  const fetchMessages = async () => {
    loading.value = true
    try {
      const data = await getMyMessages()
      messages.value = data.results || data
    } catch (error) {
      console.error('获取消息失败', error)
    } finally {
      loading.value = false
    }
  }

  // 获取未读数量
  const fetchUnreadCount = async () => {
    try {
      const data = await getUnreadCount()
      unreadCount.value = data.count
    } catch (error) {
      console.error('获取未读数量失败', error)
    }
  }

  // 标记为已读
  const markAsRead = async (messageId: number) => {
    try {
      await markMessageRead(messageId)

      // 更新本地状态
      const message = messages.value.find(m => m.id === messageId)
      if (message) {
        message.is_read = true
        message.read_at = new Date().toISOString()
      }

      // 更新未读数量
      if (unreadCount.value > 0) {
        unreadCount.value--
      }
    } catch (error) {
      console.error('标记已读失败', error)
      throw error
    }
  }

  // 全部标记为已读
  const markAllAsRead = async () => {
    try {
      await markAllMessagesRead()

      // 更新本地状态
      messages.value.forEach(m => {
        if (!m.is_read) {
          m.is_read = true
          m.read_at = new Date().toISOString()
        }
      })

      unreadCount.value = 0
    } catch (error) {
      console.error('全部标记已读失败', error)
      throw error
    }
  }

  // 添加新消息（用于WebSocket推送）
  const addMessage = (message: NotificationMessage) => {
    messages.value.unshift(message)
    if (!message.is_read) {
      unreadCount.value++
    }
  }

  // 初始化
  const init = () => {
    fetchMessages()
    fetchUnreadCount()
  }

  return {
    messages,
    unreadCount,
    loading,
    allMessages,
    unreadMessages,
    approvalMessages,
    systemMessages,
    fetchMessages,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    addMessage,
    init
  }
})
```

---

## 5. 通知配置管理页面

### NotificationSettings.vue

```vue
<template>
  <div class="notification-settings">
    <el-page-header title="通知配置" @back="$router.back()" />

    <el-card class="settings-card" shadow="never">
      <!-- 渠道配置 -->
      <h3>通知渠道</h3>
      <el-table :data="channels" style="width: 100%; margin-bottom: 20px">
        <el-table-column prop="channel_type_display" label="渠道名称" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="handleChannelToggle(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="优先级" width="100">
          <template #default="{ row }">
            <el-input-number
              v-model="row.priority"
              :min="0"
              :max="100"
              size="small"
              @change="handlePriorityChange(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleConfigChannel(row)"
            >
              配置
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 模板管理 -->
      <h3>消息模板</h3>
      <el-table :data="templates" style="width: 100%">
        <el-table-column prop="code" label="模板编码" width="180" />
        <el-table-column prop="name" label="模板名称" width="200" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="business_category_display" label="业务分类" width="120" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleEditTemplate(row)"
            >
              编辑
            </el-button>
            <el-button
              link
              type="primary"
              size="small"
              @click="handlePreviewTemplate(row)"
            >
              预览
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 渠道配置弹窗 -->
    <ChannelConfigDialog
      v-model:visible="showChannelDialog"
      :channel="currentChannel"
      @save="handleChannelSave"
    />

    <!-- 模板编辑弹窗 -->
    <TemplateEditDialog
      v-model:visible="showTemplateDialog"
      :template="currentTemplate"
      @save="handleTemplateSave"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getChannels,
  updateChannel,
  getTemplates,
  updateTemplate
} from '@/api/notifications'
import ChannelConfigDialog from './components/ChannelConfigDialog.vue'
import TemplateEditDialog from './components/TemplateEditDialog.vue'

const channels = ref([])
const templates = ref([])
const showChannelDialog = ref(false)
const showTemplateDialog = ref(false)
const currentChannel = ref(null)
const currentTemplate = ref(null)

const fetchData = async () => {
  const [channelsRes, templatesRes] = await Promise.all([
    getChannels(),
    getTemplates()
  ])
  channels.value = channelsRes
  templates.value = templatesRes.results || templatesRes
}

const handleChannelToggle = async (channel) => {
  await updateChannel(channel.id, { is_enabled: channel.is_enabled })
  ElMessage.success('状态已更新')
}

const handlePriorityChange = async (channel) => {
  await updateChannel(channel.id, { priority: channel.priority })
  ElMessage.success('优先级已更新')
}

const handleConfigChannel = (channel) => {
  currentChannel.value = channel
  showChannelDialog.value = true
}

const handleChannelSave = async (config) => {
  await updateChannel(currentChannel.value.id, { config })
  showChannelDialog.value = false
  ElMessage.success('配置已保存')
}

const handleEditTemplate = (template) => {
  currentTemplate.value = template
  showTemplateDialog.value = true
}

const handleTemplateSave = async (data) => {
  await updateTemplate(currentTemplate.value.id, data)
  showTemplateDialog.value = false
  ElMessage.success('模板已保存')
}

const handlePreviewTemplate = (template) => {
  // 打开预览窗口
  const url = `/admin/notifications/templates/${template.id}/preview`
  window.open(url, '_blank')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.notification-settings {
  padding: 20px;
}

.settings-card {
  margin-top: 20px;
}

.settings-card h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
}

.settings-card h3:first-of-type {
  margin-top: 0;
}
</style>
```

---

## 6. API 集成

```typescript
// src/api/notifications/index.ts

import request from '@/utils/request'

/**
 * 获取我的通知（站内信）
 */
export const getMyMessages = (params?: { unread_only?: boolean }) => {
  return request.get('/api/notifications/my-messages/', { params })
}

/**
 * 获取未读数量
 */
export const getUnreadCount = () => {
  return request.get('/api/notifications/my-messages/unread-count/')
}

/**
 * 标记为已读
 */
export const markMessageRead = (id: number) => {
  return request.post(`/api/notifications/my-messages/${id}/mark-read/`)
}

/**
 * 全部标记为已读
 */
export const markAllMessagesRead = () => {
  return request.post('/api/notifications/my-messages/mark-all-read/')
}

/**
 * 获取通知渠道配置
 */
export const getChannels = () => {
  return request.get('/api/notifications/channels/')
}

/**
 * 更新渠道配置
 */
export const updateChannel = (id: number, data: any) => {
  return request.patch(`/api/notifications/channels/${id}/`, data)
}

/**
 * 获取消息模板
 */
export const getTemplates = (params?: { category?: string }) => {
  return request.get('/api/notifications/templates/', { params })
}

/**
 * 更新模板
 */
export const updateTemplate = (id: number, data: any) => {
  return request.patch(`/api/notifications/templates/${id}/`, data)
}

/**
 * 发送测试通知
 */
export const sendTestNotification = (data: {
  recipients: Array<{ user_id: string }>
  channels?: string[]
  title: string
  content: string
}) => {
  return request.post('/api/notifications/send/', data)
}
```

---

## 7. 在头部栏集成通知中心

```vue
<!-- src/layouts/components/AppHeader.vue -->

<template>
  <header class="app-header">
    <!-- ... 其他头部元素 ... -->

    <!-- 通知中心 -->
    <NotificationCenter />

    <!-- 用户下拉菜单 -->
    <UserDropdown />
  </header>
</template>

<script setup lang="ts">
import NotificationCenter from '@/components/NotificationCenter.vue'
import UserDropdown from './UserDropdown.vue'
</script>
```

---

## 8. WebSocket 实时通知（可选）

```typescript
// src/utils/websocket.ts

import { useNotificationStore } from '@/stores/notification'

export class NotificationWebSocket {
  private ws: WebSocket | null = null
  private reconnectTimer: number | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  constructor(private url: string) {}

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }

    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.handleMessage(data)
    }

    this.ws.onclose = () => {
      console.log('WebSocket closed')
      this.scheduleReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  private handleMessage(data: any) {
    const notificationStore = useNotificationStore()

    if (data.type === 'new_notification') {
      // 添加新消息
      notificationStore.addMessage(data.message)

      // 显示浏览器通知
      this.showBrowserNotification(data.message)
    }
  }

  private showBrowserNotification(message: any) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(message.title, {
        body: message.content,
        icon: '/logo.png'
      })
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('Max reconnect attempts reached')
      return
    }

    const delay = Math.pow(2, this.reconnectAttempts) * 1000
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    if (this.ws) {
      this.ws.close()
    }
  }
}

// 初始化
export function initNotificationWebSocket() {
  const token = localStorage.getItem('token')
  if (!token) return

  const wsUrl = `wss://api.example.com/ws/notifications/?token=${token}`
  const ws = new NotificationWebSocket(wsUrl)
  ws.connect()

  return ws
}
```

---

## 后续任务

1. Phase 3.1: 集成LogicFlow流程设计器
2. Phase 3.2: 实现工作流执行引擎
