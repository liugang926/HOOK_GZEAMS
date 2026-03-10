<template>
  <div class="login-page">
    <el-card
      ref="cardRef"
      class="login-card"
      shadow="never"
      :style="cardStyle"
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
    >
      <div
        class="logo-container stagger-item"
        style="--stagger-idx: 1"
      >
        <img
          v-if="loginLogoUrl"
          :src="loginLogoUrl"
          :alt="brandingStore.settings.appName"
          class="logo-image"
        >
        <svg
          v-else
          class="logo-svg"
          viewBox="0 0 100 100"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M50 5 L90 25 L90 75 L50 95 L10 75 L10 25 Z"
            stroke="url(#logoGradient)"
            stroke-width="8"
            stroke-linejoin="round"
          />
          <path
            d="M50 5 L50 50 L90 25"
            stroke="url(#logoGradient)"
            stroke-width="8"
            stroke-linejoin="round"
          />
          <path
            d="M50 50 L10 25"
            stroke="url(#logoGradient)"
            stroke-width="8"
            stroke-linejoin="round"
          />
          <path
            d="M50 50 L50 95"
            stroke="url(#logoGradient)"
            stroke-width="8"
            stroke-linejoin="round"
          />
          <circle
            cx="50"
            cy="50"
            r="12"
            fill="url(#logoGradient)"
          />
          <defs>
            <linearGradient
              id="logoGradient"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop
                offset="0%"
                stop-color="var(--el-color-primary)"
              />
              <stop
                offset="100%"
                stop-color="var(--sys-color-accent, #36cfc9)"
              />
            </linearGradient>
          </defs>
        </svg>
        <h2 class="login-title">
          {{ localizedLogin.title || brandingStore.settings.appName }}
        </h2>
      </div>
      <p
        class="login-subtitle stagger-item"
        style="--stagger-idx: 2"
      >
        {{ localizedLogin.subtitle || $t('login.subtitle') }}
      </p>

      <el-form
        :model="form"
        class="login-form"
        label-width="0"
        @submit.prevent="handleLogin"
      >
        <el-form-item
          class="stagger-item"
          style="--stagger-idx: 3"
        >
          <el-input
            v-model="form.username"
            :placeholder="$t('login.username')"
            :prefix-icon="User"
            size="large"
            @focus="onFocus"
            @blur="onBlur"
          />
        </el-form-item>
        <el-form-item
          class="stagger-item"
          style="--stagger-idx: 4"
        >
          <el-input
            v-model="form.password"
            type="password"
            :placeholder="$t('login.password')"
            :prefix-icon="Lock"
            size="large"
            show-password
            @focus="onFocus"
            @blur="onBlur"
          />
        </el-form-item>
        <el-form-item
          class="stagger-item btn-container"
          style="--stagger-idx: 5"
        >
          <el-button
            type="primary"
            size="large"
            class="login-submit-button"
            :class="{ 'is-animating-load': loading }"
            native-type="submit"
            :loading="loading"
            @mousedown="createRipple"
          >
            <span
              class="btn-text"
              :class="{ 'is-hidden': loading }"
            >{{ $t('login.loginButton') }}</span>
          </el-button>
        </el-form-item>

        <div
          class="login-footer stagger-item"
          style="--stagger-idx: 6"
        >
          <a class="forgot-password">{{ $t('login.forgotPassword') }}</a>
          <a class="forgot-password">{{ $t('login.contactAdmin') }}</a>
        </div>
      </el-form>
    </el-card>

    <div
      class="copyright stagger-item"
      style="--stagger-idx: 7"
    >
      {{ localizedLogin.copyright }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useBrandingStore } from '@/stores/branding'
import { useLocaleStore } from '@/stores/locale'

const router = useRouter()
const userStore = useUserStore()
const brandingStore = useBrandingStore()
const localeStore = useLocaleStore()
const loading = ref(false)
const { t } = useI18n()
const loginLogoUrl = computed(() => brandingStore.loginLogoUrl)
const localizedLogin = computed(() => {
  const localeKey = localeStore.currentLocale
  return brandingStore.settings.loginI18n?.[localeKey] || brandingStore.settings.login
})

const form = ref({
  username: '',
  password: ''
})

const cardRef = ref<any>(null)
const cardStyle = ref({
  transform: 'perspective(1000px) rotateX(0deg) rotateY(0deg)',
  transition: 'transform 0.6s cubic-bezier(0.25, 0.8, 0.25, 1)'
})

const onMouseMove = (e: MouseEvent) => {
  if (!cardRef.value) return

  const card = cardRef.value.$el || cardRef.value
  const rect = card.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top

  const centerX = rect.width / 2
  const centerY = rect.height / 2
  const rotateX = ((y - centerY) / centerY) * -3
  const rotateY = ((x - centerX) / centerX) * 3

  cardStyle.value.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`
  cardStyle.value.transition = 'transform 0.1s ease-out'
}

const onMouseLeave = () => {
  cardStyle.value.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)'
  cardStyle.value.transition = 'transform 0.6s cubic-bezier(0.25, 0.8, 0.25, 1)'
}

const onFocus = () => {
  document.body.classList.add('auth-active-state')
}

const onBlur = () => {
  document.body.classList.remove('auth-active-state')
}

const createRipple = (event: MouseEvent) => {
  const button = event.currentTarget as HTMLElement
  const circle = document.createElement('span')
  const diameter = Math.max(button.clientWidth, button.clientHeight)
  const radius = diameter / 2

  circle.style.width = circle.style.height = `${diameter}px`
  circle.style.left = `${event.clientX - button.getBoundingClientRect().left - radius}px`
  circle.style.top = `${event.clientY - button.getBoundingClientRect().top - radius}px`
  circle.classList.add('ripple')

  const ripple = button.getElementsByClassName('ripple')[0]
  if (ripple) ripple.remove()
  button.appendChild(circle)
}

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning(t('login.validation.required'))
    return
  }

  loading.value = true
  document.body.classList.add('auth-loading-state')

  try {
    await userStore.login(form.value)
    await brandingStore.refresh()
    ElMessage.success(t('login.success'))
    router.push('/dashboard')
  } catch (error: any) {
    if (error.isHandled) return
    ElMessage.error(error.message || t('login.failed'))
  } finally {
    loading.value = false
    document.body.classList.remove('auth-loading-state')
  }
}

onMounted(() => {
  brandingStore.initialize()
})

onUnmounted(() => {
  document.body.classList.remove('auth-active-state', 'auth-loading-state')
})
</script>

<style scoped lang="scss">
.login-page {
  width: 100%;
  max-width: 420px;
  padding: 0 20px;
  perspective: 1200px;
}

.stagger-item {
  opacity: 0;
  animation: staggerFadeInUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
  animation-delay: calc(var(--stagger-idx) * 0.1s);
}

@keyframes staggerFadeInUp {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

:deep(.el-card.login-card) {
  border: 1px solid rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 15px 35px 0 rgba(31, 38, 135, 0.15);
  border-radius: 20px;
  overflow: visible;
  will-change: transform;
}

:deep(.el-card__body) {
  padding: 40px 32px 30px;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 8px;
}

.logo-svg,
.logo-image {
  width: 64px;
  height: 64px;
  margin-bottom: 12px;
  animation: float 6s ease-in-out infinite;
}

.logo-image {
  object-fit: contain;
  filter: drop-shadow(0 8px 18px rgba(15, 23, 42, 0.14));
}

.logo-svg {
  filter: drop-shadow(0 4px 8px rgba(64, 158, 255, 0.3));
}

@keyframes float {
  0% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
  100% { transform: translateY(0); }
}

.login-title {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 2px;
  background: var(--brand-gradient-primary, linear-gradient(135deg, #1d4ed8 0%, #0ea5e9 100%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
}

.login-subtitle {
  text-align: center;
  font-size: 15px;
  color: #606266;
  margin-bottom: 35px;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.login-form {
  margin-top: 10px;
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.82) !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02) !important;
  border-radius: 10px;
  padding: 2px 15px;
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  overflow: hidden;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset, 0 4px 20px rgba(64, 158, 255, 0.25) !important;
  background-color: #ffffff !important;
  transform: translateY(-2px);
}

:deep(.el-input__wrapper::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(to right, transparent, rgba(255,255,255,0.8), transparent);
  transform: skewX(-20deg);
  z-index: 1;
  pointer-events: none;
}

:deep(.el-input__wrapper.is-focus::before) {
  animation: sweep 0.6s ease-out;
}

@keyframes sweep {
  0% { left: -100%; }
  100% { left: 200%; }
}

:deep(.el-input__inner),
:deep(.el-input__prefix),
:deep(.el-input__suffix) {
  z-index: 2;
  position: relative;
}

:deep(.el-input__inner) {
  height: 44px;
}

.btn-container {
  display: flex;
  justify-content: center;
}

.login-submit-button {
  width: 100%;
  display: block;
  margin: 15px auto 0;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
  border-radius: 10px;
  background: var(--brand-gradient-primary, linear-gradient(135deg, #409eff 0%, #36cfc9 100%));
  border: none;
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.3);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  overflow: hidden;
}

.login-submit-button:hover:not(.is-animating-load) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(64, 158, 255, 0.4);
  background: var(--brand-gradient-primary-soft, linear-gradient(135deg, #53a8ff 0%, #40d4ce 100%));
}

.login-submit-button:active:not(.is-animating-load) {
  transform: translateY(1px);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.login-submit-button.is-animating-load {
  width: 48px !important;
  border-radius: 24px !important;
  pointer-events: none;
  box-shadow: 0 4px 15px rgba(64, 158, 255, 0.5);
  transform: scale(0.95);
}

.btn-text {
  transition: opacity 0.2s;
  z-index: 2;
  position: relative;
}

.btn-text.is-hidden {
  opacity: 0;
}

:deep(.ripple) {
  position: absolute;
  border-radius: 50%;
  transform: scale(0);
  animation: ripple-animation 0.6s linear;
  background-color: rgba(255, 255, 255, 0.4);
  pointer-events: none;
  z-index: 0;
}

@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}

.login-footer {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  padding: 0 4px;
}

.forgot-password {
  color: #909399;
  text-decoration: none;
  transition: color 0.3s;
  cursor: pointer;
  font-weight: 500;
  text-align: center;
}

.forgot-password:hover {
  color: var(--el-color-primary);
}

.copyright {
  text-align: center;
  margin-top: 25px;
  font-size: 12px;
  color: #909399;
  letter-spacing: 0.5px;
  opacity: 0.8;
}
</style>
