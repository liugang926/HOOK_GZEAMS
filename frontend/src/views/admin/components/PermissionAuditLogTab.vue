<template>
  <div class="permission-audit-log-tab">
    <!-- Filters -->
    <el-form :model="filterForm" inline class="filter-form">
      <el-form-item label="操作类型">
        <el-select v-model="filterForm.action" clearable placeholder="全部" @change="handleSearch">
          <el-option label="授权" value="grant" />
          <el-option label="撤销" value="revoke" />
          <el-option label="修改" value="update" />
        </el-select>
      </el-form-item>
      <el-form-item label="时间范围">
        <el-date-picker
          v-model="filterForm.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleSearch"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <!-- Statistics Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">今日授权</div>
            <div class="stat-value">{{ stats.todayGrants }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">今日撤销</div>
            <div class="stat-value">{{ stats.todayRevokes }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">本周操作</div>
            <div class="stat-value">{{ stats.weekTotal }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-item">
            <div class="stat-label">活跃用户</div>
            <div class="stat-value">{{ stats.activeUsers }}</div>
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
      <el-table-column prop="createdAt" label="操作时间" width="180" />
      <el-table-column prop="operatorName" label="操作人" width="120" />
      <el-table-column label="操作类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="getActionTag(row.action)" size="small">
            {{ getActionLabel(row.action) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="permissionType" label="权限类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.permissionType === 'field' ? 'primary' : 'success'" size="small">
            {{ row.permissionType === 'field' ? '字段权限' : '数据权限' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="targetName" label="目标对象" width="120" />
      <el-table-column prop="details" label="操作详情" min-width="250" show-overflow-tooltip />
      <el-table-column prop="ipAddress" label="IP地址" width="140" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleViewDetail(row)">详情</el-button>
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
      title="日志详情"
      width="600px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="操作时间">{{ currentLog?.createdAt }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentLog?.operatorName }}</el-descriptions-item>
        <el-descriptions-item label="操作类型">
          <el-tag :type="getActionTag(currentLog?.action)">
            {{ getActionLabel(currentLog?.action) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="权限类型">
          <el-tag :type="currentLog?.permissionType === 'field' ? 'primary' : 'success'">
            {{ currentLog?.permissionType === 'field' ? '字段权限' : '数据权限' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="目标对象" :span="2">{{ currentLog?.targetName }}</el-descriptions-item>
        <el-descriptions-item label="操作详情" :span="2">{{ currentLog?.details }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog?.ipAddress }}</el-descriptions-item>
        <el-descriptions-item label="用户代理">{{ currentLog?.userAgent }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { permissionAuditLogApi } from '@/api/permissions'

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
    'grant': '授权',
    'revoke': '撤销',
    'update': '修改'
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
    ElMessage.error('加载数据失败')
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
