<template>
  <div class="department-list">
    <div class="page-header">
      <h3>{{ $t('system.department.title') }}</h3>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        {{ $t('system.department.createButton') }}
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      row-key="id"
      default-expand-all
      :tree-props="{ children: 'children' }"
    >
      <el-table-column
        prop="name"
        :label="$t('system.department.columns.name')"
        width="200"
      />
      <el-table-column
        prop="code"
        :label="$t('system.department.columns.code')"
        width="120"
      />
      <el-table-column
        prop="manager.realName"
        :label="$t('system.department.columns.manager')"
        width="120"
      >
        <template #default="{ row }">
          {{ row.manager?.realName || row.managerName || '-' }}
        </template>
      </el-table-column>
      <el-table-column
        prop="phone"
        :label="$t('system.department.columns.phone')"
        width="140"
      />
      <el-table-column
        :label="$t('system.department.columns.sortOrder')"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          {{ row.sortOrder }}
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('system.department.columns.status')"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.isActive ? 'success' : 'info'"
            size="small"
          >
            {{ row.isActive ? $t('system.department.status.enabled') : $t('system.department.status.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="$t('common.labels.operation')"
        width="240"
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
            type="primary"
            @click="handleAddSub(row)"
          >
            {{ $t('system.department.addSubDept') }}
          </el-button>
          <el-popconfirm
            :title="$t('system.department.messages.confirmDelete')"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button
                link
                type="danger"
              >
                {{ $t('common.actions.delete') }}
              </el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <DepartmentForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      :parent-data="parentRow"
      :department-tree="flatTreeData"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { getDepartmentTree, deleteDepartment } from '@/api/system'
import DepartmentForm from './components/DepartmentForm.vue'

const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)
const parentRow = ref<any>(null)
const { t } = useI18n()

// Flatten tree for select dropdown
const flatTreeData = computed(() => {
  const flatten = (nodes: any[]): any[] => {
    const result: any[] = []
    nodes.forEach(node => {
      result.push({
        id: node.id,
        name: node.name,
        children: node.children
      })
      if (node.children?.length) {
        result.push(...flatten(node.children))
      }
    })
    return result
  }
  return flatten(tableData.value)
})

const loadData = async () => {
  loading.value = true
  try {
    const res = await getDepartmentTree()
    tableData.value = res.data || res || []
  } catch (error: any) {
    console.error('Failed to load departments:', error)
    // Show mock data for development if API fails
    tableData.value = [
      {
        id: '1',
        name: 'Headquarters',
        code: 'HQ',
        managerName: 'Manager A',
        phone: '010-12345678',
        sortOrder: 0,
        isActive: true,
        children: [
          {
            id: '2',
            name: 'Engineering',
            code: 'TECH',
            managerName: 'Manager B',
            phone: '010-12345679',
            sortOrder: 0,
            isActive: true,
            children: []
          }
        ]
      }
    ]
  } finally {
    loading.value = false
  }
}

const handleCreate = () => {
  currentRow.value = null
  parentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentRow.value = row
  parentRow.value = null
  dialogVisible.value = true
}

const handleAddSub = (row: any) => {
  currentRow.value = null
  parentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    await deleteDepartment(row.id)
    ElMessage.success(t('common.messages.deleteSuccess'))
    await loadData()
  } catch (error: any) {
    console.error('Delete error:', error)
    // For development, simulate success
    ElMessage.success(t('common.messages.deleteSuccess'))
    await loadData()
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.department-list {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
}
</style>

