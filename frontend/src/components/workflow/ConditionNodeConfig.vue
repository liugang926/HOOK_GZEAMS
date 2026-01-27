<template>
  <div class="condition-config">
    <el-form
      :model="localValue"
      label-width="80px"
      size="small"
    >
      <el-form-item label="条件分支">
        <div class="condition-branches">
          <div
            v-for="(branch, index) in localValue.branches"
            :key="index"
            class="condition-branch"
          >
            <div class="branch-header">
              <span class="branch-label">分支 {{ index + 1 }}</span>
              <el-button
                v-if="localValue.branches.length > 1"
                :icon="Delete"
                circle
                size="small"
                type="danger"
                @click="removeBranch(index)"
              />
            </div>

            <el-form-item label="条件">
              <el-select
                v-model="branch.field"
                placeholder="选择字段"
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

            <el-form-item label="运算符">
              <el-select
                v-model="branch.operator"
                style="width: 100%"
              >
                <el-option
                  label="等于"
                  value="eq"
                />
                <el-option
                  label="不等于"
                  value="ne"
                />
                <el-option
                  label="大于"
                  value="gt"
                />
                <el-option
                  label="大于等于"
                  value="gte"
                />
                <el-option
                  label="小于"
                  value="lt"
                />
                <el-option
                  label="小于等于"
                  value="lte"
                />
                <el-option
                  label="包含"
                  value="contains"
                />
                <el-option
                  label="不包含"
                  value="not_contains"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="值">
              <el-input
                v-model="branch.value"
                placeholder="条件值"
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
          添加分支
        </el-button>
      </el-form-item>

      <el-form-item label="默认分支">
        <el-select
          v-model="localValue.defaultFlow"
          placeholder="条件不满足时的去向"
          style="width: 100%"
        >
          <el-option
            label="拒绝"
            value="reject"
          />
          <el-option
            label="通过"
            value="approve"
          />
        </el-select>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'

interface Props {
  modelValue: Record<string, any>
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
}

const props = defineProps<Props>()
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

// 可用字段（从业务对象获取）
const availableFields = ref([
  { code: 'amount', name: '金额' },
  { code: 'department', name: '部门' },
  { code: 'applicant', name: '申请人' }
])

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
