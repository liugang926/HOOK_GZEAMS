<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? 'Edit Maintenance Record' : 'Add Maintenance Record'"
    width="700px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
    >
      <el-form-item
        label="Asset"
        prop="asset"
      >
        <el-select
          v-model="formData.asset"
          placeholder="Select asset"
          filterable
          remote
          :remote-method="searchAssets"
          :loading="assetLoading"
          style="width: 100%"
        >
          <el-option
            v-for="item in assetOptions"
            :key="item.id"
            :label="`${item.asset_code} - ${item.asset_name}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        label="Maintenance Type"
        prop="maintenance_type"
      >
        <el-select
          v-model="formData.maintenance_type"
          placeholder="Select type"
          style="width: 100%"
        >
          <el-option
            label="Preventive"
            value="preventive"
          />
          <el-option
            label="Corrective"
            value="corrective"
          />
          <el-option
            label="Upgrade"
            value="upgrade"
          />
          <el-option
            label="Replacement"
            value="replacement"
          />
          <el-option
            label="Inspection"
            value="inspection"
          />
          <el-option
            label="Cleaning"
            value="cleaning"
          />
          <el-option
            label="Other"
            value="other"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        label="Title"
        prop="title"
      >
        <el-input
          v-model="formData.title"
          placeholder="Brief title of the maintenance activity"
        />
      </el-form-item>

      <el-form-item
        label="Description"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="4"
          placeholder="Detailed description of work performed"
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item
            label="Maintenance Date"
            prop="maintenance_date"
          >
            <el-date-picker
              v-model="formData.maintenance_date"
              type="date"
              placeholder="Select date"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            label="Cost"
            prop="cost"
          >
            <el-input-number
              v-model="formData.cost"
              :min="0"
              :precision="2"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item
        label="Vendor"
        prop="vendor"
      >
        <el-input
          v-model="formData.vendor"
          placeholder="External vendor (if applicable)"
        />
      </el-form-item>

      <el-form-item
        label="Notes"
        prop="notes"
      >
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="2"
          placeholder="Additional notes"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        Cancel
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? 'Save' : 'Add' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { ITMaintenanceRecord } from '@/api/itAssets'
import { itMaintenanceApi } from '@/api/itAssets'

interface Props {
  visible: boolean
  data?: ITMaintenanceRecord | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const assetLoading = ref(false)
const assetOptions = ref<any[]>([])

const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  asset: '',
  maintenance_type: 'preventive' as 'preventive' | 'corrective' | 'upgrade' | 'replacement' | 'inspection' | 'cleaning' | 'other',
  title: '',
  description: '',
  maintenance_date: '',
  cost: undefined as number | undefined,
  vendor: '',
  notes: ''
})

const rules: FormRules = {
  asset: [
    { required: true, message: 'Please select asset', trigger: 'change' }
  ],
  maintenance_type: [
    { required: true, message: 'Please select maintenance type', trigger: 'change' }
  ],
  title: [
    { required: true, message: 'Please enter title', trigger: 'blur' }
  ],
  maintenance_date: [
    { required: true, message: 'Please select maintenance date', trigger: 'change' }
  ]
}

const searchAssets = async (query: string) => {
  if (!query) return
  assetLoading.value = true
  try {
    const res = await fetch(`/api/assets/?search=${query}&page_size=20`).then(r => r.json())
    assetOptions.value = res.results || []
  } catch (error) {
    assetOptions.value = []
  } finally {
    assetLoading.value = false
  }
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    if (props.data.asset_code) {
      searchAssets(props.data.asset_code)
    }
    Object.assign(formData.value, {
      asset: props.data.asset || '',
      maintenance_type: props.data.maintenance_type || 'preventive',
      title: props.data.title || '',
      description: props.data.description || '',
      maintenance_date: props.data.maintenance_date || '',
      cost: props.data.cost,
      vendor: props.data.vendor || '',
      notes: props.data.notes || ''
    })
  } else if (val) {
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
    asset: '',
    maintenance_type: 'preventive',
    title: '',
    description: '',
    maintenance_date: '',
    cost: undefined,
    vendor: '',
    notes: ''
  }
  assetOptions.value = []
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
        await itMaintenanceApi.update(props.data!.id, formData.value)
      } else {
        await itMaintenanceApi.create(formData.value)
      }
      ElMessage.success(isEdit.value ? 'Updated successfully' : 'Added successfully')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('Operation failed')
    } finally {
      submitting.value = false
    }
  })
}
</script>
