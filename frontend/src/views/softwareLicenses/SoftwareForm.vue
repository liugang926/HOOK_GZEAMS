<!-- frontend/src/views/softwareLicenses/SoftwareForm.vue -->

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>{{ isEdit ? $t('softwareLicenses.catalog.edit') : $t('softwareLicenses.catalog.add') }}</span>
        <el-button @click="handleBack">
          {{ $t('common.actions.cancel') }}
        </el-button>
      </div>
    </template>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item
        :label="$t('softwareLicenses.catalog.fields.code')"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          :placeholder="$t('softwareLicenses.catalog.placeholders.code')"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.catalog.fields.name')"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          :placeholder="$t('softwareLicenses.catalog.placeholders.name')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.catalog.fields.version')"
        prop="version"
      >
        <el-input
          v-model="formData.version"
          :placeholder="$t('softwareLicenses.catalog.placeholders.version')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.catalog.fields.vendor')"
        prop="vendor"
      >
        <el-input
          v-model="formData.vendor"
          :placeholder="$t('softwareLicenses.catalog.placeholders.vendor')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.catalog.fields.type')"
        prop="softwareType"
      >
        <el-select
          v-model="formData.softwareType"
          :placeholder="$t('common.placeholders.select')"
        >
          <el-option
            :label="$t('softwareLicenses.catalog.types.os')"
            value="os"
          />
          <el-option
            :label="$t('softwareLicenses.catalog.types.office')"
            value="office"
          />
          <el-option
            :label="$t('softwareLicenses.catalog.types.professional')"
            value="professional"
          />
          <el-option
            :label="$t('softwareLicenses.catalog.types.development')"
            value="development"
          />
          <el-option
            :label="$t('softwareLicenses.catalog.types.security')"
            value="security"
          />
          <el-option
            :label="$t('softwareLicenses.catalog.types.database')"
            value="database"
          />
          <el-option
            :label="$t('softwareLicenses.catalog.types.other')"
            value="other"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.catalog.fields.licenseType')"
        prop="licenseType"
      >
        <el-input
          v-model="formData.licenseType"
          :placeholder="$t('softwareLicenses.catalog.placeholders.licenseType')"
        />
      </el-form-item>

      <el-form-item
        :label="$t('softwareLicenses.catalog.fields.status')"
        prop="isActive"
      >
        <el-switch
          v-model="formData.isActive"
          :active-text="$t('common.status.active')"
          :inactive-text="$t('common.status.inactive')"
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
import { softwareApi } from '@/api/softwareLicenses'
import type { Software } from '@/types/softwareLicenses'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!route.params.id)

const formData = ref<Partial<Software>>({
  code: '',
  name: '',
  version: '',
  vendor: '',
  softwareType: 'other',
  licenseType: '',
  isActive: true
})

const rules = computed<FormRules>(() => ({
  code: [
    { required: true, message: t('validation.required'), trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: t('validation.pattern'), trigger: 'blur' }
  ],
  name: [
    { required: true, message: t('validation.required'), trigger: 'blur' }
  ],
  softwareType: [
    { required: true, message: t('validation.required'), trigger: 'change' }
  ]
}))

const loadSoftware = async () => {
  const id = route.params.id as string
  try {
    const data = await softwareApi.get(id)
    formData.value = data
  } catch (error) {
    ElMessage.error(t('common.messages.loadFailed', '加载失败'))
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await softwareApi.update(route.params.id as string, formData.value)
        ElMessage.success(t('common.messages.operationSuccess'))
      } else {
        await softwareApi.create(formData.value)
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
  if (isEdit.value) {
    loadSoftware()
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
