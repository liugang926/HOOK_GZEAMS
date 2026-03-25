<template>
  <div class="user-portal">
    <PortalHeader
      :greeting="$t('portal.greeting', { name: displayName })"
      :stats="headerStats"
      :subtitle="$t('portal.subtitle')"
      :user-initial="userInitial"
    />

    <el-tabs
      v-model="activeTab"
      class="portal-tabs"
    >
      <PortalAssetsTab
        :assets="myAssets"
        :current-page="assetPage"
        :loading="loadingAssets"
        :page-size="assetPageSize"
        :search="assetSearch"
        :status-filter="assetStatusFilter"
        :statuses="assetStatuses"
        :total="assetTotal"
        @update:current-page="assetPage = $event"
        @update:page-size="assetPageSize = $event"
        @update:search="assetSearch = $event"
        @update:status-filter="assetStatusFilter = $event"
        @refresh="loadMyAssets"
        @view="goToAsset"
      />

      <PortalRequestsTab
        :can-cancel="canCancelRequest"
        :can-submit="canSubmitRequest"
        :current-page="requestPage"
        :loading="loadingRequests"
        :page-size="requestPageSize"
        :pending-count="pendingRequestCount"
        :request-type="requestType"
        :requests="myRequests"
        :status-filter="requestStatusFilter"
        :statuses="requestStatuses"
        :total="requestTotal"
        @cancel="cancelRequest"
        @create="createNewRequest"
        @update:current-page="requestPage = $event"
        @update:page-size="requestPageSize = $event"
        @update:request-type="requestType = $event"
        @update:status-filter="requestStatusFilter = $event"
        @refresh="loadMyRequests"
        @submit="submitRequest"
        @view="viewRequest"
      />

      <PortalTasksTab
        :current-page="taskPage"
        :loading="loadingTasks"
        :page-size="taskPageSize"
        :pending-count="pendingTaskCount"
        :tasks="myTasks"
        :total="taskTotal"
        @approve="quickApprove"
        @open="openTask"
        @reject="openRejectDialog"
        @refresh="loadMyTasks"
        @update:current-page="taskPage = $event"
        @update:page-size="taskPageSize = $event"
      />
    </el-tabs>

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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'

import { useUserStore } from '@/stores/user'

import PortalAssetsTab from './PortalAssetsTab.vue'
import PortalHeader from './PortalHeader.vue'
import PortalRequestsTab from './PortalRequestsTab.vue'
import PortalTasksTab from './PortalTasksTab.vue'
import {
  createPortalAssetStatusOptions,
} from './portalAssetModel'
import {
  buildPortalHeaderStats,
  getPortalDisplayName,
  getPortalUserInitial,
} from './portalHeaderModel'
import { usePortalAssets } from './usePortalAssets'
import { usePortalRequests } from './usePortalRequests'
import { usePortalTasks } from './usePortalTasks'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const displayName = computed(() => getPortalDisplayName(userStore.userInfo))
const userInitial = computed(() => getPortalUserInitial(displayName.value))
const activeTab = ref('assets')
const actionNotifier = {
  success: (message: string) => ElMessage.success(message),
  warning: (message: string) => ElMessage.warning(message),
  error: (message: string) => ElMessage.error(message),
}
const userId = computed(() => userStore.userInfo?.id)

const assetStatuses = createPortalAssetStatusOptions(t)
const requestStatuses = [
  { value: 'draft', label: t('portal.requests.status.draft') },
  { value: 'pending', label: t('portal.requests.status.pending') },
  { value: 'approved', label: t('portal.requests.status.approved') },
  { value: 'rejected', label: t('portal.requests.status.rejected') },
  { value: 'completed', label: t('portal.requests.status.completed') },
]

const {
  assetPage,
  assetPageSize,
  assetSearch,
  assetStatusFilter,
  assetTotal,
  goToAsset,
  loadingAssets,
  loadMyAssets,
  myAssetCount,
  myAssets,
  refreshMyAssetCount,
} = usePortalAssets(userId, router)
const {
  canCancelRequest,
  canSubmitRequest,
  cancelRequest,
  createNewRequest,
  loadMyRequests,
  loadingRequests,
  myRequests,
  pendingRequestCount,
  refreshPendingRequestCount,
  requestPage,
  requestPageSize,
  requestStatusFilter,
  requestTotal,
  requestType,
  submitRequest,
  viewRequest,
} = usePortalRequests(t, router, actionNotifier)
const {
  confirmReject,
  loadMyTasks,
  loadingTasks,
  myTasks,
  openRejectDialog,
  openTask,
  pendingTaskCount,
  processingTask,
  quickApprove,
  rejectComment,
  rejectDialog,
  taskPage,
  taskPageSize,
  taskTotal,
} = usePortalTasks(t, router, actionNotifier)

const headerStats = computed(() => buildPortalHeaderStats({
  assets: myAssetCount.value,
  pendingRequests: pendingRequestCount.value,
  pendingTasks: pendingTaskCount.value,
}, t))

onMounted(async () => {
  await Promise.all([
    loadMyAssets(),
    refreshMyAssetCount(),
    loadMyRequests(),
    refreshPendingRequestCount(),
    loadMyTasks(),
  ])
})
</script>

<style scoped>
.user-portal { padding: 20px; }

.portal-tabs { background: #fff; border-radius: 8px; padding: 0; }
</style>
