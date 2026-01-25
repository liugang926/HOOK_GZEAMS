<template>
  <el-dialog
    :model-value="visible"
    title="编辑字段权限"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      label-width="120px"
    >
      <el-form-item label="角色">
        <el-select v-model="formData.roleName" disabled>
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
          <el-option label="访客" value="guest" />
        </el-select>
      </el-form-item>

      <el-form-item label="业务对象">
        <el-select v-model="formData.businessObjectName" disabled>
          <el-option label="固定资产" value="Asset" />
          <el-option label="员工信息" value="Employee" />
        </el-select>
      </el-form-item>

      <el-form-item label="字段名称">
        <el-input v-model="formData.fieldName" disabled />
      </el-form-item>

      <el-form-item label="读取权限">
        <el-switch v-model="formData.canRead" active-text="允许" inactive-text="禁止" />
      </el-form-item>

      <el-form-item label="写入权限">
        <el-switch v-model="formData.canWrite" active-text="允许" inactive-text="禁止" />
      </el-form-item>

      <el-form-item label="可见性">
        <el-switch v-model="formData.isVisible" active-text="显示" inactive-text="隐藏" />
      </el-form-item>

      <el-form-item label="说明">
        <el-input v-model="formData.description" type="textarea" :rows="2" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'

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
    ElMessage.success('保存成功')
    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}
</script>
