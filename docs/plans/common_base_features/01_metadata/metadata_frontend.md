# 元数据驱动前端组件

## 任务概述

实现基于元数据的前端组件，支持根据BusinessObject/FieldDefinition/PageLayout自动渲染表单和列表，实现真正的零代码前端。

---

## 元数据前端组件模型

### MetadataDrivenForm 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| businessObjectCode | string | - | 业务对象编码（必填） |
| layoutCode | string | 'form' | 布局编码 |
| mode | 'form' | 'view' | 'form' | 显示模式 |
| initialData | object | {} | 初始数据 |
| dataId | string | null | 数据ID（编辑模式） |
| submitText | string | '提交' | 提交按钮文本 |
| labelWidth | string | '120px' | 表单标签宽度 |
| labelPosition | string | 'right' | 标签位置 |
| disabledFields | array | [] | 禁用的字段列表 |
| resetOnSuccess | boolean | false | 提交成功后重置表单 |

### MetadataDrivenList 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| businessObjectCode | string | - | 业务对象编码（必填） |
| columns | ColumnConfig[] | [] | 列配置 |
| showCreate | boolean | true | 显示创建按钮 |
| showBatchDelete | boolean | true | 显示批量删除按钮 |
| showSearch | boolean | true | 显示搜索栏 |
| showSelection | boolean | true | 显示复选框列 |
| showRowNumber | boolean | false | 显示行号列 |
| showActions | boolean | true | 显示操作列 |
| showPagination | boolean | true | 显示分页 |
| border | boolean | true | 表格边框 |
| stripe | boolean | true | 表格斑马纹 |
| actionColumnWidth | number | 200 | 操作列宽度 |
| actionFixed | string | 'right' | 操作列固定位置 |
| paginationLayout | string | 'total, sizes, prev, pager, next, jumper' | 分页布局 |
| pageSizes | array | [10, 20, 50, 100] | 页面大小选项 |

### FieldRenderer 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| fieldDefinition | object | - | 字段定义对象 |
| value | any | - | 字段值 |
| modelValue | any | - | v-model绑定值 |
| disabled | boolean | false | 是否禁用 |
| readonly | boolean | false | 是否只读 |
| placeholder | string | - | 占位符 |
| size | string | 'default' | 组件大小 |

### useMetadata Hook 返回值模型

| 属性 | 类型 | 说明 |
|------|------|------|
| loading | Ref\<boolean\> | 元数据加载状态 |
| metadata | Ref\<object\> | 业务对象元数据 |
| fieldDefinitions | Ref\<array\> | 字段定义列表 |
| fieldMap | ComputedRef\<Map\> | 字段编码→定义映射 |
| listLayout | Ref\<object\> | 列表页布局配置 |
| formLayout | Ref\<object\> | 表单页布局配置 |
| error | Ref\<Error\> | 加载错误 |
| businessObject | ComputedRef\<object\> | 业务对象信息 |
| searchableFields | ComputedRef\<array\> | 可搜索字段列表 |
| sortableFields | ComputedRef\<array\> | 可排序字段列表 |
| filterableFields | ComputedRef\<array\> | 可过滤字段列表 |
| requiredFields | ComputedRef\<array\> | 必填字段列表 |
| readonlyFields | ComputedRef\<array\> | 只读字段列表 |
| loadMetadata | function | 加载元数据方法 |
| getFieldDefinition | function | 获取字段定义方法 |
| getFieldOptions | function | 获取字段选项方法 |
| isFieldVisible | function | 检查字段是否可见方法 |
| getFormSections | function | 获取表单分组方法 |
| getListColumns | function | 获取列表列配置方法 |

### useValidation Hook 返回值模型

| 属性 | 类型 | 说明 |
|------|------|------|
| rules | Ref\<object\> | 生成的验证规则 |
| errors | Ref\<object\> | 当前验证错误 |
| valid | Ref\<boolean\> | 总体验证状态 |
| validateField | function | 验证单个字段方法 |
| validateAll | function | 验证所有字段方法 |
| clearErrors | function | 清除所有错误方法 |
| clearFieldError | function | 清除单个字段错误方法 |

### useFormula Hook 返回值模型

| 属性 | 类型 | 说明 |
|------|------|------|
| formulaFields | ComputedRef\<array\> | 公式字段列表 |
| calculatedValues | Ref\<object\> | 缓存的计算结果 |
| calculateFormula | function | 计算单个公式方法 |
| calculateAll | function | 计算所有公式字段方法 |

---

### 1.1 核心功能

- 根据元数据自动渲染表单
- 根据元数据自动渲染列表
- 根据元数据自动生成验证规则
- 支持字段级联和依赖
- 支持公式字段的实时计算
- 支持动态字段的显示/隐藏
- 与现有的DynamicForm组件集成

### 1.2 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    元数据驱动前端架构                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              页面组件层 (Page Components)                  │ │
│  │  ┌──────────────────────┐  ┌────────────────────────────┐ │ │
│  │  │ MetadataDrivenList   │  │ MetadataDrivenForm         │ │ │
│  │  └──────────────────────┘  └────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              组件层 (Components)                           │ │
│  │  ┌──────────────────────────────────────────────────────┐ │ │
│  │  │              FieldRenderer                           │ │ │
│  │  │  - TextField  - NumberField  - DateField            │ │ │
│  │  │  - SelectField  - ReferenceField  - FormulaField    │ │ │
│  │  └──────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              服务层 (Services)                            │ │
│  │  ┌──────────────────────┐  ┌────────────────────────────┐ │ │
│  │  │ MetadataService      │  │ ValidationService          │ │ │
│  │  └──────────────────────┘  └────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              API层                                         │ │
│  │  GET /api/dynamic/{code}/metadata/                        │ │
│  │  GET /api/dynamic/{code}/schema/                          │ │
│  │  GET/POST/PUT /api/dynamic/{code}/                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 文件结构

```
frontend/src/
├── api/
│   ├── metadata.js              # 元数据API
│   └── dynamic.js               # 动态数据API
├── components/
│   ├── metadata/
│   │   ├── MetadataDrivenList.vue       # 元数据驱动列表
│   │   ├── MetadataDrivenForm.vue       # 元数据驱动表单
│   │   ├── MetadataFields/
│   │   │   ├── TextField.vue            # 文本字段
│   │   │   ├── NumberField.vue          # 数值字段
│   │   │   ├── DateField.vue            # 日期字段
│   │   │   ├── SelectField.vue          # 选择字段
│   │   │   ├── ReferenceField.vue       # 关联字段
│   │   │   └── FormulaField.vue         # 公式字段
│   │   └── composable/
│   │       ├── useMetadata.js           # 元数据Hook
│   │       ├── useValidation.js         # 验证Hook
│   │       └── useFormula.js            # 公式计算Hook
├── utils/
│   └── validation.js            # 验证规则转换
└── stores/
    └── metadata.js              # 元数据状态管理
```

---

## 3. 元数据API服务

### 3.1 元数据API

```javascript
// frontend/src/api/metadata.js

import request from '@/utils/request'

/**
 * 获取业务对象元数据
 */
export function getBusinessObjectMetadata(objectCode) {
    return request({
        url: `/api/dynamic/${objectCode}/metadata/`,
        method: 'get'
    })
}

/**
 * 获取业务对象数据模式（Schema）
 */
export function getBusinessObjectSchema(objectCode) {
    return request({
        url: `/api/dynamic/${objectCode}/schema/`,
        method: 'get'
    })
}

/**
 * 获取字段定义列表
 */
export function getFieldDefinitions(objectCode) {
    return request({
        url: `/api/system/field-definitions/`,
        method: 'get',
        params: { business_object: objectCode }
    })
}

/**
 * 获取页面布局
 */
export function getPageLayout(objectCode, layoutType = 'form') {
    return request({
        url: `/api/system/page-layouts/`,
        method: 'get',
        params: {
            business_object: objectCode,
            layout_type: layoutType
        }
    })
}

/**
 * 获取验证规则
 */
export function getValidationRules(objectCode) {
    return request({
        url: `/api/system/business-objects/${objectCode}/validation-rules/`,
        method: 'get'
    })
}
```

### 3.2 动态数据API

```javascript
// frontend/src/api/dynamic.js

import request from '@/utils/request'

/**
 * 获取动态数据列表
 */
export function getDynamicDataList(objectCode, params) {
    return request({
        url: `/api/dynamic/${objectCode}/`,
        method: 'get',
        params
    })
}

/**
 * 获取单条动态数据
 */
export function getDynamicData(objectCode, id) {
    return request({
        url: `/api/dynamic/${objectCode}/${id}/`,
        method: 'get'
    })
}

/**
 * 创建动态数据
 */
export function createDynamicData(objectCode, data) {
    return request({
        url: `/api/dynamic/${objectCode}/`,
        method: 'post',
        data
    })
}

/**
 * 更新动态数据
 */
export function updateDynamicData(objectCode, id, data) {
    return request({
        url: `/api/dynamic/${objectCode}/${id}/`,
        method: 'put',
        data
    })
}

/**
 * 部分更新动态数据
 */
export function patchDynamicData(objectCode, id, data) {
    return request({
        url: `/api/dynamic/${objectCode}/${id}/`,
        method: 'patch',
        data
    })
}

/**
 * 删除动态数据
 */
export function deleteDynamicData(objectCode, id) {
    return request({
        url: `/api/dynamic/${objectCode}/${id}/`,
        method: 'delete'
    })
}

/**
 * 批量删除动态数据
 */
export function batchDeleteDynamicData(objectCode, ids) {
    return request({
        url: `/api/dynamic/${objectCode}/batch-delete/`,
        method: 'post',
        data: { ids }
    })
}
```

---

## 4. 元数据Hook

### 4.1 useMetadata Hook

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| objectCode | string | Yes | Business object code |

#### Return Values

| Property | Type | Description |
|----------|------|-------------|
| loading | Ref\<boolean\> | Metadata loading state |
| metadata | Ref\<object\> | Business object metadata |
| fieldDefinitions | Ref\<array\> | Field definition list |
| fieldMap | ComputedRef\<Map\> | Field code -> definition map |
| listLayout | Ref\<object\> | List page layout config |
| formLayout | Ref\<object\> | Form page layout config |
| error | Ref\<Error\> | Loading error |
| businessObject | ComputedRef\<object\> | Business object info |
| searchableFields | ComputedRef\<array\> | Fields with is_searchable=true |
| sortableFields | ComputedRef\<array\> | Fields with sortable=true |
| filterableFields | ComputedRef\<array\> | Fields with show_in_filter=true |
| requiredFields | ComputedRef\<array\> | Fields with is_required=true |
| readonlyFields | ComputedRef\<array\> | Fields with is_readonly=true |
| loadMetadata | function | Load all metadata for the object |
| getFieldDefinition | function | Get field definition by code |
| getFieldOptions | function | Get field options |
| isFieldVisible | function | Check if field is visible in layout |
| getFormSections | function | Get form layout sections |
| getListColumns | function | Get list layout columns |

### 4.2 useValidation Hook

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| fieldDefinitions | Ref\<array\> | Yes | Field definition list |
| formData | Ref\<object\> | Yes | Form data to validate |

#### Return Values

| Property | Type | Description |
|----------|------|-------------|
| rules | Ref\<object\> | Generated validation rules |
| errors | Ref\<object\> | Current validation errors |
| valid | Ref\<boolean\> | Overall validation status |
| validateField | function | Validate single field (fieldCode) => boolean |
| validateAll | function | Validate all fields => boolean |
| clearErrors | function | Clear all errors |
| clearFieldError | function | Clear single field error (fieldCode) |

#### Validation Rules Mapping

| Backend Field | Validation Rule | Condition |
|---------------|-----------------|-----------|
| is_required | required | Value cannot be empty |
| max_length | max | String length <= max_length |
| min_value | minimum | Number >= min_value |
| max_value | maximum | Number <= max_value |
| validation_regex | pattern | Must match regex pattern |
| options | enum | Value must be in options |

### 4.3 useFormula Hook

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| fieldDefinitions | Ref\<array\> | Yes | Field definition list |
| formData | Ref\<object\> | Yes | Form data for calculations |

#### Return Values

| Property | Type | Description |
|----------|------|-------------|
| formulaFields | ComputedRef\<array\> | Fields with field_type='formula' |
| calculatedValues | Ref\<object\> | Cached calculation results |
| calculateFormula | function | Calculate single formula (fieldDef) => any |
| calculateAll | function | Recalculate all formula fields => object |

#### Built-in Formula Context

| Variable/Function | Type | Description |
|-------------------|------|-------------|
| NOW | Date | Current date and time |
| TODAY | string | Current date (ISO format) |
| TRUE/FALSE | boolean | Boolean constants |
| NULL | null | Null constant |
| abs() | function | Absolute value |
| round() | function | Round number |
| min()/max() | function | Min/max of values |
| sum() | function | Sum array values |
| avg() | function | Average array values |
| count() | function | Count non-null array values |
| len() | function | Get length |
| days_between() | function | Days between two dates |
| years_between() | function | Years between two dates |

#### Auto-calculation Trigger

Formula fields are automatically recalculated when formData changes (deep watch).

---

## 5. MetadataDrivenForm 组件

### 5.1 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| objectCode | string | - | Yes | Business object code |
| initialData | object | {} | No | Initial form data (for edit) |
| dataId | string | null | No | Data ID (for edit mode) |
| submitText | string | '提交' | No | Submit button text |
| labelWidth | string | '120px' | No | Form label width |
| labelPosition | string | 'right' | No | Form label position |
| disabledFields | array | [] | No | List of disabled field codes |
| resetOnSuccess | boolean | false | No | Reset form after successful submit |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| submit-success | data: object | Emitted when form submits successfully |
| submit-error | error: Error | Emitted when submit fails |
| cancel | - | Emitted when cancel button is clicked |

#### Slots

| Slot | Props | Description |
|------|-------|-------------|
| actions | valid: boolean, loading: boolean | Custom action buttons |

#### Exposed Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| validate | - | Promise | Validate entire form |
| clearValidation | - | void | Clear validation errors |
| resetForm | - | void | Reset form to initial state |
| formData | - | object | Current form data (reactive) |

#### Field Span Mapping

| Field Type | Default Span |
|------------|--------------|
| textarea | 24 (full width) |
| date/datetime | 12 (half width) |
| boolean | 12 (half width) |
| other | 12 (half width) |

---

## 6. MetadataDrivenList 组件

### 6.1 组件API

#### Props

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|
| objectCode | string | - | Yes | Business object code |
| showCreate | boolean | true | No | Show create button |
| showBatchDelete | boolean | true | No | Show batch delete button |
| showSearch | boolean | true | No | Show search bar |
| showSelection | boolean | true | No | Show checkbox column |
| showRowNumber | boolean | false | No | Show row number column |
| showActions | boolean | true | No | Show actions column |
| showPagination | boolean | true | No | Show pagination |
| border | boolean | true | No | Table border |
| stripe | boolean | true | No | Table stripe |
| actionColumnWidth | number | 200 | No | Actions column width |
| actionFixed | string | 'right' | No | Actions column fixed position |
| paginationLayout | string | 'total, sizes, prev, pager, next, jumper' | No | Pagination layout |
| pageSizes | array | [10, 20, 50, 100] | No | Page size options |

#### Events

| Event | Payload | Description |
|-------|---------|-------------|
| row-click | row: object | Emitted when row is clicked |
| create | - | Emitted when create button is clicked |
| view | row: object | Emitted when view action is clicked |
| edit | row: object | Emitted when edit action is clicked |
| delete | row: object | Emitted when delete action is clicked |
| refresh | - | Emitted when data is refreshed |

#### Slots

| Slot | Props | Description |
|------|-------|-------------|
| actions | - | Custom header action buttons |
| row-actions | row: object | Custom row action buttons |
| column-[fieldCode] | row: object, value: any | Custom column cell content |

#### Exposed Methods

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| refresh | - | void | Reload table data |
| loadData | - | Promise | Force load data from API |
| tableData | - | Ref\<array\> | Current table data |
| selectedRows | - | Ref\<array\> | Current selected rows |

#### Cell Value Formatting

| Field Type | Format |
|------------|--------|
| choice | Map value to label from options |
| multi_choice | Join array values with commas |
| boolean | '是' / '否' |
| date | Locale date string |
| datetime | Locale datetime string |
| reference | Display field from referenced object |
| other | Original value |

---

## 7. 输出产物

| 文件 | 说明 |
|------|------|
| `frontend/src/api/metadata.js` | 元数据API服务 |
| `frontend/src/api/dynamic.js` | 动态数据API服务 |
| `frontend/src/components/metadata/composable/useMetadata.js` | 元数据Hook |
| `frontend/src/components/metadata/composable/useValidation.js` | 验证Hook |
| `frontend/src/components/metadata/composable/useFormula.js` | 公式计算Hook |
| `frontend/src/components/metadata/MetadataDrivenForm.vue` | 元数据驱动表单 |
| `frontend/src/components/metadata/MetadataDrivenList.vue` | 元数据驱动列表 |
| `frontend/src/components/metadata/MetadataSearchBar.vue` | 搜索栏组件 |
| `frontend/src/components/metadata/MetadataFields/` | 字段组件集合 |
| `frontend/src/utils/validation.js` | 验证规则转换工具 |
| `frontend/src/utils/formula.js` | 公式计算工具 |

---

## 8. 使用示例

### 8.1 在路由中使用

```javascript
// frontend/src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import MetadataDrivenList from '@/components/metadata/MetadataDrivenList.vue'
import MetadataDrivenForm from '@/components/metadata/MetadataDrivenForm.vue'

const routes = [
    {
        path: '/dynamic/:objectCode',
        name: 'DynamicList',
        component: MetadataDrivenList,
        props: true
    },
    {
        path: '/dynamic/:objectCode/create',
        name: 'DynamicCreate',
        component: MetadataDrivenForm,
        props: true
    },
    {
        path: '/dynamic/:objectCode/edit/:id',
        name: 'DynamicEdit',
        component: MetadataDrivenForm,
        props: true
    }
]
```

### 8.2 在页面中使用

```vue
<template>
    <MetadataDrivenList
        object-code="Asset"
        :show-create="true"
        :show-batch-delete="true"
        @create="handleCreate"
        @edit="handleEdit"
        @view="handleView"
    />
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function handleCreate() {
    router.push({ name: 'DynamicCreate', params: { objectCode: 'Asset' } })
}

function handleEdit(row) {
    router.push({
        name: 'DynamicEdit',
        params: { objectCode: 'Asset', id: row.id }
    })
}

function handleView(row) {
    // 显示详情对话框
}
</script>
```
