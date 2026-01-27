<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑业务对象' : '新建业务对象'"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-tabs v-model="activeTab">
      <el-tab-pane
        label="Basic Info"
        name="basic"
      >
        <el-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-width="120px"
        >
          <el-form-item
            label="对象编码"
            prop="code"
          >
            <el-input
              v-model="formData.code"
              placeholder="请输入对象编码（英文，如：Asset）"
              :disabled="isEdit"
            />
          </el-form-item>

          <el-form-item
            label="对象名称"
            prop="name"
          >
            <el-input
              v-model="formData.name"
              placeholder="请输入对象名称（中文，如：固定资产）"
            />
          </el-form-item>

          <el-form-item
            label="描述"
            prop="description"
          >
            <el-input
              v-model="formData.description"
              type="textarea"
              :rows="3"
              placeholder="请输入对象描述"
            />
          </el-form-item>

          <el-form-item
            label="数据表名"
            prop="tableName"
          >
            <el-input
              v-model="formData.tableName"
              placeholder="数据库表名（如：assets_asset）"
            />
          </el-form-item>

          <el-form-item label="主键字段">
            <el-input
              v-model="formData.pkField"
              placeholder="默认为 id"
            />
          </el-form-item>

          <el-form-item label="启用工作流">
            <el-switch v-model="formData.enableWorkflow" />
            <span class="form-tip">启用后可配置审批流程</span>
          </el-form-item>

          <el-form-item label="启用版本控制">
            <el-switch v-model="formData.enableVersion" />
            <span class="form-tip">启用后记录数据变更历史</span>
          </el-form-item>

          <el-form-item label="启用软删除">
            <el-switch v-model="formData.enableSoftDelete" />
            <span class="form-tip">删除数据时不物理删除</span>
          </el-form-item>

          <el-form-item label="是否系统对象">
            <el-switch
              v-model="formData.isSystem"
              :disabled="isEdit"
            />
            <span class="form-tip">系统对象不可删除</span>
          </el-form-item>
        </el-form>
      </el-tab-pane>

      <el-tab-pane
        label="Custom Actions"
        name="actions"
      >
        <div class="info-box">
          <p>Define custom actions (buttons/triggers) for this object.</p>
          <p>Example: [{"code": "approve", "label": "Approve", "type": "api"}]</p>
        </div>
        <el-input
          type="textarea"
          :rows="15"
          :model-value="JSON.stringify(formData.actions || [], null, 2)"
          placeholder="[{&quot;code&quot;: &quot;...&quot;, &quot;label&quot;: &quot;...&quot;}]"
          @change="(val) => {
            try {
              formData.actions = JSON.parse(val)
            } catch (e) {
              // Ignore parse error
            }
          }"
        />
      </el-tab-pane>
    </el-tabs>

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
const activeTab = ref('basic')

const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  code: '',
  name: '',
  description: '',
  tableName: '',
  pkField: 'id',
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  enableSoftDelete: true,
  isSystem: false,
  actions: []
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入对象编码', trigger: 'blur' },
    { pattern: /^[A-Z][a-zA-Z0-9]*$/, message: '编码必须以大写字母开头，只能包含字母和数字', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入对象名称', trigger: 'blur' }
  ],
  tableName: [
    { required: true, message: '请输入数据表名', trigger: 'blur' }
  ]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    // Edit mode - populate form
    Object.assign(formData.value, props.data)
  } else if (val) {
    // Create mode - reset form
    formRef.value?.resetFields()
    formData.value = {
      code: '',
      name: '',
      description: '',
      tableName: '',
      pkField: 'id',
      enableWorkflow: false,
      enableVersion: false,
      enableSoftDelete: true,
      enableSoftDelete: true,
      isSystem: false,
      actions: []
    }
  }
})

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
      if (isEdit.value) {
        // await businessObjectApi.update(props.data.id, formData.value)
      } else {
        // await businessObjectApi.create(formData.value)
      }
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

<style scoped>
.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
