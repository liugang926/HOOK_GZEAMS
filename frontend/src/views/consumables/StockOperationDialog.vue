<template>
  <el-dialog
    :title="type === 'in' ? '耗材入库' : '领用出库'"
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
        label="耗材"
        prop="consumable_id"
      >
        <el-select
          v-model="form.consumable_id"
          filterable
          remote
          :remote-method="searchConsumables"
          placeholder="搜索耗材"
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
        label="数量"
        prop="quantity"
      >
        <el-input-number
          v-model="form.quantity"
          :min="1"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item
        label="备注"
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
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="submit"
      >
        确认
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, defineProps, defineEmits } from 'vue'
import { stockIn, stockOut, getConsumables } from '@/api/consumables'
import { ElMessage } from 'element-plus'

const props = defineProps({
    modelValue: Boolean,
    type: {
        type: String,
        default: 'in' // 'in' or 'out'
    }
})
const emit = defineEmits(['update:modelValue', 'success'])

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
    consumable_id: [{ required: true, message: '请选择耗材', trigger: 'change' }],
    quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }]
}

const searchConsumables = async (query: string) => {
    if (query) {
        loading.value = true
        try {
            const res = await getConsumables({ search: query })
            options.value = res.results || res.items || []
        } finally {
            loading.value = false
        }
    } else {
        options.value = []
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
    await formRef.value.validate(async (valid: boolean) => {
        if (valid) {
            submitting.value = true
            try {
                const payload = { ...form, type: props.type as 'in' | 'out' }
                if (props.type === 'in') {
                    await stockIn(payload)
                } else {
                    await stockOut(payload)
                }
                ElMessage.success('操作成功')
                emit('success')
                handleClose()
            } catch (e: any) {
                ElMessage.error(e.message || '操作失败')
            } finally {
                submitting.value = false
            }
        }
    })
}
</script>
