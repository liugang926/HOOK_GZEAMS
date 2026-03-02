# Phase 2.5: 权限体系增强 - 前端实现

## 1. 页面结构

### 1.1 页面目录

```
src/views/system/permissions/
├── index.vue                    # 权限管理首页
├── field/
│   ├── Index.vue               # 字段权限列表
│   ├── Form.vue                # 字段权限表单
│   └── BatchForm.vue           # 批量配置表单
├── data/
│   ├── Index.vue               # 数据权限列表
│   ├── Form.vue                # 数据权限表单
│   └── ExpandForm.vue          # 权限扩展表单
├── inheritance/
│   ├── Index.vue               # 继承关系列表
│   ├── Tree.vue                # 继承关系树
│   └── Form.vue                # 继承关系表单
├── audit/
│   ├── Index.vue               # 审计日志列表
│   ├── Detail.vue              # 日志详情
│   └── Sensitive.vue           # 敏感操作日志
└── templates/
    ├── Index.vue               # 权限模板列表
    └── Preview.vue             # 模板预览
```

### 1.2 组件目录

```
src/components/permissions/
├── FieldPermissionSelector.vue  # 字段权限选择器
├── DataScopeSelector.vue        # 数据范围选择器
├── PermissionTree.vue           # 权限树组件
├── PermissionMatrix.vue         # 权限矩阵
├── MaskingRuleEditor.vue        # 脱敏规则编辑器
└── ConditionBuilder.vue         # 条件构建器
```

---

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
- ✓ 列的显示/隐藏
- ✓ 列的拖拽排序
- ✓ 列宽调整
- ✓ 列固定（左/右）
- ✓ 用户个性化配置保存

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
<!-- 列表页面 -->
<BaseListPage
    title="页面标题"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
>
    <!-- 自定义列插槽 -->
</BaseListPage>

<!-- 表单页面 -->
<BaseFormPage
    title="表单标题"
    :submit-method="handleSubmit"
    :initial-data="formData"
    :rules="rules"
>
    <!-- 自定义表单项 -->
</BaseFormPage>
```

---

## 2. 字段权限管理

### 2.1 字段权限列表页面

**文件**: `src/views/system/permissions/field/Index.vue`

```vue
<template>
  <div class="field-permission-page">
    <!-- 页面头部 -->
    <PageHeader title="字段权限管理">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增权限
      </el-button>
      <el-button @click="openBatchDialog">
        <el-icon><Grid /></el-icon>
        批量配置
      </el-button>
    </PageHeader>

    <!-- 筛选条件 -->
    <SearchPanel>
      <el-form :model="searchForm" inline>
        <el-form-item label="角色">
          <RoleSelect v-model="searchForm.role_id" clearable />
        </el-form-item>
        <el-form-item label="用户">
          <UserSelect v-model="searchForm.user_id" clearable />
        </el-form-item>
        <el-form-item label="对象类型">
          <ObjectTypeSelect v-model="searchForm.object_type" clearable />
        </el-form-item>
        <el-form-item label="权限类型">
          <el-select v-model="searchForm.permission_type" clearable>
            <el-option label="只读" value="read" />
            <el-option label="可写" value="write" />
            <el-option label="隐藏" value="hidden" />
            <el-option label="脱敏" value="masked" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </SearchPanel>

    <!-- 权限列表 -->
    <el-table
      v-loading="loading"
      :data="tableData"
      border
      stripe
    >
      <el-table-column prop="role.name" label="角色" width="150" />
      <el-table-column prop="user.username" label="用户" width="120" />
      <el-table-column prop="object_type_display" label="对象类型" width="150" />
      <el-table-column prop="field_label" label="字段" width="150" />
      <el-table-column label="权限类型" width="100">
        <template #default="{ row }">
          <PermissionTypeTag :type="row.permission_type" />
        </template>
      </el-table-column>
      <el-table-column label="脱敏规则" width="120">
        <template #default="{ row }">
          <span v-if="row.mask_rule">{{ row.mask_rule }}</span>
          <span v-else class="text-gray">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="priority" label="优先级" width="80" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link @click="openEditDialog(row)">编辑</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      @current-change="fetchData"
      @size-change="fetchData"
    />

    <!-- 权限表单对话框 -->
    <FieldPermissionForm
      v-model="formVisible"
      :permission-id="currentPermissionId"
      @success="fetchData"
    />

    <!-- 批量配置对话框 -->
    <BatchFieldPermissionForm
      v-model="batchVisible"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Grid } from '@element-plus/icons-vue'
import FieldPermissionForm from './Form.vue'
import BatchFieldPermissionForm from './BatchForm.vue'
import PermissionTypeTag from '@/components/permissions/PermissionTypeTag.vue'
import { fieldPermissionApi } from '@/api/permissions'

const loading = ref(false)
const tableData = ref([])
const formVisible = ref(false)
const batchVisible = ref(false)
const currentPermissionId = ref<number | null>(null)

const searchForm = reactive({
  role_id: null,
  user_id: null,
  object_type: '',
  permission_type: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await fieldPermissionApi.list({
      ...searchForm,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = data.results
    pagination.total = data.count
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  currentPermissionId.value = null
  formVisible.value = true
}

const openEditDialog = (row: any) => {
  currentPermissionId.value = row.id
  formVisible.value = true
}

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm('确认删除此权限配置？', '提示', {
    type: 'warning'
  })
  await fieldPermissionApi.delete(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    role_id: null,
    user_id: null,
    object_type: '',
    permission_type: ''
  })
  handleSearch()
}

onMounted(() => {
  fetchData()
})
</script>
```

### 2.2 字段权限表单组件

**文件**: `src/views/system/permissions/field/Form.vue`

```vue
<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑字段权限' : '新增字段权限'"
    width="600px"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
    >
      <!-- 绑定目标 -->
      <el-form-item label="绑定类型" prop="bind_type">
        <el-radio-group v-model="formData.bind_type">
          <el-radio value="role">角色</el-radio>
          <el-radio value="user">用户</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item
        v-if="formData.bind_type === 'role'"
        label="角色"
        prop="role_id"
      >
        <RoleSelect v-model="formData.role_id" />
      </el-form-item>

      <el-form-item
        v-if="formData.bind_type === 'user'"
        label="用户"
        prop="user_id"
      >
        <UserSelect v-model="formData.user_id" />
      </el-form-item>

      <!-- 对象和字段 -->
      <el-form-item label="对象类型" prop="object_type">
        <ObjectTypeSelect
          v-model="formData.object_type"
          @change="handleObjectTypeChange"
        />
      </el-form-item>

      <el-form-item label="字段" prop="field_name">
        <el-select
          v-model="formData.field_name"
          :loading="fieldsLoading"
          filterable
        >
          <el-option
            v-for="field in availableFields"
            :key="field.name"
            :label="field.label"
            :value="field.name"
          >
            <span>{{ field.label }}</span>
            <el-tag
              v-if="field.sensitive"
              size="small"
              type="warning"
              style="margin-left: 8px"
            >
              敏感
            </el-tag>
          </el-option>
        </el-select>
      </el-form-item>

      <!-- 权限类型 -->
      <el-form-item label="权限类型" prop="permission_type">
        <el-radio-group v-model="formData.permission_type">
          <el-radio value="read">只读</el-radio>
          <el-radio value="write">可写</el-radio>
          <el-radio value="hidden">隐藏</el-radio>
          <el-radio value="masked">脱敏</el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 脱敏规则（脱敏时显示） -->
      <template v-if="formData.permission_type === 'masked'">
        <el-form-item label="脱敏规则" prop="mask_rule">
          <el-select v-model="formData.mask_rule">
            <el-option label="保留前3后4位（手机号）" value="phone" />
            <el-option label="保留前3后4位（身份证）" value="id_card" />
            <el-option label="保留后4位（银行卡）" value="bank_card" />
            <el-option label="保留最后一个字（姓名）" value="name" />
            <el-option label="显示范围（金额）" value="range" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item
          v-if="formData.mask_rule === 'custom'"
          label="自定义规则"
          prop="mask_params"
        >
          <MaskingRuleEditor v-model="formData.mask_params" />
        </el-form-item>
      </template>

      <!-- 条件配置 -->
      <el-form-item label="生效条件">
        <ConditionBuilder v-model="formData.condition" />
      </el-form-item>

      <!-- 优先级 -->
      <el-form-item label="优先级" prop="priority">
        <el-input-number
          v-model="formData.priority"
          :min="0"
          :max="100"
        />
        <span class="form-tip">数字越大优先级越高</span>
      </el-form-item>

      <!-- 备注 -->
      <el-form-item label="备注">
        <el-input
          v-model="formData.remark"
          type="textarea"
          :rows="3"
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
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { fieldPermissionApi } from '@/api/permissions'

interface Props {
  modelValue: boolean
  permissionId?: number | null
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const fieldsLoading = ref(false)
const submitting = ref(false)
const availableFields = ref([])

const isEdit = computed(() => !!props.permissionId)

const formData = reactive({
  bind_type: 'role',
  role_id: null,
  user_id: null,
  object_type: '',
  field_name: '',
  permission_type: 'read',
  mask_rule: '',
  mask_params: null,
  condition: null,
  priority: 0,
  remark: ''
})

const formRules = {
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
  user_id: [{ required: true, message: '请选择用户', trigger: 'change' }],
  object_type: [{ required: true, message: '请选择对象类型', trigger: 'change' }],
  field_name: [{ required: true, message: '请选择字段', trigger: 'change' }],
  permission_type: [{ required: true, message: '请选择权限类型', trigger: 'change' }]
}

const handleObjectTypeChange = async (objectType: string) => {
  if (!objectType) {
    availableFields.value = []
    return
  }
  fieldsLoading.value = true
  try {
    const { data } = await fieldPermissionApi.getAvailableFields(objectType)
    availableFields.value = data.fields
  } finally {
    fieldsLoading.value = false
  }
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true

  try {
    if (isEdit.value) {
      await fieldPermissionApi.update(props.permissionId!, formData)
    } else {
      await fieldPermissionApi.create(formData)
    }
    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    emit('success')
    handleClose()
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (val) => {
  if (val && isEdit.value) {
    // 加载权限详情
  }
})
</script>
```

### 2.3 批量配置表单

**文件**: `src/views/system/permissions/field/BatchForm.vue`

```vue
<template>
  <el-dialog
    :model-value="modelValue"
    title="批量配置字段权限"
    width="800px"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-form
      ref="formRef"
      :model="formData"
      label-width="120px"
    >
      <!-- 基本信息 -->
      <el-form-item label="角色" prop="role_id">
        <RoleSelect v-model="formData.role_id" />
      </el-form-item>

      <el-form-item label="对象类型" prop="object_type">
        <ObjectTypeSelect
          v-model="formData.object_type"
          @change="loadFields"
        />
      </el-form-item>

      <!-- 字段权限矩阵 -->
      <el-form-item label="字段权限">
        <PermissionMatrix
          v-model="formData.permissions"
          :fields="availableFields"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        批量创建
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { fieldPermissionApi } from '@/api/permissions'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const submitting = ref(false)
const availableFields = ref([])

const formData = reactive({
  role_id: null,
  object_type: '',
  permissions: []
})

const loadFields = async (objectType: string) => {
  const { data } = await fieldPermissionApi.getAvailableFields(objectType)
  availableFields.value = data.fields
  // 初始化权限矩阵
  formData.permissions = data.fields.map((f: any) => ({
    field_name: f.name,
    permission_type: f.sensitive ? 'masked' : 'read'
  }))
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    await fieldPermissionApi.batchCreate(formData)
    ElMessage.success(`成功创建 ${formData.permissions.length} 条权限配置`)
    emit('success')
    emit('update:modelValue', false)
  } finally {
    submitting.value = false
  }
}
</script>
```

---

## 3. 数据权限管理

### 3.1 数据权限列表页面

**文件**: `src/views/system/permissions/data/Index.vue`

```vue
<template>
  <div class="data-permission-page">
    <PageHeader title="数据权限管理">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新增权限
      </el-button>
    </PageHeader>

    <!-- 筛选条件 -->
    <SearchPanel>
      <el-form :model="searchForm" inline>
        <el-form-item label="角色">
          <RoleSelect v-model="searchForm.role_id" clearable />
        </el-form-item>
        <el-form-item label="对象类型">
          <ObjectTypeSelect v-model="searchForm.object_type" clearable />
        </el-form-item>
        <el-form-item label="范围类型">
          <el-select v-model="searchForm.scope_type" clearable>
            <el-option label="全部数据" value="all" />
            <el-option label="本部门" value="self_dept" />
            <el-option label="本部门及下级" value="self_and_sub" />
            <el-option label="指定部门" value="specified" />
            <el-option label="自定义规则" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </SearchPanel>

    <!-- 权限列表 -->
    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="role.name" label="角色" width="150" />
      <el-table-column prop="object_type_display" label="对象类型" width="180" />
      <el-table-column label="数据范围" width="150">
        <template #default="{ row }">
          <DataScopeTag :scope="row.scope_type" />
        </template>
      </el-table-column>
      <el-table-column label="允许继承" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_inherited ? 'success' : 'info'" size="small">
            {{ row.is_inherited ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="权限扩展" width="100">
        <template #default="{ row }">
          <el-button
            v-if="row.expansions_count > 0"
            link
            type="primary"
            @click="showExpansions(row)"
          >
            {{ row.expansions_count }} 项
          </el-button>
          <span v-else class="text-gray">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button link @click="openEditDialog(row)">编辑</el-button>
          <el-button link @click="openExpandDialog(row)">扩展</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 数据权限表单 -->
    <DataPermissionForm
      v-model="formVisible"
      :permission-id="currentPermissionId"
      @success="fetchData"
    />

    <!-- 扩展配置对话框 -->
    <DataExpandForm
      v-model="expandVisible"
      :permission-id="currentPermissionId"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { dataPermissionApi } from '@/api/permissions'
import DataPermissionForm from './Form.vue'
import DataExpandForm from './ExpandForm.vue'
import DataScopeTag from '@/components/permissions/DataScopeTag.vue'

// 类似字段权限列表的实现
// ...
</script>
```

### 3.2 数据范围选择器组件

**文件**: `src/components/permissions/DataScopeSelector.vue`

```vue
<template>
  <div class="data-scope-selector">
    <el-radio-group v-model="localValue.scope_type" @change="handleScopeChange">
      <el-radio value="all">全部数据</el-radio>
      <el-radio value="self_dept">本部门</el-radio>
      <el-radio value="self_and_sub">本部门及下级</el-radio>
      <el-radio value="specified">指定部门</el-radio>
      <el-radio value="custom">自定义规则</el-radio>
    </el-radio-group>

    <!-- 指定部门 -->
    <div v-if="localValue.scope_type === 'specified'" class="scope-config">
      <el-tree-select
        v-model="localValue.scope_value.department_ids"
        :data="departmentTree"
        multiple
        show-checkbox
        check-strictly
        placeholder="选择部门"
      />
    </div>

    <!-- 自定义规则 -->
    <div v-if="localValue.scope_type === 'custom'" class="scope-config">
      <el-form label-width="100px">
        <el-form-item label="过滤字段">
          <el-select v-model="localValue.scope_value.filter_field">
            <el-option label="部门" value="department" />
            <el-option label="创建人" value="created_by" />
            <el-option label="状态" value="status" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件">
          <el-row :gutter="10">
            <el-col :span="8">
              <el-select v-model="localValue.scope_value.operator">
                <el-option label="等于" value="eq" />
                <el-option label="不等于" value="ne" />
                <el-option label="包含" value="in" />
                <el-option label="大于" value="gt" />
                <el-option label="小于" value="lt" />
              </el-select>
            </el-col>
            <el-col :span="16">
              <el-input v-model="localValue.scope_value.filter_value" />
            </el-col>
          </el-row>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useOrganizationStore } from '@/stores/organization'

interface Props {
  modelValue: {
    scope_type: string
    scope_value: any
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const organizationStore = useOrganizationStore()
const departmentTree = computed(() => organizationStore.departmentTree)

const localValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const handleScopeChange = (scopeType: string) => {
  // 初始化scope_value
  if (scopeType === 'specified') {
    localValue.value.scope_value = { department_ids: [] }
  } else if (scopeType === 'custom') {
    localValue.value.scope_value = {
      filter_field: 'department',
      operator: 'eq',
      filter_value: ''
    }
  } else {
    localValue.value.scope_value = {}
  }
}
</script>

<style scoped>
.scope-config {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}
</style>
```

---

## 4. 权限继承管理

### 4.1 继承关系树组件

**文件**: `src/views/system/permissions/inheritance/Tree.vue`

```vue
<template>
  <div class="inheritance-tree-page">
    <PageHeader title="权限继承关系">
      <el-button @click="refreshTree">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        添加继承
      </el-button>
    </PageHeader>

    <div class="tree-container">
      <el-tree
        v-loading="loading"
        :data="treeData"
        :props="treeProps"
        node-key="id"
        default-expand-all
        :expand-on-click-node="false"
      >
        <template #default="{ node, data }">
          <div class="tree-node">
            <div class="node-info">
              <RoleAvatar :role="data.role" :size="32" />
              <span class="role-name">{{ data.role.name }}</span>
              <el-tag v-if="data.inherit_type" size="small" type="info">
                {{ getInheritTypeLabel(data.inherit_type) }}
              </el-tag>
            </div>
            <div class="node-actions">
              <el-button
                link
                size="small"
                @click="viewPermissions(data.role)"
              >
                查看权限
              </el-button>
              <el-dropdown @command="handleCommand($event, data)">
                <el-button link size="small">
                  更多<el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑继承</el-dropdown-item>
                    <el-dropdown-item command="summary">权限汇总</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除继承</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

    <!-- 继承关系表单 -->
    <InheritanceForm
      v-model="formVisible"
      @success="refreshTree"
    />

    <!-- 权限汇总对话框 -->
    <RolePermissionSummary
      v-model="summaryVisible"
      :role-id="currentRoleId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus, Refresh, ArrowDown } from '@element-plus/icons-vue'
import { inheritanceApi } from '@/api/permissions'
import InheritanceForm from './Form.vue'
import RolePermissionSummary from './RolePermissionSummary.vue'

const loading = ref(false)
const treeData = ref([])
const formVisible = ref(false)
const summaryVisible = ref(false)
const currentRoleId = ref<number | null>(null)

const treeProps = {
  children: 'children',
  label: 'role.name'
}

const getInheritTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    full: '完全继承',
    partial: '部分继承',
    override: '覆盖继承'
  }
  return labels[type] || type
}

const refreshTree = async () => {
  loading.value = true
  try {
    const { data } = await inheritanceApi.getTree()
    treeData.value = data.tree
  } finally {
    loading.value = false
  }
}

const viewPermissions = (role: any) => {
  currentRoleId.value = role.id
  summaryVisible.value = true
}

const handleCommand = (command: string, data: any) => {
  switch (command) {
    case 'edit':
      // 打开编辑对话框
      break
    case 'summary':
      currentRoleId.value = data.role.id
      summaryVisible.value = true
      break
    case 'delete':
      // 删除继承关系
      break
  }
}

onMounted(() => {
  refreshTree()
})
</script>

<style scoped>
.tree-container {
  padding: 20px;
  background: white;
  border-radius: 4px;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 400px;
  padding-right: 20px;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.role-name {
  font-weight: 500;
}
</style>
```

---

## 5. 权限审计

### 5.1 审计日志列表

**文件**: `src/views/system/permissions/audit/Index.vue`

```vue
<template>
  <div class="audit-log-page">
    <PageHeader title="权限审计日志">
      <el-button @click="exportLogs">
        <el-icon><Download /></el-icon>
        导出日志
      </el-button>
    </PageHeader>

    <!-- 筛选条件 -->
    <SearchPanel>
      <el-form :model="searchForm" inline>
        <el-form-item label="操作人">
          <UserSelect v-model="searchForm.actor_id" clearable />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="searchForm.action" clearable>
            <el-option label="创建" value="create" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="授权" value="grant" />
            <el-option label="撤销" value="revoke" />
            <el-option label="访问" value="access" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            @change="handleDateChange"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </el-form-item>
      </el-form>
    </SearchPanel>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <el-row :gutter="16">
        <el-col :span="6">
          <StatCard
            title="今日操作"
            :value="stats.today_count"
            icon="Operation"
          />
        </el-col>
        <el-col :span="6">
          <StatCard
            title="敏感操作"
            :value="stats.sensitive_count"
            icon="Warning"
            color="warning"
          />
        </el-col>
        <el-col :span="6">
          <StatCard
            title="失败操作"
            :value="stats.failed_count"
            icon="CircleClose"
            color="danger"
          />
        </el-col>
        <el-col :span="6">
          <StatCard
            title="活跃用户"
            :value="stats.active_users"
            icon="User"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 日志列表 -->
    <el-table v-loading="loading" :data="tableData" border stripe>
      <el-table-column prop="created_at" label="时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作人" width="150">
        <template #default="{ row }">
          {{ row.actor?.full_name || row.actor?.username }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <ActionTag :action="row.action" />
        </template>
      </el-table-column>
      <el-table-column prop="target_name" label="目标" min-width="200" />
      <el-table-column prop="ip_address" label="IP地址" width="140" />
      <el-table-column label="结果" width="80">
        <template #default="{ row }">
          <el-tag :type="row.success ? 'success' : 'danger'" size="small">
            {{ row.success ? '成功' : '失败' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button link @click="showDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
    />

    <!-- 详情对话框 -->
    <AuditDetail
      v-model="detailVisible"
      :log-id="currentLogId"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { auditApi } from '@/api/permissions'
import AuditDetail from './Detail.vue'

const loading = ref(false)
const tableData = ref([])
const detailVisible = ref(false)
const currentLogId = ref<number | null>(null)
const dateRange = ref()

const searchForm = reactive({
  actor_id: null,
  action: '',
  date_from: '',
  date_to: ''
})

const stats = ref({
  today_count: 0,
  sensitive_count: 0,
  failed_count: 0,
  active_users: 0
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await auditApi.list({
      ...searchForm,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    tableData.value = data.results
    pagination.total = data.count
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  const { data } = await auditApi.getStats()
  stats.value = data
}

const handleDateChange = (dates: any) => {
  if (dates) {
    searchForm.date_from = dates[0]
    searchForm.date_to = dates[1]
  } else {
    searchForm.date_from = ''
    searchForm.date_to = ''
  }
}

const showDetail = (row: any) => {
  currentLogId.value = row.id
  detailVisible.value = true
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

onMounted(() => {
  fetchData()
  fetchStats()
})
</script>
```

---

## 6. 公共组件

### 6.1 权限类型标签

**文件**: `src/components/permissions/PermissionTypeTag.vue`

```vue
<template>
  <el-tag :type="tagType" size="small">
    {{ label }}
  </el-tag>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  type: string
}

const props = defineProps<Props>()

const config: Record<string, { label: string; type: any }> = {
  read: { label: '只读', type: 'info' },
  write: { label: '可写', type: 'success' },
  hidden: { label: '隐藏', type: 'danger' },
  masked: { label: '脱敏', type: 'warning' }
}

const label = computed(() => config[props.type]?.label || props.type)
const tagType = computed(() => config[props.type]?.type || 'info')
</script>
```

### 6.2 权限矩阵组件

**文件**: `src/components/permissions/PermissionMatrix.vue`

```vue
<template>
  <div class="permission-matrix">
    <el-table :data="localValue" border size="small">
      <el-table-column prop="field_label" label="字段" width="180" />
      <el-table-column label="权限类型" width="200">
        <template #default="{ row }">
          <el-select v-model="row.permission_type" size="small">
            <el-option label="默认" value="" />
            <el-option label="只读" value="read" />
            <el-option label="可写" value="write" />
            <el-option label="隐藏" value="hidden" />
            <el-option label="脱敏" value="masked" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="脱敏规则" width="180">
        <template #default="{ row }">
          <el-select
            v-model="row.mask_rule"
            size="small"
            :disabled="row.permission_type !== 'masked'"
          >
            <el-option label="手机号" value="phone" />
            <el-option label="身份证" value="id_card" />
            <el-option label="银行卡" value="bank_card" />
            <el-option label="姓名" value="name" />
            <el-option label="金额" value="range" />
          </el-select>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: Array<{
    field_name: string
    field_label: string
    permission_type: string
    mask_rule?: string
  }>
  fields: Array<{
    name: string
    label: string
    sensitive: boolean
  }>
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const localValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
</script>
```

### 6.3 条件构建器

**文件**: `src/components/permissions/ConditionBuilder.vue`

```vue
<template>
  <div class="condition-builder">
    <div v-for="(condition, index) in conditions" :key="index" class="condition-row">
      <el-row :gutter="10">
        <el-col :span="6">
          <el-select v-model="condition.type" placeholder="条件类型" size="small">
            <el-option label="等于" value="eq" />
            <el-option label="包含" value="in" />
            <el-option label="操作" value="action" />
          </el-select>
        </el-col>
        <el-col :span="8">
          <el-input v-model="condition.field" placeholder="字段名" size="small" />
        </el-col>
        <el-col :span="8">
          <el-input v-model="condition.value" placeholder="值" size="small" />
        </el-col>
        <el-col :span="2">
          <el-button
            link
            type="danger"
            icon="Delete"
            @click="removeCondition(index)"
          />
        </el-col>
      </el-row>
    </div>
    <el-button
      link
      type="primary"
      icon="Plus"
      @click="addCondition"
    >
      添加条件
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  modelValue: any[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue'])

const conditions = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val)
})

const addCondition = () => {
  conditions.value = [
    ...conditions.value,
    { type: 'eq', field: '', value: '' }
  ]
}

const removeCondition = (index: number) => {
  conditions.value = conditions.value.filter((_, i) => i !== index)
}
</script>

<style scoped>
.condition-row {
  margin-bottom: 8px;
}
</style>
```

---

## 7. API 请求模块

**文件**: `src/api/permissions.ts`

```typescript
import request from '@/utils/request'

// 字段权限 API
export const fieldPermissionApi = {
  list: (params: any) => request.get('/api/permissions/field/', { params }),
  create: (data: any) => request.post('/api/permissions/field/', data),
  update: (id: number, data: any) => request.put(`/api/permissions/field/${id}/`, data),
  delete: (id: number) => request.delete(`/api/permissions/field/${id}/`),
  batchCreate: (data: any) => request.post('/api/permissions/field/batch/', data),
  getAvailableFields: (objectType: string) =>
    request.get('/api/permissions/field/available-fields/', {
      params: { object_type: objectType }
    })
}

// 数据权限 API
export const dataPermissionApi = {
  list: (params: any) => request.get('/api/permissions/data/', { params }),
  create: (data: any) => request.post('/api/permissions/data/', data),
  update: (id: number, data: any) => request.put(`/api/permissions/data/${id}/`, data),
  delete: (id: number) => request.delete(`/api/permissions/data/${id}/`),
  addExpansion: (id: number, data: any) =>
    request.post(`/api/permissions/data/${id}/expansions/`, data),
  deleteExpansion: (expansionId: number) =>
    request.delete(`/api/permissions/data/expansions/${expansionId}/`)
}

// 权限继承 API
export const inheritanceApi = {
  list: (params: any) => request.get('/api/permissions/inheritance/', { params }),
  create: (data: any) => request.post('/api/permissions/inheritance/', data),
  update: (id: number, data: any) => request.put(`/api/permissions/inheritance/${id}/`, data),
  delete: (id: number) => request.delete(`/api/permissions/inheritance/${id}/`),
  getTree: () => request.get('/api/permissions/inheritance/tree/'),
  getRoleSummary: (roleId: number) =>
    request.get(`/api/permissions/inheritance/role-summary/${roleId}/`)
}

// 审计日志 API
export const auditApi = {
  list: (params: any) => request.get('/api/permissions/audit/', { params }),
  getStats: () => request.get('/api/permissions/audit/stats/'),
  getSensitive: (params: any) =>
    request.get('/api/permissions/audit/sensitive/', { params }),
  getHistory: (targetType: string, targetId: number) =>
    request.get(`/api/permissions/audit/history/${targetType}/${targetId}/`),
  getAnomalies: (params: any) =>
    request.get('/api/permissions/audit/anomalies/', { params })
}

// 权限检查 API
export const permissionCheckApi = {
  check: (data: any) => request.post('/api/permissions/check/', data),
  batchCheck: (checks: any[]) => request.post('/api/permissions/check/batch/', { checks }),
  getAccessibleDepartments: (params: any) =>
    request.get('/api/permissions/accessible-departments/', { params })
}
```

---

## 8. 权限 Store

**文件**: `src/stores/permission.ts`

```typescript
import { defineStore } from 'pinia'
import { permissionCheckApi } from '@/api/permissions'
import { ref } from 'vue'

interface FieldPermissions {
  [field: string]: 'read' | 'write' | 'hidden' | 'masked'
}

interface DataScope {
  scope_type: string
  scope_value: any
}

export const usePermissionStore = defineStore('permission', () => {
  const fieldPermissions = ref<Record<string, FieldPermissions>>({})
  const dataScopes = ref<Record<string, DataScope>>({})

  // 获取字段权限
  const getFieldPermissions = async (objectType: string, action = 'view') => {
    const key = `${objectType}:${action}`
    if (fieldPermissions.value[key]) {
      return fieldPermissions.value[key]
    }

    const { data } = await permissionCheckApi.check({
      object_type: objectType,
      action
    })
    fieldPermissions.value[key] = data.field_permissions
    return data.field_permissions
  }

  // 获取数据范围
  const getDataScope = async (objectType: string) => {
    if (dataScopes.value[objectType]) {
      return dataScopes.value[objectType]
    }

    const { data } = await permissionCheckApi.check({
      object_type: objectType,
      action: 'view'
    })
    dataScopes.value[objectType] = data.data_scope
    return data.data_scope
  }

  // 检查字段是否隐藏
  const isFieldHidden = (objectType: string, field: string) => {
    const perms = fieldPermissions.value[`${objectType}:view`]
    return perms?.[field] === 'hidden'
  }

  // 检查字段是否只读
  const isFieldReadOnly = (objectType: string, field: string) => {
    const perms = fieldPermissions.value[`${objectType}:update`]
    return perms?.[field] === 'read'
  }

  // 获取脱敏值
  const getMaskedValue = (value: any, maskRule: string) => {
    if (!value) return value

    switch (maskRule) {
      case 'phone':
        return value.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
      case 'id_card':
        return value.replace(/(\d{3})\d{10}(\d{4})/, '$1**********$2')
      case 'bank_card':
        return value.replace(/\d(?=\d{4})/g, '*')
      case 'name':
        return value.replace(/./, '*')
      case 'range':
        return '***'
      default:
        return '***'
    }
  }

  // 清除缓存
  const clearCache = (objectType?: string) => {
    if (objectType) {
      Object.keys(fieldPermissions.value)
        .filter(k => k.startsWith(objectType))
        .forEach(k => delete fieldPermissions.value[k])
      delete dataScopes.value[objectType]
    } else {
      fieldPermissions.value = {}
      dataScopes.value = {}
    }
  }

  return {
    fieldPermissions,
    dataScopes,
    getFieldPermissions,
    getDataScope,
    isFieldHidden,
    isFieldReadOnly,
    getMaskedValue,
    clearCache
  }
})
```

---

## 9. 动态表单权限指令

**文件**: `src/directives/permission.ts`

```typescript
import { usePermissionStore } from '@/stores/permission'

// v-field-permission 指令
export const fieldPermissionDirective = {
  mounted(el: HTMLElement, binding: any) {
    const { objectType, field, action } = binding.value || {}
    if (!objectType || !field) return

    const permissionStore = usePermissionStore()
    const permissions = permissionStore.fieldPermissions[`${objectType}:${action || 'view'}`]

    if (permissions?.[field] === 'hidden') {
      el.style.display = 'none'
    } else if (permissions?.[field] === 'read') {
      const input = el.querySelector('input, textarea')
      if (input) {
        input.setAttribute('readonly', 'readonly')
        input.classList.add('is-disabled')
      }
    }
  }
}

// 注册指令
export default {
  install(app: any) {
    app.directive('field-permission', fieldPermissionDirective)
  }
}
```

---

## 10. 移动端适配

移动端权限管理采用简化视图，主要功能：

1. **权限查看**: 用户可查看自己的权限配置
2. **敏感数据提示**: 脱敏字段显示特殊标识
3. **权限申请**: 通过移动端申请权限提升

**文件**: `src/mobile/views/permissions/Index.vue`

```vue
<template>
  <div class="mobile-permission-page">
    <van-nav-bar title="我的权限" />

    <van-cell-group title="数据权限">
      <van-cell title="可见范围" :value="dataScopeLabel" />
      <van-cell title="可访问部门" :value="accessibleDeptsLabel" />
    </van-cell-group>

    <van-cell-group title="字段权限">
      <van-collapse v-model="activeNames">
        <van-collapse-item
          v-for="(fields, obj) in fieldPermissions"
          :key="obj"
          :title="getObjectTypeLabel(obj)"
          :name="obj"
        >
          <van-cell
            v-for="(perm, field) in fields"
            :key="field"
            :title="field"
          >
            <template #right-icon>
              <van-tag :type="getPermTagType(perm)">
                {{ getPermLabel(perm) }}
              </van-tag>
            </template>
          </van-cell>
        </van-collapse-item>
      </van-collapse>
    </van-cell-group>

    <van-button type="primary" block @click="openApplyDialog">
      申请权限提升
    </van-button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { permissionCheckApi } from '@/api/permissions'

const activeNames = ref([])
const fieldPermissions = ref({})
const dataScope = ref({})

onMounted(async () => {
  const { data } = await permissionCheckApi.check({
    object_type: 'assets.Asset',
    action: 'view'
  })
  fieldPermissions.value = data.field_permissions
  dataScope.value = data.data_scope
})

const getPermLabel = (perm: string) => {
  const labels: Record<string, string> = {
    read: '只读',
    write: '可写',
    hidden: '隐藏',
    masked: '脱敏'
  }
  return labels[perm] || perm
}

const getPermTagType = (perm: string) => {
  const types: Record<string, string> = {
    read: 'primary',
    write: 'success',
    hidden: 'danger',
    masked: 'warning'
  }
  return types[perm] || 'default'
}
</script>
```
