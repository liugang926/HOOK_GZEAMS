<template>
  <div
    class="main-layout"
    :class="{ 'sidebar-collapsed': isCollapsed }"
  >
    <el-container>
      <!-- Sidebar -->
      <el-aside
        v-if="!isMobile"
        :width="isCollapsed ? '64px' : '220px'"
        class="sidebar"
      >
        <div class="sidebar-header">
          <h1 class="logo">
            <span class="logo-icon">{{ $t('common.brand.icon') }}</span>
            <transition name="fade">
              <span
                v-if="!isCollapsed"
                class="logo-text"
              >{{ $t('common.brand.name') }}</span>
            </transition>
          </h1>
        </div>

        <el-scrollbar class="sidebar-menu-scroll">
          <el-menu
            :default-active="activeMenu"
            router
            :collapse="isCollapsed"
            :collapse-transition="true"
            class="sidebar-menu"
            background-color="transparent"
            text-color="rgba(255,255,255,0.7)"
            active-text-color="#ffffff"
          >
            <el-menu-item
              index="/dashboard"
              class="sidebar-menu-item"
            >
              <el-icon><Odometer /></el-icon>
              <template #title>
                {{ $t('menu.menu.dashboard') }}
              </template>
            </el-menu-item>

            <template
              v-for="(group, groupIdx) in menuGroups"
              :key="getMenuGroupIdentity(group, groupIdx)"
            >
              <!-- Multi-item group to sub-menu -->
              <el-sub-menu
                v-if="group.items.length > 1"
                :index="getMenuGroupIdentity(group, groupIdx)"
                class="sidebar-sub-menu"
              >
                <template #title>
                  <el-icon v-if="group.icon">
                    <component :is="resolveIcon(group.icon)" />
                  </el-icon>
                  <span>{{ getGroupLabel(group) }}</span>
                </template>
                <el-menu-item
                  v-for="item in group.items"
                  :key="item.code"
                  :index="item.url"
                >
                  <el-icon v-if="item.icon">
                    <component :is="resolveIcon(item.icon)" />
                  </el-icon>
                  <template #title>
                    {{ getItemLabel(item) }}
                  </template>
                </el-menu-item>
              </el-sub-menu>

              <!-- Single-item group to direct menu item -->
              <el-menu-item
                v-else-if="group.items.length === 1"
                :key="group.items[0].code"
                :index="group.items[0].url"
                class="sidebar-menu-item"
              >
                <el-icon v-if="group.items[0].icon">
                  <component :is="resolveIcon(group.items[0].icon)" />
                </el-icon>
                <template #title>
                  {{ getItemLabel(group.items[0]) }}
                </template>
              </el-menu-item>
            </template>
          </el-menu>
        </el-scrollbar>

        <!-- Collapse toggle -->
        <div
          class="sidebar-footer"
          @click="toggleCollapse"
        >
          <el-icon :size="18">
            <Fold v-if="!isCollapsed" />
            <Expand v-else />
          </el-icon>
          <transition name="fade">
            <span
              v-if="!isCollapsed"
              class="collapse-label"
            >{{ $t('common.actions.collapse') }}</span>
          </transition>
        </div>
      </el-aside>

      <!-- Mobile Drawer -->
      <el-drawer
        v-model="drawerVisible"
        v-focus-trap.autofocus="drawerVisible"
        direction="ltr"
        size="240px"
        :with-header="false"
        class="mobile-drawer"
      >
        <div class="drawer-menu-container">
          <div class="drawer-logo">
            <span class="logo-icon">{{ $t('common.brand.icon') }}</span> {{ $t('common.brand.name') }}
          </div>
          <el-menu
            :default-active="activeMenu"
            router
            class="mobile-menu"
            @select="drawerVisible = false"
          >
            <el-menu-item index="/dashboard">
              <el-icon><Odometer /></el-icon>
              <span>{{ $t('menu.menu.dashboard') }}</span>
            </el-menu-item>
            <template
              v-for="(group, groupIdx) in menuGroups"
              :key="getMenuGroupIdentity(group, groupIdx)"
            >
              <el-sub-menu
                v-if="group.items.length > 1"
                :index="getMenuGroupIdentity(group, groupIdx)"
              >
                <template #title>
                  {{ getGroupLabel(group) }}
                </template>
                <el-menu-item
                  v-for="item in group.items"
                  :key="item.code"
                  :index="item.url"
                >
                  {{ getItemLabel(item) }}
                </el-menu-item>
              </el-sub-menu>
              <el-menu-item
                v-else-if="group.items.length === 1"
                :index="group.items[0].url"
              >
                {{ getItemLabel(group.items[0]) }}
              </el-menu-item>
            </template>
          </el-menu>
        </div>
      </el-drawer>

      <!-- Main content column -->
      <el-container class="main-container">
        <!-- Top header bar -->
        <el-header
          class="top-header"
          height="56px"
        >
          <div class="header-left">
            <el-button
              v-if="isMobile"
              :icon="Menu"
              class="mobile-menu-btn"
              text
              @click="drawerVisible = true"
            />
            <!-- Breadcrumb -->
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/dashboard' }">
                {{ $t('menu.menu.dashboard') }}
              </el-breadcrumb-item>
              <el-breadcrumb-item
                v-for="crumb in breadcrumbs"
                :key="crumb.path"
                :to="crumb.to"
              >
                {{ crumb.label }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <div class="header-right">
            <LocaleSwitcher />
            <NotificationBell />
          </div>
        </el-header>

        <!-- Page content -->
        <el-main class="page-main">
          <router-view v-slot="{ Component }">
            <transition
              name="page-fade"
              mode="out-in"
            >
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, shallowRef, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Menu, Fold, Expand, Odometer } from '@element-plus/icons-vue'
import NotificationBell from '@/components/layout/NotificationBell.vue'
import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import { businessObjectApi, menuApi, type BusinessObject, type MenuGroup, type MenuItem } from '@/api/system'
import { translateObjectCodeLabel, resolveObjectDisplayName } from '@/utils/objectDisplay'
import * as ElementPlusIcons from '@element-plus/icons-vue'

interface LocalMenuItem extends MenuItem {
  code: string
  name: string
  url: string
}

interface LocalMenuGroup extends MenuGroup {
  code?: string
  items: LocalMenuItem[]
}

type AnyRecord = Record<string, unknown>
const AUTO_DYNAMIC_ENTRY_EXCLUDE_CODES = new Set<string>([
  'Role'
])

const route = useRoute()
const { t, te } = useI18n()
const activeMenu = computed(() => route.path)
const drawerVisible = ref(false)
const isMobile = ref(false)
const isCollapsed = ref(false)

// Dynamic menu state
const menuGroups = shallowRef<LocalMenuGroup[]>([])
const isLoading = ref(false)

// ============================================================================
// Auto-collapse sidebar on designer routes
// ============================================================================
watch(() => route.meta?.hideMenu, (hideMenu) => {
  if (hideMenu && !isMobile.value) {
    isCollapsed.value = true
  }
}, { immediate: true })

const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// ============================================================================
// Breadcrumb generation
// ============================================================================
const breadcrumbs = computed(() => {
  const crumbs: { label: string; path: string; to?: { path: string } }[] = []
  const path = route.path

  // Dynamic object pages: /objects/:code/...
  if (path.startsWith('/objects/')) {
    const objectCode = route.params.code as string
    if (objectCode) {
      const objectLabel = resolveObjectDisplayName(
        objectCode, objectCode,
        t as (key: string) => string, te
      ) || objectCode

      // List page
      crumbs.push({
        label: objectLabel,
        path: `/objects/${objectCode}`,
        to: { path: `/objects/${objectCode}` }
      })

      // Detail or Edit
      const id = route.params.id as string
      if (id) {
        if (path.endsWith('/edit')) {
          crumbs.push({ label: t('common.actions.edit'), path })
        } else {
          crumbs.push({ label: t('common.actions.detail'), path })
        }
      } else if (path.endsWith('/create')) {
        crumbs.push({ label: t('common.actions.create'), path })
      }
    }
  } else if (path.startsWith('/assets/lifecycle/')) {
    // Lifecycle pages: /assets/lifecycle/purchase-requests, etc.
    crumbs.push({
      label: t('menu.menu.lifecycle'),
      path: '/assets/lifecycle/purchase-requests',
      to: { path: '/assets/lifecycle/purchase-requests' }
    })
    if (route.meta?.title) {
      const titleKey = route.meta.title as string
      const label = te(titleKey) ? t(titleKey) : titleKey
      crumbs.push({ label, path })
    }
  } else if (route.meta?.title) {
    // Static routes with meta.title
    const titleKey = route.meta.title as string
    const label = te(titleKey) ? t(titleKey) : titleKey
    crumbs.push({ label, path })
  }

  return crumbs
})

// ============================================================================
// Icon resolution
// ============================================================================
const iconComponents: Record<string, unknown> = ElementPlusIcons

const resolveIcon = (iconName: string) => {
  return iconComponents[iconName] || null
}

// ============================================================================
// Menu label translation (reused from previous implementation)
// ============================================================================
const getGroupLabel = (group: LocalMenuGroup) => {
  const groupCode = String(group.code || '').trim()
  const groupName = String(group.name || '').trim()

  if (groupCode) {
    const normalizedCode = groupCode.toLowerCase()
    const groupCodeToKeyMap: Record<string, string> = {
      dashboard: 'dashboard',
      asset: 'assets',
      asset_operation: 'assetOperations',
      lifecycle: 'lifecycle',
      insurance: 'insurance',
      leasing: 'leasing',
      consumable: 'consumables',
      purchase: 'procurement',
      maintenance: 'maintenance',
      inventory: 'inventory',
      organization: 'organization',
      finance: 'finance',
      workflow: 'workflowManagement',
      system: 'system',
      dynamicobjects: 'dynamicObjects'
    }

    const mappedByCode = groupCodeToKeyMap[normalizedCode] || groupCode
    const translationKey = `menu.menu.${mappedByCode}`
    if (te(translationKey)) {
      return t(translationKey)
    }
  }

  return groupName
}

const getItemLabel = (item: LocalMenuItem) => {
  const itemCode = String(item.code || '').trim()
  const itemName = String(item.name || '').trim()

  if (itemCode) {
    const objectCodeLabel = translateObjectCodeLabel(itemCode, t as (key: string) => string, te)
    if (objectCodeLabel) {
      return objectCodeLabel
    }

    const menuKey = `menu.menu.${itemCode}`
    if (te(menuKey)) {
      return t(menuKey)
    }

    const routeKey = `menu.routes.${itemCode}`
    if (te(routeKey)) {
      return t(routeKey)
    }
  }

  return itemName
}

const getMenuGroupIdentity = (group: LocalMenuGroup, index: number): string => {
  const code = String(group.code || '').trim()
  if (code) return code

  const name = String(group.name || '').trim()
  if (name) return `${name}-${index}`

  return `group-${index}`
}

// ============================================================================
// Responsive
// ============================================================================
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

// ============================================================================
// Menu data fetching (unchanged logic)
// ============================================================================
const normalizeBusinessObjects = (payload: AnyRecord): BusinessObject[] => {
  const source: AnyRecord[] = []
  if (Array.isArray(payload)) source.push(...payload)
  if (Array.isArray(payload?.results)) source.push(...payload.results)
  if (Array.isArray(payload?.hardcoded)) source.push(...payload.hardcoded)
  if (Array.isArray(payload?.custom)) source.push(...payload.custom)

  const normalized: BusinessObject[] = []
  const seen = new Set<string>()
  for (const item of source) {
    const code = String(item?.code || '').trim()
    if (!code || seen.has(code)) continue
    seen.add(code)
    normalized.push({
      id: String(item?.id || code),
      code,
      name: String(item?.name || code),
      nameEn: String(item?.nameEn || ''),
      description: String(item?.description || ''),
      enableWorkflow: item?.enableWorkflow === true,
      enableVersion: item?.enableVersion === true,
      enableSoftDelete: item?.enableSoftDelete !== false,
      isHardcoded: item?.isHardcoded === true || item?.type === 'hardcoded',
      djangoModelPath: String(item?.djangoModelPath || item?.modelPath || ''),
      tableName: String(item?.tableName || ''),
      fieldCount: Number(item?.fieldCount || 0),
      layoutCount: Number(item?.layoutCount || 0)
    })
  }
  return normalized
}

const normalizeMenuGroups = (payload: unknown): LocalMenuGroup[] => {
  if (Array.isArray(payload)) {
    return payload as LocalMenuGroup[]
  }
  if (payload && typeof payload === 'object') {
    const data = payload as AnyRecord
    if (Array.isArray(data.groups)) {
      return data.groups as LocalMenuGroup[]
    }
  }
  return []
}

const extractObjectCodeFromUrl = (url: string): string => {
  const value = String(url || '').trim()
  const match = value.match(/^\/objects\/([^/?#]+)/)
  return match ? decodeURIComponent(match[1]) : ''
}

const collectMenuObjectCodes = (groups: LocalMenuGroup[]): Set<string> => {
  const codes = new Set<string>()
  groups.forEach((group) => {
    group.items.forEach((item) => {
      const code = String(item?.code || '').trim()
      if (code) codes.add(code)
      const urlCode = extractObjectCodeFromUrl(String(item?.url || ''))
      if (urlCode) codes.add(urlCode)
    })
  })
  return codes
}

const buildMissingObjectGroup = (objects: BusinessObject[], menuGroupsData: LocalMenuGroup[]): LocalMenuGroup | null => {
  const existingCodes = collectMenuObjectCodes(menuGroupsData)
  const missingObjects = objects
    .filter((obj) => !existingCodes.has(obj.code))
    .filter((obj) => !AUTO_DYNAMIC_ENTRY_EXCLUDE_CODES.has(obj.code))
    .sort((a, b) => a.code.localeCompare(b.code))

  if (!missingObjects.length) return null

  return {
    name: '',
    code: 'dynamicObjects',
    icon: 'Grid',
    order: 999,
    items: missingObjects.map((obj, index) => ({
      code: obj.code,
      name: obj.nameEn || obj.name || obj.code,
      nameEn: obj.nameEn || '',
      url: `/objects/${obj.code}`,
      icon: 'Document',
      order: index + 1,
      group: '',
      badge: null
    }))
  }
}

const fetchMenu = async () => {
  if (isLoading.value) return
  isLoading.value = true

  try {
    const [menuResponse, objectsResponse] = await Promise.all([
      menuApi.get(),
      businessObjectApi.list({ pageSize: 500 })
    ])

    const baseGroups = normalizeMenuGroups(menuResponse)
    const objects = normalizeBusinessObjects((objectsResponse || {}) as unknown as AnyRecord)
    const missingGroup = buildMissingObjectGroup(objects, baseGroups)
    menuGroups.value = missingGroup ? [...baseGroups, missingGroup] : baseGroups
  } catch (error) {
    console.error(error)
    menuGroups.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  fetchMenu()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;
/* ====================================================================
   Layout Shell
   ==================================================================== */
.main-layout {
  min-height: 100vh;
  --sidebar-bg: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  --sidebar-width: 220px;
  --sidebar-collapsed-width: 64px;
  --header-height: 56px;
}

/* ====================================================================
   Sidebar
   ==================================================================== */
.sidebar {
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 10;
}

.sidebar-header {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.logo {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  overflow: hidden;
}

.logo-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #60a5fa, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 1px;
}

.sidebar-menu-scroll {
  flex: 1;
  overflow: hidden;
}

/* Sidebar menu overrides */
.sidebar-menu {
  border-right: none !important;
  padding: 8px 0;
}

.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
  margin: 2px 8px;
  border-radius: 8px;
  padding-left: 20px !important;
}

.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background-color: rgba(255, 255, 255, 0.08) !important;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.25), rgba(167, 139, 250, 0.15)) !important;
  color: #ffffff !important;
  font-weight: 500;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 52px !important;
  height: 40px;
  line-height: 40px;
  font-size: 13px;
}

/* Collapsed sidebar */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item),
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title) {
  margin: 2px 6px;
  padding-left: 0 !important;
  justify-content: center;
}

.sidebar-footer {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  flex-shrink: 0;
  transition: color 0.2s;
  white-space: nowrap;
  overflow: hidden;
}

.sidebar-footer:hover {
  color: rgba(255, 255, 255, 0.85);
}

.collapse-label {
  font-size: 13px;
}

/* ====================================================================
   Top Header Bar
   ==================================================================== */
.top-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: $bg-card;
  border-bottom: 1px solid $border-light;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-menu-btn {
  font-size: 20px;
}

/* ====================================================================
   Main Content
   ==================================================================== */
.main-container {
  flex-direction: column;
  min-height: 100vh;
}

.page-main {
  background: $bg-body;
  padding: 20px;
  flex: 1;
}

/* ====================================================================
   Mobile Drawer
   ==================================================================== */
.drawer-menu-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-logo {
  padding: 20px;
  font-size: 18px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #e6e6e6;
}

.drawer-logo .logo-icon {
  font-size: 22px;
}

.mobile-menu {
  flex: 1;
  border-right: none !important;
}

/* ====================================================================
   Transitions
   ==================================================================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.15s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* ====================================================================
   Responsive
   ==================================================================== */
@media (max-width: 768px) {
  .top-header {
    padding: 0 12px;
  }
  .page-main {
    padding: 12px;
  }
}
</style>

