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
          :placeholder="$t('system.permission.data.dialog.rolePlaceholder')"
          :disabled="isEdit"
        >
          <el-option
            label="管理员"
            value="admin"
          />
          <el-option
            label="部门主管"
            value="manager"
          />
          <el-option
            label="普通员工"
            value="employee"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="$t('system.permission.data.dialog.object')"
        prop="businessObjectName"
      >
        <el-select
          v-model="formData.businessObjectName"
          :placeholder="$t('system.permission.data.dialog.objectPlaceholder')"
          :disabled="isEdit"
        >
          <el-option
            label="固定资产"
            value="Asset"
          />
          <el-option
            label="员工信息"
            value="Employee"
          />
          <el-option
            label="部门"
            value="Department"
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
        :label="$t('system.permission.data.dialog.status')"
        prop="isActive"
      >
        <el-switch
          v-model="formData.isActive"
          :active-text="$t('system.permission.data.status.enable')"
          :inactive-text="$t('system.permission.data.status.disable')"
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
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

interface Props {
  visible: boolean
  data?: any
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
  roleName: '',
  businessObjectName: '',
  permissionType: 'department',
  scopeExpression: '',
  isActive: true,
  description: ''
})

const rules: FormRules = {
  roleName: [{ required: true, message: t('system.permission.data.dialog.rolePlaceholder'), trigger: 'change' }],
  businessObjectName: [{ required: true, message: t('system.permission.data.dialog.objectPlaceholder'), trigger: 'change' }],
  permissionType: [{ required: true, message: t('system.permission.data.dialog.typePlaceholder'), trigger: 'change' }]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, props.data)
  } else if (val) {
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
    roleName: '',
    businessObjectName: '',
    permissionType: 'department',
    scopeExpression: '',
    isActive: true,
    description: ''
  }
  formRef.value?.clearValidate()
}

const handlePermissionTypeChange = () => {
  formData.value.scopeExpression = ''
}

const getScopePreview = () => {
  const previews: Record<string, string> = {
    'all': t('system.permission.data.types.all'),
    'department': t('system.permission.data.types.department'),
    'department_and_sub': t('system.permission.data.types.department_and_sub'),
    'self': t('system.permission.data.types.self')
  }
  return previews[formData.value.permissionType] || ''
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
      // TODO: Replace with actual API call
      // if (isEdit.value) {
      //   await dataPermissionApi.update(props.data.id, formData.value)
      // } else {
      //   await dataPermissionApi.create(formData.value)
      // }
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
