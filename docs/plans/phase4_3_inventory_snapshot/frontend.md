# Phase 4.3: 盘点快照和差异处理 - 前端实现

## 概述

实现盘点快照管理、差异检测与处理、盘点报告等前端功能。

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

## 1. 差异列表页面

### 1.1 PC端差异列表

```
┌─────────────────────────────────────────────────────────────────┐
│  盘点差异 - PD001 3楼盘点                                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [全部] [待处理 15] [已处理] [已忽略]           [导出报告]   ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ☐  ZC001  MacBook Pro 16寸   [盘亏]       待处理            ││
│  │     资产 ZC001 未盘点到                                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ☐  ZC002  Dell显示器        [位置不符]   待处理            ││
│  │     存放地点不符: 原位置3楼A区，实际位置3楼B区               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ☐  ZC003  键盘鼠标          [损坏]       待处理            ││
│  │     资产损坏: 键盘按键失灵                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ ☑  ZC004  耳机              [保管人不符]  已处理           ││
│  │     保管人不符: 原保管人张三，实际保管人李四                  ││
│  │     处理方案: 更新保管人为李四                               ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 批量操作: [批量处理] [批量忽略]           [共 15 条差异]    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Vue组件

```vue
<!-- src/views/inventory/DifferenceList.vue -->

<template>
  <div class="difference-list-page">
    <el-page-header @back="goBack" :title="taskName">
      <template #extra>
        <el-button type="primary" :icon="Download" @click="handleExport">
          导出报告
        </el-button>
      </template>
    </el-page-header>

    <!-- 筛选标签 -->
    <el-tabs v-model="activeStatus" @tab-change="handleTabChange">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane :label="`待处理 ${pendingCount}`" name="pending" />
      <el-tab-pane label="已处理" name="resolved" />
      <el-tab-pane label="已忽略" name="ignored" />
    </el-tabs>

    <!-- 差异列表 -->
    <div class="difference-list">
      <div
        v-for="diff in differences"
        :key="diff.id"
        :class="['difference-item', `type-${diff.difference_type}`, `status-${diff.status}`]"
      >
        <el-checkbox
          v-model="selectedIds"
          :label="diff.id"
          @change="handleSelectChange"
        />

        <div class="difference-content">
          <div class="difference-header">
            <span class="asset-code">{{ diff.asset_code }}</span>
            <span class="asset-name">{{ diff.asset_name }}</span>
            <el-tag :type="getDifferenceTypeTag(diff.difference_type)">
              {{ diff.difference_type_display }}
            </el-tag>
            <el-tag :type="getStatusTag(diff.status)">
              {{ diff.status_display }}
            </el-tag>
          </div>

          <div class="difference-description">
            {{ diff.description }}
          </div>

          <div v-if="diff.status === 'resolved'" class="difference-resolution">
            <span class="label">处理方案:</span>
            <span class="content">{{ diff.resolution }}</span>
            <span class="resolver">处理人: {{ diff.resolved_by_name }}</span>
          </div>

          <div v-if="diff.status === 'pending'" class="difference-actions">
            <el-button size="small" @click="handleResolve(diff)">
              处理
            </el-button>
            <el-button size="small" type="info" @click="handleIgnore(diff)">
              忽略
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-actions">
      <span>已选择 {{ selectedIds.length }} 项</span>
      <el-button type="primary" @click="handleBatchResolve">
        批量处理
      </el-button>
      <el-button @click="handleBatchIgnore">
        批量忽略
      </el-button>
    </div>

    <!-- 处理对话框 -->
    <DifferenceResolveDialog
      v-model="resolveDialogVisible"
      :difference="currentDifference"
      @confirm="handleResolveConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import DifferenceResolveDialog from '@/components/inventory/DifferenceResolveDialog.vue'
import { inventoryApi } from '@/api/inventory'

const route = useRoute()
const router = useRouter()

const taskId = ref(Number(route.query.taskId))
const taskName = ref(route.query.taskName || '盘点任务')
const activeStatus = ref('pending')
const differences = ref([])
const selectedIds = ref<number[]>([])
const resolveDialogVisible = ref(false)
const currentDifference = ref(null)

const pendingCount = computed(() => {
  return differences.value.filter(d => d.status === 'pending').length
})

const loadDifferences = async () => {
  try {
    const { data } = await inventoryApi.getDifferences({
      task_id: taskId.value,
      status: activeStatus.value === 'all' ? undefined : activeStatus.value
    })
    differences.value = data.results
  } catch (error) {
    ElMessage.error('加载差异列表失败')
  }
}

const handleTabChange = () => {
  loadDifferences()
}

const handleResolve = (diff: any) => {
  currentDifference.value = diff
  resolveDialogVisible.value = true
}

const handleResolveConfirm = async (resolution: string, updateAsset: boolean) => {
  try {
    await inventoryApi.resolveDifference(currentDifference.value.id, {
      resolution,
      update_asset: updateAsset
    })
    ElMessage.success('差异已处理')
    resolveDialogVisible.value = false
    loadDifferences()
  } catch (error) {
    ElMessage.error('处理失败')
  }
}

const handleIgnore = async (diff: any) => {
  try {
    await ElMessageBox.confirm('确认忽略此差异？', '提示')
    await inventoryApi.ignoreDifference(diff.id)
    ElMessage.success('已忽略')
    loadDifferences()
  } catch (error) {
    // 用户取消
  }
}

const handleBatchResolve = async () => {
  // 批量处理逻辑
  const { value } = await ElMessageBox.prompt('请输入批量处理方案:', '批量处理')
  try {
    await inventoryApi.batchResolve({
      difference_ids: selectedIds.value,
      resolution: value
    })
    ElMessage.success('批量处理成功')
    selectedIds.value = []
    loadDifferences()
  } catch (error) {
    ElMessage.error('批量处理失败')
  }
}

const handleExport = async () => {
  try {
    const response = await inventoryApi.exportReport(taskId.value, 'pdf')
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `inventory_report_${taskId.value}.pdf`)
    document.body.appendChild(link)
    link.click()
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  loadDifferences()
})
</script>

<style scoped lang="scss">
.difference-list-page {
  padding: 20px;
}

.difference-item {
  display: flex;
  padding: 16px;
  margin-bottom: 12px;
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid #e4e7ed;
  transition: all 0.3s;

  &.type-missing {
    border-left-color: #f56c6c;
  }

  &.type-location_mismatch {
    border-left-color: #e6a23c;
  }

  &.type-damaged {
    border-left-color: #f56c6c;
  }

  &.type-custodian_mismatch {
    border-left-color: #409eff;
  }
}

.difference-content {
  flex: 1;
  margin-left: 12px;
}

.difference-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;

  .asset-code {
    font-weight: bold;
    color: #303133;
  }

  .asset-name {
    color: #606266;
  }
}

.difference-description {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.difference-resolution {
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;

  .label {
    color: #909399;
  }

  .content {
    color: #67c23a;
    margin: 0 8px;
  }

  .resolver {
    color: #909399;
  }
}

.batch-actions {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 20px;
  background: #fff;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
```

---

## 2. 差异处理对话框

```vue
<!-- src/components/inventory/DifferenceResolveDialog.vue -->

<template>
  <el-dialog
    v-model="visible"
    :title="`处理差异 - ${difference?.asset_code}`"
    width="600px"
    @close="handleClose"
  >
    <div v-if="difference" class="resolve-form">
      <!-- 差异详情 -->
      <div class="difference-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="资产编码">
            {{ difference.asset_code }}
          </el-descriptions-item>
          <el-descriptions-item label="资产名称">
            {{ difference.asset_name }}
          </el-descriptions-item>
          <el-descriptions-item label="差异类型">
            <el-tag :type="getDifferenceTypeTag(difference.difference_type)">
              {{ difference.difference_type_display }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            {{ difference.status_display }}
          </el-descriptions-item>
          <el-descriptions-item label="差异描述" :span="2">
            {{ difference.description }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 处理表单 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="resolve-form-content"
      >
        <el-form-item label="处理方案" prop="resolution">
          <el-input
            v-model="form.resolution"
            type="textarea"
            :rows="4"
            placeholder="请输入处理方案..."
          />
        </el-form-item>

        <el-form-item label="更新资产" prop="updateAsset">
          <el-switch
            v-model="form.updateAsset"
            active-text="是"
            inactive-text="否"
          />
          <span class="form-tip">
            根据处理方案同步更新资产信息（位置、保管人、状态等）
          </span>
        </el-form-item>

        <!-- 根据差异类型显示额外选项 -->
        <template v-if="difference.difference_type === 'location_mismatch'">
          <el-form-item label="新位置">
            <el-cascader
              v-model="form.newLocation"
              :options="locationOptions"
              placeholder="选择新位置"
            />
          </el-form-item>
        </template>

        <template v-if="difference.difference_type === 'custodian_mismatch'">
          <el-form-item label="新保管人">
            <user-select v-model="form.newCustodian" />
          </el-form-item>
        </template>

        <template v-if="difference.difference_type === 'damaged'">
          <el-form-item label="资产状态">
            <el-select v-model="form.newAssetStatus">
              <el-option label="需维修" value="repair" />
              <el-option label="已报废" value="scrapped" />
              <el-option label="可继续使用" value="normal" />
            </el-select>
          </el-form-item>
        </template>
      </el-form>
    </div>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleConfirm">
        确认处理
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import UserSelect from '@/components/common/UserSelect.vue'
import { inventoryApi } from '@/api/inventory'

interface Props {
  modelValue: boolean
  difference: any
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', resolution: string, updateAsset: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = ref({
  resolution: '',
  updateAsset: true,
  newLocation: null,
  newCustodian: null,
  newAssetStatus: ''
})

const rules = {
  resolution: [
    { required: true, message: '请输入处理方案', trigger: 'blur' }
  ]
}

const locationOptions = ref([])

const handleConfirm = () => {
  // 组合处理方案文本
  let resolutionText = form.value.resolution

  if (form.value.newLocation) {
    resolutionText += `\n位置: ${form.value.newLocation.join('/')}`
  }
  if (form.value.newCustodian) {
    resolutionText += `\n保管人: ${form.value.newCustodian}`
  }
  if (form.value.newAssetStatus) {
    resolutionText += `\n状态: ${form.value.newAssetStatus}`
  }

  emit('confirm', resolutionText, form.value.updateAsset)
}

const handleClose = () => {
  visible.value = false
  form.value = {
    resolution: '',
    updateAsset: true,
    newLocation: null,
    newCustodian: null,
    newAssetStatus: ''
  }
}
</script>
```

---

## 3. 盘点报告页面

```vue
<!-- src/views/inventory/InventoryReport.vue -->

<template>
  <div class="inventory-report-page">
    <el-page-header @back="goBack" title="盘点报告">
      <template #extra>
        <el-button :icon="Download" @click="handleExport('pdf')">
          导出PDF
        </el-button>
        <el-button :icon="Download" @click="handleExport('excel')">
          导出Excel
        </el-button>
      </template>
    </el-page-header>

    <!-- 报告概览 -->
    <div class="report-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-label">应盘资产</div>
            <div class="stat-value">{{ report.total_assets }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card success">
            <div class="stat-label">已盘资产</div>
            <div class="stat-value">{{ report.scanned_assets }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card warning">
            <div class="stat-label">差异资产</div>
            <div class="stat-value">{{ report.difference_count }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card info">
            <div class="stat-label">盘点进度</div>
            <div class="stat-value">{{ report.progress }}%</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 差异统计图表 -->
    <div class="report-charts">
      <el-card>
        <template #header>
          <span>差异类型分布</span>
        </template>
        <div ref="pieChartRef" style="height: 300px" />
      </el-card>
    </div>

    <!-- 差异详情 -->
    <el-card class="difference-table-card">
      <template #header>
        <span>差异明细</span>
      </template>
      <el-table :data="report.differences" border stripe>
        <el-table-column prop="asset_code" label="资产编码" width="120" />
        <el-table-column prop="asset_name" label="资产名称" />
        <el-table-column prop="difference_type_display" label="差异类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getDifferenceTypeTag(row.difference_type)">
              {{ row.difference_type_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="差异描述" />
        <el-table-column prop="status_display" label="处理状态" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { inventoryApi } from '@/api/inventory'

const route = useRoute()
const taskId = ref(Number(route.params.taskId))
const pieChartRef = ref<HTMLElement>()

const report = ref({
  total_assets: 0,
  scanned_assets: 0,
  difference_count: 0,
  progress: 0,
  differences: []
})

const loadReport = async () => {
  const { data } = await inventoryApi.getReport(taskId.value)
  report.value = data

  // 渲染图表
  renderChart(data)
}

const renderChart = (data: any) => {
  const chart = echarts.init(pieChartRef.value!)
  chart.setOption({
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '差异类型',
        type: 'pie',
        radius: '50%',
        data: data.difference_by_type,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  })
}

const handleExport = async (format: 'pdf' | 'excel') => {
  const response = await inventoryApi.exportReport(taskId.value, format)
  // 处理文件下载
}

onMounted(() => {
  loadReport()
})
</script>

<style scoped lang="scss">
.report-overview {
  margin: 20px 0;

  .stat-card {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);

    .stat-label {
      color: #909399;
      font-size: 14px;
      margin-bottom: 8px;
    }

    .stat-value {
      font-size: 32px;
      font-weight: bold;
      color: #303133;
    }

    &.success .stat-value {
      color: #67c23a;
    }

    &.warning .stat-value {
      color: #e6a23c;
    }

    &.info .stat-value {
      color: #409eff;
    }
  }
}

.report-charts {
  margin: 20px 0;
}
</style>
```

---

## 4. 移动端差异处理

### 4.1 移动端差异列表

```vue
<!-- src/views/mobile/inventory/DifferenceList.vue -->

<template>
  <div class="mobile-difference-list">
    <van-nav-bar
      title="盘点差异"
      left-arrow
      @click-left="goBack"
    >
      <template #right>
        <van-icon :name="FilterO" @click="showFilter = true" />
      </template>
    </van-nav-bar>

    <!-- 筛选标签 -->
    <van-tabs v-model:active="activeStatus" @change="loadDifferences">
      <van-tab title="全部" name="all" />
      <van-tab title="待处理" name="pending" />
      <van-tab title="已处理" name="resolved" />
    </van-tabs>

    <!-- 差异列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        @load="loadDifferences"
      >
        <van-cell
          v-for="diff in differences"
          :key="diff.id"
          is-link
          @click="handleDetail(diff)"
        >
          <template #title>
            <div class="difference-title">
              <span class="asset-code">{{ diff.asset_code }}</span>
              <van-tag :type="getDifferenceTypeTag(diff.difference_type)">
                {{ diff.difference_type_display }}
              </van-tag>
            </div>
          </template>
          <template #label>
            <div class="difference-desc">{{ diff.description }}</div>
            <van-tag v-if="diff.status === 'pending'" type="danger">待处理</van-tag>
            <van-tag v-else type="success">已处理</van-tag>
          </template>
        </van-cell>
      </van-list>
    </van-pull-refresh>

    <!-- 筛选弹窗 -->
    <van-popup v-model:show="showFilter" position="top" :style="{ height: '40%' }">
      <van-form @submit="handleFilter">
        <van-cell-group inset>
          <van-field
            v-model="filter.keyword"
            label="关键词"
            placeholder="资产编码/名称"
          />
          <van-field name="type" label="差异类型">
            <template #input>
              <van-radio-group v-model="filter.type" direction="horizontal">
                <van-radio name="">全部</van-radio>
                <van-radio name="missing">盘亏</van-radio>
                <van-radio name="location_mismatch">位置不符</van-radio>
              </van-radio-group>
            </template>
          </van-field>
        </van-cell-group>
        <div class="filter-actions">
          <van-button block type="primary" native-type="submit">应用筛选</van-button>
        </div>
      </van-form>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { FilterO } from '@vant/icons-vue'
import { inventoryApi } from '@/api/inventory'

const activeStatus = ref('pending')
const differences = ref([])
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const showFilter = ref(false)
const filter = ref({
  keyword: '',
  type: ''
})

const loadDifferences = async () => {
  const { data } = await inventoryApi.getDifferences({
    task_id: taskId.value,
    status: activeStatus.value === 'all' ? undefined : activeStatus.value,
    keyword: filter.value.keyword,
    difference_type: filter.value.type
  })
  differences.value = data.results
  loading.value = false
  finished.value = true
}

const onRefresh = async () => {
  await loadDifferences()
  refreshing.value = false
}

const handleDetail = (diff: any) => {
  // 跳转到差异详情页
  router.push({
    path: '/mobile/difference/detail',
    query: { id: diff.id }
  })
}
</script>
```

### 4.2 移动端差异详情

```vue
<!-- src/views/mobile/inventory/DifferenceDetail.vue -->

<template>
  <div class="mobile-difference-detail">
    <van-nav-bar
      title="差异详情"
      left-arrow
      @click-left="goBack"
    />

    <van-cell-group inset title="资产信息">
      <van-cell title="资产编码" :value="difference.asset_code" />
      <van-cell title="资产名称" :value="difference.asset_name" />
    </van-cell-group>

    <van-cell-group inset title="差异信息">
      <van-cell title="差异类型">
        <template #value>
          <van-tag :type="getDifferenceTypeTag(difference.difference_type)">
            {{ difference.difference_type_display }}
          </van-tag>
        </template>
      </van-cell>
      <van-cell title="差异描述" :value="difference.description" />
      <van-cell title="状态">
        <template #value>
          <van-tag :type="getStatusTag(difference.status)">
            {{ difference.status_display }}
          </van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <van-cell-group v-if="difference.status === 'resolved'" inset title="处理信息">
      <van-cell title="处理方案" :value="difference.resolution" />
      <van-cell title="处理人" :value="difference.resolved_by_name" />
      <van-cell title="处理时间" :value="formatDate(difference.resolved_at)" />
    </van-cell-group>

    <div v-if="difference.status === 'pending'" class="action-buttons">
      <van-button block type="primary" @click="showResolveDialog = true">
        处理差异
      </van-button>
      <van-button block @click="handleIgnore">
        忽略差异
      </van-button>
    </div>

    <!-- 处理对话框 -->
    <van-dialog
      v-model:show="showResolveDialog"
      title="处理差异"
      show-cancel-button
      @confirm="handleResolve"
    >
      <van-field
        v-model="resolution"
        type="textarea"
        label="处理方案"
        placeholder="请输入处理方案"
        rows="3"
      />
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { inventoryApi } from '@/api/inventory'

const route = useRoute()
const router = useRouter()
const differenceId = ref(Number(route.params.id))

const difference = ref({})
const resolution = ref('')
const showResolveDialog = ref(false)

const loadDetail = async () => {
  const { data } = await inventoryApi.getDifferenceDetail(differenceId.value)
  difference.value = data
}

const handleResolve = async () => {
  await inventoryApi.resolveDifference(differenceId.value, {
    resolution: resolution.value,
    update_asset: true
  })
  showToast('处理成功')
  loadDetail()
}

const handleIgnore = async () => {
  await inventoryApi.ignoreDifference(differenceId.value)
  showToast('已忽略')
  router.back()
}

onMounted(() => {
  loadDetail()
})
</script>
```

---

## 5. API封装

```typescript
// src/api/inventory.ts

import request from '@/utils/request'

export const inventoryApi = {
  // 获取差异列表
  getDifferences(params: {
    task_id?: number
    status?: string
    difference_type?: string
    keyword?: string
    page?: number
    page_size?: number
  }) {
    return request.get('/api/inventory/differences/by_task/', { params })
  },

  // 获取差异详情
  getDifferenceDetail(id: number) {
    return request.get(`/api/inventory/differences/${id}/`)
  },

  // 处理差异
  resolveDifference(id: number, data: {
    resolution: string
    update_asset?: boolean
  }) {
    return request.post(`/api/inventory/differences/${id}/resolve/`, data)
  },

  // 忽略差异
  ignoreDifference(id: number) {
    return request.post(`/api/inventory/differences/${id}/ignore/`)
  },

  // 批量处理
  batchResolve(data: {
    difference_ids: number[]
    resolution: string
  }) {
    return request.post('/api/inventory/differences/batch_resolve/', data)
  },

  // 获取盘点报告
  getReport(taskId: number) {
    return request.get(`/api/inventory/differences/report/${taskId}/`)
  },

  // 导出报告
  exportReport(taskId: number, format: 'pdf' | 'excel') {
    return request.get(`/api/inventory/differences/report/${taskId}/`, {
      params: { format },
      responseType: 'blob'
    })
  }
}
```

---

## 后续任务

1. Phase 5.1: 实现万达宝M18采购对接
2. Phase 5.2: 实现万达宝M18财务对接
