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
    >
      <el-form-item
        :label="$t('system.fieldDefinition.fields.code')"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          :placeholder="$t('system.fieldDefinition.placeholders.code')"
          :disabled="isEdit"
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

const { t } = useI18n()

interface Props {
  visible: boolean
  data?: any
  objectCode?: string
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

const formData = ref({
  code: '',
  name: '',
  fieldType: 'text',
  referenceObject: '',
  options: [] as Array<{ label: string; value: string; color: string }>,
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
  minValue: undefined as number | undefined,
  maxValue: undefined as number | undefined,
  decimalPlaces: 2
})

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
    { required: true, message: t('system.fieldDefinition.validation.referenceObjectRequired'), trigger: 'change' }
  ]
}))

watch(() => props.visible, (val) => {
  if (val && props.data) {
    // Edit mode
    Object.assign(formData.value, props.data)
    if (!formData.value.options) {
      formData.value.options = []
    }
  } else if (val) {
    // Create mode
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
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
  }
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

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true
    try {
      const data = {
        ...formData.value,
        businessObject: props.objectCode
      }

      // TODO: Replace with actual API call
      if (isEdit.value) {
        // await fieldDefinitionApi.update(props.data.id, data)
      } else {
        // await fieldDefinitionApi.create(data)
      }

      ElMessage.success(isEdit.value ? t('common.messages.updateSuccess') : t('common.messages.addSuccess'))
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
