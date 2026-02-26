<template>
  <div class="main-layout">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="header-logo-row">
            <el-button
              v-if="isMobile"
              :icon="Menu"
              class="mobile-menu-btn"
              text
              @click="drawerVisible = true"
            />
            <h1 class="logo">
              GZEAMS
            </h1>
          </div>

          <!-- Desktop Menu - Dynamic -->
          <el-menu
            v-if="!isMobile"
            mode="horizontal"
            :default-active="activeMenu"
            router
            class="desktop-menu"
          >
            <el-menu-item index="/dashboard">
              {{ $t('menu.menu.dashboard') }}
            </el-menu-item>
            <template
              v-for="group in menuGroups"
              :key="group.name"
            >
              <el-sub-menu
                v-if="group.items.length > 1"
                :index="group.name"
              >
                <template #title>
                  <el-icon v-if="group.icon">
                    <component :is="group.icon" />
                  </el-icon>
                  {{ getGroupLabel(group) }}
                </template>
                <el-menu-item
                  v-for="item in group.items"
                  :key="item.code"
                  :index="item.url"
                >
                  <el-icon v-if="item.icon">
                    <component :is="item.icon" />
                  </el-icon>
                  {{ getItemLabel(item) }}
                </el-menu-item>
              </el-sub-menu>
              <el-menu-item
                v-else-if="group.items.length === 1"
                :key="group.items[0].code"
                :index="group.items[0].url"
              >
                <el-icon v-if="group.items[0].icon">
                  <component :is="group.items[0].icon" />
                </el-icon>
                {{ getItemLabel(group.items[0]) }}
              </el-menu-item>
            </template>
          </el-menu>

          <div style="flex: 1" />

          <LocaleSwitcher />
          <NotificationBell />
        </div>
      </el-header>

      <!-- Mobile Drawer Menu - Dynamic -->
      <el-drawer
        v-model="drawerVisible"
        direction="ltr"
        size="240px"
        :with-header="false"
      >
        <div class="drawer-menu-container">
          <div class="drawer-logo">
            GZEAMS
          </div>
          <el-menu
            :default-active="activeMenu"
            router
            class="mobile-menu"
            @select="drawerVisible = false"
          >
            <el-menu-item index="/dashboard">
              {{ $t('menu.menu.dashboard') }}
            </el-menu-item>
            <template
              v-for="group in menuGroups"
              :key="group.name"
            >
              <el-sub-menu
                v-if="group.items.length > 1"
                :index="group.name"
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

      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Menu } from '@element-plus/icons-vue'
import NotificationBell from '@/components/layout/NotificationBell.vue'
import LocaleSwitcher from '@/components/common/LocaleSwitcher.vue'
import { menuApi, type MenuGroup } from '@/api/system'
import * as ElementPlusIcons from '@element-plus/icons-vue'

const route = useRoute()
const { t, te } = useI18n()
const activeMenu = computed(() => route.path)
const drawerVisible = ref(false)
const isMobile = ref(false)

// Dynamic menu state
const menuGroups = shallowRef<MenuGroup[]>([])
const isLoading = ref(false)

// Icon name to component mapping
const iconComponents: Record<string, any> = ElementPlusIcons

const getGroupLabel = (group: any) => {
  // If group has a code, use it for translation
  if (group.code) {
    const translationKey = `menu.menu.${group.code}`
    if (te(translationKey)) {
      return t(translationKey)
    }
  }

  // Fallback: try to match name to known translation keys
  // This handles cases where backend returns localized names without codes
  const normalizedGroupName = group.name?.toLowerCase().trim()

  // Map common group names to their translation keys
  const groupNameToKeyMap: Record<string, string> = {
    // Chinese names
    '资产管理': 'assets',
    '耗材管理': 'consumables',
    '盘点管理': 'inventory',
    '工作流': 'workflow',
    '系统管理': 'system',
    '管理员': 'admin',
    '采购管理': 'procurement',
    '维保管理': 'maintenance',
    '组织管理': 'organization',
    '流程管理': 'workflowManagement',
    // English names
    'asset management': 'assets',
    'consumables': 'consumables',
    'inventory': 'inventory',
    'workflow': 'workflow',
    'system': 'system',
    'admin': 'admin',
    'procurement': 'procurement',
    'maintenance': 'maintenance',
    'organization': 'organization',
    'workflow management': 'workflowManagement'
  }

  const mappedKey = groupNameToKeyMap[normalizedGroupName]
  if (mappedKey && te(`menu.menu.${mappedKey}`)) {
    return t(`menu.menu.${mappedKey}`)
  }

  // Final fallback: return the name as-is
  return group.name
}

const getItemLabel = (item: any) => {
  // Priority 1: Use item.code for translation
  if (item.code) {
    // First try menu.menu namespace (for top-level items)
    const menuKey = `menu.menu.${item.code}`
    if (te(menuKey)) {
      return t(menuKey)
    }

    // Then try menu.routes namespace (for route items)
    const routeKey = `menu.routes.${item.code}`
    if (te(routeKey)) {
      return t(routeKey)
    }
  }

  // Priority 2: Fallback to name-based translation
  // This handles cases where backend returns localized names without codes
  const normalizedName = item.name?.toLowerCase().trim()

  // Map common item names to their translation keys
  const itemNameToKeyMap: Record<string, string> = {
    // Chinese names
    '业务对象': 'businessObjects',
    '用户': 'users',
    '字段定义': 'fieldDefinitions',
    '页面布局': 'pageLayouts',
    '字典类型': 'dictionaryTypes',
    '编号规则': 'sequenceRules',
    '业务规则': 'businessRules',
    '配置包': 'configPackages',
    '系统配置': 'systemConfig',
    '文件管理': 'systemFiles',
    '权限管理': 'permissions',
    '工作流定义': 'workflowDefinitions',
    '工作流实例': 'workflowInstances',
    '资产卡片': 'assetList',
    '资产分类': 'assetCategory',
    '存放地点': 'location',
    '供应商': 'supplier',
    '资产状态日志': 'assetStatusLog',
    'it资产管理': 'itAssets',
    'it维护记录': 'itMaintenance',
    '配置变更记录': 'configChanges',
    '软件目录': 'softwareCatalog',
    '软件许可证': 'softwareLicenses',
    '分配记录': 'licenseAllocations',
    '集成配置管理': 'integrationConfigs',
    // English names
    'business objects': 'businessObjects',
    'users': 'users',
    'field definitions': 'fieldDefinitions',
    'page layouts': 'pageLayouts',
    'dictionary types': 'dictionaryTypes',
    'sequence rules': 'sequenceRules',
    'business rules': 'businessRules',
    'config packages': 'configPackages',
    'system config': 'systemConfig',
    'system files': 'systemFiles',
    'permissions': 'permissions',
    'workflow definitions': 'workflowDefinitions',
    'workflow instances': 'workflowInstances',
    'asset list': 'assetList',
    'asset categories': 'assetCategory',
    'locations': 'location',
    'suppliers': 'supplier',
    'asset status logs': 'assetStatusLog',
    'it assets': 'itAssets',
    'it maintenance': 'itMaintenance',
    'config changes': 'configChanges',
    'software catalog': 'softwareCatalog',
    'software licenses': 'softwareLicenses',
    'license allocations': 'licenseAllocations',
    'integration configs': 'integrationConfigs'
  }

  const mappedKey = itemNameToKeyMap[normalizedName]
  if (mappedKey && te(`menu.routes.${mappedKey}`)) {
    return t(`menu.routes.${mappedKey}`)
  }

  // Final fallback: return the name as-is
  return item.name
}

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

const fetchMenu = async () => {
  if (isLoading.value) return
  isLoading.value = true

  try {
    // Response interceptor automatically unwraps { success, data } -> returns data directly
    const response = await menuApi.get() as any
    console.log('Menu API response:', response)
    // response should be { groups: [...], items: [...] }
    if (response && response.groups) {
      menuGroups.value = response.groups
    } else if (Array.isArray(response)) {
      // Handle case where response is directly an array
      menuGroups.value = response
    }
  } catch (error) {
    console.error('Failed to fetch menu:', error)
    // Fallback to empty menu on error
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

<style scoped>
.main-layout {
  min-height: 100vh;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.logo {
  margin: 0 30px 0 0;
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.el-main {
  background: #f5f7fa;
  padding: 20px;
}

.header-logo-row {
  display: flex;
  align-items: center;
}

.mobile-menu-btn {
  margin-right: 10px;
  font-size: 20px;
}

.desktop-menu {
  border-bottom: none !important;
  flex: 1;
  margin-left: 20px;
  overflow-x: auto;
  overflow-y: hidden;
  min-width: 0;
}

/* Hide scrollbar for cleaner look while maintaining scroll functionality */
.desktop-menu::-webkit-scrollbar {
  height: 4px;
}

.desktop-menu::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 2px;
}

.desktop-menu::-webkit-scrollbar-track {
  background: transparent;
}

.drawer-menu-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-logo {
  padding: 20px;
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  border-bottom: 1px solid #e6e6e6;
}

.mobile-menu {
  flex: 1;
  border-right: none !important;
}

@media (max-width: 768px) {
  .el-header {
    padding: 0 10px;
  }
  .el-main {
    padding: 10px;
  }
}
</style>
