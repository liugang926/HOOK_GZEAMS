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
            :title="`${t('assets.category.title')} ${t('common.actions.detail')}`"
            :column="1"
            border
          >
            <template #extra>
              <el-button
                type="primary"
                @click="handleEdit"
              >
                {{ t('common.actions.edit') }}
              </el-button>
            </template>
            <el-descriptions-item :label="t('assets.category.code')">
              {{ currentCategory.code }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('assets.category.name')">
              {{ currentCategory.name }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('assets.category.parent')">
              {{ currentCategory.parent_id || '-' }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('assets.category.method')">
              {{ formatDepreciationMethod(currentCategory.depreciation_method) }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('assets.category.usefulLife')">
              {{ currentCategory.useful_life }} {{ t('assets.category.months') }}
            </el-descriptions-item>
            <el-descriptions-item :label="t('assets.category.salvageRate')">
              {{ currentCategory.salvage_rate }}%
            </el-descriptions-item>
          </el-descriptions>

          <div
            v-if="!currentCategory.id"
            class="empty-tip"
            style="text-align: center; margin-top: 100px; color: #909399;"
          >
            {{ t('common.messages.noData') }}
          </div>
        </div>

        <div
          v-else-if="mode === 'view' && !currentCategory"
          class="empty-state"
        >
          <el-empty :description="t('common.messages.noData')" />
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
import { useI18n } from 'vue-i18n'
import CategoryTree from './components/CategoryTree.vue'
import CategoryForm from './components/CategoryForm.vue'

const { t } = useI18n()

const treeRef = ref()
const mode = ref<'view' | 'edit' | 'create'>('view')
const currentCategory = ref<any>(null)
const editData = ref<any>(null)
const parentId = ref<string | null>(null)
const parentName = ref<string>('')

const handleSelectCategory = (category: any) => {
  if (mode.value === 'edit' || mode.value === 'create') {
    // Keep current behavior: skip dirty-check confirmation for now.
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
}

const handleSuccess = () => {
  mode.value = 'view'
  currentCategory.value = null
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
    straight_line: t('assets.depreciation.straightLine'),
    double_declining: t('assets.depreciation.doubleDeclining'),
    sum_of_years: t('assets.depreciation.sumOfYears'),
    none: t('assets.depreciation.noDepreciation')
  }
  return map[val] || val
}
</script>

<style scoped>
.category-management {
  height: calc(100vh - 84px);
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
