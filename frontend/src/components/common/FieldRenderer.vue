<template>
  <div
    class="field-renderer"
    :class="[`mode-${mode}`, `type-${field.type}`]"
  >
    <!-- WRITE MODE -->
    <template v-if="mode === 'write'">
      <!-- Input -->
      <el-input
        v-if="['text', 'string', 'email', 'phone'].includes(field.type)"
        :model-value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        clearable
        @update:model-value="handleChange"
      />

      <!-- Textarea -->
      <el-input
        v-else-if="field.type === 'textarea'"
        :model-value="modelValue"
        type="textarea"
        :rows="field.rows || 3"
        :placeholder="placeholder"
        :disabled="disabled"
        @update:model-value="handleChange"
      />

      <!-- Number -->
      <el-input-number
        v-else-if="['number', 'integer', 'float'].includes(field.type)"
        :model-value="modelValue"
        :disabled="disabled"
        class="full-width"
        controls-position="right"
        @update:model-value="handleChange"
      />

      <!-- Select / Enum -->
      <el-select
        v-else-if="['select', 'enum', 'status'].includes(field.type)"
        :model-value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        clearable
        class="full-width"
        @update:model-value="handleChange"
      >
        <el-option
          v-for="opt in options"
          :key="opt.value"
          :label="opt.label"
          :value="opt.value"
        />
      </el-select>

      <!-- Date -->
      <el-date-picker
        v-else-if="['date', 'datetime'].includes(field.type)"
        :model-value="modelValue"
        :type="field.type === 'datetime' ? 'datetime' : 'date'"
        :placeholder="placeholder"
        :disabled="disabled"
        class="full-width"
        value-format="YYYY-MM-DD"
        @update:model-value="handleChange"
      />

      <!-- Progress -->
      <el-input-number
        v-else-if="field.type === 'progress'"
        :model-value="modelValue"
        :min="0"
        :max="100"
        :disabled="disabled"
        class="full-width"
        @update:model-value="handleChange"
      />

      <!-- Reference -->
      <el-input
        v-else-if="field.type === 'reference'"
        :model-value="modelValue?.name || modelValue"
        readonly
        placeholder="Click to select..."
        :disabled="disabled"
      >
        <template #append>
          <el-button :icon="Search" />
        </template>
      </el-input>

      <!-- Formula (Readonly) -->
      <el-input
        v-else-if="field.type === 'formula'"
        :model-value="modelValue"
        readonly
        disabled
      />

      <!-- File (Simple URL input for now) -->
      <el-input
        v-else-if="field.type === 'file'"
        :model-value="modelValue"
        placeholder="File URL"
        :disabled="disabled"
        @update:model-value="handleChange"
      />

      <!-- Fallback -->
      <span
        v-else
        class="text-gray-400"
      >Unsupported type: {{ field.type }}</span>
    </template>

    <!-- READ / TABLE MODE -->
    <template v-else>
      <!-- Status / Enum (Tag) -->
      <template v-if="['status', 'enum'].includes(field.type)">
        <el-tag
          :type="getStatusType(modelValue)"
          size="small"
          effect="plain"
        >
          {{ getStatusLabel(modelValue) }}
        </el-tag>
      </template>

      <!-- Date -->
      <template v-else-if="['date', 'datetime'].includes(field.type)">
        <span class="text-sm font-mono text-gray-600">
          {{ formatDateDisplay(modelValue) }}
        </span>
      </template>

      <!-- User -->
      <template v-else-if="field.type === 'user'">
        <div class="flex items-center gap-2">
          <el-avatar
            :size="24"
            :src="getUserAvatar(modelValue)"
          >
            {{ getUserInitials(modelValue) }}
          </el-avatar>
          <span class="text-sm">{{ getUserName(modelValue) }}</span>
        </div>
      </template>

      <!-- Currency -->
      <template v-else-if="field.type === 'currency'">
        <span class="font-mono">{{ formatCurrency(modelValue) }}</span>
      </template>

      <!-- Boolean -->
      <template v-else-if="field.type === 'boolean'">
        <el-icon
          v-if="modelValue"
          color="#67C23A"
        >
          <Check />
        </el-icon>
        <el-icon
          v-else
          color="#F56C6C"
        >
          <Close />
        </el-icon>
      </template>

      <!-- Progress -->
      <el-progress
        v-else-if="field.type === 'progress'"
        :percentage="Number(modelValue || 0)"
        :status="Number(modelValue) === 100 ? 'success' : ''"
      />

      <!-- File -->
      <template v-else-if="field.type === 'file'">
        <a
          v-if="modelValue"
          :href="modelValue"
          target="_blank"
          class="flex items-center gap-1 text-blue-500 hover:text-blue-700"
        >
          <el-icon><Document /></el-icon>
          <span>Download</span>
        </a>
        <span v-else>-</span>
      </template>

      <!-- Reference -->
      <template v-else-if="field.type === 'reference'">
        <router-link 
          v-if="modelValue && field.referenceRoute" 
          :to="{ name: field.referenceRoute, params: { id: modelValue.id || modelValue } }"
          class="text-blue-500 hover:underline"
        >
          {{ modelValue.name || modelValue.label || modelValue }}
        </router-link>
        <span v-else>{{ modelValue?.name || modelValue || '-' }}</span>
      </template>

      <!-- Formula -->
      <span
        v-else-if="field.type === 'formula'"
        class="font-mono text-gray-600 bg-gray-50 px-1 rounded"
      >
        {{ modelValue || '-' }}
      </span>

      <!-- Default Text -->
      <span
        v-else
        class="text-sm truncate block"
        :title="String(modelValue || '')"
      >
        {{ modelValue || '-' }}
      </span>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Check, Close, Document, Search } from '@element-plus/icons-vue'
import dayjs from 'dayjs'

interface FieldConfig {
  prop: string
  label: string
  type: string // text, number, date, status, user, etc.
  options?: { label: string; value: any; color?: string }[]
  [key: string]: any
}

interface Props {
  field: FieldConfig
  modelValue?: any
  mode?: 'read' | 'write' | 'table'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'read',
  disabled: false
})

const emit = defineEmits(['update:modelValue', 'change'])

const placeholder = computed(() => `Please enter ${props.field.label}`)

const options = computed(() => props.field.options || [])

const handleChange = (val: any) => {
  emit('update:modelValue', val)
  emit('change', val)
}

// --- Helpers ---

const getStatusLabel = (val: any) => {
  const opt = options.value.find(o => o.value === val)
  return opt ? opt.label : val
}

const getStatusType = (val: any) => {
  // Simple mapping or use config
  const opt = options.value.find(o => o.value === val)
  if (opt?.color) return opt.color // If specialized
  
  const map: Record<string, string> = {
    active: 'success',
    enabled: 'success',
    draft: 'info',
    pending: 'warning',
    rejected: 'danger',
    deleted: 'danger'
  }
  return map[String(val).toLowerCase()] || ''
}

const formatDateDisplay = (val: any) => {
  if (!val) return '-'
  return dayjs(val).format('YYYY-MM-DD')
}

const formatCurrency = (val: any) => {
  if (val === null || val === undefined) return '-'
  return `¥${Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}

// Mock User helpers - in real app, fetch from store or input object
const getUserName = (val: any) => typeof val === 'object' ? (val.name || val.username) : val
const getUserAvatar = (val: any) => typeof val === 'object' ? val.avatar : ''
const getUserInitials = (val: any) => {
  const name = getUserName(val)
  return name ? String(name).substring(0, 1).toUpperCase() : 'U'
}
</script>

<style scoped>
.field-renderer {
  @apply w-full;
}
.full-width {
  @apply w-full;
}
</style>
