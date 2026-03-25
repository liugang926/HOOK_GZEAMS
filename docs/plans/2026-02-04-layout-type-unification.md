# 布局设计器类型统一 PRD

## 文档信息
| 项目 | 说明 |
|------|------|
| PRD版本 | v1.1 |
| 创建日期 | 2026-02-04 |
| 修订日期 | 2026-02-04 |
| 作者 | Claude (基于原始PRD补充) |
| 状态 | 待审核 |

---

## 1. 目标

统一布局设计器的类型定义，消除重复定义和命名不一致问题。

---

## 2. 问题分析

### 2.1 类型定义分散

| 文件 | 重复类型 |
|------|----------|
| `services/layoutMerge.ts` | `SectionConfig`, `TabConfig`, `FieldOverride` |
| `services/layoutSchema.ts` | `SectionConfig`, `TabConfig`, `FieldOverride` |
| `types/layout.ts` | `LayoutSection`, `LayoutTab`, `LayoutField` |
| `LayoutPreview.vue` | `LayoutField`, `PreviewField` |
| `PropertyPanel.vue` | `LayoutField`, `LayoutSection`, `LayoutTab` |

### 2.2 命名不一致

| 位置 | 当前命名风格 | 说明 |
|------|-------------|------|
| PropertyPanel.vue | `field_code`, `default_value` | snake_case |
| CanvasArea.vue | `field_code`, `field_code` | snake_case |
| layoutMerge.ts | `default_value` | snake_case |
| layoutSchema.ts | `default_value` | snake_case |

**注意：** 当前使用 `snake_case` 与后端 Django REST Framework 默认序列化格式一致。

### 2.3 缺失的类型文件

`@/types/metadata` 被以下文件引用但不存在：
- `services/layoutMerge.ts:10`
- `services/layoutSchema.ts:10`
- `LayoutPreview.vue:14`

**影响：** 代码当前可能无法通过 TypeScript 编译。

### 2.4 缺失的类型定义

| 缺失类型 | 被引用位置 | 用途 |
|---------|-----------|------|
| `LayoutConfig` | layoutMerge.ts, layoutSchema.ts | 布局配置容器 |
| `FieldDefinition` | LayoutPreview.vue | 字段定义基类 |

---

## 3. 解决方案

### 3.1 创建 types/metadata.ts

```typescript
/**
 * metadata.ts - Unified metadata type definitions
 *
 * This file consolidates all metadata-related types for the layout designer.
 * Types use camelCase to match the frontend coding standard.
 *
 * Backend Integration Note:
 * - Backend uses djangorestframework-camel-case for API serialization
 * - All API responses should be in camelCase format
 * - If backend returns snake_case, configure djangorestframework-camel-case
 */

// ============================================================================
// Field Metadata Types
// ============================================================================

/**
 * Field metadata from backend API
 * Represents a field definition in a business object
 */
export interface FieldMetadata {
  /** Unique field identifier */
  code: string

  /** Human-readable field name */
  name: string

  /** Field type (text, number, reference, enum, etc.) */
  fieldType: string

  /** Whether field is required */
  isRequired: boolean

  /** Whether field is read-only */
  isReadonly: boolean

  /** Display sort order */
  sortOrder: number

  /** Section this field belongs to */
  sectionName?: string

  /** Whether this is a reverse relation field */
  isReverseRelation?: boolean

  /** How reverse relation is displayed */
  relationDisplayMode?: string

  /** Related object code (for reference fields) */
  relatedObject?: string

  /** Whether field is visible in form */
  showInForm?: boolean

  /** Whether field is visible in list */
  showInList?: boolean

  /** Custom CSS class */
  customClass?: string

  /** Field span (1-24, based on 24-column grid) */
  span?: number

  /** Default value */
  defaultValue?: any

  /** Help text for field */
  helpText?: string

  /** Placeholder text */
  placeholder?: string
}

/**
 * Field definition for layout designer
 * Used in designer components for field configuration
 */
export interface FieldDefinition extends FieldMetadata {
  /** Internal component ID */
  id: string

  /** Field label (can override name) */
  label: string

  /** Grid column span (1-24) */
  span: number

  /** Whether field is currently visible */
  visible?: boolean

  /** Whether field is read-only in current context */
  readonly?: boolean

  /** Whether field is required in current context */
  required?: boolean

  /** Placeholder text */
  placeholder?: string

  /** Help text */
  helpText?: string

  /** Field width (CSS value) */
  width?: string

  /** Custom CSS class */
  customClass?: string

  /** Visible rules (conditional visibility) */
  visibleRules?: Array<{ field: string; value: any }>

  /** Validation rules */
  validationRules?: Array<{ logic: string; message: string }>

  /** Regex pattern for validation */
  regexPattern?: string

  /** Minimum value (for numbers) */
  minValue?: number

  /** Maximum value (for numbers) */
  maxValue?: number

  /** Reference filters (for reference fields) */
  referenceFilters?: Record<string, any>
}

// ============================================================================
// Layout Configuration Types
// ============================================================================

/**
 * Complete layout configuration
 * Top-level container for all layout settings
 */
export interface LayoutConfig {
  /** Layout sections */
  sections?: SectionConfig[]

  /** Column configuration (for list layouts) */
  columns?: LayoutColumn[]

  /** Action buttons */
  actions?: LayoutAction[]

  /** Page title */
  title?: string

  /** Page icon */
  icon?: string

  /** Field order override */
  fieldOrder?: string[]

  /** Field-specific overrides */
  fieldOverrides?: Record<string, FieldOverride>

  /** Tab configurations */
  tabs?: TabConfig[]

  /** Container configurations */
  containers?: ContainerConfig[]

  /** Additional metadata */
  [key: string]: any
}

/**
 * Differential configuration for layout customization
 * Represents changes from default layout
 */
export interface DifferentialConfig {
  /** Custom field order */
  fieldOrder?: string[]

  /** Field-specific overrides */
  fieldOverrides?: Record<string, FieldOverride>

  /** Section configurations */
  sections?: SectionConfig[]

  /** Tab configurations */
  tabs?: TabConfig[]

  /** Container configurations */
  containers?: ContainerConfig[]
}

/**
 * Field override in differential config
 * Allows overriding default field properties
 */
export interface FieldOverride {
  /** Visibility override */
  visible?: boolean

  /** Read-only override */
  readonly?: boolean

  /** Required override */
  required?: boolean

  /** Column span override */
  span?: number

  /** Default value override */
  defaultValue?: any

  /** Label override */
  label?: string

  /** Placeholder override */
  placeholder?: string

  /** Help text override */
  helpText?: string
}

// ============================================================================
// Section Types
// ============================================================================

/**
 * Section configuration
 * Groups related fields together
 */
export interface SectionConfig {
  /** Section identifier */
  id: string

  /** Section title */
  title: string

  /** Field codes in this section */
  fields: string[]

  /** Number of columns (1-4) */
  columns?: number

  /** Whether section is collapsed by default */
  collapsed?: boolean

  /** Background color */
  backgroundColor?: string

  /** Border visibility */
  border?: boolean

  /** Section icon name */
  icon?: string

  /** Custom CSS class */
  customClass?: string

  /** Whether section is visible */
  visible?: boolean
}

/**
 * Layout section (from types/layout.ts)
 * Similar to SectionConfig but with additional properties
 */
export interface LayoutSection {
  /** Section identifier */
  id: string

  /** Section name/key */
  name: string

  /** Section display title */
  title?: string

  /** Section type */
  type?: SectionType

  /** Whether section is collapsible */
  collapsible?: boolean

  /** Whether section is collapsed by default */
  collapsed?: boolean

  /** Number of columns in the section */
  columnCount?: number

  /** Fields in this section (field codes or field objects) */
  fields: (string | LayoutField)[]

  /** Display order */
  order?: number

  /** Whether section is visible */
  visible?: boolean

  /** Whether to show border */
  border?: boolean

  /** Section icon */
  icon?: string

  /** Whether to show title */
  showTitle?: boolean

  /** Shadow effect */
  shadow?: string

  /** Section span (grid columns) */
  span?: number
}

/** Section types */
export type SectionType = 'default' | 'card' | 'fieldset' | 'tab' | 'collapse'

// ============================================================================
// Tab Types
// ============================================================================

/**
 * Tab configuration
 * Defines a tab in tabbed layout
 */
export interface TabConfig {
  /** Tab identifier */
  id: string

  /** Tab title */
  title: string

  /** Field codes in this tab */
  fields?: string[]

  /** Related object codes in this tab */
  relations?: string[]

  /** Whether tab is disabled */
  disabled?: boolean

  /** Tab icon name */
  icon?: string
}

/**
 * Layout tab (from types/layout.ts)
 * Similar to TabConfig but with sections support
 */
export interface LayoutTab {
  /** Tab identifier */
  id: string

  /** Tab name/key */
  name: string

  /** Tab title */
  title: string

  /** Tab icon */
  icon?: string

  /** Sections in this tab */
  sections: LayoutSection[]

  /** Whether tab is disabled */
  disabled?: boolean

  /** Display order */
  order?: number
}

// ============================================================================
// Container Types
// ============================================================================

/**
 * Container configuration
 * Defines layout containers for organizing content
 */
export interface ContainerConfig {
  /** Container type */
  type: ContainerType

  /** Container identifier */
  id: string

  /** Container title */
  title?: string

  /** Container items */
  items?: ContainerConfig[]

  /** Additional properties */
  [key: string]: any
}

/** Container types */
export type ContainerType = 'tab' | 'column' | 'collapse' | 'divider'

// ============================================================================
// Field Types
// ============================================================================

/**
 * Layout field (from types/layout.ts)
 * Used within sections to configure individual field display
 */
export interface LayoutField {
  /** Field code */
  fieldCode: string

  /** Grid span */
  span?: number

  /** Whether field is read-only */
  readonly?: boolean

  /** Whether field is visible */
  visible?: boolean

  /** Display order */
  order?: number

  /** Field-specific props */
  props?: Record<string, any>
}

/**
 * Preview field (for layout preview)
 * Extends LayoutField with simulated values
 */
export interface PreviewField extends FieldDefinition {
  /** Simulated value for preview */
  simulatedValue?: any
}

// ============================================================================
// Column Types (for List Layouts)
// ============================================================================

/**
 * Layout column definition
 * Used for list view columns
 */
export interface LayoutColumn {
  /** Field code */
  fieldCode: string

  /** Column span */
  span?: number

  /** Whether column is read-only */
  readonly?: boolean

  /** Whether column is visible */
  visible?: boolean

  /** Display order */
  order?: number

  /** Column width */
  width?: number

  /** Whether column is sortable */
  sortable?: boolean

  /** Fixed position */
  fixed?: 'left' | 'right'
}

/**
 * List column (from PropertyPanel.vue)
 * Used in list layout designer
 */
export interface ListColumn {
  /** Field code */
  fieldCode: string

  /** Column label */
  label: string

  /** Column width (px) */
  width?: number

  /** Fixed position */
  fixed?: string

  /** Whether sortable */
  sortable?: boolean
}

// ============================================================================
// Action Types
// ============================================================================

/**
 * Layout action definition
 * Defines action buttons on the page
 */
export interface LayoutAction {
  /** Action code */
  code: string

  /** Action label */
  label: string

  /** Button type */
  type: ActionType

  /** Action type */
  actionType: ActionCategory

  /** API endpoint for custom actions */
  apiEndpoint?: string

  /** HTTP method */
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE' | 'PATCH'

  /** Confirmation message */
  confirmMessage?: string

  /** Display order */
  order: number

  /** Whether action is visible */
  visible?: boolean

  /** Whether action is disabled */
  disabled?: boolean

  /** Button icon */
  icon?: string

  /** Additional props */
  props?: Record<string, any>
}

/** Action button types */
export type ActionType = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'

/** Action categories */
export type ActionCategory = 'submit' | 'cancel' | 'custom' | 'workflow'

// ============================================================================
// Validation Types
// ============================================================================

/**
 * Validation result
 */
export interface ValidationResult {
  /** Whether validation passed */
  valid: boolean

  /** Validation errors */
  errors: ValidationError[]
}

/**
 * Validation error detail
 */
export interface ValidationError {
  /** Error path (dot notation) */
  path: string

  /** Error message */
  message: string

  /** Error code */
  code: string
}

/** Standard error codes */
export const ERROR_CODES = {
  REQUIRED_FIELD: 'REQUIRED_FIELD',
  INVALID_TYPE: 'INVALID_TYPE',
  INVALID_VALUE: 'INVALID_VALUE',
  DUPLICATE_ID: 'DUPLICATE_ID',
  UNKNOWN_FIELD: 'UNKNOWN_FIELD',
  INVALID_STRUCTURE: 'INVALID_STRUCTURE'
} as const
```

### 3.2 更新 types/index.ts

```typescript
// types/index.ts - 添加导出

// ========================================
// Metadata Types (NEW)
// ========================================
export * from './metadata'
```

### 3.3 更新导入路径

| 文件 | 变更内容 |
|------|---------|
| `services/layoutMerge.ts` | 删除 `SectionConfig`, `TabConfig`, `FieldOverride` 定义，改为从 `@/types/metadata` 导入 |
| `services/layoutSchema.ts` | 删除 `FieldOverride` 定义，改为从 `@/types/metadata` 导入 |
| `LayoutPreview.vue` | 添加 `LayoutConfig`, `FieldDefinition` 从 `@/types/metadata` 导入 |
| `PropertyPanel.vue` | 更新类型导入路径 |
| `CanvasArea.vue` | 更新类型导入路径 |

---

## 4. 实施计划

### 4.1 分阶段执行

#### 阶段一：类型文件创建（高优先级，低风险）

| 步骤 | 任务 | 产出 |
|------|------|------|
| 1.1 | 创建 `types/metadata.ts` | 完整的类型定义文件 |
| 1.2 | 更新 `types/index.ts` | 导出 metadata 类型 |
| 1.3 | 删除 `services/layoutMerge.ts` 中的重复类型 | 清理冗余定义 |
| 1.4 | 删除 `services/layoutSchema.ts` 中的重复类型 | 清理冗余定义 |
| 1.5 | 更新所有导入路径 | 统一从 `@/types/metadata` 导入 |
| 1.6 | TypeScript 编译验证 | 确保无类型错误 |

**阶段一验收标准：**
- [ ] TypeScript 编译无错误
- [ ] 所有类型导入路径正确
- [ ] 布局设计器可正常加载

#### 阶段二：命名统一（低优先级，高风险）

> **前提条件：**
> 1. 确认后端已配置 `djangorestframework-camel-case`
> 2. 或确认前端已有 camelCase 转换层
> 3. 阶段一已完成并通过验证

| 步骤 | 任务 | 影响范围 |
|------|------|---------|
| 2.1 | 统一 `FieldMetadata` 类型字段名 | 类型定义 |
| 2.2 | 更新 `PropertyPanel.vue` 中的字段引用 | 模板 + 脚本 |
| 2.3 | 更新 `CanvasArea.vue` 中的字段引用 | 模板 + 脚本 |
| 2.4 | 更新 `LayoutPreview.vue` 中的字段引用 | 模板 + 脚本 |
| 2.5 | 更新 `layoutMerge.ts` 中的字段访问 | 业务逻辑 |
| 2.6 | 全局搜索替换 snake_case → camelCase | 所有相关文件 |
| 2.7 | API 响应格式验证 | 确保后端返回 camelCase |

**阶段二验收标准：**
- [ ] 所有属性名使用 camelCase
- [ ] API 数据绑定正常
- [ ] 布局设计器功能正常
- [ ] 属性面板编辑正常
- [ ] 预览功能正常
- [ ] 回归测试通过

### 4.2 文件变更清单

#### 新增文件
- `frontend/src/types/metadata.ts`

#### 修改文件（阶段一）
| 文件 | 变更类型 | 变更说明 |
|------|----------|---------|
| `types/index.ts` | 新增导出 | 添加 `export * from './metadata'` |
| `services/layoutMerge.ts` | 删除 + 导入 | 删除重复类型，添加从 metadata 导入 |
| `services/layoutSchema.ts` | 删除 + 导入 | 删除重复类型，添加从 metadata 导入 |
| `LayoutPreview.vue` | 导入 | 更新类型导入路径 |
| `PropertyPanel.vue` | 导入 | 更新类型导入路径 |
| `CanvasArea.vue` | 导入 | 更新类型导入路径 |

#### 修改文件（阶段二）
| 文件 | 变更类型 | 变更说明 |
|------|----------|---------|
| `PropertyPanel.vue` | 重命名 | `field_code` → `fieldCode`, `default_value` → `defaultValue` 等 |
| `CanvasArea.vue` | 重命名 | `field_code` → `fieldCode` |
| `LayoutPreview.vue` | 重命名 | `field_code` → `fieldCode`, `default_value` → `defaultValue` |
| `layoutMerge.ts` | 重命名 | `default_value` → `defaultValue`, `section_name` → `sectionName` 等 |
| `layoutSchema.ts` | 重命名 | `default_value` → `defaultValue` |

---

## 5. 风险评估与缓解

### 5.1 风险矩阵

| 风险 | 概率 | 影响 | 风险等级 | 缓解措施 |
|------|------|------|----------|---------|
| 后端API返回snake_case导致数据绑定失败 | 高 | 高 | **高** | 实施前确认后端序列化配置 |
| 现有代码大量引用需修改 | 高 | 中 | 中 | 使用IDE重构工具 |
| 类型定义不完整需反复补充 | 中 | 低 | 低 | 分阶段提交，及时验证 |
| 组件props传递格式变化导致子组件异常 | 中 | 中 | 中 | 全面回归测试 |

### 5.2 后端API兼容性检查

**执行前必须确认以下任一条件：**

1. **后端已配置 camelCase 序列化**
   ```python
   # backend/config/settings/base.py
   REST_FRAMEWORK = {
       'DEFAULT_RENDERER_CLASSES': [
           'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
       ],
       'DEFAULT_PARSER_CLASSES': [
           'djangorestframework_camel_case.parser.CamelCaseJSONParser',
       ],
   }
   ```

2. **前端有转换层**
   - 检查 `utils/request.ts` 是否有响应转换
   - 或检查是否有 axios 拦截器处理命名转换

3. **API响应格式验证脚本**
   ```bash
   # 验证后端API响应格式
   curl -H "Authorization: Bearer <token>" \
        http://localhost:8000/api/system/field-definitions/ | jq .
   ```

### 5.3 回滚计划

如果阶段二执行出现问题，准备以下回滚方案：

1. **保留阶段一的代码分支**
   - 阶段一完成后创建 tag: `type-unification-phase1`

2. **快速回滚命令**
   ```bash
   git checkout type-unification-phase1
   ```

3. **数据兼容性层（备选）**
   - 如果无法统一命名，可添加转换函数
   ```typescript
   // utils/fieldTransform.ts
   export function toCamelCase(obj: any): any {
     // 转换逻辑
   }

   export function toSnakeCase(obj: any): any {
     // 转换逻辑
   }
   ```

---

## 6. 测试验证与检查点

### 6.1 阶段一检查点（类型文件创建）

#### 6.1.1 编译检查点

| 检查点 | 命令 | 预期结果 | 阻塞级别 |
|--------|------|----------|----------|
| CP-1.1 | `npx tsc --noEmit` | 无类型错误 | 🔴 阻塞 |
| CP-1.2 | `npm run build` | 构建成功无错误 | 🔴 阻塞 |
| CP-1.3 | `npm run lint` | 无 ESLint 错误 | 🟡 警告 |
| CP-1.4 | `npx vue-tsc --noEmit` | Vue 组件类型检查通过 | 🔴 阻塞 |

**验证脚本：**
```bash
#!/bin/bash
# 阶段一验证脚本

echo "=== 阶段一验证开始 ==="

# 检查 metadata.ts 文件存在
if [ ! -f "frontend/src/types/metadata.ts" ]; then
    echo "❌ metadata.ts 文件不存在"
    exit 1
fi
echo "✅ metadata.ts 文件已创建"

# 检查类型导出
if grep -q "export.*interface.*FieldMetadata" frontend/src/types/metadata.ts; then
    echo "✅ FieldMetadata 类型已定义"
else
    echo "❌ FieldMetadata 类型缺失"
    exit 1
fi

# 检查 index.ts 导出
if grep -q "export \* from './metadata'" frontend/src/types/index.ts; then
    echo "✅ types/index.ts 已导出 metadata"
else
    echo "❌ types/index.ts 未导出 metadata"
    exit 1
fi

# TypeScript 编译检查
cd frontend
npx tsc --noEmit
if [ $? -eq 0 ]; then
    echo "✅ TypeScript 编译通过"
else
    echo "❌ TypeScript 编译失败"
    exit 1
fi

echo "=== 阶段一验证完成 ==="
```

#### 6.1.2 导入路径检查点

| 文件 | 检查项 | 验证方法 |
|------|--------|----------|
| `layoutMerge.ts` | 从 `@/types/metadata` 导入类型 | `grep "from '@/types/metadata'"` |
| `layoutSchema.ts` | 从 `@/types/metadata` 导入类型 | `grep "from '@/types/metadata'"` |
| `LayoutPreview.vue` | 从 `@/types/metadata` 导入类型 | `grep "from '@/types/metadata'"` |
| `PropertyPanel.vue` | 可从 `@/types/metadata` 导入类型 | 检查导入路径 |
| `CanvasArea.vue` | 可从 `@/types/metadata` 导入类型 | 检查导入路径 |

**验证命令：**
```bash
# 检查所有文件是否正确导入
grep -r "from '@/types/metadata'" frontend/src/components/designer/
grep -r "from '@/types/metadata'" frontend/src/components/designer/services/
```

#### 6.1.3 类型定义完整性检查点

| 类型定义 | 必需属性 | 验证方法 |
|----------|----------|----------|
| `FieldMetadata` | code, name, fieldType, isRequired, isReadonly, sortOrder | 类型检查 |
| `FieldDefinition` | 继承 FieldMetadata + id, label, span | 类型检查 |
| `LayoutConfig` | sections, tabs, containers, fieldOrder, fieldOverrides | 类型检查 |
| `DifferentialConfig` | fieldOrder, fieldOverrides, sections, tabs | 类型检查 |
| `SectionConfig` | id, title, fields | 类型检查 |
| `TabConfig` | id, title, fields?, relations? | 类型检查 |
| `FieldOverride` | visible, readonly, required, span, defaultValue | 类型检查 |
| `ValidationResult` | valid, errors | 类型检查 |

#### 6.1.4 阶段一验收标准

**必须满足（阻塞）：**
- [ ] TypeScript 编译零错误
- [ ] 所有导入路径正确解析
- [ ] `metadata.ts` 包含所有必需类型定义
- [ ] `types/index.ts` 正确导出 metadata 模块
- [ ] 删除了重复的类型定义

**建议满足（非阻塞）：**
- [ ] 所有类型包含完整的 JSDoc 注释
- [ ] 类型定义按功能分组并有清晰的分隔注释
- [ ] ESLint 检查通过（允许修复警告）

---

### 6.2 阶段二检查点（命名统一）

#### 6.2.1 后端API兼容性检查点

**在执行阶段二之前必须验证：**

| 检查点 | 验证方法 | 预期结果 |
|--------|----------|----------|
| CP-2.1 | 检查 `settings/base.py` | 已配置 `djangorestframework_camel_case` |
| CP-2.2 | API 响应格式测试 | 返回 camelCase 格式 |
| CP-2.3 | 前端转换层检查 | 如无后端配置，需有前端转换层 |

**API 格式验证脚本：**
```bash
#!/bin/bash
# 后端 API 格式验证

TOKEN="your_test_token"
API_BASE="http://localhost:8000/api"

echo "=== 验证后端 API 响应格式 ==="

# 获取字段定义
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "$API_BASE/system/field-definitions/?limit=1")

echo "API 响应示例:"
echo "$RESPONSE" | jq '.'

# 检查是否为 camelCase
if echo "$RESPONSE" | jq -e '.results[0].fieldCode' > /dev/null; then
    echo "✅ API 返回 camelCase 格式"
elif echo "$RESPONSE" | jq -e '.results[0].field_code' > /dev/null; then
    echo "❌ API 返回 snake_case 格式，需要配置后端"
    exit 1
else
    echo "⚠️ 无法确定 API 格式"
fi
```

**后端配置检查（如需配置）：**
```python
# backend/config/settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'djangorestframework_camel_case.parser.CamelCaseJSONParser',
    ],
}
```

#### 6.2.2 命名替换检查点

| 文件 | 原属性名 | 新属性名 | 检查方法 |
|------|---------|---------|----------|
| `PropertyPanel.vue` | `field_code` | `fieldCode` | `grep -c "fieldCode"` |
| `PropertyPanel.vue` | `default_value` | `defaultValue` | `grep -c "defaultValue"` |
| `CanvasArea.vue` | `field_code` | `fieldCode` | `grep -c "fieldCode"` |
| `LayoutPreview.vue` | `field_code` | `fieldCode` | `grep -c "fieldCode"` |
| `LayoutPreview.vue` | `default_value` | `defaultValue` | `grep -c "defaultValue"` |
| `layoutMerge.ts` | `section_name` | `sectionName` | `grep -c "sectionName"` |
| `layoutMerge.ts` | `sort_order` | `sortOrder` | `grep -c "sortOrder"` |
| `layoutMerge.ts` | `is_reverse_relation` | `isReverseRelation` | `grep -c "isReverseRelation"` |
| `layoutSchema.ts` | `default_value` | `defaultValue` | `grep -c "defaultValue"` |

**全局搜索验证：**
```bash
# 确保没有遗留的 snake_case 引用（排除注释和字符串）
# 排除常见的安全模式
grep -r "field_code\|default_value\|section_name\|sort_order\|is_required\|is_readonly" \
    frontend/src/components/designer/ \
    --include="*.vue" --include="*.ts" --include="*.tsx" \
    | grep -v "// " | grep -v "^\s*//" | grep -v "\.camelCase"
```

#### 6.2.3 阶段二验收标准

**必须满足（阻塞）：**
- [ ] 所有属性名使用 camelCase
- [ ] TypeScript 编译零错误
- [ ] 后端 API 返回 camelCase 或前端有转换层
- [ ] 全局搜索无遗留的 snake_case 属性引用

**建议满足（非阻塞）：**
- [ ] ESLint 检查通过
- [ ] 代码风格一致

---

### 6.3 功能测试检查点

#### 6.3.1 布局设计器功能测试

| 测试用例 | 测试步骤 | 预期结果 | 检查点ID |
|----------|----------|----------|----------|
| FT-1 | 打开布局设计器页面 | 页面正常加载，无控制台错误 | FT-CP-1 |
| FT-2 | 从组件面板拖拽字段到画布 | 字段成功添加，显示正确 | FT-CP-2 |
| FT-3 | 拖拽区块到画布 | 区块成功添加，可配置属性 | FT-CP-3 |
| FT-4 | 点击字段打开属性面板 | 属性面板显示正确的字段属性 | FT-CP-4 |
| FT-5 | 修改字段属性（标签、跨度等） | 修改成功，预览实时更新 | FT-CP-5 |
| FT-6 | 切换到预览标签 | 预览正确显示布局效果 | FT-CP-6 |
| FT-7 | 保存布局配置 | 保存成功，返回成功消息 | FT-CP-7 |
| FT-8 | 重新加载布局设计器 | 之前保存的配置正确加载 | FT-CP-8 |
| FT-9 | 拖拽调整字段顺序 | 字段顺序正确更新 | FT-CP-9 |
| FT-10 | 拖拽字段到不同区块 | 字段成功移动到目标区块 | FT-CP-10 |

#### 6.3.2 字段属性测试

| 测试用例 | 测试属性 | 测试值 | 预期结果 | 检查点ID |
|----------|----------|--------|----------|----------|
| FA-1 | 可见性 | visible: false | 字段在预览中隐藏 | FA-CP-1 |
| FA-2 | 只读 | readonly: true | 字段显示为只读状态 | FA-CP-2 |
| FA-3 | 必填 | required: true | 字段显示必填标记 | FA-CP-3 |
| FA-4 | 列跨度 | span: 24 | 字段占满整行 | FA-CP-4 |
| FA-5 | 列跨度 | span: 12 | 字段占半行 | FA-CP-5 |
| FA-6 | 列跨度 | span: 6 | 字段占1/4行 | FA-CP-6 |
| FA-7 | 标签覆盖 | label: "自定义" | 显示自定义标签 | FA-CP-7 |
| FA-8 | 占位符 | placeholder: "请输入" | 显示占位符文本 | FA-CP-8 |
| FA-9 | 帮助文本 | helpText: "说明" | 显示帮助文本 | FA-CP-9 |
| FA-10 | 自定义CSS类 | customClass: "test" | 应用自定义样式 | FA-CP-10 |

#### 6.3.3 区块属性测试

| 测试用例 | 测试属性 | 测试值 | 预期结果 | 检查点ID |
|----------|----------|--------|----------|----------|
| SA-1 | 区块标题 | title: "基本信息" | 显示区块标题 | SA-CP-1 |
| SA-2 | 列数 | columns: 1 | 单列布局 | SA-CP-2 |
| SA-3 | 列数 | columns: 2 | 双列布局 | SA-CP-3 |
| SA-4 | 列数 | columns: 3 | 三列布局 | SA-CP-4 |
| SA-5 | 列数 | columns: 4 | 四列布局 | SA-CP-5 |
| SA-6 | 可折叠 | collapsible: true | 显示折叠控制 | SA-CP-6 |
| SA-7 | 默认折叠 | collapsed: true | 区块默认折叠 | SA-CP-7 |
| SA-8 | 边框 | border: false | 隐藏边框 | SA-CP-8 |
| SA-9 | 背景色 | backgroundColor: "#f0f0f0" | 应用背景色 | SA-CP-9 |
| SA-10 | 图标 | icon: "Edit" | 显示图标 | SA-CP-10 |

#### 6.3.4 API 集成测试

| 测试用例 | API 端点 | 测试步骤 | 预期结果 | 检查点ID |
|----------|----------|----------|----------|----------|
| API-1 | GET /api/system/field-definitions/ | 获取字段定义列表 | 返回 camelCase 格式数据 | API-CP-1 |
| API-2 | GET /api/system/page-layouts/ | 获取布局列表 | 正确加载布局配置 | API-CP-2 |
| API-3 | POST /api/system/page-layouts/ | 创建新布局 | 布局保存成功 | API-CP-3 |
| API-4 | PUT /api/system/page-layouts/{id}/ | 更新布局 | 更新成功，数据持久化 | API-CP-4 |
| API-5 | GET /api/system/page-layouts/{id}/ | 获取单个布局 | 返回完整的布局配置 | API-CP-5 |
| API-6 | DELETE /api/system/page-layouts/{id}/ | 删除布局 | 删除成功 | API-CP-6 |

---

### 6.4 回归测试检查点

#### 6.4.1 资产管理页面测试

| 测试用例 | 测试步骤 | 预期结果 | 检查点ID |
|----------|----------|----------|----------|
| RT-1 | 打开资产列表页 | 页面正常显示，列配置正确 | RT-CP-1 |
| RT-2 | 点击新建资产 | 表单布局正确显示 | RT-CP-2 |
| RT-3 | 填写表单并保存 | 数据保存成功 | RT-CP-3 |
| RT-4 | 打开资产详情页 | 详情布局正确显示 | RT-CP-4 |
| RT-5 | 编辑资产 | 表单正确加载数据 | RT-CP-5 |
| RT-6 | 列排序和筛选 | 功能正常 | RT-CP-6 |

#### 6.4.2 其他业务对象测试

| 业务对象 | 测试步骤 | 预期结果 | 检查点ID |
|----------|----------|----------|----------|
| AssetCategory | 分类列表/表单/详情 | 功能正常 | RT-CP-7 |
| Consumable | 耗材列表/表单/详情 | 功能正常 | RT-CP-8 |
| Department | 部门列表/表单/详情 | 功能正常 | RT-CP-9 |
| Location | 位置列表/表单/详情 | 功能正常 | RT-CP-10 |

---

### 6.5 自动化测试规范

#### 6.5.1 单元测试

为新增的工具函数添加单元测试：

```typescript
// tests/unit/metadataTypes.test.ts
import { describe, it, expect } from 'vitest'
import type { FieldMetadata, SectionConfig, DifferentialConfig } from '@/types/metadata'

describe('Metadata Types', () => {
  describe('FieldMetadata', () => {
    it('should accept valid field metadata', () => {
      const field: FieldMetadata = {
        code: 'test_field',
        name: 'Test Field',
        fieldType: 'text',
        isRequired: false,
        isReadonly: false,
        sortOrder: 1
      }
      expect(field.code).toBe('test_field')
    })

    it('should accept optional properties', () => {
      const field: FieldMetadata = {
        code: 'test_field',
        name: 'Test Field',
        fieldType: 'text',
        isRequired: false,
        isReadonly: false,
        sortOrder: 1,
        sectionName: 'basic',
        defaultValue: 'default'
      }
      expect(field.sectionName).toBe('basic')
      expect(field.defaultValue).toBe('default')
    })
  })

  describe('SectionConfig', () => {
    it('should accept valid section config', () => {
      const section: SectionConfig = {
        id: 'section_1',
        title: 'Basic Information',
        fields: ['field1', 'field2']
      }
      expect(section.fields).toHaveLength(2)
    })
  })
})
```

#### 6.5.2 类型测试

确保类型定义的运行时正确性：

```typescript
// tests/unit/typeGuards.test.ts
import { describe, it, expect } from 'vitest'
import type { FieldMetadata, FieldDefinition } from '@/types/metadata'

describe('Type Guards', () => {
  it('should distinguish FieldMetadata from FieldDefinition', () => {
    const metadata: FieldMetadata = {
      code: 'test',
      name: 'Test',
      fieldType: 'text',
      isRequired: false,
      isReadonly: false,
      sortOrder: 1
    }

    const definition: FieldDefinition = {
      ...metadata,
      id: 'def_1',
      label: 'Test Label',
      span: 12
    }

    // FieldDefinition should have id
    expect('id' in definition).toBe(true)
    expect('id' in metadata).toBe(false)
  })
})
```

#### 6.5.3 集成测试

布局设计器集成测试示例：

```typescript
// tests/e2e/layoutDesigner.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Layout Designer Type Unification', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('[name="username"]', 'admin')
    await page.fill('[name="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard')
  })

  test('should open layout designer', async ({ page }) => {
    await page.goto('http://localhost:5173/system/layouts/designer')
    await expect(page.locator('.layout-designer')).toBeVisible()
  })

  test('should display fields with camelCase properties', async ({ page }) => {
    await page.goto('http://localhost:5173/system/layouts/designer?object=Asset')

    // 检查字段面板
    const fieldBadge = page.locator('.field-badge').first()
    await expect(fieldBadge).toBeVisible()

    // 检查属性面板
    await fieldBadge.click()
    const propertyPanel = page.locator('.property-panel')
    await expect(propertyPanel).toBeVisible()

    // 验证属性名使用 camelCase
    const fieldCodeInput = propertyPanel.locator('input[value*="code"]')
    await expect(fieldCodeInput).toBeVisible()
  })

  test('should save layout with correct format', async ({ page }) => {
    await page.goto('http://localhost:5173/system/layouts/designer?object=Asset')

    // 拖拽字段到画布
    await page.dragAndDrop(
      '.component-panel .field-item:first-child',
      '.canvas-area .sections-container'
    )

    // 点击保存
    await page.click('button:has-text("Save")')

    // 等待成功提示
    await expect(page.locator('.el-message--success')).toBeVisible()
  })
})
```

---

### 6.6 测试执行计划

#### 6.6.1 测试执行顺序

```
┌─────────────────────────────────────────────────────────────┐
│                        测试执行流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────┐  │
│  │ 阶段一   │───▶│ 编译检查 │───▶│ 类型检查 │───▶│ 功能  │  │
│  │ 开发完成 │    │          │    │          │    │ 测试  │  │
│  └─────────┘    └──────────┘    └──────────┘    └──────┘  │
│                                                   │        │
│                                              全部通过      │
│                                                   │        │
│                                                   ▼        │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────┐  │
│  │ 阶段二   │───▶│ 编译检查 │───▶│ API兼容  │───▶│ 回归  │  │
│  │ 开发完成 │    │          │    │   性检查  │    │ 测试  │  │
│  └─────────┘    └──────────┘    └──────────┘    └──────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 6.6.2 测试执行清单

**阶段一测试执行：**
```bash
# 1. 编译检查
npm run build
npx tsc --noEmit

# 2. 类型检查
npx vue-tsc --noEmit

# 3. Lint 检查
npm run lint

# 4. 单元测试
npm run test:unit

# 5. 功能测试（手动）
# - 按照功能测试检查点逐项验证
```

**阶段二测试执行：**
```bash
# 1. API 兼容性检查
./scripts/check-api-format.sh

# 2. 编译检查
npm run build
npx tsc --noEmit

# 3. 全局命名检查
./scripts/check-naming.sh

# 4. E2E 测试
npm run test:e2e

# 5. 回归测试（手动）
# - 按照回归测试检查点逐项验证
```

---

### 6.7 测试报告模板

#### 测试报告格式

```markdown
# 布局设计器类型统一测试报告

## 测试信息
| 项目 | 说明 |
|------|------|
| 测试日期 | YYYY-MM-DD |
| 测试人员 | [姓名] |
| 测试阶段 | 阶段一 / 阶段二 |
| PRD 版本 | v1.1 |

## 编译检查结果
| 检查项 | 结果 | 说明 |
|--------|------|------|
| TypeScript 编译 | ✅ / ❌ | |
| ESLint 检查 | ✅ / ❌ | |
| Vue 组件类型检查 | ✅ / ❌ | |

## 功能测试结果
| 用例ID | 测试用例 | 结果 | 备注 |
|--------|----------|------|------|
| FT-1 | 打开布局设计器 | ✅ / ❌ | |
| FT-2 | 拖拽字段 | ✅ / ❌ | |
| ... | ... | ... | |

## API 测试结果
| 用例ID | 测试用例 | 结果 | 备注 |
|--------|----------|------|------|
| API-1 | 获取字段定义 | ✅ / ❌ | |
| ... | ... | ... | |

## 回归测试结果
| 用例ID | 测试用例 | 结果 | 备注 |
|--------|----------|------|------|
| RT-1 | 资产列表页 | ✅ / ❌ | |
| ... | ... | ... | |

## 问题清单
| ID | 问题描述 | 严重程度 | 状态 |
|----|----------|----------|------|
| 1 | | 🔴/🟡/🟢 | |

## 测试结论
- [ ] 通过，可以发布
- [ ] 有问题，需要修复后重新测试
```

---

## 7. 时间估算

### 7.1 阶段一时间估算

| 任务 | 工时 | 说明 |
|------|------|------|
| 创建 metadata.ts | 0.5天 | 包含所有类型定义 |
| 更新 types/index.ts | 0.1天 | 添加导出 |
| 删除重复类型定义 | 0.2天 | 2个服务文件 |
| 更新导入路径 | 0.3天 | 6个文件 |
| TypeScript 编译验证 | 0.2天 | 修复类型错误 |
| 功能测试 | 0.2天 | 基本功能验证 |
| **阶段一小计** | **1.5天** | |

### 7.2 阶段时间估算

| 任务 | 工时 | 说明 |
|------|------|------|
| 后端API兼容性确认 | 0.2天 | 可能需要配置后端 |
| 命名统一（组件文件） | 0.5天 | 3个Vue组件 |
| 命名统一（服务文件） | 0.3天 | 2个服务文件 |
| 全局搜索替换验证 | 0.3天 | 确保无遗漏 |
| API集成测试 | 0.3天 | 验证数据绑定 |
| 回归测试 | 0.5天 | 完整功能测试 |
| **阶段二小计** | **2.1天** | |

### 7.3 总计

| 阶段 | 工时 | 建议执行顺序 |
|------|------|-------------|
| 阶段一 | 1.5天 | **立即执行** |
| 阶段二 | 2.1天 | 等待后端配置确认后执行 |
| 缓冲时间 | 0.4天 | 应对意外问题 |
| **总计** | **4天** | |

---

## 8. 依赖关系

### 8.1 前置依赖
- 无（阶段一可独立执行）

### 8.2 阶段二前置条件
- 阶段一已完成
- 后端已配置 `djangorestframework-camel-case` 或确认API响应格式

### 8.3 后续任务
- 类型统一完成后，可继续优化布局设计器其他功能
- 可考虑添加类型生成工具（从后端自动生成TypeScript类型）

---

## 9. 附录

### 9.1 相关文档
- `docs/plans/frontend/TYPE_UNIFICATION_EXECUTION_PLAN.md`
- `frontend/src/types/layout.ts`
- `backend/config/settings/base.py`

### 9.2 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-02-04 | 初始版本 | 原始PRD |
| v1.1 | 2026-02-04 | 补充完整类型定义、分阶段执行计划、风险评估 | Claude |
