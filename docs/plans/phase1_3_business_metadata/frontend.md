# Phase 1.3: 核心业务单据元数据配置 - 前端实现

## 任务概述
基于元数据配置实现前端动态表单和动态列表渲染，这是低代码平台的核心功能。

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

## 前端组件架构

```
src/components/engine/
├── DynamicForm.vue           # 动态表单主组件
├── DynamicList.vue           # 动态列表主组件
├── FieldRenderer.vue         # 字段渲染器（分发到具体字段组件）
├── SectionLayout.vue         # 分组布局组件
├── fields/                   # 字段组件目录
│   ├── TextField.vue        # 文本字段
│   ├── NumberField.vue      # 数字字段
│   ├── DateField.vue        # 日期字段
│   ├── SelectField.vue      # 下拉选择字段
│   ├── UserField.vue        # 用户选择字段
│   ├── DeptField.vue        # 部门选择字段
│   ├── ReferenceField.vue   # 关联引用字段
│   ├── FormulaField.vue     # 公式字段（只读）
│   ├── SubTableField.vue    # 子表字段
│   └── DisplayField.vue     # 展示字段
└── hooks/
    ├── useDynamicForm.js    # 动态表单逻辑hook
    ├── useFieldPermissions.js # 字段权限hook
    └── useFormula.js        # 公式计算hook
```

## 核心组件实现

### 1. 动态表单主组件

```vue
<!-- src/components/engine/DynamicForm.vue -->
<template>
  <div class="dynamic-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-width="labelWidth"
      :label-position="labelPosition"
    >
      <!-- 遍历布局分组 -->
      <template v-for="section in layoutSections" :key="section.id">
        <el-card v-if="section.visible !== false" class="form-section">
          <template #header v-if="section.title">
            <span>{{ section.title }}</span>
          </template>

          <!-- 分组内的字段网格 -->
          <el-row :gutter="20">
            <el-col
              v-for="field in getSectionFields(section)"
              :key="field.code"
              :span="field.colspan || 24"
              v-show="isFieldVisible(field)"
            >
              <!-- 字段权限：只读 -->
              <template v-if="isFieldReadonly(field)">
                <el-form-item :label="field.name" :prop="field.code">
                  <DisplayField :field="field" :value="formData[field.code]" />
                </el-form-item>
              </template>

              <!-- 字段权限：可编辑 -->
              <template v-else>
                <el-form-item
                  :label="field.name"
                  :prop="field.code"
                  :required="field.is_required"
                >
                  <FieldRenderer
                    :field="field"
                    :model-value="formData[field.code]"
                    @update:model-value="handleFieldValueChange(field.code, $event)"
                  />
                </el-form-item>
              </template>
            </el-col>
          </el-row>
        </el-card>
      </template>
    </el-form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useDynamicForm } from './hooks/useDynamicForm'
import { useFieldPermissions } from './hooks/useFieldPermissions'
import FieldRenderer from './FieldRenderer.vue'
import DisplayField from './fields/DisplayField.vue'

const props = defineProps({
  businessObject: { type: String, required: true },
  layoutCode: { type: String, default: 'form' },
  modelValue: { type: Object, default: () => ({}) },
  fieldPermissions: { type: Object, default: () => ({}) },
  labelWidth: { type: String, default: '120px' },
  labelPosition: { type: String, default: 'right' }
})

const emit = defineEmits(['update:modelValue', 'change', 'submit'])

// 使用动态表单hook
const {
  formRef,
  formData,
  formRules,
  fieldDefinitions,
  layoutSections,
  loadMetadata,
  validate,
  resetFields
} = useDynamicForm(props.businessObject, props.layoutCode)

// 使用字段权限hook
const {
  getFieldPermission,
  isFieldReadonly,
  isFieldVisible
} = useFieldPermissions(props.fieldPermissions, fieldDefinitions)

// 加载元数据
onMounted(async () => {
  await loadMetadata()
  if (props.modelValue && Object.keys(props.modelValue).length > 0) {
    Object.assign(formData, props.modelValue)
  }
})

// 处理字段值变化
const handleFieldValueChange = (fieldCode, value) => {
  formData[fieldCode] = value
  updateFormulaFields(fieldCode, value)
  emit('update:modelValue', { ...formData })
  emit('change', { fieldCode, value })
}

// 更新公式字段
const updateFormulaFields = async (triggerField, triggerValue) => {
  const formulaFields = fieldDefinitions.value.filter(
    f => f.field_type === 'formula' && f.formula?.includes(triggerField)
  )

  for (const field of formulaFields) {
    const result = await calculateFormula(field.formula, formData)
    formData[field.code] = result
  }
}

// 获取分组内的字段
const getSectionFields = (section) => {
  const fieldCodes = section.fields || []
  return fieldDefinitions.value.filter(f => fieldCodes.includes(f.code))
}

// 暴露方法给父组件
defineExpose({
  validate,
  resetFields,
  getFormData: () => formData
})
</script>

<style scoped>
.dynamic-form {
  width: 100%;
}

.form-section {
  margin-bottom: 20px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.form-section :deep(.el-card__header) {
  background: #f5f7fa;
  padding: 12px 20px;
}
</style>
```

### 2. 字段渲染器组件

```vue
<!-- src/components/engine/FieldRenderer.vue -->
<template>
  <component
    :is="fieldComponent"
    :field="field"
    :model-value="modelValue"
    v-bind="fieldProps"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Object, Array], default: null },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

// 字段类型到组件的映射
const FIELD_COMPONENTS = {
  text: () => import('./fields/TextField.vue'),
  textarea: () => import('./fields/TextField.vue'),
  number: () => import('./fields/NumberField.vue'),
  currency: () => import('./fields/NumberField.vue'),
  date: () => import('./fields/DateField.vue'),
  datetime: () => import('./fields/DateField.vue'),
  select: () => import('./fields/SelectField.vue'),
  multi_select: () => import('./fields/SelectField.vue'),
  user: () => import('./fields/UserField.vue'),
  department: () => import('./fields/DeptField.vue'),
  reference: () => import('./fields/ReferenceField.vue'),
  formula: () => import('./fields/FormulaField.vue'),
  sub_table: () => import('./fields/SubTableField.vue'),
  boolean: () => import('./fields/BooleanField.vue'),
  file: () => import('./fields/FileField.vue'),
  image: () => import('./fields/ImageField.vue'),
}

// 计算要使用的组件
const fieldComponent = computed(() => {
  const componentLoader = FIELD_COMPONENTS[props.field.field_type]
  if (!componentLoader) {
    console.warn(`未知字段类型: ${props.field.field_type}`)
    return defineAsyncComponent(() => import('./fields/TextField.vue'))
  }
  return defineAsyncComponent(componentLoader)
})

// 传递给字段组件的属性
const fieldProps = computed(() => ({
  disabled: props.disabled,
  placeholder: props.field.placeholder || `请输入${props.field.name}`,
  ...props.field.component_props
}))
</script>
```

### 3. 动态表单Hook

```javascript
// src/components/engine/hooks/useDynamicForm.js
import { ref, reactive } from 'vue'
import { getFieldDefinitions, getPageLayout } from '@/api/metadata'
import { buildFormRules } from '@/utils/formBuilder'

export function useDynamicForm(businessObject, layoutCode = 'form') {
  const formRef = ref(null)
  const formData = reactive({})
  const formRules = reactive({})
  const fieldDefinitions = ref([])
  const layoutSections = ref([])

  // 加载元数据
  const loadMetadata = async () => {
    try {
      const [fieldsRes, layoutRes] = await Promise.all([
        getFieldDefinitions(businessObject),
        getPageLayout(businessObject, layoutCode)
      ])

      fieldDefinitions.value = fieldsRes.fields || []
      layoutSections.value = parseLayoutConfig(layoutRes.layout_config)
      Object.assign(formRules, buildFormRules(fieldDefinitions.value))
      initFormData(fieldDefinitions.value)

    } catch (error) {
      console.error('加载元数据失败:', error)
      throw error
    }
  }

  // 解析布局配置
  const parseLayoutConfig = (config) => {
    if (!config) {
      return [{
        id: 'default',
        title: '',
        columns: 1,
        fields: fieldDefinitions.value.map(f => f.code),
        visible: true
      }]
    }

    return (config.sections || []).map(section => ({
      ...section,
      visible: true,
      collapsed: false
    }))
  }

  // 初始化表单数据
  const initFormData = (fields) => {
    fields.forEach(field => {
      if (!(field.code in formData)) {
        if (field.default_value !== undefined && field.default_value !== null) {
          formData[field.code] = parseDefaultValue(field.default_value)
        } else if (field.field_type === 'select') {
          formData[field.code] = field.multiple ? [] : ''
        } else if (field.field_type === 'number') {
          formData[field.code] = 0
        } else if (field.field_type === 'sub_table') {
          formData[field.code] = []
        } else {
          formData[field.code] = ''
        }
      }
    })
  }

  // 解析默认值（支持变量）
  const parseDefaultValue = (value) => {
    if (typeof value !== 'string') return value

    const variables = {
      '{current_user}': () => store.state.user?.info?.id,
      '{current_user.name}': () => store.state.user?.info?.real_name,
      '{current_user.department}': () => store.state.user?.info?.department_id,
      '{today}': () => new Date().toISOString().split('T')[0],
      '{now}': () => new Date().toISOString()
    }

    for (const [key, getter] of Object.entries(variables)) {
      if (value.includes(key)) {
        return value.replace(key, getter())
      }
    }

    return value
  }

  // 表单验证
  const validate = () => formRef.value?.validate()

  // 重置表单
  const resetFields = () => {
    formRef.value?.resetFields()
    Object.keys(formData).forEach(key => delete formData[key])
    initFormData(fieldDefinitions.value)
  }

  return {
    formRef,
    formData,
    formRules,
    fieldDefinitions,
    layoutSections,
    loadMetadata,
    validate,
    resetFields
  }
}
```

### 4. 字段权限Hook

```javascript
// src/components/engine/hooks/useFieldPermissions.js
import { computed } from 'vue'

export function useFieldPermissions(fieldPermissions = {}, fieldDefinitions = ref([])) {
  // 获取字段权限: 'editable' | 'read_only' | 'hidden'
  const getFieldPermission = (field) => {
    // 优先使用工作流传入的权限
    if (fieldPermissions.value && fieldPermissions.value[field.code]) {
      return fieldPermissions.value[field.code]
    }

    // 使用字段定义中的默认权限
    if (field.is_readonly) return 'read_only'
    if (field.is_system) return 'read_only'

    return 'editable'
  }

  const isFieldReadonly = (field) => getFieldPermission(field) === 'read_only'
  const isFieldVisible = (field) => getFieldPermission(field) !== 'hidden'

  return {
    getFieldPermission,
    isFieldReadonly,
    isFieldVisible
  }
}
```

### 5. 子表字段组件（主子表）

```vue
<!-- src/components/engine/fields/SubTableField.vue -->
<template>
  <div class="sub-table-field">
    <el-table
      :data="localValue"
      border
      size="small"
      :max-height="400"
    >
      <el-table-column type="index" label="序号" width="50" />

      <!-- 子表字段列 -->
      <el-table-column
        v-for="subField in subTableFields"
        :key="subField.code"
        :label="subField.name"
        :width="subField.width || 150"
      >
        <template #default="{ row, $index }">
          <!-- 引用字段 -->
          <template v-if="subField.field_type === 'reference'">
            <ReferenceField
              v-model="row[subField.code]"
              :field="subField"
              :sub-table-index="$index"
              @change="handleSubFieldChange($index, subField.code, $event)"
            />
          </template>

          <!-- 数字字段 -->
          <template v-else-if="subField.field_type === 'number'">
            <el-input-number
              v-model="row[subField.code]"
              :precision="subField.precision || 2"
              :disabled="disabled"
              @change="handleSubFieldChange($index, subField.code, $event)"
            />
          </template>

          <!-- 下拉选择 -->
          <template v-else-if="subField.field_type === 'select'">
            <el-select
              v-model="row[subField.code]"
              :disabled="disabled"
              @change="handleSubFieldChange($index, subField.code, $event)"
            >
              <el-option
                v-for="opt in subField.options"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </template>

          <!-- 文本字段 -->
          <template v-else>
            <el-input
              v-model="row[subField.code]"
              :disabled="disabled"
              @change="handleSubFieldChange($index, subField.code, $event)"
            />
          </template>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ $index }">
          <el-button
            link
            type="danger"
            size="small"
            @click="handleDeleteRow($index)"
            :disabled="disabled"
          >
            删除
          </el-button>
        </template>
      </el-table-column>

      <!-- 合计行 -->
      <template #append>
        <tr class="summary-row">
          <td colspan="1">合计</td>
          <td v-for="subField in subTableFields" :key="`sum-${subField.code}`">
            <span v-if="subField.show_sum">
              {{ getFieldSum(subField.code) }}
            </span>
          </td>
          <td></td>
        </tr>
      </template>
    </el-table>

    <el-button
      type="primary"
      size="small"
      @click="handleAddRow"
      :disabled="disabled"
      style="margin-top: 10px"
    >
      + 添加行
    </el-button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import ReferenceField from './ReferenceField.vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'change'])

const localValue = ref([])
const subTableFields = computed(() => props.field.sub_table_fields || [])

watch(() => props.modelValue, (newVal) => {
  if (newVal !== localValue.value) {
    localValue.value = [...(newVal || [])]
  }
}, { immediate: true, deep: true })

watch(localValue, (newVal) => {
  emit('update:modelValue', newVal)
  emit('change', newVal)
}, { deep: true })

// 添加行
const handleAddRow = () => {
  const newRow = {}
  subTableFields.value.forEach(field => {
    if (field.default_value !== undefined) {
      newRow[field.code] = field.default_value
    } else if (field.field_type === 'number') {
      newRow[field.code] = 0
    } else {
      newRow[field.code] = ''
    }
  })
  localValue.value.push(newRow)
}

// 删除行
const handleDeleteRow = (index) => {
  localValue.value.splice(index, 1)
}

// 子字段值变化
const handleSubFieldChange = (rowIndex, fieldCode, value) => {
  updateSubTableFormulas(rowIndex, fieldCode, value)
}

// 更新子表公式
const updateSubTableFormulas = (rowIndex, triggerField, triggerValue) => {
  const row = localValue.value[rowIndex]

  subTableFields.value.forEach(field => {
    if (field.field_type === 'formula' && field.formula) {
      if (field.formula.includes(triggerField)) {
        const result = calculateRowFormula(field.formula, row)
        row[field.code] = result
      }
    }
  })
}

// 计算行内公式
const calculateRowFormula = (formula, row) => {
  let expression = formula
  for (const [key, value] of Object.entries(row)) {
    const regex = new RegExp(`\\{${key}\\}`, 'g')
    expression = expression.replace(regex, value || 0)
  }

  try {
    return new Function('return ' + expression)()
  } catch {
    return 0
  }
}

// 计算字段合计
const getFieldSum = (fieldCode) => {
  const field = subTableFields.value.find(f => f.code === fieldCode)
  if (!field || !field.show_sum) return ''

  const sum = localValue.value.reduce((total, row) => {
    return total + (parseFloat(row[fieldCode]) || 0)
  }, 0)

  return sum.toFixed(2)
}
</script>

<style scoped>
.sub-table-field {
  width: 100%;
}

.summary-row {
  background: #f5f7fa;
  font-weight: bold;
}

.summary-row td {
  padding: 8px;
}
</style>
```

### 6. 具体字段组件示例

```vue
<!-- src/components/engine/fields/TextField.vue -->
<template>
  <el-input
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :maxlength="field.max_length"
    :show-word-limit="field.show_word_limit"
    :type="field.field_type === 'textarea' ? 'textarea' : 'text'"
    :rows="field.rows || 2"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
defineProps({
  field: Object,
  modelValue: String,
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])
</script>
```

```vue
<!-- src/components/engine/fields/ReferenceField.vue -->
<template>
  <div class="reference-field">
    <el-select
      :model-value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :remote="true"
      :remote-method="searchReference"
      :loading="loading"
      filterable
      clearable
      value-key="id"
      @update:model-value="$emit('update:modelValue', $event)"
    >
      <el-option
        v-for="item in options"
        :key="item.id"
        :label="item[field.display_field || 'name']"
        :value="item.id"
      />
    </el-select>

    <el-button
      link
      type="primary"
      size="small"
      @click="handleSelect"
      style="margin-left: 8px"
    >
      选择
    </el-button>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { searchReferenceData } from '@/api/reference'

const props = defineProps({
  field: Object,
  modelValue: [String, Number],
  disabled: Boolean,
  placeholder: String
})

const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const options = ref([])

const searchReference = async (query) => {
  if (!query) {
    options.value = []
    return
  }

  loading.value = true
  try {
    const result = await searchReferenceData({
      reference_object: props.field.reference_object,
      search: query
    })
    options.value = result.items || []
  } finally {
    loading.value = false
  }
}

const handleSelect = () => {
  emit('open-selector', props.field)
}

watch(() => props.modelValue, async (newValue) => {
  if (newValue && options.value.length === 0) {
    const result = await searchReferenceData({
      reference_object: props.field.reference_object,
      ids: [newValue]
    })
    options.value = result.items || []
  }
}, { immediate: true })
</script>

<style scoped>
.reference-field {
  display: flex;
  align-items: center;
  width: 100%;
}

.reference-field .el-select {
  flex: 1;
}
</style>
```

### 7. 业务页面使用示例

```vue
<!-- src/views/assets/AssetForm.vue -->
<template>
  <div class="asset-form-page">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        {{ isEdit ? '编辑资产' : '新增资产' }}
      </template>
    </el-page-header>

    <el-card style="margin-top: 20px">
      <!-- 动态表单组件 -->
      <DynamicForm
        ref="formRef"
        business-object="Asset"
        layout-code="asset_form"
        v-model="formData"
        :field-permissions="fieldPermissions"
        @change="handleFormChange"
      />

      <!-- 表单操作按钮 -->
      <div class="form-actions">
        <el-button @click="goBack">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          保存
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import { getBusinessDataDetail, createBusinessData, updateBusinessData } from '@/api/dynamic'

const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const formData = ref({})
const submitting = ref(false)
const fieldPermissions = ref({})

const isEdit = computed(() => !!route.params.id)

const loadDetail = async () => {
  const id = route.params.id
  const data = await getBusinessDataDetail('Asset', id)
  formData.value = data

  if (route.query.fieldPermissions) {
    fieldPermissions.value = JSON.parse(route.query.fieldPermissions)
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await updateBusinessData('Asset', route.params.id, formData.value)
    } else {
      await createBusinessData('Asset', formData.value)
    }
    ElMessage.success('保存成功')
    goBack()
  } finally {
    submitting.value = false
  }
}

const handleFormChange = ({ fieldCode, value }) => {
  console.log('字段变化:', fieldCode, value)
}

const goBack = () => router.back()

onMounted(() => {
  if (isEdit.value) loadDetail()
})
</script>
```

## 组件目录结构

```
frontend/src/
├── components/
│   └── engine/
│       ├── DynamicForm.vue
│       ├── DynamicList.vue
│       ├── FieldRenderer.vue
│       ├── SectionLayout.vue
│       ├── fields/
│       │   ├── TextField.vue
│       │   ├── NumberField.vue
│       │   ├── DateField.vue
│       │   ├── SelectField.vue
│       │   ├── UserField.vue
│       │   ├── DeptField.vue
│       │   ├── ReferenceField.vue
│       │   ├── FormulaField.vue
│       │   ├── SubTableField.vue
│       │   ├── DisplayField.vue
│       │   └── BooleanField.vue
│       └── hooks/
│           ├── useDynamicForm.js
│           ├── useFieldPermissions.js
│           └── useFormula.js
├── api/
│   ├── metadata.js
│   └── dynamic.js
└── utils/
    └── formBuilder.js
```

## 实施步骤

1. ✅ 创建动态表单主组件 (DynamicForm.vue)
2. ✅ 创建字段渲染器 (FieldRenderer.vue)
3. ✅ 创建动态表单Hook (useDynamicForm.js)
4. ✅ 创建字段权限Hook (useFieldPermissions.js)
5. ✅ 创建各类型字段组件
6. ✅ 创建子表字段组件 (SubTableField.vue)
7. ✅ 配置API接口

## 输出产物

| 文件 | 说明 |
|------|------|
| `frontend/src/components/engine/DynamicForm.vue` | 动态表单主组件 |
| `frontend/src/components/engine/FieldRenderer.vue` | 字段渲染器 |
| `frontend/src/components/engine/fields/*.vue` | 各类型字段组件 |
| `frontend/src/components/engine/hooks/*.js` | 表单逻辑hooks |
| `frontend/src/api/metadata.js` | 元数据API |
| `frontend/src/api/dynamic.js` | 动态数据API |
