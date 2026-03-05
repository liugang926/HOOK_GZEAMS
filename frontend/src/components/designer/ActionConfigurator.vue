<!--
  ActionConfigurator.vue - Configure rule actions based on rule type
-->

<template>
  <div class="action-configurator">
    <div class="config-header">
      <span class="header-title">{{ t('system.businessRule.designer.actionConfigurator.title') }}</span>
      <el-tag
        :type="ruleTypeTag.type"
        size="small"
      >
        {{ ruleTypeTag.label }}
      </el-tag>
    </div>

    <div class="config-content">
      <template v-if="ruleType === 'validation'">
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.errorMessageLocal')">
          <el-input
            :model-value="action.error_message"
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.errorMessageLocal')"
            @update:model-value="updateAction('error_message', $event)"
          />
        </el-form-item>
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.errorMessageEnglish')">
          <el-input
            :model-value="action.error_message_en"
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.errorMessageEnglish')"
            @update:model-value="updateAction('error_message_en', $event)"
          />
        </el-form-item>
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.severity')">
          <el-radio-group
            :model-value="action.severity || 'error'"
            @update:model-value="updateAction('severity', $event)"
          >
            <el-radio value="error">
              {{ t('system.businessRule.designer.actionConfigurator.severity.error') }}
            </el-radio>
            <el-radio value="warning">
              {{ t('system.businessRule.designer.actionConfigurator.severity.warning') }}
            </el-radio>
            <el-radio value="info">
              {{ t('system.businessRule.designer.actionConfigurator.severity.info') }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'visibility'">
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.targetFields')">
          <el-select
            :model-value="action.target_fields"
            multiple
            filterable
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.targetFields')"
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
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.visibility')">
          <el-radio-group
            :model-value="action.visible ?? true"
            @update:model-value="updateAction('visible', $event)"
          >
            <el-radio :value="true">
              {{ t('system.businessRule.designer.actionConfigurator.visibility.show') }}
            </el-radio>
            <el-radio :value="false">
              {{ t('system.businessRule.designer.actionConfigurator.visibility.hide') }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'computed'">
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.targetField')">
          <el-select
            :model-value="action.target_field"
            filterable
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.computedTargetField')"
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
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.formula')">
          <el-input
            :model-value="action.formula"
            type="textarea"
            :rows="4"
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.formula')"
            @update:model-value="updateAction('formula', $event)"
          />
          <el-text
            size="small"
            type="info"
            class="formula-hint"
          >
            {{ t('system.businessRule.designer.actionConfigurator.formulaHint') }}
          </el-text>
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'linkage'">
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.linkageType')">
          <el-radio-group
            :model-value="action.linkage_type || 'set_value'"
            @update:model-value="updateAction('linkage_type', $event)"
          >
            <el-radio value="set_value">
              {{ t('system.businessRule.designer.actionConfigurator.linkageTypes.setValue') }}
            </el-radio>
            <el-radio value="load_options">
              {{ t('system.businessRule.designer.actionConfigurator.linkageTypes.loadOptions') }}
            </el-radio>
            <el-radio value="clear">
              {{ t('system.businessRule.designer.actionConfigurator.linkageTypes.clear') }}
            </el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.targetField')">
          <el-select
            :model-value="action.target_field"
            filterable
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.linkageTargetField')"
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
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.targetValue')">
          <el-input
            :model-value="action.value"
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.targetValue')"
            @update:model-value="updateAction('value', $event)"
          />
        </el-form-item>
      </template>

      <template v-else-if="ruleType === 'trigger'">
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.actionType')">
          <el-select
            :model-value="action.type || 'webhook'"
            @update:model-value="updateAction('type', $event)"
          >
            <el-option
              :label="t('system.businessRule.designer.actionConfigurator.actionTypes.webhook')"
              value="webhook"
            />
            <el-option
              :label="t('system.businessRule.designer.actionConfigurator.actionTypes.notify')"
              value="notify"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.apiEndpoint')">
          <el-input
            :model-value="action.api_endpoint"
            :placeholder="t('system.businessRule.designer.actionConfigurator.placeholders.apiEndpoint')"
            @update:model-value="updateAction('api_endpoint', $event)"
          />
        </el-form-item>
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.apiMethod')">
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
        <el-form-item :label="t('system.businessRule.designer.actionConfigurator.labels.ruleConfigJson')">
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
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()

const action = computed<RuleAction>(() => props.modelValue || {})

const ruleTypeTagMap: Record<string, { type: TagType; labelKey: string }> = {
  validation: { type: 'danger', labelKey: 'system.businessRule.types.validation' },
  visibility: { type: 'warning', labelKey: 'system.businessRule.types.visibility' },
  computed: { type: 'info', labelKey: 'system.businessRule.types.computed' },
  linkage: { type: 'success', labelKey: 'system.businessRule.types.linkage' },
  trigger: { type: 'primary', labelKey: 'system.businessRule.types.trigger' }
}

const ruleTypeTag = computed(() => {
  const typeConfig = ruleTypeTagMap[props.ruleType]
  if (typeConfig) {
    return {
      type: typeConfig.type,
      label: t(typeConfig.labelKey)
    }
  }
  return {
    type: 'info' as TagType,
    label: props.ruleType || t('system.businessRule.designer.actionConfigurator.unknownRule')
  }
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
