<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑数据权限规则' : '新增数据权限规则'"
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
        label="角色"
        prop="roleName"
      >
        <el-select
          v-model="formData.roleName"
          placeholder="请选择角色"
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
        label="业务对象"
        prop="businessObjectName"
      >
        <el-select
          v-model="formData.businessObjectName"
          placeholder="请选择业务对象"
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
        label="权限类型"
        prop="permissionType"
      >
        <el-select
          v-model="formData.permissionType"
          placeholder="请选择权限类型"
          @change="handlePermissionTypeChange"
        >
          <el-option
            label="全部数据"
            value="all"
          />
          <el-option
            label="本部门"
            value="department"
          />
          <el-option
            label="本部门及子部门"
            value="department_and_sub"
          />
          <el-option
            label="仅本人"
            value="self"
          />
          <el-option
            label="自定义"
            value="custom"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        v-if="formData.permissionType === 'custom'"
        label="权限表达式"
        prop="scopeExpression"
      >
        <el-input
          v-model="formData.scopeExpression"
          type="textarea"
          :rows="3"
          placeholder="自定义权限表达式，如: department_id in (1, 2, 3)"
        />
      </el-form-item>

      <el-form-item
        v-else
        label="权限范围"
      >
        <el-input
          :value="getScopePreview()"
          disabled
        />
      </el-form-item>

      <el-form-item
        label="状态"
        prop="isActive"
      >
        <el-switch
          v-model="formData.isActive"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>

      <el-form-item
        label="说明"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          placeholder="请输入权限规则说明"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

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
  roleName: [{ required: true, message: '请选择角色', trigger: 'change' }],
  businessObjectName: [{ required: true, message: '请选择业务对象', trigger: 'change' }],
  permissionType: [{ required: true, message: '请选择权限类型', trigger: 'change' }]
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
    'all': '全部数据',
    'department': '本部门数据',
    'department_and_sub': '本部门及子部门数据',
    'self': '仅本人数据'
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
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitting.value = false
    }
  })
}
</script>
