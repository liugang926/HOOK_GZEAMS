<template>
  <el-dialog
    :title="id ? '编辑耗材' : '新建耗材'"
    :model-value="modelValue"
    width="500px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item
        label="名称"
        prop="name"
      >
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item
        label="编码"
        prop="code"
      >
        <el-input v-model="form.code" />
      </el-form-item>
      <el-form-item
        label="类别"
        prop="category"
      >
        <el-select
          v-model="form.category"
          style="width: 100%"
        >
          <el-option
            label="办公用品"
            value="office"
          />
          <el-option
            label="IT耗材"
            value="it"
          />
        </el-select>
      </el-form-item>
      <el-form-item
        label="规格"
        prop="spec"
      >
        <el-input v-model="form.spec" />
      </el-form-item>
      <el-form-item
        label="单位"
        prop="unit"
      >
        <el-input v-model="form.unit" />
      </el-form-item>
      <el-form-item
        label="预警阈值"
        prop="warning_quantity"
      >
        <el-input-number
          v-model="form.warning_quantity"
          :min="0"
        />
      </el-form-item>
      <el-form-item
        label="描述"
        prop="description"
      >
        <el-input
          v-model="form.description"
          type="textarea"
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
        @click="submit"
      >
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, defineProps, defineEmits } from 'vue'
import { createConsumable, updateConsumable, getConsumable } from '@/api/consumables'
import { ElMessage } from 'element-plus'

const props = defineProps({
    modelValue: Boolean,
    id: Number
})
const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const submitting = ref(false)
const form = reactive({
    name: '',
    code: '',
    category: 'office',
    spec: '',
    unit: '个',
    warning_quantity: 10,
    description: ''
})

const rules = {
    name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
    code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
    unit: [{ required: true, message: '请输入单位', trigger: 'blur' }]
}

watch(() => props.modelValue, async (val) => {
    if (val) {
        if (props.id) {
            try {
                const res = await getConsumable(props.id)
                Object.assign(form, res)
            } catch (e) {
                console.error(e)
            }
        } else {
            // Reset
            Object.assign(form, {
                name: '',
                code: '',
                category: 'office',
                spec: '',
                unit: '个',
                warning_quantity: 10,
                description: ''
            })
        }
    }
})

const handleClose = () => {
    emit('update:modelValue', false)
}

const submit = async () => {
    if (!formRef.value) return
    await formRef.value.validate(async (valid: boolean) => {
        if (valid) {
            submitting.value = true
            try {
                if (props.id) {
                    await updateConsumable(props.id, form)
                } else {
                    await createConsumable(form)
                }
                ElMessage.success('保存成功')
                emit('success')
                handleClose()
            } catch (e) {
                ElMessage.error('保存失败')
                console.error(e)
            } finally {
                submitting.value = false
            }
        }
    })
}
</script>
