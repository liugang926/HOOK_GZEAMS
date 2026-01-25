<template>
  <div class="main-layout">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="header-logo-row">
             <el-button v-if="isMobile" @click="drawerVisible = true" :icon="Menu" class="mobile-menu-btn" text />
             <h1 class="logo">GZEAMS</h1>
          </div>

          <!-- Desktop Menu -->
          <el-menu v-if="!isMobile" mode="horizontal" :default-active="activeMenu" router class="desktop-menu">
            <el-menu-item index="/dashboard">工作台</el-menu-item>
            <el-sub-menu index="/assets">
              <template #title>资产管理</template>
              <el-menu-item index="/assets">资产列表</el-menu-item>
              <el-menu-item index="/assets/operations/pickup">领用管理</el-menu-item>
              <el-menu-item index="/assets/operations/transfer">调拨管理</el-menu-item>
              <el-menu-item index="/assets/operations/return">退库管理</el-menu-item>
              <el-menu-item index="/assets/operations/loans">借出管理</el-menu-item>
              <el-menu-item index="/assets/settings/categories">分类管理</el-menu-item>
              <el-menu-item index="/assets/settings/suppliers">供应商管理</el-menu-item>
              <el-menu-item index="/assets/settings/locations">存放位置管理</el-menu-item>
              <el-menu-item index="/assets/status-logs">状态日志</el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/inventory">盘点管理</el-menu-item>
            <el-sub-menu index="/finance">
              <template #title>财务管理</template>
              <el-menu-item index="/finance/vouchers">财务凭证</el-menu-item>
              <el-menu-item index="/finance/depreciation">折旧管理</el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/consumables">耗材管理</el-menu-item>
            <el-sub-menu index="/software-licenses">
              <template #title>软件许可</template>
              <el-menu-item index="/software-licenses/software">软件目录</el-menu-item>
              <el-menu-item index="/software-licenses/licenses">许可证管理</el-menu-item>
              <el-menu-item index="/software-licenses/allocations">分配记录</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="/system">
              <template #title>系统管理</template>
              <el-menu-item index="/system/business-objects">业务对象管理</el-menu-item>
              <el-menu-item index="/system/field-definitions">字段定义管理</el-menu-item>
              <el-menu-item index="/system/page-layouts">页面布局管理</el-menu-item>
              <el-menu-item index="/system/dictionary-types">数据字典管理</el-menu-item>
              <el-menu-item index="/system/departments">部门管理</el-menu-item>
              <el-menu-item index="/admin/permissions">权限管理</el-menu-item>
            </el-sub-menu>
            <el-menu-item index="/workflow/tasks">我的待办</el-menu-item>
          </el-menu>

          <div style="flex: 1"></div>

          <NotificationBell />
        </div>
      </el-header>

      <!-- Mobile Drawer Menu -->
      <el-drawer v-model="drawerVisible" direction="ltr" size="240px" :with-header="false">
         <div class="drawer-menu-container">
            <div class="drawer-logo">GZEAMS</div>
            <el-menu :default-active="activeMenu" router class="mobile-menu" @select="drawerVisible = false">
              <el-menu-item index="/dashboard">工作台</el-menu-item>
              <el-sub-menu index="/assets">
                <template #title>资产管理</template>
                <el-menu-item index="/assets">资产列表</el-menu-item>
                <el-menu-item index="/assets/operations/pickup">领用管理</el-menu-item>
                <el-menu-item index="/assets/operations/transfer">调拨管理</el-menu-item>
                <el-menu-item index="/assets/operations/return">退库管理</el-menu-item>
                <el-menu-item index="/assets/operations/loans">借出管理</el-menu-item>
                <el-menu-item index="/assets/settings/categories">分类管理</el-menu-item>
                <el-menu-item index="/assets/settings/suppliers">供应商管理</el-menu-item>
                <el-menu-item index="/assets/settings/locations">存放位置管理</el-menu-item>
                <el-menu-item index="/assets/status-logs">状态日志</el-menu-item>
              </el-sub-menu>
              <el-menu-item index="/inventory">盘点管理</el-menu-item>
              <el-sub-menu index="/finance">
                <template #title>财务管理</template>
                <el-menu-item index="/finance/vouchers">财务凭证</el-menu-item>
                <el-menu-item index="/finance/depreciation">折旧管理</el-menu-item>
              </el-sub-menu>
              <el-menu-item index="/consumables">耗材管理</el-menu-item>
              <el-sub-menu index="/software-licenses">
                <template #title>软件许可</template>
                <el-menu-item index="/software-licenses/software">软件目录</el-menu-item>
                <el-menu-item index="/software-licenses/licenses">许可证管理</el-menu-item>
                <el-menu-item index="/software-licenses/allocations">分配记录</el-menu-item>
              </el-sub-menu>
              <el-sub-menu index="/system">
                <template #title>系统管理</template>
                <el-menu-item index="/system/business-objects">业务对象管理</el-menu-item>
                <el-menu-item index="/system/field-definitions">字段定义管理</el-menu-item>
                <el-menu-item index="/system/page-layouts">页面布局管理</el-menu-item>
                <el-menu-item index="/system/dictionary-types">数据字典管理</el-menu-item>
                <el-menu-item index="/system/departments">部门管理</el-menu-item>
                <el-menu-item index="/admin/permissions">权限管理</el-menu-item>
              </el-sub-menu>
              <el-menu-item index="/workflow/tasks">我的待办</el-menu-item>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Menu } from '@element-plus/icons-vue'
import NotificationBell from '@/components/layout/NotificationBell.vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
const drawerVisible = ref(false)
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
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
