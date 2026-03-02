<!--
  RuleDesigner.vue - Visual Business Rule Designer
  Complete interface for creating and editing business rules
-->

<template>
  <div class="rule-designer">
    <!-- Header -->
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
          {{ isEdit ? '编辑规则' : '创建时"
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

    <!-- Main Form -->
    <div class="designer-body">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
        class="rule-form"
      >
        <!-- Basic Info Section -->
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
                label="规则编码'field_change')"
            class="field-trigger"
          >
            <el-form-item
              label="监听字段"
              class="mt-3"
            >
              <el-select
                v-model="formData.watch_fields"
                multiple
                filterable
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

        <!-- Condition Section -->
        <el-card
          class="form-card"
          shadow="never"
        >
          <template #header>
            <div class="card-header">
              <el-icon><Filter /></el-icon>
              <span>触发条件</span>
              <el-text
                size="small"
                type="info"
                class="header-hint"
              >
                满足以下条件时执行规则动�?
              </el-text>
            </div>
          </template>

          <ConditionBuilder
            v-model="formData.condition"
            :fields="fields"
            title="条件表达式"form-card"
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

    <!-- Test Dialog -->
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
              placeholder="输入 JSON 格式的测试数据"testResult"
          class="test-result"
        >
          <el-divider content-position="left">
            测试结果
          </el-divider>
          <el-alert
            :title="testResult.passed ? '条件满足' : '条件不满足'success' : 'warning'"
            show-icon
            :closable="false"
          />
          <pre class="result-json">{{ JSON.stringify(testResult, null, 2) }}</pre>
        </h3>
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
  fields: () => []
})

const emit = defineEmits<{
  back: []
  saved: [rule: any]
}>()

const { getRuleById, createRule, updateRule, evaluateRule } = useBusinessRulesApi()

// State
const formRef = ref()
const saving = ref(false)
const testDialogVisible = ref(false)
const testData = ref('{}')
const testResult = ref<any>(null)

const formData = reactive({
  rule_code: '',
  rule_name: '',
  rule_type: 'validation' as 'validation' | 'visibility' | 'computed' | 'linkage' | 'trigger',
  priority: 0,
  is_active: true,
  description: '',
  trigger_events: ['update'] as string[],
  watch_fields: [] as string[],
  condition: {} as Record<string, any>,
  action: {} as Record<string, any>
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

// Load rule data if editing
onMounted(async () => {
  if (props.ruleId) {
    try {
      const rule = await getRuleById(props.ruleId)
      Object.assign(formData, rule)
    } catch (error) {
      ElMessage.error('加载规则失败')
    }
  }
})

// Actions
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

    let result
    if (isEdit.value) {
      result = await updateRule(props.ruleId!, payload)
    } else {
      result = await createRule(payload)
    }

    ElMessage.success(isEdit.value ? '规则已更新' : '规则已创建')
    emit('saved', result)
  } catch (error: any) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

function handleTest() {
  // Pre-fill with sample data based on fields
  const sampleData: Record<string, any> = {}
  props.fields.forEach(field => {
    if (field.type === 'number') {
      sampleData[field.code] = 0
    } else if (field.type === 'boolean') {
      sampleData[field.code] = false
    } else {
      sampleData[field.code] = ''
    }
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
  } catch (error: any) {
    if (error instanceof SyntaxError) {
      ElMessage.error('测试数据 JSON 格式无效')
    } else {
      ElMessage.error(error.message || '测试失败')
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

.header-hint {
  margin-left: auto;
}

.full-width {
  width: 100%;
}

.mt-3 {
  margin-top: 12px;
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
