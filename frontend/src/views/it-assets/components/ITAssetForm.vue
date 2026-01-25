<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? 'Edit IT Asset Info' : 'Add IT Asset Info'"
    width="800px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="160px"
    >
      <el-divider content-position="left">Hardware Configuration</el-divider>

      <el-form-item label="Asset" prop="asset">
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

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="CPU Model" prop="cpu_model">
            <el-input v-model="formData.cpu_model" placeholder="e.g., Intel Core i7-12700K" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="CPU Cores" prop="cpu_cores">
            <el-input-number v-model="formData.cpu_cores" :min="1" :max="128" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="CPU Threads" prop="cpu_threads">
            <el-input-number v-model="formData.cpu_threads" :min="1" :max="256" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="RAM Capacity (GB)" prop="ram_capacity">
            <el-input-number v-model="formData.ram_capacity" :min="1" :max="1024" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="RAM Type" prop="ram_type">
            <el-select v-model="formData.ram_type" placeholder="Select type" style="width: 100%">
              <el-option label="DDR3" value="DDR3" />
              <el-option label="DDR4" value="DDR4" />
              <el-option label="DDR5" value="DDR5" />
              <el-option label="LPDDR3" value="LPDDR3" />
              <el-option label="LPDDR4" value="LPDDR4" />
              <el-option label="LPDDR5" value="LPDDR5" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="RAM Slots" prop="ram_slots">
            <el-input-number v-model="formData.ram_slots" :min="1" :max="16" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="Disk Type" prop="disk_type">
            <el-select v-model="formData.disk_type" placeholder="Select type" style="width: 100%">
              <el-option label="HDD" value="HDD" />
              <el-option label="SSD" value="SSD" />
              <el-option label="NVMe" value="NVMe" />
              <el-option label="SATA" value="SATA" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Disk Capacity (GB)" prop="disk_capacity">
            <el-input-number v-model="formData.disk_capacity" :min="1" :max="10240" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="Disk Count" prop="disk_count">
            <el-input-number v-model="formData.disk_count" :min="1" :max="10" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="16">
          <el-form-item label="GPU Model" prop="gpu_model">
            <el-input v-model="formData.gpu_model" placeholder="e.g., NVIDIA GeForce RTX 3080" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="GPU Memory (MB)" prop="gpu_memory">
            <el-input-number v-model="formData.gpu_memory" :min="1" :max="48144" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">Network Information</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="MAC Address" prop="mac_address">
            <el-input v-model="formData.mac_address" placeholder="XX:XX:XX:XX:XX:XX" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="IP Address" prop="ip_address">
            <el-input v-model="formData.ip_address" placeholder="192.168.1.1" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="Hostname" prop="hostname">
        <el-input v-model="formData.hostname" placeholder="e.g., PC-DESKTOP-001" />
      </el-form-item>

      <el-divider content-position="left">Operating System</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="OS Name" prop="os_name">
            <el-select v-model="formData.os_name" placeholder="Select OS" allow-create filterable style="width: 100%">
              <el-option label="Windows" value="Windows" />
              <el-option label="macOS" value="macOS" />
              <el-option label="Linux" value="Linux" />
              <el-option label="Ubuntu" value="Ubuntu" />
              <el-option label="CentOS" value="CentOS" />
              <el-option label="Debian" value="Debian" />
              <el-option label="Red Hat" value="Red Hat" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="OS Version" prop="os_version">
            <el-input v-model="formData.os_version" placeholder="e.g., 11, 22.04, 10.0.19043" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="OS Architecture" prop="os_architecture">
            <el-select v-model="formData.os_architecture" placeholder="Select architecture" style="width: 100%">
              <el-option label="x64" value="x64" />
              <el-option label="x86" value="x86" />
              <el-option label="ARM64" value="ARM64" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="OS License Key" prop="os_license_key">
            <el-input v-model="formData.os_license_key" placeholder="XXXXX-XXXXX-XXXXX-XXXXX" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">Security</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="Disk Encrypted" prop="disk_encrypted">
            <el-switch
              v-model="formData.disk_encrypted"
              active-text="Yes"
              inactive-text="No"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="Antivirus Enabled" prop="antivirus_enabled">
            <el-switch
              v-model="formData.antivirus_enabled"
              active-text="Yes"
              inactive-text="No"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="Antivirus Software" prop="antivirus_software">
        <el-input v-model="formData.antivirus_software" placeholder="e.g., Windows Defender, McAfee, Norton" />
      </el-form-item>

      <el-divider content-position="left">Active Directory</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="AD Domain" prop="ad_domain">
            <el-input v-model="formData.ad_domain" placeholder="e.g., corp.local" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="AD Computer Name" prop="ad_computer_name">
            <el-input v-model="formData.ad_computer_name" placeholder="e.g., DESKTOP-001" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">Cancel</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ isEdit ? 'Save' : 'Add' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { ITAssetInfo } from '@/api/itAssets'
import { itAssetInfoApi } from '@/api/itAssets'

// Asset search - using the assets API
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

interface Props {
  visible: boolean
  data?: ITAssetInfo | null
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
  cpu_model: '',
  cpu_cores: undefined as number | undefined,
  cpu_threads: undefined as number | undefined,
  ram_capacity: undefined as number | undefined,
  ram_type: '',
  ram_slots: undefined as number | undefined,
  disk_type: '',
  disk_capacity: undefined as number | undefined,
  disk_count: undefined as number | undefined,
  gpu_model: '',
  gpu_memory: undefined as number | undefined,
  mac_address: '',
  ip_address: '',
  hostname: '',
  os_name: '',
  os_version: '',
  os_architecture: '',
  os_license_key: '',
  disk_encrypted: false,
  antivirus_enabled: true,
  antivirus_software: '',
  ad_domain: '',
  ad_computer_name: ''
})

const rules: FormRules = {
  asset: [
    { required: true, message: 'Please select asset', trigger: 'change' }
  ],
  mac_address: [
    {
      pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})|$/,
      message: 'Invalid MAC address format',
      trigger: 'blur'
    }
  ],
  ip_address: [
    {
      pattern: /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|$/,
      message: 'Invalid IP address format',
      trigger: 'blur'
    }
  ]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    // Load asset options when editing
    if (props.data.asset_code) {
      searchAssets(props.data.asset_code)
    }
    Object.assign(formData.value, {
      asset: props.data.asset || '',
      cpu_model: props.data.cpu_model || '',
      cpu_cores: props.data.cpu_cores,
      cpu_threads: props.data.cpu_threads,
      ram_capacity: props.data.ram_capacity,
      ram_type: props.data.ram_type || '',
      ram_slots: props.data.ram_slots,
      disk_type: props.data.disk_type || '',
      disk_capacity: props.data.disk_capacity,
      disk_count: props.data.disk_count,
      gpu_model: props.data.gpu_model || '',
      gpu_memory: props.data.gpu_memory,
      mac_address: props.data.mac_address || '',
      ip_address: props.data.ip_address || '',
      hostname: props.data.hostname || '',
      os_name: props.data.os_name || '',
      os_version: props.data.os_version || '',
      os_architecture: props.data.os_architecture || '',
      os_license_key: props.data.os_license_key || '',
      disk_encrypted: props.data.disk_encrypted || false,
      antivirus_enabled: props.data.antivirus_enabled ?? true,
      antivirus_software: props.data.antivirus_software || '',
      ad_domain: props.data.ad_domain || '',
      ad_computer_name: props.data.ad_computer_name || ''
    })
  } else if (val) {
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
    asset: '',
    cpu_model: '',
    cpu_cores: undefined,
    cpu_threads: undefined,
    ram_capacity: undefined,
    ram_type: '',
    ram_slots: undefined,
    disk_type: '',
    disk_capacity: undefined,
    disk_count: undefined,
    gpu_model: '',
    gpu_memory: undefined,
    mac_address: '',
    ip_address: '',
    hostname: '',
    os_name: '',
    os_version: '',
    os_architecture: '',
    os_license_key: '',
    disk_encrypted: false,
    antivirus_enabled: true,
    antivirus_software: '',
    ad_domain: '',
    ad_computer_name: ''
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
        await itAssetInfoApi.update(props.data!.id, formData.value)
      } else {
        await itAssetInfoApi.create(formData.value)
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

<style scoped>
.el-divider {
  margin: 20px 0;
}
</style>
