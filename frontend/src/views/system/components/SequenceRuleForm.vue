<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? 'Edit Sequence Rule' : 'Create Sequence Rule'"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
    >
      <el-form-item
        label="Rule Code"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          placeholder="e.g., ASSET_CODE, ORDER_NO"
          :disabled="isEdit"
        />
        <div class="form-tip">
          Unique identifier for the sequence rule (uppercase)
        </div>
      </el-form-item>

      <el-form-item
        label="Rule Name"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          placeholder="e.g., Asset Code, Order Number"
        />
      </el-form-item>

      <el-form-item
        label="Prefix"
        prop="prefix"
      >
        <el-input
          v-model="formData.prefix"
          placeholder="e.g., AST, ORD-"
          style="width: 200px"
        />
        <div class="form-tip">
          Fixed prefix for generated numbers
        </div>
      </el-form-item>

      <el-form-item
        label="Sequence Length"
        prop="seq_length"
      >
        <el-input-number
          v-model="formData.seq_length"
          :min="1"
          :max="10"
          style="width: 150px"
        />
        <div class="form-tip">
          Number of digits for the sequence part
        </div>
      </el-form-item>

      <el-form-item
        label="Current Value"
        prop="current_value"
      >
        <el-input-number
          v-model="formData.current_value"
          :min="0"
          style="width: 150px"
        />
        <div class="form-tip">
          Starting value for the sequence
        </div>
      </el-form-item>

      <el-form-item
        label="Reset Period"
        prop="reset_period"
      >
        <el-select
          v-model="formData.reset_period"
          placeholder="Select reset period"
          style="width: 200px"
        >
          <el-option
            label="Never"
            value="never"
          />
          <el-option
            label="Yearly"
            value="yearly"
          />
          <el-option
            label="Monthly"
            value="monthly"
          />
          <el-option
            label="Daily"
            value="daily"
          />
        </el-select>
        <div class="form-tip">
          When to reset the counter to 0
        </div>
      </el-form-item>

      <el-form-item label="Pattern Preview">
        <el-tag type="info">
          {{ patternPreview }}
        </el-tag>
        <div class="form-tip">
          Example: {{ patternExample }}
        </div>
      </el-form-item>

      <el-form-item
        label="Description"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="Describe what this sequence is used for"
        />
      </el-form-item>

      <el-form-item
        label="Active"
        prop="is_active"
      >
        <el-switch
          v-model="formData.is_active"
          active-text="Active"
          inactive-text="Inactive"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        Cancel
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? 'Save' : 'Create' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { SequenceRule } from '@/api/system'
import { sequenceRuleApi } from '@/api/system'

interface Props {
  visible: boolean
  data?: SequenceRule | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  code: '',
  name: '',
  prefix: '',
  pattern: '',
  seq_length: 4,
  current_value: 1,
  reset_period: 'never' as 'never' | 'yearly' | 'monthly' | 'daily',
  description: '',
  is_active: true
})

const rules: FormRules = {
  code: [
    { required: true, message: 'Please enter rule code', trigger: 'blur' },
    {
      pattern: /^[A-Z_][A-Z0-9_]*$/,
      message: 'Code must be uppercase letters, numbers, and underscores only',
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: 'Please enter rule name', trigger: 'blur' }
  ],
  seq_length: [
    { required: true, message: 'Please enter sequence length', trigger: 'blur' }
  ],
  current_value: [
    { required: true, message: 'Please enter current value', trigger: 'blur' }
  ],
  reset_period: [
    { required: true, message: 'Please select reset period', trigger: 'change' }
  ]
}

const patternPreview = computed(() => {
  const prefix = formData.value.prefix || ''
  const seqLen = formData.value.seq_length || 4
  const hash = '#'.repeat(seqLen)
  return `${prefix}${hash}`
})

const patternExample = computed(() => {
  const prefix = formData.value.prefix || ''
  const seqLen = formData.value.seq_length || 4
  const num = String(formData.value.current_value || 1).padStart(seqLen, '0')
  return `${prefix}${num}`
})

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, {
      code: props.data.code || '',
      name: props.data.name || '',
      prefix: props.data.prefix || '',
      pattern: props.data.pattern || '',
      seq_length: props.data.seq_length || 4,
      current_value: props.data.current_value || 1,
      reset_period: props.data.reset_period || 'never',
      description: props.data.description || '',
      is_active: props.data.is_active ?? true
    })
  } else if (val) {
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
    code: '',
    name: '',
    prefix: '',
    pattern: '',
    seq_length: 4,
    current_value: 1,
    reset_period: 'never',
    description: '',
    is_active: true
  }
  formRef.value?.clearValidate()
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      // Auto-generate pattern from prefix and seq_length
      const formDataWithPattern = {
        ...formData.value,
        pattern: `${formData.value.prefix}{${formData.value.seq_length}}`
      }

      if (isEdit.value) {
        await sequenceRuleApi.update(props.data!.id, formDataWithPattern)
      } else {
        await sequenceRuleApi.create(formDataWithPattern)
      }
      ElMessage.success(isEdit.value ? 'Updated successfully' : 'Created successfully')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('Operation failed')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
