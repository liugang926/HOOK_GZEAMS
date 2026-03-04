<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('system.fieldDefinition.editTitle') : $t('system.fieldDefinition.createTitle')"
    width="700px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      :disabled="isReadonlyContext"
    >
      <el-form-item
        :label="$t('system.fieldDefinition.fields.code')"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          :placeholder="$t('system.fieldDefinition.placeholders.code')"
          :disabled="isEdit || isReadonlyContext"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.fieldDefinition.fields.name')"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          :placeholder="$t('system.fieldDefinition.placeholders.name')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.fieldDefinition.fields.type')"
        prop="fieldType"
      >
        <!-- Use grouped select with optgroups for better UX -->
        <el-select
          v-model="formData.fieldType"
          :placeholder="$t('system.fieldDefinition.placeholders.type')"
          :loading="fieldTypes.isLoading.value"
          @change="handleFieldTypeChange"
        >
          <el-option-group
            v-for="group in fieldTypes.groups.value"
            :key="group.label"
            :label="group.label"
          >
            <el-option
              v-for="type in group.types"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-option-group>
        </el-select>
        <el-button
          v-if="fieldTypes.error.value"
          link
          type="warning"
          size="small"
          @click="refreshFieldTypes"
        >
          {{ $t('system.fieldDefinition.actions.retry') }}
        </el-button>
      </el-form-item>

      <!-- Reference target for reference type -->
      <el-form-item
        v-if="fieldTypes.requiresReference(formData.fieldType)"
        :label="$t('system.fieldDefinition.fields.referenceObject')"
        prop="referenceObject"
      >
        <el-select
          v-model="formData.referenceObject"
          :placeholder="$t('system.fieldDefinition.placeholders.referenceObject')"
        >
          <el-option
            v-for="obj in businessObjects"
            :key="obj.code"
            :label="obj.name"
            :value="obj.code"
          />
        </el-select>
      </el-form-item>

      <!-- Options for select/radio/checkbox -->
      <el-form-item
        v-if="fieldTypes.supportsOptions(formData.fieldType)"
        :label="$t('system.fieldDefinition.fields.options')"
      >
        <div class="options-editor">
          <div
            v-for="(option, index) in formData.options"
            :key="index"
            class="option-item"
          >
            <el-input
              v-model="option.label"
              :placeholder="$t('system.fieldDefinition.placeholders.optionLabel')"
              style="width: 150px"
            />
            <el-input
              v-model="option.value"
              :placeholder="$t('system.fieldDefinition.placeholders.optionValue')"
              style="width: 100px"
            />
            <el-color-picker
              v-model="option.color"
              show-alpha
              size="small"
            />
            <el-button
              link
              type="danger"
              @click="removeOption(index)"
            >
              {{ $t('common.actions.delete') }}
            </el-button>
          </div>
          <el-button
            link
            type="primary"
            @click="addOption"
          >
            + {{ $t('system.fieldDefinition.actions.addOption') }}
          </el-button>
        </div>
      </el-form-item>

      <!-- Formula expression -->
      <el-form-item
        v-if="formData.fieldType === 'formula'"
        :label="$t('system.fieldDefinition.fields.formula')"
      >
        <el-input
          v-model="formData.formulaExpression"
          type="textarea"
          :rows="2"
          :placeholder="$t('system.fieldDefinition.placeholders.formula')"
        />
        <div class="form-tip">
          {{ $t('system.fieldDefinition.tips.formula') }}
        </div>
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.sortOrder')">
        <el-input-number
          v-model="formData.sortOrder"
          :min="0"
          :max="9999"
        />
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.defaultValue')">
        <el-input
          v-model="formData.defaultValue"
          :placeholder="getDefaultValuePlaceholder()"
        />
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.placeholder')">
        <el-input
          v-model="formData.placeholder"
          :placeholder="$t('system.fieldDefinition.placeholders.placeholder')"
        />
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.description')">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          :placeholder="$t('system.fieldDefinition.placeholders.description')"
        />
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.required')">
        <el-switch v-model="formData.isRequired" />
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.readonly')">
        <el-switch v-model="formData.isReadonly" />
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.unique')">
        <el-switch v-model="formData.isUnique" />
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.showInList')">
        <el-switch v-model="formData.showInList" />
        <span class="form-tip">{{ $t('system.fieldDefinition.tips.showInList') }}</span>
      </el-form-item>

      <el-form-item :label="$t('system.fieldDefinition.fields.listWidth')">
        <el-input-number
          v-model="formData.listWidth"
          :min="50"
          :max="500"
          :step="10"
        />
        <span class="form-tip">{{ $t('system.fieldDefinition.tips.listWidth') }}</span>
      </el-form-item>

      <!-- Validation rules -->
      <el-form-item
        v-if="['text', 'textarea'].includes(formData.fieldType)"
        :label="$t('system.fieldDefinition.fields.maxLength')"
      >
        <el-input-number
          v-model="formData.maxLength"
          :min="1"
          :max="10000"
        />
      </el-form-item>

      <el-form-item
        v-if="['number', 'currency'].includes(formData.fieldType)"
        :label="$t('system.fieldDefinition.fields.numericRange')"
      >
        <el-input-number
          v-model="formData.minValue"
          :placeholder="$t('system.fieldDefinition.placeholders.minValue')"
          style="width: 120px"
        />
        <span style="margin: 0 10px">-</span>
        <el-input-number
          v-model="formData.maxValue"
          :placeholder="$t('system.fieldDefinition.placeholders.maxValue')"
          style="width: 120px"
        />
      </el-form-item>

      <el-form-item
        v-if="formData.fieldType === 'number'"
        :label="$t('system.fieldDefinition.fields.decimalPlaces')"
      >
        <el-input-number
          v-model="formData.decimalPlaces"
          :min="0"
          :max="6"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.actions.cancel') }}
      </el-button>
      <el-button
        v-if="!isReadonlyContext"
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
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useFieldTypes } from '@/composables/useFieldTypes'
import { fieldDefinitionApi } from '@/api/system'
import type { FieldDefinitionPayload } from '@/api/system/fieldDefinition'

const { t } = useI18n()

interface Props {
  visible: boolean
  data?: ExistingFieldData
  objectCode?: string
  objectId?: string
  isHardcoded?: boolean
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
const isReadonlyContext = computed(() => Boolean(props.isHardcoded || props.data?.isSystem))

// Field types composable - loads from API with caching
const fieldTypes = useFieldTypes()

// Load field types on mount
onMounted(async () => {
  await fieldTypes.fetch()
})

// Refresh field types (for error recovery)
async function refreshFieldTypes() {
  await fieldTypes.fetch(true)
}

// Mock business objects for reference
const businessObjects = ref([
  { code: 'Asset', name: t('system.fieldDefinition.types.asset') },
  { code: 'Employee', name: t('system.fieldDefinition.types.user') },
  { code: 'Department', name: t('system.fieldDefinition.types.department') }
])

type ExistingFieldData = {
  id?: string
  isSystem?: boolean
  code?: string
  name?: string
  fieldType?: string
  field_type?: string
  referenceObject?: string
  reference_object?: string
  options?: Array<{ label?: string; value?: string; color?: string }>
  formulaExpression?: string
  formula?: string
  sortOrder?: number
  sort_order?: number
  defaultValue?: string
  default_value?: string
  placeholder?: string
  description?: string
  isRequired?: boolean
  is_required?: boolean
  isReadonly?: boolean
  is_readonly?: boolean
  isUnique?: boolean
  is_unique?: boolean
  showInList?: boolean
  show_in_list?: boolean
  listWidth?: number
  columnWidth?: number
  column_width?: number
  maxLength?: number
  max_length?: number
  minValue?: number
  min_value?: number
  maxValue?: number
  max_value?: number
  decimalPlaces?: number
  decimal_places?: number
}

type FieldOption = { label: string; value: string; color: string }
type FieldFormData = {
  code: string
  name: string
  fieldType: string
  referenceObject: string
  options: FieldOption[]
  formulaExpression: string
  sortOrder: number
  defaultValue: string
  placeholder: string
  description: string
  isRequired: boolean
  isReadonly: boolean
  isUnique: boolean
  showInList: boolean
  listWidth: number
  maxLength: number
  minValue: number | undefined
  maxValue: number | undefined
  decimalPlaces: number
}

const createDefaultFormData = (): FieldFormData => ({
  code: '',
  name: '',
  fieldType: 'text',
  referenceObject: '',
  options: [],
  formulaExpression: '',
  sortOrder: 0,
  defaultValue: '',
  placeholder: '',
  description: '',
  isRequired: false,
  isReadonly: false,
  isUnique: false,
  showInList: true,
  listWidth: 120,
  maxLength: 255,
  minValue: undefined,
  maxValue: undefined,
  decimalPlaces: 2
})

const formData = ref<FieldFormData>(createDefaultFormData())

const rules = computed<FormRules>(() => ({
  code: [
    { required: true, message: t('system.fieldDefinition.validation.codeRequired'), trigger: 'blur' },
    { pattern: /^[a-z][a-zA-Z0-9]*$/, message: t('system.fieldDefinition.validation.codePattern'), trigger: 'blur' }
  ],
  name: [
    { required: true, message: t('system.fieldDefinition.validation.nameRequired'), trigger: 'blur' }
  ],
  fieldType: [
    { required: true, message: t('system.fieldDefinition.validation.typeRequired'), trigger: 'change' }
  ],
  referenceObject: [
    {
      validator: (_rule: unknown, value: string, callback: (error?: Error) => void) => {
        if (fieldTypes.requiresReference(formData.value.fieldType) && !String(value || '').trim()) {
          callback(new Error(t('system.fieldDefinition.validation.referenceObjectRequired')))
          return
        }
        callback()
      },
      trigger: 'change'
    }
  ]
}))

const normalizeIncomingField = (source: ExistingFieldData): FieldFormData => {
  const row = source || {}
  const normalizedOptions = Array.isArray(row.options)
    ? row.options
      .map((option) => ({
        label: String(option?.label ?? ''),
        value: String(option?.value ?? ''),
        color: String(option?.color ?? '#409eff')
      }))
      .filter((option: FieldOption) => option.label || option.value)
    : []

  return {
    ...createDefaultFormData(),
    code: String(row.code ?? ''),
    name: String(row.name ?? ''),
    fieldType: String(row.fieldType ?? row.field_type ?? 'text'),
    referenceObject: String(row.referenceObject ?? row.reference_object ?? ''),
    options: normalizedOptions,
    formulaExpression: String(row.formulaExpression ?? row.formula ?? ''),
    sortOrder: Number(row.sortOrder ?? row.sort_order ?? 0) || 0,
    defaultValue: String(row.defaultValue ?? row.default_value ?? ''),
    placeholder: String(row.placeholder ?? ''),
    description: String(row.description ?? ''),
    isRequired: Boolean(row.isRequired ?? row.is_required),
    isReadonly: Boolean(row.isReadonly ?? row.is_readonly),
    isUnique: Boolean(row.isUnique ?? row.is_unique),
    showInList: row.showInList ?? row.show_in_list ?? true,
    listWidth: Number(row.listWidth ?? row.columnWidth ?? row.column_width ?? 120) || 120,
    maxLength: Number(row.maxLength ?? row.max_length ?? 255) || 255,
    minValue: row.minValue ?? row.min_value ?? undefined,
    maxValue: row.maxValue ?? row.max_value ?? undefined,
    decimalPlaces: Number(row.decimalPlaces ?? row.decimal_places ?? 2) || 0
  }
}

watch(() => props.visible, (val) => {
  if (!val) return
  if (props.data) {
    formData.value = normalizeIncomingField(props.data)
  } else {
    resetForm()
  }
})

const resetForm = () => {
  formData.value = createDefaultFormData()
  formRef.value?.clearValidate()
}

const getDefaultValuePlaceholder = () => {
  const type = formData.value.fieldType
  const placeholders: Record<string, string> = {
    text: t('system.fieldDefinition.placeholders.defaultValue.text'),
    number: t('system.fieldDefinition.placeholders.defaultValue.number'),
    date: t('system.fieldDefinition.placeholders.defaultValue.date'),
    switch: t('system.fieldDefinition.placeholders.defaultValue.switch'),
    select: t('system.fieldDefinition.placeholders.defaultValue.select')
  }
  return placeholders[type] || ''
}

const handleFieldTypeChange = () => {
  // Reset type-specific fields
  formData.value.options = []
  formData.value.formulaExpression = ''
  formData.value.referenceObject = ''
}

const addOption = () => {
  formData.value.options.push({
    label: '',
    value: '',
    color: '#409eff'
  })
}

const removeOption = (index: number) => {
  formData.value.options.splice(index, 1)
}

const handleClose = () => {
  emit('update:visible', false)
}

const getReadonlySubmitBlockedMessage = (): string => {
  const key = 'system.fieldDefinition.messages.readOnlySubmitBlocked'
  const message = t(key)
  return message !== key ? message : 'This field is read-only and cannot be modified.'
}

const getMissingObjectIdMessage = (): string => {
  const key = 'system.fieldDefinition.messages.missingObjectMeta'
  const message = t(key)
  return message !== key ? message : 'Missing business object metadata. Please refresh and try again.'
}

const buildPayload = (): FieldDefinitionPayload => {
  const payload: FieldDefinitionPayload = {
    code: formData.value.code,
    name: formData.value.name,
    fieldType: formData.value.fieldType,
    sortOrder: formData.value.sortOrder,
    defaultValue: formData.value.defaultValue,
    placeholder: formData.value.placeholder,
    isRequired: formData.value.isRequired,
    isReadonly: formData.value.isReadonly,
    isUnique: formData.value.isUnique,
    showInList: formData.value.showInList,
    showInDetail: true,
    showInForm: true,
    maxLength: formData.value.maxLength,
    minValue: formData.value.minValue ?? null,
    maxValue: formData.value.maxValue ?? null,
    decimalPlaces: formData.value.decimalPlaces
  }

  if (formData.value.description) {
    payload.description = formData.value.description
  }
  if (fieldTypes.requiresReference(formData.value.fieldType)) {
    payload.referenceObject = formData.value.referenceObject
  }
  if (fieldTypes.supportsOptions(formData.value.fieldType)) {
    payload.options = formData.value.options
      .map((option) => ({
        label: String(option.label || '').trim(),
        value: String(option.value || '').trim(),
        color: String(option.color || '#409eff')
      }))
      .filter((option) => option.label || option.value)
  } else {
    payload.options = []
  }
  if (formData.value.fieldType === 'formula') {
    payload.formula = formData.value.formulaExpression
  }

  return payload
}

const handleSubmit = async () => {
  if (!formRef.value) return
  if (isReadonlyContext.value) {
    ElMessage.warning(getReadonlySubmitBlockedMessage())
    return
  }

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true
    try {
      const payload = buildPayload()
      if (isEdit.value) {
        const fieldId = props.data?.id
        if (!fieldId) {
          ElMessage.error(t('common.messages.operationFailed'))
          return
        }
        await fieldDefinitionApi.update(fieldId, payload)
      } else {
        if (!props.objectId) {
          ElMessage.error(getMissingObjectIdMessage())
          return
        }
        await fieldDefinitionApi.create({
          ...payload,
          businessObject: props.objectId
        })
      }

      ElMessage.success(isEdit.value ? t('common.messages.updateSuccess') : t('common.messages.addSuccess'))
      emit('success')
      handleClose()
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { error?: { message?: string } } }; message?: string }
      const errorMsg = apiError?.response?.data?.error?.message || apiError?.message || t('common.messages.operationFailed')
      ElMessage.error(errorMsg)
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.options-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
