<!-- frontend/src/views/softwareLicenses/SoftwareLicenseForm.vue -->

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>{{ isEdit ? $t('softwareLicenses.licenses.edit') : $t('softwareLicenses.licenses.add') }}</span>
        <el-button @click="handleBack">
          {{ $t('common.actions.cancel') }}
        </el-button>
      </div>
    </template>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item
        :label="$t('softwareLicenses.licenses.fields.licenseNo')"
        prop="licenseNo"
      >
        <el-input
          v-model="formData.licenseNo"
          :placeholder="$t('softwareLicenses.licenses.placeholders.licenseNo')"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.licenses.fields.software')"
        prop="software"
      >
        <el-select
          v-model="formData.software"
          filterable
          :placeholder="$t('common.placeholders.select')"
          style="width: 100%"
        >
          <el-option
            v-for="item in softwareOptions"
            :key="item.id"
            :label="`${item.name} ${item.version}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.licenses.fields.licenseKey')"
        prop="licenseKey"
      >
        <el-input
          v-model="formData.licenseKey"
          type="password"
          show-password
          :placeholder="$t('softwareLicenses.licenses.placeholders.key')"
        />
      </el-form-item>

      <el-divider>{{ $t('softwareLicenses.licenses.fields.totalUnits') }}</el-divider>

      <el-form-item
        :label="$t('softwareLicenses.licenses.fields.totalUnits')"
        prop="totalUnits"
      >
        <el-input-number
          v-model="formData.totalUnits"
          :min="1"
          :max="10000"
        />
      </el-form-item>

      <el-form-item :label="$t('softwareLicenses.licenses.fields.usedUnits')">
        <el-input-number
          v-model="formData.usedUnits"
          :min="0"
          disabled
        />
        <el-text
          size="small"
          type="info"
        >
          {{ $t('softwareLicenses.licenses.systemUpdate') }}
        </el-text>
      </el-form-item>

      <el-divider>{{ $t('softwareLicenses.licenses.sections.term') }}</el-divider>

      <el-form-item
        :label="$t('softwareLicenses.licenses.fields.purchaseDate')"
        prop="purchaseDate"
      >
        <el-date-picker
          v-model="formData.purchaseDate"
          type="date"
          :placeholder="$t('common.placeholders.select')"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item :label="$t('softwareLicenses.licenses.fields.expiryDate')">
        <el-date-picker
          v-model="formData.expiryDate"
          type="date"
          :placeholder="$t('common.placeholders.select')"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-divider>{{ $t('softwareLicenses.licenses.sections.financial') }}</el-divider>

      <el-form-item :label="$t('softwareLicenses.licenses.fields.purchasePrice')">
        <el-input-number
          v-model="formData.purchasePrice"
          :min="0"
          :precision="2"
        />
        <span style="margin-left: 10px">{{ $t('common.units.yuan') }}</span>
      </el-form-item>

      <el-form-item :label="$t('softwareLicenses.licenses.fields.annualCost')">
        <el-input-number
          v-model="formData.annualCost"
          :min="0"
          :precision="2"
        />
        <span style="margin-left: 10px">{{ $t('common.units.yuan') }}/{{ $t('common.units.year') }}</span>
      </el-form-item>

      <el-divider>{{ $t('softwareLicenses.licenses.sections.status') }}</el-divider>

      <el-form-item
        :label="$t('softwareLicenses.licenses.fields.status')"
        prop="status"
      >
        <el-select v-model="formData.status">
          <el-option
            :label="$t('softwareLicenses.licenses.status.active')"
            value="active"
          />
          <el-option
            :label="$t('softwareLicenses.licenses.status.expired')"
            value="expired"
          />
          <el-option
            :label="$t('softwareLicenses.licenses.status.suspended')"
            value="suspended"
          />
          <el-option
            :label="$t('softwareLicenses.licenses.status.revoked')"
            value="revoked"
          />
        </el-select>
      </el-form-item>

      <el-form-item :label="$t('softwareLicenses.catalog.fields.licenseType')">
        <el-input
          v-model="formData.licenseType"
          :placeholder="$t('softwareLicenses.licenses.placeholders.type')"
        />
      </el-form-item>

      <el-form-item :label="$t('softwareLicenses.licenses.fields.agreementNo')">
        <el-input
          v-model="formData.agreementNo"
          :placeholder="$t('softwareLicenses.licenses.placeholders.agreement')"
        />
      </el-form-item>

      <el-form-item :label="$t('softwareLicenses.licenses.fields.notes')">
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="3"
          :placeholder="$t('softwareLicenses.licenses.placeholders.notes')"
        />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          :loading="submitting"
        >
          {{ $t('common.actions.save') }}
        </el-button>
        <el-button @click="handleBack">
          {{ $t('common.actions.cancel') }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { softwareLicenseApi, softwareApi } from '@/api/softwareLicenses'
import type { SoftwareLicense, Software } from '@/types/softwareLicenses'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!route.params.id)

const formData = ref<Partial<SoftwareLicense>>({
  licenseNo: '',
  software: '',
  licenseKey: '',
  totalUnits: 1,
  usedUnits: 0,
  purchaseDate: '',
  expiryDate: undefined,
  purchasePrice: undefined,
  annualCost: undefined,
  status: 'active',
  licenseType: '',
  agreementNo: '',
  notes: ''
})

const softwareOptions = ref<Software[]>([])

const rules = computed<FormRules>(() => ({
  licenseNo: [
    { required: true, message: t('common.validation.required', { field: t('softwareLicenses.licenses.fields.licenseNo') }), trigger: 'blur' }
  ],
  software: [
    { required: true, message: t('common.validation.required', { field: t('softwareLicenses.licenses.fields.software') }), trigger: 'change' }
  ],
  totalUnits: [
    { required: true, message: t('common.validation.required', { field: t('softwareLicenses.licenses.fields.totalUnits') }), trigger: 'blur' }
  ],
  purchaseDate: [
    { required: true, message: t('common.validation.required', { field: t('softwareLicenses.licenses.fields.purchaseDate') }), trigger: 'change' }
  ],
  status: [
    { required: true, message: t('common.validation.required', { field: t('softwareLicenses.licenses.fields.status') }), trigger: 'change' }
  ]
}))

const loadSoftware = async () => {
  try {
    const response = await softwareApi.list({ pageSize: 1000 })
    softwareOptions.value = response.results || []
  } catch (error) {
    console.error('Failed to load software list:', error)
  }
}

const loadLicense = async () => {
  const id = route.params.id as string
  try {
    const data = await softwareLicenseApi.get(id)
    formData.value = data
  } catch (error) {
    ElMessage.error(t('common.messages.loadFailed'))
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await softwareLicenseApi.update(route.params.id as string, formData.value)
        ElMessage.success(t('common.messages.operationSuccess'))
      } else {
        await softwareLicenseApi.create(formData.value)
        ElMessage.success(t('common.messages.operationSuccess'))
      }
      handleBack()
    } catch (error: any) {
      ElMessage.error(error.message || t('common.messages.operationFailed'))
    } finally {
      submitting.value = false
    }
  })
}

const handleBack = () => {
  router.back()
}

onMounted(() => {
  loadSoftware()
  if (isEdit.value) {
    loadLicense()
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
