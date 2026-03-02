# 前端多语言组件设计

## 任务概述

为前端提供完整的多语言（i18n）支持方案，包括 vue-i18n 集成、动态语言包加载、多语言组件，以及与后端翻译服务的集成。

---

## 1. 设计目标

### 1.1 核心功能

| 功能 | 说明 |
|------|------|
| vue-i18n 集成 | 使用 vue-i18n 作为基础框架 |
| 动态语言包 | 从后端 API 动态加载翻译 |
| 语言切换 | 无刷新切换语言 |
| 组件级翻译 | 支持组件内嵌翻译 |
| 翻译指令 | `v-i18n` 指令简化使用 |
| 格式化工具 | 日期、数字、货币的本地化 |

### 1.2 技术选型

- **vue-i18n@9**: Vue 3 官方 i18n 方案
- **后端集成**: 从 Translation API 加载语言包
- **本地缓存**: localStorage 缓存语言包

---

## 国际化前端组件模型

### I18nProvider 组件模型

| 属性 | 类型 | 默认值 | 必需 | 说明 |
|------|------|--------|------|------|
| language | string | 'zh-CN' | 否 | 初始语言代码 |
| fallbackLanguage | string | 'en' | 否 | 回退语言代码 |
| messages | Record<string, string> | {} | 否 | 静态翻译消息 |
| loadFromAPI | boolean | true | 否 | 是否从 API 加载语言包 |
| cacheKey | string | 'locale' | 否 | localStorage 缓存键 |

### I18nProvider 事件模型

| 事件名 | 参数 | 说明 |
|--------|------|------|
| languageChanged | lang: string | 语言切换时触发 |
| languageLoaded | lang: string, messages: object | 语言包加载完成时触发 |
| languageError | error: Error | 语言加载失败时触发 |

### useI18n Composable 返回模型

| 属性 | 类型 | 说明 |
|------|------|------|
| locale | Ref<string> | 当前语言代码 (响应式) |
| t | (key: string, params?: object) => string | 翻译函数 (支持插值) |
| te | (key: string) => boolean | 检查翻译是否存在 |
| rt | (key: string) => string | 富文本翻译 |
| d | (value: Date, format?: string) => string | 日期格式化 |
| n | (value: number, options?: object) => string | 数字格式化 |
| setLocale | (lang: string) => Promise<void> | 设置语言 (异步加载) |
| switchLocale | (lang: string) => Promise<void> | 切换语言 (并更新 localStorage) |
| isLocale | (lang: string) => boolean | 检查是否为指定语言 |
| translateEnum | (namespace: string, value: string, default?: string) => string | 翻译枚举值 |
| translateBatch | (keys: string[]) => string[] | 批量翻译 |
| locales | Ref<LocaleInfo[]> | 可用语言列表 |

### LocaleInfo 对象模型

| 属性 | 类型 | 说明 |
|------|------|------|
| code | string | 语言代码 (zh-CN, en-US) |
| name | string | 语言名称 (简体中文, English) |
| native_name | string | 本地语言名称 |
| flag | string | 语言图标 (🇨🇳, 🇺🇸) |
| is_default | boolean | 是否为默认语言 |

### v-i18n 指令模型

| 指令用法 | 参数 | 说明 |
|---------|------|------|
| `v-i18n="'key'"` | 翻译键字符串 | 简单文本翻译 |
| `v-i18n="{key: 'key', params: {}}"` | 对象 | 带参数的翻译 |
| `v-i18n:text="'key'"` | 翻译键 | 修改文本内容 |
| `v-i18n:placeholder="'key'"` | 翻译键 | 修改指定属性 |
| `v-i18n:title="'key'"` | 翻译键 | 修改 title 属性 |

### LanguageSwitcher 组件模型

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| showFlag | boolean | true | 是否显示语言图标 |
| showName | boolean | true | 是否显示语言名称 |
| trigger | string | 'click' | 触发方式 (click/hover) |
| placement | string | 'bottom' | 下拉菜单位置 |

| 事件 | 参数 | 说明 |
|------|------|------|
| change | lang: string | 语言切换时触发 |

### 格式化工具函数模型

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| formatDate | date: Date, format?: string | string | 日期格式化 |
| formatRelativeTime | date: Date | string | 相对时间格式化 |
| formatNumber | value: number, options?: object | string | 数字格式化 |
| formatCurrency | value: number, currency?: string | string | 货币格式化 |
| formatPercent | value: number, decimals?: number | string | 百分比格式化 |
| formatFileSize | bytes: number | string | 文件大小格式化 |

---

## 2. 文件结构

```
frontend/src/
├── i18n/
│   ├── index.js                  # i18n 配置入口
│   ├── locales/                  # 本地语言包（静态）
│   │   ├── zh-CN.js             # 中文（默认）
│   │   └── en-US.js             # 英文
│   └── utils/
│       ├── currency.js           # 货币格式化
│       ├── date.js               # 日期格式化
│       └── number.js             # 数字格式化
├── composables/
│   └── useI18n.js                # i18n 组合函数
├── directives/
│   └── i18n.js                   # v-i18n 指令
└── api/
    └── i18n.js                   # 翻译 API
```

---

## 3. i18n 配置

### 3.1 入口配置

#### 文件结构

| 文件 | 说明 |
|------|------|
| `src/i18n/index.js` | i18n 配置入口 |
| `src/i18n/locales/zh-CN.js` | 中文语言包 |
| `src/i18n/locales/en-US.js` | 英文语言包 |

#### createI18n 配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `legacy` | `false` | 使用 Composition API 模式 |
| `locale` | `'zh-CN'` | 默认语言 |
| `fallbackLocale` | `'zh-CN'` | 回退语言 |
| `globalInjection` | `true` | 允许全局使用 `$t` |
| `missing` | `function` | 缺失翻译时的处理函数 |

#### 导出函数

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `loadLanguagePack` | `lang: str` | `Promise<void>` | 动态加载语言包 (从 API 或缓存) |
| `loadLanguagePackFromCache` | `lang: str` | `bool` | 从 localStorage 加载语言包 |
| `getCurrentLocale` | - | `str` | 获取当前语言代码 |
| `setLocale` | `lang: str` | `Promise<void>` | 设置当前语言并更新 localStorage |

#### 语言包缓存

| 缓存键 | 格式 | 说明 |
|--------|------|------|
| `locale` | `lang_code` | 当前语言代码 |
| `locale_{lang}` | `JSON string` | 语言包翻译数据 |

### 3.2 默认语言包

```javascript
// frontend/src/i18n/locales/zh-CN.js

export default {
  // 通用
  common: {
    appName: '钩子固定资产',
    actions: {
      confirm: '确认',
      cancel: '取消',
      save: '保存',
      delete: '删除',
      edit: '编辑',
      view: '查看',
      search: '搜索',
      reset: '重置',
      export: '导出',
      import: '导入',
      refresh: '刷新',
      close: '关闭',
      submit: '提交',
      back: '返回',
      more: '更多'
    },
    status: {
      loading: '加载中...',
      noData: '暂无数据',
      error: '操作失败',
      success: '操作成功'
    },
    messages: {
      deleteConfirm: '确定要删除吗？',
      deleteSuccess: '删除成功',
      saveSuccess: '保存成功',
      operationSuccess: '操作成功',
      operationFailed: '操作失败',
      networkError: '网络错误，请稍后重试'
    },
    validation: {
      required: '此项为必填项',
      email: '请输入有效的邮箱地址',
      phone: '请输入有效的手机号',
      url: '请输入有效的URL'
    }
  },

  // 资产模块
  assets: {
    title: '资产管理',
    fields: {
      code: '资产编码',
      name: '资产名称',
      category: '资产分类',
      status: '资产状态',
      location: '存放位置',
      purchasePrice: '采购价格',
      purchaseDate: '采购日期'
    },
    status: {
      idle: '闲置',
      inUse: '使用中',
      maintenance: '维修中',
      scrapped: '已报废'
    },
    actions: {
      create: '新建资产',
      edit: '编辑资产',
      delete: '删除资产',
      transfer: '资产调拨',
      scrap: '资产报废'
    }
  },

  // 权限模块
  permissions: {
    title: '权限管理',
    denied: '您没有权限执行此操作',
    loginRequired: '请先登录'
  }
}
```

```javascript
// frontend/src/i18n/locales/en-US.js

export default {
  common: {
    appName: 'Hook Fixed Assets',
    actions: {
      confirm: 'Confirm',
      cancel: 'Cancel',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      view: 'View',
      search: 'Search',
      reset: 'Reset',
      export: 'Export',
      import: 'Import',
      refresh: 'Refresh',
      close: 'Close',
      submit: 'Submit',
      back: 'Back',
      more: 'More'
    },
    status: {
      loading: 'Loading...',
      noData: 'No Data',
      error: 'Operation Failed',
      success: 'Operation Successful'
    },
    messages: {
      deleteConfirm: 'Are you sure you want to delete?',
      deleteSuccess: 'Deleted successfully',
      saveSuccess: 'Saved successfully',
      operationSuccess: 'Operation successful',
      operationFailed: 'Operation failed',
      networkError: 'Network error, please try again later'
    },
    validation: {
      required: 'This field is required',
      email: 'Please enter a valid email address',
      phone: 'Please enter a valid phone number',
      url: 'Please enter a valid URL'
    }
  },

  assets: {
    title: 'Asset Management',
    fields: {
      code: 'Asset Code',
      name: 'Asset Name',
      category: 'Asset Category',
      status: 'Asset Status',
      location: 'Location',
      purchasePrice: 'Purchase Price',
      purchaseDate: 'Purchase Date'
    },
    status: {
      idle: 'Idle',
      inUse: 'In Use',
      maintenance: 'Under Maintenance',
      scrapped: 'Scrapped'
    },
    actions: {
      create: 'Create Asset',
      edit: 'Edit Asset',
      delete: 'Delete Asset',
      transfer: 'Transfer Asset',
      scrap: 'Scrap Asset'
    }
  },

  permissions: {
    title: 'Permission Management',
    denied: 'You do not have permission to perform this action',
    loginRequired: 'Please login first'
  }
}
```

---

## 4. useI18n 组合函数

### 4.1 实现

```javascript
// frontend/src/composables/useI18n.js

import { computed } from 'vue'
import { useI18n as useVueI18n } from 'vue-i18n'
import { setLocale, getCurrentLocale } from '@/i18n'

export function useI18n() {
  const { t, locale, availableLocales } = useVueI18n()

  /**
   * 获取翻译文本
   */
  const translate = (key, params = {}) => {
    return t(key, params)
  }

  /**
   * 获取当前语言
   */
  const currentLocale = computed(() => getCurrentLocale())

  /**
   * 可用语言列表
   */
  const locales = computed(() => [
    { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
    { code: 'en-US', name: 'English', flag: '🇺🇸' }
  ])

  /**
   * 切换语言
   */
  const switchLocale = async (lang) => {
    await setLocale(lang)
    // 可选：刷新页面以应用某些全局更改
    // window.location.reload()
  }

  /**
   * 检查是否为指定语言
   */
  const isLocale = (lang) => {
    return currentLocale.value === lang
  }

  /**
   * 翻译枚举值
   */
  const translateEnum = (namespace, value, defaultText = null) => {
    return translate(`${namespace}.${value}`) || defaultText || value
  }

  /**
   * 批量翻译
   */
  const translateBatch = (keys) => {
    return keys.map(key => translate(key))
  }

  return {
    // vue-i18n 方法
    t: translate,
    te: (key) => !!translate(key), // 检查翻译是否存在
    rt: (key) => translate(key), // 富文本翻译
    d: (value) => value, // 日期时间（需要额外配置）
    n: (value) => value, // 数字（需要额外配置）

    // 自定义方法
    locale: currentLocale,
    locales,
    switchLocale,
    isLocale,
    translateEnum,
    translateBatch
  }
}
```

### 4.2 使用示例

```vue
<script setup>
import { useI18n } from '@/composables/useI18n'

const { t, locale, switchLocale, translateEnum } = useI18n()

// 获取翻译
const saveText = t('common.actions.save')  // '保存'
const title = t('assets.title')            // '资产管理'

// 翻译枚举值
const statusText = translateEnum('assets.status', 'idle')  // '闲置'

// 切换语言
const handleLanguageChange = (lang) => {
  switchLocale(lang)
}
</script>

<template>
  <div>
    <h1>{{ title }}</h1>
    <el-button>{{ t('common.actions.save') }}</el-button>
    <el-select v-model="locale" @change="switchLocale">
      <el-option label="简体中文" value="zh-CN" />
      <el-option label="English" value="en-US" />
    </el-select>
  </div>
</template>
```

---

## 5. v-i18n 指令

### 5.1 实现

```javascript
// frontend/src/directives/i18n.js

import { useI18n as useVueI18n } from 'vue-i18n'

/**
 * 翻译指令
 *
 * 用法:
 * v-i18n="'common.actions.save'"              - 简单翻译
 * v-i18n="{key: 'common.hello', params: {name: 'John'}}"  - 带参数
 * v-i18n:text="'common.actions.save'"        - 修改文本内容
 * v-i18n:placeholder="'common.search'"        - 修改属性
 */
export const i18n = {
  mounted(el, binding) {
    updateI18n(el, binding)
  },
  updated(el, binding) {
    updateI18n(el, binding)
  }
}

function updateI18n(el, binding) {
  const { t } = useVueI18n()

  let key, params

  if (typeof binding.value === 'string') {
    key = binding.value
  } else if (typeof binding.value === 'object') {
    key = binding.value.key
    params = binding.value.params
  } else {
    return
  }

  const translated = t(key, params || {})

  if (binding.arg) {
    // 修改属性
    el.setAttribute(binding.arg, translated)
  } else {
    // 修改文本内容
    el.textContent = translated
  }
}
```

### 5.2 注册

```javascript
// frontend/src/directives/index.js

import { i18n } from './i18n'

export default {
  install(app) {
    app.directive('i18n', i18n)
  }
}
```

### 5.3 使用示例

```vue
<template>
  <!-- 翻译文本内容 -->
  <button v-i18n="'common.actions.save'">保存</button>

  <!-- 翻译属性 -->
  <input v-i18n:placeholder="'common.search'" />

  <!-- 带参数的翻译 -->
  <span v-i18n="{key: 'common.hello', params: {name: userName}}" />
</template>
```

---

## 6. 翻译 API

### 6.1 API 定义

```javascript
// frontend/src/api/i18n.js

import request from '@/utils/request'

export const translationApi = {
  /**
   * 获取前端语言包
   */
  getLanguagePack(lang) {
    return request({
      url: '/api/translations/language_pack/',
      method: 'get',
      params: { lang }
    })
  },

  /**
   * 获取所有命名空间
   */
  getNamespaces() {
    return request({
      url: '/api/translations/namespaces/',
      method: 'get'
    })
  },

  /**
   * 获取所有启用的语言
   */
  getLanguages() {
    return request({
      url: '/api/translations/languages/',
      method: 'get'
    })
  },

  /**
   * 同步翻译
   */
  syncTranslations(namespace, translations) {
    return request({
      url: '/api/translations/sync/',
      method: 'post',
      data: { namespace, translations }
    })
  },

  /**
   * 清除翻译缓存
   */
  clearCache() {
    return request({
      url: '/api/translations/clear_cache/',
      method: 'post'
    })
  }
}
```

---

## 7. 格式化工具

### 7.1 日期格式化

```javascript
// frontend/src/i18n/utils/date.js

import { useI18n as useVueI18n } from 'vue-i18n'

/**
 * 日期格式化
 */
export function formatDate(date, format = 'short') {
  if (!date) return ''

  const { locale } = useVueI18n()

  const options = {
    short: { year: 'numeric', month: '2-digit', day: '2-digit' },
    long: { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' },
    full: { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long', hour: '2-digit', minute: '2-digit' }
  }

  return new Date(date).toLocaleDateString(locale.value, options[format] || options.short)
}

/**
 * 相对时间格式化
 */
export function formatRelativeTime(date) {
  if (!date) return ''

  const { locale } = useVueI18n()
  const now = new Date()
  const target = new Date(date)
  const diff = (now - target) / 1000 // 秒

  const rtf = new Intl.RelativeTimeFormat(locale.value, { numeric: 'auto' })

  if (diff < 60) return rtf.format(-Math.floor(diff), 'second')
  if (diff < 3600) return rtf.format(-Math.floor(diff / 60), 'minute')
  if (diff < 86400) return rtf.format(-Math.floor(diff / 3600), 'hour')
  if (diff < 2592000) return rtf.format(-Math.floor(diff / 86400), 'day')
  if (diff < 31536000) return rtf.format(-Math.floor(diff / 2592000), 'month')
  return rtf.format(-Math.floor(diff / 31536000), 'year')
}
```

### 7.2 数字格式化

```javascript
// frontend/src/i18n/utils/number.js

import { useI18n as useVueI18n } from 'vue-i18n'

/**
 * 数字格式化
 */
export function formatNumber(value, options = {}) {
  if (value === null || value === undefined) return ''

  const { locale } = useVueI18n()

  return new Intl.NumberFormat(locale.value, options).format(value)
}

/**
 * 货币格式化
 */
export function formatCurrency(value, currency = 'CNY') {
  return formatNumber(value, {
    style: 'currency',
    currency: currency
  })
}

/**
 * 百分比格式化
 */
export function formatPercent(value, decimals = 2) {
  return formatNumber(value / 100, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * 文件大小格式化
 */
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B'

  const { locale } = useVueI18n()
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const size = bytes / Math.pow(1024, i)

  return `${formatNumber(size, { maximumFractionDigits: 2 })} ${units[i]}`
}
```

---

## 8. 语言切换组件

### 8.1 LanguageSwitcher 组件

```vue
<!-- frontend/src/components/common/LanguageSwitcher.vue -->

<template>
  <el-dropdown @command="handleLanguageChange" trigger="click">
    <span class="language-switcher">
      <span class="flag">{{ currentLocale.flag }}</span>
      <span class="name">{{ currentLocale.name }}</span>
      <el-icon><ArrowDown /></el-icon>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="lang in locales"
          :key="lang.code"
          :command="lang.code"
          :class="{ active: lang.code === locale }"
        >
          <span class="flag">{{ lang.flag }}</span>
          <span class="name">{{ lang.name }}</span>
          <el-icon v-if="lang.code === locale"><Check /></el-icon>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowDown, Check } from '@element-plus/icons-vue'
import { useI18n } from '@/composables/useI18n'

const { locale, locales, switchLocale } = useI18n()

const currentLocale = computed(() => {
  return locales.value.find(l => l.code === locale.value) || locales.value[0]
})

const handleLanguageChange = (lang) => {
  switchLocale(lang)
}
</script>

<style scoped>
.language-switcher {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.flag {
  font-size: 18px;
}

.name {
  font-size: 14px;
}

.el-dropdown-menu__item {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 140px;
}

.el-dropdown-menu__item.active {
  color: var(--el-color-primary);
}
</style>
```

---

## 9. 在 main.js 中集成

```javascript
// frontend/src/main.js

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import directives from './directives'

// 初始化语言
const savedLocale = localStorage.getItem('locale') || 'zh-CN'
i18n.global.locale.value = savedLocale
document.documentElement.lang = savedLocale

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus)
app.use(i18n)
app.use(directives)

// Element Plus 多语言配置
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import en from 'element-plus/es/locale/lang/en'
import * as ElementPlusLocale from 'element-plus/es/locale'

app.use(ElementPlus, {
  locale: savedLocale === 'zh-CN' ? zhCn : en
})

app.mount('#app')
```

---

## 10. 输出产物

| 文件 | 说明 |
|------|------|
| `frontend/src/i18n/index.js` | i18n 配置入口 |
| `frontend/src/i18n/locales/zh-CN.js` | 中文语言包 |
| `frontend/src/i18n/locales/en-US.js` | 英文语言包 |
| `frontend/src/i18n/utils/currency.js` | 货币格式化 |
| `frontend/src/i18n/utils/date.js` | 日期格式化 |
| `frontend/src/i18n/utils/number.js` | 数字格式化 |
| `frontend/src/composables/useI18n.js` | i18n 组合函数 |
| `frontend/src/directives/i18n.js` | v-i18n 指令 |
| `frontend/src/components/common/LanguageSwitcher.vue` | 语言切换组件 |
| `frontend/src/api/i18n.js` | 翻译 API |

---

## 11. 使用场景总结

| 场景 | 使用方式 | 示例 |
|------|---------|------|
| 模板翻译 | `{{ $t('key') }}` | `<h1>{{ $t('assets.title') }}</h1>` |
| 脚本翻译 | `useI18n()` | `const { t } = useI18n()` |
| 指令翻译 | `v-i18n` | `<button v-i18n="'common.save'">` |
| 枚举翻译 | `translateEnum()` | 翻译状态选项 |
| 语言切换 | `switchLocale()` | 无刷新切换 |
| 日期格式化 | `formatDate()` | 本地化日期显示 |
| 货币格式化 | `formatCurrency()` | 本地化货币显示 |
