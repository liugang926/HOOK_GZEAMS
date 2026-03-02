<!--
  ConditionBuilder.vue - Visual JSON Logic condition builder
  Allows users to build complex conditions without writing JSON
-->

<template>
  <div class="condition-builder">
    <div class="builder-header">
      <span class="header-title">{{ title }}</span>
      <el-tag
        type="info"
        size="small"
      >
        {{ conditionCount }} 条件
      </el-tag>
    </div>

    <!-- Empty State -->
    <div
      v-if="!hasConditions"
      class="empty-condition"
    >
      <el-icon class="empty-icon">
        <Filter />
      </el-icon>
      <p>暂无条件</p>
      <el-button
        type="primary"
        size="small"
        @click="addCondition"
      >
        <el-icon><Plus /></el-icon>
        添加条件组
      </el-button>
    </div>

    <!-- Condition Groups -->
    <div
      v-else
      class="condition-groups"
    >
      <!-- Root Group -->
      <ConditionGroup
        v-model="conditionModel"
        :fields="fields"
        :operators="operators"
        :depth="0"
        @remove="removeRootCondition"
      />

      <div class="builder-actions">
        <el-button
          size="small"
          @click="addCondition"
        >
          <el-icon><Plus /></el-icon>
          添加条件组
        </el-button>
        <el-button
          size="small"
          @click="addGroup"
        >
          <el-icon><FolderAdd /></el-icon>
          添加条件组
        </el-button>
      </div>
    </div>

    <!-- JSON Preview (collapsible) -->
    <el-collapse
      v-model="showPreview"
      class="json-preview"
    >
      <el-collapse-item
        title="查看 JSON"
        name="preview"
      >
        <pre class="json-code">{{ formattedJson }}</pre>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Filter, Plus, FolderAdd } from '@element-plus/icons-vue'
import ConditionGroup from './ConditionGroup.vue'

interface FieldOption {
  code: string
  name: string
  type: string
}

interface Props {
  modelValue: Record<string, any>
  fields: FieldOption[]
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '条件配置'
})

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
}>()

// Internal model
const conditionModel = computed({
  get: () => props.modelValue || {},
  set: (val) => emit('update:modelValue', val)
})

// State
const showPreview = ref<string[]>([])

// Operators available for conditions
const operators = [
  { value: '==', label: '等于', types: ['all'] },
  { value: '!=', label: '不等于', types: ['all'] },
  { value: '>', label: '大于', types: ['number', 'date'] },
  { value: '>=', label: '大于等于', types: ['number', 'date'] },
  { value: '<', label: '小于', types: ['number', 'date'] },
  { value: '<=', label: '小于等于', types: ['number', 'date'] },
  { value: 'in', label: '包含于', types: ['all'] },
  { value: '!', label: '为空', types: ['all'] },
  { value: '!!', label: '不为空', types: ['all'] },
  { value: 'startsWith', label: '开头是', types: ['string'] },
  { value: 'endsWith', label: '结尾是', types: ['string'] },
]

// Computed
const hasConditions = computed(() => {
  return Object.keys(props.modelValue || {}).length > 0
})

const conditionCount = computed(() => {
  return countConditions(props.modelValue || {})
})

const formattedJson = computed(() => {
  return JSON.stringify(props.modelValue || {}, null, 2)
})

// Helper to count conditions
function countConditions(obj: Record<string, any>): number {
  if (!obj || typeof obj !== 'object') return 0
  
  let count = 0
  for (const key in obj) {
    if (['and', 'or'].includes(key)) {
      count += (obj[key] as any[]).reduce((sum, item) => sum + countConditions(item), 0)
    } else if (key !== 'var') {
      count += 1
    }
  }
  return count
}

// Actions
function addCondition() {
  const newCondition = {
    '==': [{ var: '' }, '']
  }
  
  if (!hasConditions.value) {
    emit('update:modelValue', newCondition)
  } else if (props.modelValue.and) {
    emit('update:modelValue', {
      and: [...props.modelValue.and, newCondition]
    })
  } else if (props.modelValue.or) {
    emit('update:modelValue', {
      or: [...props.modelValue.or, newCondition]
    })
  } else {
    // Wrap existing in AND
    emit('update:modelValue', {
      and: [props.modelValue, newCondition]
    })
  }
}

function addGroup() {
  const newGroup = {
    and: [{ '==': [{ var: '' }, ''] }]
  }
  
  if (!hasConditions.value) {
    emit('update:modelValue', newGroup)
  } else if (props.modelValue.and) {
    emit('update:modelValue', {
      and: [...props.modelValue.and, newGroup]
    })
  } else if (props.modelValue.or) {
    emit('update:modelValue', {
      or: [...props.modelValue.or, newGroup]
    })
  } else {
    emit('update:modelValue', {
      and: [props.modelValue, newGroup]
    })
  }
}

function removeRootCondition() {
  emit('update:modelValue', {})
}
</script>

<style scoped>
.condition-builder {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  background: var(--el-bg-color);
}

.builder-header {
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

.empty-condition {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.3;
}

.empty-condition p {
  margin: 0 0 16px 0;
}

.condition-groups {
  padding: 16px;
}

.builder-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--el-border-color-lighter);
}

.json-preview {
  border-top: 1px solid var(--el-border-color-lighter);
}

.json-preview :deep(.el-collapse-item__header) {
  padding: 0 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.json-code {
  margin: 0;
  padding: 12px;
  background: var(--el-fill-color);
  border-radius: 4px;
  font-size: 11px;
  font-family: 'Monaco', 'Menlo', monospace;
  overflow-x: auto;
  max-height: 200px;
}
</style>
