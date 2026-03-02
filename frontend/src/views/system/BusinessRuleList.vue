<template>
  <div class="business-rule-list">
    <div class="list-header">
      <div class="header-left">
        <h4>{{ $t('system.businessRule.title') }}</h4>
        <el-tag
          type="warning"
          size="small"
          effect="plain"
        >
          {{ objectDisplayName }}
        </el-tag>
        <el-tag
          type="info"
          size="small"
        >
          {{ $t('common.labels.totalItems', { count: rules.length }) }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button
          type="primary"
          size="small"
          @click="handleCreate"
        >
          <el-icon><Plus /></el-icon>
          {{ $t('system.businessRule.create') }}
        </el-button>
      </div>
    </div>

    <el-tabs
      v-model="activeType"
      class="rule-tabs"
    >
      <el-tab-pane
        name="all"
        :label="$t('system.businessRule.types.all')"
      />
      <el-tab-pane
        name="validation"
        :label="$t('system.businessRule.types.validation')"
      />
      <el-tab-pane
        name="visibility"
        :label="$t('system.businessRule.types.visibility')"
      />
      <el-tab-pane
        name="computed"
        :label="$t('system.businessRule.types.computed')"
      />
      <el-tab-pane
        name="linkage"
        :label="$t('system.businessRule.types.linkage')"
      />
      <el-tab-pane
        name="trigger"
        :label="$t('system.businessRule.types.trigger')"
      />
    </el-tabs>

    <el-empty
      v-if="!loading && filteredRules.length === 0"
      :description="emptyDescription"
    >
      <el-button
        type="primary"
        size="small"
        @click="handleCreate"
      >
        {{ $t('system.businessRule.create') }}
      </el-button>
    </el-empty>

    <el-table
      v-else
      v-loading="loading"
      :data="filteredRules"
      stripe
      class="rules-table"
    >
      <el-table-column
        prop="rule_code"
        :label="$t('system.businessRule.columns.code')"
        width="150"
      >
        <template #default="{ row }">
          <el-text class="rule-code">
            {{ row.rule_code }}
          </el-text>
        </template>
      </el-table-column>

      <el-table-column
        prop="rule_name"
        :label="$t('system.businessRule.columns.name')"
        min-width="180"
      >
        <template #default="{ row }">
          <div class="rule-name-cell">
            <span>{{ row.rule_name }}</span>
            <el-text
              v-if="row.description"
              type="info"
              size="small"
              class="rule-desc"
            >
              {{ row.description }}
            </el-text>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        prop="rule_type"
        :label="$t('system.businessRule.columns.type')"
        width="110"
      >
        <template #default="{ row }">
          <el-tag
            :type="getRuleTypeStyle(row.rule_type)"
            size="small"
          >
            {{ row.rule_type_display || getRuleTypeLabel(row.rule_type) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        prop="priority"
        :label="$t('system.businessRule.columns.priority')"
        width="90"
        align="center"
      />

      <el-table-column
        prop="is_active"
        :label="$t('system.businessRule.columns.status')"
        width="90"
        align="center"
      >
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_active"
            size="small"
            @change="(val) => handleToggleActive(row, val)"
          />
        </template>
      </el-table-column>

      <el-table-column
        :label="$t('common.labels.operation')"
        width="180"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            size="small"
            @click="handleEdit(row)"
          >
            {{ $t('common.actions.edit') }}
          </el-button>
          <el-button
            link
            type="info"
            size="small"
            @click="handleTest(row)"
          >
            {{ $t('common.actions.test') }}
          </el-button>
          <el-popconfirm
            :title="$t('system.businessRule.messages.confirmDelete')"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
                size="small"
              >
                {{ $t('common.actions.delete') }}
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="designerVisible"
      :title="currentRule ? $t('system.businessRule.editTitle') : $t('system.businessRule.createTitle')"
      width="90%"
      top="5vh"
      destroy-on-close
      class="designer-dialog"
    >
      <RuleDesigner
        v-if="designerVisible"
        :object-code="objectCode"
        :rule-id="currentRule?.id"
        :fields="fields"
        @back="designerVisible = false"
        @saved="handleRuleSaved"
      />
    </el-dialog>

    <el-dialog
      v-model="testDialogVisible"
      :title="$t('system.businessRule.messages.testTitle')"
      width="600px"
    >
      <div class="test-content">
        <el-alert
          v-if="currentRule"
          :title="currentRule.rule_name"
          :type="getRuleTypeStyle(currentRule.rule_type)"
          :closable="false"
          show-icon
          class="rule-info"
        />

        <el-form label-width="80px">
          <el-form-item :label="$t('system.businessRule.messages.testData')">
            <el-input
              v-model="testData"
              type="textarea"
              :rows="8"
              :placeholder="$t('system.businessRule.messages.testDataPlaceholder')"
            />
          </el-form-item>
        </el-form>

        <div
          v-if="testResult"
          class="test-result"
        >
          <el-divider content-position="left">
            {{ $t('system.businessRule.messages.testResult') }}
          </el-divider>
          <el-alert
            :title="testResult.is_valid ? $t('system.businessRule.messages.testPassed') : $t('system.businessRule.messages.testFailed')"
            :type="testResult.is_valid ? 'success' : 'error'"
            show-icon
            :closable="false"
          />
          <pre class="result-json">{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="testDialogVisible = false">
          {{ $t('common.actions.close') }}
        </el-button>
        <el-button
          type="primary"
          :loading="testing"
          @click="runTest"
        >
          {{ $t('common.actions.test') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import RuleDesigner from '@/components/designer/RuleDesigner.vue'
import { dynamicApi } from '@/api/dynamic'
import { useBusinessRulesApi } from '@/api/businessRules'
import { resolveObjectDisplayName } from '@/utils/objectDisplay'

type RuleType = 'all' | 'validation' | 'visibility' | 'computed' | 'linkage' | 'trigger'

const route = useRoute()
const { t, te } = useI18n()
const { getRulesByObject, deleteRule, updateRule, evaluateRule } = useBusinessRulesApi()

const objectCode = ref<string>(String(route.query.objectCode || route.query.code || 'Asset'))
const objectName = ref<string>(String(route.query.objectName || ''))
const objectDisplayName = computed(() => {
  return resolveObjectDisplayName(
    objectCode.value,
    objectName.value,
    t as (key: string) => string,
    te
  )
})
const activeType = ref<RuleType>('all')
const loading = ref(false)
const rules = ref<any[]>([])

const designerVisible = ref(false)
const currentRule = ref<any | null>(null)

const testDialogVisible = ref(false)
const testData = ref('{}')
const testResult = ref<any | null>(null)
const testing = ref(false)

const fields = ref<Array<{ code: string; name: string; type: string }>>([])

const filteredRules = computed(() => {
  const list = rules.value || []
  if (activeType.value === 'all') return list
  return list.filter((r) => r?.rule_type === activeType.value)
})

const emptyDescription = computed(() => {
  return t('system.businessRule.empty') || '暂无规则'
})

const getRuleTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    validation: 'Validation',
    visibility: 'Visibility',
    computed: 'Computed',
    linkage: 'Linkage',
    trigger: 'Trigger'
  }
  return map[type] || type
}

const getRuleTypeStyle = (type: string) => {
  const map: Record<string, any> = {
    validation: 'warning',
    visibility: 'info',
    computed: 'success',
    linkage: 'primary',
    trigger: 'danger'
  }
  return map[type] || 'info'
}

const loadFields = async () => {
  try {
    const rt = await dynamicApi.getRuntime(objectCode.value, 'edit')
    const raw = rt?.fields?.editableFields || []
    fields.value = raw.map((f: any) => ({
      code: f.code,
      name: f.name,
      type: f.fieldType || 'text'
    }))
  } catch {
    fields.value = []
  }
}

const loadRules = async () => {
  loading.value = true
  try {
    rules.value = await getRulesByObject(objectCode.value)
  } catch (err: any) {
    if (!err?.isHandled) ElMessage.error(err?.message || 'Failed to load rules')
    rules.value = []
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentRule.value = null
  designerVisible.value = true
}

const handleEdit = (row: any) => {
  currentRule.value = row || null
  designerVisible.value = true
}

const handleRuleSaved = () => {
  designerVisible.value = false
  loadRules()
}

const handleDelete = async (row: any) => {
  try {
    await deleteRule(String(row?.id))
    ElMessage.success('Deleted')
    await loadRules()
  } catch (err: any) {
    if (!err?.isHandled) ElMessage.error(err?.message || 'Delete failed')
  }
}

const handleToggleActive = async (row: any, val: any) => {
  try {
    await updateRule(String(row?.id), { is_active: !!val })
    row.is_active = !!val
  } catch (err: any) {
    if (!err?.isHandled) ElMessage.error(err?.message || 'Update failed')
  }
}

const handleTest = (row: any) => {
  currentRule.value = row || null
  testResult.value = null
  testData.value = '{}'
  testDialogVisible.value = true
}

const runTest = async () => {
  testing.value = true
  try {
    const payload = JSON.parse(testData.value || '{}')
    testResult.value = await evaluateRule(objectCode.value, { record: payload, event: 'update' })
  } catch (err: any) {
    if (err instanceof SyntaxError) {
      ElMessage.error('Invalid JSON')
    } else if (!err?.isHandled) {
      ElMessage.error(err?.message || 'Test failed')
    }
  } finally {
    testing.value = false
  }
}

watch(
  () => [route.query.objectCode, route.query.code, route.query.objectName],
  ([objectCodeQuery, codeQuery, objectNameQuery]) => {
    const next = String(objectCodeQuery || codeQuery || 'Asset')
    if (next && next !== objectCode.value) objectCode.value = next
    objectName.value = String(objectNameQuery || objectName.value || '')
  }
)

watch(
  () => objectCode.value,
  async () => {
    await Promise.all([loadFields(), loadRules()])
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.rule-tabs {
  margin-bottom: 16px;
}

.rule-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}

.rules-table {
  border-radius: 8px;
}

.rule-code {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
}

.rule-name-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.rule-desc {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.designer-dialog :deep(.el-dialog__body) {
  padding: 0;
  height: calc(90vh - 100px);
  overflow: hidden;
}

.test-content {
  min-height: 200px;
}

.rule-info {
  margin-bottom: 16px;
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
