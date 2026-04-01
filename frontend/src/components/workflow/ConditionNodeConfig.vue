<template>
  <div class="condition-config">
    <el-form
      :model="localValue"
      :label-width="locale === 'zh-CN' ? '80px' : '120px'"
      size="small"
    >
      <el-form-item :label="t('workflow.designer.conditionBranch')">
        <div class="condition-branches">
          <div
            v-for="(branch, index) in localValue.branches"
            :key="index"
            class="condition-branch"
          >
            <div class="branch-header">
              <span class="branch-label">{{ t('workflow.designer.branch', { index: index + 1 }) }}</span>
              <el-button
                v-if="localValue.branches.length > 1"
                :icon="Delete"
                circle
                size="small"
                type="danger"
                @click="removeBranch(index)"
              />
            </div>

            <el-form-item :label="t('workflow.designer.condition')">
              <el-select
                v-model="branch.field"
                :placeholder="t('workflow.designer.selectField')"
                style="width: 100%"
              >
                <el-option
                  v-for="field in availableFields"
                  :key="field.code"
                  :label="field.name"
                  :value="field.code"
                />
              </el-select>
            </el-form-item>

            <el-form-item :label="t('workflow.designer.operator')">
              <el-select
                v-model="branch.operator"
                style="width: 100%"
              >
                <el-option
                  :label="t('workflow.operators.eq')"
                  value="eq"
                />
                <el-option
                  :label="t('workflow.operators.ne')"
                  value="ne"
                />
                <el-option
                  :label="t('workflow.operators.gt')"
                  value="gt"
                />
                <el-option
                  :label="t('workflow.operators.gte')"
                  value="gte"
                />
                <el-option
                  :label="t('workflow.operators.lt')"
                  value="lt"
                />
                <el-option
                  :label="t('workflow.operators.lte')"
                  value="lte"
                />
                <el-option
                  :label="t('workflow.operators.contains')"
                  value="contains"
                />
                <el-option
                  :label="t('workflow.operators.notContains')"
                  value="not_contains"
                />
              </el-select>
            </el-form-item>

            <el-form-item :label="t('workflow.designer.value')">
              <el-input
                v-model="branch.value"
                :placeholder="t('workflow.designer.conditionValue')"
              />
            </el-form-item>
          </div>
        </div>
      </el-form-item>

      <el-form-item>
        <el-button
          :icon="Plus"
          @click="addBranch"
        >
          {{ t('workflow.designer.addBranch') }}
        </el-button>
      </el-form-item>

      <el-form-item :label="t('workflow.designer.defaultBranch')">
        <el-select
          v-model="localValue.defaultFlow"
          :placeholder="t('workflow.designer.defaultBranchHint')"
          style="width: 100%"
        >
          <el-option
            :label="t('workflow.actions.reject')"
            value="reject"
          />
          <el-option
            :label="t('workflow.actions.approve')"
            value="approve"
          />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { computed, withDefaults } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Delete } from '@element-plus/icons-vue'

const { t } = useI18n()
const locale = computed(() => t('locale'))

interface FieldDef {
  code: string
  name: string
}

interface Props {
  modelValue: Record<string, any>
  /** Field definitions passed down from WorkflowDesigner (real object fields). */
  availableFields?: FieldDef[]
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
}

const props = withDefaults(defineProps<Props>(), {
  availableFields: () => [],
})
const emit = defineEmits<Emits>()

const localValue = computed({
  get: () => props.modelValue || {
    branches: [
      { field: '', operator: 'eq', value: '' }
    ],
    defaultFlow: 'reject'
  },
  set: (val) => emit('update:modelValue', val)
})

// Use fields injected by WorkflowDesigner; fall back to a minimal static list
// when the parent does not yet supply any (e.g. businessObject not selected).
const availableFields = computed<FieldDef[]>(() => {
  if (props.availableFields && props.availableFields.length > 0) {
    return props.availableFields
  }
  return [
    { code: 'amount', name: t('workflow.fields.amount') },
    { code: 'department', name: t('workflow.fields.department') },
    { code: 'applicant', name: t('workflow.fields.applicant') },
  ]
})

const addBranch = () => {
  if (!localValue.value.branches) {
    localValue.value.branches = []
  }
  localValue.value.branches.push({
    field: '',
    operator: 'eq',
    value: ''
  })
  emit('update:modelValue', localValue.value)
}

const removeBranch = (index: number) => {
  localValue.value.branches.splice(index, 1)
  emit('update:modelValue', localValue.value)
}
</script>

<style scoped>
.condition-config {
  padding: 5px 0;
}

.condition-branches {
  width: 100%;
}

.condition-branch {
  padding: 10px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  margin-bottom: 10px;
}

.branch-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.branch-label {
  font-weight: 500;
  color: #606266;
}
</style>
