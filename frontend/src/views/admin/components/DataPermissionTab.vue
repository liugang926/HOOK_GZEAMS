<template>
  <div class="data-permission-tab">
    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item label="角色">
        <el-select
          v-model="filterForm.role"
          clearable
          placeholder="选择角色"
          @change="handleSearch"
        >
          <el-option
            label="管理员"
            value="admin"
          />
          <el-option
            label="部门主管"
            value="manager"
          />
          <el-option
            label="普通员工"
            value="employee"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          @click="handleSearch"
        >
          查询
        </el-button>
        <el-button @click="handleReset">
          重置
        </el-button>
        <el-button
          type="success"
          @click="handleCreate"
        >
          新增规则
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Data Permission Rules -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column
        prop="roleName"
        label="角色"
        width="120"
      />
      <el-table-column
        prop="businessObjectName"
        label="业务对象"
        width="150"
      />
      <el-table-column
        label="权限类型"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="getPermissionTypeTag(row.permissionType)"
            size="small"
          >
            {{ getPermissionTypeLabel(row.permissionType) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="scopeExpression"
        label="权限范围"
        min-width="250"
        show-overflow-tooltip
      />
      <el-table-column
        label="状态"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.isActive ? 'success' : 'info'"
            size="small"
          >
            {{ row.isActive ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        label="说明"
        min-width="200"
        show-overflow-tooltip
      />
      <el-table-column
        label="操作"
        width="150"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            link
            :type="row.isActive ? 'warning' : 'success'"
            @click="handleToggleActive(row)"
          >
            {{ row.isActive ? '禁用' : '启用' }}
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

    <!-- Edit Dialog -->
    <DataPermissionDialog
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { dataPermissionApi } from '@/api/permissions'
import DataPermissionDialog from './DataPermissionDialog.vue'

const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)

const filterForm = reactive({
  role: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const getPermissionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'all': '全部数据',
    'department': '本部门',
    'department_and_sub': '本部门及子部门',
    'self': '仅本人',
    'custom': '自定义'
  }
  return labels[type] || type
}

const getPermissionTypeTag = (type: string) => {
  const tags: Record<string, any> = {
    'all': 'danger',
    'department': 'warning',
    'department_and_sub': 'warning',
    'self': 'info',
    'custom': 'primary'
  }
  return tags[type] || 'info'
}

const fetchData = async () => {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const res = await dataPermissionApi.list({
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
        roleName: '管理员',
        businessObjectName: '固定资产',
        permissionType: 'all',
        scopeExpression: '全部数据',
        isActive: true,
        description: '管理员可查看所有资产'
      },
      {
        id: '2',
        roleName: '部门主管',
        businessObjectName: '固定资产',
        permissionType: 'department_and_sub',
        scopeExpression: '部门及子部门数据',
        isActive: true,
        description: '部门主管可查看本部门及下级部门资产'
      },
      {
        id: '3',
        roleName: '普通员工',
        businessObjectName: '固定资产',
        permissionType: 'self',
        scopeExpression: '仅本人使用资产',
        isActive: true,
        description: '普通员工只能查看自己使用的资产'
      }
    ]
    pagination.total = 3
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
  filterForm.role = ''
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleToggleActive = async (row: any) => {
  try {
    // TODO: Replace with actual API call
    row.isActive = !row.isActive
    ElMessage.success(row.isActive ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.data-permission-tab {
  padding: 10px 0;
}
.filter-form {
  margin-bottom: 20px;
}
.pagination-footer {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
