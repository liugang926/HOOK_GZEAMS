<!--
  ConditionGroup.vue - Recursive condition group component
  Handles AND/OR groups and individual conditions
-->

<template>
  <div
    class="condition-group"
    :class="{ 'is-nested': depth > 0 }"
  >
    <!-- Group Logic Toggle (AND/OR) -->
    <div
      v-if="isGroup"
      class="group-logic"
    >
      <el-radio-group
        :model-value="groupLogic"
        size="small"
        @update:model-value="toggleLogic"
      >
        <el-radio-button value="and">
          {{ t('form.actions.logicAnd') }}
        </el-radio-button>
        <el-radio-button value="or">
          {{ t('form.actions.logicOr') }}
        </el-radio-button>
      </el-radio-group>
      <el-button
        v-if="depth > 0"
        type="danger"
        text
        size="small"
        @click="$emit('remove')"
      >
        <el-icon><Delete /></el-icon>
        {{ t('form.actions.removeGroup') }}
      </el-button>
    </div>

    <!-- Conditions List -->
    <div class="conditions-list">
      <template v-if="isGroup">
        <div
          v-for="(item, index) in groupItems"
          :key="index"
          class="condition-item"
        >
          <!-- Nested Group -->
          <ConditionGroup
            v-if="isSubGroup(item)"
            :model-value="item"
            :fields="fields"
            :operators="operators"
            :depth="depth + 1"
            @update:model-value="updateItem(index, $event)"
            @remove="removeItem(index)"
          />

          <!-- Single Condition -->
          <SingleCondition
            v-else
            :condition="item"
            :fields="fields"
            :operators="operators"
            @update="updateItem(index, $event)"
            @remove="removeItem(index)"
          />
        </div>
      </template>

      <!-- Root Single Condition -->
      <SingleCondition
        v-else
        :condition="modelValue"
        :fields="fields"
        :operators="operators"
        @update="$emit('update:modelValue', $event)"
        @remove="$emit('remove')"
      />
    </div>

    <!-- Add within group -->
    <div
      v-if="isGroup && depth > 0"
      class="group-actions"
    >
      <el-button
        size="small"
        text
        type="primary"
        @click="addConditionToGroup"
      >
        <el-icon><Plus /></el-icon>
        {{ t('form.actions.addCondition') }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Delete, Plus } from '@element-plus/icons-vue'
import SingleCondition from './SingleCondition.vue'

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
  modelValue: Record<string, any>
  fields: FieldOption[]
  operators: Operator[]
  depth: number
}

const props = defineProps<Props>()
const { t } = useI18n()

const emit = defineEmits<{
  'update:modelValue': [value: Record<string, any>]
  remove: []
}>()

// Check if this is a group (AND/OR)
const isGroup = computed(() => {
  return props.modelValue?.and || props.modelValue?.or
})

const groupLogic = computed(() => {
  return props.modelValue?.and ? 'and' : props.modelValue?.or ? 'or' : null
})

const groupItems = computed(() => {
  return props.modelValue?.and || props.modelValue?.or || []
})

function isSubGroup(item: Record<string, any>): boolean {
  return !!item.and || !!item.or
}

function toggleLogic(logic: 'and' | 'or') {
  const currentLogic = groupLogic.value
  if (currentLogic === logic) return

  const items = groupItems.value
  emit('update:modelValue', { [logic]: items })
}

function updateItem(index: number, value: Record<string, any>) {
  const logic = groupLogic.value
  if (!logic) return

  const newItems = [...groupItems.value]
  newItems[index] = value
  emit('update:modelValue', { [logic]: newItems })
}

function removeItem(index: number) {
  const logic = groupLogic.value
  if (!logic) return

  const newItems = groupItems.value.filter((_: any, i: number) => i !== index)
  
  if (newItems.length === 0) {
    emit('remove')
  } else if (newItems.length === 1 && props.depth > 0) {
    // Unwrap single item
    emit('update:modelValue', newItems[0])
  } else {
    emit('update:modelValue', { [logic]: newItems })
  }
}

function addConditionToGroup() {
  const logic = groupLogic.value
  if (!logic) return

  const newCondition = { '==': [{ var: '' }, ''] }
  emit('update:modelValue', {
    [logic]: [...groupItems.value, newCondition]
  })
}
</script>

<style scoped>
.condition-group {
  padding: 12px;
}

.condition-group.is-nested {
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  margin-bottom: 8px;
}

.group-logic {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.condition-item {
  position: relative;
}

.group-actions {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--el-border-color-lighter);
}
</style>
