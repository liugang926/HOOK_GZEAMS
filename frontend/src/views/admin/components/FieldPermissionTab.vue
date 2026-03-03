<template>
  <div class="field-permission-tab">
    <el-form
      :model="filterForm"
      inline
      class="filter-form"
    >
      <el-form-item :label="$t('system.permission.field.toolbar.role')">
        <el-select
          v-model="filterForm.role"
          filterable
          remote
          reserve-keyword
          clearable
          :placeholder="$t('system.permission.field.toolbar.rolePlaceholder')"
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
      <el-form-item :label="$t('system.permission.field.toolbar.object')">
        <el-select
          v-model="filterForm.businessObject"
          filterable
          remote
          reserve-keyword
          clearable
          :placeholder="$t('system.permission.field.toolbar.objectPlaceholder')"
          :loading="optionsLoading.objects"
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
        :label="$t('system.permission.field.columns.role')"
        width="160"
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
        min-width="220"
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
import {
  fieldPermissionApi,
  type FieldPermissionRecord,
  type PermissionListParams
} from '@/api/permissions'
import {
  fetchPermissionUserOptions,
  fetchPermissionObjectOptions,
  type PermissionUserOption,
  type PermissionObjectOption
} from './permissionOptions'
import FieldPermissionDialog from './FieldPermissionDialog.vue'

const { t } = useI18n()

const loading = ref(false)
const tableData = ref<FieldPermissionViewRow[]>([])
const dialogVisible = ref(false)
const currentRow = ref<FieldPermissionViewRow | null>(null)
const userOptions = ref<PermissionUserOption[]>([])
const objectOptions = ref<PermissionObjectOption[]>([])
const optionsLoading = reactive({
  users: false,
  objects: false
})

interface FieldPermissionViewRow {
  id: string
  roleName: string
  businessObjectName: string
  fieldName: string
  canRead: boolean
  canWrite: boolean
  isVisible: boolean
  description: string
  permissionType: FieldPermissionRecord['permissionType']
  permissionTypeDisplay?: string
  maskRule?: string | null
  customMaskPattern?: string
}

const filterForm = reactive({
  role: '',
  businessObject: ''
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

const mapPermissionToFlags = (permissionType: FieldPermissionRecord['permissionType']) => {
  switch (permissionType) {
    case 'write':
      return { canRead: true, canWrite: true, isVisible: true }
    case 'hidden':
      return { canRead: false, canWrite: false, isVisible: false }
    case 'masked':
      return { canRead: true, canWrite: false, isVisible: true }
    case 'read':
    default:
      return { canRead: true, canWrite: false, isVisible: true }
  }
}

const mapRow = (item: FieldPermissionRecord): FieldPermissionViewRow => {
  const flags = mapPermissionToFlags(item.permissionType)
  return {
    id: item.id,
    roleName: item.userDisplay || '-',
    businessObjectName: item.contentTypeDisplay || '-',
    fieldName: item.fieldName,
    canRead: flags.canRead,
    canWrite: flags.canWrite,
    isVisible: flags.isVisible,
    description: item.description || '',
    permissionType: item.permissionType,
    permissionTypeDisplay: item.permissionTypeDisplay,
    maskRule: item.maskRule,
    customMaskPattern: item.customMaskPattern,
  }
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

    if (filterForm.businessObject.trim()) {
      params.content_type_model = parseModelIdentifier(filterForm.businessObject).model
    }

    const res = await fieldPermissionApi.list(params)
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
  filterForm.businessObject = ''
  handleSearch()
}

const handleEdit = (row: FieldPermissionViewRow) => {
  currentRow.value = row
  dialogVisible.value = true
}

onMounted(() => {
  loadOptions()
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
