# Phase 1.5: 资产领用/调拨/退库业务 - 后端实现

## 1. 功能概述

### 1.1 业务场景

实现资产领用、调拨、借用、退库等日常运营业务单据管理，记录资产在组织内部的流动轨迹。

| 业务类型 | 场景 | 核心价值 |
|---------|------|----------|
| **资产领用** | 员工领用资产用于工作 | 记录领用轨迹，明确保管责任 |
| **资产调拨** | 部门间资产转移 | 实现资产合理配置 |
| **资产借用** | 临时借用资产 | 临时使用管理，归还追踪 |
| **资产退库** | 离职或项目结束退回 | 资产回收再利用 |

### 1.2 用户角色与权限

| 角色 | 权限 |
|------|------|
| **资产管理员** | 全部业务单据的审批、执行 |
| **部门负责人** | 本部门业务单据审批 |
| **普通员工** | 发起申请、查看自己相关的单据 |
| **仓库管理员** | 确认发放、接收、归还 |

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
# ✅ 所有业务单据模型继承 BaseModel
class AssetPickup(BaseModel):
    """资产领用单 - 自动获得组织隔离、软删除、审计字段"""
    pickup_no = models.CharField(max_length=50, unique=True)
    applicant = models.ForeignKey(User, on_delete=models.PROTECT)
    # ... 其他业务字段

# ✅ 序列化器继承 BaseModelSerializer
class AssetPickupSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = AssetPickup
        fields = BaseModelSerializer.Meta.fields + ['pickup_no', 'applicant', ...]

# ✅ 服务层继承 BaseCRUDService
class AssetPickupService(BaseCRUDService):
    def __init__(self):
        super().__init__(AssetPickup)  # 自动获得所有CRUD方法

# ✅ ViewSet继承 BaseModelViewSetWithBatch
class AssetPickupViewSet(BaseModelViewSetWithBatch):
    """自动获得: 组织过滤、软删除、批量操作"""
    queryset = AssetPickup.objects.all()
    serializer_class = AssetPickupSerializer
```

---

## 3. 数据模型设计

### 3.1 资产领用单（AssetPickup）

**AssetPickup Model**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pickup_no | string | max_length=50, unique, db_index | 领用单号 (自动生成: LY+YYYYMM+序号) |
| applicant | FK(User) | PROTECT, related_name='pickup_applications' | 申请人 |
| department | FK(Department) | PROTECT | 领用部门 |
| pickup_date | date | - | 领用日期 |
| pickup_reason | text | blank=True | 领用原因 |
| status | string | max_length=20, choices=STATUS_CHOICES | 状态: draft/pending/approved/rejected/completed/cancelled |
| approved_by | FK(User) | SET_NULL, null=True, related_name='approved_pickups' | 审批人 |
| approved_at | datetime | null=True | 审批时间 |
| approval_comment | text | blank=True | 审批意见 |
| completed_at | datetime | null=True | 完成时间 |

*状态选项: draft(草稿) → pending(待审批) → approved(已批准) → completed(已完成) / rejected(已拒绝)*

**PickupItem (领用单明细)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| pickup | FK(AssetPickup) | CASCADE, related_name='items' | 领用单 |
| asset | FK(Asset) | PROTECT | 资产 |
| quantity | int | default=1 | 数量 |
| remark | text | blank=True | 备注 |
| snapshot_original_location | FK(Location) | SET_NULL, null=True, related_name='+' | 原存放地点（快照） |
| snapshot_original_custodian | FK(User) | SET_NULL, null=True, related_name='+' | 原保管人（快照） |

*注: 继承 BaseModel 自动获得 organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields*

### 3.2 资产调拨单（AssetTransfer）

**AssetTransfer Model**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| transfer_no | string | max_length=50, unique, db_index | 调拨单号 (自动生成: TF+YYYYMM+序号) |
| from_department | FK(Department) | PROTECT, related_name='transfers_out' | 调出部门 |
| to_department | FK(Department) | PROTECT, related_name='transfers_in' | 调入部门 |
| transfer_date | date | - | 调拨日期 |
| transfer_reason | text | blank=True | 调拨原因 |
| status | string | max_length=20, choices=STATUS_CHOICES | 状态: draft/pending/out_approved/approved/rejected/completed/cancelled |
| from_approved_by | FK(User) | SET_NULL, null=True, related_name='out_approved_transfers' | 调出方审批人 |
| to_approved_by | FK(User) | SET_NULL, null=True, related_name='in_approved_transfers' | 调入方审批人 |

*状态流程: draft → pending → out_approved(调出方已批准) → approved(双方已批准) → completed*

**TransferItem (调拨单明细)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| transfer | FK(AssetTransfer) | CASCADE, related_name='items' | 调拨单 |
| asset | FK(Asset) | PROTECT | 资产 |
| from_location | FK(Location) | SET_NULL, null=True, related_name='+' | 原存放地点（快照） |
| from_custodian | FK(User) | SET_NULL, null=True, related_name='+' | 原保管人（快照） |
| to_location | FK(Location) | SET_NULL, null=True, related_name='transfer_in_locations' | 目标存放地点 |
| remark | text | blank=True | 备注 |

### 3.3 资产退库单（AssetReturn）

**AssetReturn Model**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| return_no | string | max_length=50, unique, db_index | 退库单号 (自动生成: RT+YYYYMM+序号) |
| returner | FK(User) | PROTECT, related_name='asset_returns' | 退库人 |
| return_date | date | - | 退库日期 |
| return_reason | text | blank=True | 退库原因 |
| return_location | FK(Location) | PROTECT, related_name='asset_returns' | 退库存放地点 |
| status | string | max_length=20, choices=STATUS_CHOICES | 状态: pending/approved/rejected/completed |
| confirmed_by | FK(User) | SET_NULL, null=True, related_name='confirmed_returns' | 确认人 |
| confirmed_at | datetime | null=True | 确认时间 |

*状态流程: pending(待确认) → approved(已确认) → completed(已完成) / rejected(已拒绝)*

**ReturnItem (退库单明细)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| asset_return | FK(AssetReturn) | CASCADE, related_name='items' | 退库单 |
| asset | FK(Asset) | PROTECT | 资产 |
| asset_status | string | max_length=20, choices | 退库后状态: idle(闲置)/maintenance(需维修)/scrapped(需报废) |
| condition_description | text | blank=True | 资产状况描述 |
| remark | text | blank=True | 备注 |

### 3.4 资产借用单（AssetLoan）

**AssetLoan Model**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| loan_no | string | max_length=50, unique, db_index | 借用单号 (自动生成: LN+YYYYMM+序号) |
| borrower | FK(User) | PROTECT, related_name='asset_loans' | 借用人 |
| borrow_date | date | - | 借出日期 |
| expected_return_date | date | - | 预计归还日期 |
| actual_return_date | date | null=True | 实际归还日期 |
| loan_reason | text | blank=True | 借用原因 |
| status | string | max_length=20, choices=STATUS_CHOICES | 状态: pending/approved/borrowed/returned/overdue/rejected/cancelled |
| approved_by | FK(User) | SET_NULL, null=True, related_name='approved_loans' | 审批人 |
| lent_by | FK(User) | SET_NULL, null=True, related_name='lent_assets' | 借出确认人 |
| returned_at | datetime | null=True | 归还时间 |
| asset_condition | string | max_length=20, choices | 归还时资产状况: good/minor_damage/major_damage/lost |

*状态流程: pending → approved → borrowed(借出中) → returned(已归还) / overdue(已逾期)*

**LoanItem (借用单明细)**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| loan | FK(AssetLoan) | CASCADE, related_name='items' | 借用单 |
| asset | FK(Asset) | PROTECT | 资产 |
| remark | text | blank=True | 备注 |

---

## 4. 序列化器设计

所有序列化器继承 `BaseModelSerializer`，自动序列化公共字段。

| 序列化器 | 继承 | 业务字段 |
|---------|------|---------|
| AssetPickupSerializer | BaseModelSerializer | pickup_no, applicant, department, pickup_date, pickup_reason, status, approved_by, approved_at, approval_comment, completed_at |
| AssetTransferSerializer | BaseModelSerializer | transfer_no, from_department, to_department, transfer_date, transfer_reason, status, from_approved_by, to_approved_by |
| AssetReturnSerializer | BaseModelSerializer | return_no, returner, return_date, return_reason, return_location, status, confirmed_by, confirmed_at |
| AssetLoanSerializer | BaseModelSerializer | loan_no, borrower, borrow_date, expected_return_date, actual_return_date, loan_reason, status, approved_by, lent_by, returned_at, asset_condition |

*注: 所有序列化器自动包含 BaseModelSerializer.Meta.fields (id, organization, is_deleted, deleted_at, created_at, updated_at, created_by)*

---

## 5. 服务层设计

所有服务类继承 `BaseCRUDService`，自动获得 CRUD 方法。

| 服务类 | 继承 | 业务方法 |
|-------|------|---------|
| AssetPickupService | BaseCRUDService | approve_pickup() - 审批领用单<br>complete_pickup() - 完成领用，更新资产保管信息 |
| AssetTransferService | BaseCRUDService | complete_transfer() - 完成调拨，更新资产归属 |
| AssetReturnService | BaseCRUDService | confirm_return() - 确认退库，更新资产状态 |
| AssetLoanService | BaseCRUDService | confirm_borrow() - 确认借出<br>confirm_return() - 确认归还 |

*注: 所有服务类自动获得 create(), update(), delete(), restore(), get(), query(), paginate(), batch_delete() 等方法*

---

## 6. ViewSet设计

所有 ViewSet 继承 `BaseModelViewSetWithBatch`，自动获得组织过滤、软删除、批量操作。

| ViewSet | 继承 | Serializer | 自定义Actions |
|---------|------|-----------|--------------|
| AssetPickupViewSet | BaseModelViewSetWithBatch | AssetPickupSerializer | approve() - 审批领用单 |
| AssetTransferViewSet | BaseModelViewSetWithBatch | AssetTransferSerializer | - |
| AssetReturnViewSet | BaseModelViewSetWithBatch | AssetReturnSerializer | - |
| AssetLoanViewSet | BaseModelViewSetWithBatch | AssetLoanSerializer | - |

*注: 所有 ViewSet 自动提供 list, create, retrieve, update, destroy, batch-delete, batch-restore, deleted, restore 等标准 CRUD 操作*

---

## 7. URL配置

```python
# backend/config/urls.py

from apps.assets.views import (
    AssetPickupViewSet, AssetTransferViewSet,
    AssetReturnViewSet, AssetLoanViewSet
)

router.register(r'assets/pickups', AssetPickupViewSet, basename='asset-pickup')
router.register(r'assets/transfers', AssetTransferViewSet, basename='asset-transfer')
router.register(r'assets/returns', AssetReturnViewSet, basename='asset-return')
router.register(r'assets/loans', AssetLoanViewSet, basename='asset-loan')
```

---

## 8. 核心优势

### 8.1 使用公共基类的优势

- ✅ **自动组织隔离**: 所有单据自动按组织过滤
- ✅ **软删除支持**: 删除单据不会真正删除数据
- ✅ **批量操作**: 支持批量删除、恢复、更新
- ✅ **审计字段**: 自动记录创建人、创建时间等
- ✅ **代码减少**: 约60%的重复代码被基类替代

### 8.2 代码对比

**迁移前**:
```python
class AssetPickupViewSet(viewsets.ModelViewSet):
    # 需要手动实现: 组织过滤、软删除、批量操作等
    pass
```

**迁移后**:
```python
class AssetPickupViewSet(BaseModelViewSetWithBatch):
    # 自动获得所有功能
    pass
```

---

## 9. 输出产物

| 文件 | 说明 | 继承关系 |
|------|------|---------|
| `apps/assets/models.py` | 四种业务单据模型 | BaseModel |
| `apps/assets/serializers.py` | 业务单据序列化器 | BaseModelSerializer |
| `apps/assets/services/operation_service.py` | 业务服务 | BaseCRUDService |
| `apps/assets/views.py` | 业务API | BaseModelViewSetWithBatch |

---

## 10. 实施步骤

| 阶段 | 任务 | 状态 |
|------|------|------|
| 1 | 创建四种业务单据模型（继承 BaseModel） | ✅ |
| 2 | 创建序列化器（继承 BaseModelSerializer） | ✅ |
| 3 | 创建服务层（继承 BaseCRUDService） | ✅ |
| 4 | 创建ViewSet（继承 BaseModelViewSetWithBatch） | ✅ |
| 5 | 配置 URL 路由 | ✅ |
| 6 | 编写单元测试 | 待开发 |
| 7 | 编写API文档 | 待开发 |

---

## 11. API接口规范

### 11.1 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 11.1.1 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 11.1.2 列表响应
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

#### 11.1.3 错误响应
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

### 11.2 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |

---

**版本**: 1.0.0
**更新日期**: 2026-01-15
**维护人**: GZEAMS 开发团队
