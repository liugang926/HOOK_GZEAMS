<template>
  <div class="category-management">
    <el-container style="height: 100%;">
      <el-aside width="300px">
        <CategoryTree
          ref="treeRef"
          @select="handleSelectCategory"
          @add-root="handleAddRoot"
          @add-child="handleAddChild"
          @delete="handleDelete"
        />
      </el-aside>
      
      <el-main>
        <div
          v-if="mode === 'view' && currentCategory"
          class="category-detail"
        >
          <el-descriptions
            title="分类详情"
            :column="1"
            border
          >
            <template #extra>
              <el-button
                type="primary"
                @click="handleEdit"
              >
                编辑
              </el-button>
            </template>
            <el-descriptions-item label="编码">
              {{ currentCategory.code }}
            </el-descriptions-item>
            <el-descriptions-item label="名称">
              {{ currentCategory.name }}
            </el-descriptions-item>
            <el-descriptions-item label="上级分类ID">
              {{ currentCategory.parent_id || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="折旧方法">
              {{ formatDepreciationMethod(currentCategory.depreciation_method) }}
            </el-descriptions-item>
            <el-descriptions-item label="预计使用年限">
              {{ currentCategory.useful_life }} 月
            </el-descriptions-item>
            <el-descriptions-item label="残值率">
              {{ currentCategory.salvage_rate }}%
            </el-descriptions-item>
          </el-descriptions>
          
          <div
            v-if="!currentCategory.id"
            class="empty-tip"
            style="text-align: center; margin-top: 100px; color: #909399;"
          >
            请点击左侧添加或选择分类
          </div>
        </div>

        <div
          v-else-if="mode === 'view' && !currentCategory"
          class="empty-state"
        >
          <el-empty description="请选择左侧分类或新增分类" />
        </div>

        <CategoryForm
          v-else
          :model-value="editData"
          :parent-id="parentId"
          :parent-name="parentName"
          @success="handleSuccess"
          @cancel="handleCancel"
        />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CategoryTree from './components/CategoryTree.vue'
import CategoryForm from './components/CategoryForm.vue'

const treeRef = ref()
const mode = ref<'view' | 'edit' | 'create'>('view')
const currentCategory = ref<any>(null)
const editData = ref<any>(null)
const parentId = ref<string | null>(null)
const parentName = ref<string>('')

const handleSelectCategory = (category: any) => {
  if (mode.value === 'edit' || mode.value === 'create') {
    // Confirm if unsaved changes? Skipped for simplicity
  }
  mode.value = 'view'
  currentCategory.value = category
}

const handleAddRoot = () => {
  mode.value = 'create'
  editData.value = null
  parentId.value = null
  parentName.value = ''
}

const handleAddChild = (parent: any) => {
  mode.value = 'create'
  editData.value = null
  parentId.value = parent.id
  parentName.value = parent.name
}

const handleEdit = () => {
  mode.value = 'edit'
  editData.value = { ...currentCategory.value }
  parentId.value = currentCategory.value.parent_id
  // parentName logic is tricky if we don't have the parent object loaded.
  // For now we might ignore parent name in edit, or better, Tree could provide it.
}

const handleSuccess = () => {
  mode.value = 'view'
  currentCategory.value = null // Reset view or auto-select the new one?
  treeRef.value.fetchTree()
}

const handleCancel = () => {
  mode.value = 'view'
}

const handleDelete = () => {
  currentCategory.value = null
  mode.value = 'view'
}

const formatDepreciationMethod = (val: string) => {
  const map: Record<string, string> = {
    'straight_line': '年限平均法',
    'double_declining': '双倍余额递减法',
    'sum_of_years': '年数总和法',
    'none': '不计提折旧'
  }
  return map[val] || val
}
</script>

<style scoped>
.category-management {
  height: calc(100vh - 84px); /* Adjust based on layout header */
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.category-detail {
  padding: 20px;
  max-width: 800px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}
</style>
