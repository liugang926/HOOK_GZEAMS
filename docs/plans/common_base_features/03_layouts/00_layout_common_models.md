# 00. 布局公共模型规范 (Layout Common Models)

## 1. 概述

本此文档是所有布局相关 PRD 的**基石 (Foundation)**。它定义了整个低代码平台通用的数据结构、枚举和合并策略。
任何具体的布局配置文件（如 `PageLayout`、`UserColumnConfig`）都必须引用本文档定义的标准模型，禁止私自重新定义核心 Schema。

---

## 2. 核心合并策略 (The "Field-Driven" Strategy)

为了解决字段定义 (`FieldDefinition`) 与布局展示 (`LayoutConfig`) 和用户偏好 (`UserConfig`) 之间的冲突，系统严格遵循以下合并优先级：

### 2.1 属性优先级矩阵

| 属性 | Source (L0: FieldDefinition) | Layout (L2: PageLayout) | Preference (L1: UserConfig) | 最终生效逻辑 (Resolved Value) |
| :--- | :--- | :--- | :--- | :--- |
| **Identity** | `code` | `field_code` | `field_code` | 必须一致 (Join Key) |
| **Label** | `name` (默认) | `label` (覆盖) | `label_override` (覆盖) | `User.label_override ?? Page.label ?? Field.name` |
| **Visible** | `!is_hidden` (硬约束) | `visible` (默认) | `visible` (偏好) | `!Field.is_hidden && (User.visible ?? Page.visible ?? true)` |
| **Sortable** | `enable_sorting` | - | - | `Field.enable_sorting` (仅由后端决定) |
| **Filterable** | `enable_filtering` | - | - | `Field.enable_filtering` (仅由后端决定) |
| **Width** | - | `width` | `width` | `User.width ?? Page.width ?? 'auto'` |
| **Order** | `sort_order` (默认) | `order` (默认) | `order_index` (偏好) | `User.order_index ?? Page.order ?? Field.sort_order` |

**原则**：
1.  **能力 (Capability)** 由 L0 决定（如是否可排序、是否敏感数据）。
2.  **展示 (Presentation)** 由 L1/L2 决定（如宽度、颜色、顺序）。
3.  **约束 (Constraint)** 由 L0 决定（如系统级隐藏、只读）。

---

## 3. 通用数据模型 (Common Schemas)

### 3.1 字段引用 (FieldReference)

所有布局配置中引用字段时，**必须**使用包含 `field_code` 的结构。

```typescript
interface FieldReference {
  /**
   * 字段唯一标识 (对应 FieldDefinition.code)
   * 必须是全小写 snake_case
   */
  field_code: string;

  /**
   * 展示层覆盖名称
   * 如果未定义，前端渲染时自动回退使用 FieldDefinition.name
   */
  label_override?: string;
  
  /**
   * 帮助文本覆盖
   */
  help_text_override?: string;
}
```

### 3.2 可见性规则 (VisibilityRule)

用于控制区段、字段、按钮的动态显示。

```typescript
interface VisibilityRule {
  /**
   * 逻辑连接符 ('and' | 'or')
   * 默认为 'and'
   */
  logic?: 'and' | 'or';

  /**
   * 条件列表
   */
  conditions: Array<{
    /**
     * 目标字段 code
     */
    field_code: string;
    
    /**
     * 操作符
     */
    operator: 'eq' | 'neq' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'not_in' | 'contains' | 'empty' | 'not_empty';
    
    /**
     * 比较值
     */
    value?: any;
  }>;
}
```

### 3.3 验证规则 (ValidationRule)

虽然主要由 `FieldDefinition` 定义，但布局层可追加前端特有的验证（如确认密码）。

```typescript
interface ValidationRule {
  type: 'required' | 'pattern' | 'min' | 'max' | 'email' | 'url' | 'custom';
  
  /**
   * 验证参数 (如 min=10)
   */
  value?: any;
  
  /**
   * 错误提示消息
   */
  message: string;
  
  /**
   * 触发方式
   */
  trigger: 'blur' | 'change' | 'submit';
}
```

### 3.4 操作按钮 (ActionConfig)

用于列表工具栏、行操作、详情页右上角等位置。

```typescript
interface ActionConfig {
  /**
   * 操作唯一标识 (e.g. 'create_asset', 'export_excel')
   */
  key: string;
  
  /**
   * 按钮文本
   */
  label: string;
  
  /**
   * 按钮样式类型
   */
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default' | 'text';
  
  /**
   * 图标 (Shadcn/Lucide icon name, e.g. 'plus', 'trash')
   */
  icon?: string;
  
  /**
   * 权限标识 (e.g. 'asset.create')
   * 如果用户无此权限，按钮自动隐藏
   */
  permission?: string;
  
  /**
   * 二次确认消息
   * 存在则弹出确认框
   */
  confirm_message?: string;
  
  /**
   * 批量操作配置
   */
  web_action?: {
      target: 'api' | 'route' | 'modal' | 'download';
      uri: string; // API URL or Route Path
  }
}
```

### 3.5 分区/分组 (SectionConfig)

用于 `FormLayout`, `DetailLayout` 中的内容分组。

```typescript
interface SectionConfig {
  id: string;
  title: string;
  description?: string;
  
  /**
   * 是否可折叠
   */
  collapsible?: boolean;
  default_collapsed?: boolean;
  
  /**
   * 布局列数 (1 | 2 | 3 | 4)
   * 默认 1
   */
  columns?: number;
  
  /**
   * 子项目 (可能是字段引用，也可能是嵌套的 Section)
   */
  items: Array<FieldReference | SectionConfig>;
  
  visibility_rules?: VisibilityRule[];
}
```

### 3.6 标签页 (TabConfig)

```typescript
interface TabConfig {
  id: string;
  title: string;
  icon?: string;
  
  /**
   * 标签页内的内容通常是 Section 列表
   */
  content: SectionConfig[];
  
  visibility_rules?: VisibilityRule[];
}
```

---

## 4. 布局类型定义 (Layout Types)

### 4.1 表单布局 (FormLayout)

```typescript
interface FormLayoutConfig {
    type: 'form';
    mode: 'single_page' | 'tabs' | 'steps';
    sections: SectionConfig[]; // if mode == single_page
    tabs?: TabConfig[];       // if mode == tabs
    actions: ActionConfig[];  // 底部按钮 (Submit, Cancel)
}
```

### 4.2 列表布局 (ListLayout)

```typescript
interface ListLayoutConfig {
    type: 'list';
    
    // 默认展示的列 (Level 2 Config)
    default_columns: Array<FieldReference & {
        width?: number;
        fixed?: 'left' | 'right';
    }>;
    
    // 工具栏按钮
    toolbar_actions: ActionConfig[];
    
    // 行级按钮
    row_actions: ActionConfig[];
    
    // 默认排序
    default_sort?: {
        field_code: string;
        order: 'asc' | 'desc';
    };
}
```

---

## 5. 前端组件实现建议

前端应当封装 `LayoutRenderer` 组件，输入 Common Model JSON，输出 Shadcn UI 结构。

```vue
<!-- LayoutRenderer.vue -->
<template>
  <component :is="layoutComponent" :config="config" />
</template>
```

所有子组件（FieldRenderer, SectionRenderer）通过 Props 接收来自 Common Model 的配置对象，并结合 `useFieldDefinition(field_code)` 钩子获取 L0 级能力，进行最终渲染决策。
