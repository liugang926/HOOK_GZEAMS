# Phase 4.5: 盘点业务链条 - 总览

## 概述

本模块实现固定资产盘点的完整业务链条管理，确保盘点结果准确、差异处理合规、盘点报告可审计。与 phase4_3 的快照功能不同，本模块聚焦于**盘点业务流程**的处理，包括差异处理、审批流程和结果确认。

---

## 1. 业务背景

### 1.1 当前痛点

| 痛点 | 说明 | 影响 |
|------|------|------|
| **差异处理缺失** | 发现差异后没有规范的认定和处理流程 | 差异处理随意，资产账实不符 |
| **审批缺失** | 盘点结果没有审批确认流程 | 结果可信度低，责任不清 |
| **调账缺失** | 盘点差异无法自动触发账务调整 | 财务账面与实物不一致 |
| **报告缺失** | 盘点结果没有标准报告输出 | 管理层无法掌握盘点结果 |

### 1.2 业务目标

- **差异可追溯**：每个盘点差异都有完整的处理记录
- **审批合规**：盘点结果需经多级审批确认
- **调账自动**：审批通过后自动触发资产调账
- **报告规范**：生成标准化的盘点报告

---

## 2. 模块架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         盘点业务链条管理                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │
│  │  盘点快照      │ → │  盘点执行      │ → │  差异发现      │         │
│  │  [phase4_3]   │   │  [phase4_2]   │   │  Difference   │         │
│  └───────────────┘   └───────────────┘   └───────────────┘         │
│                                                   ↓                    │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐         │
│  │  盘点报告      │ ← │  差异处理      │ ← │  差异认定      │         │
│  │  Report       │   │  Resolution   │   │  Approval     │         │
│  └───────────────┘   └───────────────┘   └───────────────┘         │
│           ↓                   ↓                                      │
│  ┌───────────────┐   ┌───────────────┐                              │
│  │  报告审批      │   │  资产调账      │                              │
│  │  (Workflow)   │   │  Adjustment   │                              │
│  └───────────────┘   └───────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 功能范围

### 3.1 差异认定 (Difference Approval)

| 功能点 | 说明 |
|--------|------|
| 差异列表 | 按盘点任务展示所有盘点差异 |
| 差异类型 | 盘盈、盘亏、位置不符、状态不符 |
| 差异认定 | 资产管理员对差异进行初步认定 |
| 责任确认 | 确认差异责任人 |
| 处理建议 | 提出差异处理建议 |

### 3.2 差异处理 (Difference Resolution)

| 功能点 | 说明 |
|--------|------|
| 处理方式 | 调整账面、调整实物、报损、转入待处理 |
| 批量处理 | 支持批量处理同类型差异 |
| 处理审批 | 根据差异金额设置不同审批级别 |
| 处理记录 | 完整记录差异处理过程 |

### 3.3 盘点报告 (Inventory Report)

| 功能点 | 说明 |
|--------|------|
| 报告生成 | 自动生成盘点报告 |
| 报告内容 | 盘点概况、差异明细、处理结果、资产分布 |
| 报告导出 | 支持PDF、Excel格式导出 |
| 报告模板 | 支持自定义报告模板 |

### 3.4 报告审批 (Report Approval)

| 功能点 | 说明 |
|--------|------|
| 审批流程 | 多级审批：资产管理 → 财务 → 管理层 |
| 审批意见 | 审批人可签署意见 |
| 审批通知 | 关键节点通知相关人员 |
| 审批记录 | 完整的审批轨迹 |

### 3.5 资产调账 (Asset Adjustment)

| 功能点 | 说明 |
|--------|------|
| 自动调账 | 审批通过后自动更新资产信息 |
| 调账类型 | 位置调整、状态调整、价值调整 |
| 调账凭证 | 生成财务调账凭证 |
| 调账回滚 | 支持调账回滚（在审批期内） |

---

## 4. 业务流程

### 4.1 差异处理流程

```
盘点完成 → 差异生成 → 资产管理员认定 → 责任人确认 → 处理方案制定
                                                    ↓
                                             审批流程
                                                    ↓
                                             执行处理 → 资产调账 → 差异关闭
```

### 4.2 报告生成流程

```
盘点完成 → 生成报告草稿 → 差异处理完成 → 定稿 → 审批 → 归档
```

### 4.3 审批级别规则

| 差异类型 | 金额范围 | 审批级别 |
|----------|----------|----------|
| 账实不符 | < 1万元 | 资产管理员 |
| 账实不符 | 1万-10万 | 资产管理员 + 财务主管 |
| 账实不符 | > 10万 | 资产管理员 + 财务主管 + 总经理 |
| 位置调整 | 全部 | 资产管理员 |
| 状态调整 | 全部 | 资产管理员 + 资产使用部门 |

---

## 5. 数据模型关系

```
InventoryTask (盘点任务) [phase4_1]
    │
    ↓ (盘点完成)
    │
InventorySnapshot (盘点快照) [phase4_3]
    │
    ↓ (差异分析)
    │
InventoryDifference (盘点差异)
    │
    ├── 差异类型: type (surplus/loss/location_mismatch/status_mismatch)
    ├── 差异状态: status (pending/confirmed/approved/resolved/closed)
    ├── 认定信息:认定人, 认定时间, 认定意见
    ├── 责任信息: 责任人, 责任部门
    │
    ↓ (差异认定)
    │
DifferenceResolution (差异处理)
    │
    ├── 处理方式: action (adjust_account/adjust_asset/write_off/pending)
    ├── 处理审批: 审批人, 审批时间, 审批意见
    ├── 处理执行: 执行人, 执行时间
    │
    ↓ (处理完成)
    │
AssetAdjustment (资产调账)
    │
    ├── 调账类型: type (location/status/value)
    ├── 调账前值: before_value
    ├── 调账后值: after_value
    │
    ↓ (所有差异处理完成)
    │
InventoryReport (盘点报告)
    │
    ├── 报告状态: status (draft/pending_approval/approved)
    ├── 报告内容: JSON结构化存储
    ├── 审批记录: ApprovalRecord[]
```

---

## 公共模型引用声明

本模块所有组件严格遵循 GZEAMS 公共基类规范，所有后端组件均继承相应的基类以获得标准功能。

### 基类引用表

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离（org字段）、软删除（is_deleted+deleted_at）、审计字段（created_at+updated_at+created_by）、动态字段（custom_fields JSONB） |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields自动处理、created_by用户信息嵌入 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除过滤、审计字段自动设置、批量操作（/batch-delete/、/batch-restore/、/batch-update/） |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离、复杂查询、分页支持 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤（时间范围、用户、组织） |

### 核心模型继承关系

```python
# 盘点差异模型
class InventoryDifference(BaseModel):
    """盘点差异记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    task = models.ForeignKey('inventory.InventoryTask', ...)
    difference_type = models.CharField(...)  # surplus/loss/location_mismatch/status_mismatch/value_mismatch
    status = models.CharField(...)  # pending/confirmed/processing/approved/rejected/resolved
    asset = models.ForeignKey('assets.Asset', ...)
    account_location = models.ForeignKey(...)
    actual_location = models.ForeignKey(...)
    process_instance_id = models.CharField(...)  # 工作流实例ID（BPMN）

# 差异处理模型
class DifferenceResolution(BaseModel):
    """差异处理记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    resolution_no = models.CharField(unique=True)
    action = models.CharField(...)  # adjust_account/adjust_asset/record_asset/write_off/pending
    status = models.CharField(...)  # draft/submitted/approved/rejected/executing/completed/failed
    process_instance_id = models.CharField(...)  # 工作流实例ID

# 资产调账模型
class AssetAdjustment(BaseModel):
    """资产调账记录"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    adjustment_no = models.CharField(unique=True)
    adjustment_type = models.CharField(...)  # location/status/value/info/new/remove
    status = models.CharField(...)  # pending/executing/completed/failed/rolled_back
    before_value = models.JSONField(...)
    after_value = models.JSONField(...)

# 盘点报告模型
class InventoryReport(BaseModel):
    """盘点报告"""
    # 继承BaseModel自动获得：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields
    report_no = models.CharField(unique=True)
    task = models.OneToOneField('inventory.InventoryTask', ...)
    status = models.CharField(...)  # draft/pending_approval/approved/rejected
    report_data = models.JSONField(...)  # JSON结构化报告内容
```

### 序列化器继承关系

```python
# 所有序列化器必须继承 BaseModelSerializer
class InventoryDifferenceSerializer(BaseModelSerializer):
    """盘点差异序列化器"""
    # 继承BaseModelSerializer获得所有公共字段
    class Meta(BaseModelSerializer.Meta):
        model = InventoryDifference
        fields = BaseModelSerializer.Meta.fields + [
            'task', 'difference_type', 'status', 'asset',
            'account_location', 'actual_location', 'process_instance_id'
        ]

class DifferenceResolutionSerializer(BaseModelSerializer):
    """差异处理序列化器"""
    # 继承BaseModelSerializer获得所有公共字段

class AssetAdjustmentSerializer(BaseModelSerializer):
    """资产调账序列化器"""
    # 继承BaseModelSerializer获得所有公共字段
```

### 服务层继承关系

```python
# 服务类必须继承 BaseCRUDService
class DifferenceAnalysisService(BaseCRUDService):
    """差异分析服务"""
    def __init__(self):
        super().__init__(InventoryDifference)
        # 自动获得：create(), update(), delete(), restore(), get(), query(), paginate()

class DifferenceConfirmationService(BaseCRUDService):
    """差异认定服务"""
    # 继承BaseCRUDService获得所有CRUD方法

class DifferenceResolutionService(BaseCRUDService):
    """差异处理服务"""
    # 继承BaseCRUDService获得所有CRUD方法
    # 集成工作流引擎进行审批流程管理

class AssetAdjustmentService(BaseCRUDService):
    """资产调账服务"""
    # 继承BaseCRUDService获得所有CRUD方法
    # 执行资产信息更新操作
```

### ViewSet继承关系

```python
# 所有ViewSet必须继承 BaseModelViewSetWithBatch
class InventoryDifferenceViewSet(BaseModelViewSetWithBatch):
    """盘点差异API"""
    serializer_class = InventoryDifferenceSerializer
    # 自动获得：组织过滤、软删除、审计字段、批量操作

class DifferenceResolutionViewSet(BaseModelViewSetWithBatch):
    """差异处理API"""
    # 自动获得所有公共功能

class AssetAdjustmentViewSet(BaseModelViewSetWithBatch):
    """资产调账API"""
    # 自动获得所有公共功能

class InventoryReportViewSet(BaseModelViewSetWithBatch):
    """盘点报告API"""
    # 自动获得所有公共功能
```

### 过滤器继承关系

```python
# 所有过滤器必须继承 BaseModelFilter
class InventoryDifferenceFilter(BaseModelFilter):
    """盘点差异过滤器"""
    difference_type = filters.ChoiceFilter(choices=[...])
    status = filters.ChoiceFilter(choices=[...])
    # 自动继承：created_at, updated_at, created_by, is_deleted 等过滤

    class Meta(BaseModelFilter.Meta):
        model = InventoryDifference
        fields = BaseModelFilter.Meta.fields + ['task', 'difference_type', 'status']
```

---

## 6. 与其他模块的集成

| 集成点 | 关联模块 | 集成方式 |
|--------|---------|---------|
| 盘点快照 | phase4_3 | 读取快照数据进行差异分析 |
| 扫描记录 | phase4_2 | 基于扫描结果计算差异 |
| 工作流引擎 | phase3_2 | 差异处理审批、报告审批 |
| 资产管理 | phase1_4 | 调账时更新资产信息 |
| 财务集成 | phase5_2 | 生成财务调账凭证 |
| 通知模块 | 通用 | 审批通知、结果通知 |

---

## 7. 盘点差异类型定义

### 7.1 差异类型

| 类型 | 代码 | 说明 | 处理方式 |
|------|------|------|----------|
| 盘盈 | surplus | 实物有但账面无 | 补录资产 |
| 盘亏 | loss | 账面有但实物无 | 调减资产或报损 |
| 位置不符 | location_mismatch | 实物位置与账面不符 | 更新位置 |
| 状态不符 | status_mismatch | 实物状态与账面不符 | 更新状态 |
| 价值不符 | value_mismatch | 实物价值与账面不符 | 重新评估 |
| 信息不符 | info_mismatch | 其他信息不符 | 更新信息 |

### 7.2 差异状态流转

```
pending (待认定) → confirmed (已认定) → approved (已批准处理)
                                                    ↓
                                               resolved (已处理)
                                                    ↓
                                                closed (已关闭)

                              rejected (被驳回) ↗
```

---

## 8. 盘点报告结构

### 8.1 报告内容

```json
{
  "report_no": "RPT2024010001",
  "task": {
    "task_no": "PD2024010001",
    "task_name": "2024年1月全公司盘点",
    "period": "2024-01-01 ~ 2024-01-15"
  },
  "summary": {
    "total_assets": 1000,
    "scanned_assets": 950,
    "unscanned_assets": 50,
    "difference_count": 15,
    "difference_rate": "1.5%"
  },
  "differences": [
    {
      "type": "loss",
      "count": 5,
      "total_value": 25000
    },
    {
      "type": "surplus",
      "count": 3,
      "total_value": 0
    },
    {
      "type": "location_mismatch",
      "count": 7,
      "total_value": 0
    }
  ],
  "by_department": [
    {
      "department": "研发部",
      "total": 500,
      "scanned": 480,
      "differences": 10
    }
  ],
  "approvals": [
    {
      "level": "资产管理员",
      "approver": "张三",
      "status": "approved",
      "opinion": "盘点结果确认无误",
      "approved_at": "2024-01-20T10:00:00Z"
    }
  ]
}
```

---

## 9. 子文档索引

| 文档 | 说明 |
|------|------|
| [backend.md](./backend.md) | 后端实现 - 模型设计、服务层、API |
| [api.md](./api.md) | API接口定义 |
| [frontend.md](./frontend.md) | 前端实现 - 页面组件、交互设计 |
| [test.md](./test.md) | 测试计划 |

---

## 10. 后续任务

1. 实现差异认定模块
2. 实现差异处理模块
3. 实现盘点报告生成
4. 实现报告审批流程
5. 实现资产调账功能
6. 与工作流引擎集成
7. 与财务模块集成
