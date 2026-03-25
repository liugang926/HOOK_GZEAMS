<template>
  <div class="task-execute-page">
    <!-- Header -->
    <div class="task-header">
      <div class="header-left">
        <el-button
          icon="ArrowLeft"
          circle
          @click="$router.back()"
        />
        <div class="task-info">
          <h2 class="task-title">
            {{ task?.name || 'Loading...' }}
          </h2>
          <span class="task-status">{{ task?.status_display || task?.status }}</span>
        </div>
      </div>
      <div class="header-right">
        <el-button
          type="primary"
          link
          @click="refreshData"
        >
          {{ t('common.actions.refresh') }}
        </el-button>
      </div>
    </div>

    <!-- Progress -->
    <div
      v-if="task"
      class="task-progress"
    >
      <div class="progress-stats">
        <span>{{ t('inventory.columns.progress') }}: {{ task.progress_percent }}%</span>
        <span>{{ task.scanned_count }} / {{ task.total_count }}</span>
      </div>
      <el-progress
        :percentage="task.progress_percent"
        :show-text="false"
      />
    </div>

    <!-- Tabs -->
    <el-tabs
      v-model="activeTab"
      class="execute-tabs"
      stretch
    >
      <!-- SCAN TAB -->
      <el-tab-pane
        name="scan"
        :label="t('inventory.actions.scan')"
      >
        <div class="scan-container">
          <div class="scanner-wrapper">
            <MobileQRScanner 
              ref="scannerRef"
              :auto-start="false"
              :auto-submit="true"
              :show-preview="false"
              @scan="handleScan"
              @error="handleScanError"
            />
          </div>
          
          <!-- Last Scanned Result -->
          <div
            v-if="lastScanned"
            class="last-scan-card"
          >
            <div
              class="scan-status"
              :class="lastScanned.status"
            >
              <el-icon><Check v-if="lastScanned.status === 'success'" /><Warning v-else /></el-icon>
            </div>
            <div class="scan-info">
              <p class="asset-name">
                {{ lastScanned.asset_name }}
              </p>
              <p class="asset-code">
                {{ lastScanned.asset_code }}
              </p>
              <p class="scan-msg">
                {{ lastScanned.message }}
              </p>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- LIST TAB -->
      <el-tab-pane
        name="list"
        :label="t('inventory.execute.scannedList')"
      >
        <div
          v-loading="loadingList"
          class="list-container"
        >
          <div class="filter-bar">
            <el-radio-group
              v-model="listFilter"
              size="small"
              @change="fetchSnapshots"
            >
              <el-radio-button label="all">
                {{ t('common.filters.all') || 'All' }}
              </el-radio-button>
              <el-radio-button label="unscanned">
                {{ t('inventory.execute.unscannedList') }}
              </el-radio-button>
              <el-radio-button label="scanned">
                {{ t('inventory.execute.scannedList') }}
              </el-radio-button>
            </el-radio-group>
          </div>
           
          <div class="snapshot-list">
            <div
              v-for="item in snapshots"
              :key="item.id"
              class="snapshot-item"
              :class="{ scanned: item.is_scanned }"
            >
              <div class="item-main">
                <div class="item-name">
                  {{ item.asset_name }}
                </div>
                <div class="item-code">
                  {{ item.asset_code }}
                </div>
              </div>
              <div class="item-status">
                <el-tag
                  v-if="item.is_scanned"
                  type="success"
                  size="small"
                >
                  {{ t('inventory.status.completed') }}
                </el-tag>
                <el-tag
                  v-else
                  type="info"
                  size="small"
                >
                  {{ t('inventory.status.pending') }}
                </el-tag>
              </div>
            </div>
            <el-empty
              v-if="snapshots.length === 0"
              :description="t('common.messages.noData')"
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- DIFF TAB -->
      <el-tab-pane
        name="diff"
        :label="t('inventory.actions.viewDiff')"
      >
        <div
          v-loading="loadingList"
          class="list-container"
        >
          <div class="snapshot-list">
            <div
              v-for="item in diffSnapshots"
              :key="item.id"
              class="snapshot-item abnormal"
            >
              <div class="item-main">
                <div class="item-name">
                  {{ item.asset_name }}
                </div>
                <div class="item-code">
                  {{ item.asset_code }}
                </div>
                <div class="diff-reason">
                  {{ item.result_display }}
                </div>
              </div>
              <div class="item-status">
                <el-tag
                  type="warning"
                  size="small"
                >
                  {{ t('common.status.abnormal') || 'Abnormal' }}
                </el-tag>
              </div>
            </div>
            <el-empty
              v-if="diffSnapshots.length === 0"
              :description="t('common.messages.noData')"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { inventoryApi } from '@/api/inventory'
import MobileQRScanner from '@/components/mobile/MobileQRScanner.vue'
import { ElMessage } from 'element-plus'
import { Check, Warning } from '@element-plus/icons-vue'

const { t } = useI18n()
const route = useRoute()
const taskId = route.params.id as string

type ListFilter = 'all' | 'unscanned' | 'scanned'
type ScanStatus = 'success' | 'warning' | 'error'

interface TaskSnapshotItem {
  id: string | number
  asset_name: string
  asset_code: string
  is_scanned: boolean
  result_display?: string
}

interface LastScannedResult {
  status: ScanStatus
  asset_name?: string
  asset_code?: string
  message: string
}

const task = ref<any>(null)
const activeTab = ref('scan')
const scannerRef = ref<InstanceType<typeof MobileQRScanner> | null>(null)
const loadingList = ref(false)
const listFilter = ref<ListFilter>('all')
const snapshots = ref<TaskSnapshotItem[]>([])
const diffSnapshots = ref<TaskSnapshotItem[]>([])
const lastScanned = ref<LastScannedResult | null>(null)

const normalizeSnapshot = (item: any): TaskSnapshotItem => ({
  id: item?.id ?? item?.assetId ?? item?.asset_id ?? `${item?.asset_code || item?.assetCode || Date.now()}`,
  asset_name: item?.asset_name || item?.assetName || '-',
  asset_code: item?.asset_code || item?.assetCode || '-',
  is_scanned: Boolean(item?.is_scanned ?? item?.scanned),
  result_display: item?.result_display || item?.resultDisplay
})

const fetchTask = async () => {
  try {
    const res = await inventoryApi.getTask(taskId)
    task.value = res
  } catch (e) {
    console.error(e)
  }
}

const fetchSnapshots = async () => {
  loadingList.value = true
  try {
    const res = await inventoryApi.getSnapshots(taskId, {
      page: 1,
      pageSize: 1000,
      filter: listFilter.value
    })
    const items = Array.isArray(res.results) ? res.results : []
    snapshots.value = items.map(normalizeSnapshot)
  } catch (e) {
    console.error(e)
  } finally {
    loadingList.value = false
  }
}

const fetchDiffs = async () => {
  try {
    const res = await inventoryApi.getSnapshots(taskId, {
      page: 1,
      pageSize: 100,
      filter: 'abnormal'
    })
    const items = Array.isArray(res.results) ? res.results : []
    diffSnapshots.value = items.map(normalizeSnapshot)
  } catch (e) {
    console.error(e)
  }
}

const refreshData = () => {
  fetchTask()
  fetchSnapshots()
  fetchDiffs()
}

// Handle Scan
const handleScan = async (code: string) => {
  try {
    const res: any = await inventoryApi.scanAsset(taskId, { qrCode: code })
    const resultType = res?.result

    if (resultType === 'match') {
      lastScanned.value = {
        status: 'success',
        asset_name: res?.asset_name || res?.assetName,
        asset_code: res?.asset_code || res?.assetCode || code,
        message: t('common.messages.operationSuccess')
      }
    } else {
      lastScanned.value = {
        status: 'warning',
        asset_name: res?.asset_name || res?.assetName,
        asset_code: res?.asset_code || res?.assetCode || code,
        message: res?.result_display || `${t('common.status.warning')}: ${resultType || 'unknown'}`
      }
      fetchDiffs()
    }

    fetchTask()
    fetchSnapshots()
  } catch (e: any) {
    console.error(e)
    lastScanned.value = {
      status: 'error',
      message: e?.message || t('common.messages.operationFailed'),
      asset_code: code
    }
  }
}

const handleScanError = (msg: string) => {
  ElMessage.warning(msg)
}

onMounted(() => {
  refreshData()
})

</script>

<style scoped lang="scss">
.task-execute-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.task-header {
  padding: 12px 16px;
  background: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #ebedf0;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .task-info {
    h2 {
       margin: 0;
       font-size: 16px;
       font-weight: 600;
    }
    .task-status {
       font-size: 12px;
       color: #909399;
    }
  }
}

.task-progress {
  background: white;
  padding: 12px 16px;
  margin-bottom: 8px;

  .progress-stats {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #606266;
    margin-bottom: 4px;
    font-weight: 500;
  }
}

.execute-tabs {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
  
  :deep(.el-tabs__content) {
     flex: 1;
     overflow: hidden;
     position: relative;
  }
  :deep(.el-tab-pane) {
     height: 100%;
     overflow-y: auto;
  }
}

.scan-container {
   height: 100%;
   display: flex;
   flex-direction: column;
}

.scanner-wrapper {
   flex: 1;
   background: #000;
   position: relative;
   overflow: hidden;
}

.last-scan-card {
   background: white;
   padding: 16px;
   border-top: 1px solid #ebedf0;
   display: flex;
   align-items: center;
   gap: 12px;
   
   .scan-status {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: white;
      
      &.success { background-color: #67C23A; }
      &.warning { background-color: #E6A23C; }
      &.error { background-color: #F56C6C; }
   }
   
   .scan-info {
      flex: 1;
      .asset-name { font-weight: 600; font-size: 14px; margin: 0; }
      .asset-code { font-size: 12px; color: #909399; margin: 2px 0 0; }
      .scan-msg { font-size: 12px; color: #606266; margin: 4px 0 0; }
   }
}

.list-container {
  padding: 12px;
  .filter-bar {
     margin-bottom: 12px;
     text-align: center;
  }
}

.snapshot-item {
   background: white;
   padding: 12px;
   border-radius: 8px;
   margin-bottom: 8px;
   display: flex;
   justify-content: space-between;
   align-items: center;
   border: 1px solid #ebedf0;
   
   &.scanned {
     background-color: #f0f9eb;
     border-color: #e1f3d8;
   }
   
   &.abnormal {
     background-color: #fdf6ec;
     border-color: #faecd8;
   }
   
   .item-main {
      .item-name { font-weight: 500; font-size: 14px; margin-bottom: 4px; }
      .item-code { font-size: 12px; color: #909399; }
      .diff-reason { font-size: 12px; color: #F56C6C; margin-top: 4px; }
   }
}
</style>
