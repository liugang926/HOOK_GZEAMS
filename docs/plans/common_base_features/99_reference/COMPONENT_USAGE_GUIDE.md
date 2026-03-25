# 前端组件使用场景指南

> **目标**：帮助开发者快速决策在不同场景下应该使用哪个组件，避免选择困难和错误使用。

---

## 1. 组件选择决策树

```
开始
  │
  ├─ 需要开发什么类型页面？
  │   │
  │   ├─ 列表展示页面 ────────────────────┐
  │   │                                  │
  │   ├─ 表单编辑页面 ────────────────────┤
  │   │                                  │
  │   ├─ 详情查看页面 ────────────────────┤
  │   │                                  │
  │   └─ 复杂业务页面 ────────────────────┘
  │                                      │
  │                                      ▼
  │                            数据模型是否已存在？
  │                                      │
  │                         ┌────────────┴────────────┐
  │                         │                         │
  │                        是                        否
  │                         │                         │
  │                         ▼                         ▼
  │                    传统模式                元数据驱动模式
  │                         │                         │
  │                    需要自定义？              需要快速上线？
  │                         │                         │
  │                    ┌────┴────┐              ┌────┴────┐
  │                    │         │              │         │
  │                   是        否             是        否
  │                    │         │              │         │
  │                    ▼         ▼              ▼         ▼
  │              BaseListPage  BaseListPage  MetadataDrivenList  自定义开发
  │              +自定义插槽   (直接使用)    (配置元数据)      (完全自定义)
```

---

## 2. 列表页面组件选择

### 2.1 BaseListPage

**使用场景**：

| 场景 | 是否适用 | 说明 |
|------|---------|------|
| 标准 CRUD 列表页面 | ✅ | 适用于大多数业务实体的列表展示 |
| 需要自定义列渲染 | ✅ | 支持插槽自定义列内容 |
| 需要复杂搜索条件 | ✅ | 支持自定义搜索字段和筛选字段 |
| 需要批量操作 | ✅ | 内置批量删除等操作支持 |
| 数据模型已固定 | ✅ | 适用于 Asset、Category 等传统模型 |
| 需要自定义表格样式 | ✅ | 可以通过自定义插槽实现 |

**使用示例**：

```vue
<template>
    <BaseListPage
        title="资产列表"
        :fetch-method="fetchAssets"
        :batch-delete-method="batchDeleteAssets"
        :columns="columns"
        :search-fields="searchFields"
        :filter-fields="filterFields"
        :custom-slots="['status', 'actions']"
        @row-click="handleRowClick"
        @create="handleCreate"
    >
        <template #status="{ row }">
            <el-tag :type="getStatusType(row.status)">
                {{ getStatusLabel(row.status) }}
            </el-tag>
        </template>
    </BaseListPage>
</template>
```

**何时选择 BaseListPage**：
- ✅ 后端已有固定的 Django Model
- ✅ API 端点已定义完成
- ✅ 列表结构相对稳定
- ✅ 需要精细控制每个列的展示

### 2.2 MetadataDrivenList

**使用场景**：

| 场景 | 是否适用 | 说明 |
|------|---------|------|
| 快速原型开发 | ✅ | 无需前端代码，仅配置元数据即可 |
| 动态业务对象 | ✅ | 用户自定义的业务对象 |
| 列表结构频繁变化 | ✅ | 修改元数据配置即可生效 |
| 无需自定义列渲染 | ✅ | 标准列展示满足需求 |
| 降低开发成本 | ✅ | 减少前端代码量 |

**使用示例**：

```vue
<template>
    <MetadataDrivenList
        object-code="ProcurementRequest"
        :layout-code="listLayoutCode"
        :read-only="false"
        @row-click="handleRowClick"
    />
</template>

<script setup>
import { MetadataDrivenList } from '@/components/metadata'
</script>
```

**何时选择 MetadataDrivenList**：
- ✅ 业务对象是用户自定义的（DynamicData）
- ✅ 快速开发标准 CRUD 页面
- ✅ 列表结构可能随配置变化
- ✅ 不需要复杂的自定义渲染

### 2.3 对比总结

| 对比维度 | BaseListPage | MetadataDrivenList |
|---------|-------------|-------------------|
| **开发速度** | 中等（需定义列） | 快（仅配置） |
| **灵活性** | 高（完全自定义） | 中（受限于元数据配置） |
| **适用模型** | Django Model | BusinessObject + DynamicData |
| **自定义能力** | 插槽 + 事件 | 元数据配置 + 钩子 |
| **维护成本** | 中等（代码变更） | 低（配置变更） |

---

## 3. 表单页面组件选择

### 3.1 BaseFormPage

**使用场景**：

| 场景 | 是否适用 | 说明 |
|------|---------|------|
| 标准表单编辑 | ✅ | 适用于大多数表单场景 |
| 复杂表单布局 | ✅ | 支持任意自定义布局 |
| 复杂验证规则 | ✅ | 支持自定义验证逻辑 |
| 主子表单 | ✅ | 支持 SubTableField 等复杂组件 |
| 数据模型已固定 | ✅ | 适用于传统 Model |

**使用示例**：

```vue
<template>
    <BaseFormPage
        title="资产信息"
        :submit-method="handleSubmit"
        :initial-data="assetData"
        :rules="rules"
        submit-text="保存"
        redirect-path="/assets"
    >
        <template #default="{ data }">
            <el-form-item label="资产编码" prop="code">
                <el-input v-model="data.code" />
            </el-form-item>
            <!-- 自定义表单布局 -->
        </template>
    </BaseFormPage>
</template>
```

**何时选择 BaseFormPage**：
- ✅ 需要完全自定义表单布局
- ✅ 表单验证逻辑复杂
- ✅ 需要特殊的表单交互
- ✅ 表单结构固定不常变

### 3.2 MetadataDrivenForm

**使用场景**：

| 场景 | 是否适用 | 说明 |
|------|---------|------|
| 动态表单生成 | ✅ | 根据元数据自动生成表单 |
| 快速表单开发 | ✅ | 无需编写表单代码 |
| 工作流表单 | ✅ | 支持节点级字段权限控制 |
| 用户自定义表单 | ✅ | 支持用户自定义字段 |

**使用示例**：

```vue
<template>
    <MetadataDrivenForm
        object-code="ProcurementRequest"
        :data-id="requestId"
        :layout-code="formLayoutCode"
        :workflow-node="currentNode"
        @submit="handleSubmit"
        @cancel="handleCancel"
    />
</template>
```

**何时选择 MetadataDrivenForm**：
- ✅ 业务对象是动态配置的
- ✅ 需要工作流节点权限控制
- ✅ 字段可能随配置变化
- ✅ 标准表单布局即可满足需求

### 3.3 DynamicForm（引擎组件）

**使用场景**：

| 场景 | 是否适用 | 说明 |
|------|---------|------|
| 需要手动控制元数据加载 | ✅ | 自己管理元数据和布局 |
| 嵌入到其他组件中 | ✅ | 作为子组件使用 |
| 需要精细控制渲染过程 | ✅ | 可访问更多底层能力 |

**使用示例**：

```vue
<template>
    <DynamicForm
        :metadata="metadata"
        :layout="layout"
        :data="formData"
        :read-only="readOnly"
        @field-change="handleFieldChange"
    />
</template>

<script setup>
import { ref } from 'vue'
import { DynamicForm } from '@/components/engine'
import { useMetadata } from '@/composables/useMetadata'

const { fetchMetadata } = useMetadata()
const metadata = ref(null)
const layout = ref(null)

// 手动加载元数据
onMounted(async () => {
    metadata.value = await fetchMetadata('Asset')
    layout.value = metadata.value.layouts.form
})
</script>
```

**何时选择 DynamicForm**：
- ✅ 需要手动管理元数据加载
- ✅ 需要更底层的控制能力
- ✅ 作为可复用表单组件嵌入

### 3.4 表单组件对比

| 对比维度 | BaseFormPage | MetadataDrivenForm | DynamicForm |
|---------|-------------|-------------------|------------|
| **开发方式** | 编写表单代码 | 配置元数据 | 手动加载元数据 |
| **灵活性** | 最高 | 高 | 中高 |
| **工作流支持** | 手动实现 | 内置支持 | 需自行处理 |
| **自动验证** | 手动定义 | 从元数据生成 | 从元数据生成 |
| **适用场景** | 复杂自定义表单 | 标准业务表单 | 嵌入式场景 |

---

## 4. 详情页面组件选择

### 4.1 BaseDetailPage

**使用场景**：
- ✅ 标准详情展示
- ✅ 需要自定义详情布局
- ✅ 需要展示审计信息
- ✅ 需要操作按钮

**使用示例**：

```vue
<template>
    <BaseDetailPage
        title="资产详情"
        :fetch-method="fetchAssetDetail"
        :id="assetId"
        :show-audit="true"
    >
        <template #actions="{ data }">
            <el-button type="primary" @click="handleEdit">编辑</el-button>
        </template>

        <template #content="{ data }">
            <el-descriptions :column="2" border>
                <el-descriptions-item label="资产编码">
                    {{ data.code }}
                </el-descriptions-item>
                <!-- ... -->
            </el-descriptions>
        </template>
    </BaseDetailPage>
</template>
```

### 4.2 元数据驱动详情

**使用场景**：
- ✅ 标准详情展示
- ✅ 字段结构由元数据定义
- ✅ 快速开发

**实现方式**：使用 `MetadataDrivenForm` 的只读模式：

```vue
<template>
    <MetadataDrivenForm
        object-code="Asset"
        :data-id="assetId"
        :read-only="true"
    />
</template>
```

---

## 5. 特殊场景组件选择

### 5.1 主子表单

**场景**：需要在一个表单中同时编辑主表和子表数据

**推荐组件**：`BaseFormPage` + `SubTableField`

```vue
<template>
    <BaseFormPage :submit-method="handleSubmit" :initial-data="data">
        <template #default="{ data }">
            <!-- 主表字段 -->
            <el-form-item label="单据编号" prop="code">
                <el-input v-model="data.code" />
            </el-form-item>

            <!-- 子表字段 -->
            <SubTableField
                v-model="data.items"
                :columns="subTableColumns"
                :sub-object-code="ProcurementItem"
            />
        </template>
    </BaseFormPage>
</template>
```

### 5.2 工作流表单

**场景**：表单字段权限需根据工作流节点动态控制

**推荐组件**：`MetadataDrivenForm`

```vue
<template>
    <MetadataDrivenForm
        object-code="ProcurementRequest"
        :data-id="requestId"
        :workflow-node="workflowNode"
        :node-config="nodeFieldConfig"
    />
</template>

<script setup>
// workflowNode 决定哪些字段只读/隐藏/可编辑
const workflowNode = ref('approval')
const nodeFieldConfig = ref({
    approval: {
        readonly_fields: ['amount', 'requester'],
        hidden_fields: ['attachments']
    }
})
</script>
```

### 5.3 移动端表单

**场景**：需要适配移动端的表单

**推荐组件**：`MetadataDrivenForm` + 移动端布局配置

```vue
<template>
    <MetadataDrivenForm
        object-code="Asset"
        :data-id="assetId"
        layout-type="mobile"
    />
</template>
```

---

## 6. 组件迁移指南

### 6.1 从传统模式迁移到元数据驱动

**场景**：现有 `BaseFormPage` 表单需要支持用户自定义字段

**迁移步骤**：

1. **评估字段结构**：确定哪些字段固定，哪些需要动态
2. **创建 BusinessObject**：定义业务对象和字段
3. **配置 PageLayout**：设置表单布局
4. **替换组件**：逐步替换为 `MetadataDrivenForm`
5. **保留自定义部分**：使用插槽保留特殊逻辑

```vue
<!-- 迁移前：全部固定字段 -->
<BaseFormPage :submit-method="handleSubmit">
    <template #default="{ data }">
        <el-form-item label="编码" prop="code">
            <el-input v-model="data.code" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
            <el-input v-model="data.name" />
        </el-form-item>
        <!-- 更多固定字段... -->
    </template>
</BaseFormPage>

<!-- 迁移后：混合模式 -->
<MetadataDrivenForm
    object-code="Asset"
    :data-id="assetId"
    @submit="handleSubmit"
>
    <!-- 保留自定义扩展区域 -->
    <template #extension="{ data }">
        <el-form-item label="特殊计算字段">
            <SpecialCalculationField v-model="data.special_field" />
        </el-form-item>
    </template>
</MetadataDrivenForm>
```

### 6.2 从元数据驱动迁移到传统模式

**场景**：动态表单逐渐稳定，需要更高性能或更复杂交互

**迁移步骤**：

1. **生成固定代码**：根据当前元数据生成传统代码
2. **优化交互逻辑**：添加复杂的交互效果
3. **替换组件**：使用 `BaseFormPage` 替换
4. **删除元数据配置**：清理不再使用的配置

---

## 7. 最佳实践

### 7.1 新功能开发

```
问题：开发新功能时，应该选择哪种组件？

决策流程：
1. 是否是核心稳定业务（如资产、分类）？
   ├─ 是 → 使用传统模式（BaseListPage/BaseFormPage）
   └─ 否 → 继续下一步

2. 用户是否需要自定义字段？
   ├─ 是 → 使用元数据驱动（MetadataDrivenList/Form）
   └─ 否 → 继续下一步

3. 是否需要快速上线？
   ├─ 是 → 使用元数据驱动
   └─ 否 → 使用传统模式（长期维护成本更低）
```

### 7.2 混合使用

**推荐做法**：核心模块用传统模式，扩展模块用元数据驱动

```
项目结构示例：
├── assets/              # 资产核心模块 - 传统模式
│   ├── AssetList.vue    (BaseListPage)
│   └── AssetForm.vue    (BaseFormPage)
│
└── procurement/         # 采购扩展模块 - 元数据驱动
    ├── RequestList.vue  (MetadataDrivenList)
    └── RequestForm.vue  (MetadataDrivenForm)
```

### 7.3 性能考虑

| 场景 | 推荐组件 | 原因 |
|------|---------|------|
| 大数据量列表 | BaseListPage | 可精细化控制渲染 |
| 复杂计算表单 | BaseFormPage | 避免元数据解析开销 |
| 标准CRUD | MetadataDrivenList/Form | 减少代码量 |
| 频繁变更结构 | MetadataDrivenList/Form | 配置即可生效 |

### 7.4 维护成本

```
组件选择与维护成本关系：

传统模式（BaseListPage/BaseFormPage）
├─ 优点：性能好、调试方便、逻辑清晰
├─ 缺点：代码量大、变更需改代码
└─ 适用：核心稳定模块

元数据驱动（MetadataDrivenList/Form）
├─ 优点：代码量少、配置变更生效
├─ 缺点：调试复杂、性能略低
└─ 适用：扩展模块、快速原型
```

---

## 8. 组件使用速查表

| 页面类型 | 传统模式组件 | 元数据驱动组件 | 选择依据 |
|---------|-------------|---------------|---------|
| 列表页 | `BaseListPage` | `MetadataDrivenList` | 模型固定用前者，动态用后者 |
| 表单页 | `BaseFormPage` | `MetadataDrivenForm` | 布局复杂用前者，标准用后者 |
| 详情页 | `BaseDetailPage` | `MetadataDrivenForm(readOnly)` | 自定义布局用前者，标准用后者 |
| 工作流表单 | 手动实现 | `MetadataDrivenForm` | 推荐使用后者 |
| 主子表单 | `BaseFormPage` + `SubTableField` | `MetadataDrivenForm` | 复杂交互用前者 |
| 移动端表单 | 自定义适配 | `MetadataDrivenForm(mobileLayout)` | 快速适配用后者 |

---

## 9. 常见问题

### Q1: 可以在同一个项目中混用两种模式吗？

**答**: 可以，且推荐这样做。核心稳定模块使用传统模式，扩展模块使用元数据驱动。

### Q2: 元数据驱动模式的性能如何？

**答**: 对于标准CRUD场景性能差异不大。对于大数据量或高频操作场景，建议使用传统模式。

### Q3: 如何从元数据驱动切换到传统模式？

**答**: 参考本文档"6.2 从元数据驱动迁移到传统模式"章节。

### Q4: BaseFormPage 和 MetadataDrivenForm 可以互相嵌套吗？

**答**: 不建议。但可以在 `MetadataDrivenForm` 中使用插槽扩展自定义区域。

### Q5: DynamicForm 和 MetadataDrivenForm 有什么区别？

**答**:
- `MetadataDrivenForm`: 自动加载元数据的高级封装，使用简单
- `DynamicForm`: 需要手动传入元数据和布局，控制更精细

---

## 10. 参考文档

- [前端公共组件详细设计](./frontend.md) - BaseListPage/BaseFormPage 完整实现
- [元数据驱动前端组件](./metadata_frontend.md) - MetadataDriven 组件详细说明
- [元数据驱动使用指南](./METADATA_DRIVEN_GUIDE.md) - 完整的元数据驱动开发指南
- [页面布局配置](./page_layout_config.md) - PageLayout 配置规范
- [PRD编写指南](./prd_writing_guide.md) - PRD 中如何声明组件使用
