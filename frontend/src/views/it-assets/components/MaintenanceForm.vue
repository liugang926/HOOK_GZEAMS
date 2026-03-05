<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? $t('itAssets.form.maintenance.editTitle') : $t('itAssets.form.maintenance.addTitle')"
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
        :label="$t('itAssets.common.asset')"
        prop="asset"
      >
        <el-select
          v-model="formData.asset"
          :placeholder="$t('itAssets.form.placeholders.selectAsset')"
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
        :label="$t('itAssets.maintenance.type')"
        prop="maintenance_type"
      >
        <el-select
          v-model="formData.maintenance_type"
          :placeholder="$t('itAssets.maintenance.allTypes')"
          style="width: 100%"
        >
          <el-option
            :label="$t('itAssets.maintenance.types.preventive')"
            value="preventive"
          />
          <el-option
            :label="$t('itAssets.maintenance.types.corrective')"
            value="corrective"
          />
          <el-option
            :label="$t('itAssets.maintenance.types.upgrade')"
            value="upgrade"
          />
          <el-option
            :label="$t('itAssets.maintenance.types.replacement')"
            value="replacement"
          />
          <el-option
            :label="$t('itAssets.maintenance.types.inspection')"
            value="inspection"
          />
          <el-option
            :label="$t('itAssets.maintenance.types.cleaning')"
            value="cleaning"
          />
          <el-option
            :label="$t('itAssets.maintenance.types.other')"
            value="other"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="$t('itAssets.common.title')"
        prop="title"
      >
        <el-input
          v-model="formData.title"
          :placeholder="$t('itAssets.form.maintenance.placeholders.title')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('itAssets.common.description')"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="4"
          :placeholder="$t('itAssets.form.maintenance.placeholders.description')"
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item
            :label="$t('itAssets.common.date')"
            prop="maintenance_date"
          >
            <el-date-picker
              v-model="formData.maintenance_date"
              type="date"
              :placeholder="$t('common.placeholders.select')"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item
            :label="$t('itAssets.common.cost')"
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
        :label="$t('itAssets.common.vendor')"
        prop="vendor"
      >
        <el-input
          v-model="formData.vendor"
          :placeholder="$t('itAssets.form.maintenance.placeholders.vendor')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('itAssets.common.notes')"
        prop="notes"
      >
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="2"
          :placeholder="$t('itAssets.form.maintenance.placeholders.notes')"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        {{ $t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? $t('common.actions.save') : $t('common.actions.add') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { ITMaintenanceRecord } from '@/api/itAssets'
import { itMaintenanceApi } from '@/api/itAssets'
import request from '@/utils/request'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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
    { required: true, message: t('itAssets.form.validation.selectAsset'), trigger: 'change' }
  ],
  maintenance_type: [
    { required: true, message: t('itAssets.form.maintenance.validation.selectType'), trigger: 'change' }
  ],
  title: [
    { required: true, message: t('itAssets.form.maintenance.validation.enterTitle'), trigger: 'blur' }
  ],
  maintenance_date: [
    { required: true, message: t('itAssets.form.maintenance.validation.selectDate'), trigger: 'change' }
  ]
}

const searchAssets = async (query: string) => {
  if (!query) return
  assetLoading.value = true
  try {
    const res: any = await request.get('/assets/', {
      params: { search: query, page_size: 20 },
      silent: true
    })
    const results = res?.results || []
    assetOptions.value = results.map((item: any) => ({
      ...item,
      asset_code: item.asset_code || item.assetCode || item.code || '',
      asset_name: item.asset_name || item.assetName || item.name || ''
    }))
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

  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await itMaintenanceApi.update(props.data!.id, formData.value)
      } else {
        await itMaintenanceApi.create(formData.value)
      }
      ElMessage.success(isEdit.value ? t('itAssets.messages.updateSuccess') : t('itAssets.messages.addSuccess'))
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error(t('itAssets.messages.operationFailed'))
    } finally {
      submitting.value = false
    }
  })
}
</script>
