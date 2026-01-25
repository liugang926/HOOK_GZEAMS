<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑字段' : '添加字段'"
    width="700px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="字段编码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="请输入字段编码（英文，如：userName）"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item label="字段名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入字段名称（中文，如：用户名）"
        />
      </el-form-item>

      <el-form-item label="字段类型" prop="fieldType">
        <el-select
          v-model="formData.fieldType"
          placeholder="请选择字段类型"
          @change="handleFieldTypeChange"
        >
          <el-option label="单行文本" value="text" />
          <el-option label="多行文本" value="textarea" />
          <el-option label="数字" value="number" />
          <el-option label="货币" value="currency" />
          <el-option label="日期" value="date" />
          <el-option label="日期时间" value="datetime" />
          <el-option label="下拉选择" value="select" />
          <el-option label="多选" value="multi_select" />
          <el-option label="单选" value="radio" />
          <el-option label="复选框" value="checkbox" />
          <el-option label="开关" value="switch" />
          <el-option label="用户选择" value="user" />
          <el-option label="部门选择" value="dept" />
          <el-option label="资产选择" value="asset" />
          <el-option label="关联引用" value="reference" />
          <el-option label="子表" value="subtable" />
          <el-option label="文件上传" value="file" />
          <el-option label="图片上传" value="image" />
          <el-option label="计算公式" value="formula" />
          <el-option label="自动编号" value="auto_number" />
        </el-select>
      </el-form-item>

      <!-- Reference target for reference type -->
      <el-form-item
        v-if="formData.fieldType === 'reference' || formData.fieldType === 'subtable'"
        label="关联对象"
        prop="referenceObject"
      >
        <el-select
          v-model="formData.referenceObject"
          placeholder="请选择关联的业务对象"
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
        v-if="['select', 'multi_select', 'radio', 'checkbox'].includes(formData.fieldType)"
        label="选项配置"
      >
        <div class="options-editor">
          <div
            v-for="(option, index) in formData.options"
            :key="index"
            class="option-item"
          >
            <el-input
              v-model="option.label"
              placeholder="选项名称"
              style="width: 150px"
            />
            <el-input
              v-model="option.value"
              placeholder="选项值"
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
              删除
            </el-button>
          </div>
          <el-button link type="primary" @click="addOption">
            + 添加选项
          </el-button>
        </div>
      </el-form-item>

      <!-- Formula expression -->
      <el-form-item
        v-if="formData.fieldType === 'formula'"
        label="公式表达式"
      >
        <el-input
          v-model="formData.formulaExpression"
          type="textarea"
          :rows="2"
          placeholder="如: {quantity} * {price}"
        />
        <div class="form-tip">使用 {字段编码} 引用其他字段</div>
      </el-form-item>

      <el-form-item label="排序号">
        <el-input-number v-model="formData.sortOrder" :min="0" :max="9999" />
      </el-form-item>

      <el-form-item label="默认值">
        <el-input
          v-model="formData.defaultValue"
          :placeholder="getDefaultValuePlaceholder()"
        />
      </el-form-item>

      <el-form-item label="占位提示">
        <el-input
          v-model="formData.placeholder"
          placeholder="输入框的占位提示文字"
        />
      </el-form-item>

      <el-form-item label="描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          placeholder="字段描述说明"
        />
      </el-form-item>

      <el-form-item label="是否必填">
        <el-switch v-model="formData.isRequired" />
      </el-form-item>

      <el-form-item label="是否只读">
        <el-switch v-model="formData.isReadonly" />
      </el-form-item>

      <el-form-item label="是否唯一">
        <el-switch v-model="formData.isUnique" />
      </el-form-item>

      <el-form-item label="是否列表显示">
        <el-switch v-model="formData.showInList" />
        <span class="form-tip">在列表页默认显示</span>
      </el-form-item>

      <el-form-item label="列表宽度">
        <el-input-number
          v-model="formData.listWidth"
          :min="50"
          :max="500"
          :step="10"
        />
        <span class="form-tip">列表页列宽度（像素）</span>
      </el-form-item>

      <!-- Validation rules -->
      <el-form-item
        v-if="['text', 'textarea'].includes(formData.fieldType)"
        label="最大长度"
      >
        <el-input-number v-model="formData.maxLength" :min="1" :max="10000" />
      </el-form-item>

      <el-form-item
        v-if="['number', 'currency'].includes(formData.fieldType)"
        label="数值范围"
      >
        <el-input-number
          v-model="formData.minValue"
          placeholder="最小值"
          style="width: 120px"
        />
        <span style="margin: 0 10px">-</span>
        <el-input-number
          v-model="formData.maxValue"
          placeholder="最大值"
          style="width: 120px"
        />
      </el-form-item>

      <el-form-item
        v-if="formData.fieldType === 'number'"
        label="小数位数"
      >
        <el-input-number v-model="formData.decimalPlaces" :min="0" :max="6" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ isEdit ? '保存' : '添加' }}
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

// Mock business objects for reference
const businessObjects = ref([
  { code: 'Asset', name: '固定资产' },
  { code: 'Employee', name: '员工信息' },
  { code: 'Department', name: '部门' }
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

const rules: FormRules = {
  code: [
    { required: true, message: '请输入字段编码', trigger: 'blur' },
    { pattern: /^[a-z][a-zA-Z0-9]*$/, message: '编码必须以小写字母开头', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入字段名称', trigger: 'blur' }
  ],
  fieldType: [
    { required: true, message: '请选择字段类型', trigger: 'change' }
  ],
  referenceObject: [
    { required: true, message: '请选择关联对象', trigger: 'change' }
  ]
}

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
    text: '默认文本值',
    number: '默认数字值',
    date: '如: 2024-01-01',
    switch: 'true/false',
    select: '选项值'
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

  await formRef.value.validate(async (valid) => {
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

      ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
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
