<template>
  <el-dialog
    v-model="visible"
    :title="t('softwareLicenses.allocationDialog.title', { name: license?.softwareName || '' })"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item :label="t('softwareLicenses.allocationDialog.availableUnits')">
        <el-text>{{ license?.availableUnits }} / {{ license?.totalUnits }}</el-text>
      </el-form-item>

      <el-form-item
        :label="t('softwareLicenses.allocationDialog.asset')"
        prop="asset"
      >
        <el-select
          v-model="formData.asset"
          filterable
          remote
          :remote-method="searchAssets"
          :placeholder="t('softwareLicenses.allocationDialog.placeholders.assetSearch')"
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

      <el-form-item :label="t('softwareLicenses.allocationDialog.allocationKey')">
        <el-input
          v-model="formData.allocationKey"
          type="password"
          show-password
          :placeholder="t('softwareLicenses.allocationDialog.placeholders.allocationKey')"
        />
      </el-form-item>

      <el-form-item :label="t('softwareLicenses.allocationDialog.notes')">
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="3"
          :placeholder="t('softwareLicenses.allocationDialog.placeholders.notes')"
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
        @click="handleSubmit"
      >
        {{ t('softwareLicenses.allocationDialog.actions.allocate') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
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
const { t } = useI18n()

const formRef = ref<any>()
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

const rules = {
  asset: [
    { required: true, message: t('softwareLicenses.allocationDialog.validation.assetRequired'), trigger: 'change' }
  ]
}

const searchAssets = async (query: string) => {
  if (!query) return

  searching.value = true
  try {
    const response = await assetApi.list({ search: query, pageSize: 50 })
    assetOptions.value = response.results || []
  } catch (error) {
    console.error('Failed to search assets:', error)
  } finally {
    searching.value = false
  }
}

const handleSubmit = async () => {
  const currentLicense = props.license
  if (!formRef.value || !currentLicense) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await licenseAllocationApi.create({
      license: currentLicense.id,
      asset: formData.value.asset,
      allocationKey: formData.value.allocationKey || undefined,
      notes: formData.value.notes || undefined
    })
    ElMessage.success(t('softwareLicenses.allocationDialog.messages.allocateSuccess'))
    emit('allocated')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error.message || t('softwareLicenses.allocationDialog.messages.allocateFailed'))
  } finally {
    submitting.value = false
  }
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
