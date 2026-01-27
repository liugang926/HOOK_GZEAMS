<!-- frontend/src/views/softwareLicenses/SoftwareLicenseForm.vue -->

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>{{ isEdit ? '编辑许可证' : '新建许可证' }}</span>
        <el-button @click="handleBack">
          返回
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
        label="许可证编号"
        prop="licenseNo"
      >
        <el-input
          v-model="formData.licenseNo"
          placeholder="如: OFF365-2024-001"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item
        label="软件"
        prop="software"
      >
        <el-select
          v-model="formData.software"
          filterable
          placeholder="选择软件"
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
        label="许可证密钥"
        prop="licenseKey"
      >
        <el-input
          v-model="formData.licenseKey"
          type="password"
          show-password
          placeholder="可选，加密存储"
        />
      </el-form-item>

      <el-divider>许可数量</el-divider>

      <el-form-item
        label="总许可数"
        prop="totalUnits"
      >
        <el-input-number
          v-model="formData.totalUnits"
          :min="1"
          :max="10000"
        />
      </el-form-item>

      <el-form-item label="已使用数">
        <el-input-number
          v-model="formData.usedUnits"
          :min="0"
          disabled
        />
        <el-text
          size="small"
          type="info"
        >
          系统自动更新
        </el-text>
      </el-form-item>

      <el-divider>许可期限</el-divider>

      <el-form-item
        label="购买日期"
        prop="purchaseDate"
      >
        <el-date-picker
          v-model="formData.purchaseDate"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="到期日期">
        <el-date-picker
          v-model="formData.expiryDate"
          type="date"
          placeholder="留空表示永久许可"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-divider>财务信息</el-divider>

      <el-form-item label="购买价格">
        <el-input-number
          v-model="formData.purchasePrice"
          :min="0"
          :precision="2"
        />
        <span style="margin-left: 10px">元</span>
      </el-form-item>

      <el-form-item label="年维护成本">
        <el-input-number
          v-model="formData.annualCost"
          :min="0"
          :precision="2"
        />
        <span style="margin-left: 10px">元/年</span>
      </el-form-item>

      <el-divider>状态信息</el-divider>

      <el-form-item
        label="状态"
        prop="status"
      >
        <el-select v-model="formData.status">
          <el-option
            label="生效中"
            value="active"
          />
          <el-option
            label="已过期"
            value="expired"
          />
          <el-option
            label="暂停"
            value="suspended"
          />
          <el-option
            label="撤销"
            value="revoked"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="许可类型">
        <el-input
          v-model="formData.licenseType"
          placeholder="如: perpetual, subscription, OEM, volume"
        />
      </el-form-item>

      <el-form-item label="协议编号">
        <el-input
          v-model="formData.agreementNo"
          placeholder="企业协议编号"
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="3"
          placeholder="许可证相关备注"
        />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          native-type="submit"
          :loading="submitting"
        >
          保存
        </el-button>
        <el-button @click="handleBack">
          取消
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { softwareLicenseApi, softwareApi } from '@/api/softwareLicenses'
import type { SoftwareLicense, Software } from '@/types/softwareLicenses'

const router = useRouter()
const route = useRoute()
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

const rules: FormRules = {
  licenseNo: [
    { required: true, message: '请输入许可证编号', trigger: 'blur' }
  ],
  software: [
    { required: true, message: '请选择软件', trigger: 'change' }
  ],
  totalUnits: [
    { required: true, message: '请输入许可数量', trigger: 'blur' }
  ],
  purchaseDate: [
    { required: true, message: '请选择购买日期', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const loadSoftware = async () => {
  try {
    const response = await softwareApi.list({ pageSize: 1000 })
    softwareOptions.value = response.data.results || []
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
    ElMessage.error('加载许可证信息失败')
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
        ElMessage.success('更新成功')
      } else {
        await softwareLicenseApi.create(formData.value)
        ElMessage.success('创建成功')
      }
      handleBack()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
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
