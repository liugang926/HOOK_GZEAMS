# Phase 5.4: 财务报表生成 - 前端实现

## 1. 页面结构

### 1.1 页面层级

```
src/views/reports/
├── ReportCenter.vue              # 报表中心首页
├── TemplateList.vue              # 报表模板列表
├── TemplateDetail.vue            # 模板详情
├── TemplateManage.vue            # 模板管理（设计器）
├── ReportGenerate.vue            # 报表生成页面
├── ReportPreview.vue             # 报表预览页面
├── GenerationHistory.vue         # 生成历史
├── ScheduleManage.vue            # 定时报表管理
├── SubscriptionManage.vue        # 我的订阅
└── components/
    ├── TemplateCard.vue          # 模板卡片
    ├── FilterPanel.vue           # 筛选面板
    ├── ReportViewer.vue          # 报表查看器
    ├── ScheduleForm.vue          # 调度表单
    ├── ExportDialog.vue          # 导出对话框
    └── ReportStatistics.vue      # 报表统计
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

## 2. 报表中心页面

### 2.1 报表中心首页 (ReportCenter.vue)

```vue
<template>
  <div class="report-center">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>报表中心</h1>
      <p class="subtitle">快速生成各类财务报表</p>
    </div>

    <!-- 快捷入口 -->
    <el-row :gutter="16" class="quick-links">
      <el-col :span="6" v-for="template in quickTemplates" :key="template.id">
        <el-card class="template-card" @click="handleGenerate(template)">
          <div class="card-icon">
            <el-icon :size="32"><Document /></el-icon>
          </div>
          <div class="card-content">
            <h3>{{ template.template_name }}</h3>
            <p>{{ template.description }}</p>
          </div>
          <el-icon class="card-arrow"><ArrowRight /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <!-- 所有报表 -->
    <el-card class="all-reports">
      <template #header>
        <div class="header-content">
          <span>所有报表</span>
          <el-button-group>
            <el-button :icon="Grid" :active="viewMode === 'grid'" @click="viewMode = 'grid'" />
            <el-button :icon="List" :active="viewMode === 'list'" @click="viewMode = 'list'" />
          </el-button-group>
        </div>
      </template>

      <!-- 分类标签 -->
      <el-tabs v-model="activeCategory" @tab-change="handleCategoryChange">
        <el-tab-pane label="全部" name="all" />
        <el-tab-pane label="资产报表" name="asset" />
        <el-tab-pane label="折旧报表" name="depreciation" />
        <el-tab-pane label="分析报表" name="analysis" />
        <el-tab-pane label="自定义" name="custom" />
      </el-tabs>

      <!-- 模板列表 -->
      <template-list v-if="viewMode === 'list'" :templates="filteredTemplates" />
      <template-grid v-else :templates="filteredTemplates" />
    </el-card>

    <!-- 生成历史 -->
    <el-card class="recent-generations">
      <template #header>
        <div class="header-content">
          <span>最近生成</span>
          <el-link type="primary" @click="handleViewAllHistory">查看全部</el-link>
        </div>
      </template>
      <generation-list :generations="recentGenerations" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Document, ArrowRight, Grid, List } from '@element-plus/icons-vue'
import { reportApi } from '@/api/reports'
import TemplateList from './components/TemplateList.vue'
import TemplateGrid from './components/TemplateGrid.vue'
import GenerationList from './components/GenerationList.vue'

const router = useRouter()
const viewMode = ref<'grid' | 'list'>('grid')
const activeCategory = ref('all')
const templates = ref([])
const recentGenerations = ref([])

const quickTemplates = computed(() => {
  return templates.value.slice(0, 4)
})

const filteredTemplates = computed(() => {
  if (activeCategory.value === 'all') {
    return templates.value
  }
  return templates.value.filter(t => {
    if (activeCategory.value === 'asset') {
      return ['asset_detail', 'asset_change'].includes(t.report_type)
    } else if (activeCategory.value === 'depreciation') {
      return t.report_type === 'depreciation_summary'
    } else if (activeCategory.value === 'analysis') {
      return ['category_analysis', 'department_analysis'].includes(t.report_type)
    }
    return t.report_type === 'custom'
  })
})

const handleGenerate = (template: any) => {
  router.push({
    path: '/reports/generate',
    query: { template_code: template.template_code }
  })
}

const handleCategoryChange = () => {
  // 筛选逻辑在computed中处理
}

const handleViewAllHistory = () => {
  router.push('/reports/history')
}

onMounted(async () => {
  const [templatesRes, historyRes] = await Promise.all([
    reportApi.listTemplates({ status: 'active' }),
    reportApi.listGenerations({ page: 1, page_size: 5 })
  ])
  templates.value = templatesRes.results
  recentGenerations.value = historyRes.results
})
</script>

<style scoped>
.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  color: #909399;
}

.quick-links {
  margin-bottom: 24px;
}

.template-card {
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.template-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 16px;
}

.card-content h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.card-content p {
  font-size: 13px;
  color: #909399;
  line-height: 1.5;
}

.card-arrow {
  position: absolute;
  top: 16px;
  right: 16px;
  color: #C0C4CC;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.all-reports,
.recent-generations {
  margin-bottom: 24px;
}
</style>
```

---

## 3. 报表生成页面

### 3.1 生成页面 (ReportGenerate.vue)

```vue
<template>
  <div class="report-generate">
    <el-page-header @back="handleBack">
      <template #content>
        <span>{{ template?.template_name }}</span>
      </template>
    </el-page-header>

    <div class="generate-layout">
      <!-- 筛选面板 -->
      <div class="filter-panel">
        <filter-panel
          v-model="filterParams"
          :config="template?.data_source?.filters || []"
          @preview="handlePreview"
        />
      </div>

      <!-- 预览区域 -->
      <div class="preview-area">
        <el-card v-loading="previewLoading">
          <template #header>
            <div class="preview-header">
              <span>报表预览</span>
              <div class="actions">
                <el-button :icon="Refresh" @click="handlePreview">刷新</el-button>
                <el-button
                  type="primary"
                  :icon="Download"
                  :disabled="!previewData"
                  @click="handleExport"
                >
                  导出报表
                </el-button>
              </div>
            </div>
          </template>

          <!-- 数据预览 -->
          <div v-if="previewData" class="preview-content">
            <!-- 表格类型 -->
            <data-table
              v-if="displayType === 'table'"
              :data="previewData.data"
              :columns="tableColumns"
              :summary="previewData.summary"
            />

            <!-- 汇总类型 -->
            <summary-view
              v-else-if="displayType === 'summary'"
              :data="previewData"
            />

            <!-- 图表类型 -->
            <chart-view
              v-else-if="displayType === 'chart'"
              :data="previewData"
            />
          </div>

          <el-empty v-else description="点击预览按钮查看报表数据" />
        </el-card>
      </div>
    </div>

    <!-- 导出对话框 -->
    <export-dialog
      v-model="exportDialogVisible"
      :template="template"
      :params="filterParams"
      @success="handleExportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Refresh, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reportApi } from '@/api/reports'
import FilterPanel from './components/FilterPanel.vue'
import DataTable from './components/DataTable.vue'
import SummaryView from './components/SummaryView.vue'
import ChartView from './components/ChartView.vue'
import ExportDialog from './components/ExportDialog.vue'

const router = useRouter()
const route = useRoute()

const template = ref<any>(null)
const filterParams = ref<any>({})
const previewData = ref<any>(null)
const previewLoading = ref(false)
const exportDialogVisible = ref(false)

const displayType = computed(() => {
  if (!template.value) return 'table'
  const reportType = template.value.report_type
  if (['category_analysis', 'department_analysis'].includes(reportType)) {
    return 'chart'
  } else if (['depreciation_summary'].includes(reportType)) {
    return 'summary'
  }
  return 'table'
})

const tableColumns = computed(() => {
  if (!previewData.value || !template.value) return []
  const templateConfig = template.value.template_config
  const sections = templateConfig.sections || []
  const tableSection = sections.find((s: any) => s.type === 'table')
  return tableSection?.columns || []
})

const handlePreview = async () => {
  previewLoading.value = true
  try {
    const result = await reportApi.preview({
      template_code: template.value.template_code,
      params: filterParams.value
    })
    previewData.value = result.data
  } catch {
    ElMessage.error('预览失败')
  } finally {
    previewLoading.value = false
  }
}

const handleExport = () => {
  exportDialogVisible.value = true
}

const handleExportSuccess = (generation: any) => {
  exportDialogVisible.value = false
  ElMessage.success('报表生成成功')
  // 可以选择跳转到下载或直接下载
}

const handleBack = () => {
  router.back()
}

onMounted(async () => {
  const templateCode = route.query.template_code
  if (templateCode) {
    template.value = await reportApi.getTemplate(templateCode)
  } else {
    router.push('/reports')
  }
})
</script>

<style scoped>
.generate-layout {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.filter-panel {
  width: 280px;
  flex-shrink: 0;
}

.preview-area {
  flex: 1;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-content {
  min-height: 400px;
}
</style>
```

### 3.2 筛选面板 (FilterPanel.vue)

```vue
<template>
  <el-card class="filter-panel">
    <template #header>
      <span>筛选条件</span>
    </template>

    <el-form :model="localParams" label-width="80px">
      <el-form-item label="部门">
        <dept-picker v-model="localParams.department_id" placeholder="全部部门" clearable />
      </el-form-item>

      <el-form-item label="资产类别">
        <asset-category-picker v-model="localParams.category_id" placeholder="全部类别" clearable />
      </el-form-item>

      <el-form-item label="存放位置">
        <location-picker v-model="localParams.location_id" placeholder="全部位置" clearable />
      </el-form-item>

      <el-form-item label="使用状态">
        <el-select v-model="localParams.status" placeholder="全部状态" clearable>
          <el-option label="在用" value="in_use" />
          <el-option label="闲置" value="idle" />
          <el-option label="维修中" value="maintenance" />
        </el-select>
      </el-form-item>

      <el-form-item label="日期范围">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleDateChange"
        />
      </el-form-item>

      <!-- 动态筛选条件 -->
      <template v-for="filter in dynamicFilters" :key="filter.field">
        <filter-field
          :filter="filter"
          v-model="localParams[filter.param_key || filter.field]"
        />
      </template>
    </el-form>

    <div class="filter-actions">
      <el-button @click="handleReset">重置</el-button>
      <el-button type="primary" @click="handleApply">应用</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'

const props = defineProps<{
  modelValue: any
  config: any[]
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
  (e: 'preview'): void
}>()

const localParams = reactive({ ...props.modelValue })
const dateRange = ref<any[]>([])

const dynamicFilters = computed(() => {
  return props.config || []
})

const handleDateChange = (value: any) => {
  if (value && value.length === 2) {
    localParams.period_from = value[0]
    localParams.period_to = value[1]
  } else {
    localParams.period_from = null
    localParams.period_to = null
  }
}

const handleReset = () => {
  Object.keys(localParams).forEach(key => {
    localParams[key] = null
  })
  dateRange.value = []
  emit('update:modelValue', localParams)
}

const handleApply = () => {
  emit('update:modelValue', localParams)
  emit('preview')
}

watch(() => props.modelValue, (newVal) => {
  Object.assign(localParams, newVal)
}, { deep: true })
</script>

<style scoped>
.filter-panel {
  position: sticky;
  top: 20px;
}

.filter-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.filter-actions .el-button {
  flex: 1;
}
</style>
```

---

## 4. 报表查看组件

### 4.1 数据表格 (DataTable.vue)

```vue
<template>
  <div class="data-table">
    <el-table
      :data="paginatedData"
      border
      stripe
      :summary-method="getSummaries"
      show-summary
      height="500"
    >
      <el-table-column
        v-for="col in columns"
        :key="col.field"
        :prop="col.field"
        :label="col.title"
        :width="col.width"
        :align="col.align || 'left'"
      >
        <template #default="{ row }">
          <span v-if="col.format === 'currency'">
            ¥{{ formatCurrency(row[col.field]) }}
          </span>
          <span v-else>{{ row[col.field] }}</span>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="data.length"
      layout="total, sizes, prev, pager, next"
      :page-sizes="[50, 100, 200, 500]"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  data: any[]
  columns: any[]
  summary?: any
}>()

const pagination = ref({
  page: 1,
  pageSize: 50
})

const paginatedData = computed(() => {
  const start = (pagination.value.page - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return props.data.slice(start, end)
})

const formatCurrency = (value: any) => {
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

const getSummaries = (param: any) => {
  const { columns, data } = param
  const sums: string[] = []

  columns.forEach((column: any, index: number) => {
    if (index === 0) {
      sums[index] = '合计'
      return
    }

    const col = props.columns[index - 1]
    if (col?.format === 'currency') {
      const values = data.map((item: any) => Number(item[column.property] || 0))
      const sum = values.reduce((prev, curr) => prev + curr, 0)
      sums[index] = formatCurrency(sum)
    } else {
      sums[index] = ''
    }
  })

  return sums
}

const handleSizeChange = () => {
  pagination.value.page = 1
}
</script>

<style scoped>
.data-table {
  padding: 16px 0;
}

.el-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
```

### 4.2 汇总视图 (SummaryView.vue)

```vue
<template>
  <div class="summary-view">
    <!-- 总览卡片 -->
    <el-row :gutter="16" class="summary-cards">
      <el-col :span="6" v-for="(item, key) in summaryCards" :key="key">
        <el-card class="summary-card">
          <div class="card-label">{{ item.label }}</div>
          <div class="card-value">{{ item.value }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细汇总 -->
    <el-tabs v-model="activeTab" class="summary-tabs">
      <el-tab-pane
        v-for="(data, key) in summaryData"
        :key="key"
        :label="getTabLabel(key)"
        :name="key"
      >
        <el-table :data="data" border>
          <el-table-column
            v-for="col in getColumns(key)"
            :key="col.field"
            :prop="col.field"
            :label="col.label"
          />
          <el-table-column label="金额" align="right">
            <template #default="{ row }">
              ¥{{ formatCurrency(row.total_depreciation || row.total_original || row.total_net || 0) }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  data: any
}>()

const activeTab = ref('by_category')

const summaryCards = computed(() => {
  const summary = props.data.summary || {}
  return {
    total_count: {
      label: '资产数量',
      value: summary.total_count || 0
    },
    total_original: {
      label: '资产原值',
      value: formatCurrency(summary.total_original || 0)
    },
    total_depreciation: {
      label: '累计折旧',
      value: formatCurrency(summary.total_depreciation || 0)
    },
    total_net: {
      label: '资产净值',
      value: formatCurrency(summary.total_net || 0)
    }
  }
})

const summaryData = computed(() => {
  return {
    by_category: props.data.by_category || [],
    by_period: props.data.by_period || []
  }
})

const getTabLabel = (key: string) => {
  const labels: Record<string, string> = {
    by_category: '按类别',
    by_period: '按期间'
  }
  return labels[key] || key
}

const getColumns = (key: string) => {
  const columns: Record<string, any[]> = {
    by_category: [
      { field: 'category', label: '类别' },
      { field: 'count', label: '数量' }
    ],
    by_period: [
      { field: 'period', label: '期间' },
      { field: 'count', label: '数量' }
    ]
  }
  return columns[key] || []
}

const formatCurrency = (value: number) => {
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}
</script>

<style scoped>
.summary-cards {
  margin-bottom: 20px;
}

.summary-card {
  text-align: center;
}

.card-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.summary-tabs {
  margin-top: 20px;
}
</style>
```

### 4.3 导出对话框 (ExportDialog.vue)

```vue
<template>
  <el-dialog
    v-model="visible"
    title="导出报表"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form :model="form" label-width="100px">
      <el-form-item label="报表名称">
        <el-input v-model="form.report_name" placeholder="默认名称" />
      </el-form-item>

      <el-form-item label="导出格式">
        <el-radio-group v-model="form.output_format">
          <el-radio label="pdf">
            <div class="format-option">
              <el-icon><Document /></el-icon>
              <span>PDF</span>
            </div>
          </el-radio>
          <el-radio label="excel">
            <div class="format-option">
              <el-icon><Tickets /></el-icon>
              <span>Excel</span>
            </div>
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="导出选项" v-if="form.output_format === 'pdf'">
        <el-checkbox v-model="form.include_summary">包含汇总信息</el-checkbox>
        <el-checkbox v-model="form.include_signature">包含签字区</el-checkbox>
      </el-form-item>

      <el-form-item label="发送至邮箱" v-if="form.output_format === 'pdf'">
        <el-checkbox v-model="form.send_email">
          同时发送到邮箱
        </el-checkbox>
        <el-input
          v-if="form.send_email"
          v-model="form.email"
          placeholder="请输入邮箱地址"
          style="margin-top: 8px"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleExport" :loading="exporting">
        生成并导出
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Document, Tickets } from '@element-plus/icons-vue'
import { reportApi } from '@/api/reports'

const props = defineProps<{
  template: any
  params: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success', generation: any): void
}>()

const visible = defineModel<boolean>()
const exporting = ref(false)

const form = reactive({
  report_name: '',
  output_format: 'pdf',
  include_summary: true,
  include_signature: false,
  send_email: false,
  email: ''
})

const handleExport = async () => {
  exporting.value = true
  try {
    const generation = await reportApi.generate({
      template_code: props.template.template_code,
      params: props.params,
      output_format: form.output_format
    })

    // 等待生成完成
    const result = await pollGenerationStatus(generation.id)

    if (result.status === 'success' && result.file_url) {
      // 自动下载
      window.open(result.file_url, '_blank')
      emit('success', result)
    } else {
      ElMessage.error('报表生成失败')
    }
  } catch {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const pollGenerationStatus = async (id: number) => {
  const maxAttempts = 60
  let attempts = 0

  while (attempts < maxAttempts) {
    const result = await reportApi.getGeneration(id)
    if (result.status !== 'pending') {
      return result
    }
    await new Promise(resolve => setTimeout(resolve, 1000))
    attempts++
  }

  throw new Error('生成超时')
}
</script>

<style scoped>
.format-option {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
```

---

## 5. 定时报表管理

### 5.1 调度管理 (ScheduleManage.vue)

```vue
<template>
  <div class="schedule-manage">
    <div class="page-header">
      <h1>定时报表</h1>
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建调度
      </el-button>
    </div>

    <!-- 调度列表 -->
    <el-table :data="schedules" border stripe v-loading="loading">
      <el-table-column prop="schedule_name" label="任务名称" min-width="200" />
      <el-table-column prop="template.template_name" label="报表模板" width="200" />
      <el-table-column label="执行频率" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.frequency_display }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="next_run_at" label="下次运行" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.next_run_at) }}
        </template>
      </el-table-column>
      <el-table-column label="订阅人数" width="100" align="center">
        <template #default="{ row }">
          {{ row.subscriptions_count }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-switch
            v-model="row.is_active"
            @change="handleToggle(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleView(row)">查看</el-button>
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleSubscribe(row)">订阅</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 调度表单对话框 -->
    <schedule-form
      v-model="formDialogVisible"
      :schedule="currentSchedule"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { scheduleApi } from '@/api/reports/schedule'
import { formatDateTime } from '@/utils/format'
import ScheduleForm from './components/ScheduleForm.vue'

const router = useRouter()
const loading = ref(false)
const schedules = ref([])
const formDialogVisible = ref(false)
const currentSchedule = ref<any>(null)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await scheduleApi.list()
    schedules.value = res.results
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentSchedule.value = null
  formDialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentSchedule.value = row
  formDialogVisible.value = true
}

const handleToggle = async (row: any) => {
  try {
    await scheduleApi.toggle(row.id)
    ElMessage.success(row.is_active ? '已启用' : '已停用')
  } catch {
    // 恢复状态
    row.is_active = !row.is_active
  }
}

const handleSubscribe = (row: any) => {
  // 打开订阅对话框
}

const handleFormSuccess = () => {
  formDialogVisible.value = false
  fetchData()
}

onMounted(fetchData)
</script>
```

---

## 6. API 封装

```typescript
// src/api/reports/index.ts

import request from '@/utils/request'

export const reportApi = {
  // 模板
  listTemplates: (params?: any) =>
    request.get('/reports/templates/', { params }),

  getTemplate: (code: string) =>
    request.get(`/reports/templates/${code}/`),

  // 生成
  generate: (data: any) =>
    request.post('/reports/generate/', data),

  preview: (data: any) =>
    request.post('/reports/preview/', data),

  getGeneration: (id: number) =>
    request.get(`/reports/generations/${id}/`),

  listGenerations: (params?: any) =>
    request.get('/reports/generations/', { params }),

  download: (id: number) =>
    request.get(`/reports/generations/${id}/download/`, {
      responseType: 'blob'
    }),

  // 调度
  listSchedules: (params?: any) =>
    request.get('/reports/schedules/', { params }),

  createSchedule: (data: any) =>
    request.post('/reports/schedules/', data),

  updateSchedule: (id: number, data: any) =>
    request.put(`/reports/schedules/${id}/`, data),

  toggleSchedule: (id: number) =>
    request.post(`/reports/schedules/${id}/toggle/`),

  // 订阅
  mySubscriptions: () =>
    request.get('/reports/my-subscriptions/'),

  subscribe: (data: any) =>
    request.post('/reports/subscriptions/', data),

  unsubscribe: (id: number) =>
    request.delete(`/reports/subscriptions/${id}/`),

  // 统计
  getStatistics: (params: any) =>
    request.get('/reports/statistics/', { params })
}

// src/api/reports/schedule.ts
export { scheduleApi } from './index'
```

---

## 7. 路由配置

```typescript
// src/router/reports.ts

export default [
  {
    path: '/reports',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { title: '报表中心', icon: 'DataAnalysis' },
    children: [
      {
        path: '',
        component: () => import('@/views/reports/ReportCenter.vue'),
        meta: { title: '报表中心' }
      },
      {
        path: 'templates',
        component: () => import('@/views/reports/TemplateList.vue'),
        meta: { title: '报表模板' }
      },
      {
        path: 'templates/:code',
        component: () => import('@/views/reports/TemplateDetail.vue'),
        meta: { title: '模板详情', hidden: true }
      },
      {
        path: 'generate',
        component: () => import('@/views/reports/ReportGenerate.vue'),
        meta: { title: '生成报表', hidden: true }
      },
      {
        path: 'history',
        component: () => import('@/views/reports/GenerationHistory.vue'),
        meta: { title: '生成历史' }
      },
      {
        path: 'schedule',
        component: () => import('@/views/reports/ScheduleManage.vue'),
        meta: { title: '定时报表' }
      },
      {
        path: 'subscription',
        component: () => import('@/views/reports/SubscriptionManage.vue'),
        meta: { title: '我的订阅' }
      }
    ]
  }
]
```
