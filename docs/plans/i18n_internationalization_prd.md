# 前端多语言国际化 (i18n) 产品需求文档

## 1. 目标与背景

### 1.1 背景
GZEAMS 固定资产管理系统当前前端硬编码使用中文，无法支持多语言切换。随着业务扩展至海外市场或服务多语言用户群体，需要实现完整的国际化支持。

### 1.2 目标
- **支持语言**：中文简体（zh-CN，默认）、英文（en-US）
- **可扩展性**：支持快速添加其他语言（如繁体中文、日语等）
- **用户体验**：语言切换即时生效，无需刷新页面
- **持久化**：记住用户语言偏好

---

## 2. 当前状态分析

### 2.1 技术栈
| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.4.21 | 组合式 API (Composition API) |
| Vite | 5.1.5 | 构建工具 |
| Element Plus | 2.5.6 | UI 组件库 |
| Pinia | 2.1.7 | 状态管理 |
| Vue Router | 4.3.0 | 路由管理 |

### 2.2 当前 i18n 状态
- **Element Plus**：已使用 `zh-cn` locale，但硬编码在 `main.ts`
- **业务文本**：所有组件、视图中直接使用中文字符串
- **无 i18n 库**：未安装 vue-i18n 或类似库

### 2.3 需要国际化的内容范围

#### 主要涉及文件统计
| 类别 | 数量 | 典型文件示例 |
|------|------|-------------|
| 视图 (views/) | 82+ | Dashboard.vue, AssetList.vue |
| 通用组件 (components/common/) | 20+ | BaseListPage.vue, BaseFormPage.vue |
| 引擎组件 (components/engine/) | 44+ | DynamicForm.vue, FieldRenderer.vue |
| 布局 (layouts/) | 2 | MainLayout.vue, AuthLayout.vue |
| 路由配置 (router/) | 1 | index.ts (450+ 行) |
| Store (stores/) | 5 | user.ts, notification.ts |

---

## 3. 技术方案

### 3.1 推荐方案：Vue I18n + Element Plus 集成

### 3.2 依赖安装

```bash
npm install vue-i18n@9
```

### 3.3 目录结构设计

```
frontend/src/
├── locales/                    # 翻译资源目录
│   ├── index.ts               # i18n 配置入口
│   ├── zh-CN/                 # 中文翻译
│   │   ├── index.ts           # 聚合导出
│   │   ├── common.json        # 通用词汇
│   │   ├── menu.json          # 菜单
│   │   ├── dashboard.json     # 仪表板
│   │   ├── assets.json        # 资产模块
│   │   └── ...                # 其他模块
│   ├── en-US/                 # 英文翻译
│   │   └── ... (相同结构)
├── stores/
│   └── locale.ts              # 语言设置 store
└── main.ts                    # 注册 i18n 插件
```

---

## 4. 详细设计

### 4.1 i18n 配置初始化

#### `src/locales/index.ts`
```typescript
import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'

export const SUPPORT_LOCALES = ['zh-CN', 'en-US'] as const
export type LocaleType = typeof SUPPORT_LOCALES[number]

const i18n = createI18n({
  legacy: false,                    // 使用 Composition API 模式
  locale: localStorage.getItem('locale') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  },
  globalInjection: true             // 允许在模板中使用 $t
})

export default i18n
```

### 4.2 翻译资源结构示例

#### `src/locales/zh-CN/common.json`
```json
{
  "actions": {
    "search": "搜索",
    "reset": "重置",
    "create": "新建",
    "save": "保存",
    "cancel": "取消"
  },
  "placeholders": {
    "input": "请输入{field}",
    "select": "请选择{field}"
  },
  "messages": {
    "operationSuccess": "操作成功",
    "operationFailed": "操作失败"
  }
}
```

### 4.3 语言持久化 Store

#### `src/stores/locale.ts`
```typescript
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import i18n, { type LocaleType, SUPPORT_LOCALES } from '@/locales'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'

const ELEMENT_LOCALES = {
  'zh-CN': zhCn,
  'en-US': en
}

export const useLocaleStore = defineStore('locale', () => {
  const currentLocale = ref<LocaleType>(
    (localStorage.getItem('locale') as LocaleType) || 'zh-CN'
  )
  
  const elementLocale = ref(ELEMENT_LOCALES[currentLocale.value])

  const setLocale = (locale: LocaleType) => {
    if (!SUPPORT_LOCALES.includes(locale)) return
    
    currentLocale.value = locale
    i18n.global.locale.value = locale
    elementLocale.value = ELEMENT_LOCALES[locale]
    localStorage.setItem('locale', locale)
  }

  return { currentLocale, elementLocale, setLocale, supportedLocales: SUPPORT_LOCALES }
})
```

---

## 5. 组件改造示例

### 5.1 模板改造

**改造前：**
```vue
<el-button type="primary" @click="handleSearch">搜索</el-button>
```

**改造后：**
```vue
<el-button type="primary" @click="handleSearch">{{ $t('common.actions.search') }}</el-button>
```

### 5.2 Script 改造（状态映射）

**改造前：**
```typescript
const statusMap = {
  'idle': { label: '闲置', color: '#67C23A' },
  'in_use': { label: '使用中', color: '#409EFF' },
}
```

**改造后：**
```typescript
import { useI18n } from 'vue-i18n'
const { t } = useI18n()

const statusMap = computed(() => ({
  'idle': { label: t('assets.status.idle'), color: '#67C23A' },
  'in_use': { label: t('assets.status.inUse'), color: '#409EFF' },
}))
```

---

## 6. 实施计划

| 阶段 | 内容 | 预计工时 |
|------|------|----------|
| Phase 1 | 基础设施搭建（vue-i18n、locales 目录、store、语言切换组件） | 2 天 |
| Phase 2 | 通用组件国际化（BaseListPage、BaseFormPage、BaseDetailPage 等） | 3 天 |
| Phase 3 | 布局与导航国际化（MainLayout、路由 meta.title） | 1 天 |
| Phase 4 | 业务模块国际化（Dashboard、Assets、Workflow、System 等） | 5 天 |
| Phase 5 | 测试与优化 | 2 天 |
| **合计** | | **13 天** |

---

## 7. 验收标准

| ID | 验收项 | 标准 |
|----|--------|------|
| AC-1 | 语言切换 | 用户可在 Header 区域切换语言，切换后 UI 即时更新 |
| AC-2 | 语言持久化 | 刷新页面后保持用户选择的语言 |
| AC-3 | Element Plus 组件 | 日期选择器、分页等组件文本跟随语言切换 |
| AC-4 | 业务文本 | 所有按钮、标签、提示信息正确显示对应语言 |
| AC-5 | 菜单导航 | 导航菜单根据语言显示正确翻译 |
| AC-6 | 表单占位符 | 输入框、选择框占位符显示正确语言 |
| AC-7 | 响应式 | 移动端语言切换功能正常 |

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 翻译缺失 | 显示 key 而非文本 | 配置 fallbackLocale，开发时开启翻译警告 |
| 动态内容翻译 | 后端返回的中文无法翻译 | 后端配合返回翻译 key 或多语言字段 |
| 包体积增加 | 增加语言包体积 | 使用按需加载，懒加载语言包 |

---

## 9. 未来扩展

- **多语言管理后台**：提供 Web 界面编辑翻译内容
- **自动翻译集成**：集成翻译 API 辅助翻译
- **RTL 支持**：支持阿拉伯语等从右到左书写语言
- **语言检测**：根据浏览器设置自动选择语言
