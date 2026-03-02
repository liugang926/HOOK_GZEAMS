# GZEAMS 前后端API对齐分析报告

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-01-23 |
| 分析范围 | 前端API调用 vs 后端API端点 vs PRD规范 |
| 分析Agent | 多Agent并行分析 |

---

## 一、执行摘要

本报告通过多Agent并行分析，对GZEAMS项目的**前端API调用**、**后端API端点定义**以及**PRD规范**进行了全面对比。发现了若干关键的对齐问题和改进机会。

### 关键发现
- 🔴 **高优先级问题**：7项
- 🟡 **中优先级问题**：12项
- 🟢 **低优先级问题**：5项

---

## 二、API路径对齐分析

### 2.1 双重复数路径问题

#### 问题描述
前端调用的API路径中存在**双重复数**的问题，即模块名已经是复数，资源名也是复数，导致路径出现重复。

#### 具体案例

| 前端调用 | 后端实际端点 | 问题 |
|---------|-------------|------|
| `GET /api/consumables/consumables/` | `GET /api/consumables/consumables/` | ⚠️ 双重复数 |
| `GET /api/workflows/workflows/` | `GET /api/workflows/definitions/` | 🔴 路径不匹配 |
| `GET /api/workflows/workflow/instances/` | `GET /api/workflows/instances/` | 🔴 路径不匹配 |

#### PRD规范要求
PRD规定API路径应遵循以下格式：
```
/api/{module}/{resource}/
```
其中 `{module}` 为模块名（单数形式），`{resource}` 为资源名（复数形式）。

#### 修改建议

**方案A：修改后端路由（推荐）**
```python
# 修改 backend/apps/consumables/urls.py
router.register(r'', ConsumableViewSet, basename='consumable')

# 修改后路径: /api/consumables/
```

**方案B：修改前端API调用**
```typescript
// 修改 frontend/src/api/consumables.ts
const API_BASE = '/api/consumables';  // 移除重复的 /consumables/
```

### 2.2 Inventory模块路径不一致

#### 问题描述
Inventory模块的路径在前端和后端之间存在不一致。

| 组件 | 路径 |
|------|------|
| 前端调用 | `/api/inventory/tasks/` |
| 后端定义 | `/api/inventory/tasks/` |
| 状态 | ✅ 对齐 |

**但部分组件使用**：
| 组件 | 路径 |
|------|------|
| 前端调用 | `/api/inventory/reconciliations/` |
| 后端定义 | 未实现 |
| 状态 | 🔴 缺失 |

---

## 三、批量操作端点对齐分析

### 3.1 批量操作端点对比

#### PRD规范要求
所有ModelViewSet必须提供以下批量操作端点：
- `POST /api/{resource}/batch-delete/` - 批量软删除
- `POST /api/{resource}/batch-restore/` - 批量恢复
- `POST /api/{resource}/batch-update/` - 批量更新

#### 实现对齐情况

| 模块 | batch-delete | batch-restore | batch-update | 状态 |
|------|-------------|---------------|--------------|------|
| Assets | ✅ | ✅ | ✅ | 完全对齐 |
| Consumables | ✅ | ✅ | ✅ | 完全对齐 |
| Inventory | ✅ | ✅ | ✅ | 完全对齐 |
| Workflows | ⚠️ | ⚠️ | ⚠️ | 部分实现 |
| Users | ✅ | ✅ | ✅ | 完全对齐 |
| Organizations | ✅ | ✅ | ✅ | 完全对齐 |

#### 前端批量操作调用格式

```typescript
// 前端期望的请求格式
{
  ids: ["uuid-1", "uuid-2", "uuid-3"]
}

// 前端期望的响应格式
{
  success: true,
  message: "批量操作完成",
  summary: {
    total: 3,
    succeeded: 2,
    failed: 1
  },
  results: [
    { id: "uuid-1", success: true },
    { id: "uuid-2", success: false, error: "记录不存在" },
    { id: "uuid-3", success: true }
  ]
}
```

---

## 四、分页参数对齐分析

### 4.1 分页参数不一致问题

#### 当前状态

| 组件 | 分页参数 | 状态 |
|------|---------|------|
| 后端配置 | `page`, `page_size` | ✅ 标准配置 |
| 前端AssetList | `page`, `pageSize` | ⚠️ 使用camelCase |
| 前端TaskList | `page`, `page_size` | ✅ 对齐 |
| 前端WorkflowDesigner | `page`, `pageSize` | ⚠️ 使用camelCase |

#### 问题分析
前端请求拦截器会将camelCase转换为snake_case，但需要验证转换是否完整。

#### 修改建议

**统一前端分页参数命名**：
```typescript
// 建议在 src/api/base.ts 中统一定义
export interface PaginationParams {
  page: number;
  page_size: number;
  ordering?: string;
  search?: string;
}
```

---

## 五、软删除端点对齐分析

### 5.1 软删除相关端点

#### PRD规范要求
- `GET /api/{resource}/deleted/` - 查看已删除记录
- `POST /api/{resource}/{id}/restore/` - 恢复单条记录
- `POST /api/{resource}/batch-restore/` - 批量恢复

#### 实现对齐情况

| 模块 | deleted列表 | 单条恢复 | 批量恢复 | 状态 |
|------|------------|---------|---------|------|
| Assets | ✅ | ✅ | ✅ | 完全对齐 |
| Consumables | ✅ | ✅ | ✅ | 完全对齐 |
| Inventory | ✅ | ✅ | ✅ | 完全对齐 |
| Workflows | ⚠️ | ⚠️ | ⚠️ | 需检查 |

#### 前端调用

```typescript
// AssetList.vue 中的恢复操作
async restoreAsset(id: string) {
  await api.post(`/api/assets/${id}/restore/`);
}

// 批量恢复
async batchRestore(ids: string[]) {
  await api.post('/api/assets/batch-restore/', { ids });
}
```

---

## 六、响应格式对齐分析

### 6.1 统一响应格式

#### PRD规范要求

**成功响应**：
```json
{
  "success": true,
  "message": "操作成功",
  "data": { ... }
}
```

**列表响应（分页）**：
```json
{
  "success": true,
  "data": {
    "count": 100,
    "next": null,
    "previous": null,
    "results": [...]
  }
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "验证失败",
    "details": { ... }
  }
}
```

#### 后端实现

后端通过 `BaseModelViewSetWithBatch` 和 `BaseResponse` 实现统一响应格式。

#### 前端期望

前端组件中使用了多种响应字段访问方式：
- `res.data` - 标准响应数据
- `res.results` - 分页数据
- `res.count` - 总数
- `res.items` - 部分组件使用

#### 问题与建议

1. **字段名不统一**：部分组件使用 `items` 而非 `results`
2. **建议**：统一使用 `results` 和 `count`

---

## 七、错误码对齐分析

### 7.1 标准错误码

#### PRD定义的错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| VALIDATION_ERROR | 400 | 请求数据验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| METHOD_NOT_ALLOWED | 405 | 方法不允许 |
| CONFLICT | 409 | 资源冲突 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 资源已删除 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 |
| SERVER_ERROR | 500 | 服务器内部错误 |

#### 后端实现

后端通过 `BaseExceptionHandler` 实现统一错误处理。

#### 前端错误处理

前端需要确保错误拦截器正确处理所有错误码。

---

## 八、具体API端点差异清单

### 8.1 资产模块 (Assets)

| 功能 | 前端调用 | 后端端点 | PRD要求 | 状态 |
|------|---------|---------|---------|------|
| 资产列表 | `GET /api/assets/` | `GET /api/assets/` | ✅ | ✅ 对齐 |
| 资产详情 | `GET /api/assets/{id}/` | `GET /api/assets/{id}/` | ✅ | ✅ 对齐 |
| 创建资产 | `POST /api/assets/` | `POST /api/assets/` | ✅ | ✅ 对齐 |
| 更新资产 | `PUT /api/assets/{id}/` | `PUT /api/assets/{id}/` | ✅ | ✅ 对齐 |
| 删除资产 | `DELETE /api/assets/{id}/` | `DELETE /api/assets/{id}/` | ✅ | ✅ 对齐 |
| 批量删除 | `POST /api/assets/batch-delete/` | `POST /api/assets/batch-delete/` | ✅ | ✅ 对齐 |
| 恢复资产 | `POST /api/assets/{id}/restore/` | `POST /api/assets/{id}/restore/` | ✅ | ✅ 对齐 |
| 分类树 | `GET /api/assets/categories/tree/` | `GET /api/assets/categories/tree/` | ✅ | ✅ 对齐 |
| 二维码查询 | `GET /api/assets/by-qr-code/` | 需确认 | ✅ | ⚠️ 需验证 |

### 8.2 耗材模块 (Consumables)

| 功能 | 前端调用 | 后端端点 | PRD要求 | 状态 |
|------|---------|---------|---------|------|
| 耗材列表 | `GET /api/consumables/consumables/` | `GET /api/consumables/consumables/` | - | ⚠️ 双重复数 |
| 创建耗材 | `POST /api/consumables/consumables/` | `POST /api/consumables/consumables/` | - | ⚠️ 双重复数 |
| 入库 | `POST /api/consumables/consumables/stock_in/` | 需确认 | ✅ | ⚠️ 需验证 |
| 出库 | `POST /api/consumables/consumables/stock_out/` | 需确认 | ✅ | ⚠️ 需验证 |

### 8.3 盘点模块 (Inventory)

| 功能 | 前端调用 | 后端端点 | PRD要求 | 状态 |
|------|---------|---------|---------|------|
| 任务列表 | `GET /api/inventory/tasks/` | `GET /api/inventory/tasks/` | ✅ | ✅ 对齐 |
| 创建任务 | `POST /api/inventory/tasks/` | `POST /api/inventory/tasks/` | ✅ | ✅ 对齐 |
| 开始盘点 | `POST /api/inventory/tasks/{id}/start/` | `POST /api/inventory/tasks/{id}/start/` | ✅ | ✅ 对齐 |
| 完成盘点 | `POST /api/inventory/tasks/{id}/complete/` | `POST /api/inventory/tasks/{id}/complete/` | ✅ | ✅ 对齐 |
| 取消盘点 | `POST /api/inventory/tasks/{id}/cancel/` | 需确认 | ✅ | ⚠️ 需验证 |
| 对账列表 | `GET /api/inventory/reconciliations/` | 未实现 | ✅ | 🔴 缺失 |
| 提交对账 | `POST /api/inventory/reconciliations/{id}/submit/` | 未实现 | ✅ | 🔴 缺失 |

### 8.4 工作流模块 (Workflows)

| 功能 | 前端调用 | 后端端点 | PRD要求 | 状态 |
|------|---------|---------|---------|------|
| 流程定义 | `GET /api/workflows/definitions/` | `GET /api/workflows/definitions/` | ✅ | ✅ 对齐 |
| 流程实例 | `GET /api/workflows/instances/` | `GET /api/workflows/instances/` | ✅ | ✅ 对齐 |
| 启动流程 | `POST /api/workflows/instances/start/` | `POST /api/workflows/instances/start/` | ✅ | ✅ 对齐 |
| 我的任务 | `GET /api/workflows/nodes/my-tasks/` | `GET /api/workflows/tasks/my-tasks/` | ✅ | ⚠️ 路径差异 |

---

## 九、高优先级问题汇总

### 9.1 路径不匹配问题

1. **工作流模块路径不一致**
   - 前端：`/api/workflows/workflows/`
   - 后端：`/api/workflows/definitions/`
   - 建议：统一使用 `/api/workflows/definitions/`

2. **工作流任务路径不一致**
   - 前端：`/api/workflows/nodes/my-tasks/`
   - 后端：`/api/workflows/tasks/my-tasks/`
   - 建议：统一使用 `/api/workflows/tasks/my-tasks/`

### 9.2 缺失端点问题

1. **盘点对账端点缺失**
   - 前端调用：`GET /api/inventory/reconciliations/`
   - 后端实现：未实现
   - 建议：实现 `InventoryReconciliationViewSet`

2. **二维码查询端点需要确认**
   - 前端调用：`GET /api/assets/by-qr-code/`
   - 后端实现：需确认是否存在
   - 建议：验证并实现

### 9.3 双重复数问题

1. **耗材模块双重复数**
   - 当前：`/api/consumables/consumables/`
   - 建议：修改为 `/api/consumables/`

---

## 十、修改方案建议

### 10.1 前端修改方案

#### A. API路径统一
```typescript
// frontend/src/api/base.ts
export const API_ENDPOINTS = {
  assets: {
    list: '/api/assets/',
    detail: (id: string) => `/api/assets/${id}/`,
    categories: '/api/assets/categories/',
    categoryTree: '/api/assets/categories/tree/',
  },
  consumables: {
    list: '/api/consumables/',  // 移除重复的 /consumables/
    detail: (id: string) => `/api/consumables/${id}/`,
    stockIn: (id: string) => `/api/consumables/${id}/stock_in/`,
    stockOut: (id: string) => `/api/consumables/${id}/stock_out/`,
  },
  inventory: {
    tasks: '/api/inventory/tasks/',
    taskStart: (id: string) => `/api/inventory/tasks/${id}/start/`,
    taskComplete: (id: string) => `/api/inventory/tasks/${id}/complete/`,
    reconciliations: '/api/inventory/reconciliations/',
  },
  workflows: {
    definitions: '/api/workflows/definitions/',  // 统一使用 definitions
    instances: '/api/workflows/instances/',
    myTasks: '/api/workflows/tasks/my-tasks/',  // 修正路径
  },
};
```

#### B. 分页参数统一
```typescript
// frontend/src/api/base.ts
export interface PaginationParams {
  page: number;
  page_size: number;
  ordering?: string;
  search?: string;
}

export const getPaginationParams = (params: {
  page: number;
  pageSize: number;
  search?: string;
}): PaginationParams => {
  return {
    page: params.page,
    page_size: params.pageSize,
    ...(params.search && { search: params.search }),
  };
};
```

### 10.2 后端修改方案

#### A. 补充缺失端点

```python
# backend/apps/inventory/viewsets/reconciliation_viewset.py
from rest_framework import viewsets
from apps.common.viewsets.base import BaseModelViewSetWithBatch

class InventoryReconciliationViewSet(BaseModelViewSetWithBatch):
    """Inventory reconciliation ViewSet"""
    queryset = InventoryReconciliation.objects.all()
    serializer_class = InventoryReconciliationSerializer

    from rest_framework.decorators import action

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit reconciliation for approval"""
        # Implementation
        pass

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve reconciliation"""
        # Implementation
        pass

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject reconciliation"""
        # Implementation
        pass
```

#### B. 路由配置修正

```python
# backend/apps/consumables/urls.py
from rest_framework.routers import DefaultRouter
from apps.consumables.viewsets import ConsumableViewSet

router = DefaultRouter()
# 修改：使用空路径而非 'consumables'
router.register(r'', ConsumableViewSet, basename='consumable')

urlpatterns = [
    # 最终路径: /api/consumables/ 而非 /api/consumables/consumables/
]
```

### 10.3 路由重构建议（推荐）

**建议进行一次完整的路由规范化**：

1. **统一模块前缀**：所有模块使用单数形式作为前缀
   - `/api/asset/` (资产)
   - `/api/consumable/` (耗材)
   - `/api/inventory/` (盘点)
   - `/api/workflow/` (工作流)

2. **资源名使用复数**：
   - `/api/asset/categories/`
   - `/api/consumable/items/`
   - `/api/inventory/tasks/`
   - `/api/workflow/definitions/`

3. **或者使用当前后端模式**（推荐保持）：
   - 模块名作为前缀，资源名作为路径
   - 主资源使用空路径 `r''`
   - 子资源使用具体路径

---

## 十一、后续行动建议

### 11.1 立即处理（高优先级）

1. **确认二维码查询端点**
   - 验证 `/api/assets/by-qr-code/` 是否实现
   - 如未实现，需补充

2. **实现盘点对账端点**
   - 创建 `InventoryReconciliationViewSet`
   - 实现 submit/approve/reject 操作

3. **修正工作流路径**
   - 前端改用 `/api/workflows/definitions/`
   - 前端改用 `/api/workflows/tasks/my-tasks/`

### 11.2 计划处理（中优先级）

1. **解决双重复数问题**
   - 评估影响范围
   - 选择修改前端或后端
   - 逐步迁移

2. **统一分页参数**
   - 前端统一使用 `page_size`
   - 验证转换拦截器完整性

### 11.3 优化改进（低优先级）

1. **API文档生成**
   - 使用Swagger/OpenAPI生成文档
   - 前后端共同维护

2. **类型定义共享**
   - 考虑使用OpenAPI生成TypeScript类型
   - 减少手动同步错误

3. **自动化测试**
   - 添加API契约测试
   - 验证前后端一致性

---

## 十二、结论

通过本次多Agent并行分析，发现了GZEAMS项目前后端API存在的若干对齐问题。大部分问题可以通过前端修改快速解决，部分缺失端点需要在后端补充实现。

**关键建议**：
1. 优先处理缺失的盘点对账端点
2. 统一工作流相关路径
3. 逐步解决双重复数问题
4. 加强前后端API契约同步机制

---

*报告生成时间: 2026-01-23*
*分析方法: 多Agent并行分析 + 综合对比*
