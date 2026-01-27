<template>
  <div class="supplier-form">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? '编辑供应商' : '新建供应商'"
        @back="goBack"
      />
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存
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
              label="供应商编码"
              prop="code"
            >
              <el-input
                v-model="form.code"
                placeholder="请输入供应商编码"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              label="供应商名称"
              prop="name"
            >
              <el-input
                v-model="form.name"
                placeholder="请输入供应商名称"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="联系人"
              prop="contact_person"
            >
              <el-input
                v-model="form.contactPerson"
                placeholder="请输入联系人"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              label="联系电话"
              prop="contact_phone"
            >
              <el-input
                v-model="form.contactPhone"
                placeholder="请输入联系电话"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              label="邮箱"
              prop="email"
            >
              <el-input
                v-model="form.email"
                placeholder="请输入邮箱"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              label="状态"
              prop="isActive"
            >
              <el-switch
                v-model="form.isActive"
                active-text="启用"
                inactive-text="停用"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item
          label="地址"
          prop="address"
        >
          <el-input
            v-model="form.address"
            placeholder="请输入地址"
          />
        </el-form-item>
        <el-form-item
          label="备注"
          prop="remark"
        >
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            placeholder="请输入备注"
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
import { createSupplier, updateSupplier, getSupplierDetail } from '@/api/assets/suppliers'

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
    code: [{ required: true, message: '请输入供应商编码', trigger: 'blur' }],
    name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }],
    contactPerson: [{ required: true, message: '请输入联系人', trigger: 'blur' }],
    contactPhone: [
        { required: true, message: '请输入联系电话', trigger: 'blur' },
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
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
            ElMessage.success('更新成功')
        } else {
            await createSupplier(payload)
            ElMessage.success('保存成功')
        }
        goBack()
    } catch (e: any) {
        if (e !== false) {
            console.error(e)
            ElMessage.error(e.response?.data?.message || e.message || '操作失败')
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
            ElMessage.error('加载失败')
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
