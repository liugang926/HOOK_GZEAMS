# 字段级联功能设计文档

## 1. 设计目标

### 1.0 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

**注意**: 字段级联配置存储在 FieldDefinition.cascade_config JSON 字段中，不是独立的数据库表。

### 1.1 核心功能

字段级联是低代码平台的核心能力之一,实现字段间的动态关联和自动化计算,提升表单的智能化水平和用户体验。

#### 三种级联类型

1. **可见性级联 (Visibility Cascade)**
   - 根据字段值动态控制其他字段的显示/隐藏
   - 支持多条件组合逻辑(AND/OR)
   - 实时响应字段值变化

2. **选项级联 (Options Cascade)**
   - 根据上级字段值动态加载下级选项
   - 支持多级联动(省市区三级联动)
   - 支持API动态加载和静态选项映射

3. **值级联 (Value Cascade / Formula Calculation)**
   - 根据多个字段值自动计算目标字段值
   - 支持常用运算符和函数
   - 实时计算并更新结果

### 1.2 应用场景

#### 场景1: 资产入库单动态表单
```
资产类型选择 "IT设备" → 显示 "配置参数"、"序列号" 字段
资产类型选择 "办公家具" → 显示 "材质"、"尺寸" 字段
```

#### 场景2: 多组织架构选择
```
选择公司 → 动态加载该公司下的部门列表
选择部门 → 动态加载该部门下的员工列表
```

#### 场景3: 资产折旧计算
```
原值 * 残值率 = 残值
(原值 - 残值) / 使用年限 = 月折旧额
```

---

## 2. FieldDefinition 模型扩展

### 2.1 数据库模型设计

```python
# backend/apps/system/models.py

from django.db import models
from apps.common.models import BaseModel

class FieldDefinition(BaseModel):
    """
    字段定义模型 - 支持级联配置
    """
    # 现有字段
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='field_definitions',
        verbose_name='所属业务对象'
    )
    field_name = models.CharField(max_length=100, verbose_name='字段名称')
    field_type = models.CharField(
        max_length=50,
        choices=[
            ('text', '文本'),
            ('number', '数字'),
            ('date', '日期'),
            ('select', '下拉选择'),
            ('multiselect', '多选'),
            ('reference', '引用'),
            ('formula', '公式'),
            # ... 其他类型
        ],
        verbose_name='字段类型'
    )

    # ====== 新增: 级联配置字段 ======
    cascade_config = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='级联配置',
        help_text='字段级联规则配置'
    )

    class Meta:
        db_table = 'system_field_definitions'
        unique_together = [['business_object', 'field_name']]
        indexes = [
            models.Index(fields=['business_object', 'field_name']),
        ]
```

### 2.2 cascade_config 数据结构

#### 2.2.1 完整配置示例

```json
{
  "visibility": [
    {
      "id": "rule_001",
      "target_field": "city",
      "condition": {
        "logic": "AND",
        "rules": [
          {
            "field": "province",
            "operator": "equals",
            "value": "Beijing"
          },
          {
            "field": "country",
            "operator": "equals",
            "value": "China"
          }
        ]
      },
      "show_when": true,
      "enabled": true
    }
  ],
  "options": [
    {
      "id": "rule_002",
      "target_field": "district",
      "trigger_field": "city",
      "load_mode": "api",
      "api_config": {
        "endpoint": "/api/locations/districts/",
        "method": "GET",
        "params": {
          "city": "{{city}}"
        },
        "label_field": "name",
        "value_field": "id"
      },
      "static_mapping": null,
      "enabled": true
    }
  ],
  "value": [
    {
      "id": "rule_003",
      "target_field": "full_address",
      "expression": "province + ' ' + city + ' ' + street",
      "expression_type": "formula",
      "auto_commit": true,
      "enabled": true
    }
  ]
}
```

#### 2.2.2 可见性级联配置 (visibility)

```json
{
  "visibility": [
    {
      "id": "unique_rule_id",
      "target_field": "字段名称",           // 目标字段(被控制显示/隐藏的字段)
      "condition": {
        "logic": "AND",                    // 逻辑关系: AND / OR
        "rules": [
          {
            "field": "province",           // 触发字段
            "operator": "equals",          // 操作符: equals / not_equals / contains / in / gt / gte / lt / lte
            "value": "Beijing"             // 比较值
          },
          {
            "field": "country",
            "operator": "in",
            "value": ["China", "Singapore"]
          }
        ]
      },
      "show_when": true,                   // 满足条件时显示(true)或隐藏(false)
      "enabled": true                      // 规则是否启用
    }
  ]
}
```

**支持的操作符 (operators):**
- `equals`: 等于
- `not_equals`: 不等于
- `contains`: 包含(字符串模糊匹配)
- `not_contains`: 不包含
- `in`: 在列表中
- `not_in`: 不在列表中
- `is_empty`: 为空
- `is_not_empty`: 不为空
- `gt`: 大于(数字)
- `gte`: 大于等于
- `lt`: 小于
- `lte`: 小于等于

#### 2.2.3 选项级联配置 (options)

**模式A: API动态加载**
```json
{
  "options": [
    {
      "id": "rule_004",
      "target_field": "district",          // 目标字段
      "trigger_field": "city",             // 触发字段
      "load_mode": "api",                  // 加载模式: api / static
      "api_config": {
        "endpoint": "/api/locations/districts/",
        "method": "GET",
        "params": {
          "city": "{{city}}"               // 模板变量: 引用触发字段的值
        },
        "label_field": "name",             // 选项显示字段
        "value_field": "id"                // 选项值字段
      },
      "static_mapping": null,
      "clear_on_empty": true,              // 触发字段为空时清空目标字段
      "enabled": true
    }
  ]
}
```

**模式B: 静态选项映射**
```json
{
  "options": [
    {
      "id": "rule_005",
      "target_field": "district",
      "trigger_field": "city",
      "load_mode": "static",
      "api_config": null,
      "static_mapping": {
        "Beijing": [
          {"label": "朝阳区", "value": "chaoyang"},
          {"label": "海淀区", "value": "haidian"}
        ],
        "Shanghai": [
          {"label": "浦东新区", "value": "pudong"},
          {"label": "黄浦区", "value": "huangpu"}
        ]
      },
      "clear_on_empty": true,
      "enabled": true
    }
  ]
}
```

#### 2.2.4 值级联配置 (value)

```json
{
  "value": [
    {
      "id": "rule_006",
      "target_field": "total_amount",
      "expression": "quantity * unit_price",
      "expression_type": "formula",        // 表达式类型: formula / custom
      "auto_commit": true,                 // 自动提交到后端
      "decimal_places": 2,                 // 保留小数位
      "enabled": true
    }
  ]
}
```

**支持的公式表达式:**
- 基础运算: `+`, `-`, `*`, `/`, `%`
- 字段引用: 直接使用字段名(如 `quantity`, `unit_price`)
- 括号优先级: `(quantity + tax) * discount_rate`
- 内置函数:
  - `SUM(field1, field2, ...)`
  - `AVG(field1, field2, ...)`
  - `ROUND(value, decimal_places)`
  - `MAX(field1, field2, ...)`
  - `MIN(field1, field2, ...)`
  - `IF(condition, true_value, false_value)`
  - `CONCAT(str1, str2, ...)`
  - `DATEDIFF(end_date, start_date)` (天数差)
  - `NOW()` (当前时间)

---

## 3. 前端级联处理实现

### 3.1 useFieldCascade Hook

```javascript
// frontend/src/composables/useFieldCascade.js

import { ref, watch, computed } from 'vue'
import { debounce } from 'lodash-es'

export function useFieldCascade(formData, cascadeRules) {
  const loadingFields = ref(new Set())
  const fieldErrors = ref({})

  /**
   * 处理可见性级联
   */
  const handleVisibilityCascade = (rules) => {
    const visibilityMap = {}

    rules.forEach(rule => {
      if (!rule.enabled) return

      const { target_field, condition, show_when } = rule
      const shouldShow = evaluateCondition(condition, formData.value)

      visibilityMap[target_field] = show_when ? shouldShow : !shouldShow

      // 如果字段隐藏,清空其值
      if (!visibilityMap[target_field]) {
        formData.value[target_field] = null
      }
    })

    return visibilityMap
  }

  /**
   * 评估条件逻辑
   */
  const evaluateCondition = (condition, data) => {
    const { logic, rules: conditionRules } = condition

    const results = conditionRules.map(rule => {
      const fieldValue = data[rule.field]
      const compareValue = rule.value

      switch (rule.operator) {
        case 'equals':
          return fieldValue == compareValue
        case 'not_equals':
          return fieldValue != compareValue
        case 'contains':
          return String(fieldValue).includes(String(compareValue))
        case 'not_contains':
          return !String(fieldValue).includes(String(compareValue))
        case 'in':
          return Array.isArray(compareValue) && compareValue.includes(fieldValue)
        case 'not_in':
          return Array.isArray(compareValue) && !compareValue.includes(fieldValue)
        case 'is_empty':
          return !fieldValue
        case 'is_not_empty':
          return !!fieldValue
        case 'gt':
          return Number(fieldValue) > Number(compareValue)
        case 'gte':
          return Number(fieldValue) >= Number(compareValue)
        case 'lt':
          return Number(fieldValue) < Number(compareValue)
        case 'lte':
          return Number(fieldValue) <= Number(compareValue)
        default:
          return false
      }
    })

    return logic === 'AND'
      ? results.every(r => r)
      : results.some(r => r)
  }

  /**
   * 处理选项级联 - API动态加载
   */
  const loadOptionsCascade = async (rule) => {
    const { target_field, trigger_field, load_mode, api_config, static_mapping } = rule

    if (load_mode === 'static') {
      // 静态映射模式
      const triggerValue = formData.value[trigger_field]
      return static_mapping[triggerValue] || []
    }

    if (load_mode === 'api') {
      // API动态加载模式
      loadingFields.value.add(target_field)

      try {
        // 构建请求参数(替换模板变量)
        const params = {}
        Object.entries(api_config.params).forEach(([key, value]) => {
          params[key] = value.replace(/\{\{(\w+)\}\}/g, (_, fieldName) => {
            return formData.value[fieldName] || ''
          })
        })

        const response = await fetch(api_config.endpoint, {
          method: api_config.method,
          headers: { 'Content-Type': 'application/json' },
          body: api_config.method === 'GET' ? undefined : JSON.stringify(params)
        })

        const data = await response.json()

        // 转换为标准选项格式
        return data.map(item => ({
          label: item[api_config.label_field],
          value: item[api_config.value_field]
        }))
      } catch (error) {
        fieldErrors.value[target_field] = `加载选项失败: ${error.message}`
        return []
      } finally {
        loadingFields.value.delete(target_field)
      }
    }
  }

  /**
   * 处理值级联 - 公式计算
   */
  const evaluateFormula = (expression, context) => {
    // 安全的公式计算引擎(使用 simpleeval 或自行实现)
    try {
      // 替换字段引用
      let formula = expression
      Object.keys(context).forEach(fieldName => {
        const regex = new RegExp(`\\b${fieldName}\\b`, 'g')
        formula = formula.replace(regex, context[fieldName] || 0)
      })

      // 使用 Function 构造器进行安全计算
      // 注意: 生产环境应使用专门的公式解析库
      return eval(formula)
    } catch (error) {
      console.error('公式计算错误:', error)
      return null
    }
  }

  const handleValueCascade = (rules) => {
    rules.forEach(rule => {
      if (!rule.enabled) return

      const { target_field, expression, expression_type } = rule

      if (expression_type === 'formula') {
        const result = evaluateFormula(expression, formData.value)

        if (rule.decimal_places !== undefined) {
          formData.value[target_field] = Number(result).toFixed(rule.decimal_places)
        } else {
          formData.value[target_field] = result
        }
      }
    })
  }

  /**
   * 监听字段变化并触发级联
   */
  const setupCascadeWatchers = () => {
    const allTriggerFields = new Set()

    // 收集所有触发字段
    Object.values(cascadeRules).forEach(rules => {
      rules.forEach(rule => {
        if (rule.trigger_field) {
          allTriggerFields.add(rule.trigger_field)
        }
        if (rule.condition?.rules) {
          rule.condition.rules.forEach(r => {
            allTriggerFields.add(r.field)
          })
        }
      })
    })

    // 为每个触发字段设置监听器
    allTriggerFields.forEach(field => {
      watch(
        () => formData.value[field],
        debounce((newValue, oldValue) => {
          if (newValue === oldValue) return

          // 触发可见性级联
          if (cascadeRules.visibility?.length) {
            handleVisibilityCascade(cascadeRules.visibility)
          }

          // 触发选项级联
          if (cascadeRules.options?.length) {
            cascadeRules.options.forEach(rule => {
              if (rule.trigger_field === field) {
                loadOptionsCascade(rule)
              }
            })
          }

          // 触发值级联
          if (cascadeRules.value?.length) {
            handleValueCascade(cascadeRules.value)
          }
        }, 300),
        { deep: true }
      )
    })
  }

  return {
    loadingFields,
    fieldErrors,
    handleVisibilityCascade,
    loadOptionsCascade,
    handleValueCascade,
    setupCascadeWatchers
  }
}
```

### 3.2 DynamicForm 组件集成

```vue
<!-- frontend/src/components/engine/DynamicForm.vue -->

<template>
  <el-form :model="formData" :rules="formRules" ref="formRef">
    <el-form-item
      v-for="field in visibleFields"
      :key="field.field_name"
      :label="field.label"
      :prop="field.field_name"
      v-show="fieldVisibility[field.field_name] !== false"
    >
      <!-- 字段渲染器 -->
      <FieldRenderer
        :field="field"
        :value="formData[field.field_name]"
        :options="fieldOptions[field.field_name]"
        :loading="loadingFields.has(field.field_name)"
        @update:value="handleFieldChange(field.field_name, $event)"
      />
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useFieldCascade } from '@/composables/useFieldCascade'
import FieldRenderer from './FieldRenderer.vue'

const props = defineProps({
  fields: Array,           // 字段定义列表
  cascadeRules: Object,    // 级联规则
  initialData: Object
})

const emit = defineEmits(['update:modelValue'])

const formData = ref({ ...props.initialData })
const fieldOptions = ref({})
const formRules = ref({})

// 使用级联 Hook
const {
  loadingFields,
  fieldErrors,
  handleVisibilityCascade,
  loadOptionsCascade,
  handleValueCascade,
  setupCascadeWatchers
} = useFieldCascade(formData, props.cascadeRules)

// 字段可见性状态
const fieldVisibility = ref({})

// 计算可见字段列表
const visibleFields = computed(() => {
  return props.fields.filter(field => fieldVisibility.value[field.field_name] !== false)
})

// 初始化级联规则
const initCascade = () => {
  // 初始化可见性
  if (props.cascadeRules.visibility?.length) {
    fieldVisibility.value = handleVisibilityCascade(props.cascadeRules.visibility)
  } else {
    // 默认所有字段可见
    props.fields.forEach(field => {
      fieldVisibility.value[field.field_name] = true
    })
  }

  // 初始化选项
  if (props.cascadeRules.options?.length) {
    props.cascadeRules.options.forEach(async rule => {
      const options = await loadOptionsCascade(rule)
      fieldOptions.value[rule.target_field] = options
    })
  }

  // 设置字段变化监听
  setupCascadeWatchers()
}

// 处理字段值变化
const handleFieldChange = (fieldName, value) => {
  formData.value[fieldName] = value

  // 触发值级联计算
  if (props.cascadeRules.value?.length) {
    handleValueCascade(props.cascadeRules.value)
  }

  // 向父组件发送更新
  emit('update:modelValue', formData.value)
}

onMounted(() => {
  initCascade()
})
</script>
```

### 3.3 级联事件总线

```javascript
// frontend/src/utils/cascadeEvents.js

import { EventEmitter } from 'events'

class CascadeEventBus extends EventEmitter {
  constructor() {
    super()
    this.eventHistory = []
  }

  /**
   * 发布级联事件
   */
  publishCascadeEvent(eventType, payload) {
    const event = {
      type: eventType,
      payload,
      timestamp: new Date().toISOString()
    }

    this.eventHistory.push(event)
    this.emit('cascade', event)
  }

  /**
   * 订阅级联事件
   */
  subscribeToCascadeEvents(callback) {
    this.on('cascade', callback)
  }

  /**
   * 获取事件历史
   */
  getEventHistory(filter = {}) {
    let history = this.eventHistory

    if (filter.type) {
      history = history.filter(e => e.type === filter.type)
    }

    if (filter.fieldName) {
      history = history.filter(e =>
        e.payload.fieldName === filter.fieldName ||
        e.payload.targetField === filter.fieldName
      )
    }

    return history
  }
}

export const cascadeEventBus = new CascadeEventBus()
```

---

## 4. 后端级联验证实现

### 4.1 CascadeFieldValidator

```python
# backend/apps/system/validators.py

from rest_framework import serializers
from .simpleeval import EvalWithCompoundTypes

class CascadeFieldValidator:
    """
    字段级联规则验证器
    """

    def __init__(self, business_object):
        self.business_object = business_object

    def validate_cascade_config(self, cascade_config):
        """
        验证级联配置的完整性和正确性
        """
        errors = []

        # 验证可见性规则
        if 'visibility' in cascade_config:
            visibility_errors = self._validate_visibility_rules(
                cascade_config['visibility']
            )
            errors.extend(visibility_errors)

        # 验证选项规则
        if 'options' in cascade_config:
            options_errors = self._validate_options_rules(
                cascade_config['options']
            )
            errors.extend(options_errors)

        # 验证值规则
        if 'value' in cascade_config:
            value_errors = self._validate_value_rules(
                cascade_config['value']
            )
            errors.extend(value_errors)

        if errors:
            raise serializers.ValidationError({
                'cascade_config': errors
            })

        return cascade_config

    def _validate_visibility_rules(self, rules):
        """验证可见性规则"""
        errors = []

        for idx, rule in enumerate(rules):
            # 必填字段检查
            required_fields = ['id', 'target_field', 'condition', 'show_when']
            for field in required_fields:
                if field not in rule:
                    errors.append(
                        f"可见性规则[{idx}]: 缺少必填字段 '{field}'"
                    )

            # 验证目标字段存在性
            if 'target_field' in rule:
                if not self._field_exists(rule['target_field']):
                    errors.append(
                        f"可见性规则[{idx}]: 目标字段 '{rule['target_field']}' 不存在"
                    )

            # 验证条件逻辑
            if 'condition' in rule:
                condition_errors = self._validate_condition(rule['condition'], idx)
                errors.extend(condition_errors)

        return errors

    def _validate_condition(self, condition, rule_idx):
        """验证条件表达式"""
        errors = []

        if 'logic' not in condition:
            errors.append(f"规则[{rule_idx}]: 条件缺少 'logic' 字段")
            return errors

        if condition['logic'] not in ['AND', 'OR']:
            errors.append(
                f"规则[{rule_idx}]: 逻辑关系必须是 'AND' 或 'OR'"
            )

        if 'rules' not in condition or not isinstance(condition['rules'], list):
            errors.append(f"规则[{rule_idx}]: 条件缺少 'rules' 列表")
            return errors

        for sub_rule_idx, sub_rule in enumerate(condition['rules']):
            # 验证触发字段存在性
            if 'field' in sub_rule:
                if not self._field_exists(sub_rule['field']):
                    errors.append(
                        f"规则[{rule_idx}]: 触发字段 '{sub_rule['field']}' 不存在"
                    )

            # 验证操作符
            valid_operators = [
                'equals', 'not_equals', 'contains', 'not_contains',
                'in', 'not_in', 'is_empty', 'is_not_empty',
                'gt', 'gte', 'lt', 'lte'
            ]
            if 'operator' in sub_rule:
                if sub_rule['operator'] not in valid_operators:
                    errors.append(
                        f"规则[{rule_idx}]: 不支持的操作符 '{sub_rule['operator']}'"
                    )

        return errors

    def _validate_options_rules(self, rules):
        """验证选项级联规则"""
        errors = []

        for idx, rule in enumerate(rules):
            required_fields = ['id', 'target_field', 'trigger_field', 'load_mode']
            for field in required_fields:
                if field not in rule:
                    errors.append(
                        f"选项规则[{idx}]: 缺少必填字段 '{field}'"
                    )

            # 验证字段存在性
            if 'target_field' in rule:
                if not self._field_exists(rule['target_field']):
                    errors.append(
                        f"选项规则[{idx}]: 目标字段 '{rule['target_field']}' 不存在"
                    )

            if 'trigger_field' in rule:
                if not self._field_exists(rule['trigger_field']):
                    errors.append(
                        f"选项规则[{idx}]: 触发字段 '{rule['trigger_field']}' 不存在"
                    )

            # 验证加载模式
            if rule.get('load_mode') == 'api':
                if 'api_config' not in rule:
                    errors.append(
                        f"选项规则[{idx}]: API加载模式缺少 'api_config' 配置"
                    )
                else:
                    api_errors = self._validate_api_config(rule['api_config'], idx)
                    errors.extend(api_errors)

            elif rule.get('load_mode') == 'static':
                if 'static_mapping' not in rule:
                    errors.append(
                        f"选项规则[{idx}]: 静态加载模式缺少 'static_mapping' 配置"
                    )

        return errors

    def _validate_api_config(self, api_config, rule_idx):
        """验证API配置"""
        errors = []

        required_fields = ['endpoint', 'method', 'label_field', 'value_field']
        for field in required_fields:
            if field not in api_config:
                errors.append(
                    f"选项规则[{rule_idx}]: API配置缺少必填字段 '{field}'"
                )

        if 'method' in api_config and api_config['method'] not in ['GET', 'POST']:
            errors.append(
                f"选项规则[{rule_idx}]: 不支持的HTTP方法 '{api_config['method']}'"
            )

        return errors

    def _validate_value_rules(self, rules):
        """验证值级联规则"""
        errors = []

        for idx, rule in enumerate(rules):
            required_fields = ['id', 'target_field', 'expression']
            for field in required_fields:
                if field not in rule:
                    errors.append(
                        f"值规则[{idx}]: 缺少必填字段 '{field}'"
                    )

            # 验证目标字段存在性
            if 'target_field' in rule:
                if not self._field_exists(rule['target_field']):
                    errors.append(
                        f"值规则[{idx}]: 目标字段 '{rule['target_field']}' 不存在"
                    )

            # 验证公式表达式
            if 'expression' in rule:
                formula_errors = self._validate_formula(rule['expression'], idx)
                errors.extend(formula_errors)

        return errors

    def _validate_formula(self, expression, rule_idx):
        """验证公式表达式"""
        errors = []

        try:
            # 检查表达式中的字段引用是否有效
            fields = self._extract_field_references(expression)

            for field in fields:
                if not self._field_exists(field):
                    errors.append(
                        f"值规则[{rule_idx}]: 公式中引用的字段 '{field}' 不存在"
                    )

            # 尝试解析表达式语法
            # 使用空上下文测试表达式是否合法
            evaluator = EvalWithCompoundTypes({}, {})
            evaluator.eval(expression)

        except Exception as e:
            errors.append(
                f"值规则[{rule_idx}]: 公式表达式无效 - {str(e)}"
            )

        return errors

    def _extract_field_references(self, expression):
        """
        从公式表达式中提取字段引用
        简单实现: 提取所有可能的变量名
        """
        import re

        # 匹配字母开头的标识符
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        matches = re.findall(pattern, expression)

        # 过滤掉操作符和函数名
        keywords = {
            'SUM', 'AVG', 'MAX', 'MIN', 'ROUND', 'IF', 'CONCAT',
            'DATEDIFF', 'NOW', 'AND', 'OR', 'NOT', 'TRUE', 'FALSE'
        }

        fields = [m for m in matches if m not in keywords]

        return list(set(fields))

    def _field_exists(self, field_name):
        """检查字段是否存在于业务对象中"""
        return self.business_object.field_definitions.filter(
            field_name=field_name
        ).exists()
```

### 4.2 公式计算引擎

```python
# backend/apps/system/simpleeval.py

"""
安全的表达式求值引擎
基于 simpleeval 库进行扩展
"""

from operator import itemgetter
import re

class EvalWithCompoundTypes:
    """
    支持复合数据类型和字段引用的表达式求值器
    """

    # 支持的运算符
    OPERATORS = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b if b != 0 else 0,
        '%': lambda a, b: a % b if b != 0 else 0,
        '**': lambda a, b: a ** b,
    }

    # 比较运算符
    COMPARATORS = {
        '==': lambda a, b: a == b,
        '!=': lambda a, b: a != b,
        '<': lambda a, b: a < b,
        '<=': lambda a, b: a <= b,
        '>': lambda a, b: a > b,
        '>=': lambda a, b: a >= b,
    }

    def __init__(self, names=None, functions=None):
        self.names = names or {}
        self.functions = functions or {}

    def eval(self, expr):
        """
        计算表达式
        :param expr: 表达式字符串
        :return: 计算结果
        """
        # 替换字段名为实际值
        processed_expr = self._replace_names(expr)

        # 注册内置函数
        self._register_builtin_functions()

        # 安全的求值
        return self._safe_eval(processed_expr)

    def _replace_names(self, expr):
        """替换变量名为实际值"""
        result = expr

        # 按长度降序排序,避免部分替换问题
        sorted_names = sorted(self.names.keys(), key=len, reverse=True)

        for name in sorted_names:
            value = self.names.get(name)

            # 字符串值需要加引号
            if isinstance(value, str):
                value = f"'{value}'"
            elif isinstance(value, bool):
                value = str(value).upper()
            elif value is None:
                value = 'None'

            # 使用单词边界匹配,避免部分替换
            pattern = r'\b' + re.escape(name) + r'\b'
            result = re.sub(pattern, str(value), result)

        return result

    def _register_builtin_functions(self):
        """注册内置函数"""
        builtin_functions = {
            'SUM': sum,
            'AVG': lambda lst: sum(lst) / len(lst) if lst else 0,
            'MAX': max,
            'MIN': min,
            'ROUND': round,
            'ABS': abs,
            'IF': lambda condition, true_val, false_val: true_val if condition else false_val,
            'CONCAT': lambda *args: ''.join(str(arg) for arg in args),
            'NOW': lambda: datetime.now().isoformat(),
        }

        self.functions.update(builtin_functions)

    def _safe_eval(self, expr):
        """安全求值"""
        try:
            # 使用 ast.literal_eval 或限制 eval 的命名空间
            return eval(expr, {'__builtins__': None}, self.functions)
        except Exception as e:
            raise ValueError(f"表达式求值失败: {str(e)}")


# 使用示例
if __name__ == '__main__':
    from datetime import datetime

    # 模拟字段数据
    field_values = {
        'quantity': 10,
        'unit_price': 99.99,
        'discount_rate': 0.9,
        'province': 'Beijing',
        'city': 'Haidian'
    }

    # 创建求值器
    evaluator = EvalWithCompoundTypes(names=field_values)

    # 测试公式
    expressions = [
        'quantity * unit_price',
        'quantity * unit_price * discount_rate',
        'CONCAT(province, " ", city)',
        'ROUND(quantity * unit_price, 2)'
    ]

    for expr in expressions:
        result = evaluator.eval(expr)
        print(f"{expr} = {result}")
```

### 4.3 级联序列化器

```python
# backend/apps/system/serializers.py

from rest_framework import serializers
from .models import FieldDefinition
from .validators import CascadeFieldValidator

class FieldDefinitionSerializer(serializers.ModelSerializer):
    """字段定义序列化器 - 支持级联配置"""

    class Meta:
        model = FieldDefinition
        fields = [
            'id', 'business_object', 'field_name', 'field_type',
            'cascade_config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_cascade_config(self, value):
        """
        验证级联配置
        """
        if not value:
            return {}

        # 获取业务对象实例
        business_object = self.context.get('business_object')
        if business_object:
            # 使用级联验证器
            validator = CascadeFieldValidator(business_object)
            value = validator.validate_cascade_config(value)

        return value

    def to_representation(self, instance):
        """
        输出时格式化级联配置
        """
        data = super().to_representation(instance)

        # 格式化级联配置为前端友好格式
        if data.get('cascade_config'):
            data['cascade_config'] = self._format_cascade_config(
                data['cascade_config']
            )

        return data

    def _format_cascade_config(self, config):
        """格式化级联配置"""
        # 这里可以添加格式化逻辑
        return config
```

### 4.4 级联计算服务

```python
# backend/apps/system/services/cascade_service.py

from typing import Dict, Any, List
from .simpleeval import EvalWithCompoundTypes

class CascadeCalculationService:
    """
    级联计算服务
    """

    def __init__(self, field_definitions: List[FieldDefinition]):
        self.field_definitions = field_definitions
        self.cascade_rules = self._extract_cascade_rules()

    def _extract_cascade_rules(self) -> Dict[str, List]:
        """提取所有级联规则"""
        rules = {
            'visibility': [],
            'options': [],
            'value': []
        }

        for field_def in self.field_definitions:
            cascade_config = field_def.cascade_config

            if not cascade_config:
                continue

            # 提取可见性规则
            if 'visibility' in cascade_config:
                rules['visibility'].extend(cascade_config['visibility'])

            # 提取选项规则
            if 'options' in cascade_config:
                rules['options'].extend(cascade_config['options'])

            # 提取值规则
            if 'value' in cascade_config:
                rules['value'].extend(cascade_config['value'])

        return rules

    def calculate_value_cascades(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算所有值级联
        :param form_data: 表单数据
        :return: 更新后的表单数据
        """
        updated_data = form_data.copy()

        for rule in self.cascade_rules['value']:
            if not rule.get('enabled', True):
                continue

            target_field = rule['target_field']
            expression = rule['expression']

            # 创建求值器
            evaluator = EvalWithCompoundTypes(names=updated_data)

            try:
                # 计算公式
                result = evaluator.eval(expression)

                # 处理小数位
                if rule.get('decimal_places') is not None:
                    result = round(result, rule['decimal_places'])

                updated_data[target_field] = result

            except Exception as e:
                # 记录错误但不中断计算
                print(f"值级联计算失败 [{target_field}]: {str(e)}")
                continue

        return updated_data

    def get_visibility_map(self, form_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        计算字段可见性映射
        :param form_data: 表单数据
        :return: {字段名: 是否可见}
        """
        visibility_map = {}

        for rule in self.cascade_rules['visibility']:
            if not rule.get('enabled', True):
                continue

            target_field = rule['target_field']
            condition = rule['condition']
            show_when = rule.get('show_when', True)

            # 评估条件
            should_show = self._evaluate_condition(condition, form_data)

            visibility_map[target_field] = show_when if should_show else not show_when

        return visibility_map

    def _evaluate_condition(self, condition: Dict, data: Dict) -> bool:
        """评估条件"""
        logic = condition.get('logic', 'AND')
        rules = condition.get('rules', [])

        results = []

        for rule in rules:
            field = rule['field']
            operator = rule['operator']
            compare_value = rule.get('value')

            field_value = data.get(field)

            # 根据操作符判断
            result = self._compare_values(field_value, operator, compare_value)
            results.append(result)

        # 根据逻辑关系返回结果
        return all(results) if logic == 'AND' else any(results)

    def _compare_values(self, field_value: Any, operator: str, compare_value: Any) -> bool:
        """比较值"""
        if operator == 'equals':
            return field_value == compare_value
        elif operator == 'not_equals':
            return field_value != compare_value
        elif operator == 'contains':
            return str(compare_value) in str(field_value)
        elif operator == 'not_contains':
            return str(compare_value) not in str(field_value)
        elif operator == 'in':
            return field_value in compare_value if isinstance(compare_value, list) else False
        elif operator == 'not_in':
            return field_value not in compare_value if isinstance(compare_value, list) else True
        elif operator == 'is_empty':
            return not field_value
        elif operator == 'is_not_empty':
            return bool(field_value)
        elif operator == 'gt':
            return Number(field_value) > Number(compare_value)
        elif operator == 'gte':
            return Number(field_value) >= Number(compare_value)
        elif operator == 'lt':
            return Number(field_value) < Number(compare_value)
        elif operator == 'lte':
            return Number(field_value) <= Number(compare_value)

        return False
```

---

## 5. API 接口设计

### 5.1 获取级联配置

```http
GET /api/system/business-objects/{object_id}/cascade-config/
```

**响应示例:**
```json
{
  "business_object": "asset",
  "cascade_rules": {
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
        "show_when": true
      }
    ],
    "options": [
      {
        "id": "rule_002",
        "target_field": "district",
        "trigger_field": "city",
        "load_mode": "api",
        "api_config": {
          "endpoint": "/api/locations/districts/",
          "method": "GET",
          "params": {
            "city": "{{city}}"
          }
        }
      }
    ],
    "value": [
      {
        "id": "rule_003",
        "target_field": "total_amount",
        "expression": "quantity * unit_price"
      }
    ]
  }
}
```

### 5.2 验证级联配置

```http
POST /api/system/field-definitions/validate-cascade/
```

**请求体:**
```json
{
  "business_object_id": 1,
  "cascade_config": {
    "visibility": [...],
    "options": [...],
    "value": [...]
  }
}
```

**响应示例:**
```json
{
  "valid": true,
  "errors": []
}
```

### 5.3 动态加载选项API

```http
GET /api/locations/districts/?city=Beijing
```

**响应示例:**
```json
{
  "results": [
    {
      "id": "chaoyang",
      "name": "朝阳区"
    },
    {
      "id": "haidian",
      "name": "海淀区"
    }
  ]
}
```

---

## 6. 前端使用示例

### 6.1 在 DynamicForm 中使用

```vue
<template>
  <DynamicForm
    :fields="fieldDefinitions"
    :cascade-rules="cascadeRules"
    :initial-data="formData"
    @update:modelValue="handleFormUpdate"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import { getFieldDefinitions } from '@/api/system'

const fieldDefinitions = ref([])
const cascadeRules = ref({})
const formData = ref({})

onMounted(async () => {
  // 获取字段定义和级联规则
  const response = await getFieldDefinitions('asset')

  fieldDefinitions.value = response.fields
  cascadeRules.value = response.cascade_rules
})

const handleFormUpdate = (newData) => {
  formData.value = newData
  console.log('表单数据已更新:', newData)
}
</script>
```

### 6.2 手动触发级联

```javascript
import { useFieldCascade } from '@/composables/useFieldCascade'

const { setupCascadeWatchers } = useFieldCascade(formData, cascadeRules)

// 手动触发级联计算
const triggerCascade = () => {
  setupCascadeWatchers()
}
```

---

## 7. 测试用例

### 7.1 可见性级联测试

```python
# backend/apps/system/tests/test_cascade.py

from django.test import TestCase
from .models import FieldDefinition, BusinessObject

class VisibilityCascadeTestCase(TestCase):
    """可见性级联测试"""

    def setUp(self):
        self.business_object = BusinessObject.objects.create(
            name="TestObject",
            table_name="test_table"
        )

        # 创建字段定义
        self.province_field = FieldDefinition.objects.create(
            business_object=self.business_object,
            field_name="province",
            field_type="select"
        )

        self.city_field = FieldDefinition.objects.create(
            business_object=self.business_object,
            field_name="city",
            field_type="select",
            cascade_config={
                "visibility": [{
                    "id": "rule_001",
                    "target_field": "city",
                    "condition": {
                        "logic": "AND",
                        "rules": [{
                            "field": "province",
                            "operator": "equals",
                            "value": "Beijing"
                        }]
                    },
                    "show_when": True,
                    "enabled": True
                }]
            }
        )

    def test_visibility_condition_met(self):
        """测试条件满足时字段显示"""
        from .services.cascade_service import CascadeCalculationService

        service = CascadeCalculationService([self.city_field])

        form_data = {"province": "Beijing"}
        visibility_map = service.get_visibility_map(form_data)

        self.assertTrue(visibility_map.get("city"))

    def test_visibility_condition_not_met(self):
        """测试条件不满足时字段隐藏"""
        from .services.cascade_service import CascadeCalculationService

        service = CascadeCalculationService([self.city_field])

        form_data = {"province": "Shanghai"}
        visibility_map = service.get_visibility_map(form_data)

        self.assertFalse(visibility_map.get("city"))
```

### 7.2 值级联测试

```python
class ValueCascadeTestCase(TestCase):
    """值级联测试"""

    def setUp(self):
        self.business_object = BusinessObject.objects.create(
            name="TestObject",
            table_name="test_table"
        )

        self.total_field = FieldDefinition.objects.create(
            business_object=self.business_object,
            field_name="total_amount",
            field_type="number",
            cascade_config={
                "value": [{
                    "id": "rule_001",
                    "target_field": "total_amount",
                    "expression": "quantity * unit_price",
                    "expression_type": "formula",
                    "auto_commit": True,
                    "enabled": True
                }]
            }
        )

    def test_formula_calculation(self):
        """测试公式计算"""
        from .services.cascade_service import CascadeCalculationService

        service = CascadeCalculationService([self.total_field])

        form_data = {
            "quantity": 10,
            "unit_price": 99.99
        }

        updated_data = service.calculate_value_cascades(form_data)

        self.assertEqual(updated_data["total_amount"], 999.9)
```

---

## 8. 性能优化建议

### 8.1 前端优化

1. **防抖处理 (Debounce)**
   - 字段值变化时使用300ms防抖,避免频繁触发级联计算

2. **级联规则缓存**
   - 缓存已加载的选项数据,避免重复API请求

3. **懒加载**
   - 仅在字段首次可见时加载其级联选项

4. **虚拟滚动**
   - 对于大量选项的下拉框,使用虚拟滚动提升性能

### 8.2 后端优化

1. **级联配置缓存**
   - 使用Redis缓存业务对象的级联配置

2. **批量计算**
   - 一次性计算所有值级联,避免重复遍历

3. **索引优化**
   - 为 `business_object` 和 `field_name` 添加复合索引

4. **异步加载**
   - 对于耗时的API选项加载,使用Celery异步任务

---

## 9. 安全考虑

### 9.1 表达式注入防护

- 使用安全的公式计算引擎,禁用危险函数
- 限制表达式中的字段引用范围

### 9.2 API访问控制

- 验证API端点的访问权限
- 防止未授权的级联规则修改

### 9.3 数据验证

- 严格验证级联配置的完整性
- 防止循环依赖导致无限循环

---

## 10. 实施计划

### 10.1 第一阶段: 基础架构 (Week 1-2)
- [ ] 扩展 FieldDefinition 模型
- [ ] 实现 CascadeFieldValidator
- [ ] 开发公式计算引擎

### 10.2 第二阶段: 前端实现 (Week 3-4)
- [ ] 开发 useFieldCascade Hook
- [ ] 集成 DynamicForm 组件
- [ ] 实现级联事件总线

### 10.3 第三阶段: API与服务 (Week 5-6)
- [ ] 开发级联配置API
- [ ] 实现 CascadeCalculationService
- [ ] 添加单元测试

### 10.4 第四阶段: 测试与优化 (Week 7-8)
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 文档完善

---

## 11. 附录

### 11.1 相关文件清单

**后端文件:**
```
backend/apps/system/
├── models.py                    # FieldDefinition 模型扩展
├── serializers.py              # 级联配置序列化器
├── validators.py               # CascadeFieldValidator
├── services/
│   ├── cascade_service.py      # 级联计算服务
│   └── simpleeval.py           # 公式计算引擎
└── tests/
    └── test_cascade.py         # 级联测试用例
```

**前端文件:**
```
frontend/src/
├── composables/
│   └── useFieldCascade.js     # 级联 Hook
├── components/
│   └── engine/
│       ├── DynamicForm.vue    # 动态表单组件
│       └── FieldRenderer.vue  # 字段渲染器
└── utils/
    └── cascadeEvents.js       # 级联事件总线
```

### 11.2 数据库迁移脚本

```python
# backend/apps/system/migrations/000X_add_cascade_config.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('system', '000X_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='fielddefinition',
            name='cascade_config',
            field=models.JSONField(default=dict, blank=True, verbose_name='级联配置'),
        ),
    ]
```

---

## 12. 变更历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0.0 | 2026-01-15 | Claude Code | 初始版本,完成字段级联完整设计 |

---

**文档状态**: 🟢 已完成

**审核状态**: 待审核

**下一步行动**: 按照实施计划开始第一阶段开发
