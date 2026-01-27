<!-- frontend/src/components/softwareLicenses/AllocationDialog.vue -->

<template>
  <el-dialog
    v-model="visible"
    :title="`分配许可证 - ${license?.softwareName}`"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="可用数量">
        <el-text>{{ license?.availableUnits }} / {{ license?.totalUnits }}</el-text>
      </el-form-item>

      <el-form-item
        label="资产"
        prop="asset"
      >
        <el-select
          v-model="formData.asset"
          filterable
          remote
          :remote-method="searchAssets"
          placeholder="搜索资产编码或名称"
          style="width: 100%"
          :loading="searching"
        >
          <el-option
            v-for="item in assetOptions"
            :key="item.id"
            :label="`${item.assetCode} - ${item.assetName}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="分配密钥">
        <el-input
          v-model="formData.allocationKey"
          type="password"
          show-password
          placeholder="可选，特定于此分配的密钥"
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="3"
          placeholder="分配备注"
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
        分配
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { licenseAllocationApi } from '@/api/softwareLicenses'
import { assetApi } from '@/api/assets'
import type { SoftwareLicense } from '@/types/softwareLicenses'

interface Props {
  modelValue: boolean
  license?: SoftwareLicense | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'allocated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const searching = ref(false)
const assetOptions = ref<any[]>([])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formData = ref({
  asset: '',
  allocationKey: '',
  notes: ''
})

const rules: FormRules = {
  asset: [
    { required: true, message: '请选择资产', trigger: 'change' }
  ]
}

const searchAssets = async (query: string) => {
  if (!query) return

  searching.value = true
  try {
    const response = await assetApi.list({ search: query, pageSize: 50 })
    assetOptions.value = response.data.results || []
  } catch (error) {
    console.error('Failed to search assets:', error)
  } finally {
    searching.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value || !props.license) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      await licenseAllocationApi.create({
        license: props.license.id,
        asset: formData.value.asset,
        allocationKey: formData.value.allocationKey || undefined,
        notes: formData.value.notes || undefined
      })
      ElMessage.success('分配成功')
      emit('allocated')
      handleClose()
    } catch (error: any) {
      ElMessage.error(error.message || '分配失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleClose = () => {
  formRef.value?.resetFields()
  formData.value = {
    asset: '',
    allocationKey: '',
    notes: ''
  }
  assetOptions.value = []
  visible.value = false
}
</script>
