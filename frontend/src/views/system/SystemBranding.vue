<template>
  <div class="system-branding page-container">
    <div class="page-header">
      <div>
        <h2>{{ pageText.title }}</h2>
        <p>{{ pageText.subtitle }}</p>
      </div>
      <div class="header-actions">
        <el-button @click="resetDraft">
          {{ pageText.buttons.reset }}
        </el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="saveBranding"
        >
          {{ pageText.buttons.save }}
        </el-button>
      </div>
    </div>

    <div class="branding-layout">
      <div class="branding-config">
        <el-card
          shadow="never"
          class="config-card"
        >
          <template #header>
            <div class="card-title">
              {{ pageText.sections.identity }}
            </div>
          </template>
          <el-form label-width="120px">
            <el-form-item :label="pageText.fields.appName">
              <el-input
                v-model="draft.appName"
                maxlength="80"
                show-word-limit
              />
            </el-form-item>
            <el-form-item :label="pageText.fields.appShortName">
              <el-input
                v-model="draft.appShortName"
                maxlength="40"
                show-word-limit
              />
            </el-form-item>
            <el-form-item :label="pageText.fields.appTagline">
              <el-input
                v-model="draft.appTagline"
                maxlength="120"
                show-word-limit
              />
            </el-form-item>
            <el-form-item :label="pageText.fields.appIconText">
              <el-input
                v-model="draft.appIconText"
                maxlength="4"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card
          shadow="never"
          class="config-card"
        >
          <template #header>
            <div class="card-title">
              {{ pageText.sections.theme }}
            </div>
          </template>
          <el-form label-width="150px">
            <el-form-item :label="pageText.fields.primaryColor">
              <div class="color-row">
                <el-color-picker v-model="draft.theme.primaryColor" />
                <el-input v-model="draft.theme.primaryColor" />
              </div>
            </el-form-item>
            <el-form-item :label="pageText.fields.accentColor">
              <div class="color-row">
                <el-color-picker v-model="draft.theme.accentColor" />
                <el-input v-model="draft.theme.accentColor" />
              </div>
            </el-form-item>
            <el-form-item :label="pageText.fields.sidebarGradientStart">
              <div class="color-row">
                <el-color-picker v-model="draft.theme.sidebarGradientStart" />
                <el-input v-model="draft.theme.sidebarGradientStart" />
              </div>
            </el-form-item>
            <el-form-item :label="pageText.fields.sidebarGradientEnd">
              <div class="color-row">
                <el-color-picker v-model="draft.theme.sidebarGradientEnd" />
                <el-input v-model="draft.theme.sidebarGradientEnd" />
              </div>
            </el-form-item>
            <el-form-item :label="pageText.fields.borderRadius">
              <div class="slider-row">
                <el-slider
                  v-model="draft.theme.borderRadius"
                  :min="0"
                  :max="32"
                />
                <span>{{ draft.theme.borderRadius }}px</span>
              </div>
            </el-form-item>
            <el-form-item :label="pageText.fields.darkMode">
              <el-switch v-model="draft.theme.darkMode" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card
          shadow="never"
          class="config-card"
        >
          <template #header>
            <div class="card-title">
              {{ pageText.sections.login }}
            </div>
          </template>
          <el-form label-width="120px">
            <el-form-item :label="pageText.fields.loginTitle">
              <el-input
                v-model="draft.login.title"
                maxlength="80"
                show-word-limit
              />
            </el-form-item>
            <el-form-item :label="pageText.fields.loginSubtitle">
              <el-input
                v-model="draft.login.subtitle"
                type="textarea"
                :rows="3"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
            <el-form-item :label="pageText.fields.copyright">
              <el-input
                v-model="draft.login.copyright"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-form>
          <el-divider>{{ pageText.sections.loginI18n }}</el-divider>
          <el-tabs v-model="activeLocaleTab">
            <el-tab-pane
              :label="localeTabLabels['zh-CN']"
              name="zh-CN"
            >
              <el-form label-width="120px">
                <el-form-item :label="pageText.fields.loginTitle">
                  <el-input
                    v-model="draft.loginI18n['zh-CN'].title"
                    maxlength="80"
                    show-word-limit
                  />
                </el-form-item>
                <el-form-item :label="pageText.fields.loginSubtitle">
                  <el-input
                    v-model="draft.loginI18n['zh-CN'].subtitle"
                    type="textarea"
                    :rows="3"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
                <el-form-item :label="pageText.fields.copyright">
                  <el-input
                    v-model="draft.loginI18n['zh-CN'].copyright"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            <el-tab-pane
              :label="localeTabLabels['en-US']"
              name="en-US"
            >
              <el-form label-width="120px">
                <el-form-item :label="pageText.fields.loginTitle">
                  <el-input
                    v-model="draft.loginI18n['en-US'].title"
                    maxlength="80"
                    show-word-limit
                  />
                </el-form-item>
                <el-form-item :label="pageText.fields.loginSubtitle">
                  <el-input
                    v-model="draft.loginI18n['en-US'].subtitle"
                    type="textarea"
                    :rows="3"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
                <el-form-item :label="pageText.fields.copyright">
                  <el-input
                    v-model="draft.loginI18n['en-US'].copyright"
                    maxlength="200"
                    show-word-limit
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <el-card
          shadow="never"
          class="config-card"
        >
          <template #header>
            <div class="card-title">
              {{ pageText.sections.assets }}
            </div>
          </template>
          <div class="asset-grid">
            <div
              v-for="asset in assetDefinitions"
              :key="asset.field"
              class="asset-tile"
            >
              <div
                class="asset-preview"
                :class="{ 'is-wide': asset.field === 'loginBackgroundFileId' }"
              >
                <img
                  v-if="getAssetUrl(asset.field)"
                  :src="getAssetUrl(asset.field)"
                  :alt="asset.label"
                >
                <div
                  v-else
                  class="asset-placeholder"
                >
                  {{ asset.placeholder }}
                </div>
              </div>
              <div class="asset-content">
                <div class="asset-name">
                  {{ asset.label }}
                </div>
                <div class="asset-hint">
                  {{ asset.hint }}
                </div>
                <div class="asset-actions">
                  <el-upload
                    :show-file-list="false"
                    :accept="asset.accept"
                    :http-request="buildUploadRequestHandler(asset.field)"
                    :before-upload="buildBeforeUploadHandler(asset.field)"
                  >
                    <el-button>{{ pageText.actions.upload }}</el-button>
                  </el-upload>
                  <el-button
                    text
                    :disabled="!draft.assets[asset.field]"
                    @click="clearAsset(asset.field)"
                  >
                    {{ pageText.actions.remove }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <div class="branding-preview">
        <el-card
          shadow="never"
          class="preview-card"
        >
          <template #header>
            <div class="card-title">
              {{ pageText.sections.preview }}
            </div>
          </template>

          <div class="preview-shell">
            <div
              class="preview-sidebar"
              :style="sidebarStyle"
            >
              <div class="preview-sidebar-brand">
                <img
                  v-if="previewSidebarLogoUrl"
                  :src="previewSidebarLogoUrl"
                  :alt="draft.appName"
                  class="preview-logo"
                >
                <div
                  v-else
                  class="preview-logo-fallback"
                >
                  {{ draft.appIconText || 'G' }}
                </div>
                <div class="preview-brand-text">
                  <div class="preview-brand-name">
                    {{ draft.appShortName || draft.appName }}
                  </div>
                  <div class="preview-brand-tagline">
                    {{ draft.appTagline }}
                  </div>
                </div>
              </div>
              <div class="preview-nav-list">
                <span class="preview-nav-item active">{{ previewText.dashboard }}</span>
                <span class="preview-nav-item">{{ previewText.systemConfig }}</span>
                <span class="preview-nav-item">{{ pageText.title }}</span>
              </div>
            </div>
            <div class="preview-main">
              <div class="preview-topbar">
                <div class="preview-breadcrumb">
                  {{ draft.appName }}
                </div>
                <div
                  class="preview-chip"
                  :style="chipStyle"
                >
                  {{ draft.theme.primaryColor }}
                </div>
              </div>
              <div class="preview-content">
                <div class="preview-stat">
                  <span>{{ pageText.previewStats.primaryAction }}</span>
                  <el-button
                    type="primary"
                    round
                  >
                    {{ pageText.buttons.save }}
                  </el-button>
                </div>
                <div class="preview-stat">
                  <span>{{ pageText.previewStats.radius }}</span>
                  <strong>{{ draft.theme.borderRadius }}px</strong>
                </div>
              </div>
            </div>
          </div>

          <div
            class="preview-login"
            :style="loginPreviewStyle"
          >
            <div class="preview-login-overlay">
              <div
                class="preview-login-card"
                :style="loginCardStyle"
              >
                <img
                  v-if="previewLoginLogoUrl"
                  :src="previewLoginLogoUrl"
                  :alt="draft.appName"
                  class="preview-login-logo"
                >
                <div
                  v-else
                  class="preview-login-mark"
                >
                  {{ draft.appIconText || 'G' }}
                </div>
                <div class="preview-login-title">
                  {{ previewLoginCopy.title || draft.appName }}
                </div>
                <div class="preview-login-subtitle">
                  {{ previewLoginCopy.subtitle }}
                </div>
                <div
                  class="preview-login-button"
                  :style="buttonStyle"
                >
                  {{ $t('login.loginButton') }}
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { BrandingSettings } from '@/api/system/branding'
import { systemFileApi, validateFile } from '@/api/systemFile'
import { DEFAULT_BRANDING_SETTINGS, useBrandingStore } from '@/stores/branding'
import { useLocaleStore } from '@/stores/locale'

type AssetField = keyof BrandingSettings['assets']
type LocaleKey = 'zh-CN' | 'en-US'

interface UploadRequestLike {
  file: File
}

interface AssetDefinition {
  field: AssetField
  label: string
  hint: string
  placeholder: string
  accept: string
}

const BRANDING_COPY = {
  'zh-CN': {
    title: '品牌主题管理',
    subtitle: '统一管理系统主题、应用名称、Logo、图标和登录页体验。',
    buttons: {
      reset: '重置',
      save: '保存',
    },
    sections: {
      identity: '品牌标识',
      theme: '主题变量',
      login: '登录体验',
      loginI18n: '登录页多语言文案',
      assets: 'Logo 与图标资源',
      preview: '实时预览',
    },
    fields: {
      appName: '应用名称',
      appShortName: '简称',
      appTagline: '品牌副标题',
      appIconText: '兜底图标文字',
      primaryColor: '主色',
      accentColor: '强调色',
      sidebarGradientStart: '侧边栏渐变起点',
      sidebarGradientEnd: '侧边栏渐变终点',
      borderRadius: '圆角',
      darkMode: '深色模式',
      loginTitle: '登录主标题',
      loginSubtitle: '登录副标题',
      copyright: '页脚版权文案',
    },
    actions: {
      upload: '上传',
      remove: '移除',
    },
    previewStats: {
      primaryAction: '主操作按钮',
      radius: '组件圆角',
    },
    localeTabs: {
      'zh-CN': '简体中文',
      'en-US': 'English',
    },
    navigation: {
      dashboard: '工作台',
      systemConfig: '系统配置',
    },
    assets: {
      sidebarLogoFileId: {
        label: '侧边栏 Logo',
        hint: '用于桌面侧边栏和移动端抽屉。',
        placeholder: 'LOGO',
      },
      loginLogoFileId: {
        label: '登录页 Logo',
        hint: '显示在登录卡片的主视觉区域。',
        placeholder: 'LOGIN',
      },
      faviconFileId: {
        label: '站点图标',
        hint: '显示在浏览器标签页与收藏夹。',
        placeholder: 'ICON',
      },
      loginBackgroundFileId: {
        label: '登录背景图',
        hint: '用于认证页背景展示。',
        placeholder: 'BANNER',
      },
    },
    messages: {
      invalidFile: '文件格式或大小不符合要求。',
      assetUploaded: '品牌资源上传成功。',
      assetUploadFailed: '品牌资源上传失败。',
      brandingUpdated: '品牌主题已更新。',
      brandingSaveFailed: '品牌主题保存失败。',
    },
  },
  'en-US': {
    title: 'Branding Settings',
    subtitle: 'Manage the system theme, application identity, logo assets, and login experience from one place.',
    buttons: {
      reset: 'Reset',
      save: 'Save',
    },
    sections: {
      identity: 'Identity',
      theme: 'Theme Tokens',
      login: 'Login Experience',
      loginI18n: 'Login Copy by Locale',
      assets: 'Logo & Icon Assets',
      preview: 'Live Preview',
    },
    fields: {
      appName: 'Application Name',
      appShortName: 'Short Name',
      appTagline: 'Tagline',
      appIconText: 'Fallback Mark',
      primaryColor: 'Primary Color',
      accentColor: 'Accent Color',
      sidebarGradientStart: 'Sidebar Gradient Start',
      sidebarGradientEnd: 'Sidebar Gradient End',
      borderRadius: 'Border Radius',
      darkMode: 'Dark Mode',
      loginTitle: 'Login Title',
      loginSubtitle: 'Login Subtitle',
      copyright: 'Footer Copyright',
    },
    actions: {
      upload: 'Upload',
      remove: 'Remove',
    },
    previewStats: {
      primaryAction: 'Primary Action',
      radius: 'Component Radius',
    },
    localeTabs: {
      'zh-CN': 'Simplified Chinese',
      'en-US': 'English',
    },
    navigation: {
      dashboard: 'Dashboard',
      systemConfig: 'System Config',
    },
    assets: {
      sidebarLogoFileId: {
        label: 'Sidebar Logo',
        hint: 'Used in desktop sidebar and mobile drawer.',
        placeholder: 'LOGO',
      },
      loginLogoFileId: {
        label: 'Login Logo',
        hint: 'Shown on the login card hero block.',
        placeholder: 'LOGIN',
      },
      faviconFileId: {
        label: 'Favicon',
        hint: 'Shown in browser tabs and bookmarks.',
        placeholder: 'ICON',
      },
      loginBackgroundFileId: {
        label: 'Login Background',
        hint: 'Background illustration for the auth shell.',
        placeholder: 'BANNER',
      },
    },
    messages: {
      invalidFile: 'File type or size is not allowed.',
      assetUploaded: 'Brand asset uploaded.',
      assetUploadFailed: 'Failed to upload brand asset.',
      brandingUpdated: 'Branding updated.',
      brandingSaveFailed: 'Failed to save branding.',
    },
  },
} as const

const brandingStore = useBrandingStore()
const localeStore = useLocaleStore()
const saving = ref(false)
const activeLocaleTab = ref<LocaleKey>('zh-CN')

const cloneBranding = (value: BrandingSettings): BrandingSettings =>
  JSON.parse(JSON.stringify(value))

const currentLocale = computed<LocaleKey>(() =>
  localeStore.currentLocale === 'en-US' ? 'en-US' : 'zh-CN'
)

const localizedCopy = computed(() => BRANDING_COPY[currentLocale.value])
const pageText = computed(() => localizedCopy.value)

const localeTabLabels = computed(() => localizedCopy.value.localeTabs)
const previewText = computed(() => localizedCopy.value.navigation)

const ensureLoginI18nShape = (value: BrandingSettings): BrandingSettings => {
  value.loginI18n = {
    'zh-CN': {
      ...DEFAULT_BRANDING_SETTINGS.login,
      ...DEFAULT_BRANDING_SETTINGS.loginI18n?.['zh-CN'],
      ...value.loginI18n?.['zh-CN'],
    },
    'en-US': {
      ...DEFAULT_BRANDING_SETTINGS.login,
      ...DEFAULT_BRANDING_SETTINGS.loginI18n?.['en-US'],
      ...value.loginI18n?.['en-US'],
    },
  }
  return value
}

const draft = ref<BrandingSettings>(ensureLoginI18nShape(cloneBranding(DEFAULT_BRANDING_SETTINGS)))

const assetDefinitions = computed<Array<AssetDefinition>>(() => {
  const copy = localizedCopy.value.assets
  return [
    {
      field: 'sidebarLogoFileId',
      label: copy.sidebarLogoFileId.label,
      hint: copy.sidebarLogoFileId.hint,
      placeholder: copy.sidebarLogoFileId.placeholder,
      accept: 'image/*',
    },
    {
      field: 'loginLogoFileId',
      label: copy.loginLogoFileId.label,
      hint: copy.loginLogoFileId.hint,
      placeholder: copy.loginLogoFileId.placeholder,
      accept: 'image/*',
    },
    {
      field: 'faviconFileId',
      label: copy.faviconFileId.label,
      hint: copy.faviconFileId.hint,
      placeholder: copy.faviconFileId.placeholder,
      accept: '.ico,.png,.svg,image/*',
    },
    {
      field: 'loginBackgroundFileId',
      label: copy.loginBackgroundFileId.label,
      hint: copy.loginBackgroundFileId.hint,
      placeholder: copy.loginBackgroundFileId.placeholder,
      accept: 'image/*',
    },
  ]
})

const getResolvedAssetKey = (field: AssetField) => {
  const map: Record<AssetField, keyof NonNullable<BrandingSettings['resolvedAssets']>> = {
    sidebarLogoFileId: 'sidebarLogo',
    loginLogoFileId: 'loginLogo',
    faviconFileId: 'favicon',
    loginBackgroundFileId: 'loginBackground',
  }
  return map[field]
}

const getAssetUrl = (field: AssetField) => {
  const key = getResolvedAssetKey(field)
  return draft.value.resolvedAssets?.[key]?.thumbnailUrl || draft.value.resolvedAssets?.[key]?.url || ''
}

const previewSidebarLogoUrl = computed(() => getAssetUrl('sidebarLogoFileId'))
const previewLoginLogoUrl = computed(() => getAssetUrl('loginLogoFileId') || getAssetUrl('sidebarLogoFileId'))
const previewLoginCopy = computed(() => draft.value.loginI18n?.[activeLocaleTab.value] || draft.value.login)

const sidebarStyle = computed(() => ({
  background: `linear-gradient(180deg, ${draft.value.theme.sidebarGradientStart} 0%, ${draft.value.theme.sidebarGradientEnd} 100%)`,
}))

const chipStyle = computed(() => ({
  borderRadius: `${draft.value.theme.borderRadius}px`,
  background: `linear-gradient(135deg, ${draft.value.theme.primaryColor} 0%, ${draft.value.theme.accentColor} 100%)`,
}))

const buttonStyle = computed(() => ({
  borderRadius: `${draft.value.theme.borderRadius}px`,
  background: `linear-gradient(135deg, ${draft.value.theme.primaryColor} 0%, ${draft.value.theme.accentColor} 100%)`,
}))

const loginCardStyle = computed(() => ({
  borderRadius: `${Math.max(draft.value.theme.borderRadius + 8, 16)}px`,
}))

const loginPreviewStyle = computed(() => ({
  backgroundImage: getAssetUrl('loginBackgroundFileId')
    ? `linear-gradient(180deg, rgba(255,255,255,0.18), rgba(15,23,42,0.2)), url("${getAssetUrl('loginBackgroundFileId')}")`
    : `linear-gradient(135deg, ${draft.value.theme.primaryColor} 0%, ${draft.value.theme.accentColor} 100%)`,
}))

const beforeAssetUpload = (file: File, field: AssetField) => {
  const maxSize = field === 'faviconFileId' ? 2 * 1024 * 1024 : 8 * 1024 * 1024
  const result = validateFile(file, {
    maxSize,
    allowedTypes: field === 'faviconFileId'
      ? ['image/*', '.ico', '.png', '.svg']
      : ['image/*'],
  })

  if (!result.valid) {
    ElMessage.error(result.error || localizedCopy.value.messages.invalidFile)
    return false
  }
  return true
}

const buildBeforeUploadHandler = (field: AssetField) => {
  return (file: File) => beforeAssetUpload(file, field)
}

const handleAssetUpload = async (options: UploadRequestLike, field: AssetField) => {
  try {
    const uploaded = await systemFileApi.upload(options.file, {
      objectCode: 'SystemBranding',
      fieldCode: field,
      description: `Branding asset: ${field}`,
    })

    const resolvedKey = getResolvedAssetKey(field)
    draft.value.assets[field] = uploaded.id
    draft.value.resolvedAssets = {
      ...(draft.value.resolvedAssets || {}),
      [resolvedKey]: {
        id: uploaded.id,
        fileName: uploaded.fileName,
        fileType: uploaded.fileType,
        url: uploaded.url,
        thumbnailUrl: uploaded.thumbnailUrl || uploaded.url,
      }
    }
    ElMessage.success(localizedCopy.value.messages.assetUploaded)
  } catch (error) {
    console.error('[branding] upload failed', error)
    ElMessage.error(localizedCopy.value.messages.assetUploadFailed)
  }
}

const buildUploadRequestHandler = (field: AssetField) => {
  return (options: UploadRequestLike) => handleAssetUpload(options, field)
}

const clearAsset = (field: AssetField) => {
  const resolvedKey = getResolvedAssetKey(field)
  draft.value.assets[field] = null
  draft.value.resolvedAssets = {
    ...(draft.value.resolvedAssets || {}),
    [resolvedKey]: undefined,
  }
}

const resetDraft = () => {
  draft.value = ensureLoginI18nShape(cloneBranding(brandingStore.settings))
}

const saveBranding = async () => {
  saving.value = true
  try {
    const payload = ensureLoginI18nShape(cloneBranding(draft.value))
    const saved = await brandingStore.save(payload)
    draft.value = ensureLoginI18nShape(cloneBranding(saved))
    ElMessage.success(localizedCopy.value.messages.brandingUpdated)
  } catch (error) {
    console.error('[branding] save failed', error)
    ElMessage.error(localizedCopy.value.messages.brandingSaveFailed)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await localeStore.initialize()
  await brandingStore.refresh()
  draft.value = ensureLoginI18nShape(cloneBranding(brandingStore.settings))
})
</script>

<style scoped lang="scss">
.system-branding {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
}

.page-header p {
  margin: 8px 0 0;
  color: #64748b;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.branding-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(340px, 0.75fr);
  gap: 20px;
  align-items: start;
}

.branding-config {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.config-card,
.preview-card {
  border-radius: 18px !important;
}

.card-title {
  font-weight: 700;
  color: #0f172a;
}

.color-row {
  display: grid;
  grid-template-columns: 56px 1fr;
  gap: 12px;
  width: 100%;
  align-items: center;
}

.slider-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 16px;
  width: 100%;
  align-items: center;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.asset-tile {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 14px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}

.asset-preview {
  height: 160px;
  border-radius: 12px;
  background: #eff6ff;
  border: 1px dashed #bfdbfe;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.asset-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.asset-placeholder {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #3b82f6;
}

.asset-content {
  margin-top: 12px;
}

.asset-name {
  font-weight: 700;
  color: #0f172a;
}

.asset-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
  min-height: 32px;
}

.asset-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.branding-preview {
  position: sticky;
  top: 16px;
}

.preview-shell {
  display: grid;
  grid-template-columns: 180px 1fr;
  min-height: 280px;
  border: 1px solid #e2e8f0;
  border-radius: 22px;
  overflow: hidden;
  background: #fff;
}

.preview-sidebar {
  padding: 20px 16px;
  color: #fff;
}

.preview-sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.preview-logo,
.preview-logo-fallback {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
  object-fit: contain;
  padding: 6px;
}

.preview-brand-name {
  font-weight: 700;
}

.preview-brand-tagline {
  margin-top: 2px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.64);
}

.preview-nav-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-nav-item {
  display: block;
  border-radius: 10px;
  padding: 10px 12px;
  color: rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.06);
}

.preview-nav-item.active {
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
}

.preview-main {
  padding: 18px;
  background: #f8fafc;
}

.preview-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-breadcrumb {
  color: #475569;
  font-weight: 600;
}

.preview-chip {
  padding: 8px 12px;
  color: #fff;
  font-size: 12px;
}

.preview-content {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.preview-stat {
  min-height: 110px;
  border-radius: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.preview-login {
  margin-top: 18px;
  min-height: 300px;
  border-radius: 22px;
  overflow: hidden;
  background-size: cover;
  background-position: center;
}

.preview-login-overlay {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.2), rgba(15, 23, 42, 0.34));
}

.preview-login-card {
  width: 100%;
  max-width: 320px;
  padding: 28px 24px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(14px);
  text-align: center;
}

.preview-login-logo,
.preview-login-mark {
  width: 60px;
  height: 60px;
  margin: 0 auto 12px;
  border-radius: 16px;
  object-fit: contain;
  background: rgba(15, 23, 42, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-login-title {
  font-size: 24px;
  font-weight: 800;
  color: #0f172a;
}

.preview-login-subtitle {
  margin-top: 8px;
  color: #64748b;
  line-height: 1.5;
}

.preview-login-button {
  margin-top: 20px;
  padding: 12px 16px;
  color: #fff;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .branding-layout {
    grid-template-columns: 1fr;
  }

  .branding-preview {
    position: static;
  }
}

@media (max-width: 720px) {
  .page-header {
    flex-direction: column;
  }

  .asset-grid,
  .preview-content,
  .preview-shell {
    grid-template-columns: 1fr;
  }
}
</style>
