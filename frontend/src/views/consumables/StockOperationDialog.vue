<template>
  <el-dialog
    :title="type === 'in' ? t('consumables.stockDialog.titleIn') : t('consumables.stockDialog.titleOut')"
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
        :label="t('consumables.stockDialog.fields.consumable')"
        prop="consumable_id"
      >
        <el-select
          v-model="form.consumable_id"
          filterable
          remote
          :remote-method="searchConsumables"
          :placeholder="t('consumables.stockDialog.placeholders.searchConsumable')"
          style="width: 100%"
          :loading="loading"
        >
          <el-option
            v-for="item in options"
            :key="item.id"
            :label="item.name + ' (' + item.code + ')'"
            :value="item.id"
          >
            <span style="float: left">{{ item.name }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px">{{ item.stock_quantity }} {{ item.unit }}</span>
          </el-option>
        </el-select>
      </el-form-item>
      <el-form-item
        :label="t('consumables.stockDialog.fields.quantity')"
        prop="quantity"
      >
        <el-input-number
          v-model="form.quantity"
          :min="1"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item
        :label="t('consumables.stockDialog.fields.remark')"
        prop="remark"
      >
        <el-input
          v-model="form.remark"
          type="textarea"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">
        {{ t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="submit"
      >
        {{ t('common.actions.confirm') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineEmits } from 'vue'
import { useI18n } from 'vue-i18n'
import { stockIn, stockOut, getConsumables } from '@/api/consumables'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean,
  type: {
    type: String,
    default: 'in'
  }
})
const emit = defineEmits(['update:modelValue', 'success'])
const { t } = useI18n()

const formRef = ref()
const submitting = ref(false)
const loading = ref(false)
const options = ref<any[]>([])

const form = reactive({
  consumable_id: undefined,
  quantity: 1,
  remark: ''
})

const rules = {
  consumable_id: [{ required: true, message: t('common.validation.requiredWithField', { field: t('consumables.stockDialog.fields.consumable') }), trigger: 'change' }],
  quantity: [{ required: true, message: t('common.validation.requiredWithField', { field: t('consumables.stockDialog.fields.quantity') }), trigger: 'blur' }]
}

const searchConsumables = async (query: string) => {
  if (!query) {
    options.value = []
    return
  }

  loading.value = true
  try {
    const res = await getConsumables({ search: query })
    options.value = res.results || []
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
  form.consumable_id = undefined
  form.quantity = 1
  form.remark = ''
  options.value = []
}

const submit = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = { ...form, type: props.type as 'in' | 'out' }
    if (props.type === 'in') {
      await stockIn(payload)
    } else {
      await stockOut(payload)
    }
    ElMessage.success(t('consumables.stockDialog.messages.operationSuccess'))
    emit('success')
    handleClose()
  } catch (e: any) {
    ElMessage.error(e.message || t('consumables.stockDialog.messages.operationFailed'))
  } finally {
    submitting.value = false
  }
}
</script>
