# PRD: 记录页 Surface Priority 运行时治理

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.50 |
| 作者/Agent | Codex |

## 1. 功能概述与业务场景

### 1.1 背景
Phase 7.2.48 和 Phase 7.2.49 已完成记录页 / 工作台模式拆分和默认模式元数据化，但默认记录页仍然缺少“哪些 surface 可以留在记录页，哪些必须下沉到工作台”的统一治理协议。

典型问题：
- 同一对象的 `summary card / queue / detail panel / recommended action` 仍可能同时进入默认记录页。
- 前端虽然有 `record / workspace` 模式，但缺少 item 级别优先级，无法做细粒度收敛。
- 工作台配置对象越来越多，如果没有 surface 优先级，记录页最终还会继续变重。

### 1.2 目标
引入 item 级别 `surfacePriority` 运行时协议，并在默认记录页中只保留 `primary / context` 类 surface：
- `primary`: 首屏关键摘要
- `context`: 状态、闭环、SLA 等上下文摘要
- `related`: 队列、关联导航、扩展 panel
- `activity`: 活动/时间线类 surface
- `admin`: 运维/建议动作/异步指示类 surface

同时满足：
- 记录页默认只展示 `primary / context`
- `workspace` 模式展示全部 surface
- 仅对明确标注了 surface priority 的对象开启 page mode 切换，避免影响未治理对象

### 1.3 适用对象
- 资产主对象：`Asset`
- 资产项目：`AssetProject`
- 生命周期单据：`PurchaseRequest`、`AssetReceipt`、`Maintenance`、`DisposalRequest`
- 资产操作单据：`AssetPickup`、`AssetTransfer`、`AssetReturn`、`AssetLoan`

### 1.4 本阶段不做
- 不引入数据库字段
- 不改对象动作协议
- 不改列表页
- 不将 `surfacePriority` 配置暴露到后台 UI 编辑器

## 2. 用户角色与权限

| 角色 | 查看记录页 | 切换工作台 | 查看关联队列 | 查看工作台面板 | 执行动作 |
|------|------------|------------|--------------|----------------|----------|
| 资产管理员 | 是 | 是 | 是 | 是 | 是 |
| 单据经办人 | 是 | 是 | 是 | 是 | 是 |
| 审批人 | 是 | 是 | 按流程权限 | 按对象权限 | 按流程权限 |
| 普通查看用户 | 是 | 否/按对象权限 | 否/按对象权限 | 否/按对象权限 | 否 |

说明：
- 本阶段不新增权限点。
- `workspace` 的可见性仍由对象和运行时配置决定。

## 3. 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |

补充说明：
- 本阶段不增加新模型，仅扩展 runtime workbench nested metadata。

## 4. 数据模型设计

### 4.1 持久化模型
本阶段无数据库 schema 变更。

### 4.2 运行时协议扩展

| 字段 | 作用域 | 可选值 | 说明 |
|------|--------|--------|------|
| `surfacePriority` | workbench item | `primary / context / related / activity / admin` | item 级展示优先级 |
| `surface_priority` | workbench item | 同上 | 后端 snake_case 兼容键 |

适用对象：
- `summary_cards`
- `queue_panels`
- `exception_panels`
- `detail_panels`
- `async_indicators`
- `sla_indicators`
- `recommended_actions`
- `closure_panel`

### 4.3 记录页过滤规则
1. 如果对象没有 workspace-only surface priority，则保持既有详情页行为。
2. 如果对象存在 `related / activity / admin` surface，默认记录页只显示 `primary / context`。
3. 当 `page_mode=workspace` 时，显示全部 surface。
4. `ClosedLoopNavigationCard` 与 `ObjectWorkbenchPanelHost` 视为 workspace-only surface。

## 5. API 接口设计

本阶段不新增接口，仅扩展 runtime nested metadata：

| 方法 | 接口 | 变更 |
|------|------|------|
| `GET` | `/api/system/objects/{code}/{id}/runtime/` | `workbench` nested items 允许返回 `surface_priority` |

错误码继续沿用：
- `VALIDATION_ERROR`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `SERVER_ERROR`

## 6. 前端组件设计

### 6.1 useObjectWorkbench
- 新增 `allowedSurfacePriorities` 输入。
- 如果 item 定义了 `surfacePriority`，则按允许集合过滤。
- 未定义 `surfacePriority` 的旧对象保持兼容，不强制过滤。

### 6.2 DynamicDetailPage
- 基于 runtime workbench 判断当前对象是否存在 workspace-only surface。
- 仅在存在 workspace-only surface 时展示 `record / workspace` 切换。
- 记录页默认只渲染 `primary / context` surface。
- 工作台模式继续展示完整 process surface。

### 6.3 Runtime Contract
- 为 workbench nested items 的 `surfacePriority` 加入枚举校验。

### 6.4 后端 Menu Config
- 为目标对象的 workbench 配置补齐 `surface_priority` 默认值。
- 不直接手工散落到每个 item，而是在配置层做统一装饰。

## 7. 测试用例

### 7.1 前端
- `useObjectWorkbench` 能过滤 workspace-only surface
- `DynamicDetailPage` 记录页模式隐藏 `related / admin` surface
- `DynamicDetailPage` `page_mode=workspace` 恢复完整 surface
- runtime contract 对非法 `surfacePriority` 报错

### 7.2 后端
- `menu_config` 输出预期的 `surface_priority`
- `runtime` API 能透传 `surfacePriority`

### 7.3 验收标准
- 目标对象默认记录页明显减载
- 记录页与工作台不再只是“页面模式切换”，而是有明确的 surface 分层
- 未治理对象不发生意外回退
