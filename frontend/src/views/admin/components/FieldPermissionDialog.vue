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
        <el-select
          v-model="formData.roleName"
          disabled
        >
          <el-option
            label="管理员"
            value="admin"
          />
          <el-option
            label="普通用户"
            value="user"
          />
          <el-option
            label="访客"
            value="guest"
          />
        </el-select>
      </el-form-item>

      <el-form-item :label="$t('system.permission.field.dialog.object')">
        <el-select
          v-model="formData.businessObjectName"
          disabled
        >
          <el-option
            label="固定资产"
            value="Asset"
          />
          <el-option
            label="员工信息"
            value="Employee"
          />
        </el-select>
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

const formData = ref({
  roleName: '',
  businessObjectName: '',
  fieldName: '',
  canRead: true,
  canWrite: true,
  isVisible: true,
  description: ''
})

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, props.data)
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    // TODO: Replace with actual API call
    // await fieldPermissionApi.update(props.data.id, formData.value)
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
