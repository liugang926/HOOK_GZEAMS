<template>
  <div class="business-object-list">
    <div class="page-header">
      <h3>业务对象管理</h3>
      <el-button type="primary" @click="handleCreate">新建业务对象</el-button>
    </div>

    <el-table
      :data="tableData"
      border
      v-loading="loading"
      stripe
    >
      <el-table-column prop="name" label="对象名称" width="200" />
      <el-table-column prop="code" label="对象编码" width="150" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="类型" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.isCustom ? 'warning' : 'success'" size="small">
            {{ row.isCustom ? '自定义' : '内置' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="工作流" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.enableWorkflow ? 'success' : 'info'" size="small">
            {{ row.enableWorkflow ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="版本控制" width="90" align="center">
        <template #default="{ row }">
          <el-tag :type="row.enableVersion ? 'success' : 'info'" size="small">
            {{ row.enableVersion ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="软删除" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.enableSoftDelete ? 'success' : 'info'" size="small">
            {{ row.enableSoftDelete ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="tableName" label="数据表" width="150" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleFields(row)">字段管理</el-button>
          <el-button link type="primary" @click="handleLayouts(row)">布局管理</el-button>
          <el-popconfirm
            v-if="row.isCustom"
            title="确定删除该业务对象吗？"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Business Object Form Dialog -->
    <BusinessObjectForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import BusinessObjectForm from './components/BusinessObjectForm.vue'

const router = useRouter()
const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)

// Mock API function - replace with actual API call
const loadBusinessObjects = async () => {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const res = await businessObjectApi.list()
    // tableData.value = res.data || res.results || []

    // Mock data for now
    tableData.value = [
      {
        id: '1',
        code: 'Asset',
        name: '固定资产',
        description: '固定资产主数据对象',
        isCustom: false,
        enableWorkflow: true,
        enableVersion: true,
        enableSoftDelete: true,
        tableName: 'assets_asset'
      },
      {
        id: '2',
        code: 'Employee',
        name: '员工信息',
        description: '员工基本信息对象',
        isCustom: true,
        enableWorkflow: false,
        enableVersion: false,
        enableSoftDelete: true,
        tableName: 'dynamic_employee'
      }
    ]
  } catch (error) {
    console.error('Failed to load business objects:', error)
  } finally {
    loading.value = false
  }
}

const loadData = () => {
  loadBusinessObjects()
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleFields = (row: any) => {
  router.push({
    path: '/system/field-definitions',
    query: { objectCode: row.code, objectName: row.name }
  })
}

const handleLayouts = (row: any) => {
  router.push({
    path: '/system/page-layouts',
    query: { objectCode: row.code, objectName: row.name }
  })
}

const handleDelete = async (row: any) => {
  try {
    // TODO: Replace with actual API call
    // await businessObjectApi.delete(row.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.business-object-list {
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
