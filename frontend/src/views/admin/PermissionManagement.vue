<template>
  <div class="permission-management">
    <div class="page-header">
      <h3>权限管理</h3>
    </div>

    <el-tabs
      v-model="activeTab"
      class="permission-tabs"
    >
      <!-- Field Permissions Tab -->
      <el-tab-pane
        label="字段权限"
        name="field"
      >
        <FieldPermissionTab />
      </el-tab-pane>

      <!-- Data Permissions Tab -->
      <el-tab-pane
        label="数据权限"
        name="data"
      >
        <DataPermissionTab />
      </el-tab-pane>

      <!-- Audit Log Tab -->
      <el-tab-pane
        label="权限日志"
        name="audit"
      >
        <PermissionAuditLogTab />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FieldPermissionTab from './components/FieldPermissionTab.vue'
import DataPermissionTab from './components/DataPermissionTab.vue'
import PermissionAuditLogTab from './components/PermissionAuditLogTab.vue'

const activeTab = ref('field')
</script>

<style scoped>
.permission-management {
  padding: 20px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}
.permission-tabs {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}
</style>
