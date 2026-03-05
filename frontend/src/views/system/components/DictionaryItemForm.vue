<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('common.actions.edit') + $t('system.dictionary.item') : $t('common.actions.add') + $t('system.dictionary.item')"
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
        :label="$t('system.dictionary.itemCode')"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          :placeholder="$t('system.dictionary.itemCodePlaceholder')"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.dictionary.displayName')"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          :placeholder="$t('system.dictionary.displayNamePlaceholder')"
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
        :label="$t('system.dictionary.color')"
        prop="color"
      >
        <div class="color-picker-wrapper">
          <el-color-picker
            v-model="formData.color"
            show-alpha
          />
          <el-input
            v-model="formData.color"
            :placeholder="$t('system.dictionary.colorPlaceholder')"
            style="width: 200px; margin-left: 10px"
          />
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.dictionary.icon')"
        prop="icon"
      >
        <el-select
          v-model="formData.icon"
          :placeholder="$t('system.dictionary.iconPlaceholder')"
          filterable
          clearable
        >
          <el-option
            v-for="icon in commonIcons"
            :key="icon.value"
            :label="icon.label"
            :value="icon.value"
          >
            <div class="icon-option">
              <el-icon><component :is="icon.value" /></el-icon>
              <span>{{ icon.label }}</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item
        :label="$t('system.dictionary.isDefault')"
        prop="is_default"
      >
        <el-switch v-model="formData.is_default" />
        <div class="form-tip">
          {{ $t('system.dictionary.isDefaultTip') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('system.dictionary.enabled')"
        prop="is_active"
      >
        <el-switch
          v-model="formData.is_active"
          :active-text="$t('system.dictionary.status.enabled')"
          :inactive-text="$t('system.dictionary.status.disabled')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('common.labels.description')"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          :placeholder="$t('system.dictionary.descriptionPlaceholder')"
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
        {{ isEdit ? $t('common.actions.save') : $t('common.actions.add') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { DictionaryItem } from '@/api/system'
import { dictionaryItemApi } from '@/api/system'

const { t } = useI18n()

interface Props {
  visible: boolean
  dictionaryTypeCode: string
  data?: DictionaryItem | null
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
  color: '',
  icon: '',
  sort_order: 0,
  is_default: false,
  is_active: true,
  description: ''
})

const rules: FormRules = {
  code: [
    { required: true, message: t('system.dictionary.validation.itemCodeRequired'), trigger: 'blur' },
    { pattern: /^[A-Za-z_][A-Za-z0-9_]*$/, message: t('system.dictionary.validation.itemCodePattern'), trigger: 'blur' }
  ],
  name: [{ required: true, message: t('system.dictionary.validation.displayNameRequired'), trigger: 'blur' }]
}

const commonIcons = [
  { value: 'Check', label: 'Check' },
  { value: 'Close', label: 'Close' },
  { value: 'Delete', label: 'Delete' },
  { value: 'Edit', label: 'Edit' },
  { value: 'Search', label: 'Search' },
  { value: 'Star', label: 'Star' },
  { value: 'Plus', label: 'Plus' },
  { value: 'Minus', label: 'Minus' },
  { value: 'Warning', label: 'Warning' },
  { value: 'InfoFilled', label: 'InfoFilled' },
  { value: 'SuccessFilled', label: 'SuccessFilled' },
  { value: 'CircleCheck', label: 'CircleCheck' },
  { value: 'CircleClose', label: 'CircleClose' },
  { value: 'CirclePlus', label: 'CirclePlus' },
  { value: 'Remove', label: 'Remove' },
  { value: 'Refresh', label: 'Refresh' },
  { value: 'Download', label: 'Download' },
  { value: 'Upload', label: 'Upload' },
  { value: 'Folder', label: 'Folder' },
  { value: 'Document', label: 'Document' },
  { value: 'Files', label: 'Files' },
  { value: 'Link', label: 'Link' },
  { value: 'User', label: 'User' },
  { value: 'Setting', label: 'Setting' },
  { value: 'Bell', label: 'Bell' },
  { value: 'ChatDotRound', label: 'ChatDotRound' },
  { value: 'Message', label: 'Message' },
  { value: 'Phone', label: 'Phone' },
  { value: 'Location', label: 'Location' },
  { value: 'Calendar', label: 'Calendar' },
  { value: 'Clock', label: 'Clock' },
  { value: 'Timer', label: 'Timer' },
  { value: 'StarFilled', label: 'StarFilled' },
  { value: 'Thumb', label: 'Thumb' }
]

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, {
      code: props.data.code || '',
      name: props.data.name || '',
      name_en: props.data.name_en || '',
      color: props.data.color || '',
      icon: props.data.icon || '',
      sort_order: props.data.sort_order || 0,
      is_default: props.data.is_default || false,
      is_active: props.data.is_active ?? true,
      description: props.data.description || ''
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
    color: '',
    icon: '',
    sort_order: 0,
    is_default: false,
    is_active: true,
    description: ''
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
        await dictionaryItemApi.update(props.data!.id, formData.value)
      } else {
        await dictionaryItemApi.create({
          ...formData.value,
          dictionary_type: props.dictionaryTypeCode
        })
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
.color-picker-wrapper {
  display: flex;
  align-items: center;
}

.icon-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
