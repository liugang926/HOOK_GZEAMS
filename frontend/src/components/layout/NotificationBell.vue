<template>
  <div class="notification-bell">
    <el-popover
      placement="bottom-end"
      :width="360"
      trigger="click"
      popper-class="notification-popover"
      @show="handlePopoverShow"
    >
      <template #reference>
        <el-badge
          :value="store.unreadCount"
          :hidden="!store.hasUnread"
          class="bell-badge"
        >
          <el-button
            link
            :icon="Bell"
            class="bell-icon"
            :title="$t('notifications.header.title')"
          />
        </el-badge>
      </template>

      <div class="notification-list">
        <div class="list-header">
          <div class="title-wrap">
            <span class="title">{{ $t('notifications.header.title') }}</span>
            <el-tag
              v-if="store.hasUnread"
              size="small"
              type="danger"
              effect="light"
            >
              {{ store.unreadCount }}
            </el-tag>
          </div>
          <div class="header-actions">
            <el-link
              v-if="store.hasUnread"
              type="primary"
              underline="never"
              @click="handleMarkAllAsRead"
            >
              {{ $t('notifications.actions.markAllRead') }}
            </el-link>
            <el-link
              type="primary"
              underline="never"
              @click="viewAll"
            >
              {{ $t('notifications.actions.viewAll') }}
            </el-link>
          </div>
        </div>

        <el-divider style="margin: 10px 0" />

        <div
          v-if="store.recentNotifications.length > 0"
          class="message-items"
        >
          <div
            v-for="item in store.recentNotifications"
            :key="item.id"
            class="message-item"
            :class="{ unread: !item.readAt }"
            @click="openNotification(item)"
          >
            <div class="message-title-row">
              <span class="message-title">{{ item.title || $t('notifications.fallback.untitled') }}</span>
              <el-tag
                v-if="!item.readAt"
                size="small"
                type="warning"
                effect="plain"
              >
                {{ $t('notifications.status.unread') }}
              </el-tag>
            </div>
            <div
              v-if="item.content"
              class="message-content"
            >
              {{ item.content }}
            </div>
            <div class="message-meta">
              <span class="meta-type">{{ item.notificationType || '-' }}</span>
              <span class="meta-time">{{ formatDisplayDate(item.createdAt) }}</span>
            </div>
          </div>
        </div>

        <div
          v-else
          class="empty-list"
        >
          <el-empty
            :description="$t('notifications.messages.empty')"
            :image-size="72"
          />
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Bell } from '@element-plus/icons-vue'
import { useNotificationStore, resolveNotificationRoute, type NotificationItem } from '@/stores/notification'
import { formatDate } from '@/utils/dateFormat'

const router = useRouter()
const { t } = useI18n()
const store = useNotificationStore()

const handlePopoverShow = () => {
  store.refreshHeaderNotifications()
}

const viewAll = () => {
  router.push('/notifications/center')
}

const handleMarkAllAsRead = async () => {
  await store.markAllAsRead()
  ElMessage.success(t('notifications.messages.markAllReadSuccess'))
}

const openNotification = async (item: NotificationItem) => {
  if (!item.readAt) {
    await store.markAsRead(item.id)
  }

  const targetRoute = resolveNotificationRoute(item)
  if (targetRoute) {
    router.push(targetRoute)
    return
  }

  router.push('/notifications/center')
}

const formatDisplayDate = (value?: string) => {
  if (!value) return '-'
  return formatDate(value)
}

onMounted(() => {
  store.startPolling()
})

onUnmounted(() => {
  store.stopPolling()
})
</script>

<style scoped lang="scss">
.notification-bell {
  display: flex;
  align-items: center;
}

.bell-badge {
  display: flex;
  align-items: center;
}

.bell-icon {
  font-size: 20px;
  color: #606266;

  &:hover {
    color: #409eff;
  }
}

.notification-list {
  max-height: 420px;
  overflow: auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
}

.title-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.header-actions {
  display: inline-flex;
  gap: 8px;
  align-items: center;
}

.message-item {
  padding: 10px 6px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-left: 2px solid transparent;

  &:hover {
    background-color: #f5f7fa;
  }

  &.unread {
    border-left-color: #e6a23c;
    background-color: #fffbf2;
  }
}

.message-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.message-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.message-content {
  color: #606266;
  font-size: 12px;
  line-height: 1.45;
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.empty-list {
  padding: 10px 0;
}
</style>
