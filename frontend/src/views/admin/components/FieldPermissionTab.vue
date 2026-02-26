<template>
  <div class="field-permission-tab">
    <!-- Filters -->
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.permission.field.toolbar.role')">
        <el-select
          v-model="filterForm.role"
          clearable
          :placeholder="$t('system.permission.field.toolbar.rolePlaceholder')"
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
      <el-form-item :label="$t('system.permission.field.toolbar.object')">
        <el-select
          v-model="filterForm.businessObject"
          clearable
          :placeholder="$t('system.permission.field.toolbar.objectPlaceholder')"
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
          {{ $t('common.actions.search') }}
        </el-button>
        <el-button @click="handleReset">
          {{ $t('common.actions.reset') }}
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
        :label="$t('system.permission.field.columns.role')"
        width="120"
        fixed="left"
      />
      <el-table-column
        prop="businessObjectName"
        :label="$t('system.permission.field.columns.object')"
        width="150"
      />
      <el-table-column
        prop="fieldName"
        :label="$t('system.permission.field.columns.field')"
        width="150"
      />
      <el-table-column
        :label="$t('system.permission.field.columns.read')"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.canRead ? 'success' : 'info'"
            size="small"
          >
            {{ row.canRead ? $t('system.permission.field.status.allow') : $t('system.permission.field.status.deny') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.permission.field.columns.write')"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.canWrite ? 'success' : 'info'"
            size="small"
          >
            {{ row.canWrite ? $t('system.permission.field.status.allow') : $t('system.permission.field.status.deny') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.permission.field.columns.visibility')"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.isVisible ? 'success' : 'warning'"
            size="small"
          >
            {{ row.isVisible ? $t('system.permission.field.status.show') : $t('system.permission.field.status.hide') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        :label="$t('system.permission.field.columns.description')"
        min-width="200"
        show-overflow-tooltip
      />
      <el-table-column
        :label="$t('system.permission.field.columns.operation')"
        width="120"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
          >
            {{ $t('common.actions.edit') }}
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
import { useI18n } from 'vue-i18n'
import { fieldPermissionApi } from '@/api/permissions'
import FieldPermissionDialog from './FieldPermissionDialog.vue'

const { t } = useI18n()

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
