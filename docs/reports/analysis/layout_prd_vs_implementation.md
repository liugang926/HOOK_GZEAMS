# 前端 PRD 与现有代码实现差异分析报告

**日期**: 2026-01-27
**比较对象**:
- **PRD**: `docs/plans/common_base_features/03_layouts/00_layout_common_models.md`
- **Frontend Code**: `BaseListPage.vue`, `DynamicForm.vue`, `FieldRenderer.vue`, `ColumManager.vue`, `types/common.ts`

## 1. 总体评价

现有的前端代码已经实现了“元数据驱动UI”的核心思想，与 PRD 的大方向（Schema-Driven）保持一致。特别是在 **列表页（BaseListPage）** 和 **表单页（DynamicForm）** 的分离与复用上，结构清晰。

然而，PRD 文档 (`00_layout_common_models.md`) 提出的规范更加严格和抽象，强调 **L0/L1/L2 的严格分层合并策略** 以及 **通用的 LayoutRenderer** 概念。现有代码在命名规范、深度嵌套支持、以及复杂规则引擎（可见性、验证）的实现上，与新 PRD 尚有差距。

## 2. 详细差异点分析

### 2.1 核心数据模型 (Core Schemas)

| 特性 | PRD 规范 | 现有代码 (`types/common.ts` 等) | 差异与风险 |
| :--- | :--- | :--- | :--- |
| **字段标识** | 强制使用 `field_code` (snake_case) | 混用 `prop` (camelCase/snake_case) 和 `code` | **高**: 造成前后端字段映射混乱，需统一为 `field_code`。 |
| **字段定义** | `FieldReference` 包含 `label_override`, `help_text` | `TableColumn` / `FieldConfig` 较为简单 | **中**: 现有 Config 无法完整承载 PRD 定义的覆盖逻辑。 |
| **布局嵌套** | `SectionConfig` 支持递归嵌套 (`items` 含 `SectionConfig`) | `DynamicForm` 中 Section 为扁平结构 (`section.fields` 为 string[]) | **中**: 无法实现复杂的“分组套分组”布局。 |
| **可见性规则** | `VisibilityRule` 支持复杂的 `and/or` 及操作符 | `visible` boolean 标识或简单的 Hook 逻辑 | **高**: 无法支持“当字段A=X时显示字段B”的动态配置化规则。 |

### 2.2 组件架构 (Component Architecture)

- **PRD 建议**: 使用单一的 `LayoutRenderer` 组件，根据 `layout_type` 派发给 `FormRenderer` 或 `ListRenderer`。
- **现有实现**:
    - `BaseListPage`：高度封装的列表组件。
    - `DynamicForm`：高度封装的表单组件。
    - 缺少统一入口：目前页面级别各自分离，缺乏统一的 `PageLayout` 解析入口。

### 2.3 字段渲染 (Field Rendering)

- **FieldRenderer.vue**:
    - **优点**: 已经实现了按类型分发 (`text`, `select`, `date` 等) 和读写模式分离。
    - **缺口**:
        - 缺少对 PRD 中 `ValidationRule` (前端扩展验证) 的支持。
        - 缺少对复杂对象的渲染支持 (PRD 中提到的 `sub_object_layout`)。

### 2.4 用户偏好 (User Config / L1)

- **ColumnManager.vue**: 实现了列的显示/隐藏/排序/宽度调整，并有 `useColumnConfig` 钩子进行持久化。
- **一致性**: 这部分实现与 PRD 的 L1 层级（User Preference）吻合度较高。唯一的差距在于合并逻辑 `applyConfig` 可能需要对照 PRD 的“优先级矩阵”进行微调，确保 `L0(Field).is_hidden` 具有最高优先级（硬约束）。

## 3. 改进建议 (Action Plan)

基于以上分析，建议分阶段进行重构和对齐：

### 阶段一：模型对齐 (Schema Alignment)
1.  **统一类型定义**: 更新 `frontend/src/types/common.ts`，引入 `FieldReference`、`LayoutConfig` 等接口，与 PRD 保持 1:1 一致。
2.  **标准化 Props**: 将 `FieldRenderer` 的 `prop` 改为 `field_code`，并接受完整的 `FieldDefinition` 对象而非简化的 config。

### 阶段二：增强渲染引擎 (Enhanced Engine)
1.  **升级 DynamicForm**:
    - 支持递归 Section (`section.items` 而非 `section.fields`)。
    - 引入 `useVisibility` hook，解析 PRD 格式的 `VisibilityRule` JSON，实现动态联动。
2.  **重构 BaseListPage**: 使用与 PRD 一致的 `ListLayout` 配置对象来驱动 `tableColumns` 的生成，而非混杂的 props。

### 阶段三：统一入口 (Unified Entry)
1.  **开发 LayoutRenderer**: 创建一个顶层组件，只接受 `layoutConfig` JSON 参数，自动判断渲染 Form 还是 List，或者 Dashboard。

## 4. 结论

现有代码是一个良好的基础，涵盖了核心功能。**不需要推倒重来**，而是需要进行**渐进式重构** (Refactor)，主要是**类型定义的标准化**和**规则引擎的增强**。

建议优先着手 **字段标识统一 (`field_code`)** 和 **引入 VisibilityRule引擎**，这两点对用户体验和配置灵活性的提升最为直接。
