# Phase 4.5 盘点对账 - PRD与代码实现差异修复方案

> **实施状态**: ✅ 已完成
> **实施日期**: 2025-01-14

## 问题概述

经深度分析，`phase4_5_inventory_reconciliation` 模块存在严重的 PRD 与实现脱节问题：

- **核心业务闭环缺失**：差异模型、分析服务、认定流程、调账处理均未实现
- **字段命名不一致**：前后端字段命名风格未统一（CamelCase vs snake_case）
- **前端为 Mock 实现**：未对接真实 API，枚举值不完整

---

## 一、实施完成情况

### 1.1 后端模型层 ✅ 已完成

**文件**: `backend/apps/inventory/models.py`

| 模型 | 状态 | 说明 |
|-----|------|-----|
| `InventoryTask` | ✅ 已更新 | 新增统计字段、状态枚举 |
| `InventoryTaskItem` | ✅ 已更新 | 完整的快照+扫描字段 |
| `InventoryDifference` | ✅ 新增 | 完整的差异记录模型 |
| `ScanningLog` | ✅ 已更新 | 审计日志记录 |

**InventoryDifference 模型字段**:
```python
class InventoryDifference(BaseModel):
    # 差异类型: surplus, loss, location_mismatch, condition_mismatch, value_mismatch
    difference_type: CharField

    # 差异状态: pending, confirmed, adjusting, resolved, rejected
    status: CharField

    # 账面信息
    book_quantity, book_location, book_condition, book_value

    # 实盘信息
    actual_quantity, actual_location, actual_condition, actual_value

    # 差异计算
    quantity_diff, value_diff

    # 认定信息
    confirmed_by, confirmed_at, confirmation_note

    # 处理方式: adjustment, write_off, transfer, ignore, manual_fix
    resolution_method

    # 关联
    task (FK), item (FK), asset (FK), adjustment_operation (FK)
```

### 1.2 后端服务层 ✅ 已完成

| 服务 | 文件 | 状态 |
|-----|------|-----|
| `DifferenceAnalysisService` | `services/difference_analysis.py` | ✅ 已实现 |
| `DifferenceConfirmationService` | `services/difference_confirmation.py` | ✅ 已实现 |

**DifferenceAnalysisService 方法**:
- `analyze_task(task_id)` - 分析任务差异
- `detect_surplus_assets(task_id, scanned_codes)` - 检测盘盈
- `detect_loss_assets(task_id)` - 检测盘亏
- `get_difference_summary(task_id)` - 获取差异汇总

**DifferenceConfirmationService 方法**:
- `confirm_difference(difference_id, confirmed_by_id, resolution_method, confirmation_note)` - 认定差异
- `batch_confirm_differences(difference_ids, ...)` - 批量认定
- `reject_difference(difference_id, ...)` - 驳回差异
- `get_confirmation_statistics(task_id)` - 获取统计

### 1.3 后端 API 层 ✅ 已完成

| 组件 | 文件 | 状态 |
|-----|------|-----|
| Serializers | `serializers.py` | ✅ 已实现 |
| ViewSets | `views.py` | ✅ 已实现 |
| URLs | `urls.py` | ✅ 已配置 |

**API 端点清单**:
```
盘点任务:
- GET    /api/inventory/tasks/                      列表
- POST   /api/inventory/tasks/                      创建
- GET    /api/inventory/tasks/{id}/                 详情
- POST   /api/inventory/tasks/{id}/start/           开始
- POST   /api/inventory/tasks/{id}/submit/          提交
- POST   /api/inventory/tasks/{id}/analyze/         差异分析
- GET    /api/inventory/tasks/{id}/differences/     差异列表
- GET    /api/inventory/tasks/{id}/summary/         统计汇总

盘点差异:
- GET    /api/inventory/differences/                列表
- POST   /api/inventory/differences/confirm/        认定
- POST   /api/inventory/differences/batch-confirm/  批量认定
- POST   /api/inventory/differences/{id}/reject/    驳回
- GET    /api/inventory/differences/statistics/     统计
```

---

## 二、字段命名统一方案 ✅ 已完成

### 2.1 命名约定

| 层级 | 命名风格 | 示例 |
|-----|---------|------|
| 后端模型/API | `snake_case` | `task_no`, `task_name`, `reconciliation_status` |
| 前端业务代码 | `camelCase` | `taskNo`, `taskName`, `reconciliationStatus` |

### 2.2 字段映射对照表

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|---------------------|---------------------|------|
| `task_no` | `taskNo` | 盘点单号 |
| `task_name` | `taskName` | 盘点名称 |
| `planned_at` | `plannedAt` | 计划日期 |
| `started_at` | `startedAt` | 开始时间 |
| `completed_at` | `completedAt` | 完成时间 |
| `total_assets` | `totalAssets` | 应盘资产总数 |
| `scanned_count` | `scannedCount` | 已扫描数量 |
| `normal_count` | `normalCount` | 正常数量 |
| `difference_count` | `differenceCount` | 差异数量 |
| `reconciliation_status` | `reconciliationStatus` | 核对状态 |
| `difference_type` | `differenceType` | 差异类型 |
| `book_quantity` | `bookQuantity` | 账面数量 |
| `actual_quantity` | `actualQuantity` | 实盘数量 |
| `quantity_diff` | `quantityDiff` | 数量差异 |
| `confirmed_by` | `confirmedBy` | 认定人 |
| `confirmed_at` | `confirmedAt` | 认定时间 |
| `confirmation_note` | `confirmationNote` | 认定说明 |
| `resolution_method` | `resolutionMethod` | 处理方式 |

### 2.3 转换实现

**文件**: `frontend/src/api/index.js`

```javascript
// 请求拦截器: camelCase -> snake_case
api.interceptors.request.use((config) => {
  if (config.data) config.data = objectToSnakeCase(config.data)
  if (config.params) config.params = objectToSnakeCase(config.params)
  return config
})

// 响应拦截器: snake_case -> camelCase
api.interceptors.response.use((response) => {
  return objectToCamelCase(response.data)
})
```

---

## 三、前端实现 ✅ 已完成

### 3.1 API 模块

**文件**: `frontend/src/api/inventory/index.js`

| 函数 | 说明 |
|-----|------|
| `getInventoryTasks(params)` | 获取任务列表 |
| `createInventoryTask(data)` | 创建任务 |
| `startInventoryTask(id)` | 开始盘点 |
| `analyzeTaskDifferences(id, options)` | 差异分析 |
| `getDifferences(params)` | 获取差异列表 |
| `confirmDifference(data)` | 认定差异 |
| `batchConfirmDifferences(data)` | 批量认定 |

### 3.2 常量定义

**文件**: `frontend/src/constants/inventory.js`

```javascript
// 任务状态
export const TaskStatus = {
  DRAFT: 'draft',
  IN_PROGRESS: 'in_progress',
  SUBMITTED: 'submitted',
  ANALYZING: 'analyzing',
  CONFIRMED: 'confirmed',
  COMPLETED: 'completed',
}

// 差异类型
export const DifferenceType = {
  SURPLUS: 'surplus',           // 盘盈
  LOSS: 'loss',                 // 盘亏
  LOCATION_MISMATCH: 'location_mismatch',
  CONDITION_MISMATCH: 'condition_mismatch',
}

// 处理方式
export const ResolutionMethod = {
  ADJUSTMENT: 'adjustment',
  WRITE_OFF: 'write_off',
  TRANSFER: 'transfer',
  IGNORE: 'ignore',
}
```

---

## 四、文件清单

### 后端文件

| 文件 | 状态 | 行数 |
|-----|------|-----|
| `backend/apps/inventory/models.py` | ✅ 已更新 | ~400 |
| `backend/apps/inventory/services/__init__.py` | ✅ 新增 | ~10 |
| `backend/apps/inventory/services/difference_analysis.py` | ✅ 新增 | ~200 |
| `backend/apps/inventory/services/difference_confirmation.py` | ✅ 新增 | ~180 |
| `backend/apps/inventory/serializers.py` | ✅ 已更新 | ~400 |
| `backend/apps/inventory/views.py` | ✅ 已更新 | ~540 |
| `backend/apps/inventory/urls.py` | ✅ 已更新 | ~70 |

### 前端文件

| 文件 | 状态 | 行数 |
|-----|------|-----|
| `frontend/src/api/index.js` | ✅ 已更新 | ~200 |
| `frontend/src/api/inventory/index.js` | ✅ 新增 | ~250 |
| `frontend/src/constants/inventory.js` | ✅ 新增 | ~150 |

---

## 五、待办事项 (TODO)

| 优先级 | 任务 | 说明 |
|-------|------|-----|
| P0 | 数据库迁移 | `python manage.py makemigrations && migrate` |
| P1 | AssetOperation 集成 | 调账操作与资产模块集成 |
| P1 | 前端视图组件 | 创建任务列表、差异处理页面 |
| P2 | 单元测试 | 为 Service 层编写测试 |

---

## 六、验证检查清单

完成后需验证：

- [x] InventoryDifference 模型已创建
- [x] DifferenceAnalysisService 已实现
- [x] DifferenceConfirmationService 已实现
- [x] Serializers 字段映射完整
- [x] ViewSets API 端点已配置
- [x] 前端 API 模块已创建
- [x] 前后端字段转换拦截器已实现
- [x] 常量和枚举定义已导出
- [ ] 数据库迁移已执行
- [ ] 前端视图组件已对接
- [ ] 集成测试通过
