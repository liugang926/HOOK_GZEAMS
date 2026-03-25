# 布局可视化设计器规范 (Layout Visual Designer)

## 1. 设计器概述

### 1.0 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

**注意**: 布局设计器是前端 Vue 组件，配置数据存储在 PageLayout.layout_config JSON 字段中。

### 1.1 功能目标
布局可视化设计器是 GZEAMS 低代码平台的核心组件，旨在让管理员通过**拖拽方式**自定义页面布局，无需编写代码即可实现：
- 表单布局自定义（字段排列、分组、标签页）
- 列表布局自定义（列配置、筛选器、批量操作）
- 详情页布局自定义（信息分组、关联数据展示）
- 移动端布局适配（响应式布局配置）

### 1.2 技术选型 (Modernized Stack)
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4.0 | 核心框架 (Composition API) |
| Tailwind CSS | ^3.4.0 | 原子化 CSS 引擎 (样式 & 布局) |
| Radix Vue | ^1.0.0 | 无头组件库 (交互逻辑 & A11y) |
| Shadcn-Vue | - | UI 组件集合 (Premium Aesthetics) |
| Sortable.js | ^1.15.0 | 拖拽排序功能 |
| VueUse | ^10.0 | 组合式工具集 (核心交互逻辑) |
| Pinia | ^2.1.0 | 状态管理 |
| Zod | ^3.22 | 运行时 Schema 验证 |

### 1.4 工程化标准 (Engineering Standards)
为确保设计器预览与运行时的高度一致性，以及实现"Premium"级 UI 效果，采用以下工程化策略：

1.  **原子化布局系统 (Atomic Layout System)**
    - 摒弃传统的 `el-row/el-col` 栅格，采用 Tailwind CSS Grid/Flex 系统。
    - **布局即数据**: 布局配置直接存储 Tailwind 类名 (e.g., `class: "grid grid-cols-12 gap-4"`)。
    - **零运行时偏差**: 渲染引擎直接应用类名，无需 JavaScript 计算布局宽。

2.  **样式隔离与预览 (Style Isolation)**
    - **IFrame 预览沙箱**: 在设计器的"预览"模式下，使用 IFrame 加载运行时页面，确保 CSS 环境（尤其是 Viewport 和 Media Queries）的物理隔离。
    - **禁止全局样式污染**: 所有组件样式通过 Tailwind Utility 类实现，严禁使用全局 SCSS 覆盖组件库内部样式。

3.  **高级视觉效果 (Premium Aesthetics)**
    - 使用 **Radix Vue** 作为交互底座，确保 Focus Trap、Keyboard Navigation 等无障碍特性达到国际标准。
    - 采用 **Inter** 字体与 **Zinc** 色板，打造 Clean/Flat 风格界面。

### 1.3 设计器组件架构
```
LayoutDesigner/
├── components/
│   ├── DesignerToolbar.vue        # 工具栏
│   ├── ComponentPanel.vue         # 组件面板
│   ├── CanvasArea.vue             # 画布区域
│   ├── PropertyPanel.vue          # 属性面板
│   ├── FieldElement.vue           # 字段元素
│   ├── SectionBlock.vue           # 区块组件
│   ├── TabPanel.vue               # 标签页组件
│   └── ColumnLayout.vue           # 分栏组件
├── composables/
│   ├── useDraggable.js            # 拖拽逻辑
│   ├── useLayoutHistory.js        # 撤销/重做历史
│   └── useLayoutValidation.js     # 布局验证
├── stores/
│   └── layoutDesigner.js          # Pinia 状态管理
└── utils/
    ├── layoutSchema.js            # 布局 Schema 定义
    └── layoutConverter.js         # 布局格式转换
```

---

## 2. 设计器界面布局

### 2.1 整体布局结构
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  页面配置 > 资产管理 > 表单布局                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  工具栏 (DesignerToolbar)                                                    │
│  [保存草稿] [发布] [预览] [撤销] [重做] [清空] [导入] [导出]                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  组件面板 (240px)  │  画布区域 (自适应)           │  属性面板 (320px)     │
│                    │                              │                        │
│  ┌──────────────┐ │  ┌──────────────────────────┐ │  ┌────────────────┐  │
│  │ 可用字段     │ │  │  基本信息 [▼]             │ │  │ 字段: 资产编码  │  │
│  ├──────────────┤ │  │  [资产编码____] [资产名称] │ │  ├────────────────┤  │
│  │ ☑ 资产编码   │ │  │  [分类________] [状态____]  │ │  │ 标签宽度        │  │
│  │ ☑ 资产名称   │ │  │                           │ │  │ [120px   ▼]    │  │
│  │ ☑ 资产分类   │ │  │  详细信息 [▼]             │ │  │                 │  │
│  │ ☑ 资产状态   │ │  │  [规格型号________]       │ │  │ 占位符          │  │
│  │ ☑ 购置日期   │ │  │  [序列号__________]       │ │  │ [请输入资产码]  │  │
│  │ ☑ 原值       │ │  │                           │ │  │                 │  │
│  │ ☑ 存放位置   │ │  │  维护信息 [▼]             │ │  │ 必填            │  │
│  └──────────────┘ │  │  [责任人____] [保养日期]  │ │  │ [✓] 是          │  │
│                    │  │                           │ │  │                 │  │
│  ┌──────────────┐ │  └──────────────────────────┘ │  │ 只读            │  │
│  │ 布局组件     │ │                              │  │ [ ] 是          │  │
│  ├──────────────┤ │  [+ 添加区块] [+ 添加标签页] │  │                 │  │
│  │ [区块____]   │ │                              │  │ 默认值          │  │
│  │ [标签页___]  │ │                              │  │ [ASSET2024001] │  │
│  │ [分栏____]   │ │                              │  │                 │  │
│  │ [分隔线___]  │ │                              │  │ [删除字段]      │  │
│  │ [折叠面板_]  │ │                              │  │                 │  │
│  └──────────────┘ │                              │  └────────────────┘  │
│                    │                              │                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 组件面板 (ComponentPanel)
**位置**: 左侧，宽度 240px

**功能分区**:
1. **可用字段列表**
   - 从 `FieldDefinition` 获取当前业务对象的字段
   - 支持搜索过滤字段
   - 按字段分组显示（系统字段/自定义字段）
   - 复选框标记已使用的字段

2. **布局组件**
   - 区块 (Section): 可折叠的信息分组
   - 标签页 (Tab): 多标签页切换
   - 分栏 (Column): 水平分栏布局
   - 分隔线 (Divider): 视觉分隔
   - 折叠面板 (Collapse): 可折叠内容区

**拖拽行为**:
- 字段从组件面板拖拽到画布
- 布局组件拖拽到画布插入位置
- 拖拽时显示半透明幽灵元素

### 2.3 画布区域 (CanvasArea)
**位置**: 中间，自适应宽度

**核心功能**:
1. **可视化编辑**
   - 实时预览布局效果
   - 字段拖拽排序（Sortable.js）
   - 字段跨列调整（2列/3列/4列）
   - 区块嵌套支持（最多3层）

2. **交互操作**
   - 点击选中元素（高亮显示）
   - 右键上下文菜单（复制/粘贴/删除）
   - 快捷键支持（Ctrl+Z撤销/Ctrl+Y重做/Delete删除）
   - 拖拽插入辅助线显示

3. **响应式预览**
   - 桌面端预览 (1920px)
   - 平板预览 (768px)
   - 移动端预览 (375px)

### 2.4 属性面板 (PropertyPanel)
**位置**: 右侧，宽度 320px

**动态属性表单**:
根据选中元素类型显示对应的属性配置：

#### 字段属性 (FieldElement)

对应 `FieldReference` 模型。注意：只有 `label_override` 和 `help_text_override` 可编辑，其他属性（如 required, readonly）若由 FieldDefinition 定义则显示为只读状态。

```javascript
{
  // 核心引用
  field_code: "asset_code",   // 不可变

  // 展示层覆盖 (Layout Config)
  label_override: "资产编码",  // 默认 placeholder 为 Field.name
  help_text_override: "规则：ASSET+年份+4位序号",
  
  // 布局属性
  span: 12,                   // ColSpan
  hidden: false,              // Visible

  // 只读展示 (来自 FieldDefinition L0)
  _meta: {
    type: "string",
    required: true,
    readonly: false
  }
}
```

#### 区块属性 (SectionBlock)

对应 `SectionConfig` 模型。

```javascript
{
  id: "section_basic",
  title: "基本信息",
  
  // 布局控制
  collapsible: true,
  default_collapsed: false,
  columns: 2, // 1 | 2 | 3 | 4

  // 样式类原子化 (Tailwind)
  container_class: "bg-white p-6 rounded-lg border border-slate-200 shadow-sm"
}
```
}
```

#### 标签页属性 (TabPanel)
```javascript
{
  title: "基本信息",           // 标签页标题
  icon: "el-icon-document",   // 图标
  position: "top",            // 位置 (top/left/right/bottom)
  lazy: true,                 // 是否懒加载
  closable: false,            // 是否可关闭
  custom_class: "basic-info-tab"
}
```

---

## 3. 工具栏功能

### 3.1 工具栏组件 (DesignerToolbar)

```vue
<template>
  <div class="h-full flex flex-col bg-slate-50">
    <div class="h-14 border-b bg-white flex items-center justify-between px-4">
      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" @click="handleSave">
          <Icon name="save" class="mr-2 h-4 w-4" />
          保存草稿
        </Button>
        <Button variant="default" size="sm" @click="handlePublish">
          <Icon name="publish" class="mr-2 h-4 w-4" />
          发布
        </Button>
      </div>

      <div class="flex items-center gap-2 bg-slate-100 p-1 rounded-md">
        <Button variant="ghost" size="icon" :disabled="!canUndo" @click="handleUndo">
          <Icon name="undo" class="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" :disabled="!canRedo" @click="handleRedo">
          <Icon name="redo" class="h-4 w-4" />
        </Button>
      </div>

      <div class="flex items-center gap-2">
        <Button variant="outline" size="sm" @click="handlePreview">
          <Icon name="eye" class="mr-2 h-4 w-4" />
          预览
        </Button>
      </div>
    </div>
  </div>
</template>
```

### 3.2 工具栏功能详解

#### 3.2.1 保存草稿
**功能**: 保存当前布局为草稿状态，不发布到生产环境

**API 调用**:
```http
POST /api/system/page-layouts/{id}/save_draft/
Content-Type: application/json

{
  "config": { /* 布局配置 */ },
  "comment": "更新了基本信息区块的字段顺序"
}
```

**响应**:
```json
{
  "success": true,
  "message": "草稿保存成功",
  "data": {
    "id": "uuid",
    "status": "draft",
    "version": "1.0.1-draft",
    "modified_at": "2024-01-15T10:30:00Z"
  }
}
```

#### 3.2.2 发布
**功能**: 将布局发布到生产环境，需要审批（可选）

**发布流程**:
1. 验证布局配置完整性
2. 生成新版本号
3. 保存版本快照
4. 更新状态为 `published`
5. 记录发布日志

**API 调用**:
```http
POST /api/system/page-layouts/{id}/publish/
Content-Type: application/json

{
  "comment": "发布新的资产表单布局",
  "require_approval": false
}
```

**响应**:
```json
{
  "success": true,
  "message": "布局发布成功",
  "data": {
    "id": "uuid",
    "status": "published",
    "version": "1.0.1",
    "published_at": "2024-01-15T10:35:00Z",
    "published_by": {
      "id": "user_uuid",
      "username": "admin"
    }
  }
}
```

#### 3.2.3 预览
**功能**: 在新窗口中预览布局效果

**预览模式**:
- **设计模式**: 显示字段占位符和边框
- **预览模式**: 模拟真实数据填充效果
- **响应式预览**: 切换桌面/平板/移动端视图

**实现方式**:
```javascript
const handlePreview = () => {
  const layoutData = JSON.stringify(layoutConfig.value)
  const previewUrl = `/preview-layout?data=${encodeURIComponent(layoutData)}`
  window.open(previewUrl, '_blank', 'width=1200,height=800')
}
```

#### 3.2.4 撤销/重做
**功能**: 操作历史管理，支持多步撤销和重做

**历史栈结构**:
```javascript
const historyState = {
  past: [],      // 历史记录栈
  present: null, // 当前状态
  future: []     // 未来记录栈（重做栈）
}

// 最大历史记录数
const MAX_HISTORY_SIZE = 50
```

**实现逻辑**:
```javascript
// 撤销
const handleUndo = () => {
  if (historyState.past.length === 0) return

  const previousState = historyState.past.pop()
  historyState.future.push(historyState.present)
  historyState.present = previousState

  layoutConfig.value = previousState
}

// 重做
const handleRedo = () => {
  if (historyState.future.length === 0) return

  const nextState = historyState.future.pop()
  historyState.past.push(historyState.present)
  historyState.present = nextState

  layoutConfig.value = nextState
}
```

#### 3.2.5 清空
**功能**: 清空画布所有元素（需二次确认）

**确认对话框**:
```javascript
const handleClear = () => {
  // Using a custom confirm dialog component or composable
  // const { confirm } = useConfirm() 
  // if (await confirm('Are you sure?', 'This action cannot be undone.')) { ... }
  
  layoutConfig.value = { sections: [] }
  toast({
    title: "Success",
    description: "Layout cleared successfully"
  })
}
```

#### 3.2.6 导入/导出
**导入功能**:
```javascript
const handleImport = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    const file = e.target.files[0]
    const text = await file.text()
    const config = JSON.parse(text)

    // 验证 Schema
    const validation = validateLayoutSchema(config)
    if (!validation.valid) {
      toast({
        variant: "destructive",
        title: "Validation Error",
        description: `Invalid layout config: ${validation.errors.join(', ')}`
      })
      return
    }

    layoutConfig.value = config
    toast({
      title: "Success",
      description: "Layout imported successfully"
    })
  }
  input.click()
}
```

**导出功能**:
```javascript
const handleExport = () => {
  const dataStr = JSON.stringify(layoutConfig.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `layout-${businessObject.value}-${Date.now()}.json`
  link.click()

  URL.revokeObjectURL(url)
  toast({
    title: "Success",
    description: "Layout exported successfully"
  })
}
```

---

## 4. 布局配置数据结构

### 4.1 完整布局 Schema

```javascript
{
  "layout_id": "uuid-v4",
  "business_object": "Asset",           // 业务对象编码
  "layout_type": "form",                // 布局类型: form | list | detail
  "layout_name": "资产表单布局",
  "description": "资产新增/编辑表单布局",
  "status": "published",                // draft | published | archived
  "version": "1.0.0",
  "config": {
    "sections": [                       // 区块列表
      {
        "id": "section-1",
        "type": "section",
        "title": "基本信息",
        "collapsible": true,
        "collapsed": false,
        "columns": 2,
        "border": false,
        "render_as_card": false,
        "icon": "i-heroicons-document-text",
        "fields": [
          {
            "id": "field-1",
            "field_code": "asset_code",
            "span": 12,
            "label": "资产编码",
            "width": "120px",
            "placeholder": "请输入资产编码",
            "required": true,
            "readonly": false,
            "default_value": "",
            "help_text": "资产编码规则：ASSET+年份+4位序号"
          },
          {
            "id": "field-2",
            "field_code": "asset_name",
            "span": 12,
            "label": "资产名称",
            "width": "120px",
            "placeholder": "请输入资产名称",
            "required": true
          }
        ]
      },
      {
        "id": "section-2",
        "type": "tab",
        "position": "top",
        "tabs": [
          {
            "id": "tab-1",
            "title": "详细信息",
            "icon": "i-heroicons-information-circle",
            "fields": [
              {
                "id": "field-3",
                "field_code": "specification",
                "span": 12,
                "label": "规格型号"
              },
              {
                "id": "field-4",
                "field_code": "serial_number",
                "span": 12,
                "label": "序列号"
              }
            ]
          },
          {
            "id": "tab-2",
            "title": "维护信息",
            "icon": "i-heroicons-cog-6-tooth",
            "fields": [
              {
                "id": "field-5",
                "field_code": "custodian",
                "span": 12,
                "label": "责任人"
              }
            ]
          }
        ]
      }
    ],
    "actions": [                         // 布局级操作按钮
      {
        "code": "submit",
        "label": "提交",
        "type": "primary",
        "position": "bottom-right"
      },
      {
        "code": "cancel",
        "label": "取消",
        "type": "default",
        "position": "bottom-right"
      }
    ],
    "events": {                          // 布局事件绑定
      "on_load": "",                    // 加载时执行脚本
      "before_submit": "",              // 提交前验证脚本
      "after_submit": ""                // 提交后执行脚本
    }
  },
  "created_by": "user_uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "modified_at": "2024-01-15T10:30:00Z",
  "parent_version": null,               // 父版本号（用于版本追溯）
  "organization": "org_uuid"
}
```

### 4.2 布局组件类型

#### 4.2.1 区块 (Section)
```javascript
{
  "type": "section",
  "title": "基本信息",
  "collapsible": true,
  "collapsed": false,
  "columns": 2,               // 列数: 1 | 2 | 3 | 4
  "border": false,            // 默认不显示边框
  "render_as_card": false,    // 默认不作为卡片渲染
  "background_color": "transparent",
  "icon": "i-heroicons-document-text",
  "show_title": true,
  "fields": []                // 字段列表
}
```

#### 4.2.2 标签页 (Tab)
```javascript
{
  "type": "tab",
  "position": "top",          // top | left | right | bottom
  "type_style": "card",       // card | border
  "tabs": [
    {
      "title": "标签1",
      "icon": "i-heroicons-document-text",
      "lazy": true,
      "closable": false,
      "fields": []
    }
  ]
}
```

#### 4.2.3 分栏 (Column)
```javascript
{
  "type": "column",
  "columns": [                // 分栏配置
    {
      "span": 12,             // 列宽 (1-24)
      "fields": []
    },
    {
      "span": 12,
      "fields": []
    }
  ],
  "gutter": 20                // 栏间距 (px)
}
```

#### 4.2.4 分隔线 (Divider)
```javascript
{
  "type": "divider",
  "content": "分割文本",       // 可选
  "content_position": "left", // left | center | right
  "border_style": "solid"     // solid | dashed | dotted
}
```

#### 4.2.5 折叠面板 (Collapse)
```javascript
{
  "type": "collapse",
  "accordion": false,         // 是否手风琴模式（每次只展开一个）
  "items": [
    {
      "title": "面板1",
      "icon": "el-icon-document",
      "disabled": false,
      "fields": []
    }
  ]
}
```

---

## 5. 前端组件实现

### 5.1 主组件 (LayoutDesigner.vue)

```vue
<template>
  <div class="h-screen flex flex-col bg-slate-50">
    <!-- 头部导航 -->
    <div class="h-14 border-b bg-white flex items-center px-4 shrink-0">
      <Breadcrumb>
        <BreadcrumbItem>页面配置</BreadcrumbItem>
        <BreadcrumbItem>{{ businessObjectMeta.label }}</BreadcrumbItem>
        <BreadcrumbItem>{{ layoutTypeMeta.label }}</BreadcrumbItem>
      </Breadcrumb>
    </div>

    <!-- 工具栏 -->
    <DesignerToolbar
      :can-undo="canUndo"
      :can-redo="canRedo"
      :has-changes="hasChanges"
      @save="handleSave"
      @publish="handlePublish"
      @preview="handlePreview"
      @undo="handleUndo"
      @redo="handleRedo"
      @clear="handleClear"
      @import="handleImport"
      @export="handleExport"
    />

    <!-- 主体区域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 组件面板 -->
      <ComponentPanel
        class="w-60 border-r bg-white"
        :fields="availableFields"
        :components="layoutComponents"
        :used-field-codes="usedFieldCodes"
        @drag-start="handleComponentDragStart"
      />

      <!-- 画布区域 -->
      <CanvasArea
        class="flex-1 bg-slate-100 overflow-auto p-8"
        :config="layoutConfig"
        :selected-id="selectedElementId"
        :preview-mode="previewMode"
        :responsive-mode="responsiveMode"
        @element-select="handleElementSelect"
        @element-update="handleElementUpdate"
        @element-delete="handleElementDelete"
        @drop="handleDrop"
        @reorder="handleReorder"
      />

      <!-- 属性面板 -->
      <PropertyPanel
        class="w-80 border-l bg-white"
        :element="selectedElement"
        :field-defs="fieldDefinitions"
        @property-change="handlePropertyChange"
      />
    </div>

    <!-- 预览对话框 (Shadcn Dialog) -->
    <Dialog v-model:open="previewVisible">
      <DialogContent class="max-w-6xl h-[90vh]">
        <DialogHeader>
          <DialogTitle>布局预览</DialogTitle>
        </DialogHeader>
        <LayoutPreview
          :config="layoutConfig"
          :business-object="businessObject"
          :responsive-mode="previewResponsiveMode"
          @mode-change="previewResponsiveMode = $event"
        />
      </DialogContent>
    </Dialog>

    <!-- 发布对话框 -->
    <PublishDialog
      v-model="publishVisible"
      :layout="currentLayout"
      @confirm="handlePublishConfirm"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useToast } from '@/components/ui/toast/use-toast'
import {
  Breadcrumb,
  BreadcrumbItem
} from '@/components/ui/breadcrumb'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'
import DesignerToolbar from './components/DesignerToolbar.vue'
import ComponentPanel from './components/ComponentPanel.vue'
import CanvasArea from './components/CanvasArea.vue'
import PropertyPanel from './components/PropertyPanel.vue'
import LayoutPreview from './components/LayoutPreview.vue'
import PublishDialog from './components/PublishDialog.vue'
import { useLayoutHistory } from './composables/useLayoutHistory'
import { api } from '@/api'

const route = useRoute()
const { toast } = useToast()

// 状态管理
const layoutId = ref(route.params.id || '')
const businessObject = ref(route.query.object || 'Asset')
const layoutType = ref(route.query.type || 'form')
const layoutConfig = ref({ sections: [] })
const selectedElementId = ref('')
const previewMode = ref(false)
const previewResponsiveMode = ref('desktop')
const publishVisible = ref(false)

// 撤销/重做历史
const {
  canUndo,
  canRedo,
  hasChanges,
  pushHistory,
  undo,
  redo
} = useLayoutHistory(layoutConfig)

// 计算属性
const businessObjectMeta = computed(() => {
  const objects = {
    'Asset': { label: '资产管理' },
    'InventoryTask': { label: '盘点任务' },
    'ProcurementRequest': { label: '采购申请' }
  }
  return objects[businessObject.value] || { label: businessObject.value }
})

const layoutTypeMeta = computed(() => {
  const types = {
    'form': { label: '表单布局' },
    'list': { label: '列表布局' },
    'detail': { label: '详情布局' }
  }
  return types[layoutType.value] || { label: layoutType.value }
})

const selectedElement = computed(() => {
  return findElementById(layoutConfig.value, selectedElementId.value)
})

const usedFieldCodes = computed(() => {
  const codes = new Set()
  traverseLayout(layoutConfig.value, (element) => {
    if (element.field_code) {
      codes.add(element.field_code)
    }
  })
  return Array.from(codes)
})

// 数据获取
const availableFields = ref([])
const fieldDefinitions = ref({})
const layoutComponents = [
  { type: 'section', label: '区块', icon: 'el-icon-folder' },
  { type: 'tab', label: '标签页', icon: 'el-icon-files' },
  { type: 'column', label: '分栏', icon: 'el-icon-s-grid' },
  { type: 'divider', label: '分隔线', icon: 'el-icon-minus' },
  { type: 'collapse', label: '折叠面板', icon: 'el-icon-s-fold' }
]

const currentLayout = ref(null)

// 方法
const loadLayoutData = async () => {
  try {
    // 加载字段定义
    const fieldsRes = await api.system.fieldDefinitions.list({
      business_object: businessObject.value
    })
    availableFields.value = fieldsRes.data.results
    fieldDefinitions.value = Object.fromEntries(
      fieldsRes.data.results.map(f => [f.code, f])
    )

    // 加载布局配置
    if (layoutId.value) {
      const layoutRes = await api.system.pageLayouts.retrieve(layoutId.value)
      currentLayout.value = layoutRes.data
      layoutConfig.value = layoutRes.data.config
      pushHistory(layoutConfig.value)
    } else {
      // 新建布局：初始化默认配置
      layoutConfig.value = createDefaultLayout()
      pushHistory(layoutConfig.value)
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  }
}

const handleSave = async () => {
  try {
    // 验证配置
    const validation = validateLayoutSchema(layoutConfig.value)
    if (!validation.valid) {
      ElMessage.error(`布局配置无效: ${validation.errors.join(', ')}`)
      return
    }

    const payload = {
      business_object: businessObject.value,
      layout_type: layoutType.value,
      config: layoutConfig.value,
      status: 'draft'
    }

    let response
    if (layoutId.value) {
      response = await api.system.pageLayouts.saveDraft(layoutId.value, payload)
    } else {
      response = await api.system.pageLayouts.create(payload)
      layoutId.value = response.data.id
    }

    ElMessage.success('草稿保存成功')
    hasChanges.value = false
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  }
}

const handlePublish = () => {
  publishVisible.value = true
}

const handlePublishConfirm = async (data) => {
  try {
    await api.system.pageLayouts.publish(layoutId.value, {
      comment: data.comment,
      require_approval: data.requireApproval
    })

    ElMessage.success('布局发布成功')
    publishVisible.value = false
  } catch (error) {
    ElMessage.error('发布失败')
    console.error(error)
  }
}

const handlePreview = () => {
  previewVisible.value = true
}

const handleUndo = () => {
  undo()
}

const handleRedo = () => {
  redo()
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空当前布局吗？此操作不可撤销！',
      '清空确认',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )

    layoutConfig.value = { sections: [] }
    pushHistory(layoutConfig.value)
    ElMessage.success('布局已清空')
  } catch (error) {
    // 用户取消
  }
}

const handleImport = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e) => {
    try {
      const file = e.target.files[0]
      const text = await file.text()
      const config = JSON.parse(text)

      const validation = validateLayoutSchema(config)
      if (!validation.valid) {
        ElMessage.error(`布局配置无效: ${validation.errors.join(', ')}`)
        return
      }

      layoutConfig.value = config
      pushHistory(layoutConfig.value)
      ElMessage.success('布局导入成功')
    } catch (error) {
      ElMessage.error('导入失败')
      console.error(error)
    }
  }
  input.click()
}

const handleExport = () => {
  const dataStr = JSON.stringify(layoutConfig.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `layout-${businessObject.value}-${Date.now()}.json`
  link.click()

  URL.revokeObjectURL(url)
  ElMessage.success('布局导出成功')
}

const handleElementSelect = (elementId) => {
  selectedElementId.value = elementId
}

const handleElementUpdate = (elementId, updates) => {
  const element = findElementById(layoutConfig.value, elementId)
  if (element) {
    Object.assign(element, updates)
    pushHistory(layoutConfig.value)
  }
}

const handleElementDelete = (elementId) => {
  deleteElementById(layoutConfig.value, elementId)
  if (selectedElementId.value === elementId) {
    selectedElementId.value = ''
  }
  pushHistory(layoutConfig.value)
}

const handlePropertyChange = (property, value) => {
  if (selectedElement.value) {
    selectedElement.value[property] = value
    pushHistory(layoutConfig.value)
  }
}

const handleDrop = (data) => {
  // 处理拖拽放置
  const { component, targetSectionId, targetIndex } = data

  if (component.type === 'field') {
    // 添加字段
    const section = findElementById(layoutConfig.value, targetSectionId)
    if (section && section.fields) {
      const newField = createFieldElement(component.fieldCode)
      section.fields.splice(targetIndex, 0, newField)
      pushHistory(layoutConfig.value)
    }
  } else {
    // 添加布局组件
    const newComponent = createLayoutComponent(component.type)
    layoutConfig.value.sections.splice(targetIndex, 0, newComponent)
    pushHistory(layoutConfig.value)
  }
}

const handleReorder = (data) => {
  // 处理拖拽排序
  const { fromSection, toSection, fromIndex, toIndex } = data

  const fromSectionEl = findElementById(layoutConfig.value, fromSection)
  const toSectionEl = findElementById(layoutConfig.value, toSection)

  if (fromSectionEl && toSectionEl) {
    const [moved] = fromSectionEl.fields.splice(fromIndex, 1)
    toSectionEl.fields.splice(toIndex, 0, moved)
    pushHistory(layoutConfig.value)
  }
}

// 工具函数
const createDefaultLayout = () => {
  return {
    sections: [
      {
        id: `section-${Date.now()}`,
        type: 'section',
        title: '基本信息',
        collapsible: true,
        collapsed: false,
        columns: 2,
        border: true,
        fields: []
      }
    ]
  }
}

const createFieldElement = (fieldCode) => {
  const fieldDef = fieldDefinitions.value[fieldCode]
  return {
    id: `field-${Date.now()}`,
    field_code: fieldCode,
    label: fieldDef?.label || fieldCode,
    span: 12,
    width: '120px',
    placeholder: `请输入${fieldDef?.label || fieldCode}`,
    required: false,
    readonly: false
  }
}

const createLayoutComponent = (type) => {
  const id = `component-${Date.now()}`
  const templates = {
    section: {
      id,
      type: 'section',
      title: '新区块',
      collapsible: true,
      collapsed: false,
      columns: 2,
      border: true,
      fields: []
    },
    tab: {
      id,
      type: 'tab',
      position: 'top',
      tabs: [
        {
          id: `tab-${Date.now()}`,
          title: '标签页1',
          fields: []
        }
      ]
    },
    divider: {
      id,
      type: 'divider',
      border_style: 'solid'
    },
    collapse: {
      id,
      type: 'collapse',
      accordion: false,
      items: [
        {
          id: `collapse-item-${Date.now()}`,
          title: '面板1',
          fields: []
        }
      ]
    }
  }
  return templates[type] || templates.section
}

const findElementById = (config, id) => {
  // 递归查找元素
  for (const section of config.sections) {
    if (section.id === id) return section

    if (section.fields) {
      for (const field of section.fields) {
        if (field.id === id) return field
      }
    }

    if (section.tabs) {
      for (const tab of section.tabs) {
        if (tab.id === id) return tab
        for (const field of tab.fields || []) {
          if (field.id === id) return field
        }
      }
    }

    if (section.items) {
      for (const item of section.items) {
        if (item.id === id) return item
        for (const field of item.fields || []) {
          if (field.id === id) return field
        }
      }
    }
  }
  return null
}

const deleteElementById = (config, id) => {
  // 递归删除元素
  for (const section of config.sections) {
    if (section.fields) {
      const index = section.fields.findIndex(f => f.id === id)
      if (index !== -1) {
        section.fields.splice(index, 1)
        return true
      }
    }

    if (section.tabs) {
      for (const tab of section.tabs) {
        if (tab.fields) {
          const index = tab.fields.findIndex(f => f.id === id)
          if (index !== -1) {
            tab.fields.splice(index, 1)
            return true
          }
        }
      }
    }
  }
  return false
}

const traverseLayout = (config, callback) => {
  // 递归遍历布局
  for (const section of config.sections) {
    callback(section)
    if (section.fields) {
      section.fields.forEach(callback)
    }
    if (section.tabs) {
      section.tabs.forEach(tab => {
        callback(tab)
        tab.fields?.forEach(callback)
      })
    }
    if (section.items) {
      section.items.forEach(item => {
        callback(item)
        item.fields?.forEach(callback)
      })
    }
  }
}

// 生命周期
onMounted(() => {
  loadLayoutData()
})
</script>

<style scoped lang="scss">
.layout-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;

  .designer-header {
    padding: 16px 24px;
    background-color: #fff;
    border-bottom: 1px solid #dcdfe6;
  }

  .designer-body {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
}
</style>
```

### 5.2 画布区域组件 (CanvasArea.vue)

```vue
<template>
  <div class="canvas-area" :class="responsiveModeClass">
    <!-- 空状态 -->
    <div v-if="isEmpty" class="canvas-empty">
      <el-empty description="拖拽左侧字段到此处开始设计">
        <p class="empty-hint">提示：可以从左侧组件面板拖拽字段或布局组件到画布</p>
      </el-empty>
    </div>

    <!-- 布局渲染 -->
    <div v-else class="canvas-content">
      <div
        v-for="(section, sIndex) in config.sections"
        :key="section.id"
        class="layout-section"
        :class="{ 'is-selected': selectedId === section.id }"
        @click.stop="handleSelect(section.id)"
      >
        <!-- 区块类型 -->
        <SectionBlock
          v-if="section.type === 'section'"
          :config="section"
          :is-selected="selectedId === section.id"
          @select="handleSelect"
          @update="handleUpdate"
        />

        <!-- 标签页类型 -->
        <TabPanel
          v-else-if="section.type === 'tab'"
          :config="section"
          :is-selected="selectedId === section.id"
          @select="handleSelect"
          @update="handleUpdate"
        />

        <!-- 分隔线类型 -->
        <div
          v-else-if="section.type === 'divider'"
          class="layout-divider"
          :class="{ 'is-selected': selectedId === section.id }"
        >
          <el-divider
            :content-position="section.content_position || 'center'"
            :border-style="section.border_style || 'solid'"
          >
            {{ section.content }}
          </el-divider>
        </div>

        <!-- 折叠面板类型 -->
        <CollapsePanel
          v-else-if="section.type === 'collapse'"
          :config="section"
          :is-selected="selectedId === section.id"
          @select="handleSelect"
          @update="handleUpdate"
        />

        <!-- 删除按钮 -->
        <el-button
          v-if="selectedId === section.id"
          class="delete-btn"
          type="danger"
          size="small"
          circle
          @click.stop="handleDelete(section.id)"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>

      <!-- 添加按钮 -->
      <div class="add-section-btn">
        <el-dropdown trigger="click" @command="handleAddSection">
          <el-button type="primary" plain>
            <el-icon><Plus /></el-icon>
            添加区块
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="section">区块</el-dropdown-item>
              <el-dropdown-item command="tab">标签页</el-dropdown-item>
              <el-dropdown-item command="divider">分隔线</el-dropdown-item>
              <el-dropdown-item command="collapse">折叠面板</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 响应式切换 -->
    <div class="responsive-switcher">
      <el-radio-group v-model="responsiveMode" size="small">
        <el-radio-button label="desktop">
          <el-icon><Monitor /></el-icon>
        </el-radio-button>
        <el-radio-button label="tablet">
          <el-icon><Iphone /></el-icon>
        </el-radio-button>
        <el-radio-button label="mobile">
          <el-icon><Cellphone /></el-icon>
        </el-radio-button>
      </el-radio-group>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import SectionBlock from './SectionBlock.vue'
import TabPanel from './TabPanel.vue'
import CollapsePanel from './CollapsePanel.vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  selectedId: {
    type: String,
    default: ''
  },
  previewMode: {
    type: Boolean,
    default: false
  },
  responsiveMode: {
    type: String,
    default: 'desktop'
  }
})

const emit = defineEmits([
  'element-select',
  'element-update',
  'element-delete',
  'add-section'
])

const isEmpty = computed(() => {
  return !props.config.sections || props.config.sections.length === 0
})

const responsiveModeClass = computed(() => {
  return `mode-${props.responsiveMode}`
})

const handleSelect = (elementId) => {
  emit('element-select', elementId)
}

const handleUpdate = (elementId, updates) => {
  emit('element-update', elementId, updates)
}

const handleDelete = (elementId) => {
  emit('element-delete', elementId)
}

const handleAddSection = (type) => {
  emit('add-section', type)
}
</script>

<style scoped lang="scss">
.canvas-area {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: #f5f7fa;
  position: relative;

  &.mode-tablet {
    max-width: 768px;
    margin: 0 auto;
  }

  &.mode-mobile {
    max-width: 375px;
    margin: 0 auto;
  }

  .canvas-empty {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;

    .empty-hint {
      margin-top: 16px;
      color: #909399;
      font-size: 14px;
    }
  }

  .canvas-content {
    min-height: 400px;

    .layout-section {
      position: relative;
      margin-bottom: 16px;

      &.is-selected {
        outline: 2px solid #409eff;
        outline-offset: 2px;
      }

      .delete-btn {
        position: absolute;
        top: -12px;
        right: -12px;
        z-index: 10;
      }
    }

    .add-section-btn {
      text-align: center;
      margin-top: 24px;
    }
  }

  .responsive-switcher {
    position: fixed;
    bottom: 24px;
    right: 360px;
    background-color: #fff;
    padding: 8px;
    border-radius: 4px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  }
}

.layout-divider {
  &.is-selected {
    outline: 2px solid #409eff;
    outline-offset: 4px;
  }
}
</style>
```

### 5.3 属性面板组件 (PropertyPanel.vue)

```vue
<template>
  <div class="property-panel">
    <div class="panel-header">
      <h3>属性配置</h3>
    </div>

    <div v-if="!element" class="panel-empty">
      <el-empty description="请选择一个元素以配置属性" :image-size="80" />
    </div>

    <div v-else class="panel-content">
      <!-- 字段属性 -->
      <div v-if="element.field_code" class="property-group">
        <div class="group-title">字段属性</div>

        <el-form label-width="80px" size="small">
          <el-form-item label="字段名称">
            <el-input v-model="localProps.label" @input="handleUpdate('label', localProps.label)" />
          </el-form-item>

          <el-form-item label="标签宽度">
            <el-input
              v-model="localProps.width"
              placeholder="如: 120px"
              @input="handleUpdate('width', localProps.width)"
            />
          </el-form-item>

          <el-form-item label="列宽占比">
            <el-slider
              v-model="localProps.span"
              :min="1"
              :max="24"
              :marks="{ 6: '1/4', 12: '1/2', 24: '全宽' }"
              @change="handleUpdate('span', localProps.span)"
            />
          </el-form-item>

          <el-form-item label="占位符">
            <el-input
              v-model="localProps.placeholder"
              @input="handleUpdate('placeholder', localProps.placeholder)"
            />
          </el-form-item>

          <el-form-item label="默认值">
            <el-input
              v-model="localProps.default_value"
              @input="handleUpdate('default_value', localProps.default_value)"
            />
          </el-form-item>

          <el-form-item label="帮助文本">
            <el-input
              v-model="localProps.help_text"
              type="textarea"
              :rows="2"
              @input="handleUpdate('help_text', localProps.help_text)"
            />
          </el-form-item>

          <el-form-item label="必填">
            <el-switch
              v-model="localProps.required"
              @change="handleUpdate('required', localProps.required)"
            />
          </el-form-item>

          <el-form-item label="只读">
            <el-switch
              v-model="localProps.readonly"
              @change="handleUpdate('readonly', localProps.readonly)"
            />
          </el-form-item>

          <el-form-item label="隐藏">
            <el-switch
              v-model="localProps.visible"
              :active-value="false"
              :inactive-value="true"
              @change="handleUpdate('visible', localProps.visible)"
            />
          </el-form-item>

          <el-form-item label="自定义样式">
            <el-input
              v-model="localProps.custom_class"
              placeholder="css-class-name"
              @input="handleUpdate('custom_class', localProps.custom_class)"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 区块属性 -->
      <div v-else-if="element.type === 'section'" class="property-group">
        <div class="group-title">区块属性</div>

        <el-form label-width="80px" size="small">
          <el-form-item label="标题">
            <el-input
              v-model="localProps.title"
              @input="handleUpdate('title', localProps.title)"
            />
          </el-form-item>

          <el-form-item label="列数">
            <el-radio-group
              v-model="localProps.columns"
              @change="handleUpdate('columns', localProps.columns)"
            >
              <el-radio-button :label="1">1列</el-radio-button>
              <el-radio-button :label="2">2列</el-radio-button>
              <el-radio-button :label="3">3列</el-radio-button>
              <el-radio-button :label="4">4列</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="可折叠">
            <el-switch
              v-model="localProps.collapsible"
              @change="handleUpdate('collapsible', localProps.collapsible)"
            />
          </el-form-item>

          <el-form-item label="默认折叠">
            <el-switch
              v-model="localProps.collapsed"
              @change="handleUpdate('collapsed', localProps.collapsed)"
            />
          </el-form-item>

          <el-form-item label="显示边框">
            <el-switch
              v-model="localProps.border"
              @change="handleUpdate('border', localProps.border)"
            />
          </el-form-item>

          <el-form-item label="背景色">
            <el-color-picker
              v-model="localProps.background_color"
              @change="handleUpdate('background_color', localProps.background_color)"
            />
          </el-form-item>

          <el-form-item label="图标">
            <el-select
              v-model="localProps.icon"
              placeholder="选择图标"
              @change="handleUpdate('icon', localProps.icon)"
            >
              <el-option label="文档" value="el-icon-document" />
              <el-option label="文件夹" value="el-icon-folder" />
              <el-option label="信息" value="el-icon-info" />
              <el-option label="设置" value="el-icon-setting" />
            </el-select>
          </el-form-item>

          <el-form-item label="自定义样式">
            <el-input
              v-model="localProps.custom_class"
              @input="handleUpdate('custom_class', localProps.custom_class)"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 标签页属性 -->
      <div v-else-if="element.type === 'tab'" class="property-group">
        <div class="group-title">标签页属性</div>

        <el-form label-width="80px" size="small">
          <el-form-item label="位置">
            <el-radio-group
              v-model="localProps.position"
              @change="handleUpdate('position', localProps.position)"
            >
              <el-radio-button label="top">顶部</el-radio-button>
              <el-radio-button label="left">左侧</el-radio-button>
              <el-radio-button label="right">右侧</el-radio-button>
              <el-radio-button label="bottom">底部</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="样式类型">
            <el-radio-group
              v-model="localProps.type_style"
              @change="handleUpdate('type_style', localProps.type_style)"
            >
              <el-radio-button label="card">卡片</el-radio-button>
              <el-radio-button label="border">边框</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <!-- 操作按钮 -->
      <div class="panel-actions">
        <el-button type="danger" size="small" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除元素
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  element: {
    type: Object,
    default: null
  },
  fieldDefs: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['property-change', 'delete'])

const localProps = ref({})

// 监听元素变化，同步到本地
watch(
  () => props.element,
  (newElement) => {
    if (newElement) {
      localProps.value = { ...newElement }
    }
  },
  { immediate: true, deep: true }
)

const handleUpdate = (property, value) => {
  emit('property-change', property, value)
}

const handleDelete = () => {
  emit('delete')
}
</script>

<style scoped lang="scss">
.property-panel {
  width: 320px;
  background-color: #fff;
  border-left: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;

  .panel-header {
    padding: 16px;
    border-bottom: 1px solid #dcdfe6;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 500;
    }
  }

  .panel-empty {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }

  .panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 16px;

    .property-group {
      margin-bottom: 24px;

      .group-title {
        font-size: 14px;
        font-weight: 500;
        color: #303133;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #ebeef5;
      }
    }

    .panel-actions {
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #ebeef5;
      text-align: center;
    }
  }
}
</style>
```

---

## 6. 后端 API 设计

### 6.1 PageLayout 模型

```python
# apps/system/models.py
from django.db import models
from apps.common.models import BaseModel

class PageLayout(BaseModel):
    """页面布局模型"""

    LAYOUT_TYPE_CHOICES = [
        ('form', '表单布局'),
        ('list', '列表布局'),
        ('detail', '详情布局'),
    ]

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    # 业务对象（关联 BusinessObject）
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='layouts',
        verbose_name='业务对象'
    )

    # 布局类型
    layout_type = models.CharField(
        max_length=20,
        choices=LAYOUT_TYPE_CHOICES,
        verbose_name='布局类型'
    )

    # 布局名称
    layout_name = models.CharField(
        max_length=200,
        verbose_name='布局名称'
    )

    # 布局描述
    description = models.TextField(
        blank=True,
        verbose_name='布局描述'
    )

    # 布局配置（JSONB）
    config = models.JSONField(
        default=dict,
        verbose_name='布局配置'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )

    # 版本号
    version = models.CharField(
        max_length=20,
        default='1.0.0',
        verbose_name='版本号'
    )

    # 父版本（用于版本追溯）
    parent_version = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='父版本号'
    )

    # 是否为默认布局
    is_default = models.BooleanField(
        default=False,
        verbose_name='是否默认布局'
    )

    # 发布时间
    published_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='发布时间'
    )

    # 发布人
    published_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='published_layouts',
        verbose_name='发布人'
    )

    class Meta:
        db_table = 'system_page_layout'
        verbose_name = '页面布局'
        verbose_name_plural = '页面布局'
        ordering = ['-created_at']
        unique_together = [['business_object', 'layout_type', 'organization']]

    def __str__(self):
        return f"{self.layout_name} ({self.get_layout_type_display()})"

    def publish(self, user):
        """发布布局"""
        from django.utils import timezone

        # 更新状态
        self.status = 'published'
        self.published_at = timezone.now()
        self.published_by = user

        # 生成新版本号
        if self.parent_version:
            major, minor, patch = self.parent_version.split('.')
            self.version = f"{major}.{int(minor) + 1}.0"
        else:
            self.version = "1.0.0"

        self.save()

        # 记录发布历史
        LayoutHistory.objects.create(
            layout=self,
            version=self.version,
            config_snapshot=self.config,
            published_by=user,
            action='publish'
        )


class LayoutHistory(BaseModel):
    """布局版本历史"""

    layout = models.ForeignKey(
        PageLayout,
        on_delete=models.CASCADE,
        related_name='histories',
        verbose_name='布局'
    )

    version = models.CharField(
        max_length=20,
        verbose_name='版本号'
    )

    config_snapshot = models.JSONField(
        verbose_name='配置快照'
    )

    published_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name='发布人'
    )

    action = models.CharField(
        max_length=20,
        choices=[
            ('publish', '发布'),
            ('update', '更新'),
            ('rollback', '回滚'),
        ],
        verbose_name='操作类型'
    )

    class Meta:
        db_table = 'system_layout_history'
        verbose_name = '布局历史'
        verbose_name_plural = '布局历史'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.layout.layout_name} - {self.version}"
```

### 6.2 PageLayout Serializer

```python
# apps/system/serializers.py
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import PageLayout, LayoutHistory

class PageLayoutSerializer(BaseModelSerializer):
    """页面布局序列化器"""

    published_by_info = serializers.SerializerMethodField()
    business_object_name = serializers.SerializerMethodField()
    layout_type_display = serializers.CharField(source='get_layout_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = PageLayout
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_name',
            'layout_type',
            'layout_type_display',
            'layout_name',
            'description',
            'config',
            'status',
            'status_display',
            'version',
            'parent_version',
            'is_default',
            'published_at',
            'published_by',
            'published_by_info',
        ]

    def get_business_object_name(self, obj):
        return obj.business_object.name if obj.business_object else ''

    def get_published_by_info(self, obj):
        if obj.published_by:
            return {
                'id': str(obj.published_by.id),
                'username': obj.published_by.username,
                'full_name': obj.published_by.get_full_name()
            }
        return None

    def validate_config(self, value):
        """验证布局配置"""
        from .validators import validate_layout_config
        validate_layout_config(value)
        return value


class LayoutHistorySerializer(BaseModelSerializer):
    """布局历史序列化器"""

    published_by_info = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LayoutHistory
        fields = BaseModelSerializer.Meta.fields + [
            'layout',
            'version',
            'config_snapshot',
            'action',
            'action_display',
            'published_by',
            'published_by_info',
        ]

    def get_published_by_info(self, obj):
        if obj.published_by:
            return {
                'id': str(obj.published_by.id),
                'username': obj.published_by.username,
                'full_name': obj.published_by.get_full_name()
            }
        return None
```

### 6.3 PageLayout ViewSet

```python
# apps/system/viewsets.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from .models import PageLayout, LayoutHistory
from .serializers import PageLayoutSerializer, LayoutHistorySerializer
from .permissions import LayoutPermission


class PageLayoutViewSet(BaseModelViewSet):
    """页面布局视图集"""

    queryset = PageLayout.objects.all()
    serializer_class = PageLayoutSerializer
    permission_classes = [LayoutPermission]

    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()

        # 过滤参数
        business_object = self.request.query_params.get('business_object')
        layout_type = self.request.query_params.get('layout_type')
        status_param = self.request.query_params.get('status')
        is_default = self.request.query_params.get('is_default')

        if business_object:
            queryset = queryset.filter(business_object__code=business_object)
        if layout_type:
            queryset = queryset.filter(layout_type=layout_type)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if is_default:
            queryset = queryset.filter(is_default=is_default.lower() == 'true')

        return queryset

    def perform_create(self, serializer):
        """创建时自动设置组织"""
        serializer.save(
            organization_id=self.request.user.organization_id,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def save_draft(self, request, pk=None):
        """保存草稿"""
        layout = self.get_object()

        # 更新配置
        layout.config = request.data.get('config', layout.config)
        layout.status = 'draft'
        layout.modified_at = timezone.now()
        layout.save(update_fields=['config', 'status', 'modified_at'])

        serializer = self.get_serializer(layout)
        return Response(BaseResponse.success(
            message='草稿保存成功',
            data=serializer.data
        ))

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布布局"""
        layout = self.get_object()

        # 验证配置
        from .validators import validate_layout_config
        try:
            validate_layout_config(request.data.get('config', layout.config))
        except ValueError as e:
            return Response(BaseResponse.error(
                message='布局配置验证失败',
                details={'config': str(e)}
            ), status=status.HTTP_400_BAD_REQUEST)

        # 如果已有发布版本，保存父版本
        if layout.status == 'published':
            layout.parent_version = layout.version

        # 更新配置并发布
        layout.config = request.data.get('config', layout.config)
        layout.publish(request.user)

        serializer = self.get_serializer(layout)
        return Response(BaseResponse.success(
            message='布局发布成功',
            data=serializer.data
        ))

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """获取版本历史"""
        layout = self.get_object()
        histories = layout.histories.all()

        page = self.paginate_queryset(histories)
        if page is not None:
            serializer = LayoutHistorySerializer(page, many=True)
            return self.get_paginated_response({
                'success': True,
                'data': serializer.data
            })

        serializer = LayoutHistorySerializer(histories, many=True)
        return Response(BaseResponse.success(data=serializer.data))

    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """回滚到指定版本"""
        layout = self.get_object()
        version = request.data.get('version')

        if not version:
            return Response(BaseResponse.error(
                message='请指定要回滚的版本号'
            ), status=status.HTTP_400_BAD_REQUEST)

        # 查找历史版本
        try:
            history = LayoutHistory.objects.get(layout=layout, version=version)
        except LayoutHistory.DoesNotExist:
            return Response(BaseResponse.error(
                message=f'版本 {version} 不存在'
            ), status=status.HTTP_404_NOT_FOUND)

        # 回滚配置
        old_config = layout.config
        old_version = layout.version

        layout.config = history.config_snapshot
        layout.parent_version = old_version
        layout.version = f"{version}-rollback"
        layout.status = 'draft'
        layout.save()

        # 记录回滚操作
        LayoutHistory.objects.create(
            layout=layout,
            version=layout.version,
            config_snapshot=layout.config,
            published_by=request.user,
            action='rollback'
        )

        serializer = self.get_serializer(layout)
        return Response(BaseResponse.success(
            message=f'已回滚到版本 {version}',
            data=serializer.data
        ))

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设置为默认布局"""
        layout = self.get_object()

        # 取消同类型其他默认布局
        PageLayout.objects.filter(
            business_object=layout.business_object,
            layout_type=layout.layout_type,
            organization=layout.organization,
            is_default=True
        ).update(is_default=False)

        # 设置当前布局为默认
        layout.is_default = True
        layout.save(update_fields=['is_default'])

        serializer = self.get_serializer(layout)
        return Response(BaseResponse.success(
            message='已设置为默认布局',
            data=serializer.data
        ))

    @action(detail=False, methods=['get'])
    def default(self, request):
        """获取默认布局"""
        business_object = request.query_params.get('business_object')
        layout_type = request.query_params.get('layout_type')

        if not business_object or not layout_type:
            return Response(BaseResponse.error(
                message='缺少必要参数: business_object, layout_type'
            ), status=status.HTTP_400_BAD_REQUEST)

        try:
            layout = PageLayout.objects.get(
                business_object__code=business_object,
                layout_type=layout_type,
                organization=request.user.organization,
                is_default=True,
                status='published'
            )
            serializer = self.get_serializer(layout)
            return Response(BaseResponse.success(data=serializer.data))
        except PageLayout.DoesNotExist:
            return Response(BaseResponse.error(
                message='未找到默认布局'
            ), status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def import_config(self, request):
        """导入布局配置"""
        import json

        config_str = request.data.get('config')
        if not config_str:
            return Response(BaseResponse.error(
                message='缺少配置数据'
            ), status=status.HTTP_400_BAD_REQUEST)

        try:
            config = json.loads(config_str)
        except json.JSONDecodeError:
            return Response(BaseResponse.error(
                message='配置数据格式错误'
            ), status=status.HTTP_400_BAD_REQUEST)

        # 验证配置
        from .validators import validate_layout_config
        try:
            validate_layout_config(config)
        except ValueError as e:
            return Response(BaseResponse.error(
                message='布局配置验证失败',
                details={'config': str(e)}
            ), status=status.HTTP_400_BAD_REQUEST)

        # 创建新布局
        layout = PageLayout.objects.create(
            business_object_id=request.data.get('business_object'),
            layout_type=request.data.get('layout_type'),
            layout_name=request.data.get('layout_name', '导入的布局'),
            config=config,
            organization=request.user.organization,
            created_by=request.user
        )

        serializer = self.get_serializer(layout)
        return Response(BaseResponse.success(
            message='布局导入成功',
            data=serializer.data
        ), status=status.HTTP_201_CREATED)
```

### 6.4 布局配置验证器

```python
# apps/system/validators.py
from rest_framework.exceptions import ValidationError

def validate_layout_config(config):
    """验证布局配置结构"""

    if not isinstance(config, dict):
        raise ValidationError("配置必须是 JSON 对象")

    if 'sections' not in config:
        raise ValidationError("缺少 sections 字段")

    if not isinstance(config['sections'], list):
        raise ValidationError("sections 必须是数组")

    for section in config['sections']:
        validate_section(section)

    # 验证操作按钮（可选）
    if 'actions' in config:
        if not isinstance(config['actions'], list):
            raise ValidationError("actions 必须是数组")

        for action in config['actions']:
            if 'code' not in action or 'label' not in action:
                raise ValidationError("action 必须包含 code 和 label")


def validate_section(section):
    """验证区块配置"""

    if 'id' not in section:
        raise ValidationError("section 必须包含 id")

    if 'type' not in section:
        raise ValidationError("section 必须包含 type")

    section_type = section['type']

    if section_type == 'section':
        validate_basic_section(section)
    elif section_type == 'tab':
        validate_tab_section(section)
    elif section_type == 'divider':
        validate_divider_section(section)
    elif section_type == 'collapse':
        validate_collapse_section(section)
    else:
        raise ValidationError(f"不支持的 section 类型: {section_type}")


def validate_basic_section(section):
    """验证基础区块"""
    if 'fields' in section:
        if not isinstance(section['fields'], list):
            raise ValidationError("fields 必须是数组")

        for field in section['fields']:
            validate_field(field)


def validate_tab_section(section):
    """验证标签页区块"""
    if 'tabs' not in section:
        raise ValidationError("tab 类型必须包含 tabs")

    if not isinstance(section['tabs'], list):
        raise ValidationError("tabs 必须是数组")

    for tab in section['tabs']:
        if 'id' not in tab or 'title' not in tab:
            raise ValidationError("tab 必须包含 id 和 title")

        if 'fields' in tab:
            if not isinstance(tab['fields'], list):
                raise ValidationError("fields 必须是数组")

            for field in tab['fields']:
                validate_field(field)


def validate_divider_section(section):
    """验证分隔线区块"""
    # 分隔线只需验证 id 和 type
    pass


def validate_collapse_section(section):
    """验证折叠面板区块"""
    if 'items' not in section:
        raise ValidationError("collapse 类型必须包含 items")

    if not isinstance(section['items'], list):
        raise ValidationError("items 必须是数组")

    for item in section['items']:
        if 'id' not in item or 'title' not in item:
            raise ValidationError("collapse item 必须包含 id 和 title")

        if 'fields' in item:
            if not isinstance(item['fields'], list):
                raise ValidationError("fields 必须是数组")

            for field in item['fields']:
                validate_field(field)


def validate_field(field):
    """验证字段配置"""
    required_fields = ['id', 'field_code', 'label', 'span']

    for required_field in required_fields:
        if required_field not in field:
            raise ValidationError(f"field 必须包含 {required_field}")

    if not isinstance(field['span'], int) or field['span'] < 1 or field['span'] > 24:
        raise ValidationError("field.span 必须是 1-24 之间的整数")
```

### 6.5 URL 配置

```python
# apps/system/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import PageLayoutViewSet

router = DefaultRouter()
router.register(r'page-layouts', PageLayoutViewSet, basename='page-layout')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## 7. 权限控制

### 7.1 布局权限定义

```python
# apps/system/permissions.py
from rest_framework import permissions

class LayoutPermission(permissions.BasePermission):
    """布局权限控制"""

    def has_permission(self, request, view):
        """基础权限检查"""
        if not request.user or not request.user.is_authenticated:
            return False

        # 管理员拥有所有权限
        if request.user.is_admin:
            return True

        # 查看权限：所有认证用户
        if view.action in ['list', 'retrieve', 'default', 'versions']:
            return True

        # 编辑权限：需要布局编辑权限
        if view.action in ['create', 'update', 'partial_update', 'save_draft']:
            return self._check_permission(request.user, 'edit_layout')

        # 发布权限：需要布局发布权限
        if view.action in ['publish', 'set_default']:
            return self._check_permission(request.user, 'publish_layout')

        # 删除权限：需要布局删除权限
        if view.action in ['destroy', 'rollback']:
            return self._check_permission(request.user, 'delete_layout')

        return False

    def has_object_permission(self, request, view, obj):
        """对象级权限检查"""
        # 管理员拥有所有权限
        if request.user.is_admin:
            return True

        # 只能操作本组织的布局
        if obj.organization_id != request.user.organization_id:
            return False

        # 编辑/发布权限检查
        if view.action in ['update', 'partial_update', 'save_draft', 'publish']:
            return self._check_permission(request.user, 'edit_layout')

        # 删除权限检查
        if view.action in ['destroy', 'rollback']:
            return self._check_permission(request.user, 'delete_layout')

        return True

    def _check_permission(self, user, permission_code):
        """检查用户是否拥有指定权限"""
        # 从用户权限中查找
        return user.permissions.filter(
            code=permission_code,
            organization=user.organization
        ).exists()
```

### 7.2 权限配置示例

```python
# 权限初始化数据
permissions = [
    {
        'code': 'view_layout',
        'name': '查看布局',
        'description': '查看页面布局配置'
    },
    {
        'code': 'edit_layout',
        'name': '编辑布局',
        'description': '创建和编辑页面布局'
    },
    {
        'code': 'publish_layout',
        'name': '发布布局',
        'description': '发布页面布局到生产环境'
    },
    {
        'code': 'delete_layout',
        'name': '删除布局',
        'description': '删除页面布局'
    }
]
```

---

## 8. 设计器使用流程

### 8.1 完整操作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     布局设计器使用流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 管理员登录系统                                               │
│     ↓                                                           │
│  2. 进入"系统管理" > "页面配置"                                  │
│     ↓                                                           │
│  3. 点击"新建布局"按钮                                           │
│     ↓                                                           │
│  4. 选择业务对象（资产/盘点任务/采购申请...）                     │
│     ↓                                                           │
│  5. 选择布局类型（表单/列表/详情）                                │
│     ↓                                                           │
│  6. 进入布局设计器                                               │
│     ↓                                                           │
│  7. 从左侧组件面板拖拽字段到画布                                  │
│     ↓                                                           │
│  8. 添加区块/标签页进行分组                                      │
│     ↓                                                           │
│  9. 点击字段，在右侧属性面板配置属性                              │
│     ↓                                                           │
│  10. 调整字段顺序（拖拽排序）                                    │
│     ↓                                                           │
│  11. 点击"预览"查看效果                                          │
│     ↓                                                           │
│  12. 点击"保存草稿"（可多次保存）                                 │
│     ↓                                                           │
│  13. 确认无误后，点击"发布"                                      │
│     ↓                                                           │
│  14. 填写发布说明，提交发布                                      │
│     ↓                                                           │
│  15. 布局发布成功，用户可见新布局                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 使用场景示例

#### 场景 1：创建资产表单布局

**目标**：自定义资产新增/编辑表单的布局

**步骤**：
1. 进入"页面配置"，选择业务对象"资产管理"，布局类型"表单布局"
2. 从左侧字段列表拖拽"资产编码"、"资产名称"到"基本信息"区块
3. 添加"详细信息"区块，拖拽"规格型号"、"序列号"等字段
4. 添加"维护信息"标签页，包含"责任人"、"保养日期"等字段
5. 设置"资产编码"字段为必填、只读
6. 预览效果，确认无误后保存草稿
7. 提交发布，发布后所有用户在新增资产时将看到新布局

#### 场景 2：自定义盘点任务列表

**目标**：自定义盘点任务列表的列和筛选器

**步骤**：
1. 进入"页面配置"，选择业务对象"盘点任务"，布局类型"列表布局"
2. 在"列配置"中添加"任务编号"、"盘点状态"、"盘点人"等列
3. 配置列宽度、排序规则
4. 在"筛选器配置"中添加"状态筛选"、"日期范围筛选"
5. 添加"批量操作"按钮（批量分配、批量完成）
6. 保存并发布

---

## 9. 最佳实践与规范

### 9.1 布局设计原则

1. **信息分组合理**
   - 按业务逻辑分组（基本信息/详细信息/维护信息）
   - 每个区块字段数量不超过 8 个
   - 相关字段放在同一区块

2. **字段排列有序**
   - 必填字段优先显示
   - 高频使用字段放在前面
   - 字段按填写顺序排列（从上到下、从左到右）

3. **标签页使用规范**
   - 字段数量超过 12 个时，使用标签页分组
   - 每个标签页字段数量不超过 10 个
   - 标签页标题简洁明了

4. **响应式适配**
   - 移动端默认单列显示
   - 平板端最多 2 列
   - 桌面端最多 4 列

### 9.2 性能优化建议

1. **懒加载标签页**
   - 设置 `lazy: true`，标签页内容仅在切换时加载
   - 减少初始渲染时间

2. **限制历史记录数**
   - 撤销/重做历史栈最多保留 50 条记录
   - 超过限制时自动清理最旧的记录

3. **防抖保存**
   - 自动保存草稿时使用防抖（延迟 2 秒）
   - 避免频繁 API 调用

4. **虚拟滚动**
   - 当字段数量超过 50 个时，使用虚拟滚动
   - 提升渲染性能

### 9.3 错误处理

1. **配置验证失败**
   ```javascript
   const validation = validateLayoutSchema(config)
   if (!validation.valid) {
     ElMessage.error({
       message: '布局配置无效',
       description: validation.errors.join(', ')
     })
     return
   }
   ```

2. **保存失败处理**
   ```javascript
   try {
     await api.system.pageLayouts.saveDraft(id, config)
     ElMessage.success('保存成功')
   } catch (error) {
     if (error.response?.status === 400) {
       ElMessage.error('配置验证失败，请检查后重试')
     } else {
       ElMessage.error('保存失败，请稍后重试')
     }
   }
   ```

3. **网络异常处理**
   - 支持离线编辑（本地存储草稿）
   - 网络恢复后自动同步

---

## 10. 扩展功能（未来规划）

### 10.1 布局模板库
- 预定义常用布局模板
- 一键应用模板
- 模板分享与导入

### 10.2 AI 辅助设计
- 根据业务对象自动推荐布局
- 智能字段分组
- 布局优化建议

### 10.3 多语言支持
- 多语言标签配置
- 动态切换语言

### 10.4 布局审批流程
- 布局发布需要审批
- 审批历史记录
- 审批通知

### 10.5 布局版本对比
- 可视化版本差异
- 版本合并工具
- 版本回滚预览

---

## 11. 总结

布局可视化设计器是 GZEAMS 低代码平台的核心能力之一，通过**拖拽式操作**和**可视化配置**，让管理员无需编写代码即可自定义页面布局。

**核心优势**：
1. **零代码配置**：拖拽式操作，无需编程
2. **实时预览**：所见即所得，立即查看效果
3. **版本管理**：完整的版本历史和回滚机制
4. **权限控制**：细粒度的权限管理，确保安全
5. **响应式设计**：自动适配桌面/平板/移动端

**技术亮点**：
- Vue 3 Composition API + Pinia 状态管理
- Sortable.js 拖拽排序
- JSON Schema 配置验证
- Django REST Framework 后端 API
- PostgreSQL JSONB 存储动态配置

通过布局设计器，企业可以快速定制符合自身业务需求的页面布局，**大幅降低开发成本**，提升系统的灵活性和可维护性。
