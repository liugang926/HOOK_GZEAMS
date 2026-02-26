<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="login-title">
        GZEAMS
      </h2>
      <p class="login-subtitle">
        {{ $t('login.subtitle') }}
      </p>
      <el-form
        :model="form"
        label-width="0"
      >
        <el-form-item>
          <el-input
            v-model="form.username"
            :placeholder="$t('login.username')"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="$t('login.password')"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            {{ $t('login.loginButton') }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const { t } = useI18n()

const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning(t('login.validation.required'))
    return
  }
  
  loading.value = true
  try {
    await userStore.login(form.value)
    ElMessage.success(t('login.success'))
    router.push('/dashboard')
  } catch (error: any) {
    if (error.isHandled) return
    console.error(error)
    ElMessage.error(error.message || t('login.failed'))
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.login-page {
  width: 100%;
  max-width: 400px;
}

.login-card {
  width: 100%;
  padding: 40px;
}

.login-title {
  text-align: center;
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 8px;
}

.login-subtitle {
  text-align: center;
  font-size: 14px;
  color: #909399;
  margin-bottom: 30px;
}
</style>
