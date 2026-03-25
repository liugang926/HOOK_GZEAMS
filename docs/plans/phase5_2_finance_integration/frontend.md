# Phase 5.2: 财务凭证集成 - 前端实现

## 概述

实现财务凭证管理前端页面，包括凭证模板配置、凭证列表、凭证生成、审核和推送等功能。

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

## 1. 财务凭证列表页

### VoucherList.vue

```vue
<template>
  <div class="voucher-list">
    <el-card>
      <!-- 搜索筛选 -->
      <el-form :model="queryForm" :inline="true" class="search-form">
        <el-form-item label="凭证号">
          <el-input v-model="queryForm.voucher_no" placeholder="请输入" clearable />
        </el-form-item>
        <el-form-item label="业务类型">
          <el-select v-model="queryForm.business_type" placeholder="全部" clearable>
            <el-option label="资产购入" value="asset_purchase" />
            <el-option label="资产折旧" value="asset_depreciation" />
            <el-option label="资产处置" value="asset_disposal" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="全部" clearable>
            <el-option label="草稿" value="draft" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已审核" value="approved" />
            <el-option label="已过账" value="posted" />
          </el-select>
        </el-form-item>
        <el-form-item label="凭证日期">
          <el-date-picker
            v-model="queryForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 操作栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon> 新增凭证
        </el-button>
        <el-button @click="handleBatchPush" :disabled="selectedRows.length === 0">
          批量推送
        </el-button>
        <el-button @click="handleExport">导出</el-button>
      </div>

      <!-- 凭证表格 -->
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="voucher_no" label="凭证号" width="140" />
        <el-table-column prop="voucher_date" label="凭证日期" width="110" />
        <el-table-column prop="business_type_display" label="业务类型" width="100" />
        <el-table-column prop="voucher_type" label="凭证字" width="80" />
        <el-table-column prop="description" label="摘要" show-overflow-tooltip />
        <el-table-column prop="total_debit" label="借方合计" width="120" align="right">
          <template #default="{ row }">{{ formatMoney(row.total_debit) }}</template>
        </el-table-column>
        <el-table-column prop="total_credit" label="贷方合计" width="120" align="right">
          <template #default="{ row }">{{ formatMoney(row.total_credit) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status_display }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="integration_system" label="推送系统" width="100">
          <template #default="{ row }">
            {{ row.integration_system ? getSystemName(row.integration_system) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">详情</el-button>
            <el-button
              link
              type="primary"
              @click="handleEdit(row)"
              v-if="row.status === 'draft'"
            >
              编辑
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleSubmit(row)"
              v-if="row.status === 'draft'"
            >
              提交
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleApprove(row)"
              v-if="row.status === 'submitted'"
            >
              审核
            </el-button>
            <el-button
              link
              type="primary"
              @click="handlePush(row)"
              v-if="['approved', 'submitted'].includes(row.status)"
            >
              推送
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
      />
    </el-card>

    <!-- 凭证详情弹窗 -->
    <VoucherDetailDialog
      v-model="detailVisible"
      :voucher="currentVoucher"
      @approve="handleApproveSubmit"
      @reject="handleReject"
    />

    <!-- 凭证编辑弹窗 -->
    <VoucherFormDialog
      v-model="formVisible"
      :voucher="editingVoucher"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { financeApi } from '@/api/assets/finance'
import VoucherDetailDialog from './VoucherDetailDialog.vue'
import VoucherFormDialog from './VoucherFormDialog.vue'

const queryForm = reactive({
  voucher_no: '',
  business_type: '',
  status: '',
  date_range: []
})

const tableData = ref([])
const loading = ref(false)
const selectedRows = ref([])
const detailVisible = ref(false)
const formVisible = ref(false)
const currentVoucher = ref(null)
const editingVoucher = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      ...queryForm,
      voucher_date_from: queryForm.date_range?.[0],
      voucher_date_to: queryForm.date_range?.[1],
      page: pagination.page,
      size: pagination.size
    }
    const { data } = await financeApi.listVouchers(params)
    tableData.value = data.results
    pagination.total = data.count
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  Object.assign(queryForm, {
    voucher_no: '',
    business_type: '',
    status: '',
    date_range: []
  })
  handleSearch()
}

const handleCreate = () => {
  editingVoucher.value = null
  formVisible.value = true
}

const handleView = (row) => {
  currentVoucher.value = row
  detailVisible.value = true
}

const handleEdit = (row) => {
  editingVoucher.value = row
  formVisible.value = true
}

const handleSubmit = async (row) => {
  try {
    await ElMessageBox.confirm('确认提交此凭证？', '提示')
    await financeApi.submitVoucher(row.id)
    ElMessage.success('提交成功')
    fetchData()
  } catch {
    // cancel
  }
}

const handleApprove = (row) => {
  currentVoucher.value = row
  detailVisible.value = true
}

const handleApproveSubmit = async (data) => {
  await financeApi.approveVoucher(currentVoucher.value.id, data)
  ElMessage.success('审核成功')
  detailVisible.value = false
  fetchData()
}

const handleReject = async (comment) => {
  await financeApi.rejectVoucher(currentVoucher.value.id, { comment })
  ElMessage.success('已驳回')
  detailVisible.value = false
  fetchData()
}

const handlePush = async (row) => {
  try {
    await ElMessageBox.confirm('确认推送到ERP系统？', '提示')
    const { data } = await financeApi.pushVoucher(row.id)
    if (data.success) {
      ElMessage.success(`推送成功，外部凭证号: ${data.external_voucher_no}`)
    } else {
      ElMessage.error(`推送失败: ${data.error}`)
    }
    fetchData()
  } catch {
    // cancel
  }
}

const handleBatchPush = async () => {
  try {
    await ElMessageBox.confirm(`确认推送${selectedRows.value.length}张凭证？`, '提示')
    const results = await Promise.allSettled(
      selectedRows.value.map(row => financeApi.pushVoucher(row.id))
    )
    const success = results.filter(r => r.status === 'fulfilled').length
    ElMessage.success(`成功推送${success}/${selectedRows.value.length}张凭证`)
    fetchData()
  } catch {
    // cancel
  }
}

const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

const handleExport = async () => {
  // 导出凭证
  ElMessage.info('导出功能开发中')
}

const formatMoney = (val) => {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
}

const getStatusType = (status) => {
  const map = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    posted: '',
    rejected: 'danger'
  }
  return map[status] || ''
}

const getSystemName = (type) => {
  const map = {
    m18: 'M18',
    sap: 'SAP',
    kingdee: '金蝶',
    yonyou: '用友'
  }
  return map[type] || type
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.search-form {
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
```

---

## 2. 凭证详情弹窗

### VoucherDetailDialog.vue

```vue
<template>
  <el-dialog
    v-model="visible"
    title="凭证详情"
    width="800px"
    @close="handleClose"
  >
    <div v-if="voucher">
      <!-- 凭证头部 -->
      <el-descriptions :column="3" border class="mb-16">
        <el-descriptions-item label="凭证号">
          {{ voucher.voucher_no }}
        </el-descriptions-item>
        <el-descriptions-item label="凭证日期">
          {{ voucher.voucher_date }}
        </el-descriptions-item>
        <el-descriptions-item label="凭证字">
          {{ voucher.voucher_type }}
        </el-descriptions-item>
        <el-descriptions-item label="业务类型">
          {{ voucher.business_type_display }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(voucher.status)">
            {{ voucher.status_display }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="推送状态">
          {{ voucher.external_voucher_no || '未推送' }}
        </el-descriptions-item>
        <el-descriptions-item label="摘要" :span="3">
          {{ voucher.description }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 分录明细 -->
      <el-table :data="voucher.entries" border size="small">
        <el-table-column prop="line_no" label="行号" width="60" />
        <el-table-column prop="account_code" label="科目编码" width="120" />
        <el-table-column prop="account_name" label="科目名称" />
        <el-table-column prop="debit" label="借方金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.debit > 0 ? 'text-red' : ''">
              {{ formatMoney(row.debit) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="credit" label="贷方金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="row.credit > 0 ? 'text-green' : ''">
              {{ formatMoney(row.credit) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="摘要" />
      </el-table>

      <!-- 合计 -->
      <div class="voucher-summary">
        <span>借方合计: <strong class="text-red">{{ formatMoney(voucher.total_debit) }}</strong></span>
        <span>贷方合计: <strong class="text-green">{{ formatMoney(voucher.total_credit) }}</strong></span>
      </div>

      <!-- 审核信息 -->
      <div v-if="voucher.status !== 'draft'" class="audit-info mt-16">
        <el-divider content-position="left">审核信息</el-divider>
        <p v-if="voucher.approved_by">
          审核人: {{ voucher.approved_by.full_name }}
          | 审核时间: {{ voucher.approved_at }}
        </p>
        <p v-if="voucher.approve_comment">审核意见: {{ voucher.approve_comment }}</p>
      </div>
    </div>

    <!-- 审核操作区 -->
    <template #footer v-if="voucher && voucher.status === 'submitted'">
      <el-button @click="handleReject">驳回</el-button>
      <el-button type="primary" @click="handleApprove">审核通过</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean,
  voucher: Object
})

const emit = defineEmits(['update:modelValue', 'approve', 'reject'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formatMoney = (val) => {
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
}

const getStatusType = (status) => {
  const map = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    posted: ''
  }
  return map[status] || ''
}

const handleApprove = () => {
  emit('approve', { approved: true, comment: '' })
}

const handleReject = async () => {
  const comment = prompt('请输入驳回原因：')
  if (comment) {
    emit('reject', comment)
  }
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.mb-16 {
  margin-bottom: 16px;
}

.mt-16 {
  margin-top: 16px;
}

.voucher-summary {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  margin-top: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.text-red {
  color: #f56c6c;
}

.text-green {
  color: #67c23a;
}

.audit-info {
  color: #606266;
}
</style>
```

---

## 3. 凭证模板配置

### VoucherTemplateList.vue

```vue
<template>
  <div class="voucher-template-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>凭证模板配置</span>
          <el-button type="primary" @click="handleCreate">新增模板</el-button>
        </div>
      </template>

      <!-- 业务类型切换 -->
      <el-tabs v-model="activeType" @tab-change="fetchData">
        <el-tab-pane
          v-for="type in businessTypes"
          :key="type.value"
          :label="type.label"
          :name="type.value"
        >
          <el-table :data="tableData" border>
            <el-table-column prop="template_name" label="模板名称" />
            <el-table-column prop="voucher_type" label="凭证字" width="80" />
            <el-table-column prop="default_description" label="默认摘要" />
            <el-table-column label="分录数量" width="100">
              <template #default="{ row }">
                {{ row.entries_config?.length || 0 }}
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="80">
              <template #default="{ row }">
                <el-switch v-model="row.is_active" @change="handleToggle(row)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleEdit(row)">
                  编辑
                </el-button>
                <el-button link type="primary" @click="handlePreview(row)">
                  预览
                </el-button>
                <el-button link type="danger" @click="handleDelete(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 模板编辑弹窗 -->
    <VoucherTemplateDialog
      v-model="dialogVisible"
      :template="editingTemplate"
      :business-type="activeType"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { financeApi } from '@/api/assets/finance'
import VoucherTemplateDialog from './VoucherTemplateDialog.vue'

const activeType = ref('asset_purchase')
const tableData = ref([])
const dialogVisible = ref(false)
const editingTemplate = ref(null)

const businessTypes = [
  { value: 'asset_purchase', label: '资产购入' },
  { value: 'asset_depreciation', label: '资产折旧' },
  { value: 'asset_disposal', label: '资产处置' },
  { value: 'asset_transfer', label: '资产调拨' }
]

const fetchData = async () => {
  const { data } = await financeApi.listTemplates({
    business_type: activeType.value
  })
  tableData.value = data
}

const handleCreate = () => {
  editingTemplate.value = null
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editingTemplate.value = row
  dialogVisible.value = true
}

const handleToggle = async (row) => {
  await financeApi.updateTemplate(row.id, { is_active: row.is_active })
  ElMessage.success('状态已更新')
}

const handlePreview = (row) => {
  // 预览模板
  ElMessage.info('预览功能开发中')
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确认删除此模板？', '警告')
  await financeApi.deleteTemplate(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(() => {
  fetchData()
})
</script>
```

---

## 4. API封装

```typescript
// src/api/assets/finance.ts

import request from '@/utils/request'

export const financeApi = {
  // 凭证模板
  listTemplates(params?: any) {
    return request.get('/api/finance/voucher-templates/', { params })
  },
  createTemplate(data: any) {
    return request.post('/api/finance/voucher-templates/', data)
  },
  updateTemplate(id: string, data: any) {
    return request.put(`/api/finance/voucher-templates/${id}/`, data)
  },
  deleteTemplate(id: string) {
    return request.delete(`/api/finance/voucher-templates/${id}/`)
  },

  // 财务凭证
  listVouchers(params?: any) {
    return request.get('/api/finance/vouchers/', { params })
  },
  createVoucher(data: any) {
    return request.post('/api/finance/vouchers/', data)
  },
  getVoucher(id: string) {
    return request.get(`/api/finance/vouchers/${id}/`)
  },
  updateVoucher(id: string, data: any) {
    return request.put(`/api/finance/vouchers/${id}/`, data)
  },
  deleteVoucher(id: string) {
    return request.delete(`/api/finance/vouchers/${id}/`)
  },
  submitVoucher(id: string) {
    return request.post(`/api/finance/vouchers/${id}/submit/`)
  },
  approveVoucher(id: string, data: any) {
    return request.post(`/api/finance/vouchers/${id}/approve/`, data)
  },
  rejectVoucher(id: string, data: any) {
    return request.post(`/api/finance/vouchers/${id}/reject/`, data)
  },
  pushVoucher(id: string, data?: any) {
    return request.post(`/api/finance/vouchers/${id}/push/`, data)
  },

  // 业务凭证生成
  generateAssetPurchaseVoucher(data: any) {
    return request.post('/api/finance/vouchers/generate/asset-purchase/', data)
  },
  generateDepreciationVoucher(data: any) {
    return request.post('/api/finance/vouchers/generate/depreciation/', data)
  },
  generateDisposalVoucher(data: any) {
    return request.post('/api/finance/vouchers/generate/disposal/', data)
  }
}
```

---

## 后续任务

1. 实现其他ERP系统的财务适配器
2. 扩展更多业务类型的凭证模板
