<!--
  UserPortal.vue

  User-facing portal with three tabs:
  1. My Assets
  2. My Requests
  3. My Tasks
-->
<template>
  <div class="user-portal">
    <!-- 鈹€鈹€ Page Header 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
    <div class="portal-header">
      <div class="header-left">
        <el-avatar
          :size="48"
          class="user-avatar"
        >
          {{ userInitial }}
        </el-avatar>
        <div class="header-info">
          <h2 class="portal-title">
            {{ $t('portal.greeting', { name: displayName }) }}
          </h2>
          <p class="portal-subtitle">
            {{ $t('portal.subtitle') }}
          </p>
        </div>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <div class="stat-num">
            {{ myAssetCount }}
          </div>
          <div class="stat-label">
            {{ $t('portal.stats.assets') }}
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-num">
            {{ pendingRequestCount }}
          </div>
          <div class="stat-label">
            {{ $t('portal.stats.pendingRequests') }}
          </div>
        </div>
        <div class="stat-item danger">
          <div class="stat-num">
            {{ pendingTaskCount }}
          </div>
          <div class="stat-label">
            {{ $t('portal.stats.pendingTasks') }}
          </div>
        </div>
      </div>
    </div>

    <el-tabs
      v-model="activeTab"
      class="portal-tabs"
    >
      <!-- 鈹€鈹€ Tab 1: My Assets 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
      <el-tab-pane
        :label="$t('portal.tabs.myAssets')"
        name="assets"
      >
        <div class="tab-toolbar">
          <el-input
            v-model="assetSearch"
            :placeholder="$t('portal.assets.searchPlaceholder')"
            clearable
            style="width:240px"
            @input="loadMyAssets"
          />
          <el-select
            v-model="assetStatusFilter"
            :placeholder="$t('portal.assets.allStatus')"
            clearable
            style="width:140px"
            @change="loadMyAssets"
          >
            <el-option
              v-for="s in assetStatuses"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </div>

        <el-table
          v-loading="loadingAssets"
          :data="myAssets"
          border
          stripe
          @row-click="goToAsset"
        >
          <el-table-column
            :label="$t('portal.assets.cols.code')"
            prop="assetCode"
            width="130"
          />
          <el-table-column
            :label="$t('portal.assets.cols.name')"
            prop="name"
            min-width="160"
          />
          <el-table-column
            :label="$t('portal.assets.cols.category')"
            prop="categoryDisplay"
            width="130"
          />
          <el-table-column
            :label="$t('portal.assets.cols.status')"
            prop="statusDisplay"
            width="100"
          >
            <template #default="{ row }">
              <el-tag
                :type="statusTagType(row.status)"
                size="small"
              >
                {{ row.statusDisplay || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('portal.assets.cols.location')"
            prop="locationDisplay"
            width="140"
          />
          <el-table-column
            :label="$t('portal.assets.cols.value')"
            prop="currentValue"
            width="120"
          >
            <template #default="{ row }">
              {{ row.currentValue != null ? `${$t('common.units.yuan')} ${Number(row.currentValue).toLocaleString()}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('portal.assets.cols.actions')"
            width="120"
          >
            <template #default="{ row }">
              <el-button
                size="small"
                @click.stop="goToAsset(row)"
              >
                {{ $t('common.actions.view') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="assetPage"
          v-model:page-size="assetPageSize"
          :total="assetTotal"
          layout="total, prev, pager, next"
          class="mt-16"
          @current-change="loadMyAssets"
        />
      </el-tab-pane>

      <!-- 鈹€鈹€ Tab 2: My Requests 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
      <el-tab-pane name="requests">
        <template #label>
          <span>{{ $t('portal.tabs.myRequests') }}</span>
          <el-badge
            v-if="pendingRequestCount > 0"
            :value="pendingRequestCount"
            type="warning"
            class="tab-badge"
          />
        </template>

        <div class="tab-toolbar">
          <el-radio-group
            v-model="requestType"
            @change="loadMyRequests"
          >
            <el-radio-button value="purchase">
              {{ $t('portal.requests.type.purchase') }}
            </el-radio-button>
            <el-radio-button value="maintenance">
              {{ $t('portal.requests.type.maintenance') }}
            </el-radio-button>
            <el-radio-button value="disposal">
              {{ $t('portal.requests.type.disposal') }}
            </el-radio-button>
          </el-radio-group>
          <el-select
            v-model="requestStatusFilter"
            :placeholder="$t('portal.requests.allStatus')"
            clearable
            style="width:130px"
            @change="loadMyRequests"
          >
            <el-option
              v-for="s in requestStatuses"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
          <el-button
            type="primary"
            :icon="Plus"
            @click="createNewRequest"
          >
            {{ $t('portal.requests.new') }}
          </el-button>
        </div>

        <el-table
          v-loading="loadingRequests"
          :data="myRequests"
          border
          stripe
        >
          <el-table-column
            :label="$t('portal.requests.cols.code')"
            prop="code"
            width="140"
          />
          <el-table-column
            :label="$t('portal.requests.cols.title')"
            prop="title"
            min-width="160"
          />
          <el-table-column
            :label="$t('portal.requests.cols.status')"
            prop="statusDisplay"
            width="110"
          >
            <template #default="{ row }">
              <el-tag
                :type="requestStatusTagType(row.status)"
                size="small"
              >
                {{ row.statusDisplay || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('portal.requests.cols.createdAt')"
            prop="createdAt"
            width="155"
          >
            <template #default="{ row }">
              {{ formatDate(row.createdAt) }}
            </template>
          </el-table-column>
          <el-table-column
            :label="$t('portal.requests.cols.actions')"
            width="160"
          >
            <template #default="{ row }">
              <el-button
                size="small"
                @click="viewRequest(row)"
              >
                {{ $t('common.actions.view') }}
              </el-button>
              <el-button
                v-if="row.status === 'draft'"
                size="small"
                type="primary"
                @click="submitRequest(row)"
              >
                {{ $t('portal.requests.submit') }}
              </el-button>
              <el-button
                v-if="['draft','pending'].includes(row.status)"
                size="small"
                type="danger"
                @click="cancelRequest(row)"
              >
                {{ $t('portal.requests.cancel') }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-pagination
          v-model:current-page="requestPage"
          v-model:page-size="requestPageSize"
          :total="requestTotal"
          layout="total, prev, pager, next"
          class="mt-16"
          @current-change="loadMyRequests"
        />
      </el-tab-pane>

      <!-- 鈹€鈹€ Tab 3: My Pending Tasks 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
      <el-tab-pane name="tasks">
        <template #label>
          <span>{{ $t('portal.tabs.myTasks') }}</span>
          <el-badge
            v-if="pendingTaskCount > 0"
            :value="pendingTaskCount"
            type="danger"
            class="tab-badge"
          />
        </template>

        <div class="tab-toolbar">
          <el-button
            :icon="Refresh"
            @click="loadMyTasks"
          >
            {{ $t('common.actions.refresh') }}
          </el-button>
        </div>

        <div
          v-if="myTasks.length === 0 && !loadingTasks"
          class="no-tasks"
        >
          <el-empty :description="$t('portal.tasks.empty')" />
        </div>

        <div
          v-loading="loadingTasks"
          class="task-cards"
        >
          <div
            v-for="task in myTasks"
            :key="task.id"
            class="task-card"
            @click="openTask(task)"
          >
            <div class="task-card-left">
              <el-tag
                type="warning"
                size="small"
                class="task-type"
              >
                {{ task.taskName || task.nodeName || $t('portal.tasks.approvalTask') }}
              </el-tag>
              <div class="task-title">
                {{ task.title || task.businessTitle || task.instanceTitle || '-' }}
              </div>
              <div class="task-meta">
                <span>{{ $t('portal.tasks.initiator') }}: {{ task.initiatorDisplay || task.createdBy || '-' }}</span>
                <span class="meta-sep">•</span>
                <span>{{ formatDate(task.createdAt || task.assignedAt) }}</span>
              </div>
            </div>
            <div class="task-card-right">
              <el-button
                type="success"
                size="small"
                @click.stop="quickApprove(task)"
              >
                {{ $t('portal.tasks.approve') }}
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click.stop="openRejectDialog(task)"
              >
                {{ $t('portal.tasks.reject') }}
              </el-button>
            </div>
          </div>
        </div>

        <el-pagination
          v-model:current-page="taskPage"
          v-model:page-size="taskPageSize"
          :total="taskTotal"
          layout="total, prev, pager, next"
          class="mt-16"
          @current-change="loadMyTasks"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 鈹€鈹€ Reject Comment Dialog 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ -->
    <el-dialog
      v-model="rejectDialog"
      :title="$t('portal.tasks.rejectTitle')"
      width="420px"
      destroy-on-close
    >
      <el-form>
        <el-form-item :label="$t('portal.tasks.rejectComment')">
          <el-input
            v-model="rejectComment"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialog = false">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="danger"
          :loading="processingTask"
          @click="confirmReject"
        >
          {{ $t('portal.tasks.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { assetApi } from '@/api/assets'
import { purchaseRequestApi, maintenanceApi, disposalRequestApi } from '@/api/lifecycle'
import { workflowNodeApi, taskApi } from '@/api/workflow'
import { runAction, runFlagAction } from '@/composables'
import { formatDate } from '@/utils/dateFormat'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

// 鈹€鈹€ User Info 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const displayName = computed(() => userStore.userInfo?.fullName || userStore.userInfo?.username || '')
const userInitial = computed(() => displayName.value.charAt(0).toUpperCase() || 'U')
const activeTab = ref('assets')
const actionNotifier = {
  success: (message: string) => ElMessage.success(message),
  warning: (message: string) => ElMessage.warning(message),
  error: (message: string) => ElMessage.error(message)
}

// 鈹€鈹€ Status options 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const assetStatuses = [
  { value: 'in_use', label: t('portal.assets.status.inUse') },
  { value: 'idle', label: t('portal.assets.status.idle') },
  { value: 'under_maintenance', label: t('portal.assets.status.maintenance') },
  { value: 'disposed', label: t('portal.assets.status.disposed') }
]
const requestStatuses = [
  { value: 'draft', label: t('portal.requests.status.draft') },
  { value: 'pending', label: t('portal.requests.status.pending') },
  { value: 'approved', label: t('portal.requests.status.approved') },
  { value: 'rejected', label: t('portal.requests.status.rejected') },
  { value: 'completed', label: t('portal.requests.status.completed') }
]

const statusTagType = (s: string) => {
  const m: any = { in_use: 'success', idle: 'info', under_maintenance: 'warning', disposed: 'danger', scrapped: 'danger' }
  return m[s] || 'info'
}
const requestStatusTagType = (s: string) => {
  const m: any = { draft: 'info', pending: 'warning', approved: 'success', rejected: 'danger', completed: '', cancelled: 'info' }
  return m[s] || 'info'
}

// 鈹€鈹€ My Assets 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const loadingAssets = ref(false)
const myAssets = ref<any[]>([])
const assetSearch = ref('')
const assetStatusFilter = ref('')
const assetPage = ref(1)
const assetPageSize = ref(15)
const assetTotal = ref(0)
const myAssetCount = ref(0)

const loadMyAssets = async () => {
  loadingAssets.value = true
  try {
    const res: any = await assetApi.list({
      page: assetPage.value,
      page_size: assetPageSize.value,
      search: assetSearch.value || undefined,
      status: assetStatusFilter.value || undefined,
      responsible_user_id: userStore.userInfo?.id
    })
    myAssets.value = res?.results ?? res?.items ?? []
    assetTotal.value = res?.count ?? res?.total ?? 0
    myAssetCount.value = assetTotal.value
  } finally {
    loadingAssets.value = false
  }
}

const goToAsset = (row: any) => router.push(`/assets/${row.id}`)

// 鈹€鈹€ My Requests 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const loadingRequests = ref(false)
const myRequests = ref<any[]>([])
const requestType = ref<'purchase' | 'maintenance' | 'disposal'>('purchase')
const requestStatusFilter = ref('')
const requestPage = ref(1)
const requestPageSize = ref(15)
const requestTotal = ref(0)
const pendingRequestCount = ref(0)
const requestApiMap: Record<'purchase' | 'maintenance' | 'disposal', any> = {
  purchase: purchaseRequestApi,
  maintenance: maintenanceApi,
  disposal: disposalRequestApi
}

const loadMyRequests = async () => {
  loadingRequests.value = true
  try {
    const api = requestApiMap[requestType.value]
    const res: any = await api.list({
      page: requestPage.value,
      page_size: requestPageSize.value,
      status: requestStatusFilter.value || undefined,
      created_by_me: true
    })
    myRequests.value = res?.results ?? []
    requestTotal.value = res?.count ?? 0
  } finally {
    loadingRequests.value = false
  }
}

const viewRequest = (row: any) => {
  const routeMap: any = {
    purchase: `/assets/lifecycle/purchase-requests/${row.id}`,
    maintenance: `/assets/lifecycle/maintenance/${row.id}`,
    disposal: `/assets/lifecycle/disposal-requests/${row.id}`
  }
  router.push(routeMap[requestType.value])
}

const createNewRequest = () => {
  const routeMap: any = {
    purchase: '/assets/lifecycle/purchase-requests/create',
    maintenance: '/assets/lifecycle/maintenance/create',
    disposal: '/assets/lifecycle/disposal-requests/create'
  }
  router.push(routeMap[requestType.value])
}

const submitRequest = async (row: any) => {
  try {
    await ElMessageBox.confirm(t('portal.requests.submitConfirm'), { type: 'info' })
  } catch {
    return
  }

  const api = requestApiMap[requestType.value]
  await runAction({
    notifier: actionNotifier,
    messages: {
      successFallback: t('portal.requests.submitSuccess'),
      failureFallback: t('portal.requests.submitFailed'),
      errorFallback: t('portal.requests.submitFailed')
    },
    invoke: async () => {
      await api.submit(row.id)
      return { success: true }
    },
    onSuccess: async () => {
      await loadMyRequests()
    }
  })
}

const cancelRequest = async (row: any) => {
  try {
    await ElMessageBox.confirm(t('portal.requests.cancelConfirm'), { type: 'warning' })
  } catch {
    return
  }

  const api = requestApiMap[requestType.value]
  await runAction({
    notifier: actionNotifier,
    messages: {
      successFallback: t('common.messages.operationSuccess'),
      failureFallback: t('common.messages.operationFailed'),
      errorFallback: t('common.messages.operationFailed')
    },
    invoke: async () => {
      await api.cancel(row.id)
      return { success: true }
    },
    onSuccess: async () => {
      await loadMyRequests()
    }
  })
}

// 鈹€鈹€ My Tasks (workflow) 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
const loadingTasks = ref(false)
const myTasks = ref<any[]>([])
const taskPage = ref(1)
const taskPageSize = ref(10)
const taskTotal = ref(0)
const pendingTaskCount = ref(0)

const loadMyTasks = async () => {
  loadingTasks.value = true
  try {
    const res: any = await workflowNodeApi.getMyTasks({ page: taskPage.value, pageSize: taskPageSize.value })
    myTasks.value = res?.results ?? []
    taskTotal.value = res?.count ?? 0
    pendingTaskCount.value = taskTotal.value
  } finally {
    loadingTasks.value = false
  }
}

const openTask = (task: any) => router.push(`/workflow/tasks/${task.id}`)

// Quick approve
const processingTask = ref(false)
const quickApprove = async (task: any) => {
  await runFlagAction({
    loadingFlag: processingTask,
    notifier: actionNotifier,
    messages: {
      successFallback: t('portal.tasks.approveSuccess'),
      failureFallback: t('portal.tasks.approveFailed'),
      errorFallback: t('portal.tasks.approveFailed')
    },
    invoke: async () => {
      await taskApi.approveTask(task.id, { comment: '' })
      return { success: true }
    },
    onSuccess: async () => {
      await loadMyTasks()
    }
  })
}

// Reject
const rejectDialog = ref(false)
const rejectComment = ref('')
let rejectTargetTask: any = null

const openRejectDialog = (task: any) => {
  rejectTargetTask = task
  rejectComment.value = ''
  rejectDialog.value = true
}

const confirmReject = async () => {
  if (!rejectTargetTask) return
  await runFlagAction({
    loadingFlag: processingTask,
    notifier: actionNotifier,
    messages: {
      successFallback: t('portal.tasks.rejectSuccess'),
      failureFallback: t('portal.tasks.rejectFailed'),
      errorFallback: t('portal.tasks.rejectFailed')
    },
    invoke: async () => {
      await taskApi.rejectTask(rejectTargetTask.id, { comment: rejectComment.value })
      return { success: true }
    },
    onSuccess: async () => {
      rejectDialog.value = false
      await loadMyTasks()
    }
  })
}

onMounted(async () => {
  loadMyAssets()
  loadMyRequests()
  loadMyTasks()
})
</script>

<style scoped>
.user-portal { padding: 20px; }

/* 鈹€鈹€ Header 鈹€鈹€ */
.portal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #409eff 0%, #6366f1 100%);
  border-radius: 12px;
  padding: 24px 28px;
  margin-bottom: 20px;
  color: #fff;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.user-avatar {
  background: rgba(255,255,255,0.25);
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}
.portal-title { margin: 0 0 4px; font-size: 20px; font-weight: 700; }
.portal-subtitle { margin: 0; opacity: 0.85; font-size: 13px; }

.header-stats { display: flex; gap: 24px; }
.stat-item { text-align: center; }
.stat-item.danger .stat-num { color: #ffd666; }
.stat-num { font-size: 28px; font-weight: 700; line-height: 1; }
.stat-label { font-size: 12px; opacity: 0.8; margin-top: 4px; }

/* 鈹€鈹€ Tabs 鈹€鈹€ */
.portal-tabs { background: #fff; border-radius: 8px; padding: 0; }
.tab-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }
.tab-badge { margin-left: 4px; }
.mt-16 { margin-top: 16px; }

/* 鈹€鈹€ Task cards 鈹€鈹€ */
.no-tasks { padding: 40px 0; }
.task-cards { display: flex; flex-direction: column; gap: 10px; }
.task-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
  background: #fff;
}
.task-card:hover { border-color: #409eff; box-shadow: 0 2px 8px rgba(64,158,255,0.15); }
.task-card-left { flex: 1; min-width: 0; }
.task-type { margin-bottom: 6px; }
.task-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 6px 0 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-meta { font-size: 12px; color: #909399; }
.meta-sep { margin: 0 6px; }
.task-card-right { display: flex; gap: 6px; flex-shrink: 0; margin-left: 16px; }

/* 鈹€鈹€ Row click style 鈹€鈹€ */
:deep(.el-table__row) { cursor: pointer; }
</style>

