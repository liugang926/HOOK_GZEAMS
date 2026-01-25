<template>
  <div class="page-layout-list">
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h3>{{ objectName }} - 布局管理</h3>
      </div>
      <el-button type="primary" @click="handleCreate">新建布局</el-button>
    </div>

    <el-table
      :data="tableData"
      border
      v-loading="loading"
      stripe
    >
      <el-table-column prop="layoutName" label="布局名称" width="200" />
      <el-table-column prop="layoutCode" label="布局编码" width="150" />
      <el-table-column label="布局类型" width="120" align="center">
        <template #default="{ row }">
          <el-tag :type="getLayoutTypeTag(row.layoutType)" size="small">
            {{ getLayoutTypeLabel(row.layoutType) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
            {{ row.isActive ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleDesign(row)">设计</el-button>
          <el-button
            link
            :type="row.isActive ? 'warning' : 'success'"
            @click="handleToggleActive(row)"
          >
            {{ row.isActive ? '禁用' : '启用' }}
          </el-button>
          <el-popconfirm
            title="确定删除该布局吗？"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Layout Designer Dialog (placeholder for now) -->
    <el-dialog
      v-model="designerVisible"
      title="布局设计器"
      width="800px"
    >
      <div class="designer-placeholder">
        <el-empty description="布局设计器功能正在开发中">
          <el-button type="primary" @click="designerVisible = false">关闭</el-button>
        </el-empty>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const objectCode = computed(() => route.params.objectCode as string || route.query.objectCode as string || '')
const objectName = ref(route.query.objectName as string || '业务对象')
const loading = ref(false)
const tableData = ref<any[]>([])
const designerVisible = ref(false)
const currentLayout = ref<any>(null)

const layoutTypeMap: Record<string, string> = {
  'form': '表单布局',
  'list': '列表布局',
  'detail': '详情布局'
}

const getLayoutTypeLabel = (type: string) => {
  return layoutTypeMap[type] || type
}

const getLayoutTypeTag = (type: string) => {
  const tags: Record<string, any> = {
    'form': 'success',
    'list': 'primary',
    'detail': 'warning'
  }
  return tags[type] || 'info'
}

const loadLayouts = async () => {
  loading.value = true
  try {
    // TODO: Replace with actual API call
    // const res = await pageLayoutApi.byObject(objectCode.value)
    // tableData.value = res.data || res.results || []

    // Mock data
    tableData.value = [
      {
        id: '1',
        layoutCode: 'asset_form_default',
        layoutName: '资产表单默认布局',
        layoutType: 'form',
        description: '资产新增/编辑表单的默认布局',
        isActive: true
      },
      {
        id: '2',
        layoutCode: 'asset_list_default',
        layoutName: '资产列表默认布局',
        layoutType: 'list',
        description: '资产列表页的默认布局',
        isActive: true
      },
      {
        id: '3',
        layoutCode: 'asset_detail_default',
        layoutName: '资产详情默认布局',
        layoutType: 'detail',
        description: '资产详情页的默认布局',
        isActive: true
      }
    ]
  } catch (error) {
    console.error('Failed to load page layouts:', error)
  } finally {
    loading.value = false
  }
}

const loadData = () => {
  loadLayouts()
}

const handleBack = () => {
  router.push({ name: 'BusinessObjectList' })
}

const handleCreate = () => {
  ElMessage.info('新建布局功能正在开发中')
}

const handleEdit = (row: any) => {
  ElMessage.info('编辑布局功能正在开发中')
}

const handleDesign = (row: any) => {
  currentLayout.value = row
  designerVisible.value = true
}

const handleToggleActive = async (row: any) => {
  try {
    // TODO: Replace with actual API call
    // await pageLayoutApi.update(row.id, { isActive: !row.isActive })
    row.isActive = !row.isActive
    ElMessage.success(row.isActive ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    // TODO: Replace with actual API call
    // await pageLayoutApi.delete(row.id)
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
.page-layout-list {
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
.designer-placeholder {
  padding: 40px 0;
  text-align: center;
}
</style>
