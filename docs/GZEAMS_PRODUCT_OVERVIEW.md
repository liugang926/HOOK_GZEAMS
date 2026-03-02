# GZEAMS (钩子固定资产) - 产品概览文档

> **版本**: v1.1.0
> **更新日期**: 2026-01-22
> **项目地址**: https://github.com/liugang926/HOOK_GZEAMS.git
> **参考标杆**: [NIIMBOT Hook Fixed Assets](https://yzcweixin.niimbot.com/)

---

## 文档信息

| 项目 | 说明 |
|------|------|
| 产品名称 | GZEAMS (钩子固定资产) |
| 产品定位 | 企业级固定资产低代码管理平台 |
| 核心架构 | 元数据驱动 + 多组织隔离 + 事件驱动解耦 |
| 技术栈 | Django 5.0 + Vue 3 + PostgreSQL + Redis + Celery |
| 开发标准 | 全部代码注释必须使用英文 |

---

## 一、产品概述

### 1.1 产品定位

**GZEAMS (Hook Fixed Assets)** 是一款基于 **元数据驱动低代码架构** 的企业级固定资产管理平台。产品核心设计理念是"业务与流程分离"，通过可视化配置快速适配不同企业的资产管理需求，无需修改代码即可实现业务流程定制。

### 1.2 核心价值主张

| 价值维度 | 传统方案痛点 | GZEAMS 解决方案 |
|---------|-------------|----------------|
| **实施效率** | 需求变更需重新开发，周期长 | 元数据驱动，配置即可生效 |
| **组织适配** | 单组织设计，集团化管理困难 | 多租户架构，支持集团/公司/部门三级隔离 |
| **流程灵活性** | 流程硬编码，调整困难 | 可视化工作流设计器，拖拽式配置 |
| **数据一致性** | 盘点期间数据变动导致差异 | 快照机制，保证盘点数据准确性 |
| **系统集成** | 财务数据需手工录入 | 标准化ERP适配器，自动同步凭证 |
| **移动办公** | PC为主，现场操作不便 | 移动端PWA，支持离线盘点 |

### 1.3 适用场景

- **集团型企业**: 多公司、多部门统一管理，独立核算
- **中大型企业**: 资产数量大、种类多、流转频繁
- **监管严格行业**: 需要完整审计链和合规性报告（金融、医疗、政府）
- **快速成长企业**: 组织架构和业务流程频繁调整

---

## 二、核心架构设计

### 2.1 技术架构全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                        │
│  Vue 3 + Element Plus + LogicFlow (可视化流程设计器)             │
│  - DynamicForm (动态表单渲染)                                    │
│  - UnifiedScan (统一扫码组件)                                    │
│  - WorkflowDesigner (流程设计器)                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │ OpenAPI 3.0 (Swagger)
┌─────────────────────────────▼───────────────────────────────────┐
│                         API 网关层 (Gateway)                      │
│  drf-spectacular (自动文档) + Request/Response 拦截器           │
│  - 统一响应格式                                                  │
│  - JWT 认证 + 租户上下文                                         │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                        业务层 (Business)                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ Asset Service │  │ Inventory Svc │  │ Workflow Svc  │       │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘       │
│          │ emit events      │ emit events          │              │
└──────────┼──────────────────┼──────────────────┼────────────────┘
           │                  │                      │
┌──────────┼──────────────────┼──────────────────┼────────────────┐
│          │     事件总线 (Event Bus) - Django Signals            │
│  ┌───────▼───────┐  ┌──────▼────────┐  ┌──────▼─────────┐      │
│  │ Workflow      │  │ Notification  │  │ Audit         │      │
│  │ Listener      │  │ Listener      │  │ Listener      │      │
│  └───────────────┘  └───────────────┘  └───────────────┘      │
└─────────────────────────────────────────────────────────────────┘
           │                  │                      │
┌──────────┼──────────────────┼──────────────────┼────────────────┐
│  ┌───────▼───────┐  ┌──────▼────────┐  ┌──────▼─────────┐     │
│  │ SpiffWorkflow │  │ Redis Pub/Sub │  │ Celery        │     │
│  │ (BPMN 引擎)   │  │ (消息队列)     │  │ (异步任务)     │     │
│  └───────────────┘  └───────────────┘  └───────┬───────┘     │
│                                                   │            │
│                                        ┌──────────▼────────┐   │
│                                        │  Priority Queues  │   │
│                                        │  High/Low/Default │   │
│                                        └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
           │                  │                      │
┌──────────┼──────────────────┼──────────────────┼────────────────┐
│  ┌───────▼───────┐  ┌──────▼────────┐  ┌──────▼─────────┐     │
│  │ PostgreSQL    │  │ Redis         │  │ MinIO / S3    │     │
│  │ (JSONB动态字段)│  │ (缓存/队列)    │  │ (文件存储)     │     │
│  └───────────────┘  └───────────────┘  └───────────────┘     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          多租户中间件 (TenantMiddleware)               │   │
│  │  自动注入 current_company + Manager 默认过滤             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 元数据驱动引擎

产品的核心竞争力在于元数据驱动架构，实现"零代码"业务定制：

| 组件 | 功能 | 存储结构 |
|------|------|---------|
| **BusinessObject** | 定义可配置的业务实体 | PostgreSQL 表 |
| **FieldDefinition** | 动态字段定义（类型、验证、公式） | PostgreSQL 表 |
| **PageLayout** | 表单/列表页面的布局配置 | JSONB 字段 |
| **DynamicForm** | 前端动态表单渲染引擎 | Vue 3 组件 |

**关键特性**:
- 支持 15+ 字段类型: 文本、数字、日期、用户选择器、部门树、引用字段、公式计算等
- 公式字段支持: 使用 `simpleeval` 实现安全的表达式计算
- PostgreSQL JSONB 存储: 灵活且高效

### 2.3 多租户数据隔离

```
┌─────────────────────────────────────────────────────────┐
│                    Group (集团)                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │ Company A  │  │ Company B  │  │ Company C  │        │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │
│        │               │               │                │
│   ┌────┴────┐     ┌────┴────┐     ┌────┴────┐           │
│   │ 部门树   │     │ 部门树   │     │ 部门树   │           │
│   └─────────┘     └─────────┘     └─────────┘           │
└─────────────────────────────────────────────────────────┘

自动隔离机制:
- TenantMiddleware: 从 JWT 提取 company_id
- TenantManager: 所有查询自动添加 org 过滤
- BaseModel: 所有业务模型继承，自动获得隔离能力
```

### 2.4 事件驱动架构

```python
# 业务代码只负责"干活"
class AssetPickupService:
    def complete_pickup(self, pickup_id, user):
        # ... 业务逻辑 ...
        # 发出事件，不关心谁监听
        asset_picked_up.send(
            sender=self.__class__,
            pickup_id=pickup_id,
            asset_id=asset.id,
            user=user
        )

# 监听器处理副作用
@receiver(asset_picked_up)
def update_asset_status(sender, pickup_id, asset_id, user, **kwargs):
    """自动更新资产状态"""
    asset = Asset.objects.get(id=asset_id)
    asset.status = 'in_use'
    asset.save()

@receiver(asset_picked_up)
def start_approval_workflow(sender, pickup_id, asset_id, user, **kwargs):
    """需要审批时启动工作流"""
    if requires_approval(pickup_id):
        WorkflowService.start_process(...)

@receiver(asset_picked_up)
def send_notification(sender, pickup_id, asset_id, user, **kwargs):
    """发送通知"""
    NotificationService.notify_custodian(...)
```

**核心事件清单**:
- `asset_picked_up`: 资产领用完成
- `asset_transferred`: 资产调拨完成
- `inventory_confirmed`: 差异认定完成
- `workflow_completed`: 工作流审批完成
- `user_scanned_qr`: 用户扫码

---

## 三、产品功能模块

### 3.1 功能模块总览图

```
┌─────────────────────────────────────────────────────────────────┐
│                       GZEAMS 功能模块架构                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Phase 1: 基础资产核心                   │ │
│  │  资产分类 │ 多组织 │ 元数据引擎 │ 资产CRUD │ 资产操作     │ │
│  │  低值易耗 │ 生命周期 │ 移动端 │ 统一通知                   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Phase 2: 组织与权限                     │ │
│  │  企业微信SSO │ 组织同步 │ 通知中心 │ 组织增强 │ 权限增强   │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Phase 3: 工作流引擎                     │ │
│  │  LogicFlow设计器 │ 工作流执行引擎                         │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Phase 4: 盘点管理                       │ │
│  │  二维码盘点 │ RFID批量盘点 │ 快照差异 │ 任务分配 │ 业务链  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Phase 5: 财务集成                       │ │
│  │  集成框架 │ M18适配器 │ 凭证集成 │ 折旧计算 │ 财务报表    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Phase 6: 用户门户                       │ │
│  │  我的资产 │ 我的申请 │ 我的待办 │ 移动PWA                  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              ↓                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    Phase 7: 高级增强                       │ │
│  │  借用外借 │ 资产项目 │ 资产标签 │ 智能搜索                │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Phase 1: 基础资产核心 (Foundation)

| 模块 | 功能描述 | 核心模型 |
|------|---------|---------|
| **1.1 资产分类体系** | 树形分类，支持国标6大类，折旧方法配置 | `AssetCategory` |
| **1.2 多组织架构** | 租户数据隔离，集团/公司/部门三级管理 | `Organization`, `Department` |
| **1.3 元数据引擎** | 低代码配置，动态字段定义，页面布局 | `BusinessObject`, `FieldDefinition` |
| **1.4 资产CRUD** | 资产卡片管理，二维码生成，标签打印 | `Asset`, `AssetAttachment` |
| **1.5 资产操作** | 领用/调拨/借用/退库四类单据 | `AssetPickup`, `AssetTransfer` |
| **1.6 低值易耗** | 批次管理，库存预警，成本统计 | `Consumable`, `ConsumableStock` |
| **1.7 生命周期** | 采购→入库→领用→维护→处置全流程 | `PurchaseRequest`, `DisposalRequest` |
| **1.8 移动端增强** | 离线数据库，智能同步，移动审批 | `MobileDevice`, `SyncQueue` |
| **1.9 统一通知** | 多渠道通知（站内/邮件/短信/企微） | `Notification`, `NotificationTemplate` |

### 3.3 Phase 2: 组织与权限 (Organization & Permissions)

| 模块 | 功能描述 | 核心模型 |
|------|---------|---------|
| **2.1 企业微信SSO** | OAuth2登录，自动创建用户 | `WeWorkConfig`, `UserMapping` |
| **2.2 组织同步** | 部门/用户信息自动同步 | `SyncLog` |
| **2.3 通知中心** | 统一消息推送，模板管理 | `NotificationChannel`, `InAppMessage` |
| **2.4 组织增强** | 多部门用户，部门主管，数据权限 | `UserDepartment`, `Department` |
| **2.5 权限增强** | 字段级权限，行级权限，权限继承 | `FieldPermission`, `DataPermission` |

### 3.4 Phase 3: 工作流引擎 (Workflow Engine)

| 模块 | 功能描述 | 核心模型 |
|------|---------|---------|
| **3.1 LogicFlow设计器** | 可视化流程设计，拖拽式配置 | `WorkflowDefinition` |
| **3.2 执行引擎** | 流程实例管理，任务分配，状态流转 | `WorkflowInstance`, `WorkflowTask` |

**支持节点类型**:
- `start`: 开始节点
- `end`: 结束节点（多种结束状态）
- `approval`: 审批节点
- `condition`: 条件分支
- `parallel`: 并行网关
- `cc`: 抄送节点
- `notify`: 通知节点

### 3.5 Phase 4: 盘点管理 (Inventory Management)

| 模块 | 功能描述 | 核心模型 |
|------|---------|---------|
| **4.1 二维码盘点** | 扫码盘点，PDA/手机支持，离线缓存 | `InventoryTask`, `InventoryScan` |
| **4.2 RFID批量盘点** | 批量扫描，多读卡器协调 | `RFIDTag`, `ReaderAdapter` |
| **4.3 快照差异** | 不可变快照，自动差异检测 | `InventorySnapshot`, `InventoryDifference` |
| **4.4 任务分配** | 多种分配模式，进度监控 | `InventoryAssignment` |
| **4.5 业务链条** | 差异审批，调账处理，报告生成 | `DifferenceResolution`, `AssetAdjustment` |

**差异类型**:
- 盘亏 (有账无物)
- 盘盈 (有物无账)
- 位置不符
- 状态不符
- 信息错误

### 3.6 Phase 5: 财务集成 (Financial Integration)

| 模块 | 功能描述 | 核心模型 |
|------|---------|---------|
| **5.0 集成框架** | 通用ERP适配器，数据映射，日志监控 | `IntegrationConfig`, `FieldMapping` |
| **5.1 M18适配器** | 万达宝M18 ERP连接器 | `M18Adapter` |
| **5.2 凭证集成** | 自动生成财务凭证，推送到ERP | `Voucher`, `VoucherTemplate` |
| **5.3 折旧计算** | 多种折旧方法，月度自动计算 | `AssetDepreciation` |
| **5.4 财务报表** | 资产报表，折旧报表，变动报表 | `ReportTemplate` |

**折旧方法**:
- 直线法 (Straight-line)
- 双倍余额递减法 (Double Declining Balance)
- 年数总和法 (Sum of Years' Digits)
- 不计提折旧

### 3.7 Phase 6: 用户门户 (User Portal)

| 模块 | 功能描述 | 核心API |
|------|---------|---------|
| **6.1 我的资产** | 保管/使用/借用资产查询 | `GET /api/portal/my-assets/` |
| **6.2 我的申请** | 领用/调拨/借用申请记录 | `GET /api/portal/my-applications/` |
| **6.3 我的待办** | 待审批/待处理/待盘点事项 | `GET /api/portal/my-tasks/` |
| **6.4 移动PWA** | 离线访问，推送通知，添加到主屏幕 | PWA Manifest |

### 3.8 Phase 7: 高级增强 (Advanced Enhancements)

| 模块 | 功能描述 | 核心模型 |
|------|---------|---------|
| **7.1 借用外借增强** | 内部/外部借用，押金管理，逾期计费，信用管理 | `AssetLoan`, `LoanDeposit`, `BorrowerCredit` |
| **7.2 资产项目管理** | 项目资产分配，成本核算，项目结项回收 | `AssetProject`, `ProjectAsset`, `ProjectCost` |
| **7.3 资产标签系统** | 多维度标签，灵活分类，快速筛选 | `TagGroup`, `AssetTag`, `AssetTagRelation` |
| **7.4 智能搜索增强** | Elasticsearch全文搜索，拼音匹配，搜索建议 | `SearchHistory`, `SavedSearch` |

**Phase 7.1 借用外借增强特性**:
- 支持内部借用 (`internal`) 和外部借用 (`external`)
- 外部借用押金管理（收取、退还、支付方式）
- 逾期费用自动计算（分级费率配置）
- 借用人信用评分系统

**Phase 7.2 资产项目管理特性**:
- 项目定义（成员、时间、预算）
- 资产分配类型（永久/临时/共享）
- 项目成本核算（基于折旧）
- 跨项目调拨审批

**Phase 7.3 资产标签系统特性**:
- 标签分组管理（使用状态、来源、重要性等）
- 自定义标签（颜色、图标、描述）
- 多标签组合筛选
- 自动打标签规则

**Phase 7.4 智能搜索增强特性**:
- Elasticsearch 8.x 全文索引
- 中文分词 + 拼音支持
- 实时搜索建议
- 搜索历史和收藏搜索
- 结果高亮和聚合过滤

---

## 四、公共基类体系

GZEAMS 的核心设计理念是"约定优于配置"，所有业务模块必须继承公共基类，自动获得标准功能。

### 4.1 公共基类清单

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields处理 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法、组织隔离 |

### 4.2 BaseModel 自动字段

```python
class BaseModel(models.Model):
    # 组织隔离
    org = models.ForeignKey('organizations.Organization', ...)

    # 软删除
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # 审计字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('users.User', ...)

    # 动态扩展
    custom_fields = models.JSONField(default=dict, null=True, blank=True)

    def soft_delete(self):
        """软删除方法，禁止物理删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
```

### 4.3 统一API响应格式

**成功响应**:
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        "code": "ASSET001"
    }
}
```

**错误响应**:
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "code": ["该字段不能为空"]
        }
    }
}
```

**批量操作响应**:
```json
{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": true}
    ]
}
```

---

## 五、技术规范

### 5.1 后端开发规范

| 规范项 | 要求 | 说明 |
|-------|------|------|
| **代码注释** | ✅ 强制英文 | 所有注释必须是英文 |
| **模型继承** | ✅ 必须继承 BaseModel | 自动获得组织隔离等功能 |
| **软删除** | ✅ 禁止物理删除 | 使用 `soft_delete()` 方法 |
| **异步任务** | ✅ Celery 分级队列 | 高/中/低优先级队列 |
| **事件驱动** | ✅ 使用 Django Signals | 业务代码发出事件，监听器处理副作用 |
| **API文档** | ✅ drf-spectacular | 自动生成 OpenAPI 文档 |

### 5.2 前端开发规范

| 规范项 | 要求 | 说明 |
|-------|------|------|
| **框架** | Vue 3 Composition API | 禁用 Options API |
| **组件库** | Element Plus | 统一UI风格 |
| **命名** | camelCase | 后端 snake_case 自动转换 |
| **状态管理** | Pinia | 全局状态管理 |
| **错误处理** | 统一拦截器 | 禁用 `alert()` |

### 5.3 数据库设计规范

| 规范项 | 要求 |
|-------|------|
| **动态字段** | PostgreSQL JSONB |
| **索引** | 外键自动索引，常查询字段添加索引 |
| **约束** | 数据库级别约束 + 应用层验证 |

---

## 六、产品特色

### 6.1 与竞品对比

| 特性 | GZEAMS | 传统固定资产系统 | SaaS固定资产产品 |
|-----|--------|----------------|----------------|
| **定制能力** | 元数据驱动，零代码定制 | 需二次开发 | 固定功能 |
| **部署方式** | 私有化部署/云端 | 私有化部署 | 仅云端 |
| **数据所有权** | 客户完全拥有 | 客户完全拥有 | 托管在供应商 |
| **工作流** | 可视化设计器 | 硬编码 | 有限定制 |
| **财务集成** | 标准适配器 | 定制开发 | 有限集成 |
| **盘点方案** | 二维码+RFID双模 | 单一方案 | 单一方案 |

### 6.2 核心差异化功能

1. **快照盘点机制**: 业界首创，确保盘点期间数据变动不影响盘点结果
2. **双模盘点**: 二维码精准盘点 + RFID批量盘点，适应不同场景
3. **元数据驱动**: 无需代码修改即可扩展字段和表单
4. **事件驱动架构**: 业务与流程完全解耦，易于扩展
5. **多租户原生**: 从底层设计就支持多组织数据隔离

---

## 七、实施路线图

### 7.1 分阶段实施计划

```
Phase 1: 基础资产核心 [已完成]
├── 1.1 资产分类体系
├── 1.2 多组织架构
├── 1.3 元数据引擎
├── 1.4 资产CRUD
├── 1.5 资产操作
├── 1.6 低值易耗
├── 1.7 生命周期
├── 1.8 移动端增强
└── 1.9 统一通知

Phase 2: 组织与权限 [已完成]
├── 2.1 企业微信SSO
├── 2.2 组织同步
├── 2.3 通知中心
├── 2.4 组织增强
└── 2.5 权限增强

Phase 3: 工作流引擎 [已完成]
├── 3.1 LogicFlow设计器
└── 3.2 执行引擎

Phase 4: 盘点管理 [已完成]
├── 4.1 二维码盘点
├── 4.2 RFID批量盘点
├── 4.3 快照差异
├── 4.4 任务分配
└── 4.5 业务链条

Phase 5: 财务集成 [已完成]
├── 5.0 集成框架
├── 5.1 M18适配器
├── 5.2 凭证集成
├── 5.3 折旧计算
└── 5.4 财务报表

Phase 6: 用户门户 [开发中]
├── 6.1 我的资产
├── 6.2 我的申请
├── 6.3 我的待办
└── 6.4 移动PWA

Phase 7: 高级增强 [规划中]
├── 7.1 借用外借增强
│   ├── 内部/外部借用支持
│   ├── 押金管理
│   ├── 逾期计费
│   └── 信用评分系统
├── 7.2 资产项目管理
│   ├── 项目资产分配
│   ├── 成本核算
│   ├── 项目结项回收
│   └── 跨项目调拨
├── 7.3 资产标签系统
│   ├── 标签分组管理
│   ├── 多维度标签
│   ├── 组合筛选
│   └── 自动打标签
└── 7.4 智能搜索增强
    ├── Elasticsearch集成
    ├── 中文分词+拼音
    ├── 搜索建议
    └── 搜索历史收藏
```

### 7.2 技术债务与持续改进

- [ ] 完善 E2E 测试覆盖
- [ ] 性能优化与压力测试
- [ ] 国际化支持 (i18n)
- [ ] 更多ERP适配器 (SAP, Oracle, Kingdee)
- [ ] AI 辅助盘点 (图像识别)

---

## 八、文档索引

### 8.1 架构文档

- [技术架构规范](architecture/technical-architecture.md) - 详细的技术架构定义
- [数据库设计文档](database/) - 数据模型设计

### 8.2 PRD 文档

- [Phase 1 PRDs](plans/phase1_*/) - 基础资产核心模块
- [Phase 2 PRDs](plans/phase2_*/) - 组织与权限模块
- [Phase 3 PRDs](plans/phase3_*/) - 工作流引擎模块
- [Phase 4 PRDs](plans/phase4_*/) - 盘点管理模块
- [Phase 5 PRDs](plans/phase5_*/) - 财务集成模块
- [Phase 6 PRDs](plans/phase6_*/) - 用户门户模块
- [Phase 7 PRDs](plans/phase7_*/) - 高级增强模块

### 8.3 实施报告

- [实施报告](reports/implementation/) - 各阶段实施详情
- [合规验证报告](reports/compliance/) - 代码规范验证
- [快速入门指南](reports/quickstart/) - 模块快速入门

---

## 九、联系与支持

- **GitHub**: https://github.com/liugang926/HOOK_GZEAMS.git
- **参考标杆**: https://yzcweixin.niimbot.com/
- **问题反馈**: GitHub Issues

---

> 本文档由 GZEAMS 项目团队维护，最后更新于 2026-01-22
