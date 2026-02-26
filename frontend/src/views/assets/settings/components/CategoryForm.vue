<template>
  <div class="category-form">
    <div class="form-header">
      <h3>{{ isEdit ? t('assets.category.edit') : t('assets.category.create') }}</h3>
      <div
        v-if="parentCategory"
        class="parent-info"
      >
        {{ t('assets.category.parent') }}: {{ parentCategory.name }}
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
        :label="t('assets.category.code')"
        prop="code"
      >
        <el-input
          v-model="form.code"
          :placeholder="t('assets.category.enterCode')"
        />
      </el-form-item>

      <el-form-item
        :label="t('assets.category.name')"
        prop="name"
      >
        <el-input
          v-model="form.name"
          :placeholder="t('assets.category.enterName')"
        />
      </el-form-item>

      <el-divider content-position="left">
        {{ t('assets.category.depreciation') }}
      </el-divider>

      <el-form-item
        :label="t('assets.category.method')"
        prop="depreciation_method"
      >
        <el-select
          v-model="form.depreciation_method"
          :placeholder="t('assets.category.selectMethod')"
          style="width: 100%"
        >
          <el-option
            :label="t('assets.depreciation.straightLine')"
            value="straight_line"
          />
          <el-option
            :label="t('assets.depreciation.doubleDeclining')"
            value="double_declining"
          />
          <el-option
            :label="t('assets.depreciation.sumOfYears')"
            value="sum_of_years"
          />
          <el-option
            :label="t('assets.depreciation.noDepreciation')"
            value="none"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="t('assets.category.usefulLife')"
        prop="useful_life"
      >
        <el-input-number
          v-model="form.useful_life"
          :min="0"
          :precision="0"
          style="width: 100%"
        >
          <template #append>
            {{ t('assets.category.months') }}
          </template>
        </el-input-number>
        <div class="form-tip">
          {{ t('assets.category.usefulLifeHint') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="t('assets.category.salvageRate')"
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
          {{ t('common.actions.save') }}
        </el-button>
        <el-button @click="$emit('cancel')">
          {{ t('common.actions.cancel') }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { categoryApi } from '@/api/assets'

const { t } = useI18n()

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
  code: [{ required: true, message: t('assets.category.enterCode'), trigger: 'blur' }],
  name: [{ required: true, message: t('assets.category.enterName'), trigger: 'blur' }],
  depreciation_method: [{ required: true, message: t('assets.category.selectMethod'), trigger: 'change' }]
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
      ElMessage.success(t('common.messages.updateSuccess'))
    } else {
      await categoryApi.create(payload)
      ElMessage.success(t('common.messages.createSuccess'))
    }
    emit('success')
  } catch (error: any) {
    ElMessage.error(error.message || t('common.messages.operationFailed'))
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
