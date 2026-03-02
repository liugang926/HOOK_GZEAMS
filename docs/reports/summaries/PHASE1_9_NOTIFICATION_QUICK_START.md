# Notification Enhancement - Quick Start Guide

## Installation & Setup

### 1. Files Overview
The following files have been created:

```
frontend/src/
├── api/
│   └── notifications.js              # API module
├── stores/
│   ├── notification.js               # Notification store
│   └── websocket.js                  # WebSocket store
├── components/
│   ├── layout/
│   │   └── Header.vue                # Header with notification bell
│   └── notifications/
│       ├── index.js                  # Component exports
│       ├── NotificationBadge.vue     # Bell icon + drawer
│       ├── NotificationList.vue      # Scrollable list
│       └── NotificationItem.vue      # Individual notification
└── views/
    └── system/
        └── notifications/
            └── Config.vue            # Settings page
```

### 2. Usage in Your Application

#### Step 1: Import and Register Stores (if needed)
```javascript
// main.js
import { createPinia } from 'pinia'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
```

#### Step 2: Use Header Component with Notification Badge
```vue
<!-- App.vue or MainLayout.vue -->
<template>
  <div class="app-container">
    <Header />
    <router-view />
  </div>
</template>

<script setup>
import Header from '@/components/layout/Header.vue'
// WebSocket connection is automatically managed by NotificationBadge
</script>
```

#### Step 3: Add Router Route for Settings
```javascript
// router/index.js
const routes = [
  // ... other routes
  {
    path: '/system/notifications/config',
    name: 'NotificationConfig',
    component: () => import('@/views/system/notifications/Config.vue'),
    meta: { requiresAuth: true }
  }
]
```

### 3. Using Notification Store Programmatically

```vue
<script setup>
import { useNotificationStore } from '@/stores/notification'
import { storeToRefs } from 'pinia'

const notificationStore = useNotificationStore()
const { notifications, unreadCount, hasUnread } = storeToRefs(notificationStore)

// Fetch notifications
await notificationStore.fetchNotifications()

// Mark as read
await notificationStore.markAsRead(notificationId)

// Mark all as read
await notificationStore.markAllAsRead()

// Delete notification
await notificationStore.deleteNotification(notificationId)
</script>
```

### 4. Using WebSocket Store

```vue
<script setup>
import { useWebSocketStore } from '@/stores/websocket'

const websocketStore = useWebSocketStore()

// Subscribe to custom events
websocketStore.on('notification.created', (data) => {
  console.log('New notification:', data)
})

// Unsubscribe
const handler = (data) => console.log(data)
websocketStore.on('notification.created', handler)
// Later...
websocketStore.off('notification.created', handler)

// Manual connect/disconnect
websocketStore.connect()
websocketStore.disconnect()
</script>
```

### 5. Environment Configuration

Create or update `.env.development` and `.env.production`:

```bash
# .env.development
VITE_WS_URL=ws://localhost:8000/ws/notifications/
VITE_WS_HOST=localhost:8000

# .env.production
VITE_WS_URL=wss://your-domain.com/ws/notifications/
VITE_WS_HOST=your-domain.com
```

### 6. Backend API Requirements

Ensure your backend provides these endpoints:

```python
# Django REST Framework example

# urls.py
urlpatterns = [
    # User notifications
    path('api/notifications/my/', views.MyNotificationViewSet.as_view({'get': 'list'})),
    path('api/notifications/my/<uuid:id>/', views.MyNotificationViewSet.as_view({'get': 'retrieve'})),
    path('api/notifications/my/<uuid:id>/read/', views.mark_as_read),
    path('api/notifications/my/read-batch/', views.mark_all_read),
    path('api/notifications/my/<uuid:id>/', views.MyNotificationViewSet.as_view({'delete': 'destroy'})),
    path('api/notifications/my/unread-count/', views.unread_count),

    # Configuration
    path('api/notifications/config/', views.NotificationConfigView.as_view()),

    # Admin endpoints (optional)
    path('api/notifications/admin/notifications/', views.AdminNotificationViewSet.as_view({'get': 'list'})),
    path('api/notifications/admin/statistics/', views.statistics),

    # Templates (optional)
    path('api/notifications/templates/', views.NotificationTemplateViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
]

# WebSocket consumer
# consumers.py
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.group_name = f'user_{self.user.id}'

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def notification(self, event):
        await self.send(text_data=json.dumps({
            'event': event['event'],
            'payload': event['payload']
        }))
```

### 7. Sending Notifications from Backend

```python
# Example: Send notification when asset is approved
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_notification(user_id, title, content, notification_type, priority='normal', link=None):
    channel_layer = get_channel_layer()

    payload = {
        'id': str(uuid.uuid4()),
        'title': title,
        'content': content,
        'type': notification_type,
        'priority': priority,
        'is_read': False,
        'created_at': timezone.now().isoformat(),
        'data': {'link': link} if link else {}
    }

    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': 'notification',
            'event': 'notification.created',
            'payload': payload
        }
    )

# Usage
send_notification(
    user_id=request.user.id,
    title='资产审批通过',
    content='您的资产申请已通过审批',
    notification_type='workflow_approved',
    priority='high',
    link='/assets/123'
)
```

### 8. Customizing Notification Types

Edit `NotificationItem.vue` to add new notification types:

```vue
<script setup>
const iconComponent = computed(() => {
  const iconMap = {
    workflow_approval: Bell,
    workflow_approved: CircleCheck,
    workflow_rejected: Warning,
    asset_warning: Warning,
    inventory_assigned: Bell,
    system_announcement: InfoFilled,
    // Add your custom types here
    custom_type: YourCustomIcon
  }
  return iconMap[props.notification.type] || Bell
})
</script>
```

### 9. Troubleshooting

#### WebSocket Not Connecting
1. Check browser console for errors
2. Verify WebSocket URL in environment variables
3. Ensure backend WebSocket server is running
4. Check firewall/proxy settings

#### Notifications Not Appearing
1. Check `unreadCount` in notification store
2. Verify API endpoints are returning correct data
3. Check browser network tab for failed requests
4. Ensure user is authenticated

#### Desktop Notifications Not Working
1. Check browser notification permissions
2. Must be on HTTPS or localhost
3. Some browsers block notifications on iframes
4. Check browser settings

### 10. Performance Tips

1. **Limit Notifications**: The store fetches 20 notifications by default
2. **Pagination Ready**: Implement pagination in `handleLoadMore` method
3. **Debounce Updates**: If sending frequent updates, consider debouncing
4. **Cleanup**: Unsubscribe from WebSocket events when component unmounts

---

## Full Example Component

```vue
<template>
  <div>
    <el-badge :value="unreadCount" :hidden="!hasUnread">
      <el-button @click="showNotifications">通知</el-button>
    </el-badge>

    <el-dialog v-model="visible" title="我的通知" width="500px">
      <NotificationList
        :notifications="notifications"
        :loading="loading"
        @read="handleRead"
        @delete="handleDelete"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { storeToRefs } from 'pinia'
import { NotificationList } from '@/components/notifications'

const notificationStore = useNotificationStore()
const { notifications, unreadCount, hasUnread, loading } = storeToRefs(notificationStore)

const visible = ref(false)

const showNotifications = () => {
  visible.value = true
  if (notifications.value.length === 0) {
    notificationStore.fetchNotifications()
  }
}

const handleRead = async (notification) => {
  await notificationStore.markAsRead(notification.id)
}

const handleDelete = async (notification) => {
  await notificationStore.deleteNotification(notification.id)
}

onMounted(() => {
  notificationStore.fetchUnreadCount()
})
</script>
```

---

## Support & Documentation

- Full Implementation Report: `PHASE1_9_NOTIFICATION_FRONTEND_IMPLEMENTATION_REPORT.md`
- PRD Document: `docs/plans/phase1_9_notification_enhancement/frontend.md`
- Element Plus Docs: https://element-plus.org/
- Vue 3 Docs: https://vuejs.org/
- Pinia Docs: https://pinia.vuejs.org/

---

**Last Updated**: 2026-01-16
**Version**: 1.0.0
