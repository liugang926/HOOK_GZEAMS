# Phase 4.4: 盘点任务分配与执行 - 前端实现

## 概述

区分**管理端**和**用户端**两套界面：
- **管理端**：盘点任务管理、分配配置、进度追踪
- **用户端**：我的盘点任务、待盘清单、盘点操作

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

## 目录结构

```
src/views/inventory/
├── admin/                      # 管理端
│   ├── TaskList.vue           # 任务列表
│   ├── TaskCreate.vue         # 创建任务
│   ├── AssignmentConfig.vue   # 分配配置
│   ├── ViewPermissionConfig.vue  # 查看权限配置
│   └── ProgressMonitor.vue    # 进度监控
└── mobile/                     # 用户端（移动端优先）
    ├── MyTasks.vue            # 我的任务
    ├── TaskDetail.vue         # 任务详情
    ├── AssetList.vue          # 待盘资产列表
    └── ScanPage.vue           # 扫码盘点页面
```

---

## 1. 管理端 - 任务分配配置

### AssignmentConfig.vue

```vue
<template>
  <div class="assignment-config">
    <el-card header="盘点分配配置">
      <!-- 任务信息 -->
      <el-descriptions :column="3" border class="mb-16">
        <el-descriptions-item label="任务编号">{{ task.task_code }}</el-descriptions-item>
        <el-descriptions-item label="任务名称">{{ task.task_name }}</el-descriptions-item>
        <el-descriptions-item label="盘点类型">
          {{ getTaskTypeName(task.inventory_type) }}
        </el-descriptions-item>
        <el-descriptions-item label="应盘数量">{{ task.total_count }}</el-descriptions-item>
        <el-descriptions-item label="已分配">{{ assignedCount }}</el-descriptions-item>
        <el-descriptions-item label="未分配">{{ task.total_count - assignedCount }}</el-descriptions-item>
      </el-descriptions>

      <!-- 分配方式选择 -->
      <el-radio-group v-model="assignMode" class="mb-16">
        <el-radio-button value="template">使用模板</el-radio-button>
        <el-radio-button value="rule">按规则自动分配</el-radio-button>
        <el-radio-button value="custodian">按保管人自盘</el-radio-button>
        <el-radio-button value="region">按区域分配</el-radio-button>
        <el-radio-button value="category">按分类分配</el-radio-button>
        <el-radio-button value="random">随机盲抽</el-radio-button>
        <el-radio-button value="manual">手动分配</el-radio-button>
      </el-radio-group>

      <!-- 模板模式 -->
      <div v-if="assignMode === 'template'" class="config-panel">
        <el-form :model="templateForm" label-width="100px">
          <el-form-item label="选择模板">
            <el-select v-model="templateForm.template_id" placeholder="请选择模板">
              <el-option
                v-for="tpl in templates"
                :key="tpl.id"
                :label="tpl.template_name"
                :value="tpl.id"
              >
                <div>
                  <span>{{ tpl.template_name }}</span>
                  <span class="text-gray text-sm ml-8">{{ tpl.rules.length }} 条规则</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
        </el-form>
      </div>

      <!-- 规则自动分配 -->
      <div v-if="assignMode === 'rule'" class="config-panel">
        <el-alert
          title="将按组织配置的分配规则自动分配"
          type="info"
          :closable="false"
          class="mb-16"
        />
        <div class="rule-preview">
          <h4>当前生效的规则：</h4>
          <el-table :data="effectiveRules" size="small" border>
            <el-table-column prop="rule_code" label="规则编码" width="120" />
            <el-table-column prop="rule_name" label="规则名称" />
            <el-table-column prop="assignment_mode" label="分配模式" width="100">
              <template #default="{ row }">
                {{ getModeName(row.assignment_mode) }}
              </template>
            </el-table-column>
            <el-table-column prop="priority" label="优先级" width="80" />
          </el-table>
        </div>
      </div>

      <!-- 按保管人自盘 -->
      <div v-if="assignMode === 'custodian'" class="config-panel">
        <el-alert
          title="将资产自动分配给各自的保管人，每人盘点自己名下的资产"
          type="success"
          :closable="false"
          class="mb-16"
        />
        <div class="custodian-preview">
          <h4>预计分配情况：</h4>
          <el-table :data="custodianPreview" size="small" border>
            <el-table-column prop="custodian_name" label="保管人" />
            <el-table-column prop="asset_count" label="资产数量" width="100" />
          </el-table>
        </div>
      </div>

      <!-- 按区域分配 -->
      <div v-if="assignMode === 'region'" class="config-panel">
        <el-form :model="regionForm" label-width="100px">
          <el-form-item label="选择区域">
            <el-select v-model="regionForm.location_ids" multiple placeholder="请选择地点">
              <el-option
                v-for="loc in locations"
                :key="loc.id"
                :label="loc.name"
                :value="loc.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="分配给">
            <user-selector v-model="regionForm.executor_id" />
          </el-form-item>
          <el-form-item label="说明">
            <el-input v-model="regionForm.instruction" placeholder="给执行人的说明" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 按分类分配 -->
      <div v-if="assignMode === 'category'" class="config-panel">
        <el-form :model="categoryForm" label-width="100px">
          <el-form-item label="资产分类">
            <el-cascader
              v-model="categoryForm.category_ids"
              :options="categoryTree"
              :props="{ multiple: true, value: 'id', label: 'name' }"
              placeholder="请选择分类"
            />
          </el-form-item>
          <el-form-item label="分配给">
            <user-selector v-model="categoryForm.executor_id" />
          </el-form-item>
          <el-form-item label="说明">
            <el-input v-model="categoryForm.instruction" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 随机盲抽 -->
      <div v-if="assignMode === 'random'" class="config-panel">
        <el-alert
          title="将资产随机分配给执行人，适用于交叉盘点等场景"
          type="warning"
          :closable="false"
          class="mb-16"
        />
        <el-form :model="randomForm" label-width="120px">
          <el-form-item label="选择人员">
            <user-selector v-model="randomForm.executor_ids" multiple />
          </el-form-item>
          <el-form-item label="分配方式">
            <el-radio-group v-model="randomForm.distribute_type">
              <el-radio value="even">平均分配</el-radio>
              <el-radio value="fixed">指定数量</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item
            v-if="randomForm.distribute_type === 'fixed'"
            label="每人数量"
          >
            <el-input-number
              v-model="randomForm.per_executor"
              :min="1"
              :max="task.total_count"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 手动分配 -->
      <div v-if="assignMode === 'manual'" class="config-panel">
        <div class="manual-assignment">
          <div class="left-panel">
            <h4>可选资产</h4>
            <el-input
              v-model="assetSearch"
              placeholder="搜索资产"
              prefix-icon="Search"
              class="mb-8"
            />
            <el-table
              :data="filteredAssets"
              border
              height="400"
              @selection-change="handleAssetSelection"
            >
              <el-table-column type="selection" width="50" />
              <el-table-column prop="asset_code" label="编码" width="120" />
              <el-table-column prop="asset_name" label="名称" />
              <el-table-column prop="location_name" label="位置" width="120" />
              <el-table-column prop="custodian_name" label="保管人" width="100" />
            </el-table>
          </div>
          <div class="center-panel">
            <el-button
              type="primary"
              :disabled="selectedAssets.length === 0 || !manualForm.executor_id"
              @click="addManualAssignment"
            >
              添加 &rarr;
            </el-button>
          </div>
          <div class="right-panel">
            <h4>已添加分配</h4>
            <el-form label-width="80px" class="mb-8">
              <el-form-item label="执行人">
                <user-selector v-model="manualForm.executor_id" />
              </el-form-item>
            </el-form>
            <el-table :data="manualAssignments" border height="300">
              <el-table-column prop="asset_code" label="编码" width="120" />
              <el-table-column prop="asset_name" label="名称" />
              <el-table-column label="操作" width="60">
                <template #default="{ $index }">
                  <el-button
                    link
                    type="danger"
                    size="small"
                    @click="removeManualAssignment($index)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-bar mt-16">
        <el-button @click="$router.back()">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          确认分配
        </el-button>
      </div>
    </el-card>

    <!-- 分配结果 -->
    <el-dialog
      v-model="resultVisible"
      title="分配结果"
      width="800px"
    >
      <el-table :data="assignResults" border>
        <el-table-column prop="executor_name" label="执行人" />
        <el-table-column prop="mode_display" label="分配模式" width="100" />
        <el-table-column prop="total_assigned" label="分配数量" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewAssignmentDetail(row)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { inventoryApi } from '@/api/inventory'

const route = useRoute()
const taskId = route.params.id

const task = ref({})
const assignMode = ref('template')
const submitting = ref(false)
const resultVisible = ref(false)
const assignResults = ref([])

// 各种表单数据
const templateForm = reactive({ template_id: null })
const regionForm = reactive({ location_ids: [], executor_id: null, instruction: '' })
const categoryForm = reactive({ category_ids: [], executor_id: null, instruction: '' })
const randomForm = reactive({ executor_ids: [], distribute_type: 'even', per_executor: 50 })
const manualForm = reactive({ executor_id: null })

// 数据源
const templates = ref([])
const locations = ref([])
const categoryTree = ref([])
const effectiveRules = ref([])
const custodianPreview = ref([])

// 手动分配
const assetSearch = ref('')
const allAssets = ref([])
const selectedAssets = ref([])
const manualAssignments = ref([])

const assignedCount = computed(() => {
  return task.value.assignments?.length || 0
})

const filteredAssets = computed(() => {
  if (!assetSearch.value) return allAssets.value
  const search = assetSearch.value.toLowerCase()
  return allAssets.value.filter(a =>
    a.asset_code.toLowerCase().includes(search) ||
    a.asset_name.toLowerCase().includes(search)
  )
})

const fetchData = async () => {
  const { data } = await inventoryApi.getTask(taskId)
  task.value = data

  // 并行获取其他数据
  await Promise.all([
    fetchTemplates(),
    fetchLocations(),
    fetchCategoryTree(),
    fetchEffectiveRules(),
    fetchCustodianPreview(),
    fetchUnassignedAssets()
  ])
}

const fetchTemplates = async () => {
  const { data } = await inventoryApi.getAssignmentTemplates()
  templates.value = data
}

const fetchLocations = async () => {
  const { data } = await inventoryApi.getLocations()
  locations.value = data
}

const fetchCategoryTree = async () => {
  const { data } = await inventoryApi.getCategoryTree()
  categoryTree.value = data
}

const fetchEffectiveRules = async () => {
  const { data } = await inventoryApi.getEffectiveRules(taskId)
  effectiveRules.value = data
}

const fetchCustodianPreview = async () => {
  const { data } = await inventoryApi.getCustodianPreview(taskId)
  custodianPreview.value = data
}

const fetchUnassignedAssets = async () => {
  const { data } = await inventoryApi.getUnassignedAssets(taskId)
  allAssets.value = data
}

const handleSubmit = async () => {
  try {
    submitting.value = true

    let response
    switch (assignMode.value) {
      case 'template':
        response = await inventoryApi.autoAssignTemplate(taskId, {
          template_id: templateForm.template_id
        })
        break
      case 'rule':
        response = await inventoryApi.autoAssignRules(taskId)
        break
      case 'custodian':
        response = await inventoryApi.assignCustodian(taskId)
        break
      case 'region':
        response = await inventoryApi.createAssignments(taskId, {
          assignments: [{
            executor_id: regionForm.executor_id,
            mode: 'region',
            scope_config: { location_ids: regionForm.location_ids },
            instruction: regionForm.instruction
          }]
        })
        break
      case 'category':
        response = await inventoryApi.createAssignments(taskId, {
          assignments: [{
            executor_id: categoryForm.executor_id,
            mode: 'category',
            scope_config: { category_ids: categoryForm.category_ids },
            instruction: categoryForm.instruction
          }]
        })
        break
      case 'random':
        response = await inventoryApi.assignRandom(taskId, {
          executor_ids: randomForm.executor_ids,
          per_executor: randomForm.distribute_type === 'fixed' ? randomForm.per_executor : null
        })
        break
      case 'manual':
        // 手动分配先完成
        response = await inventoryApi.createAssignments(taskId, {
          assignments: manualAssignments.value
        })
        break
    }

    assignResults.value = response.data
    resultVisible.value = true
    ElMessage.success('分配成功')
  } catch (error) {
    ElMessage.error('分配失败')
  } finally {
    submitting.value = false
  }
}

const handleAssetSelection = (selection) => {
  selectedAssets.value = selection
}

const addManualAssignment = () => {
  selectedAssets.value.forEach(asset => {
    if (!manualAssignments.value.find(a => a.asset_id === asset.asset_id)) {
      manualAssignments.value.push({
        asset_id: asset.id,
        asset_code: asset.asset_code,
        asset_name: asset.asset_name,
        executor_id: manualForm.executor_id
      })
    }
  })
}

const removeManualAssignment = (index) => {
  manualAssignments.value.splice(index, 1)
}

const getTaskTypeName = (type) => {
  const map = {
    full: '全盘',
    partial: '抽盘',
    department: '部门盘',
    category: '分类盘'
  }
  return map[type] || type
}

const getModeName = (mode) => {
  const map = {
    region: '区域分配',
    category: '分类分配',
    custodian: '保管人分配',
    random: '盲抽分配',
    manual: '手动分配'
  }
  return map[mode] || mode
}

const viewAssignmentDetail = (row) => {
  // 查看分配详情
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.mb-8 { margin-bottom: 8px; }
.mb-16 { margin-bottom: 16px; }
.mt-16 { margin-top: 16px; }
.ml-8 { margin-left: 8px; }

.config-panel {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.manual-assignment {
  display: flex;
  gap: 16px;
}

.left-panel,
.right-panel {
  flex: 1;
}

.center-panel {
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-bar {
  text-align: right;
  border-top: 1px solid #dcdfe6;
  padding-top: 16px;
}

.text-gray { color: #909399; }
.text-sm { font-size: 12px; }
</style>
```

---

## 2. 管理端 - 进度监控

### ProgressMonitor.vue

```vue
<template>
  <div class="progress-monitor">
    <el-card header="盘点进度监控">
      <!-- 总体进度 -->
      <div class="overall-progress mb-16">
        <el-progress
          :percentage="overallProgress"
          :status="overallProgress === 100 ? 'success' : undefined"
        >
          <template #default="{ percentage }">
            <span class="progress-text">{{ percentage }}%</span>
          </template>
        </el-progress>
        <div class="progress-stats">
          <span>总进度: {{ overallStats.scanned }}/{{ overallStats.total }}</span>
          <span>正常: {{ overallStats.normal }}</span>
          <span>盘盈: {{ overallStats.extra }}</span>
          <span>盘亏: {{ overallStats.missing }}</span>
        </div>
      </div>

      <!-- 按执行人分组 -->
      <el-divider content-position="left">执行人进度</el-divider>

      <el-table :data="assignments" border>
        <el-table-column prop="executor_name" label="执行人" width="120">
          <template #default="{ row }">
            <div class="executor-cell">
              <el-avatar :size="32" :src="row.executor_avatar">
                {{ row.executor_name?.charAt(0) }}
              </el-avatar>
              <span class="ml-8">{{ row.executor_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="mode_display" label="分配模式" width="100" />
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <el-progress
              :percentage="row.progress"
              :status="row.status === 'completed' ? 'success' : undefined"
            />
          </template>
        </el-table-column>
        <el-table-column label="完成情况" width="180">
          <template #default="{ row }">
            <span class="mr-8">{{ row.completed_count }}/{{ row.total_assigned }}</span>
            <el-tag v-if="row.missing_count > 0" type="danger" size="small">
              缺{{ row.missing_count }}
            </el-tag>
            <el-tag v-if="row.extra_count > 0" type="warning" size="small">
              盈{{ row.extra_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status_display" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deadline_at" label="截止时间" width="160">
          <template #default="{ row }">
            <span :class="{ 'text-red': isOverdue(row) }">
              {{ formatTime(row.deadline_at) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              link
              type="warning"
              @click="handleRemind(row)"
              v-if="row.status === 'pending'"
            >
              催办
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 统计图表 -->
      <el-divider content-position="left">完成度分布</el-divider>

      <div class="chart-container">
        <div ref="chartRef" style="height: 300px"></div>
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <AssignmentDetailDialog
      v-model="detailVisible"
      :assignment="currentAssignment"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { inventoryApi } from '@/api/inventory'
import AssignmentDetailDialog from './AssignmentDetailDialog.vue'

const route = useRoute()
const taskId = route.params.id

const assignments = ref([])
const overallStats = reactive({
  total: 0,
  scanned: 0,
  normal: 0,
  extra: 0,
  missing: 0
})
const detailVisible = ref(false)
const currentAssignment = ref(null)
const chartRef = ref<HTMLElement>()

const overallProgress = computed(() => {
  if (overallStats.total === 0) return 0
  return Math.round(overallStats.scanned / overallStats.total * 100)
})

const fetchData = async () => {
  const { data } = await inventoryApi.getAssignmentProgress(taskId)
  assignments.value = data.assignments
  Object.assign(overallStats, data.stats)

  nextTick(() => {
    initChart()
  })
}

const initChart = () => {
  if (!chartRef.value) return

  const chart = echarts.init(chartRef.value)

  // 按完成度分组
  const statusGroups = {
    completed: 0,
    inProgress: 0,
    pending: 0,
    overdue: 0
  }

  assignments.value.forEach(a => {
    if (a.status === 'completed') statusGroups.completed++
    else if (a.status === 'in_progress') statusGroups.inProgress++
    else if (a.status === 'pending' && isOverdue(a)) statusGroups.overdue++
    else statusGroups.pending++
  })

  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', right: 10 },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: [
        { value: statusGroups.completed, name: '已完成', itemStyle: { color: '#67c23a' } },
        { value: statusGroups.inProgress, name: '进行中', itemStyle: { color: '#409eff' } },
        { value: statusGroups.pending, name: '待执行', itemStyle: { color: '#909399' } },
        { value: statusGroups.overdue, name: '已逾期', itemStyle: { color: '#f56c6c' } }
      ]
    }]
  })
}

const handleViewDetail = (row) => {
  currentAssignment.value = row
  detailVisible.value = true
}

const handleRemind = async (row) => {
  try {
    await inventoryApi.remindExecutor(row.id)
    ElMessage.success('催办通知已发送')
  } catch {
    ElMessage.error('催办失败')
  }
}

const isOverdue = (row) => {
  if (!row.deadline_at || row.status === 'completed') return false
  return new Date(row.deadline_at) < new Date()
}

const getStatusTagType = (status) => {
  const map = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    overdue: 'danger'
  }
  return map[status] || ''
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.mb-16 { margin-bottom: 16px; }

.overall-progress {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
}

.progress-stats {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
}

.progress-stats span {
  font-size: 14px;
}

.progress-text {
  font-size: 18px;
  font-weight: bold;
}

.executor-cell {
  display: flex;
  align-items: center;
}

.ml-8 { margin-left: 8px; }
.mr-8 { margin-right: 8px; }

.text-red { color: #f56c6c; }

.chart-container {
  margin-top: 16px;
}
</style>
```

---

## 3. 管理端 - 查看权限配置

### ViewPermissionConfig.vue

```vue
<template>
  <div class="view-permission-config">
    <el-card header="查看权限配置">
      <!-- 权限规则配置 -->
      <el-form :model="configForm" label-width="140px" class="config-form">
        <el-divider content-position="left">自动权限</el-divider>

        <el-form-item label="部门负责人查看">
          <el-switch
            v-model="configForm.allow_department_leader"
            active-text="允许"
            inactive-text="不允许"
          />
          <div class="form-hint">
            开启后，相关部门负责人可自动查看本部门资产盘点进度
          </div>
        </el-form-item>

        <el-form-item
          v-if="configForm.allow_department_leader"
          label="查看范围"
        >
          <el-radio-group v-model="configForm.department_leader_scope">
            <el-radio value="department_assets">仅本部门资产</el-radio>
            <el-radio value="department_assignments">本部门人员分配</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="资产管理员查看">
          <el-switch
            v-model="configForm.allow_asset_admin"
            active-text="允许"
            inactive-text="不允许"
          />
          <div class="form-hint">
            开启后，具有资产管理员角色的用户可查看全部盘点数据
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="configForm.remark"
            type="textarea"
            :rows="2"
            placeholder="权限配置备注说明"
          />
        </el-form-item>
      </el-form>

      <!-- 指定查看者 -->
      <el-divider content-position="left">指定查看者</el-divider>

      <div class="viewer-actions">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon> 添加查看者
        </el-button>
      </div>

      <!-- 查看者列表 -->
      <el-table :data="viewers" border class="viewer-table">
        <el-table-column label="查看人" width="200">
          <template #default="{ row }">
            <div class="viewer-cell">
              <el-avatar :size="32" :src="row.viewer_avatar">
                {{ row.viewer_name?.charAt(0) }}
              </el-avatar>
              <span class="ml-8">{{ row.viewer_name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="source_display" label="权限来源" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.source === 'manual' ? '' : 'info'"
              size="small"
            >
              {{ row.source_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="scope_display" label="查看范围" width="100" />
        <el-table-column prop="remark" label="说明" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="danger"
              @click="handleRemove(row)"
              :disabled="row.source !== 'manual'"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 保存按钮 -->
      <div class="save-actions">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">
          保存配置
        </el-button>
      </div>
    </el-card>

    <!-- 添加查看者弹窗 -->
    <el-dialog
      v-model="showAddDialog"
      title="添加查看者"
      width="600px"
    >
      <el-form :model="addForm" label-width="100px">
        <el-form-item label="选择人员" required>
          <user-selector
            v-model="addForm.viewer_ids"
            multiple
            placeholder="请选择查看人"
          />
        </el-form-item>
        <el-form-item label="查看范围" required>
          <el-radio-group v-model="addForm.scope">
            <el-radio value="all">全部资产</el-radio>
            <el-radio value="department">本部门资产</el-radio>
            <el-radio value="assignment">指定分配</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          v-if="addForm.scope === 'department'"
          label="选择部门"
        >
          <dept-selector v-model="addForm.scope_config.department_id" />
        </el-form-item>
        <el-form-item
          v-if="addForm.scope === 'assignment'"
          label="选择分配"
        >
          <el-select
            v-model="addForm.scope_config.assignment_ids"
            multiple
            placeholder="请选择分配"
          >
            <el-option
              v-for="assign in assignments"
              :key="assign.id"
              :label="`${assign.executor_name} (${assign.total_assigned}项)`"
              :value="assign.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="说明">
          <el-input
            v-model="addForm.remark"
            placeholder="添加说明（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAddViewers">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { assignmentApi } from '@/api/inventory/assignment'

const route = useRoute()
const taskId = route.params.id

const configForm = reactive({
  allow_department_leader: true,
  department_leader_scope: 'department_assets',
  allow_asset_admin: false,
  remark: ''
})

const viewers = ref([])
const assignments = ref([])
const showAddDialog = ref(false)
const saving = ref(false)

const addForm = reactive({
  viewer_ids: [],
  scope: 'all',
  scope_config: {},
  remark: ''
})

// 获取配置
const fetchConfig = async () => {
  const { data } = await assignmentApi.getViewConfig(taskId)
  Object.assign(configForm, data)
}

// 获取查看者列表
const fetchViewers = async () => {
  const { data } = await assignmentApi.getViewers(taskId)
  viewers.value = data
}

// 获取分配列表（用于选择范围）
const fetchAssignments = async () => {
  const { data } = await assignmentApi.getAssignments(taskId)
  assignments.value = data
}

// 保存配置
const handleSave = async () => {
  try {
    saving.value = true
    await assignmentApi.updateViewConfig(taskId, configForm)
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 取消
const handleCancel = () => {
  fetchConfig()
  ElMessage.info('已取消修改')
}

// 添加查看者
const handleAddViewers = async () => {
  if (addForm.viewer_ids.length === 0) {
    ElMessage.warning('请选择查看人')
    return
  }

  try {
    await assignmentApi.addViewers(taskId, {
      viewer_ids: addForm.viewer_ids,
      scope: addForm.scope,
      scope_config: addForm.scope_config,
      remark: addForm.remark
    })
    ElMessage.success('添加成功')
    showAddDialog.value = false
    // 重置表单
    addForm.viewer_ids = []
    addForm.scope = 'all'
    addForm.scope_config = {}
    addForm.remark = ''
    fetchViewers()
  } catch {
    ElMessage.error('添加失败')
  }
}

// 移除查看者
const handleRemove = async (row) => {
  try {
    await ElMessageBox.confirm('确认移除此查看者？', '提示')
    await assignmentApi.removeViewers(taskId, {
      viewer_ids: [row.viewer_id]
    })
    ElMessage.success('移除成功')
    fetchViewers()
  } catch {
    // cancel
  }
}

onMounted(() => {
  fetchConfig()
  fetchViewers()
  fetchAssignments()
})
</script>

<style scoped>
.view-permission-config {
  padding: 16px;
}

.config-form {
  margin-bottom: 24px;
}

.form-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.viewer-actions {
  margin-bottom: 16px;
}

.viewer-table {
  margin-bottom: 24px;
}

.viewer-cell {
  display: flex;
  align-items: center;
}

.ml-8 {
  margin-left: 8px;
}

.save-actions {
  text-align: right;
  border-top: 1px solid #dcdfe6;
  padding-top: 16px;
}
</style>
```

---

## 4. 用户端 - 我的任务列表

### mobile/MyTasks.vue

```vue
<template>
  <div class="my-tasks">
    <!-- 顶部统计 -->
    <div class="today-summary">
      <div class="summary-card" @click="goToPending">
        <div class="summary-icon pending">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="summary-info">
          <div class="summary-value">{{ todayStats.total_assets - todayStats.completed_assets }}</div>
          <div class="summary-label">待盘点</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon completed">
          <el-icon><Check /></el-icon>
        </div>
        <div class="summary-info">
          <div class="summary-value">{{ todayStats.completed_assets }}</div>
          <div class="summary-label">已盘点</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-icon tasks">
          <el-icon><Document /></el-icon>
        </div>
        <div class="summary-info">
          <div class="summary-value">{{ todayStats.total_count }}</div>
          <div class="summary-label">任务数</div>
        </div>
      </div>
    </div>

    <!-- 任务筛选 -->
    <div class="task-filters">
      <el-segmented v-model="filterStatus" :options="filterOptions" @change="fetchData" />
    </div>

    <!-- 任务列表 -->
    <div class="task-list">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        class="task-card"
        :class="{ 'overdue': task.is_overdue }"
        @click="goToDetail(task)"
      >
        <div class="task-header">
          <span class="task-name">{{ task.task_name }}</span>
          <el-tag :type="getStatusTagType(task.status)" size="small">
            {{ task.status_display }}
          </el-tag>
        </div>
        <div class="task-info">
          <span class="task-code">{{ task.task_code }}</span>
          <span class="task-mode">{{ task.mode_display }}</span>
        </div>
        <div class="task-progress">
          <span class="progress-label">进度</span>
          <el-progress
            :percentage="task.progress"
            :stroke-width="8"
            :show-text="false"
          />
          <span class="progress-text">{{ task.completed_count }}/{{ task.total_assigned }}</span>
        </div>
        <div class="task-deadline" v-if="task.deadline_at">
          <el-icon><Calendar /></el-icon>
          <span>{{ formatDeadline(task.deadline_at) }}</span>
          <el-tag v-if="task.is_overdue" type="danger" size="small">已逾期</el-tag>
        </div>
        <div class="task-action">
          <el-button type="primary" size="small" v-if="task.status === 'pending'">
            开始盘点
          </el-button>
          <el-button type="primary" size="small" v-else-if="task.status === 'in_progress'">
            继续盘点
          </el-button>
          <el-button size="small" v-else>
            查看详情
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="filteredTasks.length === 0"
        description="暂无盘点任务"
        :image-size="120"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Clock, Check, Document, Calendar } from '@element-plus/icons-vue'
import { myInventoryApi } from '@/api/inventory/my'

const router = useRouter()

const filterStatus = ref('all')
const tasks = ref([])
const todayStats = ref({
  total_count: 0,
  total_assets: 0,
  completed_assets: 0,
  assignments: []
})

const filterOptions = [
  { label: '全部', value: 'all' },
  { label: '待执行', value: 'pending' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'completed' }
]

const filteredTasks = computed(() => {
  if (filterStatus.value === 'all') {
    return tasks.value
  }
  return tasks.value.filter(t => t.status === filterStatus.value)
})

const fetchData = async () => {
  const [todayRes, listRes] = await Promise.all([
    myInventoryApi.getToday(),
    myInventoryApi.list()
  ])
  todayStats.value = todayRes.data
  tasks.value = listRes.data
}

const goToDetail = (task) => {
  router.push({
    name: 'MobileTaskDetail',
    params: { id: task.id }
  })
}

const goToPending = () => {
  router.push({ name: 'MobileAssetList', query: { status: 'pending' } })
}

const getStatusTagType = (status) => {
  const map = {
    pending: 'warning',
    in_progress: 'primary',
    completed: 'success'
  }
  return map[status] || ''
}

const formatDeadline = (dateStr) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24))

  if (days < 0) return '已逾期'
  if (days === 0) return '今天截止'
  if (days === 1) return '明天截止'
  return `${days}天后截止`
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.my-tasks {
  padding: 16px;
  background: #f5f5f5;
  min-height: 100vh;
}

.today-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.summary-card {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.summary-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.summary-icon.pending { background: #e6a23c; }
.summary-icon.completed { background: #67c23a; }
.summary-icon.tasks { background: #409eff; }

.summary-info {
  margin-left: 12px;
}

.summary-value {
  font-size: 20px;
  font-weight: bold;
}

.summary-label {
  font-size: 12px;
  color: #909399;
}

.task-filters {
  margin-bottom: 16px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.task-card.overdue {
  border-left: 4px solid #f56c6c;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-name {
  font-size: 16px;
  font-weight: bold;
}

.task-info {
  display: flex;
  gap: 12px;
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.task-progress .el-progress {
  flex: 1;
}

.progress-label {
  font-size: 12px;
  color: #909399;
}

.progress-text {
  font-size: 12px;
  color: #606266;
}

.task-deadline {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.task-action {
  text-align: right;
}
</style>
```

---

## 4. 用户端 - 待盘资产列表

### mobile/AssetList.vue

```vue
<template>
  <div class="asset-list">
    <!-- 头部 -->
    <div class="page-header">
      <el-icon @click="$router.back()" class="back-btn"><ArrowLeft /></el-icon>
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索资产编码/名称"
        prefix-icon="Search"
        clearable
      />
      <el-button @click="showFilter = true">筛选</el-button>
    </div>

    <!-- 统计条 -->
    <div class="stats-bar">
      <span>共 {{ filteredAssets.length }} 项</span>
      <span>已盘 {{ scannedCount }} 项</span>
      <span>未盘 {{ filteredAssets.length - scannedCount }} 项</span>
    </div>

    <!-- 资产列表 -->
    <div class="assets">
      <div
        v-for="asset in filteredAssets"
        :key="asset.snapshot_id"
        class="asset-card"
        :class="{ scanned: asset.is_scanned }"
        @click="goToScan(asset)"
      >
        <div class="asset-main">
          <div class="asset-icon">
            <el-icon v-if="asset.is_scanned" class="scanned-icon"><CircleCheck /></el-icon>
            <el-icon v-else class="unscanned-icon"><Circle /></el-icon>
          </div>
          <div class="asset-info">
            <div class="asset-code">{{ asset.asset_code }}</div>
            <div class="asset-name">{{ asset.asset_name }}</div>
            <div class="asset-meta">
              <span class="location">
                <el-icon><Location /></el-icon>
                {{ asset.location || '未设置' }}
              </span>
              <span class="custodian">
                <el-icon><User /></el-icon>
                {{ asset.custodian || '未设置' }}
              </span>
            </div>
          </div>
        </div>
        <div class="asset-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="filteredAssets.length === 0"
      description="暂无资产"
    />

    <!-- 筛选弹窗 -->
    <el-drawer v-model="showFilter" title="筛选条件" direction="btt">
      <el-form label-position="top">
        <el-form-item label="状态">
          <el-radio-group v-model="filterStatus">
            <el-radio value="all">全部</el-radio>
            <el-radio value="pending">未盘</el-radio>
            <el-radio value="scanned">已盘</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, ArrowRight, Search, Location, User,
  Circle, CircleCheck
} from '@element-plus/icons-vue'
import { myInventoryApi } from '@/api/inventory/my'

const route = useRoute()
const router = useRouter()

const assignmentId = route.query.assignment_id
const status = route.query.status

const assets = ref([])
const searchText = ref('')
const filterStatus = ref('all')
const showFilter = ref(false)

const pageTitle = computed(() => {
  if (status === 'pending') return '待盘点资产'
  if (status === 'scanned') return '已盘点资产'
  return '资产列表'
})

const filteredAssets = computed(() => {
  let result = assets.value

  // 搜索
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(a =>
      a.asset_code.toLowerCase().includes(search) ||
      a.asset_name.toLowerCase().includes(search)
    )
  }

  // 状态筛选
  if (filterStatus.value === 'pending') {
    result = result.filter(a => !a.is_scanned)
  } else if (filterStatus.value === 'scanned') {
    result = result.filter(a => a.is_scanned)
  }

  return result
})

const scannedCount = computed(() => {
  return assets.value.filter(a => a.is_scanned).length
})

const fetchData = async () => {
  if (status === 'pending') {
    const { data } = await myInventoryApi.getPendingAssets({ assignment_id: assignmentId })
    assets.value = data.map(a => ({ ...a, is_scanned: false }))
  } else if (status === 'scanned') {
    const { data } = await myInventoryApi.getScannedAssets({ assignment_id: assignmentId })
    assets.value = data.map(a => ({ ...a, is_scanned: true }))
  } else {
    // 全部
    const [pendingRes, scannedRes] = await Promise.all([
      myInventoryApi.getPendingAssets({ assignment_id: assignmentId }),
      myInventoryApi.getScannedAssets({ assignment_id: assignmentId })
    ])
    assets.value = [
      ...pendingRes.data.map(a => ({ ...a, is_scanned: false })),
      ...scannedRes.data.map(a => ({ ...a, is_scanned: true }))
    ]
  }
}

const goToScan = (asset) => {
  router.push({
    name: 'MobileScan',
    params: {
      snapshot_id: asset.snapshot_id,
      asset_id: asset.asset_id
    }
  })
}
</script>

<style scoped>
.asset-list {
  padding: 16px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background: white;
}

.back-btn {
  font-size: 20px;
  margin-right: 16px;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.search-bar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: white;
}

.stats-bar {
  display: flex;
  justify-content: space-between;
  padding: 8px 16px;
  font-size: 12px;
  color: #606266;
  background: white;
}

.assets {
  padding: 0 16px;
}

.asset-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border-radius: 8px;
  border-left: 3px solid #e6a23c;
}

.asset-card.scanned {
  border-left-color: #67c23a;
}

.asset-main {
  display: flex;
  align-items: center;
  flex: 1;
}

.asset-icon {
  font-size: 24px;
  margin-right: 12px;
}

.scanned-icon { color: #67c23a; }
.unscanned-icon { color: #dcdfe6; }

.asset-info {
  flex: 1;
}

.asset-code {
  font-size: 14px;
  font-weight: bold;
}

.asset-name {
  font-size: 14px;
  color: #606266;
}

.asset-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.asset-meta span {
  display: flex;
  align-items: center;
  gap: 2px;
}

.asset-arrow {
  color: #c0c4cc;
}
</style>
```

---

## 5. 用户端 - 扫码盘点页面

### mobile/ScanPage.vue

```vue
<template>
  <div class="scan-page">
    <!-- 扫描区域 -->
    <div class="scan-area" v-if="!scannedAsset">
      <video
        ref="videoRef"
        class="scan-video"
        autoplay
        playsinline
        muted
      ></video>
      <canvas ref="canvasRef" class="scan-canvas" style="display:none"></canvas>

      <!-- 扫描框 -->
      <div class="scan-frame">
        <div class="scan-line"></div>
      </div>

      <!-- 提示 -->
      <div class="scan-hint">
        将二维码放入框内即可自动扫描
      </div>

      <!-- 手动输入 -->
      <div class="manual-input">
        <el-button @click="showManualInput = true">手动输入编码</el-button>
      </div>
    </div>

    <!-- 扫描结果 -->
    <div class="scan-result" v-else>
      <div class="result-header">
        <el-icon @click="resetScan" class="back-btn"><ArrowLeft /></el-icon>
        <span>扫描结果</span>
      </div>

      <div class="asset-detail">
        <div class="detail-row">
          <span class="label">资产编码</span>
          <span class="value">{{ scannedAsset.asset_code }}</span>
        </div>
        <div class="detail-row">
          <span class="label">资产名称</span>
          <span class="value">{{ scannedAsset.asset_name }}</span>
        </div>
        <div class="detail-row">
          <span class="label">存放地点</span>
          <span class="value">{{ scannedAsset.location || '未设置' }}</span>
        </div>
        <div class="detail-row">
          <span class="label">保管人</span>
          <span class="value">{{ scannedAsset.custodian || '未设置' }}</span>
        </div>
      </div>

      <!-- 盘点状态选择 -->
      <div class="status-selector">
        <h3>盘点状态</h3>
        <div class="status-options">
          <div
            class="status-option"
            :class="{ active: scanStatus === 'normal' }"
            @click="scanStatus = 'normal'"
          >
            <el-icon><CircleCheck /></el-icon>
            <span>正常</span>
          </div>
          <div
            class="status-option"
            :class="{ active: scanStatus === 'location_changed' }"
            @click="scanStatus = 'location_changed'"
          >
            <el-icon><Location /></el-icon>
            <span>位置变更</span>
          </div>
          <div
            class="status-option"
            :class="{ active: scanStatus === 'damaged' }"
            @click="scanStatus = 'damaged'"
          >
            <el-icon><Warning /></el-icon>
            <span>损坏</span>
          </div>
        </div>
      </div>

      <!-- 位置变更时显示 -->
      <div v-if="scanStatus === 'location_changed'" class="location-input">
        <h4>请输入实际位置</h4>
        <el-input v-model="actualLocation" placeholder="输入实际存放位置" />
      </div>

      <!-- 备注输入 -->
      <div class="remark-input">
        <h4>备注</h4>
        <el-input
          v-model="remark"
          type="textarea"
          :rows="3"
          placeholder="输入备注信息（可选）"
        />
      </div>

      <!-- 提交按钮 -->
      <div class="submit-actions">
        <el-button @click="resetScan">重扫</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确认提交
        </el-button>
      </div>

      <!-- 拍照按钮 -->
      <div class="photo-actions">
        <el-button @click="takePhoto">
          <el-icon><Camera /></el-icon>
          拍照记录
        </el-button>
      </div>
    </div>

    <!-- 手动输入弹窗 -->
    <el-dialog v-model="showManualInput" title="手动输入资产编码" width="400px">
      <el-input
        v-model="manualCode"
        placeholder="请输入资产编码"
        @keyup.enter="handleManualInput"
      />
      <template #footer>
        <el-button @click="showManualInput = false">取消</el-button>
        <el-button type="primary" @click="handleManualInput">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, CircleCheck, Location, Warning, Camera
} from '@element-plus/icons-vue'
import { BrowserMultiFormatReader } from '@zxing/library'
import { myInventoryApi } from '@/api/inventory/my'

const route = useRoute()
const router = useRouter()

const snapshot_id = route.params.snapshot_id
const asset_id = route.params.asset_id
const assignment_id = route.query.assignment_id

const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const codeReader = new BrowserMultiFormatReader()

const scannedAsset = ref(null)
const scanStatus = ref('normal')
const actualLocation = ref('')
const remark = ref('')
const submitting = ref(false)
const showManualInput = ref(false)
const manualCode = ref('')

// 启动相机
const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    })
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      videoRef.value.play()
      startScan()
    }
  } catch (error) {
    ElMessage.error('无法访问相机，请使用手动输入')
  }
}

// 开始扫描
const startScan = () => {
  if (!videoRef.value) return

  codeReader.decodeFromVideoDevice(
    videoRef.value,
    (result) => {
      if (result) {
        handleScanResult(result.text)
      }
    }
  )
}

// 处理扫描结果
const handleScanResult = async (qrData: string) => {
  try {
    codeReader.reset()
    const { data } = await myInventoryApi.parseQRCode(qrData)

    if (data.asset_id) {
      scannedAsset.value = data
      // 如果在分配任务中，检查资产是否在分配范围内
      if (assignment_id) {
        const checkRes = await myInventoryApi.checkInAssignment(assignment_id, data.asset_id)
        if (!checkRes.data.in_assignment) {
          ElMessage.warning('该资产不在您的盘点范围内')
        }
      }
    } else {
      ElMessage.error('二维码格式错误')
    }
  } catch (error) {
    ElMessage.error('解析二维码失败')
  }
}

// 手动输入
const handleManualInput = async () => {
  if (!manualCode.value) return

  try {
    const { data } = await myInventoryApi.getByCode(manualCode.value)
    scannedAsset.value = data
    showManualInput.value = false
  } catch {
    ElMessage.error('未找到该资产')
  }
}

// 重置扫描
const resetScan = () => {
  scannedAsset.value = null
  scanStatus.value = 'normal'
  actualLocation.value = ''
  remark.value = ''
  startScan()
}

// 提交盘点
const handleSubmit = async () => {
  try {
    submitting.value = true

    await myInventoryApi.recordScan({
      task_id: route.query.task_id,
      assignment_id: assignment_id,
      asset_id: scannedAsset.value.asset_id,
      scan_method: 'qr',
      status: scanStatus.value,
      actual_location: actualLocation.value,
      remark: remark.value
    })

    ElMessage.success('提交成功')
    router.back()
  } catch {
    ElMessage.error('提交失败')
  } finally {
    submitting.value = false
  }
}

// 拍照
const takePhoto = () => {
  // 实现拍照功能
  ElMessage.info('拍照功能开发中')
}

onMounted(() => {
  startCamera()
})

onUnmounted(() => {
  codeReader.reset()
  if (videoRef.value && videoRef.value.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(track => track.stop())
  }
})
</script>

<style scoped>
.scan-page {
  min-height: 100vh;
  background: #000;
}

.scan-area {
  position: relative;
  height: 100vh;
}

.scan-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scan-canvas {
  display: none;
}

.scan-frame {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 280px;
  height: 280px;
  border: 2px solid rgba(255,255,255,0.5);
  border-radius: 8px;
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(to right, transparent, #67c23a, transparent);
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% { top: 0; }
  50% { top: 100%; }
  100% { top: 0; }
}

.scan-hint {
  position: absolute;
  bottom: 200px;
  left: 0;
  right: 0;
  text-align: center;
  color: white;
  font-size: 14px;
}

.manual-input {
  position: absolute;
  bottom: 120px;
  left: 0;
  right: 0;
  text-align: center;
}

/* 扫描结果 */
.scan-result {
  min-height: 100vh;
  background: #f5f5f5;
}

.result-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background: white;
  border-bottom: 1px solid #dcdfe6;
}

.back-btn {
  font-size: 20px;
  margin-right: 16px;
}

.asset-detail {
  background: white;
  padding: 16px;
  margin: 12px;
  border-radius: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f5f7fa;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row .label {
  color: #909399;
  font-size: 14px;
}

.detail-row .value {
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.status-selector {
  background: white;
  padding: 16px;
  margin: 12px;
  border-radius: 8px;
}

.status-selector h3 {
  font-size: 16px;
  margin-bottom: 12px;
}

.status-options {
  display: flex;
  gap: 12px;
}

.status-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  font-size: 12px;
}

.status-option.active {
  border-color: #409eff;
  background: #ecf5ff;
  color: #409eff;
}

.status-option .el-icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.location-input {
  background: white;
  padding: 16px;
  margin: 12px;
  border-radius: 8px;
}

.location-input h4 {
  font-size: 14px;
  margin-bottom: 8px;
}

.remark-input {
  background: white;
  padding: 16px;
  margin: 12px;
  border-radius: 8px;
}

.remark-input h4 {
  font-size: 14px;
  margin-bottom: 8px;
}

.submit-actions {
  display: flex;
  gap: 12px;
  padding: 16px;
}

.photo-actions {
  padding: 0 16px 16px;
}

.photo-actions .el-button {
  width: 100%;
}
</style>
```

---

## 6. API封装

```typescript
// src/api/inventory/assignment.ts

import request from '@/utils/request'

// 管理端API
export const assignmentApi = {
  // 分配相关
  getAssignments(taskId: string) {
    return request.get(`/api/inventory/tasks/${taskId}/assignments/`)
  },

  createAssignments(taskId: string, data: any) {
    return request.post(`/api/inventory/tasks/${taskId}/create-assignments/`, data)
  },

  autoAssignTemplate(taskId: string, data: any) {
    return request.post(`/api/inventory/tasks/${taskId}/auto-assign-template/`, data)
  },

  autoAssignRules(taskId: string) {
    return request.post(`/api/inventory/tasks/${taskId}/auto-assign-rules/`)
  },

  assignCustodian(taskId: string) {
    return request.post(`/api/inventory/tasks/${taskId}/assign-custodian/`)
  },

  assignRandom(taskId: string, data: any) {
    return request.post(`/api/inventory/tasks/${taskId}/assign-random/`, data)
  },

  // 进度监控
  getProgress(taskId: string) {
    return request.get(`/api/inventory/tasks/${taskId}/progress/`)
  },

  remindExecutor(assignmentId: string) {
    return request.post(`/api/inventory/assignments/${assignmentId}/remind/`)
  },

  // 数据源
  getTemplates() {
    return request.get('/api/inventory/assignment-templates/')
  },

  getEffectiveRules(taskId: string) {
    return request.get(`/api/inventory/tasks/${taskId}/effective-rules/`)
  },

  getCustodianPreview(taskId: string) {
    return request.get(`/api/inventory/tasks/${taskId}/custodian-preview/`)
  },

  getUnassignedAssets(taskId: string) {
    return request.get(`/api/inventory/tasks/${taskId}/unassigned-assets/`)
  },

  // 查看权限相关
  getViewConfig(taskId: string) {
    return request.get(`/api/inventory/tasks/${taskId}/view-config/`)
  },

  updateViewConfig(taskId: string, data: any) {
    return request.put(`/api/inventory/tasks/${taskId}/view-config/`, data)
  },

  getViewers(taskId: string, params?: any) {
    return request.get(`/api/inventory/tasks/${taskId}/viewers/`, { params })
  },

  addViewers(taskId: string, data: any) {
    return request.post(`/api/inventory/tasks/${taskId}/viewers/`, data)
  },

  removeViewers(taskId: string, data: any) {
    return request.delete(`/api/inventory/tasks/${taskId}/viewers/`, { data })
  },

  getMyPermission(taskId: string) {
    return request.get(`/api/inventory/tasks/${taskId}/my-permission/`)
  },

  getViewLogs(taskId: string, params?: any) {
    return request.get(`/api/inventory/tasks/${taskId}/view-logs/`, { params })
  }
}

// 用户端API
export const myInventoryApi = {
  // 我的任务
  list() {
    return request.get('/api/inventory/my/tasks/')
  },

  getToday() {
    return request.get('/api/inventory/my/today/')
  },

  // 资产列表
  getPendingAssets(params: any) {
    return request.get('/api/inventory/my/pending-assets/', { params })
  },

  getScannedAssets(params: any) {
    return request.get('/api/inventory/my/scanned-assets/', { params })
  },

  // 扫描操作
  parseQRCode(qrData: string) {
    return request.post('/api/inventory/my/parse-qr/', { qr_data: qrData })
  },

  getByCode(assetCode: string) {
    return request.get(`/api/inventory/my/asset-by-code/${assetCode}/`)
  },

  checkInAssignment(assignmentId: string, assetId: string) {
    return request.get(`/api/inventory/my/check-assignment/`, {
      params: { assignment_id: assignmentId, asset_id: assetId }
    })
  },

  recordScan(data: any) {
    return request.post('/api/inventory/my/record-scan/', data)
  },

  // 任务操作
  startAssignment(assignmentId: string) {
    return request.post(`/api/inventory/my/start/`, { assignment_id: assignmentId })
  },

  completeAssignment(assignmentId: string) {
    return request.post(`/api/inventory/my/complete/`, { assignment_id: assignmentId })
  }
}
```

---

## 后续任务

所有Phase已完成！
