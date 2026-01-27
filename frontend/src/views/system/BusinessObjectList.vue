<template>
  <div class="business-object-list">
    <div class="page-header">
      <h3>业务对象管理</h3>
      <el-button
        type="primary"
        @click="handleCreate"
      >
        新建业务对象
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
    >
      <el-table-column
        prop="name"
        label="对象名称"
        width="200"
      />
      <el-table-column
        prop="code"
        label="对象编码"
        width="150"
      />
      <el-table-column
        prop="description"
        label="描述"
        show-overflow-tooltip
      />
      <el-table-column
        label="类型"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="!row.is_hardcoded ? 'warning' : 'success'"
            size="small"
          >
            {{ !row.is_hardcoded ? '自定义' : '内置' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="field_count"
        label="字段数"
        width="80"
        align="center"
      />
      <el-table-column
        prop="layout_count"
        label="布局数"
        width="80"
        align="center"
      />
      <el-table-column
        label="工作流"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="row.enable_workflow ? 'success' : 'info'"
            size="small"
          >
            {{ row.enable_workflow ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="200"
        fixed="right"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleFields(row)"
          >
            字段管理
          </el-button>
          <el-button
            link
            type="primary"
            @click="handleLayouts(row)"
          >
            布局管理
          </el-button>
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
import { businessObjectApi, type BusinessObject } from '@/api/system'

const router = useRouter()
const loading = ref(false)
const tableData = ref<BusinessObject[]>([])
const dialogVisible = ref(false)
const currentRow = ref<BusinessObject | null>(null)

const loadBusinessObjects = async () => {
  loading.value = true
  try {
    const response = await businessObjectApi.list() as any
    // Backend returns {hardcoded: [...], custom: [...]}
    // We need to merge both arrays
    const hardcoded = response?.hardcoded || []
    const custom = response?.custom || []

    // Transform to table format with required properties
    tableData.value = [
      ...hardcoded.map((obj: any) => ({
        id: obj.code,
        code: obj.code,
        name: obj.name,
        nameEn: obj.nameEn || obj.name_en,
        description: obj.nameEn || obj.name_en || '',
        isHardcoded: true,
        is_hardcoded: true,
        enableWorkflow: false,
        enable_workflow: false,
        enableVersion: false,
        enable_version: false,
        enableSoftDelete: false,
        enable_soft_delete: false,
        fieldTypeCount: 0,
        layoutCount: 0,
        field_count: 0,
        layout_count: 0
      })),
      ...custom.map((obj: any) => ({
        id: obj.code,
        code: obj.code,
        name: obj.name,
        nameEn: obj.nameEn || obj.name_en,
        description: obj.description || '',
        isHardcoded: false,
        is_hardcoded: false,
        enableWorkflow: obj.enableWorkflow || obj.enable_workflow || false,
        enable_workflow: obj.enable_workflow || false,
        enableVersion: obj.enableVersion || obj.enable_version || false,
        enable_version: obj.enable_version || false,
        enableSoftDelete: obj.enableSoftDelete || obj.enable_soft_delete || false,
        enable_soft_delete: obj.enable_soft_delete || false,
        fieldTypeCount: obj.fieldCount || obj.field_count || 0,
        layoutCount: obj.layoutCount || obj.layout_count || 0,
        field_count: obj.field_count || 0,
        layout_count: obj.layout_count || 0
      }))
    ]
  } catch (error) {
    console.error('Failed to load business objects:', error)
    ElMessage.error('加载业务对象失败')
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

const handleEdit = (row: BusinessObject) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleFields = (row: BusinessObject) => {
  router.push({
    path: '/system/field-definitions',
    query: { objectCode: row.code, objectName: row.name }
  })
}

const handleLayouts = (row: BusinessObject) => {
  router.push({
    path: '/system/page-layouts',
    query: { objectCode: row.code, objectName: row.name }
  })
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
