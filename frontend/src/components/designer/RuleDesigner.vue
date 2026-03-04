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
          返回
        </el-button>
        <h3 class="title">
          {{ isEdit ? '编辑规则' : '创建规则' }}
        </h3>
      </div>
      <div class="header-right">
        <el-button @click="handleTest">
          <el-icon><VideoPlay /></el-icon>
          测试规则
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSave"
        >
          <el-icon><Check /></el-icon>
          保存
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
              <span>基本信息</span>
            </div>
          </template>

          <el-row :gutter="24">
            <el-col :span="12">
              <el-form-item
                label="规则编码"
                prop="rule_code"
              >
                <el-input
                  v-model="formData.rule_code"
                  placeholder="如: validate_amount_limit"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item
                label="规则名称"
                prop="rule_name"
              >
                <el-input
                  v-model="formData.rule_name"
                  placeholder="请输入规则名称"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item
                label="规则类型"
                prop="rule_type"
              >
                <el-select
                  v-model="formData.rule_type"
                  class="full-width"
                >
                  <el-option
                    label="校验规则"
                    value="validation"
                  />
                  <el-option
                    label="显示规则"
                    value="visibility"
                  />
                  <el-option
                    label="计算规则"
                    value="computed"
                  />
                  <el-option
                    label="联动规则"
                    value="linkage"
                  />
                  <el-option
                    label="触发规则"
                    value="trigger"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="优先级">
                <el-input-number
                  v-model="formData.priority"
                  :min="0"
                  :max="9999"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="启用状态">
                <el-switch
                  v-model="formData.is_active"
                  active-text="启用"
                  inactive-text="停用"
                />
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="描述">
                <el-input
                  v-model="formData.description"
                  type="textarea"
                  :rows="3"
                  placeholder="可选，描述规则用途和范围"
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
              <span>触发配置</span>
            </div>
          </template>

          <el-form-item label="触发事件">
            <el-checkbox-group v-model="formData.trigger_events">
              <el-checkbox label="create">
                新建
              </el-checkbox>
              <el-checkbox label="update">
                更新
              </el-checkbox>
              <el-checkbox label="submit">
                提交
              </el-checkbox>
              <el-checkbox label="approve">
                审批
              </el-checkbox>
              <el-checkbox label="field_change">
                字段变更
              </el-checkbox>
            </el-checkbox-group>
          </el-form-item>

          <div
            v-if="formData.trigger_events.includes('field_change')"
            class="field-trigger"
          >
            <el-form-item label="监听字段">
              <el-select
                v-model="formData.watch_fields"
                multiple
                filterable
                class="full-width"
                placeholder="选择要监听变化的字段"
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
              <span>触发条件</span>
            </div>
          </template>
          <ConditionBuilder
            v-model="formData.condition"
            :fields="fields"
            title="条件表达式"
          />
        </el-card>

        <el-card
          class="form-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <el-icon><Operation /></el-icon>
              <span>规则动作</span>
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
      title="规则测试"
      width="600px"
    >
      <div class="test-content">
        <el-form label-width="80px">
          <el-form-item label="测试数据">
            <el-input
              v-model="testData"
              type="textarea"
              :rows="8"
              placeholder="输入 JSON 格式的测试数据"
            />
          </el-form-item>
        </el-form>

        <div
          v-if="testResult"
          class="test-result"
        >
          <el-divider content-position="left">
            测试结果
          </el-divider>
          <el-alert
            :title="testResult.is_valid ? '条件满足' : '条件不满足'"
            :type="testResult.is_valid ? 'success' : 'warning'"
            show-icon
            :closable="false"
          />
          <pre class="result-json">{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="testDialogVisible = false">
          关闭
        </el-button>
        <el-button
          type="primary"
          @click="runTest"
        >
          执行测试
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
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
  rule_type: 'validation' as 'validation' | 'visibility' | 'computed' | 'linkage' | 'trigger',
  priority: 0,
  is_active: true,
  description: '',
  trigger_events: ['update'] as string[],
  watch_fields: [] as string[],
  condition: {} as Record<string, unknown>,
  action: {} as Record<string, unknown>
})

const formRules = {
  rule_code: [
    { required: true, message: '请输入规则编码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '只允许小写字母、数字和下划线', trigger: 'blur' }
  ],
  rule_name: [
    { required: true, message: '请输入规则名称', trigger: 'blur' }
  ],
  rule_type: [
    { required: true, message: '请选择规则类型', trigger: 'change' }
  ]
}

const isEdit = computed(() => !!props.ruleId)

onMounted(async () => {
  if (!props.ruleId) return
  try {
    const rule = await getRuleById(props.ruleId)
    Object.assign(formData, rule)
  } catch {
    ElMessage.error('加载规则失败')
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

    ElMessage.success(isEdit.value ? '规则已更新' : '规则已创建')
    emit('saved', result)
  } catch (error: unknown) {
    ElMessage.error(getErrorMessage(error, '保存失败'))
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
      ElMessage.error('测试数据 JSON 格式无效')
    } else {
      ElMessage.error(getErrorMessage(error, '测试失败'))
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
