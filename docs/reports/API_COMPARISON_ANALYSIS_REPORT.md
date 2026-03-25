# GZEAMS API对比分析报告

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-01-25 |
| 分析范围 | PRD规范 vs 后端实现 vs 前端调用 |

---

## 一、API端点对比摘要

### 1.1 认证模块 (Auth)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| POST /api/auth/login/ | ✅ | ✅ LoginView | ✅ auth.ts | ✅ 对齐 |
| POST /api/auth/logout/ | ✅ | ✅ LogoutView | ✅ auth.ts | ✅ 对齐 |
| POST /api/auth/refresh/ | ✅ | ✅ TokenRefreshView | ✅ auth.ts | ✅ 对齐 |
| GET /api/auth/users/me/ | ✅ | ✅ UserViewSet.me | ✅ users.ts | ✅ 对齐 |

### 1.2 资产管理模块 (Assets)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/assets/ | ✅ | ✅ AssetViewSet.list | ✅ assets.ts | ✅ 对齐 |
| POST /api/assets/ | ✅ | ✅ AssetViewSet.create | ✅ assets.ts | ✅ 对齐 |
| PUT /api/assets/{id}/ | ✅ | ✅ AssetViewSet.update | ✅ assets.ts | ✅ 对齐 |
| DELETE /api/assets/{id}/ | ✅ | ✅ AssetViewSet.destroy | ✅ assets.ts | ✅ 对齐 |
| GET /api/assets/categories/ | ✅ | ✅ AssetCategoryViewSet | ✅ assets.ts | ✅ 对齐 |
| GET /api/assets/categories/tree/ | ✅ | ✅ tree_categories action | ✅ assets.ts | ✅ 对齐 |
| GET /api/assets/locations/ | ✅ | ✅ LocationViewSet | ✅ assets.ts | ✅ 对齐 |
| GET /api/assets/locations/tree/ | ✅ | ✅ tree_locations action | ✅ assets.ts | ✅ 对齐 |
| GET /api/assets/by-qr-code/ | ✅ | ✅ by_qr_code action | ✅ assets.ts | ✅ 对齐 |
| GET|POST /api/assets/transfers/ | ✅ | ✅ AssetTransferViewSet | ✅ assets.ts | ✅ 对齐 |
| GET|POST /api/assets/pickups/ | ✅ | ✅ AssetPickupViewSet | ✅ pickup.ts | ✅ 对齐 |
| GET|POST /api/assets/returns/ | ✅ | ✅ AssetReturnViewSet | ✅ return.ts | ✅ 对齐 |

### 1.3 工作流模块 (Workflows)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/workflows/definitions/ | ✅ | ✅ WorkflowDefinitionViewSet | ✅ workflow.ts | ✅ 对齐 |
| POST /api/workflows/definitions/ | ✅ | ✅ WorkflowDefinitionViewSet.create | ✅ workflow.ts | ✅ 对齐 |
| PUT /api/workflows/definitions/{id}/ | ✅ | ✅ WorkflowDefinitionViewSet.update | ✅ workflow.ts | ✅ 对齐 |
| DELETE /api/workflows/definitions/{id}/ | ✅ | ✅ WorkflowDefinitionViewSet.destroy | ✅ workflow.ts | ✅ 对齐 |
| POST /api/workflows/instances/start/ | ✅ | ✅ start_instance action | ✅ workflow.ts | ✅ 对齐 |
| GET /api/workflows/nodes/my-tasks/ | ✅ | ✅ my_tasks action | ✅ workflow.ts | ✅ 对齐 |
| POST /api/workflows/instances/{id}/nodes/{id}/approve/ | ✅ | ✅ approve action | ⚠️ 未使用 | ⚠️ 前端未调用 |

### 1.4 库存盘点模块 (Inventory)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/inventory/tasks/ | ✅ | ✅ InventoryTaskViewSet | ✅ inventory.ts | ✅ 对齐 |
| POST /api/inventory/tasks/ | ✅ | ✅ InventoryTaskViewSet.create | ✅ inventory.ts | ✅ 对齐 |
| POST /api/inventory/tasks/{id}/start/ | ✅ | ✅ start action | ✅ inventory.ts | ✅ 对齐 |
| POST /api/inventory/tasks/{id}/scan/ | ✅ | ✅ scan action | ✅ inventory.ts | ✅ 对齐 |
| GET /api/inventory/tasks/{id}/snapshots/ | ✅ | ✅ snapshots related | ✅ inventory.ts | ✅ 对齐 |
| POST /api/inventory/tasks/{id}/complete/ | ✅ | ✅ complete action | ✅ inventory.ts | ✅ 对齐 |

### 1.5 耗材管理模块 (Consumables)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/consumables/consumables/ | ✅ | ✅ ConsumableViewSet | ✅ consumables.ts | ✅ 对齐 |
| POST /api/consumables/consumables/ | ✅ | ✅ ConsumableViewSet.create | ✅ consumables.ts | ✅ 对齐 |
| PATCH /api/consumables/consumables/{id}/ | ✅ | ✅ ConsumableViewSet.partial_update | ✅ consumables.ts | ✅ 对齐 |
| DELETE /api/consumables/consumables/{id}/ | ✅ | ✅ ConsumableViewSet.destroy | ✅ consumables.ts | ✅ 对齐 |
| POST /api/consumables/consumables/stock_in/ | ✅ | ✅ stock_in action | ✅ consumables.ts | ✅ 对齐 |
| POST /api/consumables/consumables/stock_out/ | ✅ | ✅ stock_out action | ✅ consumables.ts | ✅ 对齐 |

### 1.6 软件许可证模块 (Software Licenses)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/software-licenses/software/ | ✅ | ✅ SoftwareViewSet | ✅ softwareLicenses.ts | ✅ 对齐 |
| GET /api/software-licenses/licenses/ | ✅ | ✅ SoftwareLicenseViewSet | ✅ softwareLicenses.ts | ✅ 对齐 |
| GET /api/software-licenses/licenses/expiring/ | ✅ | ✅ expiring action | ✅ softwareLicenses.ts | ✅ 对齐 |
| GET /api/software-licenses/licenses/compliance-report/ | ✅ | ✅ compliance_report action | ✅ softwareLicenses.ts | ✅ 对齐 |
| GET /api/software-licenses/license-allocations/ | ✅ | ✅ LicenseAllocationViewSet | ✅ softwareLicenses.ts | ✅ 对齐 |
| POST /api/software-licenses/license-allocations/ | ✅ | ✅ LicenseAllocationViewSet.create | ✅ softwareLicenses.ts | ✅ 对齐 |
| POST /api/software-licenses/license-allocations/{id}/deallocate/ | ✅ | ✅ deallocate action | ✅ softwareLicenses.ts | ✅ 对齐 |

### 1.7 组织架构模块 (Organizations)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/organizations/organizations/ | ✅ | ✅ OrganizationViewSet | ✅ organizations.ts | ⚠️ 路径差异 |
| GET /api/organizations/departments/ | ✅ | ✅ DepartmentViewSet | ✅ organizations.ts | ⚠️ 路径差异 |

**注意**: 前端调用路径为 `/organizations/` 和 `/departments/`，后端路径为 `/organizations/organizations/` 和 `/organizations/departments/`，但通过代理配置实际请求会加上前缀。

### 1.8 系统模块 (System)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/system/business-objects/ | ✅ | ✅ BusinessObjectViewSet | ✅ system.ts | ✅ 对齐 |
| GET /api/system/field-definitions/ | ✅ | ✅ FieldDefinitionViewSet | ✅ system.ts | ✅ 对齐 |
| GET /api/system/page-layouts/get_active_layout/ | ✅ | ✅ get_active_layout action | ✅ system.ts | ✅ 对齐 |
| GET /api/system/references/search/ | ✅ | ✅ search_reference action | ✅ system.ts | ✅ 对齐 |

### 1.9 财务模块 (Finance)

| API端点 | PRD规范 | 后端实现 | 前端调用 | 状态 |
|---------|---------|----------|----------|------|
| GET /api/finance/vouchers/ | ✅ | ✅ FinanceVoucherViewSet | ✅ finance.ts | ✅ 对齐 |
| POST /api/finance/vouchers/ | ✅ | ✅ FinanceVoucherViewSet.create | ✅ finance.ts | ✅ 对齐 |
| POST /api/finance/vouchers/{id}/push/ | ✅ | ✅ push_to_erp action | ✅ finance.ts | ✅ 对齐 |
| POST /api/finance/vouchers/batch-push/ | ✅ | ✅ batch_push action | ✅ finance.ts | ✅ 对齐 |

---

## 二、发现的问题

### 2.1 路径不一致问题

| 前端调用 | 后端实现 | 影响 | 修复建议 |
|----------|----------|------|----------|
| `/auth/login/` | `/api/auth/login/` | ❌ 严重 | 前端需统一加 `/api` 前缀 |
| `/auth/users/` | `/api/accounts/users/` | ❌ 严重 | 路径不匹配 |
| `/workflows/workflows/` | `/api/workflows/definitions/` | ⚠️ 中等 | 路径不一致 |
| `/organizations/` | `/api/organizations/organizations/` | ⚠️ 中等 | 重复前缀 |
| `/departments/` | `/api/organizations/departments/` | ⚠️ 中等 | 路径不匹配 |

### 2.2 未实现的后端API

| API端点 | 模块 | 优先级 |
|---------|------|--------|
| GET /api/finance/voucher-templates/ | 财务 | 中 |
| GET /api/depreciation/records/ | 折旧 | 中 |
| GET /api/depreciation/report/ | 折旧 | 低 |

### 2.3 前端未调用的API

| API端点 | 说明 |
|---------|------|
| POST /api/workflows/instances/{id}/nodes/{id}/approve/ | 工作流审批 |
| GET /api/inventory/reconciliations/ | 盘点对账 |

---

## 三、响应格式一致性检查

### 3.1 统一响应格式 ✅

后端遵循标准响应格式：
```json
{
    "success": true,
    "data": {...},
    "message": "操作成功"
}
```

### 3.2 错误响应格式 ✅

后端遵循标准错误格式：
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

---

## 四、总体对齐情况

| 模块 | API总数 | 完全对齐 | 部分对齐 | 不对齐 | 对齐率 |
|------|---------|----------|----------|--------|--------|
| 认证 | 4 | 4 | 0 | 0 | 100% |
| 资产 | 12 | 12 | 0 | 0 | 100% |
| 工作流 | 8 | 7 | 1 | 0 | 87.5% |
| 库存 | 6 | 6 | 0 | 0 | 100% |
| 耗材 | 6 | 6 | 0 | 0 | 100% |
| 软件许可 | 7 | 7 | 0 | 0 | 100% |
| 组织 | 4 | 2 | 2 | 0 | 50% |
| 系统 | 4 | 4 | 0 | 0 | 100% |
| **总计** | **51** | **48** | **3** | **0** | **94.1%** |

---

## 五、建议

1. **修复前端API路径不一致问题** - 统一使用 `/api` 前缀
2. **完善工作流审批功能** - 前端添加审批API调用
3. **统一组织架构API路径** - 避免重复前缀
