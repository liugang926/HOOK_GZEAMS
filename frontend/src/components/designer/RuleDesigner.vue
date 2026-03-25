<!--
  RuleDesigner.vue - Visual Business Rule Designer
  Complete interface for creating and editing business rules
-->

<template>
  <div class="rule-designer">
    <div class="designer-header">
      <div class="header-left">
        <el-button
          link
          @click="$emit('back')"
        >
          <el-icon><ArrowLeft /></el-icon>
          {{ t('common.actions.back') }}
        </el-button>
        <h3 class="title">
          {{ isEdit ? t('system.businessRule.editTitle') : t('system.businessRule.createTitle') }}
        </h3>
      </div>
      <div class="header-right">
        <el-button @click="handleTest">
          <el-icon><VideoPlay /></el-icon>
          {{ t('common.actions.test') }}
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSave"
        >
          <el-icon><Check /></el-icon>
          {{ t('common.actions.save') }}
        </el-button>
      </div>
    </div>

    <div class="designer-body">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="rule-form"
      >
        <el-card
          class="form-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <el-icon><InfoFilled /></el-icon>
              <span>{{ t('common.basicInfo') }}</span>
            </div>
          </template>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item
                :label="t('system.businessRule.columns.code')"
                prop="rule_code"
              >
                <el-input
                  v-model="formData.rule_code"
                  :placeholder="t('system.businessRule.designer.placeholders.ruleCode')"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item
                :label="t('system.businessRule.columns.name')"
                prop="rule_name"
              >
                <el-input
                  v-model="formData.rule_name"
                  :placeholder="t('system.businessRule.designer.placeholders.ruleName')"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item
                :label="t('system.businessRule.columns.type')"
                prop="rule_type"
              >
                <el-select
                  v-model="formData.rule_type"
                  class="full-width"
                >
                  <el-option
                    :label="t('system.businessRule.types.validation')"
                    value="validation"
                  />
                  <el-option
                    :label="t('system.businessRule.types.visibility')"
                    value="visibility"
                  />
                  <el-option
                    :label="t('system.businessRule.types.computed')"
                    value="computed"
                  />
                  <el-option
                    :label="t('system.businessRule.types.linkage')"
                    value="linkage"
                  />
                  <el-option
                    :label="t('system.businessRule.types.trigger')"
                    value="trigger"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('system.businessRule.columns.priority')">
                <el-input-number
                  v-model="formData.priority"
                  :min="0"
                  :max="9999"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('system.businessRule.columns.status')">
                <el-switch
                  v-model="formData.is_active"
                  :active-text="t('common.status.active')"
                  :inactive-text="t('common.status.inactive')"
                />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item :label="t('common.description')">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="3"
                  :placeholder="t('system.businessRule.designer.placeholders.description')"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-card>

        <el-card
          class="form-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <el-icon><Timer /></el-icon>
              <span>{{ t('system.businessRule.designer.triggerConfig') }}</span>
            </div>
          </template>

          <el-form-item :label="t('system.businessRule.designer.triggerEvents')">
            <el-checkbox-group v-model="formData.trigger_events">
              <el-checkbox label="create">
                {{ t('common.actions.create') }}
              </el-checkbox>
              <el-checkbox label="update">
                {{ t('system.businessRule.designer.events.update') }}
              </el-checkbox>
              <el-checkbox label="submit">
                {{ t('system.businessRule.designer.events.submit') }}
              </el-checkbox>
              <el-checkbox label="approve">
                {{ t('system.businessRule.designer.events.approve') }}
              </el-checkbox>
              <el-checkbox label="field_change">
                {{ t('system.businessRule.designer.events.fieldChange') }}
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <div
            v-if="formData.trigger_events.includes('field_change')"
            class="field-trigger"
          >
            <el-form-item :label="t('system.businessRule.designer.watchFields')">
              <el-select
                v-model="formData.watch_fields"
                multiple
                filterable
                class="full-width"
                :placeholder="t('system.businessRule.designer.watchFieldsPlaceholder')"
              >
                <el-option
                  v-for="field in fields"
                  :key="field.code"
                  :label="field.name"
                  :value="field.code"
                />
              </el-select>
            </el-form-item>
          </div>
        </el-card>

        <el-card
          class="form-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <el-icon><Filter /></el-icon>
              <span>{{ t('system.businessRule.designer.triggerCondition') }}</span>
            </div>
          </template>
          <ConditionBuilder
            v-model="formData.condition"
            :fields="fields"
            :title="t('system.businessRule.designer.conditionExpression')"
          />
        </el-card>

        <el-card
          class="form-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>{{ t('system.businessRule.designer.ruleActions') }}</span>
            </div>
          </template>
          <ActionConfigurator
            v-model="formData.action"
            :rule-type="formData.rule_type"
            :fields="fields"
          />
        </el-card>
      </el-form>
    </div>

    <el-dialog
      v-model="testDialogVisible"
      :title="t('system.businessRule.messages.testTitle')"
      width="600px"
    >
      <div class="test-content">
        <el-form label-width="80px">
          <el-form-item :label="t('system.businessRule.messages.testData')">
            <el-input
              v-model="testData"
              type="textarea"
              :rows="8"
              :placeholder="t('system.businessRule.messages.testDataPlaceholder')"
            />
          </el-form-item>
        </el-form>

        <div
          v-if="testResult"
          class="test-result"
        >
          <el-divider content-position="left">
            {{ t('system.businessRule.messages.testResult') }}
          </el-divider>
          <el-alert
            :title="testResult.is_valid ? t('system.businessRule.messages.testPassed') : t('system.businessRule.messages.testFailed')"
            :type="testResult.is_valid ? 'success' : 'warning'"
            show-icon
            :closable="false"
          />
          <pre class="result-json">{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="testDialogVisible = false">
          {{ t('common.actions.close') }}
        </el-button>
        <el-button
          type="primary"
          @click="runTest"
        >
          {{ t('common.actions.test') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  Check,
  VideoPlay,
  InfoFilled,
  Timer,
  Filter,
  Operation
} from '@element-plus/icons-vue'
import ConditionBuilder from './ConditionBuilder.vue'
import ActionConfigurator from './ActionConfigurator.vue'
import { useBusinessRulesApi } from '@/api/businessRules'
import type { BusinessRule, RuleEvaluationResult } from '@/api/businessRules'

interface FieldOption {
  code: string
  name: string
  type: string
}

interface Props {
  objectCode: string
  ruleId?: string
  fields?: FieldOption[]
}

const props = withDefaults(defineProps<Props>(), {
  ruleId: '',
  fields: () => []
})

const emit = defineEmits<{
  back: []
  saved: [rule: BusinessRule]
}>()

const { t } = useI18n()
const { getRuleById, createRule, updateRule, evaluateRule } = useBusinessRulesApi()

interface RuleFormData {
  rule_code: string
  rule_name: string
  rule_type: 'validation' | 'visibility' | 'computed' | 'linkage' | 'trigger'
  priority: number
  is_active: boolean
  description: string
  trigger_events: string[]
  watch_fields: string[]
  condition: Record<string, unknown>
  action: Record<string, unknown>
}

const formRef = ref<any>(null)
const saving = ref(false)
const testDialogVisible = ref(false)
const testData = ref('{}')
const testResult = ref<RuleEvaluationResult | null>(null)

const formData = reactive<RuleFormData>({
  rule_code: '',
  rule_name: '',
  rule_type: 'validation',
  priority: 0,
  is_active: true,
  description: '',
  trigger_events: ['update'],
  watch_fields: [],
  condition: {},
  action: {}
})

const formRules = {
  rule_code: [
    {
      required: true,
      message: t('common.validation.requiredWithField', { field: t('system.businessRule.columns.code') }),
      trigger: 'blur'
    },
    {
      pattern: /^[a-z][a-z0-9_]*$/,
      message: t('common.validation.lowercaseNumberUnderscore'),
      trigger: 'blur'
    }
  ],
  rule_name: [
    {
      required: true,
      message: t('common.validation.requiredWithField', { field: t('system.businessRule.columns.name') }),
      trigger: 'blur'
    }
  ],
  rule_type: [
    {
      required: true,
      message: t('common.validation.requiredWithField', { field: t('system.businessRule.columns.type') }),
      trigger: 'change'
    }
  ]
}

const isEdit = computed(() => !!props.ruleId)

onMounted(async () => {
  if (!props.ruleId) return
  try {
    const rule = await getRuleById(props.ruleId)
    Object.assign(formData, rule)
  } catch {
    ElMessage.error(t('common.messages.loadFailed'))
  }
})

function getErrorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === 'object' && 'message' in error) {
    const message = (error as { message?: unknown }).message
    if (typeof message === 'string' && message.trim()) return message
  }
  return fallback
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    const payload = {
      ...formData,
      business_object_code: props.objectCode
    }

    const result = isEdit.value
      ? await updateRule(props.ruleId!, payload)
      : await createRule(payload)

    ElMessage.success(isEdit.value ? t('common.messages.updateSuccess') : t('common.messages.createSuccess'))
    emit('saved', result)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, t('common.messages.operationFailed')))
  } finally {
    saving.value = false
  }
}

function handleTest() {
  const sampleData: Record<string, unknown> = {}
  props.fields.forEach((field) => {
    if (field.type === 'number') sampleData[field.code] = 0
    else if (field.type === 'boolean') sampleData[field.code] = false
    else sampleData[field.code] = ''
  })
  testData.value = JSON.stringify(sampleData, null, 2)
  testResult.value = null
  testDialogVisible.value = true
}

async function runTest() {
  try {
    const data = JSON.parse(testData.value)
    const result = await evaluateRule(props.objectCode, {
      record: data,
      event: 'update'
    })
    testResult.value = result
  } catch (error: unknown) {
    if (error instanceof SyntaxError) {
      ElMessage.error(t('system.businessRule.messages.invalidJson'))
    } else {
      ElMessage.error(getErrorMessage(error, t('system.businessRule.messages.testFailed')))
    }
  }
}
</script>

<style scoped>
.rule-designer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--el-bg-color-page);
}

.designer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  gap: 12px;
}

.designer-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.rule-form {
  max-width: 900px;
  margin: 0 auto;
}

.form-card {
  margin-bottom: 20px;
}

.form-card :deep(.el-card__header) {
  padding: 14px 20px;
  background: var(--el-fill-color-light);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.full-width {
  width: 100%;
}

.field-trigger {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--el-border-color-lighter);
}

.test-content {
  min-height: 200px;
}

.test-result {
  margin-top: 16px;
}

.result-json {
  margin-top: 12px;
  padding: 12px;
  background: var(--el-fill-color);
  border-radius: 4px;
  font-size: 12px;
  font-family: monospace;
  overflow-x: auto;
  max-height: 200px;
}
</style>
