# Phase 4.1: QR码扫描盘点 - 前端实现

## 概述

前端实现二维码扫描组件、盘点执行页面、资产标签打印等功能。

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

## 页面结构

```
src/views/inventory/
├── TaskList.vue           # 盘点任务列表
├── TaskCreate.vue         # 创建盘点任务
├── TaskExecute.vue        # 执行盘点任务
├── TaskDetail.vue         # 任务详情
└── components/
    ├── QRScanner.vue      # 二维码扫描器
    ├── ScanResult.vue     # 扫描结果卡片
    ├── InventoryProgress.vue # 盘点进度
    ├── AssetList.vue      # 资产列表（已盘/未盘）
    └── LabelPreview.vue   # 标签预览
```

---

## 1. 二维码扫描器组件

```vue
<!-- src/components/inventory/QRScanner.vue -->
<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { BrowserMultiFormatReader } from '@zxing/library'
import { getAssetByCode } from '@/api/assets'

const props = defineProps({
  taskId: {
    type: [String, Number],
    default: null
  },
  continuous: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['scanned', 'error'])

// 视频相关
const videoRef = ref(null)
const canvasRef = ref(null)
const scanning = ref(false)
const codeReader = ref(null)

// 扫描结果
const scannedAsset = ref(null)
const scanHistory = ref([])

// 手动输入
const manualCode = ref('')
const manualInputVisible = ref(false)

// 摄像头列表
const videoDevices = ref([])
const selectedDeviceId = ref('')

// 初始化
onMounted(async () => {
  await initCamera()
})

onUnmounted(() => {
  stopScan()
})

// 初始化摄像头
const initCamera = async () => {
  try {
    codeReader.value = new BrowserMultiFormatReader()
    const devices = await codeReader.value.listVideoInputDevices()
    videoDevices.value = devices

    if (devices.length > 0) {
      selectedDeviceId.value = devices[0].deviceId
    }
  } catch (error) {
    console.error('摄像头初始化失败', error)
    emit('error', '无法访问摄像头')
  }
}

// 开始扫描
const startScan = async () => {
  if (!selectedDeviceId.value) {
    emit('error', '未检测到摄像头设备')
    return
  }

  try {
    await codeReader.value.decodeFromVideoDevice(
      selectedDeviceId.value,
      videoRef.value,
      (result, error) => {
        if (result) {
          handleScanResult(result.text)
        }
      }
    )
    scanning.value = true
  } catch (error) {
    emit('error', '无法启动摄像头: ' + error.message)
  }
}

// 停止扫描
const stopScan = () => {
  if (codeReader.value) {
    codeReader.value.reset()
  }
  scanning.value = false
}

// 切换摄像头
const switchCamera = async () => {
  stopScan()
  const currentIndex = videoDevices.value.findIndex(
    d => d.deviceId === selectedDeviceId.value
  )
  const nextIndex = (currentIndex + 1) % videoDevices.value.length
  selectedDeviceId.value = videoDevices.value[nextIndex].deviceId
  await startScan()
}

// 处理扫描结果
const handleScanResult = async (qrData) => {
  try {
    // 解析二维码数据
    const data = JSON.parse(qrData)

    if (data.type !== 'asset') {
      emit('error', '请扫描资产二维码')
      return
    }

    // 验证校验和
    const calculatedChecksum = generateChecksum(data)
    if (data.checksum !== calculatedChecksum) {
      emit('error', '二维码无效')
      return
    }

    // 获取资产信息
    const asset = await getAssetByCode(data.asset_code)
    scannedAsset.value = asset

    // 播放提示音
    playBeep()

    // 震动反馈
    if (navigator.vibrate) {
      navigator.vibrate(200)
    }

    // 触发事件
    emit('scanned', asset)

    // 添加到历史
    scanHistory.value.unshift({
      ...asset,
      scannedAt: new Date().toISOString()
    })

    // 如果不是连续扫描，则停止
    if (!props.continuous) {
      stopScan()
    }

  } catch (error) {
    emit('error', error.message || '无效的二维码')
  }
}

// 手动输入
const handleManualInput = async () => {
  if (!manualCode.value.trim()) {
    return
  }

  try {
    const asset = await getAssetByCode(manualCode.value.trim())
    scannedAsset.value = asset
    emit('scanned', asset)
    manualCode.value = ''
    manualInputVisible.value = false
  } catch (error) {
    emit('error', '未找到该资产')
  }
}

// 生成校验和
const generateChecksum = (data) => {
  const str = `${data.asset_id}:${data.asset_code}:${data.org_id}`
  // 简化实现
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return Math.abs(hash).toString(16).padStart(8, '0').slice(0, 8)
}

// 播放提示音
const playBeep = () => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  const oscillator = audioContext.createOscillator()
  const gainNode = audioContext.createGain()

  oscillator.connect(gainNode)
  gainNode.connect(audioContext.destination)

  oscillator.frequency.value = 1000
  oscillator.type = 'sine'

  gainNode.gain.setValueAtTime(0.1, audioContext.currentTime)

  oscillator.start()
  oscillator.stop(audioContext.currentTime + 0.15)
}

// 继续扫描
const continueScan = () => {
  scannedAsset.value = null
  if (!scanning.value) {
    startScan()
  }
}
</script>

<template>
  <div class="qr-scanner">
    <!-- 扫描区域 -->
    <div class="scanner-container" v-if="!scannedAsset">
      <!-- 视频预览 -->
      <div class="video-container" ref="videoContainer">
        <video
          ref="videoRef"
          muted
          playsinline
          :class="{ active: scanning }"
        ></video>

        <!-- 扫描框 -->
        <div class="scan-overlay" v-if="scanning">
          <div class="scan-corner corner-tl"></div>
          <div class="scan-corner corner-tr"></div>
          <div class="scan-corner corner-bl"></div>
          <div class="scan-corner corner-br"></div>
          <div class="scan-line"></div>
          <div class="scan-tip">将二维码放入框内</div>
        </div>

        <!-- 未启动时的占位 -->
        <div class="camera-placeholder" v-else>
          <el-icon :size="60"><Camera /></el-icon>
          <p>点击下方按钮启动摄像头</p>
        </div>
      </div>

      <!-- 控制按钮 -->
      <div class="scanner-controls">
        <el-button
          v-if="!scanning"
          type="primary"
          size="large"
          :icon="VideoCamera"
          @click="startScan"
        >
          启动扫描
        </el-button>

        <template v-else>
          <el-button
            size="large"
            :icon="RefreshRight"
            @click="switchCamera"
            v-if="videoDevices.length > 1"
          >
            切换摄像头
          </el-button>
          <el-button
            type="danger"
            size="large"
            :icon="VideoPause"
            @click="stopScan"
          >
            停止扫描
          </el-button>
        </template>

        <el-button
          size="large"
          :icon="Edit"
          @click="manualInputVisible = true"
        >
          手动输入
        </el-button>
      </div>

      <!-- 扫描历史 -->
      <div class="scan-history" v-if="scanHistory.length > 0">
        <div class="history-header">
          <span>扫描历史 ({{ scanHistory.length }})</span>
        </div>
        <div class="history-list">
          <div
            v-for="(item, index) in scanHistory.slice(0, 5)"
            :key="index"
            class="history-item"
          >
            <span class="asset-code">{{ item.asset_code }}</span>
            <span class="scan-time">{{ formatTime(item.scannedAt) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 扫描结果 -->
    <div class="scan-result" v-else>
      <el-card>
        <template #header>
          <div class="result-header">
            <div class="success-icon">
              <el-icon color="#67c23a" :size="32"><CircleCheck /></el-icon>
            </div>
            <span class="result-title">扫描成功</span>
            <el-button
              text
              type="primary"
              @click="continueScan"
            >
              继续扫描
            </el-button>
          </div>
        </template>

        <ScanResult
          :asset="scannedAsset"
          :task-id="taskId"
          @confirmed="handleConfirmed"
          @continue="continueScan"
        />
      </el-card>
    </div>

    <!-- 手动输入对话框 -->
    <el-dialog
      v-model="manualInputVisible"
      title="手动输入资产编码"
      width="400px"
    >
      <el-input
        v-model="manualCode"
        placeholder="请输入资产编码"
        clearable
        @keyup.enter="handleManualInput"
        autofocus
      >
        <template #prepend>
          <el-icon><Document /></el-icon>
        </template>
      </el-input>

      <template #footer>
        <el-button @click="manualInputVisible = false">取消</el-button>
        <el-button type="primary" @click="handleManualInput">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.qr-scanner {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
}

.video-container {
  position: relative;
  width: 100%;
  height: 400px;
  background: #000;
  border-radius: 16px;
  overflow: hidden;

  video {
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.3;

    &.active {
      opacity: 1;
    }
  }
}

.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  .scan-corner {
    position: absolute;
    width: 60px;
    height: 60px;
    border: 3px solid #00ff00;

    &.corner-tl {
      top: 80px;
      left: 50%;
      transform: translateX(-50%);
      border-right: none;
      border-bottom: none;
    }

    &.corner-tr {
      top: 80px;
      left: 50%;
      transform: translateX(-50%);
      border-left: none;
      border-bottom: none;
    }

    &.corner-bl {
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      border-right: none;
      border-top: none;
    }

    &.corner-br {
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      border-left: none;
      border-top: none;
    }
  }

  .scan-line {
    position: absolute;
    top: 80px;
    left: 50%;
    transform: translateX(-50%);
    width: 240px;
    height: 2px;
    background: linear-gradient(to right, transparent, #00ff00, transparent);
    animation: scanMove 2s infinite;
  }

  .scan-tip {
    position: absolute;
    bottom: 60px;
    left: 50%;
    transform: translateX(-50%);
    color: white;
    font-size: 14px;
    white-space: nowrap;
  }
}

@keyframes scanMove {
  0%, 100% { top: 80px; }
  50% { top: 300px; }
}

.camera-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: rgba(255, 255, 255, 0.6);

  p {
    margin-top: 16px;
    font-size: 14px;
  }
}

.scanner-controls {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  flex-wrap: wrap;
}

.scan-history {
  margin-top: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;

  .history-header {
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 12px;
  }

  .history-list {
    .history-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #ebeef5;

      &:last-child {
        border-bottom: none;
      }

      .asset-code {
        font-family: 'Monaco', monospace;
        color: #303133;
      }

      .scan-time {
        color: #909399;
        font-size: 12px;
      }
    }
  }
}

.result-header {
  display: flex;
  align-items: center;
  gap: 12px;

  .success-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: #f0f9ff;
    border-radius: 50%;
  }

  .result-title {
    flex: 1;
    font-size: 16px;
    font-weight: 500;
  }
}
</style>
```

---

## 2. 扫描结果组件

```vue
<!-- src/components/inventory/ScanResult.vue -->
<script setup>
import { ref, computed } from 'vue'
import { recordInventoryScan } from '@/api/inventory'

const props = defineProps({
  asset: {
    type: Object,
    required: true
  },
  taskId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['confirmed', 'continue'])

// 表单数据
const formData = ref({
  status: 'normal',
  actualLocation: '',
  photos: [],
  remark: ''
})

const submitting = ref(false)

// 状态选项
const statusOptions = [
  { label: '正常', value: 'normal', type: 'success' },
  { label: '位置变更', value: 'location_changed', type: 'warning' },
  { label: '损坏', value: 'damaged', type: 'danger' },
  { label: '丢失', value: 'missing', type: 'info' }
]

// 是否显示位置选择
const showLocationSelect = computed(() => {
  return formData.value.status === 'location_changed'
})

// 提交记录
const handleSubmit = async () => {
  submitting.value = true
  try {
    await recordInventoryScan(props.taskId, {
      asset_id: props.asset.id,
      scan_method: 'qr',
      ...formData.value
    })

    emit('confirmed', props.asset)
  } catch (error) {
    // 错误处理
  } finally {
    submitting.value = false
  }
}

// 获取位置变更后的实际位置
const handleLocationChange = (location) => {
  formData.value.actualLocation = location.name
}
</script>

<template>
  <div class="scan-result">
    <!-- 资产信息 -->
    <el-descriptions :column="2" border>
      <el-descriptions-item label="资产编码">
        <span class="asset-code">{{ asset.asset_code }}</span>
      </el-descriptions-item>
      <el-descriptions-item label="资产名称">
        {{ asset.asset_name }}
      </el-descriptions-item>
      <el-descriptions-item label="资产分类">
        {{ asset.asset_category?.name }}
      </el-descriptions-item>
      <el-descriptions-item label="资产状态">
        <el-tag :type="getAssetStatusType(asset.asset_status)">
          {{ getAssetStatusLabel(asset.asset_status) }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="保管人">
        {{ asset.custodian?.real_name || '-' }}
      </el-descriptions-item>
      <el-descriptions-item label="存放地点">
        {{ asset.location?.name || '-' }}
      </el-descriptions-item>
    </el-descriptions>

    <!-- 盘点表单 -->
    <el-form
      :model="formData"
      label-width="100px"
      class="inventory-form"
    >
      <!-- 盘点状态 -->
      <el-form-item label="盘点状态">
        <el-radio-group v-model="formData.status">
          <el-radio
            v-for="option in statusOptions"
            :key="option.value"
            :label="option.value"
            border
          >
            <el-tag :type="option.type" size="small">
              {{ option.label }}
            </el-tag>
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 实际位置（位置变更时） -->
      <el-form-item
        v-if="showLocationSelect"
        label="实际位置"
      >
        <LocationCascader
          v-model="formData.actualLocation"
          @change="handleLocationChange"
        />
      </el-form-item>

      <!-- 照片（可选） -->
      <el-form-item label="拍照">
        <ImageUploader
          v-model="formData.photos"
          :max-count="3"
        />
      </el-form-item>

      <!-- 备注 -->
      <el-form-item label="备注">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注信息..."
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <!-- 操作按钮 -->
      <el-form-item>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          确认记录
        </el-button>
        <el-button @click="emit('continue')">
          继续扫描
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped lang="scss">
.scan-result {
  .asset-code {
    font-family: 'Monaco', monospace;
    font-size: 14px;
    font-weight: 500;
  }

  .inventory-form {
    margin-top: 24px;
  }
}
</style>
```

---

## 3. 盘点执行页面

```vue
<!-- src/views/inventory/TaskExecute.vue -->
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import QRScanner from '@/components/inventory/QRScanner.vue'
import InventoryProgress from '@/components/inventory/InventoryProgress.vue'
import {
  getInventoryTask,
  getInventoryStatistics,
  completeInventory
} from '@/api/inventory'

const route = useRoute()
const router = useRouter()

const taskId = route.params.id
const task = ref(null)
const activeTab = ref('scan')
const statistics = ref({
  total: 0,
  scanned: 0,
  normal: 0,
  extra: 0,
  missing: 0,
  damaged: 0,
  progress: 0
})
const scannedAssets = ref([])
const unscannedAssets = ref([])
const loading = ref(false)

// 是否可以完成盘点
const canComplete = computed(() => {
  return statistics.value.scanned > 0
})

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const [taskRes, statsRes] = await Promise.all([
      getInventoryTask(taskId),
      getInventoryStatistics(taskId)
    ])
    task.value = taskRes
    statistics.value = statsRes
  } finally {
    loading.value = false
  }
}

// 扫描成功回调
const handleScanned = async (asset) => {
  // 刷新统计
  await fetchData()

  // 添加到已盘列表
  scannedAssets.value.unshift({
    ...asset,
    scan_time: new Date().toISOString(),
    scan_status: 'normal'
  })

  // 从未盘列表移除
  const index = unscannedAssets.value.findIndex(a => a.id === asset.id)
  if (index > -1) {
    unscannedAssets.value.splice(index, 1)
  }

  // 切换到已盘标签页显示
  // activeTab.value = 'scanned'
}

// 完成盘点
const handleComplete = async () => {
  const { scanned, total, extra, missing, damaged } = statistics.value

  await ElMessageBox.confirm(
    `盘点统计:\n` +
    `• 应盘: ${total} 项\n` +
    `• 已盘: ${scanned} 项\n` +
    `• 正常: ${statistics.value.normal} 项\n` +
    `• 盘盈: ${extra} 项\n` +
    `• 盘亏: ${missing} 项\n` +
    `• 损坏: ${damaged} 项\n\n` +
    `确认完成盘点？`,
    '完成盘点',
    {
      confirmButtonText: '确认完成',
      cancelButtonText: '取消',
      type: 'warning',
      dangerouslyUseHTMLString: true
    }
  )

  await completeInventory(taskId)
  router.push('/inventory/tasks')
}

// 返回
const goBack = () => {
  router.push('/inventory/tasks')
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="inventory-execute" v-loading="loading">
    <!-- 头部 -->
    <el-page-header @back="goBack">
      <template #content>
        <div class="page-header-content">
          <span>{{ task?.task_name }}</span>
          <el-tag :type="getTaskStatusType(task?.status)">
            {{ getTaskStatusLabel(task?.status) }}
          </el-tag>
        </div>
      </template>
    </el-page-header>

    <!-- 进度统计 -->
    <InventoryProgress :statistics="statistics" :task="task" />

    <!-- 主内容区 -->
    <el-card class="main-card">
      <el-tabs v-model="activeTab">
        <!-- 扫码盘点 -->
        <el-tab-pane name="scan">
          <template #label>
            <span class="tab-label">
              <el-icon><Scan /></el-icon>
              扫码盘点
            </span>
          </template>

          <QRScanner
            :task-id="taskId"
            :continuous="true"
            @scanned="handleScanned"
          />
        </el-tab-pane>

        <!-- 已盘资产 -->
        <el-tab-pane name="scanned">
          <template #label>
            <span class="tab-label">
              <el-icon><CircleCheck /></el-icon>
              已盘资产
              <el-badge
                v-if="statistics.scanned > 0"
                :value="statistics.scanned"
                type="success"
              />
            </span>
          </template>

          <AssetList
            :assets="scannedAssets"
            type="scanned"
            @refresh="fetchData"
          />
        </el-tab-pane>

        <!-- 未盘资产 -->
        <el-tab-pane name="unscanned">
          <template #label>
            <span class="tab-label">
              <el-icon><Clock /></el-icon>
              未盘资产
              <el-badge
                v-if="statistics.total - statistics.scanned > 0"
                :value="statistics.total - statistics.scanned"
                type="warning"
              />
            </span>
          </template>

          <AssetList
            :assets="unscannedAssets"
            type="unscanned"
            @refresh="fetchData"
          />
        </el-tab-pane>

        <!-- 差异列表 -->
        <el-tab-pane name="differences">
          <template #label>
            <span class="tab-label">
              <el-icon><Warning /></el-icon>
              差异列表
              <el-badge
                v-if="statistics.extra + statistics.missing + statistics.damaged > 0"
                :value="statistics.extra + statistics.missing + statistics.damaged"
                type="danger"
              />
            </span>
          </template>

          <DifferenceList :task-id="taskId" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 底部操作栏 -->
    <div class="footer-actions">
      <el-button
        type="primary"
        size="large"
        :disabled="!canComplete"
        @click="handleComplete"
      >
        <el-icon><CircleCheckFilled /></el-icon>
        完成盘点 ({{ statistics.scanned }}/{{ statistics.total }})
      </el-button>
    </div>
  </div>
</template>

<style scoped lang="scss">
.inventory-execute {
  padding: 20px;
  min-height: 100vh;
  background: #f5f7fa;

  .page-header-content {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .main-card {
    margin-top: 20px;

    .tab-label {
      display: flex;
      align-items: center;
      gap: 6px;
    }
  }

  .footer-actions {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px;
    background: white;
    border-top: 1px solid #ebeef5;
    display: flex;
    justify-content: center;
    box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
  }
}
</style>
```

---

## 4. API封装

```javascript
// src/api/inventory.js

import request from '@/utils/request'

export default {
  // 获取盘点任务列表
  getTasks(params) {
    return request({
      url: '/api/inventory/tasks/',
      method: 'get',
      params
    })
  },

  // 获取任务详情
  getTask(id) {
    return request({
      url: `/api/inventory/tasks/${id}/`,
      method: 'get'
    })
  },

  // 创建任务
  createTask(data) {
    return request({
      url: '/api/inventory/tasks/',
      method: 'post',
      data
    })
  },

  // 开始任务
  startTask(id) {
    return request({
      url: `/api/inventory/tasks/${id}/start/`,
      method: 'post'
    })
  },

  // 完成任务
  completeTask(id) {
    return request({
      url: `/api/inventory/tasks/${id}/complete/`,
      method: 'post'
    })
  },

  // 获取统计
  getStatistics(id) {
    return request({
      url: `/api/inventory/tasks/${id}/statistics/`,
      method: 'get'
    })
  },

  // 获取已盘资产
  getScannedAssets(id, params) {
    return request({
      url: `/api/inventory/tasks/${id}/scanned_assets/`,
      method: 'get',
      params
    })
  },

  // 获取未盘资产
  getUnscannedAssets(id, params) {
    return request({
      url: `/api/inventory/tasks/${id}/unscanned_assets/`,
      method: 'get',
      params
    })
  },

  // 记录扫描
  recordScan(taskId, data) {
    return request({
      url: `/api/inventory/tasks/${taskId}/record_scan/`,
      method: 'post',
      data
    })
  }
}
```

---

## 5. 路由配置

```javascript
// src/router/inventory.js

export default [
  {
    path: '/inventory',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/inventory/tasks'
      },
      {
        path: 'tasks',
        name: 'InventoryTasks',
        component: () => import('@/views/inventory/TaskList.vue'),
        meta: { title: '盘点任务', icon: 'List' }
      },
      {
        path: 'tasks/create',
        name: 'InventoryTaskCreate',
        component: () => import('@/views/inventory/TaskCreate.vue'),
        meta: { title: '创建盘点任务' }
      },
      {
        path: 'tasks/:id/execute',
        name: 'InventoryTaskExecute',
        component: () => import('@/views/inventory/TaskExecute.vue'),
        meta: { title: '执行盘点' }
      },
      {
        path: 'tasks/:id',
        name: 'InventoryTaskDetail',
        component: () => import('@/views/inventory/TaskDetail.vue'),
        meta: { title: '盘点详情' }
      }
    ]
  }
]
```

---

## 后续任务

1. Phase 4.2: 实现RFID批量盘点
2. Phase 4.3: 实现盘点快照和差异处理

---

## 移动端盘点 UI 设计

### 概述

移动端盘点是核心业务场景，需要针对手机屏幕优化交互流程，支持单手操作、离线扫描、网络容错等功能。

**设计原则**：
- 移动优先（Mobile First）
- 单手操作友好
- 网络容错（离线/弱网）
- 视觉反馈清晰
- 参考 NIIMBOT 标的系统

### 1. 移动端页面结构

```
src/views/mobile/inventory/
├── TaskList.vue              # 盘点任务列表
├── TaskDetail.vue            # 任务详情
├── ScanPage.vue              # 扫码页面
├── ScanResult.vue            # 扫描结果确认
├── OfflineQueue.vue          # 离线队列
└── InventorySummary.vue      # 盘点汇总

src/components/mobile/
├── ScanCamera.vue            # 扫码相机组件
├── ScanInput.vue             # 手动输入组件
├── AssetCard.vue             # 资产卡片
├── ProgressBar.vue           # 进度条
└── OfflineIndicator.vue      # 离线状态指示器
```

### 2. 扫码页面布局

```
┌─────────────────────────────────────┐
│ ← 盘点任务              [设置] [离线] │
├─────────────────────────────────────┤
│                                     │
│         ┌─────────────────┐         │
│         │   扫码区域      │         │
│         │                 │         │
│         │   [相机预览]    │         │
│         │                 │         │
│         └─────────────────┘         │
│                                     │
│        将二维码对准扫描框           │
│                                     │
├─────────────────────────────────────┤
│ [🔦 手电筒]  [📷 相册]  [⌨️ 手动]   │
├─────────────────────────────────────┤
│  任务进度： 150/200 (75%)           │
│  ████████████░░░░░░░░░░░░           │
├─────────────────────────────────────┤
│  今日已扫：120  正常：115  异常：5   │
└─────────────────────────────────────┘
```

### 3. 离线模式设计

**核心策略**：
- 扫描数据优先存储到本地（IndexedDB）
- 网络恢复时自动批量上传
- 离线状态清晰指示
- 上传失败自动重试

**离线队列数据结构**：
```typescript
interface OfflineQueueItem {
  id: string
  type: 'scan' | 'task_start' | 'task_complete'
  data: any
  timestamp: number
  retryCount: number
}
```

### 4. 移动端适配规范

| 元素 | 最小尺寸 | 说明 |
|------|----------|------|
| 可点击区域 | 44×44px | 符合 iOS 规范 |
| 扫描框 | 280×280px | 适应各种屏幕 |
| 按钮高度 | 48px | 方便点击 |

| 场景 | 字号 | 字重 |
|------|------|------|
| 标题 | 20px | Bold |
| 正文 | 14-16px | Regular |
| 辅助信息 | 12px | Regular |

### 5. 交互流程图

**扫描流程**：
```
打开扫描页 → 相机可用? → 启动相机/手动输入
→ 检测到码 → 解析数据 → 解析成功?
→ 显示结果确认页 → 用户确认 → 记录扫描 → 继续扫描
```

**离线处理流程**：
```
开始扫描 → 网络在线? → 上传数据 / 存入本地队列
→ 网络恢复? → 检测队列数据 → 批量上传 → 完成
```

### 6. 核心组件示例

#### ScanCamera.vue

```vue
<template>
  <div class="scan-camera">
    <video ref="videoRef" playsinline muted></video>
    <canvas ref="canvasRef" style="display:none"></canvas>

    <!-- 扫描框 -->
    <div class="scan-frame" v-if="isActive">
      <div class="scan-line"></div>
    </div>

    <!-- 扫描状态 -->
    <div class="scan-status" :class="statusClass">
      {{ statusText }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { BrowserMultiFormatReader } from '@zxing/library'

const emit = defineEmits(['detect', 'error'])
const videoRef = ref()
const codeReader = ref(null)
const isActive = ref(false)

const start = async () => {
  codeReader.value = new BrowserMultiFormatReader()
  const devices = await codeReader.value.listVideoInputDevices()
  if (devices.length > 0) {
    await codeReader.value.decodeFromVideoDevice(
      devices[0].deviceId,
      videoRef.value,
      (result, error) => {
        if (result) emit('detect', result.text)
      }
    )
    isActive.value = true
  }
}

onMounted(() => start())
onUnmounted(() => codeReader.value?.reset())
</script>
```

### 7. 兼容性要求

| 平台 | 版本要求 |
|------|----------|
| iOS Safari | 14+ |
| Android Chrome | 90+ |
| 微信浏览器 | 7.0+ |
| 钉钉浏览器 | 6.0+ |
| 飞书浏览器 | 4.0+ |
