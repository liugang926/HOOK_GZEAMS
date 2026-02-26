<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('system.sequenceRule.editTitle') : $t('system.sequenceRule.createTitle')"
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
        :label="$t('system.sequenceRule.fields.code')"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          :placeholder="$t('system.sequenceRule.placeholders.code')"
          :disabled="isEdit"
        />
        <div class="form-tip">
          {{ $t('system.sequenceRule.tips.code') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.sequenceRule.fields.name')"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          :placeholder="$t('system.sequenceRule.placeholders.name')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.sequenceRule.fields.prefix')"
        prop="prefix"
      >
        <el-input
          v-model="formData.prefix"
          :placeholder="$t('system.sequenceRule.placeholders.prefix')"
          style="width: 200px"
        />
        <div class="form-tip">
          {{ $t('system.sequenceRule.tips.prefix') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.sequenceRule.fields.seqLength')"
        prop="seq_length"
      >
        <el-input-number
          v-model="formData.seq_length"
          :min="1"
          :max="10"
          style="width: 150px"
        />
        <div class="form-tip">
          {{ $t('system.sequenceRule.tips.seqLength') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.sequenceRule.fields.currentValue')"
        prop="current_value"
      >
        <el-input-number
          v-model="formData.current_value"
          :min="0"
          style="width: 150px"
        />
        <div class="form-tip">
          {{ $t('system.sequenceRule.tips.currentValue') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.sequenceRule.fields.resetPeriod')"
        prop="reset_period"
      >
        <el-select
          v-model="formData.reset_period"
          placeholder="Select reset period"
          style="width: 200px"
        >
          <el-option
            v-for="(label, key) in resetPeriodOptions"
            :key="key"
            :label="label"
            :value="key"
          />
        </el-select>
        <div class="form-tip">
          {{ $t('system.sequenceRule.tips.resetPeriod') }}
        </div>
      </el-form-item>

      <el-form-item :label="$t('system.sequenceRule.fields.pattern')">
        <el-tag type="info">
          {{ patternPreview }}
        </el-tag>
        <div class="form-tip">
          {{ $t('system.sequenceRule.tips.example') }} {{ patternExample }}
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.sequenceRule.fields.description')"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          :placeholder="$t('system.sequenceRule.placeholders.description')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.sequenceRule.fields.active')"
        prop="is_active"
      >
        <el-switch
          v-model="formData.is_active"
          :active-text="$t('common.status.active')"
          :inactive-text="$t('common.status.inactive')"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? $t('common.actions.save') : $t('common.actions.create') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { SequenceRule } from '@/api/system'
import { sequenceRuleApi } from '@/api/system'

const { t } = useI18n()

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

const rules = computed<FormRules>(() => ({
  code: [
    { required: true, message: t('system.fieldDefinition.validation.codeRequired'), trigger: 'blur' },
    {
      pattern: /^[A-Z_][A-Z0-9_]*$/,
      message: t('system.fieldDefinition.validation.codePattern'),
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: t('system.fieldDefinition.validation.nameRequired'), trigger: 'blur' }
  ],
  seq_length: [
    { required: true, message: t('common.validation.required'), trigger: 'blur' }
  ],
  current_value: [
    { required: true, message: t('common.validation.required'), trigger: 'blur' }
  ],
  reset_period: [
    { required: true, message: t('common.validation.required'), trigger: 'change' }
  ]
}))

const resetPeriodOptions = computed(() => ({
  never: t('system.sequenceRule.periods.never'),
  yearly: t('system.sequenceRule.periods.yearly'),
  monthly: t('system.sequenceRule.periods.monthly'),
  daily: t('system.sequenceRule.periods.daily')
}))

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

  await formRef.value.validate(async (valid: boolean) => {
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
      ElMessage.success(isEdit.value ? t('common.messages.updateSuccess') : t('common.messages.createSuccess'))
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error(t('common.messages.operationFailed'))
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
