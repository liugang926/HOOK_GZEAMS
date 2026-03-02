## 公共模型引用

> 本模块所有后端组件必须继承以下公共基类

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法 |

---

# Phase 1.6: 低值易耗品/办公用品管理 - 后端实现

## 1. 功能概述

### 1.1 业务场景

管理低值易耗品和办公用品的入库、领用、库存管理，与固定资产管理形成互补，实现企业物资的全面管理。

| 功能 | 说明 | 核心价值 |
|------|------|----------|
| **档案管理** | 耗材分类、基础档案 | 标准化物资管理 |
| **库存管理** | 实时库存、出入库记录 | 库存透明化 |
| **采购入库** | 采购单、入库单 | 供应链管理 |
| **领用出库** | 领用单、出库单 | 费用管控 |
| **库存预警** | 最低库存、补货提醒 | 及时补货 |
| **库存盘点** | 盘点单、盘盈盘亏 | 库存准确性 |

### 1.2 与固定资产的核心差异

| 对比项 | 固定资产 | 低值易耗品/办公用品 |
|--------|----------|---------------------|
| **管理颗粒度** | 单个资产（一物一码） | 批次/库存数量 |
| **折旧处理** | 需要计提折旧 | 不需要折旧 |
| **使用方式** | 领用后可退回 | 领用后消耗（不退回） |
| **盘点方式** | 逐一扫码盘点 | 数量盘点/抽盘 |
| **价值阈值** | 通常>2000元 | 通常<2000元 |
| **财务处理** | 资本性支出 | 费用性支出 |

### 1.3 用户角色与权限

| 角色 | 权限 |
|------|------|
| **仓库管理员** | 耗材CRUD全权限、出入库操作 |
| **部门管理员** | 本部门领用申请 |
| **普通员工** | 查看耗材信息、发起领用申请 |
| **财务人员** | 查看耗材采购成本、领用费用统计 |

---

## 2. 公共模型引用声明

### 2.1 后端公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作、审计字段设置 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤、状态过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法、组织隔离、分页查询 |

### 2.2 继承关系示例

```python
# ✅ 耗材模型继承 BaseModel
class Consumable(BaseModel):
    """低值易耗品 - 自动获得组织隔离、软删除、审计字段"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    # ... 其他业务字段

# ✅ 序列化器继承 BaseModelSerializer
class ConsumableSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Consumable
        fields = BaseModelSerializer.Meta.fields + ['code', 'name', ...]

# ✅ 服务层继承 BaseCRUDService
class ConsumableService(BaseCRUDService):
    def __init__(self):
        super().__init__(Consumable)  # 自动获得所有CRUD方法

# ✅ ViewSet继承 BaseModelViewSetWithBatch
class ConsumableViewSet(BaseModelViewSetWithBatch):
    """自动获得: 组织过滤、软删除、批量操作"""
    queryset = Consumable.objects.all()
    serializer_class = ConsumableSerializer
```

---

## 3. 数据模型设计

### 3.1 ConsumableCategory（耗材分类）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| code | string | max_length=50, unique, db_index | 分类编码 |
| name | string | max_length=100 | 分类名称 |
| parent | FK(self) | null=True, CASCADE, related_name='children' | 上级分类 |
| level | int | default=1 | 层级 |
| path | string | max_length=500, blank=True | 分类路径 |
| enable_alert | bool | default=True | 启用库存预警 |
| min_stock | int | default=10 | 最低库存 |
| max_stock | int | default=100 | 最高库存 |
| reorder_point | int | default=20 | 补货点 |
| unit | string | max_length=20, default='件' | 计量单位 |
| default_supplier | FK(Supplier) | SET_NULL, null=True | 默认供应商 |
| reference_price | decimal | max_digits=10, decimal_places=2, null=True | 参考价格 |
| is_active | bool | default=True | 启用状态 |

*注: 继承 BaseModel 自动获得 organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields*

### 3.2 Consumable（耗材档案）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| code | string | max_length=50, unique | 编码 |
| name | string | max_length=200 | 名称 |
| category | FK(ConsumableCategory) | PROTECT, related_name='consumables' | 分类 |
| specification | string | max_length=200, blank=True | 规格型号 |
| brand | string | max_length=100, blank=True | 品牌 |
| unit | string | max_length=20, default='件' | 单位 |
| current_stock | int | default=0 | 当前库存 |
| available_stock | int | default=0 | 可用库存 |
| locked_stock | int | default=0 | 锁定库存 |
| purchase_price | decimal | max_digits=10, decimal_places=2, default=0 | 采购价格 |
| average_price | decimal | max_digits=10, decimal_places=2, default=0 | 平均价格 |
| min_stock | int | default=10 | 最低库存 |
| max_stock | int | default=100 | 最高库存 |
| reorder_point | int | default=20 | 补货点 |
| status | string | max_length=20, choices | 状态: normal/low_stock/out_of_stock/discontinued |
| warehouse | FK(Location) | SET_NULL, null=True, related_name='consumables' | 存放仓库 |
| remark | text | blank=True | 备注 |

*状态自动更新: available_stock ≤ 0 → out_of_stock; available_stock ≤ min_stock → low_stock; 否则 → normal*

### 3.3 ConsumableStock（库存台账）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| consumable | FK(Consumable) | CASCADE, related_name='stock_logs' | 耗材 |
| transaction_type | string | max_length=20, choices | 变动类型: purchase/issue/return/transfer_in/transfer_out/inventory_add/inventory_reduce/adjustment |
| quantity | int | - | 数量（正数入库，负数出库） |
| before_stock | int | - | 变动前库存 |
| after_stock | int | - | 变动后库存 |
| source_type | string | max_length=50, blank=True | 来源类型 |
| source_id | string | max_length=100, blank=True | 来源ID |
| source_no | string | max_length=100, blank=True | 来源单号 |
| handler | FK(User) | SET_NULL, null=True | 经手人 |
| remark | text | blank=True | 备注 |

### 3.4 ConsumablePurchase（采购入库单）

**ConsumablePurchase Model**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| purchase_no | string | max_length=50, unique, db_index | 采购单号 (自动生成: CP+YYYYMM+序号) |
| purchase_date | date | - | 采购日期 |
| supplier | FK(Supplier) | PROTECT, related_name='consumable_purchases' | 供应商 |
| total_amount | decimal | max_digits=12, decimal_places=2, default=0 | 采购总额 |
| status | string | max_length=20, choices | 状态: draft/pending/approved/received/completed/cancelled |
| approved_by | FK(User) | SET_NULL, null=True, related_name='approved_purchases' | 审批人 |
| approved_at | datetime | null=True | 审批时间 |
| received_by | FK(User) | SET_NULL, null=True, related_name='received_purchases' | 收货人 |
| received_at | datetime | null=True | 收货时间 |
| remark | text | blank=True | 备注 |

**PurchaseItem (采购单明细)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| purchase | FK(ConsumablePurchase) | CASCADE, related_name='items' | 采购单 |
| consumable | FK(Consumable) | PROTECT | 耗材 |
| quantity | int | - | 采购数量 |
| unit_price | decimal | max_digits=10, decimal_places=2 | 单价 |
| amount | decimal | max_digits=12, decimal_places=2 | 金额 |
| remark | text | blank=True | 备注 |

### 3.5 ConsumableIssue（领用出库单）

**ConsumableIssue Model**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| issue_no | string | max_length=50, unique, db_index | 领用单号 (自动生成: CI+YYYYMM+序号) |
| issue_date | date | - | 领用日期 |
| applicant | FK(User) | PROTECT, related_name='consumable_issues' | 申请人 |
| department | FK(Department) | PROTECT | 领用部门 |
| issue_reason | text | blank=True | 领用原因 |
| status | string | max_length=20, choices | 状态: draft/pending/approved/issued/completed/rejected |
| approved_by | FK(User) | SET_NULL, null=True, related_name='approved_issues' | 审批人 |
| issued_by | FK(User) | SET_NULL, null=True, related_name='issued_consumables' | 发放人 |
| issued_at | datetime | null=True | 发放时间 |
| remark | text | blank=True | 备注 |

**IssueItem (领用单明细)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| issue | FK(ConsumableIssue) | CASCADE, related_name='items' | 领用单 |
| consumable | FK(Consumable) | PROTECT | 耗材 |
| quantity | int | - | 领用数量 |
| remark | text | blank=True | 备注 |

---

## 4. 序列化器设计

所有序列化器继承 `BaseModelSerializer`，自动序列化公共字段。

| 序列化器 | 继承 | 业务字段 |
|---------|------|---------|
| ConsumableCategorySerializer | BaseModelSerializer | code, name, parent, level, path, enable_alert, min_stock, max_stock, reorder_point, unit, default_supplier, reference_price, is_active |
| ConsumableSerializer | BaseModelSerializer | code, name, category, specification, brand, unit, current_stock, available_stock, locked_stock, purchase_price, average_price, min_stock, max_stock, reorder_point, status, warehouse, remark |
| ConsumableStockSerializer | BaseModelSerializer | consumable, transaction_type, quantity, before_stock, after_stock, source_type, source_id, source_no, handler, remark |
| ConsumablePurchaseSerializer | BaseModelSerializer | purchase_no, purchase_date, supplier, total_amount, status, approved_by, approved_at, received_by, received_at, remark |
| ConsumableIssueSerializer | BaseModelSerializer | issue_no, issue_date, applicant, department, issue_reason, status, approved_by, issued_by, issued_at, remark |

---

## 5. 服务层设计

所有服务类继承 `BaseCRUDService`，自动获得 CRUD 方法。

| 服务类 | 继承 | 业务方法 |
|-------|------|---------|
| ConsumableService | BaseCRUDService | check_low_stock() - 检查低库存耗材 |
| ConsumablePurchaseService | BaseCRUDService | complete_purchase() - 完成采购，自动入库更新库存 |
| ConsumableIssueService | BaseCRUDService | complete_issue() - 完成领用，自动出库减少库存 |

*注: 所有服务类自动获得 create(), update(), delete(), restore(), get(), query(), paginate(), batch_delete() 等方法*

---

## 6. ViewSet设计

所有 ViewSet 继承 `BaseModelViewSetWithBatch`，自动获得组织过滤、软删除、批量操作。

| ViewSet | 继承 | Serializer | 自定义Actions |
|---------|------|-----------|--------------|
| ConsumableViewSet | BaseModelViewSetWithBatch | ConsumableSerializer | low_stock() - 获取低库存耗材 |
| ConsumablePurchaseViewSet | BaseModelViewSetWithBatch | ConsumablePurchaseSerializer | complete() - 完成采购入库 |
| ConsumableIssueViewSet | BaseModelViewSetWithBatch | ConsumableIssueSerializer | complete() - 完成领用出库 |

*注: 所有 ViewSet 自动提供 list, create, retrieve, update, destroy, batch-delete, batch-restore, deleted, restore 等标准 CRUD 操作*

---

## 7. URL配置

```python
# backend/config/urls.py

from apps.consumables.views import (
    ConsumableViewSet, ConsumablePurchaseViewSet, ConsumableIssueViewSet
)

router.register(r'consumables/consumables', ConsumableViewSet, basename='consumable')
router.register(r'consumables/purchases', ConsumablePurchaseViewSet, basename='consumable-purchase')
router.register(r'consumables/issues', ConsumableIssueViewSet, basename='consumable-issue')
```

---

## 8. 核心优势

### 8.1 使用公共基类的优势

- ✅ **自动组织隔离**: 所有耗材数据自动按组织过滤
- ✅ **软删除支持**: 删除耗材/单据不会真正删除数据
- ✅ **批量操作**: 支持批量删除、恢复、更新
- ✅ **审计字段**: 自动记录创建人、创建时间等
- ✅ **代码减少**: 约60%的重复代码被基类替代

### 8.2 库存管理特性

- ✅ **实时库存更新**: 出入库自动更新库存
- ✅ **库存流水追溯**: 完整的库存变动记录
- ✅ **库存预警**: 自动触发低库存提醒
- ✅ **批次管理**: 支持批次号管理

---

## 9. 输出产物

| 文件 | 说明 | 继承关系 |
|------|------|---------|
| `apps/consumables/models.py` | 耗材模型 | BaseModel |
| `apps/consumables/serializers.py` | 耗材序列化器 | BaseModelSerializer |
| `apps/consumables/services/consumable_service.py` | 耗材服务 | BaseCRUDService |
| `apps/consumables/views.py` | 耗材API | BaseModelViewSetWithBatch |

---

## 10. 实施步骤

| 阶段 | 任务 | 状态 |
|------|------|------|
| 1 | 创建耗材数据模型（继承 BaseModel） | ✅ |
| 2 | 创建序列化器（继承 BaseModelSerializer） | ✅ |
| 3 | 创建服务层（继承 BaseCRUDService） | ✅ |
| 4 | 创建ViewSet（继承 BaseModelViewSetWithBatch） | ✅ |
| 5 | 配置 URL 路由 | ✅ |
| 6 | 实现库存预警机制 | 待开发 |
| 7 | 编写单元测试 | 待开发 |
| 8 | 编写API文档 | 待开发 |

---

## 11. API接口规范

### 11.1 统一响应格式

#### 成功响应格式
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "HB2026010001",
        "name": "A4打印纸",
        ...
    }
}
```

#### 列表响应格式（分页）
```json
{
    "success": true,
    "data": {
        "count": 50,
        "next": "https://api.example.com/api/consumables/consumables/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "HB2026010001",
                "name": "A4打印纸",
                ...
            }
        ]
    }
}
```

#### 错误响应格式
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "name": ["该字段不能为空"],
            "current_stock": ["库存不能为负数"]
        }
    }
}
```

### 11.2 标准CRUD接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **列表查询** | GET | `/api/consumables/consumables/` | 分页查询耗材列表，支持分类、状态等过滤 |
| **详情查询** | GET | `/api/consumables/consumables/{id}/` | 获取单个耗材详情信息 |
| **创建耗材** | POST | `/api/consumables/consumables/` | 创建新耗材档案 |
| **更新耗材** | PUT | `/api/consumables/consumables/{id}/` | 完整更新耗材信息 |
| **部分更新** | PATCH | `/api/consumables/consumables/{id}/` | 部分更新耗材信息 |
| **软删除** | DELETE | `/api/consumables/consumables/{id}/` | 软删除耗材 |
| **已删除列表** | GET | `/api/consumables/consumables/deleted/` | 查询已删除的耗材列表 |
| **恢复耗材** | POST | `/api/consumables/consumables/{id}/restore/` | 恢复已删除的耗材 |

### 11.3 批量操作接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **批量删除** | POST | `/api/consumables/consumables/batch-delete/` | 批量软删除多个耗材 |
| **批量恢复** | POST | `/api/consumables/consumables/batch-restore/` | 批量恢复多个已删除的耗材 |
| **批量更新** | POST | `/api/consumables/consumables/batch-update/` | 批量更新耗材字段 |

**批量删除请求格式**：
```json
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

### 11.4 耗材分类接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **分类列表** | GET | `/api/consumables/categories/` | 获取耗材分类树形结构 |
| **分类详情** | GET | `/api/consumables/categories/{id}/` | 获取分类详情 |
| **创建分类** | POST | `/api/consumables/categories/` | 创建耗材分类 |
| **更新分类** | PUT | `/api/consumables/categories/{id}/` | 更新分类信息 |

### 11.5 采购入库接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **采购单列表** | GET | `/api/consumables/purchases/` | 查询采购单列表 |
| **采购单详情** | GET | `/api/consumables/purchases/{id}/` | 获取采购单详情 |
| **创建采购单** | POST | `/api/consumables/purchases/` | 创建新的采购单 |
| **完成入库** | POST | `/api/consumables/purchases/{id}/complete/` | 完成采购入库，更新库存 |
| **采购单审批** | POST | `/api/consumables/purchases/{id}/approve/` | 审批采购单 |

### 11.6 领用出库接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **领用单列表** | GET | `/api/consumables/issues/` | 查询领用单列表 |
| **领用单详情** | GET | `/api/consumables/issues/{id}/` | 获取领用单详情 |
| **创建领用单** | POST | `/api/consumables/issues/` | 创建新的领用单 |
| **完成出库** | POST | `/api/consumables/issues/{id}/complete/` | 完成领用出库，减少库存 |
| **领用单审批** | POST | `/api/consumables/issues/{id}/approve/` | 审批领用单 |

### 11.7 库存管理接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| **库存流水** | GET | `/api/consumables/stocks/` | 查询库存变动流水 |
| **低库存预警** | GET | `/api/consumables/consumables/low_stock/` | 获取低库存耗材列表 |
| **库存统计** | GET | `/api/consumables/statistics/` | 获取库存统计信息 |

### 11.8 标准错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已被软删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

### 11.9 扩展接口示例

#### 库存统计接口
```http
GET /api/consumables/statistics/
```

**响应格式**：
```json
{
    "success": true,
    "data": {
        "total_consumables": 200,
        "total_categories": 20,
        "low_stock_items": 5,
        "out_of_stock_items": 2,
        "total_value": "50000.00",
        "by_category": [
            {"category": "办公用品", "count": 100, "total_value": "30000.00"},
            {"category": "清洁用品", "count": 50, "total_value": "10000.00"}
        ],
        "by_status": [
            {"status": "normal", "count": 180},
            {"status": "low_stock", "count": 15},
            {"status": "out_of_stock", "count": 5}
        ]
    }
}
```

#### 库存流水查询接口
```http
GET /api/consumables/stocks/?consumable_id=uuid1&transaction_type=purchase
```

---

**版本**: 1.0.0
**更新日期**: 2026-01-15
**维护人**: GZEAMS 开发团队
