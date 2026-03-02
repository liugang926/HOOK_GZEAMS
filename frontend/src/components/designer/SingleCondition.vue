<!--
  SingleCondition.vue - Single condition row
  Field selector, operator, and value input
-->

<template>
  <div class="single-condition">
    <el-select
      :model-value="fieldCode"
      placeholder="选择字段"
      size="small"
      class="field-select"
      filterable
      @update:model-value="updateField"
    >
      <el-option
        v-for="field in fields"
        :key="field.code"
        :label="field.name"
        :value="field.code"
      >
        <span>{{ field.name }}</span>
        <span class="field-code">{{ field.code }}</span>
      </el-option>
    </el-select>

    <el-select
      :model-value="operator"
      placeholder="运算符"
      size="small"
      class="operator-select"
      @update:model-value="updateOperator"
    >
      <el-option
        v-for="op in filteredOperators"
        :key="op.value"
        :label="op.label"
        :value="op.value"
      />
    </el-select>

    <template v-if="!isUnaryOperator">
      <el-input
        v-if="fieldType === 'string'"
        :model-value="value"
        placeholder="输入值"
        size="small"
        class="value-input"
        @update:model-value="updateValue"
      />
      <el-input-number
        v-else-if="fieldType === 'number'"
        :model-value="value"
        size="small"
        class="value-input"
        @update:model-value="updateValue"
      />
      <el-date-picker
        v-else-if="fieldType === 'date'"
        :model-value="value"
        type="date"
        placeholder="选择日期"
        size="small"
        class="value-input"
        @update:model-value="updateValue"
      />
      <el-select
        v-else-if="fieldType === 'boolean'"
        :model-value="value"
        size="small"
        class="value-input"
        @update:model-value="updateValue"
      >
        <el-option
          :value="true"
          label="是"
        />
        <el-option
          :value="false"
          label="否"
        />
      </el-select>
      <el-input
        v-else
        :model-value="value"
        placeholder="输入值"
        size="small"
        class="value-input"
        @update:model-value="updateValue"
      />
    </template>

    <el-button
      type="danger"
      text
      size="small"
      class="remove-btn"
      @click="$emit('remove')"
    >
      <el-icon><Delete /></el-icon>
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete } from '@element-plus/icons-vue'

interface FieldOption {
  code: string
  name: string
  type: string
}

interface Operator {
  value: string
  label: string
  types: string[]
}

interface Props {
  condition: Record<string, unknown>
  fields: FieldOption[]
  operators: Operator[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  update: [value: Record<string, unknown>]
  remove: []
}>()

const operator = computed(() => {
  const keys = Object.keys(props.condition || {})
  return keys.find((k) => !['var'].includes(k)) || '=='
})

const conditionArgs = computed<unknown[]>(() => {
  const raw = props.condition?.[operator.value] as unknown
  if (Array.isArray(raw)) return raw
  if (raw && typeof raw === 'object' && 'var' in (raw as Record<string, unknown>)) return [raw]
  return []
})

const fieldCode = computed(() => {
  const firstArg = conditionArgs.value[0]
  if (typeof firstArg === 'object' && firstArg?.var !== undefined) {
    return firstArg.var
  }
  return ''
})

const value = computed(() => conditionArgs.value[1])

const selectedField = computed(() => props.fields.find((f) => f.code === fieldCode.value))

const fieldType = computed(() => selectedField.value?.type || 'string')

const isUnaryOperator = computed(() => ['!', '!!'].includes(operator.value))

const filteredOperators = computed(() => {
  const type = fieldType.value
  return props.operators.filter((op) => op.types.includes('all') || op.types.includes(type))
})

function updateField(code: string) {
  if (isUnaryOperator.value) {
    emit('update', {
      [operator.value]: { var: code }
    })
    return
  }
  emit('update', {
    [operator.value]: [{ var: code }, value.value]
  })
}

function updateOperator(op: string) {
  if (['!', '!!'].includes(op)) {
    emit('update', {
      [op]: { var: fieldCode.value }
    })
    return
  }

  emit('update', {
    [op]: [{ var: fieldCode.value }, value.value ?? '']
  })
}

function updateValue(val: unknown) {
  emit('update', {
    [operator.value]: [{ var: fieldCode.value }, val]
  })
}
</script>

<style scoped>
.single-condition {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 6px;
}

.field-select {
  width: 160px;
}

.operator-select {
  width: 100px;
}

.value-input {
  flex: 1;
  min-width: 120px;
}

.remove-btn {
  flex-shrink: 0;
}

.field-code {
  float: right;
  font-size: 11px;
  color: var(--el-text-color-secondary);
  font-family: monospace;
}
</style>
