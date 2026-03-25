<template>
  <el-dropdown
    trigger="click"
    @command="handleCommand"
  >
    <span class="locale-trigger">
      <span style="font-size: 16px;">🌐</span>
      <span class="locale-label">{{ currentLabel }}</span>
      <el-icon class="el-icon--right"><ArrowDown /></el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="locale in locales"
          :key="locale.value"
          :command="locale.value"
          :disabled="locale.value === currentLocale"
        >
          <span :class="{ 'is-active': locale.value === currentLocale }">
            {{ locale.label }}
          </span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useLocaleStore } from '@/stores/locale'
import type { LocaleType } from '@/locales'
import { ArrowDown } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api/users'
import { setStoredLocaleSource } from '@/platform/i18n/localePreference'

const localeStore = useLocaleStore()
const userStore = useUserStore()
const { t } = useI18n()
const currentLocale = computed(() => localeStore.currentLocale)

const locales = computed<Array<{ value: LocaleType; label: string }>>(() => {
  const supported = new Set(localeStore.supportedLocales)
  const fromApi = localeStore.activeLanguages
    .map((language) => {
      if (!supported.has(language.code as LocaleType)) return null
      return {
        value: language.code as LocaleType,
        label: language.nativeName || language.name || language.code
      }
    })
    .filter((item): item is { value: LocaleType; label: string } => Boolean(item))

  if (fromApi.length > 0) return fromApi
  return localeStore.supportedLocales.map((locale) => ({ value: locale, label: locale }))
})

const currentLabel = computed(
  () => locales.value.find((l) => l.value === currentLocale.value)?.label || t('notifications.columns.language')
)

const applyLocalLocale = (locale: LocaleType) => {
  localeStore.setLocale(locale)
  setStoredLocaleSource('local')
}

const syncProfileLocale = async (locale: LocaleType): Promise<boolean> => {
  try {
    await userApi.updateProfile({ preferredLanguage: locale })
    setStoredLocaleSource('profile')
    if (userStore.userInfo) {
      userStore.userInfo.preferredLanguage = locale
    }
    return true
  } catch {
    setStoredLocaleSource('local')
    ElMessage.error(t('common.localeSwitcher.messages.profileSyncFailed'))
    return false
  }
}

const handleCommand = async (locale: LocaleType) => {
  if (locale === currentLocale.value) return

  // Guest users can only switch locally.
  if (!userStore.token) {
    applyLocalLocale(locale)
    return
  }

  try {
    await ElMessageBox.confirm(
      t('common.localeSwitcher.prompts.syncProfile'),
      t('common.localeSwitcher.title'),
      {
        type: 'info',
        distinguishCancelAndClose: true,
        confirmButtonText: t('common.localeSwitcher.actions.syncProfile'),
        cancelButtonText: t('common.localeSwitcher.actions.localOnly')
      }
    )

    applyLocalLocale(locale)
    const synced = await syncProfileLocale(locale)
    if (synced) {
      ElMessage.success(t('common.localeSwitcher.messages.profileSynced'))
    }
  } catch (action: unknown) {
    if (action === 'cancel') {
      applyLocalLocale(locale)
      ElMessage.success(t('common.localeSwitcher.messages.localOnlySwitched'))
    }
  }
}

onMounted(async () => {
  if (!localeStore.languagesLoaded) {
    await localeStore.initialize()
  }
})
</script>

<style scoped>
.locale-trigger {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  color: #606266;
  transition: color 0.3s;
}

.locale-trigger:hover {
  color: #409eff;
}

.locale-label {
  margin-left: 4px;
  font-size: 14px;
}

.is-active {
  color: #409eff;
  font-weight: 600;
}
</style>

