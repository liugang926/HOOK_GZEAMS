# Phase 1.4: 资产卡片CRUD - 前端实现

## 任务概述
实现资产卡片的前端页面，包括列表查询、表单编辑、二维码展示等功能。

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

## 页面组件

### 1. 资产列表页面

```vue
<!-- frontend/src/views/assets/AssetList.vue -->
<template>
  <div class="asset-list">
    <!-- 页面头部 -->
    <el-page-header title="资产卡片" @back="goBack">
      <template #extra>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增资产
        </el-button>
      </template>
    </el-page-header>

    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="queryForm" class="search-form">
        <el-form-item label="关键词">
          <el-input
            v-model="queryForm.search"
            placeholder="资产编码/名称/序列号"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="资产分类">
          <el-cascader
            v-model="queryForm.category"
            :options="categoryTree"
            :props="{ value: 'id', label: 'name', checkStrictly: true }"
            clearable
            placeholder="全部分类"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="资产状态">
          <DictionarySelect 
            code="ASSET_STATUS" 
            v-model="queryForm.status" 
            clearable 
            placeholder="全部状态" 
            style="width: 150px" 
          />
        </el-form-item>
        <el-form-item label="使用部门">
          <el-select v-model="queryForm.department" clearable placeholder="全部部门" style="width: 150px">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="保管人">
          <el-select
            v-model="queryForm.custodian"
            filterable
            remote
            :remote-method="searchUsers"
            placeholder="选择保管人"
            clearable
            style="width: 150px"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="user.real_name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 统计信息 -->
      <div class="statistics-bar" v-if="statistics.total">
        <el-tag type="info">总数: {{ statistics.total }}</el-tag>
        <el-tag type="success">在用: {{ statistics.by_status.in_use || 0 }}</el-tag>
        <el-tag type="warning">闲置: {{ statistics.by_status.idle || 0 }}</el-tag>
        <el-tag type="info">总价值: ¥{{ formatMoney(statistics.total_value) }}</el-tag>
      </div>
    </el-card>

    <!-- 资产列表 -->
    <el-card class="table-card">
      <el-table
        :data="assetList"
        v-loading="loading"
        border
        stripe
        @row-click="handleRowClick"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="asset_code" label="资产编码" width="150" fixed />
        <el-table-column prop="asset_name" label="资产名称" width="200" show-overflow-tooltip />
        <el-table-column prop="asset_category.name" label="分类" width="120" />
        <el-table-column prop="specification" label="规格型号" width="150" show-overflow-tooltip />
        <el-table-column prop="purchase_price" label="原值" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatMoney(row.purchase_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="department.name" label="使用部门" width="120" />
        <el-table-column prop="custodian.real_name" label="保管人" width="100">
          <template #default="{ row }">
            {{ row.custodian?.real_name || row.custodian?.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="location.name" label="存放地点" width="120" />
        <el-table-column prop="asset_status" label="状态" width="90" fixed="right">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.asset_status)">
              {{ getStatusLabel(row.asset_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="handleView(row)">查看</el-button>
            <el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button>
            <el-button link @click.stop="handleQRCode(row)">二维码</el-button>
            <el-button link type="danger" @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </el-card>

    <!-- 批量操作栏 -->
    <div class="batch-bar" v-if="selectedAssets.length > 0">
      <span>已选择 {{ selectedAssets.length }} 项</span>
      <el-button size="small" @click="handleBatchQRCode">批量二维码</el-button>
      <el-button size="small" @click="handleBatchExport">导出</el-button>
    </div>

    <!-- 二维码弹窗 -->
    <el-dialog v-model="qrDialogVisible" title="资产二维码" width="400px">
      <div class="qr-code-container">
        <img :src="qrCodeUrl" alt="二维码" v-if="qrCodeUrl" />
        <p class="qr-code-text">{{ currentAsset.asset_code }}</p>
        <p class="qr-code-name">{{ currentAsset.asset_name }}</p>
      </div>
      <template #footer>
        <el-button @click="qrDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="downloadQRCode">下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getAssetList,
  getAssetStatistics,
  deleteAsset,
  getAssetQRCode
} from '@/api/assets'
import { getCategoryTree } from '@/api/assetCategory'
import { getDepartments } from '@/api/organization'
import { searchUsers } from '@/api/accounts'

const router = useRouter()

const queryForm = reactive({
  search: '',
  category: null,
  status: null,
  department: null,
  custodian: null
})

const assetList = ref([])
const categoryTree = ref([])
const departments = ref([])
const userOptions = ref([])
const statistics = ref({})
const selectedAssets = ref([])

const loading = ref(false)
const qrDialogVisible = ref(false)
const qrCodeUrl = ref('')
const currentAsset = ref({})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 加载分类树
const loadCategoryTree = async () => {
  const { data } = await getCategoryTree()
  categoryTree.value = data
}

// 加载部门列表
const loadDepartments = async () => {
  const { data } = await getDepartments()
  departments.value = data.results || []
}

// 搜索用户
const searchUsers = async (query) => {
  if (!query) return
  const { data } = await searchUsers({ search: query })
  userOptions.value = data.results || []
}

// 加载统计数据
const loadStatistics = async () => {
  const { data } = await getAssetStatistics()
  statistics.value = data
}

// 加载资产列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      ...queryForm,
      page: pagination.page,
      page_size: pagination.pageSize
    }
    const { data } = await getAssetList(params)
    assetList.value = data.items
    pagination.total = data.total
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
    search: '',
    category: null,
    status: null,
    department: null,
    custodian: null
  })
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchData()
}

const handleAdd = () => {
  router.push('/assets/new')
}

const handleView = (row) => {
  router.push(`/assets/${row.id}`)
}

const handleEdit = (row) => {
  router.push(`/assets/${row.id}/edit`)
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除资产"${row.asset_name}"吗？`, '删除确认', {
      type: 'warning'
    })
    await deleteAsset(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleRowClick = (row) => {
  handleView(row)
}

const handleQRCode = async (row) => {
  currentAsset.value = row
  const { data } = await getAssetQRCode(row.id)
  qrCodeUrl.value = URL.createObjectURL(new Blob([data]))
  qrDialogVisible.value = true
}

const downloadQRCode = () => {
  const link = document.createElement('a')
  link.href = qrCodeUrl.value
  link.download = `${currentAsset.value.asset_code}_qrcode.png`
  link.click()
}

const formatMoney = (value) => {
  return Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getStatusType = (status) => {
  const map = {
    pending: 'info',
    in_use: 'success',
    idle: 'warning',
    maintenance: 'danger',
    lost: 'danger',
    scrapped: 'info'
  }
  return map[status] || 'info'
}

const getStatusLabel = (status) => {
  const map = {
    pending: '待入库',
    in_use: '在用',
    idle: '闲置',
    maintenance: '维修中',
    lost: '已丢失',
    scrapped: '已报废'
  }
  return map[status] || status
}

const goBack = () => {
  router.back()
}

onMounted(async () => {
  await Promise.all([
    loadCategoryTree(),
    loadDepartments(),
    loadStatistics(),
    fetchData()
  ])
})
</script>

<style scoped>
.asset-list {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.search-form {
  margin-bottom: 0;
}

.statistics-bar {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}

.table-card {
  margin-bottom: 20px;
}

.batch-bar {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 10px 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  gap: 10px;
  align-items: center;
  z-index: 100;
}

.qr-code-container {
  text-align: center;
  padding: 20px;
}

.qr-code-container img {
  width: 200px;
  height: 200px;
}

.qr-code-text {
  font-size: 18px;
  font-weight: bold;
  margin-top: 10px;
}

.qr-code-name {
  color: #666;
  margin-top: 5px;
}
</style>
```

### 2. 资产表单页面

```vue
<!-- frontend/src/views/assets/AssetForm.vue -->
<template>
  <div class="asset-form">
    <el-page-header @back="goBack" :title="isEdit ? '编辑资产' : '新增资产'" />

    <el-card style="margin-top: 20px">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-tabs v-model="activeTab">
          <!-- 基础信息 -->
          <el-tab-pane label="基础信息" name="basic">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="资产编码" prop="asset_code">
                  <el-input v-model="formData.asset_code" disabled />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="资产名称" prop="asset_name">
                  <el-input v-model="formData.asset_name" placeholder="请输入资产名称" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="资产分类" prop="asset_category">
                  <el-cascader
                    v-model="formData.categoryPath"
                    :options="categoryTree"
                    :props="{ value: 'id', label: 'name' }"
                    placeholder="请选择分类"
                    @change="handleCategoryChange"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="计量单位" prop="unit">
                  <el-input v-model="formData.unit" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="品牌">
                  <el-input v-model="formData.brand" placeholder="请输入品牌" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="型号">
                  <el-input v-model="formData.model" placeholder="请输入型号" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="规格型号">
                  <el-input v-model="formData.specification" placeholder="请输入规格型号" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="序列号">
                  <el-input v-model="formData.serial_number" placeholder="请输入序列号" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- 财务信息 -->
          <el-tab-pane label="财务信息" name="finance">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="购置原值" prop="purchase_price">
                  <el-input-number
                    v-model="formData.purchase_price"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="购置日期" prop="purchase_date">
                  <el-date-picker
                    v-model="formData.purchase_date"
                    type="date"
                    placeholder="选择日期"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="使用年限(月)">
                  <el-input-number
                    v-model="formData.useful_life"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="残值率(%)">
                  <el-input-number
                    v-model="formData.residual_rate"
                    :precision="2"
                    :min="0"
                    :max="100"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="当前价值">
                  <el-input-number
                    v-model="formData.current_value"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="累计折旧">
                  <el-input-number
                    v-model="formData.accumulated_depreciation"
                    :precision="2"
                    :min="0"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="供应商">
                  <el-select
                    v-model="formData.supplier"
                    filterable
                    allow-create
                    placeholder="选择或输入供应商"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="item in suppliers"
                      :key="item.id"
                      :label="item.name"
                      :value="item.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="采购订单号">
                  <el-input v-model="formData.supplier_order_no" placeholder="请输入订单号" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- 使用信息 -->
          <el-tab-pane label="使用信息" name="usage">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="使用部门">
                  <el-select
                    v-model="formData.department"
                    filterable
                    clearable
                    placeholder="选择部门"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="dept in departments"
                      :key="dept.id"
                      :label="dept.name"
                      :value="dept.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="存放地点">
                  <el-cascader
                    v-model="formData.locationPath"
                    :options="locationTree"
                    :props="{ value: 'id', label: 'name' }"
                    clearable
                    placeholder="选择地点"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="保管人">
                  <el-select
                    v-model="formData.custodian"
                    filterable
                    remote
                    :remote-method="searchUsers"
                    placeholder="选择保管人"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="user in userOptions"
                      :key="user.id"
                      :label="user.real_name || user.username"
                      :value="user.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="使用人">
                  <el-select
                    v-model="formData.user"
                    filterable
                    remote
                    :remote-method="searchUsers"
                    placeholder="选择使用人"
                    style="width: 100%"
                  >
                    <el-option
                      v-for="user in userOptions"
                      :key="user.id"
                      :label="user.real_name || user.username"
                      :value="user.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="资产状态">
                  <DictionarySelect 
                    code="ASSET_STATUS" 
                    v-model="formData.asset_status" 
                    style="width: 100%" 
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-tab-pane>

          <!-- 附件备注 -->
          <el-tab-pane label="附件备注" name="attachment">
            <el-form-item label="资产图片">
              <AttachmentUpload 
                biz-type="asset_image" 
                :biz-id="formData.id" 
                v-model="formData.images"
                accept=".jpg,.png"
              />
            </el-form-item>
            <el-form-item label="附件">
              <AttachmentUpload 
                biz-type="asset_attachment" 
                :biz-id="formData.id" 
                v-model="formData.attachments"
              />
            </el-form-item>

            <el-form-item label="备注">
              <el-input
                v-model="formData.remarks"
                type="textarea"
                :rows="4"
                placeholder="请输入备注信息"
              />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>

        <!-- 表单操作 -->
        <div class="form-actions">
          <el-button @click="goBack">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            保存
          </el-button>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getAssetDetail,
  createAsset,
  updateAsset
} from '@/api/assets'
import { getCategoryTree } from '@/api/assetCategory'
import { getDepartments } from '@/api/organization'
import { searchUsers } from '@/api/accounts'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const activeTab = ref('basic')
const submitting = ref(false)

const formData = reactive({
  asset_code: '',
  asset_name: '',
  asset_category: null,
  categoryPath: [],
  unit: '台',
  brand: '',
  model: '',
  specification: '',
  serial_number: '',
  purchase_price: 0,
  current_value: 0,
  accumulated_depreciation: 0,
  purchase_date: null,
  useful_life: 60,
  residual_rate: 5,
  supplier: null,
  supplier_order_no: '',
  department: null,
  location: null,
  locationPath: [],
  custodian: null,
  user: null,
  asset_status: 'pending',
  images: [],
  remarks: ''
})

const formRules = {
  asset_name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  asset_category: [{ required: true, message: '请选择资产分类', trigger: 'change' }],
  purchase_price: [{ required: true, message: '请输入购置原值', trigger: 'blur' }],
  purchase_date: [{ required: true, message: '请选择购置日期', trigger: 'change' }]
}

const categoryTree = ref([])
const departments = ref([])
const locationTree = ref([])
const suppliers = ref([])
const userOptions = ref([])

const isEdit = computed(() => !!route.params.id)

const loadDetail = async () => {
  const { data } = await getAssetDetail(route.params.id)
  Object.assign(formData, data.asset)

  // 设置级联选择器路径
  if (data.asset_category) {
    formData.categoryPath = data.asset_category.path || []
  }
  if (data.location) {
    formData.locationPath = data.location.path || []
  }
}

const handleCategoryChange = (value) => {
  formData.asset_category = value[value.length - 1]
}

const searchUsers = async (query) => {
  if (!query) return
  const { data } = await searchUsers({ search: query })
  userOptions.value = data.results || []
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return

  submitting.value = true
  try {
    const data = { ...formData }
    // 处理级联选择器值
    if (formData.categoryPath.length > 0) {
      data.asset_category = formData.categoryPath[formData.categoryPath.length - 1]
    }
    if (formData.locationPath.length > 0) {
      data.location = formData.locationPath[formData.locationPath.length - 1]
    }

    if (isEdit.value) {
      await updateAsset(route.params.id, data)
    } else {
      await createAsset(data)
    }

    ElMessage.success('保存成功')
    goBack()
  } finally {
    submitting.value = false
  }
}

const goBack = () => router.back()

onMounted(async () => {
  const [categories, depts] = await Promise.all([
    getCategoryTree(),
    getDepartments()
  ])
  categoryTree.value = categories.data
  departments.value = depts.data.results || []

  if (isEdit.value) {
    loadDetail()
  }
})
</script>

<style scoped>
.asset-form {
  padding: 20px;
}

.form-actions {
  margin-top: 20px;
  text-align: center;
}
</style>
```

## API集成

```javascript
// frontend/src/api/assets.js

import request from '@/utils/request'

// 获取资产列表
export function getAssetList(params) {
  return request({
    url: '/api/assets/assets/',
    method: 'get',
    params
  })
}

// 获取资产详情
export function getAssetDetail(id) {
  return request({
    url: `/api/assets/assets/${id}/`,
    method: 'get'
  })
}

// 创建资产
export function createAsset(data) {
  return request({
    url: '/api/assets/assets/',
    method: 'post',
    data
  })
}

// 更新资产
export function updateAsset(id, data) {
  return request({
    url: `/api/assets/assets/${id}/`,
    method: 'put',
    data
  })
}

// 删除资产
export function deleteAsset(id) {
  return request({
    url: `/api/assets/assets/${id}/`,
    method: 'delete'
  })
}

// 获取资产统计
export function getAssetStatistics() {
  return request({
    url: '/api/assets/assets/statistics/',
    method: 'get'
  })
}

// 获取资产二维码
export function getAssetQRCode(id) {
  return request({
    url: `/api/assets/assets/${id}/qr_code/`,
    method: 'get',
    responseType: 'blob'
  })
}

// 变更资产状态
export function changeAssetStatus(id, data) {
  return request({
    url: `/api/assets/assets/${id}/change_status/`,
    method: 'post',
    data
  })
}
```

## 路由配置

```javascript
// frontend/src/router/index.js

{
  path: '/assets',
  component: Layout,
  children: [
    {
      path: '',
      name: 'AssetList',
      component: () => import('@/views/assets/AssetList.vue'),
      meta: { title: '资产卡片', requiresAuth: true }
    },
    {
      path: 'new',
      name: 'AssetCreate',
      component: () => import('@/views/assets/AssetForm.vue'),
      meta: { title: '新增资产', requiresAuth: true }
    },
    {
      path: ':id',
      name: 'AssetDetail',
      component: () => import('@/views/assets/AssetDetail.vue'),
      meta: { title: '资产详情', requiresAuth: true }
    },
    {
      path: ':id/edit',
      name: 'AssetEdit',
      component: () => import('@/views/assets/AssetForm.vue'),
      meta: { title: '编辑资产', requiresAuth: true }
    }
  ]
}
```

## 组件目录结构

```
frontend/src/
├── views/
│   └── assets/
│       ├── AssetList.vue    # 资产列表页面
│       ├── AssetForm.vue    # 资产表单页面
│       └── AssetDetail.vue  # 资产详情页面
├── components/
│   └── assets/
│       ├── ImageUploader.vue    # 图片上传组件
│       └── AssetCard.vue        # 资产卡片组件
├── api/
│   └── assets.js               # 资产API
└── router/
    └── index.js                # 路由配置
```

## 实施步骤

1. ✅ 创建资产列表页面 (AssetList.vue)
2. ✅ 创建资产表单页面 (AssetForm.vue)
3. ✅ 配置API接口
4. ✅ 配置路由

## 输出产物

| 文件 | 说明 |
|------|------|
| `frontend/src/views/assets/AssetList.vue` | 资产列表页面 |
| `frontend/src/views/assets/AssetForm.vue` | 资产表单页面 |
| `frontend/src/api/assets.js` | 资产API |
| `frontend/src/router/index.js` | 路由配置 |
