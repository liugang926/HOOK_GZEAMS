<template>
  <el-dialog
    :title="id ? t('consumables.form.titleEdit') : t('consumables.form.titleCreate')"
    :model-value="modelValue"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="90px"
    >
      <el-form-item
        :label="t('consumables.form.fields.name')"
        prop="name"
      >
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item
        :label="t('consumables.form.fields.code')"
        prop="code"
      >
        <el-input v-model="form.code" />
      </el-form-item>
      <el-form-item
        :label="t('consumables.form.fields.category')"
        prop="category"
      >
        <el-select
          v-model="form.category"
          style="width: 100%"
        >
          <el-option
            :label="t('consumables.form.category.office')"
            value="office"
          />
          <el-option
            :label="t('consumables.form.category.it')"
            value="it"
          />
        </el-select>
      </el-form-item>
      <el-form-item
        :label="t('consumables.form.fields.spec')"
        prop="spec"
      >
        <el-input v-model="form.spec" />
      </el-form-item>
      <el-form-item
        :label="t('consumables.form.fields.unit')"
        prop="unit"
      >
        <el-input v-model="form.unit" />
      </el-form-item>
      <el-form-item
        :label="t('consumables.form.fields.warningQuantity')"
        prop="warning_quantity"
      >
        <el-input-number
          v-model="form.warning_quantity"
          :min="0"
        />
      </el-form-item>
      <el-form-item
        :label="t('consumables.form.fields.description')"
        prop="description"
      >
        <el-input
          v-model="form.description"
          type="textarea"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">
        {{ t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="submit"
      >
        {{ t('common.actions.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, defineProps, defineEmits } from 'vue'
import { useI18n } from 'vue-i18n'
import { createConsumable, updateConsumable, getConsumable } from '@/api/consumables'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean,
  id: [Number, String]
})
const emit = defineEmits(['update:modelValue', 'success'])
const { t } = useI18n()

const formRef = ref()
const submitting = ref(false)
const form = reactive({
  name: '',
  code: '',
  category: 'office',
  spec: '',
  unit: 'pcs',
  warning_quantity: 10,
  description: ''
})

const resetFormData = () => {
  Object.assign(form, {
    name: '',
    code: '',
    category: 'office',
    spec: '',
    unit: 'pcs',
    warning_quantity: 10,
    description: ''
  })
}

const rules = {
  name: [{ required: true, message: t('common.validation.requiredWithField', { field: t('consumables.form.fields.name') }), trigger: 'blur' }],
  code: [{ required: true, message: t('common.validation.requiredWithField', { field: t('consumables.form.fields.code') }), trigger: 'blur' }],
  unit: [{ required: true, message: t('common.validation.requiredWithField', { field: t('consumables.form.fields.unit') }), trigger: 'blur' }]
}

watch(
  () => props.modelValue,
  async (val) => {
    if (!val) return

    if (props.id) {
      try {
        const res = await getConsumable(props.id)
        Object.assign(form, res)
      } catch (e) {
        console.error(e)
      }
    } else {
      resetFormData()
    }
  }
)

const handleClose = () => {
  emit('update:modelValue', false)
}

const submit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (props.id) {
      await updateConsumable(props.id, form)
    } else {
      await createConsumable(form)
    }
    ElMessage.success(t('consumables.form.messages.saveSuccess'))
    emit('success')
    handleClose()
  } catch (e: any) {
    ElMessage.error(e?.message || t('consumables.form.messages.saveFailed'))
    console.error(e)
  } finally {
    submitting.value = false
  }
}
</script>
