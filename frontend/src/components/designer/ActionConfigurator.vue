<!--
  ActionConfigurator.vue - Configure rule actions based on rule type
-->

<template>
  <div class="action-configurator">
    <div class="config-header">
      <span class="header-title">动作配置</span>
      <el-tag
        :type="ruleTypeTag.type"
        size="small"
      >
        {{ ruleTypeTag.label }}
      </el-tag>
    </div>

    <div class="config-content">
      <template v-if="ruleType === 'validation'">
        <el-form-item label="错误消息 (中文)">
          <el-input
            :model-value="action.error_message"
            placeholder="请输入验证失败时显示的中文消息"
            @update:model-value="updateAction('error_message', $event)"
          />
        </el-form-item>
        <el-form-item label="错误消息 (英文)">
          <el-input
            :model-value="action.error_message_en"
            placeholder="Enter English message for validation failure"
            @update:model-value="updateAction('error_message_en', $event)"
          />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-radio-group
            :model-value="action.severity || 'error'"
            @update:model-value="updateAction('severity', $event)"
          >
            <el-radio value="error">
              错误
            </el-radio>
            <el-radio value="warning">
              警告
            </el-radio>
            <el-radio value="info">
              提示
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'visibility'">
        <el-form-item label="目标字段">
          <el-select
            :model-value="action.target_fields"
            multiple
            filterable
            placeholder="选择要控制显示/隐藏的字段"
            @update:model-value="updateAction('target_fields', $event)"
          >
            <el-option
              v-for="field in fields"
              :key="field.code"
              :label="field.name"
              :value="field.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="显示状态">
          <el-radio-group
            :model-value="action.visible ?? true"
            @update:model-value="updateAction('visible', $event)"
          >
            <el-radio :value="true">
              显示
            </el-radio>
            <el-radio :value="false">
              隐藏
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'computed'">
        <el-form-item label="目标字段">
          <el-select
            :model-value="action.target_field"
            filterable
            placeholder="选择计算结果存储字段"
            @update:model-value="updateAction('target_field', $event)"
          >
            <el-option
              v-for="field in fields"
              :key="field.code"
              :label="field.name"
              :value="field.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="计算表达式">
          <el-input
            :model-value="action.formula"
            type="textarea"
            :rows="4"
            placeholder="例如: {amount} * 1.13"
            @update:model-value="updateAction('formula', $event)"
          />
          <el-text
            size="small"
            type="info"
            class="formula-hint"
          >
            可用 {field_code} 引用字段值
          </el-text>
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'linkage'">
        <el-form-item label="联动类型">
          <el-radio-group
            :model-value="action.linkage_type || 'set_value'"
            @update:model-value="updateAction('linkage_type', $event)"
          >
            <el-radio value="set_value">
              设置值
            </el-radio>
            <el-radio value="load_options">
              加载选项
            </el-radio>
            <el-radio value="clear">
              清空
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标字段">
          <el-select
            :model-value="action.target_field"
            filterable
            placeholder="选择被联动字段"
            @update:model-value="updateAction('target_field', $event)"
          >
            <el-option
              v-for="field in fields"
              :key="field.code"
              :label="field.name"
              :value="field.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标值">
          <el-input
            :model-value="action.value"
            placeholder="设置字段的新值（可选）"
            @update:model-value="updateAction('value', $event)"
          />
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'trigger'">
        <el-form-item label="动作类型">
          <el-select
            :model-value="action.type || 'webhook'"
            @update:model-value="updateAction('type', $event)"
          >
            <el-option
              label="Webhook"
              value="webhook"
            />
            <el-option
              label="消息通知"
              value="notify"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="接口地址">
          <el-input
            :model-value="action.api_endpoint"
            placeholder="https://example.com/hooks/rule"
            @update:model-value="updateAction('api_endpoint', $event)"
          />
        </el-form-item>
        <el-form-item label="请求方法">
          <el-select
            :model-value="action.api_method || 'POST'"
            @update:model-value="updateAction('api_method', $event)"
          >
            <el-option
              label="POST"
              value="POST"
            />
            <el-option
              label="PUT"
              value="PUT"
            />
          </el-select>
        </el-form-item>
      </template>

      <template v-else>
        <el-form-item label="规则配置(JSON)">
          <el-input
            :model-value="JSON.stringify(action, null, 2)"
            type="textarea"
            :rows="6"
            @update:model-value="updateActionJson"
          />
        </el-form-item>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type TagType = 'primary' | 'success' | 'info' | 'warning' | 'danger'

interface FieldOption {
  code: string
  name: string
  type: string
}

interface RuleAction {
  [key: string]: unknown
  error_message?: string
  error_message_en?: string
  severity?: 'error' | 'warning' | 'info'
  target_fields?: string[]
  visible?: boolean
  target_field?: string
  formula?: string
  linkage_type?: 'set_value' | 'load_options' | 'clear'
  value?: string | number | boolean | null
  type?: 'webhook' | 'notify'
  api_endpoint?: string
  api_method?: 'POST' | 'PUT'
}

interface Props {
  modelValue: RuleAction
  ruleType: string
  fields?: FieldOption[]
}

const props = withDefaults(defineProps<Props>(), {
  fields: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: RuleAction]
}>()

const action = computed<RuleAction>(() => props.modelValue || {})

const ruleTypeTag = computed(() => {
  const types: Record<string, { type: TagType; label: string }> = {
    validation: { type: 'danger', label: '校验规则' },
    visibility: { type: 'warning', label: '显示规则' },
    computed: { type: 'info', label: '计算规则' },
    linkage: { type: 'success', label: '联动规则' },
    trigger: { type: 'primary', label: '触发规则' }
  }
  return types[props.ruleType] || { type: 'info' as TagType, label: props.ruleType || '规则' }
})

function updateAction(key: string, value: unknown) {
  emit('update:modelValue', {
    ...action.value,
    [key]: value
  })
}

function updateActionJson(json: string) {
  try {
    const parsed = JSON.parse(json) as unknown
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return
    emit('update:modelValue', parsed as RuleAction)
  } catch {
    // ignore invalid json
  }
}
</script>

<style scoped>
.action-configurator {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
  border-radius: 8px 8px 0 0;
}

.header-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.config-content {
  padding: 16px;
}

.config-content :deep(.el-form-item) {
  margin-bottom: 16px;
}

.config-content :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.config-content :deep(.el-form-item__label) {
  color: var(--el-text-color-regular);
}

.formula-hint {
  margin-top: 4px;
}
</style>
