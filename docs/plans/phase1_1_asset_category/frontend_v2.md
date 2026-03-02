# Phase 1.1: Asset Category System - Frontend Implementation

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement complete frontend functionality for asset category management, including tree display, CRUD operations, and custom category addition.

**Key Changes from v1:**
- ✅ All code converted to TypeScript
- ✅ All field names use camelCase consistently
- ✅ API service layer follows standard pattern
- ✅ Error handling uses standardized error codes
- ✅ Component examples updated with proper types

---

## Public Component References

### Page Components

| Component | Purpose | Import Path |
|-----------|---------|-------------|
| `BaseListPage` | Standard list page | `@/components/common/BaseListPage.vue` |
| `BaseFormPage` | Standard form page | `@/components/common/BaseFormPage.vue` |
| `BaseDetailPage` | Standard detail page | `@/components/common/BaseDetailPage.vue` |

### Base Components

| Component | Purpose | Import Path |
|-----------|---------|-------------|
| `BaseTable` | Unified table | `@/components/common/BaseTable.vue` |
| `BaseSearchBar` | Search bar | `@/components/common/BaseSearchBar.vue` |
| `BasePagination` | Pagination | `@/components/common/BasePagination.vue` |
| `BaseAuditInfo` | Audit information | `@/components/common/BaseAuditInfo.vue` |

### Column Management (Recommended)

| Component | Hook | Reference |
|-----------|-------|-----------|
| `ColumnManager` | Column visibility/sort/width config | `list_column_configuration.md` |
| `useColumnConfig` | Column config hook | `list_column_configuration.md` |

### Composables

| Hook | Purpose | Import Path |
|------|---------|-------------|
| `useListPage` | List page logic | `@/composables/useListPage.ts` |
| `useFormPage` | Form page logic | `@/composables/useFormPage.ts` |
| `usePermission` | Permission check | `@/composables/usePermission.ts` |

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/models/asset.ts

/**
 * Asset Category Model
 * All fields use camelCase naming convention
 */
export interface AssetCategory {
  id: string
  code: string
  name: string
  parentId: string | null
  parentPath: string[]
  level: number
  hasChildren: boolean
  children?: AssetCategory[]
  depreciationMethod: string
  defaultUsefulLife: number
  residualRate: number
  sortOrder: number
  isCustom: boolean
  isSystem: boolean
  fullName: string
  organizationId: string
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: string
  updatedBy?: string
}

/**
 * Category tree node for display
 */
export interface CategoryTreeNode extends AssetCategory {
  // Additional tree-specific properties
}

/**
 * Category creation data
 */
export interface CategoryCreate {
  code: string
  name: string
  parentId?: string | null
  depreciationMethod?: string
  defaultUsefulLife?: number
  residualRate?: number
  sortOrder?: number
}

/**
 * Category update data
 */
export interface CategoryUpdate extends Partial<CategoryCreate> {}

/**
 * Category filters for list view
 */
export interface CategoryFilters {
  page?: number
  pageSize?: number
  search?: string
  level?: number
  isCustom?: boolean
  parentId?: string | null
}
```

### API Service

```typescript
// frontend/src/api/assets.ts

import request from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type {
  AssetCategory,
  CategoryCreate,
  CategoryUpdate,
  CategoryFilters,
  CategoryTreeNode
} from '@/types/models/asset'

/**
 * Asset Category API
 * All methods return camelCase data
 * All request parameters accept camelCase (auto-converted to snake_case)
 */
export const categoryApi = {
  /**
   * Get category tree structure
   * @returns Category tree array
   */
  getTree(): Promise<CategoryTreeNode[]> {
    return request.get('/assets/categories/tree/')
  },

  /**
   * Get category list with pagination
   * @param filters - Filter parameters (camelCase)
   * @returns Paginated category list
   */
  list(filters?: CategoryFilters): Promise<PaginatedResponse<AssetCategory>> {
    return request.get('/assets/categories/', { params: filters })
  },

  /**
   * Get single category by ID
   * @param id - Category UUID
   * @returns Category detail
   */
  get(id: string): Promise<AssetCategory> {
    return request.get(`/assets/categories/${id}/`)
  },

  /**
   * Create new category
   * @param data - Category creation data (camelCase)
   * @returns Created category
   */
  create(data: CategoryCreate): Promise<AssetCategory> {
    return request.post('/assets/categories/', data)
  },

  /**
   * Update category
   * @param id - Category UUID
   * @param data - Category update data (camelCase)
   * @returns Updated category
   */
  update(id: string, data: CategoryUpdate): Promise<AssetCategory> {
    return request.put(`/assets/categories/${id}/`, data)
  },

  /**
   * Partial update category
   * @param id - Category UUID
   * @param data - Partial category data (camelCase)
   * @returns Updated category
   */
  partialUpdate(id: string, data: Partial<CategoryUpdate>): Promise<AssetCategory> {
    return request.patch(`/assets/categories/${id}/`, data)
  },

  /**
   * Delete category (soft delete)
   * @param id - Category UUID
   */
  delete(id: string): Promise<void> {
    return request.delete(`/assets/categories/${id}/`)
  },

  /**
   * Add child category
   * @param parentId - Parent category UUID
   * @param data - Child category data
   * @returns Created child category
   */
  addChild(parentId: string, data: CategoryCreate): Promise<AssetCategory> {
    return request.post(`/assets/categories/${parentId}/add_child/`, data)
  },

  /**
   * Batch delete categories
   * @param ids - Array of category UUIDs
   * @returns Batch operation result
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/assets/categories/batch-delete/', { ids })
  },

  /**
   * Restore deleted category
   * @param id - Category UUID
   */
  restore(id: string): Promise<void> {
    return request.post(`/assets/categories/${id}/restore/`)
  },

  /**
   * Get deleted categories
   * @param filters - Filter parameters
   * @returns Paginated deleted category list
   */
  getDeleted(filters?: CategoryFilters): Promise<PaginatedResponse<AssetCategory>> {
    return request.get('/assets/categories/deleted/', { params: filters })
  }
}

/**
 * Batch operation response
 */
export interface BatchResponse {
  summary: {
    total: number
    succeeded: number
    failed: number
  }
  results: Array<{
    id: string
    success: boolean
    error?: string
  }>
}
```

---

## Error Handling

All API calls are automatically handled by the axios interceptor. Components should use try-catch for specific error handling:

### Standard Error Handling Pattern

```vue
<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { categoryApi } from '@/api/assets'

const handleDelete = async (id: string) => {
  try {
    await categoryApi.delete(id)
    ElMessage.success('删除成功')
    // Refresh list or navigate
  } catch (error) {
    // Error already handled by interceptor showing user message
    // Optional: Add specific handling or logging here
    console.error('Delete failed:', error)
  }
}

const handleSubmit = async (data: CategoryCreate) => {
  try {
    await categoryApi.create(data)
    ElMessage.success('创建成功')
    // Navigate or refresh
  } catch (error) {
    // Validation errors are automatically displayed
    // Additional handling if needed
  }
}
</script>
```

### Standard Error Codes

| Error Code | HTTP Status | User Message |
|------------|-------------|--------------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问，请重新登录 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 请求的资源不存在 |
| `CONFLICT` | 409 | 资源冲突（如分类编码重复） |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被删除 |
| `SERVER_ERROR` | 500 | 服务器错误，请稍后再试 |

### Handling Validation Errors

```vue
<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { categoryApi } from '@/api/assets'

const handleSubmit = async (data: CategoryCreate) => {
  try {
    await categoryApi.create(data)
    ElMessage.success('创建成功')
  } catch (error: any) {
    // Check for validation errors
    if (error.code === 'VALIDATION_ERROR' && error.details) {
      // Show first validation error
      const firstField = Object.keys(error.details)[0]
      const firstMessage = error.details[firstField]?.[0]
      if (firstMessage) {
        ElMessage.error(firstMessage)
      }
    }
    // Error interceptor already shows general message
  }
}
</script>
```

---

## Component Implementation

### Category Management Page (Tree View)

```vue
<!-- frontend/src/views/assets/CategoryManagement.vue -->
<template>
  <div class="category-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资产分类</span>
          <el-button type="primary" @click="handleCreate">
            新建分类
          </el-button>
        </div>
      </template>

      <!-- Category Tree -->
      <el-tree
        v-loading="loading"
        :data="categoryTree"
        :props="treeProps"
        node-key="id"
        default-expand-all
        :expand-on-click-node="false"
        @node-click="handleNodeClick"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <span class="node-label">{{ node.label }}</span>
            <span class="node-code">({{ data.code }})</span>
            <span v-if="data.isSystem" class="system-tag">系统</span>
            <span v-else class="custom-tag">自定义</span>

            <div class="node-actions">
              <el-button
                link
                type="primary"
                size="small"
                @click.stop="handleAddChild(data)"
              >
                添加子分类
              </el-button>
              <el-button
                link
                type="primary"
                size="small"
                @click.stop="handleEdit(data)"
              >
                编辑
              </el-button>
              <el-button
                v-if="!data.isSystem"
                link
                type="danger"
                size="small"
                @click.stop="handleDelete(data)"
              >
                删除
              </el-button>
            </div>
          </div>
        </template>
      </el-tree>
    </el-card>

    <!-- Category Form Dialog -->
    <CategoryFormDialog
      v-model="formVisible"
      :category-id="selectedCategoryId"
      :parent-id="addParentId"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoryApi } from '@/api/assets'
import type { CategoryTreeNode } from '@/types/models/asset'
import CategoryFormDialog from './components/CategoryFormDialog.vue'

const loading = ref(false)
const categoryTree = ref<CategoryTreeNode[]>([])
const formVisible = ref(false)
const selectedCategoryId = ref<string>()
const addParentId = ref<string>()

const treeProps = {
  label: 'name',
  children: 'children'
}

/**
 * Load category tree
 */
const loadTree = async () => {
  loading.value = true
  try {
    categoryTree.value = await categoryApi.getTree()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

/**
 * Handle node click
 */
const handleNodeClick = (data: CategoryTreeNode) => {
  selectedCategoryId.value = data.id
  // Could show detail panel or navigate to detail page
}

/**
 * Handle create button
 */
const handleCreate = () => {
  selectedCategoryId.value = undefined
  addParentId.value = undefined
  formVisible.value = true
}

/**
 * Handle add child
 */
const handleAddChild = (data: CategoryTreeNode) => {
  selectedCategoryId.value = undefined
  addParentId.value = data.id
  formVisible.value = true
}

/**
 * Handle edit
 */
const handleEdit = (data: CategoryTreeNode) => {
  selectedCategoryId.value = data.id
  addParentId.value = undefined
  formVisible.value = true
}

/**
 * Handle delete
 */
const handleDelete = async (data: CategoryTreeNode) => {
  if (data.hasChildren) {
    ElMessage.warning('请先删除子分类')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除分类"${data.name}"吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await categoryApi.delete(data.id)
    ElMessage.success('删除成功')
    await loadTree()
  } catch (error) {
    // User cancelled or error handled by interceptor
  }
}

/**
 * Handle form saved
 */
const handleSaved = () => {
  formVisible.value = false
  loadTree()
}

onMounted(() => {
  loadTree()
})
</script>

<style scoped>
.category-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.node-label {
  font-weight: 500;
}

.node-code {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.system-tag,
.custom-tag {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.system-tag {
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.custom-tag {
  background: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.node-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}
</style>
```

### Category Form Dialog Component

```vue
<!-- frontend/src/views/assets/components/CategoryFormDialog.vue -->
<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑分类' : '新建分类'"
    width="600px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
    >
      <el-form-item label="分类编码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="请输入分类编码"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item label="分类名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入分类名称"
        />
      </el-form-item>

      <el-form-item label="上级分类" prop="parentId">
        <CategoryTreeSelect
          v-model="formData.parentId"
          :exclude-id="categoryId"
          placeholder="无（表示顶级分类）"
          clearable
        />
      </el-form-item>

      <el-form-item label="折旧方法" prop="depreciationMethod">
        <el-select
          v-model="formData.depreciationMethod"
          placeholder="请选择折旧方法"
        >
          <el-option label="平均年限法" value="straight_line" />
          <el-option label="双倍余额递减法" value="double_declining" />
          <el-option label="年数总和法" value="sum_of_years" />
          <el-option label="不计提折旧" value="no_depreciation" />
        </el-select>
      </el-form-item>

      <el-form-item label="使用年限（月）" prop="defaultUsefulLife">
        <el-input-number
          v-model="formData.defaultUsefulLife"
          :min="0"
          :max="600"
          placeholder="请输入使用年限"
        />
      </el-form-item>

      <el-form-item label="残值率（%）" prop="residualRate">
        <el-input-number
          v-model="formData.residualRate"
          :min="0"
          :max="100"
          :precision="2"
          placeholder="请输入残值率"
        />
      </el-form-item>

      <el-form-item label="排序号" prop="sortOrder">
        <el-input-number
          v-model="formData.sortOrder"
          :min="0"
          placeholder="请输入排序号"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ isEdit ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { categoryApi } from '@/api/assets'
import type { CategoryCreate, CategoryUpdate } from '@/types/models/asset'

interface Props {
  modelValue: boolean
  categoryId?: string
  parentId?: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'saved'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!props.categoryId)

// Form data - all fields in camelCase
const formData = ref<CategoryCreate & { id?: string }>({
  code: '',
  name: '',
  parentId: null,
  depreciationMethod: 'straight_line',
  defaultUsefulLife: 60,
  residualRate: 5,
  sortOrder: 0
})

// Validation rules
const rules: FormRules = {
  code: [
    { required: true, message: '请输入分类编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '只能包含大写字母、数字和下划线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' }
  ],
  defaultUsefulLife: [
    { required: true, message: '请输入使用年限', trigger: 'blur' }
  ],
  residualRate: [
    { required: true, message: '请输入残值率', trigger: 'blur' }
  ]
}

/**
 * Load category data for edit
 */
const loadData = async () => {
  if (!props.categoryId) return

  try {
    const category = await categoryApi.get(props.categoryId)

    // Map response to form data (all camelCase)
    formData.value = {
      id: category.id,
      code: category.code,
      name: category.name,
      parentId: category.parentId,
      depreciationMethod: category.depreciationMethod,
      defaultUsefulLife: category.defaultUsefulLife,
      residualRate: category.residualRate,
      sortOrder: category.sortOrder
    }
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Handle submit
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return // Validation failed
  }

  submitting.value = true

  try {
    if (isEdit.value) {
      // Update existing category
      const updateData: CategoryUpdate = {
        name: formData.value.name,
        parentId: formData.value.parentId,
        depreciationMethod: formData.value.depreciationMethod,
        defaultUsefulLife: formData.value.defaultUsefulLife,
        residualRate: formData.value.residualRate,
        sortOrder: formData.value.sortOrder
      }
      await categoryApi.update(props.categoryId!, updateData)
    } else {
      // Create new category
      const createData: CategoryCreate = {
        code: formData.value.code,
        name: formData.value.name,
        parentId: formData.value.parentId || props.parentId || null,
        depreciationMethod: formData.value.depreciationMethod,
        defaultUsefulLife: formData.value.defaultUsefulLife,
        residualRate: formData.value.residualRate,
        sortOrder: formData.value.sortOrder
      }
      await categoryApi.create(createData)
    }

    ElMessage.success(isEdit.value ? '保存成功' : '创建成功')
    emit('saved')
  } catch (error) {
    // Error handled by interceptor
  } finally {
    submitting.value = false
  }
}

/**
 * Handle close
 */
const handleClose = () => {
  emit('update:modelValue', false)
}

// Watch for dialog open
watch(() => props.modelValue, (val) => {
  if (val) {
    loadData()
    if (props.parentId) {
      formData.value.parentId = props.parentId
    }
  } else {
    formRef.value?.resetFields()
  }
})
</script>
```

### Category Tree Select Component

```vue
<!-- frontend/src/components/assets/CategoryTreeSelect.vue -->
<template>
  <el-tree-select
    v-model="selectedValue"
    :data="categories"
    :props="treeProps"
    :render-after-expand="false"
    check-strictly
    :placeholder="placeholder"
    clearable
    filterable
    :filter-node-method="filterNode"
    node-key="id"
    :exclude-id="excludeId"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { categoryApi } from '@/api/assets'
import type { CategoryTreeNode } from '@/types/models/asset'

interface Props {
  modelValue: string | null
  excludeId?: string
  placeholder?: string
}

interface Emits {
  (e: 'update:modelValue', value: string | null): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const categories = ref<CategoryTreeNode[]>([])
const selectedValue = ref<string | null>(props.modelValue)

const treeProps = {
  label: 'name',
  value: 'id',
  children: 'children'
}

/**
 * Filter tree nodes
 */
const filterNode = (value: string, data: CategoryTreeNode) => {
  if (!value) return true
  return data.name.toLowerCase().includes(value.toLowerCase()) ||
         data.code.toLowerCase().includes(value.toLowerCase())
}

/**
 * Load categories
 */
const loadCategories = async () => {
  try {
    let tree = await categoryApi.getTree()

    // Exclude specified ID and its descendants
    if (props.excludeId) {
      tree = excludeNode(tree, props.excludeId)
    }

    categories.value = tree
  } catch (error) {
    // Error handled by interceptor
  }
}

/**
 * Recursively exclude node and its children
 */
const excludeNode = (nodes: CategoryTreeNode[], excludeId: string): CategoryTreeNode[] => {
  return nodes
    .filter(node => node.id !== excludeId)
    .map(node => ({
      ...node,
      children: node.children ? excludeNode(node.children, excludeId) : undefined
    }))
}

/**
 * Handle model value changes
 */
watch(() => props.modelValue, (val) => {
  selectedValue.value = val
})

watch(selectedValue, (val) => {
  emit('update:modelValue', val)
})

onMounted(() => {
  loadCategories()
})
</script>
```

---

## Page Routes

```typescript
// frontend/src/router/index.ts

{
  path: '/assets',
  component: Layout,
  children: [
    {
      path: 'categories',
      name: 'AssetCategories',
      component: () => import('@/views/assets/CategoryManagement.vue'),
      meta: {
        title: '资产分类',
        requiresAuth: true,
        permissions: ['assets.view_category']
      }
    }
  ]
}
```

---

## Dependencies

### Backend Dependencies

| Module | Endpoint | Method | Purpose |
|--------|----------|--------|---------|
| Assets | `/api/assets/categories/tree/` | GET | Get category tree |
| Assets | `/api/assets/categories/` | GET/POST | List/Create categories |
| Assets | `/api/assets/categories/{id}/` | GET/PUT/DELETE | Category CRUD |
| Assets | `/api/assets/categories/{parentId}/add_child/` | POST | Add child category |
| Assets | `/api/assets/categories/batch-delete/` | POST | Batch delete |

### External Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| element-plus | latest | UI components |
| vue | 3.4+ | Frontend framework |
| vue-router | 4.x | Routing |
| pinia | 2.x | State management |
| axios | 1.x | HTTP client |

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/models/asset.ts` | Asset type definitions |
| `frontend/src/api/assets.ts` | Asset API service (includes category APIs) |
| `frontend/src/views/assets/CategoryManagement.vue` | Category management page |
| `frontend/src/views/assets/components/CategoryFormDialog.vue` | Category form dialog |
| `frontend/src/components/assets/CategoryTreeSelect.vue` | Category tree select component |

---

## Testing Checklist

- [ ] Tree loads and displays all categories
- [ ] Can create top-level category
- [ ] Can create child category under parent
- [ ] Can edit existing category
- [ ] Can delete category (without children)
- [ ] Cannot delete category with children (warning shown)
- [ ] System categories cannot be deleted
- [ ] Form validation works correctly
- [ ] API error handling displays correct messages
- [ ] All field names use camelCase in components
- [ ] Field names automatically convert to snake_case for API
