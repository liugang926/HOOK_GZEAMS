<!-- frontend/src/views/softwareLicenses/SoftwareForm.vue -->

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>{{ isEdit ? '编辑软件' : '新建软件' }}</span>
        <el-button @click="handleBack">
          返回
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
        label="软件代码"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          placeholder="如: WIN11, OFF365"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item
        label="软件名称"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          placeholder="软件产品名称"
        />
      </el-form-item>

      <el-form-item
        label="版本"
        prop="version"
      >
        <el-input
          v-model="formData.version"
          placeholder="如: 2021, Pro, 22H2"
        />
      </el-form-item>

      <el-form-item
        label="厂商"
        prop="vendor"
      >
        <el-input
          v-model="formData.vendor"
          placeholder="软件厂商"
        />
      </el-form-item>

      <el-form-item
        label="软件类型"
        prop="softwareType"
      >
        <el-select
          v-model="formData.softwareType"
          placeholder="选择类型"
        >
          <el-option
            label="操作系统"
            value="os"
          />
          <el-option
            label="办公软件"
            value="office"
          />
          <el-option
            label="专业软件"
            value="professional"
          />
          <el-option
            label="开发工具"
            value="development"
          />
          <el-option
            label="安全软件"
            value="security"
          />
          <el-option
            label="数据库"
            value="database"
          />
          <el-option
            label="其他"
            value="other"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        label="许可类型"
        prop="licenseType"
      >
        <el-input
          v-model="formData.licenseType"
          placeholder="如: perpetual, subscription, OEM"
        />
      </el-form-item>

      <el-form-item
        label="状态"
        prop="isActive"
      >
        <el-switch
          v-model="formData.isActive"
          active-text="启用"
          inactive-text="停用"
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
import { softwareApi } from '@/api/softwareLicenses'
import type { Software } from '@/types/softwareLicenses'

const router = useRouter()
const route = useRoute()
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

const rules: FormRules = {
  code: [
    { required: true, message: '请输入软件代码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '代码只能包含大写字母、数字和下划线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入软件名称', trigger: 'blur' }
  ],
  softwareType: [
    { required: true, message: '请选择软件类型', trigger: 'change' }
  ]
}

const loadSoftware = async () => {
  const id = route.params.id as string
  try {
    const data = await softwareApi.get(id)
    formData.value = data
  } catch (error) {
    ElMessage.error('加载软件信息失败')
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
        ElMessage.success('更新成功')
      } else {
        await softwareApi.create(formData.value)
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
