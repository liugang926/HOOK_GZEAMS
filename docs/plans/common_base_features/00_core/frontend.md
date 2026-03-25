# Common Base Features: 前端公共组件

## 任务概述

基于 Vue 3 Composition API 实现统一的页面级公共组件，为所有业务模块提供标准的列表、表单、详情页面布局。

---

## 前端组件模型定义

### BaseListPage 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | string | - | 页面标题 |
| columns | ColumnItem[] | [] | 列配置 |
| searchFields | SearchField[] | [] | 搜索字段 |
| filterFields | FilterField[] | [] | 筛选字段 |
| fetchMethod | Function | - | 数据获取方法 |
| batchDeleteMethod | Function | null | 批量删除方法 |
| showCreate | boolean | true | 显示新建按钮 |
| showBatchDelete | boolean | true | 显示批量删除按钮 |
| customSlots | string[] | [] | 自定义插槽名称 |

### BaseFormPage 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | string | - | 页面标题 |
| submitMethod | Function | - | 提交方法 |
| initialData | object | {} | 初始数据 |
| rules | ValidationRule | {} | 验证规则 |
| submitText | string | '提交' | 提交按钮文本 |
| labelWidth | string | '120px' | 标签宽度 |
| redirectPath | string | '' | 提交成功后跳转路径 |

### BaseDetailPage 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | string | - | 页面标题 |
| fetchMethod | Function | - | 数据获取方法 |
| id | string/number | - | 数据ID |
| showAudit | boolean | true | 显示审计信息 |

### 组件事件模型

| 组件 | 事件名 | 参数类型 | 说明 |
|------|--------|----------|------|
| BaseListPage | search | SearchParams | 搜索触发 |
| BaseListPage | row-click | RowData | 行点击 |
| BaseListPage | create | - | 新建按钮点击 |
| BaseFormPage | submit-success | ResponseData | 提交成功 |
| BaseFormPage | cancel | - | 取消按钮点击 |
| BaseDetailPage | loaded | DetailData | 数据加载完成 |

### 列配置模型 (ColumnItem)

| 字段 | 类型 | 说明 |
|------|------|------|
| prop | string | 字段名(支持点号嵌套) |
| label | string | 列标题 |
| width | number | 固定列宽(px) |
| minWidth | number | 最小列宽(px) |
| fixed | string | 固定列(left/right) |
| align | string | 对齐方式(left/center/right) |
| slot | boolean | 启用自定义插槽 |
| tag | boolean | 渲染为标签 |
| type | string | 特殊列类型(image/link/datetime) |
| formatter | Function | 自定义格式化函数 |

### 搜索字段模型 (SearchField)

| 字段 | 类型 | 说明 |
|------|------|------|
| prop | string | 字段名 |
| label | string | 字段标签 |
| placeholder | string | 输入占位符 |
| type | string | 字段类型(text/select/date) |
| options | OptionItem[] | 选项(仅select类型) |

---

## 1. 组件结构

```
frontend/src/components/common/
├── BaseListPage.vue           # 标准列表页面组件
├── BaseFormPage.vue           # 标准表单页面组件
├── BaseDetailPage.vue         # 标准详情页面组件
├── BaseSearchBar.vue          # 搜索栏组件
├── BaseTable.vue              # 表格组件
├── BasePagination.vue         # 分页组件
├── BaseForm.vue               # 表单组件
└── BaseAuditInfo.vue          # 审计信息组件
```

---

## 2. BaseListPage - 标准列表页面

### 2.1 设计目标

- 提供统一的列表页面布局
- 内置搜索、筛选、排序功能
- 内置分页组件
- 支持批量操作

### 2.2 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| title | string | - | Yes | Page title |
| fetchMethod | Function | - | Yes | API method to fetch list data |
| deleteMethod | Function | null | No | Method to delete single item |
| batchDeleteMethod | Function | null | No | Method to batch delete items |
| columns | array | [] | Yes | Table column definitions |
| searchFields | array | [] | No | Search field configurations |
| filterFields | array | [] | No | Filter field configurations |
| showCreate | boolean | true | No | Show create button |
| showBatchDelete | boolean | true | No | Show batch delete button |
| customSlots | array | [] | No | Custom slot names for columns |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| row-click | row: object | Emitted when table row is clicked |
| create | - | Emitted when create button is clicked |
| refresh | - | Emitted when data is refreshed |

#### Exposed Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| refresh | - | void | Reload table data |

#### Column Definition Format

| Field | Type | Description |
|-------|------|-------------|
| prop | string | Field name (supports dot notation for nested fields) |
| label | string | Column header |
| width | number | Fixed column width (px) |
| minWidth | number | Minimum column width (px) |
| fixed | string/left/right | Fixed column position |
| align | left/center/right | Text alignment |
| slot | boolean | Enable custom slot for this column |
| tag | boolean | Render as tag |
| tagTypes | object | Tag type mapping (value -> type) |
| tagOptions | object | Tag label mapping (value -> label) |
| type | string | Special column type: 'image', 'link', 'datetime' |
| formatter | function | Custom value formatter |
| showOverflowTooltip | boolean | Show overflow tooltip |

### 2.3 使用示例

```vue
<!-- AssetList.vue -->

<template>
    <BaseListPage
        title="资产列表"
        :fetch-method="fetchAssets"
        :delete-method="deleteAsset"
        :batch-delete-method="batchDeleteAssets"
        :columns="columns"
        :search-fields="searchFields"
        :filter-fields="filterFields"
        :custom-slots="['status', 'actions']"
        @row-click="handleRowClick"
        @create="handleCreate"
    >
        <!-- 状态列插槽 -->
        <template #status="{ row }">
            <el-tag :type="getStatusType(row.status)">
                {{ getStatusLabel(row.status) }}
            </el-tag>
        </template>

        <!-- 操作列插槽 -->
        <template #actions="{ row }">
            <el-button link type="primary" @click.stop="handleEdit(row)">
                编辑
            </el-button>
            <el-button link type="danger" @click.stop="handleDelete(row)">
                删除
            </el-button>
        </template>
    </BaseListPage>
</template>

<script setup>
import { h } from 'vue'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetApi } from '@/api/assets'

const columns = [
    { prop: 'code', label: '资产编码', width: 150 },
    { prop: 'name', label: '资产名称', minWidth: 200 },
    { prop: 'category.name', label: '分类', width: 120 },
    { prop: 'status', label: '状态', width: 100, slot: true },
    { prop: 'created_at', label: '创建时间', width: 180 },
    { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]

const searchFields = [
    { prop: 'keyword', label: '搜索', placeholder: '编码/名称' }
]

const filterFields = [
    { prop: 'status', label: '状态', options: [...] },
    { prop: 'category', label: '分类', options: [...], type: 'select' }
]

const fetchAssets = (params) => assetApi.list(params)
const batchDeleteAssets = (data) => assetApi.batchDelete(data)

// ... 其他方法
</script>
```

---

## 3. BaseFormPage - 标准表单页面

### 3.1 设计目标

- 提供统一的表单页面布局
- 统一的表单验证处理
- 统一的提交/取消操作

### 3.2 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| title | string | - | Yes | Page title |
| submitMethod | Function | - | Yes | API method to submit form |
| initialData | object | {} | No | Initial form data |
| rules | object | {} | No | Form validation rules |
| submitText | string | '提交' | No | Submit button text |
| labelWidth | string | '120px' | No | Form label width |
| labelPosition | string | 'right' | No | Form label position |
| redirectPath | string | '' | No | Redirect path after success |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| submit-success | data: object | Emitted when form submits successfully |
| cancel | - | Emitted when cancel button is clicked |

#### Slots

| Slot | Props | Description |
|------|-------|-------------|
| default | data: object | Form content slot, receives formData |

#### Exposed Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| resetForm | - | void | Reset form to initial state |
| validate | - | Promise | Validate entire form |
| clearValidate | - | void | Clear validation errors |

### 3.3 使用示例

```vue
<!-- AssetForm.vue -->

<template>
    <BaseFormPage
        title="资产信息"
        :submit-method="handleSubmit"
        :initial-data="assetData"
        :rules="rules"
        submit-text="保存"
        redirect-path="/assets"
    >
        <template #default="{ data }">
            <el-form-item label="资产编码" prop="code">
                <el-input v-model="data.code" placeholder="请输入资产编码" />
            </el-form-item>

            <el-form-item label="资产名称" prop="name">
                <el-input v-model="data.name" placeholder="请输入资产名称" />
            </el-form-item>

            <el-form-item label="资产分类" prop="category_id">
                <CategorySelect v-model="data.category_id" />
            </el-form-item>

            <el-form-item label="状态" prop="status">
                <el-select v-model="data.status" placeholder="请选择状态">
                    <el-option label="闲置" value="idle" />
                    <el-option label="在用" value="in_use" />
                    <el-option label="维修" value="maintenance" />
                </el-select>
            </el-form-item>
        </template>
    </BaseFormPage>
</template>

<script setup>
import { ref } from 'vue'
import BaseFormPage from '@/components/common/BaseFormPage.vue'
import { assetApi } from '@/api/assets'

const assetData = ref({
    code: '',
    name: '',
    category_id: null,
    status: 'idle'
})

const rules = {
    code: [{ required: true, message: '请输入资产编码', trigger: 'blur' }],
    name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
    category_id: [{ required: true, message: '请选择分类', trigger: 'change' }]
}

const handleSubmit = (data) => assetApi.create(data)
</script>
```

---

## 4. BaseDetailPage - 标准详情页面

### 4.1 设计目标

- 提供统一的详情页面布局
- 自动展示审计信息
- 支持变更历史展示

### 4.2 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| title | string | - | Yes | Page title |
| fetchMethod | Function | - | Yes | API method to fetch detail data |
| id | string/number | - | Yes | Data ID |
| showAudit | boolean | true | No | Show audit information |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| loaded | data: object | Emitted when detail data is loaded |

#### Slots

| Slot | Props | Description |
|------|-------|-------------|
| actions | - | Custom action buttons in header |
| content | data: object | Main content area |

#### Exposed Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| refresh | - | void | Reload detail data |

### 4.3 使用示例

```vue
<!-- AssetDetail.vue -->

<template>
    <BaseDetailPage
        title="资产详情"
        :fetch-method="fetchAssetDetail"
        :id="assetId"
    >
        <template #actions="{ data }">
            <el-button type="primary" @click="handleEdit">编辑</el-button>
            <el-button type="danger" @click="handleDelete">删除</el-button>
        </template>

        <template #content="{ data }">
            <el-descriptions :column="2" border>
                <el-descriptions-item label="资产编码">
                    {{ data.code }}
                </el-descriptions-item>
                <el-descriptions-item label="资产名称">
                    {{ data.name }}
                </el-descriptions-item>
                <el-descriptions-item label="资产分类">
                    {{ data.category?.name }}
                </el-descriptions-item>
                <el-descriptions-item label="状态">
                    <el-tag :type="getStatusType(data.status)">
                        {{ getStatusLabel(data.status) }}
                    </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="存放位置">
                    {{ data.location?.name }}
                </el-descriptions-item>
                <el-descriptions-item label="保管人">
                    {{ data.custodian?.name }}
                </el-descriptions-item>
                <el-descriptions-item label="采购日期" :span="2">
                    {{ formatDate(data.purchase_date) }}
                </el-descriptions-item>
            </el-descriptions>
        </template>
    </BaseDetailPage>
</template>
```

---

## 5. BaseAuditInfo - 审计信息组件

### 5.1 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| createdAt | string | '' | No | Creation timestamp |
| createdBy | object | null | No | Creator user object |
| updatedAt | string | '' | No | Update timestamp |
| updatedBy | object | null | No | Updater user object |

---

## 6. 元数据驱动组件

GZEAMS 作为低代码平台，除了传统的页面组件外，还提供了元数据驱动的零代码组件。

详见：[metadata_frontend.md](./metadata_frontend.md)

### 6.1 两种模式对比

| 维度 | 传统模式（BaseListPage/BaseFormPage） | 元数据驱动模式（MetadataDriven） |
|------|-------------------------------------|-------------------------------|
| **适用场景** | 需要自定义布局的业务页面 | 标准CRUD页面、快速原型 |
| **配置方式** | 手动定义列/表单字段 | 从元数据自动生成 |
| **组件** | `BaseListPage` + `BaseFormPage` | `MetadataDrivenList` + `MetadataDrivenForm` |
| **列定义** | 手动配置 `columns` 数组 | 从 `PageLayout` 自动获取 |
| **表单字段** | 手动编写表单项 | 从 `FieldDefinition` 自动生成 |
| **验证规则** | 手动定义 `rules` | 从 `FieldDefinition` 自动生成 |
| **搜索筛选** | 手动配置搜索/筛选字段 | 从 `FieldDefinition` 自动获取 |

### 6.2 元数据驱动组件

| 组件 | 说明 | 文档 |
|------|------|------|
| `MetadataDrivenList` | 元数据驱动列表页面 | [metadata_frontend.md](./metadata_frontend.md) |
| `MetadataDrivenForm` | 元数据驱动表单页面 | [metadata_frontend.md](./metadata_frontend.md) |
| `useMetadata` Hook | 元数据加载和管理 | [metadata_frontend.md](./metadata_frontend.md) |
| `useValidation` Hook | 动态验证规则生成 | [metadata_frontend.md](./metadata_frontend.md) |
| `useFormula` Hook | 公式字段实时计算 | [metadata_frontend.md](./metadata_frontend.md) |

### 6.3 使用示例

```vue
<!-- 传统模式：需要手动配置列和表单 -->
<template>
    <BaseListPage
        title="资产列表"
        :fetch-method="fetchAssets"
        :columns="columns"
        :search-fields="searchFields"
    />
</template>

<script setup>
const columns = [
    { prop: 'code', label: '资产编码', width: 150 },
    { prop: 'name', label: '资产名称', width: 200 },
    // ... 需要手动配置每个列
]
</script>

<!-- 元数据驱动模式：仅需指定业务对象编码 -->
<template>
    <MetadataDrivenList
        object-code="Asset"
    />
</template>

<!-- 元数据驱动表单：仅需指定业务对象编码 -->
<template>
    <MetadataDrivenForm
        object-code="Asset"
        :data-id="assetId"
    />
</template>
```

### 6.4 元数据驱动组件结构

```
frontend/src/components/metadata/
├── MetadataDrivenList.vue       # 元数据驱动列表
├── MetadataDrivenForm.vue       # 元数据驱动表单
├── MetadataSearchBar.vue        # 元数据驱动搜索栏
├── MetadataFields/              # 动态字段组件
│   ├── MetadataField.vue        # 字段容器
│   ├── TextField.vue            # 文本字段
│   ├── NumberField.vue          # 数值字段
│   ├── DateField.vue            # 日期字段
│   ├── SelectField.vue          # 选择字段
│   ├── ReferenceField.vue       # 关联字段
│   └── FormulaField.vue         # 公式字段（只读）
└── composable/                  # 组合式函数
    ├── useMetadata.js           # 元数据管理
    ├── useValidation.js         # 验证规则
    └── useFormula.js            # 公式计算
```

---

## 7. BaseSearchBar - 搜索栏组件

### 7.1 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| searchFields | array | [] | No | Search field configurations |
| filterFields | array | [] | No | Filter field configurations |
| searchPlaceholder | string | '请输入搜索关键词' | No | Search input placeholder |
| showToggle | boolean | false | No | Show expand/collapse button |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| search | params: object | Emitted when search is triggered |
| reset | - | Emitted when reset is clicked |

#### Filter Field Definition

| Field | Type | Description |
|-------|------|-------------|
| prop | string | Field name |
| label | string | Field label |
| type | string | Field type: 'select', 'date', 'date_range', or text input |
| options | array | Options for select type [{value, label}] |

#### Search Field Definition

| Field | Type | Description |
|-------|------|-------------|
| prop | string | Field name |
| label | string | Field label |
| placeholder | string | Input placeholder |

---

## 8. BaseTable - 表格组件

### 8.1 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| data | array | [] | Yes | Table data |
| columns | array | - | Yes | Column definitions (see format below) |
| loading | boolean | false | No | Loading state |
| selectionEnabled | boolean | false | No | Show checkbox column |
| showIndex | boolean | false | No | Show row number column |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| selection-change | selection: array | Emitted when row selection changes |
| row-click | row: object | Emitted when row is clicked |
| link-click | {row, column} | Emitted when link column is clicked |

#### Slots

| Slot | Props | Description |
|------|-------|-------------|
| [column.prop] | row: object, $index: number | Custom column content |

#### Column Type Options

| Type | Description |
|------|-------------|
| image | Render as image with preview |
| link | Render as clickable link |
| datetime | Auto-format as datetime |
| tag (with tag: true) | Render as Element Plus tag |

### 8.2 列配置示例

```javascript
// 列配置示例
const columns = [
    // 普通列
    { prop: 'code', label: '资产编码', width: 150, fixed: 'left' },

    // 带插槽的列（自定义渲染）
    { prop: 'status', label: '状态', width: 100, slot: true },

    // 标签列
    {
        prop: 'status',
        label: '状态',
        width: 100,
        tag: true,
        tagTypes: {
            'idle': 'info',
            'in_use': 'success',
            'maintenance': 'warning',
            'scrapped': 'danger'
        },
        tagOptions: {
            'idle': '闲置',
            'in_use': '在用',
            'maintenance': '维修中',
            'scrapped': '已报废'
        }
    },

    // 图片列
    { prop: 'image', label: '图片', type: 'image', width: 80 },

    // 日期列
    { prop: 'created_at', label: '创建时间', type: 'datetime', width: 180 },

    // 格式化列
    {
        prop: 'amount',
        label: '金额',
        width: 120,
        align: 'right',
        formatter: (value) => `¥${Number(value).toLocaleString()}`
    },

    // 操作列
    { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]
```

---

## 9. BasePagination - 分页组件

### 9.1 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| total | number | 0 | No | Total number of records |
| page | number | 1 | No | Current page number |
| pageSize | number | 20 | No | Records per page |
| pageSizes | array | [10, 20, 50, 100] | No | Available page size options |
| layout | string | 'total, sizes, prev, pager, next, jumper' | No | Pagination layout |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| update:page | page: number | Current page changed (v-model) |
| update:pageSize | pageSize: number | Page size changed (v-model) |
| change | {page, pageSize} | Page or page size changed |

---

## 10. 全局错误处理

### 10.1 请求拦截器配置

#### Axios Instance Configuration

| Config | Type | Default | Description |
|--------|------|---------|-------------|
| baseURL | string | '/api' | API base URL from env or default |
| timeout | number | 30000 | Request timeout (ms) |
| headers | object | {'Content-Type': 'application/json'} | Default request headers |

#### Request Interceptor Headers

| Header | Source | Description |
|--------|--------|-------------|
| Authorization | localStorage.access_token | Bearer token for authentication |
| X-Organization-ID | localStorage.current_org_id | Current organization context |

#### Response Error Handling

| Status Code | Handler | User Message |
|-------------|---------|--------------|
| 401 | Redirect to login | '登录已过期，是否重新登录？' |
| 403 | Show error | '权限不足' |
| 404 | Show error | '请求的资源不存在' |
| 410 | Show error | '资源已被删除' |
| 429 | Show error | '请求过于频繁，请稍后再试' |
| 500/502/503 | Show error | '服务器错误，请稍后再试' |

### 10.2 Global Error Handler Plugin

#### Error Handler Features

| Feature | Description |
|---------|-------------|
| Vue error handler | Catches component lifecycle errors |
| Unhandled rejection | Catches uncaught Promise rejections |
| Dev vs Prod | Different error detail levels |
| User feedback | Shows friendly error messages |

---

## 11. BaseFileUpload - 文件上传组件

### 11.1 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| modelValue | array | [] | No | File URL array (v-model) |
| action | string | '/api/files/upload/' | No | Upload endpoint URL |
| maxFiles | number | 5 | No | Maximum number of files |
| maxSize | number | 10485760 (10MB) | No | Maximum file size in bytes |
| accept | string | '' | No | Accepted file types (e.g., '.png,.jpg') |
| multiple | boolean | true | No | Allow multiple file selection |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| update:modelValue | urls: array | Emitted when file list changes (v-model) |
| change | {urls, ids, files} | Emitted when upload status changes |

#### Upload Validation

| Validation | Trigger | Error Message |
|------------|---------|---------------|
| File size | Before upload | '文件大小不能超过 {maxSize}' |
| File type | Before upload | '不支持的文件类型，仅支持：{accept}' |
| File count | On exceed | '最多只能上传 {maxFiles} 个文件' |

---

## 12. 输出产物

### 12.1 传统模式文件

| 文件 | 说明 |
|------|------|
| `frontend/src/components/common/BaseListPage.vue` | 标准列表页面组件 |
| `frontend/src/components/common/BaseFormPage.vue` | 标准表单页面组件 |
| `frontend/src/components/common/BaseDetailPage.vue` | 标准详情页面组件 |
| `frontend/src/components/common/BaseSearchBar.vue` | 搜索栏组件 |
| `frontend/src/components/common/BaseTable.vue` | 表格组件 |
| `frontend/src/components/common/BasePagination.vue` | 分页组件 |
| `frontend/src/components/common/BaseAuditInfo.vue` | 审计信息组件 |
| `frontend/src/components/common/BaseFileUpload.vue` | 文件上传组件 |
| `frontend/src/utils/request.js` | 请求拦截器 |
| `frontend/src/plugins/errorHandler.js` | 全局错误处理插件 |

### 12.2 权限组件

> 详见：[permission_frontend.md](./permission_frontend.md)

| 文件 | 说明 |
|------|------|
| `frontend/src/stores/permission.js` | 权限 Store |
| `frontend/src/composables/usePermission.js` | 权限组合函数 |
| `frontend/src/directives/permission.js` | `v-permission` 指令 |
| `frontend/src/directives/index.js` | 指令入口 |
| `frontend/src/components/common/PermissionButton.vue` | 权限按钮 |
| `frontend/src/components/common/PermissionLink.vue` | 权限链接 |
| `frontend/src/components/common/PermissionVisible.vue` | 权限容器 |
| `frontend/src/api/permissions.js` | 权限 API |

使用示例：
```vue
<template>
  <!-- 权限指令 -->
  <el-button v-permission="'assets.create_asset'">新建</el-button>

  <!-- 权限组件 -->
  <PermissionButton :permission="['assets.update', 'assets.delete']" mode="any">
    批量操作
  </PermissionButton>

  <!-- 权限组合函数 -->
  <script setup>
  import { usePermission } from '@/composables/usePermission'
  const { hasPermission, hasRole } = usePermission()
  const canEdit = hasPermission('assets.update_asset')
  </script>
</template>
```

### 12.3 元数据驱动文件

| 文件 | 说明 |
|------|------|
| `frontend/src/components/metadata/MetadataDrivenList.vue` | 元数据驱动列表 |
| `frontend/src/components/metadata/MetadataDrivenForm.vue` | 元数据驱动表单 |
| `frontend/src/components/metadata/composable/useMetadata.js` | 元数据Hook |
| `frontend/src/components/metadata/composable/useValidation.js` | 验证Hook |
| `frontend/src/components/metadata/composable/useFormula.js` | 公式计算Hook |
| `frontend/src/api/metadata.js` | 元数据API |
| `frontend/src/api/dynamic.js` | 动态数据API |
| `frontend/src/utils/validation.js` | 验证规则转换 |
| `frontend/src/utils/formula.js` | 公式计算工具 |

### 12.4 多语言组件

> 详见：[i18n_frontend.md](./i18n_frontend.md)

| 文件 | 说明 |
|------|------|
| `frontend/src/i18n/index.js` | i18n 配置入口 |
| `frontend/src/i18n/locales/zh-CN.js` | 中文语言包 |
| `frontend/src/i18n/locales/en-US.js` | 英文语言包 |
| `frontend/src/i18n/utils/currency.js` | 货币格式化 |
| `frontend/src/i18n/utils/date.js` | 日期格式化 |
| `frontend/src/i18n/utils/number.js` | 数字格式化 |
| `frontend/src/composables/useI18n.js` | i18n 组合函数 |
| `frontend/src/directives/i18n.js` | `v-i18n` 指令 |
| `frontend/src/components/common/LanguageSwitcher.vue` | 语言切换组件 |
| `frontend/src/api/i18n.js` | 翻译 API |

使用示例：
```vue
<template>
  <!-- 模板翻译 -->
  <h1>{{ $t('assets.title') }}</h1>
  <el-button>{{ $t('common.actions.save') }}</el-button>

  <!-- 语言切换组件 -->
  <LanguageSwitcher />
</template>

<script setup>
import { useI18n } from '@/composables/useI18n'

const { t, locale, switchLocale, translateEnum } = useI18n()

// 获取翻译
const saveText = t('common.actions.save')  // '保存'

// 翻译枚举值
const statusText = translateEnum('assets.status', 'idle')  // '闲置'

// 切换语言
const handleLanguageChange = (lang) => {
  switchLocale(lang)
}
</script>
```

---

## 13. Public Business Components (公共业务组件)

基于后端公共模型构建的通用前端业务组件。

### 13.1 DictionarySelect (字典选择器)

基于 `Dictionary` 模型的通用下拉选择组件。

**Props**:
-   `code`: 字典类型代码 (e.g., `"ASSET_STATUS"`)
-   `modelValue`: 绑定值
-   `multiple`: 是否多选
-   `showAll`: 是否显示"全部"选项

**Usage**:
```vue
<DictionarySelect code="ASSET_TYPE" v-model="formData.type" />
```

### 13.2 AttachmentUpload (统一附件上传)

基于 `SystemFile` 模型的通用附件管理组件。

**Props**:
-   `bizType`: 业务类型 (e.g., `"contract"`, `"invoice"`)
-   `bizId`: 业务ID
-   `readOnly`: 是否只读

**Features**:
-   拖拽上传
-   文件预览 (图片/PDF)
-   下载文件
-   删除确认

**Usage**:
```vue
<AttachmentUpload biz-type="asset_contract" :biz-id="asset.id" />
```

### 13.3 TagInput (标签输入组件)

基于 `Tag` 模型的标签管理组件。

**Props**:
-   `modelValue`: 标签数组
-   `allowCreate`: 是否允许创建新标签
-   `colorEncoded`: 是否显示颜色

**Usage**:
```vue
<TagInput v-model="asset.tags" allow-create />
```

### 13.4 SequenceInput (流水号输入组件)

自动生成并展示流水号，支持手动修改（如果配置允许）。

**Props**:
-   `ruleCode`: 规则代码 (e.g., `"ASSET_CODE"`)
-   `modelValue`: 绑定值

**Usage**:
```vue
<SequenceInput rule-code="ASSET_CODE" v-model="formData.code" />
```

