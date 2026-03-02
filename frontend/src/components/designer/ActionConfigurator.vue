<!--
  ActionConfigurator.vue - Configure rule actions based on rule type
  Different UI for validation, visibility, computed, linkage, trigger rules
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
      <!-- Validation Rule Actions -->
      <template v-if="ruleType === 'validation'">
        <el-form-item label="错误消息 (中文)">
          <el-input
            :model-value="action.error_message"
            placeholder="请输入验证失败时显示的消息"
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
          </el-input>
        </el-form-item>
      </template>

      <!-- Visibility Rule Actions -->
      <template v-else-if="ruleType === 'visibility'">
        <el-form-item label="目标字段">
          <el-select
            :model-value="action.target_fields"
            multiple
            filterable
            placeholder="选择要控制的字段"
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

      <!-- Computed Rule Actions -->
      <template v-else-if="ruleType === 'computed'">
        <el-form-item label="目标字段">
          <el-select
            :model-value="action.target_field"
            filterable
            placeholder="选择计算结果存储的字段"
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
          </el-select>
        </el-form-item>
        <el-form-item label="目标字段">
          <el-select
            :model-value="action.target_field"
            filterable
            placeholder="选择被联动的字段"
            :model-value="action.api_method || 'POST'"
            @update:model-value="updateAction('api_method', $event)"
          >
            <el-radio value="POST">
              POST
            </el-radio>
            <el-radio value="PUT">
              PUT
            </el-radio>
            </el-radio-group>
          </el-select>
        </el-form-item>
      </template>
    </div>
  </div>
</template>

      <!-- Default fallback -->
      <template v-else>
        <el-form-item label="规则配置">
          <el-input
            :model-value="JSON.stringify(action, null, 2)"
            type="textarea"
            :rows="5"
            @update:model-value="updateActionJson"
          />
        </el-form-item>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface FieldOption {
  code: string
  name: string
  type: string
}

interface Props {
  modelValue: Record<string, any>
  ruleType: string
  fields?: FieldOption[]
}

const props = withDefaults(defineProps<Props>(), {
  fields: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

const action = computed(() => props.modelValue || {})

const ruleTypeTag = computed(() => {
  const types: Record<string, { type: string; label: string }> = {
    validation: { type: 'danger', label: '校验规则' },
    visibility: { type: 'warning', label: '显示规则' },
    computed: { type: 'info', label: '计算规则' },
    linkage: { type: 'success', label: '联动规则' },
    trigger: { type: 'primary', label: '触发规则' },
  }
  return types[props.ruleType] || { type: 'info', label: props.ruleType }
})

function updateAction(key: string, value: any) {
  emit('update:modelValue', {
    ...action.value,
    [key]: value
  })
}

function updateActionJson(json: string) {
  try {
    const parsed = JSON.parse(json)
    emit('update:modelValue', parsed)
  } catch {
    // Invalid JSON, ignore
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
