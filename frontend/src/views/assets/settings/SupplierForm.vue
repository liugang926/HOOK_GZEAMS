<template>
  <div class="supplier-form">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? t('assets.supplier.edit') : t('assets.supplier.create')"
        @back="goBack"
      />
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ t('common.actions.save') }}
        </el-button>
      </div>
    </div>

    <el-card
      shadow="never"
      class="mt-4"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              :label="t('assets.supplier.code')"
              prop="code"
            >
              <el-input
                v-model="form.code"
                :placeholder="t('assets.supplier.enterCode')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              :label="t('assets.supplier.name')"
              prop="name"
            >
              <el-input
                v-model="form.name"
                :placeholder="t('assets.supplier.enterName')"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              :label="t('assets.supplier.contact')"
              prop="contact_person"
            >
              <el-input
                v-model="form.contactPerson"
                :placeholder="t('assets.supplier.enterContact')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              :label="t('assets.supplier.phone')"
              prop="contact_phone"
            >
              <el-input
                v-model="form.contactPhone"
                :placeholder="t('assets.supplier.enterPhone')"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              :label="t('assets.supplier.email')"
              prop="email"
            >
              <el-input
                v-model="form.email"
                :placeholder="t('common.placeholders.input', { field: t('assets.supplier.email') })"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              :label="t('common.labels.status')"
              prop="isActive"
            >
              <el-switch
                v-model="form.isActive"
                :active-text="t('common.status.enabled')"
                :inactive-text="t('common.status.inactive')"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item
          :label="t('assets.supplier.address')"
          prop="address"
        >
          <el-input
            v-model="form.address"
            :placeholder="t('common.placeholders.input', { field: t('assets.supplier.address') })"
          />
        </el-form-item>
        <el-form-item
          :label="t('common.labels.remark')"
          prop="remark"
        >
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            :placeholder="t('common.placeholders.input', { field: t('common.labels.remark') })"
          />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { createSupplier, updateSupplier, getSupplierDetail } from '@/api/assets/suppliers'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

const formRef = ref()
const submitting = ref(false)

const form = reactive({
    id: null,
    code: '',
    name: '',
    contactPerson: '',
    contactPhone: '',
    email: '',
    address: '',
    remark: '',
    isActive: true
})

const rules = {
    code: [{ required: true, message: t('assets.supplier.enterCode'), trigger: 'blur' }],
    name: [{ required: true, message: t('assets.supplier.enterName'), trigger: 'blur' }],
    contactPerson: [{ required: true, message: t('assets.supplier.enterContact'), trigger: 'blur' }],
    contactPhone: [
        { required: true, message: t('assets.supplier.enterPhone'), trigger: 'blur' },
        { pattern: /^1[3-9]\d{9}$/, message: t('common.validation.phone'), trigger: 'blur' }
    ]
}

const isEdit = computed(() => !!route.params.id)

const handleSubmit = async () => {
    try {
        await formRef.value.validate()
        submitting.value = true

        const payload = {
            code: form.code,
            name: form.name,
            contact_person: form.contactPerson,
            contact_phone: form.contactPhone,
            email: form.email,
            address: form.address,
            remark: form.remark,
            is_active: form.isActive
        }

        if (isEdit.value) {
            await updateSupplier(String(route.params.id), payload)
            ElMessage.success(t('common.messages.updateSuccess'))
        } else {
            await createSupplier(payload)
            ElMessage.success(t('common.messages.saveSuccess'))
        }
        goBack()
    } catch (e: any) {
        if (e !== false) {
            console.error(e)
            ElMessage.error(e.response?.data?.message || e.message || t('common.messages.operationFailed'))
        }
    } finally {
        submitting.value = false
    }
}

const goBack = () => {
    router.back()
}

onMounted(async () => {
    if (isEdit.value) {
        try {
            const data = await getSupplierDetail(String(route.params.id))
            form.id = data.id
            form.code = data.code
            form.name = data.name
            form.contactPerson = data.contact_person
            form.contactPhone = data.contact_phone
            form.email = data.email
            form.address = data.address
            form.remark = data.remark
            form.isActive = data.is_active
        } catch (e) {
            console.error(e)
            ElMessage.error(t('common.messages.loadFailed'))
            goBack()
        }
    }
})
</script>

<style scoped>
.supplier-form {
    padding: 20px;
}
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.mt-4 {
    margin-top: 20px;
}
</style>
