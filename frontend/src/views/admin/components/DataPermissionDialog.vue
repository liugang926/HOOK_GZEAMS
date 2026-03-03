<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('system.permission.data.dialog.editTitle') : $t('system.permission.data.dialog.createTitle')"
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
        :label="$t('system.permission.data.dialog.role')"
        prop="roleName"
      >
        <el-select
          v-model="formData.roleName"
          filterable
          remote
          reserve-keyword
          clearable
          :placeholder="$t('system.permission.data.dialog.rolePlaceholder')"
          :loading="optionsLoading.users"
          :disabled="isEdit"
          :remote-method="handleUserRemoteSearch"
        >
          <el-option
            v-for="option in userOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="$t('system.permission.data.dialog.object')"
        prop="businessObjectName"
      >
        <el-select
          v-model="formData.businessObjectName"
          filterable
          remote
          reserve-keyword
          clearable
          allow-create
          default-first-option
          :placeholder="objectPlaceholder"
          :loading="optionsLoading.objects"
          :disabled="isEdit"
          :remote-method="handleObjectRemoteSearch"
        >
          <el-option
            v-for="option in objectOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="$t('system.permission.data.dialog.type')"
        prop="permissionType"
      >
        <el-select
          v-model="formData.permissionType"
          :placeholder="$t('system.permission.data.dialog.typePlaceholder')"
          @change="handlePermissionTypeChange"
        >
          <el-option
            :label="$t('system.permission.data.types.all')"
            value="all"
          />
          <el-option
            :label="$t('system.permission.data.types.department')"
            value="department"
          />
          <el-option
            :label="$t('system.permission.data.types.department_and_sub')"
            value="department_and_sub"
          />
          <el-option
            :label="$t('system.permission.data.types.self')"
            value="self"
          />
          <el-option
            :label="$t('system.permission.data.types.custom')"
            value="custom"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        v-if="formData.permissionType === 'custom'"
        :label="$t('system.permission.data.dialog.expression')"
        prop="scopeExpression"
      >
        <el-input
          v-model="formData.scopeExpression"
          type="textarea"
          :rows="3"
          :placeholder="$t('system.permission.data.dialog.expressionPlaceholder')"
        />
      </el-form-item>

      <el-form-item
        v-else
        :label="$t('system.permission.data.dialog.scope')"
      >
        <el-input
          :value="getScopePreview()"
          disabled
        />
      </el-form-item>

      <el-form-item
        :label="$t('system.permission.data.dialog.description')"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          :placeholder="$t('system.permission.data.dialog.descriptionPlaceholder')"
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
import { ref, computed, watch, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'
import {
  dataPermissionApi,
  type DataPermissionUpdatePayload,
  type DataPermissionCreatePayload,
  type DataPermissionRecord
} from '@/api/permissions'
import {
  fetchPermissionUserOptions,
  fetchPermissionObjectOptions,
  type PermissionUserOption,
  type PermissionObjectOption
} from './permissionOptions'

const { t } = useI18n()

interface DataPermissionDialogData {
  id?: string
  roleName?: string
  businessObjectName?: string
  permissionType?: DataPermissionFormState['permissionType']
  scopeType?: DataPermissionRecord['scopeType']
  scopeValue?: Record<string, unknown>
  departmentField?: string
  userField?: string
  description?: string
}

interface DataPermissionFormState {
  roleName: string
  businessObjectName: string
  permissionType: 'all' | 'department' | 'department_and_sub' | 'self' | 'custom'
  scopeExpression: string
  departmentField: string
  userField: string
  description: string
}

interface Props {
  visible: boolean
  data?: DataPermissionDialogData | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const userOptions = ref<PermissionUserOption[]>([])
const objectOptions = ref<PermissionObjectOption[]>([])
const optionsLoading = reactive({
  users: false,
  objects: false
})

const isEdit = computed(() => !!props.data?.id)
const objectPlaceholder = computed(() => {
  const base = t('system.permission.data.dialog.objectPlaceholder')
  return isEdit.value ? base : `${base} (app.model)`
})

const formData = ref<DataPermissionFormState>({
  roleName: '',
  businessObjectName: '',
  permissionType: 'department',
  scopeExpression: '',
  departmentField: 'department',
  userField: 'created_by',
  description: ''
})

const rules: FormRules = {
  roleName: [{ required: true, message: t('system.permission.data.dialog.rolePlaceholder'), trigger: 'blur' }],
  businessObjectName: [{ required: true, message: t('system.permission.data.dialog.objectPlaceholder'), trigger: 'blur' }],
  permissionType: [{ required: true, message: t('system.permission.data.dialog.typePlaceholder'), trigger: 'change' }]
}

const asRecord = (value: unknown): Record<string, unknown> => {
  if (value && typeof value === 'object') {
    return value as Record<string, unknown>
  }
  return {}
}

const getScopeExpressionFromValue = (scopeValue: Record<string, unknown>): string => {
  const candidate = scopeValue.filterExpression
  return typeof candidate === 'string' ? candidate : ''
}

const mapScopeTypeToUiType = (scopeType?: DataPermissionRecord['scopeType']): DataPermissionFormState['permissionType'] => {
  const map: Record<DataPermissionRecord['scopeType'], DataPermissionFormState['permissionType']> = {
    all: 'all',
    self_dept: 'department',
    self_and_sub: 'department_and_sub',
    self: 'self',
    custom: 'custom',
    specified: 'custom'
  }
  if (!scopeType) return 'custom'
  return map[scopeType] || 'custom'
}

const mapUiTypeToScopeType = (uiType: DataPermissionFormState['permissionType']): DataPermissionRecord['scopeType'] => {
  const map: Record<DataPermissionFormState['permissionType'], DataPermissionRecord['scopeType']> = {
    all: 'all',
    department: 'self_dept',
    department_and_sub: 'self_and_sub',
    self: 'self',
    custom: 'custom'
  }
  return map[uiType] || 'custom'
}

const resetForm = () => {
  formData.value = {
    roleName: '',
    businessObjectName: '',
    permissionType: 'department',
    scopeExpression: '',
    departmentField: 'department',
    userField: 'created_by',
    description: ''
  }
  formRef.value?.clearValidate()
}

watch(() => props.visible, (val) => {
  if (!val) return

  loadOptions()

  if (props.data) {
    const scopeValue = asRecord(props.data.scopeValue)
    formData.value = {
      roleName: props.data.roleName || '',
      businessObjectName: props.data.businessObjectName || '',
      permissionType: props.data.permissionType || mapScopeTypeToUiType(props.data.scopeType),
      scopeExpression: getScopeExpressionFromValue(scopeValue),
      departmentField: props.data.departmentField || 'department',
      userField: props.data.userField || 'created_by',
      description: props.data.description || ''
    }
    formRef.value?.clearValidate()
    return
  }

  resetForm()
})

const fetchUserOptions = async (search = '') => {
  optionsLoading.users = true
  try {
    const users = await fetchPermissionUserOptions(search).catch(() => [])
    userOptions.value = users
  } finally {
    optionsLoading.users = false
  }
}

const fetchObjectOptions = async (search = '') => {
  optionsLoading.objects = true
  try {
    const objects = await fetchPermissionObjectOptions(search).catch(() => [])
    objectOptions.value = objects
  } finally {
    optionsLoading.objects = false
  }
}

const loadOptions = async () => {
  await Promise.all([
    fetchUserOptions(''),
    fetchObjectOptions('')
  ])
}

const handleUserRemoteSearch = (query: string) => {
  if (isEdit.value) return
  fetchUserOptions(query)
}

const handleObjectRemoteSearch = (query: string) => {
  if (isEdit.value) return
  fetchObjectOptions(query)
}

const handlePermissionTypeChange = () => {
  if (formData.value.permissionType !== 'custom') {
    formData.value.scopeExpression = ''
  }
}

const getScopePreview = () => {
  const previews: Record<string, string> = {
    all: t('system.permission.data.types.all'),
    department: t('system.permission.data.types.department'),
    department_and_sub: t('system.permission.data.types.department_and_sub'),
    self: t('system.permission.data.types.self')
  }
  return previews[formData.value.permissionType] || ''
}

const handleClose = () => {
  emit('update:visible', false)
}

const parseModelIdentifier = (input: string) => {
  const raw = input.trim()
  if (!raw) {
    return { appLabel: 'objects', model: '' }
  }

  const chunks = raw.split('.')
  if (chunks.length >= 2) {
    return {
      appLabel: chunks[0],
      model: chunks.slice(1).join('.')
    }
  }

  return {
    appLabel: 'objects',
    model: raw
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      let scopeType = mapUiTypeToScopeType(formData.value.permissionType)
      let scopeValue: Record<string, unknown> = scopeType === 'custom'
        ? { filterExpression: formData.value.scopeExpression.trim() }
        : {}

      // Preserve legacy "specified" rules when opened in edit mode.
      if (
        isEdit.value &&
        props.data?.scopeType === 'specified' &&
        formData.value.permissionType === 'custom' &&
        !formData.value.scopeExpression.trim()
      ) {
        scopeType = 'specified'
        scopeValue = asRecord(props.data.scopeValue)
      }

      const payload: DataPermissionUpdatePayload = {
        scopeType,
        scopeValue,
        departmentField: formData.value.departmentField,
        userField: formData.value.userField,
        description: formData.value.description || ''
      }

      if (isEdit.value) {
        const targetId = props.data?.id
        if (!targetId) {
          throw new Error('Missing data permission id')
        }
        await dataPermissionApi.update(targetId, payload)
      } else {
        const target = parseModelIdentifier(formData.value.businessObjectName)
        const createPayload: DataPermissionCreatePayload = {
          userUsername: formData.value.roleName.trim(),
          contentTypeAppLabel: target.appLabel,
          contentTypeModel: target.model,
          ...payload
        }
        await dataPermissionApi.create(createPayload)
      }

      ElMessage.success(isEdit.value ? t('system.permission.data.messages.updateSuccess') : t('system.permission.data.messages.createSuccess'))
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
