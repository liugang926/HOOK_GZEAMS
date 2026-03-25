<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('system.translations.edit') : $t('system.translations.create')"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <!-- Translation Mode -->
      <el-form-item :label="$t('system.translations.mode')">
        <el-radio-group
          v-model="mode"
          :disabled="Boolean(props.lockObjectTarget && !isEdit)"
          @change="handleModeChange"
        >
          <el-radio value="namespace">
            {{ $t('system.translations.modes.namespace') }}
          </el-radio>
          <el-radio value="object">
            {{ $t('system.translations.modes.object') }}
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- Language -->
      <el-form-item
        :label="$t('system.translations.language')"
        prop="languageCode"
      >
        <el-select
          v-model="formData.languageCode"
          style="width: 100%"
        >
          <el-option
            v-for="lang in languages"
            :key="lang.code"
            :label="`${lang.flagEmoji} ${lang.name}`"
            :value="lang.code"
          />
        </el-select>
      </el-form-item>

      <!-- Namespace/Key mode -->
      <template v-if="mode === 'namespace'">
        <el-form-item
          :label="$t('system.translations.namespace')"
          prop="namespace"
        >
          <el-input
            v-model="formData.namespace"
            :placeholder="$t('system.translations.namespacePlaceholder')"
          />
        </el-form-item>
        <el-form-item
          :label="$t('system.translations.key')"
          prop="key"
        >
          <el-input
            v-model="formData.key"
            :placeholder="$t('system.translations.keyPlaceholder')"
          />
        </el-form-item>
      </template>

      <!-- Object mode -->
      <template v-else>
        <el-form-item
          :label="$t('system.translations.contentType')"
          prop="contentType"
        >
          <el-select
            v-model="formData.contentTypeModel"
            style="width: 100%"
            :disabled="Boolean(props.lockObjectTarget && !isEdit)"
          >
            <el-option
              value="businessobject"
              :label="$t('system.translations.contentTypes.businessObject')"
            />
            <el-option
              value="dictionarytype"
              :label="$t('system.translations.contentTypes.dictionaryType')"
            />
            <el-option
              value="dictionaryitem"
              :label="$t('system.translations.contentTypes.dictionaryItem')"
            />
            <el-option
              value="modelfielddefinition"
              :label="$t('system.translations.contentTypes.modelFieldDefinition')"
            />
            <el-option
              value="menugroup"
              :label="$t('system.translations.contentTypes.menuGroup')"
            />
          </el-select>
        </el-form-item>
        <el-form-item
          :label="$t('system.translations.objectId')"
          prop="objectId"
        >
          <el-input
            v-model="formData.objectId"
            :placeholder="$t('system.translations.objectIdPlaceholder')"
            style="width: 100%"
            :disabled="Boolean(props.lockObjectTarget && !isEdit)"
          />
        </el-form-item>
        <el-form-item
          :label="$t('system.translations.fieldName')"
          prop="fieldName"
        >
          <el-input
            v-model="formData.fieldName"
            :placeholder="$t('system.translations.fieldNamePlaceholder')"
            :disabled="Boolean(props.lockObjectTarget && !isEdit)"
          />
        </el-form-item>
      </template>

      <!-- Translation Text -->
      <el-form-item
        :label="$t('system.translations.text')"
        prop="text"
      >
        <el-input
          v-model="formData.text"
          type="textarea"
          :rows="3"
          :placeholder="$t('system.translations.textPlaceholder')"
        />
      </el-form-item>

      <!-- Context (optional) -->
      <el-form-item :label="$t('system.translations.context')">
        <el-input
          v-model="formData.context"
          :placeholder="$t('system.translations.contextPlaceholder')"
        />
      </el-form-item>

      <!-- Type -->
      <el-form-item :label="$t('system.translations.type')">
        <el-select
          v-model="formData.type"
          style="width: 100%"
        >
          <el-option
            value="label"
            :label="$t('system.translations.types.label')"
          />
          <el-option
            value="message"
            :label="$t('system.translations.types.message')"
          />
          <el-option
            value="enum"
            :label="$t('system.translations.types.enum')"
          />
          <el-option
            value="object_field"
            :label="$t('system.translations.types.objectField')"
          />
        </el-select>
      </el-form-item>

      <!-- Is System -->
      <el-form-item>
        <el-checkbox v-model="formData.isSystem">
          {{ $t('system.translations.isSystemLabel') }}
        </el-checkbox>
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
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { translationApi } from '@/api/translations'
import type { Translation, Language } from '@/api/translations'

interface Props {
  visible: boolean
  translation?: Translation | null
  preset?: Partial<Translation> | null
  lockObjectTarget?: boolean
  languages: Language[]
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const { t } = useI18n()

const formRef = ref<any>()
const saving = ref(false)
const mode = ref<'namespace' | 'object'>('namespace')

// Form data
const formData = reactive<{
  namespace: string
  key: string
  contentTypeModel: string
  objectId: string | null
  fieldName: string
  languageCode: string
  text: string
  context: string
  type: string
  isSystem: boolean
}>({
  namespace: '',
  key: '',
  contentTypeModel: '',
  objectId: null,
  fieldName: '',
  languageCode: 'zh-CN',
  text: '',
  context: '',
  type: 'label',
  isSystem: false
})

// Validation rules
const requiredWithField = (fieldKey: string) => {
  return t('common.validation.requiredWithField', { field: t(fieldKey) })
}

const rules = {
  languageCode: [{ required: true, message: requiredWithField('system.translations.language'), trigger: 'change' }],
  namespace: [{ required: true, message: requiredWithField('system.translations.namespace'), trigger: 'blur' }],
  key: [{ required: true, message: requiredWithField('system.translations.key'), trigger: 'blur' }],
  contentTypeModel: [{ required: true, message: requiredWithField('system.translations.contentType'), trigger: 'change' }],
  objectId: [{ required: true, message: requiredWithField('system.translations.objectId'), trigger: 'blur' }],
  fieldName: [{ required: true, message: requiredWithField('system.translations.fieldName'), trigger: 'blur' }],
  text: [{ required: true, message: requiredWithField('system.translations.text'), trigger: 'blur' }]
}

// Computed
const isEdit = computed(() => !!props.translation)

const applyPreset = () => {
  formData.namespace = ''
  formData.key = ''
  formData.contentTypeModel = String(props.preset?.contentTypeModel || '')
  formData.objectId = props.preset?.objectId ? String(props.preset.objectId) : null
  formData.fieldName = String(props.preset?.fieldName || '')
  formData.languageCode = props.languages.find((lang) => lang.isDefault)?.code || 'zh-CN'
  formData.text = ''
  formData.context = ''
  formData.type = String(props.preset?.type || 'object_field')
  formData.isSystem = false
  mode.value = formData.contentTypeModel && formData.objectId ? 'object' : 'namespace'
  formRef.value?.clearValidate()
}

// Watch for translation prop changes
watch(
  () => props.translation,
  (val) => {
    if (val) {
      // Edit mode - populate form
      formData.namespace = val.namespace || ''
      formData.key = val.key || ''
      formData.contentTypeModel = val.contentTypeModel || ''
      formData.objectId = val.objectId || null
      formData.fieldName = val.fieldName || ''
      formData.languageCode = val.languageCode || 'zh-CN'
      formData.text = val.text || ''
      formData.context = val.context || ''
      formData.type = val.type || 'label'
      formData.isSystem = val.isSystem || false

      // Determine mode
      mode.value = val.namespace && val.key ? 'namespace' : 'object'
    } else {
      props.visible ? applyPreset() : resetForm()
    }
  },
  { immediate: true }
)

watch(
  () => props.visible,
  (visible) => {
    if (!visible || props.translation) return
    applyPreset()
  }
)

// Handle mode change
const handleModeChange = (newMode: 'namespace' | 'object') => {
  if (newMode === 'namespace') {
    formData.contentTypeModel = ''
    formData.objectId = null
    formData.fieldName = ''
  } else {
    formData.namespace = ''
    formData.key = ''
  }
}

// Reset form
const resetForm = () => {
  formData.namespace = ''
  formData.key = ''
  formData.contentTypeModel = ''
  formData.objectId = null
  formData.fieldName = ''
  formData.languageCode = 'zh-CN'
  formData.text = ''
  formData.context = ''
  formData.type = 'label'
  formData.isSystem = false
  mode.value = 'namespace'
  formRef.value?.clearValidate()
}

// Close dialog
const handleClose = () => {
  emit('update:visible', false)
}

// Save translation
const handleSave = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload: any = {
      languageCode: formData.languageCode,
      text: formData.text,
      context: formData.context,
      type: formData.type,
      isSystem: formData.isSystem
    }

    if (mode.value === 'namespace') {
      payload.namespace = formData.namespace
      payload.key = formData.key
    } else {
      payload.contentType = formData.contentTypeModel
      payload.objectId = formData.objectId
      payload.fieldName = formData.fieldName
    }

    if (isEdit.value && props.translation?.id) {
      await translationApi.update(props.translation.id, payload)
      ElMessage.success(t('system.translations.messages.updateSuccess'))
    } else {
      await translationApi.create(payload)
      ElMessage.success(t('system.translations.messages.createSuccess'))
    }

    emit('success')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error.message || t('system.translations.messages.saveFailed'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped lang="scss">
:deep(.el-dialog__body) {
  padding-top: 16px;
}
</style>
