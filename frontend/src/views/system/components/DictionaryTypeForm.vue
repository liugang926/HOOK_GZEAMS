<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑字典类型' : '新建字典类型'"
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
        label="字典编码"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          placeholder="请输入字典编码（英文，如：ASSET_STATUS）"
          :disabled="isEdit"
        />
        <div class="form-tip">
          编码必须唯一，建议使用大写字母和下划线
        </div>
      </el-form-item>

      <el-form-item
        label="字典名称"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          placeholder="请输入字典名称（中文）"
        />
      </el-form-item>

      <el-form-item
        label="英文名称"
        prop="name_en"
      >
        <el-input
          v-model="formData.name_en"
          placeholder="请输入英文名称"
        />
      </el-form-item>

      <el-form-item
        label="排序号"
        prop="sort_order"
      >
        <el-input-number
          v-model="formData.sort_order"
          :min="0"
          :max="9999"
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
          placeholder="请输入字典类型描述"
        />
      </el-form-item>

      <el-form-item
        label="状态"
        prop="is_active"
      >
        <el-switch
          v-model="formData.is_active"
          active-text="启用"
          inactive-text="禁用"
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
import type { DictionaryType } from '@/api/system'
import { dictionaryTypeApi } from '@/api/system'

interface Props {
  visible: boolean
  data?: DictionaryType | null
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
  description: '',
  sort_order: 0,
  is_active: true
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入字典编码', trigger: 'blur' },
    { pattern: /^[A-Z_][A-Z0-9_]*$/, message: '编码只能包含大写字母、数字和下划线，且必须以字母或下划线开头', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入字典名称', trigger: 'blur' }]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, {
      code: props.data.code || '',
      name: props.data.name || '',
      name_en: props.data.name_en || '',
      description: props.data.description || '',
      sort_order: props.data.sort_order || 0,
      is_active: props.data.is_active ?? true
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
    description: '',
    sort_order: 0,
    is_active: true
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
        await dictionaryTypeApi.update(props.data!.id, formData.value)
      } else {
        await dictionaryTypeApi.create(formData.value)
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
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
