<template>
  <div class="data-permission-tab">
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.permission.data.toolbar.role')">
        <el-select
          v-model="filterForm.role"
          filterable
          remote
          reserve-keyword
          clearable
          :placeholder="$t('system.permission.data.toolbar.rolePlaceholder')"
          :loading="optionsLoading.users"
          :remote-method="handleUserRemoteSearch"
          @change="handleSearch"
        >
          <el-option
            v-for="option in userOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>
      <el-form-item :label="$t('system.permission.data.columns.object')">
        <el-select
          v-model="filterForm.objectModel"
          filterable
          remote
          reserve-keyword
          clearable
          :loading="optionsLoading.objects"
          :placeholder="$t('system.permission.data.dialog.objectPlaceholder')"
          :remote-method="handleObjectRemoteSearch"
          @change="handleSearch"
        >
          <el-option
            v-for="option in objectOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
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
        <el-button
          type="success"
          @click="handleCreate"
        >
          {{ $t('system.permission.data.toolbar.createRule') }}
        </el-button>
      </el-form-item>
    </el-form>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
      style="width: 100%"
    >
      <el-table-column
        prop="roleName"
        :label="$t('system.permission.data.columns.role')"
        width="160"
      />
      <el-table-column
        prop="businessObjectName"
        :label="$t('system.permission.data.columns.object')"
        width="160"
      />
      <el-table-column
        :label="$t('system.permission.data.columns.type')"
        width="140"
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
        :label="$t('system.permission.data.columns.scope')"
        min-width="260"
        show-overflow-tooltip
      />
      <el-table-column
        prop="description"
        :label="$t('system.permission.data.columns.description')"
        min-width="220"
        show-overflow-tooltip
      />
      <el-table-column
        :label="$t('system.permission.data.columns.operation')"
        width="140"
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
          <el-button
            link
            type="danger"
            @click="handleDelete(row)"
          >
            {{ $t('common.actions.delete') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

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

    <DataPermissionDialog
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import {
  dataPermissionApi,
  type DataPermissionRecord,
  type PermissionListParams
} from '@/api/permissions'
import {
  fetchPermissionUserOptions,
  fetchPermissionObjectOptions,
  type PermissionUserOption,
  type PermissionObjectOption
} from './permissionOptions'
import DataPermissionDialog from './DataPermissionDialog.vue'

const { t } = useI18n()

const loading = ref(false)
const tableData = ref<DataPermissionViewRow[]>([])
const dialogVisible = ref(false)
const currentRow = ref<DataPermissionViewRow | null>(null)
const userOptions = ref<PermissionUserOption[]>([])
const objectOptions = ref<PermissionObjectOption[]>([])
const optionsLoading = reactive({
  users: false,
  objects: false
})

interface DataPermissionViewRow {
  id: string
  roleName: string
  businessObjectName: string
  permissionType: 'all' | 'department' | 'department_and_sub' | 'self' | 'custom'
  scopeType: DataPermissionRecord['scopeType']
  scopeExpression: string
  description: string
  scopeValue: Record<string, unknown>
  departmentField?: string
  userField?: string
}

const filterForm = reactive({
  role: '',
  objectModel: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const parseModelIdentifier = (input: string) => {
  const raw = input.trim()
  if (!raw) return { model: '' }
  const chunks = raw.split('.')
  if (chunks.length >= 2) {
    return { model: chunks[chunks.length - 1] }
  }
  return { model: raw }
}

const mapScopeTypeToUiType = (scopeType: DataPermissionRecord['scopeType']): DataPermissionViewRow['permissionType'] => {
  const map: Record<string, string> = {
    all: 'all',
    self_dept: 'department',
    self_and_sub: 'department_and_sub',
    self: 'self',
    custom: 'custom',
    specified: 'custom'
  }
  return map[scopeType] || 'custom'
}

const formatScopeExpression = (item: DataPermissionRecord) => {
  if (item.scopeType === 'custom') {
    const expression = item.scopeValue?.filterExpression
    if (typeof expression === 'string' && expression.trim()) {
      return expression
    }
    return item.scopeTypeDisplay || item.scopeType
  }

  if (item.scopeType === 'specified') {
    const departmentIds = item.scopeValue?.departmentIds
    if (Array.isArray(departmentIds) && departmentIds.length > 0) {
      return `department_ids: ${departmentIds.join(', ')}`
    }
    return item.scopeTypeDisplay || item.scopeType
  }

  return item.scopeTypeDisplay || item.scopeType
}

const mapRow = (item: DataPermissionRecord): DataPermissionViewRow => {
  const permissionType = mapScopeTypeToUiType(item.scopeType)

  return {
    id: item.id,
    roleName: item.userDisplay || '-',
    businessObjectName: item.contentTypeDisplay || '-',
    permissionType,
    scopeType: item.scopeType,
    scopeExpression: formatScopeExpression(item),
    description: item.description || '',
    scopeValue: item.scopeValue || {},
    departmentField: item.departmentField,
    userField: item.userField,
  }
}

const getPermissionTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    all: t('system.permission.data.types.all'),
    department: t('system.permission.data.types.department'),
    department_and_sub: t('system.permission.data.types.department_and_sub'),
    self: t('system.permission.data.types.self'),
    custom: t('system.permission.data.types.custom')
  }
  return labels[type] || type
}

const getPermissionTypeTag = (type: string) => {
  const tags: Record<string, string> = {
    all: 'danger',
    department: 'warning',
    department_and_sub: 'warning',
    self: 'info',
    custom: 'primary'
  }
  return tags[type] || 'info'
}

const fetchUserOptions = async (search = '') => {
  optionsLoading.users = true
  try {
    const users = await fetchPermissionUserOptions(search).catch(() => [])
    userOptions.value = users
  } finally {
    optionsLoading.users = false
  }
}

const fetchObjectOptions = async (search = '') => {
  optionsLoading.objects = true
  try {
    const objects = await fetchPermissionObjectOptions(search).catch(() => [])
    objectOptions.value = objects
  } finally {
    optionsLoading.objects = false
  }
}

const loadOptions = async () => {
  await Promise.all([
    fetchUserOptions(''),
    fetchObjectOptions('')
  ])
}

const handleUserRemoteSearch = (query: string) => {
  fetchUserOptions(query)
}

const handleObjectRemoteSearch = (query: string) => {
  fetchObjectOptions(query)
}

const fetchData = async () => {
  loading.value = true
  try {
    const params: PermissionListParams = {
      page: pagination.page,
      page_size: pagination.pageSize
    }

    if (filterForm.role.trim()) {
      params.user_username = filterForm.role.trim()
    }

    if (filterForm.objectModel.trim()) {
      params.content_type_model = parseModelIdentifier(filterForm.objectModel).model
    }

    const res = await dataPermissionApi.list(params)
    const results = Array.isArray(res?.results) ? res.results : []

    tableData.value = results.map(mapRow)
    pagination.total = Number(res?.count || 0)
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
  filterForm.objectModel = ''
  handleSearch()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: DataPermissionViewRow) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: DataPermissionViewRow) => {
  try {
    await ElMessageBox.confirm(
      t('common.messages.confirmDelete'),
      t('common.actions.confirm'),
      {
        type: 'warning'
      }
    )

    await dataPermissionApi.delete(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))

    if (tableData.value.length === 1 && pagination.page > 1) {
      pagination.page -= 1
    }

    fetchData()
  } catch (error: unknown) {
    if (error === 'cancel' || error === 'close') {
      return
    }
    ElMessage.error(t('common.messages.operationFailed'))
  }
}

onMounted(() => {
  loadOptions()
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
