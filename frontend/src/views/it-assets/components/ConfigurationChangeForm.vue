<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? 'Edit Configuration Change' : 'Add Configuration Change'"
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
        label="Field Name"
        prop="field_name"
      >
        <el-select
          v-model="formData.field_name"
          placeholder="Select field"
          allow-create
          filterable
          style="width: 100%"
        >
          <el-option
            label="CPU Model"
            value="cpu_model"
          />
          <el-option
            label="CPU Cores"
            value="cpu_cores"
          />
          <el-option
            label="CPU Threads"
            value="cpu_threads"
          />
          <el-option
            label="RAM Capacity"
            value="ram_capacity"
          />
          <el-option
            label="RAM Type"
            value="ram_type"
          />
          <el-option
            label="Disk Type"
            value="disk_type"
          />
          <el-option
            label="Disk Capacity"
            value="disk_capacity"
          />
          <el-option
            label="GPU Model"
            value="gpu_model"
          />
          <el-option
            label="MAC Address"
            value="mac_address"
          />
          <el-option
            label="IP Address"
            value="ip_address"
          />
          <el-option
            label="Hostname"
            value="hostname"
          />
          <el-option
            label="OS Name"
            value="os_name"
          />
          <el-option
            label="OS Version"
            value="os_version"
          />
          <el-option
            label="Antivirus Software"
            value="antivirus_software"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        label="Old Value"
        prop="old_value"
      >
        <el-input
          v-model="formData.old_value"
          type="textarea"
          :rows="2"
          placeholder="Previous value"
        />
      </el-form-item>

      <el-form-item
        label="New Value"
        prop="new_value"
      >
        <el-input
          v-model="formData.new_value"
          type="textarea"
          :rows="2"
          placeholder="New value"
        />
      </el-form-item>

      <el-form-item
        label="Change Date"
        prop="change_date"
      >
        <el-date-picker
          v-model="formData.change_date"
          type="date"
          placeholder="Select date"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item
        label="Reason"
        prop="change_reason"
      >
        <el-input
          v-model="formData.change_reason"
          type="textarea"
          :rows="3"
          placeholder="Explain why this change was made"
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
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { ConfigurationChange } from '@/api/itAssets'
import { configurationChangeApi } from '@/api/itAssets'

interface Props {
  visible: boolean
  data?: ConfigurationChange | null
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
  field_name: '',
  old_value: '',
  new_value: '',
  change_date: '',
  change_reason: ''
})

const rules: FormRules = {
  asset: [
    { required: true, message: 'Please select asset', trigger: 'change' }
  ],
  field_name: [
    { required: true, message: 'Please enter field name', trigger: 'blur' }
  ],
  change_date: [
    { required: true, message: 'Please select change date', trigger: 'change' }
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
      field_name: props.data.field_name || '',
      old_value: props.data.old_value || '',
      new_value: props.data.new_value || '',
      change_date: props.data.change_date || '',
      change_reason: props.data.change_reason || ''
    })
  } else if (val) {
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
    asset: '',
    field_name: '',
    old_value: '',
    new_value: '',
    change_date: '',
    change_reason: ''
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
        await configurationChangeApi.update(props.data!.id, formData.value)
      } else {
        await configurationChangeApi.create(formData.value)
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
