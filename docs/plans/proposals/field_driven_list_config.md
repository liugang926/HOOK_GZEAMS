# 方案建议：列表配置与字段管理的深度融合

## 1. 核心问题分析 (Problem Analysis)
当前的 `list_column_configuration.md` 侧重于前端交互和用户偏好存储，但缺乏对后端 `FieldDefinition` 的强约束。这会导致以下问题：
1.  **数据源割裂**：列表配置可能引用了不存在或已废弃的字段。
2.  **能力不一致**：字段定义为“不可排序”或“敏感数据（脱敏）”，但列表配置中未继承这些约束。
3.  **维护成本高**：修改字段名称（Label）后，需要分别更新字段定义和列表配置。

## 2. 融合方案 (Integration Principles)

### 2.1 "Single Source of Truth" (单一数据源)
确立 `FieldDefinition` 为唯一的能力定义源，`ListColumnConfig` 为展示偏好层。

-   **FieldDefinition (后端/全局)**: 定义 `code`, `name`, `type`, `is_sortable`, `is_filterable`, `data_sensitivity`.
-   **ListColumnConfig (前端/用户)**: 定义 `visible`, `width`, `fixed`, `order`.

### 2.2 数据结构融合 (Schema Integration)

建议修改 `ColumnItem` 结构，移除冗余定义，改为引用模式：

**Before (独立定义):**
```typescript
interface ColumnItem {
    field: string;
    label: string; // 容易与 FieldDefinition.name 不一致
    sortable: boolean; // 容易与 FieldDefinition.is_sortable 冲突
    ...
}
```

**After (引用与覆盖):**
```typescript
interface ColumnItem {
    // 1. 引用核心
    field_code: string; // 对应 FieldDefinition.code

    // 2. 覆盖属性 (Optional overrides)
    // 仅当用户想要自定义表头时才设置，否则 === undefined (使用 FieldDefinition.name)
    label_override?: string; 
    
    // 3. 纯展示属性 (Presentation Only)
    visible: boolean;
    width?: number; // 像素值
    fixed?: 'left' | 'right';
    order_index: number; // 排序权重
}
```

### 2.3 自动能力映射 (Automatic Capability Mapping)

前端组件 `ColumnManager` 在渲染时，应动态合并 `FieldDefinition` 和 `ColumnConfig`：

```javascript
const finalColumns = computed(() => {
  return fieldDefinitions.map(def => {
    const userConfig = userColumnPreferences.find(c => c.field_code === def.code);
    
    return {
      field: def.code,
      // 优先显示用户重命名的标签，否则显示系统定义的字段名
      label: userConfig?.label_override ?? def.name,
      // 类型决定了渲染组件 (e.g., date -> DateCell, user -> UserTag)
      type: def.field_type,
      // 权限约束：如果字段本身系统隐藏，则强制 false
      visible: def.is_system_hidden ? false : (userConfig?.visible ?? true),
      // 排序能力继承字段定义
      sortable: def.enable_sorting, 
      width: userConfig?.width ?? def.default_width ?? 'auto'
    };
  });
});
```

## 3. 交互流程优化 (Workflow Optimization)

在“列配置”侧滑抽屉中：

1.  **左侧数据池**：不再是写死的字符串列表，而是从 Backend 加载 `Available Fields`。
    -   按 `Group` (基础信息/审计信息/自定义字段) 分组展示。
    -   显示字段类型图标 (Text/Date/Number)。
2.  **约束校验**：
    -   当 `FieldDefinition.is_required_in_list` (列表必显) 为 true 时，禁止用户取消勾选 `visible`。
3.  **批量管理**：
    -   新增“同步最新字段”按钮：当后端增加了新字段时，允许用户一键将其加入当前列表视图。

## 4. 后续建议 (Next Steps)

如果您认可此方案，我建议：
1.  **修订 PRD**：更新 `list_column_configuration.md`，显式加入 `FieldDefinition` 的引用约束。
2.  **API 调整**：确保 `/api/system/column-config` 接口只返回配置差异 (Diff)，前端负责 Merge。
