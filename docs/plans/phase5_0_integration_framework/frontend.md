# Phase 5.0: 通用ERP集成框架 - 前端实现

## 概述

实现集成管理前端页面，支持配置多种ERP系统、查看同步状态、管理数据映射等。

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

## 1. 集成配置列表页

### IntegrationList.vue

```vue
<template>
  <div class="integration-list">
    <el-card>
      <!-- 标题栏 -->
      <template #header>
        <div class="card-header">
          <span>集成配置</span>
          <el-button type="primary" @click="handleAdd">新增集成</el-button>
        </div>
      </template>

      <!-- 系统类型切换 -->
      <el-tabs v-model="activeSystem" @tab-change="handleTabChange">
        <el-tab-pane
          v-for="system in supportedSystems"
          :key="system.value"
          :label="system.label"
          :name="system.value"
        >
          <!-- 集成卡片列表 -->
          <el-row :gutter="16">
            <el-col :span="8" v-for="config in filteredConfigs" :key="config.id">
              <el-card class="integration-card" shadow="hover">
                <template #header>
                  <div class="card-header">
                    <span>{{ config.system_name }}</span>
                    <el-switch
                      v-model="config.is_enabled"
                      @change="handleToggleEnable(config)"
                    />
                  </div>
                </template>

                <!-- 系统信息 -->
                <div class="system-info">
                  <div class="system-type">
                    <el-tag :type="getSystemTagType(config.system_type)">
                      {{ getSystemTypeName(config.system_type) }}
                    </el-tag>
                  </div>
                  <div class="system-modules">
                    <span>启用模块：</span>
                    <el-tag
                      v-for="module in config.enabled_modules"
                      :key="module"
                      size="small"
                    >
                      {{ getModuleName(module) }}
                    </el-tag>
                  </div>
                </div>

                <!-- 健康状态 -->
                <div class="health-status">
                  <el-progress
                    :percentage="config.health_status === 'healthy' ? 100 : 0"
                    :color="getHealthColor(config.health_status)"
                    :show-text="false"
                  />
                  <span class="status-text">
                    {{ getHealthStatusName(config.health_status) }}
                  </span>
                </div>

                <!-- 同步信息 -->
                <div class="sync-info">
                  <div>最后同步: {{ formatTime(config.last_sync_at) }}</div>
                  <el-tag :type="getSyncStatusTagType(config.last_sync_status)">
                    {{ getSyncStatusName(config.last_sync_status) }}
                  </el-tag>
                </div>

                <!-- 操作按钮 -->
                <div class="card-actions">
                  <el-button link type="primary" @click="handleEdit(config)">
                    配置
                  </el-button>
                  <el-button link type="primary" @click="handleTest(config)">
                    测试连接
                  </el-button>
                  <el-button link type="primary" @click="handleSync(config)">
                    手动同步
                  </el-button>
                  <el-dropdown @command="(cmd) => handleMore(cmd, config)">
                    <el-button link type="primary">
                      更多<el-icon><arrow-down /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="mapping">数据映射</el-dropdown-item>
                        <el-dropdown-item command="logs">同步日志</el-dropdown-item>
                        <el-dropdown-item command="health">健康检查</el-dropdown-item>
                        <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </el-card>
            </el-col>
          </el-row>

          <!-- 空状态 -->
          <el-empty
            v-if="filteredConfigs.length === 0"
            description="暂无集成配置"
          >
            <el-button type="primary" @click="handleAdd">
              新增{{ getSystemTypeName(activeSystem) }}集成
            </el-button>
          </el-empty>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 配置弹窗 -->
    <IntegrationConfigDialog
      v-model="configDialogVisible"
      :config="editingConfig"
      @success="fetchData"
    />

    <!-- 测试连接结果弹窗 -->
    <TestResultDialog
      v-model="testResultVisible"
      :result="testResult"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import { integrationApi } from '@/api/integration'

const activeSystem = ref('m18')
const configs = ref([])
const configDialogVisible = ref(false)
const editingConfig = ref(null)
const testResultVisible = ref(false)
const testResult = ref(null)

const supportedSystems = [
  { value: 'm18', label: '万达宝M18' },
  { value: 'sap', label: 'SAP' },
  { value: 'kingdee', label: '金蝶' },
  { value: 'yonyou', label: '用友' },
  { value: 'odoo', label: 'Odoo' }
]

const moduleMap = {
  procurement: '采购管理',
  finance: '财务核算',
  inventory: '库存管理',
  hr: '人力资源',
  crm: '客户关系'
}

const filteredConfigs = computed(() => {
  return configs.value.filter(c => c.system_type === activeSystem.value)
})

const fetchData = async () => {
  const { data } = await integrationApi.listConfigs()
  configs.value = data
}

const handleTabChange = () => {
  // 切换系统类型
}

const handleAdd = () => {
  editingConfig.value = {
    system_type: activeSystem.value,
    connection_config: {},
    enabled_modules: [],
    sync_config: {}
  }
  configDialogVisible.value = true
}

const handleEdit = (config) => {
  editingConfig.value = { ...config }
  configDialogVisible.value = true
}

const handleToggleEnable = async (config) => {
  try {
    await integrationApi.updateConfig(config.id, {
      is_enabled: config.is_enabled
    })
    ElMessage.success(config.is_enabled ? '已启用' : '已禁用')
  } catch (error) {
    config.is_enabled = !config.is_enabled
    ElMessage.error('操作失败')
  }
}

const handleTest = async (config) => {
  try {
    const { data } = await integrationApi.testConnection(config.id)
    testResult.value = data
    testResultVisible.value = true
  } catch (error) {
    ElMessage.error('测试连接失败')
  }
}

const handleSync = async (config) => {
  try {
    await ElMessageBox.confirm('确认执行手动同步？', '提示')
    await integrationApi.triggerSync(config.id)
    ElMessage.success('同步任务已提交')
  } catch (error) {
    // cancel
  }
}

const handleMore = async (command, config) => {
  switch (command) {
    case 'mapping':
      // 跳转到数据映射页面
      break
    case 'logs':
      // 跳转到同步日志页面
      break
    case 'health':
      await handleTest(config)
      break
    case 'delete':
      await handleDelete(config)
      break
  }
}

const handleDelete = async (config) => {
  try {
    await ElMessageBox.confirm('确认删除此集成配置？', '警告', {
      type: 'warning'
    })
    await integrationApi.deleteConfig(config.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    // cancel
  }
}

const getSystemTypeName = (type) => {
  return supportedSystems.find(s => s.value === type)?.label || type
}

const getSystemTagType = (type) => {
  const typeMap = {
    m18: 'success',
    sap: 'danger',
    kingdee: 'warning',
    yonyou: 'primary',
    odoo: ''
  }
  return typeMap[type] || ''
}

const getModuleName = (key) => {
  return moduleMap[key] || key
}

const getHealthColor = (status) => {
  const colorMap = {
    healthy: '#67c23a',
    degraded: '#e6a23c',
    unhealthy: '#f56c6c'
  }
  return colorMap[status] || '#909399'
}

const getHealthStatusName = (status) => {
  const nameMap = {
    healthy: '健康',
    degraded: '降级',
    unhealthy: '不可用'
  }
  return nameMap[status] || '未知'
}

const getSyncStatusName = (status) => {
  const nameMap = {
    pending: '待执行',
    running: '执行中',
    success: '成功',
    partial_success: '部分成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return nameMap[status] || status
}

const getSyncStatusTagType = (status) => {
  const typeMap = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    partial_success: 'warning',
    failed: 'danger',
    cancelled: 'info'
  }
  return typeMap[status] || ''
}

const formatTime = (time) => {
  return time ? new Date(time).toLocaleString('zh-CN') : '未同步'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.integration-card {
  margin-bottom: 16px;
}

.integration-card :deep(.el-card__header) {
  padding: 12px 16px;
}

.integration-card :deep(.el-card__body) {
  padding: 16px;
}

.system-info {
  margin-bottom: 12px;
}

.system-modules {
  margin-top: 8px;
}

.system-modules .el-tag {
  margin-right: 4px;
}

.health-status {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.health-status .el-progress {
  flex: 1;
  margin-right: 12px;
}

.status-text {
  font-size: 14px;
}

.sync-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.card-actions {
  display: flex;
  gap: 8px;
}
</style>
```

---

## 2. 集成配置弹窗

### IntegrationConfigDialog.vue

```vue
<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑集成配置' : '新增集成配置'"
    width="700px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
    >
      <!-- 基础信息 -->
      <el-form-item label="系统类型" prop="system_type">
        <el-select
          v-model="formData.system_type"
          :disabled="isEdit"
          placeholder="选择系统类型"
        >
          <el-option
            v-for="system in supportedSystems"
            :key="system.value"
            :label="system.label"
            :value="system.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="系统名称" prop="system_name">
        <el-input
          v-model="formData.system_name"
          placeholder="如：生产环境M18"
        />
      </el-form-item>

      <!-- 连接配置 -->
      <el-divider content-position="left">连接配置</el-divider>

      <!-- 动态连接配置表单 -->
      <component
        :is="connectionConfigComponent"
        v-model="formData.connection_config"
      />

      <!-- 模块配置 -->
      <el-divider content-position="left">启用模块</el-divider>

      <el-form-item label="启用模块">
        <el-checkbox-group v-model="formData.enabled_modules">
          <el-checkbox label="procurement">采购管理</el-checkbox>
          <el-checkbox label="finance">财务核算</el-checkbox>
          <el-checkbox label="inventory">库存管理</el-checkbox>
          <el-checkbox label="hr">人力资源</el-checkbox>
          <el-checkbox label="crm">客户关系</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <!-- 同步配置 -->
      <el-divider content-position="left">同步配置</el-divider>

      <el-form-item label="自动同步">
        <el-switch v-model="formData.sync_config.auto_sync" />
      </el-form-item>

      <el-form-item
        label="同步间隔"
        v-if="formData.sync_config.auto_sync"
      >
        <el-input-number
          v-model="formData.sync_config.sync_interval"
          :min="1"
          :max="1440"
        />
        <span style="margin-left: 8px">分钟</span>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { integrationApi } from '@/api/integration'

// 各系统的连接配置组件
import M18ConnectionForm from './connection-forms/M18ConnectionForm.vue'
import SAPConnectionForm from './connection-forms/SAPConnectionForm.vue'
import KingdeeConnectionForm from './connection-forms/KingdeeConnectionForm.vue'

const props = defineProps({
  modelValue: Boolean,
  config: Object
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.config?.id)

const formRef = ref()
const submitting = ref(false)

const formData = reactive({
  system_type: '',
  system_name: '',
  connection_config: {},
  enabled_modules: [],
  sync_config: {
    auto_sync: false,
    sync_interval: 60
  }
})

const formRules = {
  system_type: [{ required: true, message: '请选择系统类型' }],
  system_name: [{ required: true, message: '请输入系统名称' }]
}

const supportedSystems = [
  { value: 'm18', label: '万达宝M18' },
  { value: 'sap', label: 'SAP' },
  { value: 'kingdee', label: '金蝶' },
  { value: 'yonyou', label: '用友' },
  { value: 'odoo', label: 'Odoo' }
]

// 根据系统类型动态加载连接配置组件
const connectionConfigComponent = computed(() => {
  const componentMap = {
    m18: M18ConnectionForm,
    sap: SAPConnectionForm,
    kingdee: KingdeeConnectionForm,
    yonyou: KingdeeConnectionForm,  // 复用金蝶的表单结构
    odoo: M18ConnectionForm  // 复用M18的表单结构
  }
  return componentMap[formData.system_type] || M18ConnectionForm
})

watch(() => props.config, (config) => {
  if (config) {
    Object.assign(formData, {
      system_type: config.system_type,
      system_name: config.system_name,
      connection_config: config.connection_config || {},
      enabled_modules: config.enabled_modules || [],
      sync_config: config.sync_config || { auto_sync: false, sync_interval: 60 }
    })
  }
}, { immediate: true })

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()

    submitting.value = true
    if (isEdit.value) {
      await integrationApi.updateConfig(props.config.id, formData)
    } else {
      await integrationApi.createConfig(formData)
    }

    ElMessage.success(isEdit.value ? '更新成功' : '创建成功')
    emit('success')
    handleClose()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    submitting.value = false
  }
}
</script>
```

---

## 3. M18连接配置组件

### M18ConnectionForm.vue

```vue
<template>
  <div class="m18-connection-form">
    <el-form-item label="API地址" required>
      <el-input
        :model-value="modelValue.api_url"
        @input="updateField('api_url', $event)"
        placeholder="http://m18.example.com/M18/api/"
      />
    </el-form-item>

    <el-form-item label="API密钥" required>
      <el-input
        :model-value="modelValue.api_key"
        @input="updateField('api_key', $event)"
        type="password"
        show-password
        placeholder="请输入API密钥"
      />
    </el-form-item>

    <el-form-item label="用户名" required>
      <el-input
        :model-value="modelValue.username"
        @input="updateField('username', $event)"
        placeholder="请输入用户名"
      />
    </el-form-item>

    <el-form-item label="密码" required>
      <el-input
        :model-value="modelValue.password"
        @input="updateField('password', $event)"
        type="password"
        show-password
        placeholder="请输入密码"
      />
    </el-form-item>

    <el-form-item label="超时时间">
      <el-input-number
        :model-value="modelValue.timeout || 30"
        @change="updateField('timeout', $event)"
        :min="5"
        :max="300"
      />
      <span style="margin-left: 8px">秒</span>
    </el-form-item>
  </div>
</template>

<script setup lang="ts">
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const updateField = (field, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}
</script>
```

---

## 4. 同步日志页面

### SyncLogs.vue

```vue
<template>
  <div class="sync-logs">
    <el-card>
      <!-- 筛选条件 -->
      <el-form :model="queryForm" :inline="true">
        <el-form-item label="集成系统">
          <el-select v-model="queryForm.system_type" placeholder="全部" clearable>
            <el-option
              v-for="system in supportedSystems"
              :key="system.value"
              :label="system.label"
              :value="system.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="全部" clearable>
            <el-option label="成功" value="success" />
            <el-option label="部分成功" value="partial_success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="queryForm.date_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchData">查询</el-button>
        </el-form-item>
      </el-form>

      <!-- 日志列表 -->
      <el-table :data="tableData" v-loading="loading" border>
        <el-table-column prop="task_id" label="任务ID" width="200" />
        <el-table-column prop="system_type" label="系统" width="120">
          <template #default="{ row }">
            {{ getSystemTypeName(row.system_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="module_type" label="模块" width="100">
          <template #default="{ row }">
            {{ getModuleName(row.module_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="direction" label="方向" width="100">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'push' ? 'success' : 'warning'" size="small">
              {{ row.direction === 'push' ? '推送' : '拉取' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行结果" width="200">
          <template #default="{ row }">
            成功: {{ row.success_count }} / 失败: {{ row.failed_count }}
          </template>
        </el-table-column>
        <el-table-column prop="duration_ms" label="耗时" width="100">
          <template #default="{ row }">
            {{ row.duration_ms ? `${row.duration_ms}ms` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button
              link
              type="primary"
              @click="handleViewErrors(row)"
              v-if="row.failed_count > 0"
            >
              错误
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        @current-change="fetchData"
      />
    </el-card>

    <!-- 详情弹窗 -->
    <TaskDetailDialog
      v-model="detailVisible"
      :task="currentTask"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { integrationApi } from '@/api/integration'
import TaskDetailDialog from './TaskDetailDialog.vue'

const queryForm = reactive({
  system_type: '',
  status: '',
  date_range: []
})

const tableData = ref([])
const loading = ref(false)
const detailVisible = ref(false)
const currentTask = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const supportedSystems = [
  { value: 'm18', label: '万达宝M18' },
  { value: 'sap', label: 'SAP' },
  { value: 'kingdee', label: '金蝶' }
]

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await integrationApi.listSyncTasks({
      ...queryForm,
      page: pagination.page,
      size: pagination.size
    })
    tableData.value = data.results
    pagination.total = data.count
  } finally {
    loading.value = false
  }
}

const handleViewDetail = (row) => {
  currentTask.value = row
  detailVisible.value = true
}

const handleViewErrors = (row) => {
  // 显示错误详情
}

const getSystemTypeName = (type) => {
  return supportedSystems.find(s => s.value === type)?.label || type
}

const getModuleName = (key) => {
  const map = {
    procurement: '采购',
    finance: '财务',
    inventory: '库存'
  }
  return map[key] || key
}

const getStatusName = (status) => {
  const map = {
    pending: '待执行',
    running: '执行中',
    success: '成功',
    partial_success: '部分成功',
    failed: '失败'
  }
  return map[status] || status
}

const getStatusTagType = (status) => {
  const map = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    partial_success: 'warning',
    failed: 'danger'
  }
  return map[status] || ''

onMounted(() => {
  fetchData()
})
</script>
```

---

## 5. 数据映射管理

### DataMappingList.vue

```vue
<template>
  <div class="data-mapping">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据映射配置</span>
          <el-button type="primary" @click="handleAdd">新增映射</el-button>
        </div>
      </template>

      <!-- 筛选 -->
      <el-form :model="queryForm" :inline="true">
        <el-form-item label="系统类型">
          <el-select v-model="queryForm.system_type">
            <el-option
              v-for="system in supportedSystems"
              :key="system.value"
              :label="system.label"
              :value="system.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="业务类型">
          <el-select v-model="queryForm.business_type">
            <el-option label="采购订单" value="purchase_order" />
            <el-option label="资产" value="asset" />
            <el-option label="财务凭证" value="voucher" />
          </el-select>
        </el-form-item>
      </el-form>

      <!-- 映射列表 -->
      <el-table :data="tableData" border>
        <el-table-column prop="template_name" label="模板名称" />
        <el-table-column prop="system_type" label="系统类型">
          <template #default="{ row }">
            {{ getSystemTypeName(row.system_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="business_type" label="业务类型" />
        <el-table-column label="映射字段数">
          <template #default="{ row }">
            {{ Object.keys(row.field_mappings || {}).length }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态">
          <template #default="{ row }">
            <el-switch v-model="row.is_active" @change="handleToggle(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 映射编辑器 -->
    <MappingEditorDialog
      v-model="editorVisible"
      :mapping="editingMapping"
      @success="fetchData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { integrationApi } from '@/api/integration'
import MappingEditorDialog from './MappingEditorDialog.vue'

const queryForm = reactive({
  system_type: '',
  business_type: ''
})

const tableData = ref([])
const editorVisible = ref(false)
const editingMapping = ref(null)

const supportedSystems = [
  { value: 'm18', label: '万达宝M18' },
  { value: 'sap', label: 'SAP' },
  { value: 'kingdee', label: '金蝶' }
]

const fetchData = async () => {
  const { data } = await integrationApi.listMappings(queryForm)
  tableData.value = data
}

const handleAdd = () => {
  editingMapping.value = {
    system_type: queryForm.system_type,
    business_type: queryForm.business_type,
    field_mappings: {},
    value_mappings: {},
    is_active: true
  }
  editorVisible.value = true
}

const handleEdit = (row) => {
  editingMapping.value = { ...row }
  editorVisible.value = true
}

const handleToggle = async (row) => {
  await integrationApi.updateMapping(row.id, { is_active: row.is_active })
  ElMessage.success('状态已更新')
}

const handleDelete = async (row) => {
  await ElMessageBox.confirm('确认删除此映射？', '警告')
  await integrationApi.deleteMapping(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

const getSystemTypeName = (type) => {
  return supportedSystems.find(s => s.value === type)?.label || type
}

onMounted(() => {
  fetchData()
})
</script>
```

---

## 后续任务

1. Phase 5.1: 实现万达宝M18适配器（基于通用框架）
2. Phase 5.2: 实现财务凭证集成（基于通用框架）
3. 扩展其他ERP适配器
