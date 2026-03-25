# 布局公共模型分析与优化建议 (Layout Common Model Analysis & Proposal)

## 1. 现状分析 (Current State Analysis)

经过对 `docs/plans/common_base_features/03_layouts` 目录下核心 PRD 的审查，发现当前的布局模型存在以下特征：

### 1.1 分散的模型定义
目前没有一个统一的文档定义"布局公共模型"。相反，每个 PRD 都在开头部分重复定义了各自的依赖：
- **PageLayoutConfig**: 完整定义了 `PageLayout` 数据库模型。
- **LayoutDesigner**: 重复引用了 `BaseModel`, `FieldDefinition` 等概念。
- **ListColumnConfig**: 定义了 `ColumnItem` 和 `ColumnConfig`。
- **FieldConfiguration**: 再次定义了 `FieldDefinition` 和 `PageLayout` 的关系。

### 1.2 核心问题 (Key Issues)
1.  **定义冗余 (Redundancy)**: `PageLayout` 的 JSON Schema 在多个文档中部分重复，且细节可能不一致（例如 `layout_type` 的枚举值在不同文档中可能有细微偏差）。
2.  **字段引用不一致 (Inconsistent Referencing)**:
    -   有的文档用 `field` (string) 引用字段。
    -   有的文档用 `field_code` (string) 引用字段（我们刚更新了 List Config）。
    -   有的文档混合使用了 `label` (在 PageLayout) 和 `name` (在 FieldDefinition)。
3.  **职责模糊 (Ambiguous Responsibility)**:
    -   `FieldDefinition` 应该负责"数据定义"（类型、校验）。
    -   `PageLayout` 应该负责"展示定义"（布局、样式）。
    -   现状是两者在 `readonly`, `visible`, `required` 等属性上存在重叠，缺乏明确的"合并策略"文档。

## 2. 优化建议 (Proposal)

建议创建一个新的核心 PRD：`00_layout_common_models.md`，作为所有布局相关文档的**基石 (Foundation)**。

### 2.1 建立统一公共模型 (Unified Common Models)

**建议在 `00_layout_common_models.md` 中定义以下标准类型，其他文档仅引用：**

```typescript
// 1. 字段引用标准 (Field Reference)
// 所有布局配置引用字段时，必须使用此结构
interface FieldReference {
  field_code: string;       // 唯一标识 (Source of Truth)
  label_override?: string;  // 展示层覆盖名称 (可选)
  // 禁止存储 type, default_value 等属于 FieldDefinition 的属性
}

// 2. 统一可见性规则 (Unified Visibility Rule)
interface VisibilityRule {
  logic: 'and' | 'or';
  conditions: Array<{
    field_code: string;
    operator: 'eq' | 'neq' | 'in' | 'contains' | ...;
    value: any;
  }>;
}

// 3. 统一布局节点抽象 (Abstract Layout Node)
// 用于 Form, Detail, Card 等多种视图
interface LayoutNode {
  id: string;
  type: 'section' | 'tab' | 'grid' | 'field';
  children?: LayoutNode[];
  // ...
}
```

### 2.2 明确"字段驱动"的合并策略 (Merge Strategy)

在公共模型中确立以下原则（并在所有子 PRD 中强制执行）：

| 属性 | FieldDefinition (L0) | PageLayout (L2) | UserConfig (L1) | 最终生效逻辑 |
| :--- | :--- | :--- | :--- | :--- |
| **Label** | `name` (默认) | `label` (覆盖) | `label_override` (覆盖) | `User || Page || Field` |
| **Visible**| `is_hidden` (硬约束) | `visible` (默认) | `visible` (偏好) | `!Field.hidden && (User ?? Page ?? true)` |
| **Sortable**| `enable_sorting` | - | - | 仅由 Field 决定 |
| **Width** | - | `default_width` | `width` | `User ?? Page ?? auto` |

### 2.3 修订现有 PRD (Action Plan)

1.  **创建 `00_layout_common_models.md`**: 提取公共 Schema（Section, Tab, Action, Pagination）。
2.  **瘦身现有文档**:
    -   `page_layout_config.md`: 删除 Schema 定义细节，改为引用 Common Models。
    -   `layout_designer.md`: 移除数据模型描述，专注于 UI/交互规范。
    -   `field_configuration_layout.md`: 专注于字段层面的属性解析，而非重复布局结构。

## 3. 预期收益 (Benefits)

1.  **Single Source of Truth**: 修改一处模型定义，所有文档自动对齐。
2.  **开发一致性**: 前后端对其字段命名 (`field_code` vs `field`) 更加严格，减少转换成本。
3.  **可维护性**: 新增布局类型（如 Kanban, Calendar）时，可直接复用 Common Models 中的 Section/Filter/Action 定义。

---
**等待您的决策**：是否执行此重构计划？
