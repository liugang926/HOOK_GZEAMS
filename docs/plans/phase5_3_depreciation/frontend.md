# Phase 5.3: 折旧自动计算 - 前端实现

## 概述

实现折旧管理前端页面，包括折旧记录查询、折旧报表、资产折旧详情等功能。

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

## 1. 折旧记录列表页

### DepreciationList.vue

```vue
<template>
  <div class="depreciation-list">
    <el-card>
      <!-- 搜索筛选 -->
      <el-form :model="queryForm" :inline="true" class="search-form">
        <el-form-item label="资产编码">
          <el-input v-model="queryForm.asset_code" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="折旧期间">
          <el-date-picker
            v-model="queryForm.period"
            type="month"
            format="YYYY-MM"
            value-format="YYYY-MM"
            placeholder="选择月份"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已审核" value="approved" />
            <el-option label="已过账" value="posted" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="handleCalculate" :loading="calculating">
          计算当月折旧
        </el-button>
        <el-button @click="handleExport">导出</el-button>
      </div>

      <!-- 折旧记录表格 -->
      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="asset.asset_code" label="资产编码" width="140" />
        <el-table-column prop="asset.asset_name" label="资产名称" width="180" />
        <el-table-column prop="period" label="折旧期间" width="100" />
        <el-table-column prop="depreciation_method" label="折旧方法" width="120">
          <template #default="{ row }">
            <el-tag>{{ getMethodName(row.depreciation_method) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="purchase_price" label="原值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.purchase_price) }}</template>
        </el-table-column>
        <el-table-column prop="depreciation_amount" label="本月折旧" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.depreciation_amount) }}</template>
        </el-table-column>
        <el-table-column prop="accumulated_depreciation" label="累计折旧" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.accumulated_depreciation) }}</template>
        </el-table-column>
        <el-table-column prop="net_value" label="净值" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.net_value) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusName(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">详情</el-button>
            <el-button link type="primary" @click="handlePost(row)" v-if="row.status === 'approved'">
              过账
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        @current-change="fetchData"
        @size-change="fetchData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { depreciationApi } from '@/api/assets/depreciation'

const queryForm = reactive({
  asset_code: '',
  period: '',
  status: ''
})

const tableData = ref([])
const loading = ref(false)
const calculating = ref(false)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 折旧方法映射
const methodMap = {
  straight_line: '直线法',
  double_declining: '双倍余额递减法',
  sum_of_years: '年数总和法'
}

// 状态映射
const statusMap = {
  draft: '草稿',
  submitted: '已提交',
  approved: '已审核',
  posted: '已过账'
}

const statusTypeMap = {
  draft: 'info',
  submitted: 'warning',
  approved: 'success',
  posted: ''
}

const getMethodName = (method: string) => methodMap[method] || method
const getStatusName = (status: string) => statusMap[status] || status
const getStatusType = (status: string) => statusTypeMap[status] || ''

const formatMoney = (val: number) => {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await depreciationApi.list({
      ...queryForm,
      page: pagination.page,
      size: pagination.size
    })
    tableData.value = data.results
    pagination.total = data.count
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

// 重置
const handleReset = () => {
  Object.assign(queryForm, {
    asset_code: '',
    period: '',
    status: ''
  })
  handleSearch()
}

// 计算当月折旧
const handleCalculate = async () => {
  try {
    await ElMessageBox.confirm('确认计算当月所有资产的折旧？', '提示', { type: 'warning' })
    calculating.value = true
    await depreciationApi.calculate()
    ElMessage.success('折旧计算任务已提交，请稍后刷新查看')
    fetchData()
  } catch (error) {
    // cancel
  } finally {
    calculating.value = false
  }
}

// 导出
const handleExport = async () => {
  try {
    const blob = await depreciationApi.export(queryForm)
    // 下载文件
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `折旧记录_${queryForm.period || '全部'}.xlsx`
    a.click()
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 详情
const handleView = (row) => {
  // 跳转到详情页
  console.log('View:', row)
}

// 过账
const handlePost = async (row) => {
  try {
    await ElMessageBox.confirm('确认过账此折旧记录？过账后将无法修改', '提示', { type: 'warning' })
    await depreciationApi.post(row.id)
    ElMessage.success('过账成功')
    fetchData()
  } catch (error) {
    // cancel
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.depreciation-list .search-form {
  margin-bottom: 16px;
}

.depreciation-list .toolbar {
  margin-bottom: 16px;
}
</style>
```

---

## 2. 资产折旧详情页

### AssetDepreciationDetail.vue

```vue
<template>
  <div class="depreciation-detail">
    <el-page-header @back="$router.back()" title="返回">
      <template #content>
        <span>资产折旧详情 - {{ assetInfo.asset_code }}</span>
      </template>
    </el-page-header>

    <!-- 资产基本信息 -->
    <el-card class="info-card" header="资产信息">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="资产编码">{{ assetInfo.asset_code }}</el-descriptions-item>
        <el-descriptions-item label="资产名称">{{ assetInfo.asset_name }}</el-descriptions-item>
        <el-descriptions-item label="资产分类">{{ assetInfo.category_name }}</el-descriptions-item>
        <el-descriptions-item label="原值">¥{{ formatMoney(assetInfo.purchase_price) }}</el-descriptions-item>
        <el-descriptions-item label="残值率">{{ assetInfo.residual_rate }}%</el-descriptions-item>
        <el-descriptions-item label="预计残值">¥{{ formatMoney(assetInfo.residual_value) }}</el-descriptions-item>
        <el-descriptions-item label="使用年限">{{ assetInfo.useful_life }}月</el-descriptions-item>
        <el-descriptions-item label="折旧方法">
          <el-tag>{{ getMethodName(assetInfo.depreciation_method) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="启用日期">{{ assetInfo.purchase_date }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 折旧统计 -->
    <el-card class="info-card" header="折旧汇总">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">已使用月数</div>
            <div class="stat-value">{{ depreciationStat.used_months }} 月</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">累计折旧</div>
            <div class="stat-value">¥{{ formatMoney(depreciationStat.accumulated) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">当前净值</div>
            <div class="stat-value">¥{{ formatMoney(depreciationStat.net_value) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">折旧进度</div>
            <div class="stat-value">{{ depreciationStat.progress }}%</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 折旧趋势图 -->
    <el-card class="info-card" header="折旧趋势">
      <div ref="chartRef" style="height: 300px"></div>
    </el-card>

    <!-- 折旧明细记录 -->
    <el-card class="info-card" header="折旧明细">
      <el-table :data="depreciationRecords" border>
        <el-table-column prop="period" label="折旧期间" width="100" />
        <el-table-column prop="used_months" label="已用月数" width="100" />
        <el-table-column prop="depreciation_amount" label="本月折旧" width="120" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.depreciation_amount) }}</template>
        </el-table-column>
        <el-table-column prop="accumulated_depreciation" label="累计折旧" width="140" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.accumulated_depreciation) }}</template>
        </el-table-column>
        <el-table-column prop="net_value" label="期末净值" width="140" align="right">
          <template #default="{ row }">¥{{ formatMoney(row.net_value) }}</template>
        </el-table-column>
        <el-table-column prop="voucher_no" label="凭证号" width="140" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusName(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { depreciationApi } from '@/api/assets/depreciation'

const route = useRoute()
const assetId = route.params.id
const chartRef = ref<HTMLElement>()

const assetInfo = reactive({
  asset_code: '',
  asset_name: '',
  category_name: '',
  purchase_price: 0,
  residual_rate: 0,
  residual_value: 0,
  useful_life: 0,
  depreciation_method: '',
  purchase_date: ''
})

const depreciationStat = reactive({
  used_months: 0,
  accumulated: 0,
  net_value: 0,
  progress: 0
})

const depreciationRecords = ref([])

const methodMap = {
  straight_line: '直线法',
  double_declining: '双倍余额递减法',
  sum_of_years: '年数总和法'
}

const statusMap = {
  draft: '草稿',
  submitted: '已提交',
  approved: '已审核',
  posted: '已过账'
}

const statusTypeMap = {
  draft: 'info',
  submitted: 'warning',
  approved: 'success',
  posted: ''
}

const getMethodName = (method: string) => methodMap[method] || method
const getStatusName = (status: string) => statusMap[status] || status
const getStatusType = (status: string) => statusTypeMap[status] || ''

const formatMoney = (val: number) => {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return

  const chart = echarts.init(chartRef.value)
  const periods = depreciationRecords.value.map(r => r.period)
  const accumulated = depreciationRecords.value.map(r => Number(r.accumulated_depreciation))
  const netValues = depreciationRecords.value.map(r => Number(r.net_value))

  chart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['累计折旧', '净值'] },
    xAxis: { type: 'category', data: periods },
    yAxis: { type: 'value' },
    series: [
      {
        name: '累计折旧',
        type: 'line',
        data: accumulated,
        itemStyle: { color: '#f56c6c' }
      },
      {
        name: '净值',
        type: 'line',
        data: netValues,
        itemStyle: { color: '#67c23a' }
      }
    ]
  })
}

onMounted(async () => {
  // 获取资产折旧详情
  const { data } = await depreciationApi.assetDetail(assetId)
  Object.assign(assetInfo, data.asset_info)
  Object.assign(depreciationStat, data.stat)
  depreciationRecords.value = data.records

  // 初始化图表
  setTimeout(initChart, 100)
})
</script>

<style scoped>
.depreciation-detail {
  padding: 20px;
}

.info-card {
  margin-top: 16px;
}

.stat-item {
  text-align: center;
  padding: 20px 0;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  color: #303133;
  font-size: 24px;
  font-weight: bold;
}
</style>
```

---

## 3. 折旧报表页

### DepreciationReport.vue

```vue
<template>
  <div class="depreciation-report">
    <el-card>
      <!-- 查询条件 -->
      <el-form :model="queryForm" :inline="true">
        <el-form-item label="统计周期">
          <el-date-picker
            v-model="queryForm.period"
            type="month"
            format="YYYY-MM"
            value-format="YYYY-MM"
            placeholder="选择月份"
          />
        </el-form-item>
        <el-form-item label="资产分类">
          <el-cascader
            v-model="queryForm.category_id"
            :options="categoryTree"
            :props="{ value: 'id', label: 'name', children: 'children' }"
            clearable
            placeholder="全部分类"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchReport">查询</el-button>
          <el-button @click="handleExport">导出报表</el-button>
        </el-form-item>
      </el-form>

      <!-- 报表统计 -->
      <el-row :gutter="16" class="report-summary">
        <el-col :span="6">
          <div class="summary-card">
            <div class="summary-icon" style="background: #409eff">
              <el-icon><Document /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">应折旧资产</div>
              <div class="summary-value">{{ summary.asset_count }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-card">
            <div class="summary-icon" style="background: #67c23a">
              <el-icon><Money /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">本月折旧额</div>
              <div class="summary-value">¥{{ formatMoney(summary.current_amount) }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-card">
            <div class="summary-icon" style="background: #e6a23c">
              <el-icon><Wallet /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">累计折旧额</div>
              <div class="summary-value">¥{{ formatMoney(summary.accumulated_amount) }}</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="summary-card">
            <div class="summary-icon" style="background: #f56c6c">
              <el-icon><PieChart /></el-icon>
            </div>
            <div class="summary-content">
              <div class="summary-label">资产净值</div>
              <div class="summary-value">¥{{ formatMoney(summary.net_value) }}</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 按分类统计 -->
      <el-card header="按分类统计" class="mt-16">
        <el-table :data="categoryReport" border>
          <el-table-column prop="category_name" label="资产分类" />
          <el-table-column prop="asset_count" label="资产数量" align="right" />
          <el-table-column prop="original_value" label="原值合计" align="right">
            <template #default="{ row }">¥{{ formatMoney(row.original_value) }}</template>
          </el-table-column>
          <el-table-column prop="current_depreciation" label="本月折旧" align="right">
            <template #default="{ row }">¥{{ formatMoney(row.current_depreciation) }}</template>
          </el-table-column>
          <el-table-column prop="accumulated_depreciation" label="累计折旧" align="right">
            <template #default="{ row }">¥{{ formatMoney(row.accumulated_depreciation) }}</template>
          </el-table-column>
          <el-table-column prop="net_value" label="净值合计" align="right">
            <template #default="{ row }">¥{{ formatMoney(row.net_value) }}</template>
          </el-table-column>
          <el-table-column prop="depreciation_rate" label="折旧进度" align="right">
            <template #default="{ row }">{{ row.depreciation_rate }}%</template>
          </el-table-column>
        </el-table>
      </el-card>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Money, Wallet, PieChart } from '@element-plus/icons-vue'
import { depreciationApi } from '@/api/assets/depreciation'

const queryForm = reactive({
  period: '',
  category_id: []
})

const summary = reactive({
  asset_count: 0,
  current_amount: 0,
  accumulated_amount: 0,
  net_value: 0
})

const categoryReport = ref([])
const categoryTree = ref([])

const formatMoney = (val: number) => {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const fetchReport = async () => {
  try {
    const { data } = await depreciationApi.report(queryForm)
    Object.assign(summary, data.summary)
    categoryReport.value = data.by_category
  } catch (error) {
    ElMessage.error('获取报表失败')
  }
}

const handleExport = async () => {
  try {
    const blob = await depreciationApi.exportReport(queryForm)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `折旧报表_${queryForm.period}.xlsx`
    a.click()
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

onMounted(() => {
  // 默认查询本月
  const now = new Date()
  queryForm.period = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  fetchReport()
})
</script>

<style scoped>
.report-summary {
  margin-bottom: 16px;
}

.summary-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  margin-right: 16px;
}

.summary-content {
  flex: 1;
}

.summary-label {
  color: #909399;
  font-size: 14px;
}

.summary-value {
  color: #303133;
  font-size: 20px;
  font-weight: bold;
  margin-top: 4px;
}

.mt-16 {
  margin-top: 16px;
}
</style>
```

---

## 4. 折旧方法配置

### DepreciationMethodConfig.vue

```vue
<template>
  <div class="depreciation-config">
    <el-card header="折旧方法配置">
      <el-alert
        title="折旧方法说明"
        type="info"
        :closable="false"
        class="mb-16"
      >
        <ul>
          <li><b>直线法：</b>月折旧额 = (原值 - 残值) / 使用月数</li>
          <li><b>双倍余额递减法：</b>月折旧额 = 账面净值 × 2 / 使用年限 / 12</li>
          <li><b>年数总和法：</b>月折旧额 = (原值 - 残值) × 剩余月数 / 总月数</li>
        </ul>
      </el-alert>

      <el-table :data="categories" border>
        <el-table-column prop="name" label="资产分类" width="200" />
        <el-table-column prop="depreciation_method" label="折旧方法" width="180">
          <template #default="{ row }">
            <el-select v-model="row.depreciation_method" @change="handleSave(row)">
              <el-option label="直线法" value="straight_line" />
              <el-option label="双倍余额递减法" value="double_declining" />
              <el-option label="年数总和法" value="sum_of_years" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="useful_life" label="使用年限(月)" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.useful_life"
              :min="1"
              :max="600"
              @change="handleSave(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="residual_rate" label="残值率(%)" width="150">
          <template #default="{ row }">
            <el-input-number
              v-model="row.residual_rate"
              :min="0"
              :max="100"
              :precision="2"
              @change="handleSave(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { categoryApi } from '@/api/assets/category'

const categories = ref([])

const fetchCategories = async () => {
  const { data } = await categoryApi.list({ params: { with_depreciation: true } })
  categories.value = data
}

const handleSave = async (row) => {
  try {
    await categoryApi.update(row.id, {
      depreciation_method: row.depreciation_method,
      useful_life: row.useful_life,
      residual_rate: row.residual_rate
    })
    ElMessage.success('保存成功')
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<style scoped>
.mb-16 {
  margin-bottom: 16px;
}
</style>
```

---

## 5. 路由配置

```typescript
// router/assets.ts

export const depreciationRoutes = [
  {
    path: '/depreciation',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { title: '折旧管理', icon: 'Calculator' },
    children: [
      {
        path: '',
        name: 'DepreciationList',
        component: () => import('@/views/assets/depreciation/DepreciationList.vue'),
        meta: { title: '折旧记录' }
      },
      {
        path: 'asset/:id',
        name: 'AssetDepreciationDetail',
        component: () => import('@/views/assets/depreciation/AssetDepreciationDetail.vue'),
        meta: { title: '资产折旧详情' }
      },
      {
        path: 'report',
        name: 'DepreciationReport',
        component: () => import('@/views/assets/depreciation/DepreciationReport.vue'),
        meta: { title: '折旧报表' }
      },
      {
        path: 'config',
        name: 'DepreciationConfig',
        component: () => import('@/views/assets/depreciation/DepreciationMethodConfig.vue'),
        meta: { title: '折旧方法配置' }
      }
    ]
  }
]
```

---

## 后续任务

所有Phase已完成！
