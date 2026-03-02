# 05. 通用字段配置系统 - 详细设计

## 概述

通用字段配置系统是一个全局性的配置模块，允许管理员为各种列表类页面（我的资产、我的申请、我的待办等）自定义显示字段、排序、宽度、对齐方式等。配置按层级组织，支持模板复用。

---

## 1. 配置层级结构

### 1.1 层级定义

```
┌─────────────────────────────────────────────────────────────────┐
│  配置层级（优先级从高到低）                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 用户个性化配置                                (最高优先级) ││
│  │  • 用户自己保存的个人偏好                                     ││
│  │  • 仅对自己生效                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                          ↓ 继承 (可覆盖)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 模块级配置模板                                                ││
│  │  • 针对特定模块的配置（如"我的资产-精简模板"）               ││
│  │  • 管理员创建，组织内可选                                    ││
│  └─────────────────────────────────────────────────────────────┘│
│                          ↓ 继承 (可覆盖)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 组织级默认配置                                                ││
│  │  • 组织管理员设置的全组织默认配置                            ││
│  │  • 对组织内所有用户生效（未自定义时）                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                          ↓ 继承 (可覆盖)                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 系统默认配置                                  (最低优先级) ││
│  │  • 系统预置的默认配置                                        ││
│  │  • 所有组织的基础配置                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 配置继承规则

| 场景 | 使用的配置 |
|------|-----------|
| 用户未配置，组织有模板 | 组织级配置 |
| 用户未配置，组织无模板 | 系统默认配置 |
| 用户有配置 | 用户个性化配置 |
| 用户配置后重置 | 回退到组织级配置 |

---

## 2. 配置管理界面

### 2.1 字段配置主页面

```
┌─────────────────────────────────────────────────────────────────┐
│  字段配置管理                                           [+ 新建模板]│
├─────────────────────────────────────────────────────────────────┤
│  模块: [我的资产 ▼]  作用范围: [组织级 ▼]                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 模板名称              适用模块    作用范围    创建时间   操作││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ 默认模板              我的资产    系统级      -          [设为默认]││
│  │ 精简模板              我的资产    组织级      2024-01-10 [编辑][删除]││
│  │ 财务模板              我的资产    组织级      2024-01-09 [编辑][删除]││
│  │ 我的申请-标准模板     我的申请    组织级      2024-01-08 [编辑][删除]││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  < 1 2 3 4 5 >                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 字段配置编辑器

```
┌─────────────────────────────────────────────────────────────────┐
│  编辑字段配置 - 我的资产-精简模板                      [保存][取消]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 基本信息                                                     ││
│  │  模板名称: 我的资产-精简模板                                 ││
│  │  适用模块: 我的资产                                          ││
│  │  作用范围: 组织级                                           ││
│  │  说明: 只显示核心字段，便于快速浏览                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 列表字段配置 (拖拽调整顺序)                                  ││
│  │                                                             ││
│  │  已选字段                              可选字段             ││
│  │  ┌───────────────────────────────┐    ┌─────────────────────┐││
│  │  │ ⋮⋮ ┌─────────────────────┐    │    │ ☑ 资产照片         │││
│  │  │    │ ☑ 资产编码          │    │    │ ☑ 资产分类         │││
│  │  │    └─────────────────────┘    │    │ ☑ 规格型号         │││
│  │  │ ⋮⋮ ┌─────────────────────┐    │    │ ☑ 序列号           │││
│  │  │    │ ☑ 资产名称          │    │    │ ☑ 使用部门         │││
│  │  │    └─────────────────────┘    │    │ ☑ 存放地点         │││
│  │  │ ⋮⋮ ┌─────────────────────┐    │    │ ☑ 保管人           │││
│  │  │    │ ☑ 关系类型          │    │    │ ☑ 领用日期         │││
│  │  │    └─────────────────────┘    │    │ ☑ 资产状态         │││
│  │  │ ⋮⋮ ┌─────────────────────┐    │    │ ☑ 借用日期         │││
│  │  │    │ ☑ 资产状态          │    │    │ ☑ 预计归还         │││
│  │  │    └─────────────────────┘    │    │ ☑ 资产原值         │││
│  │  │ └───────────────────────────────┘    │ ☑ 操作列           │││
│  │                                      └─────────────────────┘││
│  │              [+ 添加自定义字段]                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 字段样式配置                                                 ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │ 字段: 资产编码                    ▼                      │││
│  │  │ ─────────────────────────────────────────────────────── │││
│  │  │ 宽度:   ━━━━━━━━━━━━━━━━━━  □ 自动  ☑ 固定  140px      │││
│  │  │ 对齐:  ○ 左对齐  ● 居中  ○ 右对齐                       ││
│  │  │                                                             ││
│  │  │ 条件格式（可选）:                                           ││
│  │  │  ☑ 启用条件格式                                             ││
│  │  │  ┌─────────────────────────────────────────────────────┐││
│  │  │  │ • 以 "ZC00" 开头的行  背景:浅蓝  文字:深蓝    [删除]│││
│  │  │  └─────────────────────────────────────────────────────┘││
│  │  │  [+ 添加条件]                                               ││
│  │  └───────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ 预览                                                         ││
│  │  ┌─────────────────────────────────────────────────────────┐││
│  │  │ 资产编码     资产名称       关系类型   资产状态         │││
│  │  │ ─────────────────────────────────────────────────────   │││
│  │  │ ZC001      MacBook Pro    保管中      在用             │││
│  │  │ ZC002      Dell显示器     保管中      在用             │││
│  │  └─────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 配置数据结构

### 3.1 配置JSON格式

```json
{
  "template_id": "tpl_my_assets_simple",
  "template_name": "我的资产-精简模板",
  "module": "my_assets",
  "scope": "organization",
  "scope_id": 1,
  "description": "只显示核心字段",
  "config": {
    "list_fields": [
      {
        "field_id": "asset_code",
        "field_label": "资产编码",
        "visible": true,
        "order": 1,
        "width": {
          "mode": "fixed",
          "value": 140
        },
        "align": "center",
        "fixed": true
      },
      {
        "field_id": "asset_name",
        "field_label": "资产名称",
        "visible": true,
        "order": 2,
        "width": {
          "mode": "auto",
          "value": null
        },
        "align": "left"
      },
      {
        "field_id": "relation_type",
        "field_label": "关系类型",
        "visible": true,
        "order": 3,
        "width": {
          "mode": "fixed",
          "value": 100
        },
        "align": "center"
      },
      {
        "field_id": "asset_status",
        "field_label": "资产状态",
        "visible": true,
        "order": 4,
        "width": {
          "mode": "fixed",
          "value": 90
        },
        "align": "center",
        "conditional_formats": [
          {
            "condition": "asset_status == 'maintenance'",
            "background": "#FDE2E2",
            "color": "#F56C6C"
          }
        ]
      }
    ],
    "sort_config": {
      "default_sort_by": "asset_code",
      "default_sort_order": "asc"
    },
    "group_config": {
      "default_group_by": "relation_type"
    }
  }
}
```

### 3.2 条件格式定义

```json
{
  "conditional_formats": [
    {
      "id": "cf_001",
      "condition": "asset_status == 'maintenance'",
      "background": "#FDE2E2",
      "color": "#F56C6C",
      "font_weight": "bold"
    },
    {
      "id": "cf_002",
      "condition": "asset_code.startsWith('ZC00')",
      "background": "#E1F3D8",
      "color": "#67C23A"
    }
  ]
}
```

---

## 4. API设计

### 4.1 获取字段模板列表

```http
GET /api/system/field-templates/

Query Parameters:
  - module: string           # 模块筛选 (my_assets | my_requests | my_tasks)
  - scope: string           # 作用范围筛选 (system | organization | user)

Response:
{
  "templates": [
    {
      "id": "tpl_default",
      "name": "默认模板",
      "module": "my_assets",
      "scope": "system",
      "is_default": true,
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "tpl_simple",
      "name": "精简模板",
      "module": "my_assets",
      "scope": "organization",
      "scope_id": 1,
      "is_default": false,
      "created_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### 4.2 创建字段模板

```http
POST /api/system/field-templates/

Request:
{
  "name": "我的资产-精简模板",
  "module": "my_assets",
  "scope": "organization",
  "description": "只显示核心字段",
  "config": {...}
}

Response:
{
  "id": "tpl_123",
  "name": "我的资产-精简模板",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 4.3 更新字段模板

```http
PUT /api/system/field-templates/{template_id}/

Request:
{
  "name": "我的资产-精简模板（更新）",
  "config": {...}
}

Response:
{
  "success": true,
  "message": "模板已更新"
}
```

### 4.4 设置默认模板

```http
POST /api/system/field-templates/{template_id}/set-default/

Request:
{
  "scope": "organization",
  "scope_id": 1
}

Response:
{
  "success": true,
  "message": "已设为默认模板"
}
```

### 4.5 获取用户的字段配置

```http
GET /api/system/my-field-config/

Query Parameters:
  - module: string           # 模块名称

Response:
{
  "module": "my_assets",
  "config": {
    "template_id": "tpl_simple",
    "template_name": "精简模板",
    "overrides": {
      "list_fields": [
        // 用户自定义的字段配置
      ]
    },
    "is_customized": false
  },
  "available_templates": [
    {
      "id": "tpl_default",
      "name": "默认模板"
    },
    {
      "id": "tpl_simple",
      "name": "精简模板"
    }
  ]
}
```

### 4.6 保存用户字段配置

```http
POST /api/system/my-field-config/

Request:
{
  "module": "my_assets",
  "config": {...}
}

Response:
{
  "success": true,
  "message": "配置已保存"
}
```

### 4.7 重置为默认配置

```http
POST /api/system/my-field-config/reset/

Request:
{
  "module": "my_assets"
}

Response:
{
  "success": true,
  "message": "已重置为默认配置"
}
```

---

## 5. 前端组件

### 5.1 字段配置组件

```vue
<!-- src/components/system/FieldConfigPanel.vue -->

<template>
  <div class="field-config-panel">
    <!-- 基本信息 -->
    <el-form-item label="模板名称" prop="name">
      <el-input v-model="config.name" />
    </el-form-item>

    <el-form-item label="说明">
      <el-input v-model="config.description" type="textarea" />
    </el-form-item>

    <!-- 字段选择器 -->
    <FieldSelector
      v-model="config.list_fields"
      :available-fields="availableFields"
      :module="module"
    />

    <!-- 字段样式编辑器 -->
    <FieldStyleEditor
      v-model="selectedFieldStyle"
      :field="selectedField"
      @change="handleFieldStyleChange"
    />

    <!-- 预览 -->
    <ConfigPreview
      :config="config"
      :sample-data="sampleData"
      :module="module"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  module: string
  config: any
  availableFields: any[]
}

const props = defineProps<Props>()

const selectedField = ref(null)
const selectedFieldStyle = computed(() => {
  if (!selectedField.value) return null
  return props.config.list_fields.find(
    (f: any) => f.field_id === selectedField.value
  )
})

const handleFieldStyleChange = (style: any) => {
  // 更新字段样式
}
</script>
```

### 5.2 字段选择器组件

```vue
<!-- src/components/system/FieldSelector.vue -->

<template>
  <div class="field-selector">
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="selected-fields">
          <div class="panel-header">已选字段</div>
          <draggable
            v-model="selectedFields"
            :animation="200"
            item-key="field_id"
            @end="handleDragEnd"
          >
            <template #item="{ element }">
              <div class="field-item">
                <el-icon class="drag-handle"><Rank /></el-icon>
                <el-checkbox
                  :model-value="element.visible"
                  @change="handleVisibleChange(element, $event)"
                >
                  {{ element.field_label }}
                </el-checkbox>
                <el-button
                  link
                  type="primary"
                  @click="handleStyleEdit(element)"
                >
                  样式
                </el-button>
              </div>
            </template>
          </draggable>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="available-fields">
          <div class="panel-header">可选字段</div>
          <el-checkbox-group v-model="enabledFieldIds">
            <div
              v-for="field in availableFields"
              :key="field.field_id"
              class="field-item"
            >
              <el-checkbox :label="field.field_id">
                {{ field.field_label }}
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import draggable from 'vuedraggable'

interface Props {
  modelValue: any[]
  availableFields: any[]
  module: string
}

const props = defineProps<Props>()
const emit = defineEmits(['update:modelValue', 'style-edit'])

const selectedFields = ref(props.modelValue)

const enabledFieldIds = computed(() => {
  return selectedFields.value
    .filter((f: any) => f.visible)
    .map((f: any) => f.field_id)
})

const handleVisibleChange = (field: any, visible: boolean) => {
  field.visible = visible
  emit('update:modelValue', selectedFields.value)
}

const handleDragEnd = () => {
  // 更新顺序
  selectedFields.value.forEach((f: any, index: number) => {
    f.order = index + 1
  })
  emit('update:modelValue', selectedFields.value)
}

const handleStyleEdit = (field: any) => {
  emit('style-edit', field)
}
</script>
```

---

## 6. 支持的模块

| 模块编码 | 模块名称 | 可配置字段数 | 配置类型 |
|---------|---------|-------------|---------|
| my_assets | 我的资产 | 15+ | 列表 |
| my_requests | 我的申请 | 12+ | 列表、卡片 |
| my_tasks | 我的待办 | 10+ | 列表、卡片 |
| inventory_tasks | 盘点任务 | 12+ | 列表、详情 |
| asset_list | 资产列表 | 20+ | 列表 |
| consumable_list | 耗材列表 | 15+ | 列表 |
