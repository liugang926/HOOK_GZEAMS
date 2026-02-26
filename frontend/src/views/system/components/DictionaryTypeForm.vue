<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('common.actions.edit') + $t('system.dictionary.type') : $t('common.actions.create') + $t('system.dictionary.type')"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item
        :label="$t('system.dictionary.code')"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          :placeholder="$t('system.dictionary.codePlaceholder')"
          :disabled="isEdit"
        />
        <div class="form-tip">
          {{ $t('system.dictionary.codeTip') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.dictionary.name')"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          :placeholder="$t('system.dictionary.namePlaceholder')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.dictionary.englishName')"
        prop="name_en"
      >
        <el-input
          v-model="formData.name_en"
          :placeholder="$t('system.dictionary.englishNamePlaceholder')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.dictionary.sortOrder')"
        prop="sort_order"
      >
        <el-input-number
          v-model="formData.sort_order"
          :min="0"
          :max="9999"
        />
      </el-form-item>

      <el-form-item
        :label="$t('common.labels.description')"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          :placeholder="$t('system.dictionary.descriptionPlaceholder')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.department.columns.status')"
        prop="is_active"
      >
        <el-switch
          v-model="formData.is_active"
          :active-text="$t('system.dictionary.status.enabled')"
          :inactive-text="$t('system.dictionary.status.disabled')"
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
import type { DictionaryType } from '@/api/system'
import { dictionaryTypeApi } from '@/api/system'

const { t } = useI18n()

interface Props {
  visible: boolean
  data?: DictionaryType | null
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
  name_en: '',
  description: '',
  sort_order: 0,
  is_active: true
})

const rules: FormRules = {
  code: [
    { required: true, message: t('system.dictionary.validation.codeRequired'), trigger: 'blur' },
    { pattern: /^[A-Z_][A-Z0-9_]*$/, message: t('system.dictionary.validation.codePattern'), trigger: 'blur' }
  ],
  name: [{ required: true, message: t('system.dictionary.validation.nameRequired'), trigger: 'blur' }]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, {
      code: props.data.code || '',
      name: props.data.name || '',
      name_en: props.data.name_en || '',
      description: props.data.description || '',
      sort_order: props.data.sort_order || 0,
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
    name_en: '',
    description: '',
    sort_order: 0,
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
      if (isEdit.value) {
        await dictionaryTypeApi.update(props.data!.id, formData.value)
      } else {
        await dictionaryTypeApi.create(formData.value)
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
