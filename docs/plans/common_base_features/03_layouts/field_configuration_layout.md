# 字段配置与布局规范

## 1. 字段配置概述

### 1.0 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 1.0 公共模型引用

> **Core Dependency**:
> 本文档详细解释字段属性的**解析逻辑 (Resolution Logic)**。
> 所有数据结构定义（如 `FieldReference`, `ValidationRule`）均以 [00_layout_common_models.md](./00_layout_common_models.md) 为准。

### 1.1 字段驱动配置架构 (Field-Driven Architecture)

系统遵循 **"Single Source of Truth"** 原则：

1.  **FieldDef (L0)**: 定义**能力 (Capability)** 和 **约束 (Constraint)**。
    *   *e.g. 字段类型, 可否排序, 正则校验, 必填约束*
2.  **PageLayout (L2)**: 定义**默认展示 (Default Presentation)**。
    *   *e.g. 默认列宽, 默认Label, 默认分组*
3.  **UserConfig (L1)**: 定义**个人偏好 (Personal Preference)**。
    *   *e.g. 隐藏某列, 调整列序, 个性化Label*

**优先级合并策略 (Merge Strategy)**：

| 属性 | 来源 | 合并逻辑 |
| :--- | :--- | :--- |
| **Label** | Field.name | `User.label_override ?? Page.label ?? Field.name` |
| **Visible** | Field.is_hidden | `!Field.hidden && (User.visible ?? Page.visible ?? true)` |
| **Required** | Field.is_required | `Field.required || Page.required` (约束叠加) |
| **Readonly**| Field.is_readonly | `Field.readonly || Page.readonly` (约束叠加) |

---

## 2. 字段显示配置

### 2.1 标签配置 (label)

### 2.1 标签配置 (Label Resolution)

#### 2.1.1 定义位置

- **L0 (FieldDefinition)**: `name` (默认数据库字段名)
- **L2 (LayoutConfig)**: `label_override` (在特定页面重命名)

**PageLayout 配置示例 (FieldReference)：**

```json
{
  "field_code": "asset_name",
  "label_override": "资产全称",  // 覆盖默认的 "资产名称"
  "label_width": "120px"
}
```

**支持的格式**:
- 像素值: `"100px"`, `"120px"`
- 百分比: `"20%"`, `"30%"`
- 自动: `"auto"` (默认)
- 全局配置: 在 PageLayout 级别设置统一标签宽度

#### 2.1.3 标签对齐方式

```json
{
  "field": "asset_code",
  "label": "资产编码",
  "label_align": "right"  // left / center / right
}
```

#### 2.1.4 占位符 (placeholder)

```json
{
  "field": "asset_name",
  "placeholder": "请输入资产名称"
}
```

**不同字段类型的占位符示例**:

```json
{
  "text_field": {
    "placeholder": "请输入文本内容"
  },
  "select_field": {
    "placeholder": "请选择选项"
  },
  "date_field": {
    "placeholder": "请选择日期"
  },
  "number_field": {
    "placeholder": "请输入数字"
  }
}
```

#### 2.1.5 帮助文本 (help_text)

```json
{
  "field": "serial_number",
  "label": "序列号",
  "help_text": "设备的唯一序列号,通常位于设备底部标签上"
}
```

**前端渲染**:

```vue
<el-form-item :label="field.label">
  <el-input v-model="value" :placeholder="field.placeholder" />
  <div class="help-text">{{ field.help_text }}</div>
</el-form-item>
```

#### 2.1.6 提示图标

```json
{
  "field": "depreciation_rate",
  "label": "折旧率",
  "tooltip": {
    "icon": "QuestionFilled",
    "content": "年折旧率,通常在5%-20%之间",
    "placement": "top"
  }
}
```

---

## 3. Field Layout Configuration

Layout configuration handles the arrangement and visual presentation of fields. It strictly follows the **Common Layout Models** defined in `00_layout_common_models.md`.

### 3.1 Column Width (`span`)

Field width is controlled by the `span` property, based on a 24-column grid system.

**Priority:** `PageLayout` (L2) > `FieldDefinition` (L0)

#### 3.1.1 Basic Span
In `PageLayout`:

```json
{
  "sections": [
    {
      "key": "section_basic",
      "columns": 2,  // Parent section has 2 columns
      "fields": [
        {
          "field_code": "code",
          "span": 1  // Occupies 1 column unit
        },
        {
          "field_code": "description",
          "span": 2  // Occupies 2 column units (full width of the section)
        }
      ]
    }
  ]
}
```

#### 3.1.2 Responsive Span
Responsive breakpoints can be defined in `PageLayout`:

```json
{
  "field_code": "image_preview",
  "styles": {
    "span": {
      "xs": 24,    // Mobile: Full width
      "sm": 12,    // Tablet: Half width
      "md": 8,     // Desktop: 1/3 width
      "lg": 6      // Large: 1/4 width
    }
  }
}
```

### 3.2 Field Ordering

Field order is determined by the sequence of `FieldReference` objects within the `fields` array of a `SectionConfig` or `PageLayout`.

**Priority:** `UserConfig` (L1 - if customizable) > `PageLayout` (L2)

### 3.3 Grouping (Sections & Tabs)

Grouping is handled by `SectionConfig` and `TabConfig` models. See `00_layout_common_models.md` for full schemas.

#### 3.3.1 Sections
```json
{
  "sections": [
    {
      "key": "basic_info",
      "title": "Basic Information",
      "fields": [
        { "field_code": "code" },
        { "field_code": "name" }
      ]
    },
    {
      "key": "details",
      "title": "Details",
      "collapsible": true,
      "fields": [
        { "field_code": "brand" },
        { "field_code": "model" }
      ]
    }
  ]
}
```

---

## 4. Field States Configuration

Field states (`required`, `readonly`, `visible`, `disabled`) are determined by merging Level 0 `FieldDefinition` attributes with Level 2 `PageLayout` overrides, following the **Attribute Priority Matrix**.

### 4.1 Required State

**Priority:** `PageLayout` (L2) > `FieldDefinition` (L0)

*   **L0 (FieldDefinition):** Defines the business rule (e.g., "Code is always mandatory").
*   **L2 (PageLayout):** Can make a field mandatory in a specific form context (e.g., "Reason is mandatory only in Approval Form").

#### 4.1.1 Configuration
```json
// PageLayout
{
  "field_code": "close_reason",
  "required": true // Overrides L0 if L0 is false
}
```

#### 4.1.2 Conditional Required
Used for dynamic validation logic.

```json
{
  "field_code": "other_description",
  "validation_rules": [
    {
      "type": "required",
      "trigger": "blur",
      "conditions": [
        {
          "field_code": "category",
          "operator": "eq",
          "value": "other"
        }
      ]
    }
  ]
}
```

### 4.2 Readonly & Disabled State

**Priority:** `PageLayout` (L2) > `FieldDefinition` (L0)

*   **Readonly:** Field value cannot be changed, but text can be selected/copied. Often used for generic display.
*   **Disabled:** Field is non-interactive. Often used for permission restrictions or logic-based blocking.

#### 4.2.1 Conditional Readonly
```json
{
  "field_code": "price",
  "readonly_when": {
    "conditions": [
      {
        "field_code": "status",
        "operator": "in",
        "value": ["approved", "archived"]
      }
    ]
  }
}
```

### 4.3 Visibility State

**Priority:** `PageLayout` (L2) > `FieldDefinition` (L0)

Visibility logic is handled by the `VisibilityRule` model.

#### 4.3.1 Configuration
```json
{
  "field_code": "warranty_period",
  "visibility": {
    "logic": "and",
    "conditions": [
      {
        "field_code": "has_warranty",
        "operator": "eq",
        "value": true
      }
    ]
  }
}
```

---

## 5. Field Validation Configuration

Validation rules are centrally defined in `FieldDefinition` (L0) to ensure data integrity, but can be enhanced or contextually overridden by `PageLayout` (L2).

**Model:** `ValidationRule` (see `00_layout_common_models.md`)

### 5.1 Common Validators

| Type | Parameters | Description |
| :--- | :--- | :--- |
| `required` | `message` | Checks if value is empty. |
| `pattern` | `pattern`, `message` | Regex validation. |
| `min`, `max` | `value`, `message` | Number range or string length. |
| `email`, `url` | `message` | Built-in format checkers. |
| `custom` | `handler`, `message` | Custom function name. |

### 5.2 Example Configuration

```json
{
  "field_code": "email",
  "validation_rules": [
    {
      "type": "required",
      "message": "Email is required",
      "trigger": "blur"
    },
    {
      "type": "email",
      "message": "Please enter a valid email",
      "trigger": ["blur", "change"]
    }
  ]
}
```

### 5.3 Asynchronous Validation

Used for backend checks (e.g., uniqueness).

```json
{
  "field_code": "code",
  "validation_rules": [
    {
      "type": "custom",
      "handler": "checkUnique",
      "message": "Code already exists",
      "trigger": "blur"
    }
  ]
}
```

---

## 6. Field Style Configuration

Field styling can be customized via the `styles` property in `FieldReference`.

### 6.1 Custom Classes
```json
{
  "field_code": "total_amount",
  "styles": {
    "class_name": "text-lg font-bold text-primary"
  }
}
```

### 6.2 Conditional Styles
(Reserved for future implementation - currently handled via custom renderers if complex logic is needed).

        "background_color": "#fee",
        "color": "#f56c6c",
        "font_weight": "bold"
      }
    },
    {
      "condition": {
        "field": "status",
        "operator": "equals",
        "value": "normal"
      },
      "style": {
        "background_color": "#f0f9ff",
        "color": "#409eff"
      }
    }
  ]
}
```

**动态样式计算**:

```vue
<template>
  <el-form-item
    :class="getFieldClasses(field)"
    :style="getFieldStyles(field)"
  >
    <!-- field content -->
  </el-form-item>
</template>

<script setup>
function getFieldClasses(field) {
  const classes = []

  // 基础类
  if (field.class_name) {
    classes.push(field.class_name)
  }

  // 状态类
  if (field.required) {
    classes.push('required-field')
  }
  if (field.readonly) {
    classes.push('readonly-field')
  }

  // 条件样式类
  if (field.conditional_styles) {
    for (const style_rule of field.conditional_styles) {
      if (evaluateCondition(style_rule.condition, formData.value)) {
        classes.push(style_rule.class_name)
      }
    }
  }

  return classes.join(' ')
}

function getFieldStyles(field) {
  const styles = {}

  if (field.conditional_styles) {
    for (const style_rule of field.conditional_styles) {
      if (evaluateCondition(style_rule.condition, formData.value)) {
        Object.assign(styles, style_rule.style)
      }
    }
  }

  return styles
}
</script>
```

### 6.3 字段容器样式

```json
{
  "field": "description",
  "container_style": {
    "margin_bottom": "20px",
    "padding": "15px",
    "border": "1px solid #e4e7ed",
    "border_radius": "4px",
    "background_color": "#fafafa"
  }
}
```

---

## 7. 字段联动配置

### 7.1 级联显示/隐藏

```json
{
  "field": "asset_type",
  "cascade_config": {
    "visibility": [
      {
        "id": "rule_001",
        "target_field": "serial_number",
        "condition": {
          "logic": "AND",
          "rules": [
            {
              "field": "asset_type",
              "operator": "equals",
              "value": "IT设备"
            }
          ]
        },
        "show_when": true,
        "enabled": true
      }
    ]
  }
}
```

### 7.2 级联启用/禁用

```json
{
  "field": "is_warranty",
  "cascade_config": {
    "disabled": [
      {
        "id": "rule_002",
        "target_field": "warranty_date",
        "condition": {
          "logic": "AND",
          "rules": [
            {
              "field": "is_warranty",
              "operator": "equals",
              "value": false
            }
          ]
        },
        "disabled_when": true,
        "enabled": true
      }
    ]
  }
}
```

### 7.3 级联选项更新

```json
{
  "field": "province",
  "cascade_config": {
    "options": [
      {
        "id": "rule_003",
        "target_field": "city",
        "trigger_field": "province",
        "load_mode": "api",
        "api_config": {
          "endpoint": "/api/locations/cities/",
          "method": "GET",
          "params": {
            "province": "{{province}}"
          },
          "label_field": "name",
          "value_field": "code"
        },
        "clear_on_empty": true,
        "enabled": true
      }
    ]
  }
}
```

### 7.4 级联值填充

```json
{
  "field": "quantity",
  "cascade_config": {
    "value": [
      {
        "id": "rule_004",
        "target_field": "total_amount",
        "expression": "quantity * unit_price",
        "expression_type": "formula",
        "auto_commit": true,
        "decimal_places": 2,
        "enabled": true
      }
    ]
  }
}
```

**详细实现**参见: `field_cascade.md`

---

## 8. 完整配置示例

### 8.1 简单字段配置

```json
{
  "field": "asset_name",
  "label": "资产名称",
  "span": 1,
  "required": true,
  "placeholder": "请输入资产名称",
  "help_text": "资产的正式名称,用于标识和管理"
}
```

### 8.2 复杂字段配置

```json
{
  "field": "purchase_price",
  "label": "采购价格",
  "span": 1,
  "required": true,
  "placeholder": "请输入采购价格",
  "default_value": 0,
  "help_text": "含税采购价格(元)",
  "tooltip": {
    "icon": "QuestionFilled",
    "content": "指采购资产时支付的全部费用,包括购买价款、相关税费、运输费等",
    "placement": "top"
  },
  "validation_rules": [
    {
      "type": "required",
      "message": "采购价格不能为空"
    },
    {
      "type": "min",
      "value": 0,
      "message": "采购价格不能小于0"
    },
    {
      "type": "pattern",
      "value": "^\\d+(\\.\\d{1,2})?$",
      "message": "请输入有效的价格格式(最多两位小数)"
    }
  ],
  "readonly_when": {
    "field": "status",
    "operator": "in",
    "value": ["已入库", "已领用", "已调拨"]
  },
  "class_name": "price-field",
  "formatter": "formatCurrency",
  "conditional_styles": [
    {
      "condition": {
        "field": "purchase_price",
        "operator": "gt",
        "value": 10000
      },
      "style": {
        "color": "#e6a23c",
        "font_weight": "bold"
      }
    }
  ]
}
```

### 8.3 表单布局完整示例

```json
{
  "layout_type": "form",
  "layout_mode": "tabs",
  "label_width": "120px",
  "label_position": "right",
  "tabs": [
    {
      "id": "tab_basic",
      "title": "基本信息",
      "icon": "Document",
      "sections": [
        {
          "id": "section_basic",
          "title": "基本资料",
          "columns": 2,
          "collapsible": false,
          "fields": [
            {
              "field": "code",
              "span": 1,
              "required": true,
              "readonly_when": {
                "field": "id",
                "operator": "is_not_empty",
                "value": null
              }
            },
            {
              "field": "name",
              "span": 1,
              "required": true,
              "placeholder": "请输入资产名称"
            },
            {
              "field": "category",
              "span": 2,
              "required": true,
              "placeholder": "请选择资产分类"
            },
            {
              "field": "status",
              "span": 1,
              "readonly": true,
              "default_value": "待入库"
            },
            {
              "field": "organization",
              "span": 1,
              "default_value": "@current_org",
              "readonly": true
            }
          ]
        },
        {
          "id": "section_detail",
          "title": "详细信息",
          "columns": 2,
          "collapsible": true,
          "collapsed": true,
          "fields": [
            {
              "field": "brand",
              "span": 1,
              "placeholder": "请输入品牌"
            },
            {
              "field": "model",
              "span": 1,
              "placeholder": "请输入型号"
            },
            {
              "field": "specification",
              "span": 2,
              "placeholder": "请输入规格型号"
            },
            {
              "field": "description",
              "span": 2,
              "field_type": "textarea",
              "placeholder": "请输入资产描述"
            }
          ]
        }
      ]
    },
    {
      "id": "tab_purchase",
      "title": "采购信息",
      "icon": "ShoppingCart",
      "sections": [
        {
          "id": "section_purchase",
          "title": "采购详情",
          "columns": 2,
          "fields": [
            {
              "field": "purchase_date",
              "span": 1,
              "required": true,
              "placeholder": "请选择采购日期"
            },
            {
              "field": "purchase_price",
              "span": 1,
              "required": true,
              "validation_rules": [
                {
                  "type": "min",
                  "value": 0,
                  "message": "采购价格不能小于0"
                }
              ]
            },
            {
              "field": "supplier",
              "span": 2,
              "placeholder": "请选择供应商"
            }
          ]
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "submit",
      "label": "提交",
      "type": "primary",
      "handler": "handleSubmit"
    },
    {
      "key": "reset",
      "label": "重置",
      "type": "default",
      "handler": "handleReset"
    },
    {
      "key": "cancel",
      "label": "取消",
      "type": "default",
      "handler": "handleCancel"
    }
  ]
}
```

---

## 9. 前端渲染实现

### 9.1 FieldRenderer 组件

```vue
<!-- frontend/src/components/engine/FieldRenderer.vue -->

<template>
  <el-form-item
    :label="fieldLabel"
    :prop="fieldCode"
    :required="isRequired"
    :rules="fieldRules"
    :class="fieldClasses"
    :style="fieldStyles"
  >
    <!-- 标签提示图标 -->
    <template #label>
      <span>{{ fieldLabel }}</span>
      <el-tooltip
        v-if="field.tooltip"
        :content="field.tooltip.content"
        :placement="field.tooltip.placement || 'top'"
      >
        <el-icon class="tooltip-icon">
          <component :is="field.tooltip.icon" />
        </el-icon>
      </el-tooltip>
    </template>

    <!-- 字段组件 -->
    <component
      :is="fieldComponent"
      v-model="localValue"
      v-bind="fieldProps"
      :disabled="isDisabled"
      :readonly="isReadonly"
      :placeholder="field.placeholder"
      @change="handleChange"
      @blur="handleBlur"
    />

    <!-- 帮助文本 -->
    <div v-if="field.help_text" class="help-text">
      {{ field.help_text }}
    </div>
  </el-form-item>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useFieldValidation } from '@/composables/useFieldValidation'

const props = defineProps({
  field: Object,
  modelValue: [String, Number, Boolean, Array, Object],
  formData: Object
})

const emit = defineEmits(['update:modelValue', 'change', 'blur'])

const localValue = ref(props.modelValue)

// 字段标签
const fieldLabel = computed(() => {
  return props.field.label || props.field.name || props.field.field_name
})

// 是否必填
const isRequired = computed(() => {
  // 基础必填
  if (props.field.required) {
    return true
  }

  // 条件必填
  if (props.field.required_when) {
    const { field, operator, value } = props.field.required_when
    return evaluateCondition(props.formData[field], operator, value)
  }

  return false
})

// 是否只读
const isReadonly = computed(() => {
  if (props.field.readonly) {
    return true
  }

  if (props.field.readonly_when) {
    return evaluateCondition(
      props.formData[props.field.readonly_when.field],
      props.field.readonly_when.operator,
      props.field.readonly_when.value
    )
  }

  return false
})

// 是否禁用
const isDisabled = computed(() => {
  return props.field.disabled || false
})

// 字段验证规则
const { fieldRules } = useFieldValidation(props.field)

// 字段CSS类
const fieldClasses = computed(() => {
  const classes = []

  if (props.field.class_name) {
    classes.push(props.field.class_name)
  }

  if (isRequired.value) {
    classes.push('required-field')
  }

  if (isReadonly.value) {
    classes.push('readonly-field')
  }

  // 条件样式
  if (props.field.conditional_styles) {
    for (const style_rule of props.field.conditional_styles) {
      if (evaluateCondition(style_rule.condition, props.formData)) {
        classes.push(style_rule.class_name || '')
      }
    }
  }

  return classes.join(' ')
})

// 字段样式
const fieldStyles = computed(() => {
  const styles = {}

  if (props.field.container_style) {
    Object.assign(styles, props.field.container_style)
  }

  if (props.field.conditional_styles) {
    for (const style_rule of props.field.conditional_styles) {
      if (evaluateCondition(style_rule.condition, props.formData)) {
        Object.assign(styles, style_rule.style)
      }
    }
  }

  return styles
})

// 字段组件
const fieldComponent = computed(() => {
  const fieldType = props.field.field_type || 'text'

  const componentMap = {
    text: 'el-input',
    textarea: 'el-input',
    number: 'el-input-number',
    date: 'el-date-picker',
    datetime: 'el-date-picker',
    select: 'el-select',
    multiselect: 'el-select',
    boolean: 'el-switch',
    radio: 'el-radio-group',
    checkbox: 'el-checkbox-group',
    reference: 'ReferenceField',
    formula: 'FormulaField',
    file: 'FileUpload',
    image: 'ImageUpload'
  }

  return componentMap[fieldType] || 'el-input'
})

// 字段属性
const fieldProps = computed(() => {
  const fieldType = props.field.field_type || 'text'
  const props = {}

  switch (fieldType) {
    case 'textarea':
      props.type = 'textarea'
      props.rows = props.field.rows || 3
      break

    case 'date':
      props.type = 'date'
      props.format = 'YYYY-MM-DD'
      props.valueFormat = 'YYYY-MM-DD'
      break

    case 'datetime':
      props.type = 'datetime'
      props.format = 'YYYY-MM-DD HH:mm:ss'
      props.valueFormat = 'YYYY-MM-DD HH:mm:ss'
      break

    case 'select':
    case 'multiselect':
      props.multiple = fieldType === 'multiselect'
      props.options = props.field.options || []
      break

    case 'number':
      props.min = props.field.min_value
      props.max = props.field.max_value
      props.precision = props.field.decimal_places || 2
      props.step = props.field.step || 1
      break
  }

  return props
})

// 条件评估函数
function evaluateCondition(fieldValue, operator, compareValue) {
  switch (operator) {
    case 'equals':
      return fieldValue == compareValue
    case 'not_equals':
      return fieldValue != compareValue
    case 'in':
      return Array.isArray(compareValue) && compareValue.includes(fieldValue)
    case 'not_in':
      return Array.isArray(compareValue) && !compareValue.includes(fieldValue)
    case 'gt':
      return Number(fieldValue) > Number(compareValue)
    case 'gte':
      return Number(fieldValue) >= Number(compareValue)
    case 'lt':
      return Number(fieldValue) < Number(compareValue)
    case 'lte':
      return Number(fieldValue) <= Number(compareValue)
    case 'is_empty':
      return !fieldValue
    case 'is_not_empty':
      return !!fieldValue
    default:
      return false
  }
}

// 处理值变化
function handleChange(value) {
  localValue.value = value
  emit('update:modelValue', value)
  emit('change', value)
}

// 处理失焦
function handleBlur() {
  emit('blur')
}

// 监听外部值变化
watch(() => props.modelValue, (newValue) => {
  localValue.value = newValue
})
</script>

<style scoped>
.help-text {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.tooltip-icon {
  margin-left: 4px;
  color: #909399;
  cursor: help;
}
</style>
```

---

## 10. 最佳实践

### 10.1 字段配置原则

1. **简洁性原则**
   - 避免过度复杂的条件嵌套
   - 保持字段名称简洁明了
   - 合理使用默认值

2. **一致性原则**
   - 同类型字段使用相似的配置
   - 标签宽度和对齐方式保持统一
   - 验证规则前后端一致

3. **用户体验优先**
   - 提供清晰的占位符和帮助文本
   - 合理设置字段顺序和分组
   - 必填字段明确标注

4. **性能优化**
   - 避免过多的实时验证
   - 异步验证使用防抖
   - 大表单分标签页组织

### 10.2 常见配置模式

#### 模式1: 只在编辑时显示的字段

```json
{
  "field": "updated_at",
  "label": "更新时间",
  "readonly": true,
  "visible": false,
  "visible_when": {
    "field": "id",
    "operator": "is_not_empty",
    "value": null
  }
}
```

#### 模式2: 根据权限显示的字段

```json
{
  "field": "purchase_price",
  "label": "采购价格",
  "visible": true,
  "visible_when": {
    "permission": "assets.view_price"
  }
}
```

#### 模式3: 级联下拉选择

```json
{
  "field": "province",
  "label": "省份",
  "required": true
},
{
  "field": "city",
  "label": "城市",
  "required": true,
  "visible_when": {
    "field": "province",
    "operator": "is_not_empty",
    "value": null
  },
  "options_source": {
    "type": "api",
    "endpoint": "/api/locations/cities/",
    "params": {
      "province": "{{province}}"
    }
  }
}
```

#### 模式4: 公式计算字段

```json
{
  "field": "total_amount",
  "label": "总金额",
  "readonly": true,
  "field_type": "formula",
  "formula_expression": "quantity * unit_price * (1 - discount_rate)",
  "decimal_places": 2,
  "formatter": "formatCurrency"
}
```

### 10.3 调试技巧

#### 前端调试

```javascript
// 在浏览器控制台查看字段配置
console.log('Field Config:', field)

// 查看表单数据
console.log('Form Data:', formData)

// 查看验证规则
console.log('Validation Rules:', formRules)

// 查看字段状态
console.log('Field State:', {
  required: isRequired.value,
  readonly: isReadonly.value,
  disabled: isDisabled.value,
  visible: isVisible.value
})
```

#### 后端调试

```python
# 查看字段定义
field_def = FieldDefinition.objects.get(field_name='asset_code')
print(field_def.__dict__)

# 查看布局配置
layout = PageLayout.objects.get(name='asset_form')
import json
print(json.dumps(layout.layout_config, indent=2, ensure_ascii=False))

# 验证配置
from apps.system.validators import CascadeFieldValidator
validator = CascadeFieldValidator(business_object)
validator.validate_cascade_config(cascade_config)
```

---

## 11. 附录

### 11.1 字段配置速查表

| 配置项 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `field` | string | - | 字段名称 (必填) |
| `label` | string | FieldDefinition.name | 显示标签 |
| `label_width` | string | "auto" | 标签宽度 |
| `label_align` | string | "right" | 标签对齐方式 |
| `span` | number\|object | 1 | 列宽配置 |
| `placeholder` | string | - | 占位符 |
| `help_text` | string | - | 帮助文本 |
| `tooltip` | object | - | 提示配置 |
| `required` | boolean | false | 是否必填 |
| `readonly` | boolean | false | 是否只读 |
| `disabled` | boolean | false | 是否禁用 |
| `visible` | boolean | true | 是否可见 |
| `default_value` | any | - | 默认值 |
| `options` | array | - | 选项列表 |
| `validation_rules` | array | - | 验证规则 |
| `class_name` | string | - | 自定义CSS类 |
| `container_style` | object | - | 容器样式 |
| `conditional_styles` | array | - | 条件样式 |

### 11.2 相关文档

| 文档 | 说明 |
|------|------|
| `page_layout_config.md` | PageLayout 完整配置规范 |
| `field_cascade.md` | 字段级联功能设计 |
| `metadata_frontend.md` | 元数据驱动前端组件 |
| `field_types.md` | 字段类型定义 |

### 11.3 更新日志

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0.0 | 2026-01-15 | Claude Code | 初始版本,完成字段配置与布局规范 |

---

**文档状态**: 🟢 已完成

**审核状态**: 待审核

**下一步行动**: 开始实现 FieldRenderer 组件和字段配置验证器
