<template>
  <div class="field-definition-list">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h3>{{ objectName }} - 字段管理</h3>
      </div>
      <el-button type="primary" @click="handleCreate">添加字段</el-button>
    </div>

    <el-table
      :data="tableData"
      border
      v-loading="loading"
      stripe
      row-key="id"
    >
      <el-table-column prop="sortOrder" label="排序" width="70" align="center" />
      <el-table-column prop="name" label="字段名称" width="150" />
      <el-table-column prop="code" label="字段编码" width="150" />
      <el-table-column label="字段类型" width="120" align="center">
        <template #default="{ row }">
          <el-tag size="small">{{ getFieldTypeLabel(row.fieldType) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="必填" width="70" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.isRequired" color="#f56c6c"><Check /></el-icon>
        </template>
      </el-table-column>
      <el-table-column label="只读" width="70" align="center">
        <template #default="{ row }">
          <el-icon v-if="row.isReadonly"><Lock /></el-icon>
        </template>
      </el-table-column>
      <el-table-column label="系统字段" width="90" align="center">
        <template #default="{ row }">
          <el-tag v-if="row.isSystem" type="info" size="small">系统</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            @click="handleEdit(row)"
            :disabled="row.isSystem"
          >
            编辑
          </el-button>
          <el-popconfirm
            v-if="!row.isSystem"
            title="确定删除该字段吗？"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Field Definition Form Dialog -->
    <FieldDefinitionForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      :object-code="objectCode"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Check, Lock } from '@element-plus/icons-vue'
import FieldDefinitionForm from './components/FieldDefinitionForm.vue'

const route = useRoute()
const router = useRouter()

const objectCode = computed(() => route.params.objectCode as string || route.query.objectCode as string || '')
const objectName = ref(route.query.objectName as string || '业务对象')
const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)

// Field type mapping
const fieldTypeOptions: Record<string, string> = {
  'text': '单行文本',
  'textarea': '多行文本',
  'number': '数字',
  'currency': '货币',
  'date': '日期',
  'datetime': '日期时间',
  'select': '下拉选择',
  'multi_select': '多选',
  'radio': '单选',
  'checkbox': '复选框',
  'switch': '开关',
  'user': '用户选择',
  'dept': '部门选择',
  'asset': '资产选择',
  'reference': '关联引用',
  'subtable': '子表',
  'file': '文件上传',
  'image': '图片上传',
  'formula': '计算公式',
  'auto_number': '自动编号'
}

const getFieldTypeLabel = (type: string) => {
  return fieldTypeOptions[type] || type
}

// Load field definitions
const loadFields = async () => {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const res = await fieldDefinitionApi.byObject(objectCode.value)
    // tableData.value = res.data || res.results || []

    // Mock data
    tableData.value = [
      {
        id: '1',
        code: 'name',
        name: '资产名称',
        fieldType: 'text',
        isRequired: true,
        isReadonly: false,
        isSystem: false,
        sortOrder: 1,
        description: '资产的名称'
      },
      {
        id: '2',
        code: 'category',
        name: '资产分类',
        fieldType: 'select',
        isRequired: true,
        isReadonly: false,
        isSystem: false,
        sortOrder: 2,
        description: '资产所属分类'
      },
      {
        id: '3',
        code: 'purchaseDate',
        name: '购置日期',
        fieldType: 'date',
        isRequired: false,
        isReadonly: false,
        isSystem: false,
        sortOrder: 3,
        description: '资产购置日期'
      },
      {
        id: '4',
        code: 'price',
        name: '资产原值',
        fieldType: 'currency',
        isRequired: false,
        isReadonly: false,
        isSystem: false,
        sortOrder: 4,
        description: '资产购置原值'
      }
    ]
  } catch (error) {
    console.error('Failed to load field definitions:', error)
  } finally {
    loading.value = false
  }
}

const loadData = () => {
  loadFields()
}

const handleBack = () => {
  router.push({ name: 'BusinessObjectList' })
}

const handleCreate = () => {
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentRow.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  try {
    // TODO: Replace with actual API call
    // await fieldDefinitionApi.delete(row.id)
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
.field-definition-list {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
}
</style>
