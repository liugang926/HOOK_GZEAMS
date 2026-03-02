# Phase 1.1: 资产分类体系 - 前端实现

## 任务概述
实现资产分类的完整前端功能，支持树形展示、CRUD操作、自定义分类添加等。

---

## 公共组件引用

### 页面组件
本模块使用以下公共页面组件（详见 `common_base_features/frontend.md`）：

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseListPage` | 标准列表页面 | `@/components/common/BaseListPage.vue` |
| `BaseFormPage` | 标准表单页面 | `@/components/common/BaseFormPage.vue` |
| `BaseDetailPage` | 标准详情页面 | `@/components/common/BaseDetailPage.vue` |

### 基础组件

| 组件 | 用途 | 引用路径 |
|------|------|---------|
| `BaseTable` | 统一表格 | `@/components/common/BaseTable.vue` |
| `BaseSearchBar` | 搜索栏 | `@/components/common/BaseSearchBar.vue` |
| `BasePagination` | 分页 | `@/components/common/BasePagination.vue` |
| `BaseAuditInfo` | 审计信息 | `@/components/common/BaseAuditInfo.vue` |
| `BaseFileUpload` | 文件上传 | `@/components/common/BaseFileUpload.vue` |

### 列表字段显示管理（推荐）

| 组件 | Hook | 参考文档 |
|------|------|---------|
| `ColumnManager` | 列显示/隐藏/排序/列宽配置 | `list_column_configuration.md` |
| `useColumnConfig` | 列配置Hook（获取/保存/重置） | `list_column_configuration.md` |

**功能包括**:
- ✅ 列的显示/隐藏
- ✅ 列的拖拽排序
- ✅ 列宽调整
- ✅ 列固定（左/右）
- ✅ 用户个性化配置保存

### 布局组件

| 组件 | 用途 | 参考文档 |
|------|------|---------|
| `DynamicTabs` | 动态标签页 | `tab_configuration.md` |
| `SectionBlock` | 区块容器 | `section_block_layout.md` |
| `FieldRenderer` | 动态字段渲染 | `field_configuration_layout.md` |

### Composables/Hooks

| Hook | 用途 | 引用路径 |
|------|------|---------|
| `useListPage` | 列表页面逻辑 | `@/composables/useListPage.js` |
| `useFormPage` | 表单页面逻辑 | `@/composables/useFormPage.js` |
| `usePermission` | 权限检查 | `@/composables/usePermission.js` |

### 组件继承关系

```vue
<!-- 分类列表页面 -->
<BaseListPage
    title="资产分类"
    :fetch-method="fetchCategories"
    :columns="columns"
    :search-fields="searchFields"
>
    <!-- 自定义列插槽 -->
</BaseListPage>

<!-- 分类表单页面 -->
<BaseFormPage
    title="分类信息"
    :submit-method="handleSubmit"
    :initial-data="categoryData"
    :rules="rules"
>
    <!-- 自定义表单项 -->
</BaseFormPage>
```

---

## 页面路由

```javascript
// frontend/src/router/index.js

{
  path: '/assets',
  component: Layout,
  children: [
    {
      path: 'categories',
      name: 'AssetCategories',
      component: () => import('@/views/assets/CategoryManagement.vue'),
      meta: { title: '资产分类', requiresAuth: true }
    }
  ]
}
```

## API接口

```javascript
// frontend/src/api/assets.js

import request from '@/utils/request'

// 获取分类树
export function getCategoryTree() {
  return request({
    url: '/api/assets/categories/tree/',
    method: 'get'
  })
}

// 获取分类列表
export function getCategories(params) {
  return request({
    url: '/api/assets/categories/',
    method: 'get',
    params
  })
}

// 获取分类详情
export function getCategory(id) {
  return request({
    url: `/api/assets/categories/${id}/`,
    method: 'get'
  })
}

// 创建分类
export function createCategory(data) {
  return request({
    url: '/api/assets/categories/',
    method: 'post',
    data
  })
}

// 更新分类
export function updateCategory(id, data) {
  return request({
    url: `/api/assets/categories/${id}/`,
    method: 'put',
    data
  })
}

// 删除分类
export function deleteCategory(id) {
  return request({
    url: `/api/assets/categories/${id}/`,
    method: 'delete'
  })
}

// 添加子分类
export function addChildCategory(parentId, data) {
  return request({
    url: `/api/assets/categories/${parentId}/add_child/`,
    method: 'post',
    data
  })
}
```

## 主页面组件

```vue
<!-- frontend/src/views/assets/CategoryManagement.vue -->
<template>
  <div class="category-management">
    <!-- 页面头部 -->
    <el-page-header title="资产分类管理">
      <template #extra>
        <el-button type="primary" @click="handleAddRoot">
          <el-icon><Plus /></el-icon>
          添加根分类
        </el-button>
      </template>
    </el-page-header>

    <div class="content-container">
      <!-- 左侧分类树 -->
      <div class="tree-panel">
        <el-card header="分类树">
          <el-tree
            ref="treeRef"
            :data="categoryTree"
            :props="treeProps"
            node-key="id"
            :expand-on-click-node="false"
            highlight-current
            @node-click="handleNodeClick"
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node">
                <span class="node-name">{{ data.name }}</span>
                <span class="node-code">({{ data.code }})</span>
                <span class="node-actions">
                  <el-button
                    v-if="!data.is_custom"
                    link
                    size="small"
                    @click.stop="handleAddChild(node, data)"
                  >
                    添加子类
                  </el-button>
                  <el-button
                    link
                    size="small"
                    @click.stop="handleEdit(node, data)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    v-if="data.is_custom"
                    link
                    type="danger"
                    size="small"
                    @click.stop="handleDelete(node, data)"
                  >
                    删除
                  </el-button>
                </span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </div>

      <!-- 右侧详情/编辑面板 -->
      <div class="detail-panel">
        <el-card v-if="selectedCategory">
          <template #header>
            <span>{{ isEditMode ? '编辑分类' : '分类详情' }}</span>
          </template>

          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="120px"
            :disabled="!isEditMode && selectedCategory"
          >
            <el-form-item label="分类编码" prop="code">
              <el-input
                v-model="formData.code"
                placeholder="请输入分类编码"
                :disabled="!isEditMode || !selectedCategory.is_custom"
              />
            </el-form-item>

            <el-form-item label="分类名称" prop="name">
              <el-input
                v-model="formData.name"
                placeholder="请输入分类名称"
                :disabled="!isEditMode"
              />
            </el-form-item>

            <el-form-item label="上级分类">
              <el-cascader
                v-model="formData.parent_path"
                :options="categoryOptions"
                :props="{ value: 'id', label: 'name', checkStrictly: true }"
                :disabled="!isEditMode"
                clearable
                placeholder="无上级分类则为根分类"
              />
            </el-form-item>

            <el-form-item label="折旧方法" prop="depreciation_method">
              <el-select
                v-model="formData.depreciation_method"
                :disabled="!isEditMode"
              >
                <el-option label="直线法" value="straight_line" />
                <el-option label="双倍余额递减法" value="double_declining" />
                <el-option label="年数总和法" value="sum_of_years" />
                <el-option label="不计提折旧" value="no_depreciation" />
              </el-select>
            </el-form-item>

            <el-form-item label="使用年限(月)" prop="default_useful_life">
              <el-input-number
                v-model="formData.default_useful_life"
                :min="0"
                :disabled="!isEditMode"
              />
            </el-form-item>

            <el-form-item label="残值率(%)" prop="residual_rate">
              <el-input-number
                v-model="formData.residual_rate"
                :min="0"
                :max="100"
                :precision="2"
                :disabled="!isEditMode"
              />
            </el-form-item>

            <el-form-item label="排序号">
              <el-input-number
                v-model="formData.sort_order"
                :disabled="!isEditMode"
              />
            </el-form-item>

            <el-form-item v-if="isEditMode">
              <el-button type="primary" @click="handleSave">保存</el-button>
              <el-button @click="handleCancel">取消</el-button>
            </el-form-item>
          </el-form>

          <!-- 查看模式下的统计信息 -->
          <div v-if="!isEditMode" class="category-stats">
            <el-divider />
            <el-descriptions :column="2" border>
              <el-descriptions-item label="分类层级">
                {{ selectedCategory.level }}
              </el-descriptions-item>
              <el-descriptions-item label="子分类数量">
                {{ selectedCategory.children?.length || 0 }}
              </el-descriptions-item>
              <el-descriptions-item label="是否自定义">
                <el-tag :type="selectedCategory.is_custom ? 'success' : 'info'">
                  {{ selectedCategory.is_custom ? '是' : '否' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="完整路径">
                {{ selectedCategory.full_name }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>

        <!-- 未选择分类时的提示 -->
        <el-empty v-else description="请选择左侧分类查看详情或添加子分类" />
      </div>
    </div>

    <!-- 添加根分类对话框 -->
    <el-dialog v-model="addRootDialogVisible" title="添加根分类" width="500px">
      <el-form ref="addRootFormRef" :model="addRootForm" :rules="addRootRules" label-width="120px">
        <el-form-item label="分类编码" prop="code">
          <el-input v-model="addRootForm.code" placeholder="请输入分类编码" />
        </el-form-item>
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="addRootForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        <el-form-item label="折旧方法" prop="depreciation_method">
          <el-select v-model="addRootForm.depreciation_method">
            <el-option label="直线法" value="straight_line" />
            <el-option label="双倍余额递减法" value="double_declining" />
            <el-option label="年数总和法" value="sum_of_years" />
            <el-option label="不计提折旧" value="no_depreciation" />
          </el-select>
        </el-form-item>
        <el-form-item label="使用年限(月)" prop="default_useful_life">
          <el-input-number v-model="addRootForm.default_useful_life" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addRootDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveAddRoot">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getCategoryTree,
  createCategory,
  updateCategory,
  deleteCategory,
  addChildCategory
} from '@/api/assets'

// 状态数据
const categoryTree = ref([])
const selectedCategory = ref(null)
const isEditMode = ref(false)
const addRootDialogVisible = ref(false)

// 表单数据
const formData = reactive({
  id: null,
  code: '',
  name: '',
  parent_id: null,
  parent_path: [],
  depreciation_method: 'straight_line',
  default_useful_life: 60,
  residual_rate: 5.00,
  sort_order: 0
})

// 添加根分类表单
const addRootForm = reactive({
  code: '',
  name: '',
  depreciation_method: 'straight_line',
  default_useful_life: 60
})

// 表单校验规则
const formRules = {
  code: [
    { required: true, message: '请输入分类编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '编码只能包含大写字母、数字和下划线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' }
  ],
  depreciation_method: [
    { required: true, message: '请选择折旧方法', trigger: 'change' }
  ],
  default_useful_life: [
    { required: true, message: '请输入使用年限', trigger: 'blur' }
  ]
}

const addRootRules = {
  code: [{ required: true, message: '请输入分类编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }]
}

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'name',
  value: 'id'
}

// 获取分类列表（用于级联选择）
const categoryOptions = computed(() => {
  return buildCascaderOptions(categoryTree.value)
})

function buildCascaderOptions(tree) {
  const options = []
  for (const node of tree) {
    const option = {
      id: node.id,
      name: node.name,
      code: node.code,
      children: buildCascaderOptions(node.children || [])
    }
    options.push(option)
  }
  return options
}

// 加载分类树
const loadCategoryTree = async () => {
  try {
    const data = await getCategoryTree()
    categoryTree.value = data
  } catch (error) {
    ElMessage.error('加载分类失败')
  }
}

// 节点点击事件
const handleNodeClick = (node, data) => {
  selectedCategory.value = data
  isEditMode.value = false

  // 填充表单数据
  Object.assign(formData, {
    id: data.id,
    code: data.code,
    name: data.name,
    parent_id: data.parent_id || null,
    parent_path: data.parent_path || [],
    depreciation_method: data.depreciation_method,
    default_useful_life: data.default_useful_life,
    residual_rate: data.residual_rate,
    sort_order: data.sort_order
  })
}

// 添加根分类
const handleAddRoot = () => {
  addRootDialogVisible.value = true
}

// 保存添加根分类
const handleSaveAddRoot = async () => {
  try {
    await createCategory({
      ...addRootForm,
      parent_id: null
    })
    ElMessage.success('添加成功')
    addRootDialogVisible.value = false
    // 重置表单
    Object.assign(addRootForm, {
      code: '',
      name: '',
      depreciation_method: 'straight_line',
      default_useful_life: 60
    })
    await loadCategoryTree()
  } catch (error) {
    ElMessage.error('添加失败')
  }
}

// 添加子分类
const handleAddChild = (node, data) => {
  selectedCategory.value = data
  isEditMode.value = true

  // 重置表单，设置父分类
  Object.assign(formData, {
    id: null,
    code: '',
    name: '',
    parent_id: data.id,
    parent_path: [],
    depreciation_method: data.depreciation_method,
    default_useful_life: data.default_useful_life,
    residual_rate: data.residual_rate
  })
}

// 编辑分类
const handleEdit = (node, data) => {
  if (data.is_custom) {
    selectedCategory.value = data
    isEditMode.value = true
  } else {
    ElMessage.warning('系统分类不可编辑')
  }
}

// 删除分类
const handleDelete = async (node, data) => {
  try {
    await ElMessageBox.confirm(
      `确认删除分类"${data.name}"吗？`,
      '确认删除',
      { type: 'warning' }
    )

    await deleteCategory(data.id)
    ElMessage.success('删除成功')
    selectedCategory.value = null
    await loadCategoryTree()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 保存表单
const handleSave = async () => {
  try {
    if (formData.id) {
      // 更新
      await updateCategory(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      // 新建
      await createCategory(formData)
      ElMessage.success('创建成功')
    }

    isEditMode.value = false
    await loadCategoryTree()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 取消编辑
const handleCancel = () => {
  isEditMode.value = false
  // 恢复原始数据
  if (selectedCategory.value) {
    handleNodeClick(null, selectedCategory.value)
  }
}

onMounted(() => {
  loadCategoryTree()
})
</script>

<style scoped>
.category-management {
  padding: 20px;
}

.content-container {
  display: flex;
  gap: 20px;
  margin-top: 20px;
}

.tree-panel {
  width: 350px;
  flex-shrink: 0;
}

.detail-panel {
  flex: 1;
  min-width: 0;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  width: 100%;
  padding-right: 20px;
}

.node-name {
  flex: 1;
}

.node-code {
  margin-left: 10px;
  color: #999;
  font-size: 12px;
}

.node-actions {
  display: none;
  margin-left: 10px;
}

.custom-tree-node:hover .node-actions {
  display: flex;
  gap: 5px;
}

.category-stats {
  margin-top: 20px;
}
</style>
```

## 组件目录结构

```
frontend/src/
├── api/
│   └── assets.js                    # API接口定义
├── views/
│   └── assets/
│       └── CategoryManagement.vue    # 分类管理页面
├── components/
│   └── assets/
│       └── CategoryTree.vue          # 可复用的分类树组件（可选）
└── router/
    └── index.js                      # 路由配置
```

## 实施步骤

1. ✅ 创建 API 接口文件 `api/assets.js`
2. ✅ 创建页面组件 `views/assets/CategoryManagement.vue`
3. ✅ 配置路由
4. ✅ 验证功能

## 输出产物

- API接口文件: `frontend/src/api/assets.js`
- 页面组件: `frontend/src/views/assets/CategoryManagement.vue`
- 路由配置: `frontend/src/router/index.js`
