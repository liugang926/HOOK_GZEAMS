<template>
  <el-dialog
    :model-value="visible"
    :title="$t('system.permission.field.dialog.title')"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      label-width="120px"
    >
      <el-form-item :label="$t('system.permission.field.dialog.role')">
        <el-input
          v-model="formData.roleName"
          disabled
        />
      </el-form-item>

      <el-form-item :label="$t('system.permission.field.dialog.object')">
        <el-input
          v-model="formData.businessObjectName"
          disabled
        />
      </el-form-item>

      <el-form-item :label="$t('system.permission.field.dialog.field')">
        <el-input
          v-model="formData.fieldName"
          disabled
        />
      </el-form-item>

      <el-form-item :label="$t('system.permission.field.dialog.read')">
        <el-switch
          v-model="formData.canRead"
          :active-text="$t('system.permission.field.status.allow')"
          :inactive-text="$t('system.permission.field.status.deny')"
        />
      </el-form-item>

      <el-form-item :label="$t('system.permission.field.dialog.write')">
        <el-switch
          v-model="formData.canWrite"
          :active-text="$t('system.permission.field.status.allow')"
          :inactive-text="$t('system.permission.field.status.deny')"
        />
      </el-form-item>

      <el-form-item :label="$t('system.permission.field.dialog.visibility')">
        <el-switch
          v-model="formData.isVisible"
          :active-text="$t('system.permission.field.status.show')"
          :inactive-text="$t('system.permission.field.status.hide')"
        />
      </el-form-item>

      <el-form-item :label="$t('system.permission.field.dialog.description')">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
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
        {{ $t('common.actions.save') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { fieldPermissionApi, type FieldPermissionRecord } from '@/api/permissions'

const { t } = useI18n()

interface Props {
  visible: boolean
  data?: FieldPermissionDialogData | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

interface FieldPermissionDialogData {
  id: string
  roleName: string
  businessObjectName: string
  fieldName: string
  description?: string
  permissionType: FieldPermissionRecord['permissionType']
  maskRule?: string | null
  customMaskPattern?: string
}

const formData = ref({
  roleName: '',
  businessObjectName: '',
  fieldName: '',
  canRead: true,
  canWrite: false,
  isVisible: true,
  description: '',
  permissionType: 'read',
  maskRule: null as string | null,
  customMaskPattern: ''
})

const mapPermissionToFlags = (permissionType: FieldPermissionRecord['permissionType']) => {
  switch (permissionType) {
    case 'write':
      return { canRead: true, canWrite: true, isVisible: true }
    case 'hidden':
      return { canRead: false, canWrite: false, isVisible: false }
    case 'masked':
      return { canRead: true, canWrite: false, isVisible: true }
    case 'read':
    default:
      return { canRead: true, canWrite: false, isVisible: true }
  }
}

watch(() => props.visible, (val) => {
  if (!val) return

  if (props.data) {
    const flags = mapPermissionToFlags(props.data.permissionType)
    formData.value = {
      roleName: props.data.roleName || '',
      businessObjectName: props.data.businessObjectName || '',
      fieldName: props.data.fieldName || '',
      canRead: flags.canRead,
      canWrite: flags.canWrite,
      isVisible: flags.isVisible,
      description: props.data.description || '',
      permissionType: props.data.permissionType || 'read',
      maskRule: props.data.maskRule || null,
      customMaskPattern: props.data.customMaskPattern || ''
    }
    formRef.value?.clearValidate()
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const resolvePermissionType = () => {
  if (!formData.value.isVisible || (!formData.value.canRead && !formData.value.canWrite)) {
    return 'hidden'
  }

  if (formData.value.canWrite) {
    return 'write'
  }

  if (formData.value.canRead) {
    if (formData.value.permissionType === 'masked') {
      return 'masked'
    }
    return 'read'
  }

  return 'hidden'
}

const handleSubmit = async () => {
  if (!props.data?.id) {
    ElMessage.error(t('system.permission.field.messages.saveFailed'))
    return
  }

  submitting.value = true
  try {
    const permissionType = resolvePermissionType()

    await fieldPermissionApi.update(props.data.id, {
      permissionType,
      maskRule: permissionType === 'masked' ? formData.value.maskRule : null,
      customMaskPattern: permissionType === 'masked' ? formData.value.customMaskPattern : '',
      description: formData.value.description || ''
    })

    ElMessage.success(t('system.permission.field.messages.saveSuccess'))
    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error(t('system.permission.field.messages.saveFailed'))
  } finally {
    submitting.value = false
  }
}
</script>
