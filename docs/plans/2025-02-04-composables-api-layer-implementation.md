# 执行计划：前端Composables API层统一架构

## 计划信息
| 项目 | 说明 |
|------|------|
| 关联PRD | `2025-02-04-composables-api-layer-prd.md` |
| 创建日期 | 2025-02-04 |
| 预计工期 | 2-3天 |
| 优先级 | P0 |

---

## 一、任务清单

### 第一阶段：核心Composables创建

#### Task 1.1: 创建 `useLayoutFields.ts`

**文件**: `frontend/src/composables/useLayoutFields.ts`

**职责**:
- 获取业务对象的字段定义列表
- 字段按类型分组
- 字段搜索过滤

**接口定义**:
```typescript
interface UseLayoutFieldsReturn {
  availableFields: Ref<AvailableField[]>
  fieldGroups: Ref<FieldGroup[]>
  loading: Ref<boolean>
  error: Ref<Error | null>
  fetchFields: () => Promise<void>
  searchFields: (query: string) => AvailableField[]
  clearCache: () => void
}
```

**验收标准**:
- [ ] 使用 `request` 工具而非 `fetch()`
- [ ] 完整TypeScript类型定义
- [ ] 错误处理通过 `request` 拦截器
- [ ] 支持字段缓存

---

#### Task 1.2: 创建 `useLayoutDesigner.ts`

**文件**: `frontend/src/composables/useLayoutDesigner.ts`

**职责**:
- 布局加载与保存
- 布局发布
- 撤销/重做状态管理

**接口定义**:
```typescript
interface UseLayoutDesignerReturn {
  layout: Ref<LayoutConfig | null>
  loading: Ref<boolean>
  saving: Ref<boolean>
  publishing: Ref<boolean>
  error: Ref<Error | null>

  // 方法
  loadLayout: () => Promise<void>
  saveLayout: () => Promise<void>
  publishLayout: () => Promise<void>

  // 状态
  canUndo: Ref<boolean>
  canRedo: Ref<boolean>
  undo: () => void
  redo: () => void

  // 重置
  reset: () => void
}
```

**验收标准**:
- [ ] 统一使用 `pageLayoutApi`
- [ ] 保存前自动验证布局配置
- [ ] 成功后显示友好提示

---

#### Task 1.3: 更新 `composables/index.ts`

**文件**: `frontend/src/composables/index.ts`

**变更**:
```typescript
// 新增导出
export * from './useLayoutFields'
export * from './useLayoutDesigner'
```

---

### 第二阶段：组件迁移

#### Task 2.1: 重构 `WysiwygLayoutDesigner.vue`

**变更内容**:

1. **移除fetch调用** (line ~1312):
```typescript
// 删除
const response = await fetch(`/api/system/business-objects/fields/?object_code=${props.objectCode}`)

// 替换为
const { fetchFields } = useLayoutFields(props.objectCode)
```

2. **导入新的composables**:
```typescript
import { useLayoutFields, useLayoutDesigner } from '@/composables'
```

3. **使用composable替代内联逻辑**:
```typescript
const {
  availableFields,
  fieldGroups,
  loading: fieldsLoading,
  fetchFields
} = useLayoutFields(props.objectCode)

const {
  layout,
  loading: layoutLoading,
  saving,
  publishing,
  saveLayout,
  publishLayout,
  canUndo,
  canRedo,
  undo,
  redo
} = useLayoutDesigner(props.layoutId)
```

**验收标准**:
- [ ] 无 `fetch()` 调用
- [ ] 字段列表正确加载
- [ ] 保存/发布功能正常

---

#### Task 2.2: 重构 `useFieldMetadata.ts`

**文件**: `frontend/src/composables/useFieldMetadata.ts`

**变更内容**:

1. **移除fetch调用** (line ~156):
```typescript
// 删除
const response = await fetch(
  `/api/system/objects/${objectCode}/fields/?${queryParams}`,
  {
    headers: {
      'Authorization': `Bearer ${userStore.token}`,
      'Content-Type': 'application/json'
    }
  }
)

// 替换为
import { businessObjectApi } from '@/api/system'
const result = await businessObjectApi.getFieldsWithContext(
  objectCode,
  context,
  { includeRelations: options.includeRelations !== false }
)
```

**验收标准**:
- [ ] 使用 `businessObjectApi.getFieldsWithContext()`
- [ ] 认证通过request拦截器自动处理
- [ ] 缓存机制保留

---

#### Task 2.3: 更新 `PageLayoutList.vue`

**变更内容**:
- 使用 `useLayoutFields` 获取可用字段
- 使用 `useLayoutDesigner` 处理布局CRUD

---

### 第三阶段：API层完善

#### Task 3.1: 完善 `system.ts` 类型定义

**文件**: `frontend/src/api/system.ts`

**新增类型**:
```typescript
/**
 * Available field for layout designer
 */
export interface AvailableField {
  code: string
  name: string
  fieldType: string
  fieldTypeDisplay?: string
  isRequired: boolean
  isSystem: boolean
  showInForm: boolean
  showInList: boolean
  showInDetail: boolean
}

/**
 * Field group for designer UI
 */
export interface FieldGroup {
  type: string
  label: string
  icon: Component
  fields: AvailableField[]
}
```

---

### 第四阶段：单元测试

#### Task 4.1: 创建测试工具函数

**文件**: `frontend/src/test/utils/composables.ts`

**内容**:
```typescript
import { ref } from 'vue'

/**
 * 创建mock的API响应
 */
export function createMockApiResponse<T>(data: T, delay = 0) {
  return Promise.resolve({
    success: true,
    data
  })
}

/**
 * 创建mock的错误响应
 */
export function createMockApiError(code: string, message: string) {
  return Promise.reject({
    success: false,
    error: { code, message }
  })
}

/**
 * 等待Vue响应式更新
 */
export async function flushPromises() {
  return new Promise(resolve => setTimeout(resolve, 0))
}
```

---

#### Task 4.2: 创建 `useLayoutFields.test.ts`

**文件**: `frontend/src/composables/__tests__/useLayoutFields.test.ts`

**测试用例**:
| 用例ID | 测试场景 | 验证点 |
|--------|----------|--------|
| UF-001 | 成功获取字段列表 | 返回正确的字段数组 |
| UF-002 | API错误处理 | error状态正确设置 |
| UF-003 | 字段缓存机制 | 第二次调用使用缓存 |
| UF-004 | 搜索字段过滤 | 按名称/编码正确过滤 |
| UF-005 | 字段分组 | 按类型正确分组 |

---

#### Task 4.3: 创建 `useLayoutDesigner.test.ts`

**文件**: `frontend/src/composables/__tests__/useLayoutDesigner.test.ts`

**测试用例**:
| 用例ID | 测试场景 | 验证点 |
|--------|----------|--------|
| UL-001 | 成功加载布局 | layout数据正确设置 |
| UL-002 | 保存布局成功 | saving状态正确切换 |
| UL-003 | 保存失败处理 | error状态正确设置 |
| UL-004 | 撤销/重做 | 状态栈正确管理 |
| UL-005 | 发布布局 | publishing状态正确切换 |

---

### 第五阶段：E2E测试

#### Task 5.1: 创建 `layout-designer.spec.ts`

**文件**: `frontend/e2e/layout-designer.spec.ts`

**测试场景** (TC-001 ~ TC-008):

| 场景ID | 测试场景 | 测试点 | 优先级 |
|--------|----------|--------|--------|
| TC-001 | 布局设计器 - 加载字段列表 | 字段正确显示，无401错误 | P0 |
| TC-002 | 布局设计器 - 搜索字段 | 搜索结果正确 | P1 |
| TC-003 | 布局设计器 - 拖拽字段 | 字段成功添加到画布 | P0 |
| TC-004 | 布局设计器 - 保存布局 | 保存成功，状态更新 | P0 |
| TC-005 | 布局设计器 - 发布布局 | 发布成功，版本号更新 | P0 |
| TC-006 | 布局设计器 - 撤销/重做 | 状态正确回退/恢复 | P1 |
| TC-007 | 布局列表 - 查看布局 | 布局列表正确显示 | P1 |
| TC-008 | 未认证访问 | 自动跳转登录页 | P0 |

---

#### Task 5.2: 更新package.json测试脚本

**文件**: `frontend/package.json`

**新增脚本**:
```json
{
  "scripts": {
    "test:unit": "vitest",
    "test:unit:coverage": "vitest --coverage",
    "test:unit:watch": "vitest --watch",
    "test:e2e": "playwright test",
    "test:e2e:headed": "playwright test --headed",
    "test:e2e:debug": "playwright test --debug",
    "test:composables": "vitest --run src/composables",
    "test:layout": "vitest --run src/composables --layout"
  }
}
```

---

### 第六阶段：验收与文档

#### Task 6.1: 功能验收

| 测试场景 | 预期结果 | 优先级 |
|----------|----------|--------|
| 打开布局设计器 | 字段列表正确加载 | P0 |
| 搜索字段 | 正确过滤字段 | P1 |
| 拖拽字段到画布 | 字段成功添加 | P0 |
| 保存布局 | 布局成功保存 | P0 |
| 发布布局 | 布局成功发布 | P0 |
| 未登录访问 | 自动跳转登录页 | P0 |

---

#### Task 6.2: 代码审查检查项

- [ ] 所有 `.vue` 和 `.ts` 文件中无 `fetch()` 调用
- [ ] 所有API调用使用 `request` 或 API模块
- [ ] 新增代码有完整TypeScript类型
- [ ] 错误处理统一且友好
- [ ] ESLint检查通过
- [ ] **单元测试覆盖率≥80%**
- [ ] **所有E2E测试通过**

---

## 二、文件清单

### 新建文件

| 文件 | 行数估算 |
|------|----------|
| `frontend/src/composables/useLayoutFields.ts` | ~150 |
| `frontend/src/composables/useLayoutDesigner.ts` | ~200 |
| `frontend/src/test/utils/composables.ts` | ~50 |
| `frontend/src/composables/__tests__/useLayoutFields.test.ts` | ~200 |
| `frontend/src/composables/__tests__/useLayoutDesigner.test.ts` | ~250 |
| `frontend/e2e/layout-designer.spec.ts` | ~300 |

### 修改文件

| 文件 | 修改类型 |
|------|----------|
| `frontend/src/composables/index.ts` | 新增导出 |
| `frontend/src/composables/useFieldMetadata.ts` | 重构fetch |
| `frontend/src/components/designer/WysiwygLayoutDesigner.vue` | 重构 |
| `frontend/src/views/system/PageLayoutList.vue` | 重构 |
| `frontend/src/api/system.ts` | 新增类型 |
| `frontend/package.json` | 新增测试脚本 |

---

## 三、测试配置

### 3.1 Vitest配置

**文件**: `frontend/vitest.config.ts`

确保包含以下配置:
```typescript
export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [...],
      statements: 80,
      branches: 75,
      functions: 80,
      lines: 80
    }
  }
})
```

### 3.2 Playwright配置

**文件**: `frontend/playwright.config.ts`

确保包含:
```typescript
export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5174',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ... }
    }
  ]
})
```

---

## 四、依赖关系

```
Task 1.1 (useLayoutFields) ──┐
                              ├─> Task 2.1 (WysiwygLayoutDesigner)
Task 1.2 (useLayoutDesigner) ┘

Task 2.1 ──> Task 2.3 (PageLayoutList)

Task 1.3 (index.ts) ──> Task 2.1, 2.2, 2.3

Task 3.1 (system.ts) ──> Task 1.1

Task 4.1 (测试工具) ──┬─> Task 4.2 (useLayoutFields.test)
                        └─> Task 4.3 (useLayoutDesigner.test)

Task 2.1, 2.2, 2.3 ──> Task 5.1 (E2E测试)

Task 5.1 ──> Task 6.1 (验收)
```

---

## 五、风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 破坏现有布局功能 | 充分测试，保留原逻辑回滚 |
| API响应格式变化 | 保持后端API不变 |
| 性能下降 | 引入字段缓存 |
| 测试环境不稳定 | 使用Docker容器化测试环境 |
| Mock数据不真实 | 定期同步Mock数据与API定义 |

---

## 六、完成标准

1. **功能完整**: 所有布局设计器功能正常工作
2. **无fetch调用**: 代码扫描无 `fetch()` 使用
3. **类型安全**: TypeScript编译无错误
4. **测试覆盖**:
   - 单元测试覆盖率≥80%
   - E2E测试TC-001~TC-008全部通过
5. **文档更新**: 架构文档更新

---

## 七、下一步

等待用户审批后开始执行。

**执行顺序**:
1. Task 1.1 -> 1.2 -> 1.3 (核心Composables)
2. Task 2.1 -> 2.2 -> 2.3 (组件迁移)
3. Task 3.1 (API类型完善)
4. Task 4.1 -> 4.2 -> 4.3 (单元测试)
5. Task 5.1 -> 5.2 (E2E测试)
6. Task 6.1 -> 6.2 (验收)
