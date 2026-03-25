## 公共组件引用

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| BaseListPage | 标准列表页面 | `@/components/common/BaseListPage.vue` |
| BaseFormPage | 标准表单页面 | `@/components/common/BaseFormPage.vue` |
| BaseDetailPage | 标准详情页面 | `@/components/common/BaseDetailPage.vue` |

---

# Phase 1.9: 统一通知机制 - 前端实现

## 1. 页面结构

### 1.1 页面目录

```
src/views/system/notifications/
├── index.vue                    # 通知管理首页
├── templates/
│   ├── Index.vue               # 模板列表
│   ├── Form.vue                # 模板表单
│   └── Preview.vue             # 模板预览
├── logs/
│   ├── Index.vue               # 发送日志
│   └── Detail.vue              # 日志详情
└── statistics/
    └── Index.vue               # 通知统计
```

### 1.2 组件目录

```
src/components/notifications/
├── NotificationBadge.vue        # 通知徽章/铃铛
├── NotificationCenter.vue       # 消息中心
├── NotificationItem.vue         # 通知列表项
├── NotificationConfig.vue       # 通知设置
└── TemplateEditor.vue           # 模板编辑器
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

## 2. 消息中心组件

### 2.1 通知徽章

**文件**: `src/components/notifications/NotificationBadge.vue`

```vue
<template>
  <div class="notification-badge">
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
      <el-button :icon="Bell" circle @click="openDrawer" />
    </el-badge>

    <!-- 通知抽屉 -->
    <el-drawer
      v-model="visible"
      title="消息中心"
      size="400px"
      @close="handleClose"
    >
      <!-- Tab切换 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name="all">
          <NotificationList
            :notifications="notifications"
            :loading="loading"
            @read="handleRead"
            @delete="handleDelete"
          />
        </el-tab-pane>
        <el-tab-pane label="未读" name="unread">
          <NotificationList
            :notifications="unreadNotifications"
            :loading="loading"
            @read="handleRead"
            @delete="handleDelete"
          />
        </el-tab-pane>
      </el-tabs>

      <!-- 底部操作 -->
      <div class="drawer-footer">
        <el-button link @click="markAllRead">全部标为已读</el-button>
        <el-button link @click="goToSettings">通知设置</el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { notificationApi } from '@/api/notifications'
import NotificationList from './NotificationList.vue'
import { useWebSocketStore } from '@/stores/websocket'

const visible = ref(false)
const activeTab = ref('all')
const loading = ref(false)
const notifications = ref([])
const unreadCount = ref(0)

const websocketStore = useWebSocketStore()

const unreadNotifications = computed(() => {
  return notifications.value.filter(n => !n.is_read)
})

const fetchNotifications = async () => {
  loading.value = true
  try {
    const { data } = await notificationApi.getMyNotifications({
      page: 1,
      page_size: 20
    })
    notifications.value = data.results
    unreadCount.value = data.unread_count
  } finally {
    loading.value = false
  }
}

const fetchUnreadCount = async () => {
  const { data } = await notificationApi.getUnreadCount()
  unreadCount.value = data.unread_count
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
  // 切换Tab时重新加载
}

const handleRead = async (notification: any) => {
  await notificationApi.markAsRead(notification.id)
  notification.is_read = true
  unreadCount.value = Math.max(0, unreadCount.value - 1)
}

const handleDelete = async (notification: any) => {
  await notificationApi.delete(notification.id)
  notifications.value = notifications.value.filter(n => n.id !== notification.id)
  if (!notification.is_read) {
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
}

const markAllRead = async () => {
  await notificationApi.markAllRead()
  notifications.value.forEach(n => n.is_read = true)
  unreadCount.value = 0
}

const goToSettings = () => {
  window.location.href = '/system/notifications/config'
}

// WebSocket 通知监听
const handleNewNotification = (data: any) => {
  notifications.value.unshift(data)
  unreadCount.value += 1

  // 显示桌面通知
  showDesktopNotification(data)
}

const showDesktopNotification = (notification: any) => {
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
})

onUnmounted(() => {
  websocketStore.off('notification.created', handleNewNotification)
})

// 请求桌面通知权限
if ('Notification' in window && Notification.permission === 'default') {
  Notification.requestPermission()
}
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

### 2.2 通知列表项

**文件**: `src/components/notifications/NotificationItem.vue`

```vue
<template>
  <div
    :class="['notification-item', { 'is-unread': !notification.is_read, [`priority-${notification.priority}`]: true }]"
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
        <span class="item-time">{{ formatTime(notification.created_at) }}</span>
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
            <el-dropdown-item command="read" v-if="!notification.is_read">
              标为已读
            </el-dropdown-item>
            <el-dropdown-item command="unread" v-else>
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
import { formatRelativeTime } from '@/utils/date'

interface Props {
  notification: {
    id: number
    title: string
    content: string
    type: string
    priority: string
    is_read: boolean
    created_at: string
    data?: { link?: string }
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['read', 'unread', 'delete', 'click'])

const iconComponent = computed(() => {
  const iconMap: Record<string, any> = {
    workflow_approval: Bell,
    workflow_approved: CircleCheck,
    workflow_rejected: Warning,
    asset_warning: Warning,
    system_announcement: InfoFilled
  }
  return iconMap[props.notification.type] || Bell
})

const iconColor = computed(() => {
  if (!props.notification.is_read) return '#409eff'
  if (props.notification.priority === 'urgent') return '#f56c6c'
  if (props.notification.priority === 'high') return '#e6a23c'
  return '#909399'
})

const formatTime = (time: string) => {
  return formatRelativeTime(new Date(time))
}

const handleClick = () => {
  emit('click', props.notification)

  // 如果有链接，跳转
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

## 3. 通知配置页面

**文件**: `src/views/system/notifications/Config.vue`

```vue
<template>
  <div class="notification-config-page">
    <PageHeader title="通知设置">
      <el-button type="primary" @click="handleSave">保存设置</el-button>
    </PageHeader>

    <el-card>
      <el-form :model="form" label-width="120px">
        <!-- 全局开关 -->
        <div class="config-section">
          <h3>通知渠道</h3>
          <el-form-item label="站内信">
            <el-switch v-model="form.enable_inbox" />
            <span class="form-tip">系统内消息通知</span>
          </el-form-item>
          <el-form-item label="邮件通知">
            <el-switch v-model="form.enable_email" />
            <span class="form-tip">发送到邮箱</span>
          </el-form-item>
          <el-form-item label="短信通知">
            <el-switch v-model="form.enable_sms" />
            <span class="form-tip">发送到手机</span>
          </el-form-item>
          <el-form-item label="企业微信">
            <el-switch v-model="form.enable_wework" />
            <span class="form-tip">推送到企业微信</span>
          </el-form-item>
        </div>

        <!-- 分类设置 -->
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

        <!-- 免打扰设置 -->
        <div class="config-section">
          <h3>免打扰设置</h3>
          <el-form-item label="启用免打扰">
            <el-switch v-model="form.quiet_hours_enabled" />
          </el-form-item>
          <template v-if="form.quiet_hours_enabled">
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

        <!-- 联系方式 -->
        <div class="config-section">
          <h3>联系方式</h3>
          <el-form-item label="接收邮箱">
            <el-input
              v-model="form.email_address"
              placeholder="留空则使用默认邮箱"
            />
          </el-form-item>
          <el-form-item label="接收手机号">
            <el-input
              v-model="form.phone_number"
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
import { ElMessage } from 'element-plus'
import { notificationApi } from '@/api/notifications'

const form = reactive({
  enable_inbox: true,
  enable_email: true,
  enable_sms: false,
  enable_wework: true,
  enable_dingtalk: false,
  channel_settings: {},
  quiet_hours_enabled: false,
  quiet_hours_start: '22:00:00',
  quiet_hours_end: '08:00:00',
  email_address: '',
  phone_number: ''
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
  const { data } = await notificationApi.getConfig()
  Object.assign(form, data)

  // 更新分类设置
  typeSettings.value.forEach(item => {
    const config = data.channel_settings?.[item.type] || {}
    Object.assign(item, config)
  })
}

const handleSave = async () => {
  // 构建保存数据
  const saveData = {
    ...form,
    channel_settings: {}
  }

  typeSettings.value.forEach(item => {
    saveData.channel_settings[item.type] = {
      inbox: item.inbox,
      email: item.email,
      sms: item.sms,
      wework: item.wework
    }
  })

  await notificationApi.updateConfig(saveData)
  ElMessage.success('保存成功')
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
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

## 4. 模板编辑器

**文件**: `src/components/notifications/TemplateEditor.vue`

```vue
<template>
  <div class="template-editor">
    <div class="editor-header">
      <h4>模板编辑器</h4>
      <div class="editor-actions">
        <el-button size="small" @click="insertVariable">插入变量</el-button>
        <el-button size="small" type="primary" @click="handlePreview">预览</el-button>
      </div>
    </div>

    <!-- 变量列表 -->
    <el-dialog v-model="showVariableDialog" title="插入变量" width="500px">
      <el-table :data="variables" @row-click="insertVariableFromRow" style="cursor: pointer">
        <el-table-column prop="name" label="变量名" width="150" />
        <el-table-column prop="description" label="说明" />
        <el-table-column label="插入" width="80">
          <template #default>
            <el-button size="small" type="primary">插入</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 标题模板 -->
    <div class="editor-section">
      <label>标题模板</label>
      <el-input
        v-model="subjectTemplate"
        placeholder="{{ title }}"
        @input="handleTemplateChange"
      />
    </div>

    <!-- 内容模板 -->
    <div class="editor-section">
      <label>内容模板</label>
      <div class="editor-toolbar">
        <el-button-group size="small">
          <el-button @click="insertFormat('bold')">加粗</el-button>
          <el-button @click="insertFormat('italic')">斜体</el-button>
          <el-button @click="insertFormat('link')">链接</el-button>
          <el-button @click="insertFormat('line')">换行</el-button>
        </el-button-group>
      </div>
      <el-input
        v-model="contentTemplate"
        type="textarea"
        :rows="10"
        placeholder="支持Jinja2语法"
        @input="handleTemplateChange"
      />
    </div>

    <!-- 预览 -->
    <div v-if="previewResult" class="preview-section">
      <label>预览效果</label>
      <div class="preview-content">
        <div class="preview-subject">{{ previewResult.subject }}</div>
        <div class="preview-body" v-html="previewResult.content"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  subject: string
  content: string
  channel: string
}

const props = defineProps<Props>()
const emit = defineEmits(['update:subject', 'update:content'])

const subjectTemplate = ref(props.subject)
const contentTemplate = ref(props.content)
const showVariableDialog = ref(false)
const previewResult = ref<any>(null)

const variables = computed(() => {
  const commonVars = [
    { name: '{{ recipient_name }}', description: '接收人姓名' },
    { name: '{{ system_name }}', description: '系统名称' },
    { name: '{{ current_date }}', description: '当前日期' },
    { name: '{{ current_time }}', description: '当前时间' }
  ]

  if (props.channel === 'email') {
    return [
      ...commonVars,
      { name: '{{ recipient_email }}', description: '接收人邮箱' }
    ]
  }

  return commonVars
})

const handleTemplateChange = () => {
  emit('update:subject', subjectTemplate.value)
  emit('update:content', contentTemplate.value)
}

const insertVariable = () => {
  showVariableDialog.value = true
}

const insertVariableFromRow = (row: any) => {
  const textarea = document.querySelector('.template-editor textarea') as HTMLTextAreaElement
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = contentTemplate.value
    const before = text.substring(0, start)
    const after = text.substring(end)

    contentTemplate.value = before + row.name + after
    handleTemplateChange()

    // 设置光标位置
    setTimeout(() => {
      textarea.focus()
      textarea.setSelectionRange(start + row.name.length, start + row.name.length)
    }, 0)
  }

  showVariableDialog.value = false
}

const insertFormat = (type: string) => {
  const textarea = document.querySelector('.template-editor textarea') as HTMLTextAreaElement
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = contentTemplate.value
  const selectedText = text.substring(start, end)

  let insertText = ''
  switch (type) {
    case 'bold':
      insertText = `<strong>${selectedText}</strong>`
      break
    case 'italic':
      insertText = `<em>${selectedText}</em>`
      break
    case 'link':
      insertText = `<a href="#">{{ selectedText }}</a>`
      break
    case 'line':
      insertText = '<br>'
      break
  }

  contentTemplate.value = text.substring(0, start) + insertText + text.substring(end)
  handleTemplateChange()
}

const handlePreview = async () => {
  // 调用预览API
  previewResult.value = {
    subject: subjectTemplate.value.replace(/{{\s*(\w+)\s*}}/g, '示例$1'),
    content: contentTemplate.value.replace(/{{\s*(\w+)\s*}}/g, '示例$1')
  }
}
</script>

<style scoped>
.template-editor {
  border: 1px solid #eee;
  border-radius: 4px;
  padding: 16px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.editor-header h4 {
  margin: 0;
}

.editor-section {
  margin-bottom: 16px;
}

.editor-section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.editor-toolbar {
  margin-bottom: 8px;
}

.preview-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.preview-content {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-subject {
  font-weight: bold;
  margin-bottom: 8px;
}

.preview-body {
  line-height: 1.6;
}
</style>
```

---

## 5. API 请求模块

**文件**: `src/api/notifications.ts`

```typescript
import request from '@/utils/request'

// 通知相关 API
export const notificationApi = {
  // 获取我的通知
  getMyNotifications: (params: any) =>
    request.get('/api/notifications/my/', { params }),

  // 获取通知详情
  getNotificationDetail: (id: number) =>
    request.get(`/api/notifications/my/${id}/`),

  // 标记已读
  markAsRead: (id: number) =>
    request.post(`/api/notifications/my/${id}/read/`),

  // 批量标记已读
  markAllRead: (data?: any) =>
    request.post('/api/notifications/my/read-batch/', data),

  // 删除通知
  delete: (id: number) =>
    request.delete(`/api/notifications/my/${id}/`),

  // 获取未读数量
  getUnreadCount: () =>
    request.get('/api/notifications/my/unread-count/'),

  // 获取通知配置
  getConfig: () =>
    request.get('/api/notifications/config/'),

  // 更新通知配置
  updateConfig: (data: any) =>
    request.patch('/api/notifications/config/', data),

  // 管理员 - 获取通知列表
  getNotifications: (params: any) =>
    request.get('/api/notifications/admin/notifications/', { params }),

  // 管理员 - 重试通知
  retryNotification: (id: number) =>
    request.post(`/api/notifications/admin/notifications/${id}/retry/`),

  // 管理员 - 获取统计
  getStatistics: (params: any) =>
    request.get('/api/notifications/admin/statistics/', { params }),

  // 模板管理
  getTemplates: (params?: any) =>
    request.get('/api/notifications/templates/', { params }),

  createTemplate: (data: any) =>
    request.post('/api/notifications/templates/', data),

  updateTemplate: (id: number, data: any) =>
    request.put(`/api/notifications/templates/${id}/`, data),

  previewTemplate: (id: number, data: any) =>
    request.post(`/api/notifications/templates/${id}/preview/`, data)
}
```

---

## 6. WebSocket 集成

**文件**: `src/stores/websocket.ts`

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useNotificationStore } from './notification'

export const useWebSocketStore = defineStore('websocket', () => {
  const connected = ref(false)
  const socket = ref<WebSocket | null>(null)
  const reconnectTimer = ref<number | null>(null)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 5

  const eventHandlers = new Map<string, Function[]>()

  const notificationStore = useNotificationStore()

  const connect = () => {
    const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws/`
    socket.value = new WebSocket(wsUrl)

    socket.value.onopen = () => {
      connected.value = true
      reconnectAttempts.value = 0
      console.log('WebSocket connected')
    }

    socket.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        handleMessage(data)
      } catch (error) {
        console.error('WebSocket message error:', error)
      }
    }

    socket.value.onclose = () => {
      connected.value = false
      scheduleReconnect()
    }

    socket.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }

  const disconnect = () => {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
    connected.value = false
  }

  const scheduleReconnect = () => {
    if (reconnectAttempts.value >= maxReconnectAttempts) {
      console.log('Max reconnect attempts reached')
      return
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.value), 30000)
    reconnectAttempts.value++

    reconnectTimer.value = window.setTimeout(() => {
      connect()
    }, delay)
  }

  const handleMessage = (data: any) => {
    const { event, payload } = data

    // 触发事件监听器
    const handlers = eventHandlers.get(event) || []
    handlers.forEach(handler => handler(payload))

    // 特殊事件处理
    switch (event) {
      case 'notification.created':
        notificationStore.addNotification(payload)
        break
      case 'notification.read':
        notificationStore.updateNotification(payload.notification_id, { is_read: true })
        break
    }
  }

  const on = (event: string, handler: Function) => {
    if (!eventHandlers.has(event)) {
      eventHandlers.set(event, [])
    }
    eventHandlers.get(event)!.push(handler)
  }

  const off = (event: string, handler: Function) => {
    const handlers = eventHandlers.get(event)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  const send = (data: any) => {
    if (socket.value && connected.value) {
      socket.value.send(JSON.stringify(data))
    }
  }

  return {
    connected,
    connect,
    disconnect,
    send,
    on,
    off
  }
})
```

---

## 7. 通知 Store

**文件**: `src/stores/notification.ts`

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { notificationApi } from '@/api/notifications'

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<any[]>([])
  const unreadCount = ref(0)

  const fetchNotifications = async () => {
    const { data } = await notificationApi.getMyNotifications({
      page: 1,
      page_size: 20
    })
    notifications.value = data.results
    unreadCount.value = data.unread_count
  }

  const fetchUnreadCount = async () => {
    const { data } = await notificationApi.getUnreadCount()
    unreadCount.value = data.unread_count
  }

  const addNotification = (notification: any) => {
    notifications.value.unshift(notification)
    if (!notification.is_read) {
      unreadCount.value++
    }
  }

  const updateNotification = (id: number, updates: any) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      Object.assign(notifications.value[index], updates)
    }
  }

  const removeNotification = (id: number) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      const notification = notifications.value[index]
      notifications.value.splice(index, 1)
      if (!notification.is_read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    }
  }

  const markAsRead = async (id: number) => {
    await notificationApi.markAsRead(id)
    updateNotification(id, { is_read: true })
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }

  const markAllAsRead = async () => {
    await notificationApi.markAllRead({ all: true })
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
  }

  return {
    notifications,
    unreadCount,
    fetchNotifications,
    fetchUnreadCount,
    addNotification,
    updateNotification,
    removeNotification,
    markAsRead,
    markAllAsRead
  }
})
```
