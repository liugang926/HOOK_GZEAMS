```html
<template>
  <div class="permission-audit-log-tab">
    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.permission.audit.toolbar.action')">
        <el-select
          v-model="filterForm.action"
          clearable
          :placeholder="$t('system.permission.audit.toolbar.actionPlaceholder')"
          @change="handleSearch"
        >
          <el-option
            :label="$t('system.permission.audit.actions.grant')"
            value="grant"
          />
          <el-option
            :label="$t('system.permission.audit.actions.revoke')"
            value="revoke"
          />
          <el-option
            :label="$t('system.permission.audit.actions.update')"
            value="update"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('system.permission.audit.toolbar.timeRange')">
        <el-date-picker
          v-model="filterForm.dateRange"
          type="daterange"
          range-separator="-"
          :start-placeholder="$t('system.permission.audit.toolbar.startDate')"
          :end-placeholder="$t('system.permission.audit.toolbar.endDate')"
          @change="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSearch"
        >
          {{ $t('common.actions.search') }}
        </el-button>
        <el-button @click="handleReset">
          {{ $t('common.actions.reset') }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Statistics Cards -->
    <el-row
      :gutter="20"
      class="stats-row"
    >
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.todayGrants') }}
            </div>
            <div class="stat-value">
              {{ stats.todayGrants }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.todayRevokes') }}
            </div>
            <div class="stat-value">
              {{ stats.todayRevokes }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.weekTotal') }}
            </div>
            <div class="stat-value">
              {{ stats.weekTotal }}
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">
              {{ $t('system.permission.audit.stats.activeUsers') }}
            </div>
            <div class="stat-value">
              {{ stats.activeUsers }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Audit Log Table -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%; margin-top: 20px"
    >
      <el-table-column
        prop="createdAt"
        :label="$t('system.permission.audit.columns.time')"
        width="180"
      />
      <el-table-column
        prop="operatorName"
        :label="$t('system.permission.audit.columns.operator')"
        width="120"
      />
      <el-table-column
        :label="$t('system.permission.audit.columns.action')"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="getActionTag(row.action)"
            size="small"
          >
            {{ getActionLabel(row.action) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="permissionType"
        :label="$t('system.permission.audit.columns.type')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.permissionType === 'field' ? 'primary' : 'success'"
            size="small"
          >
            {{ row.permissionType === 'field' ? $t('system.permission.audit.types.field') : $t('system.permission.audit.types.data') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="targetName"
        :label="$t('system.permission.audit.columns.target')"
        width="120"
      />
      <el-table-column
        prop="details"
        :label="$t('system.permission.audit.columns.details')"
        min-width="250"
        show-overflow-tooltip
      />
      <el-table-column
        prop="ipAddress"
        :label="$t('system.permission.audit.columns.ip')"
        width="140"
      />
      <el-table-column
        :label="$t('system.permission.audit.columns.operation')"
        width="100"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleViewDetail(row)"
          >
            {{ $t('common.actions.detail') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Pagination -->
    <div class="pagination-footer">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </div>

    <!-- Detail Dialog -->
    <el-dialog
      v-model="detailVisible"
      :title="$t('system.permission.audit.dialog.title')"
      width="600px"
    >
      <el-descriptions
        :column="2"
        border
      >
        <el-descriptions-item :label="$t('system.permission.audit.dialog.time')">
          {{ currentLog?.createdAt }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.operator')">
          {{ currentLog?.operatorName }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.action')">
          <el-tag :type="getActionTag(currentLog?.action)">
            {{ getActionLabel(currentLog?.action) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.type')">
          <el-tag :type="currentLog?.permissionType === 'field' ? 'primary' : 'success'">
            {{ currentLog?.permissionType === 'field' ? $t('system.permission.audit.types.field') : $t('system.permission.audit.types.data') }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('system.permission.audit.dialog.target')"
          :span="2"
        >
          {{ currentLog?.targetName }}
        </el-descriptions-item>
        <el-descriptions-item
          :label="$t('system.permission.audit.dialog.details')"
          :span="2"
        >
          {{ currentLog?.details }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.ip')">
          {{ currentLog?.ipAddress }}
        </el-descriptions-item>
        <el-descriptions-item :label="$t('system.permission.audit.dialog.userAgent')">
          {{ currentLog?.userAgent }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { permissionAuditLogApi } from '@/api/permissions'

const { t } = useI18n()

const loading = ref(false)
const tableData = ref<any[]>([])
const detailVisible = ref(false)
const currentLog = ref<any>(null)

const filterForm = reactive({
  action: '',
  dateRange: null as any
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const stats = ref({
  todayGrants: 0,
  todayRevokes: 0,
  weekTotal: 0,
  activeUsers: 0
})

const getActionLabel = (action: string) => {
  const labels: Record<string, string> = {
    'grant': t('system.permission.audit.actions.grant'),
    'revoke': t('system.permission.audit.actions.revoke'),
    'update': t('system.permission.audit.actions.update')
  }
  return labels[action] || action
}

const getActionTag = (action: string) => {
  const tags: Record<string, any> = {
    'grant': 'success',
    'revoke': 'danger',
    'update': 'warning'
  }
  return tags[action] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const res = await permissionAuditLogApi.list({
    //   ...filterForm,
    //   page: pagination.page,
    //   pageSize: pagination.pageSize
    // })
    // tableData.value = res.results || []
    // pagination.total = res.count || 0

    // Mock data
    tableData.value = [
      {
        id: '1',
        createdAt: '2025-01-25 14:30:15',
        operatorName: '张三',
        action: 'grant',
        permissionType: 'field',
        targetName: '固定资产.资产名称',
        details: '授予角色[普通用户]字段[资产名称]的读取权限',
        ipAddress: '192.168.1.100',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0)'
      },
      {
        id: '2',
        createdAt: '2025-01-25 14:25:30',
        operatorName: '李四',
        action: 'revoke',
        permissionType: 'data',
        targetName: '固定资产',
        details: '撤销用户[王五]的数据权限',
        ipAddress: '192.168.1.101',
        userAgent: 'Mozilla/5.0 (Macintosh)'
      },
      {
        id: '3',
        createdAt: '2025-01-25 14:20:00',
        operatorName: '张三',
        action: 'update',
        permissionType: 'field',
        targetName: '固定资产.资产原值',
        details: '修改角色[普通用户]字段[资产原值]的权限为只读',
        ipAddress: '192.168.1.100',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0)'
      }
    ]
    pagination.total = 3

    // Mock stats
    stats.value = {
      todayGrants: 15,
      todayRevokes: 3,
      weekTotal: 87,
      activeUsers: 8
    }
  } catch (error) {
    ElMessage.error(t('common.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  filterForm.action = ''
  filterForm.dateRange = null
  handleSearch()
}

const handleViewDetail = (row: any) => {
  currentLog.value = row
  detailVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.permission-audit-log-tab {
  padding: 10px 0;
}
.filter-form {
  margin-bottom: 20px;
}
.stats-row {
  margin-bottom: 20px;
}
.stat-item {
  text-align: center;
}
.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}
.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
```
