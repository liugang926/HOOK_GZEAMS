# System Management Frontend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build frontend UI for the metadata-driven low-code system management features, enabling users to configure business objects, field definitions, page layouts, and other system settings through a visual interface.

**Architecture:** Vue 3 (Composition API) + TypeScript + Element Plus UI, following the existing codebase patterns (BaseListPage component, centralized API clients, camelCase/snake_case transformation).

**Tech Stack:** Vue 3, TypeScript, Element Plus, Vite, Pinia (for state management)

---

## Prerequisites

**Files to Reference:**
- `frontend/src/views/system/DepartmentList.vue` - Example of a complete list page
- `frontend/src/components/common/BaseListPage.vue` - Reusable list component
- `frontend/src/api/system.ts` - System API client (already exists)
- `frontend/src/types/common.ts` - Common TypeScript interfaces
- `frontend/src/router/index.ts` - Router configuration

**Key Patterns:**
- Use `BaseListPage` for all list views
- Use Composition API with `<script setup>`
- Use Element Plus components
- Use centralized API clients from `@/api/`
- Handle loading states and error messages

---

## Phase 1: Low-Code Core UI (P0)

### Task 1: Business Object Management List Page

**Files:**
- Create: `frontend/src/views/system/BusinessObjectList.vue`

**Step 1: Create the Business Object List component**

Create `frontend/src/views/system/BusinessObjectList.vue`:

```vue
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
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleFields(row)">字段管理</el-button>
          <el-button link type="primary" @click="handleLayouts(pageLayout)">布局管理</el-button>
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
    name: 'FieldDefinitionList',
    params: { objectCode: row.code }
  })
}

const handleLayouts = (row: any) => {
  router.push({
    name: 'PageLayoutList',
    params: { objectCode: row.code }
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
```

**Step 2: Create the Business Object Form component**

Create `frontend/src/views/system/components/BusinessObjectForm.vue`:

```vue
<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑业务对象' : '新建业务对象'"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="对象编码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="请输入对象编码（英文，如：Asset）"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item label="对象名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入对象名称（中文，如：固定资产）"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入对象描述"
        />
      </el-form-item>

      <el-form-item label="数据表名" prop="tableName">
        <el-input
          v-model="formData.tableName"
          placeholder="数据库表名（如：assets_asset）"
        />
      </el-form-item>

      <el-form-item label="主键字段">
        <el-input
          v-model="formData.pkField"
          placeholder="默认为 id"
        />
      </el-form-item>

      <el-form-item label="启用工作流">
        <el-switch v-model="formData.enableWorkflow" />
        <span class="form-tip">启用后可配置审批流程</span>
      </el-form-item>

      <el-form-item label="启用版本控制">
        <el-switch v-model="formData.enableVersion" />
        <span class="form-tip">启用后记录数据变更历史</span>
      </el-form-item>

      <el-form-item label="启用软删除">
        <el-switch v-model="formData.enableSoftDelete" />
        <span class="form-tip">删除数据时不物理删除</span>
      </el-form-item>

      <el-form-item label="是否系统对象">
        <el-switch v-model="formData.isSystem" :disabled="isEdit" />
        <span class="form-tip">系统对象不可删除</span>
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

interface Props {
  visible: boolean
  data?: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  code: '',
  name: '',
  description: '',
  tableName: '',
  pkField: 'id',
  enableWorkflow: false,
  enableVersion: false,
  enableSoftDelete: true,
  isSystem: false
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入对象编码', trigger: 'blur' },
    { pattern: /^[A-Z][a-zA-Z0-9]*$/, message: '编码必须以大写字母开头，只能包含字母和数字', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入对象名称', trigger: 'blur' }
  ],
  tableName: [
    { required: true, message: '请输入数据表名', trigger: 'blur' }
  ]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    // Edit mode - populate form
    Object.assign(formData.value, props.data)
  } else if (val) {
    // Create mode - reset form
    formRef.value?.resetFields()
    formData.value = {
      code: '',
      name: '',
      description: '',
      tableName: '',
      pkField: 'id',
      enableWorkflow: false,
      enableVersion: false,
      enableSoftDelete: true,
      isSystem: false
    }
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      // TODO: Replace with actual API call
      if (isEdit.value) {
        // await businessObjectApi.update(props.data.id, formData.value)
      } else {
        // await businessObjectApi.create(formData.value)
      }
      ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
```

**Step 3: Add routes to router**

Edit `frontend/src/router/index.ts`, add after the `system/departments` route (around line 237):

```typescript
// System - Business Objects
{
  path: 'system/business-objects',
  name: 'BusinessObjectList',
  component: () => import('@/views/system/BusinessObjectList.vue'),
  meta: { title: '业务对象管理' }
},
{
  path: 'system/business-objects/create',
  name: 'BusinessObjectCreate',
  component: () => import('@/views/system/components/BusinessObjectForm.vue'),
  meta: { title: '新建业务对象' }
},
{
  path: 'system/business-objects/:id/edit',
  name: 'BusinessObjectEdit',
  component: () => import('@/views/system/components/BusinessObjectForm.vue'),
  meta: { title: '编辑业务对象' }
},
```

**Step 4: Run dev server to verify**

```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:5173/system/business-objects` and verify the page loads without errors.

**Step 5: Commit**

```bash
git add frontend/src/views/system/BusinessObjectList.vue
git add frontend/src/views/system/components/BusinessObjectForm.vue
git add frontend/src/router/index.ts
git commit -m "feat(system): add business object management list and form pages"
```

---

### Task 2: Field Definition Management Page

**Files:**
- Create: `frontend/src/views/system/FieldDefinitionList.vue`
- Create: `frontend/src/views/system/components/FieldDefinitionForm.vue`

**Step 1: Create the Field Definition List component**

Create `frontend/src/views/system/FieldDefinitionList.vue`:

```vue
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

const route = useRoute()
const router = useRouter()

const objectCode = computed(() => route.params.objectCode as string || route.query.objectCode as string)
const objectName = ref('业务对象')
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
```

**Step 2: Create the Field Definition Form component**

Create `frontend/src/views/system/components/FieldDefinitionForm.vue`:

```vue
<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑字段' : '添加字段'"
    width="700px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="字段编码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="请输入字段编码（英文，如：userName）"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item label="字段名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入字段名称（中文，如：用户名）"
        />
      </el-form-item>

      <el-form-item label="字段类型" prop="fieldType">
        <el-select
          v-model="formData.fieldType"
          placeholder="请选择字段类型"
          @change="handleFieldTypeChange"
        >
          <el-option label="单行文本" value="text" />
          <el-option label="多行文本" value="textarea" />
          <el-option label="数字" value="number" />
          <el-option label="货币" value="currency" />
          <el-option label="日期" value="date" />
          <el-option label="日期时间" value="datetime" />
          <el-option label="下拉选择" value="select" />
          <el-option label="多选" value="multi_select" />
          <el-option label="单选" value="radio" />
          <el-option label="复选框" value="checkbox" />
          <el-option label="开关" value="switch" />
          <el-option label="用户选择" value="user" />
          <el-option label="部门选择" value="dept" />
          <el-option label="资产选择" value="asset" />
          <el-option label="关联引用" value="reference" />
          <el-option label="子表" value="subtable" />
          <el-option label="文件上传" value="file" />
          <el-option label="图片上传" value="image" />
          <el-option label="计算公式" value="formula" />
          <el-option label="自动编号" value="auto_number" />
        </el-select>
      </el-form-item>

      <!-- Reference target for reference type -->
      <el-form-item
        v-if="formData.fieldType === 'reference' || formData.fieldType === 'subtable'"
        label="关联对象"
        prop="referenceObject"
      >
        <el-select
          v-model="formData.referenceObject"
          placeholder="请选择关联的业务对象"
        >
          <el-option
            v-for="obj in businessObjects"
            :key="obj.code"
            :label="obj.name"
            :value="obj.code"
          />
        </el-select>
      </el-form-item>

      <!-- Options for select/radio/checkbox -->
      <el-form-item
        v-if="['select', 'multi_select', 'radio', 'checkbox'].includes(formData.fieldType)"
        label="选项配置"
        prop="options"
      >
        <div class="options-editor">
          <div
            v-for="(option, index) in formData.options"
            :key="index"
            class="option-item"
          >
            <el-input
              v-model="option.label"
              placeholder="选项名称"
              style="width: 150px"
            />
            <el-input
              v-model="option.value"
              placeholder="选项值"
              style="width: 100px"
            />
            <el-color-picker
              v-model="option.color"
              show-alpha
              size="small"
            />
            <el-button
              link
              type="danger"
              @click="removeOption(index)"
            >
              删除
            </el-button>
          </div>
          <el-button link type="primary" @click="addOption">
            + 添加选项
          </el-button>
        </div>
      </el-form-item>

      <!-- Formula expression -->
      <el-form-item
        v-if="formData.fieldType === 'formula'"
        label="公式表达式"
        prop="formulaExpression"
      >
        <el-input
          v-model="formData.formulaExpression"
          type="textarea"
          :rows="2"
          placeholder="如: {quantity} * {price}"
        />
        <div class="form-tip">使用 {字段编码} 引用其他字段</div>
      </el-form-item>

      <el-form-item label="排序号" prop="sortOrder">
        <el-input-number v-model="formData.sortOrder" :min="0" :max="9999" />
      </el-form-item>

      <el-form-item label="默认值" prop="defaultValue">
        <el-input
          v-model="formData.defaultValue"
          :placeholder="getDefaultValuePlaceholder()"
        />
      </el-form-item>

      <el-form-item label="占位提示" prop="placeholder">
        <el-input
          v-model="formData.placeholder"
          placeholder="输入框的占位提示文字"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          placeholder="字段描述说明"
        />
      </el-form-item>

      <el-form-item label="是否必填">
        <el-switch v-model="formData.isRequired" />
      </el-form-item>

      <el-form-item label="是否只读">
        <el-switch v-model="formData.isReadonly" />
      </el-form-item>

      <el-form-item label="是否唯一">
        <el-switch v-model="formData.isUnique" />
      </el-form-item>

      <el-form-item label="是否列表显示">
        <el-switch v-model="formData.showInList" />
        <span class="form-tip">在列表页默认显示</span>
      </el-form-item>

      <el-form-item label="列表宽度">
        <el-input-number
          v-model="formData.listWidth"
          :min="50"
          :max="500"
          :step="10"
        />
        <span class="form-tip">列表页列宽度（像素）</span>
      </el-form-item>

      <!-- Validation rules -->
      <el-form-item
        v-if="['text', 'textarea'].includes(formData.fieldType)"
        label="最大长度"
      >
        <el-input-number v-model="formData.maxLength" :min="1" :max="10000" />
      </el-form-item>

      <el-form-item
        v-if="['number', 'currency'].includes(formData.fieldType)"
        label="数值范围"
      >
        <el-input-number
          v-model="formData.minValue"
          placeholder="最小值"
          style="width: 120px"
        />
        <span style="margin: 0 10px">-</span>
        <el-input-number
          v-model="formData.maxValue"
          placeholder="最大值"
          style="width: 120px"
        />
      </el-form-item>

      <el-form-item
        v-if="formData.fieldType === 'number'"
        label="小数位数"
      >
        <el-input-number v-model="formData.decimalPlaces" :min="0" :max="6" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ isEdit ? '保存' : '添加' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

interface Props {
  visible: boolean
  data?: any
  objectCode?: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!props.data?.id)

// Mock business objects for reference
const businessObjects = ref([
  { code: 'Asset', name: '固定资产' },
  { code: 'Employee', name: '员工信息' },
  { code: 'Department', name: '部门' }
])

const formData = ref({
  code: '',
  name: '',
  fieldType: 'text',
  referenceObject: '',
  options: [] as Array<{ label: string; value: string; color: string }>,
  formulaExpression: '',
  sortOrder: 0,
  defaultValue: '',
  placeholder: '',
  description: '',
  isRequired: false,
  isReadonly: false,
  isUnique: false,
  showInList: true,
  listWidth: 120,
  maxLength: 255,
  minValue: undefined as number | undefined,
  maxValue: undefined as number | undefined,
  decimalPlaces: 2
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入字段编码', trigger: 'blur' },
    { pattern: /^[a-z][a-zA-Z0-9]*$/, message: '编码必须以小写字母开头', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入字段名称', trigger: 'blur' }
  ],
  fieldType: [
    { required: true, message: '请选择字段类型', trigger: 'change' }
  ],
  referenceObject: [
    { required: true, message: '请选择关联对象', trigger: 'change' }
  ]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    // Edit mode
    Object.assign(formData.value, props.data)
    if (!formData.value.options) {
      formData.value.options = []
    }
  } else if (val) {
    // Create mode
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
    code: '',
    name: '',
    fieldType: 'text',
    referenceObject: '',
    options: [],
    formulaExpression: '',
    sortOrder: tableData.value?.length || 0,
    defaultValue: '',
    placeholder: '',
    description: '',
    isRequired: false,
    isReadonly: false,
    isUnique: false,
    showInList: true,
    listWidth: 120,
    maxLength: 255,
    minValue: undefined,
    maxValue: undefined,
    decimalPlaces: 2
  }
  formRef.value?.clearValidate()
}

const getDefaultValuePlaceholder = () => {
  const type = formData.value.fieldType
  const placeholders: Record<string, string> = {
    text: '默认文本值',
    number: '默认数字值',
    date: '如: 2024-01-01',
    switch: 'true/false',
    select: '选项值'
  }
  return placeholders[type] || ''
}

const handleFieldTypeChange = () => {
  // Reset type-specific fields
  formData.value.options = []
  formData.value.formulaExpression = ''
  formData.value.referenceObject = ''
}

const addOption = () => {
  formData.value.options.push({
    label: '',
    value: '',
    color: '#409eff'
  })
}

const removeOption = (index: number) => {
  formData.value.options.splice(index, 1)
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const data = {
        ...formData.value,
        businessObject: props.objectCode
      }

      // TODO: Replace with actual API call
      if (isEdit.value) {
        // await fieldDefinitionApi.update(props.data.id, data)
      } else {
        // await fieldDefinitionApi.create(data)
      }

      ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitting.value = false
    }
  })
}

// Reference to table data for default sort order
const tableData = ref<any[]>([])
</script>

<style scoped>
.options-editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
</style>
```

**Step 3: Add routes to router**

Edit `frontend/src/router/index.ts`, add after the business object routes:

```typescript
// System - Field Definitions
{
  path: 'system/field-definitions',
  name: 'FieldDefinitionList',
  component: () => import('@/views/system/FieldDefinitionList.vue'),
  meta: { title: '字段定义管理' }
},
```

**Step 4: Run dev server to verify**

```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:5173/system/field-definitions?objectCode=Asset` and verify.

**Step 5: Commit**

```bash
git add frontend/src/views/system/FieldDefinitionList.vue
git add frontend/src/views/system/components/FieldDefinitionForm.vue
git add frontend/src/router/index.ts
git commit -m "feat(system): add field definition management page"
```

---

### Task 3: Page Layout Designer

**Files:**
- Create: `frontend/src/views/system/PageLayoutList.vue`
- Create: `frontend/src/views/system/components/PageLayoutDesigner.vue`

**Step 1: Create the Page Layout List component**

Create `frontend/src/views/system/PageLayoutList.vue`:

```vue
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

    <!-- Layout Form Dialog -->
    <PageLayoutForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      :object-code="objectCode"
      @success="loadData"
    />

    <!-- Layout Designer Dialog -->
    <PageLayoutDesigner
      v-model:visible="designerVisible"
      :layout="currentLayout"
      :object-code="objectCode"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const objectCode = computed(() => route.params.objectCode as string || route.query.objectCode as string)
const objectName = ref('业务对象')
const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const designerVisible = ref(false)
const currentRow = ref<any>(null)
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
  currentRow.value = null
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  currentRow.value = row
  dialogVisible.value = true
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
</style>
```

**Step 2: Create the Page Layout Designer component**

Create `frontend/src/views/system/components/PageLayoutDesigner.vue`:

```vue
<template>
  <el-dialog
    :model-value="visible"
    :title="layout?.layoutName ? `设计布局: ${layout.layoutName}` : '设计布局'"
    width="900px"
    fullscreen
    @update:model-value="handleClose"
  >
    <div class="layout-designer">
      <!-- Toolbar -->
      <div class="designer-toolbar">
        <div class="toolbar-left">
          <el-select v-model="layoutType" placeholder="布局类型" disabled>
            <el-option label="表单布局" value="form" />
            <el-option label="列表布局" value="list" />
            <el-option label="详情布局" value="detail" />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button @click="handleAddSection">
            <el-icon><Plus /></el-icon>
            添加分组
          </el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">
            保存布局
          </el-button>
        </div>
      </div>

      <!-- Canvas -->
      <div class="designer-canvas">
        <div
          v-for="(section, sIndex) in layoutConfig.sections"
          :key="section.id"
          class="layout-section"
          :class="{ collapsed: section.collapsed }"
        >
          <div class="section-header" @click="toggleSection(sIndex)">
            <span class="section-title">{{ section.title || `分组 ${sIndex + 1}` }}</span>
            <div class="section-actions">
              <el-button
                link
                size="small"
                @click.stop="editSection(sIndex)"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button
                link
                size="small"
                type="danger"
                @click.stop="removeSection(sIndex)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
              <el-button link size="small">
                <el-icon>
                  <component :is="section.collapsed ? 'ArrowDown' : 'ArrowUp'" />
                </el-icon>
              </el-button>
            </div>
          </div>

          <div v-show="!section.collapsed" class="section-content">
            <div class="section-fields">
              <draggable
                v-model="section.fields"
                group="fields"
                item-key="id"
                @end="onFieldDragEnd"
              >
                <template #item="{ element: field, index }">
                  <div class="field-item">
                    <el-icon class="drag-handle"><Rank /></el-icon>
                    <span class="field-label">{{ getFieldLabel(field) }}</span>
                    <el-button
                      link
                      size="small"
                      type="danger"
                      @click="removeField(sIndex, index)"
                    >
                      <el-icon><Close /></el-icon>
                    </el-button>
                  </div>
                </template>
              </draggable>

              <div class="add-field-area">
                <el-dropdown trigger="click" @command="cmd => addField(sIndex, cmd)">
                  <el-button link type="primary">
                    <el-icon><Plus /></el-icon>
                    添加字段
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item
                        v-for="field in availableFields"
                        :key="field.code"
                        :command="field.code"
                      >
                        {{ field.name }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- Section layout settings -->
            <div class="section-settings">
              <el-form-item label="列数">
                <el-radio-group v-model="section.columns">
                  <el-radio-button :label="1">1列</el-radio-button>
                  <el-radio-button :label="2">2列</el-radio-button>
                  <el-radio-button :label="3">3列</el-radio-button>
                  <el-radio-button :label="4">4列</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <el-empty
          v-if="layoutConfig.sections.length === 0"
          description="暂无分组，点击上方按钮添加"
          :image-size="100"
        />
      </div>

      <!-- Available Fields Panel -->
      <div class="fields-panel">
        <div class="panel-header">
          <span>可用字段</span>
        </div>
        <div class="panel-content">
          <div
            v-for="field in availableFields"
            :key="field.code"
            class="available-field"
            draggable="true"
            @dragstart="onFieldDragStart($event, field)"
          >
            <el-tag size="small">{{ field.name }}</el-tag>
            <span class="field-code">{{ field.code }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Section Edit Dialog -->
    <el-dialog
      v-model="sectionDialogVisible"
      title="编辑分组"
      width="500px"
    >
      <el-form :model="sectionForm" label-width="80px">
        <el-form-item label="分组名称">
          <el-input v-model="sectionForm.title" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="默认展开">
          <el-switch v-model="sectionForm.collapsed" :active-value="false" :inactive-value="true" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sectionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSection">确定</el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete, Close, Rank, ArrowDown, ArrowUp } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'

interface Props {
  visible: boolean
  layout?: any
  objectCode?: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const saving = ref(false)
const layoutType = ref('form')
const sectionDialogVisible = ref(false)
const currentSectionIndex = ref(-1)

const layoutConfig = ref({
  sections: [] as Array<{
    id: string
    title?: string
    fields: string[]
    columns: number
    collapsed: boolean
    visible: boolean
  }>
})

const sectionForm = ref({
  title: '',
  collapsed: false
})

// Mock available fields
const availableFields = ref([
  { code: 'name', name: '资产名称', fieldType: 'text' },
  { code: 'code', name: '资产编码', fieldType: 'text' },
  { code: 'category', name: '资产分类', fieldType: 'select' },
  { code: 'status', name: '资产状态', fieldType: 'select' },
  { code: 'purchaseDate', name: '购置日期', fieldType: 'date' },
  { code: 'price', name: '资产原值', fieldType: 'currency' },
  { code: 'location', name: '存放位置', fieldType: 'select' },
  { code: 'manager', name: '使用人', fieldType: 'user' },
  { code: 'department', name: '使用部门', fieldType: 'dept' },
  { code: 'description', name: '备注说明', fieldType: 'textarea' }
])

watch(() => props.visible, (val) => {
  if (val && props.layout) {
    // Load existing layout
    layoutType.value = props.layout.layoutType || 'form'
    // TODO: Load actual layout config
    layoutConfig.value = {
      sections: [
        {
          id: 'section_1',
          title: '基本信息',
          fields: ['code', 'name', 'category'],
          columns: 2,
          collapsed: false,
          visible: true
        },
        {
          id: 'section_2',
          title: '详细信息',
          fields: ['purchaseDate', 'price', 'location'],
          columns: 2,
          collapsed: false,
          visible: true
        }
      ]
    }
  }
})

const getFieldLabel = (fieldCode: string) => {
  const field = availableFields.value.find(f => f.code === fieldCode)
  return field ? field.name : fieldCode
}

const handleAddSection = () => {
  layoutConfig.value.sections.push({
    id: `section_${Date.now()}`,
    title: `分组 ${layoutConfig.value.sections.length + 1}`,
    fields: [],
    columns: 2,
    collapsed: false,
    visible: true
  })
}

const editSection = (index: number) => {
  currentSectionIndex.value = index
  const section = layoutConfig.value.sections[index]
  sectionForm.value = {
    title: section.title || '',
    collapsed: section.collapsed || false
  }
  sectionDialogVisible.value = true
}

const saveSection = () => {
  if (currentSectionIndex.value >= 0) {
    layoutConfig.value.sections[currentSectionIndex.value].title = sectionForm.value.title
    layoutConfig.value.sections[currentSectionIndex.value].collapsed = sectionForm.value.collapsed
  }
  sectionDialogVisible.value = false
}

const removeSection = (index: number) => {
  layoutConfig.value.sections.splice(index, 1)
}

const toggleSection = (index: number) => {
  layoutConfig.value.sections[index].collapsed = !layoutConfig.value.sections[index].collapsed
}

const addField = (sectionIndex: number, fieldCode: string) => {
  const section = layoutConfig.value.sections[sectionIndex]
  if (!section.fields.includes(fieldCode)) {
    section.fields.push(fieldCode)
  }
}

const removeField = (sectionIndex: number, fieldIndex: number) => {
  layoutConfig.value.sections[sectionIndex].fields.splice(fieldIndex, 1)
}

const onFieldDragStart = (event: DragEvent, field: any) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('fieldCode', field.code)
  }
}

const onFieldDragEnd = () => {
  // Handle drag end if needed
}

const handleSave = async () => {
  saving.value = true
  try {
    const config = {
      layoutConfig: layoutConfig.value,
      businessObject: props.objectCode
    }

    // TODO: Replace with actual API call
    // if (props.layout?.id) {
    //   await pageLayoutApi.update(props.layout.id, config)
    // } else {
    //   await pageLayoutApi.create(config)
    // }

    ElMessage.success('保存成功')
    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.layout-designer {
  display: flex;
  flex-direction: column;
  height: 70vh;
}

.designer-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.designer-canvas {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #ffffff;
}

.fields-panel {
  width: 200px;
  border-left: 1px solid #dcdfe6;
  background-color: #f5f7fa;
}

.panel-header {
  padding: 10px;
  font-weight: bold;
  border-bottom: 1px solid #dcdfe6;
}

.panel-content {
  padding: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.available-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px;
  margin-bottom: 5px;
  background-color: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: move;
}

.field-code {
  font-size: 12px;
  color: #909399;
}

.layout-section {
  margin-bottom: 20px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  cursor: pointer;
  user-select: none;
}

.section-title {
  font-weight: bold;
}

.section-actions {
  display: flex;
  gap: 5px;
}

.section-content {
  padding: 15px;
}

.section.collapsed .section-content {
  display: none;
}

.section-fields {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background-color: #ecf5ff;
  border: 1px dashed #409eff;
  border-radius: 4px;
}

.drag-handle {
  cursor: move;
}

.field-label {
  flex: 1;
}

.add-field-area {
  padding: 10px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  text-align: center;
}

.section-settings {
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
}
</style>
```

**Step 3: Add routes to router**

Edit `frontend/src/router/index.ts`:

```typescript
// System - Page Layouts
{
  path: 'system/page-layouts',
  name: 'PageLayoutList',
  component: () => import('@/views/system/PageLayoutList.vue'),
  meta: { title: '页面布局管理' }
},
```

**Step 4: Install vuedraggable for drag-drop**

```bash
cd frontend
npm install vuedraggable@next
```

**Step 5: Run dev server to verify**

```bash
npm run dev
```

**Step 6: Commit**

```bash
git add frontend/src/views/system/PageLayoutList.vue
git add frontend/src/views/system/components/PageLayoutDesigner.vue
git add frontend/src/router/index.ts
git add frontend/package.json
git add frontend/package-lock.json
git commit -m "feat(system): add page layout designer with drag-drop"
```

---

### Task 4: Category Management Page

**Files:**
- Create: `frontend/src/views/assets/settings/CategoryManagement.vue`

**Step 1: Create the Category Management component**

Create `frontend/src/views/assets/settings/CategoryManagement.vue`:

```vue
<template>
  <div class="category-management">
    <div class="page-header">
      <h3>资产分类管理</h3>
      <el-button type="primary" @click="handleCreate">新建分类</el-button>
    </div>

    <el-table
      :data="tableData"
      border
      row-key="id"
      default-expand-all
      :tree-props="{ children: 'children' }"
      v-loading="loading"
    >
      <el-table-column prop="name" label="分类名称" width="200" />
      <el-table-column prop="code" label="编码" width="120" />
      <el-table-column prop="path" label="完整路径" show-overflow-tooltip />
      <el-table-column label="层级" width="80" align="center">
        <template #default="{ row }">{{ row.level }}</template>
      </el-table-column>
      <el-table-column label="排序" width="80" align="center">
        <template #default="{ row }">{{ row.sortOrder }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.isActive ? 'success' : 'info'" size="small">
            {{ row.isActive ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="handleAddSub(row)">添加子分类</el-button>
          <el-popconfirm
            title="确定删除该分类吗？"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button link type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Category Form Dialog -->
    <CategoryForm
      v-model:visible="dialogVisible"
      :data="currentRow"
      :parent-data="parentRow"
      :category-tree="flatTreeData"
      @success="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { categoryApi } from '@/api/assets'
import CategoryForm from './components/CategoryForm.vue'

const loading = ref(false)
const tableData = ref<any[]>([])
const dialogVisible = ref(false)
const currentRow = ref<any>(null)
const parentRow = ref<any>(null)

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
    // TODO: Replace with actual API call
    // const res = await categoryApi.list({ tree: true })
    // tableData.value = res.data || res || []

    // Mock data
    tableData.value = [
      {
        id: '1',
        name: '电子设备',
        code: 'ELECTRONIC',
        path: '电子设备',
        level: 1,
        sortOrder: 1,
        isActive: true,
        children: [
          {
            id: '1-1',
            name: '计算机设备',
            code: 'COMPUTER',
            path: '电子设备/计算机设备',
            level: 2,
            sortOrder: 1,
            isActive: true,
            children: []
          },
          {
            id: '1-2',
            name: '办公设备',
            code: 'OFFICE_EQUIPMENT',
            path: '电子设备/办公设备',
            level: 2,
            sortOrder: 2,
            isActive: true,
            children: []
          }
        ]
      },
      {
        id: '2',
        name: '办公家具',
        code: 'FURNITURE',
        path: '办公家具',
        level: 1,
        sortOrder: 2,
        isActive: true,
        children: []
      }
    ]
  } catch (error) {
    console.error('Failed to load categories:', error)
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
    // TODO: Replace with actual API call
    // await categoryApi.delete(row.id)
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
.category-management {
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
```

**Step 2: Create Category Form component**

Create `frontend/src/views/assets/settings/components/CategoryForm.vue`:

```vue
<template>
  <el-dialog
    :model-value="visible"
    :title="dialogTitle"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="上级分类" prop="parentId">
        <el-tree-select
          v-model="formData.parentId"
          :data="categoryTree"
          :props="{ label: 'name', value: 'id' }"
          placeholder="请选择上级分类（不选则为顶级分类）"
          clearable
          check-strictly
          :disabled="!!parentData"
        />
      </el-form-item>

      <el-form-item label="分类名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入分类名称" />
      </el-form-item>

      <el-form-item label="分类编码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="请输入分类编码（英文大写）"
        />
      </el-form-item>

      <el-form-item label="排序号" prop="sortOrder">
        <el-input-number v-model="formData.sortOrder" :min="0" />
      </el-form-item>

      <el-form-item label="状态" prop="isActive">
        <el-switch v-model="formData.isActive" active-text="启用" inactive-text="停用" />
      </el-form-item>

      <el-form-item label="备注" prop="remark">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
          placeholder="请输入备注说明"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

interface Props {
  visible: boolean
  data?: any
  parentData?: any
  categoryTree?: any[]
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const dialogTitle = computed(() => {
  if (props.parentData) return `添加子分类: ${props.parentData.name}`
  if (props.data?.id) return '编辑分类'
  return '新建分类'
})

const formData = ref({
  parentId: null as string | null,
  name: '',
  code: '',
  sortOrder: 0,
  isActive: true,
  remark: ''
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入分类名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入分类编码', trigger: 'blur' },
    { pattern: /^[A-Z_]+$/, message: '编码必须是大写字母或下划线', trigger: 'blur' }
  ]
}

watch(() => props.visible, (val) => {
  if (val) {
    if (props.parentData) {
      formData.value.parentId = props.parentData.id
    } else if (props.data?.id) {
      Object.assign(formData.value, props.data)
    } else {
      resetForm()
    }
  }
})

const resetForm = () => {
  formData.value = {
    parentId: null,
    name: '',
    code: '',
    sortOrder: 0,
    isActive: true,
    remark: ''
  }
  formRef.value?.clearValidate()
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      // TODO: Replace with actual API call
      if (props.data?.id) {
        // await categoryApi.update(props.data.id, formData.value)
      } else {
        // await categoryApi.create(formData.value)
      }

      ElMessage.success(props.data?.id ? '更新成功' : '创建成功')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitting.value = false
    }
  })
}
</script>
```

**Step 3: Run dev server to verify**

```bash
cd frontend
npm run dev
```

**Step 4: Commit**

```bash
git add frontend/src/views/assets/settings/CategoryManagement.vue
git add frontend/src/views/assets/settings/components/CategoryForm.vue
git commit -m "feat(assets): add category management page"
```

---

## Phase 2: Additional Management Pages (P1)

### Task 5: Supplier Management

**Files:**
- Create: `frontend/src/views/assets/settings/SupplierList.vue`
- Create: `frontend/src/views/assets/settings/SupplierForm.vue`
- Create: `frontend/src/api/suppliers.ts`

**Step 1: Create the Supplier API client**

Create `frontend/src/api/suppliers.ts`:

```typescript
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

export interface Supplier {
  id: string
  name: string
  code: string
  contact?: string
  phone?: string
  email?: string
  address?: string
  creditLevel?: string
  isActive: boolean
}

export const supplierApi = {
  list(params?: any): Promise<PaginatedResponse<Supplier>> {
    return request.get('/assets/suppliers/', { params })
  },

  detail(id: string): Promise<Supplier> {
    return request.get(`/assets/suppliers/${id}/`)
  },

  create(data: Partial<Supplier>): Promise<Supplier> {
    return request.post('/assets/suppliers/', data)
  },

  update(id: string, data: Partial<Supplier>): Promise<Supplier> {
    return request.put(`/assets/suppliers/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/assets/suppliers/${id}/`)
  }
}
```

**Step 2: Create Supplier List component**

Create `frontend/src/views/assets/settings/SupplierList.vue`:

```vue
<template>
  <BaseListPage
    title="供应商管理"
    :search-fields="searchFields"
    :table-columns="tableColumns"
    :api="supplierApi.list"
  >
    <template #toolbar>
      <el-button type="primary" @click="handleCreate">新建供应商</el-button>
    </template>
    <template #actions="{ row }">
      <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
      <el-popconfirm title="确定删除吗？" @confirm="handleDelete(row)">
        <template #reference>
          <el-button link type="danger">删除</el-button>
        </template>
      </el-popconfirm>
    </template>
  </BaseListPage>

  <SupplierForm
    v-model:visible="dialogVisible"
    :data="currentRow"
    @success="refreshList"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import type { TableColumn, SearchField } from '@/types/common'
import { supplierApi } from '@/api/suppliers'
import SupplierForm from './SupplierForm.vue'

const dialogVisible = ref(false)
const currentRow = ref<any>(null)

const searchFields: SearchField[] = [
  { prop: 'name', label: '供应商名称', type: 'text' },
  { prop: 'code', label: '供应商编码', type: 'text' },
  { prop: 'isActive', label: '状态', type: 'select', options: [
    { label: '启用', value: true },
    { label: '停用', value: false }
  ]}
]

const tableColumns: TableColumn[] = [
  { prop: 'code', label: '编码', width: 120 },
  { prop: 'name', label: '供应商名称', width: 200 },
  { prop: 'contact', label: '联系人', width: 120 },
  { prop: 'phone', label: '联系电话', width: 140 },
  { prop: 'email', label: '邮箱', width: 180 },
  { prop: 'address', label: '地址', showOverflowTooltip: true },
  { prop: 'creditLevel', label: '信用等级', width: 100 }
]

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
    await supplierApi.delete(row.id)
    ElMessage.success('删除成功')
    refreshList()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const refreshList = () => {
  // Trigger BaseListPage refresh
  window.location.reload()
}
</script>
```

**Step 3: Create Supplier Form component**

Create `frontend/src/views/assets/settings/SupplierForm.vue`:

```vue
<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑供应商' : '新建供应商'"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="供应商编码" prop="code">
        <el-input v-model="formData.code" :disabled="isEdit" />
      </el-form-item>
      <el-form-item label="供应商名称" prop="name">
        <el-input v-model="formData.name" />
      </el-form-item>
      <el-form-item label="联系人" prop="contact">
        <el-input v-model="formData.contact" />
      </el-form-item>
      <el-form-item label="联系电话" prop="phone">
        <el-input v-model="formData.phone" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="formData.email" />
      </el-form-item>
      <el-form-item label="地址" prop="address">
        <el-input v-model="formData.address" type="textarea" />
      </el-form-item>
      <el-form-item label="状态" prop="isActive">
        <el-switch v-model="formData.isActive" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { supplierApi } from '@/api/suppliers'

interface Props {
  visible: boolean
  data?: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  code: '',
  name: '',
  contact: '',
  phone: '',
  email: '',
  address: '',
  isActive: true
})

const rules: FormRules = {
  code: [{ required: true, message: '请输入供应商编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }]
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, props.data)
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (isEdit.value) {
        await supplierApi.update(props.data.id, formData.value)
      } else {
        await supplierApi.create(formData.value)
      }
      ElMessage.success('操作成功')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('操作失败')
    }
  })
}
</script>
```

**Step 4: Commit**

```bash
git add frontend/src/views/assets/settings/SupplierList.vue
git add frontend/src/views/assets/settings/SupplierForm.vue
git add frontend/src/api/suppliers.ts
git commit -m "feat(assets): add supplier management pages"
```

---

### Task 6: Location Management

Similar pattern to Supplier Management. Create:
- `frontend/src/api/locations.ts`
- `frontend/src/views/assets/settings/LocationList.vue`
- `frontend/src/views/assets/settings/LocationForm.vue`

Follow the same pattern as Task 5.

---

### Task 7: Permission Management UI

**Files:**
- Create: `frontend/src/views/admin/PermissionManagement.vue`

**Step 1: Create Permission Management component**

Create `frontend/src/views/admin/PermissionManagement.vue`:

```vue
<template>
  <div class="permission-management">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="字段权限" name="field">
        <FieldPermissionMatrix />
      </el-tab-pane>
      <el-tab-pane label="数据权限" name="data">
        <DataPermissionMatrix />
      </el-tab-pane>
      <el-tab-pane label="权限日志" name="log">
        <PermissionAuditLog />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import FieldPermissionMatrix from './components/FieldPermissionMatrix.vue'
import DataPermissionMatrix from './components/DataPermissionMatrix.vue'
import PermissionAuditLog from './components/PermissionAuditLog.vue'

const activeTab = ref('field')
</script>

<style scoped>
.permission-management {
  padding: 20px;
}
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/admin/PermissionManagement.vue
git commit -m "feat(admin): add permission management page shell"
```

---

## Summary

After completing all tasks in this plan, you will have:

1. **Business Object Management** - Create and manage custom business objects
2. **Field Definition Management** - Configure dynamic fields with 20+ field types
3. **Page Layout Designer** - Visual drag-drop layout builder
4. **Category Management** - Tree-structured asset categories
5. **Supplier Management** - Supplier CRUD operations
6. **Location Management** - Location CRUD with hierarchy
7. **Permission Management** - Field and data permission matrix

**Total Estimated Tasks:** 15+
**Total Files to Create:** ~20
**Total Commits:** ~7

---

## Testing Checklist

After each phase, verify:

- [ ] Pages load without TypeScript errors
- [ ] API calls work correctly (or show proper error messages)
- [ ] Forms validate input correctly
- [ ] Navigation between pages works
- [ ] Build passes: `npm run build`

---

**Plan complete and saved to `docs/plans/2025-01-25-system-management-implementation.md`.**

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
