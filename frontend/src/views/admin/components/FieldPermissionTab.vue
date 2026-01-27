<template>
  <div class="field-permission-tab">
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
            label="普通用户"
            value="user"
          />
          <el-option
            label="访客"
            value="guest"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="业务对象">
        <el-select
          v-model="filterForm.businessObject"
          clearable
          placeholder="选择业务对象"
          @change="handleSearch"
        >
          <el-option
            label="固定资产"
            value="Asset"
          />
          <el-option
            label="员工信息"
            value="Employee"
          />
          <el-option
            label="部门"
            value="Department"
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
      </el-form-item>
    </el-form>

    <!-- Field Permission Matrix -->
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
        fixed="left"
      />
      <el-table-column
        prop="businessObjectName"
        label="业务对象"
        width="150"
      />
      <el-table-column
        prop="fieldName"
        label="字段名称"
        width="150"
      />
      <el-table-column
        label="读取权限"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.canRead ? 'success' : 'info'"
            size="small"
          >
            {{ row.canRead ? '允许' : '禁止' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="写入权限"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.canWrite ? 'success' : 'info'"
            size="small"
          >
            {{ row.canWrite ? '允许' : '禁止' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="可见性"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.isVisible ? 'success' : 'warning'"
            size="small"
          >
            {{ row.isVisible ? '显示' : '隐藏' }}
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
        width="120"
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
    <FieldPermissionDialog
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fieldPermissionApi } from '@/api/permissions'
import FieldPermissionDialog from './FieldPermissionDialog.vue'

const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)

const filterForm = reactive({
  role: '',
  businessObject: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const res = await fieldPermissionApi.list({
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
        fieldName: '资产名称',
        canRead: true,
        canWrite: true,
        isVisible: true,
        description: '管理员可完全控制'
      },
      {
        id: '2',
        roleName: '普通用户',
        businessObjectName: '固定资产',
        fieldName: '资产原值',
        canRead: true,
        canWrite: false,
        isVisible: true,
        description: '普通用户只读'
      },
      {
        id: '3',
        roleName: '访客',
        businessObjectName: '固定资产',
        fieldName: '资产原值',
        canRead: false,
        canWrite: false,
        isVisible: false,
        description: '访客不可见'
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
  filterForm.businessObject = ''
  handleSearch()
}

const handleEdit = (row: any) => {
  currentRow.value = row
  dialogVisible.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.field-permission-tab {
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
