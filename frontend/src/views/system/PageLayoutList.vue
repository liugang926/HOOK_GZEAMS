<template>
  <div class="page-layout-list">
    <div class="page-header">
      <div class="header-left">
        <el-button
          link
          @click="handleBack"
        >
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <h3>{{ objectName }} - 布局管理</h3>
      </div>
      <div class="header-actions">
        <el-tag
          type="info"
          size="small"
        >
          对象编码: {{ objectCode }}
        </el-tag>
        <el-button
          type="primary"
          @click="handleCreate"
        >
          新建布局
        </el-button>
      </div>
    </div>

    <!-- Layout Type Tabs -->
    <el-tabs
      v-model="activeLayoutType"
      @tab-change="handleTabChange"
    >
      <el-tab-pane
        label="表单布局"
        name="form"
      >
        <template #label>
          <span>表单布局</span>
          <el-badge
            v-if="layoutCounts.form > 0"
            :value="layoutCounts.form"
            class="layout-badge"
          />
        </template>
      </el-tab-pane>
      <el-tab-pane
        label="详情布局"
        name="detail"
      >
        <template #label>
          <span>详情布局</span>
          <el-badge
            v-if="layoutCounts.detail > 0"
            :value="layoutCounts.detail"
            class="layout-badge"
          />
        </template>
      </el-tab-pane>
      <el-tab-pane
        label="列表布局"
        name="list"
      >
        <template #label>
          <span>列表布局</span>
          <el-badge
            v-if="layoutCounts.list > 0"
            :value="layoutCounts.list"
            class="layout-badge"
          />
        </template>
      </el-tab-pane>
      <el-tab-pane
        label="搜索布局"
        name="search"
      >
        <template #label>
          <span>搜索布局</span>
          <el-badge
            v-if="layoutCounts.search > 0"
            :value="layoutCounts.search"
            class="layout-badge"
          />
        </template>
      </el-tab-pane>
    </el-tabs>

    <!-- Empty State -->
    <div
      v-if="!loading && filteredLayouts.length === 0"
      class="empty-state"
    >
      <el-empty :description="getEmptyDescription()">
        <el-button
          type="primary"
          @click="handleCreate"
        >
          创建{{ getLayoutTypeLabel(activeLayoutType) }}
        </el-button>
      </el-empty>
    </div>

    <!-- Layout Table -->
    <el-table
      v-else
      v-loading="loading"
      :data="filteredLayouts"
      border
      stripe
    >
      <el-table-column
        prop="layoutName"
        label="布局名称"
        width="220"
      >
        <template #default="{ row }">
          <div class="layout-name-cell">
            <span>{{ row.layoutName }}</span>
            <el-tag
              v-if="row.isSystem"
              type="info"
              size="small"
              effect="plain"
            >
              系统默认
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column
        prop="layoutCode"
        label="布局编码"
        width="180"
      />
      <el-table-column
        label="布局类型"
        width="120"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="getLayoutTypeTag(row.layoutType)"
            size="small"
          >
            {{ getLayoutTypeLabel(row.layoutType) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="description"
        label="描述"
        show-overflow-tooltip
      />
      <el-table-column
        label="版本"
        width="80"
        align="center"
      >
        <template #default="{ row }">
          <span class="version-badge">{{ row.version }}</span>
        </template>
      </el-table-column>
      <el-table-column
        label="默认"
        width="60"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            v-if="row.isDefault"
            type="success"
            size="small"
          >
            默认
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="状态"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <el-tag
            :type="getStatusTag(row.status)"
            size="small"
          >
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        label="操作"
        width="280"
        fixed="right"
      >
        <template #default="{ row }">
          <!-- System default layout actions -->
          <template v-if="row.isSystem">
            <el-button
              link
              type="primary"
              size="small"
              @click="handleCustomize(row)"
            >
              自定义
            </el-button>
            <el-button
              link
              type="info"
              size="small"
              @click="handlePreview(row)"
            >
              预览
            </el-button>
          </template>
          <!-- Custom layout actions -->
          <template v-else>
            <el-button
              link
              type="primary"
              size="small"
              @click="handleDesign(row)"
            >
              设计
            </el-button>
            <el-button
              link
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              link
              type="success"
              size="small"
              @click="handlePublish(row)"
            >
              发布
            </el-button>
            <el-button
              link
              :type="row.isActive ? 'warning' : 'success'"
              size="small"
              @click="handleToggleActive(row)"
            >
              {{ row.isActive ? '禁用' : '启用' }}
            </el-button>
            <el-popconfirm
              title="确定删除该布局吗？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button
                  link
                  type="danger"
                  size="small"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- Layout Designer Dialog -->
    <el-dialog
      v-model="designerVisible"
      :title="`布局设计器 - ${currentLayout?.layoutName || '新建布局'}`"
      width="95%"
      top="5vh"
      destroy-on-close
      append-to-body
    >
      <LayoutDesigner
        v-if="designerVisible && currentLayout"
        :layout-id="currentLayout.id"
        :layout-type="currentLayout.layoutType"
        :layout-name="currentLayout.layoutName"
        :object-code="objectCode"
        :business-object-id="currentLayout.business_object || currentLayout.businessObject || ''"
        @cancel="designerVisible = false"
        @save="handleLayoutSaved"
        @published="handleLayoutSaved"
      />
    </el-dialog>

    <!-- Create Layout Dialog -->
    <el-dialog
      v-model="createVisible"
      title="新建布局"
      width="600px"
    >
      <el-form
        :model="createForm"
        label-width="100px"
      >
        <el-form-item
          label="布局编码"
          required
        >
          <el-input
            v-model="createForm.layoutCode"
            placeholder="例如: asset_form_custom"
          />
        </el-form-item>
        <el-form-item
          label="布局名称"
          required
        >
          <el-input
            v-model="createForm.layoutName"
            placeholder="例如: 资产表单自定义布局"
          />
        </el-form-item>
        <el-form-item
          label="布局类型"
          required
        >
          <el-select
            v-model="createForm.layoutType"
            style="width: 100%"
          >
            <el-option
              label="表单布局"
              value="form"
            />
            <el-option
              label="列表布局"
              value="list"
            />
            <el-option
              label="详情布局"
              value="detail"
            />
            <el-option
              label="搜索布局"
              value="search"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="createForm.isDefault" />
          <span class="form-item-tip">默认布局将作为该业务对象此类型布局的首选</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="描述此布局的用途"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleCreateSubmit"
        >
          创建并设计
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import LayoutDesigner from '@/components/designer/LayoutDesigner.vue'
import { pageLayoutApi, getFieldDefinitions, type PageLayout } from '@/api/system'

const route = useRoute()
const router = useRouter()

const objectCode = computed(() => route.params.objectCode as string || route.query.objectCode as string || '')
const objectName = ref(route.query.objectName as string || '业务对象')
const loading = ref(false)
const tableData = ref<PageLayout[]>([])
const designerVisible = ref(false)
const createVisible = ref(false)
const currentLayout = ref<PageLayout | null>(null)
const submitting = ref(false)
const activeLayoutType = ref<'form' | 'list' | 'detail' | 'search'>('form')

const createForm = ref({
  layoutCode: '',
  layoutName: '',
  layoutType: 'form' as 'form' | 'list' | 'detail' | 'search',
  description: '',
  isDefault: false
})

// Layout counts by type
const layoutCounts = computed(() => {
  const counts = { form: 0, list: 0, detail: 0, search: 0 }
  tableData.value.forEach(layout => {
    if (layout.layoutType in counts) {
      counts[layout.layoutType as keyof typeof counts]++
    }
  })
  return counts
})

// Filter layouts by active tab
const filteredLayouts = computed(() => {
  return tableData.value.filter(layout => layout.layoutType === activeLayoutType.value)
})

const layoutTypeMap: Record<string, string> = {
  'form': '表单布局',
  'list': '列表布局',
  'detail': '详情布局',
  'search': '搜索布局'
}

const statusMap: Record<string, string> = {
  'draft': '草稿',
  'published': '已发布',
  'archived': '已归档'
}

const getLayoutTypeLabel = (type: string) => {
  return layoutTypeMap[type] || type
}

const getLayoutTypeTag = (type: string) => {
  const tags: Record<string, any> = {
    'form': 'success',
    'list': 'primary',
    'detail': 'warning',
    'search': 'info'
  }
  return tags[type] || 'info'
}

const getStatusLabel = (status: string) => {
  return statusMap[status] || status
}

const getStatusTag = (status: string) => {
  const tags: Record<string, any> = {
    'draft': 'info',
    'published': 'success',
    'archived': 'warning'
  }
  return tags[status] || 'info'
}

const getEmptyDescription = () => {
  const typeLabel = getLayoutTypeLabel(activeLayoutType.value)
  return `暂无${typeLabel}，点击下方按钮创建`
}

const handleTabChange = (tabName: string) => {
  activeLayoutType.value = tabName as 'form' | 'list' | 'detail' | 'search'
}

const fieldDefinitions = ref<any[]>([])

const loadFieldDefinitions = async () => {
  try {
    // The request interceptor unwraps { success: true, data: ... } automatically
    const fields = await getFieldDefinitions(objectCode.value)
    fieldDefinitions.value = fields || []
  } catch (error) {
    console.error('Failed to load field definitions:', error)
    fieldDefinitions.value = []
  }
}

const loadLayouts = async () => {
  loading.value = true
  try {
    // The request interceptor unwraps { success: true, data: ... } automatically
    // So res is already the data array
    const layouts = await pageLayoutApi.byObject(objectCode.value)
    tableData.value = layouts || []

    // If no custom layouts exist, add system default layouts
    if (tableData.value.length === 0) {
      addSystemDefaultLayouts()
    }
  } catch (error) {
    console.error('Failed to load page layouts:', error)
    // Start with empty array - user can create new layouts
    tableData.value = []
    addSystemDefaultLayouts()
  } finally {
    loading.value = false
  }
}

// Add system-generated default layouts based on field definitions
const addSystemDefaultLayouts = () => {
  const types: Array<'form' | 'list' | 'detail' | 'search'> = ['form', 'list', 'detail', 'search']

  types.forEach(type => {
    // Check if layout of this type exists
    const exists = tableData.value.some(l => l.layoutType === type)
    if (!exists) {
      // Add system default layout
      tableData.value.push({
        id: `system_${type}`,
        layoutCode: `system_default_${type}`,
        layoutName: getLayoutTypeLabel(type) + ' (系统默认)',
        layoutType: type,
        description: '基于字段定义自动生成的默认布局',
        layoutConfig: generateDefaultLayoutConfig(type),
        status: 'published',
        version: '1.0.0',
        isDefault: true,
        isActive: true,
        isSystem: true // Mark as system-generated
      } as any)
    }
  })
}

// Generate default layout config from field definitions
const generateDefaultLayoutConfig = (layoutType: 'form' | 'list' | 'detail' | 'search') => {
  const fields = fieldDefinitions.value.filter(f => !f.is_system || ['code', 'name', 'status', 'created_at'].includes(f.code))

  if (layoutType === 'list') {
    return {
      columns: fields.slice(0, 8).map(f => ({
        field_code: f.code,
        label: f.name,
        width: 120,
        sortable: !f.field_type?.includes('text') && !f.field_type?.includes('textarea'),
        fixed: ['code', 'name'].includes(f.code) ? 'left' : undefined
      })),
      actions: [
        { code: 'view', label: '查看', type: 'primary', position: 'table' },
        { code: 'edit', label: '编辑', type: 'default', position: 'table' },
        { code: 'delete', label: '删除', type: 'danger', position: 'table' }
      ]
    }
  }

  if (layoutType === 'search') {
    return {
      sections: [{
        id: 'search',
        type: 'section',
        title: '搜索条件',
        columns: 2,
        fields: fields.filter(f => f.is_searchable || ['code', 'name', 'status'].includes(f.code)).slice(0, 6).map(f => ({
          field_code: f.code,
          label: f.name,
          span: 1,
          component: getSearchComponent(f.field_type)
        }))
      }]
    }
  }

  // For form and detail
  const sections = []
  const basicFields = fields.filter(f =>
    ['code', 'name', 'status'].includes(f.code) ||
    (f.field_type !== 'sub_table' && f.field_type !== 'textarea' && f.field_type !== 'rich_text')
  ).slice(0, 12)

  if (basicFields.length > 0) {
    sections.push({
      id: 'basic',
      type: 'section',
      title: '基本信息',
      columns: 2,
      collapsible: false,
      fields: basicFields.map(f => ({
        field_code: f.code,
        label: f.name,
        span: f.field_type === 'textarea' || f.field_type === 'rich_text' ? 2 : 1,
        readonly: layoutType === 'detail',
        required: f.is_required,
        visible: true
      }))
    })
  }

  const textareaFields = fields.filter(f =>
    ['textarea', 'rich_text'].includes(f.field_type)
  )
  if (textareaFields.length > 0) {
    sections.push({
      id: 'description',
      type: 'section',
      title: '详细信息',
      columns: 1,
      collapsible: true,
      fields: textareaFields.map(f => ({
        field_code: f.code,
        label: f.name,
        span: 1,
        readonly: layoutType === 'detail',
        required: f.is_required,
        visible: true
      }))
    })
  }

  return { sections }
}

// Get search component type for field
const getSearchComponent = (fieldType: string) => {
  const componentMap: Record<string, string> = {
    'text': 'input',
    'textarea': 'input',
    'select': 'select',
    'multi_select': 'select',
    'date': 'date',
    'datetime': 'datetime',
    'boolean': 'select',
    'user': 'user',
    'department': 'department'
  }
  return componentMap[fieldType] || 'input'
}

const loadData = async () => {
  // Load field definitions first, then load layouts
  await loadFieldDefinitions()
  await loadLayouts()
}

const handleBack = () => {
  router.push({ name: 'BusinessObjectList' })
}

const handleCreate = () => {
  createForm.value = {
    layoutCode: '',
    layoutName: '',
    layoutType: activeLayoutType.value,
    description: '',
    isDefault: layoutCounts.value[activeLayoutType.value] === 0
  }
  createVisible.value = true
}

const handleCreateSubmit = async () => {
  if (!createForm.value.layoutCode || !createForm.value.layoutName) {
    ElMessage.warning('请填写布局编码和名称')
    return
  }

  submitting.value = true
  try {
    // The request interceptor unwraps { success: true, data: ... } automatically
    const newLayout = await pageLayoutApi.create({
      ...createForm.value,
      business_object: objectCode.value,
      status: 'draft',
      version: '0.1.0',
      layoutConfig: getDefaultLayoutConfig(createForm.value.layoutType)
    })
    ElMessage.success('布局创建成功')
    createVisible.value = false
    // Open designer with new layout (response is already unwrapped)
    currentLayout.value = newLayout
    designerVisible.value = true
    await loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleEdit = (row: PageLayout) => {
  currentLayout.value = row
  designerVisible.value = true
}

const handleDesign = (row: PageLayout) => {
  currentLayout.value = row
  designerVisible.value = true
}

const handlePublish = async (row: PageLayout) => {
  try {
    await ElMessageBox.confirm(
      `确定要发布布局 "${row.layoutName}" 吗？发布后将创建新版本。`,
      '确认发布',
      { type: 'warning' }
    )
    await pageLayoutApi.publish(row.id, { set_as_default: false })
    ElMessage.success('发布成功')
    await loadData()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '发布失败')
    }
  }
}

const handleToggleActive = async (row: PageLayout) => {
  try {
    await pageLayoutApi.partialUpdate(row.id, { is_active: !row.isActive })
    row.isActive = !row.isActive
    ElMessage.success(row.isActive ? '已启用' : '已禁用')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (row: PageLayout) => {
  try {
    await pageLayoutApi.delete(row.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleLayoutSaved = async () => {
  designerVisible.value = false
  await loadData()
}

// Handle customize button for system default layouts
// Creates a new custom layout based on the system default configuration
const handleCustomize = async (row: PageLayout) => {
  try {
    // Create a custom layout from the system default
    // The request interceptor unwraps the response, so customLayout is already the data
    const customLayout = await pageLayoutApi.create({
      layoutCode: `${row.layoutCode}_custom_${Date.now()}`,
      layoutName: row.layoutName.replace(' (系统默认)', ' (自定义)'),
      layoutType: row.layoutType,
      business_object: objectCode.value,
      description: `基于系统默认布局"${row.layoutName}"创建的自定义布局`,
      status: 'draft',
      version: '0.1.0',
      isDefault: false,
      layoutConfig: row.layoutConfig
    })
    ElMessage.success('已创建自定义布局')
    // Open designer with the new custom layout
    currentLayout.value = customLayout
    designerVisible.value = true
    await loadData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '创建自定义布局失败')
  }
}

// Handle preview button for layouts
const handlePreview = (row: PageLayout) => {
  ElMessage.info('预览功能开发中...')
  // TODO: Implement preview dialog showing how the layout will render
}

// Get default layout config for a layout type
function getDefaultLayoutConfig(layoutType: string) {
  if (layoutType === 'list') {
    return {
      columns: [],
      actions: []
    }
  }
  return {
    sections: []
  }
}

onMounted(() => {
  if (!objectCode.value) {
    ElMessage.warning('未指定业务对象')
    router.push({ name: 'BusinessObjectList' })
    return
  }
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
.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-header h3 {
  margin: 0;
  font-size: 18px;
}
.version-badge {
  font-size: 12px;
  color: #909399;
  font-family: monospace;
}
.layout-badge {
  margin-left: 4px;
}
:deep(.el-dialog__body) {
  padding: 0;
  max-height: 80vh;
}
.empty-state {
  padding: 60px 20px;
}
.form-item-tip {
  margin-left: 12px;
  font-size: 12px;
  color: #909399;
}
.layout-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
