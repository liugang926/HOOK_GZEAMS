# GZEAMS 对象分层与历史语义收敛 PRD

## 文档信息
| 字段 | 说明 |
|------|------|
| 功能名称 | 对象分层与历史语义收敛 |
| 功能代码 | `object_layering_history_convergence` |
| 文档版本 | 1.0.0 |
| 创建日期 | 2026-03-25 |
| 维护人 | Codex |
| 审核状态 | 草稿 |
| 关联文档 | `docs/prd/prd-business-workspace-convergence-phase1-2026-03-20.md` / `docs/prd/prd-lifecycle-cross-object-actions-closed-loop-2026-03-13.md` / `docs/prd/prd-master-detail-aggregate-closed-loop-solution-2026-03-16.md` |

## 1. 功能概述与业务场景

### 1.1 业务背景

GZEAMS 已经完成统一动态对象路由与动态详情页主干：

1. 前端统一通过 `/objects/{code}` 进入业务对象列表、表单与详情页。
2. 详情页已经具备 `Details / Related / ChangeHistory` 三段式结构。
3. 生命周期对象还会在详情页正文区加载跨对象 `Timeline`。
4. `AssetStatusLog`、`ConfigurationChange` 等“变更类对象”既被注册为 BusinessObject，又被作为详情页的反向关联对象展示。

这意味着项目当前的主要问题不再是“有没有历史能力”，而是“同一类历史信息被三套结构同时表达”。

### 1.2 当前痛点

| 现状 | 问题 | 影响 |
|------|------|------|
| 详情页固定存在 `Related` 和 `ChangeHistory` | 用户难以区分“相关业务记录”和“变更审计记录” | 信息架构混乱 |
| 资产详情页额外存在生命周期时间线 | `Timeline` 与 `ChangeHistory` 语义边界不清 | 同一事件被多处展示 |
| `AssetStatusLog` 被作为独立对象注册 | 既能作为一级对象查询，又已经被生命周期时间线消费 | 菜单和详情体验重复 |
| `ConfigurationChange` 被挂到 `Asset` / `ITAsset` 的反向关联中 | 在 `Related` 页展示“配置变更”，与 `ChangeHistory` 概念冲突 | 用户误认为这是业务子表 |
| `menu_config` 与 BusinessObject fallback 菜单并存 | 隐藏规则可能在不同入口表现不一致 | 菜单治理不稳定 |
| 历史页面与后端序列化契约已有漂移 | 旧专页字段与统一对象序列化字段不一致 | 后续维护成本持续上升 |

### 1.3 问题定义

本期将正式区分以下三类信息：

1. **业务对象**：有明确业务状态、动作、审批或业务闭环的对象，如 `Asset`、`PurchaseRequest`、`Maintenance`。
2. **关联对象**：属于业务上下游或主从关系的数据，如 `PickupItem`、`TransferItem`、`Maintenance`、`DisposalRequest`。
3. **审计对象**：用于记录字段变化、状态变化、配置变化、操作轨迹的数据，如 `ActivityLog`、`AssetStatusLog`、`ConfigurationChange`。

当前冲突的本质，是把第 3 类对象同时当成了第 1 类和第 2 类来处理。

### 1.4 本期目标

1. 建立对象分层规范，明确 `root/detail/log/reference` 的平台语义。
2. 让 `AssetStatusLog`、`ConfigurationChange` 从“业务对象”收敛为“审计对象”。
3. 让详情页 `Related` 仅展示业务关联，不再承载审计类关联。
4. 引入统一历史接口，承接字段审计、状态审计、配置审计、工作流操作等历史来源。
5. 保留管理员查询能力，但默认不再把审计对象作为业务菜单入口。
6. 统一菜单、对象元数据、运行时展示规则，避免多源定义。

### 1.5 非目标

1. 本期不重做全部时间线 UI 风格。
2. 本期不改造全部日志模型为同一物理表。
3. 本期不移除所有 legacy 页面，只定义过渡策略。
4. 本期不重做生命周期服务本身的业务逻辑，仅收敛展示与对象语义。

## 2. 用户角色与权限

| 用户角色 | 使用场景 | 核心权限 |
|---------|---------|----------|
| 系统管理员 | 维护对象元数据、菜单策略、审计入口 | 修改对象分层、发布菜单配置、查看全量审计 |
| 业务管理员 | 维护对象页面结构与关联展示策略 | 配置 `BusinessObject`、`ObjectRelationDefinition`、布局运行时 |
| 资产管理员 | 在资产详情页查看业务关联与历史轨迹 | 查看资产业务关联、查看历史、执行资产动作 |
| IT 管理员 | 查看 IT 资产配置变更与上下游记录 | 查看 IT 资产历史、查看配置变更、发起维护 |
| 审计/内控人员 | 跨资产检索状态变化与配置变化 | 只读查询审计数据 |
| 普通业务用户 | 在详情页消费统一历史与关联信息 | 按对象权限查看详情、关联、历史 |

### 2.1 权限矩阵

| 功能 | 系统管理员 | 业务管理员 | 资产管理员 | IT 管理员 | 审计人员 | 普通用户 |
|------|------------|------------|------------|-----------|----------|----------|
| 查看对象详情页 `Related` | ✅ | ✅ | ✅ | ✅ | ✅ | 视对象授权 |
| 查看对象详情页 `ChangeHistory` | ✅ | ✅ | ✅ | ✅ | ✅ | 视对象授权 |
| 查看统一历史中的审计来源明细 | ✅ | ✅ | ✅ | ✅ | ✅ | 视对象授权 |
| 独立查询 `AssetStatusLog` / `ConfigurationChange` | ✅ | ✅ | 视授权 | 视授权 | ✅ | ❌ |
| 修改对象分层规则 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 修改关联展示分区策略 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |

## 3. 公共模型引用声明

### 3.1 后端公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、引用字段归一化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围、创建人、删除状态过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 查询与分页能力 |
| Router | ObjectRouterViewSet | `apps.system.viewsets.object_router.ObjectRouterViewSet` | 统一对象路由、runtime、actions、relations |

### 3.2 本期涉及的核心模型/服务

| 组件 | 类型 | 说明 |
|------|------|------|
| `BusinessObject` | Metadata Model | 承载对象分层、菜单与独立入口策略 |
| `ObjectRelationDefinition` | Metadata Model | 承载关联对象的展示分区与表现策略 |
| `ActivityLog` | Audit Model | 通用对象活动日志 |
| `AssetStatusLog` | Audit Model | 资产状态变化审计 |
| `ConfigurationChange` | Audit Model | IT 配置变化审计 |
| `ActivityLogService` | Service | 通用对象变更差异记录 |
| `LifecycleClosedLoopService` | Service | 生命周期时间线聚合 |
| `ObjectHistoryAggregationService` | New Service | 本期新增，聚合多源历史为统一读模型 |

### 3.3 前端公共组件引用

| 组件类型 | 使用组件 | 引用路径 | 说明 |
|---------|---------|---------|------|
| 动态详情页 | DynamicDetailPage | `frontend/src/views/dynamic/DynamicDetailPage.vue` | 统一对象详情入口 |
| 详情基座 | BaseDetailPage | `frontend/src/components/common/BaseDetailPage.vue` | 统一详情布局 |
| 主标签容器 | BaseDetailMainTabs | `frontend/src/components/common/BaseDetailMainTabs.vue` | `Details / Related / ChangeHistory` 主入口 |
| 关联对象表格 | RelatedObjectTable | `frontend/src/components/common/RelatedObjectTable.vue` | 业务关联展示 |
| 历史组件 | ActivityTimeline | `frontend/src/components/common/ActivityTimeline.vue` | 历史/时间线可视化 |
| 工作区扩展宿主 | ObjectWorkbenchPanelHost | `frontend/src/components/common/ObjectWorkbenchPanelHost.vue` | 运行时扩展面板承载 |

## 4. 数据模型设计

### 4.1 对象分层标准

| 对象层级 | `object_role` | `is_top_level_navigable` | `allow_standalone_query` | `allow_standalone_route` | 默认展示位置 | 示例 |
|---------|---------------|--------------------------|--------------------------|--------------------------|--------------|------|
| 顶层业务对象 | `root` | `true` | `true` | `true` | 列表页 / 详情页 / 工作区 | `Asset`、`PurchaseRequest`、`Maintenance` |
| 明细/子对象 | `detail` | `false` | `true` | `false` | 主表详情内联或 `Related` | `PickupItem`、`TransferItem` |
| 审计/日志对象 | `log` | `false` | `true` | `false` | 详情页 `ChangeHistory` / 管理员审计页 | `AssetStatusLog`、`ConfigurationChange` |
| 引用型对象 | `reference` | `false` | `true` | `false` | 参考选择器 / 紧凑展示 | 字典类、引用辅助对象 |

### 4.2 本期对象标准化目标

| 对象代码 | 当前问题 | 目标语义 | 目标配置 |
|---------|---------|---------|---------|
| `AssetStatusLog` | 仍被视为普通可导航对象 | 资产状态审计对象 | `object_role=log`，隐藏菜单，禁止独立 runtime 路由 |
| `ConfigurationChange` | 作为反向关联和专页并存 | IT 配置审计对象 | `object_role=log`，隐藏菜单，禁止独立 runtime 路由 |

### 4.3 `BusinessObject` 配置约定

本期不新增独立表，优先复用现有字段完成分层治理：

| 字段 | 用途 | 本期规则 |
|------|------|----------|
| `object_role` | 平台对象层级 | 审计对象必须使用 `log` |
| `is_top_level_navigable` | 是否允许作为正式导航对象 | 审计对象统一为 `false` |
| `allow_standalone_query` | 是否允许独立查询 | 审计对象保留 `true`，供管理员审计使用 |
| `allow_standalone_route` | 是否允许走标准详情运行时 | 审计对象统一为 `false` |
| `is_menu_hidden` | 是否进入自动菜单 | 审计对象统一为 `true` |
| `menu_config.workbench` | 工作区扩展配置 | 允许定义历史来源策略，不再定义业务主入口 |

### 4.4 `ObjectRelationDefinition` 展示分区约定

本期不新增强制字段，优先复用 `extra_config` 承载展示语义：

```json
{
  "presentation_zone": "related",
  "history_source_type": "",
  "admin_query_entry": false
}
```

约定如下：

| 配置项 | 可选值 | 说明 |
|------|--------|------|
| `extra_config.presentation_zone` | `related` / `history` / `hidden` | 控制该关系出现在 `Related`、`ChangeHistory` 还是完全隐藏 |
| `extra_config.history_source_type` | `activity` / `status_log` / `config_change` / `workflow` | 供统一历史聚合服务识别来源类型 |
| `extra_config.admin_query_entry` | `true/false` | 是否允许从管理员审计中心独立检索 |

### 4.5 统一历史读模型

新增统一历史读模型 `ObjectHistoryEntry`，逻辑字段如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 历史事件唯一键 |
| `category` | string | `activity` / `status_change` / `config_change` / `workflow` / `custom` |
| `sourceCode` | string | 来源对象代码 |
| `sourceLabel` | string | 来源对象显示名 |
| `objectCode` | string | 当前可跳转对象代码 |
| `objectId` | string | 当前可跳转对象 ID |
| `recordLabel` | string | 当前记录标题 |
| `action` | string | 动作代码 |
| `actionLabel` | string | 动作显示名 |
| `userName` | string | 操作人 |
| `timestamp` | string | 事件时间 |
| `description` | string | 描述 |
| `changes` | array | 字段差异列表 |
| `isNavigable` | boolean | 是否允许跳转 |

## 5. API 接口设计

### 5.1 设计原则

1. `Related` 与 `ChangeHistory` 必须从后端协议上彻底分区。
2. 历史页不再直接依赖单一 `ActivityLog`，而是使用统一聚合接口。
3. 审计对象保留独立查询能力，但不再作为普通业务详情入口。

### 5.2 统一历史接口

#### 5.2.1 获取对象统一历史

```http
GET /api/system/objects/{code}/{id}/history/
```

查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `page` | int | 页码 |
| `page_size` | int | 每页条数 |
| `category` | string | 可选，按历史类别过滤 |
| `source` | string | 可选，按来源对象过滤 |

成功响应：

```json
{
  "success": true,
  "data": {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "asset-status-001",
        "category": "status_change",
        "sourceCode": "AssetStatusLog",
        "sourceLabel": "Asset Status Log",
        "objectCode": "Asset",
        "objectId": "uuid",
        "recordLabel": "ASSET001",
        "action": "status_change",
        "actionLabel": "Status Changed",
        "userName": "admin",
        "timestamp": "2026-03-25T10:30:00+08:00",
        "description": "Asset status updated.",
        "changes": [
          {
            "fieldCode": "asset_status",
            "fieldLabel": "Asset Status",
            "oldValue": "idle",
            "newValue": "maintenance"
          }
        ],
        "isNavigable": false
      }
    ]
  }
}
```

#### 5.2.2 聚合规则

| 对象 | 默认历史来源 |
|------|-------------|
| `Asset` | `ActivityLog` + `AssetStatusLog` + 生命周期工作流日志 |
| `ITAsset` | `ActivityLog` + `ConfigurationChange` |
| 生命周期对象 | `ActivityLog` + 工作流日志 |

### 5.3 Runtime 接口扩展

在运行时 payload 中新增 `history` 配置块：

```http
GET /api/system/objects/{code}/runtime/?mode=readonly
```

新增字段：

```json
{
  "success": true,
  "data": {
    "history": {
      "enabled": true,
      "fetchUrl": "/system/objects/Asset/{id}/history/",
      "defaultCategories": ["activity", "status_change"],
      "defaultSources": ["ActivityLog", "AssetStatusLog"]
    }
  }
}
```

### 5.4 审计对象独立查询策略

以下对象保留独立查询接口，但不再作为普通业务详情入口：

| 对象 | 列表查询 | 独立详情 runtime | 菜单显示 |
|------|----------|------------------|----------|
| `AssetStatusLog` | 保留 | 禁止 | 隐藏 |
| `ConfigurationChange` | 保留 | 禁止 | 隐藏 |

说明：

1. 保留 `GET /api/system/objects/AssetStatusLog/` 与 `GET /api/system/objects/ConfigurationChange/`。
2. 默认从管理员审计入口或系统管理页进入，不进入业务主菜单。
3. 独立查询页允许逐步迁移到统一“审计中心”工作区。

### 5.5 标准错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 历史聚合参数或元数据配置错误 |
| `PERMISSION_DENIED` | 403 | 用户无权查看历史或审计数据 |
| `NOT_FOUND` | 404 | 对象或历史来源不存在 |
| `CONFLICT` | 409 | 元数据配置冲突，如同时声明 `related` 与 `history` |
| `SERVER_ERROR` | 500 | 聚合服务异常 |

## 6. 前端组件设计

### 6.1 详情页主结构调整

#### 6.1.1 `Related` 页规则

`Related` 只展示以下对象：

1. 主从明细对象。
2. 生命周期上下游业务对象。
3. 业务统计或业务关联对象。

以下对象不得再出现在 `Related`：

1. `AssetStatusLog`
2. `ConfigurationChange`
3. 其他 `object_role=log` 的对象

#### 6.1.2 `ChangeHistory` 页规则

`ChangeHistory` 统一展示：

1. 通用对象活动日志
2. 状态变更日志
3. 配置变更日志
4. 工作流操作历史

`ActivityTimeline` 继续作为渲染组件使用，但数据来源切换为统一历史接口。

#### 6.1.3 生命周期时间线规则

生命周期 `Timeline` 继续保留，但只承担“跨对象业务轨迹”职责：

1. 来源单据创建
2. 审批通过/拒绝
3. 下游单据生成
4. 生命周期状态推进

不得再把普通字段更新历史混入该时间线。

### 6.2 管理员审计入口

本期采用过渡方案：

1. 保留现有 `StatusLogList`、`ConfigurationChangeList` 管理页供管理员使用。
2. 业务主菜单默认不展示这些入口。
3. 后续在系统管理域收敛为统一 `AuditWorkbench`。

### 6.3 菜单与路由治理

| 层 | 本期规则 |
|----|----------|
| `hardcoded_object_catalog` | 为审计对象写入正确默认值：`object_role=log`、隐藏菜单、禁止独立路由 |
| `BusinessObject` | 作为对象分层运行时真相来源 |
| `menu_config` | 仅负责菜单分组、顺序、图标与系统管理入口 |
| fallback 菜单生成 | 必须尊重 `is_menu_hidden`、`object_role`、`is_top_level_navigable`、`allow_standalone_route` |

## 7. 实施计划

### 7.1 Phase A: 元数据收敛

1. 修正 `AssetStatusLog`、`ConfigurationChange` 的 hardcoded object 定义。
2. 通过同步服务回写 `BusinessObject` 元数据。
3. 修正 `menu_config`，确保默认业务菜单不暴露审计对象。
4. 为相关 `ObjectRelationDefinition` 写入 `extra_config.presentation_zone=history`。

### 7.2 Phase B: 历史聚合服务

1. 新增 `ObjectHistoryAggregationService`。
2. 聚合 `ActivityLog`、`AssetStatusLog`、`ConfigurationChange`、工作流日志。
3. 提供 `/api/system/objects/{code}/{id}/history/` 接口。
4. 增加 runtime `history` 配置输出。

### 7.3 Phase C: 前端详情页收敛

1. `BaseDetailMainTabs` 的 `Related` 页按展示分区过滤关系。
2. `ChangeHistory` 切换到统一历史接口。
3. `DynamicDetailPage` 保持生命周期时间线卡片，但不承载审计类关系。
4. 资产和 IT 资产详情页移除 `ConfigurationChange` 等审计关联卡片。

### 7.4 Phase D: 过渡与退役

1. 保留管理员审计页的旧入口。
2. legacy 路由仅作为管理员或旧链接兼容，不再作为业务主入口。
3. 下一期评估统一 `AuditWorkbench`，替代散落的专页。

## 8. 测试用例

### 8.1 模型与元数据测试

| 编号 | 测试点 | 预期 |
|------|--------|------|
| TC-M1 | `AssetStatusLog` 同步后为 `object_role=log` | 元数据正确 |
| TC-M2 | `ConfigurationChange` 同步后隐藏菜单 | `is_menu_hidden=true` |
| TC-M3 | `presentation_zone=history` 的关系不进入 `Related` | 前端只走历史聚合 |

### 8.2 服务与 API 测试

| 编号 | 测试点 | 预期 |
|------|--------|------|
| TC-A1 | 获取 `Asset` 统一历史 | 返回 `ActivityLog + AssetStatusLog` 聚合结果 |
| TC-A2 | 获取 `ITAsset` 统一历史 | 返回 `ActivityLog + ConfigurationChange` 聚合结果 |
| TC-A3 | 无权限用户查询审计对象独立列表 | 返回 `PERMISSION_DENIED` |
| TC-A4 | 历史分类过滤 | 仅返回指定 `category` |

### 8.3 前端测试

| 编号 | 测试点 | 预期 |
|------|--------|------|
| TC-F1 | 资产详情页 `Related` 不再显示状态日志/配置变更 | 仅保留业务关联 |
| TC-F2 | `ChangeHistory` 可展示状态变化与配置变化 | 历史可见且可筛选 |
| TC-F3 | 生命周期时间线仍显示跨对象轨迹 | 业务时间线不回退 |
| TC-F4 | fallback 菜单生成 | 审计对象不进入主菜单 |

### 8.4 回归测试

| 编号 | 测试点 | 预期 |
|------|--------|------|
| TC-R1 | `/objects/Asset/{id}` | 详情页正常打开 |
| TC-R2 | `/assets/status-logs` legacy 入口 | 可兼容或重定向到管理员页 |
| TC-R3 | 统一菜单加载 | 不出现重复或错误入口 |

## 9. 验收标准

| 编号 | 验收项 | 标准 |
|------|--------|------|
| AC-1 | 对象分层生效 | `AssetStatusLog`、`ConfigurationChange` 为 `log` 对象 |
| AC-2 | 详情页分区收敛 | `Related` 仅展示业务关联，`ChangeHistory` 展示审计历史 |
| AC-3 | 历史聚合接口可用 | `Asset`、`ITAsset` 至少能稳定返回两类以上历史来源 |
| AC-4 | 菜单收敛 | 审计对象不进入主业务菜单 |
| AC-5 | 兼容策略有效 | 管理员仍可独立查询日志对象 |
| AC-6 | 生命周期体验不退化 | 原有资产生命周期时间线能力保持可用 |

## 10. 预期收益

1. 详情页信息架构恢复清晰，用户能区分“业务关联”和“历史审计”。
2. 审计对象不再污染主业务菜单，平台对象分层更加一致。
3. 统一历史接口可以复用于门户、通知、审批和后续审计中心。
4. 减少多套历史页面与多套字段契约并行带来的维护成本。
5. 为后续 `AuditWorkbench`、对象工作区收敛和日志模型统一奠定基础。
