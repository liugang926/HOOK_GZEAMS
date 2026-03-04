<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('system.languages.edit') : $t('system.languages.create')"
    width="500px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item
        :label="$t('system.languages.flag')"
        prop="flagEmoji"
      >
        <el-input
          v-model="formData.flagEmoji"
          :placeholder="$t('system.languages.flagPlaceholder')"
          maxlength="10"
        >
          <template #append>
            <span class="flag-preview">{{ formData.flagEmoji }}</span>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item
        :label="$t('system.languages.code')"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          :placeholder="$t('system.languages.codePlaceholder')"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.languages.name')"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          :placeholder="$t('system.languages.namePlaceholder')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.languages.nativeName')"
        prop="nativeName"
      >
        <el-input
          v-model="formData.nativeName"
          :placeholder="$t('system.languages.nativeNamePlaceholder')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.languages.locale')"
        prop="locale"
      >
        <el-input
          v-model="formData.locale"
          :placeholder="$t('system.languages.localePlaceholder')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.languages.sortOrder')"
        prop="sortOrder"
      >
        <el-input-number
          v-model="formData.sortOrder"
          :min="0"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item :label="$t('system.languages.isActive')">
        <el-switch v-model="formData.isActive" />
      </el-form-item>

      <el-form-item
        v-if="!isEdit || !language?.isDefault"
        :label="$t('system.languages.isDefault')"
      >
        <el-switch v-model="formData.isDefault" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-space>
        <el-button @click="handleClose">
          {{ $t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="handleSave"
        >
          {{ $t('common.actions.save') }}
        </el-button>
      </el-space>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { languageApi } from '@/api/translations'
import type { Language } from '@/api/translations'

interface Props {
  visible: boolean
  language?: Language | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<any>()
const saving = ref(false)

// Form data
const formData = reactive<{
  code: string
  name: string
  nativeName: string
  flagEmoji: string
  locale: string
  sortOrder: number
  isActive: boolean
  isDefault: boolean
}>({
  code: '',
  name: '',
  nativeName: '',
  flagEmoji: '',
  locale: '',
  sortOrder: 0,
  isActive: true,
  isDefault: false
})

// Validation rules
const rules = {
  code: [
    { required: true, message: 'Language code is required', trigger: 'blur' },
    { pattern: /^[a-z]{2}-[A-Z]{2}$/, message: 'Format: xx-XX (e.g., zh-CN)', trigger: 'blur' }
  ],
  name: [{ required: true, message: 'Language name is required', trigger: 'blur' }],
  nativeName: [{ required: true, message: 'Native name is required', trigger: 'blur' }],
  locale: [
    { pattern: /^[a-z]{2}[A-Z]{2}$/, message: 'Format: xxXX (e.g., zhCN)', trigger: 'blur' }
  ]
}

// Computed
const isEdit = computed(() => !!props.language)

// Watch for language prop changes
watch(
  () => props.language,
  (val) => {
    if (val) {
      formData.code = val.code || ''
      formData.name = val.name || ''
      formData.nativeName = val.nativeName || ''
      formData.flagEmoji = val.flagEmoji || ''
      formData.locale = val.locale || ''
      formData.sortOrder = val.sortOrder || 0
      formData.isActive = val.isActive ?? true
      formData.isDefault = val.isDefault ?? false
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

// Reset form
const resetForm = () => {
  formData.code = ''
  formData.name = ''
  formData.nativeName = ''
  formData.flagEmoji = ''
  formData.locale = ''
  formData.sortOrder = 0
  formData.isActive = true
  formData.isDefault = false
  formRef.value?.clearValidate()
}

// Close dialog
const handleClose = () => {
  emit('update:visible', false)
}

// Save language
const handleSave = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEdit.value && props.language?.id) {
      await languageApi.update(props.language.id, formData)
      ElMessage.success('Language updated successfully')
    } else {
      await languageApi.create(formData)
      ElMessage.success('Language created successfully')
    }

    emit('success')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error.message || 'Failed to save language')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
:deep(.el-dialog__body) {
  padding-top: 16px;
}

.flag-preview {
  font-size: 20px;
}
</style>
