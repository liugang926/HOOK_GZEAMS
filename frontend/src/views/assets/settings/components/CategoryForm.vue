<template>
  <div class="category-form">
    <div class="form-header">
      <h3>{{ isEdit ? '编辑分类' : '新建分类' }}</h3>
      <div
        v-if="parentCategory"
        class="parent-info"
      >
        上级分类: {{ parentCategory.name }}
      </div>
    </div>

    <el-form
      ref="formRef"
      v-loading="loading"
      :model="form"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item
        label="分类编码"
        prop="code"
      >
        <el-input
          v-model="form.code"
          placeholder="请输入唯一编码"
        />
      </el-form-item>

      <el-form-item
        label="分类名称"
        prop="name"
      >
        <el-input
          v-model="form.name"
          placeholder="请输入分类名称"
        />
      </el-form-item>
      
      <el-divider content-position="left">
        折旧设置
      </el-divider>

      <el-form-item
        label="折旧方法"
        prop="depreciation_method"
      >
        <el-select
          v-model="form.depreciation_method"
          placeholder="请选择折旧方法"
          style="width: 100%"
        >
          <el-option
            label="年限平均法"
            value="straight_line"
          />
          <el-option
            label="双倍余额递减法"
            value="double_declining"
          />
          <el-option
            label="年数总和法"
            value="sum_of_years"
          />
          <el-option
            label="不计提折旧"
            value="none"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        label="预计使用年限"
        prop="useful_life"
      >
        <el-input-number
          v-model="form.useful_life"
          :min="0"
          :precision="0"
          style="width: 100%"
        >
          <template #append>
            月
          </template>
        </el-input-number>
        <div class="form-tip">
          请输入月数 (例如: 5年 = 60月)
        </div>
      </el-form-item>

      <el-form-item
        label="残值率"
        prop="salvage_rate"
      >
        <el-input-number
          v-model="form.salvage_rate"
          :min="0"
          :max="100"
          :precision="2"
          :step="0.1"
          style="width: 100%"
        /> 
        <div class="form-tip">
          % (例如: 5 表示 5%)
        </div>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存
        </el-button>
        <el-button @click="$emit('cancel')">
          取消
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { categoryApi } from '@/api/assets'

const props = defineProps<{
  modelValue?: any // Current category data for edit
  parentId?: string | null
  parentName?: string
}>()

const emit = defineEmits(['success', 'cancel'])

const formRef = ref()
const loading = ref(false)
const submitting = ref(false)

const form = reactive({
  id: null,
  code: '',
  name: '',
  parent_id: '',
  depreciation_method: 'straight_line',
  useful_life: 60,
  salvage_rate: 5
})

const rules = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  depreciation_method: [{ required: true, message: '请选择折旧方法', trigger: 'change' }]
}

const isEdit = computed(() => !!form.id)

const parentCategory = computed(() => {
  if (props.parentId) {
    return { id: props.parentId, name: props.parentName || 'Unknown' }
  }
  return null
})

// Watch for changes in props to update form
watch(() => props.modelValue, (val) => {
  if (val) {
    // Edit mode
    Object.keys(form).forEach(key => {
      if (val[key] !== undefined) {
        form[key] = val[key]
      }
    })
    // Ensure id is set
    form.id = val.id
    // Parent ID might come from val or prop, usually val.parent_id
  } else {
    // Reset for Create mode
    resetForm()
  }
}, { immediate: true })

watch(() => props.parentId, (val) => {
  if (!isEdit.value) {
    form.parent_id = val || ''
  }
})

function resetForm() {
  form.id = null
  form.code = ''
  form.name = ''
  form.parent_id = props.parentId || ''
  form.depreciation_method = 'straight_line'
  form.useful_life = 60
  form.salvage_rate = 5
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate()
  
  submitting.value = true
  try {
    const payload = { ...form }
    if (isEdit.value) {
      await categoryApi.update(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await categoryApi.create(payload)
      ElMessage.success('创建成功')
    }
    emit('success')
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.category-form {
  padding: 20px;
  max-width: 600px;
}

.form-header {
  margin-bottom: 24px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 16px;
}

.parent-info {
  margin-top: 8px;
  font-size: 14px;
  color: #606266;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: normal;
  margin-top: 4px;
}
</style>
