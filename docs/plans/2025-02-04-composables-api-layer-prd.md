# PRD: 前端Composables API层统一架构

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2025-02-04 |
| 作者 | Claude |
| 状态 | 待审批 |

---

## 一、背景与问题分析

### 1.1 当前问题

在 `WysiwygLayoutDesigner.vue` 组件中发现使用原生 `fetch()` 调用API：

```javascript
// WysiwygLayoutDesigner.vue:1312
const response = await fetch(`/api/system/business-objects/fields/?object_code=${props.objectCode}`)
const data = await response.json()
```

**导致的问题：**
1. **401 Unauthorized 错误** - 原生fetch未携带认证token
2. **缺少组织上下文** - 未携带 `X-Organization-ID` header
3. **错误处理缺失** - 未使用统一的错误处理机制
4. **代码重复** - `useFieldMetadata.ts` 中也存在类似问题
5. **架构不一致** - 项目已建立 `request` 工具和API层，但未统一使用

### 1.2 影响范围

经扫描发现以下文件存在类似问题：

| 文件 | fetch/axios混用情况 | 优先级 |
|------|-------------------|--------|
| `WysiwygLayoutDesigner.vue` | 1处fetch | P0 - 阻塞功能 |
| `useFieldMetadata.ts` | 1处fetch | P0 - 阻塞功能 |
| `DynamicDetailPage.vue` | 2处request | P1 - 需审查 |
| `FieldDefinitionForm.vue` | 2处request | P1 - 需审查 |
| 其他5个文件 | - | P2 - 后续优化 |

---

## 二、设计目标

### 2.1 核心目标

建立统一的Composables API层，实现：

1. **统一HTTP调用** - 所有API调用通过 `request` 工具
2. **业务逻辑封装** - 将业务逻辑从组件中剥离
3. **可测试性** - Composable可独立mock测试
4. **类型安全** - 完整的TypeScript类型定义
5. **可复用性** - 跨组件共享业务逻辑

### 2.2 非目标

- 不修改后端API接口
- 不改变现有业务功能逻辑
- 不涉及UI组件重构

---

## 三、架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────┐
│                   Vue Components                    │
│            (PageLayoutList, WysiwygDesigner)        │
└──────────────────────┬──────────────────────────────┘
                       │ 使用
┌──────────────────────▼──────────────────────────────┐
│                  Composables Layer                   │
│         (业务逻辑 + 状态管理 + API编排)              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │useLayoutFields│ │useLayoutSave │ │useFieldTypes│ │
│  └──────────────┘  └──────────────┘  └───────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ 调用
┌──────────────────────▼──────────────────────────────┐
│                   API Layer                         │
│         (@/api/system.ts - 纯HTTP接口封装)           │
└──────────────────────┬──────────────────────────────┘
                       │ 使用
┌──────────────────────▼──────────────────────────────┐
│                  Request Utils                       │
│       (@/utils/request.ts - 拦截器/认证/错误处理)     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                    Backend API                       │
└─────────────────────────────────────────────────────┘
```

### 3.2 新增Composables模块

| 模块 | 职责 | 对应API |
|------|------|---------|
| `useLayoutFields.ts` | 获取对象字段列表、字段类型分组 | `/business-objects/fields/` |
| `useLayoutDesigner.ts` | 布局设计器核心逻辑（加载、保存、发布） | `/page-layouts/*` |
| `useLayoutPreview.ts` | 布局预览相关逻辑 | N/A (本地状态) |

---

## 四、详细规范

### 4.1 Composable命名规范

```typescript
// 命名模式: use<Domain><Action>
// 例如: useLayoutFields, useLayoutSave, useFieldTypes

export function useLayoutFields(objectCode: Ref<string> | string) {
  // 实现逻辑...
}
```

### 4.2 返回值规范

```typescript
interface UseComposableReturn<T> {
  // 数据
  data: Ref<T>

  // 状态
  loading: Ref<boolean>
  error: Ref<Error | null>

  // 方法
  fetch: () => Promise<void>
  refresh: () => Promise<void>
  clear: () => void
}
```

### 4.3 错误处理规范

```typescript
// 使用 request 实例自动处理：
// - 401: 自动跳转登录
// - 403: 显示权限错误
// - 500: 显示服务器错误

// 业务错误手动处理:
try {
  data.value = await apiCall()
} catch (err) {
  if (err instanceof ApiError) {
    // 特定业务逻辑处理
  }
}
```

---

## 五、实施计划

### 5.1 第一阶段：核心Composables创建

| 任务 | 文件 | 优先级 | 估时 |
|------|------|--------|------|
| 创建 `useLayoutFields.ts` | `frontend/src/composables/useLayoutFields.ts` | P0 | 1h |
| 创建 `useLayoutDesigner.ts` | `frontend/src/composables/useLayoutDesigner.ts` | P0 | 1.5h |
| 更新 `composables/index.ts` | `frontend/src/composables/index.ts` | P0 | 0.5h |

### 5.2 第二阶段：组件迁移

| 任务 | 文件 | 优先级 | 估时 |
|------|------|--------|------|
| 重构 `WysiwygLayoutDesigner.vue` | 移除fetch，使用composables | P0 | 2h |
| 重构 `useFieldMetadata.ts` | 移除fetch，使用request | P0 | 1h |
| 更新 `PageLayoutList.vue` | 使用新的composables | P1 | 1h |

### 5.3 第三阶段：API层完善

| 任务 | 文件 | 优先级 | 估时 |
|------|------|--------|------|
| 完善 `system.ts` | 添加缺失的类型定义 | P1 | 1h |

### 5.4 第四阶段：单元测试

| 任务 | 文件 | 优先级 | 估时 |
|------|------|--------|------|
| 创建 `useLayoutFields.test.ts` | 单元测试 | P1 | 2h |
| 创建 `useLayoutDesigner.test.ts` | 单元测试 | P1 | 2h |
| 创建测试工具函数 | `test/utils/composables.ts` | P1 | 1h |

### 5.5 第五阶段：集成测试与文档

| 任务 | 输出 | 优先级 | 估时 |
|------|------|--------|------|
| E2E测试 | Playwright测试套件 | P1 | 2h |
| 更新文档 | `docs/architecture/frontend-api-layer.md` | P2 | 0.5h |

---

## 六、测试规范

### 6.1 单元测试规范

#### 6.1.1 测试文件命名

```
测试文件与源文件同名，后缀为 `.test.ts`
例如: useLayoutFields.ts -> useLayoutFields.test.ts
位置: frontend/src/composables/__tests__/
```

#### 6.1.2 测试覆盖要求

| 模块 | 语句覆盖 | 分支覆盖 | 函数覆盖 |
|------|----------|----------|----------|
| useLayoutFields.ts | ≥80% | ≥75% | 100% |
| useLayoutDesigner.ts | ≥80% | ≥75% | 100% |

#### 6.1.3 测试用例模板

```typescript
// useLayoutFields.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ref } from 'vue'
import { useLayoutFields } from '../useLayoutFields'
import * as api from '@/api/system'

// Mock API模块
vi.mock('@/api/system', () => ({
  businessObjectApi: {
    getFieldsWithContext: vi.fn()
  }
}))

describe('useLayoutFields', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchFields', () => {
    it('should fetch fields successfully', async () => {
      const mockData = {
        editableFields: [
          { code: 'name', name: '名称', fieldType: 'text' }
        ],
        reverseRelations: []
      }
      vi.mocked(api.businessObjectApi.getFieldsWithContext)
        .mockResolvedValue(mockData)

      const { availableFields, fetchFields, loading } = useLayoutFields('Asset')

      await fetchFields()

      expect(availableFields.value).toEqual(mockData.editableFields)
      expect(loading.value).toBe(false)
    })

    it('should handle API errors', async () => {
      vi.mocked(api.businessObjectApi.getFieldsWithContext)
        .mockRejectedValue(new Error('API Error'))

      const { fetchFields, error } = useLayoutFields('Asset')

      await fetchFields()

      expect(error.value).toBeInstanceOf(Error)
      expect(error.value?.message).toBe('API Error')
    })

    it('should use cached data on second call', async () => {
      const mockData = {
        editableFields: [{ code: 'name', name: '名称', fieldType: 'text' }],
        reverseRelations: []
      }
      vi.mocked(api.businessObjectApi.getFieldsWithContext)
        .mockResolvedValue(mockData)

      const { fetchFields } = useLayoutFields('Asset')

      await fetchFields()
      await fetchFields() // 第二次调用

      expect(api.businessObjectApi.getFieldsWithContext).toHaveBeenCalledTimes(1)
    })
  })

  describe('searchFields', () => {
    it('should filter fields by search query', () => {
      const mockFields = [
        { code: 'asset_name', name: '资产名称', fieldType: 'text' },
        { code: 'asset_code', name: '资产编码', fieldType: 'text' },
        { code: 'status', name: '状态', fieldType: 'select' }
      ]
      // Setup mock data...

      const { searchFields } = useLayoutFields('Asset')

      const results = searchFields('资产')

      expect(results).toHaveLength(2)
      expect(results[0].code).toBe('asset_name')
    })
  })
})
```

#### 6.1.4 Mock工具函数

```typescript
// test/utils/composables.ts
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

### 6.2 集成测试规范 (E2E)

#### 6.2.1 Playwright测试场景

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

#### 6.2.2 测试文件模板

```typescript
// e2e/layout-designer.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Layout Designer', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('[name=username]', 'admin')
    await page.fill('[name=password]', 'admin123')
    await page.click('button[type=submit]')
    await page.waitForURL('/')
  })

  test('TC-001: should load field list without 401 error', async ({ page }) => {
    await page.goto('/system/page-layouts')
    await page.click('text=Asset')
    await page.click('text=编辑布局')

    // 等待字段列表加载
    await page.waitForSelector('.field-item')

    // 验证无401错误
    const responses = page.waitForResponse(
      response => !response.url().includes('fields') || response.ok()
    )

    // 验证字段显示
    const fieldItems = await page.locator('.field-item').count()
    expect(fieldItems).toBeGreaterThan(0)
  })

  test('TC-003: should drag field to canvas', async ({ page }) => {
    await page.goto('/system/page-layouts/Asset/edit')

    // 获取第一个字段
    const field = page.locator('.field-item').first()
    const canvas = page.locator('.canvas-area')

    // 拖拽操作
    await field.dragTo(canvas)

    // 验证字段添加成功
    await expect(canvas.locator('.layout-field').first()).toBeVisible()
  })

  test('TC-004: should save layout successfully', async ({ page }) => {
    await page.goto('/system/page-layouts/Asset/edit')

    // 修改布局
    // ... 执行一些修改操作

    // 点击保存
    await page.click('button:has-text("保存")')

    // 验证成功提示
    await expect(page.locator('.el-message--success')).toBeVisible()
  })
})
```

---

### 6.3 测试验收标准

#### 6.3.1 单元测试验收

- [ ] 所有新增Composables有对应测试文件
- [ ] 测试覆盖率达标 (语句≥80%, 分支≥75%)
- [ ] 所有测试用例通过 (`npm run test:unit`)
- [ ] 无console错误或警告

#### 6.3.2 E2E测试验收

- [ ] TC-001 ~ TC-008 全部通过
- [ ] 测试可在CI环境稳定运行
- [ ] 测试执行时间 < 5分钟
- [ ] 有测试报告输出

#### 6.3.3 测试命令

```bash
# 单元测试
npm run test:unit              # 运行所有单元测试
npm run test:unit:coverage    # 带覆盖率报告
npm run test:unit:watch       # 监视模式

# E2E测试
npm run test:e2e               # 运行所有E2E测试
npm run test:e2e:headed        # 有界面模式
npm run test:e2e:debug         # 调试模式

# 特定测试
npm run test:composables        # 只测试Composables
npm run test:layout             # 只测试布局相关
```

---

## 七、验收标准

### 7.1 功能验收

- [ ] 布局设计器能正确加载对象字段列表
- [ ] 布局保存/发布功能正常工作
- [ ] 所有API调用携带正确的认证头
- [ ] 错误处理统一且友好

### 7.2 代码规范验收

- [ ] 所有Vue组件中无 `fetch()` 调用
- [ ] 所有API调用通过 `request` 工具
- [ ] 新增Composables有完整TypeScript类型
- [ ] 代码通过ESLint检查
- [ ] **单元测试覆盖率≥80%**
- [ ] **所有测试用例通过**

### 7.3 性能验收

- [ ] 字段列表加载时间 < 500ms
- [ ] 布局保存响应时间 < 1s
- [ ] 无重复API调用

### 7.4 测试验收 (新增)

- [ ] E2E测试 TC-001 ~ TC-008 全部通过
- [ ] 单元测试覆盖率达标
- [ ] CI/CD测试管道配置完成

---

## 八、风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 破坏现有功能 | 中 | 高 | 充分测试，分阶段发布 |
| API不兼容 | 低 | 中 | 保持后端API不变 |
| 性能下降 | 低 | 中 | 引入缓存机制 |

---

## 八、附录

### 8.1 参考文档

- `docs/plans/common_base_features/frontend_api_standardization_design.md`
- `frontend/src/api/system.ts`
- `frontend/src/utils/request.ts`

### 8.2 相关Issue

解决 `WysiwygLayoutDesigner.vue` 中的401错误问题

---

## 变更历史

| 日期 | 版本 | 作者 | 变更说明 |
|------|------|------|----------|
| 2025-02-04 | v1.0 | Claude | 初始版本 |
